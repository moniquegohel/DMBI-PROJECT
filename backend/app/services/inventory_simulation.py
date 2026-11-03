"""
services/inventory_simulation.py — Milestone 9: Inventory Simulation Service

Simulates physical inventory depletion, daily fulfillment, and stockout occurrences:
  - Consumes demand forecasts generated in Milestone 8.
  - Pre-fills with actual recorded ending stock from dataset (e.g. 223 units on 2024-01-01)
    while supporting user-provided custom starting stock.
  - Enforces physical non-negativity constraint (ending inventory >= 0).
  - Calculates daily demand fulfilled, unmet demand, ending stock, and stockout status.
  - Supports optional scheduled replenishment (quantity and arrival day).
  - Computes overall service level percentage and plain-language operational summaries.
"""

import os
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np

from app.services import data_cleaning
from app.services.demand_forecasting import (
    generate_demand_forecast,
    _get_dataset_df,
)
from app.schemas.forecast import ForecastRequest
from app.schemas.inventory import (
    InventorySimulationRequest,
    DailySimulationPoint,
    InventorySimulationResponse,
    StockInfoResponse,
)


def get_stock_info(store_id: str, product_id: str) -> StockInfoResponse:
    """
    Retrieve latest recorded stock level for the given store and product
    from the cleaned retail dataset.
    """
    df = _get_dataset_df()

    store_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["storeid", "store"]), None)
    product_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["productid", "itemid", "sku"]), None)
    date_col = next((c for c in df.columns if c.lower() in ["date", "saledate", "sale_date"]), None)
    inv_col = next((c for c in df.columns if "inventory" in c.lower()), None)
    sales_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["unitssold", "sales"]), None)
    cat_col = "Category" if "Category" in df.columns else None

    if not store_col or not product_col:
        raise ValueError("Store ID and Product ID columns must be mapped.")

    mask = (df[store_col].astype(str) == str(store_id)) & (df[product_col].astype(str) == str(product_id))
    series = df[mask].copy()

    if len(series) == 0:
        raise ValueError(f"No records found for Store '{store_id}' and Product '{product_id}'.")

    if date_col:
        series["_parsed_date"] = pd.to_datetime(series[date_col], errors="coerce")
        series = series.sort_values("_parsed_date")

    latest_row = series.iloc[-1]
    rec_date = str(latest_row["_parsed_date"].strftime("%Y-%m-%d")) if date_col else "2024-01-01"
    rec_stock = float(latest_row[inv_col]) if (inv_col and pd.notna(latest_row[inv_col])) else 100.0
    units_sold = float(latest_row[sales_col]) if (sales_col and pd.notna(latest_row[sales_col])) else 0.0
    cat_val = str(latest_row[cat_col]) if (cat_col and pd.notna(latest_row[cat_col])) else None

    return StockInfoResponse(
        store_id=str(store_id),
        product_id=str(product_id),
        category=cat_val,
        recorded_stock=round(rec_stock, 1),
        recorded_date=rec_date,
        units_sold_on_date=round(units_sold, 1),
    )


