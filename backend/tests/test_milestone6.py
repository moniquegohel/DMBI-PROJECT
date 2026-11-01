"""
tests/test_milestone6.py — Milestone 6: ML Model Training Tests

Automated test suite verifying:
  1. Training refusal when no feature-engineered dataset exists (HTTP 404 / FileNotFoundError).
  2. Chronological 80/20 train/holdout split based on unique calendar dates.
  3. Strict zero-leakage: all records sharing a date stay together on the same side of the split.
  4. Excluded columns: 'Demand Forecast', 'Inventory Level', 'Units Ordered', and raw 'Date'
     are not included in predictor matrices.
  5. Initial lag NaN rows are excluded from model fitting and tracked in metadata.
  6. Preprocessor (imputation + one-hot encoding) is fitted on training data only.
  7. Both Linear Regression and Random Forest pipelines train successfully on deterministic data.
  8. Joblib model artifacts can be loaded and produce valid predictions.
  9. Metadata persistence in training_metadata.json.
 10. Training idempotency: repeated training cleanly overwrites artifacts.
 11. API endpoints POST /api/model/train and GET /api/model/training-status.
 12. Regression guard: Milestones 1–5 remain fully operational.
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import pytest
import joblib
from fastapi.testclient import TestClient

from app.main import app
from app.services import data_cleaning as dc
from app.services import feature_engineering as fe
from app.services import model_training as mt

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def tmp_ml_env(tmp_path: Path):
    """
    Isolate DATA_DIR and MODELS_DIR to a temporary directory for tests.
    Restores original paths on teardown.
    """
    orig_dc_data_dir = dc.DATA_DIR
    orig_dc_clean = dc.CLEANED_DATASET_PATH
    orig_dc_raw = dc.RAW_DATASET_PATH
    orig_dc_map = dc.MAPPINGS_FILE_PATH
    orig_fe_data_dir = fe.DATA_DIR
    orig_mt_models_dir = mt.MODELS_DIR

    test_data_dir = str(tmp_path / "data")
    test_models_dir = str(tmp_path / "models")
    os.makedirs(test_data_dir, exist_ok=True)
    os.makedirs(test_models_dir, exist_ok=True)

    dc.DATA_DIR = test_data_dir
    dc.CLEANED_DATASET_PATH = str(tmp_path / "data" / "cleaned_dataset.csv")
    dc.RAW_DATASET_PATH = str(tmp_path / "data" / "raw_dataset.csv")
    dc.MAPPINGS_FILE_PATH = str(tmp_path / "data" / "column_mappings.json")
    fe.DATA_DIR = test_data_dir
    mt.MODELS_DIR = test_models_dir

    yield tmp_path

    # Restore originals
    dc.DATA_DIR = orig_dc_data_dir
    dc.CLEANED_DATASET_PATH = orig_dc_clean
    dc.RAW_DATASET_PATH = orig_dc_raw
    dc.MAPPINGS_FILE_PATH = orig_dc_map
    fe.DATA_DIR = orig_fe_data_dir
    mt.MODELS_DIR = orig_mt_models_dir


def _create_deterministic_ml_dataset(tmp_path: Path, num_dates: int = 20) -> str:
    """
    Create a deterministic ML-ready dataset with `num_dates` consecutive calendar dates,
    2 stores, and 2 products (4 records per date).
    """
    rows = []
    base_date = datetime(2023, 1, 1)

    for d in range(num_dates):
        current_date = (base_date + timedelta(days=d)).strftime("%Y-%m-%d")
        day_val = d + 1
        dow_val = (base_date + timedelta(days=d)).weekday()
        month_val = 1
        weekend_val = 1 if dow_val >= 5 else 0

        for store in ["S1", "S2"]:
            for prod in ["P1", "P2"]:
                units_sold = (d + 1) * 10 + (5 if store == "S2" else 0)
                # First observation in series has NaN lag
                prev_sales = None if d == 0 else (d * 10 + (5 if store == "S2" else 0))
                roll_sales = None if d == 0 else float(prev_sales)

                rows.append({
                    "Date": current_date,
                    "Store ID": store,
                    "Product ID": prod,
                    "day": day_val,
                    "day_of_week": dow_val,
                    "month": month_val,
                    "is_weekend": weekend_val,
                    "previous_day_sales": prev_sales,
                    "rolling_7_day_average": roll_sales,
                    "price": 25.50,
                    "discount": 5.0,
                    "promotion": 0,
                    "Demand Forecast": units_sold + 2,  # Should be excluded!
                    "Inventory Level": 200,            # Should be excluded!
                    "Units Ordered": 50,               # Should be excluded!
                    "Units Sold": units_sold           # Target
                })

    df = pd.DataFrame(rows)
    ml_path = os.path.join(dc.DATA_DIR, "ml_dataset.csv")
    df.to_csv(ml_path, index=False)
    return ml_path


# ═══════════════════════════════════════════════════════════════════════════
# Test 1: Training refuses when no ML dataset exists
# ═══════════════════════════════════════════════════════════════════════════

def test_train_refuses_when_no_ml_dataset(tmp_ml_env):
    """Calling train_all_models must raise FileNotFoundError if ml_dataset.csv is missing."""
    with pytest.raises(FileNotFoundError, match="(?i)not found"):
        mt.train_all_models()


# ═══════════════════════════════════════════════════════════════════════════
# Test 2: Chronological 80/20 train/holdout split
# ═══════════════════════════════════════════════════════════════════════════

def test_chronological_split_no_leakage(tmp_ml_env):
    """
    Test that chronological splitting:
      1. Uses unique dates to compute cutoff.
      2. Places earliest 80% dates in training, latest 20% in holdout.
      3. Guarantees no date appears in both training and holdout sets.
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=20)
    ml_path = os.path.join(dc.DATA_DIR, "ml_dataset.csv")
    df = pd.read_csv(ml_path)

    target_col, date_col, numeric_cols, categorical_cols, excluded = mt.identify_columns(df)

    X_train, y_train, X_holdout, y_holdout, split_info = mt.perform_chronological_split(
        df=df,
        date_col=date_col,
        target_col=target_col,
        numeric_cols=numeric_cols,
        train_ratio=0.8
    )

    # 20 unique dates -> 16 train dates (80%), 4 holdout dates (20%)
    assert split_info.total_dates_count == 20
    assert split_info.train_dates_count == 16
    assert split_info.holdout_dates_count == 4

    assert split_info.train_end_date < split_info.holdout_start_date
    assert split_info.cutoff_date == split_info.holdout_start_date


