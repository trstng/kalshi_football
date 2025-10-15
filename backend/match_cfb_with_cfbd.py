"""
Match unmatched Kalshi CFB markets with CFBD API data.

Uses fuzzy team name matching to handle abbreviations like "St." vs "State".
"""
import re
import csv
import requests
from datetime import datetime
from difflib import SequenceMatcher


def normalize_team_name(name: str) -> str:
    """Normalize team name for matching."""
    # Common normalizations
    name = name.strip()

    # Expand common abbreviations
    expansions = {
        r'\bSt\.\b': 'State',
        r'\bFt\.\b': 'Fort',
        r'\bN\.C\.\b': 'North Carolina',
        r'\bS\.C\.\b': 'South Carolina',
        r'\bU\.S\.C\.\b': 'Southern California',
        r'\bU\.C\.F\.\b': 'UCF',
        r'\bS\.M\.U\.\b': 'SMU',
        r'\bT\.C\.U\.\b': 'TCU',
        r'\bB\.Y\.U\.\b': 'BYU',
        r'\bL\.S\.U\.\b': 'LSU',
    }

    for pattern, replacement in expansions.items():
        name = re.sub(pattern, replacement, name)

    # Remove parentheticals
    name = re.sub(r'\s*\([^)]*\)', '', name)

    return name.strip()


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings (0-1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_best_match(away: str, home: str, cfbd_games: list) -> dict | None:
    """
    Find best matching CFBD game for given team pair.

    Returns game dict with kickoff_ts, or None if no good match.
    """
    away_norm = normalize_team_name(away)
    home_norm = normalize_team_name(home)

    best_match = None
    best_score = 0

    for game in cfbd_games:
        cfbd_away = game.get('awayTeam', '') or ''
        cfbd_home = game.get('homeTeam', '') or ''

        # Calculate similarity scores
        away_score = similarity(away_norm, cfbd_away)
        home_score = similarity(home_norm, cfbd_home)

        # Average score (both must match reasonably well)
        avg_score = (away_score + home_score) / 2

        # Require high confidence (>0.85 average, both >0.7)
        if avg_score > best_score and avg_score > 0.85 and away_score > 0.7 and home_score > 0.7:
            best_score = avg_score
            best_match = game

    return best_match


def main():
    print("=" * 80)
    print("MATCHING UNMATCHED KALSHI MARKETS WITH CFBD DATA")
    print("=" * 80)
    print()

    # Load unmatched Kalshi markets
    print("Loading unmatched Kalshi markets...")
    with open('artifacts/cfb_unmatched_kalshi_markets.csv', 'r') as f:
        reader = csv.DictReader(f)
        unmatched = list(reader)

    print(f"Loaded {len(unmatched)} unmatched markets")
    print()

    # Fetch CFBD 2025 games
    print("Fetching 2025 CFB schedule from CFBD API...")
    url = "https://api.collegefootballdata.com/games"
    headers = {'Authorization': 'Bearer A5FKBQiqljX2u82pX1qUlc7EL1ZDK49QPqeapqeS9uHo5ewsIli7sGtVbrn2wCr8'}
    params = {'year': 2025, 'seasonType': 'regular'}

    response = requests.get(url, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    cfbd_games = response.json()

    print(f"Fetched {len(cfbd_games)} CFBD games")
    print()

    # Match each unmatched market
    print("Matching...")
    newly_matched = []
    still_unmatched = []

    for market in unmatched:
        # Parse title: "Team A at Team B Winner?"
        match = re.match(r'^(.+?)\s+at\s+(.+?)\s+Winner\?$', market['market_title'])
        if not match:
            still_unmatched.append(market)
            continue

        away = match.group(1).strip()
        home = match.group(2).strip()

        # Find best CFBD match
        cfbd_match = find_best_match(away, home, cfbd_games)

        if cfbd_match and cfbd_match.get('startDate'):
            # Parse kickoff time
            start_date = cfbd_match['startDate']
            if start_date.endswith('Z'):
                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(start_date)
            kickoff_ts = int(dt.timestamp())

            newly_matched.append({
                'event_ticker': market['event_ticker'],
                'market_ticker': market['market_ticker'],
                'market_title': market['market_title'],
                'yes_subtitle': market['yes_subtitle'],
                'series_ticker': 'KXNCAAFGAME',
                'away_team': cfbd_match['awayTeam'],
                'home_team': cfbd_match['homeTeam'],
                'kickoff_ts': kickoff_ts,
                'matched_via': 'CFBD_API',
            })
        else:
            still_unmatched.append(market)

    print(f"✓ Newly matched: {len(newly_matched)} markets")
    print(f"✗ Still unmatched: {len(still_unmatched)} markets")
    print()

    # Save newly matched
    if newly_matched:
        output_path = 'artifacts/cfb_markets_2025_cfbd_matched.csv'
        with open(output_path, 'w', newline='') as f:
            fieldnames = [
                'event_ticker', 'market_ticker', 'market_title', 'yes_subtitle',
                'series_ticker', 'away_team', 'home_team', 'kickoff_ts', 'matched_via'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(newly_matched)

        print(f"✓ Saved {len(newly_matched)} newly matched markets to: {output_path}")
        print()

        # Show samples
        print("Sample newly matched:")
        for i, m in enumerate(newly_matched[:5], 1):
            kickoff_dt = datetime.fromtimestamp(m['kickoff_ts']).strftime('%Y-%m-%d %H:%M UTC')
            print(f"{i}. {m['away_team']} @ {m['home_team']}")
            print(f"   {m['market_title']}")
            print(f"   Kickoff: {kickoff_dt}")
            print()

    # Save still unmatched
    if still_unmatched:
        with open('artifacts/cfb_still_unmatched.csv', 'w', newline='') as f:
            fieldnames = ['event_ticker', 'market_ticker', 'market_title', 'yes_subtitle']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(still_unmatched)

        print(f"Saved {len(still_unmatched)} still unmatched to: artifacts/cfb_still_unmatched.csv")
        print()
        print("Sample still unmatched:")
        for i, m in enumerate(still_unmatched[:10], 1):
            print(f"{i}. {m['market_title']}")

    print()
    print("=" * 80)
    print(f"SUMMARY: {len(newly_matched)} new matches via CFBD, {len(still_unmatched)} remaining")
    print("=" * 80)


if __name__ == '__main__':
    main()
