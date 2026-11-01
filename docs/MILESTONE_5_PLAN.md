# SMARTSTOCK — MILESTONE 5 IMPLEMENTATION PLAN: FEATURE ENGINEERING

> **Milestone:** Milestone 5 — Feature Engineering  
> **Status:** Plan Prepared & Awaiting Review  
> **Date:** October 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objective

The objective of Milestone 5 is to implement a reproducible, transparent, and leakage-safe **Feature Engineering Pipeline** for SMARTSTOCK.

The pipeline takes the active cleaned retail dataset (`cleaned_dataset.csv`, falling back to `raw_dataset.csv`) and generates an ML-ready dataset (`ml_dataset.csv`) with:
1. **Calendar date features**: `day`, `day_of_week` (Monday=0 to Sunday=6), `month`, and `is_weekend` (binary 0/1).
2. **Sales-history features**: `previous_day_sales` (lag-1) and `rolling_7_day_average` (7-day historical rolling average).
3. **Strict data-leakage protection**: Uses a shift-then-roll calculation per store-product group so current and future sales never leak into predictors.
4. **Transparent null handling**: Preserves initial rows with `NaN` rather than inventing synthetic numbers, and reports null counts.
5. **Column categorization**: Explicitly classifies all attributes as Metadata, Predictors, Target (`Units Sold`), or Excluded (`Demand Forecast`, `Inventory Level`, `Units Ordered`).
6. **Frontend inspection**: Allows the user to trigger feature generation and inspect the feature catalogue and preview in the `Model Training` tab.

> **Strict Scope Boundary:** Milestone 5 covers feature engineering only. Model training (Linear Regression, Random Forest), model evaluation (MAE, RMSE, MAPE), demand forecasting, and inventory simulation belong to Milestones 6–10 and will **not** be implemented here.

---

## 2. Dataset Context & Leakage Prevention Rules

Based on the development dataset `retail_store_inventory.csv` (73,100 records across 5 stores and 20 products):

| Concept | Rule / Specification | Rationale |
|---|---|---|
| **Target Column** | `Units Sold` | True historical sales volume to forecast in Milestone 6. |
| **Grouping Key** | `(Store ID, Product ID)` | Prevents sales from Store 1 / Product A from polluting Store 2 / Product B. |
| **Chronological Sort** | Sorted by `Store ID`, `Product ID`, `Date` | Mandatory before computing time-series lags and rolling windows. |
| **Lag-1 (`previous_day_sales`)** | `sales.shift(1)` within each group | Previous day's actual units sold. Initial row per group is `NaN`. |
| **Rolling-7 (`rolling_7_day_average`)** | `sales.shift(1).rolling(7, min_periods=1).mean()` | Average of previous 7 observations. Excludes current-day sales completely. |
| **Excluded: `Demand Forecast`** | Excluded from predictors | High correlation with target (~0.997) + 673 negative values; would constitute target leakage. |
| **Excluded: `Inventory Level`** | Excluded from predictors | Represents end-of-day stock after sales occur; not available at forecast time. |
| **Excluded: `Units Ordered`** | Excluded from predictors | Represents replenishment orders placed in response to daily sales; future-looking. |
| **Optional Predictors** | `Price`, `Discount`, `Holiday/Promotion` | Included if present in column mappings; available at prediction time. |
| **Initial Rows** | Preserved with `NaN` | Output row count matches input exactly (73,100). Null counts are tracked. |
| **Repeatability** | Overwrites `ml_dataset.csv` cleanly | Repeated runs are idempotent; no duplicate columns or duplicate rows. |

---

## 3. Architecture & File Inventory

### Backend Components

1. **`backend/app/schemas/features.py` (New)**:
   - `FeatureColumnInfo`: Schema describing name, role (`predictor`, `metadata`, `target`), description, and `null_count`.
   - `FeatureEngineeringResult`: Complete response object containing status, row counts, predictor list, metadata list, target name, null counts, excluded columns with reasons, 10-row preview, and encoding documentation.
   - `FeatureEngineeringStatus`: Lightweight status object reporting if `ml_dataset.csv` exists and its dimensions.

