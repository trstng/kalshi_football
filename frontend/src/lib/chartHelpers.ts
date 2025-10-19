import { supabase } from './supabase'

export interface MarketTick {
  timestamp: number
  yes_ask: number
  no_ask: number
  favorite_price: number
}

export interface Candle {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number // number of ticks in this candle
}

export interface TradeMarker {
  timestamp: number
  price: number
  type: 'entry' | 'exit'
  size: number
  pnl?: number
}

/**
 * Aggregate tick data into 1-minute OHLC candles
 */
export function aggregateTicksToCandles(ticks: MarketTick[]): Candle[] {
  if (ticks.length === 0) return []

  // Sort ticks by timestamp
  const sortedTicks = [...ticks].sort((a, b) => a.timestamp - b.timestamp)

  // Group ticks into 1-minute buckets
  const buckets = new Map<number, MarketTick[]>()

  for (const tick of sortedTicks) {
    // Round down to nearest minute
    const minuteTimestamp = Math.floor(tick.timestamp / 60) * 60

    if (!buckets.has(minuteTimestamp)) {
      buckets.set(minuteTimestamp, [])
    }
    buckets.get(minuteTimestamp)!.push(tick)
  }

  // Convert buckets to candles
  const candles: Candle[] = []

  for (const [timestamp, ticksInMinute] of buckets.entries()) {
    if (ticksInMinute.length === 0) continue

    const prices = ticksInMinute.map(t => t.yes_ask)

    candles.push({
      timestamp,
      open: ticksInMinute[0].yes_ask,
      high: Math.max(...prices),
      low: Math.min(...prices),
      close: ticksInMinute[ticksInMinute.length - 1].yes_ask,
      volume: ticksInMinute.length,
    })
  }

  return candles.sort((a, b) => a.timestamp - b.timestamp)
}

/**
 * Fetch market ticks for a specific game
 */
export async function fetchGameTicks(gameId: string): Promise<MarketTick[]> {
  const { data, error } = await supabase
    .from('market_ticks')
    .select('timestamp, yes_ask, no_ask, favorite_price')
    .eq('game_id', gameId)
    .order('timestamp', { ascending: true })

  if (error) {
    console.error('Error fetching ticks:', error)
    return []
  }

  return data || []
}

/**
 * Fetch entry/exit markers for a specific game
 */
export async function fetchTradeMarkers(gameId: string): Promise<TradeMarker[]> {
  const { data: positions, error } = await supabase
    .from('positions')
    .select('entry_time, entry_price, exit_time, exit_price, size, pnl')
    .eq('game_id', gameId)

  if (error) {
    console.error('Error fetching positions:', error)
    return []
  }

  if (!positions) return []

  const markers: TradeMarker[] = []

  for (const position of positions) {
    // Entry marker
    markers.push({
      timestamp: position.entry_time,
      price: position.entry_price,
      type: 'entry',
      size: position.size,
    })

    // Exit marker (if position was closed)
    if (position.exit_time && position.exit_price) {
      markers.push({
        timestamp: position.exit_time,
        price: position.exit_price,
        type: 'exit',
        size: position.size,
        pnl: position.pnl,
      })
    }
  }

  return markers.sort((a, b) => a.timestamp - b.timestamp)
}

/**
 * Fetch all games with tick data
 */
export async function fetchGamesWithData(): Promise<Array<{ id: string; title: string; ticker: string; kickoff_ts: number }>> {
  const { data, error } = await supabase
    .from('games')
    .select('id, market_title, market_ticker, kickoff_ts')
    .order('kickoff_ts', { ascending: false })
    .limit(100) // Last 100 games

  if (error) {
    console.error('Error fetching games:', error)
    return []
  }

  if (!data) return []

  // Filter to only games that have tick data
  const gamesWithTicks = []

  for (const game of data) {
    const { count } = await supabase
      .from('market_ticks')
      .select('*', { count: 'exact', head: true })
      .eq('game_id', game.id)

    if (count && count > 0) {
      gamesWithTicks.push({
        id: game.id,
        title: game.market_title,
        ticker: game.market_ticker,
        kickoff_ts: game.kickoff_ts,
      })
    }
  }

  return gamesWithTicks
}
