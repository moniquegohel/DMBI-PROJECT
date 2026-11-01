# SmartStock: Implementation Plan & Project Specification

> **Project Title:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Target Audience:** B.Tech 3rd-Year Academic Project / Beginners  
> **Key Objective:** Provide an end-to-end, beginner-friendly web application for retail sales cleaning, machine learning demand forecasting (Linear Regression & Random Forest), evaluation (MAE/RMSE/MAPE), 7-day demand forecasting, and inventory recommendation.

---

## 1. Project Understanding

SmartStock is a beginner-friendly full-stack business intelligence and demand forecasting system designed for B.Tech academic evaluation. Retailers often struggle with two costly problems: **overstocking** (leading to wasted capital and storage fees) and **stockouts** (leading to lost revenue and customer dissatisfaction).

SmartStock addresses this by allowing users to:
1. Upload public retail sales data (CSV format).
2. Clean and validate dataset anomalies.
3. Perform exploratory historical sales analysis with interactive visualizations.
4. Engineer time-based lag and rolling features.
5. Train two straightforward machine learning regression models (Linear Regression and Random Forest Regression).
6. Compare models chronologically using standard metrics (MAE, RMSE, MAPE).
7. Forecast product demand for at least 7 days.
8. Simulate inventory depletion and compute clear reorder recommendations (Stockout Risk, Overstock, Sufficient Stock, and Reorder Quantity).

The code will focus on **readability, modularity, and explainability for viva presentations**, avoiding over-engineering (no microservices, cloud deployment, deep learning, or complex hyperparameter tuning).

---

## 2. Core Requirements Summary

### A. Functional Requirements
* **Dataset Ingestion & Cleaning:** Upload retail CSV, validate columns, parse dates, handle missing values, drop duplicates, and generate dataset summary.
* **Historical Sales Analysis:** Compute total/avg/min/max sales, monthly trends, and product-wise sales aggregations.
* **Feature Engineering:** Create time features (`day`, `day_of_week`, `month`, `is_weekend`) and sales features (`previous_day_sales` / `lag_1`, `rolling_7_day_average`).
* **Machine Learning:** Perform 80/20 chronological train/test split. Train Linear Regression & Random Forest Regressor models without random shuffling.
* **Model Evaluation:** Calculate MAE, RMSE, MAPE (handling zero values), and generate Actual vs. Predicted comparison data.
* **Demand Forecast:** Generate a 7-day daily demand forecast for a selected product using recursive feature updates.
* **Inventory Simulation & Recommendation:** Accept user inputs (`current_stock`, `safety_stock`, `supplier_lead_time`), simulate day-by-day stock depletion, identify stockout/overstock conditions, and calculate `reorder_quantity`.

### B. Business Logic Formulas
1. **Stockout Risk:** `Current Stock < Total Predicted 7-Day Demand`
2. **Overstock:** `Current Stock > Total Predicted 7-Day Demand + Safety Stock`
3. **Sufficient Stock:** Otherwise
4. **Reorder Quantity:** `max(0, Total Predicted 7-Day Demand + Safety Stock - Current Stock)`

---

## 3. Proposed Architecture

```text
                      [ USER INTERFACE ]
                              │
                    React + Vite + Tailwind CSS
                              │
                     REST API / JSON Calls
                              │
                      [ FASTAPI BACKEND ]
                              │
   ┌──────────────────────────┼──────────────────────────┐
   │                          │                          │
   ▼                          ▼                          ▼
[ SQLite DB ]         [ Data Services ]            [ ML Services ]
SQLAlchemy            Pandas & NumPy               Scikit-Learn & Joblib
 - Products            - Cleaning & Validation      - Feature Creation
 - Cleaned Sales       - Historical Aggregations    - LR & RF Models
 - Saved Results       - Inventory Logic            - 7-Day Recursive Forecast
```

---

## 4. Data Requirements Analysis

### Required CSV Columns
* **Date Column:** `date` or `sale_date` (parseable to YYYY-MM-DD format).
* **Product Identifier:** `product_id` or `product_code` or `product_name`.
* **Sales/Demand Volume:** `quantity_sold` or `sales` (numeric integer/float).

### Optional Supported Columns
* `price`, `category`, `promotion`, `holiday`, `store_id`.

### Dataset Characteristics
* **Time Range:** Minimum 6 to 12 months of consecutive daily records to properly construct 7-day rolling averages and lag features.
* **Product Scope:** 5 to 20 products for manageable multi-product dropdown selections.
* **Size:** ~1,000 to 50,000 records (lightweight, runs fast on any developer laptop).

