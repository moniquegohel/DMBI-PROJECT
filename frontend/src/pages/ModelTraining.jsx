/**
 * ModelTraining.jsx — Sales Prediction Page
 *
 * Shows users whether prediction models are ready and lets them
 * trigger or retrain them. All displayed status values come from
 * actual backend API responses — nothing is hardcoded.
 *
 * Internal implementation details (pipeline class names, artifact
 * filenames, milestone labels, preprocessing config) are kept in
 * the source code and backend only; they are not shown to the user.
 */

import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Play,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Upload,
  Info,
  TrendingUp,
  GitBranch,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import {
  generateFeatures,
  getFeaturesStatus,
  getFeaturesPreview,
  trainModels,
  getModelTrainingStatus,
} from '../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (n) =>
  n == null ? '—' : Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });

// ─── Small reusable banners ───────────────────────────────────────────────────

const ErrorBanner = ({ message }) => (
  <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
    <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
    <span>{message}</span>
  </div>
);

const SuccessBanner = ({ message }) => (
  <div className="flex items-start gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm">
    <CheckCircle2 className="w-5 h-5 mt-0.5 shrink-0" />
    <span>{message}</span>
  </div>
);

const InfoBanner = ({ message }) => (
  <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-sm">
    <Info className="w-5 h-5 mt-0.5 shrink-0" />
    <span>{message}</span>
  </div>
);

// ─── Status badge ─────────────────────────────────────────────────────────────

const StatusBadge = ({ ready }) =>
  ready ? (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
      <CheckCircle2 className="w-3.5 h-3.5" />
      Ready
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
      Not trained
    </span>
  );

// ─── Page-level status summary ────────────────────────────────────────────────

const PageStatus = ({ hasFeatures, hasModels, isTraining, trainingError }) => {
  if (isTraining) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm">
        <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        Training prediction models… this may take a minute.
      </div>
    );
  }
  if (trainingError) {
    return <ErrorBanner message="Training could not be completed. Check the error below and try again." />;
  }
  if (!hasFeatures) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm">
        <Info className="w-4 h-4 shrink-0" />
        Prepare your sales data first — click <strong className="ml-1">Prepare sales data</strong> below before training.
      </div>
    );
  }
  if (hasModels) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm">
        <CheckCircle2 className="w-4 h-4 shrink-0" />
        Prediction models are ready. You can retrain them at any time.
      </div>
    );
  }
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-800/60 border border-slate-700 text-slate-300 text-sm">
      <Info className="w-4 h-4 shrink-0" />
      No prediction models trained yet. Click <strong className="ml-1">Train models</strong> to get started.
    </div>
  );
};

// ─── Model card ───────────────────────────────────────────────────────────────

