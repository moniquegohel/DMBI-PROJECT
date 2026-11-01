# SMARTSTOCK
## ML-Based Retail Demand Forecasting & Inventory Recommendation

**Project Type:** B.Tech 3rd-Year Academic Project  
**Application Type:** Beginner-friendly Full-Stack Web Application  
**Primary Goal:** Use historical retail sales data and machine learning to forecast future demand and provide simple inventory recommendations.

---

# 0. INSTRUCTIONS FOR ANTIGRAVITY

## IMPORTANT DEVELOPMENT RULES

This is a B.Tech 3rd-year academic project.

The developers are beginners.

**Do NOT over-engineer the application.**

Prefer simple, readable and well-commented code.

Do not introduce unnecessary technologies.

Do not add authentication, payment systems, cloud infrastructure, microservices, Docker, Kubernetes, real-time APIs, deep learning, LSTM models or advanced optimization unless explicitly requested.

The primary goal is:

1. Correct data processing
2. Correct machine learning workflow
3. Correct inventory logic
4. Clear business intelligence dashboard
5. Easy explanation during viva
6. Simple maintainable code

Every major implementation should be explained before or after it is created.

Do not silently change the project requirements.

If a requirement is technically ambiguous, explain the issue and choose the simplest reasonable implementation.

## Additional Agent Behaviour

- Work in clearly defined phases and milestones.
- Do not implement all project features in one step.
- Complete and verify one milestone before moving to the next.
- Before making a major architectural change, explain why it is necessary.
- Reuse simple components and functions rather than duplicating code.
- Keep frontend, backend, database, data-processing and ML responsibilities separated.
- Use meaningful variable, function, component and file names.
- Add comments where they help a beginner understand the logic.
- Avoid unnecessary abstraction.
- Do not replace a simple solution with a more advanced framework or library unless there is a clear requirement.
- Do not invent dataset columns. First inspect the actual dataset.
- If the selected dataset does not contain a required field, explain the limitation and use the simplest documented assumption or adaptation.
- Do not randomly shuffle time-series sales data when creating the ML train/test split.
- Keep the ML workflow reproducible.
- Validate important user inputs.
- Show understandable error messages instead of raw technical errors.
- Do not expose unnecessary backend stack traces in the frontend.
- Keep the application usable with a small development dataset before testing with a larger dataset.
- After each milestone, perform the relevant tests and report what works, what does not work, and what remains.
- Maintain a simple project README describing how to install, run and test the application.
- The application should remain suitable for academic demonstration and viva explanation.

---

# 1. PROJECT OVERVIEW

## 1.1 Project Name

**SMARTSTOCK**

### Full Title

**ML-Based Retail Demand Forecasting & Inventory Recommendation**

## 1.2 Project Description

SmartStock is a beginner-friendly web application designed to demonstrate how historical retail sales data can be analyzed using data mining, business intelligence and machine learning techniques.

The system will:

1. Accept a public retail sales dataset in CSV format.
2. Validate and clean the dataset.
3. Analyze historical sales.
4. Display useful business intelligence statistics and charts.
5. Create simple machine learning features.
6. Train two regression models:
   - Linear Regression
   - Random Forest Regression
7. Evaluate the models using:
   - MAE
   - RMSE
   - MAPE
8. Generate a minimum 7-day demand forecast for a selected product.
9. Accept simulated inventory information.
10. Simulate inventory conditions.
11. Identify:
   - Stockout Risk
   - Sufficient Stock
   - Overstock
12. Calculate a basic reorder quantity.
13. Display the result through a clear web dashboard.

The project should demonstrate the complete journey:

```text
Retail Sales CSV
        ↓
Data Cleaning
        ↓
Historical Sales Analysis
        ↓
Feature Engineering
        ↓
Machine Learning
        ↓
Model Evaluation
        ↓
Demand Forecast
        ↓
Inventory Simulation
        ↓
Inventory Status
        ↓
Reorder Recommendation
```

---

# 2. PROBLEM STATEMENT

Retail businesses commonly face two major inventory problems:

### Overstocking

Too many products remain unsold, increasing storage costs and the possibility of wastage or obsolete inventory.

### Stockouts

Products become unavailable when customers want to purchase them, resulting in potential lost sales.

Traditional inventory management may depend heavily on manual calculations and previous experience. However, sales demand can change because of:

- Seasonality
- Holidays
- Promotions
- Product popularity
- Customer behaviour
- Price changes
- Other factors available in the dataset

SmartStock uses historical sales data and machine learning to demonstrate how future demand can be estimated and how that estimate can be used to support simple inventory decisions.

The system is an academic demonstration and does not claim to replace professional inventory-management systems.

---

# 3. PROJECT OBJECTIVES

The main objectives are:

1. Import retail sales data from a CSV file.
2. Validate and clean historical sales data.
3. Analyze historical sales patterns.
4. Provide business intelligence visualizations.
5. Engineer useful time-based and sales-based features.
6. Train Linear Regression and Random Forest Regression models.
7. Evaluate the models using MAE, RMSE and MAPE.
8. Generate a 7-day product-level demand forecast.
9. Simulate inventory using user-provided stock assumptions.
10. Detect possible stockout and overstock situations.
11. Calculate a simple reorder quantity.
12. Present the results through a user-friendly dashboard.
13. Keep the complete workflow understandable for a B.Tech-level viva.

---

# 4. TARGET USERS

The primary target users for this academic application are:

- Small retail business users
- Inventory managers in a demonstration scenario
- Students learning data mining and business intelligence
- Students learning basic machine learning
- Project evaluators and faculty members

The application is primarily intended as an academic demonstration rather than a production enterprise inventory platform.

---

# 5. TECHNOLOGY STACK

Use a simple and beginner-friendly stack.

## 5.1 Frontend

Use:

- React
- Vite
- Tailwind CSS
- Recharts

### Purpose

React will create the web interface.

Vite will provide the frontend development environment.

Tailwind CSS will provide simple and consistent styling.

Recharts will create charts and visualizations.

---

## 5.2 Backend

Use:

- Python
- FastAPI

### Purpose

FastAPI will expose REST APIs for:

- Dataset upload
- Dataset information
- Sales analysis
- Model training
- Model evaluation
- Forecast generation
- Inventory analysis

Python will also handle:

- Pandas
- NumPy
- Scikit-learn
- Joblib
- Data processing
- Machine learning

---

## 5.3 Database

Use:

- SQLite
- SQLAlchemy

SQLite is preferred because:

- It does not require a separate database server.
- It is easy for beginners.
- It is sufficient for this academic project.
- It can be stored as a local database file.

Do not introduce PostgreSQL or another database unless specifically requested later.

---

## 5.4 Machine Learning

Use:

- Pandas
- NumPy
- Scikit-learn
- Joblib

Required models:

1. Linear Regression
2. Random Forest Regression

Do not add deep learning models.

---

# 6. SYSTEM ARCHITECTURE

The application should use the following high-level architecture:

```text
                    USER
                     |
                     v
             REACT FRONTEND
                     |
                     | REST API / JSON
                     v
              FASTAPI BACKEND
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
   DATABASE      DATA PROCESSING   ML MODULE
    SQLite          Pandas       Scikit-learn
       |             |             |
       +-------------+-------------+
                     |
                     v
              FORECAST RESULTS
                     |
                     v
            INVENTORY ANALYSIS
                     |
                     v
          RECOMMENDATION RESULT
                     |
                     v
              REACT DASHBOARD
```

## 6.1 Architectural Responsibilities

### Frontend

Responsible for:

- Navigation
- Forms
- Dataset upload interface
- Dashboard
- Tables
- Charts
- Forecast display
- Inventory input
- Recommendation display
- User-friendly error messages

### Backend

Responsible for:

- API endpoints
- File handling
- Data validation
- Data cleaning
- Database communication
- ML processing
- Forecast generation
- Inventory calculations

### Database

Responsible for storing:

- Product information
- Cleaned sales data
- Forecast results
- Inventory information
- Model evaluation results

### ML Module

Responsible for:

- Feature creation
- Train/test split
- Model training
- Prediction
- Model evaluation
- Forecast generation
- Model persistence

---

# 7. APPLICATION FLOW

The complete application flow should be:

```text
START
  ↓
Open SmartStock
  ↓
Dashboard
  ↓
Upload Retail Sales CSV
  ↓
Validate Dataset
  ↓
Clean Dataset
  ↓
Store Required Data
  ↓
Display Dataset Summary
  ↓
Historical Sales Analysis
  ↓
Feature Engineering
  ↓
Train Linear Regression
  ↓
Train Random Forest
  ↓
Evaluate Models
  ↓
Display MAE / RMSE / MAPE
  ↓
Use the selected model for forecasting
  ↓
Select Product
  ↓
Select Forecast Period
  ↓
Generate 7-Day Forecast
  ↓
Enter Current Stock
  ↓
Enter Safety Stock
  ↓
Enter Supplier Lead Time
  ↓
Run Inventory Analysis
  ↓
Identify Stockout / Sufficient / Overstock
  ↓
Calculate Reorder Quantity
  ↓
Display Recommendation
  ↓
END
```

The minimum required forecast period is 7 days.

---

# 8. FRONTEND REQUIREMENTS

The frontend should be a clean dashboard-style React application.

## 8.1 Required Pages

Create the following pages:

1. Dashboard
2. Dataset
3. Sales Analysis
4. Model Training
5. Demand Forecast
6. Inventory Analysis

---

## 8.2 Dashboard Page

The dashboard should provide an overview.

Display summary cards such as:

- Total Sales
- Number of Products
- Number of Records
- Date Range

Display:

- Sales trend chart
- Top-selling products
- Inventory status summary

Do not overcrowd the dashboard.

---

## 8.3 Dataset Page

Provide:

- CSV file upload
- Upload button
- Processing/loading indicator
- Dataset summary
- Number of records
- Number of products
- Date range
- Missing values
- Duplicate count
- Cleaning status

Example flow:

```text
Choose CSV
    ↓
Upload & Process
    ↓
Validate
    ↓
Clean
    ↓
Show Summary
```

---

## 8.4 Sales Analysis Page

Display:

### Statistics

- Total sales
- Average sales
- Minimum sales
- Maximum sales

### Charts

At minimum:

1. Sales trend over time
2. Monthly sales
3. Top-selling products

Optional if the dataset supports the required fields:

4. Sales by day of week
5. Promotion-related sales analysis

---

## 8.5 Model Training Page

Provide:

- Dataset information
- Feature list
- Target variable
- Train Model button
- Training progress indicator

Display model comparison:

```text
Model                 MAE       RMSE       MAPE
------------------------------------------------
Linear Regression     ...       ...        ...
Random Forest         ...       ...        ...
```

Also display:

- Actual vs Predicted chart
- Model used for forecasting

The interface should explain that the model used for forecasting is selected based on the evaluation results, without hiding the results of either model.

---

## 8.6 Demand Forecast Page

Allow the user to:

- Select product
- Select forecast period
- Select trained model if appropriate
- Generate forecast

Minimum:

```text
7-Day Forecast
```

Display:

- Forecast date
- Predicted demand
- Forecast line chart

---

## 8.7 Inventory Analysis Page

Provide input fields:

- Product
- Current Stock
- Safety Stock
- Supplier Lead Time

Display:

- Predicted Demand
- Current Stock
- Safety Stock
- Reorder Quantity
- Inventory Status

Use clear visual indicators but do not rely only on colour.

Example:

```text
Status: STOCKOUT RISK
Predicted Demand: 420
Current Stock: 300
Safety Stock: 100
Reorder Quantity: 220
```

---

# 9. BACKEND REQUIREMENTS

Use FastAPI.

The backend should be divided into logical modules.

## 9.1 Backend Responsibilities

The backend must handle:

1. CSV upload
2. Dataset validation
3. Data cleaning
4. Data storage
5. Historical analysis
6. Feature engineering
7. Model training
8. Model evaluation
9. Forecast generation
10. Inventory simulation
11. Recommendation calculation

---

## 9.2 Backend Design Principle

Keep the following responsibilities separate:

```text
Routes
  ↓
Services
  ↓
Database / ML / Processing
```

Routes should primarily handle API requests and responses.

Business logic should be placed in service modules rather than written entirely inside route functions.

---

# 10. DATABASE REQUIREMENTS

Use SQLite with SQLAlchemy.

## 10.1 Products Table

Suggested fields:

```text
id
product_code
product_name
category
price
created_at
```

Only include fields that are supported by the actual dataset.

---

## 10.2 Sales Table

Suggested fields:

```text
id
product_id
sale_date
quantity_sold
promotion
created_at
```

If promotion is not present in the dataset, do not invent historical promotion values.

---

## 10.3 Inventory Table

Suggested fields:

```text
id
product_id
current_stock
safety_stock
supplier_lead_time
updated_at
```

Inventory values are simulated/user-provided for this academic project.

---

## 10.4 Forecasts Table

Suggested fields:

```text
id
product_id
forecast_date
predicted_demand
model_name
created_at
```

---

## 10.5 Model Results Table

Suggested fields:

```text
id
model_name
mae
rmse
mape
training_date
```

---

# 11. DATA PROCESSING REQUIREMENTS

The application must accept a public retail sales dataset in CSV format.

Before implementation, inspect the actual selected dataset.

Do not assume that all datasets use the same column names.

## 11.1 Required Conceptual Fields

The application needs concepts corresponding to:

- Date
- Product
- Sales quantity / demand

Optional fields:

- Price
- Promotion
- Holiday
- Category
- Store

If the selected dataset uses different names, create a clear mapping between the dataset's actual columns and the application's internal column names.

---

## 11.2 Data Validation

Check:

- File type
- Empty file
- Required columns
- Missing values
- Duplicate records
- Invalid dates
- Invalid sales quantities
- Negative quantities where they are not logically valid
- Invalid product identifiers

---

## 11.3 Data Cleaning

The cleaning process should be transparent.

Potential operations:

- Convert date column to datetime
- Handle missing values appropriately
- Remove or handle duplicate records
- Handle invalid records
- Standardize column names
- Convert numeric columns to numeric types
- Sort sales data chronologically

Do not silently delete large portions of data.

If significant records are removed, report the number and reason.

---

## 11.4 Dataset Summary

After processing, provide:

```text
Total Records
Number of Products
Date Range
Missing Values
Duplicate Records
Minimum Sales
Maximum Sales
Average Sales
```

---

# 12. FEATURE ENGINEERING

Create simple features appropriate for beginner-level demand forecasting.

## 12.1 Required Features

Use:

