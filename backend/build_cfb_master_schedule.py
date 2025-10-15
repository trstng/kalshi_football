"""
Build a master CFB schedule from the 7 uploaded CSV files.
Converts ET times to UTC.
"""
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

# ET and UTC timezones
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

# Input files
CFB_FILES = [
    'artifacts/cfb_aug28_sep1_2025.csv',
    'artifacts/cfb_sep5_sep6_2025.csv',
    'artifacts/cfb_sep11_sep13_2025.csv',
    'artifacts/cfb_sep18_sep20_2025.csv',
    'artifacts/cfb_sep25_sep27_2025.csv',
    'artifacts/cfb_oct2_oct4_2025.csv',
    'artifacts/cfb_oct8_oct11_2025.csv',
]

OUTPUT_FILE = 'artifacts/cfb_2025_schedule_master.csv'

def parse_cfb_datetime(date_str: str, time_str: str) -> datetime | None:
    """
    Parse CFB date and time strings to UTC datetime.

    Args:
        date_str: e.g., "Thursday, August 28"
        time_str: e.g., "5:30pm", "12:00pm"

    Returns:
        datetime in UTC, or None if parsing fails
    """
    try:
        # Parse date (assuming 2025)
        # Format: "Thursday, August 28"
        date_obj = datetime.strptime(date_str + " 2025", "%A, %B %d %Y")

        # Parse time
        # Format: "5:30pm", "12:00pm", "11:59pm"
        time_obj = datetime.strptime(time_str, "%I:%M%p")

        # Combine date and time in ET
        dt_et = datetime(
            year=date_obj.year,
            month=date_obj.month,
            day=date_obj.day,
            hour=time_obj.hour,
            minute=time_obj.minute,
            tzinfo=ET
        )

        # Convert to UTC
        dt_utc = dt_et.astimezone(UTC)

        return dt_utc

    except Exception as e:
        print(f"Error parsing date='{date_str}' time='{time_str}': {e}")
        return None


def main():
    all_games = []

    for cfb_file in CFB_FILES:
        print(f"\nProcessing {cfb_file}...")

        with open(cfb_file, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                date_str = row['date']
                time_str = row['time_et']
                team1 = row['team1']
                team2 = row['team2']

                # Skip empty rows
                if not date_str or not time_str or not team1 or not team2:
                    continue

                # Parse datetime
                kickoff_utc = parse_cfb_datetime(date_str, time_str)

                if kickoff_utc is None:
                    continue

                # Store game info
                game = {
                    'date': date_str,
                    'time_et': time_str,
                    'kickoff_utc': kickoff_utc.isoformat(),
                    'kickoff_ts': int(kickoff_utc.timestamp()),
                    'away_team': team1,
                    'home_team': team2,
                    'away_rank': row.get('team1_rank', ''),
                    'home_rank': row.get('team2_rank', ''),
                }

                all_games.append(game)

    # Sort by kickoff time
    all_games.sort(key=lambda g: g['kickoff_ts'])

    # Write master schedule
    print(f"\n{'=' * 80}")
    print(f"Writing {len(all_games)} games to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w', newline='') as f:
        fieldnames = [
            'date', 'time_et', 'kickoff_utc', 'kickoff_ts',
            'away_team', 'home_team', 'away_rank', 'home_rank'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_games)

    print(f"✓ Master schedule created with {len(all_games)} games")
    print(f"{'=' * 80}\n")

    # Print sample
    print("Sample games:")
    for game in all_games[:5]:
        print(f"  {game['date']} {game['time_et']}: {game['away_team']} @ {game['home_team']}")

    print(f"\n... {len(all_games) - 5} more games ...")


if __name__ == '__main__':
    main()
