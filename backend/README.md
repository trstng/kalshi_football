# Backend - Kalshi Trading Bot

This directory contains the Python trading bot and all backend logic.

## Structure

```
backend/
├── live_trader_fixed.py          # Main trading bot (USE THIS ONE)
├── live_trading_config.yaml      # Bot configuration
├── test_setup.py                 # Setup verification script
├── verify_game_discovery.py      # Test game discovery
├── src/                          # Source code modules
│   └── kalshi_nfl_research/
│       ├── kalshi_client.py      # Kalshi API client
│       ├── trading_client.py     # Order placement client
│       └── ...
├── artifacts/                    # Schedule CSVs and data
│   ├── nfl_markets_2025_enriched.csv
│   ├── cfb_markets_2025_enriched.csv
│   └── ...
├── logs/                         # Bot logs
│   └── live_trading.log
├── docs/                         # Documentation
│   ├── BOT_OPERATION_GUIDE.md
│   ├── COMMANDS.txt
│   ├── LIVE_TRADING_SETUP.md
│   └── ...
├── tests/                        # Unit tests
└── requirements_trading.txt      # Python dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements_trading.txt
```

### 2. Configure Bot

Edit `live_trading_config.yaml`:
- Set your Kalshi API credentials
- Adjust trading parameters
- Set `dry_run: true` for testing

### 3. Run Bot

```bash
# Dry run (safe, no real orders)
python3 live_trader_fixed.py

# Keep Mac awake while running
caffeinate -i python3 live_trader_fixed.py
```

### 4. Monitor Logs

```bash
tail -f logs/live_trading.log
```

### 5. Stop Bot

Press `Ctrl+C` or:
```bash
ps aux | grep live_trader_fixed.py
kill <PID>
```

## Configuration

See `live_trading_config.yaml` for all settings:
- **Bankroll**: Starting capital
- **Kelly fraction**: Position sizing (15% = 1/4 Kelly)
- **Max exposure**: Maximum per game (50%)
- **Scaling levels**: Entry prices (49¢, 45¢, 41¢, etc.)
- **Revert bands**: Exit targets (55%, 60%, 65%, 70%)
- **Dry run**: Enable/disable real trading

## Documentation

See `docs/` folder:
- `BOT_OPERATION_GUIDE.md` - How the bot works
- `LIVE_TRADING_SETUP.md` - Complete setup guide
- `COMMANDS.txt` - Quick reference
- `SCHEDULE_FIX_SUMMARY.md` - Schedule data explanation

## Important Files

- **`live_trader_fixed.py`** - Main bot (uses external schedules)
- **`live_trader.py`** - Old version (don't use, assumes Kalshi has strike_date)
- **`live_trading_config.yaml`** - Configuration
- **`artifacts/nfl_markets_2025_enriched.csv`** - NFL games with kickoff times
- **`artifacts/cfb_markets_2025_enriched.csv`** - CFB games with kickoff times

## Development

### Run Backtest

```bash
python3 run_backtest_with_schedule.py
```

### Test Setup

```bash
python3 test_setup.py
```

### Verify Game Discovery

```bash
python3 verify_game_discovery.py
```

## Deployment

For 24/7 operation, deploy to:
- **Railway** (recommended, $5/month)
- **fly.io** (free tier available)
- **DigitalOcean App Platform** ($5/month)
- **Render** (free tier with limitations)

See `docs/LIVE_TRADING_SETUP.md` for deployment instructions.

## Next Steps

1. Test in dry run mode
2. Verify trades log correctly
3. Deploy to cloud for 24/7 operation
4. Add Supabase integration (see `../planning/DASHBOARD_IMPLEMENTATION_PLAN.md`)
5. Build frontend dashboard (see `../frontend/`)
