-- Migration: Add market_ticks table for price history
-- Date: 2025-10-15
-- Description: Stores all price snapshots from live monitoring for backtesting

-- Create market_ticks table
CREATE TABLE IF NOT EXISTS market_ticks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  market_ticker TEXT NOT NULL,
  game_id UUID REFERENCES games(id),
  timestamp BIGINT NOT NULL,
  favorite_price DECIMAL(5,4) NOT NULL,
  yes_ask INTEGER,
  no_ask INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_market_ticks_ticker ON market_ticks(market_ticker);
CREATE INDEX IF NOT EXISTS idx_market_ticks_timestamp ON market_ticks(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_ticks_game_id ON market_ticks(game_id);
CREATE INDEX IF NOT EXISTS idx_market_ticks_ticker_timestamp ON market_ticks(market_ticker, timestamp);

-- Enable Row Level Security
ALTER TABLE market_ticks ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed)
CREATE POLICY "Allow public read access on market_ticks" ON market_ticks FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on market_ticks" ON market_ticks FOR INSERT WITH CHECK (true);

-- Add helpful comments
COMMENT ON TABLE market_ticks IS 'Historical price snapshots from live monitoring, captured every 10 seconds';
COMMENT ON COLUMN market_ticks.favorite_price IS 'Max of yes_ask and no_ask, representing favorite probability (0-1)';
COMMENT ON COLUMN market_ticks.yes_ask IS 'Price to buy YES in cents';
COMMENT ON COLUMN market_ticks.no_ask IS 'Price to buy NO in cents';
COMMENT ON COLUMN market_ticks.timestamp IS 'Unix timestamp in seconds when price was captured';
