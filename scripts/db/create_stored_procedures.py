"""
Create Temporal Stored Procedures

Creates PostgreSQL stored procedures for temporal queries:
1. get_player_snapshot_at_time() - Get player stats at exact timestamp
2. calculate_player_age() - Calculate age to the second
3. get_game_state_at_time() - Get game situation at exact timestamp
4. get_events_in_time_range() - Get events within time range
5. aggregate_player_stats_in_period() - Aggregate stats between timestamps

Usage:
    python scripts/db/create_stored_procedures.py

Execution time: < 1 minute
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import sys

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

# SQL script path
SQL_FILE = Path(__file__).parent.parent.parent / 'sql' / 'temporal' / '03_create_stored_procedures.sql'


def check_prerequisites(cursor):
    """Check that temporal tables exist."""
    print("Checking prerequisites...")

    tables_to_check = ['temporal_events', 'player_snapshots', 'game_states', 'player_biographical']

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
    print()


def create_procedures(cursor):
    """Execute stored procedure creation SQL."""
    print("=" * 60)
    print("Creating Stored Procedures")
    print("=" * 60)
    print()

    print(f"Reading SQL from: {SQL_FILE}")

    if not SQL_FILE.exists():
        raise Exception(f"ERROR: SQL file not found: {SQL_FILE}")

    # Read and execute SQL
    with open(SQL_FILE, 'r') as f:
        sql = f.read()

    print("Executing SQL...")
    cursor.execute(sql)

    print("✓ Stored procedures created")
    print()


def validate_procedures(cursor):
    """Validate that all procedures were created."""
    print("Validating procedure creation...")

    expected_procedures = [
        'get_player_snapshot_at_time',
        'calculate_player_age',
        'get_game_state_at_time',
        'get_events_in_time_range',
        'aggregate_player_stats_in_period'
    ]

    cursor.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_name = ANY(%s)
        ORDER BY routine_name;
    """, (expected_procedures,))

    found_procedures = [row[0] for row in cursor.fetchall()]

    print(f"\nProcedures created:")
    for proc in found_procedures:
        print(f"  ✓ {proc}")

    if len(found_procedures) != len(expected_procedures):
        missing = set(expected_procedures) - set(found_procedures)
        raise Exception(f"ERROR: Missing procedures: {missing}")

    print(f"\n✓ All {len(expected_procedures)} procedures created successfully")
    print()


def print_usage_examples(cursor):
    """Print usage examples."""
    print("=" * 60)
    print("Usage Examples")
    print("=" * 60)
    print()

    print("1. Get player snapshot at exact time:")
    print("""
    SELECT *
    FROM get_player_snapshot_at_time(
        '977',  -- Kobe Bryant
        '2016-06-19 19:02:34-05:00'::TIMESTAMPTZ
    );
    """)

    print("\n2. Calculate player age:")
    print("""
    SELECT age_string
    FROM calculate_player_age(
        '977',
        '2016-06-19 19:02:34-05:00'::TIMESTAMPTZ,
        'second'
    );
    """)

    print("\n3. Get game state at specific time:")
    print("""
    SELECT quarter, game_clock_seconds, home_score, away_score
    FROM get_game_state_at_time(
        '0021500001',
        '2015-10-27 22:30:00-05:00'::TIMESTAMPTZ
    );
    """)

    print("\n4. Get events in time range:")
    print("""
    SELECT *
    FROM get_events_in_time_range(
        '2016-06-19 19:00:00-05:00'::TIMESTAMPTZ,
        '2016-06-19 19:02:00-05:00'::TIMESTAMPTZ,
        'made_shot'  -- Event type filter (optional)
    );
    """)

    print("\n5. Aggregate stats in custom period:")
    print("""
    SELECT *
    FROM aggregate_player_stats_in_period(
        '977',
        '2016-01-01 00:00:00-05:00'::TIMESTAMPTZ,
        '2016-06-30 23:59:59-05:00'::TIMESTAMPTZ
    );
    """)

    print()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Temporal Stored Procedures - Creation")
    print("=" * 60)
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

        # Create procedures
        create_procedures(cursor)

        # Validate
        validate_procedures(cursor)

        # Commit
        conn.commit()
        print("✓ Procedures committed")
        print()

        # Print usage examples
        print_usage_examples(cursor)

        # Next steps
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Run validation tests:  pytest tests/test_temporal_queries.py")
        print("2. Try a temporal query:  python scripts/queries/test_temporal_query.py")
        print("3. Generate snapshots:    python scripts/etl/generate_player_snapshots.py")
        print("=" * 60)
        print()

        print(f"✓ Stored procedures created successfully!")
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
