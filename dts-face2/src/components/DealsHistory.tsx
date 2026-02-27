import React, { useState, useEffect } from 'react';
import { fetchDealsHistory } from '../services/api';
import '../styles/components.css';

interface Deal {
  ticket: number;
  time: number;
  symbol: string;
  type: number;
  volume: number;
  price: number;
  profit: number;
  commission: number;
  swap: number;
}

const DealsHistory: React.FC = () => {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);
  const [isExpanded, setIsExpanded] = useState(false); // 默认收起

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await fetchDealsHistory(days);
      // Sort by time descending
      data.sort((a: Deal, b: Deal) => b.time - a.time);
      setDeals(data);
      setError(null);
    } catch (err) {
      setError('加载成交历史失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isExpanded) {
      loadHistory();
    }
  }, [days, isExpanded]);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getTypeName = (type: number) => {
    return type === 0 ? '买入' : '卖出';
  };

  return (
    <div className="market-monitor-card">
      <div className="card-header-row">
        <h3 className="monitor-title">Deals History</h3>
        <div className="history-controls">
          {isExpanded && (
            <select 
              value={days} 
              onChange={(e) => setDays(Number(e.target.value))}
              className="history-select"
            >
              <option value={1}>最近 24 小时</option>
              <option value={3}>最近 3 天</option>
              <option value={7}>最近 7 天</option>
              <option value={30}>最近 30 天</option>
            </select>
          )}
          <button
            className="btn-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '▼ 收起' : '▶ 展开'}
          </button>
          {isExpanded && <button className="refresh-btn" onClick={loadHistory}>刷新</button>}
        </div>
      </div>

      {isExpanded && (
        <div className="table-scroll-wrapper">
          {loading && <div className="loading-overlay">加载中...</div>}
          {error && <div className="error-banner">{error}</div>}
          
          <table className="market-table">
            <thead>
              <tr>
                <th>品种</th>
                <th>类型</th>
                <th>手数</th>
                <th>成交价</th>
                <th>盈亏</th>
                <th>成交时间</th>
              </tr>
            </thead>
            <tbody>
              {deals.length > 0 ? (
                deals.map((deal) => (
                  <tr key={deal.ticket}>
                    <td className="symbol-name">{deal.symbol}</td>
                    <td className={deal.type === 0 ? 'type-buy' : 'type-sell'}>
                      {getTypeName(deal.type)}
                    </td>
                    <td>{deal.volume.toFixed(2)}</td>
                    <td>{deal.price.toFixed(5)}</td>
                    <td className={deal.profit >= 0 ? 'profit-positive' : 'profit-negative'}>
                      {deal.profit.toFixed(2)}
                    </td>
                    <td className="update-time">{formatTime(deal.time)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '20px' }}>
                    暂无成交记录
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DealsHistory;
