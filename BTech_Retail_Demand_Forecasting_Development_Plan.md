# B.Tech 3rd Year Project
# ML-Based Retail Demand Forecasting & Inventory Recommendation

## Simplified Development Plan

### Project Goal

Build a simple **Python desktop application** that:

1. Loads retail sales data from a CSV file.
2. Analyzes historical sales.
3. Trains an ML model to predict future demand.
4. Simulates inventory using assumed stock values.
5. Identifies stockout/overstock situations.
6. Suggests a basic reorder quantity.
7. Displays the results in a simple desktop interface.

The project should remain **simple, demonstrative, and suitable for a B.Tech 3rd-year project**.

---

# Team Structure

Recommended team: **4 students**

| Student | Main Responsibility |
|---|---|
| Student 1 | Dataset & Data Preparation |
| Student 2 | Machine Learning & Forecasting |
| Student 3 | Inventory Logic & Recommendations |
| Student 4 | Desktop UI & Integration |

All students should understand the complete project for the final viva.

---

# Phase 1 — Project Setup & Understanding

## Student 1 — Dataset

Tasks:
- Find and select one public retail sales dataset.
- Understand the columns.
- Document the dataset source.
- Identify the sales/date/product columns required by the project.
- Keep a small sample dataset for development/testing.

Output:
- Selected dataset.
- Dataset description.
- Sample CSV.

---

## Student 2 — ML

Tasks:
- Understand the basic concept of demand forecasting.
- Research Linear Regression and Random Forest Regression.
- Decide which features can be used for prediction.
- Prepare a simple ML workflow diagram.

Output:
- ML approach document.
- Initial model plan.

---

## Student 3 — Inventory

Tasks:
- Understand stockout and overstock concepts.
- Define simple inventory assumptions.
- Define the reorder calculation.

Use:

```text
Reorder Quantity =
Predicted Demand + Safety Stock - Current Stock
```

If the result is below zero, use zero.

Output:
- Inventory rules document.
- Example calculations.

---

## Student 4 — UI

Tasks:
- Design a very simple desktop application layout.
- Identify required screens/buttons.
- Create a basic Tkinter prototype.

Suggested screens:

```text
Home
Data Analysis
Model Training
Demand Forecast
Inventory Analysis
```

Output:
- Basic UI prototype.

---

# Phase 2 — Data Preparation

## Student 1 — Main Owner

Tasks:
- Load CSV using Pandas.
- Check missing values.
- Check duplicate records.
- Validate dates.
- Validate sales quantities.
- Remove or handle invalid records.
- Save the cleaned dataset.

Output:

```text
data_cleaner.py
clean_sales.csv
```

---

## Student 2 — Support

Tasks:
- Check whether the cleaned data contains enough information for ML.
- Identify the target variable.

Target:

```text
Quantity Sold / Sales
```

Output:
- Confirmed ML input and target columns.

---

## Student 3 — Support

Tasks:
- Identify the fields needed later for inventory simulation.
- Define simulated values for:
  - Current Stock
  - Safety Stock
  - Supplier Lead Time

Output:
- Inventory input specification.

---

## Student 4 — Support

Tasks:
- Add "Load Dataset" functionality to the UI.
- Display:
  - Number of records
  - Number of products
  - Date range

Output:
- Working dataset-loading screen.

---

# Phase 3 — Historical Sales Analysis

## Student 1 — Main Owner

Tasks:
- Calculate:
  - Total sales
  - Average sales
  - Minimum sales
  - Maximum sales
- Generate product-wise sales summary.
- Generate monthly sales summary.

Output:
- Sales analysis module.

---

## Student 2 — Support

Tasks:
- Identify useful patterns in the data.
- Check whether sales vary by:
  - Day
  - Month
  - Product
  - Promotion, if available

Output:
- List of useful ML features.

---

## Student 3 — Support

