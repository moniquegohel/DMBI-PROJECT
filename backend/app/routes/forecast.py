"""
routes/forecast.py — Milestone 8: Demand Forecasting API Router.

Routes:
  POST /api/forecast/generate  — Generate multi-step daily retail demand forecasts
  GET  /api/forecast/options   — Retrieve stores, products, and horizon options
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.forecast import (
    ForecastRequest,
    ForecastResponse,
    ForecastOptionsResponse,
)
from app.services.demand_forecasting import (
    generate_demand_forecast,
    get_forecast_options,
)

router = APIRouter()


@router.get(
    "/options",
    response_model=ForecastOptionsResponse,
    summary="Get Forecasting Options",
    description="Retrieve available stores, products, categories, and latest inventory levels for forecasting.",
)
def get_options():
    """Return available stores and products with metadata."""
    try:
        return get_forecast_options()
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
            detail=f"Failed to retrieve forecasting options: {exc!s}",
        )


@router.post(
    "/generate",
    response_model=ForecastResponse,
    summary="Generate Demand Forecast",
    description=(
        "Generate multi-step future daily demand predictions for a specified store and product. "
        "Recursively updates lag and rolling features across the horizon."
    ),
)
def create_forecast(req: ForecastRequest):
    """Generate recursive demand forecast for the requested store and product."""
    try:
        return generate_demand_forecast(req)
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
            detail=f"An error occurred while generating the demand forecast: {exc!s}",
        )

