"""
Backtest CFB games from October 18, 2025 using Supabase market tick data.

Strategy:
- Pregame favorites (>= 57%) dropping below 50%
- Laddered entries from 49 down to 30 cents
- Exit when price reverts back to 50s in first half

This uses orderbook tick data from Supabase instead of trade history from Kalshi API.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from supabase import create_client, Client


@dataclass
class Trade:
    """Represents a single executed trade."""
    game_ticker: str
    game_title: str
    pregame_prob: float
    entry_time: int
    entry_price: int  # cents
    size: int  # contracts
    exit_time: int
    exit_price: int  # cents
    exit_reason: str
    pnl_gross: float  # dollars
    pnl_net: float  # dollars (after fees)
    hold_time_min: float


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables required")

    return create_client(url, key)


def fetch_games_from_date(client: Client, date_str: str = "2025-10-18") -> List[dict]:
    """
    Fetch all games from a specific date with their tick data.

    Args:
        client: Supabase client
        date_str: Date in YYYY-MM-DD format

    Returns:
        List of game dictionaries with metadata
    """
    # Query games from the specified date
    response = client.from_("games").select(
        "id, market_ticker, market_title, kickoff_ts, halftime_ts, pregame_prob, odds_30m, is_eligible"
    ).execute()

    games = []
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    for game in response.data:
        kickoff_dt = datetime.utcfromtimestamp(game["kickoff_ts"])
        if kickoff_dt.date() == target_date.date():
            games.append(game)

    return games


def fetch_ticks_for_game(client: Client, game_id: str) -> pd.DataFrame:
    """
    Fetch all market ticks for a game.

    Args:
        client: Supabase client
        game_id: Game UUID

    Returns:
        DataFrame with columns: timestamp, yes_ask, no_ask, favorite_price
    """
    response = client.from_("market_ticks").select(
        "timestamp, yes_ask, no_ask, favorite_price"
    ).eq("game_id", game_id).order("timestamp").execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)
    return df


def simulate_game_backtest(
    game: dict,
    ticks_df: pd.DataFrame,
    pregame_threshold: float = 0.57,
    trigger_threshold: float = 0.50,
    entry_levels: List[dict] = None,
    exit_target: float = 0.50,
    fee_per_contract: float = 0.01,
) -> Optional[Trade]:
    """
    Simulate backtest for a single game.

    Args:
        game: Game metadata dict
        ticks_df: DataFrame of market ticks
        pregame_threshold: Minimum pregame probability to qualify (0.57 = 57%)
        trigger_threshold: Price must drop below this to trigger (0.50 = 50%)
        entry_levels: List of entry price levels with sizes
        exit_target: Exit when price reaches this level
        fee_per_contract: Kalshi fee per contract per side

    Returns:
        Trade object if executed, None otherwise
    """
    if ticks_df.empty:
        return None

    # Check if game qualifies based on pregame favorite
    pregame_prob = game.get("pregame_prob") or game.get("odds_30m")
    if not pregame_prob or float(pregame_prob) < pregame_threshold:
        return None

    pregame_prob = float(pregame_prob)

    # Default entry levels (laddered from 49 to 30)
    if entry_levels is None:
        entry_levels = [
            {"price": 49, "size": 10},
            {"price": 45, "size": 15},
            {"price": 40, "size": 20},
            {"price": 35, "size": 25},
            {"price": 30, "size": 30},
        ]

    kickoff_ts = game["kickoff_ts"]
    halftime_ts = game.get("halftime_ts") or (kickoff_ts + 5400)  # 90 min default

    # Filter ticks to first half only
    first_half_ticks = ticks_df[
        (ticks_df["timestamp"] >= kickoff_ts) &
        (ticks_df["timestamp"] <= halftime_ts)
    ].copy()

    if first_half_ticks.empty:
        return None

    # Convert prices to probabilities (cents / 100)
    first_half_ticks["price"] = first_half_ticks["yes_ask"] / 100.0

    # Find trigger point (first time price drops below 50%)
    trigger_ticks = first_half_ticks[first_half_ticks["price"] < trigger_threshold]

    if trigger_ticks.empty:
        return None  # Never triggered

    trigger_idx = trigger_ticks.index[0]
    trigger_time = trigger_ticks.iloc[0]["timestamp"]
    trigger_price = trigger_ticks.iloc[0]["yes_ask"]

    # Determine which entry levels we hit
    entries = []
    for level in entry_levels:
        if trigger_price <= level["price"]:
            entries.append(level)

    if not entries:
        return None  # Price didn't drop far enough to hit any levels

    # Calculate weighted average entry price and total size
    total_size = sum(e["size"] for e in entries)
    total_capital = sum(e["price"] * e["size"] for e in entries)
    avg_entry_price = total_capital / total_size

    # Look for exit (price rebounds to exit_target or better)
    exit_target_cents = int(exit_target * 100)

    after_entry_ticks = first_half_ticks.loc[trigger_idx:]
    exit_ticks = after_entry_ticks[after_entry_ticks["yes_ask"] >= exit_target_cents]

    if not exit_ticks.empty:
        # Exit at reversion
        exit_idx = exit_ticks.index[0]
        exit_time = exit_ticks.iloc[0]["timestamp"]
        exit_price = exit_ticks.iloc[0]["yes_ask"]
        exit_reason = f"revert_to_{exit_target_cents}c"
    else:
        # Timeout at halftime
        exit_time = halftime_ts
        exit_price = after_entry_ticks.iloc[-1]["yes_ask"]
        exit_reason = "halftime_timeout"

    # Calculate P&L
    pnl_per_contract = (exit_price - avg_entry_price) / 100.0
    pnl_gross = pnl_per_contract * total_size

    # Fees: $0.01 per contract per side (entry + exit)
    total_fees = fee_per_contract * total_size * 2
    pnl_net = pnl_gross - total_fees

    hold_time_min = (exit_time - trigger_time) / 60.0

    return Trade(
        game_ticker=game["market_ticker"],
        game_title=game["market_title"],
        pregame_prob=pregame_prob,
        entry_time=trigger_time,
        entry_price=int(avg_entry_price),
        size=total_size,
        exit_time=exit_time,
        exit_price=exit_price,
        exit_reason=exit_reason,
        pnl_gross=pnl_gross,
        pnl_net=pnl_net,
        hold_time_min=hold_time_min,
    )


def run_backtest(
    date: str = "2025-10-18",
    pregame_threshold: float = 0.57,
    trigger_threshold: float = 0.50,
    exit_target: float = 0.50,
) -> tuple[List[Trade], dict]:
    """
    Run backtest on all games from a specific date.

    Args:
        date: Date string in YYYY-MM-DD format
        pregame_threshold: Minimum pregame favorite probability
        trigger_threshold: Entry trigger threshold
        exit_target: Exit target price

    Returns:
        (trades, summary_stats)
    """
    print("=" * 80)
    print(f"CFB BACKTEST - {date}")
    print("=" * 80)
    print(f"Strategy: Pregame favorites >= {pregame_threshold:.0%} dropping below {trigger_threshold:.0%}")
    print(f"Entry: Laddered bids 49→30 cents")
    print(f"Exit: Revert to {exit_target:.0%} or halftime timeout")
    print()

    # Connect to Supabase
    print("Connecting to Supabase...")
    client = get_supabase_client()

    # Fetch games
    print(f"Fetching games from {date}...")
    games = fetch_games_from_date(client, date)
    print(f"Found {len(games)} games on {date}")
    print()

    # Run backtest on each game
    trades = []
    games_qualified = 0
    games_triggered = 0

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['market_title']}")

        # Fetch tick data
        ticks_df = fetch_ticks_for_game(client, game["id"])

        if ticks_df.empty:
            print(f"  ⚠️  No tick data available")
            continue

        print(f"  📊 {len(ticks_df)} ticks captured")

        # Simulate trade
        trade = simulate_game_backtest(
            game=game,
            ticks_df=ticks_df,
            pregame_threshold=pregame_threshold,
            trigger_threshold=trigger_threshold,
            exit_target=exit_target,
        )

        if trade:
            pregame_pct = trade.pregame_prob * 100
            entry_pct = trade.entry_price
            exit_pct = trade.exit_price

            print(f"  ✅ TRADE: {pregame_pct:.0f}% → {entry_pct}¢ → {exit_pct}¢ = ${trade.pnl_net:+.2f}")
            print(f"     {trade.size} contracts, {trade.hold_time_min:.1f} min hold, {trade.exit_reason}")

            trades.append(trade)
            games_triggered += 1
        else:
            # Check if it qualified
            pregame = game.get("pregame_prob") or game.get("odds_30m")
            if pregame and float(pregame) >= pregame_threshold:
                print(f"  ⊘ Qualified ({float(pregame):.0%}) but no trigger")
                games_qualified += 1
            else:
                print(f"  ⊘ Not a strong enough favorite ({float(pregame or 0):.0%})")

        print()

    # Calculate summary statistics
    if trades:
        total_pnl = sum(t.pnl_net for t in trades)
        avg_pnl = total_pnl / len(trades)
        win_rate = sum(1 for t in trades if t.pnl_net > 0) / len(trades)
        avg_hold = sum(t.hold_time_min for t in trades) / len(trades)

        # Exit reason breakdown
        exit_reasons = {}
        for t in trades:
            exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1

        summary = {
            "total_games": len(games),
            "games_qualified": games_qualified + games_triggered,
            "games_triggered": games_triggered,
            "trades_executed": len(trades),
            "total_pnl_net": total_pnl,
            "avg_pnl_per_trade": avg_pnl,
            "win_rate": win_rate,
            "avg_hold_time_min": avg_hold,
            "exit_reasons": exit_reasons,
        }
    else:
        summary = {
            "total_games": len(games),
            "games_qualified": 0,
            "games_triggered": 0,
            "trades_executed": 0,
            "total_pnl_net": 0,
            "avg_pnl_per_trade": 0,
            "win_rate": 0,
            "avg_hold_time_min": 0,
            "exit_reasons": {},
        }

    return trades, summary


def print_summary(trades: List[Trade], summary: dict):
    """Print backtest summary."""
    print("=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"Total Games Analyzed:    {summary['total_games']}")
    print(f"Games Qualified:         {summary['games_qualified']}")
    print(f"Games Triggered:         {summary['games_triggered']}")
    print(f"Trades Executed:         {summary['trades_executed']}")
    print()

    if summary['trades_executed'] > 0:
        print(f"Total P&L (Net):         ${summary['total_pnl_net']:+,.2f}")
        print(f"Avg P&L per Trade:       ${summary['avg_pnl_per_trade']:+.2f}")
        print(f"Win Rate:                {summary['win_rate']:.1%}")
        print(f"Avg Hold Time:           {summary['avg_hold_time_min']:.1f} minutes")
        print()

        print("Exit Reason Breakdown:")
        for reason, count in summary['exit_reasons'].items():
            pct = count / summary['trades_executed'] * 100
            print(f"  {reason:25s} {count:3d} ({pct:5.1f}%)")
        print()

        # Show individual trades
        print("-" * 80)
        print("INDIVIDUAL TRADES:")
        print("-" * 80)
        for i, t in enumerate(trades, 1):
            entry_dt = datetime.utcfromtimestamp(t.entry_time).strftime('%H:%M:%S')
            print(f"{i:2d}. {t.game_title}")
            print(f"    {t.pregame_prob:.0%} → {t.entry_price}¢ @ {entry_dt} → {t.exit_price}¢ ({t.exit_reason})")
            print(f"    {t.size} contracts × ${(t.exit_price - t.entry_price)/100:+.2f} = ${t.pnl_net:+.2f}")
            print()

    print("=" * 80)


def main():
    """Run the backtest."""
    # Run backtest with specified parameters
    trades, summary = run_backtest(
        date="2025-10-18",
        pregame_threshold=0.57,  # 57%+
        trigger_threshold=0.50,  # Entry below 50%
        exit_target=0.50,        # Exit at 50%+ reversion
    )

    # Print results
    print_summary(trades, summary)

    # Save results to CSV
    if trades:
        output_path = Path("artifacts") / f"cfb_backtest_10_18_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path.parent.mkdir(exist_ok=True)

        df = pd.DataFrame([
            {
                "game": t.game_title,
                "pregame_prob": t.pregame_prob,
                "entry_time": datetime.utcfromtimestamp(t.entry_time).isoformat(),
                "entry_price": t.entry_price,
                "size": t.size,
                "exit_time": datetime.utcfromtimestamp(t.exit_time).isoformat(),
                "exit_price": t.exit_price,
                "exit_reason": t.exit_reason,
                "pnl_gross": t.pnl_gross,
                "pnl_net": t.pnl_net,
                "hold_time_min": t.hold_time_min,
            }
            for t in trades
        ])

        df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
