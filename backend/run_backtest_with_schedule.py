"""
Run backtest using enriched schedule data with external kickoff times.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.discovery import discover_games_with_markets
from kalshi_nfl_research.backtest import run_backtest
from kalshi_nfl_research.data_models import BacktestConfig
from kalshi_nfl_research.fetch import fetch_game_data
from kalshi_nfl_research.io_utils import (
    save_summary_markdown,
    save_trades_csv,
    save_band_metrics_csv,
    save_parquet,
)

def load_kickoff_times(csv_path: str) -> dict[str, int]:
    """
    Load kickoff times from enriched CSV.

    Returns:
        Dict mapping event_ticker -> Unix timestamp
    """
    kickoffs = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row['event_ticker']
            strike_date = row.get('strike_date', '')

            if strike_date and strike_date != '':
                kickoffs[ticker] = int(strike_date)

    return kickoffs


def main():
    # Configuration
    enriched_csv = 'artifacts/nfl_games_2025_with_kickoffs.csv'
    output_dir = Path('artifacts')

    print("=" * 60)
    print("RUNNING BACKTEST WITH EXTERNAL SCHEDULE DATA")
    print("=" * 60)

    # Load kickoff times
    print(f"\nLoading kickoff times from {enriched_csv}...")
    kickoff_times = load_kickoff_times(enriched_csv)
    print(f"Loaded {len(kickoff_times)} games with kickoff times")

    if len(kickoff_times) == 0:
        print("ERROR: No games with kickoff times found!")
        return

    # Create client and discover games
    print("\nDiscovering NFL games from Kalshi API...")
    client = KalshiClient()
    games_with_markets = discover_games_with_markets(
        client,
        series_ticker='KXNFLGAME',
        start_date='2025-08-01',
        end_date='2026-02-15'
    )

    print(f"Found {len(games_with_markets)} games with markets")

    # Patch EventInfo objects with kickoff times from CSV
    print("\nPatching game events with kickoff times from schedule...")
    patched = 0
    for event, market in games_with_markets:
        ticker = event.event_ticker
        if ticker in kickoff_times:
            # EventInfo is frozen, so we need to create a new instance
            # But since it's a tuple in the list, we can just modify the object's __dict__
            # Actually, Pydantic frozen models can't be modified. We need to recreate.

            # Workaround: Modify the underlying __dict__ directly (hacky but works)
            object.__setattr__(event, 'strike_date', kickoff_times[ticker])
            patched += 1

    print(f"Patched {patched} games with kickoff times")
    print(f"Games without kickoff times: {len(games_with_markets) - patched}")

    # Filter to only past games (games that have already been played)
    current_ts = int(datetime.now().timestamp())
    print(f"\nCurrent time: {datetime.now().isoformat()}")

    past_games = []
    future_games = 0
    for event, market in games_with_markets:
        if event.strike_date is None:
            continue  # Skip games without kickoff times

        # Only backtest games that have already happened
        # Add buffer time (e.g., 2 hours after kickoff to ensure game completed)
        if event.strike_date + 7200 < current_ts:
            past_games.append((event, market))
        else:
            future_games += 1

    print(f"Found {len(past_games)} past games (already played)")
    print(f"Skipping {future_games} future games (not yet played)")

    # Fetch game data for past games only
    print("\nFetching market data for past games...")
    game_data_list = []
    for event, market in past_games:
        game_data = fetch_game_data(
            client=client,
            event=event,
            market=market,
            pregame_window_sec=900,
            first_half_sec=5400,  # 90 minutes real time for NFL first half
            candle_interval='1m',
            fetch_orderbook=False,
        )

        if game_data:
            game_data_list.append(game_data)

    print(f"Successfully fetched data for {len(game_data_list)} games")

    if len(game_data_list) == 0:
        print("ERROR: No game data available for backtest!")
        return

    # Create backtest config
    config = BacktestConfig(
        kalshi_base='https://api.elections.kalshi.com/trade-api/v2',
        start_date='2025-08-01',
        end_date='2026-02-15',
        pregame_favorite_threshold=0.60,
        trigger_threshold=0.50,
        revert_bands=[0.55, 0.60, 0.65, 0.70],
        per_contract_fee=0.01,
        extra_slippage=0.005,
        mae_stop_prob=None,
        timeout='halftime',
        grace_sec_for_fill=15,
        rate_limit_sleep_ms=200,
    )

    # Run backtest
    print("\nRunning backtest...")
    print("-" * 60)

    entries, summary = run_backtest(
        game_data_list=game_data_list,
        config=config,
    )

    # Save results
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    results_dir = output_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save all output files
    save_summary_markdown(summary, entries, results_dir)
    if len(entries) > 0:
        save_trades_csv(entries, results_dir)
        save_band_metrics_csv(summary, results_dir)
        save_parquet(entries, results_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)
    print(f"Events Analyzed:     {summary.num_events_analyzed}")
    print(f"Events Qualified:    {summary.num_events_qualified}")
    print(f"Trades Executed:     {summary.num_trades_filled}")
    print(f"Total P&L (Net):     ${summary.total_pnl_net_cents / 100:.2f}")
    print(f"Win Rate:            {summary.overall_win_rate * 100:.1f}%")
    print(f"Avg Hold Time:       {summary.avg_hold_time_sec / 60:.1f} min")
    print("=" * 60)

    print(f"\nDetailed results saved to: {results_dir}")


if __name__ == '__main__':
    main()
