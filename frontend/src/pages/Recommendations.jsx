import React, { useState, useEffect, useMemo } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Package,
  TrendingDown,
  Clock,
  Filter,
  Search,
  ArrowRight,
  Boxes,
  RefreshCw,
  SlidersHorizontal,
  Info,
} from 'lucide-react';
import { getInventoryRecommendations } from '../services/api';

const Recommendations = ({ setActiveTab, onBridgeToInventory }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedStore, setSelectedStore] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  // Configurable Parameters
  const [leadTimeDays, setLeadTimeDays] = useState(2);
  const [safetyBufferDays, setSafetyBufferDays] = useState(1);
  const [showConfig, setShowConfig] = useState(false);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getInventoryRecommendations({
        store_id: selectedStore !== 'All' ? selectedStore : undefined,
        category: selectedCategory !== 'All' ? selectedCategory : undefined,
        status: selectedStatus !== 'All' ? selectedStatus : undefined,
        lead_time_days: leadTimeDays,
        safety_buffer_days: safetyBufferDays,
        horizon_days: 7,
      });
      setData(res);
    } catch (err) {
      console.error('Failed to load inventory recommendations:', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to fetch recommendations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [selectedStore, selectedCategory, selectedStatus, leadTimeDays, safetyBufferDays]);

  // Client-side text search
  const filteredItems = useMemo(() => {
    if (!data?.items) return [];
    if (!searchQuery.trim()) return data.items;
    const q = searchQuery.toLowerCase();
    return data.items.filter(
      (item) =>
        item.product_id.toLowerCase().includes(q) ||
        item.store_id.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    );
  }, [data?.items, searchQuery]);

  const handleSimulateItem = (item) => {
    if (onBridgeToInventory) {
      onBridgeToInventory({
        store_id: item.store_id,
        product_id: item.product_id,
        current_stock: item.current_stock,
        forecasted_demand: item.forecasted_demand,
        suggested_reorder_qty: item.suggested_reorder_qty,
      });
    } else if (setActiveTab) {
      setActiveTab('inventory');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <Boxes className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Smart Inventory Recommendations
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Prescriptive replenishment plan driven by ML demand forecasts and current stock levels
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-2 px-3.5 py-2 text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span>Parameters {showConfig ? '▲' : '▼'}</span>
          </button>
          <button
            onClick={fetchRecommendations}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg shadow-sm transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Config Drawer */}
      {showConfig && (
        <div className="p-5 bg-slate-800/60 border border-slate-700 rounded-xl space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-indigo-400">
            <Info className="w-4 h-4" />
            <span>Configurable Recommendation Assumptions</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Supplier Lead Time (Days): <span className="text-white font-bold">{leadTimeDays} days</span>
              </label>
              <input
                type="range"
                min="1"
                max="14"
                value={leadTimeDays}
                onChange={(e) => setLeadTimeDays(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <p className="text-xs text-slate-400 mt-1">
                Expected days between placing a purchase order and receiving goods at store.
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Safety Stock Buffer (Days): <span className="text-white font-bold">{safetyBufferDays} day(s)</span>
              </label>
              <input
                type="range"
                min="0"
                max="7"
                value={safetyBufferDays}
                onChange={(e) => setSafetyBufferDays(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <p className="text-xs text-slate-400 mt-1">
                Buffer days of demand held to protect against unexpected sales surges.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary KPI Cards */}
      {data?.summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Restock Soon */}
          <div className="p-5 bg-slate-800/50 border border-rose-500/30 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">
                Restock Soon
              </span>
              <AlertTriangle className="w-5 h-5 text-rose-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {data.summary.restock_soon_count}
              </span>
              <span className="text-xs text-rose-400 font-medium">items</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Stock at or below Reorder Point
            </p>
          </div>

          {/* Stock Available */}
          <div className="p-5 bg-slate-800/50 border border-emerald-500/30 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Stock Available
              </span>
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {data.summary.stock_available_count}
              </span>
              <span className="text-xs text-emerald-400 font-medium">items</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Healthy inventory coverage
            </p>
          </div>

          {/* Excess Stock */}
          <div className="p-5 bg-slate-800/50 border border-amber-500/30 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                Excess Stock
              </span>
              <TrendingDown className="w-5 h-5 text-amber-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {data.summary.excess_stock_count}
              </span>
              <span className="text-xs text-amber-400 font-medium">items</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Stock exceeds 1.5x target demand
            </p>
          </div>

          {/* Suggested Reorder Units */}
          <div className="p-5 bg-slate-800/50 border border-indigo-500/30 rounded-2xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                Total Reorder Units
              </span>
              <Package className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {Number(data.summary.total_reorder_units).toLocaleString('en-IN')}
              </span>
              <span className="text-xs text-indigo-400 font-medium">units</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Recommended replenishment volume
            </p>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 bg-slate-800/40 border border-slate-750 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Pills */}
          <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-slate-700/80 text-xs">
            {['All', 'Restock Soon', 'Stock Available', 'Excess Stock'].map((status) => (
              <button
                key={status}
                onClick={() => setSelectedStatus(status)}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  selectedStatus === status
                    ? status === 'Restock Soon'
                      ? 'bg-rose-500/20 text-rose-300 font-semibold'
                      : status === 'Excess Stock'
                      ? 'bg-amber-500/20 text-amber-300 font-semibold'
                      : status === 'Stock Available'
                      ? 'bg-emerald-500/20 text-emerald-300 font-semibold'
                      : 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {status}
              </button>
            ))}
          </div>

          {/* Store Selector */}
          <select
            value={selectedStore}
            onChange={(e) => setSelectedStore(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="All">All Stores (5 Locations)</option>
            {data?.stores?.map((s) => (
              <option key={s} value={s}>
                Store {s}
              </option>
            ))}
          </select>

          {/* Category Selector */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-indigo-500"
          >
            <option value="All">All Categories</option>
            {data?.categories?.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Search Input */}
        <div className="relative min-w-[220px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search SKU or Store..."
            className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg pl-9 pr-3 py-2 focus:ring-1 focus:ring-indigo-500 placeholder-slate-500"
          />
        </div>
      </div>

      {/* Main Recommendations Table */}
      <div className="bg-slate-800/40 border border-slate-750 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-750 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-white">Recommendations Ledger</span>
            <span className="px-2 py-0.5 text-xs bg-slate-700/60 text-slate-300 rounded-full font-medium">
              Showing {filteredItems.length} of {data?.summary?.total_products_evaluated || 0}
            </span>
          </div>
          <span className="text-xs text-slate-400">
            Planning Horizon: 7 Days • Lead Time: {leadTimeDays}d • Safety Buffer: {safetyBufferDays}d
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/70 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-750">
              <tr>
                <th className="px-4 py-3">Product / SKU</th>
                <th className="px-4 py-3">Store</th>
                <th className="px-4 py-3 text-right">Current Stock</th>
                <th className="px-4 py-3 text-right">7-Day Demand</th>
                <th className="px-4 py-3 text-right">Days of Supply</th>
                <th className="px-4 py-3 text-right">Reorder Point</th>
                <th className="px-4 py-3 text-right font-semibold text-indigo-300">Suggested Order</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
                    Calculating multi-store inventory recommendations...
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-400">
                    No products match the selected criteria.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => {
                  const isRestock = item.status === 'Restock Soon';
                  const isExcess = item.status === 'Excess Stock';
                  const isAvailable = item.status === 'Stock Available';

                  return (
                    <tr
                      key={`${item.store_id}-${item.product_id}`}
                      className="hover:bg-slate-750/30 transition-colors"
                    >
                      <td className="px-4 py-3.5">
                        <div className="font-semibold text-white">{item.product_id}</div>
                        <div className="text-[11px] text-slate-400">{item.category}</div>
                      </td>
                      <td className="px-4 py-3.5 font-medium text-slate-300">
                        {item.store_id}
                      </td>
                      <td className="px-4 py-3.5 text-right font-medium text-slate-200">
                        {Number(item.current_stock).toLocaleString('en-IN')} units
                      </td>
                      <td className="px-4 py-3.5 text-right font-medium text-slate-200">
                        {Number(item.forecasted_demand).toLocaleString('en-IN', { maximumFractionDigits: 1 })} units
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span
                          className={`font-semibold ${
                            item.days_of_supply < 3
                              ? 'text-rose-400 font-bold'
                              : item.days_of_supply > 15
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          {item.days_of_supply > 900 ? '—' : `${item.days_of_supply.toFixed(1)} days`}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-right text-slate-400 font-mono">
                        {Number(item.reorder_point).toFixed(0)}
                      </td>
                      <td className="px-4 py-3.5 text-right font-bold text-indigo-300 font-mono">
                        {item.suggested_reorder_qty > 0 ? (
                          <span className="text-rose-400 font-bold">
                            +{Number(item.suggested_reorder_qty).toFixed(0)} units
                          </span>
                        ) : (
                          <span className="text-slate-500 font-normal">0 units</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-center">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                            isRestock
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              : isExcess
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                              : isAvailable
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : 'bg-slate-700/30 text-slate-400 border-slate-600'
                          }`}
                        >
                          {isRestock && <AlertTriangle className="w-3 h-3" />}
                          {isAvailable && <CheckCircle2 className="w-3 h-3" />}
                          {isExcess && <TrendingDown className="w-3 h-3" />}
                          {item.status}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-center">
                        <button
                          onClick={() => handleSimulateItem(item)}
                          title="Simulate replenishment in Inventory Simulation"
                          className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-medium hover:underline"
                        >
                          <span>Simulate</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Recommendations;

