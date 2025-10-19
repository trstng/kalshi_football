"""
Backtest CFB games from October 18, 2025 with CORRECT ladder exit logic.

Each ladder level is an independent trade:
- Buy at 49¢ → Sell at 55¢ (+6¢)
- Buy at 45¢ → Sell at 51¢ (+6¢)
- Buy at 40¢ → Sell at 46¢ (+6¢)
- etc.

Each trade exits independently when profitable OR at halftime timeout.
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
class LadderTrade:
    """Represents a single ladder level trade."""
    game_ticker: str
    game_title: str
    pregame_prob: float
    entry_time: int
    entry_price: int  # cents
    size: int
    exit_time: int
    exit_price: int  # cents
    exit_reason: str
    pnl_gross: float
    pnl_net: float
    hold_time_min: float


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables required")

    return create_client(url, key)


def fetch_games_from_date(client: Client, date_str: str = "2025-10-18") -> List[dict]:
    """Fetch all games from a specific date."""
    response = client.from_("games").select(
        "id, market_ticker, market_title, kickoff_ts, halftime_ts, pregame_prob, odds_30m, is_eligible"
    ).execute()

    games = []
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    for game in response.data:
        kickoff_dt = datetime.fromtimestamp(game["kickoff_ts"])
        if kickoff_dt.date() == target_date.date():
            games.append(game)

    return games


def fetch_ticks_for_game(client: Client, game_id: str) -> pd.DataFrame:
    """Fetch all market ticks for a game."""
    response = client.from_("market_ticks").select(
        "timestamp, yes_ask, no_ask, favorite_price"
    ).eq("game_id", game_id).order("timestamp").execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)
    return df


def simulate_game_ladder_backtest(
    game: dict,
    ticks_df: pd.DataFrame,
    pregame_threshold: float = 0.57,
    trigger_threshold: float = 0.50,
    ladder_levels: List[dict] = None,
    fee_per_contract: float = 0.01,
) -> List[LadderTrade]:
    """
    Simulate backtest with independent ladder trades.

    Each ladder level:
    - Enters when price drops to or below entry price
    - Exits when price rises to exit target OR at halftime
    - Is completely independent of other levels

    Args:
        game: Game metadata
        ticks_df: Market tick data
        pregame_threshold: Minimum pregame probability
        trigger_threshold: Must drop below 50% to activate ladder
        ladder_levels: List of {entry: int, size: int, target: int} dicts
        fee_per_contract: Kalshi fee per contract per side

    Returns:
        List of executed LadderTrade objects
    """
    if ticks_df.empty:
        return []

    # Check pregame qualification
    pregame_prob = game.get("pregame_prob") or game.get("odds_30m")
    if not pregame_prob or float(pregame_prob) < pregame_threshold:
        return []

    pregame_prob = float(pregame_prob)

    # Default ladder levels with entry and exit targets
    if ladder_levels is None:
        ladder_levels = [
            {"entry": 49, "size": 10, "target": 55},  # Buy 49, sell 55 (+6)
            {"entry": 45, "size": 15, "target": 51},  # Buy 45, sell 51 (+6)
            {"entry": 40, "size": 20, "target": 46},  # Buy 40, sell 46 (+6)
            {"entry": 35, "size": 25, "target": 41},  # Buy 35, sell 41 (+6)
            {"entry": 30, "size": 30, "target": 36},  # Buy 30, sell 36 (+6)
        ]

    kickoff_ts = game["kickoff_ts"]
    halftime_ts = game.get("halftime_ts") or (kickoff_ts + 5400)

    # Filter to first half
    first_half_ticks = ticks_df[
        (ticks_df["timestamp"] >= kickoff_ts) &
        (ticks_df["timestamp"] <= halftime_ts)
    ].copy()

    if first_half_ticks.empty:
        return []

    # Check if price ever drops below trigger threshold
    trigger_ticks = first_half_ticks[first_half_ticks["yes_ask"] < (trigger_threshold * 100)]
    if trigger_ticks.empty:
        return []  # Never triggered

    # Process each ladder level independently
    trades = []

    for level in ladder_levels:
        entry_price = level["entry"]
        exit_target = level["target"]
        size = level["size"]

        # Find entry point (first tick at or below entry price)
        entry_ticks = first_half_ticks[first_half_ticks["yes_ask"] <= entry_price]

        if entry_ticks.empty:
            continue  # This level never filled

        # Entry at first tick that hits our price
        entry_idx = entry_ticks.index[0]
        entry_time = entry_ticks.iloc[0]["timestamp"]
        actual_entry_price = entry_ticks.iloc[0]["yes_ask"]

        # Look for exit after entry
        after_entry = first_half_ticks.loc[entry_idx+1:]  # Start AFTER entry tick

        if after_entry.empty:
            # Entered right at the last tick, timeout immediately
            exit_time = halftime_ts
            exit_price = actual_entry_price
            exit_reason = "halftime_timeout"
        else:
            # Look for price hitting exit target
            exit_ticks = after_entry[after_entry["yes_ask"] >= exit_target]

            if not exit_ticks.empty:
                # Exit at target
                exit_idx = exit_ticks.index[0]
                exit_time = exit_ticks.iloc[0]["timestamp"]
                exit_price = exit_ticks.iloc[0]["yes_ask"]
                exit_reason = f"target_{exit_target}c"
            else:
                # Timeout at halftime
                exit_time = halftime_ts
                exit_price = after_entry.iloc[-1]["yes_ask"]
                exit_reason = "halftime_timeout"

        # Calculate P&L
        pnl_per_contract = (exit_price - actual_entry_price) / 100.0
        pnl_gross = pnl_per_contract * size

        # Fees: $0.01 per contract, both sides
        total_fees = fee_per_contract * size * 2
        pnl_net = pnl_gross - total_fees

        hold_time_min = (exit_time - entry_time) / 60.0

        trades.append(LadderTrade(
            game_ticker=game["market_ticker"],
            game_title=game["market_title"],
            pregame_prob=pregame_prob,
            entry_time=entry_time,
            entry_price=actual_entry_price,
            size=size,
            exit_time=exit_time,
            exit_price=exit_price,
            exit_reason=exit_reason,
            pnl_gross=pnl_gross,
            pnl_net=pnl_net,
            hold_time_min=hold_time_min,
        ))

    return trades


def run_backtest(
    date: str = "2025-10-18",
    pregame_threshold: float = 0.57,
    trigger_threshold: float = 0.50,
) -> tuple[List[LadderTrade], dict]:
    """Run backtest with ladder logic."""
    print("=" * 80)
    print(f"CFB LADDER BACKTEST - {date}")
    print("=" * 80)
    print(f"Strategy: Pregame favorites >= {pregame_threshold:.0%} dropping below {trigger_threshold:.0%}")
    print(f"Ladder: 49→55 (+6), 45→51 (+6), 40→46 (+6), 35→41 (+6), 30→36 (+6)")
    print(f"Each level exits independently when profitable or at halftime")
    print()

    client = get_supabase_client()

    print(f"Fetching games from {date}...")
    games = fetch_games_from_date(client, date)
    print(f"Found {len(games)} games on {date}")
    print()

    all_trades = []
    games_with_trades = 0

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['market_title']}")

        ticks_df = fetch_ticks_for_game(client, game["id"])

        if ticks_df.empty:
            print(f"  ⚠️  No tick data available")
            print()
            continue

        print(f"  📊 {len(ticks_df)} ticks captured")

        # Simulate ladder trades
        trades = simulate_game_ladder_backtest(
            game=game,
            ticks_df=ticks_df,
            pregame_threshold=pregame_threshold,
            trigger_threshold=trigger_threshold,
        )

        if trades:
            game_pnl = sum(t.pnl_net for t in trades)
            print(f"  ✅ {len(trades)} ladder trades executed: ${game_pnl:+.2f}")

            for t in trades:
                print(f"     {t.entry_price}¢ → {t.exit_price}¢ ({t.size} contracts) = ${t.pnl_net:+.2f} [{t.exit_reason}]")

            all_trades.extend(trades)
            games_with_trades += 1
        else:
            pregame = game.get("pregame_prob") or game.get("odds_30m")
            if pregame and float(pregame) >= pregame_threshold:
                print(f"  ⊘ Qualified ({float(pregame):.0%}) but no trigger")
            else:
                print(f"  ⊘ Not a strong enough favorite ({float(pregame or 0):.0%})")

        print()

    # Calculate summary
    if all_trades:
        total_pnl = sum(t.pnl_net for t in all_trades)
        win_rate = sum(1 for t in all_trades if t.pnl_net > 0) / len(all_trades)
        avg_hold = sum(t.hold_time_min for t in all_trades) / len(all_trades)

        exit_reasons = {}
        for t in all_trades:
            exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1

        summary = {
            "total_games": len(games),
            "games_with_trades": games_with_trades,
            "total_trades": len(all_trades),
            "total_pnl_net": total_pnl,
            "avg_pnl_per_trade": total_pnl / len(all_trades),
            "win_rate": win_rate,
            "avg_hold_time_min": avg_hold,
            "exit_reasons": exit_reasons,
        }
    else:
        summary = {
            "total_games": len(games),
            "games_with_trades": 0,
            "total_trades": 0,
            "total_pnl_net": 0,
            "avg_pnl_per_trade": 0,
            "win_rate": 0,
            "avg_hold_time_min": 0,
            "exit_reasons": {},
        }

    return all_trades, summary


def print_summary(trades: List[LadderTrade], summary: dict):
    """Print backtest summary."""
    print("=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"Total Games Analyzed:    {summary['total_games']}")
    print(f"Games with Trades:       {summary['games_with_trades']}")
    print(f"Total Ladder Trades:     {summary['total_trades']}")
    print()

    if summary['total_trades'] > 0:
        print(f"Total P&L (Net):         ${summary['total_pnl_net']:+,.2f}")
        print(f"Avg P&L per Trade:       ${summary['avg_pnl_per_trade']:+.2f}")
        print(f"Win Rate:                {summary['win_rate']:.1%}")
        print(f"Avg Hold Time:           {summary['avg_hold_time_min']:.1f} minutes")
        print()

        print("Exit Reason Breakdown:")
        for reason, count in sorted(summary['exit_reasons'].items()):
            pct = count / summary['total_trades'] * 100
            print(f"  {reason:25s} {count:3d} ({pct:5.1f}%)")

    print("=" * 80)


def main():
    """Run the backtest."""
    trades, summary = run_backtest(
        date="2025-10-18",
        pregame_threshold=0.57,
        trigger_threshold=0.50,
    )

    print_summary(trades, summary)

    # Save results
    if trades:
        output_path = Path("artifacts") / f"cfb_ladder_backtest_10_18_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path.parent.mkdir(exist_ok=True)

        df = pd.DataFrame([
            {
                "game": t.game_title,
                "pregame_prob": t.pregame_prob,
                "entry_time": datetime.fromtimestamp(t.entry_time).isoformat(),
                "entry_price": t.entry_price,
                "size": t.size,
                "exit_time": datetime.fromtimestamp(t.exit_time).isoformat(),
                "exit_price": t.exit_price,
                "exit_reason": t.exit_reason,
                "pnl_gross": t.pnl_gross,
                "pnl_net": t.pnl_net,
                "hold_time_min": t.hold_time_min,
            }
            for t in trades
        ])

        df.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
