import React from 'react';

const StatCard = ({ title, value, subtitle, icon: Icon, color = "indigo" }) => {
  const colorMap = {
    indigo: "from-indigo-500/10 to-indigo-600/5 border-indigo-500/20 text-indigo-400",
    emerald: "from-emerald-500/10 to-emerald-600/5 border-emerald-500/20 text-emerald-400",
    cyan: "from-cyan-500/10 to-cyan-600/5 border-cyan-500/20 text-cyan-400",
    amber: "from-amber-500/10 to-amber-600/5 border-amber-500/20 text-amber-400",
    rose: "from-rose-500/10 to-rose-600/5 border-rose-500/20 text-rose-400",
  };

  return (
    <div className={`p-6 rounded-xl bg-linear-to-br ${colorMap[color] || colorMap.indigo} border backdrop-blur flex flex-col justify-between shadow-lg`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        {Icon && (
          <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/50">
            <Icon className="w-5 h-5 text-slate-200" />
          </div>
        )}
      </div>
      <div>
        <div className="text-2xl font-bold text-white mb-1 tracking-tight">
          {value !== undefined && value !== null ? value : '—'}
        </div>
        {subtitle && (
          <p className="text-xs text-slate-400 font-normal">{subtitle}</p>
        )}
      </div>
    </div>
  );
};

export default StatCard;
