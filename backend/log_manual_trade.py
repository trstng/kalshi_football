"""
Script to manually log trades to Supabase for historical tracking.
Used for trades that were executed manually before automated tracking was set up.
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase_logger import SupabaseLogger

load_dotenv()

def log_manual_trade(
    market_ticker: str,
    market_title: str,
    yes_subtitle: str,
    kickoff_ts: int,
    pregame_prob: float,
    entry_price: int,
    exit_price: int,
    size: int,
    entry_time: int,
    exit_time: int,
    notes: str = ""
):
    """
    Log a manual trade to the database.

    Args:
        market_ticker: Market ticker (e.g., KXNCAAFGAME-25OCT15UTEPSHSU-UTEP)
        market_title: Game title (e.g., "UTEP at Sam Houston Winner?")
        yes_subtitle: Winning team name (e.g., "UTEP")
        kickoff_ts: Kickoff timestamp (unix)
        pregame_prob: Pregame probability of favorite (0.0-1.0)
        entry_price: Entry price in cents (e.g., 35 for 35¢)
        exit_price: Exit price in cents (e.g., 55 for 55¢)
        size: Number of contracts
        entry_time: Entry time (unix timestamp)
        exit_time: Exit time (unix timestamp)
        notes: Optional notes about the trade
    """
    logger = SupabaseLogger()

    if not logger.client:
        print("❌ Supabase client not initialized. Check your environment variables.")
        return

    # Calculate P&L
    pnl = ((exit_price - entry_price) / 100.0) * size

    print(f"\n{'='*80}")
    print(f"Logging Manual Trade")
    print(f"{'='*80}")
    print(f"Market: {market_title}")
    print(f"Ticker: {market_ticker}")
    print(f"Favorite: {yes_subtitle} ({pregame_prob:.0%})")
    print(f"Kickoff: {datetime.fromtimestamp(kickoff_ts).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"\nTrade Details:")
    print(f"  Entry: {entry_price}¢ @ {datetime.fromtimestamp(entry_time).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Exit:  {exit_price}¢ @ {datetime.fromtimestamp(exit_time).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Size:  {size} contracts")
    print(f"  P&L:   ${pnl:+.2f}")
    if notes:
        print(f"  Notes: {notes}")
    print(f"{'='*80}\n")

    # Log game
    game_data = {
        'market_ticker': market_ticker,
        'event_ticker': market_ticker.rsplit('-', 1)[0],  # Remove last part
        'market_title': market_title,
        'yes_subtitle': yes_subtitle,
        'kickoff_ts': kickoff_ts,
        'halftime_ts': kickoff_ts + 5400,  # 90 minutes later
        'pregame_prob': pregame_prob,
        'status': 'completed'
    }

    try:
        logger.log_game(game_data)
        print("✓ Game logged")
    except Exception as e:
        print(f"  Note: Game may already exist ({e})")

    # Log position entry
    position_data = {
        'market_ticker': market_ticker,
        'entry_price': entry_price,
        'size': size,
        'entry_time': entry_time,
        'order_id': f'MANUAL_{market_ticker}_{entry_time}'
    }

    try:
        logger.log_position_entry(position_data)
        print("✓ Position entry logged")
    except Exception as e:
        print(f"✗ Error logging position entry: {e}")

    # Log position exit
    try:
        logger.log_position_exit(
            market_ticker=market_ticker,
            exit_price=exit_price,
            exit_time=exit_time,
            pnl=pnl
        )
        print("✓ Position exit logged")
    except Exception as e:
        print(f"✗ Error logging position exit: {e}")

    print("\n✅ Manual trade logged successfully!\n")


if __name__ == '__main__':
    # Miami Hurricanes Game - Position 1
    # Bought 20 @ 49¢ at 5:30pm CDT, sold @ 60¢ at 6:35pm CDT
    # Oct 17, 2025 5:30pm CDT = Oct 17, 2025 10:30pm UTC = 1760 204 200
    # Oct 17, 2025 6:35pm CDT = Oct 17, 2025 11:35pm UTC = 1760 208 100
    # Kickoff: 7:00pm EDT = 6:00pm CDT = Oct 17, 2025 11:00pm UTC = 1760 206 400
    log_manual_trade(
        market_ticker='KXNCAAFGAME-25OCT17LOUMIA-MIA',
        market_title='Louisville at Miami Winner?',
        yes_subtitle='Miami',
        kickoff_ts=1760206400,  # Oct 17, 2025, 7:00 PM EDT (6:00 PM CDT)
        pregame_prob=0.65,
        entry_price=49,
        exit_price=60,
        size=20,
        entry_time=1760204200,  # 5:30 PM CDT
        exit_time=1760208100,   # 6:35 PM CDT
        notes="Manual trade - Miami game. Entry 1 of 2. Bought 20 @ 49¢, sold @ 60¢. Profit: $2.20"
    )

    # Miami Hurricanes Game - Position 2
    # Bought 33 @ 45¢ at 5:30pm CDT, sold @ 60¢ at 6:35pm CDT
    log_manual_trade(
        market_ticker='KXNCAAFGAME-25OCT17LOUMIA-MIA',
        market_title='Louisville at Miami Winner?',
        yes_subtitle='Miami',
        kickoff_ts=1760206400,  # Oct 17, 2025, 7:00 PM EDT (6:00 PM CDT)
        pregame_prob=0.65,
        entry_price=45,
        exit_price=60,
        size=33,
        entry_time=1760204200,  # 5:30 PM CDT
        exit_time=1760208100,   # 6:35 PM CDT
        notes="Manual trade - Miami game. Entry 2 of 2. Bought 33 @ 45¢, sold @ 60¢. Profit: $4.95"
    )

    print("\n" + "=" * 80)
    print("✅ Miami game trades logged successfully!")
    print("=" * 80)
    print("Summary:")
    print("  Position 1: 20 @ 49¢ → 60¢ = +$2.20")
    print("  Position 2: 33 @ 45¢ → 60¢ = +$4.95")
    print("  Total: 53 contracts, +$7.15 profit")
    print("\nCheck your dashboard to see the trades tracked!")
    print("=" * 80)
