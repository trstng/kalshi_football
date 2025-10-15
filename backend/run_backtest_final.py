"""
Run backtest using corrected schedule with BOTH markets per game.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.backtest import run_backtest
from kalshi_nfl_research.data_models import BacktestConfig, EventInfo, MarketInfo
from kalshi_nfl_research.fetch import fetch_game_data
from kalshi_nfl_research.io_utils import (
    save_summary_markdown,
    save_trades_csv,
    save_band_metrics_csv,
    save_parquet,
)


def load_enriched_markets(csv_path: str) -> list[tuple[EventInfo, MarketInfo]]:
    """
    Load enriched markets from CSV.

    Returns:
        List of (EventInfo, MarketInfo) tuples
    """
    markets = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create EventInfo
            event = EventInfo(
                event_ticker=row['event_ticker'],
                series_ticker=row['series_ticker'],
                title=f"{row['away_team']} @ {row['home_team']}",
                strike_date=int(row['strike_date']) if row['strike_date'] else None,
            )

            # Create MarketInfo
            market = MarketInfo(
                ticker=row['market_ticker'],
                event_ticker=row['event_ticker'],
                market_type='binary',
                title=row['market_title'],
                yes_sub_title=row.get('yes_subtitle', ''),
            )

            markets.append((event, market))

    return markets


def main():
    enriched_csv = 'artifacts/nfl_markets_2025_enriched.csv'
    output_dir = Path('artifacts')

    print("=" * 60)
    print("RUNNING BACKTEST WITH CORRECTED SCHEDULE (BOTH MARKETS)")
    print("=" * 60)
    print()

    # Load enriched markets
    print(f"Loading enriched markets from {enriched_csv}...")
    games_with_markets = load_enriched_markets(enriched_csv)
    print(f"Loaded {len(games_with_markets)} markets")
    print()

    # Filter to past games (already happened)
    current_ts = int(datetime.now().timestamp())
    print(f"Current time: {datetime.now().isoformat()}")

    past_markets = []
    future_markets = 0

    for event, market in games_with_markets:
        if event.strike_date is None:
            continue

        # Only backtest games that finished >2 hours ago
        if event.strike_date + 7200 < current_ts:
            past_markets.append((event, market))
        else:
            future_markets += 1

    print(f"Found {len(past_markets)} past markets (games already played)")
    print(f"Skipping {future_markets} future markets")
    print()

    # Fetch game data
    print("Fetching market data...")
    client = KalshiClient()
    game_data_list = []

    for event, market in past_markets:
        game_data = fetch_game_data(
            client=client,
            event=event,
            market=market,
            pregame_window_sec=900,
            first_half_sec=5400,  # 90 minutes real time
            candle_interval='1m',
            fetch_orderbook=False,
        )

        if game_data:
            game_data_list.append(game_data)

    print(f"Successfully fetched data for {len(game_data_list)} markets")
    print()

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
    print("Running backtest...")
    print("-" * 60)

    entries, summary = run_backtest(
        game_data_list=game_data_list,
        config=config,
    )

    # Save results
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    results_dir = output_dir / f"backtest_{timestamp}"
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
    print(f"Markets Analyzed:    {summary.num_events_analyzed}")
    print(f"Markets Qualified:   {summary.num_events_qualified}")
    print(f"Trades Executed:     {summary.num_trades_filled}")
    print(f"Total P&L (Net):     ${summary.total_pnl_net_cents / 100:.2f}")
    print(f"Win Rate:            {summary.overall_win_rate * 100:.1f}%")
    print(f"Avg Hold Time:       {summary.avg_hold_time_sec / 60:.1f} min")
    print("=" * 60)

    print(f"\nDetailed results saved to: {results_dir}")


if __name__ == '__main__':
    main()
