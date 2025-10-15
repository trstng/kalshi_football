-- Migration: Add orders table for limit order tracking
-- Date: 2025-10-15
-- Description: Track all placed orders (pending/filled/cancelled) separately from positions

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  game_id UUID REFERENCES games(id),
  market_ticker TEXT NOT NULL,
  order_id TEXT NOT NULL UNIQUE,  -- Kalshi order ID
  price INTEGER NOT NULL,  -- in cents
  size INTEGER NOT NULL,   -- total contracts ordered
  filled_size INTEGER DEFAULT 0,  -- contracts actually filled
  status TEXT NOT NULL,    -- 'pending', 'filled', 'partially_filled', 'cancelled'
  side TEXT NOT NULL,      -- 'buy' or 'sell'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_orders_market_ticker ON orders(market_ticker);
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_game_id ON orders(game_id);

-- Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed)
CREATE POLICY "Allow public read access on orders" ON orders FOR SELECT USING (true);
CREATE POLICY "Allow public insert access on orders" ON orders FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access on orders" ON orders FOR UPDATE USING (true);

-- Add helpful comments
COMMENT ON TABLE orders IS 'All placed orders with their fill status - orders become positions when filled';
COMMENT ON COLUMN orders.order_id IS 'Kalshi order ID for tracking fill status';
COMMENT ON COLUMN orders.status IS 'pending = waiting to fill, filled = completely filled, partially_filled = some filled, cancelled = cancelled';
COMMENT ON COLUMN orders.filled_size IS 'Number of contracts actually filled (can be less than size)';
