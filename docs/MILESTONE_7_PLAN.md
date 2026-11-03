# SMARTSTOCK — MILESTONE 7 IMPLEMENTATION PLAN
## Model Evaluation and Comparison

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year  
> **Milestone:** 7 — Model Evaluation and Comparison  
> **Status:** APPROVED & IN EXECUTION  
> **Date:** November 2026  

---

## 1. Objective

Evaluate and compare the existing **Linear Regression** and **Random Forest Regression** models using SMARTSTOCK's held-out test dataset (chronological 80/20 train/test split).

The goal is to determine how accurately each model predicts retail demand on unseen data, identify the better model based on empirical metrics, and present the results in a simple, understandable way on the SMARTSTOCK dashboard.

This milestone is strictly limited to model evaluation and comparison. Future 7-day demand forecasting (Milestone 8) and inventory simulation/reorder recommendations (Milestones 9–10) are explicitly out of scope.

---

## 2. Methodology & Leakage Prevention

1. **Same Held-out Test Dataset**:
   - Both models are evaluated on the exact same 14,700 records from the chronological 80/20 split (`2023-08-08` to `2024-01-01`).
   - Cutoff date: `2023-08-08`.
2. **Preserve Time Order**:
   - Records are maintained in strict time order. No random shuffling or cross-validation mixing future dates into past training.
3. **Zero Data Leakage**:
   - Models are NOT refitted on test data.
   - Preprocessing steps (median imputation, one-hot encoding) are saved inside the Scikit-learn `Pipeline` and were fitted strictly on the training period. Test evaluation calls `.predict()` on the pipeline.
4. **Target Alignment**:
   - Actual test values `y_test` and predicted values `y_pred` refer to the identical aligned records.

---

## 3. Evaluation Metrics

### A. Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
- Measures the average absolute difference between actual and predicted demand in Units Sold.
- Lower MAE indicates better performance.

### B. Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- Measures prediction error while penalizing larger errors more heavily.
- Lower RMSE indicates better performance.

### C. Mean Absolute Percentage Error (MAPE)
$$\text{MAPE} = \frac{100\%}{M} \sum_{i \in \text{valid}} \frac{|y_i - \hat{y}_i|}{|y_i|}$$
- Excludes test records where actual demand is zero (`y == 0`) to prevent division-by-zero errors.
- Exactly 62 zero-demand records in the test dataset are excluded, leaving 14,638 eligible records.
- Both models are evaluated on the identical 14,638 records.
- Exclusion count (62) is reported transparently on the dashboard.

---

## 4. Empirical Benchmark on Held-out Dataset

Based on pre-verification of the actual test dataset:
- **Linear Regression**:
  - MAE: **88.80** units
  - RMSE: **108.24** units
  - MAPE: **342.94%**
- **Random Forest Regressor**:
  - MAE: **90.76** units
  - RMSE: **109.88** units
  - MAPE: **358.93%**
- **Empirical Winner**: Linear Regression is lower in all 3 error metrics on this test set. The conclusion is based strictly on these empirical numbers.

---

## 5. Visualizations

1. **Actual vs. Predicted Demand**:
   - Daily aggregated time series comparing total actual demand against Linear Regression and Random Forest predictions over the 147 test dates.
   - Preserves metric calculation on full 14,700 records while keeping frontend chart performant and legible.
2. **Model Performance Comparison**:
   - Dedicated comparison of MAE and RMSE in units, and a separate presentation for MAPE (%) so incomparable scales are not combined.

---

## 6. Implementation Scope

### Backend:
- `backend/app/schemas/evaluation.py` (Pydantic models)
- `backend/app/services/model_evaluation.py` (Evaluation service, caching)
- `backend/app/routes/model.py` (Evaluation endpoints)
- `backend/tests/test_milestone7.py` (Test suite)

### Frontend:
- `frontend/src/services/api.js` (Evaluation client methods)
- `frontend/src/pages/Dashboard.jsx` (Interactive evaluation dashboard)
- `frontend/src/pages/ModelTraining.jsx` (Post-training shortcut)
- `frontend/src/App.jsx` (Pass navigation callback to Dashboard)

### Deliverables:
- `docs/MILESTONE_7_PLAN.md`
- `docs/MILESTONE_7_VERIFICATION_REPORT.md`
- `docs/MILESTONE_7_APPROVAL.md`

