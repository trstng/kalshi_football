/**
 * API client for fetching live market data from the Kalshi data collection service
 */

const API_URL = import.meta.env.VITE_API_URL || 'https://predictiondata-production.up.railway.app'

export interface Market {
  ticker: string
  title: string
  subtitle: string
  close_time: string
  status: string
}

export interface MarketsByCategory {
  NFL: Market[]
  NHL: Market[]
  NBA: Market[]
  CFB: Market[]
  OTHER?: Market[]
}

export interface LatestPrice {
  ticker: string
  timestamp: number
  timestamp_ms: number
  yes_bid: number
  yes_ask: number
  no_bid: number
  no_ask: number
  last_price: number
  mid_price: number
  spread: number
  volume: number
  open_interest: number
}

export interface PriceHistory {
  ticker: string
  series: Array<{
    name: string
    data: Array<[number, number]> // [timestamp_ms, value]
  }>
  volume_series: Array<{
    name: string
    data: Array<[number, number]>
  }>
  count: number
  start_time: number
  end_time: number
}

export interface Candle {
  x: number // timestamp in milliseconds
  y: [number, number, number, number] // [open, high, low, close]
}

export interface CandleData {
  ticker: string
  interval: string
  candles: Candle[]
  count: number
}

export interface Trade {
  trade_id: string
  timestamp: number
  timestamp_ms: number
  price: number
  size: number
  side: string
  taker_side: string
}

export interface TradeHistory {
  ticker: string
  trades: Trade[]
  count: number
}

/**
 * Fetch all available markets grouped by sport
 */
export async function fetchMarkets(sport?: string): Promise<{ markets: MarketsByCategory; total: number }> {
  const url = sport
    ? `${API_URL}/api/markets?sport=${sport}`
    : `${API_URL}/api/markets`

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch markets: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch the latest price snapshot for a market
 */
export async function fetchLatestPrice(ticker: string): Promise<LatestPrice> {
  const response = await fetch(`${API_URL}/api/markets/${ticker}/latest`)
  if (!response.ok) {
    throw new Error(`Failed to fetch latest price: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch historical price data for line charts
 */
export async function fetchPriceHistory(
  ticker: string,
  options?: {
    start_time?: number
    end_time?: number
    limit?: number
  }
): Promise<PriceHistory> {
  const params = new URLSearchParams()
  if (options?.start_time) params.append('start_time', options.start_time.toString())
  if (options?.end_time) params.append('end_time', options.end_time.toString())
  if (options?.limit) params.append('limit', options.limit.toString())

  const url = `${API_URL}/api/markets/${ticker}/history${params.toString() ? `?${params.toString()}` : ''}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch price history: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch candlestick OHLC data
 */
export async function fetchCandles(
  ticker: string,
  options?: {
    interval?: '1m' | '5m' | '15m' | '1h'
    start_time?: number
    end_time?: number
    limit?: number
  }
): Promise<CandleData> {
  const params = new URLSearchParams()
  if (options?.interval) params.append('interval', options.interval)
  if (options?.start_time) params.append('start_time', options.start_time.toString())
  if (options?.end_time) params.append('end_time', options.end_time.toString())
  if (options?.limit) params.append('limit', options.limit.toString())

  const url = `${API_URL}/api/markets/${ticker}/candles${params.toString() ? `?${params.toString()}` : ''}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch candles: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch recent trade history
 */
export async function fetchTrades(ticker: string, limit?: number): Promise<TradeHistory> {
  const url = limit
    ? `${API_URL}/api/markets/${ticker}/trades?limit=${limit}`
    : `${API_URL}/api/markets/${ticker}/trades`

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch trades: ${response.statusText}`)
  }
  return response.json()
}
