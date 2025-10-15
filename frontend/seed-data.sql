-- Seed Data for Testing Dashboard
-- Run this in Supabase SQL Editor

-- Insert some active games
INSERT INTO games (market_ticker, event_ticker, market_title, yes_subtitle, kickoff_ts, halftime_ts, pregame_prob, status)
VALUES
  ('NFLPIT-25JAN19', 'NFL-25JAN19', 'Will the Steelers win vs Ravens?', 'Steelers win', 1737320400, 1737325800, 0.65, 'monitoring'),
  ('NFLKC-25JAN19', 'NFL-25JAN19', 'Will the Chiefs win vs Bills?', 'Chiefs win', 1737334800, 1737340200, 0.72, 'monitoring'),
  ('NFLSF-25JAN20', 'NFL-25JAN20', 'Will the 49ers win vs Packers?', '49ers win', 1737406800, 1737412200, 0.58, 'triggered');

-- Insert some positions (open and closed)
INSERT INTO positions (market_ticker, entry_price, size, entry_time, exit_price, exit_time, pnl, order_id, status)
VALUES
  -- Open position
  ('NFLSF-25JAN20', 45, 100, 1737400000, NULL, NULL, NULL, 'order_123', 'open'),
  ('NFLSF-25JAN20', 40, 150, 1737400100, NULL, NULL, NULL, 'order_124', 'open'),

  -- Closed positions (winning trades)
  ('NFLBAL-25JAN12', 35, 120, 1736700000, 65, 1736710000, 36.00, 'order_101', 'closed'),
  ('NFLDAL-25JAN12', 42, 100, 1736701000, 58, 1736711000, 16.00, 'order_102', 'closed'),

  -- Closed position (losing trade)
  ('NFLNYG-25JAN13', 55, 80, 1736800000, 45, 1736810000, -8.00, 'order_103', 'closed');

-- Insert bankroll history showing progression
INSERT INTO bankroll_history (timestamp, amount, change, description)
VALUES
  (1736600000, 500.00, 0.00, 'Starting bankroll'),
  (1736710000, 536.00, 36.00, 'Exited NFLBAL-25JAN12'),
  (1736711000, 552.00, 16.00, 'Exited NFLDAL-25JAN12'),
  (1736810000, 544.00, -8.00, 'Exited NFLNYG-25JAN13'),
  (1737400000, 544.00, 0.00, 'Entered NFLSF-25JAN20');
