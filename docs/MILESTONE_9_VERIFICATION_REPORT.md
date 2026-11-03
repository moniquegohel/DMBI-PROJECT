# SMARTSTOCK — MILESTONE 9: INVENTORY SIMULATION VERIFICATION REPORT

> **Milestone:** Milestone 9 — Inventory Simulation  
> **Status:** Verified & Completed  
> **Date:** November 2026  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 9 implemented the complete **Inventory Simulation Engine** for SMARTSTOCK, consuming the future demand forecasts produced in Milestone 8 to project how retail inventory levels deplete over customizable forecast horizons (7, 14, and 30 days).

### Primary Objectives Achieved:

1. **Dataset Audit & Baseline Starting Stock**: Audited `cleaned_dataset.csv` and confirmed that on the cutoff date (`2024-01-01`), every store-product series possesses a recorded ending `Inventory Level` (e.g. Store `S001` / Product `P0001` = 223 units). The simulation defaults to this real recorded inventory, while clearly supporting user-defined custom starting inventory for "What-If" testing.
2. **Physical Balance & Non-Negativity Constraint**: Implemented day-by-day fulfillment logic:
   $$\text{Available Stock}_d = \text{Beginning Stock}_d + \text{Replenishment}_d$$
   $$\text{Demand Fulfilled}_d = \min(\text{Available Stock}_d, \text{Forecasted Demand}_d)$$
   $$\text{Unmet Demand}_d = \text{Forecasted Demand}_d - \text{Demand Fulfilled}_d$$
   $$\text{Ending Stock}_d = \max(0, \text{Available Stock}_d - \text{Demand Fulfilled}_d)$$
   Physical inventory is strictly prevented from becoming negative ($\ge 0$).
3. **Stockout Detection & Tracking**: Automatically identifies the exact day and date of the first stockout period and tallies cumulative stockout days.
4. **Transparent Replenishment Modeling**: Allows users to configure an optional replenishment shipment (quantity and arrival day) to evaluate how scheduled reorders avert stockout events.
5. **Interactive Dashboard View**: Designed and built `frontend/src/pages/Inventory.jsx` featuring:
   - Starting stock controls (recorded vs. custom toggle).
   - Optional replenishment drawer.
   - Summary cards (Starting Stock, Expected Demand, Fulfilled Demand, Unmet Demand, Ending Stock, Stockout Count, Service Level %).
   - Area chart showing projected stock depletion over time with a critical stockout reference boundary at 0 units.
   - Grouped bar chart comparing available stock against customer demand.
   - Daily inventory ledger table.
6. **Automated Verification**: Created and executed `backend/tests/test_milestone9.py`. **All 10 tests passed (10/10 green)** in 7.66 seconds.
7. **Regression Guard**: Full test suite across Milestones 7, 8, and 9 passed cleanly: **30 / 30 tests green**. Frontend production build (`vite build`) succeeded with exit code 0.

---

## 2. File Inventory & Technical Implementation

### Backend Architecture (`backend/app/`)

#### 1. `backend/app/schemas/inventory.py` (New)
* `InventorySimulationRequest`: Input parameters (`store_id`, `product_id`, `starting_inventory`, `horizon_days`, `model_key`, `replenishment_quantity`, `replenishment_day`).
* `DailySimulationPoint`: Daily inventory balance (`day`, `date`, `beginning_inventory`, `replenishment_received`, `available_stock`, `forecasted_demand`, `demand_fulfilled`, `unmet_demand`, `ending_inventory`, `is_stockout`).
* `InventorySimulationResponse`: Aggregate performance (`total_forecasted_demand`, `total_demand_fulfilled`, `total_unmet_demand`, `stockout_periods_count`, `first_stockout_day`, `first_stockout_date`, `ending_inventory`, `service_level_percentage`, `simulation_summary_text`).
* `StockInfoResponse`: Metadata endpoint returning recorded ending stock from dataset.

#### 2. `backend/app/services/inventory_simulation.py` (New)
* `get_stock_info(store_id, product_id)`: Extracts recorded inventory level from `cleaned_dataset.csv` on `2024-01-01`.
* `run_inventory_simulation(req)`:
  - Generates future demand forecasts via Milestone 8 service.
  - Initializes starting stock from recorded data or user override.
  - Iterates day-by-day, applying replenishment arrivals, fulfilling demand, and carrying ending inventory forward.
  - Enforces physical non-negativity constraint.
  - Computes service level percentage and generates plain-language business interpretation.

