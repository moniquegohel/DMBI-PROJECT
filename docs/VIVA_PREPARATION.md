# SMARTSTOCK — VIVA PREPARATION GUIDE
## Comprehensive Questions & Answers for B.Tech Academic Viva

> **Project Title:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Subject:** Data Mining & Business Intelligence (DMBI) — B.Tech 3rd Year  
> **Target Audience:** Students defending their project before External Examiners  
> **Date:** November 2026  

---

## SECTION 1: PROJECT FUNDAMENTALS

### Q1: What is SMARTSTOCK in simple words?
**Answer:**  
SMARTSTOCK is an end-to-end retail intelligence web application. It takes historical daily sales and inventory records, trains machine learning models to forecast future customer demand across store branches, and calculates practical inventory replenishment recommendations—telling retailers exactly which products to restock, when to reorder, and how many units to purchase.

### Q2: What business problem does SMARTSTOCK solve?
**Answer:**  
Retail stores constantly face the **inventory dilemma**:
- If they order **too little stock**, products run out (stockouts), leading to lost revenue and unhappy customers.
- If they order **too much stock**, surplus products sit idle on shelves (excess stock), tying up working capital and risking obsolescence or spoilage.
SMARTSTOCK solves this by replacing guesswork with data-driven machine learning demand forecasting and calculated Reorder Points (ROP).

### Q3: Why is demand forecasting important in retail?
**Answer:**  
Suppliers require lead time to deliver goods. A store cannot wait until shelves are empty to place an order. Demand forecasting gives retailers advance visibility into customer sales velocity so purchase orders can be dispatched early enough to arrive before stockouts occur.

### Q4: What is the significance of Data Mining and Business Intelligence (DMBI) in this project?
**Answer:**  
- **Data Mining:** Extracting hidden trends, seasonal cycles, day-of-week patterns, and price elasticities from 73,100 raw transaction records through feature engineering and predictive modeling.
- **Business Intelligence:** Transforming raw machine learning predictions into actionable executive KPIs, status badges (*Restock Soon*, *Stock Available*, *Excess Stock*), and visual dashboards that non-technical store managers can immediately use to make business decisions.

---

## SECTION 2: MACHINE LEARNING & EVALUATION

### Q5: What is Linear Regression, and how does it work here?
**Answer:**  
Linear Regression models the relationship between independent input features (day of week, month, price, discount, previous day's sales, 7-day rolling average, store, and product) and continuous target demand ($y$) using a weighted linear combination:
$$\hat{y} = \beta_0 + \sum_{j=1}^p \beta_j X_j$$
The model learns coefficients $\beta_j$ by minimizing the sum of squared residuals (Ordinary Least Squares).

### Q6: What is Random Forest Regression, and how does it work?
**Answer:**  
Random Forest is an ensemble learning method that builds multiple decision trees (in our project, 100 trees) using bootstrap sampling (bagging) and random feature subsets. Each tree makes an independent prediction, and the forest outputs the average prediction across all trees:
$$\hat{y} = \frac{1}{B} \sum_{b=1}^B T_b(X)$$
This helps capture non-linear interactions between variables.

### Q7: Why did Linear Regression beat Random Forest in your empirical evaluation?
**Answer:**  
On our held-out chronological test set of 14,700 records:
- **Linear Regression:** MAE = **88.80 units**, RMSE = **108.24 units**, MAPE = **342.94%**.
- **Random Forest:** MAE = **90.76 units**, RMSE = **109.88 units**, MAPE = **358.93%**.
Linear Regression performed better because retail demand trends in this dataset exhibit smooth momentum and strong calendar periodicity. Random Forest tended to slightly overfit historical fluctuations and had higher variance on extreme points.

### Q8: How was the dataset split into training and testing data?
**Answer:**  
We used a **chronological time-series split** rather than random shuffling:
- **Training Set (80%):** 58,400 records from `2022-01-01` to `2023-08-08`.
- **Testing Set (20%):** 14,700 records from `2023-08-09` to `2024-01-01`.
Random splitting would cause **data leakage** because future sales information would leak into the training process.

### Q9: What are MAE, RMSE, and MAPE, and how do they differ?
**Answer:**  
1. **MAE (Mean Absolute Error):** Measures the average magnitude of errors in the same units as the target:
   $$\text{MAE} = \frac{1}{N} \sum |y_i - \hat{y}_i|$$
   It treats all errors proportionally.
2. **RMSE (Root Mean Squared Error):** Squares the errors before averaging:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum (y_i - \hat{y}_i)^2}$$
   It penalizes large individual prediction mistakes more heavily than MAE.
3. **MAPE (Mean Absolute Percentage Error):** Expresses error as a percentage of actual sales:
   $$\text{MAPE} = \frac{100\%}{N} \sum \left|\frac{y_i - \hat{y}_i}{y_i}\right|$$
   *Note:* Records with zero actual sales are excluded to avoid division-by-zero.

### Q10: What is Feature Engineering, and what features were created?
**Answer:**  
Feature engineering transforms raw timestamps and transaction attributes into informative predictors:
- **Calendar Features:** `day`, `day_of_week`, `month`, `is_weekend` (to capture weekend shopping spikes).
- **Lag Feature (`previous_day_sales`):** Yesterday's sales ($t-1$) to capture short-term momentum.
- **Rolling Feature (`rolling_7_day_average`):** The average sales of the preceding 7 days to smooth out daily fluctuations and capture underlying weekly trends.

### Q11: What is Data Leakage, and how did you prevent it?
**Answer:**  
Data leakage occurs when information from the future or from the test set unintentionally leaks into model training or feature generation. We prevented it by:
1. Splitting data strictly chronologically.
2. Computing lag and rolling features using strictly prior days ($t-1$ to $t-7$).
3. In multi-step future forecasting, future lag features are updated **recursively** using earlier predictions, never actual future numbers.

