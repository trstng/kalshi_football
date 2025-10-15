# Kalshi NFL Trading Bot & Dashboard

Automated NFL trading bot for Kalshi prediction markets with real-time dashboard visualization.

## 🚀 Features

- **Automated Trading Bot**: Monitors NFL games and executes trades based on probability movements
- **Real-Time Dashboard**: Beautiful React dashboard with live P&L tracking
- **Supabase Integration**: Centralized database for games, positions, and bankroll history
- **Dark Theme UI**: Modern, professional trading floor aesthetic
- **Live Charts**: Bankroll visualization and performance analytics

## 📁 Project Structure

```
kalshi_nfl_research/
├── backend/              # Python trading bot
│   ├── live_trader_fixed.py
│   ├── supabase_logger.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # React dashboard
│   ├── src/
│   ├── package.json
│   └── .env.example
└── README.md
```

## 🛠️ Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- Kalshi API credentials (for live trading)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from template:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`

5. Run the bot:
```bash
python3 live_trader_fixed.py
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file from template:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`

5. Start development server:
```bash
npm run dev
```

### Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)

2. Run the SQL schema in Supabase SQL Editor:
   - Execute `frontend/supabase-schema.sql`
   
3. (Optional) Load seed data for testing:
   - Execute `frontend/seed-data.sql`

## 🚢 Deployment

### Frontend (Vercel)

1. Push code to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Add environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
5. Deploy!

### Backend (Railway)

1. Import project from GitHub
2. Set root directory to `backend`
3. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - (Optional) Kalshi API credentials
4. Set start command: `python3 live_trader_fixed.py`
5. Deploy!

## 📊 Dashboard Features

- **Live Trading Dashboard**: Monitor active games and open positions
- **Trade History**: View all closed positions with P&L breakdown
- **Analytics**: Performance charts and bankroll visualization
- **Real-time Updates**: Supabase subscriptions for live data

## 🔐 Environment Variables

### Backend
```env
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-key
```

### Frontend
```env
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-key
```

## 📝 License

MIT License

## 🤝 Contributing

Pull requests welcome! 

---

Built with ❤️ for NFL trading on Kalshi
