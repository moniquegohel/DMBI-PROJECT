# SMARTSTOCK — PROJECT LIMITATIONS & FUTURE SCOPE

> **Project:** SMARTSTOCK — ML-Based Retail Demand Forecasting & Inventory Recommendation  
> **Academic Level:** B.Tech, Third Year (Data Mining & Business Intelligence)  
> **Target Audience:** Academic Evaluators, External Examiners & Project Guides  
> **Date:** November 2026  

---

## 1. Executive Summary

Every practical engineering project operates within defined scope boundaries and academic constraints. Transparency regarding technical assumptions, dataset limitations, and model boundaries is a hallmark of academic integrity.

This document clearly outlines the known limitations of SMARTSTOCK and proposes realistic avenues for future expansion.

---

## 2. Dataset Limitations & Modeling Assumptions

### 2.1 Scope & Demographics
- **Synthetic Retail Footprint:** The dataset simulates 5 retail stores (`S001` - `S005`) and 20 product SKUs (`P0001` - `P0020`), generating 100 continuous daily time-series. Real-world hypermarket enterprises often manage thousands of stores and 50,000+ SKUs.
- **Fixed Catalogue:** The catalogue of stores and SKUs remains static throughout the 2-year historical window (`2022-01-01` to `2024-01-01`). New product introductions (cold-start items) or phased-out items are not represented.
- **Unrecorded Supplier Variables:**
  - **Supplier Lead Time ($L$):** Real-world supply chains experience variable lead times due to vendor delays, port congestion, or transit bottlenecks. In SMARTSTOCK, supplier lead time is modeled with a configurable default of **2 days**.
  - **Safety Buffer ($S_{\text{buf}}$):** Modeled with a configurable default of **1 day** to buffer against demand fluctuations.
  - **Batch Minimum Order Quantities (MOQ):** Suppliers frequently mandate pack sizes or pallets (e.g. multiples of 50). SMARTSTOCK recommends exact continuous unit quantities without MOQ quantization.

### 2.2 Demand vs. Sales Censoring
- **Censored Demand:** The dataset records `Units Sold` rather than true unconstrained customer demand. In retail, when stock runs out mid-day, subsequent customer demand is lost and unrecorded. SMARTSTOCK uses historical sales as the proxy for demand.

---

## 3. Machine Learning & Forecasting Boundaries

### 3.1 Point Predictions vs. Probabilistic Distributions
- SMARTSTOCK produces deterministic **point forecasts** ($\hat{y}_t$) rather than quantile probabilistic cones (e.g., P10 / P50 / P90). While highly interpretable for store managers, point forecasts do not capture tail-risk distribution spreads.

### 3.2 Recursive Multi-Step Error Propagation
- For horizons of 14 and 30 days, SMARTSTOCK uses recursive multi-step forecasting: Day $t+1$ predictions feed into Day $t+2$ lag and rolling features.
- Any forecasting error introduced in early days can propagate into later horizons. Consequently, the **7-day horizon** is recommended for operational reordering, while 14 and 30-day horizons serve as strategic guidelines.

### 3.3 Model Generalization
- The empirical evaluation proved that **Linear Regression** outperformed **Random Forest** (MAE: 88.80 vs 90.76). However, linear models cannot naturally model complex cross-elasticities (e.g., when the price of SKU A drops, demand for substitute SKU B decreases).

---

## 4. Architectural & Operational Boundaries

### 4.1 Single-Tier vs. Multi-Echelon Supply Chains
- SMARTSTOCK models a **single-tier retail inventory** (direct store replenishment). It does not model a central distribution center (CDC) allocating stock among regional fulfillment hubs.

### 4.2 Local In-Memory Architecture
- In compliance with academic project rules:
  - No cloud microservices, Docker, or Kubernetes were introduced.
  - No real-time external POS streaming APIs or payment gateways were added.
  - The application runs locally on a standard Windows laptop using SQLite, local file storage, and lightweight in-memory caching.

---

## 5. Roadmap for Future Enhancements

If continued into a final-year B.Tech capstone or commercial deployment, the following enhancements would be natural extensions:

1. **Probabilistic & Deep Learning Models:**
   - Incorporate DeepAR, Temporal Fusion Transformers (TFT), or Prophet to generate confidence intervals ($P_{10}, P_{50}, P_{90}$).
2. **Dynamic Lead Time Modeling:**
   - Model supplier lead time as a stochastic distribution ($\mu_L, \sigma_L$) rather than a deterministic constant.
3. **Multi-Echelon Inventory Optimization:**
   - Optimize allocation from Central Warehouse to Regional Hubs and Local Stores simultaneously.
4. **Automated Purchase Order (PO) Generation:**
   - Direct integration with ERP systems (SAP, Oracle Retail) to automatically transmit EDI purchase orders when stock reaches ROP.
5. **Cannibalization & Substitution Effects:**
   - Machine learning features tracking cross-product substitution when preferred SKUs stock out.

