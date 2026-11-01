"""
schemas/model.py — Pydantic models for Milestone 6: ML Model Training.

Defines schemas for:
  - Trained model information (algorithm, parameters, status, artifact file)
  - Chronological 80/20 train/holdout date split metadata
  - Model training result response
  - Model training status response
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TrainedModelInfo(BaseModel):
    """Metadata describing a single trained machine learning model pipeline."""
    model_name: str = Field(..., description="Display name of the model, e.g. 'Linear Regression'")
    model_key: str = Field(..., description="Unique key identifier, e.g. 'linear_regression'")
    algorithm: str = Field(..., description="Underlying algorithm class, e.g. 'LinearRegression'")
    status: str = Field(..., description="Training status: 'trained' or 'failed'")
    training_rows_fitted: int = Field(0, description="Number of eligible training rows used for fitting")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Key hyperparameters used")
    artifact_filename: str = Field(..., description="Saved joblib pipeline filename")
    error_message: Optional[str] = Field(None, description="Error message if training failed")


class DateSplitInfo(BaseModel):
    """Details of the chronological 80/20 train/holdout split."""
    cutoff_date: str = Field(..., description="Date demarcating the 80% train vs 20% holdout split (YYYY-MM-DD)")
    train_start_date: str = Field(..., description="Earliest date in training portion")
    train_end_date: str = Field(..., description="Latest date in training portion (< cutoff_date)")
    holdout_start_date: str = Field(..., description="Earliest date in holdout portion (>= cutoff_date)")
    holdout_end_date: str = Field(..., description="Latest date in holdout portion")
    total_dates_count: int = Field(0, description="Total unique calendar dates in dataset")
    train_dates_count: int = Field(0, description="Unique dates allocated to training set (~80%)")
    holdout_dates_count: int = Field(0, description="Unique dates allocated to holdout set (~20%)")
    train_row_count: int = Field(0, description="Total raw rows falling within the training date range")
    holdout_row_count: int = Field(0, description="Total raw rows falling within the holdout date range")
    excluded_initial_rows: int = Field(
        0,
        description="Number of training rows excluded from fitting because lag features are NaN (e.g. initial rows per series)"
    )
    training_rows_fitted: int = Field(0, description="Net rows actually used to fit the models (train_row_count - excluded)")


class ModelTrainingResult(BaseModel):
    """Response returned upon completion of model training."""
    success: bool = Field(..., description="Whether training process completed successfully")
    message: str = Field(..., description="Human-readable status summary")
    target_column: str = Field(..., description="Target variable name, e.g. 'Units Sold'")
    numeric_predictors: List[str] = Field(default_factory=list, description="List of numeric features used")
    categorical_predictors: List[str] = Field(default_factory=list, description="List of categorical features used")
    total_predictors_count: int = Field(0, description="Total number of predictor features")
    excluded_columns: Dict[str, str] = Field(default_factory=dict, description="Columns excluded and reasons")
    split_info: DateSplitInfo = Field(..., description="Chronological 80/20 split metadata")
    trained_models: List[TrainedModelInfo] = Field(default_factory=list, description="Summary of each trained model")
    training_timestamp: str = Field(..., description="ISO timestamp when training was executed")


class ModelTrainingStatusResponse(BaseModel):
    """Response returned when querying current training status without re-training."""
    has_trained_models: bool = Field(..., description="Whether trained model artifacts exist on disk")
    models: List[TrainedModelInfo] = Field(default_factory=list, description="List of available models")
    target_column: Optional[str] = Field(None, description="Target variable name")
    split_info: Optional[DateSplitInfo] = Field(None, description="Cached chronological split details")
    training_timestamp: Optional[str] = Field(None, description="Timestamp of latest training execution")
    message: str = Field("", description="Status description")

