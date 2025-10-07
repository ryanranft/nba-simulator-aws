"""
Load Kaggle Data to RDS Temporal Tables

Bulk loads extracted Kaggle data into RDS PostgreSQL temporal tables:
1. player_biographical (3,632 players)
2. temporal_events (13.5M events)

Uses PostgreSQL COPY command for fast bulk loading.

Prerequisites:
    - Temporal tables created (run create_temporal_tables.py first)
    - Kaggle data extracted (run extract_kaggle_to_temporal.py first)
    - Database credentials in .env file

Usage:
    python scripts/db/load_kaggle_to_rds.py

Execution time: 30-60 minutes (13.5M rows)
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import csv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'nba_simulator'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', 5432)
}

# Data files
DATA_DIR = Path("/tmp/temporal_data_kaggle")
PLAYER_FILE = DATA_DIR / "player_biographical_clean.csv"
EVENTS_FILE = DATA_DIR / "temporal_events.csv"


def check_prerequisites(cursor):
    """Check that temporal tables exist."""
    print("Checking prerequisites...")

    tables_to_check = ['temporal_events', 'player_biographical']

    for table in tables_to_check:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{table}'
            );
        """)
        exists = cursor.fetchone()[0]

        if not exists:
            raise Exception(f"ERROR: Table '{table}' does not exist. Run create_temporal_tables.py first.")

    print("✓ All temporal tables exist")

    # Check data files
    if not PLAYER_FILE.exists():
        raise Exception(f"ERROR: Player data file not found: {PLAYER_FILE}")
    if not EVENTS_FILE.exists():
        raise Exception(f"ERROR: Events data file not found: {EVENTS_FILE}")

    print(f"✓ Data files found:")
    print(f"  - {PLAYER_FILE.name} ({PLAYER_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"  - {EVENTS_FILE.name} ({EVENTS_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
    print()


def load_player_biographical(cursor):
    """Load player biographical data using COPY command."""
    print("="*60)
    print("Loading Player Biographical Data")
    print("="*60)

    # Check if already loaded
    cursor.execute("SELECT COUNT(*) FROM player_biographical;")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"\n✓ Player biographical data already loaded ({existing_count:,} rows)")
        print("  Skipping player data load...")
        return

    # First, ensure players exist in the players table
    print("\nChecking player table...")
    cursor.execute("SELECT COUNT(*) FROM players;")
    player_count = cursor.fetchone()[0]
    print(f"  - Existing players: {player_count:,}")

    # Count rows in CSV
    with open(PLAYER_FILE, 'r') as f:
        row_count = sum(1 for line in f) - 1  # Exclude header

    print(f"\nLoading {row_count:,} players...")

    # Use COPY command for bulk insert
    # CSV columns: player_id, name, birth_date, birth_date_precision, height_inches, weight, position, college, country, draft_year, draft_round, draft_number, nba_debut_year, nba_retirement_year, data_source
    # Table columns: player_id, birth_date, birth_date_precision, height_inches, weight_pounds, draft_year, draft_round, draft_pick, college, data_source

    # Read CSV and map to table columns
    import csv
    import io

    with open(PLAYER_FILE, 'r') as f:
        csv_reader = csv.DictReader(f)
        output = io.StringIO()
        csv_writer = csv.writer(output)

        for row in csv_reader:
            # Helper function to convert float strings to int (or None)
            def to_int(val):
                if not val or val == '':
                    return None
                try:
                    return int(float(val))
                except:
                    return None

            # Map CSV columns to table columns
            csv_writer.writerow([
                row['player_id'] or None,                           # player_id
                row['birth_date'] or None,                          # birth_date
                row['birth_date_precision'] or None,                # birth_date_precision
                to_int(row['height_inches']),                       # height_inches
                to_int(row['weight']),                              # weight_pounds
                to_int(row['draft_year']),                          # draft_year
                to_int(row['draft_round']),                         # draft_round
                to_int(row['draft_number']),                        # draft_pick
                row['college'] or None,                             # college
                row['data_source'] or None                          # data_source
            ])

        output.seek(0)
        cursor.copy_expert("""
            COPY player_biographical (
                player_id, birth_date, birth_date_precision,
                height_inches, weight_pounds, draft_year, draft_round, draft_pick,
                college, data_source
            )
            FROM STDIN WITH (FORMAT CSV, NULL '')
        """, output)

    # Verify load
    cursor.execute("SELECT COUNT(*) FROM player_biographical;")
    loaded_count = cursor.fetchone()[0]

    print(f"✓ Loaded {loaded_count:,} players")

    # Show sample
    cursor.execute("""
        SELECT player_id, birth_date, height_inches, college
        FROM player_biographical
        ORDER BY birth_date
        LIMIT 5;
    """)

    print("\nSample (oldest players):")
    print(f"{'Player ID':<12} {'Birth Date':<12} {'Height':<10} {'College':<20}")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {str(row[1]):<12} {row[2] or 'N/A':<10} {row[3] or 'N/A':<20}")


def load_temporal_events(cursor, batch_size=100000):
    """Load temporal events using COPY command in batches."""
    print("\n" + "="*60)
    print("Loading Temporal Events (Play-by-Play)")
    print("="*60)

    # Count rows in CSV
    with open(EVENTS_FILE, 'r') as f:
        row_count = sum(1 for line in f) - 1  # Exclude header

    print(f"\nTotal events to load: {row_count:,}")
    print(f"Batch size: {batch_size:,}")
    print(f"Estimated time: {row_count / batch_size / 2:.1f} minutes (at ~2 batches/min)")
    print()

    # Load in single COPY command (PostgreSQL handles large files efficiently)
    print("Loading all events...")
    start_time = datetime.now()

    # Read CSV and fix JSON format (Python None → JSON null)
    import csv
    import io
    import re

    with open(EVENTS_FILE, 'r') as f:
        csv_reader = csv.DictReader(f)
        output = io.StringIO()
        csv_writer = csv.writer(output)

        for row in csv_reader:
            # Fix JSON: Replace Python None with JSON null and escape quotes
            event_data = row['event_data']
            if event_data:
                # Replace Python None with JSON null
                event_data = event_data.replace(': None', ': null')
                event_data = event_data.replace(':None', ':null')

                # The CSV already has escaped quotes as \" inside the JSON strings
                # But csv.DictReader unescapes them, so they need to be re-escaped
                # This is a complex fix - better to use json.loads/dumps
                import json
                try:
                    # Try to parse as Python dict literal
                    event_dict = eval(event_data)
                    # Convert to proper JSON
                    event_data = json.dumps(event_dict)
                except:
                    # If eval fails, leave as-is (will likely error on COPY)
                    pass

            csv_writer.writerow([
                row['game_id'],
                row['player_id'] or None,
                row['team_id'] or None,
                row['wall_clock_utc'],
                row['game_clock_seconds'] or None,
                row['quarter'],
                row['precision_level'],
                row['event_type'],
                event_data,
                row['data_source']
            ])

        output.seek(0)
        cursor.copy_expert("""
            COPY temporal_events (
                game_id, player_id, team_id, wall_clock_utc,
                game_clock_seconds, quarter, precision_level,
                event_type, event_data, data_source
            )
            FROM STDIN WITH (FORMAT CSV, NULL '')
        """, output)

    elapsed = (datetime.now() - start_time).total_seconds()

    # Verify load
    cursor.execute("SELECT COUNT(*) FROM temporal_events;")
    loaded_count = cursor.fetchone()[0]

    print(f"\n✓ Loaded {loaded_count:,} events in {elapsed:.1f} seconds")
    print(f"  Rate: {loaded_count/elapsed:.0f} rows/second")

    # Show sample
    cursor.execute("""
        SELECT game_id, quarter, wall_clock_utc, event_type
        FROM temporal_events
        ORDER BY wall_clock_utc
        LIMIT 5;
    """)

    print("\nSample (earliest events):")
    print(f"{'Game ID':<15} {'Quarter':<8} {'Timestamp':<20} {'Event Type':<15}")
    print("-" * 65)
    for row in cursor.fetchall():
        print(f"{row[0]:<15} {row[1]:<8} {str(row[2]):<20} {row[3]:<15}")

    # Check precision distribution
    print("\nPrecision level distribution:")
    cursor.execute("""
        SELECT precision_level, COUNT(*) AS count,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM temporal_events
        GROUP BY precision_level;
    """)

    print(f"{'Precision':<15} {'Count':<15} {'Percentage':<10}")
    print("-" * 40)
    for row in cursor.fetchall():
        print(f"{row[0]:<15} {row[1]:<15,} {row[2]:<10.1f}%")


def create_initial_indexes(cursor):
    """Create initial indexes for faster queries (BRIN indexes created later)."""
    print("\n" + "="*60)
    print("Creating Initial Indexes")
    print("="*60)

    print("\nNOTE: BRIN indexes will be created separately for optimal performance.")
    print("Creating essential B-tree indexes now for immediate querying...")

    # Basic indexes for lookups
    indexes = [
        ("idx_player_bio_player_id", "player_biographical", "player_id"),
        ("idx_temporal_events_game_id", "temporal_events", "game_id"),
        ("idx_temporal_events_player_id", "temporal_events", "player_id"),
    ]

    for idx_name, table, column in indexes:
        print(f"\n  Creating {idx_name}...")
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx_name}
            ON {table}({column});
        """)
        print(f"  ✓ {idx_name} created")

    print("\n✓ Initial indexes created")
    print("\nRun create_temporal_indexes.py next for BRIN time-series indexes")


def print_summary(cursor):
    """Print summary of loaded data."""
    print("\n" + "="*60)
    print("Load Summary")
    print("="*60)

    # Table sizes
    cursor.execute("""
        SELECT
            table_name,
            pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS total_size,
            pg_size_pretty(pg_relation_size(table_name::regclass)) AS table_size,
            pg_size_pretty(pg_indexes_size(table_name::regclass)) AS indexes_size
        FROM information_schema.tables
        WHERE table_name IN ('temporal_events', 'player_biographical')
        ORDER BY table_name;
    """)

    print(f"\n{'Table':<30} {'Total Size':<15} {'Table':<15} {'Indexes':<15}")
    print("-" * 75)
    for row in cursor.fetchall():
        print(f"{row[0]:<30} {row[1]:<15} {row[2]:<15} {row[3]:<15}")

    # Row counts
    print("\n" + "="*60)
    cursor.execute("SELECT COUNT(*) FROM player_biographical;")
    player_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM temporal_events;")
    event_count = cursor.fetchone()[0]

    print(f"Total players loaded: {player_count:,}")
    print(f"Total events loaded:  {event_count:,}")
    print("="*60)


def main():
    """Main execution function."""
    print("="*60)
    print("Load Kaggle Data to RDS Temporal Tables")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Validate credentials
    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        print("ERROR: Database credentials not found in .env file")
        sys.exit(1)

    # Connect to database
    print(f"Connecting to: {DB_CONFIG['database']} at {DB_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        sys.exit(1)

    try:
        # Check prerequisites
        check_prerequisites(cursor)

        # Load player biographical data
        load_player_biographical(cursor)

        # Commit player data
        conn.commit()
        print("\n✓ Player data committed")

        # Load temporal events
        load_temporal_events(cursor)

        # Commit events
        conn.commit()
        print("\n✓ Events committed")

        # Create initial indexes
        create_initial_indexes(cursor)
        conn.commit()
        print("\n✓ Indexes committed")

        # Print summary
        print_summary(cursor)

        # Next steps
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Create BRIN indexes:      python scripts/db/create_temporal_indexes.py")
        print("2. Create stored procedures: python scripts/db/create_stored_procedures.py")
        print("3. Run validation tests:     pytest tests/test_temporal_queries.py")
        print("4. Try a temporal query:     python scripts/queries/test_temporal_query.py")
        print("="*60)

        print(f"\n✓ Data load complete!")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        print("Transaction rolled back")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")


if __name__ == '__main__':
    main()
