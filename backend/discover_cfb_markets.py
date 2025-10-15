"""
Discover what CFB series/markets Kalshi has available.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

def main():
    client = KalshiClient()

    print('=' * 80)
    print('DISCOVERING CFB MARKETS ON KALSHI')
    print('=' * 80)
    print()

    # Try different possible series names
    potential_series = [
        'KXCFB',
        'KXCFBGAME',
        'KXCOLLEGE',
        'KXNCAA',
        'KXNCAAFB',
        'KXFBS',
        'CFB',
        'COLLEGE',
    ]

    for series_name in potential_series:
        print(f"Trying series: {series_name}...")
        try:
            series_list = client.list_series(series_ticker=series_name, limit=5)
            if series_list:
                print(f"  ✓ Found {len(series_list)} series matching '{series_name}'")
                for s in series_list:
                    print(f"    - {s.series_ticker}")
            else:
                print(f"  ✗ No series found for '{series_name}'")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print()
    print('=' * 80)
    print('SEARCHING ALL ACTIVE SERIES')
    print('=' * 80)
    print()

    # Get all series and filter for CFB/college/football related
    try:
        print("Fetching all active series...")
        all_series = client.list_series(limit=500)
        print(f"Found {len(all_series)} total series")
        print()

        # Filter for CFB/college/football keywords
        cfb_keywords = ['cfb', 'college', 'ncaa', 'football', 'fb', 'fbs']

        cfb_series = [
            s for s in all_series
            if any(keyword in s.series_ticker.lower() for keyword in cfb_keywords)
        ]

        if cfb_series:
            print(f"Found {len(cfb_series)} potential CFB series:")
            for s in cfb_series:
                print(f"  - {s.series_ticker}")
        else:
            print("No CFB-related series found")

    except Exception as e:
        print(f"Error fetching all series: {e}")

    print()
    print('=' * 80)


if __name__ == '__main__':
    main()
