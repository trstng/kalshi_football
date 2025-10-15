"""Merge all matched CFB markets into single enriched CSV."""
import csv

# Read both matched files
matched1 = []
with open('artifacts/cfb_markets_2025_enriched.csv', 'r') as f:
    reader = csv.DictReader(f)
    matched1 = list(reader)

matched2 = []
with open('artifacts/cfb_markets_2025_cfbd_matched.csv', 'r') as f:
    reader = csv.DictReader(f)
    matched2 = list(reader)

# Combine
all_matched = matched1 + matched2

print(f"Merged {len(matched1)} + {len(matched2)} = {len(all_matched)} total matched markets")

# Write combined file
with open('artifacts/cfb_markets_2025_enriched.csv', 'w', newline='') as f:
    fieldnames = [
        'event_ticker', 'market_ticker', 'market_title', 'yes_subtitle',
        'series_ticker', 'away_team', 'home_team', 'kickoff_ts', 'matched_via'
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for row in all_matched:
        # Ensure matched_via field exists
        if 'matched_via' not in row:
            row['matched_via'] = 'MASTER_SCHEDULE'
        writer.writerow(row)

print(f"✓ Saved combined file: artifacts/cfb_markets_2025_enriched.csv")
