# SMARTSTOCK — MILESTONE 3: DATASET UPLOAD & CLEANING VERIFICATION REPORT

> **Milestone:** Milestone 3 — Dataset Upload and Cleaning  
> **Status:** Verified & Completed  
> **Target Audience:** B.Tech 3rd-Year Academic Evaluation  

---

## 1. Overview & Objectives

Milestone 3 implemented the complete dataset ingestion, inspection, semantic column mapping, and transparent data-quality cleaning pipeline for SmartStock.

The primary objectives were:
1. Allow users to select, drag-and-drop, and upload a `.csv` retail sales file.
2. Validate file format and handle edge cases (empty files, unreadable formats, invalid extensions) with user-friendly error messages.
3. Automatically inspect the uploaded dataset and compute dynamic summary metrics without hardcoding.
4. Provide a semantic column mapping interface for standard retail forecasting roles.
5. Implement transparent data quality validation checks with a clear distinction between informational findings, warnings, and errors.
6. Specifically address the dataset characteristics of `retail_store_inventory.csv`:
   - 73,100 records and 15 columns.
   - 731 unique dates (2022-01-01 to 2024-01-01).
   - 5 unique stores and 20 unique products.
   - 0 missing values and 0 duplicate rows.
   - 673 negative values in `Demand Forecast` flagged as a prominent warning, preserved in the dataset without silent deletion, and excluded from initial predictive feature modeling.
7. Implement an explicit data cleaning action that preserves the raw dataset and generates a separate cleaned dataset with logged transformations.
8. Enable previewing both raw and cleaned records (first 10 rows) and downloading the cleaned CSV.
9. Persist dataset metadata in the SQLite database without cluttering the database with raw rows.

---

## 2. File Inventory & Technical Implementation

### Backend Modules (`backend/app/`)

#### 1. `backend/app/database/models.py` (Modified)
* Added `DatasetMetadata` SQLAlchemy ORM model to track dataset metadata (`filename`, `file_size_bytes`, `original_rows`, `original_columns`, `cleaned_rows`, `cleaned_columns`, `status`, `created_at`, `updated_at`).

#### 2. `backend/app/schemas/dataset.py` (New)
* Defined Pydantic models:
  - `ColumnInspectionInfo`: Per-column data types, null counts, null percentages, unique counts, sample values, and numeric summary statistics (`min_value`, `max_value`, `mean_value`).
  - `ColumnMappingItem`: Semantic retail role, description, required status, and mapped column name.
  - `ColumnMappingUpdateRequest`: Payload for saving user mapping adjustments.
  - `QualityCheckItem`: Quality check findings with `check_type` (`info`, `warning`, `error`), affected column, affected row count, and action recommendation.
  - `DatasetSummaryResponse`: Comprehensive inspection response object.
  - `CleaningResultResponse`: Cleaning execution report containing before/after counts, list of transformations applied, warnings, and cleaned data preview.

#### 3. `backend/app/services/data_cleaning.py` (New)
* Implemented core data processing engine using Pandas & NumPy:
  - `save_raw_csv_file()`: Securely saves uploaded files to `backend/data/raw_dataset.csv`, sanitizing filenames against path traversal.
  - `detect_suggested_mappings()`: Rule-based heuristic matcher for 12 standard retail roles (`date`, `store_id`, `product_id`, `units_sold`, `inventory_level`, `units_ordered`, `price`, `discount`, `promotion`, `weather`, `category`, `region`).
  - `inspect_dataframe()`: Computes dynamic statistics, checks missing values, exact duplicates, composite key duplicates (`Date` + `Store ID` + `Product ID`), and scans numeric columns for negative values.
  - Special Handling: Flags the 673 negative `Demand Forecast` values as a warning without row deletion.
  - `execute_data_cleaning()`: Standardizes dates to `YYYY-MM-DD`, verifies numeric types, sorts transactions chronologically, preserves domain exceptions, writes cleaned data to `backend/data/cleaned_dataset.csv`, and returns transformation logs.

#### 4. `backend/app/routes/dataset.py` (New)
* Exposed REST endpoints:
  - `POST /api/dataset/upload`: Uploads and inspects CSV.
  - `GET /api/dataset/summary`: Retrieves current inspection summary.
  - `POST /api/dataset/map`: Updates column mappings.
  - `POST /api/dataset/clean`: Runs cleaning pipeline.
  - `GET /api/dataset/download/cleaned`: Serves cleaned CSV for download.
  - `GET /api/dataset/download/raw`: Serves raw CSV for download.
  - `POST /api/dataset/load-sample`: Convenience endpoint for viva demo.

#### 5. `backend/app/main.py` (Modified)
* Mounted `dataset_router` under prefix `/api/dataset`.

