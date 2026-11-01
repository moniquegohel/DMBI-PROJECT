"""
schemas/inventory.py — Pydantic models for Milestone 9: Inventory Simulation.

Defines schemas for:
  - Inventory simulation request parameters (store, product, starting stock, replenishment)
  - Daily simulation ledger points (beginning stock, replenishment, available, fulfilled, unmet, ending)
  - Aggregate inventory simulation response
  - Latest recorded stock information query
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InventorySimulationRequest(BaseModel):
    """Parameters to execute an inventory simulation."""
    store_id: str = Field(..., description="Store identifier, e.g. 'S001'")
    product_id: str = Field(..., description="Product SKU identifier, e.g. 'P0001'")
    starting_inventory: Optional[float] = Field(
        None,
        description="Initial stock at the start of the horizon. If omitted, uses the recorded ending inventory from dataset."
    )
    horizon_days: int = Field(7, description="Number of days to simulate (e.g. 7, 14, 30)")
    model_key: Optional[str] = Field("linear_regression", description="Model used for demand forecast")
    replenishment_quantity: float = Field(0.0, description="Optional replenishment quantity arriving during horizon")
    replenishment_day: Optional[int] = Field(None, description="Day index (1..H) when replenishment arrives")


class DailySimulationPoint(BaseModel):
    """Day-by-day inventory balance and fulfillment outcome."""
    day: int = Field(..., description="Simulation day number (1..H)")
    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    beginning_inventory: float = Field(..., description="Stock level at start of day")
    replenishment_received: float = Field(0.0, description="Replenishment arriving on this day")
    available_stock: float = Field(..., description="Beginning stock + replenishment received")
    forecasted_demand: float = Field(..., description="Expected customer demand for this day")
    demand_fulfilled: float = Field(..., description="Portion of demand fulfilled from available stock")
    unmet_demand: float = Field(..., description="Demand that could not be satisfied due to stockout")
    ending_inventory: float = Field(..., description="Physical stock remaining at end of day (>= 0)")
    is_stockout: bool = Field(False, description="True if unmet demand > 0 or ending inventory == 0")


class InventorySimulationResponse(BaseModel):
    """Aggregate simulation results and daily ledger."""
    success: bool = Field(..., description="Whether simulation completed successfully")
    store_id: str = Field(..., description="Store identifier")
    product_id: str = Field(..., description="Product identifier")
    category: Optional[str] = Field(None, description="Product category")
    starting_inventory: float = Field(..., description="Initial stock used for simulation")
    is_user_provided_starting_stock: bool = Field(
        ...,
        description="True if starting stock was provided by user; False if loaded from recorded dataset"
    )
    recorded_ending_stock_from_data: float = Field(
        ...,
        description="Actual recorded inventory level from the dataset on the cutoff date"
    )
    horizon_days: int = Field(..., description="Simulation period length in days")
    forecast_start_date: str = Field(..., description="First day of simulation")
    forecast_end_date: str = Field(..., description="Last day of simulation")
    total_forecasted_demand: float = Field(..., description="Sum of expected demand over horizon")
    total_demand_fulfilled: float = Field(..., description="Total demand successfully satisfied")
    total_unmet_demand: float = Field(..., description="Total lost/unfulfilled demand")
    stockout_periods_count: int = Field(..., description="Number of days experiencing a stockout")
    first_stockout_day: Optional[int] = Field(None, description="First day index when a stockout occurs")
    first_stockout_date: Optional[str] = Field(None, description="Date of first stockout")
    ending_inventory: float = Field(..., description="Final remaining physical stock at end of horizon")
    service_level_percentage: float = Field(
        ...,
        description="Percentage of customer demand fulfilled (fulfilled / total * 100)"
    )
    simulation_points: List[DailySimulationPoint] = Field(
        default_factory=list,
        description="Daily stock balance ledger"
    )
    simulation_summary_text: str = Field(..., description="Plain-language business interpretation")


class StockInfoResponse(BaseModel):
    """Recorded stock details for a given store and product."""
    store_id: str
    product_id: str
    category: Optional[str] = None
    recorded_stock: float
    recorded_date: str
    units_sold_on_date: float