Tasks:
- Review sales patterns relevant to inventory.
- Identify high-selling and low-selling products.

Output:
- Basic inventory observations.

---

## Student 4 — Main UI Owner

Tasks:
- Display sales statistics.
- Display a basic sales trend chart.
- Display top-selling products.

Output:
- Working Sales Analysis screen.

---

# Phase 4 — Feature Engineering

## Student 1 — Main Owner

Create simple features:

```text
Day
Day of Week
Month
Weekend
Previous Day Sales
7-Day Average Sales
```

If available, optionally include:

```text
Promotion
Holiday
Price
```

Output:

```text
feature_engineering.py
```

---

## Student 2 — Main Owner

Tasks:
- Select the final ML features.
- Define the prediction target.
- Prepare the ML dataset.

Example:

```text
Features:
Day of Week
Month
Weekend
Previous Day Sales
7-Day Average Sales

Target:
Sales
```

Output:
- Final ML training dataset.

---

## Student 3

Tasks:
- Check whether the features are sufficient for inventory simulation.

Output:
- Confirmation of required forecast information.

---

## Student 4

Tasks:
- No major development required.
- Help test the feature-processing flow through the UI.

---

# Phase 5 — ML Model Development

## Student 2 — Main Owner

Train two simple models:

1. Linear Regression
2. Random Forest Regression

Process:

```text
Clean Data
   ↓
Create Features
   ↓
Time-Based Train/Test Split
   ↓
Train Model
   ↓
Generate Predictions
   ↓
Evaluate Model
```

Use a chronological split.

Example:

```text
Earlier 80% → Training
Latest 20%  → Testing
```

Do not randomly shuffle the sales data.

Output:

```text
models/
    linear_regression.py
    random_forest.py
    model_evaluation.py
```

---

## Student 1

Tasks:
- Provide cleaned data.
- Help verify the training dataset.

---

## Student 3

Tasks:
- Review predicted values.
- Check whether predictions are reasonable from an inventory perspective.

---

## Student 4

Tasks:
- Create UI area for:
  - Train Model button
  - Model comparison
  - Evaluation results

---

# Phase 6 — Model Evaluation

## Student 2 — Main Owner

Calculate:

```text
MAE
RMSE
MAPE
```

Example output:

```text
Model                 MAE     RMSE     MAPE
------------------------------------------------
Linear Regression     15.2    21.4     18.5%
Random Forest           9.8    14.1     11.7%
```

Select the model to use for forecasting based on the evaluation results.

Also create:

```text
Actual Sales vs Predicted Sales
```

graph.

Output:
- Model comparison.
- Evaluation results.
- Actual vs predicted graph.

---

## Student 4

Tasks:
- Display evaluation results in the UI.
- Display the actual vs predicted graph.

---

# Phase 7 — Demand Forecasting

## Student 2 — Main Owner

Implement future demand prediction.

Minimum requirement:

```text
7-Day Forecast
```

Optional:

```text
14-Day Forecast
30-Day Forecast
```

The user should be able to select a product and generate a forecast.

Example:

```text
Product: P001

Day 1    125
Day 2    132
Day 3    140
Day 4    128
Day 5    135
Day 6    145
Day 7    138
```

Output:

```text
demand_forecast.py
```

---

## Student 1

Tasks:
- Verify that historical data required for forecasting is available.
- Test forecasts for multiple products.

---

## Student 3

Tasks:
- Check forecast output against inventory rules.

---

## Student 4

Tasks:
- Add product selection.
- Add forecast-period selection.
- Add Forecast button.
- Display forecast table and graph.

---

# Phase 8 — Inventory Simulation

## Student 3 — Main Owner

Use simulated inventory values because actual retailer inventory may not be available.

User inputs:

```text
Current Stock
Safety Stock
Supplier Lead Time
```

Use forecast demand to simulate inventory.

Example:

