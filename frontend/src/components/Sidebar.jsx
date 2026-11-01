import React from 'react';
import {
  LayoutDashboard,
  Database,
  TrendingUp,
  BrainCircuit,
  LineChart,
  Boxes
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'dataset', label: 'Dataset Upload', icon: Database },
    { id: 'analysis', label: 'Sales Analysis', icon: TrendingUp },
    { id: 'model', label: 'Sales Prediction', icon: BrainCircuit },
    { id: 'forecast', label: 'Demand Forecast', icon: LineChart },
    { id: 'inventory', label: 'Inventory Analysis', icon: Boxes },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col min-h-screen">
      <div className="p-6 border-b border-slate-800 flex items-[#center] space-x-3">
        <div className="w-10 h-10 rounded-xl bg-linear-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-indigo-500/20">
          S
        </div>
        <div>
          <h1 className="font-extrabold text-lg text-white tracking-wide">SmartStock</h1>
          <p className="text-xs text-slate-400">Demand & Inventory AI</p>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900'
                }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
        SmartStock v1.0
      </div>
    </aside>
  );
};

export default Sidebar;
