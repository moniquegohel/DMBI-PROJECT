# SMARTSTOCK — MILESTONE 5: FEATURE ENGINEERING VERIFICATION REPORT

> **Milestone:** Milestone 5 — Feature Engineering  
> **Status:** Verified & Completed  
> **Date:** October 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 5 implemented the complete **Feature Engineering Pipeline** for SMARTSTOCK, bridging historical sales analysis (Milestone 4) and predictive model training (Milestone 6).

The primary objectives were:
1. Transform the active cleaned retail dataset (`cleaned_dataset.csv`, falling back to `raw_dataset.csv`) into a structured ML-ready dataset (`ml_dataset.csv`).
2. Generate core calendar features from transaction dates: `day` (1–31), `day_of_week` (Monday=0 to Sunday=6), `month` (1–12), and `is_weekend` (0 or 1).
3. Generate sales-history features within each independent store-product series: `previous_day_sales` (lag-1) and `rolling_7_day_average` (7-day historical rolling average).
4. Enforce strict **data-leakage prevention**: lag and rolling features use a shift-then-roll approach so that current-day or future sales never leak into predictors.
5. Exclude columns that introduce target leakage or are unavailable at prediction time (`Demand Forecast`, `Inventory Level`, `Units Ordered`), with explicit domain justifications.
6. Preserve initial rows without artificial synthetic filling; document and report null/NaN counts.
7. Expose the feature engineering pipeline through FastAPI REST endpoints under `/api/model/features/`.
8. Implement an interactive frontend dashboard on the **Model Training** tab to trigger feature generation, inspect the column catalogue (Metadata, Predictors, Target, Excluded), and preview the ML dataset.
9. Verify all calculations with unit tests, including deterministic hand-checked numerical tests and regression tests for earlier milestones.
10. Ensure zero premature implementation of Milestone 6+ features (no model training, no demand forecasting).

---

## 2. File Inventory & Technical Implementation

### Backend Architecture (`backend/app/`)

#### 1. `backend/app/schemas/features.py` (New)
* Defined Pydantic models for type safety and API serialization:
  - `FeatureColumnInfo`: Metadata for each column in the ML dataset (`name`, `role` as predictor/metadata/target, `description`, and `null_count`).
  - `FeatureEngineeringResult`: Full generation response containing status, input row count, output row count, output column count, feature catalogue, predictor list, metadata list, target name, lag/rolling NaN counts, excluded columns with reasons, 10-row preview, and day-of-week / weekend encoding descriptions.
  - `FeatureEngineeringStatus`: Lightweight status object reporting if `ml_dataset.csv` exists and its dimensions.

#### 2. `backend/app/services/feature_engineering.py` (New)
* Implemented the feature engineering engine:
  - `_resolve_mappings(df)`: Maps columns dynamically to semantic retail roles (`date`, `store_id`, `product_id`, `units_sold`, `promotion`, `price`, `discount`).
  - `run_feature_engineering()`:
    1. Loads source dataset (`cleaned_dataset.csv` or `raw_dataset.csv`) dynamically.
    2. Validates required mappings (`Date` and `Units Sold`).
    3. Chronologically sorts data by `Store ID`, `Product ID`, and `Date`.
    4. Computes calendar date features: `day`, `day_of_week` (0–6), `month`, `is_weekend`.
    5. Groups by `(Store ID, Product ID)` and applies shift-then-roll:
       - `previous_day_sales = s.shift(1)`
       - `rolling_7_day_average = s.shift(1).rolling(window=7, min_periods=1).mean()`
    6. Incorporates optional predictors if present: `promotion`, `price`, `discount`.
    7. Retains metadata columns (`Date`, `Store ID`, `Product ID`) and target (`Units Sold`).
    8. Identifies and records exclusions: `Demand Forecast`, `Inventory Level`, `Units Ordered`.
    9. Saves ML dataset to `backend/data/ml_dataset.csv` (idempotent overwrite).
    10. Produces sanitized 10-row preview and full catalogue.
  - `get_feature_engineering_status()`: Inspects `ml_dataset.csv` presence and row count efficiently without full re-computation.

#### 3. `backend/app/routes/model.py` (New)
* Exposed REST endpoints:
  - `POST /api/model/features/generate`: Runs the feature engineering pipeline.
  - `GET /api/model/features/status`: Returns current ML dataset existence and row/column counts.
  - `GET /api/model/features/preview`: Re-generates/returns fresh feature summary and 10-row preview.
* Error handling maps `FileNotFoundError` to HTTP 404 and `ValueError` to HTTP 400 without exposing stack traces.

#### 4. `backend/app/main.py` (Modified)
* Mounted `model_router` under prefix `/api/model` with tag `model`.

---

### Frontend Architecture (`frontend/src/`)

#### 5. `frontend/src/services/api.js` (Modified)
* Exported API client helper functions:
  - `generateFeatures()` -> `POST /api/model/features/generate`
  - `getFeaturesStatus()` -> `GET /api/model/features/status`
  - `getFeaturesPreview()` -> `GET /api/model/features/preview`

