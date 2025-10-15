"""
Analyze what a scaling strategy would have achieved on existing trades.
"""
import csv

print('=' * 70)
print('SCALING STRATEGY SIMULATION')
print('=' * 70)
print()

# Define scaling levels (as price drops, increase size)
SCALE_LEVELS = [
    {'trigger': 49, 'size': 1},
    {'trigger': 45, 'size': 2},
    {'trigger': 41, 'size': 3},
    {'trigger': 37, 'size': 4},
    {'trigger': 33, 'size': 5},
]

print('Strategy: Scale in as price drops')
print('(Assumes fills at trigger prices)')
print()
for level in SCALE_LEVELS:
    print(f'  {level["trigger"]}¢: {level["size"]} contracts')
print()
print('=' * 70)
print()

# Load trades
with open('artifacts/backtest_2025-10-14_11-34-45/trades.csv', 'r') as f:
    reader = csv.DictReader(f)
    trades = list(reader)

total_simple_pnl = 0
total_scaled_pnl = 0

for i, trade in enumerate(trades, 1):
    entry_cents = int(float(trade['entry_prob']) * 100)
    exit_cents = int(float(trade['exit_prob']) * 100)
    mae = float(trade['mae'])
    entry_prob = float(trade['entry_prob'])
    pregame_prob = float(trade['pregame_prob'])

    # Calculate lowest price reached
    lowest_cents = int((entry_prob - mae) * 100)

    # Determine which scaling levels were triggered
    entries = []
    for level in SCALE_LEVELS:
        if lowest_cents <= level['trigger']:
            # We hit this level - assume fill at trigger price
            entries.append({
                'price': level['trigger'],
                'size': level['size']
            })

    # Calculate weighted average entry and P&L
    if entries:
        total_size = sum(e['size'] for e in entries)
        weighted_entry = sum(e['price'] * e['size'] for e in entries) / total_size

        # P&L calculation
        simple_pnl = exit_cents - entry_cents
        scaled_pnl = (exit_cents - weighted_entry) * total_size

        multiplier = scaled_pnl / simple_pnl if simple_pnl != 0 else 0

        print(f'{i}. {trade["event_ticker"]}')
        print(f'   Pregame: {pregame_prob:.0%} → Entry: {entry_cents}¢ → Low: {lowest_cents}¢ → Exit: {exit_cents}¢')
        print(f'   Levels hit: {len(entries)} (total {total_size} contracts)')
        print(f'   Weighted avg entry: {weighted_entry:.1f}¢')
        print(f'   Simple P&L:  {simple_pnl:+4d}¢ (1 contract)')
        print(f'   Scaled P&L:  {scaled_pnl:+7.0f}¢ ({total_size} contracts)')
        print(f'   Multiplier:  {multiplier:5.1f}x better')
        print()

        total_simple_pnl += simple_pnl
        total_scaled_pnl += scaled_pnl
    else:
        # Never hit any scaling level (stayed above 49¢)
        simple_pnl = exit_cents - entry_cents
        print(f'{i}. {trade["event_ticker"]}')
        print(f'   Pregame: {pregame_prob:.0%} → Entry: {entry_cents}¢ → Low: {lowest_cents}¢ → Exit: {exit_cents}¢')
        print(f'   No scaling triggered (stayed above 49¢)')
        print(f'   Simple P&L:  {simple_pnl:+4d}¢ (1 contract)')
        print()

        total_simple_pnl += simple_pnl
        total_scaled_pnl += simple_pnl

print('=' * 70)
print('FINAL RESULTS')
print('=' * 70)
print()
print(f'Simple Strategy (1 contract each):  {total_simple_pnl:+6.0f}¢  (${total_simple_pnl / 100:+.2f})')
print(f'Scaled Strategy (pyramid sizing):   {total_scaled_pnl:+6.0f}¢  (${total_scaled_pnl / 100:+.2f})')
print()
print(f'Improvement: {total_scaled_pnl / total_simple_pnl:.1f}x better')
print()

# Calculate risk exposure
print('Risk Analysis:')
print('-' * 70)
print('With scaling, you could have lost more if trades went against you.')
print('Example: If a trade dropped to 33¢ (hitting all 5 levels = 15 contracts)')
print('  and then went to 0¢ instead of reverting, you would lose 15x more.')
print()
print('This is why Kelly sizing and position limits are critical!')
