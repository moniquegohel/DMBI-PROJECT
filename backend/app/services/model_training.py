"""
services/model_training.py — Milestone 6: ML Model Training Service

Trains and persists two supervised regression pipelines:
  1. Linear Regression (Scikit-learn LinearRegression)
  2. Random Forest Regression (Scikit-learn RandomForestRegressor)

Core requirements:
  - Predicts 'Units Sold' using only valid predictors available at prediction time.
  - Chronological 80/20 train/holdout split based on unique calendar dates.
  - Zero target leakage: all rows sharing a date stay together; preprocessing
    transformers are fitted STRICTLY on the training period.
  - Excluded columns: 'Demand Forecast', 'Inventory Level', 'Units Ordered', raw 'Date'.
  - Initial rows in each store-product group where lag features are NaN are
    excluded from model fitting (reported transparently in split metadata).
  - Both fitted pipelines (preprocessor + estimator) are serialized via Joblib
    into backend/models/ alongside training_metadata.json.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from app.services.feature_engineering import get_ml_dataset_path
from app.schemas.model import (
    TrainedModelInfo,
    DateSplitInfo,
    ModelTrainingResult,
    ModelTrainingStatusResponse,
)

# Base models storage directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Standard artifact filenames
LINEAR_REGRESSION_FILE = "linear_regression_pipeline.joblib"
RANDOM_FOREST_FILE = "random_forest_pipeline.joblib"
METADATA_FILE = "training_metadata.json"


def get_models_dir() -> str:
    """Return the active models directory path, ensuring it exists."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    return MODELS_DIR


# ---------------------------------------------------------------------------
# Column & Preprocessing Helpers
# ---------------------------------------------------------------------------

EXCLUDED_COLUMN_PATTERNS = [
    "demand forecast",
    "forecast",
    "inventory level",
    "inventorylevel",
    "units ordered",
    "unitsordered",
]


def identify_columns(df: pd.DataFrame) -> Tuple[str, str, List[str], List[str], Dict[str, str]]:
    """
    Classify DataFrame columns into target, date column, numeric predictors,
    categorical predictors, and explicitly excluded columns.
    """
    # 1. Target column (Units Sold)
    target_col = None
    for col in df.columns:
        norm = str(col).lower().replace(" ", "").replace("_", "")
        if norm in ["unitssold", "quantitysold", "sales"]:
            target_col = col
            break
    if not target_col:
        # Fallback to column named 'Units Sold' if present
        if "Units Sold" in df.columns:
            target_col = "Units Sold"
        else:
            raise ValueError("Target column 'Units Sold' could not be found in the ML dataset.")

    # 2. Date column (used for chronological split, not as a numeric feature)
    date_col = None
    for col in df.columns:
        if str(col).lower() in ["date", "saledate", "sale_date", "transaction_date"]:
            date_col = col
            break
    if not date_col:
        raise ValueError("Transaction date column could not be found in the ML dataset.")

    # 3. Identify excluded columns
    excluded: Dict[str, str] = {}
    candidate_cols = []

    for col in df.columns:
        if col == target_col:
            continue
        if col == date_col:
            continue

        col_lower = str(col).lower()
        if "demand forecast" in col_lower or ("forecast" in col_lower and "demand" in col_lower):
            excluded[str(col)] = "Excluded: Demand Forecast has ~0.997 target correlation and 673 negative values (target leakage)."
            continue
        if "inventory level" in col_lower or "inventorylevel" in col_lower:
            excluded[str(col)] = "Excluded: Inventory Level reflects post-sale end-of-day stock (unavailable at prediction time)."
            continue
        if "units ordered" in col_lower or "unitsordered" in col_lower:
            excluded[str(col)] = "Excluded: Units Ordered is a replenishment order placed in response to today's sales (future-facing)."
            continue

        candidate_cols.append(col)

    # 4. Separate remaining candidates into numeric and categorical predictors
    numeric_cols: List[str] = []
    categorical_cols: List[str] = []

    for col in candidate_cols:
        series = df[col]
        # Treat columns with object or string type as categorical
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            categorical_cols.append(str(col))
        elif pd.api.types.is_numeric_dtype(series):
            # Check if it is Store ID or Product ID encoded as integer (still categorical identifiers)
            col_clean = str(col).lower().replace(" ", "").replace("_", "")
            if col_clean in ["storeid", "productid"]:
                categorical_cols.append(str(col))
            else:
                numeric_cols.append(str(col))
        else:
            categorical_cols.append(str(col))

    return target_col, date_col, numeric_cols, categorical_cols, excluded