```text
Current Stock = 500

Day 1 Demand = 120
Remaining    = 380

Day 2 Demand = 130
Remaining    = 250

Day 3 Demand = 150
Remaining    = 100
```

Output:

```text
inventory_simulation.py
```

---

## Student 2

Tasks:
- Provide predicted demand to the inventory module.
- Verify that the forecast is passed correctly.

---

## Student 1

Tasks:
- Test inventory simulation using different products.

---

## Student 4

Tasks:
- Add inventory input fields to the UI.
- Display simulated inventory levels.

---

# Phase 9 — Stockout / Overstock / Reorder

## Student 3 — Main Owner

Implement simple rules.

### Stockout Risk

If:

```text
Current Stock < Predicted Demand
```

show:

```text
STOCKOUT RISK
```

### Reorder

Calculate:

```text
Reorder Quantity =
Predicted Demand + Safety Stock - Current Stock
```

If result < 0:

```text
Reorder Quantity = 0
```

### Overstock

Use a simple documented rule such as:

```text
Current Stock > Predicted Demand + Safety Stock
```

show:

```text
OVERSTOCK
```

Otherwise:

```text
SUFFICIENT
```

Output:
- Inventory decision module.

---

## Student 2

Tasks:
- Verify calculations using forecast results.

---

## Student 1

Tasks:
- Prepare different test cases:
  - Low stock
  - Sufficient stock
  - High stock
  - Zero stock

---

## Student 4

Tasks:
- Display:

```text
Current Stock
Predicted Demand
Safety Stock
Reorder Quantity
Status
```

---

# Phase 10 — Final Desktop Application

## Student 4 — Main Owner

Combine all modules into one simple Tkinter application.

Main flow:

```text
Start
  ↓
Load CSV
  ↓
Analyze Sales
  ↓
Train Model
  ↓
Select Product
  ↓
Forecast Demand
  ↓
Enter Inventory
  ↓
Analyze Inventory
  ↓
Show Recommendation
```

Required screens:

### 1. Home

```text
[Load Dataset]
[Sales Analysis]
[Train Model]
[Demand Forecast]
[Inventory Analysis]
```

### 2. Sales Analysis

Display:

- Dataset summary
- Sales statistics
- Sales chart

### 3. Model Training

Display:

- Models
- MAE
- RMSE
- MAPE
- Actual vs Predicted graph

### 4. Demand Forecast

Display:

- Product
- Forecast period
- Predicted demand
- Forecast graph

### 5. Inventory Analysis

Display:

- Current stock
- Safety stock
- Predicted demand
- Reorder quantity
- Inventory status

---

# Phase 11 — Testing

## Student 1 — Data Testing

Test:

- Correct CSV
- Missing values
- Duplicate records
- Invalid dates
- Empty dataset

---

## Student 2 — ML Testing

Test:

- Model training
- Model prediction
- Model evaluation
- Multiple products
- Forecast generation

---

## Student 3 — Inventory Testing

Test:

```text
Case 1: Stock > Demand
Case 2: Stock < Demand
Case 3: Stock = Demand
Case 4: Zero Stock
Case 5: Very High Stock
```

Verify reorder calculations.

---

## Student 4 — Application Testing

Test:

- Buttons
- Input fields
- Screen navigation
- Error messages
- Charts
- Complete end-to-end workflow

---

# Phase 12 — Final Integration

All students work together.

Run the complete demonstration:

```text
1. Start Application
        ↓
2. Load Public Retail Dataset
        ↓
3. Analyze Historical Sales
        ↓
4. Train ML Models
        ↓
5. Compare Models
        ↓
6. Select Model
        ↓
7. Select Product
        ↓
8. Generate 7-Day Forecast
        ↓
9. Enter Current Stock
        ↓
10. Run Inventory Simulation
        ↓
11. Show Stockout/Overstock Status
        ↓
12. Show Reorder Recommendation
```

---

# Simple Final Feature List

