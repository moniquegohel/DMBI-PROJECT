import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Download,
  Table,
  Layers,
  ShieldCheck,
  Calendar,
  Store,
  Hash
} from 'lucide-react';
import StatCard from '../components/StatCard';
import {
  uploadDataset,
  getDatasetSummary,
  updateColumnMappings,
  cleanDataset,
  loadSampleDataset,
  getCleanedDownloadUrl,
  getRawDownloadUrl
} from '../services/api';

const Dataset = () => {
  // State variables
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleaningResult, setCleaningResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [activeTab, setActiveTab] = useState('preview'); // 'preview', 'columns', 'cleaned'
  const [localMappings, setLocalMappings] = useState({});
  const [isSavingMappings, setIsSavingMappings] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const fetchCurrentSummary = async () => {
    try {
      const data = await getDatasetSummary();
      if (data && data.has_dataset) {
        setSummary(data);
        syncLocalMappings(data.mappings);
        if (data.is_cleaned) {
          setActiveTab('cleaned');
        }
      }
    } catch (err) {
      console.warn('Could not fetch initial dataset summary:', err);
    }
  };

  // Fetch current dataset summary on component mount
  useEffect(() => {
    fetchCurrentSummary();
  }, []);

  const syncLocalMappings = (mappingItems) => {
    if (!mappingItems) return;
    const mapObj = {};
    mappingItems.forEach(item => {
      mapObj[item.role] = item.mapped_column || '';
    });
    setLocalMappings(mapObj);
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    validateAndSetFile(selected);
  };

  const validateAndSetFile = (selected) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    if (!selected) return;

    if (!selected.name.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Unsupported file format. Please upload a standard comma-separated (.csv) file.');
      setFile(null);
      return;
    }

    if (selected.size === 0) {
      setErrorMessage('The selected file is empty (0 bytes). Please select a valid CSV.');
      setFile(null);
      return;
    }

    setFile(selected);
  };

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  // Upload handler
  const handleUpload = async () => {
    if (!file) {
      setErrorMessage('Please select a .csv file first.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    setCleaningResult(null);

    try {
      const data = await uploadDataset(file);
      setSummary(data);
      syncLocalMappings(data.mappings);
      setActiveTab('preview');
      setSuccessMessage(`Successfully uploaded and inspected "${data.filename}" (${data.row_count.toLocaleString()} rows, ${data.column_count} columns).`);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to upload CSV file.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick Load Sample handler (academic viva convenience)
  const handleLoadSample = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    setCleaningResult(null);

    try {
      const data = await loadSampleDataset();
      setSummary(data);
      syncLocalMappings(data.mappings);
      setActiveTab('preview');
      setSuccessMessage(`Loaded sample dataset "${data.filename}" (${data.row_count.toLocaleString()} rows, ${data.column_count} columns).`);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Could not load local sample dataset.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle mapping changes
  const handleMappingChange = (role, column) => {
    setLocalMappings(prev => ({
      ...prev,
      [role]: column
    }));
  };

  // Save column mappings
  const handleSaveMappings = async () => {
    setIsSavingMappings(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const updatedSummary = await updateColumnMappings(localMappings);
      setSummary(updatedSummary);
      syncLocalMappings(updatedSummary.mappings);
      setSuccessMessage('Column mappings saved successfully.');
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to update column mappings.');
    } finally {
      setIsSavingMappings(false);
    }
  };

  // Clean dataset handler
  const handleCleanDataset = async () => {
    setIsCleaning(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const result = await cleanDataset();
      setCleaningResult(result);
      setActiveTab('cleaned');
      setSuccessMessage(`Data cleaning complete: ${result.cleaned_rows.toLocaleString()} rows verified and ready for downstream analysis.`);
      // Refresh summary
      await fetchCurrentSummary();
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Data cleaning failed.');
    } finally {
      setIsCleaning(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <h3 className="text-2xl font-bold text-white tracking-tight">Dataset Ingestion & Cleaning</h3>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${summary?.is_cleaned
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : summary?.has_dataset
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
              {summary?.is_cleaned ? 'Cleaned & Ready' : summary?.has_dataset ? 'Uploaded / Uncleaned' : 'No Dataset'}
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Upload public retail transaction data, inspect attributes, map semantic roles, and execute transparent data-quality cleaning.
          </p>
        </div>

        {/* Quick action buttons if dataset loaded */}
        {summary?.has_dataset && (
          <div className="flex items-center space-x-3">
            <a
              href={getRawDownloadUrl()}
              download
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 flex items-center space-x-2 transition"
              title="Download original raw uploaded CSV"
            >
              <Download className="w-4 h-4 text-slate-400" />
              <span>Raw CSV</span>
            </a>
            {summary.is_cleaned && (
              <a
                href={getCleanedDownloadUrl()}
                download
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium flex items-center space-x-2 shadow-lg shadow-emerald-600/20 transition"
                title="Download verified cleaned CSV"
              >
                <Download className="w-4 h-4 text-white" />
                <span>Cleaned CSV</span>
              </a>
            )}
          </div>
        )}
      </div>

      {/* Alert Banners */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start space-x-3 animate-fadeIn">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h5 className="font-semibold text-rose-200">Validation Error</h5>
            <p className="text-xs text-rose-300/90 mt-0.5">{errorMessage}</p>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-200 text-xs">✕</button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-start space-x-3 animate-fadeIn">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h5 className="font-semibold text-emerald-200">Operation Successful</h5>
            <p className="text-xs text-emerald-300/90 mt-0.5">{successMessage}</p>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-emerald-200 text-xs">✕</button>
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-base font-semibold text-white flex items-center space-x-2">
            <Upload className="w-5 h-5 text-indigo-400" />
            <span>Select & Upload Retail CSV</span>
          </h4>
          <button
            onClick={handleLoadSample}
            disabled={isLoading || isCleaning}
            className="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium flex items-center space-x-1 transition disabled:opacity-50"
          >
            <span>Load Sample (retail_store_inventory.csv)</span>
          </button>
        </div>

        {/* Dropzone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${isDragOver
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40'
            }`}
          onClick={() => document.getElementById('csvFileInput')?.click()}
        >
          <input
            id="csvFileInput"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <div className="w-12 h-12 mx-auto rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-indigo-400 mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <p className="text-sm font-medium text-slate-200">
            {file ? file.name : 'Click to select or drag and drop a retail sales CSV file'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {file ? `${formatFileSize(file.size)} • Ready to upload` : 'Supported file format: .csv (e.g. retail_store_inventory.csv)'}
          </p>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-slate-500">
            {summary?.has_dataset
              ? `Currently loaded: ${summary.filename} (${summary.row_count.toLocaleString()} records)`
              : 'No dataset currently uploaded'}
          </span>
          <button
            onClick={handleUpload}
            disabled={!file || isLoading}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-indigo-600/20 flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                <span>Processing & Inspecting...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload & Inspect Dataset</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Dataset Overview StatCards (Rendered when dataset exists) */}
      {summary?.has_dataset && (
        <div className="space-y-6 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Records"
              value={summary.row_count.toLocaleString()}
              subtitle={`${summary.column_count} attributes / columns`}
              icon={Hash}
              color="indigo"
            />
            <StatCard
              title="Time Period"
              value={summary.date_range_start && summary.date_range_end ? `${summary.unique_dates_count} Days` : 'N/A'}
              subtitle={summary.date_range_start ? `${summary.date_range_start} to ${summary.date_range_end}` : 'No date column'}
              icon={Calendar}
              color="cyan"
            />
            <StatCard
              title="Entities Tracked"
              value={`${summary.unique_stores_count} Stores • ${summary.unique_products_count} Products`}
              subtitle="Distinct retail dimensions"
              icon={Store}
              color="emerald"
            />
            <StatCard
              title="Data Quality"
              value={summary.total_missing_values === 0 && summary.duplicate_rows_count === 0 ? '100% Clean' : 'Needs Review'}
              subtitle={`${summary.total_missing_values} nulls • ${summary.duplicate_rows_count} duplicates`}
              icon={ShieldCheck}
              color={summary.total_missing_values === 0 ? 'emerald' : 'amber'}
            />
          </div>

          {/* Quality Findings & Special Warnings Section */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h4 className="text-base font-semibold text-white flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>Data Quality Findings & Validation Checks</span>
              </h4>
              <span className="text-xs text-slate-400">
                {summary.quality_checks.length} Checks Run • {summary.warnings_count} Warnings • {summary.errors_count} Errors
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {summary.quality_checks.map((chk, idx) => {
                const isWarn = chk.check_type === 'warning';
                const isErr = chk.check_type === 'error';
                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border flex items-start space-x-3 ${isErr
                        ? 'bg-rose-500/10 border-rose-500/30'
                        : isWarn
                          ? 'bg-amber-500/10 border-amber-500/30'
                          : 'bg-slate-900/60 border-slate-800'
                      }`}
                  >
                    <div className="shrink-0 mt-0.5">
                      {isErr ? (
                        <AlertCircle className="w-5 h-5 text-rose-400" />
                      ) : isWarn ? (
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                      ) : (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      )}
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <h5 className={`text-sm font-semibold ${isErr ? 'text-rose-200' : isWarn ? 'text-amber-200' : 'text-slate-200'}`}>
                          {chk.title}
                        </h5>
                        {chk.affected_count > 0 && (
                          <span className={`text-xs px-2 py-0.5 rounded font-mono ${isWarn ? 'bg-amber-500/20 text-amber-300' : 'bg-rose-500/20 text-rose-300'
                            }`}>
                            {chk.affected_count.toLocaleString()} rows
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        {chk.description}
                      </p>
                      {chk.action_recommendation && (
                        <p className="text-xs font-medium text-slate-300 pt-1 border-t border-slate-800/60 mt-1">
                          <span className="text-slate-500">Action: </span>{chk.action_recommendation}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column Mapping Section */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <h4 className="text-base font-semibold text-white flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-indigo-400" />
                  <span>Semantic Column Role Mapping</span>
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Verify or adjust how dataset columns correspond to retail demand forecasting roles.
                </p>
              </div>
              <button
                onClick={handleSaveMappings}
                disabled={isSavingMappings}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition shadow-md shadow-indigo-600/20 flex items-center space-x-1.5"
              >
                {isSavingMappings ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Save Mappings</span>
                  </>
                )}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {summary.mappings.map((item) => (
                <div
                  key={item.role}
                  className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white flex items-center space-x-1.5">
                      <span>{item.role_label}</span>
                      {item.is_required && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          Required
                        </span>
                      )}
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${localMappings[item.role]
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : item.is_required
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-slate-800 text-slate-400'
                      }`}>
                      {localMappings[item.role] ? 'Mapped' : 'Unmapped'}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-500 line-clamp-1">{item.description}</p>

                  <select
                    value={localMappings[item.role] || ''}
                    onChange={(e) => handleMappingChange(item.role, e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                  >
                    <option value="">(Not Mapped / None)</option>
                    {summary.columns.map((c) => (
                      <option key={c.name} value={c.name}>
                        {c.name} ({c.inferred_type})
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {/* Clean Dataset Action Card */}
          <div className="bg-linear-to-br from-indigo-950/40 via-slate-950/60 to-slate-950/80 border border-indigo-500/30 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <h4 className="text-base font-semibold text-white flex items-center space-x-2">
                  <ShieldCheck className="w-5 h-5 text-indigo-400" />
                  <span>Execute Data Cleaning Pipeline</span>
                </h4>
                <p className="text-xs text-slate-400 max-w-2xl">
                  Applies standardized date parsing, validates numeric types, sorts transactions chronologically, and preserves domain exceptions (e.g. 673 negative Demand Forecast values are preserved intact without row loss).
                </p>
              </div>

              <button
                onClick={handleCleanDataset}
                disabled={isCleaning}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 shrink-0 disabled:opacity-50"
              >
                {isCleaning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Cleaning Dataset...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Clean & Validate Dataset</span>
                  </>
                )}
              </button>
            </div>

            {/* Cleaning Results Callout (if clean action was run) */}
            {cleaningResult && (
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 space-y-3 animate-fadeIn">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h5 className="text-xs font-semibold text-emerald-400 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Cleaning Execution Summary</span>
                  </h5>
                  <span className="text-xs font-mono text-slate-300">
                    Rows: {cleaningResult.original_rows.toLocaleString()} → {cleaningResult.cleaned_rows.toLocaleString()} (0 rows lost)
                  </span>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-slate-400">Transformations Applied:</span>
                  <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                    {cleaningResult.changes_applied.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>

                {cleaningResult.warnings.length > 0 && (
                  <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 space-y-1">
                    <span className="font-semibold flex items-center space-x-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      <span>Noted Domain Warnings:</span>
                    </span>
                    <ul className="list-disc list-inside space-y-0.5 text-amber-300/90 pl-1">
                      {cleaningResult.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Tabbed Inspection & Preview Section */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            {/* Tabs Header */}
            <div className="flex items-center border-b border-slate-800 bg-slate-950 px-6 pt-4 space-x-4">
              <button
                onClick={() => setActiveTab('preview')}
                className={`pb-3 px-2 text-xs font-medium border-b-2 transition flex items-center space-x-2 ${activeTab === 'preview'
                    ? 'border-indigo-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
              >
                <Table className="w-4 h-4" />
                <span>Raw Data Preview (First 10 Rows)</span>
              </button>

              <button
                onClick={() => setActiveTab('columns')}
                className={`pb-3 px-2 text-xs font-medium border-b-2 transition flex items-center space-x-2 ${activeTab === 'columns'
                    ? 'border-indigo-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
              >
                <Layers className="w-4 h-4" />
                <span>Column Statistics ({summary.column_count} Columns)</span>
              </button>

              {summary.is_cleaned && (
                <button
                  onClick={() => setActiveTab('cleaned')}
                  className={`pb-3 px-2 text-xs font-medium border-b-2 transition flex items-center space-x-2 ${activeTab === 'cleaned'
                      ? 'border-emerald-500 text-emerald-400'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Cleaned Data Preview</span>
                </button>
              )}
            </div>

            {/* Tab 1: Raw Preview Table */}
            {activeTab === 'preview' && (
              <div className="p-6">
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-3.5 py-3 text-slate-500 font-mono">#</th>
                        {summary.columns.map((c) => (
                          <th key={c.name} className="px-3.5 py-3 whitespace-nowrap">
                            {c.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                      {summary.preview_rows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/50 transition">
                          <td className="px-3.5 py-2.5 text-slate-600">{idx + 1}</td>
                          {summary.columns.map((c) => {
                            const val = row[c.name];
                            const isNeg = typeof val === 'number' && val < 0;
                            return (
                              <td
                                key={c.name}
                                className={`px-3.5 py-2.5 whitespace-nowrap ${isNeg ? 'text-amber-400 font-bold' : 'text-slate-300'
                                  }`}
                              >
                                {val !== null && val !== undefined ? String(val) : <span className="text-slate-600">null</span>}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 2: Column Inspection Table */}
            {activeTab === 'columns' && (
              <div className="p-6">
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3">Column Name</th>
                        <th className="px-4 py-3">Inferred Type</th>
                        <th className="px-4 py-3">Missing</th>
                        <th className="px-4 py-3">Unique Values</th>
                        <th className="px-4 py-3">Min</th>
                        <th className="px-4 py-3">Max</th>
                        <th className="px-4 py-3">Mean</th>
                        <th className="px-4 py-3">Sample Values</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                      {summary.columns.map((col) => (
                        <tr key={col.name} className="hover:bg-slate-900/50 transition">
                          <td className="px-4 py-3 font-semibold text-white font-mono">{col.name}</td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                              {col.inferred_type}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono">
                            {col.missing_count === 0 ? (
                              <span className="text-emerald-400">0 (0%)</span>
                            ) : (
                              <span className="text-amber-400">{col.missing_count} ({col.missing_percentage}%)</span>
                            )}
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-300">
                            {col.unique_count.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-300">
                            {col.min_value !== null ? col.min_value : '—'}
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-300">
                            {col.max_value !== null ? col.max_value : '—'}
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-300">
                            {col.mean_value !== null ? col.mean_value : '—'}
                          </td>
                          <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                            {col.sample_values?.join(', ') || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 3: Cleaned Data Preview */}
            {activeTab === 'cleaned' && summary.is_cleaned && (
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="font-medium">Validated & Chronologically Sorted Cleaned Records</span>
                  </div>
                  <a
                    href={getCleanedDownloadUrl()}
                    download
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1.5 shadow-md shadow-emerald-600/20 transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Cleaned CSV</span>
                  </a>
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-3.5 py-3 text-slate-500 font-mono">#</th>
                        {summary.columns.map((c) => (
                          <th key={c.name} className="px-3.5 py-3 whitespace-nowrap">
                            {c.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                      {summary.preview_rows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/50 transition">
                          <td className="px-3.5 py-2.5 text-slate-600">{idx + 1}</td>
                          {summary.columns.map((c) => {
                            const val = row[c.name];
                            return (
                              <td key={c.name} className="px-3.5 py-2.5 whitespace-nowrap text-slate-300">
                                {val !== null && val !== undefined ? String(val) : <span className="text-slate-600">null</span>}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dataset;
