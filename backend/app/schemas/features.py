"""
schemas/features.py — Pydantic response models for Milestone 5 Feature Engineering.

These models define the shape of API responses for:
  - Feature generation status and summary
  - Feature preview (first 10 rows)
  - Feature metadata (predictor / metadata / target classification)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FeatureColumnInfo(BaseModel):
    """Describes a single column in the feature-engineered dataset."""
    name: str = Field(..., description="Column name in the ML dataset")
    role: str = Field(
        ...,
        description="Role of this column: 'predictor', 'metadata', or 'target'"
    )
    description: str = Field(..., description="Human-readable explanation of the column")
    null_count: int = Field(
        0,
        description="Number of rows where this column is null/NaN (expected for initial lag rows)"
    )


class FeatureEngineeringResult(BaseModel):
    """
    Full result returned after running feature engineering.
    Contains status, counts, column catalogue, and a 10-row preview.
    """
    success: bool = Field(..., description="Whether feature generation succeeded")
    message: str = Field(..., description="Human-readable status message")

    # Dataset dimensions
    input_rows: int = Field(0, description="Number of rows in the cleaned source dataset")
    output_rows: int = Field(0, description="Number of rows in the ML dataset (same as input)")
    output_columns: int = Field(0, description="Total columns in the ML dataset")

    # Column catalogue
    feature_columns: List[FeatureColumnInfo] = Field(
        default_factory=list,
        description="All columns with role classification and null counts"
    )
    predictor_names: List[str] = Field(
        default_factory=list,
        description="Names of columns used as predictors (input features for ML models)"
    )
    metadata_names: List[str] = Field(
        default_factory=list,
        description="Names of identifier/metadata columns kept for interpretation"
    )
    target_name: Optional[str] = Field(
        None,
        description="Name of the target column (units_sold) for demand forecasting"
    )

    # Lag/rolling NaN counts
    previous_day_sales_nulls: int = Field(
        0,
        description="Number of rows where previous_day_sales is null (first row of each group)"
    )
    rolling_7_day_avg_nulls: int = Field(
        0,
        description=(
            "Number of rows where rolling_7_day_average is null "
            "(first 1–7 rows of each group, depending on series length)"
        )
    )

    # Excluded columns and reasons
    excluded_columns: Dict[str, str] = Field(
        default_factory=dict,
        description="Columns excluded from predictors and the reason for each exclusion"
    )

    # 10-row preview
    preview_rows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="First 10 rows of the feature-engineered dataset as JSON records"
    )

    # Day-of-week encoding note
    day_of_week_encoding: str = Field(
        "Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6",
        description="Encoding used for the day_of_week feature"
    )
    is_weekend_encoding: str = Field(
        "0=weekday (Mon–Fri), 1=weekend (Sat or Sun)",
        description="Encoding used for the is_weekend feature"
    )


class FeatureEngineeringStatus(BaseModel):
    """
    Lightweight status response — does the ML dataset exist?
    Used by the frontend to show the correct initial state.
    """
    has_ml_dataset: bool = Field(
        ...,
        description="True when a feature-engineered ML dataset file exists on disk"
    )
    ml_dataset_rows: Optional[int] = Field(
        None,
        description="Row count of the existing ML dataset"
    )
    ml_dataset_columns: Optional[int] = Field(
        None,
        description="Column count of the existing ML dataset"
    )
    message: str = Field("", description="Short status description")

