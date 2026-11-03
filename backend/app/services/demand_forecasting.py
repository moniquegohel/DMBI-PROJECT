"""
services/demand_forecasting.py — Milestone 8: Retail Demand Forecasting Service

Provides recursive multi-step daily retail demand forecasting:
  - Supports store and product level granularity (e.g. S001 / P0001).
  - Preserves daily frequency starting the day after historical data ends (2024-01-02).
  - Uses the Milestone 7 empirical winner (Linear Regression) by default, with option
    for Random Forest.
  - Recursively updates lag (previous_day_sales) and rolling features (rolling_7_day_average)
    across future days without future data leakage.
  - Clamps predictions to non-negative values.
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
    RANDOM_FOREST_FILE,
    get_models_dir,
)
from app.schemas.forecast import (
    ForecastRequest,
    ForecastPoint,
    HistoricalPoint,
    ForecastResponse,
    CatalogueItem,
    ForecastOptionsResponse,
)

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _get_dataset_df() -> pd.DataFrame:
    """Load the active cleaned dataset."""
    path = data_cleaning.CLEANED_DATASET_PATH
    if not os.path.exists(path):
        # Fallback to raw if cleaned not found
        path = data_cleaning.RAW_DATASET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError("No retail dataset found. Please upload a dataset first.")
    df = pd.read_csv(path)
    if len(df) == 0:
        raise ValueError("Dataset is empty.")
    return df


def get_forecast_options() -> ForecastOptionsResponse:
    """
    Retrieve catalogue metadata (available stores, products, categories,
    and latest inventory levels) for the frontend forecasting selector.
    """
    df = _get_dataset_df()

    store_col = None
    product_col = None
    for c in df.columns:
        norm = c.lower().replace(" ", "").replace("_", "")
        if norm in ["storeid", "store"]:
            store_col = c
        elif norm in ["productid", "itemid", "sku"]:
            product_col = c

    if not store_col or not product_col:
        raise ValueError("Store ID and Product ID columns must be mapped in dataset.")

    category_col = "Category" if "Category" in df.columns else None
    inventory_col = "Inventory Level" if "Inventory Level" in df.columns else None
    date_col = "Date" if "Date" in df.columns else None
    sales_col = "Units Sold" if "Units Sold" in df.columns else None

    # Parse dates for sorting
    if date_col:
        df["_parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["_parsed_date"] = pd.to_datetime("2024-01-01")

    unique_stores = sorted(df[store_col].dropna().astype(str).unique().tolist())
    unique_products = sorted(df[product_col].dropna().astype(str).unique().tolist())

    catalogue: List[CatalogueItem] = []
    grouped = df.groupby([store_col, product_col])

    for (s_id, p_id), grp in grouped:
        grp_sorted = grp.sort_values("_parsed_date")
        latest_row = grp_sorted.iloc[-1]
        latest_date_str = str(latest_row["_parsed_date"].strftime("%Y-%m-%d"))
        latest_stock = float(latest_row[inventory_col]) if (inventory_col and pd.notna(latest_row[inventory_col])) else 0.0
        
        # Calculate recent average daily sales (last 14 records)
        recent_sales = grp_sorted[sales_col].tail(14) if sales_col else pd.Series([0])
        recent_avg = float(recent_sales.mean()) if len(recent_sales) > 0 else 0.0

        cat_val = str(latest_row[category_col]) if (category_col and pd.notna(latest_row[category_col])) else None

        catalogue.append(
            CatalogueItem(
                store_id=str(s_id),
                product_id=str(p_id),
                category=cat_val,
                latest_date=latest_date_str,
                latest_inventory=round(latest_stock, 1),
                recent_avg_daily_sales=round(recent_avg, 1),
            )
        )

    return ForecastOptionsResponse(
        stores=unique_stores,
        products=unique_products,
        catalogue=catalogue,
        recommended_model_key="linear_regression",
        recommended_model_name="Linear Regression",
        default_horizon_days=7,
        allowed_horizons=[7, 14, 30],
    )


def generate_demand_forecast(req: ForecastRequest) -> ForecastResponse:
    """
    Generate multi-step future demand forecast for the specified store and product.
    Uses recursive feature updates to predict each future day up to the requested horizon.
    """
    df = _get_dataset_df()
    models_dir = get_models_dir()

    # 1. Identify key columns
    store_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["storeid", "store"]), None)
    product_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["productid", "itemid", "sku"]), None)
    date_col = next((c for c in df.columns if c.lower() in ["date", "saledate", "sale_date"]), None)
    sales_col = next((c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ["unitssold", "sales"]), None)

    if not store_col or not product_col or not date_col or not sales_col:
        raise ValueError("Dataset is missing essential columns (Date, Store ID, Product ID, Units Sold).")

    # 2. Filter for store & product
    mask = (df[store_col].astype(str) == str(req.store_id)) & (df[product_col].astype(str) == str(req.product_id))
    series = df[mask].copy()

    if len(series) == 0:
        raise ValueError(f"No transactions found for Store '{req.store_id}' and Product '{req.product_id}'.")

    if len(series) < 7:
        raise ValueError(
            f"Insufficient historical data: found only {len(series)} records. "
            "At least 7 consecutive historical records are required to generate lag features."
        )

    # Sort series chronologically
    series["_parsed_date"] = pd.to_datetime(series[date_col], errors="coerce")
    series = series.sort_values("_parsed_date").reset_index(drop=True)

    # 3. Model selection & loading
    chosen_key = req.model_key or "linear_regression"
    if chosen_key.lower() in ["random_forest", "rf", "randomforest"]:
        chosen_key = "random_forest"
        model_name = "Random Forest Regressor"
        artifact_file = RANDOM_FOREST_FILE
    else:
        chosen_key = "linear_regression"
        model_name = "Linear Regression (Recommended Winner)"
        artifact_file = LINEAR_REGRESSION_FILE

    artifact_path = os.path.join(models_dir, artifact_file)
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(
            f"Model artifact '{artifact_file}' not found. "
            "Please train prediction models on the Sales Prediction page before forecasting."
        )

    pipeline = joblib.load(artifact_path)

    # 4. Contextual static feature values
    last_row = series.iloc[-1]
    last_date = last_row["_parsed_date"]
    category_val = str(last_row["Category"]) if "Category" in series.columns and pd.notna(last_row["Category"]) else None
    price_val = float(last_row["Price"]) if "Price" in series.columns and pd.notna(last_row["Price"]) else 25.0
    discount_val = float(last_row["Discount"]) if "Discount" in series.columns and pd.notna(last_row["Discount"]) else 0.0

    # 5. Extract recent historical context (up to 14 days)
    recent_history_rows = series.tail(14)
    historical_points: List[HistoricalPoint] = [
        HistoricalPoint(
            date=row["_parsed_date"].strftime("%Y-%m-%d"),
            actual_sales=float(row[sales_col]),
        )
        for _, row in recent_history_rows.iterrows()
    ]

    # 6. Initialize recursive sales history buffer
    sales_history: List[float] = [float(x) for x in series[sales_col].values]

    # Validate horizon
    horizon = max(1, min(req.horizon_days, 90))

    forecast_points: List[ForecastPoint] = []

    # 7. Recursive Forecasting Loop
    for day_idx in range(1, horizon + 1):
        target_date = last_date + timedelta(days=day_idx)
        target_date_str = target_date.strftime("%Y-%m-%d")
        day_of_month = target_date.day
        dow_idx = target_date.weekday()
        day_name = DAYS_OF_WEEK[dow_idx]
        month_val = target_date.month
        is_weekend = dow_idx >= 5

        # Dynamic lag and rolling features computed strictly from prior history
        prev_day_sales = float(sales_history[-1])
        rolling_7_avg = float(np.mean(sales_history[-7:]))

        # Build single-row predictor dataframe matching pipeline expected features
        pred_input = pd.DataFrame([{
            "day": day_of_month,
            "day_of_week": dow_idx,
            "month": month_val,
            "is_weekend": 1 if is_weekend else 0,
            "previous_day_sales": prev_day_sales,
            "rolling_7_day_average": rolling_7_avg,
            "promotion": 0,
            "price": price_val,
            "discount": discount_val,
            "Store ID": str(req.store_id),
            "Product ID": str(req.product_id),
        }])

        raw_pred = float(pipeline.predict(pred_input)[0])
        # Retail demand cannot be negative; clamp to 0
        clamped_pred = max(0.0, round(raw_pred, 1))

        # Append prediction to sales buffer for subsequent recursive steps
        sales_history.append(clamped_pred)

        forecast_points.append(
            ForecastPoint(
                date=target_date_str,
                day_of_week=day_name,
                day_index=day_idx,
                predicted_demand=clamped_pred,
                is_weekend=is_weekend,
            )
        )

    # 8. Summary statistics
    total_demand = sum(p.predicted_demand for p in forecast_points)
    avg_demand = round(total_demand / horizon, 1)

    peak_point = max(forecast_points, key=lambda p: p.predicted_demand)
    start_date_str = forecast_points[0].date
    end_date_str = forecast_points[-1].date

    msg = (
        f"Generated {horizon}-day demand forecast for Store {req.store_id}, "
        f"Product {req.product_id} using {model_name}."
    )

    return ForecastResponse(
        success=True,
        store_id=str(req.store_id),
        product_id=str(req.product_id),
        category=category_val,
        model_name=model_name,
        model_key=chosen_key,
        horizon_days=horizon,
        forecast_start_date=start_date_str,
        forecast_end_date=end_date_str,
        total_forecasted_demand=round(total_demand, 1),
        avg_daily_demand=avg_demand,
        peak_demand_date=peak_point.date,
        peak_demand=peak_point.predicted_demand,
        historical_series=historical_points,
        forecast_series=forecast_points,
        message=msg,
    )

