"""
schemas/evaluation.py — Pydantic models for Milestone 7: Model Evaluation and Comparison.

Defines schemas for:
  - Individual model evaluation metrics (MAE, RMSE, MAPE)
  - Comparison items comparing Linear Regression vs. Random Forest Regressor
  - Chart visualization payloads (Timeline actual vs. predicted, Performance comparison bars)
  - Comprehensive model evaluation response and status
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    """Regression accuracy metrics computed on the held-out test dataset."""
    mae: float = Field(..., description="Mean Absolute Error in units sold")
    rmse: float = Field(..., description="Root Mean Squared Error in units sold")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (%)")
    evaluated_rows_count: int = Field(..., description="Total holdout test records evaluated")
    excluded_zero_actual_count: int = Field(0, description="Records with actual demand == 0 excluded from MAPE")
    eligible_mape_rows_count: int = Field(..., description="Records eligible for MAPE calculation")


class ModelComparisonItem(BaseModel):
    """Side-by-side comparison metadata and winner flags for a single model."""
    model_name: str = Field(..., description="Display name of the model")
    model_key: str = Field(..., description="Unique model key, e.g. 'linear_regression'")
    algorithm: str = Field(..., description="Underlying algorithm class name")
    metrics: ModelMetrics = Field(..., description="Accuracy metrics on holdout test set")
    is_winner_mae: bool = Field(False, description="Whether this model achieved the lowest MAE")
    is_winner_rmse: bool = Field(False, description="Whether this model achieved the lowest RMSE")
    is_winner_mape: bool = Field(False, description="Whether this model achieved the lowest MAPE")
    is_overall_winner: bool = Field(False, description="Whether this model is recommended as overall best")


class TimelineDataPoint(BaseModel):
    """Daily aggregated actual demand and predictions for time-series visualization."""
    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    actual: float = Field(..., description="Total actual units sold across all series on this date")
    linear_regression: float = Field(..., description="Total predicted units sold by Linear Regression")
    random_forest: float = Field(..., description="Total predicted units sold by Random Forest")


class MetricComparisonBar(BaseModel):
    """Chart data point for comparing error metrics across both models."""
    metric: str = Field(..., description="Metric identifier, e.g. 'MAE'")
    metric_label: str = Field(..., description="User-friendly metric name")
    linear_regression: float = Field(..., description="Value for Linear Regression")
    random_forest: float = Field(..., description="Value for Random Forest")
    better_model: str = Field(..., description="Name of the model with the lower error")
    unit: str = Field(..., description="Unit of measurement ('Units Sold' or '%')")


class ModelEvaluationResult(BaseModel):
    """Comprehensive response object for Milestone 7: Model Evaluation and Comparison."""
    success: bool = Field(..., description="Whether evaluation completed successfully")
    evaluation_timestamp: str = Field(..., description="ISO timestamp when evaluation was performed")
    test_period: Dict[str, Any] = Field(
        ...,
        description="Metadata describing the held-out test partition (start date, end date, row counts)"
    )
    models: Dict[str, ModelMetrics] = Field(..., description="Metrics keyed by model identifier")
    comparison: List[ModelComparisonItem] = Field(..., description="Detailed comparison per model")
    summary_table: List[Dict[str, Any]] = Field(..., description="Formatted comparison table rows")
    metric_comparison_chart: List[MetricComparisonBar] = Field(..., description="Chart series for metric comparison")
    daily_timeline: List[TimelineDataPoint] = Field(..., description="Daily actual vs predicted chart points")
    best_model: str = Field(..., description="Display name of the overall winning model")
    best_model_key: str = Field(..., description="Key of the overall winning model")
    interpretation: str = Field(..., description="Plain-language business explanation of the results")


class ModelEvaluationStatusResponse(BaseModel):
    """Status check indicating whether models are trained and evaluation results exist."""
    has_evaluation: bool = Field(..., description="Whether evaluation results are ready")
    has_models: bool = Field(..., description="Whether trained models exist on disk")
    message: str = Field("", description="Status description")
    evaluation: Optional[ModelEvaluationResult] = Field(None, description="Cached evaluation results if available")

