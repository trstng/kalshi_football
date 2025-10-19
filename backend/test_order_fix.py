#!/usr/bin/env python3
"""Test order placement fix"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.trading_client import KalshiTradingClient
from kalshi_nfl_research.kalshi_client import KalshiClient

# Load environment variables
load_dotenv()

print("=" * 80)
print("TESTING ORDER PLACEMENT FIX")
print("=" * 80)
print()

# Get credentials
api_key = os.getenv('KALSHI_API_KEY')
api_secret = os.getenv('KALSHI_API_SECRET')

if not api_key or not api_secret:
    print("✗ Missing credentials in .env file")
    exit(1)

print("✓ Credentials loaded")
print()

try:
    # Initialize trading client
    print("Initializing trading client...")
    trading_client = KalshiTradingClient(
        api_key=api_key,
        api_secret=api_secret
    )
    print("✓ Trading client initialized")
    print()

    # Get balance
    balance = trading_client.get_balance()
    print(f"Account balance: ${balance / 100:.2f}")
    print()

    # Find an active market to test with
    print("Finding an active market to test order placement...")
    public_client = KalshiClient()

    # Search for a market (using CFB first, then NFL)
    markets = public_client.get_markets(
        series_ticker="KXNCAAF",
        limit=5
    )

    if not markets:
        markets = public_client.get_markets(
            series_ticker="KXNFL",
            limit=5
        )

    if not markets:
        print("✗ No active markets found to test with")
        exit(1)

    # Find a market with available liquidity
    test_market = None
    for market in markets:
        if market.yes_ask and market.yes_ask > 0:
            test_market = market
            break

    if not test_market:
        test_market = markets[0]

    print(f"Test market: {test_market.ticker}")
    print(f"  Title: {test_market.title}")
    print(f"  Yes ask: {test_market.yes_ask}¢")
    print(f"  No ask: {test_market.no_ask}¢")
    print()

    # Place a test limit order at a very low price (unlikely to fill)
    # This tests the API call without risking actual execution
    test_price = 1  # 1 cent - very unlikely to fill
    test_size = 1   # 1 contract minimum

    print(f"Placing test order: buy 1 yes @ {test_price}¢")
    print("(This is set at 1¢ so it's very unlikely to fill - just testing the API)")
    print()

    order = trading_client.place_order(
        market_ticker=test_market.ticker,
        side="yes",
        action="buy",
        count=test_size,
        price=test_price,
        order_type="limit"
    )

    print("=" * 80)
    print("✓ SUCCESS! Order placed without errors")
    print("=" * 80)
    print(f"Order ID: {order.order_id}")
    print(f"Status: {order.status}")
    print()

    # Try to cancel the test order if it didn't execute
    if order.status != "executed":
        print("Cancelling test order...")
        try:
            trading_client.cancel_order(order.order_id)
            print("✓ Test order cancelled")
        except Exception as e:
            print(f"Note: Could not cancel order (may have already filled): {e}")
    else:
        print("Note: Order executed immediately (filled at 1¢)")
    print()

    print("=" * 80)
    print("✓ Order placement is working correctly!")
    print("=" * 80)

except Exception as e:
    print()
    print("=" * 80)
    print("✗ TEST FAILED")
    print("=" * 80)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 80)
    exit(1)
finally:
    if 'trading_client' in locals():
        trading_client.close()
    if 'public_client' in locals():
        public_client.close()
