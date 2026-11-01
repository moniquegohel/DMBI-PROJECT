# SMARTSTOCK — MILESTONE 8 IMPLEMENTATION PLAN
## Demand Forecasting

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year  
> **Milestone:** 8 — Demand Forecasting  
> **Status:** PROPOSED & AWAITING AUTHORIZATION  
> **Date:** November 2026  

---

## 1. Objective

Implement future retail demand forecasting for any selected store and product using the trained machine learning models from previous milestones.

The purpose is to provide retail managers with expected daily product sales across customizable forecast horizons (7, 14, or 30 days) to anticipate customer demand.

---

## 2. Model Selection & Justification

- **Selected Model:** **Linear Regression** (Scikit-learn pipeline).
- **Justification:** Based on Milestone 7's empirical evaluation on 14,700 held-out test records:
  - MAE: **88.80 units** (vs. Random Forest 90.76 units)
  - RMSE: **108.24 units** (vs. Random Forest 109.88 units)
  - MAPE: **342.94%** (vs. Random Forest 358.93%)
- The UI will preselect Linear Regression as the recommended baseline while still permitting users to switch to Random Forest if desired.

---

## 3. Forecasting Methodology: Recursive Multi-Step Auto-Regression

1. **Date Sequence:** Future dates advance strictly day-by-day starting from the day following the dataset's latest transaction (`2024-01-02`).
2. **Calendar Features:** `day`, `day_of_week`, `month`, `is_weekend` derived directly from future calendar dates.
3. **Lag & Rolling Recursion:**
   - Day $t+1$: `previous_day_sales` comes from actual sales on `2024-01-01`; `rolling_7_day_average` is calculated from the preceding 7 days of actual sales.
   - Day $t+2$ through $t+H$: Predictions from earlier steps are appended to the series buffer and used to dynamically compute subsequent lag and rolling features.
4. **Zero-Floor Clamping:** All predictions are clamped to $\ge 0$ units ($\hat{y} = \max(0, \text{round}(\hat{y}, 1))$).
5. **Zero Data Leakage:** Future actual sales are strictly never accessed or leaked.

---

## 4. Deliverables

- Backend Schemas: `backend/app/schemas/forecast.py`
- Backend Service: `backend/app/services/demand_forecasting.py`
- Backend Router: `backend/app/routes/forecast.py` (`POST /api/forecast/generate`, `GET /api/forecast/options`)
- Frontend View: `frontend/src/pages/DemandForecast.jsx`
- Frontend API: `frontend/src/services/api.js`
- Test Suite: `backend/tests/test_milestone8.py`
- Documentation: `docs/MILESTONE_8_VERIFICATION_REPORT.md` and `docs/MILESTONE_8_APPROVAL.md`

