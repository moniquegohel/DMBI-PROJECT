# SMARTSTOCK — TECHNICAL DOCUMENTATION
## Architectural Design, Mathematical Foundations & API Specifications

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year (Data Mining & Business Intelligence)  
> **Target Audience:** Technical Examiners, Software Engineers, and Data Scientists  
> **Date:** November 2026  

---

## 1. System Architecture Overview

SMARTSTOCK is built on a decoupled, modular client-server architecture designed for high maintainability, deterministic calculations, and interactive visualization.

```
+-------------------------------------------------------------------------------+
|                             REACT 19 FRONTEND                                 |
|   (Vite Build, Tailwind CSS, Recharts Visualization, Lucide Iconography)      |
+---------------------------------------+---------------------------------------+
                                        |  Axios HTTP / JSON REST APIs
                                        v
+-------------------------------------------------------------------------------+
|                            FASTAPI BACKEND (Python 3.14)                      |
|                                                                               |
|   [/api/dataset]        [/api/analysis]       [/api/model]                    |
|   - CSV Upload          - Sales Aggregates    - Feature Engineering           |
|   - Data Cleaning       - Category Trends     - Model Training                |
|   - Column Mapping      - Store Metrics       - Empirical Evaluation          |
|                                                                               |
|   [/api/forecast]       [/api/inventory]      [/api/recommendation]           |
|   - Multi-Step Forecast - Stock Depletion     - ROP & Safety Stock            |
|   - Horizon Selection   - Fill Rate Sim       - Executive Dashboard KPIs      |
+---------------------------------------+---------------------------------------+
                                        |
                   +--------------------+--------------------+
                   |                                         |
                   v                                         v
+--------------------------------------+   +------------------------------------+
|          PERSISTENCE LAYER           |   |       MACHINE LEARNING ENGINE      |
|  - cleaned_dataset.csv (73.1k rows)  |   |  - Scikit-learn Linear Regression  |
|  - SQLite (smartstock.db) metadata   |   |  - Scikit-learn Random Forest      |
|  - joblib Model Pipeline Artifacts   |   |  - Recursive Auto-regressive Loop  |
+--------------------------------------+   +------------------------------------+
```

---

## 2. Data Preprocessing & Validation Pipeline

### 2.1 Raw Dataset Profile
- **File:** `data/raw_dataset.csv` / `data/cleaned_dataset.csv`
- **Volume:** 73,100 transactions covering 2 full calendar years (`2022-01-01` to `2024-01-01`).
- **Granularity:** Daily transactional records for 5 distinct stores (`S001` - `S005`) across 20 distinct product SKUs (`P0001` - `P0020`), yielding $5 \times 20 = 100$ continuous time-series.
- **Attributes:**
  - `Date`: ISO timestamp (`YYYY-MM-DD`).
  - `Store ID`: Categorical store branch code.
  - `Product ID`: Categorical product SKU code.
  - `Category`: High-level merchandise category (Clothing, Electronics, Groceries, Home & Kitchen, Sports).
  - `Price`: Unit retail selling price.
  - `Discount`: Applied promotional discount fraction.
  - `Units Sold`: Primary forecasting target ($y$).
  - `Inventory Level`: Stock available at store on closing of date.

### 2.2 Data Cleaning & Integrity Safeguards
1. **Deduplication:** Verifies uniqueness of `(Store ID, Product ID, Date)` tuples.
2. **Missing Value Imputation:** Forward fills missing continuous inventory records; drops unrecoverable corrupt rows.
3. **Chronological Sorting:** Enforces strict ascending sequence by date within each series group to preserve temporal ordering.
4. **Physical Boundary Constraints:** Asserts that units sold $\ge 0$ and recorded inventory $\ge 0$.

---

## 3. Feature Engineering

To capture retail seasonality, day-of-week demand patterns, and short-term trends, the raw dataset is expanded into supervised regression features:

