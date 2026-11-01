"""
services/feature_engineering.py — Milestone 5: Feature Engineering Service

Generates an ML-ready dataset from the cleaned retail sales CSV by adding:

  Date features (computed from the mapped date column):
    - day          : day of the month (1–31)
    - day_of_week  : Monday=0 … Sunday=6 (ISO weekday, consistent encoding)
    - month        : month of the year (1–12)
    - is_weekend   : 1 if Saturday or Sunday, 0 otherwise

  Sales-history features (computed per store-product group, chronologically):
    - previous_day_sales    : Units Sold of the immediately preceding row in the
                              same store-product group.  This is a one-row lag.
    - rolling_7_day_average : Average of the 7 rows *before* the current row in
                              the same store-product group.  Implemented as a
                              one-row shift followed by a 7-observation rolling mean,
                              so the current row's sales never contribute to its
                              own rolling feature (no target leakage).

  Optional features (included when the mapped column is present):
    - promotion  (from Holiday/Promotion column)
    - price      (from Price column)
    - discount   (from Discount column)

  Explicitly EXCLUDED columns (data-leakage / domain reasons):
    - Demand Forecast : highly correlated with the target; 673 negative values;
                        would constitute target leakage.
    - Inventory Level : reflects same-day stock *after* sales are recorded;
                        not available at prediction time.
    - Units Ordered   : a replenishment order placed in response to today's
                        sales; future-looking by nature.

Grouping rule:
  Lag and rolling calculations are performed within each unique
  (Store ID, Product ID) pair — never across unrelated series.
  If either identifier is missing from the mappings, the calculation
  falls back to grouping by Product ID only, with a documented warning.

Initial rows:
  The first row of each store-product group has no previous sales,
  so 'previous_day_sales' is NaN.
  The first 1–7 rows of each group may have fewer than 7 prior observations,
  so 'rolling_7_day_average' may also be NaN for those rows.
  These rows are PRESERVED in the output with NaN values (not dropped),
  so the output always has the same number of rows as the input.

Output:
  Saved to backend/data/ml_dataset.csv.
  Re-running this function overwrites the file (idempotent).
"""

import os
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from app.services import data_cleaning
from app.schemas.features import (
    FeatureEngineeringResult,
    FeatureColumnInfo,
    FeatureEngineeringStatus,
)


DATA_DIR = data_cleaning.DATA_DIR


def get_ml_dataset_path() -> str:
    """Return the active path for the ML dataset dynamically based on data_cleaning.DATA_DIR."""
    return os.path.join(data_cleaning.DATA_DIR, "ml_dataset.csv")


# Module-level alias for backward compatibility
ML_DATASET_PATH = get_ml_dataset_path()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_mappings(df: pd.DataFrame) -> Dict[str, str]:
    """
    Resolve column role mappings from saved JSON, falling back to alias matching.
    Returns a dict of {role_key: actual_column_name}.
    """
    saved = data_cleaning.load_column_mappings_from_file()
    norm_cols = {
        str(col).strip().lower().replace("_", "").replace(" ", ""): col
        for col in df.columns
    }
    active: Dict[str, str] = {}

    for role_def in data_cleaning.STANDARD_ROLES:
        role_key = role_def["role"]
        # Priority A: user-saved mapping that still exists in the dataframe
        if role_key in saved and saved[role_key] in df.columns:
            active[role_key] = saved[role_key]
            continue
        # Priority B: exact role_label match
        if role_def["role_label"] in df.columns:
            active[role_key] = role_def["role_label"]
            continue
        # Priority C: alias matching
        for alias in role_def["aliases"]:
            clean = alias.lower().replace("_", "").replace(" ", "")
            if clean in norm_cols:
                active[role_key] = norm_cols[clean]
                break

    return active


