#!/usr/bin/env python3
"""
Load Kaggle temporal events into local PostgreSQL database
"""

import psycopg2
import pandas as pd
import sys
from datetime import datetime

# Local PostgreSQL connection settings
LOCAL_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "nba_simulator",
    "user": "ryanranft",  # Change if needed
    "password": "",  # Local PostgreSQL usually doesn't need password
}


def main():
    print("=" * 60)
    print("Load Kaggle Temporal Events to Local PostgreSQL")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Connect to local PostgreSQL
    print(f"Connecting to: {LOCAL_DB_CONFIG['dbname']} at localhost...")
    try:
        conn = psycopg2.connect(**LOCAL_DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected")
        print()
    except Exception as e:
        print(f"ERROR: Could not connect to local PostgreSQL: {e}")
        print()
        print("Please ensure:")
        print("1. PostgreSQL is running: brew services start postgresql")
        print("2. Database exists: createdb nba_simulator")
        print("3. User has access (update LOCAL_DB_CONFIG if needed)")
        sys.exit(1)

    # Create tables if they don't exist
    print("Creating tables if needed...")

    # Create games table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS games (
            game_id VARCHAR(20) PRIMARY KEY,
            game_date DATE,
            season VARCHAR(10),
            home_team_id VARCHAR(20),
            away_team_id VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create temporal_events table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS temporal_events (
            event_id BIGSERIAL PRIMARY KEY,
            game_id VARCHAR(20) NOT NULL,
            team_id VARCHAR(20),
            quarter INTEGER,
            game_clock_seconds INTEGER,
            wall_clock_utc TIMESTAMP,
            event_data JSONB,
            data_source VARCHAR(20) DEFAULT 'kaggle',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT chk_quarter CHECK (quarter BETWEEN 1 AND 10),
            CONSTRAINT chk_game_clock CHECK (game_clock_seconds BETWEEN 0 AND 720)
        )
    """
    )

    # Create possession_panel table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS possession_panel (
            possession_id BIGSERIAL PRIMARY KEY,
            game_id VARCHAR(20) NOT NULL,
            possession_number INTEGER NOT NULL,
            game_date DATE NOT NULL,
            season INTEGER NOT NULL,
            game_seconds_elapsed INTEGER NOT NULL,
            period INTEGER NOT NULL,
            seconds_remaining INTEGER NOT NULL,
            offensive_team_id VARCHAR(20) NOT NULL,
            defensive_team_id VARCHAR(20) NOT NULL,
            points_scored INTEGER NOT NULL,
            possession_result VARCHAR(20),
            possession_duration_seconds INTEGER,
            score_differential INTEGER,
            is_clutch BOOLEAN DEFAULT FALSE,
            data_source VARCHAR(20) DEFAULT 'kaggle',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT unique_possession UNIQUE (game_id, possession_number)
        )
    """
    )

    conn.commit()
    print("✓ Tables created")
    print()

    # Check current row count
    cursor.execute("SELECT COUNT(*) FROM temporal_events WHERE data_source = 'kaggle'")
    current_count = cursor.fetchone()[0]
    print(f"Current Kaggle events in database: {current_count:,}")
    print()

    # Load CSV
    csv_path = "/tmp/kaggle_temporal_events.csv"
    print(f"Loading events from {csv_path}...")

    try:
        # Read CSV in chunks for memory efficiency
        chunk_size = 100000
        total_loaded = 0

        from io import StringIO

        for chunk_num, chunk in enumerate(
            pd.read_csv(csv_path, chunksize=chunk_size), 1
        ):
            # Write to database using COPY for speed
            buffer = StringIO()
            chunk.to_csv(buffer, index=False, header=False)
            buffer.seek(0)

            cursor.copy_expert(
                """
                COPY temporal_events (
                    game_id, player_id, team_id, wall_clock_utc,
                    game_clock_seconds, quarter, precision_level,
                    event_type, event_data, data_source
                )
                FROM STDIN WITH CSV
                """,
                buffer,
            )

            total_loaded += len(chunk)

            if chunk_num % 10 == 0:
                print(f"  Loaded {total_loaded:,} events...")
                conn.commit()

        conn.commit()
        print(f"\n✓ Loaded {total_loaded:,} Kaggle events")
        print()

    except Exception as e:
        print(f"ERROR loading CSV: {e}")
        conn.rollback()
        sys.exit(1)

    # Verify final count
    cursor.execute("SELECT COUNT(*) FROM temporal_events WHERE data_source = 'kaggle'")
    final_count = cursor.fetchone()[0]
    print(f"Final Kaggle events in database: {final_count:,}")
    print(f"New events added: {final_count - current_count:,}")
    print()

    # Create indexes for performance
    print("Creating indexes...")
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_temporal_game_time
        ON temporal_events(game_id, quarter DESC, game_clock_seconds DESC)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_temporal_source
        ON temporal_events(data_source)
    """
    )
    conn.commit()
    print("✓ Indexes created")
    print()

    print("=" * 60)
    print("Load Complete!")
    print("=" * 60)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps:")
    print("1. Test possession panel locally:")
    print("   python scripts/etl/create_possession_panel_from_kaggle.py --limit 10")
    print("2. Verify data quality:")
    print("   psql nba_simulator -c 'SELECT COUNT(*) FROM temporal_events'")
    print("=" * 60)
    print()

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
