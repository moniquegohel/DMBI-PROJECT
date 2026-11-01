from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class AnalysisSummaryResponse(BaseModel):
    """Calculated sales metrics across the entire active retail dataset."""
    has_dataset: bool = True
    dataset_name: str = ""
    is_cleaned: bool = False
    total_records: int = Field(..., description="Total row count of transactions in the dataset")
    total_units_sold: int = Field(..., description="Reconciled sum of all units sold")
    average_units_sold_per_record: float = Field(
        ...,
        description="Average volume per record (Total Units Sold / Total Records). NOT a daily average."
    )
    min_units_sold_per_record: int = Field(..., description="Minimum units sold in any record")
    max_units_sold_per_record: int = Field(..., description="Maximum units sold in any record")
    unique_products_count: Optional[int] = Field(None, description="Count of distinct product identifiers")
    unique_stores_count: Optional[int] = Field(None, description="Count of distinct retail stores")
    unique_dates_count: Optional[int] = Field(None, description="Count of distinct sale dates")
    date_range_start: Optional[str] = Field(None, description="Earliest transaction date YYYY-MM-DD")
    date_range_end: Optional[str] = Field(None, description="Latest transaction date YYYY-MM-DD")
    mapped_columns: Dict[str, str] = Field(default_factory=dict, description="Active column roles used")
    message: Optional[str] = None


class MonthlySalesItem(BaseModel):
    """Monthly aggregation of sales volume in chronological order."""
    month: str = Field(..., description="Chronological year-month key, e.g. '2022-01'")
    month_label: str = Field(..., description="Formatted display label, e.g. 'Jan 2022'")
    year: int
    month_num: int
    total_units_sold: int = Field(..., description="Total units sold in this calendar month")
    total_sales: int = Field(..., description="Alias matching total_units_sold for API compatibility")
    record_count: int = Field(..., description="Number of transaction records in this month")
    average_units_sold_per_record: float = Field(
        ...,
        description="Average units sold per record within this month"
    )


class ProductSalesItem(BaseModel):
    """Product-level sales metrics ordered by total sales volume."""
    product_id: str = Field(..., description="Unique product SKU or identifier")
    product_name: str = Field(..., description="Product display name or code")
    category: Optional[str] = Field(None, description="Primary product category or concatenated categories")
    categories: List[str] = Field(default_factory=list, description="All categories associated with product")
    total_units_sold: int = Field(..., description="Total units sold for this product")
    total_sales: int = Field(..., description="Alias matching total_units_sold")
    record_count: int = Field(..., description="Number of sales records for this product")
    average_units_sold_per_record: float = Field(..., description="Average units sold per record")
    percentage_of_total: float = Field(..., description="Share of total dataset sales as percentage")


class CategorySalesItem(BaseModel):
    """Category-level aggregation of sales volume."""
    category: str
    total_units_sold: int
    total_sales: int
    record_count: int
    average_units_sold_per_record: float
    percentage_of_total: float


class StoreSalesItem(BaseModel):
    """Store-level aggregation of sales volume."""
    store_id: str
    total_units_sold: int
    total_sales: int
    record_count: int
    average_units_sold_per_record: float
    percentage_of_total: float