def build_preprocessor(numeric_cols: List[str], categorical_cols: List[str]) -> ColumnTransformer:
    """
    Build a Scikit-learn ColumnTransformer for mixed tabular data.
    - Numeric: Median imputation
    - Categorical: Most-frequent imputation + One-Hot Encoding (unknowns ignored)
    """
    transformers = []

    if numeric_cols:
        num_transformer = SimpleImputer(strategy="median")
        transformers.append(("numeric", num_transformer, numeric_cols))

    if categorical_cols:
        cat_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])
        transformers.append(("categorical", cat_transformer, categorical_cols))

    if not transformers:
        raise ValueError("No eligible predictor columns found to build preprocessor.")

    return ColumnTransformer(transformers=transformers)


# ---------------------------------------------------------------------------
# Chronological Train / Holdout Split
# ---------------------------------------------------------------------------

def perform_chronological_split(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    numeric_cols: List[str],
    train_ratio: float = 0.8
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, DateSplitInfo]:
    """
    Split the dataset chronologically based on unique calendar dates.
    - Sorts unique dates in ascending order.
    - Earliest ~80% unique dates become the Training set.
    - Latest ~20% unique dates become the Holdout set (reserved for Milestone 7).
    - All rows sharing the same calendar date remain together on the same side.
    - Initial rows where lag features (e.g. 'previous_day_sales') are NaN
      are excluded from training model fitting.
    """
    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    if parsed_dates.isna().all():
        raise ValueError(f"Could not parse any valid dates in column '{date_col}'.")

    # Format dates as YYYY-MM-DD for deterministic date-level grouping
    df_dates = parsed_dates.dt.strftime("%Y-%m-%d")
    unique_dates = sorted(df_dates.dropna().unique())

    if len(unique_dates) < 5:
        raise ValueError(
            f"Dataset has only {len(unique_dates)} unique dates. "
            "At least 5 distinct dates are required for a chronological train/holdout split."
        )

    # Compute cutoff index (80th percentile of dates)
    split_idx = int(len(unique_dates) * train_ratio)
    split_idx = max(1, min(split_idx, len(unique_dates) - 1))  # Ensure both sets have >= 1 date

    cutoff_date = unique_dates[split_idx]
    train_dates = unique_dates[:split_idx]
    holdout_dates = unique_dates[split_idx:]

    train_mask = df_dates < cutoff_date
    holdout_mask = df_dates >= cutoff_date

    raw_train_df = df[train_mask].copy()
    raw_holdout_df = df[holdout_mask].copy()

    # Identify initial rows in training set where required lag features are NaN
    # (e.g., previous_day_sales is NaN for the first day of each series)
    fitting_mask = pd.Series(True, index=raw_train_df.index)
    if "previous_day_sales" in raw_train_df.columns:
        fitting_mask = fitting_mask & raw_train_df["previous_day_sales"].notna()
    if "rolling_7_day_average" in raw_train_df.columns:
        fitting_mask = fitting_mask & raw_train_df["rolling_7_day_average"].notna()

    # Filter out initial lag NaN rows from model fitting
    fit_train_df = raw_train_df[fitting_mask].copy()
    excluded_count = int(len(raw_train_df) - len(fit_train_df))

    # Also drop rows where target is NaN (if any exist)
    target_valid_mask = fit_train_df[target_col].notna()
    fit_train_df = fit_train_df[target_valid_mask]

    X_train = fit_train_df.drop(columns=[target_col, date_col], errors="ignore")
    y_train = pd.to_numeric(fit_train_df[target_col], errors="coerce")

    X_holdout = raw_holdout_df.drop(columns=[target_col, date_col], errors="ignore")
    y_holdout = pd.to_numeric(raw_holdout_df[target_col], errors="coerce")

    split_info = DateSplitInfo(
        cutoff_date=cutoff_date,
        train_start_date=train_dates[0],
        train_end_date=train_dates[-1],
        holdout_start_date=holdout_dates[0],
        holdout_end_date=holdout_dates[-1],
        total_dates_count=len(unique_dates),
        train_dates_count=len(train_dates),
        holdout_dates_count=len(holdout_dates),
        train_row_count=int(len(raw_train_df)),
        holdout_row_count=int(len(raw_holdout_df)),
        excluded_initial_rows=excluded_count,
        training_rows_fitted=int(len(fit_train_df)),
    )

    return X_train, y_train, X_holdout, y_holdout, split_info


