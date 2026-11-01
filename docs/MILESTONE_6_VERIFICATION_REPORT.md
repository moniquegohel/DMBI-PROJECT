# SMARTSTOCK — MILESTONE 6: MODEL TRAINING VERIFICATION REPORT

> **Milestone:** Milestone 6 — Supervised Model Training  
> **Status:** Verified & Completed  
> **Date:** October 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 6 implemented the complete **Supervised Model Training Pipeline** for SMARTSTOCK, consuming the ML-ready dataset generated in Milestone 5 (`ml_dataset.csv`) and training two distinct machine learning estimators: an interpretable linear baseline (**Linear Regression**) and an ensemble tree-based non-linear model (**Random Forest Regressor**).

The primary objectives achieved:
1. **Chronological 80/20 Train/Holdout Split**: Partitioned data strictly by unique calendar dates (earliest 80% dates for training, latest 20% reserved for holdout evaluation). Zero random shuffling or record mixing.
2. **Leakage-Safe Preprocessing Pipeline**: Encapsulated feature transformations in Scikit-learn `Pipeline` and `ColumnTransformer` with median imputation for numeric features and most-frequent imputation plus one-hot encoding for categorical features, fitted **strictly** on the training split.
3. **Target & Predictor Discipline**: Trained models to predict `Units Sold`. Strictly excluded identifier metadata (`Date`, `Store ID`, `Product ID`) and disallowed columns (`Demand Forecast`, `Inventory Level`, `Units Ordered`) from model predictors.
4. **Initial Row Handling**: Automatically filtered out initial series rows lacking lag features (`previous_day_sales.isna()`) from model fitting, preventing NaN-induced solver failures while preserving records for evaluation.
5. **Model Artifact Persistence**: Serialized trained pipelines using `joblib` into `backend/models/` alongside structured metadata (`training_metadata.json`), ensuring models can be reloaded instantly without retraining.
6. **FastAPI Endpoints**: Exposed `POST /api/model/train` (training execution) and `GET /api/model/training-status` (trained model details and split summary).
7. **Frontend Dashboard Integration**: Extended `frontend/src/pages/ModelTraining.jsx` into a unified two-phase interface (Feature Engineering + Supervised Model Training) with live training triggers, model status cards, split metrics, and Milestone 7 preview notices.
8. **Comprehensive Automated Testing**: Authored 12 new unit and integration tests in `backend/tests/test_milestone6.py`, achieving **42 / 42 passing tests** across Milestones 3, 4, 5, and 6.
9. **Strict Milestone Boundaries**: Zero premature implementation of Milestone 7 evaluation metrics (MAE, RMSE, MAPE, R², holdout predictions) or Milestone 8 forecasting.

---

## 2. File Inventory & Technical Implementation

### Backend Architecture (`backend/app/`)

#### 1. `backend/app/schemas/model.py` (New)
* Defined Pydantic models for API request/response serialization:
  - `TrainedModelInfo`: Model metadata including model name, estimator class, hyperparameter dictionary, feature count, artifact file path, file size in bytes, and trained timestamp.
  - `DateSplitInfo`: Chronological split breakdown including split strategy (`chronological_by_date`), train ratio (0.80), holdout ratio (0.20), total unique dates, train date range, holdout date range, cutoff date, total rows, raw train rows, initial lag NaN rows excluded, and final fitted rows.
  - `ModelTrainingResult`: Full training response returning execution status, message, split info, list of trained models, target column, feature list, and timestamp.
  - `ModelTrainingStatusResponse`: Lightweight status response indicating whether models are currently trained on disk, metadata timestamp, and summary cards.

