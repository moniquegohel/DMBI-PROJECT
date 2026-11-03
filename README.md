# SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation

> **B.Tech 3rd-Year Academic Project — Data Mining & Business Intelligence (DMBI)**  
> **Repository:** [https://github.com/moniquegohel/DMBI-PROJECT.git](https://github.com/moniquegohel/DMBI-PROJECT.git)  
> **Status:** Completed, Fully Tested & Approved (Milestones 1–12)  

---

## 1. Project Overview & Problem Statement

Modern multi-branch retail enterprises face a persistent **inventory balance problem**:
- **Understocking (Stockouts):** When popular items run out of stock, sales are lost, and customer loyalty diminishes.
- **Overstocking (Excess Stock):** When excess inventory accumulates, working capital is needlessly locked up in idle goods, increasing storage costs and risk of obsolescence.

**SMARTSTOCK** is an end-to-end intelligent decision-support system that combines machine learning demand forecasting with prescriptive inventory management. It processes historical transaction records, predicts daily customer demand velocity across store branches, and calculates dynamic Reorder Points (ROP), Safety Stock, and Suggested Reorder Quantities to guide purchasing decisions.

---

## 2. Key Objectives & Deliverables

1. **Data Preprocessing & Feature Engineering:** Clean 73,100 transactions and engineer temporal features, lag sales, and 7-day rolling averages without future data leakage.
2. **Empirical Model Comparison:** Train and evaluate Linear Regression and Random Forest models across 14,700 held-out test records to select the best forecasting engine.
3. **Multi-Step Recursive Forecasting:** Generate daily sales forecasts for 7, 14, and 30-day horizons with physical non-negativity constraints ($\ge 0$ units).
4. **Interactive Inventory Simulation:** Simulate multi-day stock depletion, delivery arrivals, stockout detection, and fulfillment service levels (Fill Rate %).
5. **Smart Restocking Recommendations:** Classify catalogue SKUs into *Restock Soon*, *Stock Available*, and *Excess Stock*, recommending exact, non-negative reorder quantities.
6. **Executive Business Dashboard:** Provide retail executives with 6 KPI summary cards, automated narrative business insights, and 4 interactive visual charts.

---

## 3. Technology Stack

- **Frontend:** React 19, Vite v8.3.5, Tailwind CSS, Recharts (SVG data visualizations), Lucide React (iconography), Axios.
- **Backend API:** FastAPI (Python 3.14), Uvicorn ASGI Server, Pydantic v2 schemas.
- **Machine Learning & Analytics:** Scikit-learn, Pandas, NumPy, Joblib.
- **Database & Storage:** SQLite (`smartstock.db`) + CSV persistence (`cleaned_dataset.csv`).
- **Test Automation:** Python standard library `unittest` (50 automated unit & integration tests).

---

## 4. System Architecture

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

## 5. Project Folder Structure

```text
DMBI-PROJECT/
├── README.md                           <- Master Project README (this file)
├── .gitignore                          <- Git ignore rules (venv, node_modules, temp files)
├── backend/
│   ├── app/
│   │   ├── main.py                     <- FastAPI main application & CORS setup
│   │   ├── database/                   <- SQLite engine, models, and session manager
│   │   ├── routes/
│   │   │   ├── dataset.py              <- Upload, column mapping, and cleaning endpoints
│   │   │   ├── analysis.py             <- Sales aggregation & summary endpoints
│   │   │   ├── model.py                <- Feature engineering & training endpoints
│   │   │   ├── forecast.py             <- Demand forecasting endpoints
│   │   │   ├── inventory.py            <- Inventory simulation endpoints
│   │   │   └── recommendation.py       <- Inventory recommendations & dashboard APIs
│   │   ├── schemas/                    <- Pydantic validation schemas
│   │   └── services/                   <- Core business logic & ML pipelines
│   │       ├── data_cleaning.py        <- Data preprocessing and validation
│   │       ├── feature_engineering.py  <- Lag and rolling feature generators
│   │       ├── model_training.py       <- Scikit-learn pipeline builders
│   │       ├── model_evaluation.py     <- Empirical evaluation & comparison service
│   │       ├── demand_forecasting.py   <- Recursive multi-step forecasting engine
│   │       ├── inventory_simulation.py <- Daily stock balance & fill rate simulator
│   │       └── inventory_recommendation.py <- ROP, safety stock & dashboard service
│   ├── models/                         <- Trained model artifacts (.joblib, metadata.json)
│   ├── tests/                          <- Automated test suites (50 unit & integration tests)
│   │   ├── test_milestone7.py          <- 10 tests (Model Evaluation)
│   │   ├── test_milestone8.py          <- 10 tests (Demand Forecasting)
│   │   ├── test_milestone9.py          <- 10 tests (Inventory Simulation)
│   │   ├── test_milestone10.py         <- 10 tests (Smart Inventory Recommendations)
│   │   └── test_milestone11.py         <- 10 tests (Business Insights Dashboard)
│   └── requirements.txt                <- Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     <- Main React application & tab routing
│   │   ├── components/                 <- Reusable UI components (Navbar, Sidebar, StatCard)
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx           <- Executive Retail Command Center & Insights
│   │   │   ├── Dataset.jsx             <- Dataset upload & column mapping interface
│   │   │   ├── SalesAnalysis.jsx       <- Historical sales trends & category breakdown
│   │   │   ├── ModelTraining.jsx       <- Model training & empirical evaluation page
│   │   │   ├── DemandForecast.jsx      <- Multi-step daily future sales forecasting
│   │   │   ├── Inventory.jsx           <- Multi-day inventory depletion simulator
│   │   │   └── Recommendations.jsx     <- Restock action plan & reorder quantity ledger
│   │   └── services/api.js             <- Axios API client methods
│   ├── package.json                    <- Frontend dependencies & scripts
│   └── vite.config.js                  <- Vite build and proxy configuration
├── data/
│   ├── raw_dataset.csv                 <- Raw historical transactional dataset
│   └── cleaned_dataset.csv             <- Preprocessed 73,100-record dataset
└── docs/                               <- Comprehensive documentation suite
    ├── USER_GUIDE.md                   <- Beginner-friendly walkthrough
    ├── TECHNICAL_DOCUMENTATION.md      <- Formulas, equations, and API reference
    ├── PROJECT_LIMITATIONS.md          <- Dataset, modeling & architectural boundaries
    ├── VIVA_PREPARATION.md             <- Q&A guide for B.Tech academic viva
    ├── FINAL_TEST_REPORT.md            <- 50-test verification & quality audit
    ├── MILESTONE_10_APPROVAL.md        <- Formal sign-off for Milestone 10
    └── MILESTONE_11_APPROVAL.md        <- Formal sign-off for Milestone 11
```

---

## 6. Dataset Information

- **Records:** 73,100 rows
- **Time Span:** 2 full years (`2022-01-01` to `2024-01-01`)
- **Retail Branches:** 5 stores (`S001`, `S002`, `S003`, `S004`, `S005`)
- **Product SKUs:** 20 products (`P0001` through `P0020`)
- **Categories:** Clothing, Electronics, Groceries, Home & Kitchen, Sports
- **Total Continuous Series:** $5 \times 20 = 100$ series (731 days per series)
- **Key Fields:** Date, Store ID, Product ID, Category, Price, Discount, Units Sold, Inventory Level

---

## 7. Machine Learning Workflow & Empirical Winner

The dataset is partitioned using a strict **chronological time-series split**:
- **Train Set (80%):** 58,400 records (`2022-01-01` to `2023-08-08`)
- **Test Set (20%):** 14,700 records (`2023-08-09` to `2024-01-01`)

### Empirical Evaluation on 14,700 Held-Out Records:
| Model Candidate | Mean Absolute Error (MAE) | Root Mean Squared Error (RMSE) | MAPE (%) | Empirical Result |
|---|---|---|---|---|
| **Linear Regression** | **88.80 units** | **108.24 units** | **342.94%** | **Selected Winner** |
| **Random Forest** | 90.76 units | 109.88 units | 358.93% | Runner-up |

*Justification:* Linear Regression demonstrates lower absolute error, lower root-mean-squared error, and superior generalization on unseen chronological test records without overfitting.

---

## 8. Installation & Setup Instructions (Windows)

### Prerequisites
- Python 3.10 to 3.14 installed.
- Node.js (v18 or higher) and npm installed.
- Git installed.

### Step 1: Clone Repository
```powershell
git clone https://github.com/moniquegohel/DMBI-PROJECT.git
cd DMBI-PROJECT
```

### Step 2: Set Up Backend Virtual Environment
```powershell
# Create virtual environment inside backend folder
python -m venv backend\.venv

# Activate virtual environment
backend\.venv\Scripts\Activate.ps1

# Install required Python dependencies
pip install -r backend\requirements.txt
```

### Step 3: Set Up Frontend
```powershell
cd frontend
npm install
cd ..
```

---

## 9. How to Run the Application

### Option A: Run Backend API Server
In Terminal 1 (PowerShell):
```powershell
backend\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### Option B: Run Frontend Development Server
In Terminal 2 (PowerShell):
```powershell
cd frontend
npm run dev
```
- Open your browser at: `http://localhost:5173`

---

## 10. Running the Automated Test Suite

SMARTSTOCK contains **50 automated unit and integration tests** executing with Python's built-in `unittest` runner:

```powershell
# Execute all 50 tests across Milestones 7 through 11
$env:PYTHONPATH="backend"; backend\.venv\Scripts\python -m unittest `
    backend.tests.test_milestone7 `
    backend.tests.test_milestone8 `
    backend.tests.test_milestone9 `
    backend.tests.test_milestone10 `
    backend.tests.test_milestone11 -v
```

### Build Production Frontend:
```cmd
cmd.exe /c "cd frontend && npm run build"
```

---

## 11. Academic Viva & Submission Documents

For detailed study and examiner presentation, refer to the documentation in [`docs/`](./docs/):
- 📘 [User Guide](./docs/USER_GUIDE.md) — Step-by-step walkthrough of all features.
- 📐 [Technical Documentation](./docs/TECHNICAL_DOCUMENTATION.md) — Formulas, equations, and API schemas.
- ⚠️ [Project Limitations](./docs/PROJECT_LIMITATIONS.md) — Known assumptions and future scope.
- 🎓 [Viva Preparation Guide](./docs/VIVA_PREPARATION.md) — 24 examiner questions and detailed answers.
- 📊 [Final Test Report](./docs/FINAL_TEST_REPORT.md) — Full test audit report with 50/50 passed tests.

