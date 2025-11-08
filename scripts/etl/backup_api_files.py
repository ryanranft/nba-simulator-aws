#!/usr/bin/env python3
"""
Backup API-scraped files to CSV format

Converts the incorrectly scraped API JSON files to CSV for backup purposes.
"""

import json
import csv
from pathlib import Path

# File paths
GAMES = [
    {
        "game_id": "400975770",
        "source": "/Users/ryanranft/0espn/data/nba/nba_pbp/400975770.json",
        "backup": "/Users/ryanranft/nba-simulator-aws/backup_api_scrapes/400975770_api.csv",
    },
    {
        "game_id": "401070722",
        "source": "/Users/ryanranft/0espn/data/nba/nba_pbp/401070722.json",
        "backup": "/Users/ryanranft/nba-simulator-aws/backup_api_scrapes/401070722_api.csv",
    },
]


def json_to_csv(json_file: Path, csv_file: Path):
    """Convert JSON file to CSV format"""
    print(f"Backing up {json_file} to {csv_file}")

    with open(json_file, "r") as f:
        data = json.load(f)

    # Flatten the JSON structure for CSV
    rows = []

    def flatten_dict(d, parent_key="", sep="_"):
        """Recursively flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # For lists, just convert to JSON string
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    flat_data = flatten_dict(data)

    # Write to CSV
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Key", "Value"])
        for key, value in flat_data.items():
            writer.writerow([key, value])

    file_size = csv_file.stat().st_size
    print(f"  ✅ Backed up to {csv_file} ({file_size:,} bytes)")


def main():
    print("=" * 70)
    print("Backing Up API-Scraped Files to CSV")
    print("=" * 70)
    print()

    for game in GAMES:
        source_path = Path(game["source"])
        backup_path = Path(game["backup"])

        if not source_path.exists():
            print(f"❌ Source file not found: {source_path}")
            continue

        json_to_csv(source_path, backup_path)

    print()
    print("=" * 70)
    print("Backup Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
