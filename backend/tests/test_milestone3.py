import os
import io
import pytest
from fastapi.testclient import TestClient
import pandas as pd

from app.main import app

client = TestClient(app)

SAMPLE_CSV_PATH = r"C:\Users\moniq\Downloads\dataset\retail_store_inventory.csv"


def test_health_endpoint():
    """Verify health endpoint still works and reports database connected."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_upload_invalid_extension():
    """Verify uploading a non-csv file returns 400 with clear error message."""
    file_content = b"This is a plain text file, not a CSV."
    response = client.post(
        "/api/dataset/upload",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_empty_csv():
    """Verify uploading an empty 0-byte CSV returns 400 with clear error message."""
    response = client.post(
        "/api/dataset/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_corrupted_csv():
    """Verify uploading corrupted/binary data as CSV returns 400."""
    corrupted_bytes = b"\x00\x01\x02\x03\xff\xfe\x00\x00corrupted data"
    response = client.post(
        "/api/dataset/upload",
        files={"file": ("corrupted.csv", io.BytesIO(corrupted_bytes), "text/csv")}
    )
    assert response.status_code == 400


def test_upload_retail_store_inventory_csv():
    """
    Test uploading the real retail_store_inventory.csv (73,100 rows, 15 columns).
    Verifies:
    - Calculated row count (73,100) and column count (15)
    - Zero missing values and zero duplicate rows
    - Date range (2022-01-01 to 2024-01-01)
    - 5 unique stores and 20 unique products
    - Negative Demand Forecast warning (673 rows flagged, preserved without deletion)
    - 10-row preview generated
    """
    assert os.path.exists(SAMPLE_CSV_PATH), f"Sample CSV file not found at {SAMPLE_CSV_PATH}"

    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/dataset/upload",
        files={"file": ("retail_store_inventory.csv", io.BytesIO(file_bytes), "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["has_dataset"] is True
    assert data["filename"] == "retail_store_inventory.csv"
    assert data["row_count"] == 73100
    assert data["column_count"] == 15
    assert data["total_missing_values"] == 0
    assert data["duplicate_rows_count"] == 0
    assert data["date_range_start"] == "2022-01-01"
    assert data["date_range_end"] == "2024-01-01"
    assert data["unique_dates_count"] == 731
    assert data["unique_stores_count"] == 5
    assert data["unique_products_count"] == 20
    assert len(data["preview_rows"]) == 10
    assert len(data["columns"]) == 15

    # Check that negative Demand Forecast is flagged as warning
    warning_checks = [c for c in data["quality_checks"] if c["check_type"] == "warning"]
    assert len(warning_checks) >= 1
    demand_warning = next((c for c in warning_checks if "Demand Forecast" in c["title"]), None)
    assert demand_warning is not None
    assert demand_warning["affected_count"] == 673


def test_get_dataset_summary():
    """Verify GET /api/dataset/summary returns the uploaded dataset summary."""
    response = client.get("/api/dataset/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["has_dataset"] is True
    assert data["row_count"] == 73100


def test_update_column_mappings():
    """Verify POST /api/dataset/map allows saving custom column role mappings."""
    payload = {
        "mappings": {
            "date": "Date",
            "store_id": "Store ID",
            "product_id": "Product ID",
            "units_sold": "Units Sold",
            "inventory_level": "Inventory Level"
        }
    }
    response = client.post("/api/dataset/map", json=payload)
    assert response.status_code == 200
    data = response.json()
    mapped_roles = {m["role"]: m["mapped_column"] for m in data["mappings"]}
    assert mapped_roles["date"] == "Date"
    assert mapped_roles["units_sold"] == "Units Sold"


def test_clean_dataset_execution():
    """
    Test POST /api/dataset/clean:
    - Verifies row count before (73,100) and after (73,100)
    - Verifies no rows were deleted
    - Verifies warning about 673 negative Demand Forecast values is reported
    - Verifies cleaned preview is returned
    - Verifies is_ready_for_analysis is True
    """
    response = client.post("/api/dataset/clean")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["original_rows"] == 73100
    assert data["cleaned_rows"] == 73100
    assert data["original_columns"] == 15
    assert data["cleaned_columns"] == 15
    assert data["is_ready_for_analysis"] is True
    assert len(data["changes_applied"]) > 0
    assert len(data["warnings"]) >= 1
    assert any("673" in w for w in data["warnings"])
    assert len(data["cleaned_preview_rows"]) == 10


def test_download_cleaned_csv():
    """Verify GET /api/dataset/download/cleaned downloads valid cleaned CSV."""
    response = client.get("/api/dataset/download/cleaned")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    df_cleaned = pd.read_csv(io.BytesIO(response.content))
    assert len(df_cleaned) == 73100
    assert len(df_cleaned.columns) == 15


if __name__ == "__main__":
    pytest.main(["-v", __file__])
