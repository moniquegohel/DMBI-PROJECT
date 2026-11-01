# SMARTSTOCK — MILESTONE 4 APPROVAL DOCUMENT

> **Milestone:** Milestone 4 — Historical Sales Analysis  
> **Status:** APPROVED BY USER  
> **Date:** October 2026  

---

## 1. User Approval Statement

The user reviewed the **Milestone 4 Implementation & Verification Report** for SmartStock and approved it with the statement:

> *"veryyy nice. now please proceed with milestone 5."*

### Key Confirmations

1. All 5 historical sales analysis API endpoints (`/api/analysis/summary`, `/api/analysis/monthly`, `/api/analysis/products`, `/api/analysis/categories`, `/api/analysis/stores`) are implemented, tested, and returning correct data.
2. All aggregated totals reconcile exactly with the global dataset total (9,975,582 units across 73,100 records).
3. The average is correctly labelled as **per record** — not as a daily average.
4. The Sales Analysis frontend page displays live data in four chart/table sections with loading states, per-section error handling, and a no-dataset guidance state.
5. All 16 backend pytest tests pass (9 Milestone 3 + 7 Milestone 4), with no regressions.
6. The frontend production build succeeds with no errors (`vite build`, exit code 0).
7. No Milestone 5+ features were prematurely introduced.

---

## 2. Summary of Delivered Milestone 4 Features

### Backend

| Deliverable | Status |
|---|---|
| `backend/app/schemas/analysis.py` — Pydantic response models | ✅ Complete |
| `backend/app/services/analysis.py` — Pandas calculation engine with caching | ✅ Complete |
| `backend/app/routes/analysis.py` — 5 FastAPI GET endpoints | ✅ Complete |
| `backend/app/main.py` — analysis router registered | ✅ Complete |
| `backend/tests/test_milestone4.py` — 7 automated tests | ✅ Complete |

### Frontend

| Deliverable | Status |
|---|---|
| `frontend/src/services/api.js` — `getCategorySales`, `getStoreSales` added | ✅ Complete |
| `frontend/src/pages/SalesAnalysis.jsx` — full implementation | ✅ Complete |
| `frontend/src/App.jsx` — `setActiveTab` prop passed to SalesAnalysis | ✅ Complete |

### Test Results

```text
16 passed, 1 warning in 10.54s
(9 Milestone 3 tests + 7 Milestone 4 tests — all green)
```

### Build Result

```text
vite v8.3.0 — ✓ 2516 modules transformed — built in 7.87s
```

---

## 3. Directives Granted for Milestone 5

Upon approving Milestone 4, the user granted authorization to proceed to **Milestone 5 — Feature Engineering** under the following constraints:

### A. Technology Constraints

- Continue using the existing Python `.venv` with Pandas, NumPy, Scikit-learn.
- Do **not** introduce new Python ML libraries at this stage.
- Keep all code simple, readable, and well-commented for B.Tech academic presentation.

### B. Feature Engineering Requirements (from `SMARTSTOCK_REQUIREMENTS.md`, Section 12)

Create the following features from the cleaned dataset:

| Feature | Description |
|---|---|
| `day` | Day number within the month |
| `day_of_week` | Day of the week (0 = Monday … 6 = Sunday) |
| `month` | Month number (1–12) |
| `is_weekend` | 1 if Saturday or Sunday, 0 otherwise |
| `previous_day_sales` | Units sold on the previous day for the same product |
| `rolling_7_day_average` | Average units sold over the 7 days preceding the current record |

Optional features (use only if supported by the dataset):
- `promotion` / `holiday` → mapped from `Holiday/Promotion` column if available.
- `price` → from `Price` column if available.

Target variable: `units_sold` (mapped from `Units Sold`).

### C. Critical ML Rule — No Data Leakage

The feature engineering must **not** use future actual sales values as inputs:
- `previous_day_sales` must use a chronologically correct shift.
- `rolling_7_day_average` must use only past values (exclusive of the current day).
- Rows where lag/rolling features cannot be computed (first rows per product) should be handled by dropping them **after** splitting, or by setting NaN and documenting the decision.

### D. Per-Product Feature Engineering

Because the dataset contains 5 stores × 20 products = 100 distinct store-product combinations, lag features must be computed **within each product group** (and ideally per store-product group) to avoid contaminating sales from different products.

### E. Explicit Restrictions for Milestone 5

- Do **not** train any ML model yet.
- Do **not** implement demand forecasting.
- Do **not** modify or extend the Milestone 3 data cleaning pipeline.
- Do **not** expose the feature-engineered dataset to the frontend as a downloadable file (unless trivial to add without new endpoints).
- Do **not** change any Milestone 1–4 code unless a minimal fix is required and the reason is documented.
- Wait for explicit user review and approval after Milestone 5 before starting Milestone 6 (Model Training).

### F. Required Milestone 5 Deliverables

1. `backend/app/services/feature_engineering.py` — service module that loads the cleaned dataset, engineers all required features, and returns an ML-ready DataFrame or saves it to `backend/data/ml_dataset.csv`.
2. `backend/app/routes/model.py` (stub or early version) — at minimum a `GET /api/model/features` endpoint that returns the list of features, their descriptions, and a sample row for display on the Model Training page.
3. Updated `frontend/src/pages/ModelTraining.jsx` — replace the placeholder with a page showing the feature list, target variable, and a "Train Models" button (button may be inactive until Milestone 6).
4. `backend/tests/test_milestone5.py` — automated tests verifying that:
   - All required features are present in the output.
   - No future data leakage exists in lag/rolling features.
   - The ML dataset has the expected column count.
   - NaN handling is correct and documented.
5. A verified clean frontend production build.

---

## 4. Official Status

```text
Milestone 1: COMPLETE & APPROVED
Milestone 2: COMPLETE & APPROVED
Milestone 3: COMPLETE & APPROVED
Milestone 4: COMPLETE & APPROVED
Milestone 5: AUTHORIZED TO BEGIN
```