const ModelCard = ({ icon: Icon, iconColor, name, description, ready }) => (
  <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col gap-4">
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg border ${iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
        <h5 className="text-base font-semibold text-white">{name}</h5>
      </div>
      <StatusBadge ready={ready} />
    </div>
    <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────

const ModelTraining = ({ setActiveTab }) => {
  // Feature / data-prep state
  const [featuresResult, setFeaturesResult] = useState(null);
  const [generatingFeatures, setGeneratingFeatures] = useState(false);
  const [featuresError, setFeaturesError] = useState(null);

  // Model training state
  const [trainingResult, setTrainingResult] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingError, setTrainingError] = useState(null);

  // Page-level state
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState(null);
  const [noDataset, setNoDataset] = useState(false);

  // Optional details section (collapsed by default)
  const [showDetails, setShowDetails] = useState(false);

  // ── Load status on mount ────────────────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setPageError(null);
      try {
        const fStatus = await getFeaturesStatus();
        if (fStatus.has_ml_dataset) {
          try {
            const preview = await getFeaturesPreview();
            setFeaturesResult(preview);
          } catch (err) {
            console.warn('Feature preview fetch failed:', err);
          }
        }
        try {
          const mStatus = await getModelTrainingStatus();
          setTrainingStatus(mStatus);
        } catch (err) {
          console.warn('Model status fetch failed:', err);
        }
      } catch (err) {
        if (err?.response?.status === 404) {
          setNoDataset(true);
        } else {
          setPageError(err?.response?.data?.detail || err.message);
        }
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // ── Prepare sales data (feature engineering) ────────────────────────────────
  const handleGenerateFeatures = async () => {
    setGeneratingFeatures(true);
    setFeaturesError(null);
    setNoDataset(false);
    try {
      const res = await generateFeatures();
      setFeaturesResult(res);
    } catch (err) {
      if (err?.response?.status === 404) {
        setNoDataset(true);
      } else {
        setFeaturesError(err?.response?.data?.detail || err.message || 'Data preparation failed.');
      }
    } finally {
      setGeneratingFeatures(false);
    }
  };

  // ── Train models ────────────────────────────────────────────────────────────
  const handleTrainModels = async () => {
    setIsTraining(true);
    setTrainingError(null);
    try {
      const res = await trainModels();
      setTrainingResult(res);
      const statusRes = await getModelTrainingStatus();
      setTrainingStatus(statusRes);
    } catch (err) {
      setTrainingError(
        err?.response?.data?.detail || err.message || 'Model training failed.'
      );
    } finally {
      setIsTraining(false);
    }
  };

  // ── Derived state ───────────────────────────────────────────────────────────
  const hasFeatures = !!featuresResult;
  const hasModels = !!(trainingResult?.success || trainingStatus?.has_trained_models);
  const activeSplitInfo = trainingResult?.split_info || trainingStatus?.split_info;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="p-8 space-y-8 max-w-4xl">

      {/* ── Page header ── */}
      <div>
        <h3 className="text-xl font-bold text-white mb-1.5">Sales Prediction</h3>
        <p className="text-sm text-slate-400 max-w-xl">
          Prepare prediction models using your store's past sales data.
          Once trained, these models power future demand forecasts.
        </p>
      </div>

      {/* ── No dataset state ── */}
      {noDataset && (
        <div className="p-8 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col items-center text-center gap-4">
          <Upload className="w-10 h-10 text-indigo-400" />
          <div>
            <h4 className="text-base font-semibold text-white mb-1">No dataset uploaded</h4>
            <p className="text-sm text-slate-400 max-w-sm">
              Upload and clean a sales dataset first before preparing prediction models.
            </p>
          </div>
          <button
            onClick={() => setActiveTab && setActiveTab('dataset')}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
          >
            Go to Dataset
          </button>
        </div>
      )}

      {/* ── Initial loading ── */}
      {loading && (
        <div className="flex items-center gap-3 text-slate-400 text-sm py-8">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          Checking status…
        </div>
      )}

      {pageError && <ErrorBanner message={pageError} />}

      {!loading && !noDataset && (
        <>
          {/* ── Page-level status summary ── */}
          <PageStatus
            hasFeatures={hasFeatures}
            hasModels={hasModels}
            isTraining={isTraining}
            trainingError={trainingError}
          />

          {/* ── Step 1: Prepare sales data ── */}
          <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 space-y-4">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-sm font-semibold text-white">Step 1 — Prepare sales data</h4>
                  {hasFeatures && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Done
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">
                  Builds the prediction-ready version of your sales dataset from the cleaned data.
                  {hasFeatures && featuresResult?.output_rows && (
                    <span className="ml-1 text-slate-300">
                      {fmt(featuresResult.output_rows)} records prepared.
                    </span>
                  )}
                </p>
              </div>

              <button
                onClick={handleGenerateFeatures}
                disabled={generatingFeatures}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900 disabled:text-indigo-600 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors shrink-0"
              >
                {generatingFeatures ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Preparing…
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    {hasFeatures ? 'Re-prepare data' : 'Prepare sales data'}
                  </>
                )}
              </button>
            </div>

            {featuresError && <ErrorBanner message={featuresError} />}
          </div>

          {/* ── Step 2: Train prediction models ── */}
          <div className="space-y-5">
            <div className="flex items-start justify-between gap-4 flex-wrap pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-sm font-semibold text-white">Step 2 — Train prediction models</h4>
                </div>
                <p className="text-xs text-slate-400">
                  Trains two prediction methods on your historical sales data.
                  Uses older sales records for training and keeps recent data for accuracy checking.
                </p>
              </div>

              <button
                onClick={handleTrainModels}
                disabled={isTraining || !hasFeatures}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors shadow-lg shadow-emerald-950/30 shrink-0"
              >
                {isTraining ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Training…
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    {hasModels ? 'Retrain models' : 'Train models'}
                  </>
                )}
              </button>
            </div>

            {/* Feature data required warning */}
            {!hasFeatures && !isTraining && (
              <InfoBanner message="Complete Step 1 first — sales data needs to be prepared before models can be trained." />
            )}

            {/* Training errors */}
            {trainingError && <ErrorBanner message={trainingError} />}

            {/* Training success */}
            {trainingResult && !isTraining && !trainingError && (
              <SuccessBanner message="Both prediction models have been trained and saved successfully." />
            )}

            {/* Link to Dashboard for Model Evaluation */}
            {hasModels && !isTraining && (
              <div className="flex items-center justify-between p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Prediction models are trained and ready. View accuracy metrics and comparison on the Dashboard.</span>
                </div>
                <button
                  onClick={() => setActiveTab && setActiveTab('dashboard')}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors shrink-0"
                >
                  View on Dashboard
                </button>
              </div>
            )}

            {/* ── Model cards ── */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <ModelCard
                icon={TrendingUp}
                iconColor="bg-indigo-500/10 border-indigo-500/20 text-indigo-400"
                name="Trend-based model"
                description="Learns from straightforward patterns in past sales, such as day-of-week and seasonal trends. Fast and easy to interpret."
                ready={hasModels}
              />
              <ModelCard
                icon={GitBranch}
                iconColor="bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                name="Pattern-based model"
                description="Looks for more complex patterns across products, stores, and time periods. Better suited to varied or unpredictable sales behaviour."
                ready={hasModels}
              />
            </div>

            {/* ── Optional training details (collapsed) ── */}
            {hasModels && activeSplitInfo && (
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <button
                  onClick={() => setShowDetails((v) => !v)}
                  className="w-full flex items-center justify-between px-5 py-3.5 bg-slate-900/60 hover:bg-slate-800/50 text-sm text-slate-300 font-medium transition-colors"
                >
                  <span>Training information</span>
                  {showDetails ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </button>

                {showDetails && (
                  <div className="px-5 py-4 bg-slate-950/50 space-y-3 text-sm text-slate-300">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {activeSplitInfo.train_start_date && (
                        <div className="space-y-0.5">
                          <p className="text-xs text-slate-500">Training period</p>
                          <p className="font-medium text-white">
                            {activeSplitInfo.train_start_date} → {activeSplitInfo.train_end_date}
                          </p>
                        </div>
                      )}
                      {activeSplitInfo.holdout_start_date && (
                        <div className="space-y-0.5">
                          <p className="text-xs text-slate-500">Accuracy check period</p>
                          <p className="font-medium text-white">
                            {activeSplitInfo.holdout_start_date} → {activeSplitInfo.holdout_end_date}
                          </p>
                        </div>
                      )}
                      {activeSplitInfo.train_row_count != null && (
                        <div className="space-y-0.5">
                          <p className="text-xs text-slate-500">Records used for training</p>
                          <p className="font-medium text-white">{fmt(activeSplitInfo.training_rows_fitted ?? activeSplitInfo.train_row_count)}</p>
                        </div>
                      )}
                      {activeSplitInfo.holdout_row_count != null && (
                        <div className="space-y-0.5">
                          <p className="text-xs text-slate-500">Records reserved for accuracy check</p>
                          <p className="font-medium text-white">{fmt(activeSplitInfo.holdout_row_count)}</p>
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 pt-1 border-t border-slate-800">
                      Models were trained on older sales records only. Recent records are kept separate to check how well the models predict sales they have not seen before.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ModelTraining;