def _sanitize_for_json(val: Any) -> Any:
    """Convert numpy/pandas types to plain Python types for JSON serialisation."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        v = float(val)
        return None if np.isnan(v) else round(v, 4)
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val).split("T")[0]
    return val


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_feature_engineering_status() -> FeatureEngineeringStatus:
    """
    Check whether the ML dataset file already exists and return its dimensions.
    This is a cheap check — no full re-computation.
    """
    ml_path = get_ml_dataset_path()
    if os.path.exists(ml_path):
        try:
            # Read only header and count rows efficiently
            ml_df = pd.read_csv(ml_path, nrows=0)
            col_count = len(ml_df.columns)
            # Count rows without reading entire file into memory
            row_count = sum(1 for _ in open(ml_path, encoding="utf-8")) - 1
            return FeatureEngineeringStatus(
                has_ml_dataset=True,
                ml_dataset_rows=max(row_count, 0),
                ml_dataset_columns=col_count,
                message=(
                    f"ML dataset ready: {max(row_count, 0):,} rows, "
                    f"{col_count} columns."
                ),
            )
        except Exception:
            pass
    return FeatureEngineeringStatus(
        has_ml_dataset=False,
        message="ML dataset has not been generated yet. Click 'Generate Features'.",
    )


def run_feature_engineering() -> FeatureEngineeringResult:
    """
    Main feature engineering entry point.

    Steps:
      1. Load cleaned dataset (falls back to raw if clean is absent).
      2. Resolve column mappings.
      3. Validate required columns (date and units_sold are mandatory).
      4. Parse and sort dates.
      5. Add date features: day, day_of_week, month, is_weekend.
      6. Per (store, product) group: add previous_day_sales and
         rolling_7_day_average using a shift-then-roll pattern that
         excludes the current row from its own rolling window.
      7. Add optional features (promotion, price, discount) when present.
      8. Build column catalogue with role labels and NaN counts.
      9. Save to ml_dataset.csv (overwrites any previous file).
     10. Return FeatureEngineeringResult.

    Raises:
      FileNotFoundError  — if no dataset has been uploaded at all.
      ValueError         — if required column mappings are missing or invalid.
    """

    # ------------------------------------------------------------------
    # 1. Load source dataset (dynamically checking data_cleaning paths)
    # ------------------------------------------------------------------
    cleaned_path = getattr(data_cleaning, "CLEANED_DATASET_PATH", os.path.join(data_cleaning.DATA_DIR, "cleaned_dataset.csv"))
    raw_path = getattr(data_cleaning, "RAW_DATASET_PATH", os.path.join(data_cleaning.DATA_DIR, "raw_dataset.csv"))

    if os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
        source_name = os.path.basename(cleaned_path)
    elif os.path.exists(raw_path):
        df = pd.read_csv(raw_path)
        source_name = os.path.basename(raw_path)
    else:
        raise FileNotFoundError(
            "No retail dataset uploaded yet. "
            "Please upload a retail CSV on the Dataset page first."
        )

    input_rows = int(len(df))
    if input_rows == 0:
        raise ValueError("The source dataset is empty — cannot generate features.")

    # ------------------------------------------------------------------
    # 2. Resolve column mappings
    # ------------------------------------------------------------------
    mappings = _resolve_mappings(df)

    # ------------------------------------------------------------------
    # 3. Validate required columns
    # ------------------------------------------------------------------
    date_col = mappings.get("date")
    if not date_col or date_col not in df.columns:
        raise ValueError(
            "Required 'Date' column mapping is missing. "
            "Please set the Date role on the Dataset page before generating features."
        )

    units_sold_col = mappings.get("units_sold")
    if not units_sold_col or units_sold_col not in df.columns:
        raise ValueError(
            "Required 'Units Sold' column mapping is missing. "
            "Please set the Units Sold role on the Dataset page before generating features."
        )

    # ------------------------------------------------------------------
    # 4. Parse dates and sort chronologically within groups
    # ------------------------------------------------------------------
    # Work on a clean copy so the original DataFrame is not mutated
    df = df.copy()

    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    invalid_date_count = int(parsed_dates.isna().sum())
    if invalid_date_count == input_rows:
        raise ValueError(
            f"All values in the date column '{date_col}' are unparseable. "
            "Please check the column mapping."
        )

    df["_parsed_date"] = parsed_dates

    # Resolve grouping columns (store and product)
    store_col = mappings.get("store_id")
    prod_col = mappings.get("product_id")

    # Determine the sort order and grouping keys
    sort_cols = []
    group_cols = []

    if store_col and store_col in df.columns:
        sort_cols.append(store_col)
        group_cols.append(store_col)
    if prod_col and prod_col in df.columns:
        sort_cols.append(prod_col)
        group_cols.append(prod_col)
    sort_cols.append("_parsed_date")

    df = df.sort_values(by=sort_cols).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 5. Date features (derived from the parsed date — no sales values used)
    # ------------------------------------------------------------------
    df["day"] = df["_parsed_date"].dt.day
    df["day_of_week"] = df["_parsed_date"].dt.dayofweek  # Monday=0 … Sunday=6
    df["month"] = df["_parsed_date"].dt.month
    df["is_weekend"] = (df["_parsed_date"].dt.dayofweek >= 5).astype(int)

    # ------------------------------------------------------------------
    # 6. Sales-history features — computed per store-product group
    #
    # Critical leakage-prevention pattern:
    #   a. Convert units_sold to numeric.
    #   b. SHIFT the series by 1 row within the group so that position [i]
    #      holds the sales value from position [i-1].  The first row of
    #      every group becomes NaN (no prior observation).
    #   c. Apply a 7-observation rolling mean on the SHIFTED series.
    #      Because the series is already shifted, position [i] sees the
    #      7 observations from [i-7] to [i-1] — never [i] itself.
    # ------------------------------------------------------------------
    df["_numeric_sales"] = pd.to_numeric(df[units_sold_col], errors="coerce")

    if group_cols:
        # Group by store + product (or just product if store is absent)
        grouped = df.groupby(group_cols, sort=False)

        # previous_day_sales: one-row lag within each group
        df["previous_day_sales"] = grouped["_numeric_sales"].transform(
            lambda s: s.shift(1)
        )

        # rolling_7_day_average: 7-obs rolling mean on the already-shifted series
        # min_periods=1 allows partial windows at the start of a series;
        # windows with fewer than 1 valid value remain NaN automatically.
        df["rolling_7_day_average"] = grouped["_numeric_sales"].transform(
            lambda s: s.shift(1).rolling(window=7, min_periods=1).mean()
        )
    else:
        # Fallback: no grouping columns available — use global order only
        df["previous_day_sales"] = df["_numeric_sales"].shift(1)
        df["rolling_7_day_average"] = (
            df["_numeric_sales"].shift(1).rolling(window=7, min_periods=1).mean()
        )

    # ------------------------------------------------------------------
    # 7. Optional features (available at prediction time, not target-leaky)
    # ------------------------------------------------------------------
    optional_predictors: List[str] = []

    # Holiday / Promotion indicator
    promo_col = mappings.get("promotion")
    if promo_col and promo_col in df.columns:
        df["promotion"] = df[promo_col]
        optional_predictors.append("promotion")

    # Price (available at prediction time for a known product-store pair)
    price_col = mappings.get("price")
    if price_col and price_col in df.columns:
        df["price"] = pd.to_numeric(df[price_col], errors="coerce")
        optional_predictors.append("price")

    # Discount (available at prediction time when promotions are planned)
    discount_col = mappings.get("discount")
    if discount_col and discount_col in df.columns:
        df["discount"] = pd.to_numeric(df[discount_col], errors="coerce")
        optional_predictors.append("discount")

    # ------------------------------------------------------------------
    # 8. Build final column set
    # ------------------------------------------------------------------

    # Core date predictors (always present)
    date_predictors = ["day", "day_of_week", "month", "is_weekend"]

    # Core lag predictors (always present, may have NaN for first rows)
    lag_predictors = ["previous_day_sales", "rolling_7_day_average"]

    # All predictors
    all_predictors = date_predictors + lag_predictors + optional_predictors

    # Metadata columns (kept for identification and chronological split)
    metadata_cols: List[str] = [date_col]
    if store_col and store_col in df.columns:
        metadata_cols.append(store_col)
    if prod_col and prod_col in df.columns:
        metadata_cols.append(prod_col)

    # Target column
    target_col = units_sold_col

    # Columns to write into the ML dataset (metadata + predictors + target)
    output_cols = metadata_cols + all_predictors + [target_col]

    # Remove internal working columns
    ml_df = df[output_cols].copy()

    # ------------------------------------------------------------------
    # 9. Save ML dataset (idempotent — overwrites previous file)
    # ------------------------------------------------------------------
    ml_path = get_ml_dataset_path()
    ml_df.to_csv(ml_path, index=False)

    # ------------------------------------------------------------------
    # 10. Compute result statistics and catalogue
    # ------------------------------------------------------------------
    prev_nulls = int(ml_df["previous_day_sales"].isna().sum())
    roll_nulls = int(ml_df["rolling_7_day_average"].isna().sum())

    # Columns explicitly excluded and their reasons
    excluded: Dict[str, str] = {}

    for col in df.columns:
        col_lower = col.lower()
        if "demand forecast" in col_lower or (
            "forecast" in col_lower and "demand" in col_lower
        ):
            excluded[col] = (
                "Excluded: Demand Forecast is highly correlated with the target "
                "(Units Sold) and contains 673 negative values. "
                "Using it as a predictor would constitute target leakage."
            )
        elif "inventory level" in col_lower or "inventorylevel" in col_lower:
            excluded[col] = (
                "Excluded: Inventory Level reflects end-of-day stock after sales "
                "have been recorded. It is not available at demand-prediction time."
            )
        elif "units ordered" in col_lower or "unitsordered" in col_lower:
            excluded[col] = (
                "Excluded: Units Ordered is a replenishment response to today's "
                "sales — it is future-facing and would cause target leakage."
            )

    # Build feature catalogue
    feature_columns: List[FeatureColumnInfo] = []

    for col in metadata_cols:
        null_count = int(ml_df[col].isna().sum())
        desc_map = {
            date_col: "Transaction date — used for chronological ordering and splits.",
        }
        if store_col and col == store_col:
            desc_map[col] = "Store identifier — used to group time-series by store."
        if prod_col and col == prod_col:
            desc_map[col] = "Product identifier — used to group time-series by product."
        feature_columns.append(
            FeatureColumnInfo(
                name=col,
                role="metadata",
                description=desc_map.get(col, "Identifier column retained for interpretation."),
                null_count=null_count,
            )
        )

    predictor_descriptions = {
        "day": "Day of the month (1–31), extracted from the transaction date.",
        "day_of_week": (
            "Day of the week as an integer: Monday=0, Tuesday=1, Wednesday=2, "
            "Thursday=3, Friday=4, Saturday=5, Sunday=6."
        ),
        "month": "Calendar month (1–12), extracted from the transaction date.",
        "is_weekend": (
            "Weekend indicator: 1 if the date is Saturday or Sunday, 0 otherwise."
        ),
        "previous_day_sales": (
            "Units Sold in the immediately preceding row of the same store-product "
            "group (one-row lag). NaN for the first record of each group."
        ),
        "rolling_7_day_average": (
            "Average Units Sold over the 7 rows immediately before the current row "
            "in the same store-product group. Never includes the current row's sales "
            "(shift-then-roll pattern prevents target leakage). "
            "May be NaN for the first few rows of each group."
        ),
        "promotion": "Holiday or promotion indicator from the mapped promotion column.",
        "price": "Unit selling price at the time of the transaction.",
        "discount": "Discount or markdown rate applied to the transaction.",
    }

    for col in all_predictors:
        if col not in ml_df.columns:
            continue
        null_count = int(ml_df[col].isna().sum())
        feature_columns.append(
            FeatureColumnInfo(
                name=col,
                role="predictor",
                description=predictor_descriptions.get(col, f"Derived feature: {col}"),
                null_count=null_count,
            )
        )

    feature_columns.append(
        FeatureColumnInfo(
            name=target_col,
            role="target",
            description=(
                "Units Sold — the demand value to be predicted by ML models. "
                "Kept in the dataset for the train/test split in Milestone 6."
            ),
            null_count=int(ml_df[target_col].isna().sum()),
        )
    )

    # 10-row preview (NaN → None for JSON safety)
    preview_records = []
    for _, row in ml_df.head(10).iterrows():
        preview_records.append(
            {str(k): _sanitize_for_json(v) for k, v in row.items()}
        )

    group_warning = ""
    if not group_cols:
        group_warning = (
            " WARNING: No store or product identifier columns were found. "
            "Lag and rolling features were computed on the global series, "
            "which may mix sales from different products. "
            "Please check column mappings on the Dataset page."
        )

    return FeatureEngineeringResult(
        success=True,
        message=(
            f"Feature engineering completed successfully using '{source_name}'. "
            f"{input_rows:,} rows processed. "
            f"ML dataset saved to ml_dataset.csv.{group_warning}"
        ),
        input_rows=input_rows,
        output_rows=int(len(ml_df)),
        output_columns=int(len(ml_df.columns)),
        feature_columns=feature_columns,
        predictor_names=all_predictors,
        metadata_names=metadata_cols,
        target_name=target_col,
        previous_day_sales_nulls=prev_nulls,
        rolling_7_day_avg_nulls=roll_nulls,
        excluded_columns=excluded,
        preview_rows=preview_records,
        day_of_week_encoding="Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6",
        is_weekend_encoding="0=weekday (Mon–Fri), 1=weekend (Sat or Sun)",
    )
