# SMARTSTOCK — MILESTONE 10 IMPLEMENTATION PLAN
## Smart Inventory Recommendation

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year (Data Mining & Business Intelligence)  
> **Milestone:** 10 — Smart Inventory Recommendation  
> **Status:** PROPOSED & READY FOR IMPLEMENTATION  
> **Date:** November 2026  

---

## 1. Executive Summary & Objective

The objective of Milestone 10 is to translate future retail demand forecasts (from Milestone 8) and stock levels (from Milestone 9) into actionable, practical inventory replenishment recommendations.

Rather than presenting raw statistical forecasts in isolation, SMARTSTOCK will empower retail store managers to answer 5 fundamental business questions:
1. **Which products need restocking urgently?**
2. **Which products have sufficient stock to satisfy customer demand?**
3. **Which products have excess inventory tying up working capital?**
4. **When should a reorder be triggered (Reorder Point)?**
5. **How many units should be reordered (Suggested Reorder Quantity)?**

All recommendations are derived deterministically from actual dataset records and machine learning forecasts—never fabricated or hardcoded.

---

## 2. Dataset & Column Analysis

### 2.1 Available Fields in `cleaned_dataset.csv`
- **Store Identifiers:** 5 unique stores (`S001`, `S002`, `S003`, `S004`, `S005`).
- **Product Identifiers:** 20 unique products (`P0001` through `P0020`) across multiple product categories (Electronics, Clothing, Groceries, Home & Kitchen, Sports).
- **Time Horizon:** 731 daily records per store-product pair (from `2022-01-01` to `2024-01-01`). Total records: 73,100 rows.
- **Ending Inventory Level:** Recorded in the dataset on the latest transaction date (`2024-01-01`) for all 100 series (ranging from 50 to 500 units).
- **Historical Sales:** Daily transactional units sold.

### 2.2 Missing Parameter Handling
- Supplier **Lead Time** ($L$) and **Safety Stock Buffer** ($S_{\text{buf}}$) are not distinct columns in the raw historical dataset.
- In strict adherence to Section 10.1 of the requirements:
  - We do **not** invent synthetic data columns or assume hidden fields exist.
  - We establish transparent, sensible defaults: **Lead Time = 2 days**, **Safety Buffer = 1 day**.
  - We allow the retail user to adjust these parameters dynamically through the API and frontend interface.

---

## 3. Mathematical Formulas & Inventory Logic

For each store $s$ and product $p$, across planning horizon $H$ (default = 7 days):

### 3.1 Forecasted Demand & Daily Velocity
$$\hat{D}_{\text{horizon}} = \sum_{t=1}^{H} \hat{d}_t$$
$$\bar{d} = \frac{\hat{D}_{\text{horizon}}}{H} \quad (\text{Average Daily Demand})$$

### 3.2 Lead Time Demand & Safety Stock
$$D_L = \bar{d} \times L \quad (\text{Expected Demand during Supplier Lead Time})$$
$$SS = \bar{d} \times S_{\text{buf}} \quad (\text{Buffer for demand spikes})$$

### 3.3 Reorder Point (ROP)
$$\text{ROP} = D_L + SS = \bar{d} \times (L + S_{\text{buf}})$$
- **Retail Meaning:** If current stock falls to or below $\text{ROP}$, placing an order immediately ensures the new shipment arrives before stock drops to zero.

### 3.4 Target Stock Level
$$S_{\text{target}} = \hat{D}_{\text{horizon}} + SS$$

### 3.5 Suggested Reorder Quantity ($Q_{\text{reorder}}$)
$$Q_{\text{reorder}} = \begin{cases} 
\max(0, \text{round}(S_{\text{target}} - S_{\text{curr}})) & \text{if } S_{\text{curr}} \le \text{ROP} \\
0 & \text{if } S_{\text{curr}} > \text{ROP}
\end{cases}$$
- **Retail Meaning:** We only reorder when stock is at or below the reorder threshold. Reorder quantity is strictly non-negative ($\ge 0$).

