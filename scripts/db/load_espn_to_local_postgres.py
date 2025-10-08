#!/usr/bin/env python3
"""
Load ESPN Temporal Events to Local PostgreSQL

Loads extracted ESPN CSV files from /tmp/temporal_data_espn/ to local PostgreSQL database.
Adapted from load_espn_events.py for local database use.

Usage:
    # First run extraction:
    python scripts/etl/extract_espn_local_to_temporal_UPDATED.py

    # Then load to database:
    python scripts/db/load_espn_to_local_postgres.py [--test]

Options:
    --test    Load only first 10,000 events for testing
"""

import os
import sys
import csv
import json
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'nba_simulator',
    'user': 'ryanranft',
    'port': 5432
}

# Data directory
TEMPORAL_DATA_DIR = Path('/tmp/temporal_data_espn')
EVENTS_CSV = TEMPORAL_DATA_DIR / 'temporal_events_espn.csv'
PLAYERS_CSV = TEMPORAL_DATA_DIR / 'players_espn.csv'

# Test mode flag
TEST_MODE = '--test' in sys.argv
BATCH_SIZE = 5000


def log(message):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def parse_game_clock(clock_str):
    """
    Parse game clock string to seconds.

    Examples:
        "11:38" -> 698 seconds
        "0:45" -> 45 seconds
        "12:00" -> 720 seconds
    """
    if not clock_str or clock_str == '':
        return None

    try:
        parts = clock_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
    except:
        pass

    return None


def reconstruct_wall_clock(game_date, period, clock_seconds):
    """
    Reconstruct wall clock timestamp from game date, period, and clock.

    Assumptions:
    - NBA games typically start at 7:00 PM local time
    - Each quarter is 12 minutes
    - Halftime is 15 minutes
    - Timeouts/breaks add ~5 minutes per quarter

    Formula:
    - Period 1: game_date + 0 minutes
    - Period 2: game_date + 17 minutes (12 + 5)
    - Period 3: game_date + 49 minutes (12 + 5 + 15 + 12 + 5)
    - Period 4: game_date + 66 minutes (12 + 5 + 15 + 12 + 5 + 12 + 5)
    - OT: game_date + 83 minutes per OT period
    """
    if not game_date or not period:
        return None

    try:
        # Parse game_date if it's a string
        if isinstance(game_date, str):
            game_date = datetime.fromisoformat(game_date.replace('Z', '+00:00'))

        # Calculate elapsed real-time minutes before this period
        if period == 1:
            period_start = 0
        elif period == 2:
            period_start = 17  # Q1 (12 min) + break (5 min)
        elif period == 3:
            period_start = 49  # Q1 + break + halftime (15) + Q2 + break
        elif period == 4:
            period_start = 66  # Q1 + break + halftime + Q2 + break + Q3 + break
        else:
            # Overtime periods (5 minutes each + 2 min break)
            ot_number = period - 4
            period_start = 83 + (ot_number - 1) * 7  # Base + (OT - 1) * (5 + 2)

        # Add time elapsed in current period
        if clock_seconds is not None:
            # Clock counts down, so elapsed = (12 * 60) - clock_seconds for regular periods
            period_length = 720 if period <= 4 else 300  # 12 min quarters, 5 min OT
            elapsed_in_period = period_length - clock_seconds
            total_elapsed_seconds = (period_start * 60) + elapsed_in_period
        else:
            # No clock data, use period start
            total_elapsed_seconds = period_start * 60

        # Add to game date
        wall_clock = game_date + timedelta(seconds=total_elapsed_seconds)
        return wall_clock

    except Exception as e:
        log(f"Error reconstructing wall clock: {e}")
        return None


