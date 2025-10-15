"""
Prepare CFB data for backtest using Kalshi's own strike_date (kickoff times).
No need to match with external schedule - Kalshi has everything we need!
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient


def main():
    print("=" * 80)
    print("PREPARING CFB DATA FOR BACKTEST")
    print("=" * 80)
    print()

    client = KalshiClient()

    # Get CFB events with strike dates
    print("Fetching CFB events from Kalshi...")
    # Use default limit (API handles pagination internally)
    events = client.get_events(
        series_ticker='KXNCAAFGAME'
    )

    print(f"Found {len(events)} CFB events")
    print()

    # Filter for games that already happened (strike_date in the past)
    now = int(datetime.utcnow().timestamp())
    past_events = [e for e in events if e.get('strike_date') and e['strike_date'] < now]

    print(f"Events that already occurred: {len(past_events)}")
    print()

    # Get markets for each past event
    print("Fetching markets for past events...")
    enriched_markets = []

    for i, event in enumerate(past_events, 1):
        if i % 20 == 0:
            print(f"  Processing event {i}/{len(past_events)}...")

        event_ticker = event['event_ticker']
        strike_date = event['strike_date']

        try:
            markets = client.get_markets(event_ticker=event_ticker)

            for market in markets:
                enriched_markets.append({
                    'event_ticker': event_ticker,
                    'series_ticker': event.get('series_ticker', 'KXNCAAFGAME'),
                    'event_title': event.get('title', ''),
                    'strike_date': strike_date,  # This is the kickoff time!
                    'market_ticker': market.ticker,
                    'market_title': market.title,
                    'yes_subtitle': market.yes_sub_title or '',
                })

        except Exception as e:
            print(f"  Error fetching markets for {event_ticker}: {e}")

    print(f"Total markets collected: {len(enriched_markets)}")
    print()

    # Save enriched data
    output_path = 'artifacts/cfb_markets_past_enriched.csv'
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'event_ticker', 'series_ticker', 'event_title', 'strike_date',
            'market_ticker', 'market_title', 'yes_subtitle'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_markets)

    print(f"Saved {len(enriched_markets)} markets to: {output_path}")
    print()

    # Show sample
    print("Sample past CFB games:")
    for i, m in enumerate(enriched_markets[:5], 1):
        kickoff_dt = datetime.fromtimestamp(m['strike_date']).strftime('%Y-%m-%d %H:%M UTC')
        print(f"{i}. {m['event_ticker']}")
        print(f"   {m['event_title']}")
        print(f"   Market: {m['market_ticker']} ({m['yes_subtitle']})")
        print(f"   Kickoff: {kickoff_dt}")
        print()

    print("=" * 80)
    print(f"✅ DONE! Ready to backtest {len(past_events)} past CFB games")
    print("=" * 80)


if __name__ == '__main__':
    main()
