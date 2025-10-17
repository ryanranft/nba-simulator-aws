#!/usr/bin/env python3
"""
Load hoopR Data to RDS PostgreSQL

Bulk loads hoopR data from local SQLite database to RDS PostgreSQL:
1. play_by_play (13.1M events)
2. player_box (785K rows)
3. team_box (60K rows)
4. schedule (31K games)

Uses PostgreSQL COPY command for fast bulk loading (~3-4 hours).

Prerequisites:
    - hoopR local database exists (/tmp/hoopr_local.db)
    - Database credentials in nba-sim-credentials.env file
    - RDS connection established

Usage:
    python scripts/db/load_hoopr_to_rds.py
    python scripts/db/load_hoopr_to_rds.py --dry-run  # Test without loading

Execution time: 3-4 hours (13.1M rows)
Cost: ~$0.07 (one-time load)

Pattern: Local validation → RDS load (following ESPN model)
"""

import os
import sys
import sqlite3
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import argparse
import io

# Load environment variables from external credentials file
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"),
    "database": os.getenv("DB_NAME", "nba_simulator"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}

# Local SQLite database
LOCAL_DB = "/tmp/hoopr_local.db"

# Batch size for bulk loading
BATCH_SIZE = 100000  # 100K rows per batch


def check_prerequisites():
    """Check that local database exists."""
    print("Checking prerequisites...")

    if not Path(LOCAL_DB).exists():
        raise FileNotFoundError(
            f"ERROR: Local hoopR database not found: {LOCAL_DB}\n"
            f"Run: python scripts/db/create_local_hoopr_database.py first"
        )

    # Check database size
    db_size = Path(LOCAL_DB).stat().st_size / (1024**3)  # GB
    print(f"✓ Local database found: {LOCAL_DB}")
    print(f"  Size: {db_size:.2f} GB")
    print()


