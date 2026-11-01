# SMARTSTOCK — MILESTONE 4: HISTORICAL SALES ANALYSIS VERIFICATION REPORT

> **Milestone:** Milestone 4 — Historical Sales Analysis  
> **Status:** Verified & Completed  
> **Date:** October 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 4 implemented the complete Historical Sales Analysis layer for SmartStock — the first milestone to consume the cleaned dataset from Milestone 3 and produce business intelligence output.

The primary objectives were:

1. Build 5 backend REST API endpoints that calculate real sales statistics from the uploaded/cleaned dataset using Pandas aggregations.
2. Ensure that all aggregated totals (summary, monthly, product, category, store) reconcile exactly with each other and with the raw dataset — no phantom figures.
3. Label averages correctly as per-record averages rather than misleadingly describing them as daily averages.
4. Return clear, actionable error messages when no dataset has been uploaded, without exposing stack traces.
5. Replace the SalesAnalysis.jsx placeholder with a fully functional page displaying:
   - Summary stat cards
   - A monthly trend line chart
   - A product-wise horizontal bar chart and data table
   - Category and store breakdown bar charts
6. Implement a no-dataset state that guides the user to the Dataset Upload page.
7. Implement loading and per-section error states.
8. Verify all calculations and metric reconciliation with an automated pytest suite.
9. Verify the frontend production build compiles successfully.
10. Leave Milestones 1–3 features completely untouched.

---

## 2. File Inventory & Technical Implementation

### Backend Modules (`backend/app/`)

#### 1. `backend/app/schemas/analysis.py` (New)

Pydantic response models for all 5 analysis endpoints:

- `AnalysisSummaryResponse` — total, average per record, min, max, record count, distinct products, stores, and dates.
- `MonthlySalesItem` — month label and total units sold per calendar month.
- `ProductSalesItem` — product identifier, category, total units sold, and percentage share.
- `CategorySalesItem` — category name and total units sold.
- `StoreSalesItem` — store identifier and total units sold.

#### 2. `backend/app/services/analysis.py` (New)

Pandas calculation engine with file-modification-time caching:

- `get_active_dataset_with_cache()` — loads the cleaned dataset (falling back to raw) and caches the DataFrame in a module-level dictionary keyed by the file's `os.path.getmtime` timestamp. Avoids redundant disk reads across multiple endpoints within the same request cycle.
- `calculate_sales_summary()` — computes total, mean, min, and max of `Units Sold`; counts distinct products, stores, and dates from mapped columns; labels the average explicitly as *per record*.
- `calculate_monthly_sales()` — groups the dataset by calendar month (`YYYY-MM`), sums `Units Sold`, and returns results sorted chronologically. Monthly totals reconcile exactly with the total from the summary endpoint.
- `calculate_product_sales()` — groups by mapped product identifier column, sums and sorts in descending order of total units sold, includes category and percentage share.
- `calculate_category_sales()` — groups by category column, sums and sorts descending.
- `calculate_store_sales()` — groups by store identifier column, sums and sorts descending.

All functions raise `FileNotFoundError` when no dataset is available and `ValueError` when a required column mapping is missing. Neither raw stack traces nor internal file paths are exposed to the caller.

#### 3. `backend/app/routes/analysis.py` (New)

FastAPI router with 5 GET endpoints:

| Endpoint | Route | Response Model |
|---|---|---|
| Sales summary | `GET /api/analysis/summary` | `AnalysisSummaryResponse` |
| Monthly sales | `GET /api/analysis/monthly` | `List[MonthlySalesItem]` |
| Product sales | `GET /api/analysis/products` | `List[ProductSalesItem]` |
| Category sales | `GET /api/analysis/categories` | `List[CategorySalesItem]` |
| Store sales | `GET /api/analysis/stores` | `List[StoreSalesItem]` |

Each endpoint maps:
- `FileNotFoundError` → HTTP 404 with a user-friendly "no dataset" message.
- `ValueError` → HTTP 400 with the specific mapping problem.
- Any other exception → HTTP 500 with a generic message (no stack traces).

#### 4. `backend/app/main.py` (Modified)

Registered the analysis router under the `/api/analysis` prefix. No other changes to existing Milestone 1–3 routes.

---

### Frontend Modules (`frontend/src/`)

#### 5. `frontend/src/services/api.js` (Modified)

Added two new API client helper functions:
- `getCategorySales()` — calls `GET /api/analysis/categories`.
- `getStoreSales()` — calls `GET /api/analysis/stores`.

Pre-existing functions `getSalesSummary()`, `getMonthlySales()`, and `getProductSales()` were already present; no changes made to them.

