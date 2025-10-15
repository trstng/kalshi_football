-- Seed Data: Dummy orders for testing dashboard
-- Date: 2025-10-15
-- Description: Sample limit orders to visualize the order tracking system

-- NOTE: You need to first have at least one game in the games table
-- Run this AFTER you have games data, or modify the game_id values below

-- Sample limit order ladder for a CFB game
-- These simulate the 5-level ladder strategy (49¢, 45¢, 41¢, 37¢, 33¢)

INSERT INTO orders (game_id, market_ticker, order_id, price, size, filled_size, status, side, created_at) VALUES
  -- Limit Order Ladder for Delaware at Jackson St game
  (
    (SELECT id FROM games WHERE market_ticker LIKE '%DELAWARE%' LIMIT 1),
    'KXNCAAFGAME-25OCT15-DEL-JAC',
    'kalshi_order_abc123xyz',
    49,  -- 49¢ limit
    15,  -- 15 contracts
    0,   -- not filled yet
    'pending',
    'buy',
    NOW() - INTERVAL '5 minutes'
  ),
  (
    (SELECT id FROM games WHERE market_ticker LIKE '%DELAWARE%' LIMIT 1),
    'KXNCAAFGAME-25OCT15-DEL-JAC',
    'kalshi_order_def456uvw',
    45,  -- 45¢ limit
    22,  -- 22 contracts (1.5x Kelly)
    0,
    'pending',
    'buy',
    NOW() - INTERVAL '5 minutes'
  ),
  (
    (SELECT id FROM games WHERE market_ticker LIKE '%DELAWARE%' LIMIT 1),
    'KXNCAAFGAME-25OCT15-DEL-JAC',
    'kalshi_order_ghi789rst',
    41,  -- 41¢ limit
    30,  -- 30 contracts (2x Kelly)
    15,  -- partially filled!
    'partially_filled',
    'buy',
    NOW() - INTERVAL '5 minutes'
  ),
  (
    (SELECT id FROM games WHERE market_ticker LIKE '%DELAWARE%' LIMIT 1),
    'KXNCAAFGAME-25OCT15-DEL-JAC',
    'kalshi_order_jkl012opq',
    37,  -- 37¢ limit
    37,  -- 37 contracts (2.5x Kelly)
    37,  -- fully filled!
    'filled',
    'buy',
    NOW() - INTERVAL '3 minutes'
  ),
  (
    (SELECT id FROM games WHERE market_ticker LIKE '%DELAWARE%' LIMIT 1),
    'KXNCAAFGAME-25OCT15-DEL-JAC',
    'kalshi_order_mno345lmn',
    33,  -- 33¢ limit
    45,  -- 45 contracts (3x Kelly)
    45,  -- fully filled!
    'filled',
    'buy',
    NOW() - INTERVAL '2 minutes'
  );

-- Alternative: If you don't have games yet, create dummy order data without game_id
-- Uncomment the section below and comment out the section above

/*
INSERT INTO orders (game_id, market_ticker, order_id, price, size, filled_size, status, side, created_at) VALUES
  -- Example without game_id (will show as orphan orders)
  (
    NULL,
    'KXNFLGAME-25OCT20-BUF-NE',
    'kalshi_order_test001',
    49,
    15,
    0,
    'pending',
    'buy',
    NOW() - INTERVAL '10 minutes'
  ),
  (
    NULL,
    'KXNFLGAME-25OCT20-BUF-NE',
    'kalshi_order_test002',
    45,
    22,
    5,
    'partially_filled',
    'buy',
    NOW() - INTERVAL '8 minutes'
  ),
  (
    NULL,
    'KXNFLGAME-25OCT20-BUF-NE',
    'kalshi_order_test003',
    41,
    30,
    30,
    'filled',
    'buy',
    NOW() - INTERVAL '5 minutes'
  ),
  (
    NULL,
    'KXNCAAFGAME-25OCT15-ALA-TEN',
    'kalshi_order_test004',
    49,
    20,
    0,
    'pending',
    'buy',
    NOW() - INTERVAL '15 minutes'
  ),
  (
    NULL,
    'KXNCAAFGAME-25OCT15-ALA-TEN',
    'kalshi_order_test005',
    45,
    30,
    10,
    'partially_filled',
    'buy',
    NOW() - INTERVAL '12 minutes'
  );
*/

-- Verify the data was inserted
SELECT
  market_ticker,
  order_id,
  price,
  size,
  filled_size,
  status,
  created_at
FROM orders
ORDER BY created_at DESC;