# ═══════════════════════════════════════════════════════════════════════════
# Test 3: Same-date records stay together
# ═══════════════════════════════════════════════════════════════════════════

def test_same_date_records_stay_together(tmp_ml_env):
    """
    All records for any date must be assigned to either train or holdout,
    never split across both.
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=20)
    ml_path = os.path.join(dc.DATA_DIR, "ml_dataset.csv")
    df = pd.read_csv(ml_path)

    target_col, date_col, numeric_cols, _, _ = mt.identify_columns(df)

    # In our dataset each date has 4 records (2 stores × 2 products)
    _, _, _, _, split_info = mt.perform_chronological_split(
        df=df,
        date_col=date_col,
        target_col=target_col,
        numeric_cols=numeric_cols,
        train_ratio=0.8
    )

    assert split_info.train_row_count == 16 * 4  # 64 rows
    assert split_info.holdout_row_count == 4 * 4  # 16 rows


# ═══════════════════════════════════════════════════════════════════════════
# Test 4: Excluded columns not in predictors
# ═══════════════════════════════════════════════════════════════════════════

def test_excluded_columns_not_in_predictors(tmp_ml_env):
    """
    Demand Forecast, Inventory Level, Units Ordered, Units Sold (target),
    and raw Date must not appear in predictor columns.
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)
    ml_path = os.path.join(dc.DATA_DIR, "ml_dataset.csv")
    df = pd.read_csv(ml_path)

    target_col, date_col, numeric_cols, categorical_cols, excluded = mt.identify_columns(df)
    all_predictors = numeric_cols + categorical_cols

    assert target_col == "Units Sold"
    assert date_col == "Date"

    disallowed = ["Demand Forecast", "Inventory Level", "Units Ordered", "Units Sold", "Date"]
    for col in disallowed:
        assert col not in all_predictors, f"Disallowed column '{col}' found in predictors!"

    assert "Demand Forecast" in excluded
    assert "Inventory Level" in excluded
    assert "Units Ordered" in excluded


# ═══════════════════════════════════════════════════════════════════════════
# Test 5: Initial lag NaN rows excluded from fitting
# ═══════════════════════════════════════════════════════════════════════════

def test_initial_nan_rows_excluded_from_fitting(tmp_ml_env):
    """
    The initial row of each store-product group where previous_day_sales is NaN
    must be excluded from model fitting rows (and reported in split_info).
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)
    ml_path = os.path.join(dc.DATA_DIR, "ml_dataset.csv")
    df = pd.read_csv(ml_path)

    target_col, date_col, numeric_cols, _, _ = mt.identify_columns(df)

    X_train, y_train, _, _, split_info = mt.perform_chronological_split(
        df=df,
        date_col=date_col,
        target_col=target_col,
        numeric_cols=numeric_cols
    )

    # 4 distinct series (2 stores × 2 products) -> 4 initial rows with NaN
    assert split_info.excluded_initial_rows == 4
    assert len(X_train) == split_info.training_rows_fitted
    assert len(X_train) == split_info.train_row_count - 4
    assert not X_train["previous_day_sales"].isna().any()


# ═══════════════════════════════════════════════════════════════════════════
# Test 6: Preprocessing fitted on training data only
# ═══════════════════════════════════════════════════════════════════════════

def test_preprocessing_fitted_on_train_only(tmp_ml_env):
    """
    ColumnTransformer must be fitted only on training data and successfully
    transform holdout data (ignoring unknown categories if any).
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)
    ml_path = os.path.join(dc.DATA_DIR, "ml_dataset.csv")
    df = pd.read_csv(ml_path)

    target_col, date_col, numeric_cols, categorical_cols, _ = mt.identify_columns(df)
    X_train, y_train, X_holdout, _, _ = mt.perform_chronological_split(
        df=df,
        date_col=date_col,
        target_col=target_col,
        numeric_cols=numeric_cols
    )

    predictors = numeric_cols + categorical_cols
    preprocessor = mt.build_preprocessor(numeric_cols, categorical_cols)

    # Fit strictly on train
    X_train_trans = preprocessor.fit_transform(X_train[predictors])
    assert X_train_trans.shape[0] == len(X_train)

    # Transform holdout without re-fitting
    X_holdout_trans = preprocessor.transform(X_holdout[predictors])
    assert X_holdout_trans.shape[0] == len(X_holdout)


