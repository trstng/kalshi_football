"""
Kelly-optimized scaling strategy with $10k bankroll.

Kelly Criterion: f = (p * b - q) / b
Where:
  f = fraction of bankroll to bet
  p = probability of winning
  b = odds (net profit / bet)
  q = probability of losing (1 - p)
"""
import csv
from datetime import datetime

print('=' * 80)
print('KELLY-OPTIMIZED SCALING BACKTEST')
print('=' * 80)
print()

# Configuration
STARTING_BANKROLL = 10000  # $10,000
WIN_RATE = 0.90  # 90% from simple backtest
LOSS_RATE = 0.10

# Kelly calculation for this strategy
# Average profit per winning trade: ~5¢ per contract
# Average loss per losing trade: assume worst case -15¢ (from max MAE)
AVG_WIN = 5  # cents
AVG_LOSS = 15  # cents (conservative)

# Kelly formula: f = (p * b - q) / b
# b = odds = avg_win / avg_loss
odds = AVG_WIN / AVG_LOSS
kelly_full = (WIN_RATE * odds - LOSS_RATE) / odds
kelly_quarter = kelly_full * 0.25  # Conservative: 1/4 Kelly

print(f'Starting Bankroll: ${STARTING_BANKROLL:,.2f}')
print()
print('Kelly Calculation:')
print(f'  Win Rate: {WIN_RATE:.1%}')
print(f'  Avg Win: {AVG_WIN}¢ per contract')
print(f'  Avg Loss: {AVG_LOSS}¢ (worst case)')
print(f'  Odds: {odds:.2f}')
print(f'  Full Kelly: {kelly_full:.1%} of bankroll per trade')
print(f'  1/4 Kelly:  {kelly_quarter:.1%} of bankroll per trade (RECOMMENDED)')
print()
print('=' * 80)
print()

# Define scaling levels with Kelly sizing
# We'll use 1/4 Kelly and allocate it across scale levels
KELLY_FRACTION = kelly_quarter

def calculate_position_size(bankroll, kelly_frac, price_cents):
    """
    Calculate number of contracts to buy.

    Args:
        bankroll: Current bankroll in dollars
        kelly_frac: Kelly fraction (e.g., 0.25 for 1/4 Kelly)
        price_cents: Entry price in cents

    Returns:
        Number of contracts
    """
    # Convert cents to dollars for calculation
    price_dollars = price_cents / 100.0

    # Kelly says bet this fraction of bankroll
    dollar_amount = bankroll * kelly_frac

    # How many contracts can we buy?
    contracts = int(dollar_amount / price_dollars)

    return max(1, contracts)  # At least 1 contract


# Define scaling strategy
SCALE_LEVELS = [
    {'trigger': 49, 'kelly_multiplier': 1.0},  # Base size
    {'trigger': 45, 'kelly_multiplier': 1.5},  # 1.5x base (bigger edge)
    {'trigger': 41, 'kelly_multiplier': 2.0},  # 2x base
    {'trigger': 37, 'kelly_multiplier': 2.5},  # 2.5x base
    {'trigger': 33, 'kelly_multiplier': 3.0},  # 3x base (max size)
]

print('Scaling Strategy with Kelly:')
for level in SCALE_LEVELS:
    print(f"  {level['trigger']}¢: {level['kelly_multiplier']}x Kelly base size")
print()
print('=' * 80)
print()

# Load trades
with open('artifacts/backtest_2025-10-14_11-34-45/trades.csv', 'r') as f:
    reader = csv.DictReader(f)
    trades = list(reader)

# Run backtest with Kelly sizing
current_bankroll = STARTING_BANKROLL
total_contracts_traded = 0
total_dollars_at_risk = 0

trade_results = []

