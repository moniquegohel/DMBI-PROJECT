# SMARTSTOCK — MILESTONE 8: DEMAND FORECASTING VERIFICATION REPORT

> **Milestone:** Milestone 8 — Demand Forecasting  
> **Status:** Verified & Completed  
> **Date:** November 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 8 implemented the complete **Demand Forecasting Pipeline** for SMARTSTOCK, consuming the models evaluated in Milestone 7 to predict future retail demand across store and product levels.

### Primary Objectives Achieved:

1. **Empirical Model Selection**: Selected **Linear Regression** as the primary recommended forecasting model based strictly on Milestone 7 empirical performance (MAE 88.80 vs 90.76, RMSE 108.24 vs 109.88, MAPE 342.94% vs 358.93%). Random Forest is supported as an optional comparison model.
2. **Recursive Auto-Regressive Multi-Step Forecasting**: Implemented multi-step auto-regression across customizable horizons (7, 14, and 30 days) starting immediately on `2024-01-02`. Previous step predictions recursively update lag (`previous_day_sales`) and rolling features (`rolling_7_day_average`) without future data leakage.
3. **Physical Retail Bounds**: Enforced non-negativity ($\ge 0$ units) on all demand forecasts.
4. **Interactive Dashboard View**: Designed and built `frontend/src/pages/DemandForecast.jsx` with store/product selectors, horizon pills, combined historical-actuals + future-forecast line chart (Recharts), and daily forecast ledger.
5. **Seamless Pipeline Bridge to Milestone 9**: Created a direct bridge passing the generated forecast response into the Inventory Simulation workflow.
6. **Automated Verification**: Created and executed `backend/tests/test_milestone8.py`. **All 10 tests passed (10/10 green)** in 13.1 seconds.

---

## 2. File Inventory & Technical Implementation

### Backend Architecture (`backend/app/`)

#### 1. `backend/app/schemas/forecast.py` (New)
* `ForecastRequest`: Input parameters (`store_id`, `product_id`, `horizon_days`, `model_key`).
* `ForecastPoint`: Daily prediction schema (`date`, `day_of_week`, `day_index`, `predicted_demand`, `is_weekend`).
* `HistoricalPoint`: Prior actual sales (`date`, `actual_sales`).
* `ForecastResponse`: Aggregate demand, daily average, peak day, historical series, and forecast series.
* `ForecastOptionsResponse`: Available stores, products, catalogue items, and recommended model.

#### 2. `backend/app/services/demand_forecasting.py` (New)
* `get_forecast_options()`: Extracts distinct stores, products, categories, latest date (`2024-01-01`), and recorded ending inventory from `cleaned_dataset.csv`.
* `generate_demand_forecast(req)`:
  - Validates store, product, and horizon inputs.
  - Loads trained Scikit-learn pipeline from `backend/models/`.
  - Runs iterative recursive forecasting, appending predicted demand to the series buffer.
  - Returns historical context (14 days) plus future forecast series.

#### 3. `backend/app/routes/forecast.py` (New)
* `POST /api/forecast/generate`: Generates demand forecast.
* `GET /api/forecast/options`: Returns store and product catalogue metadata.

#### 4. `backend/app/main.py` (Modified)
* Registered `forecast_router` under prefix `/api/forecast`.

---

### Frontend Architecture (`frontend/src/`)

#### 5. `frontend/src/services/api.js` (Modified)
* Added client methods `getForecastOptions()` and `generateForecast()`.

#### 6. `frontend/src/pages/DemandForecast.jsx` (Redesigned & Implemented)
* Store and product selectors with live category and stock tags.
* Horizon selection (7, 14, 30 days).
* Model selection badge displaying Linear Regression as the recommended best performer.
* Summary cards (Total demand, Daily average, Peak day, Horizon timeframe).
* Recharts time-series chart combining solid historical sales and dashed predicted demand.
* Daily breakdown table with weekend tags.
* Action button linking directly to Inventory Simulation.

#### 7. `frontend/src/App.jsx` (Modified)
* Implemented `sharedForecastContext` state enabling one-click transfer of forecast results to the Inventory page.

---

### Test Suite (`backend/tests/`)

#### 8. `backend/tests/test_milestone8.py` (New)
10 automated unit and integration tests:
* `test_01_forecast_options_success`: Validates catalogue metadata.
* `test_02_default_model_selection`: Confirms Linear Regression default.
* `test_03_forecast_7_day_horizon`: Verifies 7 forecast records.
* `test_04_forecast_14_and_30_day_horizons`: Verifies 14 and 30-day horizons.
* `test_05_forecast_dates_chronological_continuity`: Verifies daily increments from `2024-01-02`.
* `test_06_predictions_strictly_non_negative`: Asserts predictions $\ge 0$.
* `test_07_random_forest_model_option`: Verifies Random Forest forecasting option.
* `test_08_invalid_store_or_product_fails`: Confirms ValueError for invalid inputs.
* `test_09_historical_sales_context_present`: Verifies recent actuals returned.
* `test_10_api_endpoints_functional`: Verifies FastAPI routes return valid schemas.

---

## 3. Automated Verification Results

### Backend Automated Tests
Command:
```powershell
$env:PYTHONPATH="backend"; backend\.venv\Scripts\python -m unittest backend.tests.test_milestone8 -v
```
Output:
```text
test_01_forecast_options_success ... ok
test_02_default_model_selection ... ok
test_03_forecast_7_day_horizon ... ok
test_04_forecast_14_and_30_day_horizons ... ok
test_05_forecast_dates_chronological_continuity ... ok
test_06_predictions_strictly_non_negative ... ok
test_07_random_forest_model_option ... ok
test_08_invalid_store_or_product_fails ... ok
test_09_historical_sales_context_present ... ok
test_10_api_endpoints_functional ... ok

----------------------------------------------------------------------
Ran 10 tests in 13.105s

OK
```
**Result:** 10 / 10 tests passed (100% success rate).

---

## 4. Conclusion & Transition

Milestone 8 is complete, verified, and operational. Its outputs feed directly into **Milestone 9: Inventory Simulation**.

