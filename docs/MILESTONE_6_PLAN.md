# SMARTSTOCK — MILESTONE 6 IMPLEMENTATION PLAN: MODEL TRAINING

> **Milestone:** Milestone 6 — Model Training  
> **Status:** Plan Prepared & Awaiting Review  
> **Date:** October 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objective

The objective of Milestone 6 is to train and persist two supervised regression models for retail demand forecasting using the ML-ready dataset (`ml_dataset.csv`) produced in Milestone 5:

1. **Linear Regression** (Scikit-learn `LinearRegression`) — provides an interpretable linear baseline.
2. **Random Forest Regression** (Scikit-learn `RandomForestRegressor`) — non-linear ensemble tree model capable of capturing complex feature interactions.

Both models will predict **`Units Sold`** using only predictors that are available at prediction time.

### Key Architectural Principles
- **Chronological 80/20 Train/Holdout Split**: Time-series observations are sorted by date. The earliest ~80% of unique dates are allocated to the training period, and the latest ~20% of dates are reserved for holdout evaluation in Milestone 7. No random shuffling.
- **Zero Target Leakage**: All records sharing a date stay together. Preprocessing imputers and encoders are fitted **strictly on the training period**.
- **Excluded Features**: `Demand Forecast` (0.997 correlation with target + negative anomalies), `Inventory Level` (end-of-day balance), and `Units Ordered` (reactive replenishment) are completely excluded from predictors.
- **Model Persistence**: Complete Scikit-learn pipelines (`ColumnTransformer` + estimator) are serialized using Joblib into `backend/models/`.
- **Frontend Dashboard**: The `ModelTraining.jsx` page is expanded with model training controls, training status indicators, and chronological split summaries.

> **Strict Scope Boundary:** Milestone 6 covers **Model Training only**. Holdout evaluation metrics (MAE, RMSE, MAPE, R²), actual-vs-predicted comparison charts, 7-day demand forecasting, and inventory simulation belong to Milestones 7–10 and will **not** be implemented here.

---

## 2. Dataset Context & Time-Aware Split Rules

Based on the development dataset `retail_store_inventory.csv` (73,100 records, 731 unique dates from 2022-01-01 to 2024-01-01):

| Feature / Step | Specification | Rationale |
|---|---|---|
| **Target Variable** | `Units Sold` | Historical daily sales volume to predict. |
| **Data Source** | `backend/data/ml_dataset.csv` | Feature-engineered dataset from Milestone 5. |
| **Chronological Split** | Earliest ~80% dates → Train<br>Latest ~20% dates → Holdout | Supervised time-series forecasting split. Never shuffle data randomly. |
| **Cutoff Rule** | 80th percentile of sorted unique dates | All rows for a date stay on the same side of the split. |
| **Lag NaNs Handling** | Excluded from training fitting | The initial row of each store-product series lacks lag features (`previous_day_sales` is NaN) and cannot be fitted without them. Exactly 100 rows excluded; documented in metadata. |
| **Holdout Reservation** | Kept untouched | Reserved for Milestone 7 evaluation; never seen during preprocessing fit or model training. |
| **Predictor Matrix** | Numeric: `day`, `day_of_week`, `month`, `is_weekend`, `previous_day_sales`, `rolling_7_day_average`, `price`, `discount`<br>Categorical: `Store ID`, `Product ID`, `promotion` | Columns available at prediction time. |
| **Excluded Columns** | `Demand Forecast`, `Inventory Level`, `Units Ordered`, `Units Sold` (target), raw `Date` string | Prevents target leakage and data snooping. |

---

## 3. Technical Architecture & File Inventory

### Backend Components

1. **`backend/app/schemas/model.py` (New)**:
   - `TrainedModelInfo`: Model name, algorithm, status (`trained` / `failed`), row count, parameters, and artifact filename.
   - `DateSplitInfo`: Cutoff date, train date range, holdout date range, train row count, holdout row count, and excluded initial row count.
   - `ModelTrainingResult`: Full training execution report with split details, target name, numeric & categorical predictor lists, and model summaries.
   - `ModelTrainingStatusResponse`: Lightweight status endpoint response reporting whether models are trained, with metadata.