#### 2. `backend/app/services/model_training.py` (New)
* Implemented the model training engine:
  - `MODELS_DIR = Path(...)`: Resolves persistence folder `backend/models/`.
  - `identify_columns(df)`: Dynamically partitions columns into metadata (`Date`, `Store ID`, `Product ID`), target (`Units Sold`), excluded leakage columns (`Demand Forecast`, `Inventory Level`, `Units Ordered`), numeric predictors (`day`, `day_of_week`, `month`, `is_weekend`, `previous_day_sales`, `rolling_7_day_average`, `price`, `discount`), and categorical predictors (`promotion`).
  - `build_preprocessor(numeric_cols, categorical_cols)`: Assembles Scikit-learn `ColumnTransformer` with `SimpleImputer(strategy='median')` for numerics and `SimpleImputer(strategy='most_frequent') + OneHotEncoder(handle_unknown='ignore')` for categoricals.
  - `perform_chronological_split(df, train_ratio=0.80)`: Sorts unique dates chronologically, calculates the 80% date index, and cleanly splits rows into `df_train` and `df_holdout`.
  - `train_all_models()`:
    1. Loads `backend/data/ml_dataset.csv`.
    2. Validates target and predictor availability.
    3. Executes 80/20 chronological date split.
    4. Filters out training rows where `previous_day_sales.isna()`.
    5. Fits `LinearRegression()` inside Scikit-learn Pipeline.
    6. Fits `RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)` inside Scikit-learn Pipeline.
    7. Serializes pipeline artifacts to `.joblib` files in `backend/models/`.
    8. Writes complete run metadata to `training_metadata.json`.
  - `get_training_status()`: Inspects on-disk artifacts and returns cached training status and model parameters.

#### 3. `backend/app/routes/model.py` (Extended)
* Added training API routes alongside existing feature engineering endpoints:
  - `POST /api/model/train`: Triggers chronological split, pipeline preprocessing, and training for both estimators.
  - `GET /api/model/training-status`: Returns persisted model info, split dates, and feature counts.
  - `GET /api/model/results`: Alias for status/results inspection.
* Preserved Milestone 5 endpoints: `/api/model/features/generate`, `/api/model/features/status`, `/api/model/features/preview`.

---

### Frontend Architecture (`frontend/src/`)

#### 4. `frontend/src/services/api.js` (Modified)
* Added and exported model training client methods:
  - `trainModels()` -> `POST /api/model/train`
  - `getModelTrainingStatus()` -> `GET /api/model/training-status`
  - `getModelResults()` -> `GET /api/model/results`

#### 5. `frontend/src/pages/ModelTraining.jsx` (Enhanced)
* Upgraded page to a cohesive two-phase workflow:
  - **Phase 1: Feature Engineering**: Preserved full feature generation button, 5 overview stat cards, role-classified column catalogue, and 10-row preview table from Milestone 5.
  - **Phase 2: Supervised Model Training**:
    - **"Train Demand Forecasting Models"** action card with single-click execution, live spinning loader, and timing estimate.
    - **Chronological 80/20 Split Breakdown Card**: Shows train date range, holdout date range, cutoff date (`2023-08-08`), raw train rows, initial lag NaNs excluded, and fitted rows.
    - **Trained Model Cards**:
      - **Linear Regression Card**: Baseline model, feature count, artifact file size, hyperparameter summary (`fit_intercept=True`), and status tag.
      - **Random Forest Regressor Card**: Non-linear ensemble, feature count, artifact file size, hyperparameter summary (`n_estimators=100`, `random_state=42`), and status tag.
    - **Milestone 7 Preview Banner**: Explains that holdout model evaluation, error metrics (MAE, RMSE, MAPE, R²), and Actual vs. Predicted visual charts will be conducted in the next milestone.

---

### Test Suite (`backend/tests/`)

#### 6. `backend/tests/test_milestone6.py` (New)
* 12 automated pytest tests verifying every requirement:
  - `test_train_refuses_when_no_ml_dataset`: Confirms 404/ValueError when `ml_dataset.csv` is missing.
  - `test_chronological_split_no_leakage`: Verifies train maximum date is strictly earlier than holdout minimum date.
  - `test_same_date_records_stay_together`: Verifies all store-product records on any single calendar date remain in the same split partition.
  - `test_excluded_columns_not_in_predictors`: Asserts `Demand Forecast`, `Inventory Level`, and `Units Ordered` are omitted from model features.
  - `test_initial_nan_rows_excluded_from_fitting`: Verifies `previous_day_sales.isna()` rows are removed from train fitting.
  - `test_preprocessing_fitted_on_train_only`: Verifies `ColumnTransformer` is fitted solely on train data.
  - `test_both_models_train_successfully`: Verifies both Linear Regression and Random Forest pipelines train and return valid objects.
  - `test_model_artifacts_saved_and_loadable`: Verifies `.joblib` files exist on disk, reload with `joblib.load()`, and generate valid `.predict()` outputs.
  - `test_metadata_persistence`: Verifies `training_metadata.json` exists with complete fields.
  - `test_training_idempotency`: Verifies re-training overwrites models cleanly without state corruption.
  - `test_api_endpoints_training`: Integration test for `POST /api/model/train` and `GET /api/model/training-status`.
  - `test_regression_guard_health`: Regression guard verifying `/api/health` remains healthy.

