"""
tests/test_milestone9.py — Milestone 9: Inventory Simulation Tests

Comprehensive test suite verifying:
  1. Recorded ending stock is retrieved accurately from the dataset on the cutoff date.
  2. Baseline simulation initializes with the recorded stock when starting stock is omitted.
  3. User override of starting inventory is supported and tracked.
  4. Physical non-negativity constraint: ending inventory is strictly >= 0 on every day.
  5. Fulfillment balance equation: demand fulfilled + unmet demand == forecasted demand.
  6. Stockout detection: flags stockout periods and identifies first stockout day.
  7. Replenishment logic: arriving inventory increases available stock on scheduled day.
  8. Inter-day carryover: beginning stock of day d+1 matches ending stock of day d.
  9. Service level mathematical accuracy: fulfilled / forecasted * 100.
 10. FastAPI route handlers execute and return valid Pydantic schemas.
"""

import unittest

from app.schemas.inventory import (
    InventorySimulationRequest,
    InventorySimulationResponse,
    StockInfoResponse,
)
from app.services.inventory_simulation import (
    get_stock_info,
    run_inventory_simulation,
)
from app.routes.inventory import (
    get_recorded_stock,
    simulate_inventory,
)


class TestMilestone9InventorySimulation(unittest.TestCase):

    def test_01_stock_info_retrieval(self):
        """Verify recorded stock level is returned for valid store and product."""
        info = get_stock_info(store_id="S001", product_id="P0001")
        self.assertIsInstance(info, StockInfoResponse)
        self.assertEqual(info.store_id, "S001")
        self.assertEqual(info.product_id, "P0001")
        self.assertGreater(info.recorded_stock, 0)
        self.assertEqual(info.recorded_date, "2024-01-01")

    def test_02_simulation_default_recorded_stock(self):
        """Verify simulation defaults to recorded stock when starting stock is omitted."""
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=7,
        )
        res = run_inventory_simulation(req)
        self.assertIsInstance(res, InventorySimulationResponse)
        self.assertTrue(res.success)
        self.assertFalse(res.is_user_provided_starting_stock)
        self.assertEqual(res.starting_inventory, res.recorded_ending_stock_from_data)

    def test_03_simulation_user_provided_stock(self):
        """Verify user can specify custom starting inventory."""
        custom_stock = 500.0
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=custom_stock,
            horizon_days=7,
        )
        res = run_inventory_simulation(req)
        self.assertTrue(res.is_user_provided_starting_stock)
        self.assertEqual(res.starting_inventory, custom_stock)

    def test_04_inventory_never_negative(self):
        """Verify physical stock constraint: ending inventory is strictly >= 0."""
        # Test with very low starting stock to force stockout
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=10.0,
            horizon_days=14,
        )
        res = run_inventory_simulation(req)
        for pt in res.simulation_points:
            self.assertGreaterEqual(
                pt.ending_inventory,
                0.0,
                f"Day {pt.day} ending inventory cannot be negative"
            )

    def test_05_fulfillment_balance_equation(self):
        """Verify demand fulfilled + unmet demand == forecasted demand on every single day."""
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=150.0,
            horizon_days=7,
        )
        res = run_inventory_simulation(req)
        for pt in res.simulation_points:
            expected_total = pt.demand_fulfilled + pt.unmet_demand
            self.assertAlmostEqual(
                expected_total,
                pt.forecasted_demand,
                places=1,
                msg=f"Day {pt.day} balance failed"
            )

    def test_06_stockout_detection(self):
        """Verify stockout periods are identified and first stockout day is tracked."""
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=50.0,
            horizon_days=7,
        )
        res = run_inventory_simulation(req)
        self.assertGreater(res.stockout_periods_count, 0)
        self.assertIsNotNone(res.first_stockout_day)
        self.assertIsNotNone(res.first_stockout_date)
        self.assertGreater(res.total_unmet_demand, 0)

    def test_07_replenishment_increases_available_stock(self):
        """Verify replenishment received on day k increases available stock."""
        replenish_qty = 300.0
        replenish_day = 3
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=50.0,
            horizon_days=7,
            replenishment_quantity=replenish_qty,
            replenishment_day=replenish_day,
        )
        res = run_inventory_simulation(req)
        day_3_pt = res.simulation_points[replenish_day - 1]
        self.assertEqual(day_3_pt.replenishment_received, replenish_qty)
        self.assertEqual(
            day_3_pt.available_stock,
            round(day_3_pt.beginning_inventory + replenish_qty, 1)
        )

    def test_08_interday_carryover_balance(self):
        """Verify ending stock of day d equals beginning stock of day d+1."""
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=250.0,
            horizon_days=7,
        )
        res = run_inventory_simulation(req)
        points = res.simulation_points
        for i in range(len(points) - 1):
            today_ending = points[i].ending_inventory
            next_beginning = points[i + 1].beginning_inventory
            self.assertEqual(
                today_ending,
                next_beginning,
                f"Day {i+1} ending stock must match Day {i+2} beginning stock"
            )

    def test_09_service_level_calculation(self):
        """Verify service level percentage equals (fulfilled / forecasted) * 100."""
        req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=200.0,
            horizon_days=7,
        )
        res = run_inventory_simulation(req)
        expected_sl = round((res.total_demand_fulfilled / res.total_forecasted_demand) * 100.0, 1)
        self.assertEqual(res.service_level_percentage, expected_sl)
        self.assertGreaterEqual(res.service_level_percentage, 0.0)
        self.assertLessEqual(res.service_level_percentage, 100.0)

    def test_10_api_endpoints_functional(self):
        """Verify FastAPI route handlers return valid schemas."""
        info_res = get_recorded_stock(store_id="S001", product_id="P0001")
        self.assertIsInstance(info_res, StockInfoResponse)

        sim_req = InventorySimulationRequest(
            store_id="S001",
            product_id="P0001",
            starting_inventory=200.0,
            horizon_days=7,
        )
        sim_res = simulate_inventory(sim_req)
        self.assertIsInstance(sim_res, InventorySimulationResponse)
        self.assertTrue(sim_res.success)


if __name__ == "__main__":
    unittest.main()

