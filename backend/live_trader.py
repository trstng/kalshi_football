"""
Live Trading Bot for Kalshi Mean Reversion Strategy.

Monitors NFL and CFB games, enters when pregame favorite drops below 50%,
scales into position, and exits at revert bands or halftime timeout.
"""
import logging
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient
from kalshi_nfl_research.trading_client import KalshiTradingClient


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
    pregame_prob: Optional[float] = None
    triggered: bool = False
    positions: list = field(default_factory=list)
    highest_entry: Optional[int] = None  # Track highest price we entered at


@dataclass
class Position:
    """Represents an open position."""
    market_ticker: str
    entry_price: int  # cents
    size: int  # number of contracts
    entry_time: int  # unix timestamp
    buy_order_id: Optional[str] = None
    buy_filled: bool = False
    sell_order_id: Optional[str] = None
    sell_filled: bool = False


class LiveTrader:
    """Main live trading bot."""

    def __init__(self, config_path: str = "live_trading_config.yaml"):
        """Initialize the live trader."""
        logger.info("=" * 80)
        logger.info("KALSHI LIVE TRADING BOT")
        logger.info("=" * 80)
        logger.info("")

        # Load configuration
        logger.info(f"Loading config from: {config_path}")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize clients
        logger.info("Initializing API clients...")
        self.public_client = KalshiClient()

        if not self.config['risk']['dry_run']:
            # Real trading - need credentials
            creds = self.config['api_credentials']
            self.trading_client = KalshiTradingClient(
                email=creds.get('email'),
                password=creds.get('password'),
                api_key=creds.get('api_key'),
                api_secret=creds.get('api_secret'),
            )
            logger.info("✓ Trading client initialized (LIVE MODE)")
        else:
            self.trading_client = None
            logger.warning("⚠️  DRY RUN MODE - No real orders will be placed")

        # Trading state
        self.bankroll = self.config['trading']['bankroll']
        self.active_games: dict[str, GameMonitor] = {}
        self.total_exposure = 0.0

        logger.info(f"Starting bankroll: ${self.bankroll:,.2f}")
        logger.info("")

    def discover_upcoming_games(self) -> list[GameMonitor]:
        """Discover games starting in the next few hours."""
        logger.info("Discovering upcoming games...")

        now = int(datetime.utcnow().timestamp())
        lookahead = now + (self.config['monitoring']['lookahead_hours'] * 3600)

        games = []

        # Check NFL
        if self.config['markets']['nfl']['enabled']:
            nfl_series = self.config['markets']['nfl']['series_ticker']
            logger.info(f"  Checking {nfl_series}...")

            nfl_events = self.public_client.get_events(series_ticker=nfl_series)

            for event in nfl_events:
                strike_date = event.get('strike_date')
                if not strike_date:
                    continue

                # Only games starting soon
                if now < strike_date < lookahead:
                    # Get markets for this event
                    markets = self.public_client.get_markets(event_ticker=event['event_ticker'])

                    for market in markets:
                        kickoff_ts = strike_date
                        halftime_ts = kickoff_ts + 5400  # 90 minutes

                        game = GameMonitor(
                            event_ticker=event['event_ticker'],
                            market_ticker=market.ticker,
                            market_title=market.title,
                            yes_subtitle=market.yes_sub_title or "",
                            kickoff_ts=kickoff_ts,
                            halftime_ts=halftime_ts,
                        )
                        games.append(game)

        # Check CFB
        if self.config['markets']['cfb']['enabled']:
            cfb_series = self.config['markets']['cfb']['series_ticker']
            logger.info(f"  Checking {cfb_series}...")

            cfb_events = self.public_client.get_events(series_ticker=cfb_series)

            for event in cfb_events:
                strike_date = event.get('strike_date')
                if not strike_date:
                    continue

                # Only games starting soon
                if now < strike_date < lookahead:
                    # Get markets for this event
                    markets = self.public_client.get_markets(event_ticker=event['event_ticker'])

                    for market in markets:
                        kickoff_ts = strike_date
                        halftime_ts = kickoff_ts + 5400  # 90 minutes

                        game = GameMonitor(
                            event_ticker=event['event_ticker'],
                            market_ticker=market.ticker,
                            market_title=market.title,
                            yes_subtitle=market.yes_sub_title or "",
                            kickoff_ts=kickoff_ts,
                            halftime_ts=halftime_ts,
                        )
                        games.append(game)

        logger.info(f"Found {len(games)} upcoming games")
        return games

    def get_current_price(self, market_ticker: str) -> Optional[float]:
        """Get current market price from orderbook."""
        try:
            orderbook = self.public_client.get_orderbook(market_ticker)
            if not orderbook or not orderbook.yes_ask:
                return None

            # Use ask price (what we'd pay to buy)
            return orderbook.yes_ask / 100.0

        except Exception as e:
            logger.error(f"Error fetching price for {market_ticker}: {e}")
            return None

    def check_order_fills(self, game: GameMonitor) -> list[Position]:
        """
        Check which buy orders have been filled.

        Returns:
            List of positions that were just filled
        """
        newly_filled = []

        for position in game.positions:
            # Skip if already checked as filled
            if position.buy_filled:
                continue

            # Skip if no order ID (shouldn't happen)
            if not position.buy_order_id:
                continue

            # Check order status
            if self.config['risk']['dry_run']:
                # In dry run, assume orders fill immediately
                position.buy_filled = True
                newly_filled.append(position)
            else:
                try:
                    status = self.trading_client.get_order_status(position.buy_order_id)
                    if status.get('status') == 'filled':
                        position.buy_filled = True
                        newly_filled.append(position)
                        logger.info(f"✓ Buy order filled: {position.size} @ {position.entry_price}¢")
                except Exception as e:
                    logger.error(f"Error checking order status for {position.buy_order_id}: {e}")

        return newly_filled

    def place_exit_orders(self, position: Position):
        """
        Place limit sell orders at target exit prices.
        This implements a bracket/take-profit strategy.
        """
        # Get the first (lowest) revert band as our exit target
        revert_bands = self.config['trading']['revert_bands']
        if not revert_bands:
            logger.warning("No revert bands configured, skipping exit order placement")
            return

        # Use the first revert band (typically 0.55)
        exit_price = revert_bands[0]
        exit_price_cents = int(exit_price * 100)

        logger.info(f"Placing exit order: {position.size} @ {exit_price_cents}¢")

        if self.config['risk']['dry_run']:
            logger.info("  [DRY RUN] Would place exit order here")
            position.sell_order_id = f"dry_run_sell_{position.buy_order_id}"
        else:
            try:
                order = self.trading_client.place_order(
                    market_ticker=position.market_ticker,
                    side="yes",
                    action="sell",
                    count=position.size,
                    price=exit_price_cents,
                    order_type="limit"
                )
                position.sell_order_id = order.order_id
                logger.info(f"  ✓ Exit order placed: {order.order_id}")

            except Exception as e:
                logger.error(f"  ✗ Error placing exit order: {e}")

    def calculate_position_sizes(
        self,
        bankroll: float,
        kelly_frac: float,
        max_exposure: float,
        current_price_cents: int,
        levels_to_hit: list[dict],
    ) -> list[tuple[int, int]]:
        """
        Calculate position sizes with Kelly criterion and exposure limits.

        Returns:
            List of (price_cents, size) tuples
        """
        # Calculate "ideal" Kelly sizes
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

        # Check if we exceed max exposure
        max_capital_allowed = bankroll * max_exposure

        if total_ideal_capital <= max_capital_allowed:
            # Use ideal sizes
            return [(p['trigger'], p['ideal_size']) for p in ideal_positions]
        else:
            # Scale down proportionally
            scale_factor = max_capital_allowed / total_ideal_capital

            scaled_positions = []
            for pos in ideal_positions:
                scaled_size = max(1, int(pos['ideal_size'] * scale_factor))
                scaled_positions.append((pos['trigger'], scaled_size))

            return scaled_positions

    def check_entry_signal(self, game: GameMonitor) -> bool:
        """Check if we should enter a position for this game."""
        now = int(datetime.utcnow().timestamp())

        # Don't trade after kickoff
        if now >= game.kickoff_ts:
            return False

        # Get current price
        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            return False

        # First time seeing this game - check if it's a pregame favorite
        if game.pregame_prob is None:
            # Need to determine if this was a pregame favorite
            # For now, we'll track from first observation
            # In production, you'd want to check historical odds
            game.pregame_prob = current_price

        # Check if pregame favorite
        favorite_threshold = self.config['trading']['pregame_favorite_threshold']
        if game.pregame_prob < favorite_threshold:
            return False  # Not a strong enough favorite

        # Check if price dropped below trigger
        trigger_threshold = self.config['trading']['trigger_threshold']
        if current_price < trigger_threshold:
            return True

        return False

    def enter_position(self, game: GameMonitor):
        """Enter position with scaling strategy."""
        logger.info("=" * 80)
        logger.info(f"ENTRY SIGNAL: {game.market_title} ({game.yes_subtitle})")
        logger.info("=" * 80)

        # Get current price
        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            logger.error("Could not get current price, skipping")
            return

        current_price_cents = int(current_price * 100)

        logger.info(f"Pregame: {game.pregame_prob:.0%} → Current: {current_price:.0%}")

        # Determine which scaling levels to hit
        scaling_levels = self.config['trading']['scaling_levels']
        levels_to_hit = [
            level for level in scaling_levels
            if current_price_cents <= level['trigger']
        ]

        if not levels_to_hit:
            logger.info("No scaling levels triggered, skipping")
            return

        logger.info(f"Scaling levels hit: {len(levels_to_hit)}")

        # Calculate position sizes
        positions = self.calculate_position_sizes(
            self.bankroll,
            self.config['trading']['kelly_fraction'],
            self.config['trading']['max_exposure_pct'],
            current_price_cents,
            levels_to_hit
        )

        # Calculate total exposure
        total_capital = sum(price * size / 100.0 for price, size in positions)
        logger.info(f"Total capital at risk: ${total_capital:,.2f}")

        # Safety check
        if total_capital > self.config['safety']['max_total_exposure']:
            logger.warning(f"⚠️  Total exposure ${total_capital:,.2f} exceeds limit, skipping")
            return

        # Place orders
        for price_cents, size in positions:
            logger.info(f"  Level: {size:4d} contracts @ {price_cents}¢ = ${price_cents * size / 100:.2f}")

            if self.config['risk']['dry_run']:
                logger.info("  [DRY RUN] Would place order here")
                # Simulate position
                position = Position(
                    market_ticker=game.market_ticker,
                    entry_price=price_cents,
                    size=size,
                    entry_time=int(time.time()),
                    buy_order_id=f"dry_run_{len(game.positions)}"
                )
                game.positions.append(position)

            else:
                # Real order placement
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
                        buy_order_id=order.order_id
                    )
                    game.positions.append(position)

                    logger.info(f"  ✓ Order placed: {order.order_id}")

                except Exception as e:
                    logger.error(f"  ✗ Error placing order: {e}")

        # Update tracking
        game.triggered = True
        game.highest_entry = max(p[0] for p in positions)
        self.total_exposure += total_capital

        logger.info(f"Position entered. Total exposure: ${self.total_exposure:,.2f}")
        logger.info("")

    def check_exit_signal(self, game: GameMonitor) -> bool:
        """Check if we should exit position (only at halftime or when ALL positions sold)."""
        if not game.positions:
            return False

        now = int(datetime.utcnow().timestamp())

        # Exit at halftime timeout (need to cancel pending sells and exit at market)
        if now >= game.halftime_ts:
            logger.info(f"Halftime timeout reached for {game.market_title}")
            return True

        # Update sell_filled status for all positions (but don't trigger exit yet)
        # Individual limit orders will exit automatically - we only exit at halftime
        for position in game.positions:
            if not position.sell_order_id:
                continue

            if position.sell_filled:
                continue

            # Check sell order status
            if self.config['risk']['dry_run']:
                # In dry run, check if current price hit the target
                current_price = self.get_current_price(game.market_ticker)
                if current_price is None:
                    continue

                revert_bands = self.config['trading']['revert_bands']
                if revert_bands and current_price >= revert_bands[0]:
                    position.sell_filled = True
                    logger.info(f"✓ [DRY RUN] Sell order would have filled @ {int(revert_bands[0] * 100)}¢")
                    # Don't return True here - let limit orders handle exits automatically
            else:
                try:
                    status = self.trading_client.get_order_status(position.sell_order_id)
                    if status.get('status') == 'filled':
                        position.sell_filled = True
                        logger.info(f"✓ Sell order filled: {position.size} contracts")
                        # Don't return True here - let limit orders handle exits automatically
                except Exception as e:
                    logger.error(f"Error checking sell order status for {position.sell_order_id}: {e}")

        # Only trigger exit_position() at halftime, not when individual limits fill
        return False

    def exit_position(self, game: GameMonitor):
        """Exit all positions for this game."""
        logger.info("=" * 80)
        logger.info(f"EXIT SIGNAL: {game.market_title}")
        logger.info("=" * 80)

        now = int(datetime.utcnow().timestamp())
        is_halftime_timeout = now >= game.halftime_ts

        if is_halftime_timeout:
            logger.info("HALFTIME TIMEOUT - Cancelling pending sell orders and exiting at market")

            # Cancel any pending sell orders
            for position in game.positions:
                if position.sell_order_id and not position.sell_filled:
                    if not self.config['risk']['dry_run']:
                        try:
                            self.trading_client.cancel_order(position.sell_order_id)
                            logger.info(f"  ✓ Cancelled sell order: {position.sell_order_id}")
                        except Exception as e:
                            logger.error(f"  ✗ Error cancelling order: {e}")

        # Get current price for P&L calculation
        current_price = self.get_current_price(game.market_ticker)
        if current_price is None:
            logger.error("Could not get current price for exit")
            return

        current_price_cents = int(current_price * 100)

        total_pnl = 0.0
        total_contracts = 0

        for position in game.positions:
            # Calculate P&L
            if position.sell_filled:
                # Sell order already filled at limit price
                revert_bands = self.config['trading']['revert_bands']
                exit_price_cents = int(revert_bands[0] * 100) if revert_bands else current_price_cents
                pnl_per_contract = (exit_price_cents - position.entry_price) / 100.0
                exit_reason = f"limit @ {exit_price_cents}¢"
            else:
                # Exiting at current market price (halftime timeout)
                pnl_per_contract = (current_price_cents - position.entry_price) / 100.0
                exit_reason = f"market @ {current_price_cents}¢"

            pnl_total = pnl_per_contract * position.size

            logger.info(
                f"  Position: {position.size} @ {position.entry_price}¢ → {exit_reason} "
                f"= ${pnl_total:+,.2f}"
            )

            total_pnl += pnl_total
            total_contracts += position.size

            # If not already filled and not dry run, place market sell order
            # IMPORTANT: Only place sell order if there's no pending sell order already!
            if not position.sell_filled and not position.sell_order_id and not self.config['risk']['dry_run']:
                try:
                    order = self.trading_client.place_order(
                        market_ticker=game.market_ticker,
                        side="yes",
                        action="sell",
                        count=position.size,
                        price=current_price_cents,
                        order_type="limit"
                    )
                    logger.info(f"  ✓ Market sell order placed: {order.order_id}")

                except Exception as e:
                    logger.error(f"  ✗ Error placing sell order: {e}")

        # Update bankroll
        old_bankroll = self.bankroll
        self.bankroll += total_pnl

        logger.info("")
        logger.info(f"Total P&L: ${total_pnl:+,.2f}")
        logger.info(f"Bankroll: ${old_bankroll:,.2f} → ${self.bankroll:,.2f}")
        logger.info("")

        # Clear positions
        game.positions.clear()

    def run(self):
        """Main trading loop."""
        logger.info("Starting trading bot...")
        logger.info("")

        try:
            while True:
                now = int(datetime.utcnow().timestamp())

                # Discover new games periodically
                if len(self.active_games) == 0:
                    upcoming_games = self.discover_upcoming_games()

                    for game in upcoming_games:
                        if game.market_ticker not in self.active_games:
                            self.active_games[game.market_ticker] = game
                            logger.info(f"Monitoring: {game.market_title} @ {datetime.fromtimestamp(game.kickoff_ts).strftime('%Y-%m-%d %H:%M UTC')}")

                # Monitor active games
                games_to_remove = []

                for market_ticker, game in list(self.active_games.items()):
                    # Remove games past halftime
                    if now > game.halftime_ts:
                        games_to_remove.append(market_ticker)
                        continue

                    # Check for entry signal
                    if not game.triggered and self.check_entry_signal(game):
                        # Check concurrent game limit
                        active_positions = sum(1 for g in self.active_games.values() if g.positions)
                        max_concurrent = self.config['risk']['max_concurrent_games']

                        if active_positions < max_concurrent:
                            self.enter_position(game)
                        else:
                            logger.warning(f"Max concurrent games ({max_concurrent}) reached, skipping entry")

                    # Check for buy order fills and place exit orders
                    if game.positions:
                        newly_filled = self.check_order_fills(game)
                        for position in newly_filled:
                            # Place exit order for this filled position
                            self.place_exit_orders(position)

                    # Check for exit signal
                    if game.positions and self.check_exit_signal(game):
                        self.exit_position(game)
                        games_to_remove.append(market_ticker)

                # Clean up finished games
                for market_ticker in games_to_remove:
                    del self.active_games[market_ticker]

                # Sleep before next poll
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
    """Entry point."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Initialize and run trader
    trader = LiveTrader()
    trader.run()


if __name__ == '__main__':
    main()
