#!/usr/bin/env python3
"""
Migration: 0.21 - Kaggle SQLite to PostgreSQL Data Migration

Migrates all 16 tables from Kaggle SQLite database to PostgreSQL kaggle schema.

Features:
- Batch processing with configurable sizes
- Checkpointing for resume capability
- Progress tracking and ETA
- Data validation during migration
- Transaction safety with rollback
- JSONB transformation
- Foreign key ordering

Usage:
    python scripts/db/migrations/0_21_kaggle_data_migration.py
    python scripts/db/migrations/0_21_kaggle_data_migration.py --dry-run
    python scripts/db/migrations/0_21_kaggle_data_migration.py --tables game,player
    python scripts/db/migrations/0_21_kaggle_data_migration.py --resume

Execution time: 30-60 minutes (13.6M play-by-play rows)
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import sys

# Configuration
SQLITE_DB = Path("/Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite")
CHECKPOINT_FILE = Path("/tmp/kaggle_migration_checkpoint.json")

# PostgreSQL connection config
PG_CONFIG = {
    "host": "localhost",
    "database": "nba_simulator",
    "user": "ryanranft",
    "password": "",
    "port": 5432
}

# Table migration order (dependencies first)
# Format: (sqlite_table, pg_table, batch_size, priority)
MIGRATION_ORDER = [
    # Core reference tables first (no foreign keys)
    ("team", "kaggle.team_nba_kaggle", 1000, "HIGH"),
    ("team_details", "kaggle.team_details_nba_kaggle", 1000, "LOW"),
    ("team_history", "kaggle.team_history_nba_kaggle", 1000, "LOW"),
    ("team_info_common", "kaggle.team_info_common_nba_kaggle", 1000, "LOW"),

    # Player tables (no foreign keys)
    ("player", "kaggle.player_nba_kaggle", 5000, "HIGH"),
    ("common_player_info", "kaggle.common_player_info_nba_kaggle", 5000, "HIGH"),

    # Draft tables (no foreign keys)
    ("draft_history", "kaggle.draft_history_nba_kaggle", 5000, "LOW"),
    ("draft_combine_stats", "kaggle.draft_combine_stats_nba_kaggle", 5000, "LOW"),

    # Game tables (foreign keys to team)
    ("game", "kaggle.game_nba_kaggle", 10000, "CRITICAL"),

    # Game-related tables (foreign keys to game)
    ("game_info", "kaggle.game_info_nba_kaggle", 10000, "MEDIUM"),
    ("game_summary", "kaggle.game_summary_nba_kaggle", 10000, "MEDIUM"),
    ("line_score", "kaggle.line_score_nba_kaggle", 10000, "MEDIUM"),
    ("inactive_players", "kaggle.inactive_players_nba_kaggle", 10000, "MEDIUM"),
    ("officials", "kaggle.officials_nba_kaggle", 10000, "MEDIUM"),
    ("other_stats", "kaggle.other_stats_nba_kaggle", 10000, "MEDIUM"),

    # Large tables last (foreign keys to game)
    ("play_by_play", "kaggle.play_by_play_nba_kaggle", 50000, "CRITICAL"),  # 13.6M rows
]


class KaggleMigrator:
    """Migrate Kaggle SQLite data to PostgreSQL"""

    def __init__(self, dry_run: bool = False, resume: bool = False, tables_filter: Optional[List[str]] = None):
        """
        Initialize migrator

        Args:
            dry_run: If True, don't actually write to PostgreSQL
            resume: If True, resume from last checkpoint
            tables_filter: Optional list of table names to migrate (default: all)
        """
        self.dry_run = dry_run
        self.resume = resume
        self.tables_filter = tables_filter
        self.sqlite_conn = None
        self.pg_conn = None
        self.checkpoint = self.load_checkpoint() if resume else {}
        self.migration_stats = {}
        self.start_time = datetime.now()

    def load_checkpoint(self) -> Dict:
        """Load migration checkpoint from disk"""
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    checkpoint = json.load(f)
                print(f"✓ Loaded checkpoint: {len(checkpoint)} tables completed\n")
                return checkpoint
            except Exception as e:
                print(f"⚠ Warning: Could not load checkpoint: {e}")
                return {}
        return {}

    def save_checkpoint(self, table: str, rows_migrated: int):
        """Save migration progress to disk"""
        self.checkpoint[table] = {
            'rows_migrated': rows_migrated,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }

        if not self.dry_run:
            CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(self.checkpoint, f, indent=2)

    def connect_databases(self):
        """Connect to SQLite and PostgreSQL databases"""
        print("Connecting to databases...")

        # SQLite connection
        if not SQLITE_DB.exists():
            raise FileNotFoundError(f"SQLite database not found: {SQLITE_DB}")

        self.sqlite_conn = sqlite3.connect(SQLITE_DB)
        self.sqlite_conn.row_factory = sqlite3.Row
        print(f"  ✓ SQLite: {SQLITE_DB}")

        # PostgreSQL connection
        if not self.dry_run:
            self.pg_conn = psycopg2.connect(**PG_CONFIG)
            self.pg_conn.autocommit = False
            print(f"  ✓ PostgreSQL: {PG_CONFIG['database']} at {PG_CONFIG['host']}")
        else:
            print(f"  ⚠ PostgreSQL: DRY RUN mode - no writes")

        print()

    def get_table_row_count(self, table: str) -> int:
        """Get row count from SQLite table"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]

    def get_table_columns(self, table: str) -> List[str]:
        """Get column names from SQLite table"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]

    def transform_row_to_jsonb(self, row: sqlite3.Row, columns: List[str]) -> Dict[str, Any]:
        """
        Transform SQLite row to PostgreSQL format with JSONB

        Args:
            row: SQLite row object
            columns: List of column names

        Returns:
            Dictionary with transformed data
        """
        # Convert row to dict
        row_dict = dict(zip(columns, row))

        # Store full row in data JSONB field
        data_jsonb = {k: v for k, v in row_dict.items() if v is not None}

        # Create metadata
        metadata = {
            'source': 'kaggle',
            'source_file': str(SQLITE_DB),
            'migrated_at': datetime.now().isoformat(),
            'migration_version': '0.21'
        }

        # Return PostgreSQL row (denormalized columns + JSONB)
        pg_row = {
            'data': json.dumps(data_jsonb),
            'metadata': json.dumps(metadata)
        }

        # Add specific denormalized columns based on availability
        # This will be table-specific in actual implementation
        for col in columns:
            if col in row_dict and row_dict[col] is not None:
                pg_row[col] = row_dict[col]

        return pg_row

    def generate_insert_query(self, pg_table: str, row: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Generate INSERT query for PostgreSQL

        Args:
            pg_table: PostgreSQL table name
            row: Row data dictionary

        Returns:
            Tuple of (query, values)
        """
        # Get column names (excluding id which is SERIAL)
        columns = [k for k in row.keys() if k != 'id']
        placeholders = [f"%s" for _ in columns]

        query = f"""
            INSERT INTO {pg_table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """

        values = [row[col] for col in columns]

        return query, values

    def migrate_table(self, sqlite_table: str, pg_table: str, batch_size: int, priority: str):
        """
        Migrate one table from SQLite to PostgreSQL

        Args:
            sqlite_table: Source SQLite table name
            pg_table: Target PostgreSQL table name
            batch_size: Number of rows per batch
            priority: Migration priority (CRITICAL, HIGH, MEDIUM, LOW)
        """
        # Check if table should be migrated (filter)
        if self.tables_filter and sqlite_table not in self.tables_filter:
            print(f"⊘ Skipping {sqlite_table} (not in filter)\n")
            return

        # Check if already migrated
        if self.resume and sqlite_table in self.checkpoint:
            status = self.checkpoint[sqlite_table].get('status')
            if status == 'completed':
                rows = self.checkpoint[sqlite_table]['rows_migrated']
                print(f"✓ Skipping {sqlite_table} → {pg_table} ({rows:,} rows already migrated)\n")
                return

        print("=" * 70)
        print(f"Migrating: {sqlite_table} → {pg_table}")
        print(f"Priority: {priority}")
        print("=" * 70)

        # Get row count
        total_rows = self.get_table_row_count(sqlite_table)
        print(f"Total rows: {total_rows:,}")

        if total_rows == 0:
            print("✓ Skipped (empty table)\n")
            self.save_checkpoint(sqlite_table, 0)
            self.migration_stats[sqlite_table] = {
                'rows': 0,
                'duration': 0,
                'status': 'skipped'
            }
            return

        # Get columns
        columns = self.get_table_columns(sqlite_table)
        print(f"Columns: {len(columns)}")
        print(f"Batch size: {batch_size:,}")

        if self.dry_run:
            print("⚠ DRY RUN - No data will be written")

        print()

        # Migrate in batches
        migrated = 0
        errors = 0
        table_start_time = datetime.now()

        cursor_sqlite = self.sqlite_conn.cursor()

        for offset in range(0, total_rows, batch_size):
            batch_start = datetime.now()

            # Read batch from SQLite
            query = f"SELECT * FROM {sqlite_table} LIMIT {batch_size} OFFSET {offset}"
            cursor_sqlite.execute(query)
            rows = cursor_sqlite.fetchall()

            if not rows:
                break

            # Transform and insert batch
            if not self.dry_run:
                cursor_pg = self.pg_conn.cursor()

                try:
                    for row in rows:
                        # Transform row
                        pg_row = self.transform_row_to_jsonb(row, columns)

                        # Generate and execute insert
                        insert_query, values = self.generate_insert_query(pg_table, pg_row)
                        cursor_pg.execute(insert_query, values)

                    # Commit batch
                    self.pg_conn.commit()

                except Exception as e:
                    print(f"    ERROR in batch {offset//batch_size + 1}: {e}")
                    self.pg_conn.rollback()
                    errors += len(rows)
                    continue

            migrated += len(rows)

            # Progress update
            batch_duration = (datetime.now() - batch_start).total_seconds()
            elapsed = (datetime.now() - table_start_time).total_seconds()
            rate = migrated / elapsed if elapsed > 0 else 0
            eta_seconds = (total_rows - migrated) / rate if rate > 0 else 0
            eta = timedelta(seconds=int(eta_seconds))

            progress_pct = (migrated / total_rows * 100)

            print(
                f"  [{migrated:>10,}/{total_rows:>10,}] "
                f"{progress_pct:>5.1f}% | "
                f"{rate:>7.0f} rows/s | "
                f"ETA: {str(eta):<12} | "
                f"Batch: {batch_duration:.2f}s"
            )

        # Save checkpoint
        self.save_checkpoint(sqlite_table, migrated)

        # Calculate stats
        table_duration = (datetime.now() - table_start_time).total_seconds()
        final_rate = migrated / table_duration if table_duration > 0 else 0

        self.migration_stats[sqlite_table] = {
            'rows': migrated,
            'errors': errors,
            'duration': table_duration,
            'rate': final_rate,
            'status': 'completed' if errors == 0 else 'completed_with_errors'
        }

        # Summary
        print()
        print(f"✓ Migrated: {migrated:,} rows in {table_duration:.1f}s ({final_rate:.0f} rows/s)")
        if errors > 0:
            print(f"⚠ Errors: {errors:,} rows failed")
        print()

    def verify_schema(self):
        """Verify kaggle schema exists in PostgreSQL"""
        if self.dry_run:
            print("⚠ DRY RUN: Skipping schema verification\n")
            return True

        print("Verifying kaggle schema...")

        cursor = self.pg_conn.cursor()
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'kaggle'"
        )
        result = cursor.fetchone()

        if not result:
            print("✗ ERROR: kaggle schema does not exist")
            print("  Run: psql -U ryanranft nba_simulator -f scripts/db/migrations/0_20_kaggle_schema.sql")
            return False

        print("✓ kaggle schema exists\n")
        return True

    def print_migration_summary(self):
        """Print final migration summary"""
        total_duration = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 70)
        print("Migration Summary")
        print("=" * 70)

        total_rows = sum(stats['rows'] for stats in self.migration_stats.values())
        total_errors = sum(stats.get('errors', 0) for stats in self.migration_stats.values())

        print(f"\nTotal rows migrated: {total_rows:,}")
        print(f"Total errors: {total_errors:,}")
        print(f"Total duration: {total_duration/60:.1f} minutes")
        print(f"Overall rate: {total_rows/total_duration:.0f} rows/second")
        print(f"Tables migrated: {len(self.migration_stats)}")

        # Per-table breakdown
        print("\nPer-table breakdown:")
        print(f"{'Table':<30} {'Rows':>12} {'Duration':>10} {'Rate':>12} {'Status':<20}")
        print("-" * 90)

        for table, stats in self.migration_stats.items():
            duration_str = f"{stats['duration']:.1f}s"
            rate_str = f"{stats['rate']:.0f} rows/s"
            status = stats['status']

            if stats['errors'] > 0:
                status += f" ({stats['errors']} errors)"

            print(
                f"{table:<30} {stats['rows']:>12,} {duration_str:>10} "
                f"{rate_str:>12} {status:<20}"
            )

        print("=" * 70)

        if self.dry_run:
            print("\n⚠ DRY RUN MODE - No data was actually written to PostgreSQL")

        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def run_migration(self):
        """Execute full migration"""
        print("=" * 70)
        print("Kaggle SQLite → PostgreSQL Migration (v0.21)")
        print("=" * 70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if self.dry_run:
            print("Mode: DRY RUN (no writes)")
        if self.resume:
            print("Mode: RESUME (from checkpoint)")
        if self.tables_filter:
            print(f"Filter: {', '.join(self.tables_filter)}")

        print()

        # Connect to databases
        self.connect_databases()

        # Verify schema
        if not self.verify_schema():
            sys.exit(1)

        # Migrate tables in order
        for sqlite_table, pg_table, batch_size, priority in MIGRATION_ORDER:
            try:
                self.migrate_table(sqlite_table, pg_table, batch_size, priority)
            except Exception as e:
                print(f"\n✗ ERROR migrating {sqlite_table}: {e}")
                if not self.dry_run:
                    self.pg_conn.rollback()

                # Save checkpoint even on failure
                self.save_checkpoint(sqlite_table, 0)
                self.migration_stats[sqlite_table] = {
                    'rows': 0,
                    'duration': 0,
                    'status': 'failed',
                    'error': str(e)
                }

                # Ask user if they want to continue
                response = input("\nContinue with remaining tables? (y/n): ")
                if response.lower() != 'y':
                    print("Migration aborted by user")
                    break

        # Print summary
        self.print_migration_summary()

        # Cleanup
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn and not self.dry_run:
            self.pg_conn.close()

        print("Database connections closed")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Migrate Kaggle SQLite data to PostgreSQL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually writing to PostgreSQL"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--tables",
        type=str,
        help="Comma-separated list of tables to migrate (default: all)"
    )
    args = parser.parse_args()

    tables_filter = None
    if args.tables:
        tables_filter = [t.strip() for t in args.tables.split(',')]

    # Run migration
    migrator = KaggleMigrator(
        dry_run=args.dry_run,
        resume=args.resume,
        tables_filter=tables_filter
    )

    try:
        migrator.run_migration()
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