---

## 5. Machine Learning Workflow

```text
Uploaded CSV
    │
    ▼
Data Cleaning & Chronological Sorting
    │
    ▼
Feature Engineering (day, day_of_week, month, is_weekend, lag_1, rolling_7)
    │
    ▼
Chronological 80/20 Train/Test Split (No Shuffling)
    │
    ├─────────────────────────────┐
    ▼                             ▼
Train Linear Regression     Train Random Forest
    │                             │
    └──────────────┬──────────────┘
                   ▼
Evaluate on Test Data (MAE, RMSE, MAPE)
                   │
                   ▼
Save Models (.joblib) & Log Evaluation Metrics
                   │
                   ▼
Recursive 7-Day Forecasting for Selected Product
```

---

## 6. Inventory Decision Workflow

```text
Inputs: product_id, current_stock, safety_stock, supplier_lead_time
                          │
                          ▼
             Retrieve 7-Day Predicted Demand
                          │
                          ▼
           Simulate Daily Remaining Stock:
   Remaining Stock(t) = max(0, Remaining Stock(t-1) - Demand(t))
                          │
                          ▼
                Evaluate Stock Status:
  ┌───────────────────────┼───────────────────────┐
  ▼                       ▼                       ▼
Current Stock < Demand   Current Stock >          Otherwise
                         Demand + Safety Stock
  │                       │                       │
  ▼                       ▼                       ▼
STOCKOUT RISK           OVERSTOCK           SUFFICIENT STOCK
  │                       │                       │
  └───────────────────────┼───────────────────────┘
                          │
                          ▼
Calculate Reorder Quantity = max(0, Demand + Safety Stock - Current Stock)
```

---

## 7. Database Plan (SQLite + SQLAlchemy)

| Table Name | Purpose | Key Fields |
| :--- | :--- | :--- |
| `products` | Store unique product definitions | `id`, `product_code`, `product_name`, `category`, `price`, `created_at` |
| `sales` | Store cleaned daily sales transactions | `id`, `product_id`, `sale_date`, `quantity_sold`, `promotion`, `created_at` |
| `inventory` | Store simulated inventory states per product | `id`, `product_id`, `current_stock`, `safety_stock`, `supplier_lead_time`, `updated_at` |
| `forecasts` | Store generated demand forecasts | `id`, `product_id`, `forecast_date`, `predicted_demand`, `model_name`, `created_at` |
| `model_results` | Store evaluation scores of trained models | `id`, `model_name`, `mae`, `rmse`, `mape`, `training_date` |

---

## 8. API Plan