| Feature Name | Type | Mathematical / Computational Definition | Retail Purpose |
|---|---|---|---|
| `day` | Integer | Day of month ($1 \dots 31$) | Captures monthly pay-cycle surges |
| `day_of_week` | Integer | Day index ($0 = \text{Monday} \dots 6 = \text{Sunday}$) | Captures weekly sales patterns |
| `month` | Integer | Month of year ($1 \dots 12$) | Captures annual retail seasonality |
| `is_weekend` | Binary | $1 \text{ if } \text{day\_of\_week} \ge 5 \text{ else } 0$ | Accounts for Saturday/Sunday shopping peaks |
| `previous_day_sales` | Continuous | $\text{Sales}_{t-1}$ (1-day lag) | Captures immediate day-to-day momentum |
| `rolling_7_day_average` | Continuous | $\frac{1}{7}\sum_{i=1}^7 \text{Sales}_{t-i}$ | Smoothes day-to-day noise to capture underlying weekly trend |
| `Price` | Continuous | Unit selling price in INR | Price elasticity factor |
| `Discount` | Continuous | Discount percentage ($0.0 \dots 0.5$) | Promotional sales uplift factor |
| `Store ID` | Categorical | One-hot encoded branch | Branch-level baseline variance |
| `Product ID` | Categorical | One-hot encoded SKU | Product-level baseline volume |

### Zero Data Leakage Guarantee
During both model training and live recursive forecasting, lag features are computed **strictly from prior time points ($t-1, t-2, \dots, t-7$)**. Future ground-truth sales are never visible to the feature extractor.

---

## 4. Machine Learning Models & Empirical Evaluation

### 4.1 Model Specifications
Two contrasting regression architectures are trained using Scikit-learn pipelines incorporating one-hot encoding and standard scaling:
1. **Linear Regression Pipeline (`linear_regression_pipeline.joblib`)**:
   - Closed-form ordinary least squares (OLS) with preprocessed categorical and continuous features.
   - Fast, highly interpretable, robust against overfitting.
2. **Random Forest Regressor (`random_forest_pipeline.joblib`)**:
   - Ensemble of 100 decision trees (`n_estimators=100`, `max_depth=12`, `random_state=42`).
   - Captures non-linear feature interactions.

### 4.2 Empirical Evaluation on Held-Out Test Set
The dataset is split chronologically:
- **Training Set:** 80% (58,400 rows, `2022-01-01` to `2023-08-08`).
- **Testing Set:** 20% (14,700 rows, `2023-08-09` to `2024-01-01`).

Both models are evaluated on the exact same 14,700 held-out test rows:

$$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$

$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$

$$\text{MAPE} = \frac{100\%}{N_{\text{active}}} \sum_{i \in \text{active}} \left|\frac{y_i - \hat{y}_i}{y_i}\right| \quad (\text{where } y_i > 0)$$

#### Empirical Results Table:
| Model Candidate | MAE (Units) | RMSE (Units) | MAPE (%) | Evaluation Outcome |
|---|---|---|---|---|
| **Linear Regression** | **88.80** | **108.24** | **342.94%** | **Selected Winner (Best Generalization)** |
| **Random Forest** | 90.76 | 109.88 | 358.93% | Runner-up (Marginally higher variance) |

**Conclusion:** Linear Regression demonstrates lower absolute error, lower root-mean-squared error, and superior generalization on unseen chronological test records. It is preselected as SMARTSTOCK's primary forecasting model.

---

## 5. Multi-Step Recursive Demand Forecasting

To project future customer sales for horizons of 7, 14, or 30 days starting on `2024-01-02`:

1. **Initialization:** Retrieve historical actual sales for target series $(s, p)$. Last actual date is $t_0 = \text{2024-01-01}$.
2. **Step $t_1$ (Day 1):**
   - Calendar features derived from `2024-01-02`.
   - `previous_day_sales` $= \text{Sales}(t_0)$.
   - `rolling_7_day_average` $= \frac{1}{7}\sum_{k=0}^6 \text{Sales}(t_{-k})$.
   - Predict $\hat{y}_1 = \max(0, \text{round}(\text{Model.predict}(X_1), 1))$.
   - Append $\hat{y}_1$ to historical buffer.
3. **Steps $t_2 \dots t_H$ (Days 2 to $H$):**
   - Each subsequent day dynamically computes its lag and rolling average using the newly appended model predictions.
   - Enforces physical non-negativity: $\hat{y}_t \ge 0$ units.

---

## 6. Inventory Depletion & Simulation Mathematics

The simulation tracks daily stock balance over the forecast period:

For each day $t \in [1, H]$:
1. **Beginning Inventory:**
   $$I_{\text{beg}, t} = \begin{cases} I_0 & \text{if } t = 1 \\ I_{\text{end}, t-1} & \text{if } t > 1 \end{cases}$$

2. **Replenishment Arrival:**
   $$R_t = \begin{cases} Q_{\text{received}} & \text{if } t = \text{Delivery Day} \\ 0 & \text{otherwise} \end{cases}$$

