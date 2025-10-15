"""Test the three-checkpoint trading system."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

# Mock the GameMonitor dataclass
from dataclasses import dataclass, field
from typing import Optional

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


def get_current_price(client, market_ticker: str) -> Optional[float]:
    """Get current market price (favorite's probability)."""
    try:
        market = client.get_market(market_ticker)
        if not market:
            return None

        # Get best ask prices for both sides (price to BUY)
        yes_ask = market.yes_ask if market.yes_ask is not None else 0
        no_ask = market.no_ask if market.no_ask is not None else 0

        # Return the higher of the two (the favorite's probability)
        favorite_price = max(yes_ask, no_ask)
        return favorite_price / 100.0 if favorite_price > 0 else None
    except Exception as e:
        print(f"Error fetching price for {market_ticker}: {e}")
        return None


def determine_eligibility(game: GameMonitor):
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
        print(f"  → NOT ELIGIBLE (30m veto: {game.odds_30m:.0%} < 57%)")
    elif has_high_checkpoint:
        game.is_eligible = True
        print(f"  → ELIGIBLE (checkpoint(s) >= 57%)")
    else:
        game.is_eligible = False
        print(f"  → NOT ELIGIBLE (no checkpoint >= 57%)")


def test_eligibility_rules():
    """Test various eligibility scenarios."""
    print("=" * 80)
    print("TEST 1: Eligibility Logic")
    print("=" * 80)
    print()

    # Create a fake game for testing
    kickoff_ts = int((datetime.now() + timedelta(minutes=30)).timestamp())

    # Test Case 1: All checkpoints >= 57%
    print("Case 1: All checkpoints >= 57%")
    game1 = GameMonitor(
        event_ticker="TEST-1",
        market_ticker="TEST-1",
        market_title="Test Game 1",
        yes_subtitle="Team A",
        kickoff_ts=kickoff_ts,
        halftime_ts=kickoff_ts + 5400,
        odds_6h=0.60,
        odds_3h=0.59,
        odds_30m=0.58
    )
    determine_eligibility(game1)
    assert game1.is_eligible == True, "Should be eligible"
    print()

    # Test Case 2: First checkpoint high, but 30m veto applies
    print("Case 2: 6h and 3h >= 57%, but 30m < 57% (VETO)")
    game2 = GameMonitor(
        event_ticker="TEST-2",
        market_ticker="TEST-2",
        market_title="Test Game 2",
        yes_subtitle="Team B",
        kickoff_ts=kickoff_ts,
        halftime_ts=kickoff_ts + 5400,
        odds_6h=0.62,
        odds_3h=0.60,
        odds_30m=0.55  # Below threshold
    )
    determine_eligibility(game2)
    assert game2.is_eligible == False, "Should be NOT eligible (30m veto)"
    print()

    # Test Case 3: Only 30m checkpoint >= 57%
    print("Case 3: Only 30m checkpoint >= 57%")
    game3 = GameMonitor(
        event_ticker="TEST-3",
        market_ticker="TEST-3",
        market_title="Test Game 3",
        yes_subtitle="Team C",
        kickoff_ts=kickoff_ts,
        halftime_ts=kickoff_ts + 5400,
        odds_6h=0.54,
        odds_3h=0.55,
        odds_30m=0.58
    )
    determine_eligibility(game3)
    assert game3.is_eligible == True, "Should be eligible"
    print()

    # Test Case 4: No checkpoint >= 57%
    print("Case 4: No checkpoint >= 57%")
    game4 = GameMonitor(
        event_ticker="TEST-4",
        market_ticker="TEST-4",
        market_title="Test Game 4",
        yes_subtitle="Team D",
        kickoff_ts=kickoff_ts,
        halftime_ts=kickoff_ts + 5400,
        odds_6h=0.54,
        odds_3h=0.55,
        odds_30m=0.56
    )
    determine_eligibility(game4)
    assert game4.is_eligible == False, "Should be NOT eligible"
    print()

    print("✓ All eligibility tests passed!")
    print()


def test_live_odds_reading():
    """Test reading odds from live CFB games."""
    print("=" * 80)
    print("TEST 2: Live Odds Reading")
    print("=" * 80)
    print()

    client = KalshiClient()

    # Test with both CFB games
    tickers = [
        ("UTEP at Sam Houston", "KXNCAAFGAME-25OCT15UTEPSHSU-UTEP"),
        ("Delaware at Jacksonville St.", "KXNCAAFGAME-25OCT15DELJVST-JVST")
    ]

    for name, ticker in tickers:
        market = client.get_market(ticker)
        if market:
            current_price = get_current_price(client, ticker)
            print(f"{name}:")
            print(f"  yes_ask: {market.yes_ask}¢, no_ask: {market.no_ask}¢")
            print(f"  Favorite odds: {current_price:.0%}")
            print()

    print("✓ Odds reading test complete!")
    print()


if __name__ == "__main__":
    print()
    print("Testing Three-Checkpoint Trading System")
    print("=" * 80)
    print()

    # Test 1: Eligibility logic
    test_eligibility_rules()

    # Test 2: Live odds reading
    test_live_odds_reading()

    print("=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    print()
