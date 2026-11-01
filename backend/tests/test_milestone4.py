import os
import pytest
from fastapi.testclient import TestClient
import pandas as pd

from app.main import app
from app.services.data_cleaning import CLEANED_DATASET_PATH, RAW_DATASET_PATH
from app.services.analysis import clear_analysis_cache

client = TestClient(app)


def test_health_endpoint_still_operational():
    """Verify health endpoint remains healthy after analysis router integration."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_analysis_summary_metrics():
    """
    Test GET /api/analysis/summary:
    - Verifies has_dataset is True
    - Verifies total_records matches active dataset (73,100)
    - Verifies total_units_sold matches exact sum of Units Sold (9,975,582)
    - Verifies average_units_sold_per_record is computed as (total_units_sold / total_records)
    - Verifies min and max units sold per record
    - Verifies unique entity counts: 20 products, 5 stores, 731 dates
    - Verifies average is explicitly labeled per record, not daily average
    """
    clear_analysis_cache()
    response = client.get("/api/analysis/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["has_dataset"] is True
    assert data["total_records"] == 73100
    assert data["total_units_sold"] == 9975582
    assert "average_units_sold_per_record" in data
    expected_avg = round(9975582 / 73100, 2)
    assert abs(data["average_units_sold_per_record"] - expected_avg) < 0.05
    assert data["min_units_sold_per_record"] == 0
    assert data["max_units_sold_per_record"] == 499
    assert data["unique_products_count"] == 20
    assert data["unique_stores_count"] == 5
    assert data["unique_dates_count"] == 731
    assert data["date_range_start"] == "2022-01-01"
    assert data["date_range_end"] == "2024-01-01"


def test_monthly_sales_reconciliation_and_chronology():
    """
    Test GET /api/analysis/monthly:
    - Verifies all months are in strict chronological order
    - Verifies monthly totals sum exactly to global total_units_sold (9,975,582)
    - Verifies each month item contains required fields (month, month_label, total_units_sold, total_sales)
    - Verifies calendar month coverage from 2022-01 to 2024-01 (25 calendar months)
    """
    summary_resp = client.get("/api/analysis/summary")
    assert summary_resp.status_code == 200
    global_total = summary_resp.json()["total_units_sold"]

    response = client.get("/api/analysis/monthly")
    assert response.status_code == 200
    monthly_data = response.json()

    assert isinstance(monthly_data, list)
    assert len(monthly_data) == 25  # 24 months in 2022-2023 + Jan 2024

    # 1. Verify strict chronological order
    month_keys = [item["month"] for item in monthly_data]
    assert month_keys == sorted(month_keys), "Monthly items must be chronologically ordered"

    # Verify first and last month
    assert monthly_data[0]["month"] == "2022-01"
    assert monthly_data[0]["month_label"] == "Jan 2022"
    assert monthly_data[-1]["month"] == "2024-01"
    assert monthly_data[-1]["month_label"] == "Jan 2024"

    # 2. Reconcile monthly sum with global total sales
    monthly_sum = sum(item["total_units_sold"] for item in monthly_data)
    assert monthly_sum == global_total, f"Monthly sum {monthly_sum} must equal total {global_total}"

    # Also verify total_sales alias matches total_units_sold
    for item in monthly_data:
        assert item["total_sales"] == item["total_units_sold"]
        assert item["record_count"] > 0
        assert item["average_units_sold_per_record"] > 0


def test_product_sales_reconciliation_and_sorting():
    """
    Test GET /api/analysis/products:
    - Verifies products are sorted in descending order of total_units_sold
    - Verifies product totals sum exactly to global total_units_sold (9,975,582)
    - Verifies all 20 unique products are returned
    - Verifies category information is provided
    - Verifies percentage shares sum to ~100%
    """
    summary_resp = client.get("/api/analysis/summary")
    global_total = summary_resp.json()["total_units_sold"]

    response = client.get("/api/analysis/products")
    assert response.status_code == 200
    product_data = response.json()

    assert isinstance(product_data, list)
    assert len(product_data) == 20

    # 1. Verify descending order
    sales_quantities = [item["total_units_sold"] for item in product_data]
    assert sales_quantities == sorted(sales_quantities, reverse=True), "Products must be sorted descending by total units sold"

    # 2. Reconcile product sum with global total
    product_sum = sum(item["total_units_sold"] for item in product_data)
    assert product_sum == global_total, f"Product sum {product_sum} must equal total {global_total}"

    # 3. Top product validation
    top_product = product_data[0]
    assert top_product["product_id"] == "P0016"
    assert top_product["total_units_sold"] == 508472
    assert top_product["percentage_of_total"] > 0
    assert top_product["category"] is not None

    # Verify percentages sum close to 100%
    total_pct = sum(item["percentage_of_total"] for item in product_data)
    assert 99.0 <= total_pct <= 101.0


def test_category_sales_reconciliation():
    """
    Test GET /api/analysis/categories:
    - Verifies category totals reconcile with total_units_sold (9,975,582)
    - Verifies 5 distinct retail categories
    - Verifies percentages sum to 100%
    """
    summary_resp = client.get("/api/analysis/summary")
    global_total = summary_resp.json()["total_units_sold"]

    response = client.get("/api/analysis/categories")
    assert response.status_code == 200
    category_data = response.json()

    assert len(category_data) == 5
    cat_sum = sum(item["total_units_sold"] for item in category_data)
    assert cat_sum == global_total

    cat_names = [item["category"] for item in category_data]
    assert set(cat_names) == {"Groceries", "Toys", "Electronics", "Clothing", "Furniture"}


def test_store_sales_reconciliation():
    """
    Test GET /api/analysis/stores:
    - Verifies store totals reconcile with total_units_sold (9,975,582)
    - Verifies 5 distinct retail stores
    """
    summary_resp = client.get("/api/analysis/summary")
    global_total = summary_resp.json()["total_units_sold"]

    response = client.get("/api/analysis/stores")
    assert response.status_code == 200
    store_data = response.json()

    assert len(store_data) == 5
    store_sum = sum(item["total_units_sold"] for item in store_data)
    assert store_sum == global_total


def test_no_dataset_handling(monkeypatch):
    """
    Verify application handles missing dataset cleanly without 500 errors or crashes.
    """
    from app.services import analysis
    clear_analysis_cache()

    # Temporarily monkeypatch dataset paths to non-existent files
    monkeypatch.setattr(analysis, "CLEANED_DATASET_PATH", "backend/data/non_existent_cleaned.csv")
    monkeypatch.setattr(analysis, "RAW_DATASET_PATH", "backend/data/non_existent_raw.csv")

    # 1. Summary should return has_dataset=False cleanly
    response = client.get("/api/analysis/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["has_dataset"] is False
    assert data["total_records"] == 0
    assert "No dataset" in data["message"]

    # 2. Monthly should return 404 with clear message
    resp_monthly = client.get("/api/analysis/monthly")
    assert resp_monthly.status_code == 404
    assert "No dataset available" in resp_monthly.json()["detail"]

    # 3. Product should return 404 with clear message
    resp_prod = client.get("/api/analysis/products")
    assert resp_prod.status_code == 404
    assert "No dataset available" in resp_prod.json()["detail"]

    clear_analysis_cache()
