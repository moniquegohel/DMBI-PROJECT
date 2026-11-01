import os
import calendar
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from app.services.data_cleaning import (
    CLEANED_DATASET_PATH,
    RAW_DATASET_PATH,
    load_cleaned_dataset,
    load_raw_dataset,
    load_column_mappings_from_file,
    STANDARD_ROLES
)
from app.schemas.analysis import (
    AnalysisSummaryResponse,
    MonthlySalesItem,
    ProductSalesItem,
    CategorySalesItem,
    StoreSalesItem
)

# Lightweight in-memory cache to avoid repeated disk reads
_CACHE: Dict[str, Any] = {
    "file_path": None,
    "mtime": None,
    "df": None,
    "is_cleaned": False,
    "mappings": None
}


def clear_analysis_cache() -> None:
    """Clear cached DataFrame in memory."""
    global _CACHE
    _CACHE = {
        "file_path": None,
        "mtime": None,
        "df": None,
        "is_cleaned": False,
        "mappings": None
    }


def get_active_dataset_with_cache() -> Tuple[pd.DataFrame, str, bool, Dict[str, str]]:
    """
    Retrieve the active retail sales DataFrame and active column mappings.
    Prefers the cleaned dataset (cleaned_dataset.csv) if available;
    falls back to the raw uploaded dataset (raw_dataset.csv).
    
    Caches parsed DataFrame in-memory using file modification timestamp
    to ensure instant response times without unnecessary disk I/O.
    """
    global _CACHE

    # 1. Determine active file path
    if os.path.exists(CLEANED_DATASET_PATH):
        active_path = CLEANED_DATASET_PATH
        is_cleaned = True
        filename = "cleaned_dataset.csv"
    elif os.path.exists(RAW_DATASET_PATH):
        active_path = RAW_DATASET_PATH
        is_cleaned = False
        filename = "raw_dataset.csv"
    else:
        raise FileNotFoundError(
            "No retail dataset uploaded yet. Please upload a retail CSV on the Dataset page."
        )

    # 2. Check if cache is still valid
    current_mtime = os.path.getmtime(active_path)
    if (
        _CACHE["df"] is not None
        and _CACHE["file_path"] == active_path
        and _CACHE["mtime"] == current_mtime
    ):
        return _CACHE["df"], filename, _CACHE["is_cleaned"], _CACHE["mappings"]

    # 3. Load DataFrame
    df = pd.read_csv(active_path)

    # 4. Resolve column mappings (saved mappings or auto-inferred aliases)
    saved_mappings = load_column_mappings_from_file()
    active_mappings: Dict[str, str] = {}

    # Standardize column lookup dictionary (normalized lowercased string -> actual column name)
    norm_cols = {str(col).strip().lower().replace("_", "").replace(" ", ""): col for col in df.columns}

    for role_def in STANDARD_ROLES:
        role_key = role_def["role"]
        # Priority A: User-saved mapping
        if role_key in saved_mappings and saved_mappings[role_key] in df.columns:
            active_mappings[role_key] = saved_mappings[role_key]
            continue

        # Priority B: Exact name match
        if role_def["role_label"] in df.columns:
            active_mappings[role_key] = role_def["role_label"]
            continue

        # Priority C: Alias matches
        for alias in role_def["aliases"]:
            clean_alias = alias.lower().replace("_", "").replace(" ", "")
            if clean_alias in norm_cols:
                active_mappings[role_key] = norm_cols[clean_alias]
                break

    # Also detect Category if available
    if "category" not in active_mappings:
        for col in df.columns:
            if "category" in str(col).lower() or "cat" == str(col).lower():
                active_mappings["category"] = col
                break

    # Update cache
    _CACHE["file_path"] = active_path
    _CACHE["mtime"] = current_mtime
    _CACHE["df"] = df
    _CACHE["is_cleaned"] = is_cleaned
    _CACHE["mappings"] = active_mappings

    return df, filename, is_cleaned, active_mappings


