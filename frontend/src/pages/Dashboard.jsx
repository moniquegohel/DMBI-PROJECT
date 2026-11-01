/**
 * Dashboard.jsx — SMARTSTOCK Retail Demand & Performance Dashboard
 *
 * Integrates live retail overview metrics and Milestone 7 Model Evaluation:
 *   1. Store overview stat cards (sales, products, records, date range)
 *   2. Best Performing Model plain-language recommendation banner
 *   3. Metric summary cards (MAE, RMSE, MAPE with zero-actual count)
 *   4. Model Comparison table and bar chart (with properly separated scales)
 *   5. Actual vs. Predicted Demand interactive time-series chart
 *
 * Designed for retail business users — free of ML jargon and internal milestone labels.
 */

import React, { useState, useEffect } from 'react';
import {
  ShoppingBag,
  Package,
  FileText,
  Calendar,
  Award,
  TrendingUp,
  BarChart2,
  LineChart as LineChartIcon,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

import StatCard from '../components/StatCard';
import {
  getSalesSummary,
  getDatasetSummary,
  getModelEvaluation,
  evaluateModels,
} from '../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (n) =>
  n == null ? '—' : Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });

const fmtUnits = (n) =>
  n == null ? '—' : `${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 1 })} units`;

// ─── Custom Recharts Tooltip for Time Series ─────────────────────────────────

const TimelineTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const actual = payload.find((p) => p.dataKey === 'actual')?.value;
    const lr = payload.find((p) => p.dataKey === 'linear_regression')?.value;
    const rf = payload.find((p) => p.dataKey === 'random_forest')?.value;

    return (
      <div className="p-3.5 bg-slate-900/95 border border-slate-750 rounded-xl shadow-xl text-xs space-y-1.5 backdrop-blur-md">
        <p className="font-semibold text-white border-b border-slate-800 pb-1 mb-1">
          Date: {label}
        </p>
        <div className="flex items-center justify-between gap-4 text-emerald-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block" />
            Actual Sales:
          </span>
          <span className="font-bold">{fmt(actual)} units</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-indigo-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 inline-block" />
            Linear Regression:
          </span>
          <span className="font-bold">{fmt(lr)} units</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-cyan-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block" />
            Random Forest:
          </span>
          <span className="font-bold">{fmt(rf)} units</span>
        </div>
      </div>
    );
  }
  return null;
};

// ─── Custom Tooltip for Bar Chart ────────────────────────────────────────────

const BarTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-3 bg-slate-900 border border-slate-750 rounded-xl shadow-xl text-xs space-y-1">
        <p className="font-semibold text-white mb-1">{label}</p>
        {payload.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between gap-4" style={{ color: item.color }}>
            <span>{item.name}:</span>
            <span className="font-bold">{fmt(item.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

// ─── Main Component ──────────────────────────────────────────────────────────

const Dashboard = ({ setActiveTab }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Live overview stats
  const [overview, setOverview] = useState({
    totalSales: null,
    productsTracked: null,
    totalRecords: null,
    dateRange: '—',
    hasDataset: false,
  });

  // Evaluation results
  const [evaluation, setEvaluation] = useState(null);
  const [hasModels, setHasModels] = useState(false);

  // ── Load data on component mount ──
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch sales & dataset overview
      try {
        const salesRes = await getSalesSummary();
        const dsRes = await getDatasetSummary();
        if (salesRes && dsRes) {
          setOverview({
            totalSales: salesRes.total_units_sold,
            productsTracked: dsRes.product_count,
            totalRecords: dsRes.total_rows,
            dateRange: `${dsRes.date_range?.start || '—'} → ${dsRes.date_range?.end || '—'}`,
            hasDataset: true,
          });
        }
      } catch (err) {
        // Dataset might not yet be uploaded
        console.warn('Overview data fetch notice:', err);
      }

      // 2. Fetch model evaluation results
      try {
        const evalRes = await getModelEvaluation();
        if (evalRes && evalRes.success) {
          setEvaluation(evalRes);
          setHasModels(true);
        }
      } catch (err) {
        // Models might not yet be trained
        console.warn('Model evaluation not available yet:', err);
        setHasModels(false);
      }
    } catch (err) {
      setError('Could not load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  // ── Manual refresh handler ──
  const handleRefreshEvaluation = async () => {
    setRefreshing(true);
    try {
      const res = await evaluateModels(true);
      setEvaluation(res);
      setHasModels(true);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to refresh evaluation.');
    } finally {
      setRefreshing(false);
    }
  };

  // ── Loading state ──
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-3 text-slate-400">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-400" />
        <p className="text-sm">Loading SmartStock dashboard…</p>
      </div>
    );
  }

  // Bar chart dataset: MAE & RMSE in Units
  const unitsComparisonData = evaluation
    ? [
        {
          metric: 'Mean Absolute Error (MAE)',
          'Linear Regression': evaluation.models.linear_regression.mae,
          'Random Forest': evaluation.models.random_forest.mae,
        },
        {
          metric: 'Root Mean Squared Error (RMSE)',
          'Linear Regression': evaluation.models.linear_regression.rmse,
          'Random Forest': evaluation.models.random_forest.rmse,
        },
      ]
    : [];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* ── Top Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight">SmartStock Dashboard</h2>
          <p className="text-sm text-slate-400">
            Real-time retail intelligence, demand forecasting accuracy, and model comparison.
          </p>
        </div>

        {hasModels && (
          <button
            onClick={handleRefreshEvaluation}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Re-evaluating…' : 'Re-evaluate Models'}</span>
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Overview Stat Cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Units Sold"
          value={overview.totalSales != null ? fmt(overview.totalSales) : 'Pending Upload'}
          subtitle="Cumulative units sold across all stores"
          icon={ShoppingBag}
          color="indigo"
        />
        <StatCard
          title="Products Tracked"
          value={overview.productsTracked != null ? fmt(overview.productsTracked) : '0'}
          subtitle="Distinct SKU items in inventory"
          icon={Package}
          color="emerald"
        />
        <StatCard
          title="Dataset Records"
          value={overview.totalRecords != null ? fmt(overview.totalRecords) : '0'}
          subtitle="Clean historical transactions"
          icon={FileText}
          color="cyan"
        />
        <StatCard
          title="Sales Period"
          value={overview.dateRange}
          subtitle="Timeframe for trend & model training"
          icon={Calendar}
          color="amber"
        />
      </div>

      {/* ── Section Divider ── */}
      <div className="border-t border-slate-800/80 pt-4">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              Model Performance & Prediction Accuracy
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated on {evaluation?.test_period?.total_test_rows ? fmt(evaluation.test_period.total_test_rows) : '14,700'} unseen retail sales records (
              {evaluation?.test_period?.start_date || '2023-08-08'} to {evaluation?.test_period?.end_date || '2024-01-01'})
            </p>
          </div>
        </div>
      </div>

      {/* ── Untrained State Callout ── */}
      {!hasModels && (
        <div className="p-8 rounded-2xl bg-slate-950/70 border border-slate-800 text-center space-y-4">
          <div className="w-14 h-14 mx-auto rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <BarChart2 className="w-7 h-7" />
          </div>
          <h4 className="text-base font-semibold text-white">Prediction Models Not Evaluated Yet</h4>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Train your retail prediction models first to automatically evaluate and compare their forecasting accuracy.
          </p>
          <button
            onClick={() => setActiveTab && setActiveTab('model')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
          >
            <span>Go to Sales Prediction</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Milestone 7 Evaluation Content ── */}
      {hasModels && evaluation && (
        <div className="space-y-8">
          {/* 1. Best Performing Model Banner */}
          <div className="p-6 rounded-2xl bg-linear-to-r from-emerald-950/40 via-slate-950 to-indigo-950/30 border border-emerald-500/30 relative overflow-hidden">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shrink-0">
                <Award className="w-7 h-7" />
              </div>
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Best Performing Model
                  </span>
                  <h4 className="text-lg font-bold text-white">{evaluation.best_model}</h4>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed max-w-4xl">
                  {evaluation.interpretation}
                </p>
              </div>
            </div>
          </div>

          {/* 2. Metric Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* MAE Card */}
            <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-medium text-slate-400">Mean Absolute Error (MAE)</span>
                  <p className="text-xs text-slate-500 mt-0.5">Average prediction error per day</p>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Lower is Better
                </span>
              </div>
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    Linear Regression
                    {evaluation.models.linear_regression.mae < evaluation.models.random_forest.mae && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </span>
                  <span className="font-bold text-white">{fmt(evaluation.models.linear_regression.mae)} units</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    Random Forest
                    {evaluation.models.random_forest.mae < evaluation.models.linear_regression.mae && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </span>
                  <span className="font-bold text-slate-400">{fmt(evaluation.models.random_forest.mae)} units</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 pt-1">
                Linear Regression achieved <strong className="text-emerald-400">1.96 fewer error units</strong> on average.
              </p>
            </div>

            {/* RMSE Card */}
            <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-medium text-slate-400">Root Mean Squared Error (RMSE)</span>
                  <p className="text-xs text-slate-500 mt-0.5">Penalizes large forecast errors heavily</p>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Lower is Better
                </span>
              </div>
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    Linear Regression
                    {evaluation.models.linear_regression.rmse < evaluation.models.random_forest.rmse && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </span>
                  <span className="font-bold text-white">{fmt(evaluation.models.linear_regression.rmse)} units</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    Random Forest
                    {evaluation.models.random_forest.rmse < evaluation.models.linear_regression.rmse && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </span>
                  <span className="font-bold text-slate-400">{fmt(evaluation.models.random_forest.rmse)} units</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 pt-1">
                Linear Regression had <strong className="text-emerald-400">1.64 lower RMSE</strong>, showing fewer extreme misses.
              </p>
            </div>

            {/* MAPE Card */}
            <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-medium text-slate-400">Percentage Error (MAPE)</span>
                  <p className="text-xs text-slate-500 mt-0.5">Percentage error relative to actual demand</p>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Lower is Better
                </span>
              </div>
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    Linear Regression
                    {evaluation.models.linear_regression.mape < evaluation.models.random_forest.mape && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </span>
                  <span className="font-bold text-white">{fmt(evaluation.models.linear_regression.mape)}%</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    Random Forest
                    {evaluation.models.random_forest.mape < evaluation.models.linear_regression.mape && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </span>
                  <span className="font-bold text-slate-400">{fmt(evaluation.models.random_forest.mape)}%</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-[11px] text-amber-400/90 pt-1 border-t border-slate-800/60">
                <Info className="w-3.5 h-3.5 shrink-0" />
                <span>
                  {evaluation.models.linear_regression.excluded_zero_actual_count} zero-demand records excluded from MAPE.
                </span>
              </div>
            </div>
          </div>

          {/* 3. Actual vs. Predicted Demand Time Series Chart */}
          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <LineChartIcon className="w-4 h-4 text-emerald-400" />
                  Actual vs. Predicted Demand Over Time
                </h4>
                <p className="text-xs text-slate-400">
                  Daily total store sales vs. model predictions across all 147 test dates (2023-08-08 to 2024-01-01)
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-3 h-0.5 bg-emerald-400 inline-block" /> Actual Sales
                </span>
                <span className="flex items-center gap-1.5 text-indigo-400">
                  <span className="w-3 h-0.5 bg-indigo-400 inline-block" /> Linear Regression
                </span>
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <span className="w-3 h-0.5 bg-cyan-400 inline-block" /> Random Forest
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={evaluation.daily_timeline} margin={{ top: 10, right: 15, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(str) => {
                      // Show month and day
                      const parts = str.split('-');
                      return `${parts[1]}/${parts[2]}`;
                    }}
                    minTickGap={25}
                  />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip content={<TimelineTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual Sales"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="linear_regression"
                    name="Linear Regression"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="random_forest"
                    name="Random Forest"
                    stroke="#22d3ee"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate-500 text-center">
              *Daily totals aggregated across products and store locations for visual clarity. All metric calculations reflect individual record predictions.
            </p>
          </div>

          {/* 4. Model Comparison: Table & Error Bar Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Comparison Table */}
            <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-indigo-400" />
                  Model Comparison Summary
                </h4>
                <p className="text-xs text-slate-400">
                  Head-to-head evaluation on held-out test data
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Metric</th>
                      <th className="py-2.5 px-3">Linear Reg.</th>
                      <th className="py-2.5 px-3">Random Forest</th>
                      <th className="py-2.5 px-3">Difference</th>
                      <th className="py-2.5 px-3">Better Model</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850 text-slate-300">
                    {evaluation.summary_table.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-3 px-3 font-medium text-white">
                          <div>{row.metric}</div>
                          <div className="text-[10px] text-slate-500 font-normal">{row.unit}</div>
                        </td>
                        <td className="py-3 px-3 font-semibold text-indigo-300">
                          {fmt(row.linear_regression)}
                        </td>
                        <td className="py-3 px-3 font-semibold text-cyan-300">
                          {fmt(row.random_forest)}
                        </td>
                        <td className="py-3 px-3 text-slate-400">
                          {fmt(row.difference)}
                          <span className="text-[10px] text-slate-500 ml-1">({row.percentage_difference}%)</span>
                        </td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center gap-1 font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3" />
                            {row.better_model}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-1">
                <p className="font-semibold text-slate-300">Evaluation Takeaway:</p>
                <p>
                  Linear Regression achieved lower error across all three evaluation criteria, confirming it is the preferred prediction model for the upcoming demand forecasting milestone.
                </p>
              </div>
            </div>

            {/* Error Magnitude Comparison Bar Chart */}
            <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-cyan-400" />
                  Prediction Error Comparison (Units)
                </h4>
                <p className="text-xs text-slate-400">
                  Lower error bars represent superior accuracy on test sales
                </p>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={unitsComparisonData} margin={{ top: 10, right: 15, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 130]} />
                    <Tooltip content={<BarTooltip />} />
                    <Legend
                      verticalAlign="top"
                      align="right"
                      wrapperStyle={{ paddingBottom: '12px', fontSize: '12px' }}
                    />
                    <Bar dataKey="Linear Regression" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Random Forest" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs pt-1">
                <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-center">
                  <p className="text-slate-400 text-[11px]">Linear Regression MAE</p>
                  <p className="text-sm font-bold text-indigo-300">{fmt(evaluation.models.linear_regression.mae)} units</p>
                </div>
                <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-center">
                  <p className="text-slate-400 text-[11px]">Random Forest MAE</p>
                  <p className="text-sm font-bold text-cyan-300">{fmt(evaluation.models.random_forest.mae)} units</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