def create_hoopr_tables(pg_cursor):
    """Create hoopR tables in PostgreSQL matching SQLite schema."""
    print("=" * 70)
    print("CREATING HOOPR TABLES IN RDS")
    print("=" * 70)
    print()

    # Get schema from SQLite
    sqlite_conn = sqlite3.connect(LOCAL_DB)
    sqlite_cursor = sqlite_conn.cursor()

    # Get table schemas
    tables_to_create = ["play_by_play", "player_box", "team_box", "schedule"]

    for table in tables_to_create:
        print(f"Creating hoopr_{table}...")

        # Check if table already exists
        pg_cursor.execute(
            f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'hoopr_{table}'
            );
        """
        )
        exists = pg_cursor.fetchone()[0]

        if exists:
            print(f"  ⚠️  Table hoopr_{table} already exists")
            pg_cursor.execute(f"SELECT COUNT(*) FROM hoopr_{table};")
            count = pg_cursor.fetchone()[0]
            print(f"  Current rows: {count:,}")

            response = input(f"  Drop and recreate table? (yes/no): ").strip().lower()
            if response == "yes":
                print(f"  Dropping hoopr_{table}...")
                pg_cursor.execute(f"DROP TABLE hoopr_{table} CASCADE;")
            else:
                print(f"  Skipping hoopr_{table} creation")
                continue

        # Get column info from SQLite
        sqlite_cursor.execute(f"PRAGMA table_info({table});")
        columns = sqlite_cursor.fetchall()

        # Map SQLite types to PostgreSQL types
        type_mapping = {
            "INTEGER": "INTEGER",
            "TEXT": "TEXT",
            "REAL": "DOUBLE PRECISION",
            "BOOLEAN": "BOOLEAN",
            "DATE": "DATE",
            "TIMESTAMP": "TIMESTAMP",
        }

        # Build CREATE TABLE statement
        column_defs = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            pg_type = type_mapping.get(col_type, "TEXT")
            column_defs.append(f"{col_name} {pg_type}")

        create_sql = f"""
            CREATE TABLE hoopr_{table} (
                {', '.join(column_defs)}
            );
        """

        pg_cursor.execute(create_sql)
        print(f"  ✓ Created hoopr_{table} ({len(columns)} columns)")

    sqlite_cursor.close()
    sqlite_conn.close()
    print()


def load_table(sqlite_conn, pg_conn, pg_cursor, table_name, batch_size=BATCH_SIZE):
    """Load a table from SQLite to PostgreSQL using batched COPY."""
    print("=" * 70)
    print(f"LOADING: hoopr_{table_name}")
    print("=" * 70)

    sqlite_cursor = sqlite_conn.cursor()

    # Get row count
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_rows = sqlite_cursor.fetchone()[0]

    if total_rows == 0:
        print(f"  ⚠️  No data to load from {table_name}")
        return

    print(f"\nTotal rows to load: {total_rows:,}")
    print(f"Batch size: {batch_size:,}")
    print(
        f"Estimated time: {total_rows / batch_size / 10:.1f} minutes (at ~10 batches/min)"
    )
    print()

    # Get column names
    sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    column_list = ", ".join(columns)

    # Stream data in batches
    start_time = datetime.now()
    loaded_rows = 0
    batch_num = 0

    # Use server-side cursor for memory efficiency
    sqlite_cursor.execute(f"SELECT * FROM {table_name};")

    while True:
        batch = sqlite_cursor.fetchmany(batch_size)
        if not batch:
            break

        batch_num += 1

        # Create CSV in memory
        output = io.StringIO()
        for row in batch:
            # Convert row to CSV format
            csv_row = []
            for value in row:
                if value is None:
                    csv_row.append("")
                else:
                    # Escape special characters for CSV
                    value_str = (
                        str(value)
                        .replace("\\", "\\\\")
                        .replace("\n", "\\n")
                        .replace("\r", "\\r")
                        .replace("\t", "\\t")
                    )
                    csv_row.append(value_str)
            output.write("\t".join(csv_row) + "\n")

        output.seek(0)

        # Use COPY for bulk insert
        try:
            pg_cursor.copy_expert(
                f"""
                COPY hoopr_{table_name} ({column_list})
                FROM STDIN WITH (FORMAT TEXT, NULL '')
            """,
                output,
            )

            loaded_rows += len(batch)

            # Commit every 10 batches
            if batch_num % 10 == 0:
                pg_conn.commit()
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = loaded_rows / elapsed if elapsed > 0 else 0
                pct = loaded_rows / total_rows * 100
                eta = (total_rows - loaded_rows) / rate if rate > 0 else 0

                print(
                    f"  Progress: {loaded_rows:,}/{total_rows:,} ({pct:.1f}%) "
                    f"| Rate: {rate:.0f} rows/sec | ETA: {eta/60:.1f} min"
                )

        except Exception as e:
            print(f"\n  ❌ Error in batch {batch_num}: {e}")
            pg_conn.rollback()
            raise

    # Final commit
    pg_conn.commit()

    elapsed = (datetime.now() - start_time).total_seconds()
    rate = loaded_rows / elapsed if elapsed > 0 else 0

    print(f"\n✓ Loaded {loaded_rows:,} rows in {elapsed/60:.1f} minutes")
    print(f"  Rate: {rate:.0f} rows/second")

    # Verify load
    pg_cursor.execute(f"SELECT COUNT(*) FROM hoopr_{table_name};")
    pg_count = pg_cursor.fetchone()[0]

    if pg_count != total_rows:
        print(f"  ⚠️  WARNING: Row count mismatch!")
        print(f"    SQLite: {total_rows:,}")
        print(f"    PostgreSQL: {pg_count:,}")
    else:
        print(f"  ✓ Row count verified: {pg_count:,}")

    sqlite_cursor.close()
    print()


def create_indexes(pg_cursor):
    """Create indexes on hoopR tables for query performance."""
    print("=" * 70)
    print("CREATING INDEXES")
    print("=" * 70)
    print()

    indexes = [
        # play_by_play indexes
        ("idx_hoopr_pbp_game_id", "hoopr_play_by_play", "game_id"),
        ("idx_hoopr_pbp_game_date", "hoopr_play_by_play", "game_date"),
        # player_box indexes
        ("idx_hoopr_player_box_game_id", "hoopr_player_box", "game_id"),
        # team_box indexes
        ("idx_hoopr_team_box_game_id", "hoopr_team_box", "game_id"),
        # schedule indexes
        ("idx_hoopr_schedule_game_id", "hoopr_schedule", "game_id"),
        ("idx_hoopr_schedule_game_date", "hoopr_schedule", "game_date"),
    ]

    for idx_name, table, column in indexes:
        try:
            print(f"Creating {idx_name}...")
            pg_cursor.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON {table}({column});
            """
            )
            print(f"  ✓ {idx_name} created")
        except Exception as e:
            print(f"  ⚠️  Skipped {idx_name}: {e}")

    print("\n✓ Indexes created")
    print()


