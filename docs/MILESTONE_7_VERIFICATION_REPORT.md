# SMARTSTOCK — MILESTONE 7: MODEL EVALUATION & COMPARISON VERIFICATION REPORT

> **Milestone:** Milestone 7 — Model Evaluation and Comparison  
> **Status:** Verified & Completed  
> **Date:** November 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 7 implemented the complete **Model Evaluation and Comparison Pipeline** for SMARTSTOCK. Consuming the supervised regression pipelines trained in Milestone 6 (**Linear Regression** and **Random Forest Regressor**), this milestone evaluates both models on the held-out chronological test partition (20% of unique calendar dates), calculates standard error metrics (**MAE**, **RMSE**, and **MAPE** with zero-actual-demand exclusion), objectively determines the superior model based on empirical data, and displays the findings on the SMARTSTOCK dashboard through interactive visualizations and business-friendly explanations.

### Primary Objectives Achieved:

1. **Chronological Holdout Evaluation**: Both models were evaluated on the **exact same 14,700 held-out test records** spanning 147 calendar dates (`2023-08-08` to `2024-01-01`). Strict time order was preserved with zero shuffling.
2. **Zero Data Leakage**: Preprocessing transformations (`SimpleImputer`, `OneHotEncoder`) were encapsulated inside the Scikit-learn `Pipeline` objects fitted strictly on the 80% training window. Holdout test data was never fitted or used during feature transformation.
3. **Mathematical Precision & Metric Integrity**:
   - **Mean Absolute Error (MAE)**: Measures average absolute difference in units sold.
   - **Root Mean Squared Error (RMSE)**: Penalizes larger prediction misses.
   - **Mean Absolute Percentage Error (MAPE)**: Accurately handles zero actual sales (`y == 0`) by excluding them from percentage division. Exactly **62 records** with zero sales were excluded, evaluating both models on identical sets of **14,638 eligible records**.
4. **Empirical Model Comparison (No Hardcoding)**:
   - **Linear Regression**: MAE = **88.80**, RMSE = **108.24**, MAPE = **342.94%**
   - **Random Forest Regressor**: MAE = **90.76**, RMSE = **109.88**, MAPE = **358.93%**
   - **Empirical Winner**: Linear Regression demonstrated lower error across all three metrics and was dynamically designated as the superior model.
5. **Dashboard Visualizations**:
   - **Actual vs. Predicted Demand Time Series**: Responsive Recharts line chart displaying daily actual sales against both model predictions across all 147 test dates.
   - **Model Performance Comparison Bar Chart**: Side-by-side comparison of MAE and RMSE in units sold, with a separate presentation for MAPE (%) to avoid misleading mixed-unit axes.
6. **Business-Oriented Frontend**: Fully integrated into `frontend/src/pages/Dashboard.jsx` using plain-language labels (*"Model Performance"*, *"Prediction Accuracy"*, *"Actual vs. Predicted Demand"*, *"Best Performing Model"*), avoiding internal technical labels.
7. **Automated Verification**: Created comprehensive test suite in `backend/tests/test_milestone7.py`. **All 10 tests passed (10/10 green)** and **frontend production build passed with exit code 0**.
8. **Strict Milestone Boundaries**: Zero premature implementation of Milestone 8 7-day demand forecasting or Milestones 9–10 inventory simulation.

---

## 2. File Inventory & Technical Implementation

### Backend Architecture (`backend/app/`)

#### 1. `backend/app/schemas/evaluation.py` (New)
Defined Pydantic schemas for serialization and validation:
* `ModelMetrics`: Stores `mae`, `rmse`, `mape`, `evaluated_rows_count`, `excluded_zero_actual_count`, and `eligible_mape_rows_count`.
* `ModelComparisonItem`: Individual model comparison metadata with flags for `is_winner_mae`, `is_winner_rmse`, `is_winner_mape`, and `is_overall_winner`.
* `TimelineDataPoint`: Daily aggregated actual demand, Linear Regression forecast, and Random Forest forecast for time-series charting.
* `MetricComparisonBar`: Chart payload for bar chart comparison.
* `ModelEvaluationResult`: Comprehensive evaluation response containing metrics, comparison items, summary table, timeline points, best model name/key, and business interpretation.
* `ModelEvaluationStatusResponse`: Status check indicating whether models are trained and evaluation results exist on disk.

