"""
Create Temporal Database Tables

This script creates the 4 core temporal tables in RDS PostgreSQL:
1. temporal_events (500M+ rows capacity)
2. player_snapshots (50M+ rows capacity)
3. game_states (10M+ rows capacity)
4. player_biographical (5K+ rows capacity)

Usage:
    python scripts/db/create_temporal_tables.py

Prerequisites:
    - RDS PostgreSQL database running
    - players and games tables exist
    - Database credentials in .env file

Execution time: 2-5 minutes
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import sys

# Load environment variables from external credentials file
load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'nba_simulator'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', 5432),
    'sslmode': 'require'
}

# SQL scripts directory
SQL_DIR = Path(__file__).parent.parent.parent / 'sql' / 'temporal'

# Table creation scripts (in order)
TABLE_SCRIPTS = [
    '01_create_temporal_events.sql',
    '01_create_player_snapshots.sql',
    '01_create_game_states.sql',
    '01_create_player_biographical.sql'
]


def check_prerequisites(cursor):
    """Check that prerequisite tables exist."""
    print("Checking prerequisites...")

    # Check for players table
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'players'
        );
    """)
    players_exists = cursor.fetchone()[0]

    # Check for games table
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'games'
        );
    """)
    games_exists = cursor.fetchone()[0]

    if not players_exists:
        raise Exception("ERROR: 'players' table does not exist. Run Phase 3 table creation first.")

    if not games_exists:
        raise Exception("ERROR: 'games' table does not exist. Run Phase 3 table creation first.")

    print("✓ Prerequisites check: PASSED")
    print(f"  - players table exists: {players_exists}")
    print(f"  - games table exists: {games_exists}")
    print()


def create_table(cursor, script_path):
    """Execute a table creation script."""
    table_name = script_path.stem.replace('01_create_', '')

    print(f"  Creating {table_name}...")

    # Read SQL script
    with open(script_path, 'r') as f:
        sql = f.read()

    # Execute script
    cursor.execute(sql)

    print(f"  ✓ {table_name} created")


def validate_tables(cursor):
    """Validate that all temporal tables were created."""
    print("\nValidating table creation...")

    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name IN ('temporal_events', 'player_snapshots', 'game_states', 'player_biographical');
    """)

    table_count = cursor.fetchone()[0]

    if table_count != 4:
        raise Exception(f"ERROR: Expected 4 temporal tables, found {table_count}")

    print("✓ Table validation: PASSED")
    print("  - All 4 temporal tables created successfully")
    print()


def print_summary(cursor):
    """Print summary of created tables."""
    print("=" * 60)
    print("Summary: Temporal Tables")
    print("=" * 60)
    print()

    cursor.execute("""
        SELECT
            table_name,
            pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS size
        FROM information_schema.tables
        WHERE table_name IN ('temporal_events', 'player_snapshots', 'game_states', 'player_biographical')
        ORDER BY table_name;
    """)

    print(f"{'Table Name':<30} {'Size':<15}")
    print("-" * 45)

    for row in cursor.fetchall():
        print(f"{row[0]:<30} {row[1]:<15}")

    print()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Temporal Panel Data System - Table Creation")
    print("=" * 60)
    print()

    # Validate DB credentials
    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        print("ERROR: Database credentials not found in .env file")
        print("\nPlease create .env file with:")
        print("  DB_USER=your_username")
        print("  DB_PASSWORD=your_password")
        print("  DB_HOST=nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com")
        print("  DB_NAME=nba_simulator")
        sys.exit(1)

    # Connect to database
    print(f"Connecting to database: {DB_CONFIG['database']} at {DB_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()
        print("✓ Connected successfully")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Check prerequisites
        check_prerequisites(cursor)

        # Create tables
        print("Creating temporal tables...")
        print()

        for script_name in TABLE_SCRIPTS:
            script_path = SQL_DIR / script_name
            if not script_path.exists():
                raise Exception(f"ERROR: Script not found: {script_path}")

            create_table(cursor, script_path)

        print()

        # Validate
        validate_tables(cursor)

        # Commit transaction
        conn.commit()
        print("✓ Transaction committed")
        print()

        # Print summary
        print_summary(cursor)

        # Next steps
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Create BRIN indexes:      python scripts/db/create_temporal_indexes.py")
        print("2. Create stored procedures: python scripts/db/create_stored_procedures.py")
        print("3. Collect birth dates:      python scripts/etl/collect_player_birth_dates.py")
        print("4. Extract timestamps:       python scripts/etl/extract_wall_clock_timestamps.py")
        print("=" * 60)
        print()

        print("✓ Temporal tables created successfully!")

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