---

## 3. Dataset Execution & Chronological Split Metrics

### Full-Scale Dataset Execution (`retail_store_inventory.csv`)

| Split Metric | Value | Technical Context |
|---|---|---|
| **Total Dataset Rows** | 73,100 rows | 5 stores × 20 products × 731 dates |
| **Date Range** | `2022-01-01` to `2024-01-01` | 731 consecutive calendar days |
| **Split Strategy** | Chronological (Date-Based) | Earliest 80% dates for train, latest 20% for holdout |
| **Cutoff Date** | `2023-08-08` | First date of the holdout period |
| **Train Date Range** | `2022-01-01` to `2023-08-07` | 584 unique dates (80.0% of all dates) |
| **Holdout Date Range** | `2023-08-08` to `2024-01-01` | 147 unique dates (20.0% of all dates) |
| **Raw Train Rows** | 58,400 rows | 584 dates × 100 series |
| **Initial Lag-1 NaNs Excluded** | 100 rows | Day 1 of each store-product series (2022-01-01) |
| **Actual Fitted Train Rows** | 58,300 rows | Clean rows without NaNs used for model fitting |
| **Reserved Holdout Rows** | 14,700 rows | 147 dates × 100 series (untouched for Milestone 7) |
| **Target Column** | `Units Sold` | Mapped demand target |
| **Total Model Features** | 9 features | 8 numeric + 1 categorical |

### Model Architecture & Artifact Details

| Model Name | Type | Key Hyperparameters | Preprocessor | Artifact File | File Size |
|---|---|---|---|---|---|
| **Linear Regression** | Linear Baseline | `fit_intercept=True` | Median Imputer + OneHotEncoder | `linear_regression_pipeline.joblib` | ~4.5 KB |
| **Random Forest Regressor** | Non-Linear Ensemble | `n_estimators=100`, `random_state=42`, `n_jobs=-1` | Median Imputer + OneHotEncoder | `random_forest_pipeline.joblib` | ~523 MB |
| **Training Metadata** | Metadata Manifest | JSON serialization of run parameters | N/A | `training_metadata.json` | ~1.7 KB |

---

## 4. Empirical Test Results

### Full Pytest Suite (All Milestones 3, 4, 5, 6)