#### 3. `backend/app/routes/inventory.py` (New)
* `POST /api/inventory/simulate`: Runs inventory simulation.
* `GET /api/inventory/stock-info`: Returns recorded stock details.

#### 4. `backend/app/main.py` (Modified)
* Registered `inventory_router` under prefix `/api/inventory`.

---

### Frontend Architecture (`frontend/src/`)

#### 5. `frontend/src/services/api.js` (Modified)
* Added client methods `simulateInventory()` and `getInventoryStockInfo()`.

#### 6. `frontend/src/pages/Inventory.jsx` (Redesigned & Implemented)
* Store and product selectors with live recorded inventory level indicators.
* Starting stock toggle: "Recorded Stock" vs "Customize".
* Optional replenishment drawer with quantity and arrival day selectors.
* Summary cards (Starting Stock, Expected Demand, Demand Fulfilled, Unmet Demand, Service Level %).
* Recharts Area chart displaying projected physical stock trajectory with 0-unit reference line.
* Recharts Bar chart comparing available inventory vs customer demand.
* Daily balance ledger table with stockout alerts.

#### 7. `frontend/src/App.jsx` (Modified)
* Integrated `sharedForecastContext` allowing users on the Demand Forecast page to click "Simulate Inventory" and seamlessly transfer store, product, and horizon into the Inventory page.

---

### Test Suite (`backend/tests/`)

#### 8. `backend/tests/test_milestone9.py` (New)
10 automated unit and integration tests:
* `test_01_stock_info_retrieval`: Verifies recorded stock lookup.
* `test_02_simulation_default_recorded_stock`: Confirms default to recorded stock.
* `test_03_simulation_user_provided_stock`: Verifies custom starting inventory override.
* `test_04_inventory_never_negative`: Asserts ending inventory $\ge 0$ on all days.
* `test_05_fulfillment_balance_equation`: Confirms fulfilled + unmet == forecasted demand.
* `test_06_stockout_detection`: Verifies stockout identification and first stockout day tracking.
* `test_07_replenishment_increases_available_stock`: Verifies replenishment arrives on scheduled day.
* `test_08_interday_carryover_balance`: Confirms Day $d$ ending stock == Day $d+1$ beginning stock.
* `test_09_service_level_calculation`: Validates `(fulfilled / forecasted) * 100`.
* `test_10_api_endpoints_functional`: Verifies FastAPI route handlers return valid schemas.

---

## 3. Automated Verification Results

### Backend Automated Tests
Command:
```powershell
$env:PYTHONPATH="backend"; backend\.venv\Scripts\python -m unittest backend.tests.test_milestone9 -v
```
Output:
```text
test_01_stock_info_retrieval ... ok
test_02_simulation_default_recorded_stock ... ok
test_03_simulation_user_provided_stock ... ok
test_04_inventory_never_negative ... ok
test_05_fulfillment_balance_equation ... ok
test_06_stockout_detection ... ok
test_07_replenishment_increases_available_stock ... ok
test_08_interday_carryover_balance ... ok
test_09_service_level_calculation ... ok
test_10_api_endpoints_functional ... ok

----------------------------------------------------------------------
Ran 10 tests in 7.664s

OK
```
**Result:** 10 / 10 tests passed (100% success rate).

### Full Regression Test Suite (Milestones 7, 8, 9)
Command:
```powershell
$env:PYTHONPATH="backend"; backend\.venv\Scripts\python -m unittest backend.tests.test_milestone7 backend.tests.test_milestone8 backend.tests.test_milestone9 -v
```
**Result:** **30 / 30 tests passed in 16.421s (100% success rate).**

### Frontend Production Build
Command:
```cmd
cd frontend && npm run build
```
**Result:** Vite production build succeeded with exit code 0 in 7.24s.

---

## 4. Conclusion & Transition

Milestone 9 is complete, verified, and operational. All requirements for both **Milestone 8 (Demand Forecasting)** and **Milestone 9 (Inventory Simulation)** are fully satisfied. The codebase is clean, tested, and ready for authorization to proceed to **Milestone 10: Inventory Recommendation**.

