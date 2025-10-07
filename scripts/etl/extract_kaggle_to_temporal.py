"""
Extract Kaggle Data to Temporal Format

Transforms Kaggle basketball database into temporal panel data format:
1. Player biographical data (birth dates, physical attributes)
2. Play-by-play events with timestamps
3. Game metadata

Output: CSV files ready to load into temporal_events, player_biographical tables

Usage:
    python scripts/etl/extract_kaggle_to_temporal.py

Execution time: 5-10 minutes (processing 13.5M play-by-play events)
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import json

# Configuration
KAGGLE_DB = Path("/tmp/kaggle_basketball/nba.sqlite")
OUTPUT_DIR = Path("/tmp/temporal_data_kaggle")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_player_biographical():
    """Extract player biographical data with birth dates."""
    print("="*60)
    print("Extracting Player Biographical Data")
    print("="*60)

    conn = sqlite3.connect(KAGGLE_DB)

    # Query common_player_info for complete biographical data
    query = """
    SELECT
        person_id as player_id,
        display_first_last as name,
        birthdate as birth_date,
        height,
        weight,
        position,
        school as college,
        country,
        draft_year,
        draft_round,
        draft_number,
        from_year as nba_debut_year,
        to_year as nba_retirement_year
    FROM common_player_info
    WHERE person_id IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)

    # Parse birth dates
    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')

    # Determine birth date precision
    df['birth_date_precision'] = df['birth_date'].apply(
        lambda x: 'day' if pd.notna(x) else 'unknown'
    )

    # Parse height (format: "6-10" → inches)
    def parse_height(height_str):
        if pd.isna(height_str):
            return None
        try:
            feet, inches = height_str.split('-')
            return int(feet) * 12 + int(inches)
        except:
            return None

    df['height_inches'] = df['height'].apply(parse_height)

    # Add data source
    df['data_source'] = 'kaggle'

    # Select final columns
    output_cols = [
        'player_id', 'name', 'birth_date', 'birth_date_precision',
        'height_inches', 'weight', 'position', 'college', 'country',
        'draft_year', 'draft_round', 'draft_number',
        'nba_debut_year', 'nba_retirement_year', 'data_source'
    ]

    df_final = df[output_cols]

    # Save to CSV
    output_file = OUTPUT_DIR / "player_biographical_clean.csv"
    df_final.to_csv(output_file, index=False)

    print(f"\n✓ Extracted {len(df_final):,} players")
    print(f"  - With birth dates: {df_final['birth_date'].notna().sum():,} ({df_final['birth_date'].notna().sum()/len(df_final)*100:.1f}%)")
    print(f"  - Output: {output_file}")

    conn.close()
    return output_file


def parse_wall_clock_time(wctimestring, game_date):
    """
    Parse wall clock time string to full timestamp.

    Input: "14:43 PM", game_date: "2024-01-15"
    Output: datetime with full timestamp
    """
    if pd.isna(wctimestring) or not game_date:
        return None

    try:
        # Parse time (format: "14:43 PM" or "2:30 PM")
        time_str = wctimestring.strip().upper()

        # Handle formats like "14:43 PM" (should be 2:43 PM)
        if 'PM' in time_str or 'AM' in time_str:
            # Remove AM/PM for now
            time_part = time_str.replace('PM', '').replace('AM', '').strip()
            hour, minute = map(int, time_part.split(':'))

            # Fix hour if > 12 (e.g., "14:43 PM" → 2:43 PM)
            if hour > 12:
                hour = hour - 12

            # Reconstruct with proper AM/PM
            if 'PM' in time_str and hour != 12:
                hour += 12
            elif 'AM' in time_str and hour == 12:
                hour = 0

            # Combine with game date
            dt = datetime.combine(game_date, datetime.min.time())
            dt = dt.replace(hour=hour, minute=minute)

            return dt

    except Exception as e:
        return None

    return None


def parse_game_clock(pctimestring):
    """
    Parse game clock to seconds remaining.

    Input: "11:45"
    Output: 705 (11*60 + 45 seconds)
    """
    if pd.isna(pctimestring):
        return None

    try:
        minutes, seconds = map(int, pctimestring.split(':'))
        return minutes * 60 + seconds
    except:
        return None


