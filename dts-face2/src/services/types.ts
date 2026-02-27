// src/services/types.ts

export interface SystemHealth {
  status: string;
  mt5_connected: boolean;
  db_ok: boolean;
  timestamp?: string;
}

export interface AccountInfo {
  login: number;
  name: string;
  server: string;
  balance: number;
  equity: number;
  margin: number;
  margin_free: number;
  leverage: number;
  currency: string;
}

export interface Quote {
  symbol: string;
  bid: number;
  ask: number;
  time: number;  // API returns 'time' not 'timestamp'
}

// Assuming symbols endpoint returns an array of objects with at least 'symbol'
export interface SymbolInfo {
  symbol: string;
  description?: string;
  digits?: number;
  min_volume?: number;
  max_volume?: number;
  volume_step?: number;
}