# ---------------------------------------------------------------------------
# Training Orchestration
# ---------------------------------------------------------------------------

def train_all_models() -> ModelTrainingResult:
    """
    Execute chronological splitting and train both Linear Regression and
    Random Forest Regressor pipelines on the active ML dataset.
    Saves trained pipelines as Joblib artifacts in backend/models/.
    """
    ml_path = get_ml_dataset_path()
    if not os.path.exists(ml_path):
        raise FileNotFoundError(
            "ML-ready dataset ('ml_dataset.csv') not found. "
            "Please generate features on the Model Training page before training models."
        )

    df = pd.read_csv(ml_path)
    if len(df) == 0:
        raise ValueError("The ML-ready dataset is empty.")

    # 1. Identify columns
    target_col, date_col, numeric_cols, categorical_cols, excluded = identify_columns(df)
    total_predictors = numeric_cols + categorical_cols

    # 2. Chronological 80/20 train/holdout split
    X_train, y_train, X_holdout, y_holdout, split_info = perform_chronological_split(
        df=df,
        date_col=date_col,
        target_col=target_col,
        numeric_cols=numeric_cols,
        train_ratio=0.8
    )

    # Select only predictor columns for training
    X_train_predictors = X_train[total_predictors].copy()

    # 3. Build preprocessing pipeline
    preprocessor = build_preprocessor(numeric_cols, categorical_cols)

    trained_models: List[TrainedModelInfo] = []
    models_dir = get_models_dir()

    # -----------------------------------------------------------------------
    # Model A: Linear Regression
    # -----------------------------------------------------------------------
    try:
        lr_estimator = LinearRegression()
        lr_pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("regressor", lr_estimator)
        ])
        lr_pipeline.fit(X_train_predictors, y_train)

        lr_artifact_path = os.path.join(models_dir, LINEAR_REGRESSION_FILE)
        joblib.dump(lr_pipeline, lr_artifact_path)

        trained_models.append(
            TrainedModelInfo(
                model_name="Linear Regression",
                model_key="linear_regression",
                algorithm="LinearRegression",
                status="trained",
                training_rows_fitted=len(X_train_predictors),
                parameters={"fit_intercept": True, "copy_X": True},
                artifact_filename=LINEAR_REGRESSION_FILE,
            )
        )
    except Exception as exc:
        trained_models.append(
            TrainedModelInfo(
                model_name="Linear Regression",
                model_key="linear_regression",
                algorithm="LinearRegression",
                status="failed",
                training_rows_fitted=0,
                parameters={},
                artifact_filename=LINEAR_REGRESSION_FILE,
                error_message=str(exc)
            )
        )

    # -----------------------------------------------------------------------
    # Model B: Random Forest Regressor
    # -----------------------------------------------------------------------
    try:
        rf_params = {
            "n_estimators": 100,
            "random_state": 42,
            "max_depth": None,
            "min_samples_split": 2,
            "n_jobs": -1
        }
        rf_estimator = RandomForestRegressor(**rf_params)
        rf_pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("regressor", rf_estimator)
        ])
        rf_pipeline.fit(X_train_predictors, y_train)

        rf_artifact_path = os.path.join(models_dir, RANDOM_FOREST_FILE)
        joblib.dump(rf_pipeline, rf_artifact_path)

        trained_models.append(
            TrainedModelInfo(
                model_name="Random Forest Regressor",
                model_key="random_forest",
                algorithm="RandomForestRegressor",
                status="trained",
                training_rows_fitted=len(X_train_predictors),
                parameters={
                    "n_estimators": rf_params["n_estimators"],
                    "random_state": rf_params["random_state"],
                    "n_jobs": rf_params["n_jobs"]
                },
                artifact_filename=RANDOM_FOREST_FILE,
            )
        )
    except Exception as exc:
        trained_models.append(
            TrainedModelInfo(
                model_name="Random Forest Regressor",
                model_key="random_forest",
                algorithm="RandomForestRegressor",
                status="failed",
                training_rows_fitted=0,
                parameters={},
                artifact_filename=RANDOM_FOREST_FILE,
                error_message=str(exc)
            )
        )

    # 4. Save metadata sidecar JSON
    timestamp = datetime.utcnow().isoformat()
    metadata_payload = {
        "timestamp": timestamp,
        "target_column": target_col,
        "date_column": date_col,
        "numeric_predictors": numeric_cols,
        "categorical_predictors": categorical_cols,
        "excluded_columns": excluded,
        "split_info": split_info.model_dump(),
        "models": [m.model_dump() for m in trained_models]
    }
    with open(os.path.join(models_dir, METADATA_FILE), "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2)

    all_trained = all(m.status == "trained" for m in trained_models)
    msg = (
        f"Model training completed. Fitted {len(trained_models)} models "
        f"on {split_info.training_rows_fitted:,} chronological training records. "
        f"Reserved {split_info.holdout_row_count:,} holdout records for Milestone 7 evaluation."
    ) if all_trained else "One or more models failed during training. See model statuses for details."

    return ModelTrainingResult(
        success=all_trained,
        message=msg,
        target_column=target_col,
        numeric_predictors=numeric_cols,
        categorical_predictors=categorical_cols,
        total_predictors_count=len(total_predictors),
        excluded_columns=excluded,
        split_info=split_info,
        trained_models=trained_models,
        training_timestamp=timestamp
    )


def get_training_status() -> ModelTrainingStatusResponse:
    """
    Inspect whether trained model artifacts exist on disk and read their metadata.
    Avoids re-running training when the user merely inspects the page.
    """
    models_dir = get_models_dir()
    meta_path = os.path.join(models_dir, METADATA_FILE)

    if not os.path.exists(meta_path):
        return ModelTrainingStatusResponse(
            has_trained_models=False,
            message="No models have been trained yet. Click 'Train Models' to begin.",
            models=[]
        )

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if actual joblib files exist
        models_list: List[TrainedModelInfo] = []
        for m in data.get("models", []):
            art_file = m.get("artifact_filename")
            art_exists = os.path.exists(os.path.join(models_dir, art_file)) if art_file else False
            status = m.get("status") if art_exists else "failed"
            models_list.append(
                TrainedModelInfo(
                    model_name=m.get("model_name", "Unknown"),
                    model_key=m.get("model_key", "unknown"),
                    algorithm=m.get("algorithm", "Unknown"),
                    status=status,
                    training_rows_fitted=m.get("training_rows_fitted", 0),
                    parameters=m.get("parameters", {}),
                    artifact_filename=art_file or "",
                    error_message=m.get("error_message")
                )
            )

        split_dict = data.get("split_info")
        split_obj = DateSplitInfo(**split_dict) if split_dict else None

        has_trained = any(m.status == "trained" for m in models_list)

        return ModelTrainingStatusResponse(
            has_trained_models=has_trained,
            models=models_list,
            target_column=data.get("target_column"),
            split_info=split_obj,
            training_timestamp=data.get("timestamp"),
            message="Models are trained and saved on the server. Ready for Milestone 7 evaluation." if has_trained else "Artifacts missing or corrupted."
        )
    except Exception as exc:
        return ModelTrainingStatusResponse(
            has_trained_models=False,
            message=f"Could not load training metadata: {str(exc)}",
            models=[]
        )