#### 6. `frontend/src/pages/ModelTraining.jsx` (Replaced)
* Replaced placeholder with complete feature engineering dashboard:
  - **Pipeline Progress Tracker**: Highlights current stage ("Feature Engineering ◀ you are here").
  - **Generate Features Action Card**: Trigger button with live spinner (`generating...`), idempotency guarantee, and leakage prevention note.
  - **Summary Stat Cards**: Input Rows, Output Rows, ML Columns, Lag-1 NaNs, Rolling-7 NaNs.
  - **Encoding Legend**: Explicitly states `Monday=0 … Sunday=6` and `is_weekend` (0=weekday, 1=weekend).
  - **Role-Classified Column Catalogue**:
    - Metadata columns (`Date`, `Store ID`, `Product ID`)
    - Predictor columns with descriptions and NaN badge tags
    - Target column (`Units Sold`) highlighted in emerald
    - Excluded columns (`Demand Forecast`, `Inventory Level`, `Units Ordered`) with explicit reasons.
  - **10-Row Interactive Preview Table**: Expandable/collapsible table displaying real data from `ml_dataset.csv`.
  - **No-Dataset State**: Guides user with button navigation to Dataset Upload page if no data is uploaded.
  - **Milestone 6 Preview Note**: Informs the user that model training (Linear Regression and Random Forest) will occur here in the next milestone.

#### 7. `frontend/src/App.jsx` (Modified)
* Passed `setActiveTab` to `<ModelTraining setActiveTab={setActiveTab} />` for tab navigation from the no-dataset state.

---

### Test Suite (`backend/tests/`)

#### 8. `backend/tests/test_milestone5.py` (New)
* 14 automated pytest tests verifying:
  - `test_date_features_values_and_types`: Checks `day`, `day_of_week` (Monday=0), `month`, `is_weekend`.
  - `test_previous_day_sales_within_group_no_bleed`: Verifies lag-1 stays strictly within product/store groups.
  - `test_rolling_7day_average_no_current_row_leakage`: Verifies shift-then-roll prevents today's sales from leaking into rolling average.
  - `test_deterministic_lag_rolling_hand_check`: Mathematical hand-check on small deterministic dataset (5 days, 2 products).
  - `test_initial_nan_rows_preserved`: Verifies initial group rows remain `NaN` and row count is not reduced.
  - `test_output_is_chronological_within_group`: Verifies chronological sorting per series.
  - `test_optional_columns_absent_does_not_crash`: Verifies pipeline runs even if optional columns (like `Store ID` or `Price`) are absent.
  - `test_missing_date_mapping_raises_value_error`: Verifies clear 400 error on missing required mappings.
  - `test_demand_forecast_excluded_from_predictors`: Verifies `Demand Forecast` is excluded.
  - `test_re_run_does_not_duplicate_rows_or_columns`: Verifies idempotency.
  - `test_health_endpoint_still_operational`: Verifies `/api/health` returns healthy.
  - `test_milestone5_feature_generate_endpoint_no_dataset`: Tests API endpoint status code behavior.
  - `test_milestone5_status_endpoint_registered`: Verifies GET `/api/model/features/status`.
  - `test_milestone5_preview_endpoint_registered`: Verifies GET `/api/model/features/preview`.

---

## 3. Empirical Test Results

### Full Pytest Suite (All Milestones 3, 4, 5)

