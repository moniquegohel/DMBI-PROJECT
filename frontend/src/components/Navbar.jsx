import React from 'react';
import { Activity } from 'lucide-react';

const Navbar = ({ activeTab, apiStatus }) => {
  const tabTitles = {
    dashboard: 'Dashboard',
    dataset: 'Dataset',
    analysis: 'Sales Analysis',
    model: 'Sales Prediction',
    forecast: 'Demand Forecast',
    inventory: 'Inventory Recommendations',
  };

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h2 className="text-lg font-semibold text-white">
          {tabTitles[activeTab] || 'SmartStock'}
        </h2>
      </div>

      <div className="flex items-center space-x-3">
        <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
          apiStatus === 'connected' 
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
            : apiStatus === 'error'
            ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
        }`}>
          <Activity className="w-3.5 h-3.5 animate-pulse" />
          <span>{apiStatus === 'connected' ? 'Online' : apiStatus === 'error' ? 'Offline' : 'Connecting…'}</span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
