"""
services/model_evaluation.py — Milestone 7: Model Evaluation and Comparison Service

Evaluates and compares the trained Linear Regression and Random Forest Regressor models
using the chronological held-out test partition (20% of unique calendar dates).

Key properties:
  - Zero leakage: models are evaluated on the reserved holdout partition without refitting.
  - Evaluation on identical records: both models are tested on the exact same test records.
  - Safe MAPE calculation: actual=0 records are excluded to prevent division-by-zero,
    and the exclusion count is reported transparently.
  - Data-driven winner determination: no hardcoded outcomes; winner is selected
    strictly by the computed error metrics.
  - Timeline aggregation: daily sums across test dates for clean, responsive frontend charting.
  - Persistence: results cached in backend/models/evaluation_results.json.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from app.services.model_training import (
    perform_chronological_split,
    identify_columns,
    MODELS_DIR,
    LINEAR_REGRESSION_FILE,
    RANDOM_FOREST_FILE,
    METADATA_FILE,
    get_models_dir,
)
from app.services.feature_engineering import get_ml_dataset_path
from app.schemas.evaluation import (
    ModelMetrics,
    ModelComparisonItem,
    TimelineDataPoint,
    MetricComparisonBar,
    ModelEvaluationResult,
    ModelEvaluationStatusResponse,
)

EVALUATION_RESULTS_FILE = "evaluation_results.json"


def get_evaluation_file_path() -> str:
    """Return the absolute path to the cached evaluation results JSON."""
    return os.path.join(get_models_dir(), EVALUATION_RESULTS_FILE)


def evaluate_models(force_recompute: bool = False) -> ModelEvaluationResult:
    """
    Evaluate trained Linear Regression and Random Forest models on the held-out test set.
    Computes MAE, RMSE, and zero-safe MAPE, determines the better model, aggregates daily
    timeline points for charting, and persists results to evaluation_results.json.
    """
    models_dir = get_models_dir()
    eval_cache_path = get_evaluation_file_path()

    # Return cached evaluation if available and not forced to recompute
    if not force_recompute and os.path.exists(eval_cache_path):
        try:
            with open(eval_cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            return ModelEvaluationResult(**cached_data)
        except Exception:
            # If cache reading/parsing fails, recompute cleanly below
            pass

    # 1. Verify ML-ready dataset exists
    ml_path = get_ml_dataset_path()
    if not os.path.exists(ml_path):
        raise FileNotFoundError(
            "ML-ready dataset ('ml_dataset.csv') not found. "
            "Please generate features and train models before performing evaluation."
        )

    # 2. Verify trained model artifacts exist
    lr_artifact_path = os.path.join(models_dir, LINEAR_REGRESSION_FILE)
    rf_artifact_path = os.path.join(models_dir, RANDOM_FOREST_FILE)

    if not os.path.exists(lr_artifact_path):
        raise FileNotFoundError(
            f"Trained Linear Regression pipeline artifact ('{LINEAR_REGRESSION_FILE}') not found. "
            "Please train the models before evaluating."
        )

    if not os.path.exists(rf_artifact_path):
        raise FileNotFoundError(
            f"Trained Random Forest pipeline artifact ('{RANDOM_FOREST_FILE}') not found. "
            "Please train the models before evaluating."
        )

    # 3. Load dataset and split chronologically
    df = pd.read_csv(ml_path)
    if len(df) == 0:
        raise ValueError("The ML-ready dataset is empty.")

    target_col, date_col, num_cols, cat_cols, _ = identify_columns(df)
    predictors = num_cols + cat_cols

    X_train, y_train, X_holdout, y_holdout, split_info = perform_chronological_split(
        df=df,
        date_col=date_col,
        target_col=target_col,
        numeric_cols=num_cols,
        train_ratio=0.8
    )

    if len(X_holdout) == 0:
        raise ValueError("Holdout test dataset is empty. Cannot perform model evaluation.")

    # 4. Load persisted model pipelines
    lr_pipeline = joblib.load(lr_artifact_path)
    rf_pipeline = joblib.load(rf_artifact_path)

    # 5. Generate predictions on the held-out test predictors
    X_test_predictors = X_holdout[predictors].copy()
    y_test_actual = y_holdout.values.astype(float)

    lr_preds = lr_pipeline.predict(X_test_predictors)
    rf_preds = rf_pipeline.predict(X_test_predictors)

    # 6. Calculate MAE and RMSE
    lr_mae = float(mean_absolute_error(y_test_actual, lr_preds))
    rf_mae = float(mean_absolute_error(y_test_actual, rf_preds))

    lr_rmse = float(root_mean_squared_error(y_test_actual, lr_preds))
    rf_rmse = float(root_mean_squared_error(y_test_actual, rf_preds))

    # 7. Calculate MAPE excluding actual == 0 records to prevent division-by-zero
    zero_actual_mask = (y_test_actual == 0)
    excluded_zero_count = int(np.sum(zero_actual_mask))
    eligible_mask = ~zero_actual_mask
    eligible_count = int(np.sum(eligible_mask))

    if eligible_count > 0:
        y_eligible = y_test_actual[eligible_mask]
        lr_mape = float(np.mean(np.abs((y_eligible - lr_preds[eligible_mask]) / y_eligible)) * 100.0)
        rf_mape = float(np.mean(np.abs((y_eligible - rf_preds[eligible_mask]) / y_eligible)) * 100.0)
    else:
        lr_mape = None
        rf_mape = None

    # 8. Model comparison & winner identification
    # Lower error is better for all metrics
    is_lr_better_mae = lr_mae < rf_mae
    is_lr_better_rmse = lr_rmse < rf_rmse
    is_lr_better_mape = (lr_mape is not None and rf_mape is not None and lr_mape < rf_mape)

    lr_win_count = sum([is_lr_better_mae, is_lr_better_rmse, is_lr_better_mape])
    rf_win_count = sum([not is_lr_better_mae, not is_lr_better_rmse, not is_lr_better_mape])

    if lr_win_count > rf_win_count:
        best_model_name = "Linear Regression"
        best_model_key = "linear_regression"
        lr_is_overall = True
        rf_is_overall = False
    elif rf_win_count > lr_win_count:
        best_model_name = "Random Forest Regressor"
        best_model_key = "random_forest"
        lr_is_overall = False
        rf_is_overall = True
    else:
        # Tie-breaker: use lower MAE
        if lr_mae <= rf_mae:
            best_model_name = "Linear Regression"
            best_model_key = "linear_regression"
            lr_is_overall = True
            rf_is_overall = False
        else:
            best_model_name = "Random Forest Regressor"
            best_model_key = "random_forest"
            lr_is_overall = False
            rf_is_overall = True

    # 9. Build metrics objects
    lr_metrics = ModelMetrics(
        mae=round(lr_mae, 4),
        rmse=round(lr_rmse, 4),
        mape=round(lr_mape, 2) if lr_mape is not None else None,
        evaluated_rows_count=len(y_test_actual),
        excluded_zero_actual_count=excluded_zero_count,
        eligible_mape_rows_count=eligible_count,
    )

    rf_metrics = ModelMetrics(
        mae=round(rf_mae, 4),
        rmse=round(rf_rmse, 4),
        mape=round(rf_mape, 2) if rf_mape is not None else None,
        evaluated_rows_count=len(y_test_actual),
        excluded_zero_actual_count=excluded_zero_count,
        eligible_mape_rows_count=eligible_count,
    )

    models_dict = {
        "linear_regression": lr_metrics,
        "random_forest": rf_metrics,
    }

    comparison_items = [
        ModelComparisonItem(
            model_name="Linear Regression",
            model_key="linear_regression",
            algorithm="LinearRegression",
            metrics=lr_metrics,
            is_winner_mae=is_lr_better_mae,
            is_winner_rmse=is_lr_better_rmse,
            is_winner_mape=is_lr_better_mape,
            is_overall_winner=lr_is_overall,
        ),
        ModelComparisonItem(
            model_name="Random Forest Regressor",
            model_key="random_forest",
            algorithm="RandomForestRegressor",
            metrics=rf_metrics,
            is_winner_mae=not is_lr_better_mae,
            is_winner_rmse=not is_lr_better_rmse,
            is_winner_mape=not is_lr_better_mape,
            is_overall_winner=rf_is_overall,
        ),
    ]

    # 10. Summary table for display
    summary_table = [
        {
            "metric": "MAE",
            "metric_name": "Mean Absolute Error",
            "description": "Average difference between actual and predicted demand",
            "unit": "Units Sold",
            "linear_regression": round(lr_mae, 2),
            "random_forest": round(rf_mae, 2),
            "difference": round(abs(lr_mae - rf_mae), 2),
            "better_model": "Linear Regression" if is_lr_better_mae else "Random Forest Regressor",
            "percentage_difference": round(abs(lr_mae - rf_mae) / min(lr_mae, rf_mae) * 100, 1),
        },
        {
            "metric": "RMSE",
            "metric_name": "Root Mean Squared Error",
            "description": "Error metric giving greater weight to large prediction misses",
            "unit": "Units Sold",
            "linear_regression": round(lr_rmse, 2),
            "random_forest": round(rf_rmse, 2),
            "difference": round(abs(lr_rmse - rf_rmse), 2),
            "better_model": "Linear Regression" if is_lr_better_rmse else "Random Forest Regressor",
            "percentage_difference": round(abs(lr_rmse - rf_rmse) / min(lr_rmse, rf_rmse) * 100, 1),
        },
        {
            "metric": "MAPE",
            "metric_name": "Mean Absolute Percentage Error",
            "description": f"Percentage deviation from actual demand (excludes {excluded_zero_count} zero-demand days)",
            "unit": "%",
            "linear_regression": round(lr_mape, 2) if lr_mape is not None else None,
            "random_forest": round(rf_mape, 2) if rf_mape is not None else None,
            "difference": round(abs(lr_mape - rf_mape), 2) if lr_mape is not None and rf_mape is not None else None,
            "better_model": ("Linear Regression" if is_lr_better_mape else "Random Forest Regressor") if lr_mape is not None else "N/A",
            "percentage_difference": round(abs(lr_mape - rf_mape) / min(lr_mape, rf_mape) * 100, 1) if lr_mape is not None and rf_mape is not None else None,
        },
    ]

    # 11. Metric comparison bars for chart
    metric_comparison_chart = [
        MetricComparisonBar(
            metric="MAE",
            metric_label="Mean Absolute Error (Units)",
            linear_regression=round(lr_mae, 2),
            random_forest=round(rf_mae, 2),
            better_model="Linear Regression" if is_lr_better_mae else "Random Forest Regressor",
            unit="Units Sold",
        ),
        MetricComparisonBar(
            metric="RMSE",
            metric_label="Root Mean Squared Error (Units)",
            linear_regression=round(lr_rmse, 2),
            random_forest=round(rf_rmse, 2),
            better_model="Linear Regression" if is_lr_better_rmse else "Random Forest Regressor",
            unit="Units Sold",
        ),
        MetricComparisonBar(
            metric="MAPE",
            metric_label="Mean Absolute Percentage Error (%)",
            linear_regression=round(lr_mape, 2) if lr_mape is not None else 0.0,
            random_forest=round(rf_mape, 2) if rf_mape is not None else 0.0,
            better_model=("Linear Regression" if is_lr_better_mape else "Random Forest Regressor") if lr_mape is not None else "N/A",
            unit="%",
        ),
    ]

    # 12. Daily timeline aggregation for chart
    # Groups test records by date to provide total daily actual demand vs predictions
    holdout_dates = pd.to_datetime(df.loc[X_holdout.index, date_col]).dt.strftime("%Y-%m-%d")
    timeline_df = pd.DataFrame({
        "date": holdout_dates.values,
        "actual": y_test_actual,
        "linear_regression": lr_preds,
        "random_forest": rf_preds,
    })

    daily_grouped = timeline_df.groupby("date").sum().reset_index()
    daily_timeline = [
        TimelineDataPoint(
            date=str(row["date"]),
            actual=round(float(row["actual"]), 1),
            linear_regression=round(float(row["linear_regression"]), 1),
            random_forest=round(float(row["random_forest"]), 1),
        )
        for _, row in daily_grouped.iterrows()
    ]

    # 13. Plain-language business interpretation
    if lr_win_count == 3:
        interpretation = (
            f"Linear Regression outperformed Random Forest across all three accuracy metrics "
            f"(MAE: {lr_mae:.2f} vs {rf_mae:.2f} units, RMSE: {lr_rmse:.2f} vs {rf_rmse:.2f} units, "
            f"MAPE: {lr_mape:.2f}% vs {rf_mape:.2f}%). "
            f"The linear model provides a more reliable and stable demand baseline on unseen future dates "
            f"without overfitting to noise. It is recommended for retail inventory planning."
        )
    elif rf_win_count == 3:
        interpretation = (
            f"Random Forest Regressor outperformed Linear Regression across all three accuracy metrics "
            f"(MAE: {rf_mae:.2f} vs {lr_mae:.2f} units, RMSE: {rf_rmse:.2f} vs {lr_rmse:.2f} units, "
            f"MAPE: {rf_mape:.2f}% vs {lr_mape:.2f}%). "
            f"The ensemble tree model captured non-linear product interactions and store variations better "
            f"than the linear baseline."
        )
    else:
        interpretation = (
            f"Evaluation produced mixed results across metrics: "
            f"Linear Regression had an MAE of {lr_mae:.2f} and RMSE of {lr_rmse:.2f}, while "
            f"Random Forest had an MAE of {rf_mae:.2f} and RMSE of {rf_rmse:.2f}. "
            f"Overall, {best_model_name} demonstrated the stronger aggregate performance."
        )

    # 14. Build test period metadata
    test_period_meta = {
        "start_date": split_info.holdout_start_date,
        "end_date": split_info.holdout_end_date,
        "cutoff_date": split_info.cutoff_date,
        "total_test_dates": split_info.holdout_dates_count,
        "total_test_rows": len(y_test_actual),
        "eligible_mape_rows": eligible_count,
        "excluded_zero_actual_count": excluded_zero_count,
    }

    timestamp = datetime.utcnow().isoformat()
    result = ModelEvaluationResult(
        success=True,
        evaluation_timestamp=timestamp,
        test_period=test_period_meta,
        models=models_dict,
        comparison=comparison_items,
        summary_table=summary_table,
        metric_comparison_chart=metric_comparison_chart,
        daily_timeline=daily_timeline,
        best_model=best_model_name,
        best_model_key=best_model_key,
        interpretation=interpretation,
    )

    # 15. Cache evaluation results to disk
    try:
        with open(eval_cache_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)
    except Exception as exc:
        # Non-fatal if caching fails
        print(f"Warning: Could not cache evaluation results to {eval_cache_path}: {exc}")

    return result


def get_evaluation_status() -> ModelEvaluationStatusResponse:
    """
    Check whether model evaluation results are available on disk or if models are ready
    to be evaluated.
    """
    models_dir = get_models_dir()
    eval_cache_path = get_evaluation_file_path()
    meta_path = os.path.join(models_dir, METADATA_FILE)

    has_models = os.path.exists(meta_path)
    has_eval = os.path.exists(eval_cache_path)

    if not has_models:
        return ModelEvaluationStatusResponse(
            has_evaluation=False,
            has_models=False,
            message="No models have been trained yet. Train models in Sales Prediction to enable evaluation.",
            evaluation=None,
        )

    if has_eval:
        try:
            with open(eval_cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_eval = ModelEvaluationResult(**data)
            return ModelEvaluationStatusResponse(
                has_evaluation=True,
                has_models=True,
                message="Model evaluation results are ready.",
                evaluation=cached_eval,
            )
        except Exception:
            pass

    return ModelEvaluationStatusResponse(
        has_evaluation=False,
        has_models=True,
        message="Models are trained but evaluation has not yet been computed.",
        evaluation=None,
    )

