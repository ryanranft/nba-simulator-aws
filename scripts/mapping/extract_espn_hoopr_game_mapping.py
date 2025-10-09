#!/usr/bin/env python3
"""
Extract ESPN-to-hoopR Game ID Mapping

Extracts ESPN game IDs from hoopR's uid field and creates a mapping table.

hoopR uid format: s:40~l:46~e:{ESPN_ID}~c:{game_id}
Example: s:40~l:46~e:220612017~c:220612017

This mapping enables proper cross-validation and gap detection between
ESPN and hoopR data sources.

Usage:
    python scripts/mapping/extract_espn_hoopr_game_mapping.py
    python scripts/mapping/extract_espn_hoopr_game_mapping.py --output-format json
    python scripts/mapping/extract_espn_hoopr_game_mapping.py --save-to-rds

Output:
    - CSV: scripts/mapping/espn_hoopr_game_mapping.csv
    - JSON: scripts/mapping/espn_hoopr_game_mapping.json (optional)
    - RDS: game_id_mapping table (optional)
"""

import sqlite3
import json
import csv
import re
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local hoopR database
HOOPR_DB = "/tmp/hoopr_local.db"

# Output paths
OUTPUT_DIR = Path(__file__).parent
CSV_OUTPUT = OUTPUT_DIR / "espn_hoopr_game_mapping.csv"
JSON_OUTPUT = OUTPUT_DIR / "espn_hoopr_game_mapping.json"


def extract_espn_id_from_uid(uid: str) -> str:
    """
    Extract ESPN game ID from hoopR uid field.

    Format: s:40~l:46~e:{ESPN_ID}~c:{game_id}
    Returns: ESPN_ID or None if not found
    """
    if not uid:
        return None

    # Pattern: e:{ESPN_ID}
    match = re.search(r'~e:(\d+)~', uid)
    if match:
        return match.group(1)

    return None


def extract_mapping_from_hoopr(db_path: str = HOOPR_DB):
    """Extract ESPN-to-hoopR mapping from local hoopR database."""

    print("=" * 70)
    print("EXTRACT ESPN-HOOPR GAME ID MAPPING")
    print("=" * 70)
    print()

    # Check database exists
    if not Path(db_path).exists():
        raise FileNotFoundError(
            f"hoopR database not found: {db_path}\n"
            f"Run: python scripts/db/create_local_hoopr_database.py"
        )

    print(f"📂 Connecting to: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("✓ Connected")
    print()

    # Get all games with uid
    print("📊 Extracting ESPN IDs from uid field...")
    cursor.execute("""
        SELECT
            game_id,
            uid,
            game_date,
            home_display_name,
            away_display_name
        FROM schedule
        WHERE uid IS NOT NULL
        ORDER BY game_date;
    """)

    rows = cursor.fetchall()
    print(f"✓ Found {len(rows):,} games with uid")
    print()

    # Extract ESPN IDs
    print("🔍 Parsing ESPN IDs from uid field...")
    mappings = []
    no_espn_id = 0

    for row in rows:
        hoopr_game_id, uid, game_date, home_team, away_team = row

        espn_id = extract_espn_id_from_uid(uid)

        if espn_id:
            mappings.append({
                'espn_game_id': espn_id,
                'hoopr_game_id': str(hoopr_game_id),
                'game_date': game_date,
                'home_team': home_team,
                'away_team': away_team,
                'uid': uid
            })
        else:
            no_espn_id += 1

    print(f"✓ Extracted {len(mappings):,} ESPN game IDs")
    if no_espn_id > 0:
        print(f"⚠️  {no_espn_id} games missing ESPN ID in uid")
    print()

    cursor.close()
    conn.close()

    return mappings


def save_to_csv(mappings: list, output_path: Path = CSV_OUTPUT):
    """Save mapping to CSV file."""

    print(f"💾 Saving to CSV: {output_path}")

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'espn_game_id', 'hoopr_game_id', 'game_date',
            'home_team', 'away_team', 'uid'
        ])
        writer.writeheader()
        writer.writerows(mappings)

    print(f"✓ Saved {len(mappings):,} mappings")
    print()


