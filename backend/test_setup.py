"""
Test script to verify live trading setup.
Run this before starting the live trader.
"""
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.kalshi_client import KalshiClient


def test_config():
    """Test configuration file."""
    print("1. Testing configuration file...")

    try:
        with open('live_trading_config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        print("   ✓ Config file loaded")

        # Check required fields
        assert 'api_credentials' in config
        assert 'trading' in config
        assert 'markets' in config
        assert 'risk' in config

        print("   ✓ Required sections present")

        # Check if dry run is enabled (recommended for first run)
        if config['risk']['dry_run']:
            print("   ✓ Dry run mode enabled (SAFE)")
        else:
            print("   ⚠️  LIVE TRADING MODE enabled (REAL MONEY)")
            response = input("     Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                print("   ✗ Please enable dry_run mode first")
                return False

        # Check API credentials
        creds = config['api_credentials']
        has_email_pw = creds.get('email') and creds.get('password')
        has_api_key = creds.get('api_key') and creds.get('api_secret')

        if has_email_pw or has_api_key:
            print("   ✓ API credentials configured")
        else:
            print("   ✗ No API credentials found")
            print("     Add your Kalshi credentials to live_trading_config.yaml")
            return False

        print()
        return True

    except FileNotFoundError:
        print("   ✗ Config file not found: live_trading_config.yaml")
        return False
    except Exception as e:
        print(f"   ✗ Error loading config: {e}")
        return False


def test_api_connection():
    """Test Kalshi API connection."""
    print("2. Testing Kalshi API connection...")

    try:
        client = KalshiClient()

        # Try to get a series
        series = client.get_series(limit=1)

        if series:
            print(f"   ✓ Connected to Kalshi API")
            print(f"   ✓ Sample series: {series[0].series_ticker}")
        else:
            print("   ⚠️  No series returned (might be an API issue)")

        client.close()
        print()
        return True

    except Exception as e:
        print(f"   ✗ API connection failed: {e}")
        return False


def test_upcoming_games():
    """Check for upcoming games to trade."""
    print("3. Checking for upcoming games...")

    try:
        client = KalshiClient()

        # Check NFL games
        nfl_events = client.get_events(series_ticker='KXNFLGAME')
        print(f"   ✓ Found {len(nfl_events)} NFL events")

        # Check CFB games
        cfb_events = client.get_events(series_ticker='KXNCAAFGAME')
        print(f"   ✓ Found {len(cfb_events)} CFB events")

        # Check for games in next 24 hours
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)

        now_ts = int(now.timestamp())
        tomorrow_ts = int(tomorrow.timestamp())

        upcoming_nfl = [
            e for e in nfl_events
            if e.get('strike_date') and now_ts < e['strike_date'] < tomorrow_ts
        ]

        upcoming_cfb = [
            e for e in cfb_events
            if e.get('strike_date') and now_ts < e['strike_date'] < tomorrow_ts
        ]

        print(f"   ✓ {len(upcoming_nfl)} NFL games in next 24 hours")
        print(f"   ✓ {len(upcoming_cfb)} CFB games in next 24 hours")

        if upcoming_nfl + upcoming_cfb:
            print("   ✓ Games available to trade!")
        else:
            print("   ⚠️  No games in next 24 hours")
            print("      Bot will wait for games to start")

        client.close()
        print()
        return True

    except Exception as e:
        print(f"   ✗ Error checking games: {e}")
        return False


def test_directories():
    """Ensure required directories exist."""
    print("4. Checking directories...")

    Path("logs").mkdir(exist_ok=True)
    print("   ✓ logs/ directory ready")

    Path("artifacts").mkdir(exist_ok=True)
    print("   ✓ artifacts/ directory ready")

    print()
    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("LIVE TRADING SETUP VERIFICATION")
    print("=" * 80)
    print()

    results = []

    results.append(("Config", test_config()))
    results.append(("API Connection", test_api_connection()))
    results.append(("Upcoming Games", test_upcoming_games()))
    results.append(("Directories", test_directories()))

    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print()

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:20s} {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("✅ All tests passed! You're ready to run the live trader.")
        print()
        print("Next steps:")
        print("  1. Review live_trading_config.yaml one more time")
        print("  2. Ensure dry_run is set to true for first run")
        print("  3. Run: python3 live_trader.py")
        print()
    else:
        print("❌ Some tests failed. Fix the issues above before running.")
        print()

    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
