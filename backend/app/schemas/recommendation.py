"""
recommendation.py — Pydantic Schemas for Milestone 10 & 11

Defines structured response and request schemas for:
- Smart Inventory Recommendations (ROP, target stock, reorder quantities, status)
- Executive Business Dashboard (KPI cards, business insight callouts, chart data)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """Inventory recommendation data for a single store-product series."""
    store_id: str = Field(..., description="Store Identifier (e.g. S001)")
    product_id: str = Field(..., description="Product Identifier (e.g. P0001)")
    category: str = Field(..., description="Product Category (e.g. Clothing)")
    current_stock: float = Field(..., description="Latest recorded inventory level")
    forecasted_demand: float = Field(..., description="Expected demand over planning horizon")
    daily_demand: float = Field(..., description="Average expected daily sales velocity")
    lead_time_days: int = Field(2, description="Supplier lead time in days")
    safety_buffer_days: int = Field(1, description="Safety stock buffer in days")
    reorder_point: float = Field(..., description="Reorder point threshold (ROP)")
    target_stock: float = Field(..., description="Optimal target inventory level")
    suggested_reorder_qty: float = Field(..., ge=0, description="Recommended replenishment units (>= 0)")
    days_of_supply: float = Field(..., description="Runway in days before stock reaches zero")
    status: str = Field(..., description="Classification: Restock Soon, Stock Available, Excess Stock, Insufficient Data")
    notes: str = Field("", description="Plain-language retail explanation")


class RecommendationSummary(BaseModel):
    """Aggregated recommendation metrics across evaluated inventory."""
    total_products_evaluated: int = Field(..., description="Total store-product series analyzed")
    restock_soon_count: int = Field(..., description="Number of items needing replenishment")
    stock_available_count: int = Field(..., description="Number of items with healthy stock")
    excess_stock_count: int = Field(..., description="Number of items with surplus stock")
    insufficient_data_count: int = Field(..., description="Number of items with insufficient data")
    total_reorder_units: float = Field(..., ge=0, description="Sum of suggested reorder units")
    average_days_of_supply: float = Field(..., description="Mean stock runway across active products")


class RecommendationResponse(BaseModel):
    """Full API response for inventory recommendations."""
    summary: RecommendationSummary
    items: List[RecommendationItem]
    stores: List[str]
    categories: List[str]
    horizon_days: int
    calculated_at: str


class BusinessInsightItem(BaseModel):
    """Actionable retail narrative insight for executive dashboard."""
    id: str
    type: str = Field(..., description="Category: URGENT_RESTOCK, HIGH_DEMAND, EXCESS_CAPITAL, STORE_LOGISTICS")
    title: str = Field(..., description="Business-friendly insight title")
    description: str = Field(..., description="Clear explanation of why this item is flagged")
    recommended_action: str = Field(..., description="Actionable recommendation for retail manager")
    severity: str = Field(..., description="CRITICAL, WARNING, or INFO")
    store_id: Optional[str] = None
    product_id: Optional[str] = None


class StoreRestockOverview(BaseModel):
    """Store-level replenishment roll-up for regional planning."""
    store_id: str
    total_items: int
    restock_items_count: int
    total_reorder_units: float
    current_inventory_units: float


class DashboardSummaryResponse(BaseModel):
    """Complete executive summary payload for Milestone 11 Dashboard."""
    total_products: int
    total_stores: int
    products_requiring_restock: int
    products_at_risk_of_stockout: int
    products_with_excess_inventory: int
    total_suggested_reorder_volume: float
    insights: List[BusinessInsightItem]
    top_demand_products: List[Dict[str, Any]]
    stockout_risks: List[Dict[str, Any]]
    excess_stock_items: List[Dict[str, Any]]
    store_replenishment: List[StoreRestockOverview]
    category_distribution: List[Dict[str, Any]]
    calculated_at: str

