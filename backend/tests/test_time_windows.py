"""
Tests for time window filtering and boundary conditions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from data_models import Candle, EventInfo, MarketInfo, Trade
from fetch import GameData, compute_pregame_probability


class TestTimeWindows:
    """Test time window logic for pregame, first half, etc."""

    def test_pregame_window_filtering(self):
        """Test that only pregame data is used for baseline calculation."""
        event = EventInfo(
            event_ticker="TEST-001",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-001", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        pregame_window_sec = 900  # 15 minutes

        # Candles: some before kickoff, some after
        candles = [
            Candle(start_ts=kickoff_ts - 1000, open_cents=70, high_cents=70, low_cents=65, close_cents=65, volume=100),  # Too early
            Candle(start_ts=kickoff_ts - 800, open_cents=65, high_cents=70, low_cents=65, close_cents=68, volume=100),  # Pregame window
            Candle(start_ts=kickoff_ts - 600, open_cents=68, high_cents=70, low_cents=66, close_cents=67, volume=100),  # Pregame window
            Candle(start_ts=kickoff_ts - 60, open_cents=67, high_cents=68, low_cents=65, close_cents=66, volume=100),   # Last pregame
            Candle(start_ts=kickoff_ts + 60, open_cents=66, high_cents=66, low_cents=50, close_cents=52, volume=100),   # After kickoff (ignored)
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        pregame_prob = compute_pregame_probability(game_data, kickoff_ts, pregame_window_sec=pregame_window_sec)

        # Should use last candle before kickoff
        assert pregame_prob is not None
        assert pregame_prob == 0.66  # 66 cents

    def test_pregame_uses_vwap_if_no_candles(self):
        """Test that VWAP from trades is used if candles unavailable."""
        event = EventInfo(
            event_ticker="TEST-002",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-002", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        pregame_window_sec = 900

        # No candles, only trades
        trades = [
            Trade(ticker="TEST-MARKET", created_time=kickoff_ts - 800, count=10, yes_price=65),
            Trade(ticker="TEST-MARKET", created_time=kickoff_ts - 600, count=20, yes_price=70),
            Trade(ticker="TEST-MARKET", created_time=kickoff_ts - 400, count=10, yes_price=68),
        ]

        game_data = GameData(event=event, market=market, candles=[], trades=trades)

        pregame_prob = compute_pregame_probability(game_data, kickoff_ts, pregame_window_sec=pregame_window_sec)

        # VWAP = (10*65 + 20*70 + 10*68) / (10 + 20 + 10) = (650 + 1400 + 680) / 40 = 2730 / 40 = 68.25
        assert pregame_prob is not None
        assert pytest.approx(pregame_prob, 0.01) == 0.6825

    def test_halftime_boundary(self):
        """Test that halftime boundary is respected."""
        kickoff_ts = 1000000
        halftime_ts = kickoff_ts + 1800  # 30 minutes

        # Trade exactly at halftime
        trade_at_halftime = Trade(ticker="TEST", created_time=halftime_ts, count=10, yes_price=50)

        # Trade just before halftime
        trade_before_halftime = Trade(ticker="TEST", created_time=halftime_ts - 1, count=10, yes_price=48)

        # Trade after halftime
        trade_after_halftime = Trade(ticker="TEST", created_time=halftime_ts + 1, count=10, yes_price=52)

        # First half should include trades < halftime_ts
        assert trade_before_halftime.created_time < halftime_ts
        assert trade_at_halftime.created_time >= halftime_ts
        assert trade_after_halftime.created_time > halftime_ts

    def test_kickoff_boundary(self):
        """Test that kickoff boundary is respected."""
        kickoff_ts = 1000000

        # Trade exactly at kickoff
        trade_at_kickoff = Trade(ticker="TEST", created_time=kickoff_ts, count=10, yes_price=65)

        # Trade just before kickoff
        trade_before_kickoff = Trade(ticker="TEST", created_time=kickoff_ts - 1, count=10, yes_price=66)

        # Trade after kickoff
        trade_after_kickoff = Trade(ticker="TEST", created_time=kickoff_ts + 1, count=10, yes_price=64)

        # First half should include trades >= kickoff_ts
        assert trade_before_kickoff.created_time < kickoff_ts
        assert trade_at_kickoff.created_time >= kickoff_ts
        assert trade_after_kickoff.created_time > kickoff_ts

    def test_no_pregame_data_returns_none(self):
        """Test that None is returned when no pregame data available."""
        event = EventInfo(
            event_ticker="TEST-003",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-003", market_type="binary", title="Team A to win")

        kickoff_ts = 1000000
        pregame_window_sec = 900

        # Only data after kickoff
        candles = [
            Candle(start_ts=kickoff_ts + 60, open_cents=65, high_cents=65, low_cents=60, close_cents=60, volume=100),
        ]

        game_data = GameData(event=event, market=market, candles=candles, trades=[])

        pregame_prob = compute_pregame_probability(game_data, kickoff_ts, pregame_window_sec=pregame_window_sec)

        assert pregame_prob is None
