# SMARTSTOCK — USER GUIDE
## Retail Demand Forecasting & Inventory Recommendation System

> **Project:** SMARTSTOCK  
> **Academic Level:** B.Tech, Third Year (Data Mining & Business Intelligence)  
> **Target Audience:** Retail Managers, Store Supervisors, and Academic Evaluators  
> **Date:** November 2026  

---

## 1. Introduction to SMARTSTOCK

Welcome to **SMARTSTOCK**, an intelligent retail decision-support system designed to solve two core challenges faced by modern retail stores:
1. **Demand Uncertainty:** How many units of each product will customers purchase over the next week or month?
2. **Inventory Imbalance:** When should the retailer reorder stock, and how many units should be ordered to prevent stockouts while avoiding excess inventory?

SMARTSTOCK bridges machine learning predictive modeling with practical retail inventory operations. This guide walks you through every feature of the application step-by-step.

---

## 2. Getting Started & Launching the Application

### 2.1 Starting the Backend API Server
Open PowerShell or Command Prompt, navigate to the project directory, and start the FastAPI backend:
```powershell
# Navigate to project root
cd "G:\DMBI Project\DMBI-PROJECT"

# Run FastAPI backend with Uvicorn
backend\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

### 2.2 Starting the React Frontend
Open a second terminal window, navigate to the `frontend` folder, and start the Vite development server:
```powershell
cd "G:\DMBI Project\DMBI-PROJECT\frontend"
npm run dev
```
- Web Application URL: `http://localhost:5173`

---

## 3. Application Workflow Walkthrough

SMARTSTOCK features 7 dedicated modules accessible via the left sidebar navigation:

```
[1] Dashboard                  --> Executive KPI overview & business insights
[2] Dataset Upload             --> Upload, inspect, and clean retail transaction data
[3] Sales Overview             --> Explore historical trends, top categories, and store sales
[4] Model Performance          --> Compare empirical forecasting accuracy (Linear Regression vs. Random Forest)
[5] Demand Forecast            --> Generate daily future sales predictions for any store and product
[6] Inventory Simulation       --> Test stock depletion, lead-time deliveries, and fill rates
[7] Inventory Recommendations  --> View catalogue-wide restock action plan with reorder quantities
```

---

### Step 1: Uploading & Preprocessing Data (`Dataset Upload`)
1. Click **Dataset Upload** in the left sidebar.
2. The system automatically loads `cleaned_dataset.csv` (73,100 records across 5 stores and 20 products).
3. If uploading a new CSV:
   - Drag and drop your `.csv` file into the upload zone.
   - Use the **Column Mapping** interface to verify essential columns:
     - `Date`: Transaction date (e.g., `2022-01-01` to `2024-01-01`)
     - `Store ID`: Retail branch (e.g., `S001` to `S005`)
     - `Product ID`: Unique SKU identifier (e.g., `P0001` to `P0020`)
     - `Units Sold`: Quantity of items purchased
     - `Inventory Level`: Stock available on shelf/backroom
4. Click **Clean & Validate Dataset** to remove duplicates, handle missing values, and verify chronological integrity.

---

### Step 2: Exploring Historical Patterns (`Sales Overview`)
1. Click **Sales Overview** to examine historical sales patterns.
2. Review:
   - **Total Revenue & Volume:** Overall units sold across all branches.
   - **Monthly Sales Trend:** Seasonality, festive spikes, and growth patterns.
   - **Category Breakdown:** Share of sales across Clothing, Electronics, Groceries, Home & Kitchen, and Sports.
   - **Store Performance:** Comparative sales volume across stores `S001` through `S005`.

---

### Step 3: Model Performance & Selection (`Model Performance`)
1. Click **Model Performance** to review the empirical machine learning evaluation.
2. SMARTSTOCK evaluates two models on **14,700 held-out test transactions**:
   - **Linear Regression Pipeline** (Recommended Winner)
   - **Random Forest Regressor**
3. Review the key accuracy metrics:
   - **Mean Absolute Error (MAE):** Average error in units sold per day. Linear Regression achieved **88.80 units** vs Random Forest's **90.76 units**.
   - **Root Mean Squared Error (RMSE):** Sensitivity to large prediction errors. Linear Regression achieved **108.24 units** vs Random Forest's **109.88 units**.
4. The system automatically preselects Linear Regression as the primary forecasting engine due to its superior empirical generalization.

---

