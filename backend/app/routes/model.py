"""
routes/model.py — Milestone 5: Feature Engineering API endpoints.

This module exposes the feature engineering step through the existing FastAPI
application.  Model training endpoints (Milestone 6) will be added here later.

Routes:
  POST /api/model/features/generate  — run feature engineering, save ML dataset
  GET  /api/model/features/status    — check whether ML dataset already exists
  GET  /api/model/features/preview   — return a summary + 10-row preview of the
                                       most recently generated ML dataset

Conventions:
  - Service logic lives in app.services.feature_engineering.
  - Pydantic response models live in app.schemas.features.
  - Errors are mapped to appropriate HTTP status codes; no stack traces exposed.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.features import FeatureEngineeringResult, FeatureEngineeringStatus
from app.services.feature_engineering import (
    run_feature_engineering,
    get_feature_engineering_status,
)
from app.schemas.model import (
    ModelTrainingResult,
    ModelTrainingStatusResponse,
)
from app.services.model_training import (
    train_all_models,
    get_training_status,
)

router = APIRouter()


@router.post(
    "/features/generate",
    response_model=FeatureEngineeringResult,
    summary="Generate ML Features",
    description=(
        "Run feature engineering on the active cleaned dataset. "
        "Creates date features (day, day_of_week, month, is_weekend) and "
        "leakage-safe lag/rolling sales features (previous_day_sales, "
        "rolling_7_day_average) computed within each store-product group. "
        "Result is saved to backend/data/ml_dataset.csv."
    ),
)
def generate_features():
    """
    Trigger feature engineering and return the full result including
    column catalogue, NaN counts, and a 10-row preview.
    """
    try:
        return run_feature_engineering()

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"An unexpected error occurred during feature engineering: {exc!s}. "
                "Please check the backend logs."
            ),
        )


@router.get(
    "/features/status",
    response_model=FeatureEngineeringStatus,
    summary="Feature Engineering Status",
    description=(
        "Check whether the ML-ready feature dataset (ml_dataset.csv) already exists. "
        "Returns row and column counts if available."
    ),
)
def get_features_status():
    """Return current status of the ML dataset without re-computing anything."""
    try:
        return get_feature_engineering_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve feature engineering status: {exc!s}",
        )


@router.get(
    "/features/preview",
    response_model=FeatureEngineeringResult,
    summary="Feature Preview",
    description=(
        "Return a fresh summary and 10-row preview of the feature-engineered ML dataset. "
        "Re-runs the full computation to ensure the preview is up to date. "
        "Returns 404 if no dataset has been uploaded yet."
    ),
)
def get_features_preview():
    """
    Re-generate features (or use the cached dataset file) and return the
    FeatureEngineeringResult including column catalogue and preview rows.
    This endpoint is useful for the frontend to display feature information
    without requiring the user to click 'Generate' again.
    """
    try:
        return run_feature_engineering()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while loading the feature preview: {exc!s}",
        )


# ===========================================================================
# Milestone 6: Model Training Endpoints
# ===========================================================================

@router.post(
    "/train",
    response_model=ModelTrainingResult,
    summary="Train Models",
    description=(
        "Train both Linear Regression and Random Forest Regressor models using a "
        "chronological 80/20 train/holdout split on the active ML dataset. "
        "Saves fitted pipelines (.joblib) to backend/models/."
    ),
)
def train_models():
    """Execute model training on the active feature-engineered dataset."""
    try:
        return train_all_models()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during model training: {exc!s}",
        )


@router.get(
    "/training-status",
    response_model=ModelTrainingStatusResponse,
    summary="Get Model Training Status",
    description="Inspect whether trained model artifacts exist on disk and read their metadata.",
)
def get_model_training_status():
    """Retrieve metadata and readiness status of trained models."""
    try:
        return get_training_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve training status: {exc!s}",
        )


@router.get(
    "/results",
    response_model=ModelTrainingStatusResponse,
    summary="Get Model Results / Status",
    description="Alias for training-status for compatibility with initial project skeleton.",
)
def get_model_results():
    """Alias returning model training status and metadata."""
    try:
        return get_training_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model results: {exc!s}",
        )


