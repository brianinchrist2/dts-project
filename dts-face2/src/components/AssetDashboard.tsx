// src/components/AssetDashboard.tsx
import React from 'react';
import '../styles/components.css'; // Import component styles
import type { AccountInfo } from '../services/types'; // Import type definitions
import LoadingSpinner from './LoadingSpinner'; // Import spinner

interface AssetDashboardProps {
  accountData?: AccountInfo;
  isLoading: boolean;
  error: string | null;
}

const AssetDashboard: React.FC<AssetDashboardProps> = ({ accountData, isLoading, error }) => {
  const [isExpanded, setIsExpanded] = React.useState(false); // 默认收起

  const formatCurrency = (value: number | undefined, currency: string = 'USD'): string => {
    if (value === undefined) return '-';
    // Basic formatting, can be enhanced for different currencies/locales
    return `${currency} ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // Calculate floating P&L from equity - balance (API doesn't return floating_pnl directly)
  const floatingPnl = accountData ? accountData.equity - accountData.balance : undefined;

  const getPnlClass = (pnl: number | undefined): string => {
    if (pnl === undefined) return 'neutral';
    if (pnl > 0) return 'positive';
    if (pnl < 0) return 'negative';
    return 'neutral';
  };

  return (
    <div className="card">
      <div className="card-header-row">
        <h3>Account Overview</h3>
        <button
          className="btn-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼ 收起' : '▶ 展开'}
        </button>
      </div>

      {isExpanded && (
        <div style={{ padding: '1rem' }}>
          {isLoading && <LoadingSpinner />}
          {error && <div className="error-message">Failed to load account data: {error}</div>}
          {!isLoading && !error && accountData && (
            <div className="asset-dashboard-grid">
              <div className="asset-metric">
                <div className="asset-metric-label">Balance</div>
                <div className="asset-metric-value" title={formatCurrency(accountData.balance, accountData.currency)}>
                  {formatCurrency(accountData.balance, accountData.currency)}
                </div>
              </div>
              <div className="asset-metric">
                <div className="asset-metric-label">Equity</div>
                <div className="asset-metric-value" title={formatCurrency(accountData.equity, accountData.currency)}>
                  {formatCurrency(accountData.equity, accountData.currency)}
                </div>
              </div>
              <div className="asset-metric">
                <div className="asset-metric-label">Margin Used</div>
                <div className="asset-metric-value" title={formatCurrency(accountData.margin, accountData.currency)}>
                  {formatCurrency(accountData.margin, accountData.currency)}
                </div>
              </div>
              <div className="asset-metric">
                <div className="asset-metric-label">Free Margin</div>
                <div className="asset-metric-value" title={formatCurrency(accountData.margin_free, accountData.currency)}>
                  {formatCurrency(accountData.margin_free, accountData.currency)}
                </div>
              </div>
              <div className="asset-metric">
                <div className="asset-metric-label">Margin Level</div>
                <div className="asset-metric-value">{accountData.leverage.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</div>
              </div>
              <div className="asset-metric">
                <div className="asset-metric-label">Floating P&amp;L</div>
                <div className={`asset-metric-value ${getPnlClass(floatingPnl)}`} data-metric="floating_pnl"
                     title={formatCurrency(floatingPnl, accountData.currency)}>
                  {formatCurrency(floatingPnl, accountData.currency)}
                </div>
              </div>
            </div>
          )}
          {!isLoading && !error && !accountData && (
            <div className="error-message">No account data available.</div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssetDashboard;