Only the following features are mandatory:

- [ ] Load CSV dataset
- [ ] Clean sales data
- [ ] Analyze historical sales
- [ ] Display sales graph
- [ ] Create basic ML features
- [ ] Train Linear Regression
- [ ] Train Random Forest
- [ ] Compare MAE/RMSE/MAPE
- [ ] Generate 7-day demand forecast
- [ ] Enter simulated inventory values
- [ ] Simulate inventory
- [ ] Detect stockout risk
- [ ] Detect overstock
- [ ] Calculate reorder quantity
- [ ] Display recommendation
- [ ] Run everything through a simple desktop application

---

# What Students Should NOT Spend Time On

Do not add complexity unless all mandatory functionality is working.

Avoid:

- Web development
- Mobile application
- Database
- Login/authentication
- Cloud hosting
- Real-time APIs
- IoT
- Weather APIs
- Deep learning
- LSTM
- Complex optimization algorithms
- Supplier integration
- POS integration

These can be mentioned as future enhancements.

---

# Suggested 8-Week Schedule

## Week 1 — Understanding & Dataset

Student 1:
- Dataset selection

Student 2:
- ML research

Student 3:
- Inventory rules

Student 4:
- UI design

**Milestone:** Dataset and project design finalized.

---

## Week 2 — Data Preparation

Student 1:
- Cleaning

Student 2:
- ML data requirements

Student 3:
- Inventory assumptions

Student 4:
- Dataset loading UI

**Milestone:** Clean dataset can be loaded.

---

## Week 3 — Sales Analysis

Student 1:
- Sales calculations

Student 2:
- Feature identification

Student 3:
- Sales/inventory observations

Student 4:
- Charts and analysis screen

**Milestone:** Historical sales analysis works.

---

## Week 4 — ML

Student 1:
- Finalize training data

Student 2:
- Train two models

Student 3:
- Review predictions

Student 4:
- Model training UI

**Milestone:** Models train successfully.

---

## Week 5 — Evaluation & Forecast

Student 1:
- Test data

Student 2:
- MAE/RMSE/MAPE
- 7-day forecast

Student 3:
- Forecast review

Student 4:
- Forecast UI

**Milestone:** Future demand can be predicted.

---

## Week 6 — Inventory

Student 1:
- Test scenarios

Student 2:
- Connect forecast to inventory

Student 3:
- Inventory simulation and recommendations

Student 4:
- Inventory UI

**Milestone:** Reorder recommendation works.

---

## Week 7 — Integration & Testing

All students:
- Connect all modules.
- Fix bugs.
- Test complete workflow.

**Milestone:** Complete application works from CSV to recommendation.

---

## Week 8 — Documentation & Presentation

All students:
- Prepare project report.
- Prepare presentation.
- Prepare demo dataset.
- Prepare screenshots.
- Practice viva questions.
- Practice final demonstration.

**Milestone:** Final project ready for evaluation.

---

# Final Expected Output

The completed application should demonstrate:

```text
                RETAIL SALES CSV
                       |
                       v
                DATA CLEANING
                       |
                       v
              SALES ANALYSIS
                       |
                       v
              ML MODEL TRAINING
                       |
                       v
               MODEL EVALUATION
                       |
                       v
              DEMAND FORECAST
                       |
                       v
             INVENTORY SIMULATION
                       |
             +---------+---------+
             |                   |
             v                   v
        STOCKOUT RISK         OVERSTOCK
             |                   |
             +---------+---------+
                       |
                       v
              REORDER QUANTITY
                       |
                       v
                FINAL REPORT
```

## Definition of Done

The project is complete when a student can start the application, load the public retail CSV, train the ML model, select a product, generate a 7-day demand forecast, enter simulated stock information, and receive a clear inventory recommendation.

The project should prioritize:

**Simple implementation + correct ML workflow + clear demonstration + explainability**

rather than advanced technology or excessive features.
