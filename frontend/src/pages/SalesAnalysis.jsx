/**
 * SalesAnalysis.jsx — Milestone 4: Historical Sales Analysis Page
 *
 * Displays:
 *  1. Summary stat cards (total, avg, min, max units sold)
 *  2. Monthly sales trend line chart
 *  3. Product-wise sales bar chart
 *  4. Category and store breakdowns
 *
 * All data is fetched live from the backend analysis APIs.
 * No hardcoded demo values are used.
 */

import React, { useState, useEffect } from 'react';
import {
  ShoppingBag,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Package,
  Store,
  BarChart2,
  Upload,
  AlertCircle,
  Loader2,
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
  Cell,
} from 'recharts';

import StatCard from '../components/StatCard';
import {
  getSalesSummary,
  getMonthlySales,
  getProductSales,
  getCategorySales,
  getStoreSales,
} from '../services/api';

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Format large numbers with commas */
const fmt = (n) =>
  n === undefined || n === null
    ? '—'
    : Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });

/** Colour palette for bar charts */
const BAR_COLOURS = [
  '#6366f1', '#22d3ee', '#10b981', '#f59e0b',
  '#f43f5e', '#8b5cf6', '#3b82f6', '#14b8a6',
  '#f97316', '#ec4899', '#a3e635', '#fb923c',
  '#c084fc', '#34d399', '#38bdf8', '#facc15',
  '#f87171', '#4ade80', '#e879f9', '#67e8f9',
];

// ─── Sub-components ──────────────────────────────────────────────────────────

/** Full-page loading spinner */
const LoadingSpinner = ({ message = 'Loading…' }) => (
  <div className="flex flex-col items-center justify-center py-24 gap-4 text-slate-400">
    <Loader2 className="w-10 h-10 animate-spin text-indigo-400" />
    <p className="text-sm">{message}</p>
  </div>
);

/** Error alert banner */
const ErrorBanner = ({ message }) => (
  <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
    <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
    <span>{message}</span>
  </div>
);

/** Section wrapper with title */
const Section = ({ title, subtitle, children }) => (
  <div className="space-y-4">
    <div>
      <h4 className="text-base font-semibold text-white">{title}</h4>
      {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
    </div>
    {children}
  </div>
);

/** Chart container card */
const ChartCard = ({ children }) => (
  <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800">
    {children}
  </div>
);

/** Custom tooltip for Recharts — dark-themed */
const DarkTooltip = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-300 font-medium mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }}>
          {entry.name}: <span className="font-bold">{Number(entry.value).toLocaleString('en-IN')}</span>
        </p>
      ))}
    </div>
  );
};

// ─── Main Component ──────────────────────────────────────────────────────────

