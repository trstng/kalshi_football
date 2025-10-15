# Database Migrations

This directory contains SQL migration scripts for the Supabase database.

## How to Apply Migrations

1. Log into your Supabase dashboard at https://supabase.com
2. Navigate to your project
3. Go to SQL Editor
4. Copy and paste the contents of the migration file
5. Execute the SQL

## Migration History

### 001_add_checkpoint_columns.sql
**Date**: 2025-10-15
**Status**: Applied

Adds the three-checkpoint trading system:
- `odds_6h`, `odds_3h`, `odds_30m` - Odds captured at each checkpoint
- `checkpoint_6h_ts`, `checkpoint_3h_ts`, `checkpoint_30m_ts` - Timestamps for each checkpoint
- `is_eligible` - Trading eligibility flag based on checkpoint rules

**Eligibility Rules**:
- If ANY checkpoint >= 57% → Eligible
- BUT if odds_30m < 57% → NOT eligible (final veto)

### 002_add_market_ticks_table.sql
**Date**: 2025-10-15
**Status**: Pending

Adds tick data collection for backtesting:
- `market_ticks` table - Stores price snapshots captured every 10 seconds
- Captures: timestamp, favorite_price, yes_ask, no_ask
- Linked to games table via game_id foreign key
- Automatically populated by live trader during monitoring