---

### Frontend Architecture (`frontend/src/`)

#### 6. `frontend/src/services/api.js` (Modified)
* Added client wrappers: `uploadDataset`, `getDatasetSummary`, `updateColumnMappings`, `cleanDataset`, `loadSampleDataset`, `getCleanedDownloadUrl`, and `getRawDownloadUrl`.

#### 7. `frontend/src/pages/Dataset.jsx` (Modified)
* Replaced placeholder with complete UI:
  - Drag-and-drop file upload dropzone with file picker and size display.
  - Loading spinners and error/success alert banners.
  - Overview stat cards (Total Records, Time Period, Entities Tracked, Quality Score).
  - Data quality findings section with distinct Info, Warning, and Error badges.
  - Column role mapping table with interactive dropdowns and save button.
  - Cleaning action trigger card with execution logs and before/after row counters.
  - Tabbed preview table: Raw Data Preview, Column Statistics & Distribution, and Cleaned Data Preview.
  - Direct download buttons for Cleaned CSV and Raw CSV.

---

### Test Suite (`backend/tests/`)

#### 8. `backend/tests/test_milestone3.py` (New)
* 9 automated tests verifying:
  - Health check endpoint.
  - Invalid file extension rejection (400).
  - Empty CSV rejection (400).
  - Corrupted CSV handling (400).
  - Full upload of `retail_store_inventory.csv` (73,100 rows, 15 columns, 0 missing, 0 duplicate, 673 negative demand forecast warning).
  - Summary endpoint accuracy.
  - Column mapping persistence.
  - Cleaning pipeline execution (73,100 -> 73,100 rows, zero records silently deleted).
  - Cleaned CSV download availability and validity.

---

## 3. Empirical Test Results

### Automated Pytest Execution

```text
tests/test_milestone3.py::test_health_endpoint PASSED                    [ 11%]
tests/test_milestone3.py::test_upload_invalid_extension PASSED           [ 22%]
tests/test_milestone3.py::test_upload_empty_csv PASSED                   [ 33%]
tests/test_milestone3.py::test_upload_corrupted_csv PASSED               [ 44%]
tests/test_milestone3.py::test_upload_retail_store_inventory_csv PASSED  [ 55%]
tests/test_milestone3.py::test_get_dataset_summary PASSED                [ 66%]
tests/test_milestone3.py::test_update_column_mappings PASSED             [ 77%]
tests/test_milestone3.py::test_clean_dataset_execution PASSED            [ 88%]
tests/test_milestone3.py::test_download_cleaned_csv PASSED               [100%]

======================== 9 passed in 6.55s ========================
```

### Frontend Production Build Verification

```text
> frontend@0.0.0 build
> vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 1943 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:  0.29 kB
dist/assets/index-Dow-ixW4.css   38.93 kB │ gzip:  6.61 kB
dist/assets/index-arMSPxtA.js   312.49 kB │ gzip: 98.89 kB

✓ built in 1.53s
```

### Live Server Verification

```json
GET /api/health
{
  "status": "healthy",
  "database": "connected",
  "ml_models": "not_loaded"
}

GET /api/dataset/summary
{
  "has_dataset": true,
  "filename": "retail_store_inventory.csv",
  "row_count": 73100,
  "column_count": 15,
  "status": "ready"
}
```

---

## 4. Verification Checklist & Compliance

- [x] CSV file upload supporting file picker and drag-and-drop.
- [x] File validation rejecting non-CSV, empty, or unparseable files with clear error messages.
- [x] Dynamic calculation of row count (73,100), column count (15), missing values (0), and duplicates (0).
- [x] Date range parsed as 2022-01-01 to 2024-01-01 (731 unique dates).
- [x] 5 stores and 20 products correctly identified.
- [x] Inferred data types, sample values, min, max, and mean calculated per column.
- [x] 673 negative `Demand Forecast` values detected and flagged as a warning without row deletion.
- [x] Semantic column mapping interface supporting 12 standard retail roles.
- [x] Explicit cleaning action executing date standardization, type validation, and chronological sorting.
- [x] Cleaned dataset row count verified as 73,100 (exactly matches original; no silent row drops).
- [x] Cleaned CSV download verified.
- [x] Dataset metadata stored in SQLite `dataset_metadata` table.
- [x] Health check and existing Milestone 1 & 2 architecture remain fully operational.
- [x] **Zero Milestone 4+ features prematurely implemented** (No sales analysis charts, no feature engineering, no model training, no forecasting math).

---

## 5. Final Status

* **Status:** **MILESTONE 3 COMPLETED, VERIFIED & READY FOR REVIEW**
* **Next Step:** Await user review and approval before proceeding to Milestone 4 (Historical Sales Analysis).
