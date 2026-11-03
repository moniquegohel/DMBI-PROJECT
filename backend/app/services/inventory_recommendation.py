"""
inventory_recommendation.py — Milestone 10 & 11: Inventory Recommendation & Dashboard Service

Implements:
1. Batch inventory recommendation across all store-product combinations:
   - Average Daily Demand Velocity (d_bar)
   - Supplier Lead Time Demand (D_L)
   - Safety Stock Buffer (SS)
   - Reorder Point (ROP = d_bar * (L + S_buf))
   - Target Stock (S_target = D_horizon + SS)
   - Suggested Reorder Quantity (Q_reorder >= 0)
   - 4-Tier Classification (Restock Soon, Stock Available, Excess Stock, Insufficient Data)
2. In-memory caching for sub-10ms response times.
3. Dashboard summary metrics, business insight callouts, and visualization data.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import joblib

from app.services import data_cleaning
from app.services.model_training import (
    MODELS_DIR,
    LINEAR_REGRESSION_FILE,
    get_models_dir,
)
from app.schemas.recommendation import (
    RecommendationItem,
    RecommendationSummary,
    RecommendationResponse,
    BusinessInsightItem,
    StoreRestockOverview,
    DashboardSummaryResponse,
)

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# In-memory recommendation cache: (horizon, lead_time, safety_buffer, mtime) -> List[RecommendationItem]
_RECOMMENDATION_CACHE: Dict[str, Any] = {}


def _get_dataset_df() -> Tuple[pd.DataFrame, float]:
    """Load the active cleaned dataset along with file modification timestamp."""
    path = data_cleaning.CLEANED_DATASET_PATH
    if not os.path.exists(path):
        path = data_cleaning.RAW_DATASET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError("No retail dataset found. Please upload a dataset first.")
    mtime = os.path.getmtime(path)
    df = pd.read_csv(path)
    if len(df) == 0:
        raise ValueError("Dataset is empty.")
    return df, mtime


def _compute_all_recommendations(
    horizon_days: int = 7,
    lead_time_days: int = 2,
    safety_buffer_days: int = 1,
) -> Tuple[List[RecommendationItem], List[str], List[str]]:
    """
    Computes inventory recommendations for every unique store-product pair.
    Uses cached calculations if the dataset and parameters have not changed.
    """
    df, mtime = _get_dataset_df()
    cache_key = f"{horizon_days}_{lead_time_days}_{safety_buffer_days}_{mtime}"
    if cache_key in _RECOMMENDATION_CACHE:
        cached = _RECOMMENDATION_CACHE[cache_key]
        return cached["items"], cached["stores"], cached["categories"]

    # 1. Identify key columns
    store_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["storeid", "store"]), None)
    product_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["productid", "itemid", "sku"]), None)
    date_col = next((c for c in df.columns if c.lower() in ["date", "saledate", "sale_date"]), None)
    sales_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["unitssold", "sales"]), None)
    inv_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["inventorylevel", "inventory", "stock"]), None)
    category_col = next((c for c in df.columns if c.lower() in ["category", "productcategory"]), None)

    if not store_col or not product_col or not date_col or not sales_col:
        raise ValueError("Dataset missing required columns (Store, Product, Date, Units Sold).")

    # Load Linear Regression pipeline
    models_dir = get_models_dir()
    artifact_path = os.path.join(models_dir, LINEAR_REGRESSION_FILE)
    if not os.path.exists(artifact_path):
        raise FileNotFoundError("Trained Linear Regression pipeline not found. Please train models first.")

    pipeline = joblib.load(artifact_path)

    # Parse dates
    df["_parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
    stores = sorted(list(df[store_col].dropna().astype(str).unique()))
    categories = sorted(list(df[category_col].dropna().astype(str).unique())) if category_col else []

    recommendation_items: List[RecommendationItem] = []

    # Group by store and product
    grouped = df.groupby([store_col, product_col])

    for (s_id, p_id), series in grouped:
        s_id_str = str(s_id)
        p_id_str = str(p_id)
        series_sorted = series.sort_values("_parsed_date").reset_index(drop=True)
        cat_val = str(series_sorted.iloc[-1][category_col]) if category_col and pd.notna(series_sorted.iloc[-1][category_col]) else "General"
        price_val = float(series_sorted.iloc[-1]["Price"]) if "Price" in series_sorted.columns and pd.notna(series_sorted.iloc[-1]["Price"]) else 25.0
        discount_val = float(series_sorted.iloc[-1]["Discount"]) if "Discount" in series_sorted.columns and pd.notna(series_sorted.iloc[-1]["Discount"]) else 0.0

        # Latest recorded stock level
        if inv_col and pd.notna(series_sorted.iloc[-1][inv_col]):
            curr_stock = float(series_sorted.iloc[-1][inv_col])
        else:
            curr_stock = 100.0  # Safe default if column omitted

        if len(series_sorted) < 7:
            # Insufficient data
            item = RecommendationItem(
                store_id=s_id_str,
                product_id=p_id_str,
                category=cat_val,
                current_stock=curr_stock,
                forecasted_demand=0.0,
                daily_demand=0.0,
                lead_time_days=lead_time_days,
                safety_buffer_days=safety_buffer_days,
                reorder_point=0.0,
                target_stock=0.0,
                suggested_reorder_qty=0.0,
                days_of_supply=999.0,
                status="Insufficient Data",
                notes=f"Insufficient history ({len(series_sorted)} records). Minimum 7 records required.",
            )
            recommendation_items.append(item)
            continue

        # Fast recursive multi-step forecasting for horizon_days
        last_date = series_sorted.iloc[-1]["_parsed_date"]
        sales_history = [float(x) for x in series_sorted[sales_col].values]
        future_forecasts = []

        for d_idx in range(1, horizon_days + 1):
            tgt_date = last_date + timedelta(days=d_idx)
            dow_idx = tgt_date.weekday()
            pred_row = pd.DataFrame([{
                "day": tgt_date.day,
                "day_of_week": dow_idx,
                "month": tgt_date.month,
                "is_weekend": 1 if dow_idx >= 5 else 0,
                "previous_day_sales": float(sales_history[-1]),
                "rolling_7_day_average": float(np.mean(sales_history[-7:])),
                "promotion": 0,
                "price": price_val,
                "discount": discount_val,
                "Store ID": s_id_str,
                "Product ID": p_id_str,
            }])
            raw_pred = float(pipeline.predict(pred_row)[0])
            clamped = max(0.0, round(raw_pred, 1))
            future_forecasts.append(clamped)
            sales_history.append(clamped)

        forecasted_total = round(float(sum(future_forecasts)), 1)
        daily_demand = round(forecasted_total / horizon_days, 2)

        # Inventory Recommendation Calculations
        lead_time_demand = daily_demand * lead_time_days
        safety_stock = daily_demand * safety_buffer_days
        reorder_point = round(lead_time_demand + safety_stock, 1)
        target_stock = round(forecasted_total + safety_stock, 1)

        # Suggested Reorder Quantity (strictly >= 0)
        if curr_stock <= reorder_point:
            suggested_reorder = max(0.0, round(target_stock - curr_stock, 1))
            status = "Restock Soon"
            notes = (
                f"Current stock of {curr_stock:.0f} units is below Reorder Point ({reorder_point:.0f}). "
                f"Order {suggested_reorder:.0f} units to maintain service."
            )
        elif curr_stock > target_stock * 1.5:
            suggested_reorder = 0.0
            status = "Excess Stock"
            surplus = curr_stock - target_stock
            notes = (
                f"Current stock ({curr_stock:.0f}) exceeds 1.5x Target Stock ({target_stock:.0f}). "
                f"Surplus of {surplus:.0f} units; pause replenishment."
            )
        else:
            suggested_reorder = 0.0
            status = "Stock Available"
            notes = f"Stock level ({curr_stock:.0f}) is healthy for expected {forecasted_total:.0f} units demand."

        # Stock Runway (Days of Supply)
        if daily_demand > 0:
            days_of_supply = round(curr_stock / daily_demand, 1)
        else:
            days_of_supply = 999.0

        item = RecommendationItem(
            store_id=s_id_str,
            product_id=p_id_str,
            category=cat_val,
            current_stock=curr_stock,
            forecasted_demand=forecasted_total,
            daily_demand=daily_demand,
            lead_time_days=lead_time_days,
            safety_buffer_days=safety_buffer_days,
            reorder_point=reorder_point,
            target_stock=target_stock,
            suggested_reorder_qty=suggested_reorder,
            days_of_supply=days_of_supply,
            status=status,
            notes=notes,
        )
        recommendation_items.append(item)

    # Cache calculated items
    _RECOMMENDATION_CACHE[cache_key] = {
        "items": recommendation_items,
        "stores": stores,
        "categories": categories,
    }

    return recommendation_items, stores, categories


def get_inventory_recommendations(
    store_id: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    lead_time_days: int = 2,
    safety_buffer_days: int = 1,
    horizon_days: int = 7,
) -> RecommendationResponse:
    """
    Retrieve filterable inventory recommendations with summary metrics.
    """
    all_items, stores, categories = _compute_all_recommendations(
        horizon_days=horizon_days,
        lead_time_days=lead_time_days,
        safety_buffer_days=safety_buffer_days,
    )

    # Filter items
    filtered = all_items
    if store_id and store_id.lower() != "all":
        filtered = [x for x in filtered if x.store_id == store_id]
    if category and category.lower() != "all":
        filtered = [x for x in filtered if x.category.lower() == category.lower()]
    if status and status.lower() != "all":
        filtered = [x for x in filtered if x.status.lower() == status.lower()]

    # Summary calculations
    restock_soon_count = sum(1 for x in filtered if x.status == "Restock Soon")
    stock_available_count = sum(1 for x in filtered if x.status == "Stock Available")
    excess_stock_count = sum(1 for x in filtered if x.status == "Excess Stock")
    insufficient_data_count = sum(1 for x in filtered if x.status == "Insufficient Data")
    total_reorder_units = round(sum(x.suggested_reorder_qty for x in filtered), 1)

    valid_runways = [x.days_of_supply for x in filtered if x.days_of_supply < 900]
    avg_runway = round(float(np.mean(valid_runways)), 1) if valid_runways else 0.0

    summary = RecommendationSummary(
        total_products_evaluated=len(filtered),
        restock_soon_count=restock_soon_count,
        stock_available_count=stock_available_count,
        excess_stock_count=excess_stock_count,
        insufficient_data_count=insufficient_data_count,
        total_reorder_units=total_reorder_units,
        average_days_of_supply=avg_runway,
    )

    return RecommendationResponse(
        summary=summary,
        items=filtered,
        stores=stores,
        categories=categories,
        horizon_days=horizon_days,
        calculated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def get_dashboard_summary() -> DashboardSummaryResponse:
    """
    Milestone 11: Business Insights Dashboard Aggregator.
    Produces high-level KPIs, business insights, rankings, and chart data.
    """
    all_items, stores, categories = _compute_all_recommendations(
        horizon_days=7,
        lead_time_days=2,
        safety_buffer_days=1,
    )

    distinct_products = set(x.product_id for x in all_items)
    distinct_stores = set(x.store_id for x in all_items)

    restock_items = [x for x in all_items if x.status == "Restock Soon"]
    excess_items = [x for x in all_items if x.status == "Excess Stock"]
    available_items = [x for x in all_items if x.status == "Stock Available"]
    stockout_risks = [x for x in all_items if x.days_of_supply < 3.0 and x.status == "Restock Soon"]

    total_reorder = round(sum(x.suggested_reorder_qty for x in all_items), 1)

    # 1. Top Demand Products (Summed across stores)
    product_demand: Dict[str, Dict[str, Any]] = {}
    for item in all_items:
        pid = item.product_id
        if pid not in product_demand:
            product_demand[pid] = {
                "product_id": pid,
                "category": item.category,
                "forecasted_demand": 0.0,
                "current_stock": 0.0,
            }
        product_demand[pid]["forecasted_demand"] += item.forecasted_demand
        product_demand[pid]["current_stock"] += item.current_stock

    top_demand_list = sorted(
        product_demand.values(),
        key=lambda x: x["forecasted_demand"],
        reverse=True
    )[:5]
    for row in top_demand_list:
        row["forecasted_demand"] = round(row["forecasted_demand"], 1)
        row["current_stock"] = round(row["current_stock"], 1)

    # 2. Stockout Risks List (Sorted by lowest runway)
    stockout_risks_sorted = sorted(
        [
            {
                "store_id": x.store_id,
                "product_id": x.product_id,
                "category": x.category,
                "current_stock": x.current_stock,
                "forecasted_demand": x.forecasted_demand,
                "days_of_supply": x.days_of_supply,
                "suggested_reorder_qty": x.suggested_reorder_qty,
            }
            for x in restock_items
        ],
        key=lambda k: k["days_of_supply"]
    )[:6]

    # 3. Excess Stock Items (Sorted by largest surplus over target)
    excess_stock_sorted = sorted(
        [
            {
                "store_id": x.store_id,
                "product_id": x.product_id,
                "category": x.category,
                "current_stock": x.current_stock,
                "target_stock": x.target_stock,
                "surplus_units": round(x.current_stock - x.target_stock, 1),
                "days_of_supply": x.days_of_supply,
            }
            for x in excess_items
        ],
        key=lambda k: k["surplus_units"],
        reverse=True
    )[:6]

    # 4. Store Replenishment Roll-up
    store_map: Dict[str, Dict[str, Any]] = {}
    for s in stores:
        store_map[s] = {
            "store_id": s,
            "total_items": 0,
            "restock_items_count": 0,
            "total_reorder_units": 0.0,
            "current_inventory_units": 0.0,
        }

    for item in all_items:
        s_data = store_map.get(item.store_id)
        if s_data:
            s_data["total_items"] += 1
            s_data["current_inventory_units"] += item.current_stock
            if item.status == "Restock Soon":
                s_data["restock_items_count"] += 1
                s_data["total_reorder_units"] += item.suggested_reorder_qty

    store_replenishment_list = [
        StoreRestockOverview(
            store_id=v["store_id"],
            total_items=v["total_items"],
            restock_items_count=v["restock_items_count"],
            total_reorder_units=round(v["total_reorder_units"], 1),
            current_inventory_units=round(v["current_inventory_units"], 1),
        )
        for v in sorted(store_map.values(), key=lambda x: x["total_reorder_units"], reverse=True)
    ]

    # 5. Category Distribution for Pie/Bar Chart
    total_items_count = len(all_items)
    category_distribution = [
        {
            "status": "Stock Available",
            "count": len(available_items),
            "percentage": round((len(available_items) / total_items_count) * 100, 1) if total_items_count else 0.0,
            "color": "#10b981",  # emerald-500
        },
        {
            "status": "Restock Soon",
            "count": len(restock_items),
            "percentage": round((len(restock_items) / total_items_count) * 100, 1) if total_items_count else 0.0,
            "color": "#ef4444",  # red-500
        },
        {
            "status": "Excess Stock",
            "count": len(excess_items),
            "percentage": round((len(excess_items) / total_items_count) * 100, 1) if total_items_count else 0.0,
            "color": "#f59e0b",  # amber-500
        },
    ]

    # 6. Dynamic Business Insight Callouts
    insights: List[BusinessInsightItem] = []

    # Insight 1: Urgent Stockout Alert
    if stockout_risks_sorted:
        top_risk = stockout_risks_sorted[0]
        insights.append(
            BusinessInsightItem(
                id="insight-stockout-1",
                type="URGENT_RESTOCK",
                title=f"Critical Stockout Alert: {top_risk['product_id']} at Store {top_risk['store_id']}",
                description=(
                    f"Available stock ({top_risk['current_stock']:.0f} units) covers only {top_risk['days_of_supply']:.1f} days "
                    f"of anticipated demand ({top_risk['forecasted_demand']:.0f} units)."
                ),
                recommended_action=f"Dispatch {top_risk['suggested_reorder_qty']:.0f} units immediately to prevent customer lost sales.",
                severity="CRITICAL",
                store_id=top_risk["store_id"],
                product_id=top_risk["product_id"],
            )
        )

    # Insight 2: Highest Demand Driver
    if top_demand_list:
        top_demand = top_demand_list[0]
        insights.append(
            BusinessInsightItem(
                id="insight-demand-1",
                type="HIGH_DEMAND",
                title=f"Primary Sales Driver: {top_demand['product_id']} ({top_demand['category']})",
                description=(
                    f"Forecasted demand reaches {top_demand['forecasted_demand']:.0f} units across retail locations over the next 7 days, "
                    f"representing the highest turnover product in the catalogue."
                ),
                recommended_action="Ensure continuous supplier allocation and prioritize central warehouse stock reserves.",
                severity="INFO",
                product_id=top_demand["product_id"],
            )
        )

    # Insight 3: Excess Stock Capital Inefficiency
    if excess_stock_sorted:
        top_excess = excess_stock_sorted[0]
        insights.append(
            BusinessInsightItem(
                id="insight-capital-1",
                type="EXCESS_CAPITAL",
                title=f"Capital Tied in Surplus: {top_excess['product_id']} at Store {top_excess['store_id']}",
                description=(
                    f"Current stock of {top_excess['current_stock']:.0f} units holds {top_excess['surplus_units']:.0f} units "
                    f"above target ({top_excess['target_stock']:.0f} units), providing {top_excess['days_of_supply']:.1f} days of supply."
                ),
                recommended_action="Pause future purchase orders or launch a promotional campaign to liquidate excess stock.",
                severity="WARNING",
                store_id=top_excess["store_id"],
                product_id=top_excess["product_id"],
            )
        )

    # Insight 4: Store Replenishment Priority
    if store_replenishment_list:
        top_store = store_replenishment_list[0]
        insights.append(
            BusinessInsightItem(
                id="insight-store-1",
                type="STORE_LOGISTICS",
                title=f"Regional Priority: Store {top_store.store_id} Requires {top_store.total_reorder_units:.0f} Replenishment Units",
                description=(
                    f"Store {top_store.store_id} accounts for {top_store.restock_items_count} items requiring restocking out of "
                    f"{top_store.total_items} total SKUs."
                ),
                recommended_action="Schedule priority delivery routes to this store to prevent regional out-of-stock events.",
                severity="INFO",
                store_id=top_store.store_id,
            )
        )

    return DashboardSummaryResponse(
        total_products=len(distinct_products),
        total_stores=len(distinct_stores),
        products_requiring_restock=len(restock_items),
        products_at_risk_of_stockout=len(stockout_risks),
        products_with_excess_inventory=len(excess_items),
        total_suggested_reorder_volume=total_reorder,
        insights=insights,
        top_demand_products=top_demand_list,
        stockout_risks=stockout_risks_sorted,
        excess_stock_items=excess_stock_sorted,
        store_replenishment=store_replenishment_list,
        category_distribution=category_distribution,
        calculated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
