-- Kalshi NFL Trading Dashboard Schema
-- Run this SQL in your Supabase SQL Editor

-- Table: games
-- Tracks NFL games being monitored for trading opportunities
CREATE TABLE IF NOT EXISTS games (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  market_ticker TEXT NOT NULL,
  event_ticker TEXT NOT NULL,
  market_title TEXT NOT NULL,
  yes_subtitle TEXT,
  kickoff_ts BIGINT NOT NULL,
  halftime_ts BIGINT,
  pregame_prob DECIMAL(5,4),
  status TEXT NOT NULL CHECK (status IN ('monitoring', 'triggered', 'completed', 'timeout')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: positions
-- Tracks all trading positions (open and closed)
CREATE TABLE IF NOT EXISTS positions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  game_id UUID REFERENCES games(id),
  market_ticker TEXT NOT NULL,
  entry_price INTEGER NOT NULL,
  size INTEGER NOT NULL,
  entry_time BIGINT NOT NULL,
  exit_price INTEGER,
  exit_time BIGINT,
  pnl DECIMAL(10,2),
  order_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('open', 'closed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: bankroll_history
-- Tracks bankroll changes over time for P&L visualization
CREATE TABLE IF NOT EXISTS bankroll_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp BIGINT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  change DECIMAL(10,2) NOT NULL,
  game_id UUID REFERENCES games(id),
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_games_kickoff ON games(kickoff_ts);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_game ON positions(game_id);
CREATE INDEX IF NOT EXISTS idx_bankroll_timestamp ON bankroll_history(timestamp);

-- Enable Row Level Security (RLS)
ALTER TABLE games ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE bankroll_history ENABLE ROW LEVEL SECURITY;

-- Create policies to allow public read access (since this is for your personal dashboard)
-- You can make these more restrictive later if needed
CREATE POLICY "Allow public read access on games" ON games FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on games" ON games FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access on games" ON games FOR UPDATE USING (true);

CREATE POLICY "Allow public read access on positions" ON positions FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on positions" ON positions FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access on positions" ON positions FOR UPDATE USING (true);

CREATE POLICY "Allow public read access on bankroll_history" ON bankroll_history FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on bankroll_history" ON bankroll_history FOR INSERT WITH CHECK (true);

-- Insert initial bankroll entry (starting with $500)
INSERT INTO bankroll_history (timestamp, amount, change, description)
VALUES (EXTRACT(EPOCH FROM NOW())::BIGINT, 500.00, 0.00, 'Initial bankroll')
ON CONFLICT DO NOTHING;
