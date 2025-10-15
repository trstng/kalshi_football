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

    triggered: bool = False
    positions: list = field(default_factory=list)


@dataclass
class Position:
    """Represents an open position."""
    market_ticker: str
    entry_price: int
    size: int
    entry_time: int
    order_id: Optional[str] = None


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

        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            return False

        trigger_threshold = self.config['trading']['trigger_threshold']
        if current_price < trigger_threshold:
            return True

        return False

    def enter_position(self, game: GameMonitor):
        """Enter position with scaling strategy."""
        logger.info("=" * 80)
        logger.info(f"ENTRY SIGNAL: {game.market_title} ({game.yes_subtitle})")
        logger.info("=" * 80)

        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            logger.error("Could not get current price, skipping")
            return

        current_price_cents = int(current_price * 100)

        logger.info(f"Pregame: {game.pregame_prob:.0%} → Current: {current_price:.0%}")

        scaling_levels = self.config['trading']['scaling_levels']
        levels_to_hit = [
            level for level in scaling_levels
            if current_price_cents <= level['trigger']
        ]

        if not levels_to_hit:
            logger.info("No scaling levels triggered, skipping")
            return

        logger.info(f"Scaling levels hit: {len(levels_to_hit)}")

        positions = self.calculate_position_sizes(
            self.bankroll,
            self.config['trading']['kelly_fraction'],
            self.config['trading']['max_exposure_pct'],
            current_price_cents,
            levels_to_hit
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
                position = Position(
                    market_ticker=game.market_ticker,
                    entry_price=price_cents,
                    size=size,
                    entry_time=int(time.time()),
                    order_id=f"dry_run_{len(game.positions)}"
                )
                game.positions.append(position)
            else:
                try:
                    order = self.trading_client.place_order(
                        market_ticker=game.market_ticker,
                        side="yes",
                        action="buy",
                        count=size,
                        price=price_cents,
                        order_type="limit"
                    )
                    position = Position(
                        market_ticker=game.market_ticker,
                        entry_price=price_cents,
                        size=size,
                        entry_time=int(time.time()),
                        order_id=order.order_id
                    )
                    game.positions.append(position)
                    logger.info(f"  ✓ Order placed: {order.order_id}")
                except Exception as e:
                    logger.error(f"  ✗ Error placing order: {e}")

            # Log position to dashboard
            if self.supabase.client:
                self.supabase.log_position_entry({
                    'market_ticker': game.market_ticker,
                    'entry_price': price_cents,
                    'size': size,
                    'entry_time': int(time.time()),
                    'order_id': position.order_id
                })

        game.triggered = True
        game.highest_entry = max(p[0] for p in positions)
        self.total_exposure += total_capital

        # Update game status to triggered
        if self.supabase.client:
            self.supabase.update_game_status(game.market_ticker, 'triggered', game.pregame_prob)

        logger.info(f"Position entered. Total exposure: ${self.total_exposure:,.2f}")
        logger.info("")

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
                        side="yes",
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
                    if now > game.halftime_ts:
                        games_to_remove.append(market_ticker)
                        continue

                    # Check and capture checkpoints (6h, 3h, 30m before kickoff)
                    self.check_and_capture_checkpoint(game, now)

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