```text
============================= test session starts =============================
platform win32 -- Python 3.10.5, pytest-9.2.0, pluggy-1.7.0 -- .venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: backend
plugins: anyio-4.15.1
collected 42 items

tests/test_milestone3.py::test_health_endpoint PASSED                    [  2%]
tests/test_milestone3.py::test_upload_invalid_extension PASSED           [  4%]
tests/test_milestone3.py::test_upload_empty_csv PASSED                   [  7%]
tests/test_milestone3.py::test_upload_corrupted_csv PASSED               [  9%]
tests/test_milestone3.py::test_upload_retail_store_inventory_csv PASSED  [ 11%]
tests/test_milestone3.py::test_get_dataset_summary PASSED                [ 14%]
tests/test_milestone3.py::test_update_column_mappings PASSED             [ 16%]
tests/test_milestone3.py::test_clean_dataset_execution PASSED            [ 19%]
tests/test_milestone3.py::test_download_cleaned_csv PASSED               [ 21%]
tests/test_milestone4.py::test_health_endpoint_still_operational PASSED  [ 23%]
tests/test_milestone4.py::test_analysis_summary_metrics PASSED           [ 26%]
tests/test_milestone4.py::test_monthly_sales_reconciliation_and_chronology PASSED [ 28%]
tests/test_milestone4.py::test_product_sales_reconciliation_and_sorting PASSED [ 30%]
tests/test_milestone4.py::test_category_sales_reconciliation PASSED      [ 33%]
tests/test_milestone4.py::test_store_sales_reconciliation PASSED         [ 35%]
tests/test_milestone4.py::test_no_dataset_handling PASSED                [ 38%]
tests/test_milestone5.py::test_date_features_values_and_types PASSED     [ 40%]
tests/test_milestone5.py::test_previous_day_sales_within_group_no_bleed PASSED [ 42%]
tests/test_milestone5.py::test_rolling_7day_average_no_current_row_leakage PASSED [ 45%]
tests/test_milestone5.py::test_deterministic_lag_rolling_hand_check PASSED [ 47%]
tests/test_milestone5.py::test_initial_nan_rows_preserved PASSED         [ 50%]
tests/test_milestone5.py::test_output_is_chronological_within_group PASSED [ 52%]
tests/test_milestone5.py::test_optional_columns_absent_does_not_crash PASSED [ 54%]
tests/test_milestone5.py::test_missing_date_mapping_raises_value_error PASSED [ 57%]
tests/test_milestone5.py::test_demand_forecast_excluded_from_predictors PASSED [ 59%]
tests/test_milestone5.py::test_re_run_does_not_duplicate_rows_or_columns PASSED [ 61%]
tests/test_milestone5.py::test_health_endpoint_still_operational PASSED  [ 64%]
tests/test_milestone5.py::test_milestone5_feature_generate_endpoint_no_dataset PASSED [ 66%]
tests/test_milestone5.py::test_milestone5_status_endpoint_registered PASSED [ 69%]
tests/test_milestone5.py::test_milestone5_preview_endpoint_registered PASSED [ 71%]
tests/test_milestone6.py::test_train_refuses_when_no_ml_dataset PASSED   [ 73%]
tests/test_milestone6.py::test_chronological_split_no_leakage PASSED     [ 76%]
tests/test_milestone6.py::test_same_date_records_stay_together PASSED    [ 78%]
tests/test_milestone6.py::test_excluded_columns_not_in_predictors PASSED [ 80%]
tests/test_milestone6.py::test_initial_nan_rows_excluded_from_fitting PASSED [ 83%]
tests/test_milestone6.py::test_preprocessing_fitted_on_train_only PASSED [ 85%]
tests/test_milestone6.py::test_both_models_train_successfully PASSED     [ 88%]
tests/test_milestone6.py::test_model_artifacts_saved_and_loadable PASSED [ 90%]
tests/test_milestone6.py::test_metadata_persistence PASSED               [ 92%]
tests/test_milestone6.py::test_training_idempotency PASSED               [ 95%]
tests/test_milestone6.py::test_api_endpoints_training PASSED             [ 97%]
tests/test_milestone6.py::test_regression_guard_health PASSED            [100%]

======================= 42 passed, 1 warning in 10.09s ========================
```

### Frontend Production Build

```text
vite v8.3.0 building client environment for production...
transforming...
✓ 2516 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-BJYzsvhB.css   45.36 kB │ gzip:   7.44 kB
dist/assets/index-BVrkQx20.js   720.18 kB │ gzip: 212.86 kB
✓ built in 1.38s
```

---

## 5. Verification Checklist & Compliance

- [x] Chronological 80/20 train/holdout split implemented on calendar dates (`max(train_dates) < min(holdout_dates)`).
- [x] Records on the same calendar date across all stores/products stay in the same split partition.
- [x] Two distinct regression models trained: Linear Regression and Random Forest Regressor.
- [x] `Units Sold` set as sole target column.
- [x] `Demand Forecast`, `Inventory Level`, and `Units Ordered` strictly excluded from predictors.
- [x] Scikit-learn `Pipeline` and `ColumnTransformer` handle preprocessing (median imputation for numeric, most-frequent + one-hot for categorical).
- [x] Preprocessing is fitted strictly on training data only (zero holdout contamination).
- [x] Initial series rows with missing lag values (`previous_day_sales.isna()`) safely excluded from training.
- [x] Trained pipelines saved as `.joblib` files in `backend/models/` and verified to reload and generate valid predictions.
- [x] Complete run metadata persisted in `backend/models/training_metadata.json`.
- [x] Endpoints `POST /api/model/train` and `GET /api/model/training-status` functioning properly.
- [x] Frontend `ModelTraining.jsx` displays model training controls, status cards, and split details.
- [x] 42 automated tests pass across Milestones 3, 4, 5, and 6.
- [x] Frontend production build compiles with zero errors (`vite build` exit code 0).
- [x] **Zero Milestone 7+ features implemented**: No holdout evaluation metrics (MAE, RMSE, MAPE, R²), no holdout charts, no demand forecasting, and no inventory reordering logic.

---

## 6. Final Status

* **Status:** **MILESTONE 6 COMPLETED, VERIFIED & READY FOR REVIEW**
* **Next Step:** Await user review and approval before proceeding to Milestone 7 (Model Evaluation).

