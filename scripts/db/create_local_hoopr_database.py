#!/usr/bin/env python3
"""
Create Local hoopR SQLite Database

This script creates a local SQLite database from hoopR parquet files for fast
local validation before loading to RDS PostgreSQL.

Similar to create_local_espn_database.py pattern - validate locally first,
then load to cloud with confidence.

Input:  hoopR parquet files (6.2 GB, 4 data types)
Output: /tmp/hoopr_local.db (SQLite, ~500 MB)

Usage:
    python scripts/db/create_local_hoopr_database.py
    python scripts/db/create_local_hoopr_database.py --source-dir /custom/path

Benefits:
    - Fast local queries (milliseconds vs network latency)
    - $0 cost validation (no RDS connection needed)
    - Catch issues before expensive cloud operations
    - Can validate offline

Version: 1.0
Created: October 9, 2025
Pattern: Local validation before cloud load (established best practice)
"""

import argparse
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Default paths
DEFAULT_SOURCE_DIR = "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba"
DEFAULT_OUTPUT_DB = "/tmp/hoopr_local.db"


class HoopRDatabaseCreator:
    """Create local SQLite database from hoopR parquet files."""

    def __init__(self, source_dir: str, output_db: str):
        self.source_dir = Path(source_dir)
        self.output_db = output_db
        self.conn = None

        # Validate source directory exists
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

    def create_database(self):
        """Main entry point - create complete database."""
        print("\n" + "="*70)
        print("CREATE LOCAL HOOPR DATABASE")
        print("="*70)
        print(f"\nSource: {self.source_dir}")
        print(f"Output: {self.output_db}")

        # Remove existing database
        if Path(self.output_db).exists():
            print(f"\n⚠️  Removing existing database: {self.output_db}")
            Path(self.output_db).unlink()

        # Create connection
        self.conn = sqlite3.connect(self.output_db)
        print(f"✅ Created database: {self.output_db}")

        # Create tables
        self._create_tables()

        # Load data
        self._load_play_by_play()
        self._load_player_box()
        self._load_team_box()
        self._load_schedule()

        # Create indexes
        self._create_indexes()

        # Summary
        self._print_summary()

        # Close
        self.conn.close()
        print(f"\n✅ Database created successfully: {self.output_db}")

    def _create_tables(self):
        """Create database tables matching hoopR schema.

        Note: Tables are created automatically by pandas to_sql()
        to match exact parquet schema. This prevents column mismatch errors.
        """
        print("\n📋 Creating tables...")
        print("  ✅ Tables will be created automatically from parquet schema (63 columns each)")

    def _load_play_by_play(self):
        """Load play-by-play data from parquet files."""
        print("\n📊 Loading play-by-play data...")

        pbp_dir = self.source_dir / "load_nba_pbp" / "parquet"
        if not pbp_dir.exists():
            print(f"  ⚠️  Directory not found: {pbp_dir}")
            return

        # Find all parquet files
        parquet_files = sorted(pbp_dir.glob("*.parquet"))
        print(f"  Found {len(parquet_files)} parquet files")

        total_rows = 0
        for i, pf in enumerate(parquet_files, 1):
            df = pd.read_parquet(pf)
            # First file creates table, subsequent files append
            if_exists = 'replace' if i == 1 else 'append'
            df.to_sql('play_by_play', self.conn, if_exists=if_exists, index=False)
            total_rows += len(df)
            if i % 5 == 0 or i == len(parquet_files):
                print(f"  Progress: {i}/{len(parquet_files)} files ({total_rows:,} rows)")

        print(f"  ✅ Loaded {total_rows:,} play-by-play events")

    def _load_player_box(self):
        """Load player box score data from parquet files."""
        print("\n📊 Loading player box scores...")

        player_dir = self.source_dir / "load_nba_player_box" / "parquet"
        if not player_dir.exists():
            print(f"  ⚠️  Directory not found: {player_dir}")
            return

        parquet_files = sorted(player_dir.glob("*.parquet"))
        print(f"  Found {len(parquet_files)} parquet files")

        total_rows = 0
        for i, pf in enumerate(parquet_files, 1):
            df = pd.read_parquet(pf)
            # First file creates table, subsequent files append
            if_exists = 'replace' if i == 1 else 'append'
            df.to_sql('player_box', self.conn, if_exists=if_exists, index=False)
            total_rows += len(df)
            if i % 5 == 0 or i == len(parquet_files):
                print(f"  Progress: {i}/{len(parquet_files)} files ({total_rows:,} rows)")

        print(f"  ✅ Loaded {total_rows:,} player box scores")

    def _load_team_box(self):
        """Load team box score data from parquet files."""
        print("\n📊 Loading team box scores...")

        team_dir = self.source_dir / "load_nba_team_box" / "parquet"
        if not team_dir.exists():
            print(f"  ⚠️  Directory not found: {team_dir}")
            return

        parquet_files = sorted(team_dir.glob("*.parquet"))
        print(f"  Found {len(parquet_files)} parquet files")

        total_rows = 0
        for i, pf in enumerate(parquet_files, 1):
            df = pd.read_parquet(pf)
            # First file creates table, subsequent files append
            if_exists = 'replace' if i == 1 else 'append'
            df.to_sql('team_box', self.conn, if_exists=if_exists, index=False)
            total_rows += len(df)
            if i % 5 == 0 or i == len(parquet_files):
                print(f"  Progress: {i}/{len(parquet_files)} files ({total_rows:,} rows)")

        print(f"  ✅ Loaded {total_rows:,} team box scores")

    def _load_schedule(self):
        """Load schedule data from parquet files."""
        print("\n📊 Loading schedule data...")

        schedule_dir = self.source_dir / "load_nba_schedule" / "parquet"
        if not schedule_dir.exists():
            print(f"  ⚠️  Directory not found: {schedule_dir}")
            return

        parquet_files = sorted(schedule_dir.glob("*.parquet"))
        print(f"  Found {len(parquet_files)} parquet files")

        total_rows = 0
        for i, pf in enumerate(parquet_files, 1):
            df = pd.read_parquet(pf)
            # First file creates table, subsequent files append
            if_exists = 'replace' if i == 1 else 'append'
            df.to_sql('schedule', self.conn, if_exists=if_exists, index=False)
            total_rows += len(df)
            if i % 5 == 0 or i == len(parquet_files):
                print(f"  Progress: {i}/{len(parquet_files)} files ({total_rows:,} rows)")

        print(f"  ✅ Loaded {total_rows:,} games")

    def _create_indexes(self):
        """Create indexes for common queries."""
        print("\n🔍 Creating indexes...")

        # Only create indexes for columns we know exist in hoopR schema
        indexes = [
            ("idx_pbp_game_id", "play_by_play", "game_id"),
            ("idx_pbp_game_date", "play_by_play", "game_date"),
            ("idx_player_box_game_id", "player_box", "game_id"),
            ("idx_team_box_game_id", "team_box", "game_id"),
            ("idx_schedule_game_id", "schedule", "game_id"),
            ("idx_schedule_game_date", "schedule", "game_date"),
        ]

        for idx_name, table, column in indexes:
            try:
                self.conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
                print(f"  ✅ Created index: {idx_name}")
            except Exception as e:
                print(f"  ⚠️  Skipped index {idx_name}: {e}")

    def _print_summary(self):
        """Print database summary statistics."""
        print("\n" + "="*70)
        print("DATABASE SUMMARY")
        print("="*70)

        # Table counts
        cursor = self.conn.cursor()

        # Play-by-play
        cursor.execute("SELECT COUNT(*) FROM play_by_play")
        pbp_count = cursor.fetchone()[0]

        # Player box
        cursor.execute("SELECT COUNT(*) FROM player_box")
        player_count = cursor.fetchone()[0]

        # Team box
        cursor.execute("SELECT COUNT(*) FROM team_box")
        team_count = cursor.fetchone()[0]

        # Schedule
        cursor.execute("SELECT COUNT(*) FROM schedule")
        schedule_count = cursor.fetchone()[0]

        # Date range (use game_date which exists in hoopR schema)
        cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM schedule")
        min_date, max_date = cursor.fetchone()

        # Seasons (extract year from game_date)
        cursor.execute("""
            SELECT COUNT(DISTINCT substr(game_date, 1, 4))
            FROM schedule
            WHERE game_date IS NOT NULL
        """)
        season_count = cursor.fetchone()[0]

        print(f"\n📊 Data Summary:")
        print(f"  Play-by-play events:  {pbp_count:,}")
        print(f"  Player box scores:    {player_count:,}")
        print(f"  Team box scores:      {team_count:,}")
        print(f"  Schedule games:       {schedule_count:,}")
        print(f"\n📅 Coverage:")
        print(f"  Date range:           {min_date} to {max_date}")
        print(f"  Seasons:              {season_count} years")

        # Database size
        db_size = Path(self.output_db).stat().st_size / (1024**2)  # MB
        print(f"\n💾 Database:")
        print(f"  Size:                 {db_size:.1f} MB")
        print(f"  Location:             {self.output_db}")

        cursor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create local hoopR SQLite database from parquet files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default paths
  python scripts/db/create_local_hoopr_database.py

  # Custom source directory
  python scripts/db/create_local_hoopr_database.py --source-dir /custom/path

Next Steps:
  1. Validate ESPN ↔ hoopR: python scripts/utils/compare_espn_hoopr_local.py
  2. Load to RDS (if validation passes): python scripts/db/load_hoopr_to_rds.py

Pattern:
  Local validation BEFORE cloud operations (saves time & cost!)
        """
    )

    parser.add_argument(
        '--source-dir',
        default=DEFAULT_SOURCE_DIR,
        help=f'hoopR parquet files directory (default: {DEFAULT_SOURCE_DIR})'
    )

    parser.add_argument(
        '--output-db',
        default=DEFAULT_OUTPUT_DB,
        help=f'Output SQLite database path (default: {DEFAULT_OUTPUT_DB})'
    )

    args = parser.parse_args()

    try:
        creator = HoopRDatabaseCreator(
            source_dir=args.source_dir,
            output_db=args.output_db
        )
        creator.create_database()

        print("\n" + "="*70)
        print("✅ SUCCESS - Ready for local validation!")
        print("="*70)
        print("\nNext step:")
        print("  python scripts/utils/compare_espn_hoopr_local.py")
        print("\n" + "="*70)

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
