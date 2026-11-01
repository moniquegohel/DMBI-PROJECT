from typing import List, Dict, Any, Optional
# pyrefly: ignore[missing-import]
from pydantic import BaseModel, Field


class ColumnInspectionInfo(BaseModel):
    """Detailed metadata and summary statistics for a single dataset column."""
    name: str
    inferred_type: str
    missing_count: int
    missing_percentage: float
    unique_count: int
    is_numeric: bool
    is_date: bool
    sample_values: List[Any] = []
    # Numeric column summary statistics (None if non-numeric)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None


class ColumnMappingItem(BaseModel):
    """Specification of a semantic retail role and the mapped CSV column."""
    role: str
    role_label: str
    description: str
    is_required: bool
    mapped_column: Optional[str] = None
    is_mapped: bool = False


class ColumnMappingUpdateRequest(BaseModel):
    """Request payload to review or update column role mappings."""
    mappings: Dict[str, Optional[str]] = Field(
        ...,
        description="Mapping from role key (e.g. 'date', 'units_sold') to CSV column name or null"
    )


class QualityCheckItem(BaseModel):
    """A single data-quality validation finding (info, warning, or error)."""
    check_type: str  # 'info', 'warning', 'error'
    title: str
    description: str
    affected_column: Optional[str] = None
    affected_count: int = 0
    action_recommendation: str = ""


class DatasetSummaryResponse(BaseModel):
    """Complete inspection and quality report returned after dataset upload or query."""
    has_dataset: bool
    filename: Optional[str] = None
    file_size_bytes: int = 0
    row_count: int = 0
    column_count: int = 0
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    unique_dates_count: int = 0
    unique_stores_count: int = 0
    unique_products_count: int = 0
    total_missing_values: int = 0
    duplicate_rows_count: int = 0
    status: str = "empty"  # 'empty', 'uploaded', 'cleaned', 'ready'
    preview_rows: List[Dict[str, Any]] = []
    columns: List[ColumnInspectionInfo] = []
    mappings: List[ColumnMappingItem] = []
    quality_checks: List[QualityCheckItem] = []
    warnings_count: int = 0
    errors_count: int = 0
    is_cleaned: bool = False
    is_ready_for_analysis: bool = False


class CleaningResultResponse(BaseModel):
    """Result report returned after the user executes the data cleaning action."""
    success: bool
    message: str
    original_rows: int
    cleaned_rows: int
    original_columns: int
    cleaned_columns: int
    changes_applied: List[str] = []
    warnings: List[str] = []
    is_ready_for_analysis: bool = True
    cleaned_preview_rows: List[Dict[str, Any]] = []