def save_to_json(mappings: list, output_path: Path = JSON_OUTPUT):
    """Save mapping to JSON file."""

    print(f"💾 Saving to JSON: {output_path}")

    # Create lookup dictionaries
    output = {
        'metadata': {
            'created': datetime.now().isoformat(),
            'total_mappings': len(mappings),
            'source': 'hoopR uid field'
        },
        'mappings': mappings,
        'espn_to_hoopr': {m['espn_game_id']: m['hoopr_game_id'] for m in mappings},
        'hoopr_to_espn': {m['hoopr_game_id']: m['espn_game_id'] for m in mappings}
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Saved {len(mappings):,} mappings")
    print()


def save_to_rds(mappings: list):
    """Save mapping to RDS PostgreSQL database."""

    try:
        import psycopg2
        from dotenv import load_dotenv
    except ImportError:
        print("⚠️  psycopg2 or dotenv not installed - skipping RDS save")
        return

    # Load credentials
    load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', 5432),
        'sslmode': 'require'
    }

    print(f"🌐 Connecting to RDS: {DB_CONFIG['database']}...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✓ Connected")
    print()

    # Create mapping table
    print("📋 Creating game_id_mapping table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_id_mapping (
            espn_game_id TEXT PRIMARY KEY,
            hoopr_game_id TEXT NOT NULL,
            game_date DATE NOT NULL,
            home_team TEXT,
            away_team TEXT,
            uid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_game_mapping_hoopr
            ON game_id_mapping(hoopr_game_id);
        CREATE INDEX IF NOT EXISTS idx_game_mapping_date
            ON game_id_mapping(game_date);
    """)
    print("✓ Table created")
    print()

    # Insert mappings
    print(f"💾 Inserting {len(mappings):,} mappings...")

    for mapping in mappings:
        cursor.execute("""
            INSERT INTO game_id_mapping
                (espn_game_id, hoopr_game_id, game_date, home_team, away_team, uid)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (espn_game_id) DO UPDATE SET
                hoopr_game_id = EXCLUDED.hoopr_game_id,
                game_date = EXCLUDED.game_date,
                home_team = EXCLUDED.home_team,
                away_team = EXCLUDED.away_team,
                uid = EXCLUDED.uid;
        """, (
            mapping['espn_game_id'],
            mapping['hoopr_game_id'],
            mapping['game_date'],
            mapping['home_team'],
            mapping['away_team'],
            mapping['uid']
        ))

    conn.commit()
    print("✓ Mappings saved to RDS")
    print()

    cursor.close()
    conn.close()


def print_summary(mappings: list):
    """Print summary statistics."""

    print("=" * 70)
    print("MAPPING SUMMARY")
    print("=" * 70)
    print()

    print(f"Total mappings: {len(mappings):,}")
    print()

    # Date range
    dates = [m['game_date'] for m in mappings if m['game_date']]
    if dates:
        print(f"Date range: {min(dates)} to {max(dates)}")
        print()

    # Sample mappings
    print("Sample mappings:")
    print(f"{'ESPN ID':<15} {'hoopR ID':<15} {'Date':<12} {'Matchup':<40}")
    print("-" * 80)
    for mapping in mappings[:5]:
        matchup = f"{mapping['away_team']} @ {mapping['home_team']}"
        print(f"{mapping['espn_game_id']:<15} {mapping['hoopr_game_id']:<15} "
              f"{mapping['game_date']:<12} {matchup:<40}")

    print()
    print("=" * 70)


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Extract ESPN-to-hoopR game ID mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract to CSV (default)
  python scripts/mapping/extract_espn_hoopr_game_mapping.py

  # Extract to JSON
  python scripts/mapping/extract_espn_hoopr_game_mapping.py --output-format json

  # Save to RDS
  python scripts/mapping/extract_espn_hoopr_game_mapping.py --save-to-rds

  # Both CSV and JSON
  python scripts/mapping/extract_espn_hoopr_game_mapping.py --output-format both
        """
    )

    parser.add_argument(
        '--output-format',
        choices=['csv', 'json', 'both'],
        default='csv',
        help='Output format (default: csv)'
    )

    parser.add_argument(
        '--save-to-rds',
        action='store_true',
        help='Also save mapping to RDS PostgreSQL'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Extract mappings
    mappings = extract_mapping_from_hoopr()

    # Save to requested formats
    if args.output_format in ['csv', 'both']:
        save_to_csv(mappings)

    if args.output_format in ['json', 'both']:
        save_to_json(mappings)

    if args.save_to_rds:
        save_to_rds(mappings)

    # Print summary
    print_summary(mappings)

    print(f"✓ Mapping extraction complete!")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
