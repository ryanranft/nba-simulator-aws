"""
Load ESPN Temporal Events to RDS

Loads extracted ESPN play-by-play data from CSV to temporal_events table.

Features:
1. Parses game clock display value ("11:38") to seconds
2. Reconstructs wall clock timestamps from game date + period + clock
3. Extracts team_id from homeAway field using games table
4. Bulk loads using PostgreSQL COPY command
5. Progress monitoring for 14.1M events

Usage:
    python scripts/db/load_espn_events.py --test  # Load first 100k events
    python scripts/db/load_espn_events.py         # Load all events
"""

import os
import sys
import psycopg2
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse

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

# Input file
ESPN_EVENTS_CSV = Path("/tmp/temporal_data_espn/temporal_events_espn.csv")


def parse_game_clock(clock_display: str) -> int:
    """
    Parse game clock display value to seconds remaining.

    Args:
        clock_display: e.g., "11:38" or "0:45"

    Returns:
        Seconds remaining in quarter
    """
    if not clock_display or pd.isna(clock_display):
        return None

    try:
        parts = clock_display.split(':')
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes * 60 + seconds
    except:
        return None


def reconstruct_wall_clock(game_start: datetime, period: int, clock_seconds: int) -> datetime:
    """
    Reconstruct wall clock timestamp from game start time and game state.

    Args:
        game_start: Game start datetime (from game date)
        period: Quarter number (1-4, 5+ for overtime)
        clock_seconds: Seconds remaining in quarter

    Returns:
        Estimated wall clock timestamp
    """
    if not game_start or pd.isna(period) or clock_seconds is None:
        return game_start

    try:
        # NBA quarter is 12 minutes (720 seconds)
        quarter_length = 720

        # Calculate elapsed time in game
        completed_quarters = period - 1
        elapsed_in_current_quarter = quarter_length - clock_seconds

        # Add quarter breaks (2 minutes each) and halftime (15 minutes)
        if period <= 4:
            # Regular game
            quarter_breaks = max(0, completed_quarters - 1) * 2 * 60  # 2 min between quarters
            halftime = 15 * 60 if period > 2 else 0
        else:
            # Overtime (period 5+)
            quarter_breaks = 3 * 2 * 60  # 3 breaks in regulation
            halftime = 15 * 60
            ot_periods = period - 5
            ot_breaks = ot_periods * 2 * 60  # 2 min between OT periods
            quarter_breaks += ot_breaks
            completed_quarters = 4 + ot_periods  # 4 regular + OT periods
            quarter_length = 5 * 60  # OT is 5 minutes
            elapsed_in_current_quarter = quarter_length - clock_seconds

        total_elapsed = (
            completed_quarters * quarter_length +
            elapsed_in_current_quarter +
            quarter_breaks +
            halftime
        )

        return game_start + timedelta(seconds=total_elapsed)
    except Exception as e:
        # If reconstruction fails, return base game time
        return game_start


def get_team_ids_for_games(cursor, game_ids: set) -> dict:
    """
    Get home and away team IDs for games from games table.

    Returns:
        dict: {game_id: {'home': home_team_id, 'away': away_team_id}}
    """
    print(f"Fetching team IDs for {len(game_ids):,} games...")

    cursor.execute("""
        SELECT game_id, home_team_id, away_team_id
        FROM games
        WHERE game_id = ANY(%s)
    """, (list(game_ids),))

    team_map = {}
    for row in cursor.fetchall():
        game_id, home_team_id, away_team_id = row
        team_map[str(game_id)] = {
            'home': str(home_team_id) if home_team_id else None,
            'away': str(away_team_id) if away_team_id else None
        }

    print(f"✓ Mapped {len(team_map):,} games to team IDs")
    return team_map


def process_batch(df: pd.DataFrame, team_map: dict) -> pd.DataFrame:
    """
    Process a batch of events: parse JSON, extract fields, reconstruct timestamps.
    """
    processed_rows = []

    for _, row in df.iterrows():
        try:
            # Parse event_data JSON
            event = json.loads(row['event_data'])

            # Parse game clock
            clock_display = event.get('clock', {}).get('displayValue')
            game_clock_seconds = parse_game_clock(clock_display)

            # Skip non-NBA games (college basketball has 20-minute halves = 1200 seconds)
            # NBA quarters are 12 minutes = 720 seconds max
            if game_clock_seconds is not None and game_clock_seconds > 720:
                continue

            # Reconstruct wall clock timestamp
            game_start = pd.to_datetime(row['wall_clock_utc'])
            period = row['period']
            wall_clock_utc = reconstruct_wall_clock(game_start, period, game_clock_seconds)

            # Get team_id from homeAway field
            game_id = str(row['game_id'])
            home_away = event.get('homeAway')
            team_id = None
            if home_away and game_id in team_map:
                team_id = team_map[game_id].get(home_away)

            # Create processed row with proper types
            processed_rows.append({
                'game_id': game_id,
                'player_id': None,  # No player IDs in ESPN data
                'team_id': team_id,
                'wall_clock_utc': wall_clock_utc,
                'game_clock_seconds': int(game_clock_seconds) if game_clock_seconds is not None else None,
                'quarter': int(period) if pd.notna(period) else None,
                'precision_level': 'minute',
                'event_type': 'play',
                'event_data': row['event_data'],  # Keep original JSON
                'data_source': 'espn'
            })
        except Exception as e:
            # Skip malformed events
            continue

    return pd.DataFrame(processed_rows)


