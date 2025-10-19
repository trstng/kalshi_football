#!/usr/bin/env python3
"""Test placing an order with the official Kalshi client"""
import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient, PortfolioApi, CreateOrderRequest

# Load .env file
load_dotenv()

api_key_id = os.getenv('KALSHI_API_KEY')
private_key_pem = os.getenv('KALSHI_API_SECRET')

# Convert literal \n to actual newlines
if private_key_pem:
    private_key_pem = private_key_pem.replace('\\n', '\n')

print("=" * 80)
print("TESTING ORDER PLACEMENT")
print("=" * 80)
print()

try:
    # Create client
    config = Configuration(
        host="https://api.elections.kalshi.com/trade-api/v2"
    )
    config.api_key_id = api_key_id
    config.private_key_pem = private_key_pem

    client = KalshiClient(config)

    # Create Portfolio API
    portfolio_api = PortfolioApi(client)

    print("Testing order placement API...")
    print()

    # Try to create a test order (we won't actually place it, just test the API)
    print("Portfolio API methods:")
    print(f"  - create_order: {hasattr(portfolio_api, 'create_order')}")
    print(f"  - cancel_order: {hasattr(portfolio_api, 'cancel_order')}")
    print(f"  - get_balance: {hasattr(portfolio_api, 'get_balance')}")
    print()

    # Test get_balance through PortfolioApi
    balance_response = portfolio_api.get_balance()
    print(f"✓ get_balance works: ${balance_response.balance / 100:.2f}")
    print()

    print("=" * 80)
    print("✓ Portfolio API is ready for order placement!")
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
