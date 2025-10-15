"""
Tests for trigger detection logic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from data_models import Candle, EventInfo, MarketInfo, Trade
from fetch import GameData, detect_trigger_time


class TestTriggerLogic:
    """Test trigger detection for price drops."""

    def test_trigger_detected_simple(self):
        """Test basic trigger detection when price drops below 50%."""
        event = EventInfo(
            event_ticker="TEST-001",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-001", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        halftime_ts = kickoff_ts + 1800

        # Candles: start high, then drop below 50%
        candles = [
            Candle(start_ts=kickoff_ts + 60, open_cents=65, high_cents=65, low_cents=60, close_cents=60, volume=100),
            Candle(start_ts=kickoff_ts + 120, open_cents=60, high_cents=60, low_cents=55, close_cents=55, volume=100),
            Candle(start_ts=kickoff_ts + 180, open_cents=55, high_cents=55, low_cents=45, close_cents=48, volume=100),  # Trigger here
            Candle(start_ts=kickoff_ts + 240, open_cents=48, high_cents=50, low_cents=45, close_cents=46, volume=100),
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        trigger_ts = detect_trigger_time(game_data, kickoff_ts, halftime_ts, trigger_threshold=0.50)

        assert trigger_ts == kickoff_ts + 180

    def test_no_trigger_stays_above_threshold(self):
        """Test no trigger when price stays above threshold."""
        event = EventInfo(
            event_ticker="TEST-002",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-002", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        halftime_ts = kickoff_ts + 1800

        # All candles stay above 50%
        candles = [
            Candle(start_ts=kickoff_ts + 60, open_cents=65, high_cents=65, low_cents=55, close_cents=60, volume=100),
            Candle(start_ts=kickoff_ts + 120, open_cents=60, high_cents=62, low_cents=58, close_cents=60, volume=100),
            Candle(start_ts=kickoff_ts + 180, open_cents=60, high_cents=63, low_cents=55, close_cents=58, volume=100),
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        trigger_ts = detect_trigger_time(game_data, kickoff_ts, halftime_ts, trigger_threshold=0.50)

        assert trigger_ts is None

    def test_trigger_before_kickoff_ignored(self):
        """Test that triggers before kickoff are ignored."""
        event = EventInfo(
            event_ticker="TEST-003",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-003", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        halftime_ts = kickoff_ts + 1800

        # Candle before kickoff drops below 50%
        candles = [
            Candle(start_ts=kickoff_ts - 60, open_cents=65, high_cents=65, low_cents=45, close_cents=48, volume=100),  # Before kickoff
            Candle(start_ts=kickoff_ts + 60, open_cents=55, high_cents=60, low_cents=55, close_cents=58, volume=100),  # After kickoff, above 50%
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        trigger_ts = detect_trigger_time(game_data, kickoff_ts, halftime_ts, trigger_threshold=0.50)

        assert trigger_ts is None

    def test_trigger_after_halftime_ignored(self):
        """Test that triggers after halftime are ignored."""
        event = EventInfo(
            event_ticker="TEST-004",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-004", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        halftime_ts = kickoff_ts + 1800

        candles = [
            Candle(start_ts=kickoff_ts + 60, open_cents=65, high_cents=65, low_cents=60, close_cents=60, volume=100),
            Candle(start_ts=halftime_ts + 60, open_cents=60, high_cents=60, low_cents=40, close_cents=45, volume=100),  # After halftime
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        trigger_ts = detect_trigger_time(game_data, kickoff_ts, halftime_ts, trigger_threshold=0.50)

        assert trigger_ts is None

    def test_first_trigger_only(self):
        """Test that only the first trigger is returned (no pyramiding)."""
        event = EventInfo(
            event_ticker="TEST-005",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-005", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        halftime_ts = kickoff_ts + 1800

        candles = [
            Candle(start_ts=kickoff_ts + 60, open_cents=60, high_cents=60, low_cents=48, close_cents=48, volume=100),  # First trigger
            Candle(start_ts=kickoff_ts + 120, open_cents=48, high_cents=52, low_cents=46, close_cents=50, volume=100),  # Recovery
            Candle(start_ts=kickoff_ts + 180, open_cents=50, high_cents=50, low_cents=42, close_cents=44, volume=100),  # Second drop
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        trigger_ts = detect_trigger_time(game_data, kickoff_ts, halftime_ts, trigger_threshold=0.50)

        # Should return first trigger only
        assert trigger_ts == kickoff_ts + 60
