"""
Live Trading Bot - FIXED VERSION
Uses external schedule CSVs since Kalshi doesn't provide strike_date for football games.
"""
import logging
import os
import time
import yaml
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.trading_client import KalshiTradingClient
from supabase_logger import SupabaseLogger

# Load environment variables
load_dotenv()

# Create logs directory before logging config
Path("logs").mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GameMonitor:
    """Monitors a single game for trading opportunities."""
    event_ticker: str
    market_ticker: str
    market_title: str
    yes_subtitle: str
    kickoff_ts: int
    halftime_ts: int

    # Legacy field (kept for compatibility, will be set at 6h checkpoint)
    pregame_prob: Optional[float] = None

    # Three checkpoint odds
    odds_6h: Optional[float] = None
    odds_3h: Optional[float] = None
    odds_30m: Optional[float] = None

    # Checkpoint timestamps (when we captured each)
    checkpoint_6h_ts: Optional[int] = None
    checkpoint_3h_ts: Optional[int] = None
    checkpoint_30m_ts: Optional[int] = None

    # Eligibility for trading
    is_eligible: Optional[bool] = None  # None = not yet determined

    # Trading side (which side we're buying: yes or no)
    position_side: Optional[str] = None  # "yes" or "no" - the favorite side we're buying

    # Order tracking
    triggered: bool = False  # Have we placed orders yet?
    order_ids: list = field(default_factory=list)  # Pending order IDs
    positions: list = field(default_factory=list)  # Filled positions only


@dataclass
class Position:
    """Represents an open position."""
    market_ticker: str
    side: str  # "yes" or "no"
    entry_price: int
    size: int
    entry_time: int
    order_id: Optional[str] = None
    exit_order_id: Optional[str] = None  # Sell order at 55¢