### 3.6 Stock Runway / Days of Supply
$$\text{Runway (Days)} = \begin{cases} 
\text{round}\left(\frac{S_{\text{curr}}}{\bar{d}}, 1\right) & \text{if } \bar{d} > 0 \\
\infty & \text{if } \bar{d} = 0
\end{cases}$$

---

## 4. Recommendation Classification Categories

Every product in every store is categorized into one of four mutually exclusive, transparent statuses:

| Status Category | Mathematical Condition | Business Explanation | UI Badge |
|---|---|---|---|
| **Restock Soon** | $S_{\text{curr}} \le \text{ROP}$ | Stock cannot cover lead-time demand + safety buffer; stockout risk within $L$ days. | 🔴 Red |
| **Stock Available** | $\text{ROP} < S_{\text{curr}} \le S_{\text{target}} \times 1.5$ | Stock is healthy and comfortably satisfies expected demand without overstocking. | 🟢 Green |
| **Excess Stock** | $S_{\text{curr}} > S_{\text{target}} \times 1.5$ | Inventory exceeds 150% of target stock; cash is unnecessarily locked in idle goods. | 🟡 Amber |
| **Insufficient Data** | Historical transactions $< 7$ days | Reliable forecast cannot be generated due to sparse data. | ⚪ Gray |

---

## 5. Technical Deliverables

### 5.1 Backend (`backend/app/`)
1. **Schema (`backend/app/schemas/recommendation.py`)**:
   - `RecommendationItem`: Stores `store_id`, `product_id`, `category`, `current_stock`, `forecasted_demand`, `daily_demand`, `lead_time_days`, `reorder_point`, `target_stock`, `suggested_reorder_qty`, `days_of_supply`, `status`, `notes`.
   - `RecommendationSummary`: Aggregated counts (`total_products`, `restock_soon_count`, `stock_available_count`, `excess_stock_count`, `insufficient_data_count`, `total_reorder_units`).
   - `RecommendationResponse`: Contains `summary`, `items`, `stores`, `categories`, and `calculated_at`.
2. **Service (`backend/app/services/inventory_recommendation.py`)**:
   - Fast batch forecast evaluation across all 100 store-product series using trained Scikit-learn Linear Regression pipeline.
   - Deterministic computation of ROP, target stock, and classification.
   - Filtering by store, category, and status.
3. **Route (`backend/app/routes/recommendation.py`)**:
   - `GET /api/recommendation/all`: Returns full recommendation dataset with query filters (`store_id`, `status`, `lead_time`, `safety_buffer`, `horizon_days`).
   - `POST /api/recommendation/calculate`: Custom parameters calculation.
4. **App Integration (`backend/app/main.py`)**:
   - Register `recommendation_router` under prefix `/api/recommendation`.

### 5.2 Frontend (`frontend/src/`)
1. **API Client (`frontend/src/services/api.js`)**:
   - Add `getInventoryRecommendations(params)`.
2. **Page (`frontend/src/pages/Recommendations.jsx`)**:
   - Metric summary cards (Restock Soon, Stock Available, Excess Stock, Total Reorder Units).
   - Filter bar: Store dropdown, Status pills, Category dropdown, Search box.
   - Responsive Recommendation Table with badges, stock levels, runway, and suggested order units.
   - Direct Action Button: "Simulate Inventory" navigates directly to Milestone 9 simulation pre-populated with selected store and product.
3. **Navigation (`frontend/src/components/Sidebar.jsx` & `App.jsx`)**:
   - Add `Inventory Recommendations` with icon to sidebar.
   - Register route in `App.jsx`.

### 5.3 Automated Test Suite (`backend/tests/test_milestone10.py`)
10 comprehensive unit & integration tests covering:
- Correct schema validation.
- Non-negative reorder quantities.
- Formula accuracy (ROP, Target Stock, Suggested Reorder).
- Edge cases (zero demand, high stock, zero stock).
- Filtering logic.
- API endpoint availability.

