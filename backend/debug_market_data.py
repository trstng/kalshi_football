"""Debug script to see all available market data."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

client = KalshiClient()

ticker = "KXNCAAFGAME-25OCT15DELJVST-JVST"

print(f"=== Market Info for {ticker} ===\n")

# Get full market data
try:
    response = client._get(f"/markets/{ticker}")
    print("Full market response:")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80 + "\n")

# Get orderbook
try:
    response = client._get(f"/markets/{ticker}/orderbook")
    print("Orderbook response:")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error: {e}")