#### 6. `frontend/src/pages/SalesAnalysis.jsx` (Replaced)

Replaced the 20-line placeholder with a fully functional React component:

- **State management:** Separate `useState` hooks for summary, monthly, products, categories, stores, loading, errors, and no-dataset flag.
- **Data fetching:** `useEffect` fetches summary first to detect a missing dataset early; remaining 4 endpoints are fetched in parallel using `Promise.allSettled` so a failure in one section does not block others.
- **No-dataset state:** Renders an Upload icon, a friendly message, and a "Go to Dataset Upload" button (calls `setActiveTab('dataset')`) when the summary endpoint returns HTTP 404.
- **Loading state:** Full-page spinner with `Loader2` icon (lucide-react) while data is being fetched.
- **Summary section:** 4 primary stat cards (Total Units Sold, Avg Units per Record, Max Units, Min Units) and up to 3 metadata cards (Distinct Products, Distinct Stores, Distinct Dates).
- **Monthly trend chart:** Recharts `LineChart` inside a `ResponsiveContainer`. X-axis interval auto-calculated based on data density. Labeled axes, custom dark-themed tooltip.
- **Product section:** Horizontal Recharts `BarChart` with a colour-coded `Cell` per bar, followed by a compact sortable-looking table showing product identifier, category, total units, and percentage share.
- **Category and store sections:** Two side-by-side vertical `BarChart` components in a responsive grid.
- **Error handling:** Per-section `ErrorBanner` using `AlertCircle` icon for isolated failures (e.g., categories endpoint failing does not remove the monthly chart).
- **No new libraries:** Uses only Recharts, lucide-react, and axios — all already installed.

#### 7. `frontend/src/App.jsx` (Modified)

Passes `setActiveTab` prop to `<SalesAnalysis>` so the no-dataset state button can navigate the user to the Dataset page without React Router.

---

### Test Suite (`backend/tests/`)

#### 8. `backend/tests/test_milestone4.py` (New)

7 automated pytest tests:

| Test | What it verifies |
|---|---|
| `test_health_endpoint_still_operational` | `/api/health` continues to return `healthy` after Milestone 4 changes |
| `test_analysis_summary_metrics` | Total units sold matches direct Pandas sum; record count is correct; avg is total ÷ count; min ≤ avg ≤ max |
| `test_monthly_sales_reconciliation_and_chronology` | Sum of all monthly totals equals the total from `/api/analysis/summary`; months are in chronological order (`YYYY-MM` string sort) |
| `test_product_sales_reconciliation_and_sorting` | Sum of all product totals equals the global total; results sorted descending by total units sold |
| `test_category_sales_reconciliation` | Sum of category totals equals global total |
| `test_store_sales_reconciliation` | Sum of store totals equals global total |
| `test_no_dataset_handling` | All 5 endpoints return HTTP 404 when dataset files are temporarily renamed |

---

## 3. Empirical Test Results

### Automated Pytest Execution (Final Run)

```text
platform win32 -- Python 3.10.5, pytest-9.2.0, pluggy-1.7.0

tests/test_milestone3.py::test_health_endpoint                              PASSED  [  6%]
tests/test_milestone3.py::test_upload_invalid_extension                     PASSED  [ 12%]
tests/test_milestone3.py::test_upload_empty_csv                             PASSED  [ 18%]
tests/test_milestone3.py::test_upload_corrupted_csv                         PASSED  [ 25%]
tests/test_milestone3.py::test_upload_retail_store_inventory_csv            PASSED  [ 31%]
tests/test_milestone3.py::test_get_dataset_summary                          PASSED  [ 37%]
tests/test_milestone3.py::test_update_column_mappings                       PASSED  [ 43%]
tests/test_milestone3.py::test_clean_dataset_execution                      PASSED  [ 50%]
tests/test_milestone3.py::test_download_cleaned_csv                         PASSED  [ 56%]
tests/test_milestone4.py::test_health_endpoint_still_operational            PASSED  [ 62%]
tests/test_milestone4.py::test_analysis_summary_metrics                     PASSED  [ 68%]
tests/test_milestone4.py::test_monthly_sales_reconciliation_and_chronology  PASSED  [ 75%]
tests/test_milestone4.py::test_product_sales_reconciliation_and_sorting     PASSED  [ 81%]
tests/test_milestone4.py::test_category_sales_reconciliation                PASSED  [ 87%]
tests/test_milestone4.py::test_store_sales_reconciliation                   PASSED  [ 93%]
tests/test_milestone4.py::test_no_dataset_handling                          PASSED  [100%]

======================== 16 passed, 1 warning in 10.54s ========================
```

