"""
Merge Kalshi games with external schedule to populate kickoff times.
"""
import csv
import re
from datetime import datetime
from pathlib import Path

def parse_kalshi_ticker(ticker: str) -> tuple[str, str, str] | None:
    """
    Parse Kalshi event ticker to extract date and teams.

    Format: KXNFLGAME-25SEP08CLEBAL
    Returns: (date_str, away_abbr, home_abbr) or None

    Examples:
    - KXNFLGAME-25SEP08CLEBAL -> ('25SEP08', 'CLE', 'BAL')
    - KXNFLGAME-25OCT20HOUSEA -> ('25OCT20', 'HOU', 'SEA')
    """
    # All NFL team abbreviations (2-3 chars)
    nfl_teams = {
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'JAC',
        'KC', 'LV', 'LAC', 'LAR', 'LA', 'MIA', 'MIN', 'NE',
        'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB',
        'TEN', 'WAS'
    }

    match = re.match(r'KXNFLGAME-(\d{2}[A-Z]{3}\d{2})(.+)', ticker)
    if not match:
        return None

    date_str = match.group(1)
    teams_str = match.group(2)

    # Try to find valid team split by checking against known teams
    # Try away team from left (2-4 chars), home team is the rest
    for away_len in range(2, min(5, len(teams_str))):
        away = teams_str[:away_len]
        home = teams_str[away_len:]

        if away.upper() in nfl_teams and home.upper() in nfl_teams:
            return (date_str, away.upper(), home.upper())

    # If no match found, return None
    return None


def normalize_team_abbr(abbr: str) -> str:
    """
    Normalize team abbreviations to handle variations.

    Kalshi uses: JAC, LA (Rams)
    Standard uses: JAX, LAR
    """
    mapping = {
        'JAC': 'JAX',
        'JAX': 'JAX',  # Ensure consistency
        'LA': 'LAR',   # Rams
        'LAR': 'LAR',
    }
    return mapping.get(abbr.upper(), abbr.upper())


def main():
    # Load Kalshi games
    kalshi_file = Path('artifacts/nfl_games_2025.csv')
    schedule_file = Path('artifacts/nfl_2025_schedule.csv')
    output_file = Path('artifacts/nfl_games_2025_with_kickoffs.csv')

    print(f"Loading Kalshi games from {kalshi_file}")
    kalshi_games = {}
    with open(kalshi_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row['event_ticker']
            kalshi_games[ticker] = row

    print(f"Found {len(kalshi_games)} Kalshi games")

    # Load schedule
    print(f"\nLoading schedule from {schedule_file}")
    schedule = []
    with open(schedule_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['kickoff_utc']:  # Skip games without kickoff times
                schedule.append(row)

    print(f"Found {len(schedule)} scheduled games with kickoff times")

    # Create lookup: (away, home) -> kickoff_utc
    schedule_lookup = {}
    for game in schedule:
        away = normalize_team_abbr(game['away_abbr'])
        home = normalize_team_abbr(game['home_abbr'])
        key = (away, home)
        kickoff_utc = game['kickoff_utc']

        # Convert ISO 8601 to Unix timestamp
        dt = datetime.fromisoformat(kickoff_utc.replace('+00:00', ''))
        timestamp = int(dt.timestamp())

        schedule_lookup[key] = {
            'kickoff_utc': kickoff_utc,
            'timestamp': timestamp,
            'game_date': game['game_date'],
        }

    print(f"\nMatching Kalshi games with schedule...")
    matched = 0
    unmatched = []

    for ticker, game in kalshi_games.items():
        parsed = parse_kalshi_ticker(ticker)
        if not parsed:
            unmatched.append((ticker, "Could not parse ticker"))
            continue

        date_str, away, home = parsed
        away = normalize_team_abbr(away)
        home = normalize_team_abbr(home)

        key = (away, home)
        if key in schedule_lookup:
            schedule_info = schedule_lookup[key]
            game['strike_date'] = schedule_info['timestamp']
            game['kickoff_utc'] = schedule_info['kickoff_utc']
            matched += 1
        else:
            unmatched.append((ticker, f"No match for {away}@{home}"))

    print(f"\nMatched: {matched} games")
    print(f"Unmatched: {len(unmatched)} games")

    if unmatched:
        print("\nUnmatched games (first 10):")
        for ticker, reason in unmatched[:10]:
            print(f"  {ticker}: {reason}")

    # Write enriched dataset
    print(f"\nWriting enriched dataset to {output_file}")
    with open(output_file, 'w', newline='') as f:
        fieldnames = list(kalshi_games[next(iter(kalshi_games))].keys())
        if 'kickoff_utc' not in fieldnames:
            fieldnames.append('kickoff_utc')

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kalshi_games.values())

    print(f"\nDone! Enriched dataset saved with {matched} games having kickoff times")
    print(f"Output: {output_file}")


if __name__ == '__main__':
    main()
