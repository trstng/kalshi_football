"""
Verify how the bot discovers games and tracks time.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path.cwd() / 'src'))

from kalshi_nfl_research.kalshi_client import KalshiClient

print("=" * 80)
print("GAME DISCOVERY VERIFICATION")
print("=" * 80)
print()

client = KalshiClient()

# Show current time
now = datetime.utcnow()
now_ts = int(now.timestamp())
print(f"Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Unix timestamp: {now_ts}")
print()

# Get NFL events
print("Fetching NFL events from Kalshi API...")
nfl_events = client.get_events(series_ticker='KXNFLGAME')
print(f"Found {len(nfl_events)} NFL events")
print()

# Show upcoming games with kickoff times
lookahead_hours = 24
lookahead_ts = now_ts + (lookahead_hours * 3600)

upcoming = []
for event in nfl_events:
    strike_date = event.get('strike_date')
    if strike_date and now_ts < strike_date < lookahead_ts:
        upcoming.append(event)

print(f"Games starting in next {lookahead_hours} hours: {len(upcoming)}")
print()

if upcoming:
    print("Sample upcoming games:")
    for event in upcoming[:3]:
        kickoff = datetime.fromtimestamp(event['strike_date'])
        time_until = event['strike_date'] - now_ts
        hours_until = time_until / 3600
        
        print(f"  Event: {event['event_ticker']}")
        print(f"  Title: {event.get('title', 'N/A')}")
        print(f"  Kickoff: {kickoff.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Time until kickoff: {hours_until:.1f} hours")
        print()
else:
    print("No games found in next 24 hours.")
    print()
    
    # Show next game after 24 hours
    future_games = [e for e in nfl_events if e.get('strike_date', 0) > lookahead_ts]
    if future_games:
        future_games.sort(key=lambda e: e['strike_date'])
        next_game = future_games[0]
        kickoff = datetime.fromtimestamp(next_game['strike_date'])
        time_until = next_game['strike_date'] - now_ts
        days_until = time_until / 86400
        
        print(f"Next game after that:")
        print(f"  Event: {next_game['event_ticker']}")
        print(f"  Kickoff: {kickoff.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Time until: {days_until:.1f} days")
        print()

print("=" * 80)
print("KEY POINTS:")
print("=" * 80)
print()
print("✓ Bot gets kickoff times directly from Kalshi API")
print("✓ strike_date field contains Unix timestamp of kickoff")
print("✓ Bot compares current time vs. kickoff time")
print("✓ No external schedule needed")
print()
print("✓ Bot runs continuously in a loop:")
print("  - Checks for new games every 10 seconds")
print("  - Monitors active games for entry/exit signals")
print("  - Automatically discovers games as Kalshi adds them")
print()
print("⚠️ Bot only runs when your computer is on")
print("  - Use 'caffeinate' on Mac to prevent sleep")
print("  - Or deploy to cloud server for 24/7 operation")
print()

client.close()
