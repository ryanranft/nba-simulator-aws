"""
Create Temporal BRIN Indexes

Creates Block Range (BRIN) indexes for temporal tables:
- 70% storage savings vs B-tree (500 MB vs 50 GB)
- Optimized for time-series sequential queries
- Ideal for temporal_events and player_snapshots

Usage:
    python scripts/db/create_temporal_indexes.py

Execution time: 10-30 minutes (depends on table size)
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
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


def check_table_size(cursor, table_name):
    """Check current table size."""
    cursor.execute(f"""
        SELECT
            pg_size_pretty(pg_total_relation_size('{table_name}'::regclass)) AS total_size,
            pg_size_pretty(pg_relation_size('{table_name}'::regclass)) AS table_size,
            pg_size_pretty(pg_indexes_size('{table_name}'::regclass)) AS indexes_size
    """)
    return cursor.fetchone()


def create_brin_indexes(cursor):
    """Create BRIN indexes for time-series optimization."""
    print("=" * 60)
    print("Creating BRIN Indexes")
    print("=" * 60)
    print()

    # BRIN indexes for temporal_events
    print("1. temporal_events table:")
    print("   Creating BRIN index on wall_clock_utc...")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_temporal_events_time_brin
        ON temporal_events USING BRIN (wall_clock_utc)
        WITH (pages_per_range = 128);
    """)
    print("   ✓ idx_temporal_events_time_brin created")

    # B-tree indexes for lookups
    print("\n   Creating B-tree indexes for fast lookups...")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_temporal_events_game_id
        ON temporal_events (game_id);
    """)
    print("   ✓ idx_temporal_events_game_id created")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_temporal_events_player_id
        ON temporal_events (player_id) WHERE player_id IS NOT NULL;
    """)
    print("   ✓ idx_temporal_events_player_id created")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_temporal_events_event_type
        ON temporal_events (event_type);
    """)
    print("   ✓ idx_temporal_events_event_type created")

    # GIN index for JSONB queries
    print("\n   Creating GIN index for event_data JSONB...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_temporal_events_event_data_gin
        ON temporal_events USING GIN (event_data);
    """)
    print("   ✓ idx_temporal_events_event_data_gin created")

    # BRIN indexes for player_snapshots
    print("\n2. player_snapshots table:")
    print("   Creating BRIN index on snapshot_time...")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_snapshots_time_brin
        ON player_snapshots USING BRIN (snapshot_time)
        WITH (pages_per_range = 128);
    """)
    print("   ✓ idx_player_snapshots_time_brin created")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_snapshots_player_id
        ON player_snapshots (player_id);
    """)
    print("   ✓ idx_player_snapshots_player_id created")

    # Composite index for snapshot queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_snapshots_player_time
        ON player_snapshots (player_id, snapshot_time);
    """)
    print("   ✓ idx_player_snapshots_player_time created")

    # BRIN index for game_states
    print("\n3. game_states table:")
    print("   Creating BRIN index on state_time...")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_game_states_time_brin
        ON game_states USING BRIN (state_time)
        WITH (pages_per_range = 128);
    """)
    print("   ✓ idx_game_states_time_brin created")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_game_states_game_id
        ON game_states (game_id);
    """)
    print("   ✓ idx_game_states_game_id created")

    # player_biographical indexes
    print("\n4. player_biographical table:")
    print("   Creating B-tree indexes...")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_biographical_birth_date
        ON player_biographical (birth_date) WHERE birth_date IS NOT NULL;
    """)
    print("   ✓ idx_player_biographical_birth_date created")

    print()


def print_index_summary(cursor):
    """Print summary of created indexes."""
    print("=" * 60)
    print("Index Summary")
    print("=" * 60)
    print()

    cursor.execute("""
        SELECT
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
        FROM pg_indexes
        WHERE tablename IN ('temporal_events', 'player_snapshots', 'game_states', 'player_biographical')
        ORDER BY tablename, indexname;
    """)

    current_table = None
    for row in cursor.fetchall():
        table = row[1]
        index = row[2]
        size = row[3]

        if table != current_table:
            print(f"\n{table}:")
            current_table = table

        print(f"  - {index}: {size}")

    print()


def print_storage_comparison(cursor):
    """Compare storage before/after indexes."""
    print("=" * 60)
    print("Storage Summary")
    print("=" * 60)
    print()

    cursor.execute("""
        SELECT
            table_name,
            pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS total_size,
            pg_size_pretty(pg_relation_size(table_name::regclass)) AS table_size,
            pg_size_pretty(pg_indexes_size(table_name::regclass)) AS indexes_size,
            ROUND(100.0 * pg_indexes_size(table_name::regclass) / NULLIF(pg_relation_size(table_name::regclass), 0), 1) AS index_ratio
        FROM information_schema.tables
        WHERE table_name IN ('temporal_events', 'player_snapshots', 'game_states', 'player_biographical')
        ORDER BY table_name;
    """)

    print(f"{'Table':<25} {'Total':<12} {'Table':<12} {'Indexes':<12} {'Index %':<10}")
    print("-" * 75)

    for row in cursor.fetchall():
        table = row[0]
        total = row[1]
        table_size = row[2]
        indexes = row[3]
        ratio = row[4] if row[4] else 0

        print(f"{table:<25} {total:<12} {table_size:<12} {indexes:<12} {ratio:<10.1f}%")

    print()


def main():
    """Main execution function."""
    print("=" * 60)
    print("Temporal BRIN Index Creation")
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
        # Create indexes
        create_brin_indexes(cursor)

        # Commit
        conn.commit()
        print("✓ Indexes created and committed")
        print()

        # Print summaries
        print_index_summary(cursor)
        print_storage_comparison(cursor)

        # Next steps
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Create stored procedures: python scripts/db/create_stored_procedures.py")
        print("2. Run validation tests:     pytest tests/test_temporal_queries.py")
        print("3. Try a temporal query:     python scripts/queries/test_temporal_query.py")
        print("=" * 60)
        print()

        print(f"✓ Index creation complete!")
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