2. **`backend/app/services/model_training.py` (New)**:
   - Dynamic path management for `backend/models/` and `ml_dataset.csv`.
   - `perform_chronological_split(df)`: Computes 80% date cutoff, splits data chronologically, filters initial lag NaN rows from fitting, and tracks metadata.
   - `build_preprocessor(numeric_cols, categorical_cols)`: Creates Scikit-learn `ColumnTransformer` with `SimpleImputer` and `OneHotEncoder(handle_unknown='ignore')`.
   - `train_linear_regression()`: Trains Scikit-learn `LinearRegression` pipeline.
   - `train_random_forest()`: Trains Scikit-learn `RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)` pipeline.
   - `save_model_artifacts()`: Persists `linear_regression_pipeline.joblib`, `random_forest_pipeline.joblib`, and `training_metadata.json`.
   - `get_training_status()`: Reads existing metadata and model artifact presence without re-training.

3. **`backend/app/routes/model.py` (Modified)**:
   - Add model training endpoints while preserving existing `/features/*` routes:
     - `POST /api/model/train`: Runs chronological split and fits both models; saves artifacts; returns `ModelTrainingResult`.
     - `GET /api/model/training-status`: Returns status and metadata of trained models.

### Frontend Components

4. **`frontend/src/services/api.js` (Modified)**:
   - Ensure `trainModels()` calls `POST /api/model/train`.
   - Add `getModelTrainingStatus()` calling `GET /api/model/training-status`.

5. **`frontend/src/pages/ModelTraining.jsx` (Modified)**:
   - Incorporate **Model Training Section** alongside Feature Engineering:
     - Student-friendly explanations of Linear Regression and Random Forest.
     - **"Train Models" action button** with live training spinner and status updates.
     - **Model Cards**:
       - Linear Regression card: Status badge (Trained/Not Trained), algorithm parameters, training row count.
       - Random Forest card: Status badge, parameters (100 estimators, random state 42), training row count.
     - **Chronological Split Summary Card**:
       - 80% Training Period (start date, end date, row count).
       - 20% Reserved Holdout Period (cutoff date, end date, row count).
       - Excluded initial NaN rows callout (100 rows).
     - Target & Predictor summary list.
     - **Milestone 7 Preview Notice**: Explains that formal evaluation (MAE, RMSE, MAPE) will occur next on the holdout set.

### Test Suite

6. **`backend/tests/test_milestone6.py` (New)**:
   - 11 automated test cases verifying:
     - Clear rejection if `ml_dataset.csv` does not exist.
     - Chronological date split integrity (no date in both sets; all records on same date stay together).
     - Target is `Units Sold`; `Demand Forecast`, `Inventory Level`, `Units Ordered` are not predictors.
     - Initial lag NaN rows are excluded from model fitting.
     - Preprocessor is fitted on training set only.
     - Both Linear Regression and Random Forest pipelines train and save artifacts cleanly.
     - Saved Joblib pipelines can be reloaded and generate valid predictions.
     - Isolated model failure handling.
     - Training idempotency on repeated execution.
     - Regression protection for `/api/health` and Milestones 1–5.

---

## 4. Verification & Testing Strategy

### Automated Backend Tests
Run the complete test suite across Milestones 3, 4, 5, and 6:
```powershell
cd "c:\Users\moniq\OneDrive\Documents\Documents\School\College\DMBI PROJECT\backend"
& "..\.venv\Scripts\python.exe" -m pytest tests/ -v
```
**Acceptance Threshold**: All tests across `test_milestone3.py`, `test_milestone4.py`, `test_milestone5.py`, and `test_milestone6.py` must pass 100% (approx. 40+ tests total).

### Frontend Production Build
Validate bundle compilation and syntax:
```powershell
cd "c:\Users\moniq\OneDrive\Documents\Documents\School\College\DMBI PROJECT\frontend"
npm run build
```
**Acceptance Threshold**: Build succeeds with exit code 0.

### Real Dataset Execution (`retail_store_inventory.csv`)
1. Run training on the full 73,100-row dataset.
2. Confirm:
   - 80% date cutoff date is computed accurately (~585 training dates, ~146 holdout dates).
   - Initial 100 NaN lag rows are excluded from fitting.
   - `linear_regression_pipeline.joblib` and `random_forest_pipeline.joblib` are created in `backend/models/`.
   - `training_metadata.json` is generated.
3. Check `http://localhost:5173/` in the browser and verify the Model Training page shows both models trained.

---

## 5. Next Steps

Upon your review and approval of this plan:
1. Implement `backend/app/schemas/model.py` and `backend/app/services/model_training.py`.
2. Update `backend/app/routes/model.py` with the training endpoints.
3. Update `frontend/src/services/api.js` and `frontend/src/pages/ModelTraining.jsx`.
4. Create `backend/tests/test_milestone6.py` and run the full test suite.
5. Run the frontend production build.
6. Generate the Milestone 6 verification report and approval document in `docs/`.

