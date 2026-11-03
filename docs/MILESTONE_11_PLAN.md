# SMARTSTOCK — MILESTONE 11 IMPLEMENTATION PLAN
## Business Insights Dashboard & Final Integration

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year (Data Mining & Business Intelligence)  
> **Milestone:** 11 — Business Insights Dashboard & Final Integration  
> **Status:** PROPOSED & READY FOR IMPLEMENTATION  
> **Date:** November 2026  

---

## 1. Executive Summary & Objective

Milestone 11 is the capstone milestone of SMARTSTOCK. It brings together all previous analytical components—dataset exploration, machine learning forecasting, inventory simulation, and replenishment recommendations—into a unified, customer-friendly executive dashboard.

The goal is to communicate clear business outcomes rather than internal machine learning mechanics:
- Help retail executives instantly monitor inventory health across all stores.
- Surface automated, actionable business insights explaining **why** items are flagged and **what action** to take.
- Provide clean, interactive visual charts summarizing demand, stock levels, and store replenishment priorities.
- Unify the application navigation with plain, business-oriented terminology appropriate for store managers and academic evaluators alike.

---

## 2. Core Dashboard Components

### 2.1 Executive KPI Summary Cards
Calculated directly from actual dataset records and batch forecasting models:
1. **Total Products Monitored:** Count of distinct product SKUs (20 items).
2. **Total Stores Monitored:** Count of retail store locations (5 stores).
3. **Products Requiring Restock:** Count of store-product pairs where $S_{\text{curr}} \le \text{ROP}$.
4. **Products at Risk of Stockout:** Products where current stock runway $< 3$ days.
5. **Products with Excess Inventory:** Products where current stock $> 1.5 \times S_{\text{target}}$.
6. **Total Suggested Reorder Volume:** Cumulative sum of recommended reorder units across all stores.

### 2.2 Automated Business Insights Callouts
Plain-language narrative callouts explaining real operational priorities:
- 🔥 **Highest Predicted Demand:** Identifies the top products driving the highest upcoming sales volume, advising managers to safeguard stock.
- ⚠️ **Immediate Stockout Threat:** Identifies the store-product series with the lowest days of supply, showing exact reorder quantity required.
- 📦 **Working Capital Inefficiency (Excess Stock):** Identifies items with large stockpiles relative to demand, suggesting promotions or procurement freezes.
- 🏬 **Store Replenishment Concentration:** Identifies which store has the highest inventory replenishment demand, aiding regional logistics planning.

### 2.3 Interactive Visualizations (Recharts)
1. **Inventory Health Distribution (Donut / Bar Chart):** Visualizes the percentage and count of products across *Stock Available*, *Restock Soon*, and *Excess Stock*.
2. **Top 5 Products by Predicted Demand (Horizontal Bar Chart):** Ranks the highest velocity SKUs by expected 7-day sales.
3. **Current Stock vs. Forecasted Demand (Grouped Bar Chart):** Direct comparison for critical restock candidates.
4. **Store-wise Replenishment Need (Bar Chart):** Compares total reorder units required across stores `S001` through `S005`.

---

## 3. Customer-Friendly Navigation Architecture

The sidebar and interface terminology are polished to eliminate technical ML jargon and present a seamless business workflow:

| Previous / Technical Term | Polished Business Label | Purpose |
|---|---|---|
| Supervised Model Evaluation | **Model Performance** | View empirical accuracy metrics (MAE, RMSE) |
| Feature Engineering Pipeline | **Sales Analysis** | Historical patterns, trends, and seasonality |
| ML Prediction Architecture | **Demand Forecast** | Daily future demand forecasts (7, 14, 30 days) |
| Inventory Balance Ledger | **Inventory Simulation** | Run multi-day stock depletion and safety stock simulations |
| Restock Classification Matrix | **Inventory Recommendations** | Practical reorder plan, ROP, and suggested quantities |
| Executive Summary | **Dashboard** | Unified command center and business insights |

---

## 4. Technical Deliverables

### 4.1 Backend (`backend/app/`)
1. **Business Insights Endpoint (`backend/app/routes/recommendation.py` or `dashboard.py`)**:
   - `GET /api/recommendation/dashboard-summary`:
     - Returns KPI card values, category breakdown, top demand items, urgent stockout risks, excess stock items, and store-wise replenishment totals.
     - Fully calculated from actual data and trained models; zero hardcoded mock values.
2. **Schema Support (`backend/app/schemas/recommendation.py`)**:
   - `DashboardSummaryResponse`, `BusinessInsightItem`, `StoreRestockOverview`.

### 4.2 Frontend (`frontend/src/`)
1. **Redesigned Dashboard (`frontend/src/pages/Dashboard.jsx`)**:
   - Top Executive KPI Cards grid with trend indicators.
   - Actionable Business Insights Section with categorized alerts (Urgent, High Demand, Working Capital, Logistics).
   - Interactive Charts section using Recharts.
   - Quick Navigation shortcuts directly linking to Demand Forecast, Inventory Simulation, and Recommendations.
2. **Sidebar Navigation Update (`frontend/src/components/Sidebar.jsx`)**:
   - Ensure clean icons, clear labels, and active tab highlighting.

### 4.3 Automated Test Suite (`backend/tests/test_milestone11.py`)
10 automated unit and integration tests verifying:
- Integrity of executive KPI card metrics.
- Correctness of top demand and stockout risk calculations.
- Store replenishment aggregation math.
- Business insights data-driven generation (non-empty, non-mocked).
- Fast API response times and proper schema conformity.

