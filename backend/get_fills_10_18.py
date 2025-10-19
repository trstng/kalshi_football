"""
Fetch actual fills from Kalshi for 10/18/2025 to compare with backtest.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from kalshi_python import Configuration, KalshiClient as OfficialKalshiClient, PortfolioApi


def get_fills(start_date: str = "2025-10-18", end_date: str = "2025-10-19"):
    """
    Fetch all fills between start_date and end_date.

    Args:
        start_date: Start date in YYYY-MM-DD format (inclusive)
        end_date: End date in YYYY-MM-DD format (exclusive)
    """
    # Initialize client
    api_key = os.environ.get("KALSHI_API_KEY")
    api_secret = os.environ.get("KALSHI_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("KALSHI_API_KEY and KALSHI_API_SECRET required")

    # Convert literal \n to actual newlines
    if '\\n' in api_secret:
        api_secret = api_secret.replace('\\n', '\n')

    config = Configuration(
        host="https://api.elections.kalshi.com/trade-api/v2"
    )
    config.api_key_id = api_key
    config.private_key_pem = api_secret

    client = OfficialKalshiClient(config)
    portfolio_api = PortfolioApi(client)

    print("=" * 80)
    print(f"FETCHING FILLS: {start_date} to {end_date}")
    print("=" * 80)
    print()

    # Convert dates to timestamps
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

    print(f"Start timestamp: {start_ts} ({datetime.fromtimestamp(start_ts)})")
    print(f"End timestamp:   {end_ts} ({datetime.fromtimestamp(end_ts)})")
    print()

    # Fetch fills
    try:
        # The PortfolioApi should have a get_fills method
        # Parameters might vary - let me try different approaches

        print("Fetching fills from Kalshi API...")

        # Try method 1: get_fills with min/max timestamps
        try:
            response = portfolio_api.get_fills(
                min_ts=start_ts,
                max_ts=end_ts,
                limit=1000
            )
            fills = response.fills if hasattr(response, 'fills') else []
        except Exception as e:
            print(f"Method 1 failed: {e}")

            # Try method 2: get_fills without timestamp filters
            try:
                response = portfolio_api.get_fills(limit=1000)
                fills = response.fills if hasattr(response, 'fills') else []

                # Filter by timestamp manually
                fills = [f for f in fills if start_ts <= f.created_time <= end_ts]
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                print("\nAvailable methods on portfolio_api:")
                print([m for m in dir(portfolio_api) if not m.startswith('_')])
                return []

        print(f"Found {len(fills)} fills")
        print()

        if not fills:
            print("No fills found for this date range")
            return []

        # Convert fills to dataframe for analysis
        fill_data = []
        for fill in fills:
            # Extract price based on side
            price = None
            if hasattr(fill, 'yes_price') and fill.yes_price is not None:
                price = fill.yes_price
            elif hasattr(fill, 'no_price') and fill.no_price is not None:
                price = fill.no_price
            elif hasattr(fill, 'price'):
                price = fill.price

            fill_dict = {
                'ticker': fill.ticker if hasattr(fill, 'ticker') else None,
                'side': fill.side if hasattr(fill, 'side') else None,
                'action': fill.action if hasattr(fill, 'action') else None,
                'count': fill.count if hasattr(fill, 'count') else None,
                'price': price,
                'created_time': fill.created_time if hasattr(fill, 'created_time') else None,
                'order_id': fill.order_id if hasattr(fill, 'order_id') else None,
                'trade_id': fill.trade_id if hasattr(fill, 'trade_id') else None,
            }

            # Debug: print first fill to see structure
            if len(fill_data) == 0:
                print("DEBUG - First fill attributes:")
                print([attr for attr in dir(fill) if not attr.startswith('_')])
                print(f"Fill object: {fill}")
                print()

            fill_data.append(fill_dict)

        df = pd.DataFrame(fill_data)

        # Add human-readable timestamp
        if 'created_time' in df.columns and not df.empty:
            df['timestamp'] = pd.to_datetime(df['created_time'], unit='s')

        # Group by ticker to show trades per game
        print("=" * 80)
        print("FILLS BY GAME")
        print("=" * 80)

        if not df.empty:
            for ticker in df['ticker'].unique():
                game_fills = df[df['ticker'] == ticker].sort_values('created_time')

                print(f"\n{ticker}")
                print("-" * 80)

                buys = game_fills[game_fills['action'] == 'buy']
                sells = game_fills[game_fills['action'] == 'sell']

                # Calculate P&L
                # Note: API returns prices as decimals (0.49 = 49 cents), already in dollar terms
                total_buy_cost = (buys['price'] * buys['count']).sum() if not buys.empty else 0
                total_sell_revenue = (sells['price'] * sells['count']).sum() if not sells.empty else 0
                total_contracts_bought = buys['count'].sum() if not buys.empty else 0
                total_contracts_sold = sells['count'].sum() if not sells.empty else 0

                # Use average of bought and sold for fee calculation (in case they differ)
                total_contracts = max(total_contracts_bought, total_contracts_sold)

                pnl_gross = total_sell_revenue - total_buy_cost  # Already in dollars
                fees = (total_contracts * 2 * 0.01) if total_contracts > 0 else 0  # $0.01 per contract, both sides
                pnl_net = pnl_gross - fees

                print(f"  Buys:  {len(buys)} fills, {buys['count'].sum() if not buys.empty else 0} contracts")
                if not buys.empty:
                    for _, fill in buys.iterrows():
                        ts = fill['timestamp'].strftime('%H:%M:%S') if 'timestamp' in fill else 'unknown'
                        print(f"    {ts}: {fill['count']} @ {fill['price']}¢")

                print(f"  Sells: {len(sells)} fills, {sells['count'].sum() if not sells.empty else 0} contracts")
                if not sells.empty:
                    for _, fill in sells.iterrows():
                        ts = fill['timestamp'].strftime('%H:%M:%S') if 'timestamp' in fill else 'unknown'
                        print(f"    {ts}: {fill['count']} @ {fill['price']}¢")

                print(f"  P&L (Net): ${pnl_net:+.2f}")

        # Overall summary
        print("\n" + "=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)

        if not df.empty:
            games = df['ticker'].nunique()
            total_fills = len(df)
            total_buys = len(df[df['action'] == 'buy'])
            total_sells = len(df[df['action'] == 'sell'])

            # Calculate total P&L across all games
            games_pnl = []
            for ticker in df['ticker'].unique():
                game_fills = df[df['ticker'] == ticker]
                buys = game_fills[game_fills['action'] == 'buy']
                sells = game_fills[game_fills['action'] == 'sell']

                total_buy_cost = (buys['price'] * buys['count']).sum() if not buys.empty else 0
                total_sell_revenue = (sells['price'] * sells['count']).sum() if not sells.empty else 0
                total_contracts_bought = buys['count'].sum() if not buys.empty else 0
                total_contracts_sold = sells['count'].sum() if not sells.empty else 0
                total_contracts = max(total_contracts_bought, total_contracts_sold)

                pnl_gross = total_sell_revenue - total_buy_cost  # Already in dollars
                fees = (total_contracts * 2 * 0.01) if total_contracts > 0 else 0
                pnl_net = pnl_gross - fees

                games_pnl.append(pnl_net)

            total_pnl = sum(games_pnl)
            winning_games = sum(1 for p in games_pnl if p > 0)
            losing_games = sum(1 for p in games_pnl if p < 0)
            breakeven_games = sum(1 for p in games_pnl if p == 0)

            print(f"Total Games Traded:  {games}")
            print(f"  Winning Games:     {winning_games} ({winning_games/games*100:.1f}%)")
            print(f"  Losing Games:      {losing_games} ({losing_games/games*100:.1f}%)")
            print(f"  Breakeven Games:   {breakeven_games}")
            print()
            print(f"Total Fills:         {total_fills} ({total_buys} buys, {total_sells} sells)")
            print(f"Total P&L (Net):     ${total_pnl:+,.2f}")
            print(f"Avg P&L per Game:    ${total_pnl/games:+.2f}")

        # Save to CSV
        output_path = Path("artifacts") / f"kalshi_fills_{start_date}.csv"
        output_path.parent.mkdir(exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\nFills saved to: {output_path}")

        return fills

    except Exception as e:
        print(f"Error fetching fills: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    fills = get_fills(start_date="2025-10-18", end_date="2025-10-19")