def create_tables(conn):
    """Create temporal_events table if it doesn't exist (uses existing schema)"""
    cur = conn.cursor()

    log("Checking temporal_events table...")

    # Table already exists with quarter column (not period)
    # Just verify it exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'temporal_events'
        );
    """)

    exists = cur.fetchone()[0]

    if not exists:
        log("⚠️  temporal_events table does not exist!")
        log("Please create it first using the standard schema.")
        raise Exception("temporal_events table missing")

    conn.commit()
    log("✅ Table ready")


def load_players(conn):
    """Load players from CSV"""
    if not PLAYERS_CSV.exists():
        log("⚠️  No players CSV found, skipping...")
        return 0

    log(f"Loading players from {PLAYERS_CSV}...")

    try:
        # Read CSV
        players = []
        with open(PLAYERS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                players.append(row)

        if not players:
            log("⚠️  No players to load")
            return 0

        log(f"Found {len(players):,} unique players")

        # Insert into players table (create if needed)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS espn_players (
                player_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(200),
                short_name VARCHAR(100),
                jersey VARCHAR(10),
                position VARCHAR(10),
                team_id VARCHAR(20),
                team_name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Batch insert
        insert_query = """
            INSERT INTO espn_players (player_id, name, short_name, jersey, position, team_id, team_name)
            VALUES %s
            ON CONFLICT (player_id) DO UPDATE SET
                name = EXCLUDED.name,
                short_name = EXCLUDED.short_name,
                jersey = EXCLUDED.jersey,
                position = EXCLUDED.position,
                team_id = EXCLUDED.team_id,
                team_name = EXCLUDED.team_name
        """

        values = [
            (
                p.get('player_id'),
                p.get('name'),
                p.get('short_name'),
                p.get('jersey'),
                p.get('position'),
                p.get('team_id'),
                p.get('team_name')
            )
            for p in players
        ]

        execute_values(cur, insert_query, values)
        conn.commit()

        log(f"✅ Loaded {len(players):,} players")
        return len(players)

    except Exception as e:
        log(f"❌ Error loading players: {e}")
        conn.rollback()
        return 0


def load_events(conn):
    """Load temporal events from CSV"""
    if not EVENTS_CSV.exists():
        log(f"❌ Events CSV not found: {EVENTS_CSV}")
        log("Run extract_espn_local_to_temporal_UPDATED.py first!")
        return 0

    log(f"Loading events from {EVENTS_CSV}...")

    cur = conn.cursor()

    # Read and process CSV in batches
    batch = []
    total_loaded = 0
    total_processed = 0
    errors = 0

    with open(EVENTS_CSV, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_processed += 1

            # Test mode: only load first 10,000
            if TEST_MODE and total_processed > 10000:
                break

            try:
                # Parse event_data JSON
                event_data = json.loads(row['event_data']) if row.get('event_data') else {}

                # Parse game clock
                clock_display = event_data.get('clock', {}).get('displayValue')
                clock_seconds = parse_game_clock(clock_display)

                # Reconstruct wall clock
                wall_clock = reconstruct_wall_clock(
                    row.get('wall_clock_utc'),
                    int(row['period']) if row.get('period') else None,
                    clock_seconds
                )

                # Extract player and team from event_data if available
                player_id = None
                team_id = None

                # Try to extract from participantIds
                if 'participantIds' in event_data and event_data['participantIds']:
                    player_id = str(event_data['participantIds'][0])

                # Try to extract team from teamId
                if 'teamId' in event_data:
                    team_id = str(event_data['teamId'])

                # Prepare row for insertion (using existing schema with 'quarter' column)
                event_row = (
                    row['game_id'],
                    wall_clock,
                    clock_seconds,
                    int(row['period']) if row.get('period') else None,  # quarter = period
                    player_id,
                    team_id,
                    row.get('precision_level', 'minute'),
                    row.get('event_type', 'play'),
                    row.get('data_source', 'espn'),
                    json.dumps(event_data)
                )

                batch.append(event_row)

                # Insert batch when it reaches BATCH_SIZE
                if len(batch) >= BATCH_SIZE:
                    insert_query = """
                        INSERT INTO temporal_events
                        (game_id, wall_clock_utc, game_clock_seconds, quarter,
                         player_id, team_id, precision_level, event_type, data_source, event_data)
                        VALUES %s
                    """
                    execute_values(cur, insert_query, batch)
                    conn.commit()
                    total_loaded += len(batch)
                    log(f"  Loaded {total_loaded:,} events...")
                    batch = []

            except Exception as e:
                errors += 1
                if errors <= 10:
                    log(f"  ⚠️  Error processing row {total_processed}: {e}")

        # Insert remaining batch
        if batch:
            insert_query = """
                INSERT INTO temporal_events
                (game_id, wall_clock_utc, game_clock_seconds, quarter,
                 player_id, team_id, precision_level, event_type, data_source, event_data)
                VALUES %s
            """
            execute_values(cur, insert_query, batch)
            conn.commit()
            total_loaded += len(batch)

    log(f"✅ Loaded {total_loaded:,} events ({errors} errors)")
    return total_loaded


def main():
    """Main loading function"""
    log("=" * 80)
    log("ESPN Temporal Events Loader - Local PostgreSQL")
    log("=" * 80)
    log(f"Data directory: {TEMPORAL_DATA_DIR}")
    log(f"Test mode: {TEST_MODE}")
    log("")

    # Check for extracted data
    if not EVENTS_CSV.exists():
        log("❌ No extracted ESPN data found!")
        log(f"Expected: {EVENTS_CSV}")
        log("")
        log("Please run extraction first:")
        log("  python scripts/etl/extract_espn_local_to_temporal_UPDATED.py")
        return

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        log("✅ Connected to PostgreSQL")
    except Exception as e:
        log(f"❌ Failed to connect to database: {e}")
        return

    # Create tables
    create_tables(conn)

    # Load players
    log("\n" + "=" * 80)
    log("Loading players...")
    log("=" * 80)
    players_loaded = load_players(conn)

    # Load events
    log("\n" + "=" * 80)
    log("Loading temporal events...")
    log("=" * 80)
    events_loaded = load_events(conn)

    # Summary
    log("\n" + "=" * 80)
    log("✅ LOAD COMPLETE")
    log("=" * 80)
    log(f"Players loaded: {players_loaded:,}")
    log(f"Events loaded: {events_loaded:,}")
    log("")

    # Show sample query
    log("Sample query to verify data:")
    log("  SELECT data_source, COUNT(*) FROM temporal_events GROUP BY data_source;")
    log("")

    conn.close()


if __name__ == '__main__':
    main()
