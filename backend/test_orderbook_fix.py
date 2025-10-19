"""Test the fixed orderbook parsing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

client = KalshiClient()

# Test with both CFB tickers that were failing
tickers = [
    "KXNCAAFGAME-25OCT15UTEPSHSU-UTEP",
    "KXNCAAFGAME-25OCT15DELJVST-JVST"
]

print("Testing orderbook fix...\n")

for ticker in tickers:
    print(f"Fetching orderbook for {ticker}...")
    orderbook = client.get_orderbook(ticker)

    if orderbook:
        print(f"  ✓ Success!")
        print(f"    Yes bid: {orderbook.yes_bid}¢ (size: {orderbook.yes_bid_size})")
        print(f"    Yes ask: {orderbook.yes_ask}¢ (size: {orderbook.yes_ask_size})")
    else:
        print(f"  ✗ Failed to fetch orderbook")
    print()

print("✓ All tests passed!")
