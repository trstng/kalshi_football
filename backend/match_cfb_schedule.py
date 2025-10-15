"""
Match CFB Kalshi markets with schedule using market titles.
"""
import csv
from datetime import datetime, timedelta
from difflib import SequenceMatcher

def normalize_team_name(name: str) -> str:
    """Normalize team name for fuzzy matching."""
    # Common abbreviations and normalizations
    replacements = {
        'St.': 'State',
        'Univ.': 'University',
        'U.': 'University',
        '(FL)': '',
        '(OH)': '',
        'Miami (Ohio)': 'Miami OH',
        'Southern Cal': 'USC',
        'Southern California': 'USC',
    }

    result = name.strip()
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result.lower().strip()


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize_team_name(a), normalize_team_name(b)).ratio()


def parse_market_title(title: str) -> tuple[str, str] | None:
    """Parse 'Team A at Team B Winner?' to extract teams."""
    if ' at ' in title:
        parts = title.split(' at ')
        if len(parts) == 2:
            away = parts[0].strip()
            home = parts[1].replace(' Winner?', '').strip()
            return (away, home)
    return None


def main():
    print("=" * 80)
    print("MATCHING CFB SCHEDULE WITH KALSHI MARKETS")
    print("=" * 80)
    print()

    # Load schedule
    print("Loading master CFB schedule...")
    schedule_games = []
    with open('artifacts/cfb_2025_schedule_master.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            schedule_games.append(row)

    print(f"Loaded {len(schedule_games)} scheduled games")
    print()

    # Load Kalshi markets
    print("Loading Kalshi CFB markets...")
    kalshi_markets = []
    with open('artifacts/cfb_kalshi_markets_raw.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kalshi_markets.append(row)

    print(f"Loaded {len(kalshi_markets)} Kalshi markets")
    print()

    # Match markets with schedule
    print("Matching markets with schedule...")
    matched = []
    unmatched_kalshi = []
    unmatched_schedule = set(range(len(schedule_games)))

    for market in kalshi_markets:
        title = market['market_title']
        teams = parse_market_title(title)

        if not teams:
            unmatched_kalshi.append((market, "Could not parse title"))
            continue

        away_kalshi, home_kalshi = teams

        # Try to find matching scheduled game
        best_match = None
        best_score = 0.0
        best_idx = None

        for idx, game in enumerate(schedule_games):
            away_sched = game['away_team']
            home_sched = game['home_team']

            # Calculate similarity scores
            away_sim = similarity(away_kalshi, away_sched)
            home_sim = similarity(home_kalshi, home_sched)

            # Average similarity (both teams must match reasonably well)
            avg_sim = (away_sim + home_sim) / 2.0

            if avg_sim > best_score:
                best_score = avg_sim
                best_match = game
                best_idx = idx

        # Require at least 70% similarity to match
        if best_score >= 0.70:
            matched.append({
                'event_ticker': market['event_ticker'],
                'market_ticker': market['market_ticker'],
                'market_title': title,
                'yes_subtitle': market['yes_subtitle'],
                'away_team_kalshi': away_kalshi,
                'home_team_kalshi': home_kalshi,
                'away_team_sched': best_match['away_team'],
                'home_team_sched': best_match['home_team'],
                'kickoff_ts': best_match['kickoff_ts'],
                'kickoff_utc': best_match['kickoff_utc'],
                'similarity': best_score,
            })
            unmatched_schedule.discard(best_idx)
        else:
            unmatched_kalshi.append((market, f"Best match only {best_score:.2f}"))

    print(f"✓ Matched: {len(matched)} markets")
    print(f"✗ Unmatched Kalshi markets: {len(unmatched_kalshi)}")
    print(f"✗ Unmatched schedule games: {len(unmatched_schedule)}")
    print()

    # Save matched markets
    if matched:
        output_path = 'artifacts/cfb_markets_2025_enriched.csv'
        with open(output_path, 'w', newline='') as f:
            fieldnames = [
                'event_ticker', 'market_ticker', 'market_title', 'yes_subtitle',
                'away_team_kalshi', 'home_team_kalshi',
                'away_team_sched', 'home_team_sched',
                'kickoff_ts', 'kickoff_utc', 'similarity'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched)

        print(f"Saved {len(matched)} enriched markets to: {output_path}")
        print()

        # Show sample matches
        print("Sample matched markets:")
        for i, m in enumerate(matched[:5], 1):
            print(f"{i}. {m['event_ticker']}")
            print(f"   Kalshi: {m['away_team_kalshi']} at {m['home_team_kalshi']}")
            print(f"   Schedule: {m['away_team_sched']} at {m['home_team_sched']}")
            print(f"   Similarity: {m['similarity']:.2%}")
            print(f"   Kickoff: {m['kickoff_utc']}")
            print()

    # Show sample unmatched
    if unmatched_kalshi:
        print("Sample unmatched Kalshi markets:")
        for i, (market, reason) in enumerate(unmatched_kalshi[:5], 1):
            print(f"{i}. {market['market_title']} - {reason}")
        print()

    print("=" * 80)
    print(f"✅ DONE! Matched {len(matched)} CFB markets with schedule")
    print("=" * 80)


if __name__ == '__main__':
    main()
