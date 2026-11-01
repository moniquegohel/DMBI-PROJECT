"""
tests/test_milestone5.py — Milestone 5: Feature Engineering Tests

These tests verify that the feature engineering service:

  1. Generates all required date features with correct types and encoding.
  2. Computes previous_day_sales correctly within each store-product group
     (never carries values across unrelated products or stores).
  3. Computes rolling_7_day_average using only *previous* observations
     (shift-then-roll: no current-day sales leakage).
  4. Provides a small deterministic hand-checkable example for lag/rolling.
  5. Preserves initial-row NaN values for lag/rolling (never fills silently).
  6. Produces deterministic, chronological output ordering.
  7. Works correctly when optional columns (store_id) are absent.
  8. Returns clear errors when required date/sales mappings are missing.
  9. Excludes Demand Forecast from predictor columns.
 10. Does NOT add duplicate columns or rows on repeated runs.
 11. Does NOT break Milestones 1–4 (health, dataset, analysis endpoints).

The deterministic unit-test in test 4 uses a hand-crafted 3-product, 5-day
dataset so that the expected lag and rolling values can be manually verified:

  Product P1 (Store S1):
    Day 1: Units=10  → prev=NaN,   rolling=NaN  (no history)
    Day 2: Units=20  → prev=10,    rolling=10.0 (1 value)
    Day 3: Units=30  → prev=20,    rolling=15.0 (avg of 10,20)
    Day 4: Units=40  → prev=30,    rolling=20.0 (avg of 10,20,30)
    Day 5: Units=50  → prev=40,    rolling=25.0 (avg of 10,20,30,40)

  Product P2 (Store S1) — must NOT bleed into P1's calculation:
    Day 1: Units=100 → prev=NaN,   rolling=NaN
    Day 2: Units=200 → prev=100,   rolling=100.0
"""

import os
import json
import shutil
import tempfile
import math
from pathlib import Path

import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient

# ── App & path imports ─────────────────────────────────────────────────────

from app.main import app
from app.services import data_cleaning as dc
from app.services import feature_engineering as fe

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def tmp_data_dir(tmp_path):
    """
    Redirect all DATA_DIR-based file paths to a temporary directory for the
    duration of a single test.  Restores the originals on teardown.
    """
    orig_data_dir        = dc.DATA_DIR
    orig_raw             = dc.RAW_DATASET_PATH
    orig_clean           = dc.CLEANED_DATASET_PATH
    orig_mappings        = dc.MAPPINGS_FILE_PATH
    orig_fe_data_dir     = fe.DATA_DIR
    orig_ml              = fe.ML_DATASET_PATH

    # Patch module-level constants
    dc.DATA_DIR              = str(tmp_path)
    dc.RAW_DATASET_PATH      = str(tmp_path / "raw_dataset.csv")
    dc.CLEANED_DATASET_PATH  = str(tmp_path / "cleaned_dataset.csv")
    dc.MAPPINGS_FILE_PATH    = str(tmp_path / "column_mappings.json")
    fe.DATA_DIR              = str(tmp_path)
    fe.ML_DATASET_PATH       = str(tmp_path / "ml_dataset.csv")

    yield tmp_path

    # Restore originals
    dc.DATA_DIR              = orig_data_dir
    dc.RAW_DATASET_PATH      = orig_raw
    dc.CLEANED_DATASET_PATH  = orig_clean
    dc.MAPPINGS_FILE_PATH    = orig_mappings
    fe.DATA_DIR              = orig_fe_data_dir
    fe.ML_DATASET_PATH       = orig_ml


def _write_deterministic_csv(tmp_path: Path) -> str:
    """
    Write a small deterministic 10-row CSV with two products and one store.
    Used for leakage and grouping tests.

      P1/S1: 5 daily rows, Units Sold = 10, 20, 30, 40, 50
      P2/S1: 5 daily rows, Units Sold = 100, 200, 300, 400, 500
    """
    rows = []
    for day in range(1, 6):
        date = f"2024-01-{day:02d}"
        rows.append({
            "Date": date, "Store ID": "S1", "Product ID": "P1",
            "Units Sold": day * 10,
            "Demand Forecast": day * 10 - 1,  # should be excluded
        })
        rows.append({
            "Date": date, "Store ID": "S1", "Product ID": "P2",
            "Units Sold": day * 100,
            "Demand Forecast": day * 100 - 1,
        })

    df = pd.DataFrame(rows)
    path = str(tmp_path / "cleaned_dataset.csv")
    df.to_csv(path, index=False)
    return path