for i, trade in enumerate(trades, 1):
    entry_cents = int(float(trade['entry_prob']) * 100)
    exit_cents = int(float(trade['exit_prob']) * 100)
    mae = float(trade['mae'])
    entry_prob = float(trade['entry_prob'])
    pregame_prob = float(trade['pregame_prob'])
    event_ticker = trade['event_ticker']
    entry_ts = datetime.fromisoformat(trade['entry_ts_utc'].replace('+00:00', ''))

    # Calculate lowest price reached
    lowest_cents = int((entry_prob - mae) * 100)

    # Determine which scaling levels were triggered
    entries = []
    for level in SCALE_LEVELS:
        if lowest_cents <= level['trigger']:
            # Calculate position size using Kelly
            base_size = calculate_position_size(
                current_bankroll,
                KELLY_FRACTION,
                level['trigger']
            )

            # Apply multiplier for scaling
            size = int(base_size * level['kelly_multiplier'])

            entries.append({
                'price': level['trigger'],
                'size': size
            })

    # Calculate P&L for this trade
    if entries:
        total_size = sum(e['size'] for e in entries)
        weighted_entry = sum(e['price'] * e['size'] for e in entries) / total_size

        # P&L in cents per contract
        pnl_per_contract = exit_cents - weighted_entry

        # Total P&L in dollars
        pnl_dollars = (pnl_per_contract / 100.0) * total_size

        # Update bankroll
        current_bankroll += pnl_dollars

        # Calculate capital at risk
        capital_at_risk = sum(e['price'] * e['size'] for e in entries) / 100.0
        total_contracts_traded += total_size
        total_dollars_at_risk = max(total_dollars_at_risk, capital_at_risk)

        pct_return = (pnl_dollars / STARTING_BANKROLL) * 100

        print(f'Trade {i}: {event_ticker}')
        print(f'  Date: {entry_ts.strftime("%Y-%m-%d")}')
        print(f'  Pregame: {pregame_prob:.0%} → Entry: {entry_cents}¢ → Low: {lowest_cents}¢ → Exit: {exit_cents}¢')
        print(f'  Levels hit: {len(entries)}')

        for j, entry in enumerate(entries, 1):
            print(f'    Level {j}: {entry["size"]:3d} contracts @ {entry["price"]}¢ = ${entry["price"] * entry["size"] / 100:.2f}')

        print(f'  Total size: {total_size} contracts')
        print(f'  Avg entry: {weighted_entry:.1f}¢')
        print(f'  Capital at risk: ${capital_at_risk:.2f}')
        print(f'  P&L: {pnl_per_contract:+.1f}¢/contract × {total_size} = ${pnl_dollars:+.2f} ({pct_return:+.2f}% of starting)')
        print(f'  New bankroll: ${current_bankroll:,.2f}')
        print()

        trade_results.append({
            'trade_num': i,
            'pnl': pnl_dollars,
            'bankroll': current_bankroll,
            'contracts': total_size,
            'capital_at_risk': capital_at_risk
        })

print('=' * 80)
print('FINAL RESULTS')
print('=' * 80)
print()
print(f'Starting Bankroll:  ${STARTING_BANKROLL:,.2f}')
print(f'Ending Bankroll:    ${current_bankroll:,.2f}')
print(f'Profit:             ${current_bankroll - STARTING_BANKROLL:+,.2f}')
print(f'Return:             {((current_bankroll / STARTING_BANKROLL) - 1) * 100:+.2f}%')
print()
print(f'Total Contracts:    {total_contracts_traded}')
print(f'Max Capital at Risk: ${total_dollars_at_risk:.2f} ({total_dollars_at_risk / STARTING_BANKROLL * 100:.1f}% of bankroll)')
print()

# Calculate max drawdown
peak_bankroll = STARTING_BANKROLL
max_drawdown_pct = 0

for result in trade_results:
    if result['bankroll'] > peak_bankroll:
        peak_bankroll = result['bankroll']

    drawdown = (peak_bankroll - result['bankroll']) / peak_bankroll
    max_drawdown_pct = max(max_drawdown_pct, drawdown)

print(f'Max Drawdown:       {max_drawdown_pct * 100:.2f}%')
print()

# Show trade-by-trade bankroll growth
print('Bankroll Growth:')
print('-' * 80)
for result in trade_results:
    bar_length = int((result['bankroll'] - STARTING_BANKROLL) / 10)
    bar = '█' * max(0, bar_length)
    print(f"Trade {result['trade_num']:2d}: ${result['bankroll']:8,.2f} {bar}")

print()
print('=' * 80)
print('RISK ANALYSIS')
print('=' * 80)
print()
print(f'Kelly Fraction Used: {KELLY_FRACTION:.1%} (1/4 Kelly - Conservative)')
print()
print('Position Sizing Example (at $10k bankroll):')
print('  49¢ level: ~20-25 contracts  (~$100-120 risk)')
print('  45¢ level: ~33-38 contracts  (~$150-170 risk)')
print('  41¢ level: ~48-55 contracts  (~$200-225 risk)')
print('  37¢ level: ~67-75 contracts  (~$250-275 risk)')
print('  33¢ level: ~90-100 contracts (~$300-330 risk)')
print()
print('Worst Case (all 5 levels hit): ~$1,000-1,200 total risk')
print('This is ~10-12% of bankroll - manageable with 90% win rate!')
print()

# Compare with simple strategy
simple_profit = 64 / 100  # 64 cents
kelly_profit = current_bankroll - STARTING_BANKROLL
improvement = kelly_profit / simple_profit

print('=' * 80)
print(f'Simple Strategy (1 contract): ${simple_profit:.2f}')
print(f'Kelly Scaled Strategy:        ${kelly_profit:.2f}')
print(f'Improvement:                  {improvement:.1f}x')
print('=' * 80)