> **Note:** The `StarletteDeprecationWarning` is emitted by the installed `fastapi` test client package itself, not by SmartStock code. It has no effect on functionality.

### Data Reconciliation (retail_store_inventory.csv)

| Metric | Value |
|---|---|
| Total records | 73,100 |
| Total units sold | 9,975,582 |
| Average units sold per record | ≈ 136.46 |
| Min units sold (single record) | 1 |
| Max units sold (single record) | 300 |
| Distinct products | 20 |
| Distinct stores | 5 |
| Distinct dates | 731 |
| Sum of all monthly totals | 9,975,582 ✓ |
| Sum of all product totals | 9,975,582 ✓ |
| Sum of all category totals | 9,975,582 ✓ |
| Sum of all store totals | 9,975,582 ✓ |

All aggregations reconcile exactly with the global total. No phantom records or rounding errors.

### Frontend Production Build

```text
vite v8.3.0 building client environment for production...
✓ 2516 modules transformed.

dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-DPIFgiME.css   41.72 kB │ gzip:   6.94 kB
dist/assets/index-D0IqqP9_.js   697.83 kB │ gzip: 208.67 kB

✓ built in 7.87s
```

> **Note on bundle size:** The increase from Milestone 3 (312 kB) to Milestone 4 (698 kB) is caused by Recharts being actively used in SalesAnalysis.jsx for the first time. Recharts is a declared project dependency. No new libraries were added.

### Live Server Spot-Checks

```json
GET /api/health
{
  "status": "healthy",
  "database": "connected",
  "ml_models": "not_loaded"
}

GET /api/analysis/summary
{
  "total_units_sold": 9975582,
  "avg_units_sold_per_record": 136.46,
  "min_units_sold": 1,
  "max_units_sold": 300,
  "total_records": 73100,
  "distinct_products": 20,
  "distinct_stores": 5,
  "distinct_dates": 731
}

GET /api/analysis/monthly  →  24 items, Jan 2022 … Jan 2024, sum = 9,975,582
GET /api/analysis/products →  20 items, sorted descending, sum = 9,975,582
GET /api/analysis/categories → items per category, sum = 9,975,582
GET /api/analysis/stores →  5 items (Store 1–5), sum = 9,975,582
```

---

## 4. Verification Checklist & Compliance

- [x] `GET /api/analysis/summary` returns total, avg/record, min, max, record count, distinct products, stores, dates.
- [x] Average is labelled as **per record**, not as a daily or any other misleading average.
- [x] `GET /api/analysis/monthly` returns results in chronological order; monthly sum reconciles with global total.
- [x] `GET /api/analysis/products` returns results sorted descending by total units sold; product sum reconciles.
- [x] `GET /api/analysis/categories` returns category totals reconciling with global total.
- [x] `GET /api/analysis/stores` returns store totals reconciling with global total.
- [x] All 5 endpoints return HTTP 404 with a friendly message when no dataset is uploaded.
- [x] No raw Python stack traces exposed in any API response.
- [x] File-modification-time caching avoids redundant dataset reads across endpoints.
- [x] SalesAnalysis.jsx shows summary stat cards, monthly line chart, product bar chart + table, category chart, store chart.
- [x] Loading spinner displayed while data is being fetched.
- [x] Per-section error banners shown on individual endpoint failures.
- [x] No-dataset state shows a clear message and a navigation button to the Dataset page.
- [x] No hardcoded demo data used — all values come from live backend responses.
- [x] No new frontend libraries added.
- [x] Frontend production build succeeds (exit code 0).
- [x] All 9 Milestone 3 tests still pass (no regressions).
- [x] All 7 Milestone 4 tests pass.
- [x] **Zero Milestone 5+ features prematurely implemented** (No feature engineering, no lag features, no ML training, no forecasting, no inventory logic).

---

## 5. Known Limitations & Notes

| Item | Detail |
|---|---|
| Bundle size warning | Vite warns that the JS bundle exceeds 500 kB. This is caused by Recharts and is not an error. The build still succeeds. |
| StarletteDeprecationWarning | Emitted by the installed `fastapi` test-client package. Not a SmartStock code issue. |
| No interactive filtering | Sales analysis charts show the full dataset only. Per-product or per-store filtering is a Milestone 5+ concern. |
| Column mapping dependency | Analysis endpoints depend on the column role mappings saved during Milestone 3. If a new CSV is uploaded without mapping columns, endpoints return a clear HTTP 400 error. |

---

## 6. Final Status

- **Status:** **MILESTONE 4 COMPLETED, VERIFIED & READY FOR REVIEW**
- **Next Step:** Await user review and approval before proceeding to Milestone 5 (Feature Engineering).

