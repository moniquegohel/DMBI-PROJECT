"""
schemas/forecast.py — Pydantic models for Milestone 8: Demand Forecasting.

Defines schemas for:
  - Forecast request parameters (store, product, horizon, model selection)
  - Individual daily forecast points and historical sales points
  - Comprehensive forecast response payload
  - Available catalogue options (stores, products, categories, latest stock)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """Parameters to trigger future demand forecasting."""
    store_id: str = Field(..., description="Store identifier, e.g. 'S001'")
    product_id: str = Field(..., description="Product SKU identifier, e.g. 'P0001'")
    horizon_days: int = Field(7, description="Number of future days to forecast (e.g. 7, 14, 30)")
    model_key: Optional[str] = Field(
        "linear_regression",
        description="Model key: 'linear_regression' (default / recommended) or 'random_forest'"
    )


class ForecastPoint(BaseModel):
    """Daily predicted demand point in the forecast horizon."""
    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    day_of_week: str = Field(..., description="Day name, e.g. 'Tuesday'")
    day_index: int = Field(..., description="1-based forecast day index (1..H)")
    predicted_demand: float = Field(..., description="Predicted demand in units sold (clamped >= 0)")
    is_weekend: bool = Field(False, description="Whether this day is a Saturday or Sunday")


class HistoricalPoint(BaseModel):
    """Daily historical actual sales point for visual context."""
    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    actual_sales: float = Field(..., description="Actual recorded units sold")


class ForecastResponse(BaseModel):
    """Structured response containing historical context and future demand forecasts."""
    success: bool = Field(..., description="Whether forecast generation succeeded")
    store_id: str = Field(..., description="Store identifier")
    product_id: str = Field(..., description="Product identifier")
    category: Optional[str] = Field(None, description="Product category name")
    model_name: str = Field(..., description="Display name of model used")
    model_key: str = Field(..., description="Identifier key of model used")
    horizon_days: int = Field(..., description="Forecast horizon length in days")
    forecast_start_date: str = Field(..., description="First day of forecast period")
    forecast_end_date: str = Field(..., description="Last day of forecast period")
    total_forecasted_demand: float = Field(..., description="Sum of predicted demand across horizon")
    avg_daily_demand: float = Field(..., description="Average daily predicted demand")
    peak_demand_date: str = Field(..., description="Date of highest expected demand")
    peak_demand: float = Field(..., description="Highest expected demand on peak day")
    historical_series: List[HistoricalPoint] = Field(
        default_factory=list,
        description="Recent historical actual sales for context (e.g. last 14 days)"
    )
    forecast_series: List[ForecastPoint] = Field(
        default_factory=list,
        description="Daily predicted demand points"
    )
    message: str = Field("", description="Status message or advisory")


class CatalogueItem(BaseModel):
    """Store-product pair with metadata."""
    store_id: str
    product_id: str
    category: Optional[str] = None
    latest_date: str
    latest_inventory: float
    recent_avg_daily_sales: float


class ForecastOptionsResponse(BaseModel):
    """Dropdown options and metadata available for forecasting."""
    stores: List[str] = Field(default_factory=list, description="Unique store identifiers")
    products: List[str] = Field(default_factory=list, description="Unique product identifiers")
    catalogue: List[CatalogueItem] = Field(default_factory=list, description="All valid store-product series")
    recommended_model_key: str = Field("linear_regression", description="Recommended model key based on Milestone 7")
    recommended_model_name: str = Field("Linear Regression", description="Recommended model display name")
    default_horizon_days: int = Field(7, description="Default forecast horizon")
    allowed_horizons: List[int] = Field([7, 14, 30], description="Permitted forecast horizons")