| Method | Endpoint | Purpose | Input | Output JSON |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/dataset/upload` | Upload & clean retail CSV | Multipart File | Dataset summary (records, missing, duplicates, date range) |
| `GET` | `/api/dataset/summary` | Fetch dataset statistics | None | Detailed summary stats |
| `GET` | `/api/analysis/summary` | Global sales metrics | None | Total, Avg, Min, Max sales |
| `GET` | `/api/analysis/monthly` | Aggregate monthly trend | None | Array of `{ month, total_sales }` |
| `GET` | `/api/analysis/products` | Top-selling products | None | Array of `{ product_name, total_sales }` |
| `GET` | `/api/products` | List product options | None | List of product IDs & names |
| `POST` | `/api/model/train` | Train LR & RF models | None / Options | Evaluation metrics & actual vs predicted data |
| `GET` | `/api/model/results` | Fetch stored evaluation scores | None | MAE, RMSE, MAPE table data |
| `POST` | `/api/forecast` | Generate 7-day demand forecast | `{ product_id, days, model }` | Daily forecast array `{ date, predicted_demand }` |
| `POST` | `/api/inventory/analyze` | Run simulation & recommendation | `{ product_id, current_stock, safety_stock, lead_time }` | Status badge, reorder quantity, simulation table |

---

## 9. Frontend Plan (React + Vite + Tailwind + Recharts)

* **Navigation Sidebar:** Persistent links for switching between all 6 pages.
* **Page 1: Dashboard (`Dashboard.jsx`)**
  * Top Summary Stat Cards: Total Revenue/Sales, Product Count, Total Records, Date Range.
  * Main Charts: Sales Trend overview, Top Products bar chart, Quick Inventory Status summary.
* **Page 2: Dataset (`Dataset.jsx`)**
  * Drag-and-drop CSV upload section.
  * Cleaning feedback report (records before/after, missing values fixed, duplicates dropped).
  * Preview table of cleaned dataset records.
* **Page 3: Sales Analysis (`SalesAnalysis.jsx`)**
  * Key sales stats cards (Min, Max, Avg, Total).
  * Interactive Recharts: Line chart of daily sales trend, Bar chart of monthly totals, Pie/Bar chart of top products.
* **Page 4: Model Training (`ModelTraining.jsx`)**
  * Interactive "Train Models" action trigger.
  * Comparative Evaluation Table displaying MAE, RMSE, MAPE for Linear Regression vs. Random Forest.
  * Recharts Line Chart: Actual Sales vs. Predicted Sales overlay on test set.
* **Page 5: Demand Forecast (`DemandForecast.jsx`)**
  * Controls: Product select dropdown, Model selection radio/select, Horizon picker (default 7 days).
  * Visuals: 7-Day Forecast Line Chart and detailed daily demand data table.
* **Page 6: Inventory Analysis (`Inventory.jsx`)**
  * Form inputs: Product, Current Stock, Safety Stock, Lead Time.
  * Visual Indicators: Status Badge (STOCKOUT RISK / OVERSTOCK / SUFFICIENT STOCK).
  * Reorder Recommendation Callout Box with exact calculated quantity.
  * Day-by-Day stock depletion table and chart.

---

## 10. Folder Structure Plan

```text
smartstock/
├── README.md
├── SMARTSTOCK_REQUIREMENTS.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── routes/
│   │   │   ├── dataset.py
│   │   │   ├── analysis.py
│   │   │   ├── model.py
│   │   │   ├── forecast.py
│   │   │   └── inventory.py
│   │   ├── services/
│   │   │   ├── data_cleaning.py
│   │   │   ├── analysis.py
│   │   │   ├── feature_engineering.py
│   │   │   ├── model_training.py
│   │   │   ├── forecasting.py
│   │   │   └── inventory_logic.py
│   │   └── schemas/
│   │       └── schemas.py
│   ├── models/             # Saved joblib model binaries (.joblib)
│   ├── data/               # Uploaded / sample CSV files
│   ├── requirements.txt
│   └── tests/
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   ├── Sidebar.jsx
    │   │   ├── StatCard.jsx
    │   │   ├── ChartCard.jsx
    │   │   ├── DataTable.jsx
    │   │   └── LoadingSpinner.jsx
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── Dataset.jsx
    │   │   ├── SalesAnalysis.jsx
    │   │   ├── ModelTraining.jsx
    │   │   ├── DemandForecast.jsx
    │   │   └── Inventory.jsx
    │   ├── services/
    │   │   └── api.js
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.js
```

---

## 11. 12-Milestone Development Roadmap

| Milestone | Objective | Key Tasks | Verification Step |
| :--- | :--- | :--- | :--- |
| **M1: Architecture Setup** | Foundation | Create folder structure, configure FastAPI and React+Vite, test CORS ping. | Backend returns `{ "status": "ok" }`, Frontend displays basic layout. |
| **M2: Database Setup** | Local DB | Configure SQLite + SQLAlchemy models (`products`, `sales`, `inventory`, `forecasts`). | Run script creating DB file and writing/querying sample product. |
| **M3: Dataset Upload & Clean** | CSV Ingestion | File upload endpoint, column mapping, null/duplicate handling, DB storage. | Upload test CSV via API/UI and verify cleaning stats response. |
| **M4: Historical Analysis** | BI Analytics | Compute summary stats, monthly aggregations, product breakdown APIs. | Verify API output matches manual Pandas calculations on test data. |
| **M5: Feature Engineering** | ML Preprocessing | Build `day`, `day_of_week`, `month`, `is_weekend`, `lag_1`, `rolling_7` features. | Inspect generated DataFrame columns and check for data leakage. |
| **M6: Model Training** | ML Models | Chronological 80/20 train/test split. Fit Linear Regression & Random Forest. | Models train cleanly and generate `.joblib` files. |
| **M7: Model Evaluation** | Evaluation | Compute MAE, RMSE, MAPE. Generate Actual vs. Predicted comparison JSON. | Display evaluation summary table comparing LR vs. RF scores. |
| **M8: Demand Forecast** | Forecasting | Construct 7-day recursive forecasting pipeline for selected product. | Request 7-day forecast for Product A and receive valid predictions. |
| **M9: Inventory Simulation** | Inventory Engine | Build day-by-day stock depletion simulator using predicted demand. | Input 500 stock, forecast [100,100...], verify daily depletion to 0. |
| **M10: Recommendation Logic** | Logic Engine | Implement Stockout Risk, Overstock, Sufficient Stock & Reorder Quantity formulas. | Test all 5 edge cases (Stock > Demand, Stock < Demand, 0 Stock, etc.). |
| **M11: Full Integration** | UI Hookup | Connect all React pages to backend FastAPI endpoints via Axios/Fetch. | Perform end-to-end workflow in browser without console errors. |
| **M12: Testing & Viva Prep** | Quality Assurance | End-to-end bug fixing, documentation, screenshots, viva QA preparation. | Smooth live demo without touching code. |

---

## 12. Team Responsibilities (4 Students)

### Student 1 — Dataset & Data Preparation
* **Focus:** Data ingestion, validation, cleaning, and database persistence.
* **Files:** `backend/app/routes/dataset.py`, `services/data_cleaning.py`, `database/models.py`.
* **Output:** Cleaned dataset saved in SQLite and ready for analysis.

### Student 2 — Machine Learning & Evaluation
* **Focus:** Feature engineering, ML pipeline (Linear Regression & Random Forest), evaluation metrics.
* **Files:** `backend/app/services/feature_engineering.py`, `services/model_training.py`, `routes/model.py`.
* **Output:** Trained `.joblib` models and MAE/RMSE/MAPE evaluation comparisons.

### Student 3 — Forecasting & Inventory Recommendation
* **Focus:** 7-Day recursive demand forecasting, daily inventory simulation, recommendation logic.
* **Files:** `backend/app/services/forecasting.py`, `services/inventory_logic.py`, `routes/forecast.py`, `routes/inventory.py`.
* **Output:** Verified 7-day forecasts and inventory decision outputs.

### Student 4 — Frontend & Integration
* **Focus:** React UI layout, Tailwind CSS styling, Recharts integration, API connection (`api.js`).
* **Files:** Entire `frontend/src/` folder (`pages/`, `components/`, `services/api.js`).
* **Output:** Interactive, user-friendly business intelligence web dashboard.

---

## 13. Risks and Mitigation Strategies

1. **Inconsistent CSV Column Names:**  
   * *Risk:* User uploads CSV with columns like `Sales_Qty`, `Date_Time`, `Item`.  
   * *Mitigation:* Flexible column mapping dictionary in `data_cleaning.py` that normalizes column names upon upload.
2. **Division by Zero in MAPE:**  
   * *Risk:* Actual demand on a day is `0`, causing `(actual - pred) / actual` to fail.  
   * *Mitigation:* Implement standard epsilon smoothing or calculate MAPE only on non-zero demand days (`actual > 0`).
3. **Data Leakage in Time Series Split:**  
   * *Risk:* Standard `train_test_split(shuffle=True)` leaks future information into historical training.  
   * *Mitigation:* Use strict chronological indexing (`train = df.iloc[:int(len(df)*0.8)]`).
4. **Recursive Feature Generation for 7-Day Forecast:**  
   * *Risk:* Future dates don't have known `previous_day_sales` or `rolling_7_day_average`.  
   * *Mitigation:* Sequentially forecast day $t$, update the feature vector with predicted demand for day $t+1$, and iterate 7 times.

---

## 14. Recommended Starting Point

1. **Step 1:** Gain user review and approval for this Implementation Plan.
2. **Step 2 (Milestone 1):** Initialize project directory structure (`backend/` and `frontend/`), set up FastAPI and Vite React applications, and establish initial communication.

---

## 15. Definition of Done Checklist

- [ ] Retail CSV upload & validation functionality working.
- [ ] Data cleaning produces missing/duplicate summary reports.
- [ ] Historical sales analysis cards & Recharts rendering real dataset metrics.
- [ ] Feature engineering creates lag and rolling window features.
- [ ] Chronological 80/20 train/test split implemented without shuffling.
- [ ] Linear Regression & Random Forest models trained and evaluated.
- [ ] Evaluation table displaying MAE, RMSE, and MAPE scores.
- [ ] Actual vs. Predicted comparison chart displayed.
- [ ] Product selection generates a 7-day demand forecast.
- [ ] Inventory simulation computes daily remaining stock.
- [ ] Inventory recommendation correctly detects Stockout Risk, Overstock, and Sufficient Stock.
- [ ] Reorder Quantity formula computed accurately.
- [ ] Full end-to-end user workflow operational through the web browser.