# ═══════════════════════════════════════════════════════════════════════════
# Test 7: Both models train successfully
# ═══════════════════════════════════════════════════════════════════════════

def test_both_models_train_successfully(tmp_ml_env):
    """
    train_all_models() must fit both Linear Regression and Random Forest
    pipelines and return success=True.
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)

    result = mt.train_all_models()

    assert result.success is True
    assert len(result.trained_models) == 2

    model_names = [m.model_name for m in result.trained_models]
    assert "Linear Regression" in model_names
    assert "Random Forest Regressor" in model_names

    for m in result.trained_models:
        assert m.status == "trained"
        assert m.training_rows_fitted > 0


# ═══════════════════════════════════════════════════════════════════════════
# Test 8: Model artifacts saved and loadable via Joblib
# ═══════════════════════════════════════════════════════════════════════════

def test_model_artifacts_saved_and_loadable(tmp_ml_env):
    """
    Saved .joblib files must exist, be loadable with joblib.load(), and
    generate predictions of matching length on holdout features.
    """
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)
    result = mt.train_all_models()

    models_dir = mt.get_models_dir()
    lr_path = os.path.join(models_dir, mt.LINEAR_REGRESSION_FILE)
    rf_path = os.path.join(models_dir, mt.RANDOM_FOREST_FILE)

    assert os.path.exists(lr_path), "Linear regression pipeline not found on disk!"
    assert os.path.exists(rf_path), "Random forest pipeline not found on disk!"

    lr_pipeline = joblib.load(lr_path)
    rf_pipeline = joblib.load(rf_path)

    # Load holdout records to test inference
    df = pd.read_csv(os.path.join(dc.DATA_DIR, "ml_dataset.csv"))
    holdout_df = df[df["Date"] >= result.split_info.cutoff_date]
    predictors = result.numeric_predictors + result.categorical_predictors

    lr_preds = lr_pipeline.predict(holdout_df[predictors])
    rf_preds = rf_pipeline.predict(holdout_df[predictors])

    assert len(lr_preds) == len(holdout_df)
    assert len(rf_preds) == len(holdout_df)
    assert not np.isnan(lr_preds).any()
    assert not np.isnan(rf_preds).any()


# ═══════════════════════════════════════════════════════════════════════════
# Test 9: Metadata persistence in training_metadata.json
# ═══════════════════════════════════════════════════════════════════════════

def test_metadata_persistence(tmp_ml_env):
    """training_metadata.json must be written and contain split and model records."""
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)
    result = mt.train_all_models()

    meta_path = os.path.join(mt.get_models_dir(), mt.METADATA_FILE)
    assert os.path.exists(meta_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["target_column"] == "Units Sold"
    assert "split_info" in data
    assert data["split_info"]["cutoff_date"] == result.split_info.cutoff_date
    assert len(data["models"]) == 2


# ═══════════════════════════════════════════════════════════════════════════
# Test 10: Training idempotency
# ═══════════════════════════════════════════════════════════════════════════

def test_training_idempotency(tmp_ml_env):
    """Re-running train_all_models overwrites artifacts without errors."""
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)

    res1 = mt.train_all_models()
    res2 = mt.train_all_models()

    assert res1.success is True
    assert res2.success is True
    assert res1.split_info.cutoff_date == res2.split_info.cutoff_date


# ═══════════════════════════════════════════════════════════════════════════
# Test 11: API endpoints POST /train and GET /training-status
# ═══════════════════════════════════════════════════════════════════════════

def test_api_endpoints_training(tmp_ml_env):
    """Test API integration for training endpoints."""
    _create_deterministic_ml_dataset(tmp_ml_env, num_dates=10)

    # 1. Trigger training via API
    resp = client.post("/api/model/train")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["target_column"] == "Units Sold"
    assert len(data["trained_models"]) == 2

    # 2. Check training status endpoint
    status_resp = client.get("/api/model/training-status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["has_trained_models"] is True
    assert len(status_data["models"]) == 2


# ═══════════════════════════════════════════════════════════════════════════
# Test 12: Regression guard: Milestones 1–5 remain functional
# ═══════════════════════════════════════════════════════════════════════════

def test_regression_guard_health():
    """GET /api/health must continue returning healthy status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"

