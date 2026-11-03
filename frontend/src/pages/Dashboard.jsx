/**
 * Dashboard.jsx — SMARTSTOCK Executive Retail Command Center (Milestones 10 & 11)
 *
 * Unified Business Intelligence Dashboard:
 * 1. Executive KPI Summary Cards (Products, Stores, Restock Needed, Stockout Risks, Excess Stock, Reorder Volume)
 * 2. Dynamic Business Insights Section (Plain-language retail explanations & recommended actions)
 * 3. Interactive Recharts Visualizations:
 *    - Inventory Health Breakdown (Donut Chart)
 *    - Top 5 Products by Forecasted Demand (Bar Chart)
 *    - Stock vs. Forecasted Demand Comparison (Grouped Bar Chart)
 *    - Store Replenishment Volume (Bar Chart)
 * 4. Empirical Model Performance Summary (Milestone 7 empirical results preserved)
 * 5. Quick Workflow Navigation Shortcuts
 */

import React, { useState, useEffect } from 'react';
import {
  Boxes,
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Package,
  Store,
  LineChart as LineChartIcon,
  ArrowRight,
  RefreshCw,
  Award,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  Zap,
  DollarSign,
  Truck,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

import { getDashboardSummary, getModelEvaluation } from '../services/api';

const fmt = (n) =>
  n == null ? '—' : Number(n).toLocaleString('en-IN', { maximumFractionDigits: 1 });

const Dashboard = ({ setActiveTab }) => {
  const [summary, setSummary] = useState(null);
  const [modelEval, setModelEval] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModelDetails, setShowModelDetails] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dashRes, evalRes] = await Promise.all([
        getDashboardSummary(),
        getModelEvaluation().catch(() => null),
      ]);
      setSummary(dashRes);
      setModelEval(evalRes);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to load executive dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
        <p className="text-slate-400 text-sm">Aggregating real-time retail intelligence...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Dashboard Offline</h2>
          <p className="text-sm text-slate-300">{error || 'Could not retrieve inventory intelligence.'}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-linear-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Boxes className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Retail Intelligence Command Center
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Executive inventory status, demand forecasts, and automated replenishment priorities
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-2 px-3.5 py-2 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync Live Data</span>
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-indigo-600/20 transition"
          >
            <span>View Restock Plan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 6 Executive KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Total Products */}
        <div className="p-4 bg-slate-800/40 border border-slate-750 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Products</span>
            <Package className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-white">{summary.total_products}</div>
          <p className="text-[11px] text-slate-400 mt-0.5">Active catalogue SKUs</p>
        </div>

        {/* Total Stores */}
        <div className="p-4 bg-slate-800/40 border border-slate-750 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Stores</span>
            <Store className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-white">{summary.total_stores}</div>
          <p className="text-[11px] text-slate-400 mt-0.5">Monitored retail sites</p>
        </div>

        {/* Requiring Restock */}
        <div className="p-4 bg-slate-800/40 border border-rose-500/30 rounded-xl bg-linear-to-b from-rose-500/5 to-transparent">
          <div className="flex items-center justify-between text-rose-400 text-xs font-semibold">
            <span>Restock Needed</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-rose-400">
            {summary.products_requiring_restock}
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">Stock &le; Reorder Point</p>
        </div>

        {/* Stockout Threat (< 3 days runway) */}
        <div className="p-4 bg-slate-800/40 border border-red-500/40 rounded-xl bg-linear-to-b from-red-600/10 to-transparent">
          <div className="flex items-center justify-between text-red-400 text-xs font-semibold">
            <span>Imminent Stockouts</span>
            <ShieldAlert className="w-4 h-4 text-red-400" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-red-400">
            {summary.products_at_risk_of_stockout}
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">&lt; 3 days of supply</p>
        </div>

        {/* Excess Stock */}
        <div className="p-4 bg-slate-800/40 border border-amber-500/30 rounded-xl bg-linear-to-b from-amber-500/5 to-transparent">
          <div className="flex items-center justify-between text-amber-400 text-xs font-semibold">
            <span>Excess Inventory</span>
            <TrendingDown className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-amber-400">
            {summary.products_with_excess_inventory}
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">&gt; 1.5x target stock</p>
        </div>

        {/* Total Reorder Volume */}
        <div className="p-4 bg-slate-800/40 border border-indigo-500/30 rounded-xl bg-linear-to-b from-indigo-500/5 to-transparent">
          <div className="flex items-center justify-between text-indigo-400 text-xs font-semibold">
            <span>Total Reorder</span>
            <Truck className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-indigo-300">
            {fmt(summary.total_suggested_reorder_volume)}
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">Suggested purchase units</p>
        </div>
      </div>

      {/* Dynamic Actionable Business Insights */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            Automated Business Insights & Operational Priorities
          </h2>
          <span className="text-xs text-slate-400">Data-driven explanations from latest forecast cycle</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {summary.insights?.map((insight) => {
            const isCritical = insight.severity === 'CRITICAL';
            const isWarning = insight.severity === 'WARNING';

            return (
              <div
                key={insight.id}
                className={`p-4 rounded-xl border backdrop-blur-xs flex flex-col justify-between space-y-3 transition ${
                  isCritical
                    ? 'bg-rose-500/5 border-rose-500/30 hover:border-rose-500/50'
                    : isWarning
                    ? 'bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50'
                    : 'bg-indigo-500/5 border-indigo-500/30 hover:border-indigo-500/50'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span
                      className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${
                        isCritical
                          ? 'bg-rose-500/20 text-rose-300'
                          : isWarning
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-indigo-500/20 text-indigo-300'
                      }`}
                    >
                      {insight.type.replace('_', ' ')}
                    </span>
                    {isCritical ? (
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                    ) : isWarning ? (
                      <DollarSign className="w-4 h-4 text-amber-400" />
                    ) : (
                      <TrendingUp className="w-4 h-4 text-indigo-400" />
                    )}
                  </div>
                  <h3 className="font-semibold text-sm text-white leading-snug">{insight.title}</h3>
                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">{insight.description}</p>
                </div>

                <div className="pt-2 border-t border-slate-700/40">
                  <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">Recommended Action:</span>
                  <p className="text-xs font-medium text-slate-200">{insight.recommended_action}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Inventory Health Distribution (Donut Chart) */}
        <div className="p-5 bg-slate-800/40 border border-slate-750 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Catalogue Inventory Health</h3>
              <p className="text-xs text-slate-400">Proportion of store-product series by stock status</p>
            </div>
            <span className="text-xs font-mono text-slate-400">100 Series Total</span>
          </div>

          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={summary.category_distribution}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                >
                  {summary.category_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-3 bg-slate-900 border border-slate-700 rounded-lg text-xs shadow-xl">
                          <p className="font-semibold text-white">{data.status}</p>
                          <p className="text-slate-300">{data.count} items ({data.percentage}%)</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend
                  formatter={(value) => <span className="text-xs text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Top 5 Highest Velocity SKUs */}
        <div className="p-5 bg-slate-800/40 border border-slate-750 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Top 5 Demand Velocity SKUs</h3>
              <p className="text-xs text-slate-400">Highest 7-day cumulative sales forecasted across stores</p>
            </div>
            <button
              onClick={() => setActiveTab('forecast')}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <span>Forecasts</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={summary.top_demand_products}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis
                  dataKey="product_id"
                  type="category"
                  stroke="#64748b"
                  tick={{ fontSize: 11, fill: '#e2e8f0' }}
                  width={60}
                />
                <Tooltip
                  formatter={(val, name) => [`${fmt(val)} units`, 'Forecasted Demand']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="forecasted_demand" fill="#6366f1" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Stockout Threats — Stock vs Demand */}
        <div className="p-5 bg-slate-800/40 border border-slate-750 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Stock vs. Anticipated Demand</h3>
              <p className="text-xs text-slate-400">Current available inventory compared with 7-day expected sales</p>
            </div>
            <span className="text-xs px-2 py-0.5 bg-rose-500/20 text-rose-300 rounded-md font-semibold">
              Restock Priority
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={summary.stockout_risks.slice(0, 5).map((x) => ({
                  name: `${x.store_id}/${x.product_id}`,
                  'Current Stock': x.current_stock,
                  '7-Day Demand': x.forecasted_demand,
                }))}
                margin={{ top: 10, right: 10, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend formatter={(val) => <span className="text-xs text-slate-300">{val}</span>} />
                <Bar dataKey="Current Stock" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="7-Day Demand" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Store-Wise Replenishment Volume */}
        <div className="p-5 bg-slate-800/40 border border-slate-750 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Regional Replenishment Demands</h3>
              <p className="text-xs text-slate-400">Total units required by each store location</p>
            </div>
            <button
              onClick={() => setActiveTab('recommendations')}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <span>View Table</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={summary.store_replenishment}
                margin={{ top: 10, right: 10, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="store_id" stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip
                  formatter={(val) => [`${fmt(val)} units`, 'Reorder Volume']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="total_reorder_units" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Model Performance Banner (Milestone 7 empirical results preserved) */}
      <div className="p-5 bg-slate-800/30 border border-slate-750 rounded-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white">
                  Empirical Model Foundation: Linear Regression Selected
                </h3>
                <span className="text-[10px] px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full font-semibold">
                  Evaluated on 14,700 Test Records
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated against Random Forest: Linear Regression achieved lower MAE (88.80 vs 90.76) and lower RMSE (108.24 vs 109.88).
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowModelDetails(!showModelDetails)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-750 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            <span>{showModelDetails ? 'Hide Metrics' : 'View Evaluation Metrics'}</span>
            {showModelDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showModelDetails && modelEval && (
          <div className="mt-4 pt-4 border-t border-slate-750 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-750">
              <span className="text-slate-400 font-medium">Mean Absolute Error (MAE):</span>
              <p className="text-white font-bold text-sm mt-1">
                {modelEval.models?.linear_regression?.mae?.toFixed(2)} units
              </p>
              <span className="text-[10px] text-emerald-400">Best generalization performance</span>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-750">
              <span className="text-slate-400 font-medium">Root Mean Squared Error (RMSE):</span>
              <p className="text-white font-bold text-sm mt-1">
                {modelEval.models?.linear_regression?.rmse?.toFixed(2)} units
              </p>
              <span className="text-[10px] text-emerald-400">Lowest penalty on extreme variances</span>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-750">
              <span className="text-slate-400 font-medium">Test Set Period:</span>
              <p className="text-white font-bold text-sm mt-1">
                {modelEval.test_period?.start_date} to {modelEval.test_period?.end_date}
              </p>
              <span className="text-[10px] text-slate-400">Chronological time-series split</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick Access Workflow Shortcuts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => setActiveTab('forecast')}
          className="p-4 bg-slate-800/40 hover:bg-slate-800 border border-slate-750 hover:border-indigo-500/40 rounded-xl text-left transition flex items-center justify-between group"
        >
          <div>
            <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <LineChartIcon className="w-4 h-4" />
              <span>Demand Forecast</span>
            </div>
            <p className="text-sm font-semibold text-white">Generate Daily Sales Forecasts</p>
            <p className="text-xs text-slate-400 mt-0.5">Explore 7, 14, and 30-day horizons per SKU</p>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition" />
        </button>

        <button
          onClick={() => setActiveTab('inventory')}
          className="p-4 bg-slate-800/40 hover:bg-slate-800 border border-slate-750 hover:border-cyan-500/40 rounded-xl text-left transition flex items-center justify-between group"
        >
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Boxes className="w-4 h-4" />
              <span>Inventory Simulation</span>
            </div>
            <p className="text-sm font-semibold text-white">Simulate Stock Depletion</p>
            <p className="text-xs text-slate-400 mt-0.5">Model delivery arrivals, stockouts & fill rate</p>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition" />
        </button>

        <button
          onClick={() => setActiveTab('recommendations')}
          className="p-4 bg-slate-800/40 hover:bg-slate-800 border border-slate-750 hover:border-emerald-500/40 rounded-xl text-left transition flex items-center justify-between group"
        >
          <div>
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Package className="w-4 h-4" />
              <span>Restock Plan</span>
            </div>
            <p className="text-sm font-semibold text-white">Smart Restock Quantities</p>
            <p className="text-xs text-slate-400 mt-0.5">Filter by store, status, and lead time</p>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition" />
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
