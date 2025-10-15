"""
Merge Kalshi CFB game data with master schedule.
Similar to merge_schedule_v2.py but for CFB.
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.discovery import discover_games_with_markets


# Common CFB team name mappings
CFB_TEAM_MAPPINGS = {
    # Common abbreviations
    'Miami (FL)': 'Miami',
    'Miami (Ohio)': 'Miami OH',
    'USC': 'Southern California',
    'TCU': 'TCU',
    'UCF': 'UCF',
    'BYU': 'BYU',
    'SMU': 'SMU',
    'LSU': 'LSU',
    # Add more as needed
}


def normalize_cfb_team(team: str) -> str:
    """Normalize CFB team name for matching."""
    # Apply mappings
    if team in CFB_TEAM_MAPPINGS:
        return CFB_TEAM_MAPPINGS[team]

    # Basic normalization
    return team.strip()


def main():
    print("=" * 80)
    print("MERGING KALSHI CFB DATA WITH MASTER SCHEDULE")
    print("=" * 80)
    print()

    # Load master CFB schedule
    schedule_path = 'artifacts/cfb_2025_schedule_master.csv'
    print(f"Loading schedule from: {schedule_path}")

    schedule_games = {}
    with open(schedule_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            away = normalize_cfb_team(row['away_team'])
            home = normalize_cfb_team(row['home_team'])

            # Create keys for matching (both directions)
            key1 = f"{away}@{home}"
            key2 = f"{home}@{away}"

            kickoff_ts = int(row['kickoff_ts'])

            game_info = {
                'kickoff_ts': kickoff_ts,
                'away': away,
                'home': home,
                'kickoff_utc': row['kickoff_utc'],
            }

            schedule_games[key1] = game_info
            schedule_games[key2] = game_info  # Bidirectional

    print(f"Loaded {len(set(tuple(v.items()) for v in schedule_games.values()))} unique games")
    print()

    # Discover Kalshi CFB markets
    print("Discovering Kalshi CFB markets (KXNCAAFGAME)...")
    print("(This may take a while...)")
    print()

    client = KalshiClient()

    try:
        games_with_markets = discover_games_with_markets(
            client,
            series_ticker='KXNCAAFGAME',
            start_date='2025-08-01',
            end_date='2025-11-30'
        )

        print(f"Found {len(games_with_markets)} Kalshi CFB markets")
        print()

        # Save all discovered markets to a file
        print("Saving all discovered CFB markets...")
        with open('artifacts/cfb_kalshi_markets_raw.csv', 'w', newline='') as f:
            fieldnames = ['event_ticker', 'market_ticker', 'market_title', 'yes_subtitle']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for event, market in games_with_markets:
                writer.writerow({
                    'event_ticker': event.event_ticker,
                    'market_ticker': market.ticker,
                    'market_title': market.title,
                    'yes_subtitle': market.yes_sub_title,
                })

        print(f"Saved raw markets to artifacts/cfb_kalshi_markets_raw.csv")
        print()

        # Now try to match with schedule
        print("Matching Kalshi markets with schedule...")
        matched_markets = []
        unmatched_markets = []

        for event, market in games_with_markets:
            # Parse title: "Team A at Team B Winner?"
            match = re.match(r'^(.+?)\s+at\s+(.+?)\s+Winner\?$', market.title, re.IGNORECASE)

            if not match:
                unmatched_markets.append((event, market, f"Could not parse title: {market.title}"))
                continue

            away_raw = match.group(1).strip()
            home_raw = match.group(2).strip()

            # Normalize names
            away = normalize_cfb_team(away_raw)
            home = normalize_cfb_team(home_raw)

            # Try to match with schedule
            key = f"{away}@{home}"
            if key in schedule_games:
                game_info = schedule_games[key]
                matched_markets.append({
                    'event_ticker': event.event_ticker,
                    'market_ticker': market.ticker,
                    'market_title': market.title,
                    'yes_subtitle': market.yes_sub_title,
                    'series_ticker': event.series_ticker,
                    'away_team': game_info['away'],
                    'home_team': game_info['home'],
                    'kickoff_ts': game_info['kickoff_ts'],
                })
            else:
                unmatched_markets.append((event, market, f"No schedule match for {away} @ {home}"))

        print(f"Matched: {len(matched_markets)} markets")
        print(f"Unmatched: {len(unmatched_markets)} markets")
        print()

        # Save enriched data
        output_path = 'artifacts/cfb_markets_2025_enriched.csv'
        with open(output_path, 'w', newline='') as f:
            fieldnames = [
                'event_ticker', 'market_ticker', 'market_title', 'yes_subtitle',
                'series_ticker', 'away_team', 'home_team', 'kickoff_ts'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched_markets)

        print(f"✓ Saved {len(matched_markets)} enriched markets to: {output_path}")
        print()

        # Show samples
        if matched_markets:
            print("Sample matched markets:")
            for i, m in enumerate(matched_markets[:5], 1):
                kickoff_dt = datetime.fromtimestamp(m['kickoff_ts']).strftime('%Y-%m-%d %H:%M UTC')
                print(f"{i}. {m['away_team']} @ {m['home_team']}")
                print(f"   {m['market_ticker']} ({m['yes_subtitle']})")
                print(f"   Kickoff: {kickoff_dt}")
                print()

        # Show sample unmatched to understand format
        if unmatched_markets:
            print("Sample unmatched markets:")
            for i, (event, market, reason) in enumerate(unmatched_markets[:10], 1):
                print(f"{i}. {market.title}")
                print(f"   Reason: {reason}")
                print()

    except Exception as e:
        print(f"Error discovering markets: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80)


if __name__ == '__main__':
    main()
