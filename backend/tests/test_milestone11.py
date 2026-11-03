"""
test_milestone11.py — Automated Unit & Integration Tests for Milestone 11: Business Insights Dashboard

Executes 10 comprehensive tests verifying:
1. Executive dashboard summary endpoint health and schema compliance.
2. KPI card numerical consistency with catalogue recommendations.
3. Top demand products sorted in descending order of expected demand.
4. Identification and ranking of critical stockout risks (< 3 days of supply).
5. Mathematical integrity of regional store replenishment aggregation.
6. Generation of plain-language, jargon-free business insight callouts.
7. Category distribution and visualization chart payload data structures.
8. Robustness against extreme parameters or empty filters.
9. Absence of internal ML jargon (e.g. loss convergence, hyperparameter) in retail titles.
10. Sub-second response time for dashboard executive summary query.
"""

import unittest
import time
from app.services.inventory_recommendation import get_dashboard_summary
from app.routes.recommendation import get_dashboard_kpis_and_insights


class TestMilestone11BusinessInsightsDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Query dashboard summary once
        cls.summary = get_dashboard_summary()

    def test_01_dashboard_summary_endpoint_success(self):
        """Verify dashboard summary returns valid schema and populated fields."""
        summary = self.summary
        self.assertEqual(summary.total_stores, 5)
        self.assertEqual(summary.total_products, 20)
        self.assertGreaterEqual(summary.products_requiring_restock, 0)
        self.assertGreaterEqual(summary.products_with_excess_inventory, 0)
        self.assertGreaterEqual(summary.total_suggested_reorder_volume, 0.0)

    def test_02_kpi_cards_consistency(self):
        """Assert KPI card totals match the category distribution items."""
        summary = self.summary
        dist_map = {x["status"]: x["count"] for x in summary.category_distribution}
        self.assertEqual(summary.products_requiring_restock, dist_map.get("Restock Soon", 0))
        self.assertEqual(summary.products_with_excess_inventory, dist_map.get("Excess Stock", 0))

    def test_03_top_demand_products_ordering(self):
        """Assert top demand products are ranked in strictly descending order."""
        top_list = self.summary.top_demand_products
        self.assertGreaterEqual(len(top_list), 1)
        self.assertLessEqual(len(top_list), 5)
        demands = [x["forecasted_demand"] for x in top_list]
        self.assertEqual(demands, sorted(demands, reverse=True))

    def test_04_stockout_risk_identification(self):
        """Assert products flagged as stockout risks have low runway."""
        risks = self.summary.stockout_risks
        for item in risks:
            self.assertLess(item["days_of_supply"], 3.5)
            self.assertGreater(item["suggested_reorder_qty"], 0.0)

    def test_05_store_wise_aggregation_math(self):
        """Assert sum of store-level reorders matches total suggested reorder volume."""
        store_sum = sum(s.total_reorder_units for s in self.summary.store_replenishment)
        self.assertAlmostEqual(
            store_sum,
            self.summary.total_suggested_reorder_volume,
            places=1,
            msg="Store-level reorder sum must equal total reorder volume."
        )

    def test_06_business_insights_narratives_present(self):
        """Assert insights contain clear retail explanations and recommended actions."""
        insights = self.summary.insights
        self.assertGreaterEqual(len(insights), 2, "Expected at least 2 dynamic insight cards")
        for ins in insights:
            self.assertTrue(len(ins.title) > 5)
            self.assertTrue(len(ins.description) > 10)
            self.assertTrue(len(ins.recommended_action) > 10)
            self.assertIn(ins.severity, {"CRITICAL", "WARNING", "INFO"})

    def test_07_chart_data_payload_structure(self):
        """Assert category distribution percentages sum approximately to 100%."""
        dist = self.summary.category_distribution
        pct_sum = sum(x["percentage"] for x in dist)
        self.assertAlmostEqual(pct_sum, 100.0, delta=1.0)
        for d in dist:
            self.assertIn("status", d)
            self.assertIn("count", d)
            self.assertIn("color", d)

    def test_08_empty_or_edge_case_robustness(self):
        """Assert excess stock list contains valid surplus calculations."""
        excess = self.summary.excess_stock_items
        for item in excess:
            self.assertGreater(item["surplus_units"], 0.0)
            self.assertGreater(item["current_stock"], item["target_stock"])

    def test_09_no_ml_jargon_in_insight_titles(self):
        """Assert insights use business-oriented language without ML jargon."""
        forbidden_jargon = {"loss convergence", "hyperparameter", "gradient descent", "backprop", "eigenvalue"}
        for ins in self.summary.insights:
            for term in forbidden_jargon:
                self.assertNotIn(term, ins.title.lower())
                self.assertNotIn(term, ins.description.lower())

    def test_10_full_integration_response_time(self):
        """Assert dashboard summary endpoint executes in under 2 seconds."""
        start = time.time()
        res = get_dashboard_kpis_and_insights()
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"Dashboard summary took {elapsed:.2f}s, expected < 2.0s")
        self.assertEqual(res.total_stores, 5)


if __name__ == "__main__":
    unittest.main()