### Step 4: Generating Demand Forecasts (`Demand Forecast`)
1. Click **Demand Forecast** in the sidebar.
2. Select your target **Store Location** (e.g., `Store S001`) and **Product SKU** (e.g., `P0001 - Clothing`).
3. Select the desired **Forecast Horizon**:
   - `7 Days` (Weekly operational replenishment)
   - `14 Days` (Bi-weekly planning)
   - `30 Days` (Monthly inventory budget)
4. Click **Generate Demand Forecast**.
5. The interface displays:
   - **Historical Actuals vs. Future Forecast Line Chart:** 14 days of prior actual sales seamlessly transitioning into dotted future predictions.
   - **Summary Cards:** Total Expected Demand, Average Daily Velocity, Peak Demand Day.
   - **Daily Breakdown Ledger:** Expected sales for each future date with weekend indicators.
6. Click **Simulate Inventory** to carry these forecast numbers directly into the Inventory Simulation module.

---

### Step 5: Simulating Stock Depletion (`Inventory Simulation`)
1. Click **Inventory Simulation** (or arrive via the one-click bridge from Forecasting).
2. The starting inventory defaults to the actual recorded stock on `2024-01-01`. You may also type a custom starting stock.
3. Configure simulation parameters:
   - **Planned Replenishment Delivery:** Day of arrival (e.g., Day 4) and quantity received (e.g., 200 units).
   - **Safety Stock Threshold:** Minimum buffer level.
4. Click **Run Inventory Simulation**.
5. Inspect the simulation results:
   - **Daily Stock Trajectory Chart:** Visual curve tracking stock depleting day-by-day.
   - **Stockout Alerts:** Days where inventory drops to 0 units.
   - **Service Level (Fill Rate):** Percentage of customer demand fulfilled without backorders.

---

### Step 6: Reviewing Restock Recommendations (`Inventory Recommendations`)
1. Click **Inventory Recommendations** to view the catalogue-wide restock action plan.
2. Review the top KPI cards:
   - **Restock Soon:** Count of items where current stock $\le$ Reorder Point (ROP).
   - **Stock Available:** Items with healthy stock satisfying upcoming demand.
   - **Excess Stock:** Items with surplus inventory ($> 1.5\times$ target stock).
   - **Total Reorder Units:** Cumulative units recommended for purchase.
3. Filter by **Store Location**, **Category**, or **Status**.
4. Search for specific SKUs using the search bar.
5. In the table, inspect:
   - **Current Stock:** Units currently on hand.
   - **7-Day Demand:** Forecasted customer demand over next 7 days.
   - **Days of Supply (Runway):** Days before stock runs out.
   - **Reorder Point (ROP):** Threshold that triggers restocking.
   - **Suggested Order Quantity:** Non-negative units to order.
6. Click **Simulate** on any row to instantly test that product in the Inventory Simulation module.

---

### Step 7: Executive Dashboard (`Dashboard`)
1. Click **Dashboard** to view the high-level executive retail command center.
2. Review:
   - **6 Executive KPI Cards:** High-level summary of catalogue health.
   - **Automated Business Insights:** 4 actionable cards explaining *why* items are flagged (e.g. Critical Stockout Alert, Primary Sales Driver, Capital Tied in Surplus, Regional Store Logistics Priority).
   - **Interactive Visualizations:**
     - Donut chart of catalogue inventory health distribution.
     - Top 5 demand velocity SKUs.
     - Stock vs. Anticipated Demand bar chart for restock candidates.
     - Store-wise replenishment demand breakdown.
3. Click any shortcut button to jump directly into detailed operational pages.

---

## 4. Frequently Asked Questions (FAQ)

**Q: Can reorder quantities ever be negative?**  
A: No. In SMARTSTOCK, suggested reorder quantities are strictly non-negative ($\ge 0$). When a store has surplus inventory, the recommended order quantity is 0 units.

**Q: Where do the lead time and safety buffer values come from?**  
A: Since the historical dataset does not record supplier contracts, SMARTSTOCK uses transparent industry defaults (Lead Time = 2 days, Safety Buffer = 1 day) and allows managers to adjust them via the **Parameters** toggle on the Recommendations page.

**Q: How does the system prevent data leakage?**  
A: When forecasting future days $t+1, t+2, \dots, t+H$, lag features (`previous_day_sales`) and rolling features (`rolling_7_day_average`) are computed strictly recursively from previous predictions. Historical future test labels are never accessed during prediction.

