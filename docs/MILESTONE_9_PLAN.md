# SMARTSTOCK — MILESTONE 9 IMPLEMENTATION PLAN
## Inventory Simulation

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year  
> **Milestone:** 9 — Inventory Simulation  
> **Status:** PROPOSED & AWAITING AUTHORIZATION  
> **Date:** November 2026  

---

## 1. Objective

Simulate physical inventory depletion and stock availability over future forecast periods using the demand forecasts generated in Milestone 8.

The simulation will determine:
1. Whether starting stock can fulfill expected demand.
2. The exact day a product will experience a stockout.
3. Total unmet customer demand due to stock depletion.
4. Projected ending inventory.
5. The impact of optional scheduled replenishments on stockout prevention.

---

## 2. Dataset Audit & Inventory Assumptions

- **Recorded Inventory Level:** Available on `2024-01-01` in `cleaned_dataset.csv` for every store-product pair (e.g. `S001` / `P0001` = 223 units). The simulation will pre-fill with this recorded value by default.
- **User Customization:** Users can override starting stock to simulate custom buffer scenarios.
- **Replenishment Modeling:** Since lead times are not recorded in the raw dataset, replenishment is modeled as an optional user parameter (quantity and arrival day) with all assumptions transparently visible.

---

## 3. Inventory Simulation Logic

For each day $d \in \{1, \dots, H\}$:

$$\text{Available Stock}_d = \text{Beginning Stock}_d + \text{Replenishment}_d$$
$$\text{Demand Fulfilled}_d = \min(\text{Available Stock}_d, \text{Forecasted Demand}_d)$$
$$\text{Unmet Demand}_d = \text{Forecasted Demand}_d - \text{Demand Fulfilled}_d$$
$$\text{Ending Stock}_d = \text{Available Stock}_d - \text{Demand Fulfilled}_d$$
$$\text{Beginning Stock}_{d+1} = \text{Ending Stock}_d$$

- **Physical Inventory Constraint:** Physical stock never becomes negative ($\text{Ending Stock} \ge 0$).
- **Stockout Flag:** A stockout is recorded whenever $\text{Unmet Demand}_d > 0$ or $\text{Ending Stock}_d == 0$.

---

## 4. Deliverables

- Backend Schemas: `backend/app/schemas/inventory.py`
- Backend Service: `backend/app/services/inventory_simulation.py`
- Backend Router: `backend/app/routes/inventory.py` (`POST /api/inventory/simulate`, `GET /api/inventory/stock-info`)
- Frontend View: `frontend/src/pages/Inventory.jsx`
- Frontend API: `frontend/src/services/api.js`
- Test Suite: `backend/tests/test_milestone9.py`
- Documentation: `docs/MILESTONE_9_VERIFICATION_REPORT.md` and `docs/MILESTONE_9_APPROVAL.md`