```text
day
day_of_week
month
is_weekend
previous_day_sales
rolling_7_day_average
```

## 12.2 Optional Features

Only use these if available and appropriate:

```text
promotion
holiday
price
category
```

## 12.3 Target

The target should represent:

```text
sales / quantity_sold
```

The exact internal column name should match the normalized dataset structure.

---

## 12.4 Feature Explanation

The application documentation should explain:

### Day

The day number within the month.

### Day of Week

Monday, Tuesday, etc., represented numerically if required by the model.

### Month

The month associated with the sales date.

### Weekend

Indicates whether the date is Saturday or Sunday.

### Previous Day Sales

Sales recorded on the previous relevant day.

### 7-Day Average Sales

Average sales over the previous seven relevant days.

These features are intended to demonstrate basic time-based feature engineering rather than advanced forecasting.

---

# 13. MACHINE LEARNING REQUIREMENTS

The project must use two simple regression models.

## 13.1 Model 1 — Linear Regression

Use Scikit-learn LinearRegression.

Purpose:

- Provide a simple baseline model.
- Demonstrate a basic regression approach.

---

## 13.2 Model 2 — Random Forest Regression

Use Scikit-learn RandomForestRegressor.

Purpose:

- Provide a second regression approach capable of learning non-linear relationships.
- Compare its results with Linear Regression.

Keep hyperparameter tuning simple.

Do not implement complex automated hyperparameter optimization.

---

## 13.3 Train/Test Split

Use a chronological split.

Example:

```text
Earlier 80% → Training
Latest 20%  → Testing
```

Do not randomly shuffle the time-series sales data.

The reason should be documented:

The model should be trained on historical information and evaluated on later information to better represent the forecasting scenario.

---

## 13.4 ML Workflow

Implement:

```text
Clean Dataset
      ↓
Feature Engineering
      ↓
Chronological Train/Test Split
      ↓
Train Linear Regression
      ↓
Train Random Forest
      ↓
Generate Test Predictions
      ↓
Calculate Metrics
      ↓
Compare Models
      ↓
Select Model
      ↓
Save Model
```

---

# 14. MODEL EVALUATION

Calculate:

## 14.1 MAE

Mean Absolute Error.

Explain it as the average absolute difference between actual and predicted sales.

---

## 14.2 RMSE

Root Mean Squared Error.

Explain it as an error metric that gives greater influence to larger prediction errors.

---

## 14.3 MAPE

Mean Absolute Percentage Error.

Use appropriate handling for zero actual values.

Do not allow division-by-zero to produce invalid results.

---

## 14.4 Model Comparison

Display:

```text
Model                 MAE       RMSE       MAPE
------------------------------------------------
Linear Regression     ...       ...        ...
Random Forest         ...       ...        ...
```

The selected forecasting model should be based on the evaluation results.

Do not hard-code a model as the winner.

---

## 14.5 Actual vs Predicted

Provide a chart comparing:

```text
Actual Sales
vs
Predicted Sales
```

Use the test dataset.

---

# 15. DEMAND FORECASTING

The minimum forecasting requirement is:

```text
7-Day Forecast
```

## 15.1 User Flow

```text
Select Product
      ↓
Select Forecast Period
      ↓
Choose Trained Model
      ↓
Generate Forecast
      ↓
Display Forecast Table
      ↓
Display Forecast Chart
```

---

## 15.2 Forecast Output

Example:

```text
Product: P001

Date          Predicted Demand
--------------------------------
Day 1              125
Day 2              132
Day 3              140
Day 4              128
Day 5              135
Day 6              145
Day 7              138
```

The actual values will be generated by the trained model.

Do not hard-code these example values.

---

## 15.3 Forecasting Considerations

The implementation must ensure that future predictions are generated using information that would be available at prediction time.

Do not accidentally use future actual sales as input features.

If recursive forecasting is required because previous-day sales or rolling averages are used, implement the simplest understandable recursive approach and document it clearly.

---

# 16. INVENTORY SIMULATION

Actual retailer inventory data may not be available.

Therefore, inventory values will be simulated/user-provided.

The user should enter:

```text
Current Stock
Safety Stock
Supplier Lead Time
```

---

## 16.1 Inventory Simulation

Example:

```text
Current Stock = 500

Day 1 Demand = 120
Remaining = 380

Day 2 Demand = 130
Remaining = 250

Day 3 Demand = 150
Remaining = 100
```

The application should allow the forecast to be used to simulate the expected inventory level across the forecast period.

---

## 16.2 Inventory Simulation Rules

For each forecast day:

```text
Remaining Stock =
Previous Stock - Predicted Demand
```

Do not allow the displayed physical inventory to become negative.

If predicted demand exceeds available inventory, identify the stockout condition.

---

# 17. RECOMMENDATION LOGIC

Use simple, explainable rules.

## 17.1 Stockout Risk

If:

```text
Current Stock < Predicted Demand
```

display:

```text
STOCKOUT RISK
```

---

## 17.2 Overstock

If:

