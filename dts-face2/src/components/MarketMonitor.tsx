// src/components/MarketMonitor.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import '../styles/components.css';
import type { Quote } from '../services/types';
import { fetchMarketQuotes } from '../services/api';
import LoadingSpinner from './LoadingSpinner';

// 默认货币对列表
const DEFAULT_SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'];
const STORAGE_KEY = 'marketMonitor_symbols';
const SYMBOL_PATTERN = /^[A-Z]{3,10}$/;
const POLLING_INTERVAL = 500; // 每 500ms 刷新一次行情

// 货币对标签组件：支持 × 按钮点击删除（桌面）和左滑删除（触屏）
const SymbolTag: React.FC<{
  symbol: string;
  onDelete: (symbol: string) => void;
}> = ({ symbol, onDelete }) => {
  const [offsetX, setOffsetX] = useState(0);
  const startX = useRef(0);
  const dragging = useRef(false);

  // 触摸开始：记录起点
  const handleTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
    dragging.current = false;
  };

  // 触摸移动：检测左滑手势
  const handleTouchMove = (e: React.TouchEvent) => {
    const diff = startX.current - e.touches[0].clientX;
    if (diff > 5) {
      dragging.current = true;
      setOffsetX(Math.min(diff, 70));
    } else if (diff < -5) {
      setOffsetX(0);
    }
  };

  // 触摸结束：左滑超过阈值则删除，否则复位
  const handleTouchEnd = () => {
    if (offsetX > 40) {
      onDelete(symbol);
    } else {
      setOffsetX(0);
    }
    dragging.current = false;
  };

  return (
    <div className="symbol-tag-item">
      {/* 左滑时显示的红色删除背景 */}
      <div className="symbol-tag-del-bg">🗑️</div>
      {/* 标签主体，左滑时向左平移 */}
      <div
        className="symbol-tag-inner"
        style={{
          transform: `translateX(-${offsetX}px)`,
          transition: dragging.current ? 'none' : 'transform 0.2s ease',
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <span className="symbol-tag-label">{symbol}</span>
        {/* 桌面可见的 × 删除按钮 */}
        <button
          className="symbol-tag-del-btn"
          onClick={() => onDelete(symbol)}
          aria-label={`删除 ${symbol}`}
        >
          ×
        </button>
      </div>
    </div>
  );
};

const MarketMonitor: React.FC = () => {
  // 从 localStorage 初始化货币对列表，回退到默认列表
  const [symbols, setSymbols] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch { /* 解析失败时使用默认值 */ }
    return DEFAULT_SYMBOLS;
  });

  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 输入框状态
  const [inputValue, setInputValue] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false); // 默认收起管理区
  const inputRef = useRef<HTMLInputElement>(null);

  // symbols 变化时持久化到 localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols));
  }, [symbols]);

  // 加载行情数据（使用 useCallback 避免 useEffect 依赖警告）
  const loadQuotes = useCallback(async () => {
    if (symbols.length === 0) {
      setQuotes([]);
      setIsLoading(false);
      return;
    }
    try {
      const data = await fetchMarketQuotes(symbols);
      setQuotes(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch market quotes:', err);
      setError('Failed to load market data.');
    } finally {
      setIsLoading(false);
    }
  }, [symbols]);

  // symbols 变化时重置 loading 并重启轮询
  useEffect(() => {
    setIsLoading(true);
    loadQuotes();
    const intervalId = setInterval(loadQuotes, POLLING_INTERVAL);
    return () => clearInterval(intervalId);
  }, [loadQuotes]);

  // 添加货币对：校验 → 去重 → 更新状态
  const handleAddSymbol = () => {
    const trimmed = inputValue.trim().toUpperCase();
    if (!SYMBOL_PATTERN.test(trimmed)) {
      setInputError('请输入 3-10 位字母，如 EURUSD');
      return;
    }
    if (symbols.includes(trimmed)) {
      setInputError(`${trimmed} 已存在`);
      return;
    }
    setSymbols(prev => [...prev, trimmed]);
    setInputValue('');
    setInputError(null);
    inputRef.current?.focus();
  };

  // 删除货币对：从列表中过滤掉目标 symbol
  const handleDeleteSymbol = useCallback((symbol: string) => {
    setSymbols(prev => prev.filter(s => s !== symbol));
  }, []);

  // 回车触发添加
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleAddSymbol();
  };

  // 价格格式化（5 位小数）
  const formatPrice = (price: number | undefined): string => {
    if (price === undefined) return '-';
    return price.toLocaleString(undefined, { minimumFractionDigits: 5, maximumFractionDigits: 5 });
  };

  return (
    <div className="card market-monitor-card">
      {/* 头部：标题 + 展开/收起切换 */}
      <div className="card-header-row">
        <h3>Market Monitor</h3>
        <button
          className="btn-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼ 收起' : '▶ 展开'}
        </button>
      </div>

      {/* 可折叠的货币对管理区域 */}
      {isExpanded && (
        <div className="symbol-manager-new">
          {/* 输入行 */}
          <div className="symbol-input-group">
            <input
              ref={inputRef}
              className="symbol-input-new"
              type="text"
              placeholder="输入货币对，如 EURUSD"
              value={inputValue}
              onChange={e => {
                setInputValue(e.target.value);
                setInputError(null);
              }}
              onKeyDown={handleKeyDown}
              maxLength={10}
            />
            <button className="btn-add-new" onClick={handleAddSymbol}>+</button>
          </div>

          {inputError && <div className="input-error">{inputError}</div>}

          {/* 货币对标签列表（桌面点 × 删除，触屏左滑删除） */}
          <div className="symbol-list">
            {symbols.map(sym => (
              <SymbolTag
                key={sym}
                symbol={sym}
                onDelete={handleDeleteSymbol}
              />
            ))}
            {symbols.length === 0 && (
              <div className="symbol-list-empty">暂无货币对，请在上方添加</div>
            )}
          </div>
        </div>
      )}

      {/* 行情数据区域 */}
      {isLoading && <LoadingSpinner />}
      {error && <div className="error-message">{error}</div>}
      {!isLoading && !error && quotes.length > 0 && (
        <div className="table-scroll-wrapper">
          <table className="market-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Bid</th>
                <th>Ask</th>
                <th className="col-time">更新时间</th>
              </tr>
            </thead>
            <tbody>
              {quotes.map((quote) => (
                <tr key={quote.symbol}>
                  <td className="symbol-name">{quote.symbol}</td>
                  <td className="price-bid">{formatPrice(quote.bid)}</td>
                  <td className="price-ask">{formatPrice(quote.ask)}</td>
                  <td className="col-time">{new Date(quote.time * 1000).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default MarketMonitor;