const SalesAnalysis = ({ setActiveTab }) => {
  // setActiveTab is passed from App.jsx to switch sidebar tabs programmatically

  // State for each API endpoint
  const [summary, setSummary] = useState(null);
  const [monthly, setMonthly] = useState([]);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [stores, setStores] = useState([]);

  // Loading / error tracking per section
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  // Whether a dataset is available at all
  const [noDataset, setNoDataset] = useState(false);

  // ── Fetch all analysis data on mount ────────────────────────────────────
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setErrors({});
      setNoDataset(false);

      try {
        // Fetch summary first so we can detect "no dataset" early
        const summaryData = await getSalesSummary();
        setSummary(summaryData);
      } catch (err) {
        const msg = err?.response?.data?.detail || err.message || 'Failed to load summary.';
        // 404 means no dataset has been uploaded yet
        if (err?.response?.status === 404) {
          setNoDataset(true);
          setLoading(false);
          return;
        }
        setErrors((prev) => ({ ...prev, summary: msg }));
      }

      // Fetch the remaining endpoints in parallel
      const [monthlyResult, productsResult, categoriesResult, storesResult] =
        await Promise.allSettled([
          getMonthlySales(),
          getProductSales(),
          getCategorySales(),
          getStoreSales(),
        ]);

      if (monthlyResult.status === 'fulfilled') {
        setMonthly(monthlyResult.value);
      } else {
        setErrors((prev) => ({
          ...prev,
          monthly:
            monthlyResult.reason?.response?.data?.detail ||
            monthlyResult.reason?.message ||
            'Failed to load monthly data.',
        }));
      }

      if (productsResult.status === 'fulfilled') {
        setProducts(productsResult.value);
      } else {
        setErrors((prev) => ({
          ...prev,
          products:
            productsResult.reason?.response?.data?.detail ||
            productsResult.reason?.message ||
            'Failed to load product data.',
        }));
      }

      if (categoriesResult.status === 'fulfilled') {
        setCategories(categoriesResult.value);
      } else {
        setErrors((prev) => ({
          ...prev,
          categories:
            categoriesResult.reason?.response?.data?.detail ||
            categoriesResult.reason?.message ||
            'Failed to load category data.',
        }));
      }

      if (storesResult.status === 'fulfilled') {
        setStores(storesResult.value);
      } else {
        setErrors((prev) => ({
          ...prev,
          stores:
            storesResult.reason?.response?.data?.detail ||
            storesResult.reason?.message ||
            'Failed to load store data.',
        }));
      }

      setLoading(false);
    };

    fetchAll();
  }, []);

  // ── No-dataset state ─────────────────────────────────────────────────────
  if (noDataset) {
    return (
      <div className="p-8 space-y-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-2">Historical Sales Analysis</h3>
          <p className="text-sm text-slate-400">
            Explore historical sales trends, monthly totals, and product performance breakdowns.
          </p>
        </div>

        <div className="p-10 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col items-center text-center gap-5">
          <div className="w-16 h-16 rounded-full bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Upload className="w-8 h-8" />
          </div>
          <div>
            <h4 className="text-lg font-semibold text-white mb-1">No Dataset Uploaded Yet</h4>
            <p className="text-sm text-slate-400 max-w-md">
              Upload and clean a retail sales CSV on the{' '}
              <strong className="text-indigo-400">Dataset Upload</strong> page to unlock all
              sales analysis charts and statistics.
            </p>
          </div>
          <button
            onClick={() => setActiveTab && setActiveTab('dataset')}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
          >
            Go to Dataset Upload
          </button>
        </div>
      </div>
    );
  }

  // ── Main loading state ───────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-white mb-2">Historical Sales Analysis</h3>
          <p className="text-sm text-slate-400">Loading analysis data…</p>
        </div>
        <LoadingSpinner message="Fetching sales analysis from the server…" />
      </div>
    );
  }

  // ── Render page ──────────────────────────────────────────────────────────
  return (
    <div className="p-8 space-y-10">

      {/* ── Page header ── */}
      <div>
        <h3 className="text-xl font-bold text-white mb-2">Historical Sales Analysis</h3>
        <p className="text-sm text-slate-400">
          Explore historical sales trends, monthly totals, and product performance breakdowns.
        </p>
      </div>

      {/* ── Summary error (top-level) ── */}
      {errors.summary && <ErrorBanner message={errors.summary} />}

      {/* ── 1. Summary stat cards ── */}
      {summary && (
        <Section
          title="Sales Overview"
          subtitle={`Analysed ${fmt(summary.total_records)} records`}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Units Sold"
              value={fmt(summary.total_units_sold)}
              subtitle="Sum across all records"
              icon={ShoppingBag}
              color="indigo"
            />
            <StatCard
              title="Avg Units per Record"
              value={fmt(summary.avg_units_sold_per_record)}
              subtitle="Mean per individual sales record"
              icon={TrendingUp}
              color="emerald"
            />
            <StatCard
              title="Max Units (Single Record)"
              value={fmt(summary.max_units_sold)}
              subtitle="Highest single-record volume"
              icon={ArrowUpRight}
              color="cyan"
            />
            <StatCard
              title="Min Units (Single Record)"
              value={fmt(summary.min_units_sold)}
              subtitle="Lowest single-record volume"
              icon={ArrowDownRight}
              color="amber"
            />
          </div>

          {/* Extra metadata row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-2">
            {summary.distinct_products !== undefined && (
              <StatCard
                title="Distinct Products"
                value={fmt(summary.distinct_products)}
                subtitle="Unique product identifiers"
                icon={Package}
                color="indigo"
              />
            )}
            {summary.distinct_stores !== undefined && (
              <StatCard
                title="Distinct Stores"
                value={fmt(summary.distinct_stores)}
                subtitle="Unique store identifiers"
                icon={Store}
                color="cyan"
              />
            )}
            {summary.distinct_dates !== undefined && (
              <StatCard
                title="Distinct Dates"
                value={fmt(summary.distinct_dates)}
                subtitle="Calendar dates in dataset"
                icon={BarChart2}
                color="emerald"
              />
            )}
          </div>
        </Section>
      )}

      {/* ── 2. Monthly Sales Trend ── */}
      <Section
        title="Monthly Sales Trend"
        subtitle="Total units sold aggregated by calendar month, in chronological order"
      >
        {errors.monthly ? (
          <ErrorBanner message={errors.monthly} />
        ) : monthly.length === 0 ? (
          <ChartCard>
            <p className="text-sm text-slate-400 text-center py-8">
              No monthly data available.
            </p>
          </ChartCard>
        ) : (
          <ChartCard>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart
                data={monthly}
                margin={{ top: 8, right: 24, bottom: 40, left: 16 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  interval={Math.max(0, Math.floor(monthly.length / 18) - 1)}
                  label={{
                    value: 'Month',
                    position: 'insideBottom',
                    offset: -28,
                    fill: '#64748b',
                    fontSize: 12,
                  }}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickFormatter={(v) => v.toLocaleString('en-IN')}
                  width={80}
                  label={{
                    value: 'Units Sold',
                    angle: -90,
                    position: 'insideLeft',
                    offset: 10,
                    fill: '#64748b',
                    fontSize: 12,
                  }}
                />
                <Tooltip content={<DarkTooltip />} />
                <Line
                  type="monotone"
                  dataKey="total_units_sold"
                  name="Units Sold"
                  stroke="#6366f1"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#6366f1' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}
      </Section>

      {/* ── 3. Product-wise Sales ── */}
      <Section
        title="Product-wise Sales"
        subtitle="Total units sold per product, sorted from highest to lowest"
      >
        {errors.products ? (
          <ErrorBanner message={errors.products} />
        ) : products.length === 0 ? (
          <ChartCard>
            <p className="text-sm text-slate-400 text-center py-8">No product data available.</p>
          </ChartCard>
        ) : (
          <ChartCard>
            <ResponsiveContainer width="100%" height={Math.max(320, products.length * 36)}>
              <BarChart
                data={products}
                layout="vertical"
                margin={{ top: 8, right: 24, bottom: 8, left: 100 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickFormatter={(v) => v.toLocaleString('en-IN')}
                  label={{
                    value: 'Units Sold',
                    position: 'insideBottom',
                    offset: -4,
                    fill: '#64748b',
                    fontSize: 12,
                  }}
                />
                <YAxis
                  type="category"
                  dataKey="product_id"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  width={90}
                />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="total_units_sold" name="Units Sold" radius={[0, 4, 4, 0]}>
                  {products.map((_, idx) => (
                    <Cell
                      key={idx}
                      fill={BAR_COLOURS[idx % BAR_COLOURS.length]}
                      fillOpacity={0.85}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Product table (compact) */}
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-xs text-slate-300">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="text-left py-2 pr-4 font-medium">Product</th>
                    <th className="text-left py-2 pr-4 font-medium">Category</th>
                    <th className="text-right py-2 font-medium">Units Sold</th>
                    <th className="text-right py-2 pl-4 font-medium">% Share</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p, i) => (
                    <tr
                      key={p.product_id}
                      className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors"
                    >
                      <td className="py-2 pr-4 font-medium text-white">{p.product_id}</td>
                      <td className="py-2 pr-4 text-slate-400">{p.category || '—'}</td>
                      <td className="py-2 text-right tabular-nums">
                        {Number(p.total_units_sold).toLocaleString('en-IN')}
                      </td>
                      <td className="py-2 pl-4 text-right tabular-nums text-slate-400">
                        {p.pct_share !== undefined ? `${Number(p.pct_share).toFixed(1)}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ChartCard>
        )}
      </Section>

      {/* ── 4. Category & Store breakdowns ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Category breakdown */}
        <Section
          title="Category Breakdown"
          subtitle="Total units sold per product category"
        >
          {errors.categories ? (
            <ErrorBanner message={errors.categories} />
          ) : categories.length === 0 ? (
            <ChartCard>
              <p className="text-sm text-slate-400 text-center py-8">No category data available.</p>
            </ChartCard>
          ) : (
            <ChartCard>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={categories}
                  margin={{ top: 8, right: 16, bottom: 40, left: 16 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="category"
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    angle={-30}
                    textAnchor="end"
                  />
                  <YAxis
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    tickFormatter={(v) => v.toLocaleString('en-IN')}
                    width={72}
                  />
                  <Tooltip content={<DarkTooltip />} />
                  <Bar dataKey="total_units_sold" name="Units Sold" radius={[4, 4, 0, 0]}>
                    {categories.map((_, idx) => (
                      <Cell key={idx} fill={BAR_COLOURS[idx % BAR_COLOURS.length]} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </Section>

        {/* Store breakdown */}
        <Section
          title="Store Breakdown"
          subtitle="Total units sold per store"
        >
          {errors.stores ? (
            <ErrorBanner message={errors.stores} />
          ) : stores.length === 0 ? (
            <ChartCard>
              <p className="text-sm text-slate-400 text-center py-8">No store data available.</p>
            </ChartCard>
          ) : (
            <ChartCard>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={stores}
                  margin={{ top: 8, right: 16, bottom: 40, left: 16 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="store_id"
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    angle={-30}
                    textAnchor="end"
                  />
                  <YAxis
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    tickFormatter={(v) => v.toLocaleString('en-IN')}
                    width={72}
                  />
                  <Tooltip content={<DarkTooltip />} />
                  <Bar dataKey="total_units_sold" name="Units Sold" radius={[4, 4, 0, 0]}>
                    {stores.map((_, idx) => (
                      <Cell key={idx} fill={BAR_COLOURS[(idx + 3) % BAR_COLOURS.length]} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </Section>

      </div>

    </div>
  );
};

export default SalesAnalysis;