def extract_temporal_events(batch_size=100000):
    """Extract play-by-play events with timestamps in batches."""
    print("\n" + "="*60)
    print("Extracting Temporal Events (Play-by-Play)")
    print("="*60)

    conn = sqlite3.connect(KAGGLE_DB)

    # First, get game dates for wall clock timestamp reconstruction
    print("\nLoading game dates...")
    game_dates_query = "SELECT game_id, game_date FROM game"
    df_games = pd.read_sql_query(game_dates_query, conn)
    df_games['game_date'] = pd.to_datetime(df_games['game_date'])
    game_date_map = dict(zip(df_games['game_id'], df_games['game_date']))

    print(f"✓ Loaded {len(game_date_map):,} game dates")

    # Get total row count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM play_by_play")
    total_rows = cursor.fetchone()[0]
    print(f"\nTotal play-by-play events: {total_rows:,}")

    # Process in batches
    output_file = OUTPUT_DIR / "temporal_events.csv"
    first_batch = True

    for offset in range(0, total_rows, batch_size):
        print(f"\nProcessing batch {offset:,} to {min(offset+batch_size, total_rows):,}...")

        query = f"""
        SELECT
            game_id,
            eventnum as event_id,
            period as quarter,
            wctimestring,
            pctimestring,
            eventmsgtype as event_type_code,
            player1_id as player_id,
            player1_team_id as team_id,
            homedescription,
            visitordescription,
            neutraldescription,
            score,
            scoremargin
        FROM play_by_play
        LIMIT {batch_size} OFFSET {offset}
        """

        df = pd.read_sql_query(query, conn)

        if len(df) == 0:
            break

        # Add game dates
        df['game_date'] = df['game_id'].map(game_date_map)

        # Parse timestamps
        print("  Parsing wall clock timestamps...")
        df['wall_clock_utc'] = df.apply(
            lambda row: parse_wall_clock_time(row['wctimestring'], row['game_date']),
            axis=1
        )

        # Parse game clock
        print("  Parsing game clocks...")
        df['game_clock_seconds'] = df['pctimestring'].apply(parse_game_clock)

        # Set precision level (Kaggle data is minute-level)
        df['precision_level'] = 'minute'

        # Map event type codes to names (simplified)
        event_type_map = {
            1: 'made_shot',
            2: 'missed_shot',
            3: 'free_throw',
            4: 'rebound',
            5: 'turnover',
            6: 'foul',
            8: 'substitution',
            9: 'timeout',
            10: 'jump_ball',
            12: 'period_start',
            13: 'period_end'
        }
        df['event_type'] = df['event_type_code'].map(event_type_map).fillna('other')

        # Create event_data JSONB (store original descriptions)
        # Use json.dumps() to properly escape special characters like apostrophes
        df['event_data'] = df.apply(lambda row: json.dumps({
            'home_description': row['homedescription'],
            'visitor_description': row['visitordescription'],
            'neutral_description': row['neutraldescription'],
            'score': row['score'],
            'score_margin': row['scoremargin']
        }), axis=1)

        # Data source
        df['data_source'] = 'kaggle'

        # Select final columns
        output_cols = [
            'game_id', 'player_id', 'team_id', 'wall_clock_utc',
            'game_clock_seconds', 'quarter', 'precision_level',
            'event_type', 'event_data', 'data_source'
        ]

        df_output = df[output_cols]

        # Save batch
        if first_batch:
            df_output.to_csv(output_file, index=False, mode='w')
            first_batch = False
        else:
            df_output.to_csv(output_file, index=False, mode='a', header=False)

        print(f"  ✓ Saved {len(df_output):,} events")

    conn.close()

    print(f"\n✓ Extraction complete")
    print(f"  - Output: {output_file}")
    print(f"  - Total events: {total_rows:,}")

    return output_file


def print_summary():
    """Print summary of extracted data."""
    print("\n" + "="*60)
    print("Extraction Summary")
    print("="*60)

    files = list(OUTPUT_DIR.glob("*.csv"))

    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nExtracted files:")

    for file in sorted(files):
        size_mb = file.stat().st_size / 1024 / 1024
        # Count rows
        with open(file) as f:
            row_count = sum(1 for line in f) - 1  # Exclude header

        print(f"  - {file.name}")
        print(f"      Size: {size_mb:.1f} MB")
        print(f"      Rows: {row_count:,}")


def main():
    """Main execution function."""
    print("="*60)
    print("Kaggle to Temporal Data Extraction")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check database exists
    if not KAGGLE_DB.exists():
        print(f"ERROR: Kaggle database not found: {KAGGLE_DB}")
        print("Run: python scripts/etl/download_kaggle_basketball.py")
        return

    # Extract player biographical data
    extract_player_biographical()

    # Extract temporal events
    extract_temporal_events(batch_size=500000)  # Process 500K rows at a time

    # Print summary
    print_summary()

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Create temporal database tables:")
    print("   python scripts/db/create_temporal_tables.py")
    print("")
    print("2. Load Kaggle data to RDS:")
    print("   python scripts/db/load_kaggle_to_rds.py")
    print("="*60)

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
