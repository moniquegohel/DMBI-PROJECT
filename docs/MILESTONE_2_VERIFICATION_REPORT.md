# SMARTSTOCK — MILESTONE 2: DATABASE SETUP & VERIFICATION REPORT

> **Milestone:** Milestone 2 — Database Setup  
> **Status:** Verified & Completed  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 2 focused on setting up a lightweight, beginner-friendly **SQLite database** using **SQLAlchemy ORM** inside the FastAPI backend (`backend/app/database/`). 

The primary objectives were:
1. Design a minimal, flexible schema to support retail sales, products, simulated inventory, demand forecasts, and model evaluation metrics.
2. Initialize database creation automatically on backend startup.
3. Update `/api/health` to perform a real database connection test and report `"database": "connected"`.
4. Verify database creation and table schemas without populating fake data or introducing dataset processing prematurely.

---

## 2. Database Schema Specification

### Entity Details

| Table Name | Purpose | Fields & Types | Primary Key | Foreign Keys |
| :--- | :--- | :--- | :--- | :--- |
| **`products`** | Stores master product definitions | `id` (Integer)<br>`product_code` (String, Unique, Index)<br>`product_name` (String)<br>`category` (String, Nullable)<br>`price` (Float, Default 0.0)<br>`created_at` (DateTime) | `id` | None |
| **`sales`** | Stores historical daily retail sales transaction records | `id` (Integer)<br>`product_id` (Integer, Index)<br>`sale_date` (Date, Index)<br>`quantity_sold` (Float)<br>`promotion` (Integer, Default 0)<br>`created_at` (DateTime) | `id` | `product_id` → `products.id` |
| **`inventory`** | Stores user-simulated inventory stock levels & parameters | `id` (Integer)<br>`product_id` (Integer, Unique, Index)<br>`current_stock` (Float, Default 0.0)<br>`safety_stock` (Float, Default 0.0)<br>`supplier_lead_time` (Integer, Default 1)<br>`updated_at` (DateTime) | `id` | `product_id` → `products.id` |
| **`forecasts`** | Stores generated 7-day demand predictions | `id` (Integer)<br>`product_id` (Integer, Index)<br>`forecast_date` (Date)<br>`predicted_demand` (Float)<br>`model_name` (String)<br>`created_at` (DateTime) | `id` | `product_id` → `products.id` |
| **`model_results`** | Stores machine learning evaluation benchmark metrics | `id` (Integer)<br>`model_name` (String)<br>`mae` (Float)<br>`rmse` (Float)<br>`mape` (Float)<br>`training_date` (DateTime) | `id` | None |

---

## 3. Entity Relationship Diagram

```text
                     +-------------------+
                     |     products      |
                     +-------------------+
                     | PK: id            |
                     |     product_code  |
                     |     product_name  |
                     +-------------------+
                               │
       ┌───────────────────────┼───────────────────────┐
       │ 1-to-Many             │ 1-to-1                │ 1-to-Many
       ▼                       ▼                       ▼
+-------------------+   +-------------------+   +-------------------+
|       sales       |   |     inventory     |   |     forecasts     |
+-------------------+   +-------------------+   +-------------------+
| PK: id            |   | PK: id            |   | PK: id            |
| FK: product_id    |   | FK: product_id    |   | FK: product_id    |
|     sale_date     |   |     current_stock |   |     forecast_date |
|     quantity_sold |   |     safety_stock  |   |   predicted_demand|
+-------------------+   +-------------------+   +-------------------+

                                                +-------------------+
                                                |   model_results   |
                                                +-------------------+
                                                | PK: id            |
                                                |     model_name    |
                                                |     mae, rmse, mape|
                                                +-------------------+
```

---

## 4. Code Implementation Details

### 1. `backend/app/database/database.py` (NEW)
* Configures SQLite database file path (`backend/data/smartstock.db`).
* Instantiates SQLAlchemy `engine` with `check_same_thread=False` for FastAPI compatibility.
* Defines `SessionLocal` session factory and `Base` declarative base class.
* Provides `get_db()` dependency helper and `check_db_connection()` live ping query execution (`SELECT 1`).

### 2. `backend/app/database/models.py` (NEW)
* Defines SQLAlchemy ORM classes: `Product`, `Sale`, `Inventory`, `Forecast`, and `ModelResult`.
* Maps column types, relationships (`relationship(...)`), cascade deletions, and index parameters.

### 3. `backend/app/main.py` (MODIFIED)
* Invokes `Base.metadata.create_all(bind=engine)` on application startup to create SQLite tables automatically if they do not exist.
* Updates `/api/health` endpoint to test database connectivity live using `check_db_connection()`.

---

## 5. Empirical Verification Results

1. **SQLite Database & Table Inspection Test:**
   * Inspected table names created inside `backend/data/smartstock.db`.
   * **Result:** All 5 database tables were successfully created:
     ```python
     ['forecasts', 'inventory', 'model_results', 'products', 'sales']
     ```
2. **Live Backend API Connection Test:**
   * Started Uvicorn server on port 8000 and queried HTTP `GET /api/health`.
   * **Result:** Endpoint returned live JSON output confirming active database connection:
     ```json
     {
       "status": "healthy",
       "database": "connected",
       "ml_models": "not_loaded"
     }
     ```
3. **Frontend Build Verification:**
   * Executed `npm run build`.
   * **Result:** Compiled cleanly in **2.21s** with **0 build errors**. UI status badge renders `BACKEND API: CONNECTED`.

---

## 6. Verification Checklist

- [x] Local SQLite database initialized (`smartstock.db`).
- [x] SQLAlchemy ORM models created (`Product`, `Sale`, `Inventory`, `Forecast`, `ModelResult`).
- [x] Relationships and foreign keys properly configured.
- [x] Database tables created automatically on FastAPI startup.
- [x] `/api/health` endpoint updated to execute a real DB connection ping (`SELECT 1`).
- [x] Live HTTP response verified as `"database": "connected"`.
- [x] Frontend builds cleanly with zero errors.
- [x] **Zero premature logic implemented** (No CSV parsing, no fake sales data, no ML training).

---

## 7. Final Status

* **Status:** **PASSED & READY FOR REVIEW**
* **Next Step:** Await user approval before starting Milestone 3 (Dataset Upload & Cleaning).