#### 2. `backend/app/services/model_evaluation.py` (New)
Implemented the core model evaluation engine:
* `evaluate_models(force_recompute=False)`:
  1. Validates that `ml_dataset.csv` and trained model artifacts (`linear_regression_pipeline.joblib`, `random_forest_pipeline.joblib`) exist.
  2. If `not force_recompute` and cached `evaluation_results.json` exists, loads and returns cached results.
  3. Uses `perform_chronological_split(train_ratio=0.8)` from `model_training.py` to extract the held-out partition (`X_holdout`, `y_holdout`).
  4. Generates predictions using `.predict()` on the fitted pipelines without refitting.
  5. Computes MAE, RMSE, and zero-safe MAPE (excluding `y == 0` records).
  6. Determines metric winners and overall best model dynamically based on lower error values.
  7. Aggregates daily demand and predictions across the 147 test dates for frontend visualization.
  8. Generates plain-language interpretation and caches results to `backend/models/evaluation_results.json`.
* `get_evaluation_status()`: Non-blocking check returning evaluation readiness and cached results.

#### 3. `backend/app/routes/model.py` (Modified)
Added evaluation endpoints to the existing model router:
* `POST /api/model/evaluate`: Executes model evaluation on held-out test data (supports `force=true` query parameter).
* `GET /api/model/evaluation`: Retrieves cached evaluation results (or computes if models are trained).
* `GET /api/model/evaluation/status`: Lightweight status check for frontend conditional rendering.

---

### Frontend Architecture (`frontend/src/`)

#### 4. `frontend/src/services/api.js` (Modified)
Added API client methods:
* `evaluateModels(force=false)` -> `POST /api/model/evaluate?force=${force}`
* `getModelEvaluation()` -> `GET /api/model/evaluation`
* `getModelEvaluationStatus()` -> `GET /api/model/evaluation/status`

#### 5. `frontend/src/pages/Dashboard.jsx` (Redesigned & Integrated)
Transformed `Dashboard.jsx` from a placeholder into an interactive retail demand intelligence overview:
* **Overview StatCards**: Live metrics (Total Units Sold, Products Tracked, Dataset Records, Sales Period).
* **Best Performing Model Banner**: Plain-language recommendation highlighting the superior model and explaining the business takeaway.
* **3 Metric Cards**:
  - **Mean Absolute Error (MAE)**: Compares error in units sold; highlights winner with checkmark badge.
  - **Root Mean Squared Error (RMSE)**: Compares error giving greater weight to large misses.
  - **Mean Absolute Percentage Error (MAPE)**: Compares percentage error and transparently reports the 62 excluded zero-demand records.
* **Actual vs. Predicted Demand Time Series**: Responsive line chart with custom tooltip displaying daily actual sales vs. Linear Regression vs. Random Forest across 147 test dates.
* **Model Comparison Table**: Clean tabular comparison showing Metric, Linear Regression, Random Forest, Difference, and Better Model.
* **Model Error Bar Chart**: Grouped bar chart comparing MAE and RMSE in units sold, keeping scales clean and uncorrupted.
* **Untrained State**: Helpful callout button guiding the user to the "Sales Prediction" tab if models have not yet been trained.

#### 6. `frontend/src/pages/ModelTraining.jsx` (Modified)
* Added a post-training shortcut banner: *"Prediction models are trained and ready. View accuracy metrics and comparison on the Dashboard"* with a one-click button to switch to the Dashboard.

#### 7. `frontend/src/App.jsx` (Modified)
* Passed `setActiveTab={setActiveTab}` to `<Dashboard />` to enable seamless tab navigation.

---

### Test Suite (`backend/tests/`)

#### 8. `backend/tests/test_milestone7.py` (New)
Authored 10 automated unit and integration tests using Python standard library `unittest`:
* `test_01_evaluation_service_success`: Verifies service executes and returns valid schema.
* `test_02_chronological_test_set_integrity`: Confirms test date range strictly matches cutoff date from metadata.
* `test_03_both_models_evaluated_on_identical_records`: Verifies identical 14,700 records evaluated for both models.
* `test_04_mape_zero_handling_and_exclusion_reporting`: Verifies 62 zero-sales records are excluded and 14,638 eligible records are evaluated.
* `test_05_metrics_mathematical_validity`: Verifies metrics are positive and mathematically consistent (RMSE >= MAE).
* `test_06_data_driven_winner_determination`: Verifies winner assignment is based on computed numbers, not hardcoding.
* `test_07_daily_timeline_aggregation`: Confirms 147 timeline points matching unique test dates.
* `test_08_api_get_evaluation_status`: Verifies `GET /api/model/evaluation/status` endpoint.
* `test_09_api_get_evaluation_results`: Verifies `GET /api/model/evaluation` endpoint.
* `test_10_api_post_evaluate`: Verifies `POST /api/model/evaluate` endpoint.