def load_events(test_mode=False):
    """
    Load ESPN temporal events to RDS.
    """
    print("=" * 60)
    print("Load ESPN Temporal Events to RDS")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Validate file exists
    if not ESPN_EVENTS_CSV.exists():
        print(f"ERROR: Events file not found: {ESPN_EVENTS_CSV}")
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
        # Check current row count
        cursor.execute("SELECT COUNT(*) FROM temporal_events;")
        existing_count = cursor.fetchone()[0]
        print(f"Current temporal_events rows: {existing_count:,}")
        print()

        # Count total events to load
        total_lines = sum(1 for _ in open(ESPN_EVENTS_CSV)) - 1  # Subtract header
        print(f"Total events in CSV: {total_lines:,}")

        if test_mode:
            total_lines = min(100000, total_lines)
            print(f"TEST MODE: Loading first {total_lines:,} events")

        print()

        # Process in batches
        batch_size = 50000
        total_batches = (total_lines + batch_size - 1) // batch_size

        print(f"Processing {total_batches:,} batches of {batch_size:,} events...")
        print()

        # Read CSV in chunks
        chunk_iterator = pd.read_csv(
            ESPN_EVENTS_CSV,
            chunksize=batch_size,
            nrows=total_lines if test_mode else None
        )

        # First pass: collect all unique game IDs
        print("Pass 1: Collecting game IDs...")
        all_game_ids = set()
        for chunk in pd.read_csv(ESPN_EVENTS_CSV, chunksize=batch_size, nrows=total_lines if test_mode else None):
            all_game_ids.update(chunk['game_id'].astype(str).unique())

        # Get team mappings
        team_map = get_team_ids_for_games(cursor, all_game_ids)
        print()

        # Second pass: process and load
        print("Pass 2: Processing and loading events...")
        print()

        loaded_count = 0
        filtered_count = 0
        batch_num = 0

        for chunk in pd.read_csv(ESPN_EVENTS_CSV, chunksize=batch_size, nrows=total_lines if test_mode else None):
            batch_num += 1
            chunk_size = len(chunk)

            # Process batch
            processed_df = process_batch(chunk, team_map)
            filtered_count += (chunk_size - len(processed_df))

            if len(processed_df) == 0:
                continue

            # Create temporary CSV for COPY
            temp_csv = f"/tmp/temp_batch_{batch_num}.csv"

            # Format integers without decimal points for PostgreSQL
            processed_df['game_clock_seconds'] = processed_df['game_clock_seconds'].apply(
                lambda x: f"{int(x)}" if pd.notna(x) else ""
            )
            processed_df['quarter'] = processed_df['quarter'].apply(
                lambda x: f"{int(x)}" if pd.notna(x) else ""
            )

            processed_df.to_csv(temp_csv, index=False, header=False)

            # Load using COPY
            with open(temp_csv, 'r') as f:
                cursor.copy_expert("""
                    COPY temporal_events (
                        game_id, player_id, team_id, wall_clock_utc,
                        game_clock_seconds, quarter, precision_level,
                        event_type, event_data, data_source
                    )
                    FROM STDIN WITH CSV
                """, f)

            loaded_count += len(processed_df)

            # Progress update
            if batch_num % 10 == 0:
                pct = (loaded_count / total_lines) * 100
                print(f"  Batch {batch_num}/{total_batches}: {loaded_count:,}/{total_lines:,} events ({pct:.1f}%)")

            # Clean up temp file
            os.remove(temp_csv)

            # Commit every 10 batches
            if batch_num % 10 == 0:
                conn.commit()

        # Final commit
        conn.commit()

        print()
        print(f"✓ Loaded {loaded_count:,} events")
        if filtered_count > 0:
            print(f"  Filtered {filtered_count:,} non-NBA events (game_clock > 720s)")
        print()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM temporal_events;")
        final_count = cursor.fetchone()[0]
        print(f"Final temporal_events rows: {final_count:,}")
        print(f"New rows added: {final_count - existing_count:,}")
        print()

        print("=" * 60)
        print("Load Complete!")
        print("=" * 60)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Next steps:")
        print("1. Create indexes: python scripts/db/create_temporal_indexes.py")
        print("2. Create procedures: python scripts/db/create_stored_procedures.py")
        print("3. Run validation: pytest tests/test_temporal_queries.py")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        print("Transaction rolled back")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")


def main():
    parser = argparse.ArgumentParser(description="Load ESPN temporal events to RDS")
    parser.add_argument('--test', action='store_true', help='Test mode: load first 100k events only')

    args = parser.parse_args()

    # Validate credentials
    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        print("ERROR: Database credentials not found in .env file")
        sys.exit(1)

    load_events(test_mode=args.test)


if __name__ == '__main__':
    main()
