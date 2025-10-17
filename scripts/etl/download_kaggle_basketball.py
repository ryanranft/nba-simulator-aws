"""
Download Kaggle Basketball Database

Downloads the comprehensive Kaggle basketball dataset which includes:
- Player biographical data (birth dates, physical attributes)
- Game data (1946-2024)
- Play-by-play data
- Team and player statistics

This provides a fast baseline for temporal data, which we'll later
cross-reference with NBA Stats API and ESPN data for verification.

Dataset: https://www.kaggle.com/datasets/wyattowalsh/basketball

Prerequisites:
    - Kaggle API credentials configured (~/.kaggle/kaggle.json)
    - See docs/KAGGLE_API_SETUP.md for setup instructions

Usage:
    python scripts/etl/download_kaggle_basketball.py

Download time: 2-5 minutes (dataset is ~2-5 GB)
"""

import os
import sys
import subprocess
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime

# Configuration
KAGGLE_DATASET = "wyattowalsh/basketball"
DOWNLOAD_DIR = Path("/tmp/kaggle_basketball")
EXTRACT_DIR = DOWNLOAD_DIR / "extracted"
OUTPUT_DIR = Path("/tmp/temporal_data_kaggle")

# Kaggle credentials check
KAGGLE_CONFIG = Path.home() / ".kaggle" / "kaggle.json"


def check_kaggle_credentials():
    """Check if Kaggle API credentials are configured."""
    print("Checking Kaggle API credentials...")

    if not KAGGLE_CONFIG.exists():
        print("\n" + "=" * 60)
        print("ERROR: Kaggle API credentials not found")
        print("=" * 60)
        print("\nPlease set up Kaggle API credentials:")
        print("1. Go to https://www.kaggle.com/[your-username]/account")
        print("2. Click 'Create New API Token'")
        print("3. Save kaggle.json to ~/.kaggle/")
        print("4. Run: chmod 600 ~/.kaggle/kaggle.json")
        print("\nSee docs/KAGGLE_API_SETUP.md for detailed instructions")
        print("=" * 60)
        return False

    # Check permissions
    stat = KAGGLE_CONFIG.stat()
    if stat.st_mode & 0o077:
        print(f"\nWARNING: {KAGGLE_CONFIG} has insecure permissions")
        print("Run: chmod 600 ~/.kaggle/kaggle.json")
        return False

    print("✓ Kaggle credentials found and secure")
    return True


def download_dataset():
    """Download Kaggle basketball dataset."""
    print(f"\nDownloading Kaggle dataset: {KAGGLE_DATASET}")
    print(f"Destination: {DOWNLOAD_DIR}")

    # Create download directory
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Download using kaggle CLI
    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        KAGGLE_DATASET,
        "-p",
        str(DOWNLOAD_DIR),
        "--unzip",
    ]

    print(f"\nExecuting: {' '.join(cmd)}")
    print("This may take 2-5 minutes...\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ Download complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Download failed")
        print(f"Error output: {e.stderr}")
        return False


def find_database_file():
    """Find the SQLite database file in download directory."""
    print("\nSearching for SQLite database file...")

    # Common patterns for the database file
    patterns = ["*.sqlite", "*.db", "*.sqlite3"]

    for pattern in patterns:
        matches = list(DOWNLOAD_DIR.rglob(pattern))
        if matches:
            db_path = matches[0]
            print(f"✓ Found database: {db_path}")
            return db_path

    print("ERROR: Could not find SQLite database file")
    print(f"Contents of {DOWNLOAD_DIR}:")
    for item in DOWNLOAD_DIR.rglob("*"):
        if item.is_file():
            print(f"  - {item}")
    return None


def extract_player_biographical(db_path):
    """Extract player biographical data (birth dates, etc.)."""
    print("\nExtracting player biographical data...")

    conn = sqlite3.connect(db_path)

    # Query player data (adjust table/column names based on actual schema)
    # Common table names: player, players, common_player_info

    # Try different possible table names
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Available tables: {', '.join(tables)}")

    # Find player table
    player_table = None
    for table in tables:
        if "player" in table.lower():
            player_table = table
            break

    if not player_table:
        print("WARNING: Could not find player table")
        return None

    print(f"Using table: {player_table}")

    # Get table schema
    cursor.execute(f"PRAGMA table_info({player_table})")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Available columns: {', '.join(columns)}")

    # Extract player data
    query = f"SELECT * FROM {player_table} LIMIT 10"
    df = pd.read_sql_query(query, conn)

    print(f"\nSample data:")
    print(df.head())

    # Save to CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "player_biographical.csv"

    # Full extraction
    query = f"SELECT * FROM {player_table}"
    df_full = pd.read_sql_query(query, conn)
    df_full.to_csv(output_file, index=False)

    print(f"\n✓ Extracted {len(df_full):,} players to {output_file}")

    conn.close()
    return output_file


def extract_game_data(db_path):
    """Extract game data with timestamps."""
    print("\nExtracting game data...")

    conn = sqlite3.connect(db_path)

    # Find game table
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    game_table = None
    for table in tables:
        if "game" in table.lower() and "player" not in table.lower():
            game_table = table
            break

    if not game_table:
        print("WARNING: Could not find game table")
        return None

    print(f"Using table: {game_table}")

    # Get sample
    query = f"SELECT * FROM {game_table} LIMIT 5"
    df = pd.read_sql_query(query, conn)
    print(f"\nSample data:")
    print(df.head())

    # Full extraction
    query = f"SELECT * FROM {game_table}"
    df_full = pd.read_sql_query(query, conn)

    output_file = OUTPUT_DIR / "games.csv"
    df_full.to_csv(output_file, index=False)

    print(f"\n✓ Extracted {len(df_full):,} games to {output_file}")

    conn.close()
    return output_file


def print_summary(db_path):
    """Print summary of Kaggle database contents."""
    print("\n" + "=" * 60)
    print("Kaggle Database Summary")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"\nTotal tables: {len(tables)}")
    print("\nTable name                        Row Count")
    print("-" * 60)

    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:<35} {count:>10,}")

    conn.close()
    print("=" * 60)


def main():
    """Main execution function."""
    print("=" * 60)
    print("Kaggle Basketball Database Download")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check credentials
    if not check_kaggle_credentials():
        sys.exit(1)

    # Download dataset
    if not download_dataset():
        sys.exit(1)

    # Find database file
    db_path = find_database_file()
    if not db_path:
        sys.exit(1)

    # Print database summary
    print_summary(db_path)

    # Extract data
    player_file = extract_player_biographical(db_path)
    game_file = extract_game_data(db_path)

    # Summary
    print("\n" + "=" * 60)
    print("Extraction Complete")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nExtracted files:")
    if player_file:
        print(
            f"  - {player_file.name} ({player_file.stat().st_size / 1024 / 1024:.1f} MB)"
        )
    if game_file:
        print(f"  - {game_file.name} ({game_file.stat().st_size / 1024 / 1024:.1f} MB)")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Inspect extracted CSV files")
    print("2. Map Kaggle columns to temporal table schemas")
    print("3. Run: python scripts/etl/load_kaggle_to_temporal.py")
    print("=" * 60)

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
