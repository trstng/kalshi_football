"""
Supabase Logger - Writes trading bot data to Supabase for dashboard visualization
"""
import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseLogger:
    """Handles all Supabase writes for the trading bot."""

    def __init__(self):
        """Initialize Supabase client from environment variables."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            logger.warning("⚠️  Supabase credentials not found. Dashboard will not update.")
            logger.warning("   Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            self.client = None
            return

        try:
            self.client: Client = create_client(url, key)
            logger.info("✓ Connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.client = None

    def log_game(self, game_data: dict) -> Optional[str]:
        """
        Log a new game to the database.

        Args:
            game_data: Dict with keys: market_ticker, event_ticker, market_title,
                      yes_subtitle, kickoff_ts, halftime_ts, pregame_prob, status

        Returns:
            Game ID if successful, None otherwise
        """
        if not self.client:
            return None

        try:
            # Check if game already exists
            existing = self.client.table('games').select('id').eq('market_ticker', game_data['market_ticker']).execute()

            if existing.data:
                return existing.data[0]['id']

            # Insert new game
            result = self.client.table('games').insert(game_data).execute()

            if result.data:
                game_id = result.data[0]['id']
                logger.debug(f"Logged game to Supabase: {game_data['market_ticker']}")
                return game_id

        except Exception as e:
            logger.error(f"Error logging game to Supabase: {e}")

        return None

    def update_game_status(self, market_ticker: str, status: str, pregame_prob: Optional[float] = None):
        """Update game status (monitoring, triggered, completed, timeout)."""
        if not self.client:
            return

        try:
            update_data = {'status': status, 'updated_at': 'now()'}
            if pregame_prob is not None:
                update_data['pregame_prob'] = pregame_prob

            self.client.table('games').update(update_data).eq('market_ticker', market_ticker).execute()
            logger.debug(f"Updated game status: {market_ticker} -> {status}")
        except Exception as e:
            logger.error(f"Error updating game status: {e}")

    def log_position_entry(self, position_data: dict) -> Optional[str]:
        """
        Log a new position entry.

        Args:
            position_data: Dict with keys: market_ticker, entry_price, size,
                          entry_time, order_id, status='open'

        Returns:
            Position ID if successful, None otherwise
        """
        if not self.client:
            return None

        try:
            # Get game_id from market_ticker
            game = self.client.table('games').select('id').eq('market_ticker', position_data['market_ticker']).execute()

            if not game.data:
                logger.warning(f"Game not found for position: {position_data['market_ticker']}")
                return None

            position_data['game_id'] = game.data[0]['id']
            position_data['status'] = 'open'

            result = self.client.table('positions').insert(position_data).execute()

            if result.data:
                position_id = result.data[0]['id']
                logger.debug(f"Logged position entry: {position_data['size']} @ {position_data['entry_price']}¢")
                return position_id

        except Exception as e:
            logger.error(f"Error logging position entry: {e}")

        return None

    def log_position_exit(self, market_ticker: str, exit_price: int, exit_time: int, pnl: float):
        """Update position with exit details and calculate P&L."""
        if not self.client:
            return

        try:
            # Update all open positions for this market
            update_data = {
                'exit_price': exit_price,
                'exit_time': exit_time,
                'pnl': pnl,
                'status': 'closed',
                'updated_at': 'now()'
            }

            self.client.table('positions').update(update_data).eq('market_ticker', market_ticker).eq('status', 'open').execute()
            logger.debug(f"Logged position exit: {market_ticker} P&L=${pnl:+.2f}")

        except Exception as e:
            logger.error(f"Error logging position exit: {e}")

    def log_bankroll_change(self, timestamp: int, new_amount: float, change: float,
                           game_id: Optional[str] = None, description: Optional[str] = None):
        """Log a bankroll change to the history table."""
        if not self.client:
            return

        try:
            data = {
                'timestamp': timestamp,
                'amount': new_amount,
                'change': change,
                'game_id': game_id,
                'description': description
            }

            self.client.table('bankroll_history').insert(data).execute()
            logger.debug(f"Logged bankroll: ${new_amount:.2f} ({change:+.2f})")

        except Exception as e:
            logger.error(f"Error logging bankroll change: {e}")