class LiveTrader:
    """Main live trading bot - FIXED to use external schedules."""

    def __init__(self, config_path: str = "live_trading_config.yaml"):
        logger.info("=" * 80)
        logger.info("KALSHI LIVE TRADING BOT (FIXED VERSION)")
        logger.info("=" * 80)
        logger.info("")

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize clients
        self.public_client = KalshiClient()

        if not self.config['risk']['dry_run']:
            creds = self.config['api_credentials']
            # Read from environment variables first, fallback to config
            email = os.getenv('KALSHI_EMAIL') or creds.get('email')
            password = os.getenv('KALSHI_PASSWORD') or creds.get('password')
            api_key = os.getenv('KALSHI_API_KEY') or creds.get('api_key')
            api_secret = os.getenv('KALSHI_API_SECRET') or creds.get('api_secret')

            self.trading_client = KalshiTradingClient(
                email=email,
                password=password,
                api_key=api_key,
                api_secret=api_secret,
            )
            logger.info("✓ Trading client initialized (LIVE MODE)")
            logger.info(f"  Using credentials from: {'environment variables' if os.getenv('KALSHI_API_KEY') else 'config file'}")
        else:
            self.trading_client = None
            logger.warning("⚠️  DRY RUN MODE - No real orders will be placed")

        # Load schedules
        self.nfl_schedule = self._load_nfl_schedule()
        self.cfb_schedule = self._load_cfb_schedule()

        logger.info(f"Loaded {len(self.nfl_schedule)} NFL games with kickoff times")
        logger.info(f"Loaded {len(self.cfb_schedule)} CFB games with kickoff times")
        logger.info("")

        # Trading state
        self.bankroll = self.config['trading']['bankroll']
        self.active_games: dict[str, GameMonitor] = {}
        self.total_exposure = 0.0

        logger.info(f"Starting bankroll: ${self.bankroll:,.2f}")
        logger.info("")

        # Initialize Supabase logger for dashboard
        self.supabase = SupabaseLogger()

        # Log initial bankroll
        if self.supabase.client:
            self.supabase.log_bankroll_change(
                timestamp=int(time.time()),
                new_amount=self.bankroll,
                change=0.0,
                description="Bot started"
            )

    def _load_nfl_schedule(self) -> dict:
        """Load NFL enriched schedule with kickoff times."""
        schedule = {}
        path = 'artifacts/nfl_markets_2025_enriched.csv'
        
        try:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Key by market_ticker for easy lookup
                    schedule[row['market_ticker']] = {
                        'event_ticker': row['event_ticker'],
                        'market_ticker': row['market_ticker'],
                        'market_title': row['market_title'],
                        'yes_subtitle': row['yes_subtitle'],
                        'kickoff_ts': int(row['strike_date']),
                    }
            logger.info(f"✓ Loaded NFL schedule from {path}")
        except Exception as e:
            logger.warning(f"Could not load NFL schedule: {e}")
        
        return schedule

    def _load_cfb_schedule(self) -> dict:
        """Load CFB enriched schedule with kickoff times."""
        schedule = {}
        path = 'artifacts/cfb_markets_2025_enriched.csv'
        
        try:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    schedule[row['market_ticker']] = {
                        'event_ticker': row['event_ticker'],
                        'market_ticker': row['market_ticker'],
                        'market_title': row['market_title'],
                        'yes_subtitle': row['yes_subtitle'],
                        'kickoff_ts': int(row['kickoff_ts']),
                    }
            logger.info(f"✓ Loaded CFB schedule from {path}")
        except Exception as e:
            logger.warning(f"Could not load CFB schedule: {e}")
        
        return schedule

    def discover_upcoming_games(self) -> list[GameMonitor]:
        """Discover games starting in the next few hours using schedules."""
        now = int(datetime.utcnow().timestamp())
        lookahead = now + (self.config['monitoring']['lookahead_hours'] * 3600)

        games = []

        # Check schedules for upcoming games
        for market_ticker, game_data in {**self.nfl_schedule, **self.cfb_schedule}.items():
            kickoff_ts = game_data['kickoff_ts']
            
            # Only games starting soon
            if now < kickoff_ts < lookahead:
                halftime_ts = kickoff_ts + 5400  # 90 minutes

                game = GameMonitor(
                    event_ticker=game_data['event_ticker'],
                    market_ticker=market_ticker,
                    market_title=game_data['market_title'],
                    yes_subtitle=game_data['yes_subtitle'],
                    kickoff_ts=kickoff_ts,
                    halftime_ts=halftime_ts,
                )
                games.append(game)

        return games

    def get_current_price(self, market_ticker: str) -> Optional[float]:
        """Get current market price (favorite's probability)."""
        try:
            market = self.public_client.get_market(market_ticker)
            if not market:
                return None

            # Get best ask prices for both sides (price to BUY)
            yes_ask = market.yes_ask if market.yes_ask is not None else 0
            no_ask = market.no_ask if market.no_ask is not None else 0

            # Return the higher of the two (the favorite's probability)
            favorite_price = max(yes_ask, no_ask)
            return favorite_price / 100.0 if favorite_price > 0 else None
        except Exception as e:
            logger.error(f"Error fetching price for {market_ticker}: {e}")
            return None

    def get_favorite_side(self, market_ticker: str) -> Optional[str]:
        """Determine which side (yes/no) represents the favorite."""
        try:
            market = self.public_client.get_market(market_ticker)
            if not market:
                return None

            # Get best ask prices for both sides (price to BUY)
            yes_ask = market.yes_ask if market.yes_ask is not None else 0
            no_ask = market.no_ask if market.no_ask is not None else 0

            # Return the side with higher probability (the favorite)
            return "yes" if yes_ask >= no_ask else "no"
        except Exception as e:
            logger.error(f"Error determining favorite side for {market_ticker}: {e}")
            return None

    def check_and_capture_checkpoint(self, game: GameMonitor, now: int) -> bool:
        """
        Check if we need to capture a checkpoint and do so.

        Returns True if a checkpoint was captured.
        """
        time_to_kickoff = game.kickoff_ts - now

        # Define checkpoint windows (in seconds)
        SIX_HOURS = 6 * 3600
        THREE_HOURS = 3 * 3600
        THIRTY_MIN = 30 * 60

        # 6-hour checkpoint (within 6h-5.5h window)
        if time_to_kickoff <= SIX_HOURS and game.odds_6h is None:
            current_price = self.get_current_price(game.market_ticker)
            if current_price:
                game.odds_6h = current_price
                game.checkpoint_6h_ts = now
                game.pregame_prob = current_price  # Set legacy field
                logger.info(f"  6h checkpoint: {current_price:.0%}")

                # Update database
                if self.supabase.client:
                    self.supabase.update_game_checkpoint(game.market_ticker, 'odds_6h', current_price, now)
                return True

        # 3-hour checkpoint (within 3h-2.5h window)
        elif time_to_kickoff <= THREE_HOURS and game.odds_3h is None:
            current_price = self.get_current_price(game.market_ticker)
            if current_price:
                game.odds_3h = current_price
                game.checkpoint_3h_ts = now
                logger.info(f"  3h checkpoint: {current_price:.0%}")

                # Update database
                if self.supabase.client:
                    self.supabase.update_game_checkpoint(game.market_ticker, 'odds_3h', current_price, now)
                return True

        # 30-min checkpoint (within 30min-25min window)
        elif time_to_kickoff <= THIRTY_MIN and game.odds_30m is None:
            current_price = self.get_current_price(game.market_ticker)
            if current_price:
                game.odds_30m = current_price
                game.checkpoint_30m_ts = now
                logger.info(f"  30m checkpoint: {current_price:.0%}")

                # Determine final eligibility
                self._determine_eligibility(game)

                # Update database
                if self.supabase.client:
                    self.supabase.update_game_checkpoint(game.market_ticker, 'odds_30m', current_price, now)
                    self.supabase.update_game_eligibility(game.market_ticker, game.is_eligible)
                return True

        return False

    def _determine_eligibility(self, game: GameMonitor):
        """
        Determine if game is eligible for trading based on checkpoint rules.

        Rules:
        - If ANY checkpoint >= 57% → Eligible
        - BUT if odds_30m < 57% → Override to NOT eligible (final veto)
        """
        threshold = 0.57

        # Check if any checkpoint >= 57%
        checkpoint_odds = [game.odds_6h, game.odds_3h, game.odds_30m]
        has_high_checkpoint = any(odds and odds >= threshold for odds in checkpoint_odds if odds is not None)

        # Final veto: if 30m checkpoint < 57%, not eligible
        if game.odds_30m is not None and game.odds_30m < threshold:
            game.is_eligible = False
            logger.info(f"  → NOT ELIGIBLE (30m veto: {game.odds_30m:.0%} < 57%)")
        elif has_high_checkpoint:
            game.is_eligible = True
            logger.info(f"  → ELIGIBLE (checkpoint(s) >= 57%)")
        else:
            game.is_eligible = False
            logger.info(f"  → NOT ELIGIBLE (no checkpoint >= 57%)")

    def calculate_position_sizes(
        self,
        bankroll: float,
        kelly_frac: float,
        max_exposure: float,
        current_price_cents: int,
        levels_to_hit: list[dict],
    ) -> list[tuple[int, int]]:
        """Calculate position sizes with Kelly criterion and exposure limits."""
        ideal_positions = []
        total_ideal_capital = 0

        for level in levels_to_hit:
            price_dollars = level['trigger'] / 100.0
            base_size = int((bankroll * kelly_frac) / price_dollars)
            actual_size = max(1, int(base_size * level['kelly_mult']))

            ideal_capital = actual_size * price_dollars
            total_ideal_capital += ideal_capital

            ideal_positions.append({
                'trigger': level['trigger'],
                'ideal_size': actual_size,
                'ideal_capital': ideal_capital
            })

        max_capital_allowed = bankroll * max_exposure

        if total_ideal_capital <= max_capital_allowed:
            return [(p['trigger'], p['ideal_size']) for p in ideal_positions]
        else:
            scale_factor = max_capital_allowed / total_ideal_capital
            scaled_positions = []
            for pos in ideal_positions:
                scaled_size = max(1, int(pos['ideal_size'] * scale_factor))
                scaled_positions.append((pos['trigger'], scaled_size))
            return scaled_positions

    def check_entry_signal(self, game: GameMonitor) -> bool:
        """Check if we should enter a position for this game."""
        now = int(datetime.utcnow().timestamp())

        if now >= game.kickoff_ts:
            return False

        # Must have completed 30m checkpoint to determine eligibility
        if game.is_eligible is None:
            return False  # Still waiting for checkpoints

        # Must be eligible based on checkpoint rules
        if not game.is_eligible:
            return False

        # Once eligible, place all limit orders immediately
        # (Kalshi will fill them as price drops through each level)
        return True

    def enter_position(self, game: GameMonitor):
        """Enter position with limit order ladder strategy."""
        logger.info("=" * 80)
        logger.info(f"ENTRY SIGNAL: {game.market_title} ({game.yes_subtitle})")
        logger.info("=" * 80)

        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            logger.error("Could not get current price, skipping")
            return

        # Determine which side to buy (yes or no) - we always want the FAVORITE
        favorite_side = self.get_favorite_side(game.market_ticker)
        if favorite_side is None:
            logger.error("Could not determine favorite side, skipping")
            return

        current_price_cents = int(current_price * 100)

        logger.info(f"Pregame: {game.pregame_prob:.0%} → Current: {current_price:.0%}")
        logger.info(f"Buying {favorite_side.upper()} (the favorite)")
        logger.info(f"Placing limit order ladder (Kalshi will fill as price drops)")

        # Use ALL scaling levels from config (don't filter by current price)
        scaling_levels = self.config['trading']['scaling_levels']

        logger.info(f"Limit orders to place: {len(scaling_levels)} levels")

        positions = self.calculate_position_sizes(
            self.bankroll,
            self.config['trading']['kelly_fraction'],
            self.config['trading']['max_exposure_pct'],
            current_price_cents,
            scaling_levels  # Use ALL levels, not filtered by current price
        )

        total_capital = sum(price * size / 100.0 for price, size in positions)
        logger.info(f"Total capital at risk: ${total_capital:,.2f}")

        if total_capital > self.config['safety']['max_total_exposure']:
            logger.warning(f"⚠️  Total exposure ${total_capital:,.2f} exceeds limit, skipping")
            return

        for price_cents, size in positions:
            logger.info(f"  Level: {size:4d} contracts @ {price_cents}¢ = ${price_cents * size / 100:.2f}")

            if self.config['risk']['dry_run']:
                logger.info("  [DRY RUN] Would place order here")
                order_id = f"dry_run_{len(game.order_ids)}"
                game.order_ids.append(order_id)
            else:
                try:
                    order = self.trading_client.place_order(
                        market_ticker=game.market_ticker,
                        side=favorite_side,  # Buy the favorite side (yes or no)
                        action="buy",
                        count=size,
                        price=price_cents,
                        order_type="limit"
                    )
                    logger.info(f"  ✓ Order placed: {order.order_id} (status: {order.status})")

                    # Check if order filled immediately
                    if order.status == "executed":
                        logger.info(f"  🎉 IMMEDIATE FILL: {size} contracts @ {price_cents}¢")
                        # Create position immediately (don't add to pending orders)
                        position = Position(
                            market_ticker=game.market_ticker,
                            side=favorite_side,
                            entry_price=price_cents,
                            size=size,
                            entry_time=int(time.time()),
                            order_id=order.order_id
                        )
                        game.positions.append(position)

                        # Log position to dashboard
                        if self.supabase.client:
                            try:
                                self.supabase.log_position_entry({
                                    'market_ticker': game.market_ticker,
                                    'entry_price': price_cents,
                                    'size': size,
                                    'entry_time': int(time.time()),
                                    'order_id': order.order_id
                                })
                            except Exception as db_error:
                                logger.error(f"    ✗ Failed to log position to dashboard: {db_error}")

                        # IMMEDIATELY place exit order at 55¢ (bracket strategy)
                        self._place_exit_order(game, position)
                    else:
                        # Order is pending - add to monitoring list
                        game.order_ids.append(order.order_id)

                        # Log order to dashboard (NOT position - that happens when order fills)
                        if self.supabase.client:
                            self.supabase.log_order(
                                market_ticker=game.market_ticker,
                                order_id=order.order_id,
                                price=price_cents,
                                size=size,
                                side='buy'
                            )

                except Exception as e:
                    logger.error(f"  ✗ Error placing order: {e}")

        game.triggered = True
        game.position_side = favorite_side  # Store which side we're trading
        game.highest_entry = max(p[0] for p in positions)
        self.total_exposure += total_capital

        # Update game status to triggered
        if self.supabase.client:
            self.supabase.update_game_status(game.market_ticker, 'triggered', game.pregame_prob)

        logger.info(f"Orders placed. Total potential exposure: ${self.total_exposure:,.2f}")
        logger.info("")

    def _place_exit_order(self, game: GameMonitor, position: Position):
        """
        Place exit order at 55¢ for a filled position (bracket strategy).
        """
        revert_bands = self.config['trading']['revert_bands']
        if not revert_bands:
            logger.warning("No revert bands configured, skipping exit order")
            return

        exit_price_cents = int(revert_bands[0] * 100)  # First band (typically 55¢)

        logger.info(f"  → Placing exit order: {position.size} contracts @ {exit_price_cents}¢")

        if self.config['risk']['dry_run']:
            logger.info("    [DRY RUN] Would place exit order here")
            position.exit_order_id = f"dry_run_exit_{position.order_id}"
            return

        if not self.trading_client:
            return

        try:
            exit_order = self.trading_client.place_order(
                market_ticker=game.market_ticker,
                side=position.side,  # Sell the same side we bought
                action="sell",
                count=position.size,
                price=exit_price_cents,
                order_type="limit"
            )
            position.exit_order_id = exit_order.order_id
            logger.info(f"    ✓ Exit order placed: {exit_order.order_id}")

        except Exception as e:
            logger.error(f"    ✗ Error placing exit order: {e}")

    def check_order_fills(self, game: GameMonitor):
        """Check if any pending orders have filled and convert them to positions."""
        if not game.order_ids or self.config['risk']['dry_run']:
            return

        if not self.trading_client:
            return

        logger.info(f"Checking {len(game.order_ids)} pending order(s) for {game.market_ticker}")
        filled_orders = []

        for order_id in game.order_ids:
            try:
                logger.info(f"  Checking order status: {order_id}")
                status_response = self.trading_client.get_order_status(order_id)

                # None means 404 - order was executed/cancelled and removed from active orders
                if status_response is None:
                    logger.info(f"  ⚠️  Order {order_id} not found (likely executed) - removing from pending list")
                    filled_orders.append(order_id)
                    continue

                if not status_response or 'order' not in status_response:
                    logger.error(f"  ✗ Invalid response for order {order_id}: {status_response}")
                    continue

                order_status = status_response.get('order', {})

                status = order_status.get('status', 'pending')
                filled_count = order_status.get('filled_count', 0)
                total_count = order_status.get('count', 0)
                price = order_status.get('yes_price') or order_status.get('no_price', 0)

                logger.info(f"    Status: {status}, Filled: {filled_count}/{total_count} @ {price}¢")

                # Handle "executed" status (Kalshi sometimes returns this instead of "filled")
                # When status is "executed" but filled_count is 0, query Supabase for original order size
                if status == 'executed' and filled_count == 0:
                    logger.info(f"    Order status is 'executed' but filled_count=0 - querying Supabase for order size")
                    if self.supabase.client:
                        order_record = self.supabase.get_order(order_id)
                        if order_record:
                            filled_count = order_record['size']
                            total_count = order_record['size']
                            price = order_record['price']
                            logger.info(f"    Retrieved from database: {filled_count} contracts @ {price}¢")
                        else:
                            logger.error(f"    Could not find order in database: {order_id}")
                            continue

                # Update order status in database
                if self.supabase.client:
                    try:
                        if status == 'filled' or status == 'executed':
                            self.supabase.update_order_status(order_id, 'filled', filled_count)
                        elif filled_count > 0 and filled_count < total_count:
                            self.supabase.update_order_status(order_id, 'partially_filled', filled_count)
                    except Exception as db_error:
                        logger.error(f"    ✗ Failed to update dashboard for order {order_id}: {db_error}")

                # Create position for filled orders (handle both "filled" and "executed" status)
                if filled_count > 0 or status == 'executed':
                    # Check if we already created a position for this order
                    existing_position = next(
                        (p for p in game.positions if p.order_id == order_id),
                        None
                    )

                    if not existing_position:
                        position = Position(
                            market_ticker=game.market_ticker,
                            side=game.position_side,  # Use the side we determined at entry
                            entry_price=price,
                            size=filled_count,
                            entry_time=int(time.time()),
                            order_id=order_id
                        )
                        game.positions.append(position)
                        logger.info(f"  ✓ NEW FILL: {filled_count} contracts @ {price}¢ (Order: {order_id})")

                        # Log position to dashboard
                        if self.supabase.client:
                            try:
                                self.supabase.log_position_entry({
                                    'market_ticker': game.market_ticker,
                                    'entry_price': price,
                                    'size': filled_count,
                                    'entry_time': int(time.time()),
                                    'order_id': order_id
                                })
                            except Exception as db_error:
                                logger.error(f"    ✗ Failed to log position to dashboard: {db_error}")

                        # IMMEDIATELY place exit order at 55¢ (bracket strategy)
                        self._place_exit_order(game, position)

                # Track fully filled orders to remove from pending list
                # Handle both "filled" and "executed" status
                if status == 'filled' or status == 'executed':
                    filled_orders.append(order_id)

            except Exception as e:
                logger.error(f"  ✗ ERROR checking order status for {order_id}: {e}")
                import traceback
                logger.error(f"    Traceback: {traceback.format_exc()}")

        # Remove fully filled orders from pending list
        for order_id in filled_orders:
            if order_id in game.order_ids:
                game.order_ids.remove(order_id)
                logger.info(f"  Removed fully filled order from pending list: {order_id}")

    def check_exit_order_fills(self, game: GameMonitor) -> bool:
        """
        Check if ANY exit orders have filled (bracket strategy).
        If any exit fills, it means price reverted → exit ALL positions immediately.

        Returns True if we should exit all positions.
        """
        if not game.positions:
            return False

        if self.config['risk']['dry_run']:
            # In dry run, check if current price >= exit target
            current_price = self.get_current_price(game.market_ticker)
            if current_price is None:
                return False

            revert_bands = self.config['trading']['revert_bands']
            if revert_bands and current_price >= revert_bands[0]:
                logger.info(f"  🎯 [DRY RUN] Exit order would have filled @ {int(revert_bands[0] * 100)}¢")
                return True
            return False

        if not self.trading_client:
            return False

        # Check each position's exit order
        for position in game.positions:
            if not position.exit_order_id:
                continue

            try:
                status_response = self.trading_client.get_order_status(position.exit_order_id)

                # 404 means order executed/cancelled - assume filled
                if status_response is None:
                    logger.info(f"  🎯 EXIT ORDER FILLED! (Order: {position.exit_order_id})")
                    logger.info(f"     Price reverted → Exiting ALL positions")
                    return True

                if not status_response or 'order' not in status_response:
                    continue

                order_status = status_response.get('order', {})
                status = order_status.get('status', 'pending')
                filled_count = order_status.get('filled_count', 0)

                # If any exit order filled, trigger full exit
                if status == 'filled' or status == 'executed' or filled_count > 0:
                    logger.info(f"  🎯 EXIT ORDER FILLED! (Order: {position.exit_order_id})")
                    logger.info(f"     Price reverted → Exiting ALL positions")
                    return True

            except Exception as e:
                logger.error(f"  ✗ Error checking exit order {position.exit_order_id}: {e}")

        return False

    def _cancel_exit_orders(self, game: GameMonitor):
        """Cancel all pending exit orders (55¢ sells) for this game."""
        exit_orders = [p.exit_order_id for p in game.positions if p.exit_order_id]

        if not exit_orders:
            return

        if self.config['risk']['dry_run']:
            logger.info(f"[DRY RUN] Would cancel {len(exit_orders)} pending exit order(s)")
            for position in game.positions:
                position.exit_order_id = None
            return

        if not self.trading_client:
            return

        logger.info(f"Cancelling {len(exit_orders)} pending exit order(s)")
        cancelled_count = 0
        failed_count = 0

        for position in game.positions:
            if not position.exit_order_id:
                continue

            try:
                logger.info(f"  Cancelling exit order: {position.exit_order_id}")
                self.trading_client.cancel_order(position.exit_order_id)
                logger.info(f"  ✓ Exit order cancelled: {position.exit_order_id}")
                cancelled_count += 1
                position.exit_order_id = None
            except Exception as e:
                logger.error(f"  ✗ Failed to cancel exit order {position.exit_order_id}: {e}")
                failed_count += 1

        logger.info(f"Exit order cancellation complete: {cancelled_count} cancelled, {failed_count} failed")

    def cancel_pending_orders(self, game: GameMonitor):
        """Cancel all unfilled orders for this game."""
        if not game.order_ids:
            return

        if self.config['risk']['dry_run']:
            logger.info(f"[DRY RUN] Would cancel {len(game.order_ids)} pending order(s)")
            game.order_ids.clear()
            return

        if not self.trading_client:
            return

        logger.info(f"Cancelling {len(game.order_ids)} pending order(s) for {game.market_ticker}")
        cancelled_count = 0
        failed_count = 0

        for order_id in list(game.order_ids):  # Use list() to avoid modifying during iteration
            try:
                logger.info(f"  Cancelling order: {order_id}")
                self.trading_client.cancel_order(order_id)
                logger.info(f"  ✓ Order cancelled: {order_id}")
                cancelled_count += 1

                # Update dashboard
                if self.supabase.client:
                    try:
                        self.supabase.update_order_status(order_id, 'cancelled', 0)
                    except Exception as db_error:
                        logger.error(f"    ✗ Failed to update dashboard for cancelled order: {db_error}")

            except Exception as e:
                logger.error(f"  ✗ Failed to cancel order {order_id}: {e}")
                failed_count += 1

        # Clear the order IDs list
        game.order_ids.clear()
        logger.info(f"Order cancellation complete: {cancelled_count} cancelled, {failed_count} failed")

    def check_exit_signal(self, game: GameMonitor) -> bool:
        """Check if we should exit position."""
        if not game.positions:
            return False

        now = int(datetime.utcnow().timestamp())

        if now >= game.halftime_ts:
            logger.info(f"Halftime timeout reached for {game.market_title}")
            return True

        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            return False

        revert_bands = self.config['trading']['revert_bands']
        for band in revert_bands:
            if current_price >= band:
                logger.info(f"Price reverted to {current_price:.0%} (band: {band:.0%})")
                return True

        return False

    def exit_position(self, game: GameMonitor):
        """Exit all positions for this game."""
        logger.info("=" * 80)
        logger.info(f"EXIT SIGNAL: {game.market_title}")
        logger.info("=" * 80)

        # First, cancel any unfilled BUY orders
        if game.order_ids:
            logger.info("Cancelling unfilled buy orders before exiting positions")
            self.cancel_pending_orders(game)

        # Cancel any pending EXIT orders (55¢ sells)
        if game.positions:
            self._cancel_exit_orders(game)

        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            logger.error("Could not get current price for exit")
            return

        current_price_cents = int(current_price * 100)

        total_pnl = 0.0
        total_contracts = 0

        for position in game.positions:
            pnl_per_contract = (current_price_cents - position.entry_price) / 100.0
            pnl_total = pnl_per_contract * position.size

            logger.info(
                f"  Position: {position.size} @ {position.entry_price}¢ → {current_price_cents}¢ "
                f"= ${pnl_total:+,.2f}"
            )

            total_pnl += pnl_total
            total_contracts += position.size

            if not self.config['risk']['dry_run']:
                try:
                    order = self.trading_client.place_order(
                        market_ticker=game.market_ticker,
                        side=position.side,  # Sell the same side we bought
                        action="sell",
                        count=position.size,
                        price=current_price_cents,
                        order_type="limit"
                    )
                    logger.info(f"  ✓ Sell order placed: {order.order_id}")
                except Exception as e:
                    logger.error(f"  ✗ Error placing sell order: {e}")

        old_bankroll = self.bankroll
        self.bankroll += total_pnl

        logger.info("")
        logger.info(f"Total P&L: ${total_pnl:+,.2f}")
        logger.info(f"Bankroll: ${old_bankroll:,.2f} → ${self.bankroll:,.2f}")
        logger.info("")

        # Log position exit to dashboard
        if self.supabase.client:
            self.supabase.log_position_exit(
                market_ticker=game.market_ticker,
                exit_price=current_price_cents,
                exit_time=int(time.time()),
                pnl=total_pnl
            )

            # Log bankroll change
            self.supabase.log_bankroll_change(
                timestamp=int(time.time()),
                new_amount=self.bankroll,
                change=total_pnl,
                description=f"Exited {game.market_title}"
            )

            # Update game status to completed
            self.supabase.update_game_status(game.market_ticker, 'completed')

        game.positions.clear()

    def run(self):
        """Main trading loop."""
        logger.info("Starting trading bot...")
        logger.info("")

        try:
            while True:
                now = int(datetime.utcnow().timestamp())

                if len(self.active_games) == 0 or now % 60 == 0:  # Rediscover every minute
                    upcoming_games = self.discover_upcoming_games()

                    for game in upcoming_games:
                        if game.market_ticker not in self.active_games:
                            self.active_games[game.market_ticker] = game
                            kickoff_dt = datetime.fromtimestamp(game.kickoff_ts)
                            logger.info(f"Monitoring: {game.market_title} @ {kickoff_dt.strftime('%Y-%m-%d %H:%M UTC')}")

                            # Fetch current odds for dashboard
                            current_price = self.get_current_price(game.market_ticker)
                            if current_price:
                                game.pregame_prob = current_price
                                logger.info(f"  Current odds: {current_price:.0%}")

                            # Log game to dashboard
                            if self.supabase.client:
                                self.supabase.log_game({
                                    'market_ticker': game.market_ticker,
                                    'event_ticker': game.event_ticker,
                                    'market_title': game.market_title,
                                    'yes_subtitle': game.yes_subtitle,
                                    'kickoff_ts': game.kickoff_ts,
                                    'halftime_ts': game.halftime_ts,
                                    'pregame_prob': game.pregame_prob,
                                    'status': 'monitoring'
                                })

                games_to_remove = []

                for market_ticker, game in list(self.active_games.items()):
                    # Log game status periodically (every minute)
                    if now % 60 == 0:
                        pending_count = len(game.order_ids) if game.order_ids else 0
                        position_count = len(game.positions) if game.positions else 0
                        logger.info(f"[{game.market_ticker}] Status: triggered={game.triggered}, pending_orders={pending_count}, positions={position_count}")

                    if now > game.halftime_ts:
                        logger.info(f"Halftime reached for {game.market_ticker} - cleaning up")
                        # Cancel any unfilled orders
                        if game.order_ids:
                            self.cancel_pending_orders(game)
                        # Exit any filled positions
                        if game.positions:
                            self.exit_position(game)
                        # Now mark for removal
                        games_to_remove.append(market_ticker)
                        continue

                    # Check and capture checkpoints (6h, 3h, 30m before kickoff)
                    self.check_and_capture_checkpoint(game, now)

                    # Log price tick ONLY for in-game data (after kickoff)
                    # Pregame polling is sparse (only 3 checkpoint polls)
                    if self.supabase.client and now >= game.kickoff_ts:
                        try:
                            market = self.public_client.get_market(game.market_ticker)
                            if market:
                                yes_ask = market.yes_ask if market.yes_ask is not None else 0
                                no_ask = market.no_ask if market.no_ask is not None else 0
                                favorite_price = max(yes_ask, no_ask) / 100.0 if max(yes_ask, no_ask) > 0 else None

                                if favorite_price:
                                    self.supabase.log_price_tick(
                                        market_ticker=game.market_ticker,
                                        timestamp=now,
                                        favorite_price=favorite_price,
                                        yes_ask=yes_ask,
                                        no_ask=no_ask
                                    )
                        except Exception as e:
                            logger.debug(f"Error logging tick for {game.market_ticker}: {e}")

                    # Check if any pending orders have filled
                    if game.triggered and game.order_ids:
                        logger.info(f"→ Monitoring orders for {game.market_ticker}")
                        self.check_order_fills(game)

                    # Check if any exit orders (55¢ sells) have filled
                    # If ANY exit fills, price reverted → exit ALL positions immediately
                    if game.positions and self.check_exit_order_fills(game):
                        logger.info("🎯 Exit order filled → Triggering full exit")
                        self.exit_position(game)
                        games_to_remove.append(market_ticker)
                        continue

                    if not game.triggered and self.check_entry_signal(game):
                        active_positions = sum(1 for g in self.active_games.values() if g.positions)
                        max_concurrent = self.config['risk']['max_concurrent_games']

                        if active_positions < max_concurrent:
                            self.enter_position(game)
                        else:
                            logger.warning(f"Max concurrent games ({max_concurrent}) reached, skipping entry")

                    if game.positions and self.check_exit_signal(game):
                        self.exit_position(game)
                        games_to_remove.append(market_ticker)

                for market_ticker in games_to_remove:
                    del self.active_games[market_ticker]

                time.sleep(self.config['monitoring']['poll_interval'])

        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 80)
            logger.info("Bot stopped by user")
            logger.info("=" * 80)
            logger.info(f"Final bankroll: ${self.bankroll:,.2f}")

        finally:
            if self.trading_client:
                self.trading_client.close()
            self.public_client.close()


def main():
    trader = LiveTrader()
    trader.run()


if __name__ == '__main__':
    main()
