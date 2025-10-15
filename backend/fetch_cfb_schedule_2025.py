"""
Fetch 2025 CFB schedule from CollegeFootballData.com API.

This fetches all 2025 regular season CFB games with kickoff times
directly from the CFBD REST API (no Python package needed).
"""
import os
import requests
import csv
from datetime import datetime
from typing import Optional

# CFBD API configuration
CFBD_BASE_URL = "https://api.collegefootballdata.com"
API_KEY = os.getenv("CFBD_API_KEY")  # Set this environment variable if you have a key

def fetch_cfb_games(year: int, season_type: str = "regular") -> list[dict]:
    """
    Fetch CFB games from the CFBD API.

    Args:
        year: Season year (e.g., 2025)
        season_type: "regular", "postseason", or "both"

    Returns:
        List of game dictionaries with fields:
        - id, season, week, season_type
        - start_date (ISO string)
        - home_team, away_team
        - home_points, away_points (null for future games)
        - completed (bool)
    """
    url = f"{CFBD_BASE_URL}/games"
    headers = {}

    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    params = {
        "year": year,
        "seasonType": season_type,
    }

    print(f"Fetching CFB games for {year} {season_type} season...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    games = response.json()
    print(f"✓ Fetched {len(games)} games")

    # Debug: show sample raw response
    if games:
        print("\nSample raw game data (first game):")
        import json
        print(json.dumps(games[0], indent=2))
        print()

    return games


def parse_iso_to_timestamp(iso_string: str) -> int:
    """Convert ISO 8601 date string to Unix timestamp."""
    # Handle both with and without timezone
    if iso_string.endswith('Z'):
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    else:
        dt = datetime.fromisoformat(iso_string)
    return int(dt.timestamp())


def main():
    print("=" * 80)
    print("FETCHING 2025 CFB SCHEDULE FROM CFBD API")
    print("=" * 80)
    print()

    # Fetch 2025 regular season games
    games = fetch_cfb_games(year=2025, season_type="regular")

    # Convert to CSV format
    output_path = "artifacts/cfb_2025_schedule_cfbd.csv"

    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'id', 'season', 'week', 'season_type',
            'start_date', 'kickoff_ts',
            'away_team', 'home_team',
            'away_points', 'home_points',
            'completed', 'neutral_site'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for game in games:
            # Parse timestamp
            kickoff_ts = None
            if game.get('start_date'):
                try:
                    kickoff_ts = parse_iso_to_timestamp(game['start_date'])
                except Exception as e:
                    print(f"Warning: Could not parse date {game.get('start_date')}: {e}")

            writer.writerow({
                'id': game.get('id'),
                'season': game.get('season'),
                'week': game.get('week'),
                'season_type': game.get('season_type'),
                'start_date': game.get('start_date'),
                'kickoff_ts': kickoff_ts,
                'away_team': game.get('away_team'),
                'home_team': game.get('home_team'),
                'away_points': game.get('away_points'),
                'home_points': game.get('home_points'),
                'completed': game.get('completed'),
                'neutral_site': game.get('neutral_site'),
            })

    print()
    print(f"✓ Saved {len(games)} games to {output_path}")
    print()

    # Show sample
    print("Sample games:")
    for i, game in enumerate(games[:5], 1):
        kickoff_str = game.get('start_date', 'Unknown')
        print(f"{i}. Week {game.get('week')}: {game.get('away_team')} @ {game.get('home_team')}")
        print(f"   Kickoff: {kickoff_str}")
        print()

    # Show team name samples for mapping
    unique_teams = set()
    for game in games:
        if game.get('home_team'):
            unique_teams.add(game['home_team'])
        if game.get('away_team'):
            unique_teams.add(game['away_team'])

    print(f"Found {len(unique_teams)} unique teams")
    print("Sample team names (first 10):")
    for team in sorted(unique_teams)[:10]:
        print(f"  - {team}")
    print()

    print("=" * 80)
    print(f"✓ SUCCESS! Now we have {len(games)} CFB games with kickoff times")
    print("=" * 80)


if __name__ == '__main__':
    main()
