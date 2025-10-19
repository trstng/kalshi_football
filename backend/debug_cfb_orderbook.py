"""Debug script to inspect CFB orderbook structure."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

client = KalshiClient()

# Try to fetch orderbook for one of the failing tickers
ticker = "KXNCAAFGAME-25OCT15UTEPSHSU-UTEP"

print(f"Fetching orderbook for {ticker}...\n")

try:
    response = client._get(f"/markets/{ticker}/orderbook")
    print("Raw API response:")
    print(json.dumps(response, indent=2))

    orderbook = response.get("orderbook", {})
    print("\nOrderbook data:")
    print(json.dumps(orderbook, indent=2))

    yes_bids = orderbook.get("yes", [])
    yes_asks = orderbook.get("no", [])

    print(f"\nyes_bids type: {type(yes_bids)}")
    print(f"yes_bids length: {len(yes_bids)}")
    if yes_bids:
        print(f"yes_bids[0] type: {type(yes_bids[0])}")
        print(f"yes_bids[0] value: {yes_bids[0]}")

    print(f"\nyes_asks (no) type: {type(yes_asks)}")
    print(f"yes_asks length: {len(yes_asks)}")
    if yes_asks:
        print(f"yes_asks[0] type: {type(yes_asks[0])}")
        print(f"yes_asks[0] value: {yes_asks[0]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
