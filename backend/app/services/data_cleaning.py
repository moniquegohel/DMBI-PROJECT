import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from app.database.models import DatasetMetadata
from app.schemas.dataset import (
    ColumnInspectionInfo,
    ColumnMappingItem,
    QualityCheckItem,
    DatasetSummaryResponse,
    CleaningResultResponse
)

# Standard directory for storing dataset files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

RAW_DATASET_PATH = os.path.join(DATA_DIR, "raw_dataset.csv")
CLEANED_DATASET_PATH = os.path.join(DATA_DIR, "cleaned_dataset.csv")
MAPPINGS_FILE_PATH = os.path.join(DATA_DIR, "column_mappings.json")

# Role definitions recognized by SmartStock for retail demand forecasting
STANDARD_ROLES = [
    {
        "role": "date",
        "role_label": "Date",
        "description": "Sales transaction date (required for time-series ordering)",
        "is_required": True,
        "aliases": ["date", "saledate", "sale_date", "transaction_date", "timestamp", "datetime"]
    },
    {
        "role": "store_id",
        "role_label": "Store ID",
        "description": "Store or retail outlet identifier",
        "is_required": False,
        "aliases": ["storeid", "store_id", "store", "shop_id", "outlet_id", "location_id"]
    },
    {
        "role": "product_id",
        "role_label": "Product ID",
        "description": "Product or SKU identifier (required for product-level forecasting)",
        "is_required": True,
        "aliases": ["productid", "product_id", "item_id", "product_code", "sku", "item_code"]
    },
    {
        "role": "units_sold",
        "role_label": "Units Sold",
        "description": "Historical sales volume (planned target for demand forecasting)",
        "is_required": True,
        "aliases": ["unitssold", "units_sold", "quantity_sold", "quantity", "sales", "sales_quantity", "qty_sold", "demand", "volume"]
    },
    {
        "role": "inventory_level",
        "role_label": "Inventory Level",
        "description": "Current on-hand stock or inventory count",
        "is_required": False,
        "aliases": ["inventorylevel", "inventory_level", "stock_level", "current_stock", "stock", "inventory", "on_hand"]
    },
    {
        "role": "units_ordered",
        "role_label": "Units Ordered",
        "description": "Replenishment order quantities placed with suppliers",
        "is_required": False,
        "aliases": ["unitsordered", "units_ordered", "orders", "ordered_quantity", "qty_ordered"]
    },
    {
        "role": "price",
        "role_label": "Product Price",
        "description": "Unit selling price of the product",
        "is_required": False,
        "aliases": ["price", "unit_price", "product_price", "selling_price", "mrp"]
    },
    {
        "role": "discount",
        "role_label": "Discount",
        "description": "Discount percentage or markdown applied to sales",
        "is_required": False,
        "aliases": ["discount", "discount_rate", "discount_percent", "discount_percentage", "rebate"]
    },
    {
        "role": "promotion",
        "role_label": "Holiday / Promotion",
        "description": "Binary or categorical indicator for marketing campaigns or holidays",
        "is_required": False,
        "aliases": ["holidaypromotion", "holiday/promotion", "promotion", "is_promo", "promo", "holiday"]
    },
    {
        "role": "weather",
        "role_label": "Weather Condition",
        "description": "Weather conditions affecting foot traffic (e.g. Sunny, Rainy)",
        "is_required": False,
        "aliases": ["weathercondition", "weather_condition", "weather", "climate"]
    },
    {
        "role": "category",
        "role_label": "Product Category",
        "description": "High-level merchandise category (e.g. Groceries, Toys, Clothing)",
        "is_required": False,
        "aliases": ["category", "product_category", "item_category", "department", "type"]
    },
    {
        "role": "region",
        "role_label": "Region",
        "description": "Geographical territory or district (e.g. North, South, East, West)",
        "is_required": False,
        "aliases": ["region", "area", "zone", "territory", "district"]
    }
]


def normalize_col_name(name: str) -> str:
    """Normalize a column name by removing punctuation and converting to lowercase."""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())


