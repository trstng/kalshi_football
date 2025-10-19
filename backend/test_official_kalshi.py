#!/usr/bin/env python3
"""Test Kalshi official Python client"""
import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient

# Load .env file
load_dotenv()

api_key_id = os.getenv('KALSHI_API_KEY')
private_key_pem = os.getenv('KALSHI_API_SECRET')

# Convert literal \n in the string to actual newlines
if private_key_pem:
    private_key_pem = private_key_pem.replace('\\n', '\n')

print("=" * 80)
print("TESTING OFFICIAL KALSHI PYTHON CLIENT")
print("=" * 80)
print()

print(f"API Key ID: {'SET' if api_key_id else 'NOT SET'}")
print(f"Private Key: {'SET' if private_key_pem else 'NOT SET'}")
print()

if not api_key_id or not private_key_pem:
    print("✗ Missing credentials in .env file")
    print()
    print("Make sure your .env contains:")
    print("  KALSHI_API_KEY=your-key-id")
    print("  KALSHI_API_SECRET=your-rsa-private-key-in-pem-format")
    exit(1)

try:
    print("Creating Kalshi client configuration...")
    config = Configuration(
        host="https://api.elections.kalshi.com/trade-api/v2"
    )

    config.api_key_id = api_key_id
    config.private_key_pem = private_key_pem

    print("Initializing Kalshi client...")
    client = KalshiClient(config)

    print("Testing API call: get_balance()...")
    balance_response = client.get_balance()

    print()
    print("=" * 80)
    print("✓ SUCCESS! Authentication works!")
    print("=" * 80)
    print(f"Account Balance: ${balance_response.balance / 100:.2f}")
    print()
    print("Your credentials are VALID and trades will work!")
    print("=" * 80)

except Exception as e:
    print()
    print("=" * 80)
    print("✗ AUTHENTICATION FAILED")
    print("=" * 80)
    print(f"Error: {e}")
    print()
    print("Possible issues:")
    print("  1. API key ID is incorrect")
    print("  2. Private key format is wrong (must be RSA PEM format)")
    print("  3. API key was deleted/revoked in Kalshi dashboard")
    print()
    print("Check your Kalshi account settings to verify API keys")
    print("=" * 80)
