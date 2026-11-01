import React from 'react';

const DemandForecast = () => {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h3 className="text-xl font-bold text-white mb-2">Demand Forecast</h3>
        <p className="text-sm text-slate-400">
          See expected daily sales for your products over the coming week based on trained prediction models.
        </p>
      </div>

      <div className="p-8 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-400 text-sm">
        Train prediction models on the <strong className="text-indigo-400">Sales Prediction</strong> page first to enable demand forecasts.
      </div>
    </div>
  );
};

export default DemandForecast;