```text
Current Stock >
Predicted Demand + Safety Stock
```

display:

```text
OVERSTOCK
```

---

## 17.3 Sufficient Stock

Otherwise:

```text
SUFFICIENT STOCK
```

---

## 17.4 Reorder Quantity

Use:

```text
Reorder Quantity =
Predicted Demand + Safety Stock - Current Stock
```

If the result is below zero:

```text
Reorder Quantity = 0
```

---

## 17.5 Important Clarification

This is a simplified academic reorder rule.

It should be clearly described as a demonstration formula rather than a complete real-world inventory optimization model.

Supplier lead time should be displayed and incorporated into the inventory simulation where the implementation supports it, but the core required reorder formula must remain understandable.

---

# 18. API SPECIFICATION

Use REST APIs with JSON responses unless a file upload is required.

## 18.1 Dataset APIs

### Upload Dataset

```text
POST /api/dataset/upload
```

Purpose:

- Upload CSV
- Validate
- Clean
- Store
- Return dataset summary

---

### Dataset Summary

```text
GET /api/dataset/summary
```

Returns:

- Records
- Products
- Date range
- Missing values
- Duplicate count

---

# 18.2 Analysis APIs

### Sales Summary

```text
GET /api/analysis/summary
```

Returns:

- Total sales
- Average sales
- Minimum sales
- Maximum sales

### Monthly Sales

```text
GET /api/analysis/monthly
```

Returns chart-ready monthly sales data.

### Product Sales

```text
GET /api/analysis/products
```

Returns product-level sales summaries.

---

# 18.3 Product API

```text
GET /api/products
```

Returns available products for dropdown selection.

---

# 18.4 Model APIs

### Train Models

```text
POST /api/model/train
```

Trains:

- Linear Regression
- Random Forest

Returns evaluation results.

### Model Results

```text
GET /api/model/results
```

Returns:

- Model names
- MAE
- RMSE
- MAPE

---

# 18.5 Forecast API

```text
POST /api/forecast
```

Example request:

```json
{
  "product_id": "P001",
  "days": 7,
  "model": "random_forest"
}
```

Example response structure:

```json
{
  "product_id": "P001",
  "model": "random_forest",
  "forecast": [
    {
      "date": "YYYY-MM-DD",
      "predicted_demand": 125
    }
  ]
}
```

Do not hard-code example dates or values.

---

# 18.6 Inventory API

```text
POST /api/inventory/analyze
```

Example request:

```json
{
  "product_id": "P001",
  "current_stock": 300,
  "safety_stock": 100,
  "supplier_lead_time": 3,
  "predicted_demand": 420
}
```

Return:

```json
{
  "predicted_demand": 420,
  "current_stock": 300,
  "safety_stock": 100,
  "reorder_quantity": 220,
  "status": "STOCKOUT_RISK"
}
```

The exact response may include additional useful fields.

---

# 19. FOLDER STRUCTURE

Use a clear separation between frontend and backend.

```text
smartstock/
│
├── README.md
├── SMARTSTOCK_REQUIREMENTS.md
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   │
│   │   ├── routes/
│   │   │   ├── dataset.py
│   │   │   ├── analysis.py
│   │   │   ├── model.py
│   │   │   ├── forecast.py
│   │   │   └── inventory.py
│   │   │
│   │   ├── services/
│   │   │   ├── data_cleaning.py
│   │   │   ├── analysis.py
│   │   │   ├── feature_engineering.py
│   │   │   ├── model_training.py
│   │   │   ├── forecasting.py
│   │   │   └── inventory_logic.py
│   │   │
│   │   └── schemas/
│   │       └── schemas.py
│   │
│   ├── models/
│   ├── data/
│   │   └── sample_sales.csv
│   ├── requirements.txt
│   └── tests/
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   ├── Sidebar.jsx
    │   │   ├── StatCard.jsx
    │   │   ├── ChartCard.jsx
    │   │   ├── DataTable.jsx
    │   │   └── LoadingSpinner.jsx
    │   │
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── Dataset.jsx
    │   │   ├── SalesAnalysis.jsx
    │   │   ├── ModelTraining.jsx
    │   │   ├── DemandForecast.jsx
    │   │   └── Inventory.jsx
    │   │
    │   ├── services/
    │   │   └── api.js
    │   │
    │   ├── App.jsx
    │   └── main.jsx
    │
    ├── package.json
    └── vite.config.js
```

The exact structure may be adjusted if necessary, but changes should be explained and should not introduce unnecessary complexity.

---

# 20. UI REQUIREMENTS

## 20.1 Design Style

The interface should look like a clean modern business intelligence dashboard.

Use:

- Clear navigation
- Cards
- Tables
- Charts
- Simple forms
- Consistent spacing
- Responsive layout
- Clear headings

Avoid excessive animations.

---

## 20.2 Navigation

Use a sidebar or top navigation with:

```text
Dashboard
Dataset
Sales Analysis
Model Training
Demand Forecast
Inventory Analysis
```

