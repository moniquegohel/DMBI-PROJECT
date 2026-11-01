# SMARTSTOCK — MILESTONE 1: PROJECT ARCHITECTURE VERIFICATION REPORT

> **Milestone:** Milestone 1 — Project Architecture  
> **Status:** Verified & Completed  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 1 established the core project foundation for SmartStock, separating the **React Frontend** and **FastAPI Backend** architectures. The goal of this milestone was to establish the initial project structure, set up build and environment configurations, create basic API routing and navigation components, and verify end-to-end communication without implementing business logic prematurely.

---

## 2. File Inventory & Technical Description

### Backend Architecture (`backend/`)

#### 1. `backend/app/main.py`
* **Purpose:** FastAPI entry point and router aggregator.
* **Role in SmartStock:** Manages API lifecycle, CORS policies, and exposes root and health endpoints.
* **Current Code:** Configures CORS middleware allowing local origins (`http://localhost:5173`) and provides `GET /` and `GET /api/health` endpoints.
* **Classification:** Foundation layer.

#### 2. `backend/app/__init__.py`
* **Purpose:** Python package initialization.
* **Role in SmartStock:** Enables modular imports across `app` sub-packages (`routes`, `services`, `database`).
* **Current Code:** Package initialization.
* **Classification:** Foundation layer.

#### 3. `backend/requirements.txt`
* **Purpose:** Python dependency manifest.
* **Role in SmartStock:** Guarantees uniform environment setup across all developer machines.
* **Current Dependencies:** `fastapi`, `uvicorn`, `pandas`, `numpy`, `scikit-learn`, `sqlalchemy`, `joblib`, `python-multipart`, `pydantic`.
* **Classification:** Configuration.

---

### Frontend Architecture (`frontend/`)

#### 4. `frontend/vite.config.js`
* **Purpose:** Vite dev server and build configuration.
* **Role in SmartStock:** Integrates React plugin, Tailwind CSS v4 compiler, and configures dev server API proxy (`/api` -> `http://127.0.0.1:8000`).
* **Classification:** Configuration.

#### 5. `frontend/src/index.css`
* **Purpose:** Global stylesheet.
* **Role in SmartStock:** Imports Tailwind CSS v4 directives and establishes base dark theme styling (`bg-slate-900 text-slate-100 font-sans`).
* **Classification:** Styling Baseline.

#### 6. `frontend/src/services/api.js`
* **Purpose:** Axios API client service layer.
* **Role in SmartStock:** Decouples API communication from React UI components.
* **Current Code:** Configures Axios instance (`baseURL: '/api'`) and exports wrapper functions (`fetchHealth`, `uploadDataset`, `getDatasetSummary`, `getSalesSummary`, `getMonthlySales`, `getProductSales`, `getProducts`, `trainModels`, `getModelResults`, `generateForecast`, `analyzeInventory`).
* **Classification:** API Client Layer.

#### 7. `frontend/src/App.jsx`
* **Purpose:** Main React application router and layout container.
* **Role in SmartStock:** Controls state-driven tab navigation and pings backend health status on mount.
* **Classification:** Application Container.

#### 8. `frontend/src/components/Sidebar.jsx` & `Navbar.jsx`
* **Purpose:** Global navigation header and sidebar.
* **Role in SmartStock:** Provides single-click navigation across all 6 core modules and displays real-time backend API status badge (`CONNECTED` / `ERROR`).
* **Classification:** UI Layout Components.

#### 9. `frontend/src/components/StatCard.jsx`
* **Purpose:** Reusable business intelligence metric card.
* **Role in SmartStock:** Displays KPI numbers, titles, icons, and trends consistently across pages.
* **Classification:** Reusable Component.

#### 10. `frontend/src/pages/` Components
* **Pages Created:** `Dashboard.jsx`, `Dataset.jsx`, `SalesAnalysis.jsx`, `ModelTraining.jsx`, `DemandForecast.jsx`, `Inventory.jsx`.
* **Current Code:** Renders UI layout placeholders and prerequisite instructions explaining dataset/model requirements.
* **Classification:** UI Placeholders.

---

## 3. Architecture Verification Diagram

```text
               +----------------------------------+
               |          REACT FRONTEND          |
               |        (Port 5173 / Vite)        |
               +----------------------------------+
               | - App.jsx                        |
               | - Sidebar.jsx & Navbar.jsx        |
               | - Dashboard, Dataset, Sales,     |
               |   Model, Forecast, Inventory Pages|
               +----------------------------------+
                                │
                                │ REST API (JSON via Axios)
                                ▼
               +----------------------------------+
               |           API SERVICE            |
               |     (src/services/api.js)        |
               +----------------------------------+
                                │
                                │ HTTP Proxy (/api -> :8000)
                                ▼
               +----------------------------------+
               |         FASTAPI BACKEND          |
               |        (Port 8000 / Python)      |
               +----------------------------------+
               | - main.py (App & Health Endpoints)|
               +----------------------------------+
```

---

## 4. Empirical Verification Results

1. **Backend Server Startup Test:**
   * Executed `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
   * **Endpoint Response (`GET /api/health`):**
     ```json
     {
       "status": "healthy",
       "database": "disconnected",
       "ml_models": "not_loaded"
     }
     ```
2. **Frontend Build Verification:**
   * Executed `npm run build`.
   * **Result:** Successfully compiled 1,943 modules in **2.00s** with **0 syntax or build errors**.
3. **API Ping & Tab Navigation Test:**
   * App initialized backend health ping, setting status badge to `BACKEND API: CONNECTED`.
   * Tab switching between all 6 pages functioned without page refreshes or console errors.

---

## 5. Verification Checklist

- [x] Project workspace separated into `backend/` and `frontend/`.
- [x] Python virtual environment dependencies defined and verified.
- [x] FastAPI application running on port 8000 with CORS middleware enabled.
- [x] React application running on Vite with Tailwind CSS v4 styling.
- [x] Vite development proxy forwarding `/api` calls to port 8000.
- [x] Centralized Axios service layer established.
- [x] Sidebar navigation switching seamlessly between all 6 pages.
- [x] Real-time backend API connection status badge displayed in top header.
- [x] **Zero premature logic implemented** (No DB tables, no ML training, no forecasting math).

---

## 6. Final Status

* **Status:** **PASSED & APPROVED**
* **Next Step:** Proceed to Milestone 2 (Database Setup).
