# Frontend - Kalshi Trading Dashboard

This directory will contain the Next.js dashboard for monitoring the trading bot in real-time.

## Coming Soon

The dashboard will provide:
- 📊 **Real-time monitoring** of active games
- 💰 **Live P&L tracking** with charts
- 📈 **Trade history** with win rate stats
- 🎯 **Open positions** view
- 📉 **Price charts** per game
- 🔔 **Alerts** (future enhancement)

## Planned Stack

- **Framework**: Vite + React 18 + TypeScript
- **Routing**: React Router v6
- **Database**: Supabase (PostgreSQL + real-time subscriptions)
- **Styling**: Tailwind CSS + shadcn/ui
- **Charts**: Recharts
- **Hosting**: Vercel (free tier)

## Implementation Plan

See `../planning/DASHBOARD_IMPLEMENTATION_PLAN.md` for complete step-by-step guide.

## Pages

1. **Dashboard** (`/`)
   - Active games being monitored
   - Open positions with live P&L
   - Current bankroll
   - Quick stats

2. **Trade History** (`/history`)
   - All completed trades
   - Win rate statistics
   - Profit/loss breakdown
   - Filter by date, game, outcome

3. **Analytics** (`/analytics`)
   - Bankroll chart over time
   - P&L distribution
   - Win rate by day/week
   - Strategy performance metrics

4. **Game Detail** (`/game/[ticker]`)
   - Price chart for specific game
   - Entry/exit timeline
   - Position details
   - Market info

## Features

### Real-time Updates
- Supabase real-time subscriptions
- Updates appear instantly when bot trades
- No page refresh needed

### Data Persistence
- All trades stored in Supabase
- Historical data for backtesting UI
- Bot restarts don't lose history

### Mobile Responsive
- Works on desktop, tablet, mobile
- Touch-friendly charts
- Optimized for small screens

## Architecture

```
Frontend (Vercel)
    ↓ (Supabase Client)
Supabase (PostgreSQL + REST API)
    ↑ (Python supabase-py)
Backend Bot (Railway)
```

## Cost

- **Vercel**: Free (unlimited deployments)
- **Supabase**: Free tier (500MB DB, 2GB bandwidth)
- **Total**: $0/month for frontend + database

## Development Setup (When Ready)

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
# Create .env with:
# VITE_SUPABASE_URL=https://xxx.supabase.co
# VITE_SUPABASE_ANON_KEY=your-anon-key

# Run dev server
npm run dev

# Open http://localhost:5173
```

## Deployment (When Ready)

1. Push to GitHub
2. Connect to Vercel
3. Configure:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
5. Deploy (automatic on push)

## Current Status

⚠️ **Not yet implemented**

To build this dashboard:
1. Follow `../planning/DASHBOARD_IMPLEMENTATION_PLAN.md`
2. Phase 1: Supabase Setup
3. Phase 2: Modify Backend Bot
4. Phase 3: Deploy Bot to Railway
5. Phase 4: Build Vite + React Dashboard
6. Phase 5: Deploy Dashboard to Vercel

## Preview

When complete, the dashboard will look like:

### Dashboard Page
```
┌─────────────────────────────────────────────────┐
│ Kalshi Trading Dashboard                        │
├─────────────────────────────────────────────────┤
│ Bankroll: $534  Active Games: 2  Positions: 1  │
├─────────────────────────────────────────────────┤
│ Active Games                                    │
│ ┌──────────────────┬────────┬─────────┬────────┐│
│ │ Game             │ Pregame│ Current │ Status ││
│ ├──────────────────┼────────┼─────────┼────────┤│
│ │ PIT @ CIN        │ 70%    │ 68%     │ Watch  ││
│ │ DAL @ PHI        │ 65%    │ 48%     │ Active ││
│ └──────────────────┴────────┴─────────┴────────┘│
│                                                  │
│ Open Positions                                  │
│ ┌──────────┬───────┬──────┬─────────┐          │
│ │ Market   │ Entry │ Size │ P&L     │          │
│ ├──────────┼───────┼──────┼─────────┤          │
│ │ DAL@PHI  │ 48¢   │ 50   │ +$4.00  │          │
│ └──────────┴───────┴──────┴─────────┘          │
└─────────────────────────────────────────────────┘
```

### Analytics Page
```
┌─────────────────────────────────────────────────┐
│ Analytics                                        │
├─────────────────────────────────────────────────┤
│ Total P&L: +$34  Trades: 12  Win Rate: 75%     │
├─────────────────────────────────────────────────┤
│ Bankroll Over Time                              │
│ ┌─────────────────────────────────────────────┐ │
│ │         📈                                  │ │
│ │    $540┤         ╱╲                        │ │
│ │    $520┤    ╱╲  ╱  ╲   ╱╲                 │ │
│ │    $500┤───╱──╲╱────╲─╱──╲────────────    │ │
│ │        └─────────────────────────────────  │ │
│ │         Mon  Tue  Wed  Thu  Fri  Sat  Sun  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ Backend organized in `../backend/`
2. ⏳ Create Supabase project
3. ⏳ Modify bot to write to Supabase
4. ⏳ Build Vite + React dashboard here
5. ⏳ Deploy to Vercel

See implementation plan for detailed steps!

## Tech Stack Benefits

**Why Vite + React over Next.js?**
- ⚡ Faster development with instant HMR
- 🎯 Simpler setup - no SSR/API routes complexity
- 📊 Same chart libraries work identically (Recharts)
- 🔌 Same Supabase integration (language-agnostic)
- 🚀 Lighter bundle size for dashboard use case
- 💰 Same free hosting on Vercel

The data flow is identical regardless of framework:
```
Python Bot → Supabase → React Dashboard
```