def print_summary(pg_cursor):
    """Print summary of loaded data."""
    print("=" * 70)
    print("LOAD SUMMARY")
    print("=" * 70)
    print()

    # Table row counts
    tables = ["play_by_play", "player_box", "team_box", "schedule"]

    print(f"{'Table':<25} {'Rows':<15}")
    print("-" * 40)

    for table in tables:
        pg_cursor.execute(f"SELECT COUNT(*) FROM hoopr_{table};")
        count = pg_cursor.fetchone()[0]
        print(f"hoopr_{table:<21} {count:>15,}")

    # Table sizes
    print()
    pg_cursor.execute(
        """
        SELECT
            table_name,
            pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS total_size,
            pg_size_pretty(pg_relation_size(table_name::regclass)) AS table_size,
            pg_size_pretty(pg_indexes_size(table_name::regclass)) AS indexes_size
        FROM information_schema.tables
        WHERE table_name LIKE 'hoopr_%'
        ORDER BY pg_total_relation_size(table_name::regclass) DESC;
    """
    )

    print(f"{'Table':<25} {'Total Size':<15} {'Table':<15} {'Indexes':<15}")
    print("-" * 70)
    for row in pg_cursor.fetchall():
        print(f"{row[0]:<25} {row[1]:<15} {row[2]:<15} {row[3]:<15}")

    # Date range
    print()
    pg_cursor.execute(
        """
        SELECT MIN(game_date), MAX(game_date)
        FROM hoopr_schedule
        WHERE game_date IS NOT NULL;
    """
    )
    min_date, max_date = pg_cursor.fetchone()
    print(f"Date range: {min_date} to {max_date}")

    # Seasons
    pg_cursor.execute(
        """
        SELECT COUNT(DISTINCT substr(game_date::TEXT, 1, 4))
        FROM hoopr_schedule
        WHERE game_date IS NOT NULL;
    """
    )
    season_count = pg_cursor.fetchone()[0]
    print(f"Seasons: {season_count} years")

    print()
    print("=" * 70)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Load hoopR data from local SQLite to RDS PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full load
  python scripts/db/load_hoopr_to_rds.py

  # Test without loading
  python scripts/db/load_hoopr_to_rds.py --dry-run

Next Steps:
  1. Create unified ESPN + hoopR view
  2. Run cross-source validation in RDS
  3. Update ML feature engineering pipeline
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test connection and show statistics without loading data",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("LOAD HOOPR DATA TO RDS POSTGRESQL")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No data will be loaded")
        print()

    # Check prerequisites
    check_prerequisites()

    # Validate credentials
    if not DB_CONFIG["user"] or not DB_CONFIG["password"]:
        print("ERROR: Database credentials not found in nba-sim-credentials.env")
        sys.exit(1)

    # Connect to databases
    print(f"Connecting to RDS: {DB_CONFIG['database']} at {DB_CONFIG['host']}...")
    try:
        pg_conn = psycopg2.connect(**DB_CONFIG)
        pg_conn.autocommit = False
        pg_cursor = pg_conn.cursor()
        print("✓ Connected to RDS")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect to RDS: {e}")
        sys.exit(1)

    print(f"Connecting to local SQLite: {LOCAL_DB}...")
    try:
        sqlite_conn = sqlite3.connect(LOCAL_DB)
        print("✓ Connected to local database")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect to local database: {e}")
        sys.exit(1)

    if args.dry_run:
        print("Dry run complete - connections successful!")
        pg_cursor.close()
        pg_conn.close()
        sqlite_conn.close()
        return

    overall_start = datetime.now()

    try:
        # Create tables
        create_hoopr_tables(pg_cursor)
        pg_conn.commit()
        print("✓ Tables created")
        print()

        # Load data
        tables_to_load = [
            ("schedule", 10000),  # 31K games - smaller batches
            ("team_box", 50000),  # 60K rows - medium batches
            ("player_box", 100000),  # 785K rows - large batches
            ("play_by_play", 100000),  # 13M rows - large batches
        ]

        for table, batch_size in tables_to_load:
            load_table(sqlite_conn, pg_conn, pg_cursor, table, batch_size)

        # Create indexes
        create_indexes(pg_cursor)
        pg_conn.commit()

        # Print summary
        print_summary(pg_cursor)

        overall_elapsed = (datetime.now() - overall_start).total_seconds()

        # Next steps
        print("=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print(
            "1. Create unified view: python scripts/db/create_unified_espn_hoopr_view.py"
        )
        print(
            "2. Cross-validate in RDS: python scripts/utils/compare_espn_hoopr_rds.py"
        )
        print("3. Update ML features: Update feature engineering to use hoopR data")
        print("4. Document results: Update DATA_CATALOG.md with RDS statistics")
        print("=" * 70)

        print(f"\n✓ hoopR data load complete!")
        print(f"Total time: {overall_elapsed/3600:.2f} hours")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\nERROR: {e}")
        pg_conn.rollback()
        print("Transaction rolled back")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        pg_cursor.close()
        pg_conn.close()
        sqlite_conn.close()
        print("\nDatabase connections closed")


if __name__ == "__main__":
    main()
