"""
Get just a few sample CFB events to understand the format.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

def main():
    client = KalshiClient()

    print('=' * 80)
    print('SAMPLING CFB EVENTS')
    print('=' * 80)
    print()

    # Get events from KXNCAAFGAME series
    print("Fetching events from KXNCAAFGAME...")
    events = client.get_events(series_ticker='KXNCAAFGAME', limit=20)

    print(f"Found {len(events)} events")
    print()

    for i, event in enumerate(events[:10], 1):
        print(f"{i}. Event: {event['event_ticker']}")
        print(f"   Title: {event.get('title', 'N/A')}")
        if event.get('strike_date'):
            from datetime import datetime
            dt = datetime.fromtimestamp(event['strike_date'])
            print(f"   Strike Date: {dt.strftime('%Y-%m-%d %H:%M UTC')}")

        # Get markets for this event
        markets = client.get_markets(event_ticker=event['event_ticker'])
        if markets:
            for market in markets[:2]:  # Show first 2 markets
                print(f"   Market: {market.ticker}")
                print(f"     Title: {market.title}")
                if market.yes_sub_title:
                    print(f"     Yes: {market.yes_sub_title}")
        print()

    print('=' * 80)


if __name__ == '__main__':
    main()
