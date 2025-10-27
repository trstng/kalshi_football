"""
Update College Football Schedule from College Football Data API
Fetches upcoming games and formats them for the Kalshi trading bot.
"""
import requests
import csv
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoints
GAMES_API_URL = "https://api.collegefootballdata.com/games"
CALENDAR_API_URL = "https://api.collegefootballdata.com/calendar"


def fetch_calendar(year: int) -> list:
    """
    Fetch CFB calendar/weeks for a given year.

    Args:
        year: Season year

    Returns:
        List of week information
    """
    params = {"year": year}

    headers = {}
    api_key = os.getenv("CFB_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    print(f"Fetching calendar for {year}...")
    response = requests.get(CALENDAR_API_URL, params=params, headers=headers)
    response.raise_for_status()

    weeks = response.json()
    print(f"Found {len(weeks)} weeks")
    return weeks


def fetch_cfb_games(year: int, week: int = None, season_type: str = "regular") -> list:
    """
    Fetch CFB games from the API.

    Args:
        year: Season year
        week: Optional week number (if None, gets all remaining games)
        season_type: "regular" or "postseason"
    """
    params = {
        "year": year,
        "seasonType": season_type
    }

    if week:
        params["week"] = week

    # Add API key if available
    headers = {}
    api_key = os.getenv("CFB_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    print(f"Fetching games for {year} {season_type} season...")
    response = requests.get(GAMES_API_URL, params=params, headers=headers)
    response.raise_for_status()

    games = response.json()
    print(f"Fetched {len(games)} games")
    return games


def team_to_kalshi_code(team_name: str) -> str:
    """Convert team name to Kalshi ticker code."""
    # Common mappings for Kalshi ticker codes
    mapping = {
        "Air Force": "AFA",
        "Akron": "AKR",
        "Alabama": "ALA",
        "Arizona": "ARIZ",
        "Arizona State": "ASU",
        "Arkansas": "ARK",
        "Army": "ARMY",
        "Auburn": "AUB",
        "Ball State": "BALL",
        "Baylor": "BAY",
        "Boise State": "BSU",
        "Boston College": "BC",
        "Bowling Green": "BGSU",
        "Buffalo": "BUFF",
        "BYU": "BYU",
        "California": "CAL",
        "Central Michigan": "CMU",
        "Charlotte": "CHAR",
        "Cincinnati": "CIN",
        "Clemson": "CLEM",
        "Coastal Carolina": "CCAR",
        "Colorado": "COLO",
        "Colorado State": "CSU",
        "Duke": "DUKE",
        "East Carolina": "ECU",
        "Eastern Michigan": "EMU",
        "Florida": "FLA",
        "Florida Atlantic": "FAU",
        "Florida State": "FSU",
        "Fresno State": "FRES",
        "Georgia": "UGA",
        "Georgia Southern": "GASO",
        "Georgia Tech": "GT",
        "Houston": "HOU",
        "Illinois": "ILL",
        "Indiana": "IND",
        "Iowa": "IOWA",
        "Iowa State": "ISU",
        "James Madison": "JMU",
        "Kansas": "KU",
        "Kansas State": "KSU",
        "Kent State": "KENT",
        "Kentucky": "UK",
        "Liberty": "LIB",
        "Louisiana": "ULL",
        "Louisiana Tech": "LT",
        "Louisville": "LOU",
        "LSU": "LSU",
        "Marshall": "MRSH",
        "Maryland": "MD",
        "Memphis": "MEM",
        "Miami": "MIA",
        "Miami (OH)": "MOH",
        "Michigan": "MICH",
        "Michigan State": "MSU",
        "Middle Tennessee": "MTSU",
        "Minnesota": "MINN",
        "Mississippi State": "MSST",
        "Missouri": "MIZZ",
        "Navy": "NAVY",
        "NC State": "NCST",
        "Nebraska": "NEB",
        "Nevada": "NEV",
        "New Mexico": "UNM",
        "New Mexico State": "NMSU",
        "North Carolina": "UNC",
        "North Texas": "UNT",
        "Northern Illinois": "NIU",
        "Northwestern": "NW",
        "Notre Dame": "ND",
        "Ohio": "OHIO",
        "Ohio State": "OSU",
        "Oklahoma": "OKLA",
        "Oklahoma State": "OKST",
        "Old Dominion": "ODU",
        "Ole Miss": "MISS",
        "Oregon": "ORE",
        "Oregon State": "ORST",
        "Penn State": "PSU",
        "Pittsburgh": "PITT",
        "Purdue": "PUR",
        "Rice": "RICE",
        "Rutgers": "RUTG",
        "San Diego State": "SDSU",
        "San José State": "SJSU",
        "SMU": "SMU",
        "South Alabama": "USA",
        "South Carolina": "SCAR",
        "South Florida": "USF",
        "Southern Miss": "USM",
        "Stanford": "STAN",
        "Syracuse": "SYR",
        "TCU": "TCU",
        "Temple": "TEM",
        "Tennessee": "TENN",
        "Texas": "TEX",
        "Texas A&M": "TXAM",
        "Texas State": "TXST",
        "Texas Tech": "TTU",
        "Toledo": "TOL",
        "Troy": "TROY",
        "Tulane": "TULN",
        "Tulsa": "TLSA",
        "UAB": "UAB",
        "UCF": "UCF",
        "UCLA": "UCLA",
        "UConn": "CONN",
        "ULM": "ULM",
        "UMass": "MASS",
        "UNLV": "UNLV",
        "USC": "USC",
        "Utah": "UTAH",
        "Utah State": "USU",
        "UTEP": "UTEP",
        "UTSA": "UTSA",
        "Vanderbilt": "VAN",
        "Virginia": "UVA",
        "Virginia Tech": "VT",
        "Wake Forest": "WAKE",
        "Washington": "WASH",
        "Washington State": "WSU",
        "West Virginia": "WVU",
        "Western Kentucky": "WKU",
        "Western Michigan": "WMU",
        "Wisconsin": "WIS",
        "Wyoming": "WYO"
    }

    return mapping.get(team_name, team_name.upper().replace(" ", "")[:4])


def format_game_for_kalshi(game: dict) -> dict:
    """Format a game from the API into Kalshi CSV format."""
    # Parse the game time - API uses camelCase
    start_date = game.get("startDate")
    if not start_date:
        return None

    # Convert to timestamp
    dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    kickoff_ts = int(dt.timestamp())

    # Get team info - API uses camelCase
    home_team = game.get("homeTeam")
    away_team = game.get("awayTeam")

    if not home_team or not away_team:
        return None

    # Get team codes
    home_code = team_to_kalshi_code(home_team)
    away_code = team_to_kalshi_code(away_team)

    # Format date for ticker (e.g., 25OCT11)
    date_str = dt.strftime("%y%b%d").upper()

    # Create tickers (format: KXNCAAFGAME-25OCT11AWAYCODE-HOMECODE)
    event_ticker = f"KXNCAAFGAME-{date_str}{away_code}{home_code}"

    # Determine yes_subtitle (typically the favorite or home team)
    # For now, use home team
    yes_subtitle = home_code
    market_ticker = f"{event_ticker}-{yes_subtitle}"

    return {
        "event_ticker": event_ticker,
        "market_ticker": market_ticker,
        "market_title": f"{away_team} at {home_team} Winner?",
        "yes_subtitle": yes_subtitle,
        "series_ticker": "KXNCAAFGAME",
        "away_team": away_team,
        "home_team": home_team,
        "kickoff_ts": kickoff_ts,
        "matched_via": "API_UPDATE"
    }


def update_cfb_schedule(output_path: str, year: int, start_week: int = None):
    """
    Update the CFB schedule file with games from the API.

    Args:
        output_path: Path to save the CSV
        year: Season year
        start_week: Optional starting week (if None, uses calendar to get remaining weeks)
    """
    # Fetch calendar to determine current and upcoming weeks
    calendar = fetch_calendar(year)

    now = datetime.now(timezone.utc)

    # Find upcoming weeks
    upcoming_weeks = []
    for week_info in calendar:
        # Check if this week has future games
        first_game_start = week_info.get("firstGameStart")
        if first_game_start:
            week_start = datetime.fromisoformat(first_game_start.replace("Z", "+00:00"))
            # Include weeks that haven't ended yet (give 7 day buffer)
            if week_start > now - timedelta(days=7):
                week_num = week_info.get("week")
                season_type = week_info.get("seasonType", "regular")
                upcoming_weeks.append((week_num, season_type))

    print(f"\nFound {len(upcoming_weeks)} upcoming weeks")

    # Fetch games for upcoming weeks
    all_games = []
    for week_num, season_type in upcoming_weeks:
        print(f"Fetching week {week_num} ({season_type})...")
        games = fetch_cfb_games(year, week_num, season_type)
        all_games.extend(games)

    # Filter and format games that haven't started yet
    now = datetime.now(timezone.utc)
    formatted_games = []

    # Filter future games
    future_count = 0
    for game in all_games:
        # Only include games that haven't started - API uses camelCase
        start_date = game.get("startDate")
        if start_date:
            game_time = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if game_time > now:
                future_count += 1
                formatted = format_game_for_kalshi(game)
                if formatted:
                    formatted_games.append(formatted)

    # Sort by kickoff time
    formatted_games.sort(key=lambda x: x["kickoff_ts"])

    # Write to CSV
    if formatted_games:
        fieldnames = ["event_ticker", "market_ticker", "market_title", "yes_subtitle",
                     "series_ticker", "away_team", "home_team", "kickoff_ts", "matched_via"]

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(formatted_games)

        print(f"\n✓ Updated CFB schedule with {len(formatted_games)} upcoming games")
        print(f"  Saved to: {output_path}")

        # Show first few games
        print("\nNext 5 games:")
        for game in formatted_games[:5]:
            dt = datetime.fromtimestamp(game["kickoff_ts"], tz=timezone.utc)
            print(f"  {dt.strftime('%Y-%m-%d %H:%M UTC')}: {game['away_team']} @ {game['home_team']}")
    else:
        print("No upcoming games found")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("CFB_API_KEY"):
        print("WARNING: CFB_API_KEY not found in environment variables")
        print("Get a free API key at: https://collegefootballdata.com/key")
        print("Add it to your .env file as: CFB_API_KEY=your_key_here")
        print("\nAttempting to fetch without authentication (may fail)...\n")

    # Determine current year and week
    now = datetime.now()
    current_year = now.year

    # Path to the schedule file
    schedule_path = Path(__file__).parent.parent / "frontend" / "public" / "schedules" / "cfb_schedule.csv"

    print(f"Updating CFB schedule for {current_year}...")

    # Update with all remaining games from current week onwards
    # You can specify a week number as a command line argument
    start_week = int(sys.argv[1]) if len(sys.argv) > 1 else None

    update_cfb_schedule(str(schedule_path), current_year, start_week)