---

## 20.3 Dashboard Cards

Use cards for:

```text
Total Sales
Products
Records
Average Sales
```

---

## 20.4 Status Display

Inventory status should be clearly displayed as text:

```text
STOCKOUT RISK
SUFFICIENT STOCK
OVERSTOCK
```

Do not depend only on red/green/yellow colour because users should be able to understand the status without colour.

---

## 20.5 Charts

Use Recharts.

Required charts:

1. Sales trend
2. Monthly sales
3. Top products
4. Actual vs predicted sales
5. Demand forecast

Only add more charts if they provide useful information.

---

# 21. VALIDATION & ERROR HANDLING

The application must handle common problems gracefully.

## 21.1 Dataset Errors

Display useful messages for:

- Invalid file type
- Empty CSV
- Missing required columns
- Invalid date values
- Invalid sales values
- Empty dataset after cleaning

---

## 21.2 ML Errors

Handle:

- Model training before data is uploaded
- Model training before enough valid data exists
- Missing features
- Invalid model state
- Forecast requested before model training

---

## 21.3 Forecast Errors

Handle:

- Invalid product
- Missing product
- Invalid forecast period
- Forecast requested without trained model

---

## 21.4 Inventory Errors

Validate:

- Current stock must be numeric and non-negative.
- Safety stock must be numeric and non-negative.
- Supplier lead time must be numeric and non-negative.
- Product must be selected.
- Required forecast information must exist.

---

# 22. TESTING REQUIREMENTS

Testing should be performed after each major milestone.

## 22.1 Dataset Testing

Test:

- Correct CSV
- Missing values
- Duplicate records
- Invalid dates
- Invalid quantities
- Empty dataset
- Missing columns

---

## 22.2 ML Testing

Test:

- Feature generation
- Train/test split
- Linear Regression training
- Random Forest training
- Prediction generation
- MAE
- RMSE
- MAPE
- Multiple products

---

## 22.3 Forecast Testing

Test:

- 7-day forecast
- Product selection
- Multiple products
- Missing model
- Missing data
- Forecast output structure

---

## 22.4 Inventory Testing

Test at minimum:

```text
Case 1: Stock > Demand
Case 2: Stock < Demand
Case 3: Stock = Demand
Case 4: Zero Stock
Case 5: Very High Stock
```

Verify reorder calculations.

---

## 22.5 Frontend Testing

Test:

- Navigation
- Buttons
- Forms
- File upload
- Loading states
- Error messages
- Tables
- Charts
- API connection

---

## 22.6 End-to-End Testing

Verify:

```text
Upload CSV
   ↓
Clean Dataset
   ↓
Analyze Sales
   ↓
Train Models
   ↓
Evaluate Models
   ↓
Generate Forecast
   ↓
Enter Inventory
   ↓
Analyze Inventory
   ↓
Display Recommendation
```

---

# 23. DEVELOPMENT PHASES

The application must be developed incrementally.

Do not attempt to build all modules simultaneously.

---

## Phase 1 — Project Setup

Tasks:

- Create repository/workspace.
- Create frontend.
- Create backend.
- Create basic folder structure.
- Install required dependencies.
- Verify frontend runs.
- Verify backend runs.
- Create basic README.

### Milestone

Frontend and backend both run successfully.

---

## Phase 2 — Database

Tasks:

- Configure SQLite.
- Configure SQLAlchemy.
- Create database connection.
- Create database models.
- Create required tables.
- Verify database operations.

### Milestone

Backend can connect to SQLite and create/read basic records.

---

## Phase 3 — Dataset Upload & Cleaning

Tasks:

- Implement CSV upload.
- Inspect actual dataset columns.
- Map required columns.
- Validate data.
- Clean data.
- Generate dataset summary.
- Store required information.

### Milestone

A user can upload a valid CSV and receive a dataset summary.

---

## Phase 4 — Historical Sales Analysis

Tasks:

- Calculate sales statistics.
- Calculate product-wise sales.
- Calculate monthly sales.
- Prepare chart-ready API responses.
- Build Sales Analysis frontend.

### Milestone

Historical sales analysis works through the web interface.

---

## Phase 5 — Feature Engineering

Tasks:

- Create day.
- Create day of week.
- Create month.
- Create weekend indicator.
- Create previous-day sales.
- Create 7-day average sales.
- Add optional fields only when supported by the dataset.
- Verify generated features.

### Milestone

A valid ML-ready dataset can be produced.

---

## Phase 6 — ML Model Development

Tasks:

- Implement chronological 80/20 split.
- Train Linear Regression.
- Train Random Forest.
- Generate test predictions.
- Save models using Joblib.
- Create model service.

### Milestone

Both required models train successfully.

---

## Phase 7 — Model Evaluation

Tasks:

- Calculate MAE.
- Calculate RMSE.
- Calculate MAPE.
- Compare models.
- Prepare actual vs predicted data.
- Build Model Training frontend.

### Milestone

