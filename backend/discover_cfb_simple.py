"""
Simple CFB market discovery using the same approach as NFL.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.discovery import discover_games_with_markets

def main():
    client = KalshiClient()

    print('=' * 80)
    print('DISCOVERING CFB MARKETS ON KALSHI')
    print('=' * 80)
    print()

    # Try the most likely CFB series names
    potential_series = [
        'KXCFBGAME',
        'KXCFB',
        'KXNCAAFB',
        'KXCOLLEGE',
    ]

    for series_ticker in potential_series:
        print(f"Trying series: {series_ticker}...")
        try:
            games_with_markets = discover_games_with_markets(
                client,
                series_ticker=series_ticker,
                start_date='2025-08-01',
                end_date='2025-11-30'
            )

            if games_with_markets:
                print(f"  ✓ Found {len(games_with_markets)} games with markets!")
                print()
                print("Sample games:")
                for event, market in games_with_markets[:5]:
                    print(f"  - {event.event_ticker}: {market.ticker}")
                    print(f"    {market.title}")
                print()
                print(f"... and {len(games_with_markets) - 5} more")
                print()

                # Save the series ticker that worked
                with open('artifacts/cfb_series_ticker.txt', 'w') as f:
                    f.write(series_ticker)

                print(f"✓ SUCCESS! Series '{series_ticker}' has CFB games")
                print(f"  Saved to artifacts/cfb_series_ticker.txt")
                break
            else:
                print(f"  ✗ No games found for '{series_ticker}'")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        print()

    print('=' * 80)


if __name__ == '__main__':
    main()
