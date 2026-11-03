"""
recommendation.py — FastAPI Router for Milestones 10 & 11

Endpoints:
- GET  /api/recommendation/all: Retrieve full inventory recommendations with filtering.
- GET  /api/recommendation/dashboard-summary: Executive dashboard KPI metrics & business insights.
- POST /api/recommendation/calculate: On-demand recommendation calculation with custom parameters.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.schemas.recommendation import (
    RecommendationResponse,
    DashboardSummaryResponse,
)
from app.services.inventory_recommendation import (
    get_inventory_recommendations,
    get_dashboard_summary,
)

router = APIRouter()


class RecommendationCalculateRequest(BaseModel):
    store_id: Optional[str] = Field(None, description="Filter by store ID (e.g. S001) or null for all")
    category: Optional[str] = Field(None, description="Filter by product category or null for all")
    status: Optional[str] = Field(None, description="Filter by status or null for all")
    horizon_days: int = Field(7, ge=1, le=90, description="Planning horizon in days (default 7)")
    lead_time_days: int = Field(2, ge=1, le=30, description="Supplier lead time in days (default 2)")
    safety_buffer_days: int = Field(1, ge=0, le=14, description="Safety stock buffer in days (default 1)")


@router.get("/all", response_model=RecommendationResponse)
def get_all_recommendations(
    store_id: Optional[str] = Query(default=None, description="Optional Store ID filter"),
    category: Optional[str] = Query(default=None, description="Optional Category filter"),
    status: Optional[str] = Query(default=None, description="Optional Status filter"),
    lead_time_days: int = Query(default=2, ge=1, le=30, description="Supplier lead time days"),
    safety_buffer_days: int = Query(default=1, ge=0, le=14, description="Safety buffer days"),
    horizon_days: int = Query(default=7, ge=1, le=90, description="Forecast horizon days"),
):
    """
    Retrieve filterable inventory recommendations across all catalogue series.
    Provides calculated reorder point, target stock, suggested reorder qty, and status classification.
    """
    # Normalize when invoked directly in Python unit tests where Query objects are not injected
    s_id = None if hasattr(store_id, "default") else store_id
    cat = None if hasattr(category, "default") else category
    stat = None if hasattr(status, "default") else status
    lt = 2 if hasattr(lead_time_days, "default") else lead_time_days
    sb = 1 if hasattr(safety_buffer_days, "default") else safety_buffer_days
    hz = 7 if hasattr(horizon_days, "default") else horizon_days

    try:
        return get_inventory_recommendations(
            store_id=s_id,
            category=cat,
            status=stat,
            lead_time_days=lt,
            safety_buffer_days=sb,
            horizon_days=hz,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.post("/calculate", response_model=RecommendationResponse)
def calculate_recommendations(req: RecommendationCalculateRequest):
    """
    Calculate recommendations with custom user-defined simulation parameters.
    """
    try:
        return get_inventory_recommendations(
            store_id=req.store_id,
            category=req.category,
            status=req.status,
            lead_time_days=req.lead_time_days,
            safety_buffer_days=req.safety_buffer_days,
            horizon_days=req.horizon_days,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate recommendations: {str(e)}")


@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
def get_dashboard_kpis_and_insights():
    """
    Milestone 11: Executive Dashboard Summary & Actionable Business Insights.
    Aggregates catalogue-wide inventory status, top demand SKUs, urgent stockout threats,
    and regional replenishment allocations.
    """
    try:
        return get_dashboard_summary()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard summary: {str(e)}")