---

## SECTION 3: INVENTORY MANAGEMENT & RECOMMENDATIONS

### Q12: What is a Stockout?
**Answer:**  
A stockout is an event where customer demand for a product exceeds available on-hand inventory, resulting in empty shelves, zero sales fulfilled, and unfulfilled customer demand.

### Q13: What is Safety Stock, and why is it needed?
**Answer:**  
Safety stock ($SS$) is a buffer of surplus inventory held to protect against unexpected demand surges or supplier delivery delays:
$$SS = \text{Daily Demand} \times \text{Safety Buffer Days}$$
In our application, the default buffer is 1 day.

### Q14: What is a Reorder Point (ROP)?
**Answer:**  
The Reorder Point is the minimum stock level that triggers a new purchase order:
$$\text{ROP} = \text{Lead Time Demand} + \text{Safety Stock} = \bar{d} \times (L + S_{\text{buf}})$$
When current on-hand stock falls to or below ROP, placing an order immediately ensures the replenishment shipment arrives before stock drops to zero.

### Q15: How does SMARTSTOCK calculate Suggested Reorder Quantity?
**Answer:**  
1. If $\text{Current Stock} \le \text{ROP}$:
   $$Q_{\text{reorder}} = \max(0, \text{round}(S_{\text{target}} - \text{Current Stock}))$$
   where $S_{\text{target}} = \text{Forecasted Demand} + \text{Safety Stock}$.
2. If $\text{Current Stock} > \text{ROP}$:
   $$Q_{\text{reorder}} = 0$$
Reorder quantities are strictly non-negative ($\ge 0$).

### Q16: How are products classified into recommendation categories?
**Answer:**  
- **Restock Soon:** $\text{Current Stock} \le \text{ROP}$ (Stock cannot cover lead-time demand + safety buffer).
- **Stock Available:** $\text{ROP} < \text{Current Stock} \le 1.5 \times S_{\text{target}}$ (Healthy inventory).
- **Excess Stock:** $\text{Current Stock} > 1.5 \times S_{\text{target}}$ (Surplus stock tying up cash).
- **Insufficient Data:** Time-series transactions $< 7$ days (Cannot compute reliable rolling features).

### Q17: What does the Inventory Simulation module do?
**Answer:**  
It tracks the daily beginning inventory, adds planned replenishment arrivals on the scheduled delivery day, subtracts forecasted demand, caps ending stock at $\ge 0$, records any unmet customer demand, and calculates the overall **Service Level (Fill Rate %)**.

---

## SECTION 4: TECHNICAL IMPLEMENTATION & ARCHITECTURE

### Q18: Why did you choose FastAPI for the backend?
**Answer:**  
- Native asynchronous execution and high performance.
- Automatic input validation and data serialization using Pydantic schemas.
- Auto-generated interactive documentation via Swagger UI (`/docs`).
- Seamless integration with Python's scientific and machine learning libraries (Pandas, NumPy, Scikit-learn, Joblib).

### Q19: Why did you choose React for the frontend?
**Answer:**  
- Component-based architecture for reusable UI widgets (KPI cards, filter bars, data tables).
- Declarative state management enabling dynamic chart and table updates without full page reloads.
- Excellent ecosystem: Tailwind CSS for modern responsive styling, Recharts for smooth SVG charting, and Lucide React for consistent icons.

### Q20: How does the frontend communicate with the backend?
**Answer:**  
Communication happens via asynchronous HTTP REST calls using Axios. In local development, the Vite server proxies `/api` requests to the FastAPI server running on `http://127.0.0.1:8000`.

### Q21: How are sub-second responses achieved for 100 series in the recommendation engine?
**Answer:**  
1. The trained Scikit-learn Linear Regression pipeline uses fast vectorized matrix operations ($\approx 0.5$ seconds for all 700 predictions).
2. Computed recommendations are cached in memory. Subsequent filter requests (by store, status, or category) are served directly from cache in under 10 milliseconds.

---

## SECTION 5: PROJECT-SPECIFIC QUESTIONS & NUMBERS

### Q22: What are the exact dataset details?
**Answer:**  
- **Total Rows:** 73,100 records
- **Number of Stores:** 5 stores (`S001`, `S002`, `S003`, `S004`, `S005`)
- **Number of Products:** 20 products (`P0001` through `P0020`)
- **Number of Series:** $5 \times 20 = 100$ continuous time-series
- **Date Range:** `2022-01-01` to `2024-01-01` (731 days per series)
- **Categories:** Clothing, Electronics, Groceries, Home & Kitchen, Sports

### Q23: How many automated tests exist in SMARTSTOCK?
**Answer:**  
The project features **50 automated unit and integration tests** across 5 test suites (10 tests per milestone):
- `test_milestone7.py`: 10 tests (Model Evaluation & Comparison)
- `test_milestone8.py`: 10 tests (Demand Forecasting)
- `test_milestone9.py`: 10 tests (Inventory Simulation)
- `test_milestone10.py`: 10 tests (Inventory Recommendations)
- `test_milestone11.py`: 10 tests (Business Insights Dashboard)
**Result: All 50 tests pass with 100% green status.**

### Q24: What are the main limitations of your project?
**Answer:**  
1. **Unrecorded Lead Times:** The dataset does not contain vendor contract records, so supplier lead time is modeled with configurable defaults (2 days lead time, 1 day safety buffer).
2. **Point Forecasts:** The models produce deterministic point estimates rather than probabilistic confidence intervals.
3. **Single-Echelon Scope:** Models store-level replenishment rather than a multi-tier network (e.g., Central Distribution Center to Regional Hub to Store).