Model comparison and evaluation are visible in the web application.

---

## Phase 8 — Demand Forecasting

Tasks:

- Select product.
- Select forecast period.
- Generate minimum 7-day forecast.
- Use trained model.
- Generate forecast table.
- Generate forecast chart.
- Handle recursive features correctly if required.

### Milestone

The application can generate a 7-day demand forecast for a selected product.

---

## Phase 9 — Inventory Simulation

Tasks:

- Add inventory input fields.
- Accept current stock.
- Accept safety stock.
- Accept supplier lead time.
- Simulate inventory across forecast days.
- Display inventory levels.

### Milestone

Forecast demand can be connected to simulated inventory.

---

## Phase 10 — Inventory Recommendation

Tasks:

- Detect stockout risk.
- Detect overstock.
- Detect sufficient stock.
- Calculate reorder quantity.
- Display recommendation.

### Milestone

The system provides an understandable inventory recommendation.

---

## Phase 11 — Frontend + Backend Integration

Tasks:

- Connect every frontend page to APIs.
- Connect dataset upload.
- Connect analysis.
- Connect model training.
- Connect forecast generation.
- Connect inventory analysis.
- Handle loading states.
- Handle errors.

### Milestone

The complete application works through the browser.

---

## Phase 12 — Final Testing & Presentation Preparation

Tasks:

- Run end-to-end tests.
- Fix bugs.
- Check all calculations.
- Check UI.
- Prepare demonstration dataset.
- Capture screenshots.
- Update README.
- Prepare project documentation.
- Prepare presentation.
- Prepare viva questions and answers.

### Milestone

A student can start the application and demonstrate the complete workflow from CSV upload to inventory recommendation.

---

# 24. TEAM RESPONSIBILITIES

Recommended team size: 4 students.

## Student 1 — Dataset & Data Preparation

Responsibilities:

- Dataset selection
- Dataset documentation
- Data cleaning
- Validation
- Database support
- Testing datasets
- Data quality verification

---

## Student 2 — Machine Learning & Forecasting

Responsibilities:

- Feature engineering
- ML dataset preparation
- Linear Regression
- Random Forest
- Model evaluation
- Forecasting
- ML testing

---

## Student 3 — Inventory & Recommendation

Responsibilities:

- Inventory assumptions
- Inventory simulation
- Stockout logic
- Overstock logic
- Reorder calculation
- Inventory testing

---

## Student 4 — Frontend & Integration

Responsibilities:

- React interface
- Dashboard
- Charts
- Forms
- Navigation
- API integration
- Frontend testing

---

## Team Requirement

All four students must understand the complete application flow for the final viva.

---

# 25. DEFINITION OF DONE

The project is complete when a student can:

1. Start the application.
2. Open the SmartStock dashboard.
3. Upload the public retail sales CSV.
4. Successfully validate and clean the dataset.
5. View historical sales analysis.
6. View sales charts.
7. Generate ML features.
8. Train Linear Regression.
9. Train Random Forest.
10. View MAE, RMSE and MAPE.
11. View actual vs predicted results.
12. Select a product.
13. Generate a 7-day demand forecast.
14. Enter simulated current stock.
15. Enter safety stock.
16. Enter supplier lead time.
17. Run inventory simulation.
18. Identify stockout/sufficient/overstock status.
19. Calculate reorder quantity.
20. View the final inventory recommendation.

The complete demonstration should work without requiring manual modification of source code during the demo.

---

# 26. FUTURE ENHANCEMENTS

The following features may be mentioned as future work but should not be implemented before the mandatory requirements are complete:

1. Weather data integration
2. Holiday/event APIs
3. Promotion-aware forecasting
4. Real-time inventory APIs
5. Supplier integration
6. Automated purchase orders
7. Multi-store inventory management
8. Advanced time-series models
9. LSTM/GRU models
10. Deep learning
11. Cloud deployment
12. Advanced optimization
13. Real-time POS integration
14. User authentication
15. Mobile application

---

# 27. IMPORTANT RESTRICTIONS

Do not add the following unless explicitly requested:

- Authentication
- Payment systems
- Cloud infrastructure
- Microservices
- Docker
- Kubernetes
- Real-time external APIs
- IoT
- Deep learning
- LSTM
- Complex optimization
- Supplier integration
- POS integration
- Unnecessary third-party services

Do not add features merely because they are technically possible.

The project should prioritize:

```text
Simple Implementation
        +
Correct Data Processing
        +
Correct ML Workflow
        +
Correct Inventory Logic
        +
Clear BI Dashboard
        +
Easy Viva Explanation
```

---

# 28. TWELVE MILESTONES — PROJECT DEVELOPMENT ORDER

The following order is mandatory for development.

## Milestone 1 — Project Architecture

First create:

- Project folders
- Frontend application
- Backend application
- Basic README
- Development configuration

Do not implement ML yet.

### Verify

- Frontend starts.
- Backend starts.
- Basic page loads.
- Basic API responds.