```text
platform win32 -- Python 3.10.5, pytest-9.2.0, pluggy-1.7.0 -- .venv\Scripts\python.exe
collected 30 items

tests/test_milestone3.py::test_health_endpoint PASSED                    [  3%]
tests/test_milestone3.py::test_upload_invalid_extension PASSED           [  6%]
tests/test_milestone3.py::test_upload_empty_csv PASSED                   [ 10%]
tests/test_milestone3.py::test_upload_corrupted_csv PASSED               [ 13%]
tests/test_milestone3.py::test_upload_retail_store_inventory_csv PASSED  [ 16%]
tests/test_milestone3.py::test_get_dataset_summary PASSED                [ 20%]
tests/test_milestone3.py::test_update_column_mappings PASSED             [ 23%]
tests/test_milestone3.py::test_clean_dataset_execution PASSED            [ 26%]
tests/test_milestone3.py::test_download_cleaned_csv PASSED               [ 30%]
tests/test_milestone4.py::test_health_endpoint_still_operational PASSED  [ 33%]
tests/test_milestone4.py::test_analysis_summary_metrics PASSED           [ 36%]
tests/test_milestone4.py::test_monthly_sales_reconciliation_and_chronology PASSED [ 40%]
tests/test_milestone4.py::test_product_sales_reconciliation_and_sorting PASSED [ 43%]
tests/test_milestone4.py::test_category_sales_reconciliation PASSED      [ 46%]
tests/test_milestone4.py::test_store_sales_reconciliation PASSED         [ 50%]
tests/test_milestone4.py::test_no_dataset_handling PASSED                [ 53%]
tests/test_milestone5.py::test_date_features_values_and_types PASSED     [ 56%]
tests/test_milestone5.py::test_previous_day_sales_within_group_no_bleed PASSED [ 60%]
tests/test_milestone5.py::test_rolling_7day_average_no_current_row_leakage PASSED [ 63%]
tests/test_milestone5.py::test_deterministic_lag_rolling_hand_check PASSED [ 66%]
tests/test_milestone5.py::test_initial_nan_rows_preserved PASSED         [ 70%]
tests/test_milestone5.py::test_output_is_chronological_within_group PASSED [ 73%]
tests/test_milestone5.py::test_optional_columns_absent_does_not_crash PASSED [ 76%]
tests/test_milestone5.py::test_missing_date_mapping_raises_value_error PASSED [ 80%]
tests/test_milestone5.py::test_demand_forecast_excluded_from_predictors PASSED [ 83%]
tests/test_milestone5.py::test_re_run_does_not_duplicate_rows_or_columns PASSED [ 86%]
tests/test_milestone5.py::test_health_endpoint_still_operational PASSED  [ 90%]
tests/test_milestone5.py::test_milestone5_feature_generate_endpoint_no_dataset PASSED [ 93%]
tests/test_milestone5.py::test_milestone5_status_endpoint_registered PASSED [ 96%]
tests/test_milestone5.py::test_milestone5_preview_endpoint_registered PASSED [100%]

======================== 30 passed, 1 warning in 9.38s ========================
```

### Full-Scale Dataset Execution Metrics (`retail_store_inventory.csv`)

| Metric | Measured Value | Analysis / Compliance |
|---|---|---|
| **Input Rows** | 73,100 | Exact match with cleaned dataset |
| **Output Rows** | 73,100 | Exact match; 0 rows dropped or lost |
| **ML Output Columns** | 13 | 3 metadata + 9 predictors + 1 target |
| **Lag NaNs (`previous_day_sales`)** | 100 | Exactly 1 per series (5 stores × 20 products = 100 series) |
| **Rolling NaNs (`rolling_7_day_average`)** | 100 | Exactly 1 per series (min_periods=1 allows partial window from day 2) |
| **Target Column** | `Units Sold` | Mapped demand target |
| **Predictor Columns** | `day`, `day_of_week`, `month`, `is_weekend`, `previous_day_sales`, `rolling_7_day_average`, `promotion`, `price`, `discount` | Core calendar + lag + retail context |
| **Metadata Columns** | `Date`, `Store ID`, `Product ID` | Preserved for series identification & split |
| **Excluded Columns** | `Demand Forecast`, `Inventory Level`, `Units Ordered` | Leakage & timing risks eliminated |
| **Output File Size** | 4.99 MB | `backend/data/ml_dataset.csv` |

### Frontend Production Build

```text
vite v8.3.0 building client environment for production...
transforming...
✓ 2516 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-GZ21vPaa.css   44.66 kB │ gzip:   7.37 kB
dist/assets/index-CrNW76GU.js   711.75 kB │ gzip: 211.44 kB
✓ built in 2.58s
```

---

## 4. Verification Checklist & Compliance

- [x] Date features generated: `day` (1–31), `day_of_week` (Monday=0 to Sunday=6), `month` (1–12), `is_weekend` (0 or 1).
- [x] Day-of-week encoding explicitly documented in schemas and displayed in UI.
- [x] `previous_day_sales` calculated strictly within store-product groups (zero cross-series contamination).
- [x] `rolling_7_day_average` uses shift-then-roll, guaranteeing zero current-day target leakage.
- [x] Deterministic mathematical hand-checked test verifies lag and rolling calculation precision.
- [x] Initial missing lag/rolling values preserved with `NaN` (no artificial synthetic averages or dropped rows).
- [x] Output ordering is deterministic and chronological within each store-product series.
- [x] Optional columns (`Store ID`, `Price`, etc.) can be absent without breaking pipeline.
- [x] Missing required mappings (`Date`, `Units Sold`) return clear HTTP 400 errors.
- [x] `Demand Forecast`, `Inventory Level`, and `Units Ordered` are excluded from predictors with domain justifications.
- [x] Idempotent re-runs: re-generating features overwrites `ml_dataset.csv` without duplicating rows or columns.
- [x] Milestones 1–4 remain 100% functional (all 30 tests pass).
- [x] Frontend production build succeeds (`vite build`, exit code 0).
- [x] **Zero Milestone 6+ features implemented** (no ML model training, no demand forecasting, no inventory logic).

---

## 5. Final Status

* **Status:** **MILESTONE 5 COMPLETED, VERIFIED & READY FOR REVIEW**
* **Next Step:** Await user review and approval before proceeding to Milestone 6 (Model Training).

