import React from 'react';
import { ShoppingBag, Package, FileText, Calendar } from 'lucide-react';
import StatCard from '../components/StatCard';

const Dashboard = () => {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h3 className="text-xl font-bold text-white mb-2">SmartStock Overview</h3>
        <p className="text-sm text-slate-400">
          Welcome to SmartStock. Upload a retail CSV to initialize sales analysis, model training, demand forecasting, and inventory recommendations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Sales" 
          value="Pending Upload" 
          subtitle="Upload CSV dataset to populate" 
          icon={ShoppingBag} 
          color="indigo" 
        />
        <StatCard 
          title="Products Tracked" 
          value="0" 
          subtitle="Distinct product identifiers" 
          icon={Package} 
          color="emerald" 
        />
        <StatCard 
          title="Dataset Records" 
          value="0" 
          subtitle="Valid daily sales records" 
          icon={FileText} 
          color="cyan" 
        />
        <StatCard 
          title="Date Range" 
          value="—" 
          subtitle="Historical sales timeframe" 
          icon={Calendar} 
          color="amber" 
        />
      </div>

      <div className="p-8 rounded-xl bg-slate-950/60 border border-slate-800 text-center space-y-4">
        <div className="w-16 h-16 mx-auto rounded-full bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <FileText className="w-8 h-8" />
        </div>
        <h4 className="text-lg font-semibold text-white">No Dataset Uploaded Yet</h4>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          Start by navigating to the <strong className="text-indigo-400">Dataset Upload</strong> tab to select and clean your retail CSV sales data.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;
