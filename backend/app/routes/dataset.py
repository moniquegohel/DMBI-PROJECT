import os
import io
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import pandas as pd

from app.database.database import get_db
from app.database.models import DatasetMetadata
from app.schemas.dataset import (
    DatasetSummaryResponse,
    ColumnMappingUpdateRequest,
    CleaningResultResponse
)
from app.services.data_cleaning import (
    DATA_DIR,
    RAW_DATASET_PATH,
    CLEANED_DATASET_PATH,
    save_raw_csv_file,
    load_raw_dataset,
    load_cleaned_dataset,
    inspect_dataframe,
    save_column_mappings_to_file,
    load_column_mappings_from_file,
    execute_data_cleaning
)

router = APIRouter()


@router.post("/upload", response_model=DatasetSummaryResponse)
async def upload_csv_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and validate a retail sales CSV file.
    Performs immediate inspection: row/col counts, missing values, duplicates,
    date range, numeric summaries, and retail column role matching.
    """
    filename = file.filename or "uploaded_dataset.csv"

    # 1. Validate file extension
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a valid .csv file."
        )

    # 2. Read file contents into memory for validation
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    # 3. Check for empty file
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file is empty (0 bytes). Please select a valid dataset."
        )

    # 4. Validate that contents can be parsed as a CSV by Pandas
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format or corrupted file: {str(e)}"
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file contains no data rows."
        )

    # 5. Save the raw CSV securely on backend
    safe_filename, file_size = save_raw_csv_file(contents, filename)

    # 6. Perform comprehensive dataset inspection
    saved_mappings = load_column_mappings_from_file()
    summary = inspect_dataframe(
        df=df,
        filename=safe_filename,
        file_size_bytes=file_size,
        saved_mappings=saved_mappings,
        is_cleaned=False
    )

    # 7. Record dataset metadata in SQLite database
    try:
        # Check if record exists
        meta = db.query(DatasetMetadata).first()
        if not meta:
            meta = DatasetMetadata(
                filename=safe_filename,
                file_size_bytes=file_size,
                original_rows=summary.row_count,
                original_columns=summary.column_count,
                status="uploaded"
            )
            db.add(meta)
        else:
            meta.filename = safe_filename
            meta.file_size_bytes = file_size
            meta.original_rows = summary.row_count
            meta.original_columns = summary.column_count
            meta.cleaned_rows = 0
            meta.cleaned_columns = 0
            meta.status = "uploaded"
        db.commit()
    except Exception as db_err:
        db.rollback()
        print(f"Warning: Failed to persist dataset metadata in DB: {db_err}")

    return summary


@router.get("/summary", response_model=DatasetSummaryResponse)
def get_dataset_summary():
    """
    Retrieve inspection summary of the currently loaded dataset.
    Returns cleaned data if cleaned, or raw uploaded data if not yet cleaned.
    """
    # Check if cleaned or raw exists
    if os.path.exists(CLEANED_DATASET_PATH):
        try:
            df = load_cleaned_dataset()
            file_size = os.path.getsize(CLEANED_DATASET_PATH)
            filename = "cleaned_dataset.csv"
            saved_mappings = load_column_mappings_from_file()
            return inspect_dataframe(df, filename, file_size, saved_mappings, is_cleaned=True)
        except Exception:
            pass

    if os.path.exists(RAW_DATASET_PATH):
        df = load_raw_dataset()
        file_size = os.path.getsize(RAW_DATASET_PATH)
        filename = "raw_dataset.csv"
        saved_mappings = load_column_mappings_from_file()
        return inspect_dataframe(df, filename, file_size, saved_mappings, is_cleaned=False)

    # No dataset uploaded yet
    return DatasetSummaryResponse(
        has_dataset=False,
        filename=None,
        file_size_bytes=0,
        row_count=0,
        column_count=0,
        status="empty"
    )


@router.post("/map", response_model=DatasetSummaryResponse)
def update_column_mappings(payload: ColumnMappingUpdateRequest):
    """
    Review and update semantic column mappings.
    Re-inspects current dataset with new mappings and returns updated summary.
    """
    if not os.path.exists(RAW_DATASET_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available. Please upload a CSV first."
        )

    # Save new mappings
    save_column_mappings_to_file(payload.mappings)

    df = load_raw_dataset()
    file_size = os.path.getsize(RAW_DATASET_PATH)
    is_cleaned = os.path.exists(CLEANED_DATASET_PATH)
    return inspect_dataframe(df, "raw_dataset.csv", file_size, payload.mappings, is_cleaned=is_cleaned)


@router.post("/clean", response_model=CleaningResultResponse)
def clean_dataset_endpoint(db: Session = Depends(get_db)):
    """
    Execute data cleaning on uploaded dataset:
    - Validates and parses dates
    - Drops exact duplicate rows (if any)
    - Verifies numeric datatypes
    - Preserves negative Demand Forecast values without silent deletion
    - Saves cleaned dataset to backend/data/cleaned_dataset.csv
    - Updates database metadata record
    """
    if not os.path.exists(RAW_DATASET_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded dataset found. Please upload a CSV file before cleaning."
        )

    try:
        result = execute_data_cleaning()

        # Update metadata in database
        meta = db.query(DatasetMetadata).first()
        if meta:
            meta.cleaned_rows = result.cleaned_rows
            meta.cleaned_columns = result.cleaned_columns
            meta.status = "ready"
            db.commit()

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during dataset cleaning: {str(e)}"
        )


@router.get("/download/cleaned")
def download_cleaned_csv():
    """Download the cleaned retail sales CSV file."""
    if not os.path.exists(CLEANED_DATASET_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cleaned dataset not available. Please run data cleaning first."
        )
    return FileResponse(
        CLEANED_DATASET_PATH,
        media_type="text/csv",
        filename="cleaned_retail_store_inventory.csv"
    )


@router.get("/download/raw")
def download_raw_csv():
    """Download the original raw uploaded CSV file."""
    if not os.path.exists(RAW_DATASET_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded dataset file available."
        )
    return FileResponse(
        RAW_DATASET_PATH,
        media_type="text/csv",
        filename="raw_retail_store_inventory.csv"
    )


@router.post("/load-sample", response_model=DatasetSummaryResponse)
def load_sample_dataset(db: Session = Depends(get_db)):
    """
    Convenience endpoint for academic demo:
    Loads retail_store_inventory.csv directly if present on local machine.
    """
    possible_paths = [
        r"C:\Users\moniq\Downloads\dataset\retail_store_inventory.csv",
        os.path.join(DATA_DIR, "retail_store_inventory.csv")
    ]
    sample_path = None
    for p in possible_paths:
        if os.path.exists(p):
            sample_path = p
            break

    if not sample_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample dataset 'retail_store_inventory.csv' not found on server."
        )

    with open(sample_path, "rb") as f:
        contents = f.read()

    safe_filename, file_size = save_raw_csv_file(contents, "retail_store_inventory.csv")
    df = pd.read_csv(io.BytesIO(contents))
    saved_mappings = load_column_mappings_from_file()
    summary = inspect_dataframe(df, safe_filename, file_size, saved_mappings, is_cleaned=False)

    meta = db.query(DatasetMetadata).first()
    if not meta:
        meta = DatasetMetadata(
            filename=safe_filename,
            file_size_bytes=file_size,
            original_rows=summary.row_count,
            original_columns=summary.column_count,
            status="uploaded"
        )
        db.add(meta)
    else:
        meta.filename = safe_filename
        meta.file_size_bytes = file_size
        meta.original_rows = summary.row_count
        meta.original_columns = summary.column_count
        meta.status = "uploaded"
    db.commit()

    return summary
