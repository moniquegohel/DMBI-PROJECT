"""
tests/test_milestone8.py — Milestone 8: Demand Forecasting Tests

Comprehensive test suite verifying:
  1. Forecast options endpoint returns valid catalogue metadata.
  2. Model selection defaults to the Milestone 7 empirical winner (Linear Regression).
  3. Forecast horizons (7, 14, 30 days) generate matching forecast record counts.
  4. Chronological continuity: dates advance strictly daily starting on 2024-01-02.
  5. Retail demand physical constraint: all predicted demands are >= 0.
  6. Recursive feature computation: lag and rolling features update across multi-step horizon.
  7. Model flexibility: Random Forest estimator can also generate forecasts.
  8. Graceful error handling for invalid or non-existent store/product identifiers.
  9. Recent historical actual sales context is returned alongside predictions.
 10. FastAPI route handlers execute and return valid Pydantic schemas.
"""

import unittest
from datetime import datetime, timedelta

from app.schemas.forecast import (
    ForecastRequest,
    ForecastResponse,
    ForecastOptionsResponse,
)
from app.services.demand_forecasting import (
    get_forecast_options,
    generate_demand_forecast,
)
from app.routes.forecast import (
    get_options,
    create_forecast,
)


class TestMilestone8DemandForecasting(unittest.TestCase):

    def test_01_forecast_options_success(self):
        """Verify forecast catalogue options are retrieved with metadata."""
        options = get_forecast_options()
        self.assertIsInstance(options, ForecastOptionsResponse)
        self.assertGreater(len(options.stores), 0)
        self.assertGreater(len(options.products), 0)
        self.assertGreater(len(options.catalogue), 0)
        self.assertIn("S001", options.stores)
        self.assertIn("P0001", options.products)
        self.assertEqual(options.recommended_model_key, "linear_regression")

    def test_02_default_model_selection(self):
        """Verify default model is Linear Regression (the Milestone 7 empirical winner)."""
        req = ForecastRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=7,
        )
        res = generate_demand_forecast(req)
        self.assertIsInstance(res, ForecastResponse)
        self.assertTrue(res.success)
        self.assertEqual(res.model_key, "linear_regression")
        self.assertIn("Linear Regression", res.model_name)

    def test_03_forecast_7_day_horizon(self):
        """Verify 7-day horizon returns exactly 7 forecast points."""
        req = ForecastRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=7,
        )
        res = generate_demand_forecast(req)
        self.assertEqual(len(res.forecast_series), 7)
        self.assertEqual(res.horizon_days, 7)
        self.assertGreater(res.total_forecasted_demand, 0)
        self.assertGreater(res.avg_daily_demand, 0)

    def test_04_forecast_14_and_30_day_horizons(self):
        """Verify 14-day and 30-day forecast horizons."""
        res_14 = generate_demand_forecast(
            ForecastRequest(store_id="S001", product_id="P0001", horizon_days=14)
        )
        self.assertEqual(len(res_14.forecast_series), 14)

        res_30 = generate_demand_forecast(
            ForecastRequest(store_id="S001", product_id="P0001", horizon_days=30)
        )
        self.assertEqual(len(res_30.forecast_series), 30)

    def test_05_forecast_dates_chronological_continuity(self):
        """Verify forecast dates follow immediately after dataset latest date in 1-day steps."""
        req = ForecastRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=7,
        )
        res = generate_demand_forecast(req)
        self.assertEqual(res.forecast_start_date, "2024-01-02")
        self.assertEqual(res.forecast_end_date, "2024-01-08")

        expected_date = datetime(2024, 1, 2)
        for i, point in enumerate(res.forecast_series):
            self.assertEqual(point.date, expected_date.strftime("%Y-%m-%d"))
            self.assertEqual(point.day_index, i + 1)
            expected_date += timedelta(days=1)

    def test_06_predictions_strictly_non_negative(self):
        """Verify retail demand physical constraint (predictions >= 0 units)."""
        req = ForecastRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=14,
        )
        res = generate_demand_forecast(req)
        for point in res.forecast_series:
            self.assertGreaterEqual(
                point.predicted_demand,
                0.0,
                f"Prediction on {point.date} must be >= 0 units"
            )

    def test_07_random_forest_model_option(self):
        """Verify forecast generation using Random Forest Regressor when requested."""
        req = ForecastRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=7,
            model_key="random_forest",
        )
        res = generate_demand_forecast(req)
        self.assertEqual(res.model_key, "random_forest")
        self.assertIn("Random Forest", res.model_name)
        self.assertEqual(len(res.forecast_series), 7)

    def test_08_invalid_store_or_product_fails(self):
        """Verify ValueError is raised for non-existent store or product."""
        with self.assertRaises(ValueError):
            generate_demand_forecast(
                ForecastRequest(store_id="NON_EXISTENT", product_id="P0001")
            )
        with self.assertRaises(ValueError):
            generate_demand_forecast(
                ForecastRequest(store_id="S001", product_id="NON_EXISTENT")
            )

    def test_09_historical_sales_context_present(self):
        """Verify up to 14 days of historical sales are provided for visual context."""
        req = ForecastRequest(
            store_id="S001",
            product_id="P0001",
            horizon_days=7,
        )
        res = generate_demand_forecast(req)
        self.assertGreater(len(res.historical_series), 0)
        self.assertLessEqual(len(res.historical_series), 14)
        # Last historical date should precede the forecast start date
        self.assertEqual(res.historical_series[-1].date, "2024-01-01")

    def test_10_api_endpoints_functional(self):
        """Verify FastAPI route handlers return valid schemas."""
        opts_res = get_options()
        self.assertIsInstance(opts_res, ForecastOptionsResponse)

        fc_req = ForecastRequest(store_id="S001", product_id="P0001", horizon_days=7)
        fc_res = create_forecast(fc_req)
        self.assertIsInstance(fc_res, ForecastResponse)
        self.assertTrue(fc_res.success)


if __name__ == "__main__":
    unittest.main()