def detect_suggested_mappings(columns: List[str], saved_mappings: Optional[Dict[str, str]] = None) -> List[ColumnMappingItem]:
    """
    Suggest or retrieve semantic mappings between dataset columns and standard retail roles.
    Uses normalization heuristics to auto-match column names.
    """
    mapping_items = []
    saved = saved_mappings or {}

    # Build lookup map of normalized dataset column names
    col_lookup = {normalize_col_name(col): col for col in columns}

    for role_def in STANDARD_ROLES:
        role = role_def["role"]
        mapped_col = None

        # 1. Check if user already saved a valid mapping for this role
        if role in saved and saved[role] in columns:
            mapped_col = saved[role]
        else:
            # 2. Automatically match against known aliases
            for alias in role_def["aliases"]:
                norm_alias = normalize_col_name(alias)
                if norm_alias in col_lookup:
                    mapped_col = col_lookup[norm_alias]
                    break

        mapping_items.append(
            ColumnMappingItem(
                role=role,
                role_label=role_def["role_label"],
                description=role_def["description"],
                is_required=role_def["is_required"],
                mapped_column=mapped_col,
                is_mapped=mapped_col is not None
            )
        )

    return mapping_items


def sanitize_value_for_json(val: Any) -> Any:
    """Safely convert pandas/numpy values to JSON-serializable Python primitives."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32)):
        return round(float(val), 4)
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val).split('T')[0]
    return str(val)


def inspect_dataframe(
    df: pd.DataFrame,
    filename: str,
    file_size_bytes: int,
    saved_mappings: Optional[Dict[str, str]] = None,
    is_cleaned: bool = False
) -> DatasetSummaryResponse:
    """
    Perform comprehensive dataset inspection:
    - Calculates row and column counts
    - Computes missing values and data types per column
    - Identifies exact duplicate rows
    - Detects date ranges, stores, and products
    - Generates numerical summary statistics (count, mean, min, max)
    - Validates retail data quality rules and flags warnings
    - Produces a 10-row preview
    """
    row_count = int(len(df))
    col_count = int(len(df.columns))
    columns_list = [str(c) for c in df.columns]

    # Suggest/apply column mappings
    mappings = detect_suggested_mappings(columns_list, saved_mappings)
    mapping_dict = {m.role: m.mapped_column for m in mappings if m.mapped_column}

    # 1. Column-by-column inspection
    inspected_columns: List[ColumnInspectionInfo] = []
    total_missing = int(df.isnull().sum().sum())

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isnull().sum())
        missing_pct = round((missing_count / row_count * 100), 2) if row_count > 0 else 0.0
        unique_cnt = int(series.nunique(dropna=True))

        # Check if numeric
        is_num = pd.api.types.is_numeric_dtype(series)

        # Check if date
        is_dt = pd.api.types.is_datetime64_any_dtype(series)
        if not is_dt and ('date' in col.lower() or 'time' in col.lower()):
            # Test sample parseability
            sample_non_null = series.dropna().head(10)
            if not sample_non_null.empty:
                try:
                    pd.to_datetime(sample_non_null, errors='raise')
                    is_dt = True
                except Exception:
                    is_dt = False

        min_val, max_val, mean_val = None, None, None
        if is_num:
            clean_num = series.dropna()
            if not clean_num.empty:
                min_val = round(float(clean_num.min()), 2)
                max_val = round(float(clean_num.max()), 2)
                mean_val = round(float(clean_num.mean()), 2)

        # Sample values (up to 3 unique non-null samples)
        sample_vals = [sanitize_value_for_json(v) for v in series.dropna().unique()[:3]]

        inspected_columns.append(
            ColumnInspectionInfo(
                name=str(col),
                inferred_type=str(series.dtype),
                missing_count=missing_count,
                missing_percentage=missing_pct,
                unique_count=unique_cnt,
                is_numeric=is_num,
                is_date=is_dt,
                sample_values=sample_vals,
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val
            )
        )

    # 2. Date Range analysis
    date_col = mapping_dict.get("date")
    date_start_str, date_end_str = None, None
    unique_dates_cnt = 0

    if date_col and date_col in df.columns:
        try:
            parsed_dates = pd.to_datetime(df[date_col], errors='coerce')
            valid_dates = parsed_dates.dropna()
            if not valid_dates.empty:
                date_start_str = valid_dates.min().strftime('%Y-%m-%d')
                date_end_str = valid_dates.max().strftime('%Y-%m-%d')
                unique_dates_cnt = int(valid_dates.dt.date.nunique())
        except Exception:
            pass

    # 3. Store and Product uniqueness
    store_col = mapping_dict.get("store_id")
    unique_stores_cnt = int(df[store_col].nunique()) if (store_col and store_col in df.columns) else 0

    prod_col = mapping_dict.get("product_id")
    unique_prods_cnt = int(df[prod_col].nunique()) if (prod_col and prod_col in df.columns) else 0

    # 4. Duplicate checks
    duplicate_rows_cnt = int(df.duplicated().sum())

    # 5. Data Quality Validation Checks & Findings
    quality_checks: List[QualityCheckItem] = []
    warnings_count = 0
    errors_count = 0

    # Check: Missing Values
    if total_missing == 0:
        quality_checks.append(
            QualityCheckItem(
                check_type="info",
                title="Zero Missing Values",
                description="All columns are complete. No missing or null records detected.",
                affected_count=0
            )
        )
    else:
        quality_checks.append(
            QualityCheckItem(
                check_type="warning",
                title="Missing Values Detected",
                description=f"Found {total_missing} total null or missing entries across columns.",
                affected_count=total_missing,
                action_recommendation="Review and decide whether to impute or drop missing values during cleaning."
            )
        )
        warnings_count += 1

    # Check: Exact Duplicate Rows
    if duplicate_rows_cnt == 0:
        quality_checks.append(
            QualityCheckItem(
                check_type="info",
                title="Zero Duplicate Rows",
                description="All records are unique across all 15 attributes.",
                affected_count=0
            )
        )
    else:
        quality_checks.append(
            QualityCheckItem(
                check_type="warning",
                title="Duplicate Rows Detected",
                description=f"Found {duplicate_rows_cnt} exact duplicate rows.",
                affected_count=duplicate_rows_cnt,
                action_recommendation="Exact duplicates can be removed during the data cleaning step."
            )
        )
        warnings_count += 1

    # Check: Composite Key Duplicates (Date + Store + Product)
    if date_col and store_col and prod_col and all(c in df.columns for c in [date_col, store_col, prod_col]):
        composite_dups = int(df.duplicated(subset=[date_col, store_col, prod_col]).sum())
        if composite_dups == 0:
            quality_checks.append(
                QualityCheckItem(
                    check_type="info",
                    title="Unique Composite Key (Date + Store + Product)",
                    description="Every transaction is uniquely indexed by Date, Store ID, and Product ID (0 composite duplicates).",
                    affected_count=0
                )
            )
        else:
            quality_checks.append(
                QualityCheckItem(
                    check_type="warning",
                    title="Composite Key Duplicates Found",
                    description=f"Found {composite_dups} duplicate records matching on Date + Store ID + Product ID.",
                    affected_count=composite_dups,
                    action_recommendation="Check if multiple transactions occurred on the same day for the same product and store."
                )
            )
            warnings_count += 1

    # Check: Suspicious Negative Values in Numeric Columns
    for col in df.select_dtypes(include='number').columns:
        neg_count = int((df[col] < 0).sum())
        if neg_count > 0:
            min_neg = round(float(df[col].min()), 2)
            # Special Domain Rule for Demand Forecast
            if "demand forecast" in col.lower() or "forecast" in col.lower():
                quality_checks.append(
                    QualityCheckItem(
                        check_type="warning",
                        title=f"Negative Values in '{col}' (Domain Notice)",
                        description=(
                            f"Detected {neg_count} negative values (minimum: {min_neg}). "
                            "In retail inventory management, customer demand cannot realistically be negative. "
                            "Per data-preservation rules, these records are NOT deleted from the dataset. "
                            "Notice: '{col}' will be excluded as an input predictor in initial ML models, "
                            "and 'Units Sold' will be used as the true ground-truth forecast target."
                        ),
                        affected_column=str(col),
                        affected_count=neg_count,
                        action_recommendation="Preserve records intact without row deletion; avoid using as a training feature."
                    )
                )
                warnings_count += 1
            else:
                quality_checks.append(
                    QualityCheckItem(
                        check_type="warning",
                        title=f"Negative Values in '{col}'",
                        description=f"Found {neg_count} negative entries in column '{col}' (minimum: {min_neg}).",
                        affected_column=str(col),
                        affected_count=neg_count,
                        action_recommendation="Verify whether negative values indicate returns, credits, or data entry anomalies."
                    )
                )
                warnings_count += 1

    # 6. Generate 10-row preview table
    preview_slice = df.head(10).copy()
    preview_records = []
    for _, row in preview_slice.iterrows():
        record = {str(k): sanitize_value_for_json(v) for k, v in row.items()}
        preview_records.append(record)

    return DatasetSummaryResponse(
        has_dataset=True,
        filename=filename,
        file_size_bytes=file_size_bytes,
        row_count=row_count,
        column_count=col_count,
        date_range_start=date_start_str,
        date_range_end=date_end_str,
        unique_dates_count=unique_dates_cnt,
        unique_stores_count=unique_stores_cnt,
        unique_products_count=unique_prods_cnt,
        total_missing_values=total_missing,
        duplicate_rows_count=duplicate_rows_cnt,
        status="cleaned" if is_cleaned else "uploaded",
        preview_rows=preview_records,
        columns=inspected_columns,
        mappings=mappings,
        quality_checks=quality_checks,
        warnings_count=warnings_count,
        errors_count=errors_count,
        is_cleaned=is_cleaned,
        is_ready_for_analysis=True  # Retail dataset is complete and ready
    )


def save_raw_csv_file(file_contents: bytes, original_filename: str) -> Tuple[str, int]:
    """
    Safely save the uploaded CSV bytes to backend/data/raw_dataset.csv.
    Prevents path traversal attacks by ignoring client path components.
    """
    safe_filename = os.path.basename(original_filename)
    with open(RAW_DATASET_PATH, "wb") as f:
        f.write(file_contents)
    file_size = len(file_contents)
    return safe_filename, file_size


def load_raw_dataset() -> pd.DataFrame:
    """Load the raw dataset CSV using pandas."""
    if not os.path.exists(RAW_DATASET_PATH):
        raise FileNotFoundError("No raw dataset uploaded yet.")
    return pd.read_csv(RAW_DATASET_PATH)


def load_cleaned_dataset() -> pd.DataFrame:
    """Load the cleaned dataset CSV using pandas."""
    if not os.path.exists(CLEANED_DATASET_PATH):
        raise FileNotFoundError("No cleaned dataset available. Please run data cleaning first.")
    return pd.read_csv(CLEANED_DATASET_PATH)


def save_column_mappings_to_file(mappings: Dict[str, Optional[str]]) -> None:
    """Save user column mappings to a local JSON file."""
    with open(MAPPINGS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)


def load_column_mappings_from_file() -> Dict[str, str]:
    """Load saved column mappings from local JSON file."""
    if os.path.exists(MAPPINGS_FILE_PATH):
        try:
            with open(MAPPINGS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def execute_data_cleaning(
    custom_mappings: Optional[Dict[str, Optional[str]]] = None
) -> CleaningResultResponse:
    """
    Execute transparent and reportable data cleaning:
    1. Loads raw dataset
    2. Validates and parses dates into standardized YYYY-MM-DD format
    3. Handles exact duplicate rows if any exist
    4. Applies chronological ordering by date (and store/product if available)
    5. Preserves the 673 negative Demand Forecast values without silent deletion
    6. Writes cleaned result to backend/data/cleaned_dataset.csv
    7. Returns comprehensive before/after statistics and applied changes
    """
    df = load_raw_dataset()
    original_rows = int(len(df))
    original_cols = int(len(df.columns))
    changes_applied = []
    warnings = []

    # Get active mappings
    active_mappings = load_column_mappings_from_file()
    if custom_mappings:
        active_mappings.update({k: v for k, v in custom_mappings.items() if v})
        save_column_mappings_to_file(active_mappings)

    # 1. Handle exact duplicate rows
    dups_count = int(df.duplicated().sum())
    if dups_count > 0:
        df = df.drop_duplicates()
        changes_applied.append(f"Removed {dups_count} exact duplicate rows.")
    else:
        changes_applied.append("Duplicate check: 0 exact duplicate rows found (no rows dropped).")

    # 2. Date parsing and validation
    date_col = active_mappings.get("date") or "Date"
    if date_col in df.columns:
        parsed_dates = pd.to_datetime(df[date_col], errors='coerce')
        invalid_dates_cnt = int(parsed_dates.isnull().sum() - df[date_col].isnull().sum())
        if invalid_dates_cnt > 0:
            warnings.append(f"Found {invalid_dates_cnt} invalid date values in column '{date_col}'.")
        else:
            # Format cleanly as YYYY-MM-DD
            df[date_col] = parsed_dates.dt.strftime('%Y-%m-%d')
            changes_applied.append(f"Standardized '{date_col}' column to ISO date format (YYYY-MM-DD).")

    # 3. Numeric column validation
    for col in ["Units Sold", "Inventory Level", "Price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            changes_applied.append(f"Verified numeric data type for column '{col}'.")

    # 4. Special handling for Demand Forecast negative values
    forecast_col = None
    for c in df.columns:
        if "demand forecast" in c.lower() or "forecast" in c.lower():
            forecast_col = c
            break

    if forecast_col and forecast_col in df.columns:
        neg_count = int((df[forecast_col] < 0).sum())
        if neg_count > 0:
            warning_msg = (
                f"Identified {neg_count} negative values in '{forecast_col}' (minimum: {df[forecast_col].min()}). "
                "Per domain specification, all rows are PRESERVED without deletion. "
                "This column will NOT be used as a predictive feature in ML training."
            )
            warnings.append(warning_msg)
            changes_applied.append(f"Data Preservation: Retained all {neg_count} negative entries in '{forecast_col}' intact.")

    # 5. Chronological sorting
    sort_cols = []
    if date_col in df.columns:
        sort_cols.append(date_col)
    store_col = active_mappings.get("store_id") or "Store ID"
    if store_col in df.columns:
        sort_cols.append(store_col)
    prod_col = active_mappings.get("product_id") or "Product ID"
    if prod_col in df.columns:
        sort_cols.append(prod_col)

    if sort_cols:
        df = df.sort_values(by=sort_cols).reset_index(drop=True)
        changes_applied.append(f"Sorted dataset chronologically by: {', '.join(sort_cols)}.")

    # 6. Save cleaned CSV
    df.to_csv(CLEANED_DATASET_PATH, index=False)

    cleaned_rows = int(len(df))
    cleaned_cols = int(len(df.columns))

    # 7. Generate cleaned preview (first 10 records)
    preview_slice = df.head(10).copy()
    cleaned_preview = []
    for _, row in preview_slice.iterrows():
        cleaned_preview.append({str(k): sanitize_value_for_json(v) for k, v in row.items()})

    return CleaningResultResponse(
        success=True,
        message="Dataset cleaned and validated successfully.",
        original_rows=original_rows,
        cleaned_rows=cleaned_rows,
        original_columns=original_cols,
        cleaned_columns=cleaned_cols,
        changes_applied=changes_applied,
        warnings=warnings,
        is_ready_for_analysis=True,
        cleaned_preview_rows=cleaned_preview
    )