def calculate_sales_summary() -> AnalysisSummaryResponse:
    """
    Compute comprehensive high-level historical sales metrics.
    Reconciles total sales volume, computes average sales per record,
    minimum/maximum per record, and distinct entity counts.
    """
    try:
        df, filename, is_cleaned, mappings = get_active_dataset_with_cache()
    except FileNotFoundError:
        return AnalysisSummaryResponse(
            has_dataset=False,
            dataset_name="None",
            is_cleaned=False,
            total_records=0,
            total_units_sold=0,
            average_units_sold_per_record=0.0,
            min_units_sold_per_record=0,
            max_units_sold_per_record=0,
            message="No dataset available. Please upload a retail sales CSV in the Dataset Upload section."
        )

    # Validate required sales column
    units_sold_col = mappings.get("units_sold")
    if not units_sold_col or units_sold_col not in df.columns:
        raise ValueError(
            "Required 'Units Sold' column mapping is missing or could not be found in the dataset. "
            "Please check column mappings on the Dataset page."
        )

    # Ensure numeric series
    sales_series = pd.to_numeric(df[units_sold_col], errors='coerce').fillna(0)
    total_records = int(len(df))
    total_units_sold = int(sales_series.sum())
    avg_per_record = round(float(sales_series.mean()), 2) if total_records > 0 else 0.0
    min_units = int(sales_series.min()) if total_records > 0 else 0
    max_units = int(sales_series.max()) if total_records > 0 else 0

    # Optional metadata counts
    unique_products = None
    prod_col = mappings.get("product_id")
    if prod_col and prod_col in df.columns:
        unique_products = int(df[prod_col].nunique())

    unique_stores = None
    store_col = mappings.get("store_id")
    if store_col and store_col in df.columns:
        unique_stores = int(df[store_col].nunique())

    unique_dates = None
    date_start = None
    date_end = None
    date_col = mappings.get("date")
    if date_col and date_col in df.columns:
        unique_dates = int(df[date_col].nunique())
        date_start = str(df[date_col].min()).split('T')[0]
        date_end = str(df[date_col].max()).split('T')[0]

    return AnalysisSummaryResponse(
        has_dataset=True,
        dataset_name=filename,
        is_cleaned=is_cleaned,
        total_records=total_records,
        total_units_sold=total_units_sold,
        average_units_sold_per_record=avg_per_record,
        min_units_sold_per_record=min_units,
        max_units_sold_per_record=max_units,
        unique_products_count=unique_products,
        unique_stores_count=unique_stores,
        unique_dates_count=unique_dates,
        date_range_start=date_start,
        date_range_end=date_end,
        mapped_columns=mappings,
        message=f"Analyzed {total_records:,} records from '{filename}' successfully."
    )


def calculate_monthly_sales() -> List[MonthlySalesItem]:
    """
    Calculate calendar month-wise sales totals in chronological order.
    Ensures that sum(monthly_totals) == total_units_sold.
    """
    df, _, _, mappings = get_active_dataset_with_cache()

    # Validate required columns
    units_sold_col = mappings.get("units_sold")
    date_col = mappings.get("date")

    if not units_sold_col or units_sold_col not in df.columns:
        raise ValueError(
            "Required 'Units Sold' column mapping is missing or could not be found in the dataset."
        )
    if not date_col or date_col not in df.columns:
        raise ValueError(
            "Required 'Date' column mapping is missing or could not be found in the dataset."
        )

    # Copy minimal columns for fast aggregation
    temp_df = pd.DataFrame({
        "raw_date": df[date_col],
        "units_sold": pd.to_numeric(df[units_sold_col], errors='coerce').fillna(0)
    })

    # Parse dates safely
    parsed_dates = pd.to_datetime(temp_df["raw_date"], errors='coerce')
    # Filter out unparseable dates if any exist
    valid_mask = parsed_dates.notna()
    if not valid_mask.all():
        temp_df = temp_df[valid_mask]
        parsed_dates = parsed_dates[valid_mask]

    temp_df["year"] = parsed_dates.dt.year
    temp_df["month_num"] = parsed_dates.dt.month
    temp_df["month_key"] = parsed_dates.dt.strftime('%Y-%m')

    # Chronological grouping
    grouped = temp_df.groupby(["year", "month_num", "month_key"]).agg(
        total_units_sold=("units_sold", "sum"),
        record_count=("units_sold", "count"),
        avg_units_sold=("units_sold", "mean")
    ).reset_index()

    # Explicit chronological sort by Year and Month number
    grouped = grouped.sort_values(by=["year", "month_num"], ascending=True)

    items: List[MonthlySalesItem] = []
    for _, row in grouped.iterrows():
        yr = int(row["year"])
        m_num = int(row["month_num"])
        month_abbr = calendar.month_abbr[m_num]
        month_label = f"{month_abbr} {yr}"
        sold_qty = int(row["total_units_sold"])
        records = int(row["record_count"])
        avg_qty = round(float(row["avg_units_sold"]), 2) if records > 0 else 0.0

        items.append(
            MonthlySalesItem(
                month=str(row["month_key"]),
                month_label=month_label,
                year=yr,
                month_num=m_num,
                total_units_sold=sold_qty,
                total_sales=sold_qty,
                record_count=records,
                average_units_sold_per_record=avg_qty
            )
        )

    return items


