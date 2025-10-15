import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types (auto-generated is better, but manual works)
export type Game = {
  id: string
  market_ticker: string
  event_ticker: string
  market_title: string
  yes_subtitle: string
  kickoff_ts: number
  halftime_ts: number
  pregame_prob: number | null
  // Three-checkpoint system
  odds_6h: number | null
  odds_3h: number | null
  odds_30m: number | null
  checkpoint_6h_ts: number | null
  checkpoint_3h_ts: number | null
  checkpoint_30m_ts: number | null
  is_eligible: boolean | null
  status: 'monitoring' | 'triggered' | 'completed' | 'timeout'
  created_at: string
  updated_at: string
}

export type Order = {
  id: string
  game_id: string
  market_ticker: string
  order_id: string
  price: number
  size: number
  filled_size: number
  status: 'pending' | 'filled' | 'partially_filled' | 'cancelled'
  side: 'buy' | 'sell'
  created_at: string
  updated_at: string
}

export type Position = {
  id: string
  game_id: string
  market_ticker: string
  entry_price: number
  size: number
  entry_time: number
  exit_price: number | null
  exit_time: number | null
  pnl: number | null
  order_id: string | null
  status: 'open' | 'closed'
  created_at: string
  updated_at: string
}

export type PriceSnapshot = {
  id: string
  market_ticker: string
  price: number
  timestamp: number
  created_at: string
}

export type BankrollHistory = {
  id: string
  timestamp: number
  amount: number
  change: number
  game_id: string | null
  description: string | null
  created_at: string
}