2. **`backend/app/services/feature_engineering.py` (New)**:
   - Dynamic path resolution referencing `app.services.data_cleaning` so tests can redirect paths cleanly.
   - `run_feature_engineering()`: Validates mappings, sorts chronologically, engineers calendar and lag/rolling features, writes `ml_dataset.csv`, and returns `FeatureEngineeringResult`.
   - `get_feature_engineering_status()`: Checks presence and dimensions of `ml_dataset.csv`.

3. **`backend/app/routes/model.py` (New)**:
   - `POST /api/model/features/generate`: Runs feature engineering.
   - `GET /api/model/features/status`: Returns current status.
   - `GET /api/model/features/preview`: Returns cached/generated summary and 10-row preview.

4. **`backend/app/main.py` (Modified)**:
   - Register `model_router` under prefix `/api/model`.

### Frontend Components

5. **`frontend/src/services/api.js` (Modified)**:
   - Added `generateFeatures()`, `getFeaturesStatus()`, and `getFeaturesPreview()`.

6. **`frontend/src/pages/ModelTraining.jsx` (Modified)**:
   - Replaces placeholder with feature engineering dashboard:
     - Pipeline stage banner ("Feature Engineering ◀ you are here").
     - "Generate Features" action button with live loader.
     - Summary stat cards: Input Rows, Output Rows, ML Columns, Lag-1 NaNs, Rolling-7 NaNs.
     - Column catalogue cards: Metadata, Predictors (with descriptions and NaN counts), Target, and Excluded columns.
     - 10-row interactive preview table of `ml_dataset.csv`.
     - Alert banner detailing data-leakage safeguards.
     - No-dataset guidance with link to Dataset page.
     - Preview notice for Milestone 6 (Model Training).

7. **`frontend/src/App.jsx` (Modified)**:
   - Passes `setActiveTab` to `<ModelTraining setActiveTab={setActiveTab} />`.

### Test Suite

8. **`backend/tests/test_milestone5.py` (New)**:
   - 11 automated test cases verifying:
     - Date feature calculation and Monday=0 encoding.
     - Group-isolated `previous_day_sales` without cross-series bleed.
     - Shift-then-roll `rolling_7_day_average` with zero current-day leakage.
     - Deterministic hand-checked mathematical verification.
     - Initial `NaN` row preservation and counting.
     - Deterministic chronological sorting.
     - Resilience when optional columns are absent.
     - Clear validation error when date or sales mapping is missing.
     - Exclusion of `Demand Forecast` from predictors.
     - Idempotency on repeated execution.
     - Regression protection for `/api/health` and Milestones 1–4.

---

## 4. Verification & Testing Strategy

### Automated Backend Tests
Run the complete test suite across Milestones 3, 4, and 5:
```powershell
cd "c:\Users\moniq\OneDrive\Documents\Documents\School\College\DMBI PROJECT\backend"
& "c:\Users\moniq\OneDrive\Documents\Documents\School\College\DMBI PROJECT\.venv\Scripts\python.exe" -m pytest tests/ -v
```
**Goal:** 100% pass rate across all test files (approx. 27+ tests total).

### Frontend Production Build
Validate bundle compilation and syntax:
```powershell
cd "c:\Users\moniq\OneDrive\Documents\Documents\School\College\DMBI PROJECT\frontend"
npm run build
```
**Goal:** Build succeeds with exit code 0.

### Live Functional Verification
1. Start backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
2. Open frontend at `http://localhost:5173/`
3. Navigate to **Model Training** tab
4. Click **Generate Features**
5. Verify that:
   - 73,100 rows are processed.
   - Exactly 100 `previous_day_sales` NaNs are found (1 per store-product series across 5 stores × 20 products).
   - Column catalogue displays metadata, predictors, target, and exclusions with clear explanations.
   - 10-row preview displays real data from `ml_dataset.csv`.

---

## 5. Next Steps

Upon your review and approval of this plan:
1. Update `backend/app/services/feature_engineering.py` with dynamic path resolution.
2. Update `backend/tests/test_milestone5.py` with clean fixture isolation.
3. Run the full test suite (`pytest tests/ -v`) and verify all tests pass.
4. Run the frontend build (`npm run build`) and verify it compiles cleanly.
5. Provide the final Milestone 5 verification report and documentation.