---

## 3. Evaluation Methodology & Leakage Prevention

| Requirement | Implementation & Verification | Status |
|---|---|---|
| **Same Held-out Test Data** | Both models evaluated on the exact same 14,700 records from `2023-08-08` to `2024-01-01`. | Verified |
| **Preserve Time Order** | Data partitioned strictly by calendar dates in ascending order without random shuffling. | Verified |
| **No Test-Set Fitting** | Pipelines fitted on train set only; test evaluation strictly invokes `.predict()`. | Verified |
| **No Preprocessing Leakage** | `ColumnTransformer` (median imputation + one-hot encoding) fitted on training split only. | Verified |
| **Record Alignment** | Actual values `y_holdout` and predicted values `lr_preds`, `rf_preds` share identical indices. | Verified |

---

## 4. Empirical Evaluation Results

The evaluation was executed on the 14,700 held-out test records of `ml_dataset.csv`:

| Evaluation Metric | Linear Regression | Random Forest Regressor | Difference | Better Model |
|---|---|---|---|---|
| **Mean Absolute Error (MAE)** | **88.8019 units** | 90.7635 units | 1.9616 units (2.2%) | **Linear Regression** |
| **Root Mean Squared Error (RMSE)** | **108.2374 units** | 109.8753 units | 1.6379 units (1.5%) | **Linear Regression** |
| **Mean Absolute Percentage Error (MAPE)** | **342.94%** | 358.93% | 15.99% (4.5%) | **Linear Regression** |

### Zero Actual Demand Handling:
* **Total Holdout Records:** 14,700
* **Records with Actual Sales = 0:** Exactly **62 records**
* **Records Evaluated for MAPE:** **14,638 records**
* **Division-by-Zero Errors:** Zero (handled cleanly)

### Plain-Language Interpretation:
Linear Regression achieved lower error on all three metrics. On this retail demand dataset, the linear baseline provides a more stable generalization across future calendar dates without overfitting to local training noise. It is recommended as the baseline forecasting model for retail demand planning.

---

## 5. Automated Verification & Test Results

### 1. Backend Automated Tests (`unittest`)
Command executed:
```powershell
$env:PYTHONPATH="backend"; backend\.venv\Scripts\python -m unittest backend.tests.test_milestone7 -v
```
Output:
```text
test_01_evaluation_service_success ... ok
test_02_chronological_test_set_integrity ... ok
test_03_both_models_evaluated_on_identical_records ... ok
test_04_mape_zero_handling_and_exclusion_reporting ... ok
test_05_metrics_mathematical_validity ... ok
test_06_data_driven_winner_determination ... ok
test_07_daily_timeline_aggregation ... ok
test_08_api_get_evaluation_status ... ok
test_09_api_get_evaluation_results ... ok
test_10_api_post_evaluate ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.071s

OK
```
**Result:** 10 / 10 tests passed (100% success rate).

### 2. Frontend Production Build (`vite build`)
Command executed:
```cmd
cd frontend && npm run build
```
Output:
```text
vite v8.3.5 building client environment for production...
transforming...
✓ 2516 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.47 kB │ gzip:   0.30 kB
dist/assets/index-BH4WhjFe.css   47.83 kB │ gzip:   7.60 kB
dist/assets/index-CsvV3TY4.js   743.86 kB │ gzip: 217.19 kB
✓ built in 7.00s
```
**Result:** Production build passed cleanly with zero errors (exit code 0).

---

## 6. Milestone Conclusion & Transition

Milestone 7 has satisfied all criteria set forth in `SMARTSTOCK_REQUIREMENTS.md`:
* Evaluation conducted on held-out test partition with zero leakage.
* MAE, RMSE, and zero-safe MAPE calculated accurately.
* Model comparison conducted objectively based on empirical metrics.
* Visualizations created for actual vs. predicted demand and model comparison with appropriate separated scales.
* Dashboard integrated with plain-language business terminology.
* All automated unit tests and frontend production build pass.

The project is ready for review and authorization to proceed to **Milestone 8: Demand Forecasting**.

