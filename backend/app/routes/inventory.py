"""
routes/inventory.py — Milestone 9: Inventory Simulation API Router.

Routes:
  POST /api/inventory/simulate   — Execute step-by-step physical inventory simulation
  GET  /api/inventory/stock-info — Query recorded ending stock from dataset
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.inventory import (
    InventorySimulationRequest,
    InventorySimulationResponse,
    StockInfoResponse,
)
from app.services.inventory_simulation import (
    run_inventory_simulation,
    get_stock_info,
)

router = APIRouter()


@router.get(
    "/stock-info",
    response_model=StockInfoResponse,
    summary="Get Recorded Stock Info",
    description="Retrieve the latest recorded inventory level and transaction date for a store and product.",
)
def get_recorded_stock(
    store_id: str = Query(..., description="Store identifier, e.g. 'S001'"),
    product_id: str = Query(..., description="Product SKU identifier, e.g. 'P0001'"),
):
    """Return recorded stock details from dataset."""
    try:
        return get_stock_info(store_id=store_id, product_id=product_id)
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
            detail=f"Failed to retrieve stock information: {exc!s}",
        )


@router.post(
    "/simulate",
    response_model=InventorySimulationResponse,
    summary="Simulate Inventory Levels",
    description=(
        "Simulate day-by-day inventory balances, customer demand fulfillment, "
        "unmet demand, and stockout occurrences based on Milestone 8 demand forecasts."
    ),
)
def simulate_inventory(req: InventorySimulationRequest):
    """Run inventory simulation across the forecast horizon."""
    try:
        return run_inventory_simulation(req)
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
            detail=f"An error occurred during inventory simulation: {exc!s}",
        )