def run_inventory_simulation(req: InventorySimulationRequest) -> InventorySimulationResponse:
    """
    Execute step-by-step physical inventory simulation over the forecast horizon.
    """
    # 1. Fetch stock metadata from dataset
    stock_info = get_stock_info(req.store_id, req.product_id)
    recorded_stock = stock_info.recorded_stock

    # Determine starting inventory
    if req.starting_inventory is not None:
        starting_stock = max(0.0, float(req.starting_inventory))
        is_user_provided = True
    else:
        starting_stock = recorded_stock
        is_user_provided = False

    # 2. Generate future demand forecast via Milestone 8 service
    horizon = max(1, min(req.horizon_days, 90))
    fc_req = ForecastRequest(
        store_id=req.store_id,
        product_id=req.product_id,
        horizon_days=horizon,
        model_key=req.model_key or "linear_regression",
    )
    forecast = generate_demand_forecast(fc_req)

    # 3. Simulate day-by-day inventory dynamics
    current_stock = starting_stock
    simulation_points: List[DailySimulationPoint] = []

    first_stockout_day: Optional[int] = None
    first_stockout_date: Optional[str] = None

    replenish_qty = max(0.0, float(req.replenishment_quantity or 0.0))
    replenish_day = int(req.replenishment_day) if req.replenishment_day is not None else None

    for day_idx in range(1, horizon + 1):
        fc_point = forecast.forecast_series[day_idx - 1]
        day_date = fc_point.date
        expected_demand = fc_point.predicted_demand

        # Replenishment arrival
        replenishment_received = replenish_qty if (replenish_day == day_idx) else 0.0
        beginning_stock = current_stock
        available_stock = beginning_stock + replenishment_received

        # Fulfillment and balance equations
        demand_fulfilled = min(available_stock, expected_demand)
        unmet_demand = expected_demand - demand_fulfilled
        ending_stock = max(0.0, available_stock - demand_fulfilled)

        is_stockout = (unmet_demand > 0.0) or (ending_stock == 0.0)

        if is_stockout and first_stockout_day is None:
            first_stockout_day = day_idx
            first_stockout_date = day_date

        simulation_points.append(
            DailySimulationPoint(
                day=day_idx,
                date=day_date,
                beginning_inventory=round(beginning_stock, 1),
                replenishment_received=round(replenishment_received, 1),
                available_stock=round(available_stock, 1),
                forecasted_demand=round(expected_demand, 1),
                demand_fulfilled=round(demand_fulfilled, 1),
                unmet_demand=round(unmet_demand, 1),
                ending_inventory=round(ending_stock, 1),
                is_stockout=is_stockout,
            )
        )

        current_stock = ending_stock

    # 4. Summary metrics
    total_forecasted = sum(p.forecasted_demand for p in simulation_points)
    total_fulfilled = sum(p.demand_fulfilled for p in simulation_points)
    total_unmet = sum(p.unmet_demand for p in simulation_points)
    stockout_count = sum(1 for p in simulation_points if p.is_stockout)
    ending_inventory = simulation_points[-1].ending_inventory

    service_level = round((total_fulfilled / total_forecasted) * 100.0, 1) if total_forecasted > 0 else 100.0

    # 5. Plain-language business interpretation
    stock_source_label = "user-provided stock" if is_user_provided else f"recorded stock from dataset ({recorded_stock} units)"
    if total_unmet == 0.0:
        summary_text = (
            f"Sufficient Inventory: Starting with {starting_stock:.0f} units ({stock_source_label}), "
            f"100% of the {total_forecasted:.0f} units demanded across the {horizon}-day horizon "
            f"can be satisfied without any stockouts. Projected ending stock is {ending_inventory:.0f} units."
        )
    else:
        summary_text = (
            f"Stockout Risk Detected: Starting with {starting_stock:.0f} units ({stock_source_label}), "
            f"available inventory will be exhausted on Day {first_stockout_day} ({first_stockout_date}). "
            f"Out of {total_forecasted:.0f} units expected demand, {total_fulfilled:.0f} units will be fulfilled "
            f"({service_level}% service level), leaving {total_unmet:.0f} units of unmet customer demand."
        )

    return InventorySimulationResponse(
        success=True,
        store_id=str(req.store_id),
        product_id=str(req.product_id),
        category=stock_info.category,
        starting_inventory=round(starting_stock, 1),
        is_user_provided_starting_stock=is_user_provided,
        recorded_ending_stock_from_data=round(recorded_stock, 1),
        horizon_days=horizon,
        forecast_start_date=forecast.forecast_start_date,
        forecast_end_date=forecast.forecast_end_date,
        total_forecasted_demand=round(total_forecasted, 1),
        total_demand_fulfilled=round(total_fulfilled, 1),
        total_unmet_demand=round(total_unmet, 1),
        stockout_periods_count=stockout_count,
        first_stockout_day=first_stockout_day,
        first_stockout_date=first_stockout_date,
        ending_inventory=round(ending_inventory, 1),
        service_level_percentage=service_level,
        simulation_points=simulation_points,
        simulation_summary_text=summary_text,
    )

