"""
Tests for fill logic and cost calculations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from data_models import Candle, EventInfo, MarketInfo, Trade
from fetch import GameData, find_fill_trade


class TestFillsAndCosts:
    """Test fill logic and P&L calculations."""

    def test_find_fill_trade_within_grace(self):
        """Test finding a fill trade within grace window."""
        event = EventInfo(
            event_ticker="TEST-001",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-001", market_type="binary", title="Team A to win")

        trigger_ts = 1000100
        grace_sec = 15

        # Trade at trigger + 5 seconds
        trades = [
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 5, count=10, yes_price=48),
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 20, count=5, yes_price=50),  # Outside grace
        ]

        game_data = GameData(event=event, market=market, candles=[], trades=trades)

        fill_trade = find_fill_trade(game_data, trigger_ts, grace_sec=grace_sec)

        assert fill_trade is not None
        assert fill_trade.created_time == trigger_ts + 5
        assert fill_trade.yes_price == 48

    def test_find_fill_trade_no_trade_within_grace(self):
        """Test unfillable when no trade within grace window."""
        event = EventInfo(
            event_ticker="TEST-002",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-002", market_type="binary", title="Team A to win")

        trigger_ts = 1000100
        grace_sec = 15

        # All trades outside grace window
        trades = [
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 20, count=10, yes_price=48),
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 30, count=5, yes_price=50),
        ]

        game_data = GameData(event=event, market=market, candles=[], trades=trades)

        fill_trade = find_fill_trade(game_data, trigger_ts, grace_sec=grace_sec)

        assert fill_trade is None

    def test_find_fill_trade_at_boundary(self):
        """Test fill at exact grace window boundary."""
        event = EventInfo(
            event_ticker="TEST-003",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-003", market_type="binary", title="Team A to win")

        trigger_ts = 1000100
        grace_sec = 15

        # Trade exactly at grace boundary
        trades = [
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 15, count=10, yes_price=48),
        ]

        game_data = GameData(event=event, market=market, candles=[], trades=trades)

        fill_trade = find_fill_trade(game_data, trigger_ts, grace_sec=grace_sec)

        assert fill_trade is not None
        assert fill_trade.created_time == trigger_ts + 15

    def test_fill_trade_first_only(self):
        """Test that only the first trade is returned."""
        event = EventInfo(
            event_ticker="TEST-004",
            series_ticker="NFL-2024",
            title="Test Game",
            strike_date=1000000,
        )
        market = MarketInfo(ticker="TEST-MARKET", event_ticker="TEST-004", market_type="binary", title="Team A to win")

        trigger_ts = 1000100
        grace_sec = 15

        # Multiple trades within grace
        trades = [
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 3, count=10, yes_price=48),
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 5, count=10, yes_price=47),
            Trade(ticker="TEST-MARKET", created_time=trigger_ts + 10, count=10, yes_price=49),
        ]

        game_data = GameData(event=event, market=market, candles=[], trades=trades)

        fill_trade = find_fill_trade(game_data, trigger_ts, grace_sec=grace_sec)

        # Should return the first trade
        assert fill_trade is not None
        assert fill_trade.created_time == trigger_ts + 3
        assert fill_trade.yes_price == 48

    def test_pnl_calculation_with_fees(self):
        """Test P&L calculation includes fees."""
        entry_price_cents = 48
        exit_price_cents = 60
        per_contract_fee = 0.01  # $0.01 per contract

        pnl_gross_cents = exit_price_cents - entry_price_cents
        fees_cents = int(per_contract_fee * 100) * 2  # Entry + exit

        pnl_net_cents = pnl_gross_cents - fees_cents

        assert pnl_gross_cents == 12
        assert fees_cents == 2
        assert pnl_net_cents == 10

    def test_pnl_calculation_with_slippage(self):
        """Test P&L calculation includes slippage."""
        base_entry_price = 48
        base_exit_price = 60
        extra_slippage = 0.005  # $0.005 = 0.5 cents

        # Entry: pay slippage
        entry_price_cents = base_entry_price + int(extra_slippage * 100)
        # Exit: lose slippage
        exit_price_cents = base_exit_price - int(extra_slippage * 100)

        pnl_gross_cents = exit_price_cents - entry_price_cents

        # entry = 48 + 0.5 = 48.5 = 48 (int)
        # exit = 60 - 0.5 = 59.5 = 59 (int)
        # pnl = 59 - 48 = 11
        assert entry_price_cents == 48  # 48 + 0 (int truncation)
        assert exit_price_cents == 59  # 60 - 1 (int truncation from 0.5)

    def test_losing_trade(self):
        """Test losing trade calculation."""
        entry_price_cents = 48
        exit_price_cents = 40  # Exit lower than entry
        per_contract_fee = 0.01

        pnl_gross_cents = exit_price_cents - entry_price_cents
        fees_cents = int(per_contract_fee * 100) * 2

        pnl_net_cents = pnl_gross_cents - fees_cents

        assert pnl_gross_cents == -8
        assert pnl_net_cents == -10  # Loss plus fees
