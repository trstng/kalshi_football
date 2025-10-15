"""
List all series on Kalshi to find CFB markets.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

def main():
    client = KalshiClient()

    print('=' * 80)
    print('LISTING ALL KALSHI SERIES')
    print('=' * 80)
    print()

    try:
        print("Fetching all series...")
        all_series = client.get_series(limit=1000)
        print(f"Total series found: {len(all_series)}")
        print()

        # Look for football, college, CFB, NCAA keywords
        keywords = ['football', 'cfb', 'college', 'ncaa', 'fb', 'fbs', 'fcs']

        print("Series containing football/college keywords:")
        print("-" * 80)

        found_any = False
        for s in all_series:
            ticker_lower = s.series_ticker.lower()
            title_lower = s.title.lower() if hasattr(s, 'title') and s.title else ""

            if any(kw in ticker_lower or kw in title_lower for kw in keywords):
                found_any = True
                print(f"  {s.series_ticker}")
                if hasattr(s, 'title') and s.title:
                    print(f"    Title: {s.title}")

        if not found_any:
            print("  (No football/college-related series found)")

        print()
        print("-" * 80)
        print()
        print("All series tickers (first 50):")
        for i, s in enumerate(all_series[:50], 1):
            print(f"  {i}. {s.series_ticker}")

        if len(all_series) > 50:
            print(f"  ... and {len(all_series) - 50} more")

    except Exception as e:
        print(f"Error: {e}")

    print()
    print('=' * 80)


if __name__ == '__main__':
    main()