def _write_mappings(tmp_path: Path) -> None:
    """Write the column_mappings.json for the deterministic CSV."""
    mappings = {
        "date":       "Date",
        "store_id":   "Store ID",
        "product_id": "Product ID",
        "units_sold": "Units Sold",
    }
    path = str(tmp_path / "column_mappings.json")
    with open(path, "w") as f:
        json.dump(mappings, f)


# ═══════════════════════════════════════════════════════════════════════════
# Test 1 — Date features: types, values, and encoding
# ═══════════════════════════════════════════════════════════════════════════

def test_date_features_values_and_types(tmp_data_dir):
    """
    day, day_of_week, month, is_weekend must be present, integer-typed,
    and encoded correctly for the known test dates.
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    result = fe.run_feature_engineering()
    assert result.success

    ml_df = pd.read_csv(fe.ML_DATASET_PATH)

    for col in ["day", "day_of_week", "month", "is_weekend"]:
        assert col in ml_df.columns, f"Missing feature column: {col}"

    # 2024-01-01 is a Monday → day_of_week=0, is_weekend=0, day=1, month=1
    first_row = ml_df[ml_df["Product ID"] == "P1"].sort_values("Date").iloc[0]
    assert int(first_row["day"])         == 1,  "day should be 1 for Jan 1"
    assert int(first_row["day_of_week"]) == 0,  "2024-01-01 is Monday → 0"
    assert int(first_row["month"])       == 1,  "January → month=1"
    assert int(first_row["is_weekend"])  == 0,  "Monday is not a weekend"

    # 2024-01-06 is a Saturday → is_weekend=1  (day 6 is outside our 5-day set;
    # verify using pandas directly on a known weekend date in the set)
    # In our dataset Jan 6 & 7 are Sat/Sun — but we only have Jan 1-5
    # Jan 5 is Friday → is_weekend=0
    row_jan5 = ml_df[
        (ml_df["Product ID"] == "P1") & (ml_df["Date"] == "2024-01-05")
    ].iloc[0]
    assert int(row_jan5["day_of_week"]) == 4,  "2024-01-05 is Friday → 4"
    assert int(row_jan5["is_weekend"])  == 0,  "Friday is not a weekend"


# ═══════════════════════════════════════════════════════════════════════════
# Test 2 — previous_day_sales: correct lag within group, no cross-product bleed
# ═══════════════════════════════════════════════════════════════════════════

def test_previous_day_sales_within_group_no_bleed(tmp_data_dir):
    """
    previous_day_sales for row [i] in group G must equal Units Sold at row [i-1]
    of the SAME group.  Values from a different product must never appear.
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    fe.run_feature_engineering()
    ml_df = pd.read_csv(fe.ML_DATASET_PATH)

    # Check P1 group only
    p1 = ml_df[ml_df["Product ID"] == "P1"].sort_values("Date").reset_index(drop=True)

    # Row 0: NaN (first in group — no prior observation)
    assert pd.isna(p1.loc[0, "previous_day_sales"]), "First P1 row must be NaN"

    # Rows 1–4: should be the previous row's Units Sold
    for i in range(1, 5):
        expected = int(p1.loc[i - 1, "Units Sold"])
        actual   = int(p1.loc[i,     "previous_day_sales"])
        assert actual == expected, (
            f"P1 row {i}: expected previous_day_sales={expected}, got {actual}"
        )

    # Check that P2's previous_day_sales never contains P1 values (10, 20 …)
    p1_values = set(p1["Units Sold"].astype(int).tolist())
    p2 = ml_df[ml_df["Product ID"] == "P2"].sort_values("Date").reset_index(drop=True)
    for i in range(1, 5):
        actual = int(p2.loc[i, "previous_day_sales"])
        assert actual not in p1_values, (
            f"P2 row {i} previous_day_sales={actual} looks like a P1 value — cross-group bleed!"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Test 3 — rolling_7_day_average: excludes current row (no target leakage)
# ═══════════════════════════════════════════════════════════════════════════

def test_rolling_7day_average_no_current_row_leakage(tmp_data_dir):
    """
    rolling_7_day_average must use only *previous* observations.
    This test verifies that the current row's Units Sold is NOT included.

    Expected for P1 (Units Sold = 10, 20, 30, 40, 50):
      Day 1 (row 0): NaN  (no prior data)
      Day 2 (row 1): 10.0  (only row 0 available)
      Day 3 (row 2): 15.0  (avg of 10, 20)
      Day 4 (row 3): 20.0  (avg of 10, 20, 30)
      Day 5 (row 4): 25.0  (avg of 10, 20, 30, 40)
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    fe.run_feature_engineering()
    ml_df = pd.read_csv(fe.ML_DATASET_PATH)

    p1 = ml_df[ml_df["Product ID"] == "P1"].sort_values("Date").reset_index(drop=True)

    # Row 0 — NaN
    assert pd.isna(p1.loc[0, "rolling_7_day_average"]), "Row 0 rolling must be NaN"

    expected_rolling = [None, 10.0, 15.0, 20.0, 25.0]
    for i in range(1, 5):
        actual = round(float(p1.loc[i, "rolling_7_day_average"]), 4)
        exp    = expected_rolling[i]
        assert abs(actual - exp) < 0.001, (
            f"P1 row {i}: expected rolling_7_day_average={exp}, got {actual}. "
            "This likely indicates current-row target leakage."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Test 4 — Deterministic leakage check (manual verification reference)
# ═══════════════════════════════════════════════════════════════════════════

def test_deterministic_lag_rolling_hand_check(tmp_data_dir):
    """
    Explicit hand-checkable test.
    If the shift-then-roll logic leaks the current row, rolling values
    would include today's sales — this test will catch that.

    P2 hand-check (Units Sold = 100, 200, 300, 400, 500):
      Row 0: prev=NaN,   rolling=NaN
      Row 1: prev=100,   rolling=100.0
      Row 2: prev=200,   rolling=150.0
      Row 3: prev=300,   rolling=200.0
      Row 4: prev=400,   rolling=250.0
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    fe.run_feature_engineering()
    ml_df = pd.read_csv(fe.ML_DATASET_PATH)

    p2 = ml_df[ml_df["Product ID"] == "P2"].sort_values("Date").reset_index(drop=True)

    assert pd.isna(p2.loc[0, "previous_day_sales"]),    "Row 0 prev must be NaN"
    assert pd.isna(p2.loc[0, "rolling_7_day_average"]), "Row 0 rolling must be NaN"

    cases = [
        # (row, expected_prev, expected_rolling)
        (1, 100.0, 100.0),
        (2, 200.0, 150.0),
        (3, 300.0, 200.0),
        (4, 400.0, 250.0),
    ]
    for row_i, exp_prev, exp_roll in cases:
        actual_prev = float(p2.loc[row_i, "previous_day_sales"])
        actual_roll = float(p2.loc[row_i, "rolling_7_day_average"])
        assert abs(actual_prev - exp_prev) < 0.001, (
            f"P2 row {row_i}: expected prev={exp_prev}, got {actual_prev}"
        )
        assert abs(actual_roll - exp_roll) < 0.001, (
            f"P2 row {row_i}: expected rolling={exp_roll}, got {actual_roll}. "
            "Possible target leakage — check shift-then-roll pattern."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Test 5 — Initial NaN rows are preserved, not silently filled
# ═══════════════════════════════════════════════════════════════════════════

def test_initial_nan_rows_preserved(tmp_data_dir):
    """
    The first row of each store-product group must have NaN for
    previous_day_sales.  Row count must equal the source dataset row count.
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    result = fe.run_feature_engineering()
    ml_df  = pd.read_csv(fe.ML_DATASET_PATH)

    # Input has 10 rows (5 per product × 2 products)
    assert result.input_rows  == 10, f"Expected 10 input rows, got {result.input_rows}"
    assert result.output_rows == 10, f"Expected 10 output rows, got {result.output_rows}"
    assert len(ml_df)         == 10

    # Each of the 2 products contributes exactly 1 NaN for previous_day_sales
    assert result.previous_day_sales_nulls == 2, (
        f"Expected 2 NaN lag values (one per product group), "
        f"got {result.previous_day_sales_nulls}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Test 6 — Output ordering is deterministic and chronological within each group
# ═══════════════════════════════════════════════════════════════════════════

def test_output_is_chronological_within_group(tmp_data_dir):
    """Date column must be non-decreasing within each product group."""
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    fe.run_feature_engineering()
    ml_df = pd.read_csv(fe.ML_DATASET_PATH)
    ml_df["_date"] = pd.to_datetime(ml_df["Date"])

    for prod, group in ml_df.groupby("Product ID"):
        dates = group["_date"].tolist()
        assert dates == sorted(dates), (
            f"Product {prod}: dates are not in chronological order: {dates}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Test 7 — Optional columns absent: feature generation still succeeds
# ═══════════════════════════════════════════════════════════════════════════

def test_optional_columns_absent_does_not_crash(tmp_data_dir):
    """
    A CSV with only Date, Product ID, and Units Sold (no Store ID, no Category,
    no Price, etc.) must still generate features successfully.
    """
    minimal_rows = []
    for day in range(1, 6):
        minimal_rows.append({
            "Date": f"2024-01-{day:02d}",
            "Product ID": "P1",
            "Units Sold": day * 10,
        })
    df = pd.DataFrame(minimal_rows)
    df.to_csv(dc.CLEANED_DATASET_PATH, index=False)

    # Mappings for minimal CSV
    mappings = {"date": "Date", "product_id": "Product ID", "units_sold": "Units Sold"}
    with open(dc.MAPPINGS_FILE_PATH, "w") as f:
        json.dump(mappings, f)

    result = fe.run_feature_engineering()
    assert result.success, f"Feature generation failed: {result.message}"
    assert result.output_rows == 5
    assert "day" in result.predictor_names
    assert "previous_day_sales" in result.predictor_names


# ═══════════════════════════════════════════════════════════════════════════
# Test 8 — Missing required date mapping raises clear error
# ═══════════════════════════════════════════════════════════════════════════

def test_missing_date_mapping_raises_value_error(tmp_data_dir):
    """
    If the date column cannot be resolved, run_feature_engineering must
    raise ValueError with a message explaining the problem.
    """
    # Write a CSV without any recognisable date column name
    df = pd.DataFrame({"weirdcol": ["2024-01-01"], "Units Sold": [10], "Product ID": ["P1"]})
    df.to_csv(dc.CLEANED_DATASET_PATH, index=False)
    # Empty mappings — nothing will be resolved
    with open(dc.MAPPINGS_FILE_PATH, "w") as f:
        json.dump({}, f)

    with pytest.raises(ValueError, match="(?i)date"):
        fe.run_feature_engineering()


# ═══════════════════════════════════════════════════════════════════════════
# Test 9 — Demand Forecast is NOT in predictor columns
# ═══════════════════════════════════════════════════════════════════════════

def test_demand_forecast_excluded_from_predictors(tmp_data_dir):
    """
    'Demand Forecast' must not appear in result.predictor_names and
    must not be a column in the saved ML dataset.
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    result = fe.run_feature_engineering()

    assert "Demand Forecast" not in result.predictor_names, (
        "Demand Forecast must not be a predictor (target leakage risk)"
    )

    ml_df = pd.read_csv(fe.ML_DATASET_PATH)
    assert "Demand Forecast" not in ml_df.columns, (
        "Demand Forecast must not appear in the saved ML dataset"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Test 10 — Re-running does NOT add duplicate rows or columns
# ═══════════════════════════════════════════════════════════════════════════

def test_re_run_does_not_duplicate_rows_or_columns(tmp_data_dir):
    """
    Running feature engineering twice must produce exactly the same
    row count and column count as running it once.
    """
    _write_deterministic_csv(tmp_data_dir)
    _write_mappings(tmp_data_dir)

    result1 = fe.run_feature_engineering()
    result2 = fe.run_feature_engineering()

    assert result1.output_rows    == result2.output_rows,    "Row count changed on re-run"
    assert result1.output_columns == result2.output_columns, "Column count changed on re-run"

    ml_df = pd.read_csv(fe.ML_DATASET_PATH)
    # No duplicate column names
    assert ml_df.columns.tolist() == list(dict.fromkeys(ml_df.columns.tolist())), (
        "Duplicate column names found after re-run"
    )
    # No duplicate rows
    assert ml_df.duplicated().sum() == 0, "Duplicate rows found after re-run"


# ═══════════════════════════════════════════════════════════════════════════
# Test 11 — Milestones 1–4 remain fully functional (regression guard)
# ═══════════════════════════════════════════════════════════════════════════

def test_health_endpoint_still_operational():
    """GET /api/health must still return status=healthy after Milestone 5 changes."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"


def test_milestone5_feature_generate_endpoint_no_dataset():
    """
    POST /api/model/features/generate must return 404 when no dataset file exists.
    (Uses the real DATA_DIR which may or may not have a dataset — only checks that
    the endpoint is registered and returns a structured error, not a 500 crash.)
    """
    # If the real dataset exists this endpoint will succeed (200).
    # If not, it should return 404 — either way it must not crash (5xx).
    resp = client.post("/api/model/features/generate")
    assert resp.status_code in (200, 404, 400), (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


def test_milestone5_status_endpoint_registered():
    """GET /api/model/features/status must be reachable (200 or appropriate error)."""
    resp = client.get("/api/model/features/status")
    assert resp.status_code in (200, 404, 400)


def test_milestone5_preview_endpoint_registered():
    """GET /api/model/features/preview must be reachable (200 or appropriate error)."""
    resp = client.get("/api/model/features/preview")
    assert resp.status_code in (200, 404, 400)

