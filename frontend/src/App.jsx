import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Dataset from './pages/Dataset';
import SalesAnalysis from './pages/SalesAnalysis';
import ModelTraining from './pages/ModelTraining';
import DemandForecast from './pages/DemandForecast';
import Inventory from './pages/Inventory';
import { fetchHealth } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('connecting');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await fetchHealth();
        setApiStatus('connected');
      } catch (err) {
        console.warn('Backend API connection check failed:', err);
        setApiStatus('error');
      }
    };
    checkBackend();
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'dataset':
        return <Dataset />;
      case 'analysis':
        return <SalesAnalysis setActiveTab={setActiveTab} />;
      case 'model':
        return <ModelTraining setActiveTab={setActiveTab} />;
      case 'forecast':
        return <DemandForecast />;
      case 'inventory':
        return <Inventory />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar activeTab={activeTab} apiStatus={apiStatus} />
        <main className="flex-1 overflow-y-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;

