"""
Merge Kalshi game data with corrected NFL schedule.

This version analyzes BOTH markets per game (home and away).
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.discovery import discover_games_with_markets


def parse_kalshi_ticker(ticker: str) -> tuple[str, str, str] | None:
    """Parse Kalshi event ticker to extract date and teams."""
    nfl_teams = {
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'JAC',
        'KC', 'LV', 'LAC', 'LAR', 'LA', 'MIA', 'MIN', 'NE',
        'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB',
        'TEN', 'WAS'
    }

    # Match pattern: KXNFLGAME-25OCT13BUFATL
    match = re.match(r'KXNFLGAME-(\d{2}[A-Z]{3}\d{2})(.+)', ticker)
    if not match:
        return None

    date_str = match.group(1)  # e.g., "25OCT13"
    teams_str = match.group(2)  # e.g., "BUFATL"

    # Try to find valid team split
    for away_len in range(2, min(5, len(teams_str))):
        away = teams_str[:away_len]
        home = teams_str[away_len:]
        if away.upper() in nfl_teams and home.upper() in nfl_teams:
            return (date_str, away.upper(), home.upper())

    return None


def normalize_team_abbr(abbr: str) -> str:
    """Normalize team abbreviations."""
    mapping = {
        'JAC': 'JAX',
        'JAX': 'JAX',
        'LA': 'LAR',
        'LAR': 'LAR',
    }
    return mapping.get(abbr.upper(), abbr.upper())


def main():
    print("=" * 70)
    print("MERGING KALSHI DATA WITH CORRECTED NFL SCHEDULE")
    print("=" * 70)
    print()

    # Load corrected schedule
    schedule_path = 'artifacts/nfl_2025_schedule_corrected.csv'
    print(f"Loading schedule from: {schedule_path}")

    schedule_games = {}
    with open(schedule_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            away = normalize_team_abbr(row['away_abbr'])
            home = normalize_team_abbr(row['home_abbr'])

            # Create bidirectional keys (both away@home and home@away)
            key1 = f"{away}@{home}"
            key2 = f"{home}@{away}"

            if row['kickoff_utc']:
                kickoff_dt = datetime.fromisoformat(row['kickoff_utc'])
                kickoff_ts = int(kickoff_dt.timestamp())

                schedule_games[key1] = {
                    'kickoff_ts': kickoff_ts,
                    'week': row['week'],
                    'away': away,
                    'home': home,
                }
                schedule_games[key2] = schedule_games[key1]  # Same data

    print(f"Loaded {len(set(tuple(v.items()) for v in schedule_games.values()))} unique games")
    print()

    # Discover Kalshi markets
    print("Discovering Kalshi markets...")
    client = KalshiClient()
    games_with_markets = discover_games_with_markets(
        client,
        series_ticker='KXNFLGAME',
        start_date='2025-08-01',
        end_date='2026-02-15'
    )

    print(f"Found {len(games_with_markets)} Kalshi markets")
    print()

    # Match and enrich
    print("Matching Kalshi markets with schedule...")
    matched_markets = []
    unmatched_markets = []

    for event, market in games_with_markets:
        parsed = parse_kalshi_ticker(event.event_ticker)

        if not parsed:
            unmatched_markets.append((event, market, "Could not parse ticker"))
            continue

        date_str, away, home = parsed
        away_norm = normalize_team_abbr(away)
        home_norm = normalize_team_abbr(home)

        # Try to match
        key = f"{away_norm}@{home_norm}"
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
                'week': game_info['week'],
                'strike_date': game_info['kickoff_ts'],
            })
        else:
            unmatched_markets.append((event, market, f"No schedule match for {key}"))

    print(f"Matched: {len(matched_markets)} markets")
    print(f"Unmatched: {len(unmatched_markets)} markets")
    print()

    # Save enriched data
    output_path = 'artifacts/nfl_markets_2025_enriched.csv'
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'event_ticker', 'market_ticker', 'market_title', 'yes_subtitle',
            'series_ticker', 'away_team', 'home_team', 'week', 'strike_date'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_markets)

    print(f"Saved {len(matched_markets)} enriched markets to: {output_path}")

    # Show sample
    print()
    print("Sample matched markets:")
    for i, market in enumerate(matched_markets[:5], 1):
        kickoff_dt = datetime.fromtimestamp(market['strike_date']).strftime('%Y-%m-%d %H:%M UTC')
        print(f"{i}. {market['event_ticker']}")
        print(f"   Market: {market['market_ticker']} ({market['yes_subtitle']})")
        print(f"   {market['away_team']} @ {market['home_team']}")
        print(f"   Week {market['week']}: {kickoff_dt}")
        print()

    # Show unmatched
    if unmatched_markets:
        print("Sample unmatched markets:")
        for i, (event, market, reason) in enumerate(unmatched_markets[:5], 1):
            print(f"{i}. {event.event_ticker}: {reason}")
        print()

    print("=" * 70)
    print(f"✅ DONE! Now you have BOTH markets per game with correct kickoff times.")
    print("=" * 70)


if __name__ == '__main__':
    main()