def calculate_product_sales() -> List[ProductSalesItem]:
    """
    Calculate product-wise sales aggregations sorted in descending order of total units sold.
    Includes category info and percentage share of global sales.
    """
    df, _, _, mappings = get_active_dataset_with_cache()

    units_sold_col = mappings.get("units_sold")
    prod_col = mappings.get("product_id")

    if not units_sold_col or units_sold_col not in df.columns:
        raise ValueError(
            "Required 'Units Sold' column mapping is missing or could not be found in the dataset."
        )
    if not prod_col or prod_col not in df.columns:
        raise ValueError(
            "Required 'Product ID' column mapping is missing or could not be found in the dataset."
        )

    category_col = mappings.get("category")
    if category_col and category_col not in df.columns:
        category_col = None

    # Prepare DataFrame for grouping
    cols_to_use = [prod_col, units_sold_col]
    if category_col:
        cols_to_use.append(category_col)

    temp_df = df[cols_to_use].copy()
    temp_df["clean_sales"] = pd.to_numeric(temp_df[units_sold_col], errors='coerce').fillna(0)

    global_total = float(temp_df["clean_sales"].sum())

    # Group by product
    grouped = temp_df.groupby(prod_col).agg(
        total_units_sold=("clean_sales", "sum"),
        record_count=("clean_sales", "count"),
        avg_units_sold=("clean_sales", "mean")
    ).reset_index()

    # Sort descending by total units sold
    grouped = grouped.sort_values(by="total_units_sold", ascending=False)

    # Collect category mappings per product if available
    prod_categories: Dict[str, List[str]] = {}
    if category_col:
        for p_id, group in temp_df.groupby(prod_col):
            cats = [str(c) for c in group[category_col].dropna().unique() if str(c).strip()]
            prod_categories[str(p_id)] = cats

    items: List[ProductSalesItem] = []
    for _, row in grouped.iterrows():
        p_id = str(row[prod_col])
        sold_qty = int(row["total_units_sold"])
        records = int(row["record_count"])
        avg_qty = round(float(row["avg_units_sold"]), 2) if records > 0 else 0.0
        pct = round((sold_qty / global_total * 100), 2) if global_total > 0 else 0.0

        cats = prod_categories.get(p_id, [])
        primary_cat = ", ".join(cats) if cats else None

        items.append(
            ProductSalesItem(
                product_id=p_id,
                product_name=p_id,
                category=primary_cat,
                categories=cats,
                total_units_sold=sold_qty,
                total_sales=sold_qty,
                record_count=records,
                average_units_sold_per_record=avg_qty,
                percentage_of_total=pct
            )
        )

    return items


def calculate_category_sales() -> List[CategorySalesItem]:
    """
    Calculate category-level sales breakdown if category column is available.
    Sorted descending by total units sold.
    """
    df, _, _, mappings = get_active_dataset_with_cache()

    units_sold_col = mappings.get("units_sold")
    category_col = mappings.get("category")

    if not units_sold_col or units_sold_col not in df.columns:
        raise ValueError("Required 'Units Sold' column mapping is missing.")
    if not category_col or category_col not in df.columns:
        return []

    temp_df = df[[category_col, units_sold_col]].copy()
    temp_df["clean_sales"] = pd.to_numeric(temp_df[units_sold_col], errors='coerce').fillna(0)
    global_total = float(temp_df["clean_sales"].sum())

    grouped = temp_df.groupby(category_col).agg(
        total_units_sold=("clean_sales", "sum"),
        record_count=("clean_sales", "count"),
        avg_units_sold=("clean_sales", "mean")
    ).reset_index()

    grouped = grouped.sort_values(by="total_units_sold", ascending=False)

    items: List[CategorySalesItem] = []
    for _, row in grouped.iterrows():
        cat = str(row[category_col])
        sold_qty = int(row["total_units_sold"])
        records = int(row["record_count"])
        avg_qty = round(float(row["avg_units_sold"]), 2) if records > 0 else 0.0
        pct = round((sold_qty / global_total * 100), 2) if global_total > 0 else 0.0

        items.append(
            CategorySalesItem(
                category=cat,
                total_units_sold=sold_qty,
                total_sales=sold_qty,
                record_count=records,
                average_units_sold_per_record=avg_qty,
                percentage_of_total=pct
            )
        )

    return items


def calculate_store_sales() -> List[StoreSalesItem]:
    """
    Calculate store-level sales breakdown if store column is available.
    Sorted descending by total units sold.
    """
    df, _, _, mappings = get_active_dataset_with_cache()

    units_sold_col = mappings.get("units_sold")
    store_col = mappings.get("store_id")

    if not units_sold_col or units_sold_col not in df.columns:
        raise ValueError("Required 'Units Sold' column mapping is missing.")
    if not store_col or store_col not in df.columns:
        return []

    temp_df = df[[store_col, units_sold_col]].copy()
    temp_df["clean_sales"] = pd.to_numeric(temp_df[units_sold_col], errors='coerce').fillna(0)
    global_total = float(temp_df["clean_sales"].sum())

    grouped = temp_df.groupby(store_col).agg(
        total_units_sold=("clean_sales", "sum"),
        record_count=("clean_sales", "count"),
        avg_units_sold=("clean_sales", "mean")
    ).reset_index()

    grouped = grouped.sort_values(by="total_units_sold", ascending=False)

    items: List[StoreSalesItem] = []
    for _, row in grouped.iterrows():
        s_id = str(row[store_col])
        sold_qty = int(row["total_units_sold"])
        records = int(row["record_count"])
        avg_qty = round(float(row["avg_units_sold"]), 2) if records > 0 else 0.0
        pct = round((sold_qty / global_total * 100), 2) if global_total > 0 else 0.0

        items.append(
            StoreSalesItem(
                store_id=s_id,
                total_units_sold=sold_qty,
                total_sales=sold_qty,
                record_count=records,
                average_units_sold_per_record=avg_qty,
                percentage_of_total=pct
            )
        )

    return items
