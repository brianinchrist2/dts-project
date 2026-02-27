// src/App.tsx
import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import StatusIndicator from './components/StatusIndicator';
import AssetDashboard from './components/AssetDashboard';
import MarketMonitor from './components/MarketMonitor';
import DealsHistory from './components/DealsHistory';
import { fetchSystemHealth, fetchAccountInfo } from './services/api';
import type { SystemHealth, AccountInfo } from './services/types';
import './styles/components.css'; // Import component-specific styles

// Constants for polling intervals
const HEALTH_POLL_INTERVAL = 1000; // 每秒刷新 1 次
const ACCOUNT_POLL_INTERVAL = 500; // 每秒刷新 2 次 (500ms)

function App() {
  const [activeTab, setActiveTab] = useState<'market' | 'history'>('market');
  const [healthData, setHealthData] = useState<SystemHealth | undefined>(undefined);
  const [accountData, setAccountData] = useState<AccountInfo | undefined>(undefined);
  const [isLoadingHealth, setIsLoadingHealth] = useState(true);
  const [isLoadingAccount, setIsLoadingAccount] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [accountError, setAccountError] = useState<string | null>(null);

  const loadHealthData = async () => {
    try {
      const data = await fetchSystemHealth();
      setHealthData(data);
      setHealthError(null);
    } catch (err: any) {
      console.error('Failed to fetch system health:', err);
      setHealthError('API Service is unavailable or malfunctioning.');
    } finally {
      setIsLoadingHealth(false);
    }
  };

  const loadAccountData = async () => {
    try {
      const data = await fetchAccountInfo();
      setAccountData(data);
      setAccountError(null);
    } catch (err: any) {
      console.error('Failed to fetch account info:', err);
      setAccountError('Could not retrieve account details. API might be down or inaccessible.');
    } finally {
      setIsLoadingAccount(false);
    }
  };

  useEffect(() => {
    loadHealthData(); // Fetch initial data
    const healthIntervalId = setInterval(loadHealthData, HEALTH_POLL_INTERVAL);

    loadAccountData(); // Fetch initial data
    const accountIntervalId = setInterval(loadAccountData, ACCOUNT_POLL_INTERVAL);

    // Cleanup intervals on component unmount
    return () => {
      clearInterval(healthIntervalId);
      clearInterval(accountIntervalId);
    };
  }, []);

  return (
    <Layout>
      <div className="dashboard-grid">
        <StatusIndicator
          healthData={healthData}
          isLoading={isLoadingHealth}
          error={healthError}
        />
        <AssetDashboard
          accountData={accountData}
          isLoading={isLoadingAccount}
          error={accountError}
        />
        
        <div className="tabs-container">
          <div className="tabs-header">
            <button 
              className={`tab-btn ${activeTab === 'market' ? 'active' : ''}`}
              onClick={() => setActiveTab('market')}
            >
              Market Monitor
            </button>
            <button 
              className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              Deals History
            </button>
          </div>
          <div className="tab-content">
            {activeTab === 'market' ? <MarketMonitor /> : <DealsHistory />}
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default App;
