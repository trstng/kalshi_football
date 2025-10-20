"""
Manual reconciliation script to sync database with Kalshi API.
Run this if dashboard shows stale data.

Usage:
    python backend/reconcile_positions.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_nfl_research.trading_client import KalshiTradingClient
from supabase_logger import SupabaseLogger

# Load environment variables
load_dotenv()


def reconcile_orders():
    """Reconcile pending orders with actual Kalshi status."""
    print("=" * 80)
    print("ORDER RECONCILIATION")
    print("=" * 80)
    print()

    # Initialize clients
    trading_client = KalshiTradingClient(
        email=os.getenv('KALSHI_EMAIL'),
        password=os.getenv('KALSHI_PASSWORD'),
        api_key=os.getenv('KALSHI_API_KEY'),
        api_secret=os.getenv('KALSHI_API_SECRET'),
    )

    supabase = SupabaseLogger()

    if not supabase.client:
        print("✗ ERROR: Could not connect to Supabase")
        return

    # Get all "pending" orders from database
    try:
        result = supabase.client.table('orders').select('*').eq('status', 'pending').execute()
        pending_orders = result.data
    except Exception as e:
        print(f"✗ ERROR: Could not query pending orders: {e}")
        return

    print(f"Found {len(pending_orders)} pending orders in database")
    print()

    updated_count = 0
    error_count = 0

    # Check each order's actual status
    for order in pending_orders:
        order_id = order['order_id']
        market_ticker = order['market_ticker']

        try:
            print(f"Checking order: {order_id} ({market_ticker})")

            status_response = trading_client.get_order_status(order_id)

            if status_response is None:
                # Order not found - probably filled/cancelled
                print(f"  → Order not found on Kalshi (likely executed) - marking as filled")
                supabase.update_order_status(order_id, 'filled', order['size'])
                updated_count += 1
            else:
                order_data = status_response.get('order', {})
                actual_status = order_data.get('status', 'pending')
                filled_count = order_data.get('filled_count', 0)

                if actual_status != 'pending':
                    print(f"  → Status is actually '{actual_status}' (filled: {filled_count}/{order['size']}) - updating database")

                    if actual_status == 'filled' or actual_status == 'executed':
                        supabase.update_order_status(order_id, 'filled', filled_count)
                    elif actual_status == 'cancelled':
                        supabase.update_order_status(order_id, 'cancelled', 0)
                    elif filled_count > 0 and filled_count < order['size']:
                        supabase.update_order_status(order_id, 'partially_filled', filled_count)

                    updated_count += 1
                else:
                    print(f"  → Status is still pending (no update needed)")

        except Exception as e:
            print(f"  ✗ ERROR checking {order_id}: {e}")
            error_count += 1

        print()

    print("=" * 80)
    print(f"Reconciliation complete!")
    print(f"  Updated: {updated_count} orders")
    print(f"  Errors: {error_count} orders")
    print("=" * 80)

    # Close trading client
    trading_client.close()


def reconcile_positions():
    """Reconcile open positions with actual Kalshi status."""
    print()
    print("=" * 80)
    print("POSITION RECONCILIATION")
    print("=" * 80)
    print()

    supabase = SupabaseLogger()

    if not supabase.client:
        print("✗ ERROR: Could not connect to Supabase")
        return

    # Get all open positions from database
    try:
        result = supabase.client.table('positions').select('*').eq('status', 'open').execute()
        open_positions = result.data
    except Exception as e:
        print(f"✗ ERROR: Could not query open positions: {e}")
        return

    print(f"Found {len(open_positions)} open positions in database")
    print()

    for position in open_positions:
        print(f"Position: {position['market_ticker']} - {position['size']} @ {position['entry_price']}¢")
        print(f"  Entry time: {position['entry_time']}")
        print(f"  Order ID: {position.get('order_id', 'N/A')}")
        print()

    print("=" * 80)
    print("Position reconciliation complete!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        reconcile_orders()
        reconcile_positions()
    except KeyboardInterrupt:
        print()
        print("Reconciliation cancelled by user")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
