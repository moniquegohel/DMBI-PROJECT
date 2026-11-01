from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.analysis import (
    AnalysisSummaryResponse,
    MonthlySalesItem,
    ProductSalesItem,
    CategorySalesItem,
    StoreSalesItem
)
from app.services.analysis import (
    calculate_sales_summary,
    calculate_monthly_sales,
    calculate_product_sales,
    calculate_category_sales,
    calculate_store_sales
)

router = APIRouter()


@router.get("/summary", response_model=AnalysisSummaryResponse)
def get_analysis_summary():
    """
    Retrieve global historical sales summary metrics:
    - Total units sold
    - Average units sold per record (labeled accurately)
    - Minimum and maximum sales volume per record
    - Total records analyzed
    - Distinct product, store, and date counts
    """
    try:
        return calculate_sales_summary()
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while calculating sales summary: {str(e)}"
        )


@router.get("/monthly", response_model=List[MonthlySalesItem])
def get_monthly_sales():
    """
    Retrieve calendar month-wise sales totals in chronological order.
    Reconciles with total units sold across the active dataset.
    """
    try:
        return calculate_monthly_sales()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available. Please upload a retail sales CSV in the Dataset Upload section."
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while calculating monthly sales: {str(e)}"
        )


@router.get("/products", response_model=List[ProductSalesItem])
def get_product_sales():
    """
    Retrieve product-wise sales aggregations sorted in descending order of total units sold.
    Includes product code, categories, total units sold, and percentage share.
    """
    try:
        return calculate_product_sales()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available. Please upload a retail sales CSV in the Dataset Upload section."
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while calculating product sales: {str(e)}"
        )


@router.get("/categories", response_model=List[CategorySalesItem])
def get_category_sales():
    """
    Retrieve category-level sales breakdown sorted in descending order of total units sold.
    """
    try:
        return calculate_category_sales()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available. Please upload a retail sales CSV in the Dataset Upload section."
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while calculating category sales: {str(e)}"
        )


@router.get("/stores", response_model=List[StoreSalesItem])
def get_store_sales():
    """
    Retrieve store-level sales breakdown sorted in descending order of total units sold.
    """
    try:
        return calculate_store_sales()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available. Please upload a retail sales CSV in the Dataset Upload section."
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while calculating store sales: {str(e)}"
        )
