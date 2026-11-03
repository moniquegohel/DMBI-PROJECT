/**
 * Inventory.jsx — Milestone 9: Inventory Simulation Page
 *
 * Simulates physical inventory depletion, customer demand fulfillment,
 * unmet demand, and stockout occurrences over the forecast horizon:
 *   1. Store & product selector (auto-synced from Demand Forecast if bridged)
 *   2. Starting stock input (defaults to actual recorded stock from dataset on 2024-01-01)
 *   3. Optional replenishment inputs (quantity and arrival day)
 *   4. Summary metric cards (Starting Stock, Expected Demand, Fulfilled, Unmet, Ending Stock, Service Level)
 *   5. Visualizations:
 *      - Chart A: Projected Inventory Over Time (Area chart with 0-unit stockout boundary)
 *      - Chart B: Available Stock vs. Forecasted Demand (Bar chart)
 *   6. Daily Inventory Balance Ledger Table
 */

import React, { useState, useEffect } from 'react';
import {
  Boxes,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Package,
  Store,
  RefreshCw,
  PlusCircle,
  BarChart2,
  Layers,
  ArrowRight,
  AlertCircle,
  Loader2,
  Info,
  ShieldAlert,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

import StatCard from '../components/StatCard';
import {
  getForecastOptions,
  simulateInventory,
  getInventoryStockInfo,
} from '../services/api';

const fmt = (n) =>
  n == null ? '—' : Number(n).toLocaleString('en-IN', { maximumFractionDigits: 1 });

// ─── Custom Tooltips ─────────────────────────────────────────────────────────

const InventoryTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const ending = payload.find((p) => p.dataKey === 'ending_inventory')?.value;
    const available = payload.find((p) => p.dataKey === 'available_stock')?.value;
    const unmet = payload.find((p) => p.dataKey === 'unmet_demand')?.value;

    return (
      <div className="p-3 bg-slate-900/95 border border-slate-750 rounded-xl shadow-xl text-xs space-y-1.5 backdrop-blur-md">
        <p className="font-semibold text-white border-b border-slate-800 pb-1 mb-1">
          {label}
        </p>
        <div className="flex justify-between gap-4 text-cyan-400">
          <span>Available Stock:</span>
          <span className="font-bold">{fmt(available)} units</span>
        </div>
        <div className="flex justify-between gap-4 text-emerald-400">
          <span>Ending Stock:</span>
          <span className="font-bold">{fmt(ending)} units</span>
        </div>
        {unmet > 0 && (
          <div className="flex justify-between gap-4 text-rose-400 font-bold border-t border-slate-800 pt-1">
            <span>Unmet Demand:</span>
            <span>{fmt(unmet)} units (Stockout!)</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

const DemandStockTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-3 bg-slate-900/95 border border-slate-750 rounded-xl shadow-xl text-xs space-y-1 backdrop-blur-md">
        <p className="font-semibold text-white mb-1">{label}</p>
        {payload.map((item, idx) => (
          <div key={idx} className="flex justify-between gap-4" style={{ color: item.color }}>
            <span>{item.name}:</span>
            <span className="font-bold">{fmt(item.value)} units</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

// ─── Main Component ──────────────────────────────────────────────────────────

const Inventory = ({ setActiveTab, initialContext }) => {
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState(null);

  // Catalogue
  const [options, setOptions] = useState(null);
  const [selectedStore, setSelectedStore] = useState('S001');
  const [selectedProduct, setSelectedProduct] = useState('P0001');
  const [horizon, setHorizon] = useState(7);

  // Inventory Inputs
  const [recordedStock, setRecordedStock] = useState(null);
  const [userStock, setUserStock] = useState('');
  const [useCustomStock, setUseCustomStock] = useState(false);

  // Optional Replenishment
  const [showReplenish, setShowReplenish] = useState(false);
  const [replenishQty, setReplenishQty] = useState('');
  const [replenishDay, setReplenishDay] = useState('2');

  // Simulation Results
  const [simResult, setSimResult] = useState(null);

  // ── Load options & initial stock ──
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setError(null);
      try {
        const opts = await getForecastOptions();
        setOptions(opts);

        let initialStore = opts.stores[0] || 'S001';
        let initialProduct = opts.products[0] || 'P0001';
        let initialHorizon = 7;

        // If bridged from Demand Forecast page with pre-selected context
        if (initialContext) {
          if (initialContext.store_id) initialStore = initialContext.store_id;
          if (initialContext.product_id) initialProduct = initialContext.product_id;
          if (initialContext.horizon_days) initialHorizon = initialContext.horizon_days;
        }

        setSelectedStore(initialStore);
        setSelectedProduct(initialProduct);
        setHorizon(initialHorizon);

        // Fetch stock info for this store and product
        try {
          const sInfo = await getInventoryStockInfo(initialStore, initialProduct);
          setRecordedStock(sInfo.recorded_stock);
        } catch (sErr) {
          console.warn('Stock info fetch error:', sErr);
        }

        // Run baseline simulation
        try {
          const sim = await simulateInventory({
            store_id: initialStore,
            product_id: initialProduct,
            horizon_days: initialHorizon,
            starting_inventory: null, // use recorded stock
          });
          setSimResult(sim);
        } catch (simErr) {
          console.warn('Initial simulation auto-run error:', simErr);
        }
      } catch (err) {
        setError(
          err?.response?.data?.detail ||
          'Failed to load inventory workspace. Please ensure a dataset is uploaded.'
        );
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [initialContext]);

  // ── When store or product changes, update recorded stock ──
  const handleStoreOrProductChange = async (newStore, newProd) => {
    setSelectedStore(newStore);
    setSelectedProduct(newProd);
    try {
      const sInfo = await getInventoryStockInfo(newStore, newProd);
      setRecordedStock(sInfo.recorded_stock);
      if (!useCustomStock) {
        setUserStock('');
      }
    } catch (err) {
      console.warn('Stock info fetch failed for pair:', err);
    }
  };

  // ── Run Simulation handler ──
  const handleRunSimulation = async () => {
    setSimulating(true);
    setError(null);
    try {
      const startStockParam = useCustomStock && userStock !== ''
        ? parseFloat(userStock)
        : null;

      const replenishQtyParam = showReplenish && replenishQty !== ''
        ? parseFloat(replenishQty)
        : 0.0;

      const replenishDayParam = showReplenish && replenishDay !== ''
        ? parseInt(replenishDay, 10)
        : null;

      const res = await simulateInventory({
        store_id: selectedStore,
        product_id: selectedProduct,
        starting_inventory: startStockParam,
        horizon_days: horizon,
        replenishment_quantity: replenishQtyParam,
        replenishment_day: replenishDayParam,
      });
      setSimResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to execute inventory simulation.');
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-3 text-slate-400">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-400" />
        <p className="text-sm">Loading inventory simulation workspace…</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <Boxes className="w-6 h-6 text-indigo-400" />
            Inventory Simulation
          </h2>
          <p className="text-sm text-slate-400">
            Simulate future stock levels, customer fulfillment, and potential stockouts based on demand forecasts.
          </p>
        </div>

        <button
          onClick={() => setActiveTab && setActiveTab('forecast')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-750 transition-colors"
        >
          <span>Adjust Demand Forecast</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Simulation Parameters Control Bar ── */}
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
              onChange={(e) => handleStoreOrProductChange(e.target.value, selectedProduct)}
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
              onChange={(e) => handleStoreOrProductChange(selectedStore, e.target.value)}
              className="w-full bg-slate-900 border border-slate-750 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {options?.products?.map((p) => (
                <option key={p} value={p}>
                  Product {p}
                </option>
              ))}
            </select>
          </div>

          {/* Simulation Horizon */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              Simulation Horizon
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

          {/* Starting Stock Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Boxes className="w-3.5 h-3.5 text-indigo-400" />
                Starting Inventory
              </label>
              <button
                type="button"
                onClick={() => setUseCustomStock(!useCustomStock)}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 underline"
              >
                {useCustomStock ? 'Use Recorded Stock' : 'Customize'}
              </button>
            </div>

            {useCustomStock ? (
              <input
                type="number"
                min="0"
                step="1"
                placeholder="Enter starting units"
                value={userStock}
                onChange={(e) => setUserStock(e.target.value)}
                className="w-full bg-slate-900 border border-indigo-500/50 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-400"
              />
            ) : (
              <div className="flex items-center justify-between bg-slate-900/90 border border-slate-750 text-white text-sm rounded-lg px-3 py-2">
                <span className="font-bold text-emerald-400">{fmt(recordedStock)} units</span>
                <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  Recorded
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Optional Replenishment Drawer Toggle */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowReplenish(!showReplenish)}
              className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>{showReplenish ? 'Hide Replenishment Settings' : '+ Add Scheduled Replenishment'}</span>
            </button>
            <span className="text-xs text-slate-500">
              (Simulate arriving stock orders to prevent stockouts)
            </span>
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={simulating}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-950/30 disabled:opacity-50 cursor-pointer"
          >
            {simulating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Simulating…</span>
              </>
            ) : (
              <>
                <Boxes className="w-4 h-4" />
                <span>Run Inventory Simulation</span>
              </>
            )}
          </button>
        </div>

        {/* Optional Replenishment Inputs */}
        {showReplenish && (
          <div className="p-4 rounded-xl bg-slate-900/80 border border-indigo-500/20 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">
                Replenishment Quantity (Units)
              </label>
              <input
                type="number"
                min="1"
                placeholder="e.g. 200"
                value={replenishQty}
                onChange={(e) => setReplenishQty(e.target.value)}
                className="w-full bg-slate-950 border border-slate-750 text-white text-sm rounded-lg px-3 py-2"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">
                Arrival Day Index
              </label>
              <select
                value={replenishDay}
                onChange={(e) => setReplenishDay(e.target.value)}
                className="w-full bg-slate-950 border border-slate-750 text-white text-sm rounded-lg px-3 py-2"
              >
                {Array.from({ length: horizon }, (_, i) => i + 1).map((d) => (
                  <option key={d} value={d}>
                    Day {d}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* ── Simulation Results ── */}
      {simResult && (
        <div className="space-y-8">
          {/* Plain-Language Business Takeaway Banner */}
          <div
            className={`p-6 rounded-2xl border relative overflow-hidden ${
              simResult.total_unmet_demand > 0
                ? 'bg-rose-950/20 border-rose-500/30'
                : 'bg-emerald-950/20 border-emerald-500/30'
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`p-3 rounded-xl border shrink-0 ${
                  simResult.total_unmet_demand > 0
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                }`}
              >
                {simResult.total_unmet_demand > 0 ? (
                  <AlertTriangle className="w-7 h-7" />
                ) : (
                  <CheckCircle2 className="w-7 h-7" />
                )}
              </div>
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <span
                    className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                      simResult.total_unmet_demand > 0
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    }`}
                  >
                    {simResult.total_unmet_demand > 0 ? 'Stockout Warning' : 'Healthy Inventory'}
                  </span>
                  <h4 className="text-lg font-bold text-white">
                    {simResult.total_unmet_demand > 0
                      ? `Stockout Expected on Day ${simResult.first_stockout_day}`
                      : 'All Customer Demand Satisfied'}
                  </h4>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed max-w-4xl">
                  {simResult.simulation_summary_text}
                </p>
              </div>
            </div>
          </div>

          {/* Metric Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Starting Inventory"
              value={`${fmt(simResult.starting_inventory)} units`}
              subtitle={
                simResult.is_user_provided_starting_stock
                  ? 'User custom starting stock'
                  : 'Recorded stock on 2024-01-01'
              }
              icon={Boxes}
              color="indigo"
            />
            <StatCard
              title="Expected Demand"
              value={`${fmt(simResult.total_forecasted_demand)} units`}
              subtitle={`Over ${simResult.horizon_days} simulation days`}
              icon={BarChart2}
              color="cyan"
            />
            <StatCard
              title="Demand Fulfilled"
              value={`${fmt(simResult.total_demand_fulfilled)} units`}
              subtitle={`${simResult.service_level_percentage}% Service Level`}
              icon={CheckCircle2}
              color="emerald"
            />
            <StatCard
              title="Unmet Demand"
              value={`${fmt(simResult.total_unmet_demand)} units`}
              subtitle={
                simResult.stockout_periods_count > 0
                  ? `${simResult.stockout_periods_count} stockout days`
                  : 'Zero stockout periods'
              }
              icon={AlertTriangle}
              color={simResult.total_unmet_demand > 0 ? 'rose' : 'emerald'}
            />
          </div>

          {/* Visualizations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart A: Inventory Over Time */}
            <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <h4 className="text-base font-bold text-white flex items-center gap-2">
                    <TrendingDown className="w-4 h-4 text-cyan-400" />
                    Simulated Inventory Over Time
                  </h4>
                  <p className="text-xs text-slate-400">
                    Day-by-day ending physical stock trajectory
                  </p>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Ending: {fmt(simResult.ending_inventory)} units
                </span>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={simResult.simulation_points} margin={{ top: 10, right: 15, left: 0, bottom: 10 }}>
                    <defs>
                      <linearGradient id="invGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(str) => {
                        const parts = str.split('-');
                        return `${parts[1]}/${parts[2]}`;
                      }}
                    />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 'auto']} />
                    <Tooltip content={<InventoryTooltip />} />
                    <ReferenceLine y={0} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: 'Stockout (0)', fill: '#f43f5e', fontSize: 10 }} />
                    <Area
                      type="monotone"
                      dataKey="ending_inventory"
                      name="Ending Inventory"
                      stroke="#22d3ee"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#invGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart B: Available Stock vs Forecasted Demand */}
            <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <h4 className="text-base font-bold text-white flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-indigo-400" />
                    Available Stock vs. Expected Demand
                  </h4>
                  <p className="text-xs text-slate-400">
                    Compare daily supply against customer demand
                  </p>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {simResult.service_level_percentage}% Fulfilled
                </span>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={simResult.simulation_points} margin={{ top: 10, right: 15, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(str) => {
                        const parts = str.split('-');
                        return `${parts[1]}/${parts[2]}`;
                      }}
                    />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip content={<DemandStockTooltip />} />
                    <Legend verticalAlign="top" align="right" wrapperStyle={{ paddingBottom: '10px', fontSize: '12px' }} />
                    <Bar dataKey="available_stock" name="Available Stock" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="forecasted_demand" name="Expected Demand" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Daily Simulation Balance Ledger Table */}
          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-indigo-400" />
                  Daily Inventory Ledger
                </h4>
                <p className="text-xs text-slate-400">
                  Detailed day-by-day fulfillment calculations and physical stock balances
                </p>
              </div>

              <span className="text-xs text-slate-400">
                Formula: Available = Beginning + Replenishment | Ending = Available − Fulfilled
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                    <th className="py-2.5 px-3">Day</th>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Beginning</th>
                    <th className="py-2.5 px-3">Replenishment</th>
                    <th className="py-2.5 px-3">Available</th>
                    <th className="py-2.5 px-3">Demand</th>
                    <th className="py-2.5 px-3">Fulfilled</th>
                    <th className="py-2.5 px-3">Unmet</th>
                    <th className="py-2.5 px-3">Ending Stock</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 text-slate-300">
                  {simResult.simulation_points.map((pt) => (
                    <tr
                      key={pt.day}
                      className={`hover:bg-slate-900/40 transition-colors ${
                        pt.is_stockout ? 'bg-rose-950/10' : ''
                      }`}
                    >
                      <td className="py-3 px-3 font-semibold text-white">Day {pt.day}</td>
                      <td className="py-3 px-3">{pt.date}</td>
                      <td className="py-3 px-3 text-slate-300">{fmt(pt.beginning_inventory)}</td>
                      <td className="py-3 px-3 font-medium text-cyan-300">
                        {pt.replenishment_received > 0 ? `+${fmt(pt.replenishment_received)}` : '—'}
                      </td>
                      <td className="py-3 px-3 font-semibold text-white">{fmt(pt.available_stock)}</td>
                      <td className="py-3 px-3 font-semibold text-indigo-300">{fmt(pt.forecasted_demand)}</td>
                      <td className="py-3 px-3 text-emerald-400 font-semibold">{fmt(pt.demand_fulfilled)}</td>
                      <td className="py-3 px-3 font-bold text-rose-400">
                        {pt.unmet_demand > 0 ? fmt(pt.unmet_demand) : '0'}
                      </td>
                      <td className="py-3 px-3 font-bold text-white">{fmt(pt.ending_inventory)}</td>
                      <td className="py-3 px-3">
                        {pt.is_stockout ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                            <ShieldAlert className="w-3 h-3" />
                            Stockout
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3" />
                            In Stock
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