3. **Available Stock for Day:**
   $$I_{\text{avail}, t} = I_{\text{beg}, t} + R_t$$

4. **Fulfilled Demand & Unmet Demand:**
   $$D_{\text{fulfilled}, t} = \min(I_{\text{avail}, t}, \hat{d}_t)$$
   $$D_{\text{unmet}, t} = \hat{d}_t - D_{\text{fulfilled}, t}$$

5. **Ending Inventory (Non-Negative):**
   $$I_{\text{end}, t} = I_{\text{avail}, t} - D_{\text{fulfilled}, t} \ge 0$$

6. **Service Level (Fill Rate %):**
   $$\text{Service Level} = \left(\frac{\sum_{t=1}^H D_{\text{fulfilled}, t}}{\sum_{t=1}^H \hat{d}_t}\right) \times 100\%$$

---

## 7. Smart Inventory Recommendation Engine

### 7.1 Mathematical Formulas
Across planning horizon $H$ (default 7 days):

1. **Cumulative Forecasted Demand:**
   $$\hat{D}_{\text{horizon}} = \sum_{t=1}^H \hat{d}_t$$

2. **Average Daily Demand Velocity:**
   $$\bar{d} = \frac{\hat{D}_{\text{horizon}}}{H}$$

3. **Lead Time Demand ($D_L$):**
   $$D_L = \bar{d} \times L \quad (\text{Default } L = 2 \text{ days})$$

4. **Safety Stock ($SS$):**
   $$SS = \bar{d} \times S_{\text{buf}} \quad (\text{Default } S_{\text{buf}} = 1 \text{ day})$$

5. **Reorder Point ($\text{ROP}$):**
   $$\text{ROP} = D_L + SS = \bar{d} \times (L + S_{\text{buf}})$$

6. **Target Stock Level ($S_{\text{target}}$):**
   $$S_{\text{target}} = \hat{D}_{\text{horizon}} + SS$$

7. **Suggested Reorder Quantity ($Q_{\text{reorder}}$):**
   $$Q_{\text{reorder}} = \begin{cases} \max(0, \text{round}(S_{\text{target}} - S_{\text{curr}})) & \text{if } S_{\text{curr}} \le \text{ROP} \\ 0 & \text{if } S_{\text{curr}} > \text{ROP} \end{cases}$$

8. **Stock Runway (Days of Supply):**
   $$\text{Runway} = \begin{cases} \text{round}\left(\frac{S_{\text{curr}}}{\bar{d}}, 1\right) & \text{if } \bar{d} > 0 \\ \infty & \text{if } \bar{d} = 0 \end{cases}$$

### 7.2 Classification Logic
- **Restock Soon:** $S_{\text{curr}} \le \text{ROP}$
- **Stock Available:** $\text{ROP} < S_{\text{curr}} \le 1.5 \times S_{\text{target}}$
- **Excess Stock:** $S_{\text{curr}} > 1.5 \times S_{\text{target}}$
- **Insufficient Data:** Time-series transactions $< 7$ days

---

## 8. REST API Reference

| Method | Endpoint | Description | Request Payload | Response Schema |
|---|---|---|---|---|
| `GET` | `/api/health` | Service & DB health check | None | `HealthResponse` |
| `POST` | `/api/dataset/upload` | Upload new retail CSV | `multipart/form-data` | `UploadResponse` |
| `GET` | `/api/dataset/summary` | Dataset metadata & shape | None | `DatasetSummary` |
| `POST` | `/api/dataset/clean` | Trigger preprocessing | None | `CleanResponse` |
| `GET` | `/api/analysis/summary` | Sales analytics summary | None | `SalesSummary` |
| `POST` | `/api/model/train` | Train regression pipelines | None | `TrainingStatus` |
| `GET` | `/api/model/evaluation` | Model metrics & winner | Query `force=bool` | `ModelEvaluationResponse` |
| `POST` | `/api/forecast/generate` | Generate future forecast | `ForecastRequest` | `ForecastResponse` |
| `POST` | `/api/inventory/simulate` | Run stock simulation | `InventorySimulationRequest` | `InventorySimulationResponse` |
| `GET` | `/api/recommendation/all` | Filterable recommendations | Query filters | `RecommendationResponse` |
| `GET` | `/api/recommendation/dashboard-summary` | Executive KPIs & insights | None | `DashboardSummaryResponse` |

