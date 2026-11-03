/**
 * DemandForecast.jsx — Milestone 8: Retail Demand Forecasting Page
 *
 * Provides store and product level daily demand forecasting:
 *   1. Store and product dropdown selection
 *   2. Horizon selection (7, 14, 30 days)
 *   3. Model selection (Linear Regression recommended winner vs Random Forest)
 *   4. Summary metrics (Total demand, Daily average, Peak day)
 *   5. Seamless historical actuals + future forecast time-series line chart
 *   6. Daily breakdown table
 *   7. Direct bridge to Milestone 9 Inventory Simulation
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart as LineChartIcon,
  TrendingUp,
  Calendar,
  Package,
  Store,
  Layers,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

import StatCard from '../components/StatCard';
import {
  getForecastOptions,
  generateForecast,
} from '../services/api';

const fmt = (n) =>
  n == null ? '—' : Number(n).toLocaleString('en-IN', { maximumFractionDigits: 1 });

// ─── Custom Tooltip for Forecast Chart ───────────────────────────────────────

const ForecastTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const historical = payload.find((p) => p.dataKey === 'actual_sales')?.value;
    const forecast = payload.find((p) => p.dataKey === 'predicted_demand')?.value;

    return (
      <div className="p-3 bg-slate-900/95 border border-slate-750 rounded-xl shadow-xl text-xs space-y-1.5 backdrop-blur-md">
        <p className="font-semibold text-white border-b border-slate-800 pb-1 mb-1">
          Date: {label}
        </p>
        {historical != null && (
          <div className="flex items-center justify-between gap-4 text-emerald-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block" />
              Recorded Actual Sales:
            </span>
            <span className="font-bold">{fmt(historical)} units</span>
          </div>
        )}
        {forecast != null && (
          <div className="flex items-center justify-between gap-4 text-indigo-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 inline-block" />
              Forecasted Demand:
            </span>
            <span className="font-bold">{fmt(forecast)} units</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

// ─── Main Component ──────────────────────────────────────────────────────────

const DemandForecast = ({ setActiveTab, onBridgeToInventory }) => {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  // Catalogue options
  const [options, setOptions] = useState(null);
  const [selectedStore, setSelectedStore] = useState('S001');
  const [selectedProduct, setSelectedProduct] = useState('P0001');
  const [horizon, setHorizon] = useState(7);
  const [selectedModel, setSelectedModel] = useState('linear_regression');

  // Forecast results
  const [forecastResult, setForecastResult] = useState(null);

  // ── Load options on mount ──
  useEffect(() => {
    const fetchOptions = async () => {
      setLoading(true);
      setError(null);
      try {
        const opts = await getForecastOptions();
        setOptions(opts);
        if (opts.stores.length > 0) setSelectedStore(opts.stores[0]);
        if (opts.products.length > 0) setSelectedProduct(opts.products[0]);

        // Auto-generate default 7-day forecast for the first store and product
        if (opts.stores.length > 0 && opts.products.length > 0) {
          try {
            const initialFc = await generateForecast({
              store_id: opts.stores[0],
              product_id: opts.products[0],
              horizon_days: 7,
              model_key: 'linear_regression',
            });
            setForecastResult(initialFc);
          } catch (fcErr) {
            console.warn('Initial forecast auto-generation skipped:', fcErr);
          }
        }
      } catch (err) {
        setError(
          err?.response?.data?.detail ||
          'Could not load catalogue options. Please ensure a dataset is uploaded and models are trained.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, []);

  // ── Generate forecast handler ──
  const handleGenerateForecast = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await generateForecast({
        store_id: selectedStore,
        product_id: selectedProduct,
        horizon_days: horizon,
        model_key: selectedModel,
      });
      setForecastResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate demand forecast.');
    } finally {
      setGenerating(false);
    }
  };

  // ── Prepare chart data combining history and future ──
  const chartData = [];
  if (forecastResult) {
    // 1. Add historical points
    forecastResult.historical_series.forEach((pt) => {
      chartData.push({
        date: pt.date,
        actual_sales: pt.actual_sales,
        predicted_demand: null,
      });
    });

    // 2. Add forecast points
    forecastResult.forecast_series.forEach((pt, idx) => {
      // Connect first forecast point to last historical point visually
      if (idx === 0 && forecastResult.historical_series.length > 0) {
        const lastHist = forecastResult.historical_series[forecastResult.historical_series.length - 1];
        chartData.push({
          date: pt.date,
          actual_sales: null,
          predicted_demand: pt.predicted_demand,
        });
      } else {
        chartData.push({
          date: pt.date,
          actual_sales: null,
          predicted_demand: pt.predicted_demand,
        });
      }
    });
  }

  // Calculate cumulative demand for table
  let cumulative = 0;
  const tableRows = forecastResult
    ? forecastResult.forecast_series.map((p) => {
        cumulative += p.predicted_demand;
        return {
          ...p,
          cumulative_demand: Math.round(cumulative * 10) / 10,
        };
      })
    : [];

  // Selected item category
  const selectedItemMeta = options?.catalogue?.find(
    (item) => item.store_id === selectedStore && item.product_id === selectedProduct
  );

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-3 text-slate-400">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-400" />
        <p className="text-sm">Loading forecasting workspace…</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <TrendingUp className="w-6 h-6 text-indigo-400" />
            Demand Forecast
          </h2>
          <p className="text-sm text-slate-400">
            Predict expected daily sales for any store and product using verified machine learning models.
          </p>
        </div>

        {forecastResult && (
          <button
            onClick={() => onBridgeToInventory && onBridgeToInventory(forecastResult)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-linear-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-xs font-bold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <span>Simulate Inventory for this Forecast</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Control Bar ── */}
      <div className="p-6 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Store Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Store className="w-3.5 h-3.5 text-indigo-400" />
              Store Location
            </label>
            <select
              value={selectedStore}
              onChange={(e) => setSelectedStore(e.target.value)}
              className="w-full bg-slate-900 border border-slate-750 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {options?.stores?.map((s) => (
                <option key={s} value={s}>
                  Store {s}
                </option>
              ))}
            </select>
          </div>

          {/* Product Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Package className="w-3.5 h-3.5 text-indigo-400" />
              Product SKU
            </label>
            <select
              value={selectedProduct}
              onChange={(e) => setSelectedProduct(e.target.value)}
              className="w-full bg-slate-900 border border-slate-750 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {options?.products?.map((p) => (
                <option key={p} value={p}>
                  Product {p}
                </option>
              ))}
            </select>
          </div>

          {/* Horizon Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              Forecast Horizon
            </label>
            <div className="grid grid-cols-3 gap-1.5">
              {[7, 14, 30].map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => setHorizon(h)}
                  className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                    horizon === h
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-850 border border-slate-750'
                  }`}
                >
                  {h} Days
                </button>
              ))}
            </div>
          </div>

          {/* Model Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Prediction Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-slate-900 border border-slate-750 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="linear_regression">
                Linear Regression (Best Performer)
              </option>
              <option value="random_forest">
                Random Forest Regressor
              </option>
            </select>
          </div>
        </div>

        {/* Action Button & Metadata Strip */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800/80 flex-wrap gap-4">
          <div className="flex items-center gap-3 text-xs text-slate-400">
            {selectedItemMeta?.category && (
              <span className="px-2.5 py-1 rounded-md bg-slate-850 text-slate-300 border border-slate-750">
                Category: <strong>{selectedItemMeta.category}</strong>
              </span>
            )}
            {selectedItemMeta?.latest_inventory != null && (
              <span className="px-2.5 py-1 rounded-md bg-slate-850 text-slate-300 border border-slate-750">
                Current Stock on Record: <strong>{fmt(selectedItemMeta.latest_inventory)} units</strong>
              </span>
            )}
          </div>

          <button
            onClick={handleGenerateForecast}
            disabled={generating}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50 cursor-pointer"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating Forecast…</span>
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4" />
                <span>Generate Forecast</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Forecast Results Content ── */}
      {forecastResult && (
        <div className="space-y-8">
          {/* Summary Stat Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Expected Demand"
              value={`${fmt(forecastResult.total_forecasted_demand)} units`}
              subtitle={`Next ${forecastResult.horizon_days} days aggregate demand`}
              icon={TrendingUp}
              color="indigo"
            />
            <StatCard
              title="Average Daily Demand"
              value={`${fmt(forecastResult.avg_daily_demand)} units/day`}
              subtitle="Projected daily sales velocity"
              icon={Calendar}
              color="emerald"
            />
            <StatCard
              title="Peak Demand Day"
              value={`${fmt(forecastResult.peak_demand)} units`}
              subtitle={`Expected on ${forecastResult.peak_demand_date}`}
              icon={Sparkles}
              color="amber"
            />
            <StatCard
              title="Forecasting Horizon"
              value={`${forecastResult.horizon_days} Days`}
              subtitle={`${forecastResult.forecast_start_date} → ${forecastResult.forecast_end_date}`}
              icon={LineChartIcon}
              color="cyan"
            />
          </div>

          {/* Combined History + Forecast Visualizer Chart */}
          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <LineChartIcon className="w-4 h-4 text-emerald-400" />
                  Demand Trend: Past Actuals vs. Future Forecast
                </h4>
                <p className="text-xs text-slate-400">
                  Last 14 days of recorded sales transitioning into the {forecastResult.horizon_days}-day future demand forecast
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-3 h-0.5 bg-emerald-400 inline-block" />
                  Historical Recorded Sales
                </span>
                <span className="flex items-center gap-1.5 text-indigo-400">
                  <span className="w-3 h-0.5 border-t-2 border-dashed border-indigo-400 inline-block" />
                  Future Predicted Demand
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 15, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(str) => {
                      const parts = str.split('-');
                      return `${parts[1]}/${parts[2]}`;
                    }}
                    minTickGap={20}
                  />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    domain={['auto', 'auto']}
                    tickFormatter={(v) => `${v}`}
                  />
                  <Tooltip content={<ForecastTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="actual_sales"
                    name="Recorded Sales"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: '#10b981' }}
                    activeDot={{ r: 5 }}
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted_demand"
                    name="Predicted Demand"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    dot={{ r: 3, fill: '#6366f1' }}
                    activeDot={{ r: 5 }}
                    connectNulls={true}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[11px] text-slate-500 text-center">
              *Historical sales represent real recorded store transactions. Future predictions use recursive feature updates based on the {forecastResult.model_name}.
            </p>
          </div>

          {/* Daily Forecast Breakdown Table */}
          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-indigo-400" />
                  Daily Forecast Schedule
                </h4>
                <p className="text-xs text-slate-400">
                  Day-by-day expected customer purchases for Store {forecastResult.store_id}, Product {forecastResult.product_id}
                </p>
              </div>

              <span className="text-xs px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                Model: {forecastResult.model_name}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                    <th className="py-2.5 px-3">Day</th>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Day of Week</th>
                    <th className="py-2.5 px-3">Forecast Demand</th>
                    <th className="py-2.5 px-3">Cumulative Demand</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 text-slate-300">
                  {tableRows.map((row) => (
                    <tr key={row.day_index} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-3 px-3 font-semibold text-white">Day {row.day_index}</td>
                      <td className="py-3 px-3">{row.date}</td>
                      <td className="py-3 px-3 font-medium text-slate-300">
                        {row.day_of_week}
                        {row.is_weekend && (
                          <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            Weekend
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-bold text-indigo-300">
                        {fmt(row.predicted_demand)} units
                      </td>
                      <td className="py-3 px-3 text-slate-400">
                        {fmt(row.cumulative_demand)} units
                      </td>
                      <td className="py-3 px-3">
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          Ready for Simulation
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Seamless Bridge Card */}
            <div className="p-4 rounded-xl bg-linear-to-r from-indigo-950/40 to-cyan-950/40 border border-indigo-500/30 flex items-center justify-between flex-wrap gap-4 mt-2">
              <div className="space-y-0.5">
                <p className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  Ready to test your stock availability?
                </p>
                <p className="text-xs text-slate-400">
                  Proceed to Inventory Simulation to check if your starting stock can fulfill this demand of {fmt(forecastResult.total_forecasted_demand)} units without stockouts.
                </p>
              </div>

              <button
                onClick={() => onBridgeToInventory && onBridgeToInventory(forecastResult)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
              >
                <span>Simulate Inventory</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DemandForecast;
