#!/usr/bin/env python3
"""Test Kalshi API credentials"""
import os
from dotenv import load_dotenv
import requests

# Load .env file
load_dotenv()

email = os.getenv('KALSHI_EMAIL')
password = os.getenv('KALSHI_PASSWORD')
api_key = os.getenv('KALSHI_API_KEY')
api_secret = os.getenv('KALSHI_API_SECRET')

print("=" * 80)
print("KALSHI API CREDENTIAL TEST")
print("=" * 80)
print()

print("Credentials loaded from .env:")
print(f"  EMAIL: {'SET' if email else 'NOT SET'}")
print(f"  PASSWORD: {'SET' if password else 'NOT SET'}")
print(f"  API_KEY: {'SET' if api_key else 'NOT SET'}")
print(f"  API_SECRET: {'SET' if api_secret else 'NOT SET'}")
print()

if email and password:
    print("Testing login with email/password...")
    try:
        response = requests.post(
            'https://api.elections.kalshi.com/trade-api/v2/login',
            json={'email': email, 'password': password},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("✓ LOGIN SUCCESSFUL!")
            data = response.json()
            if 'token' in data:
                print(f"  Token received: {data['token'][:30]}...")
                print()
                print("Credentials are VALID - bot should be able to place orders!")
            else:
                print("  Warning: No token in response")
                print(f"  Response: {data}")
        else:
            print("✗ LOGIN FAILED!")
            print(f"  Error: {response.text}")
            print()
            print("Possible issues:")
            print("  - Incorrect email or password")
            print("  - Account not activated")
            print("  - API access not enabled")
    except Exception as e:
        print(f"✗ ERROR: {e}")
else:
    print("✗ Email or password not set in .env file")
    print()
    print("Make sure your .env file contains:")
    print("  KALSHI_EMAIL=your_email@example.com")
    print("  KALSHI_PASSWORD=your_password")
    print("  KALSHI_API_KEY=your_api_key")
    print("  KALSHI_API_SECRET=your_api_secret")

print()
print("=" * 80)
