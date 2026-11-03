"""
test_milestone10.py — Automated Unit & Integration Tests for Milestone 10: Smart Inventory Recommendation

Executes 10 comprehensive tests verifying:
1. Generation of recommendations across all 100 store-product series.
2. Sourcing of inventory levels from actual recorded ending inventory on 2024-01-01.
3. Mathematical precision of Reorder Point (ROP = d_bar * (L + S_buf)).
4. Target stock (S_target = D_horizon + SS) and Suggested Reorder Quantity logic.
5. Strict non-negativity constraint (Q_reorder >= 0).
6. Four-tier mutually exclusive classification (Restock Soon, Stock Available, Excess Stock, Insufficient Data).
7. Summary metrics mathematical balance (restock + available + excess + insufficient == total).
8. Store ID and Status filter isolation.
9. Dynamic configuration of supplier lead time and safety buffer parameters.
10. FastAPI route handler validity (/api/recommendation/all and /api/recommendation/calculate).
"""

import unittest
import pandas as pd
import numpy as np

from app.services.data_cleaning import CLEANED_DATASET_PATH
from app.services.inventory_recommendation import (
    get_inventory_recommendations,
    _compute_all_recommendations,
)
from app.routes.recommendation import (
    get_all_recommendations,
    calculate_recommendations,
    RecommendationCalculateRequest,
)


class TestMilestone10InventoryRecommendation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Execute batch recommendations once for inspection
        cls.resp = get_inventory_recommendations(
            lead_time_days=2,
            safety_buffer_days=1,
            horizon_days=7,
        )

    def test_01_all_recommendations_generation(self):
        """Verify all 100 store-product series are evaluated with complete metadata."""
        items = self.resp.items
        self.assertEqual(len(items), 100, f"Expected 100 series evaluated, found {len(items)}")
        self.assertEqual(len(self.resp.stores), 5, f"Expected 5 distinct stores, found {len(self.resp.stores)}")
        self.assertGreaterEqual(len(self.resp.categories), 3, "Expected multiple product categories")

    def test_02_actual_inventory_source(self):
        """Verify current stock matches actual recorded ending inventory on 2024-01-01."""
        df = pd.read_csv(CLEANED_DATASET_PATH)
        latest_date = df["Date"].max()
        latest_slice = df[df["Date"] == latest_date]
        
        # Check first 5 items against cleaned dataset values
        for item in self.resp.items[:5]:
            match = latest_slice[
                (latest_slice["Store ID"] == item.store_id) &
                (latest_slice["Product ID"] == item.product_id)
            ]
            self.assertFalse(match.empty, f"No record found for {item.store_id} / {item.product_id}")
            expected_stock = float(match.iloc[0]["Inventory Level"])
            self.assertEqual(item.current_stock, expected_stock)

    def test_03_reorder_point_calculation(self):
        """Assert ROP = round(d_bar * (L + S_buf), 1)."""
        L = 2
        S_buf = 1
        for item in self.resp.items:
            if item.status != "Insufficient Data":
                expected_rop = round(item.daily_demand * (L + S_buf), 1)
                self.assertAlmostEqual(
                    item.reorder_point,
                    expected_rop,
                    places=1,
                    msg=f"ROP mismatch for {item.store_id}/{item.product_id}"
                )

    def test_04_target_stock_and_reorder_quantity_formula(self):
        """Assert target stock and reorder quantity follow retail balance equations."""
        S_buf = 1
        for item in self.resp.items:
            if item.status != "Insufficient Data":
                expected_target = round(item.forecasted_demand + (item.daily_demand * S_buf), 1)
                self.assertAlmostEqual(item.target_stock, expected_target, places=1)

                if item.current_stock <= item.reorder_point:
                    expected_reorder = max(0.0, round(item.target_stock - item.current_stock, 1))
                    self.assertAlmostEqual(item.suggested_reorder_qty, expected_reorder, places=1)
                else:
                    self.assertEqual(item.suggested_reorder_qty, 0.0)

    def test_05_reorder_quantity_never_negative(self):
        """Assert suggested reorder quantity is strictly non-negative across all series."""
        for item in self.resp.items:
            self.assertGreaterEqual(
                item.suggested_reorder_qty,
                0.0,
                f"Negative reorder quantity detected for {item.store_id}/{item.product_id}"
            )

    def test_06_classification_integrity(self):
        """Assert every series is classified into valid mutually exclusive categories."""
        valid_statuses = {"Restock Soon", "Stock Available", "Excess Stock", "Insufficient Data"}
        for item in self.resp.items:
            self.assertIn(item.status, valid_statuses)
            if item.status == "Restock Soon":
                self.assertLessEqual(item.current_stock, item.reorder_point)
            elif item.status == "Excess Stock":
                self.assertGreater(item.current_stock, item.target_stock * 1.5)

    def test_07_summary_counts_balance(self):
        """Assert category counts sum up exactly to total evaluated products."""
        summary = self.resp.summary
        total_counted = (
            summary.restock_soon_count +
            summary.stock_available_count +
            summary.excess_stock_count +
            summary.insufficient_data_count
        )
        self.assertEqual(total_counted, summary.total_products_evaluated)
        self.assertEqual(summary.total_products_evaluated, 100)
        self.assertGreaterEqual(summary.total_reorder_units, 0.0)

    def test_08_store_and_status_filtering(self):
        """Assert filtering isolates specific stores and statuses."""
        filtered_store = get_inventory_recommendations(store_id="S001")
        self.assertEqual(len(filtered_store.items), 20)
        for item in filtered_store.items:
            self.assertEqual(item.store_id, "S001")

        filtered_status = get_inventory_recommendations(status="Restock Soon")
        for item in filtered_status.items:
            self.assertEqual(item.status, "Restock Soon")

    def test_09_custom_lead_time_and_buffer_parameters(self):
        """Assert user customization of lead time increases ROP accordingly."""
        custom_resp = get_inventory_recommendations(
            lead_time_days=5,
            safety_buffer_days=2,
            horizon_days=7,
        )
        self.assertEqual(len(custom_resp.items), 100)
        first_item = custom_resp.items[0]
        self.assertEqual(first_item.lead_time_days, 5)
        self.assertEqual(first_item.safety_buffer_days, 2)
        expected_rop = round(first_item.daily_demand * (5 + 2), 1)
        self.assertAlmostEqual(first_item.reorder_point, expected_rop, places=1)

    def test_10_api_endpoints_functional(self):
        """Assert FastAPI route handlers return valid schemas."""
        res_all = get_all_recommendations(store_id="S002", lead_time_days=2, safety_buffer_days=1, horizon_days=7)
        self.assertEqual(len(res_all.items), 20)
        self.assertIn("S002", res_all.stores)

        req_calc = RecommendationCalculateRequest(
            store_id=None,
            category=None,
            status=None,
            horizon_days=7,
            lead_time_days=3,
            safety_buffer_days=1,
        )
        res_calc = calculate_recommendations(req_calc)
        self.assertEqual(len(res_calc.items), 100)


if __name__ == "__main__":
    unittest.main()
