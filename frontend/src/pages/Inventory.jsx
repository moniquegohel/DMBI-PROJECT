import React from 'react';

const Inventory = () => {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h3 className="text-xl font-bold text-white mb-2">Inventory Recommendations</h3>
        <p className="text-sm text-slate-400">
          Review reorder suggestions and stockout risk estimates based on predicted demand and your current stock levels.
        </p>
      </div>

      <div className="p-8 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-400 text-sm">
        Generate demand forecasts on the <strong className="text-indigo-400">Demand Forecast</strong> page first to enable inventory recommendations.
      </div>
    </div>
  );
};

export default Inventory;
