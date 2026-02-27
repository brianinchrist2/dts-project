// src/components/StatusIndicator.tsx
import React from 'react';
import '../styles/components.css'; // Import component styles
import type { SystemHealth } from '../services/types'; // Import type definitions

interface StatusIndicatorProps {
  healthData?: SystemHealth;
  isLoading: boolean;
  error: string | null;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ healthData, isLoading, error }) => {
  const [isExpanded, setIsExpanded] = React.useState(false); // 默认收起

  const getStatusClass = (status: string | boolean | undefined, healthyValue: any = 'ok', unhealthyValue: any = 'error'): string => {
    if (isLoading) return 'initializing';
    if (error) return 'unhealthy';
    if (status === healthyValue) return 'healthy';
    if (status === unhealthyValue) return 'unhealthy';
    return 'initializing'; // Default or intermediate state
  };

  return (
    <div className="card">
      <div className="card-header-row">
        <h3>System Status</h3>
        <button
          className="btn-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼ 收起' : '▶ 展开'}
        </button>
      </div>
      
      {isExpanded && (
        <div style={{ padding: '1rem' }}>
          {isLoading && <div className="loading-indicator"><div className="loading-spinner"></div>Loading status...</div>}
          {error && <div className="error-message">{error}</div>}
          {!isLoading && !error && healthData && (
            <div className="status-indicators-section">
              <div className="status-item">
                <span className={`status-indicator ${getStatusClass(healthData.status, 'ok', 'error')}`}></span>
                <span className="status-label">API Service</span>
              </div>
              <div className="status-item">
                <span className={`status-indicator ${getStatusClass(healthData.mt5_connected, true, false)}`}></span>
                <span className="status-label">MT5 Bridge</span>
              </div>
              <div className="status-item">
                <span className={`status-indicator ${getStatusClass(healthData.db_ok, true, false)}`}></span>
                <span className="status-label">Database</span>
              </div>
            </div>
          )}
          {!isLoading && !error && !healthData && (
            <div className="error-message">No health data available.</div>
          )}
        </div>
      )}
    </div>
  );
};

export default StatusIndicator;