---

## Milestone 2 — Database Setup

Implement:

- SQLite
- SQLAlchemy
- Database connection
- Product model
- Sales model
- Inventory model
- Forecast model
- Model results model

### Verify

Database can be created and queried successfully.

---

## Milestone 3 — Dataset Upload and Cleaning

Implement:

- CSV upload
- Column inspection
- Column mapping
- Validation
- Cleaning
- Dataset summary

### Verify

A valid CSV can be uploaded and processed.

---

## Milestone 4 — Sales Analysis

Implement:

- Total sales
- Average sales
- Minimum sales
- Maximum sales
- Product summaries
- Monthly summaries
- Sales trend

### Verify

Sales Analysis page displays real data from the uploaded dataset.

---

## Milestone 5 — Feature Engineering

Implement:

```text
day
day_of_week
month
is_weekend
previous_day_sales
rolling_7_day_average
```

### Verify

The ML dataset contains the expected features without unintended future-data leakage.

---

## Milestone 6 — Model Training

Implement:

- Linear Regression
- Random Forest Regression
- Chronological 80/20 split
- Model persistence

### Verify

Both models train successfully.

---

## Milestone 7 — Model Evaluation

Implement:

- MAE
- RMSE
- MAPE
- Model comparison
- Actual vs predicted chart

### Verify

Evaluation results are generated from the test data and displayed correctly.

---

## Milestone 8 — Demand Forecast

Implement:

- Product selection
- Forecast period
- Model selection
- 7-day forecast
- Forecast table
- Forecast chart

### Verify

A selected product produces a valid 7-day forecast.

---

## Milestone 9 — Inventory Simulation

Implement:

- Current stock
- Safety stock
- Supplier lead time
- Daily inventory simulation

### Verify

Forecast demand changes simulated inventory levels correctly.

---

## Milestone 10 — Inventory Recommendation

Implement:

```text
Stockout Risk
Overstock
Sufficient Stock
Reorder Quantity
```

### Verify

All inventory test scenarios produce the expected status and calculation.

---

## Milestone 11 — Complete Integration

Connect:

```text
Frontend
   ↕
FastAPI
   ↕
Database
   ↕
Data Processing
   ↕
ML
   ↕
Forecast
   ↕
Inventory
```

### Verify

The complete application works from browser upload to recommendation.

---

## Milestone 12 — Final Testing and Documentation

Complete:

- Unit testing
- Integration testing
- End-to-end testing
- Error handling
- UI review
- README
- Project report material
- Screenshots
- Presentation material
- Viva preparation

### Verify

A complete demonstration can be performed without editing source code during the demonstration.

---

# 29. REQUIRED DEVELOPMENT ORDER SUMMARY

Antigravity should follow this exact high-level order:

```text
PHASE 1
Project Setup
        ↓
PHASE 2
Database
        ↓
PHASE 3
Dataset Upload & Cleaning
        ↓
PHASE 4
Historical Sales Analysis
        ↓
PHASE 5
Feature Engineering
        ↓
PHASE 6
ML Model Development
        ↓
PHASE 7
Model Evaluation
        ↓
PHASE 8
Demand Forecasting
        ↓
PHASE 9
Inventory Simulation
        ↓
PHASE 10
Inventory Recommendation
        ↓
PHASE 11
Frontend + Backend Integration
        ↓
PHASE 12
Testing + Documentation
```

Do not skip directly from Project Setup to a fully generated application.

Each phase should be completed, tested and understandable before moving to the next phase.

---

# 30. FINAL SYSTEM FLOW

The final SmartStock application should demonstrate:

```text
                         SMARTSTOCK
                              |
                              v
                    RETAIL SALES CSV
                              |
                              v
                       DATA UPLOAD
                              |
                              v
                       DATA CLEANING
                              |
                              v
                    HISTORICAL ANALYSIS
                              |
                              v
                     FEATURE ENGINEERING
                              |
                              v
                       ML TRAINING
                       /          \
                      /            \
                     v              v
            Linear Regression   Random Forest
                     \              /
                      \            /
                       v          v
                     MODEL EVALUATION
                              |
                              v
                      MODEL SELECTION
                              |
                              v
                     DEMAND FORECAST
                              |
                              v
                   INVENTORY SIMULATION
                              |
                    +---------+---------+
                    |         |         |
                    v         v         v
                STOCKOUT  SUFFICIENT  OVERSTOCK
                  RISK       STOCK
                    \         |         /
                     \        |        /
                      +-------+-------+
                              |
                              v
                    REORDER QUANTITY
                              |
                              v
                    FINAL DASHBOARD
```

---

# 31. FINAL PROJECT PRINCIPLE

The project should prioritize:

**Simple implementation + correct ML workflow + clear business intelligence + explainability + reliable demonstration**

rather than:

**Advanced technology + unnecessary features + complex architecture.**

The final application should be simple enough for a B.Tech 3rd-year student to understand every major component and explain the complete workflow during a viva.
