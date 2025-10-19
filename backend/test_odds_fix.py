"""Test the fixed odds reading."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient

# Create a simple trader class to test get_current_price
class TestTrader:
    def __init__(self):
        self.public_client = KalshiClient()

    def get_current_price(self, market_ticker: str):
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
            print(f"Error: {e}")
            return None

trader = TestTrader()

# Test with both CFB games
tickers = [
    ("UTEP at Sam Houston", "KXNCAAFGAME-25OCT15UTEPSHSU-UTEP"),
    ("Delaware at Jacksonville St.", "KXNCAAFGAME-25OCT15DELJVST-JVST")
]

print("Testing fixed odds reading...\n")

for name, ticker in tickers:
    market = trader.public_client.get_market(ticker)
    if market:
        current_price = trader.get_current_price(ticker)
        print(f"{name}:")
        print(f"  yes_ask: {market.yes_ask}¢, no_ask: {market.no_ask}¢")
        print(f"  Favorite odds: {current_price:.0%}")
        print(f"  Expected: Delaware ~59% for second game")
        print()

print("✓ Test complete!")
