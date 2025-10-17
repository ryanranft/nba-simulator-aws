#!/usr/bin/env python3
"""
Complete the games table schema update by adding all missing columns.
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values

# Database connection
DB_HOST = os.environ.get(
    "DB_HOST", "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"
)
DB_NAME = os.environ.get("DB_NAME", "nba_simulator")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_existing_columns(cursor):
    """Get list of existing columns in games table"""
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'games'
        ORDER BY ordinal_position
    """
    )
    return {row[0] for row in cursor.fetchall()}


def main():
    # Connect to database
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )
    cursor = conn.cursor()

    print(f"✅ Connected to database: {DB_HOST}")

    # Get existing columns
    existing_columns = get_existing_columns(cursor)
    print(f"\nFound {len(existing_columns)} existing columns in games table")

    # Define all required columns with their SQL definitions
    required_columns = {
        # Game time
        "game_time": "TIMESTAMP",
        # Home team details
        "home_team_abbrev": "VARCHAR(10)",
        "home_team_name": "VARCHAR(100)",
        "home_team_short_name": "VARCHAR(100)",
        "home_team_logo": "TEXT",
        "home_team_color": "VARCHAR(10)",
        "home_team_alt_color": "VARCHAR(10)",
        "home_team_uid": "VARCHAR(50)",
        "home_team_record_summary": "VARCHAR(50)",
        "home_team_standing_summary": "VARCHAR(100)",
        "home_team_location": "VARCHAR(100)",
        "home_team_is_winner": "BOOLEAN",
        "home_team_leader_name": "VARCHAR(100)",
        "home_team_leader_stat": "VARCHAR(50)",
        # Away team details
        "away_team_abbrev": "VARCHAR(10)",
        "away_team_name": "VARCHAR(100)",
        "away_team_short_name": "VARCHAR(100)",
        "away_team_logo": "TEXT",
        "away_team_color": "VARCHAR(10)",
        "away_team_alt_color": "VARCHAR(10)",
        "away_team_uid": "VARCHAR(50)",
        "away_team_record_summary": "VARCHAR(50)",
        "away_team_standing_summary": "VARCHAR(100)",
        "away_team_location": "VARCHAR(100)",
        "away_team_is_winner": "BOOLEAN",
        "away_team_leader_name": "VARCHAR(100)",
        "away_team_leader_stat": "VARCHAR(50)",
        # Venue details
        "venue_id": "VARCHAR(50)",
        "venue_city": "VARCHAR(100)",
        "venue_state": "VARCHAR(50)",
        "venue_country": "VARCHAR(50)",
        "venue_indoor": "BOOLEAN",
        # Status details
        "status_id": "VARCHAR(50)",
        "status_state": "VARCHAR(50)",
        "status_detail": "VARCHAR(100)",
        # Broadcast info
        "broadcast_name": "VARCHAR(100)",
        "broadcast_market": "VARCHAR(50)",
        "broadcast_type": "VARCHAR(50)",
        "broadcast_count": "INTEGER",
        # Game metadata
        "completed": "BOOLEAN",
        "is_tie": "BOOLEAN",
        "periods": "INTEGER DEFAULT 4",
        "time_valid": "BOOLEAN DEFAULT TRUE",
        "game_link": "TEXT",
        "header_postfix": "VARCHAR(100)",
        "has_tickets": "BOOLEAN",
    }

    # Find missing columns
    missing_columns = []
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            missing_columns.append((col_name, col_type))

    if not missing_columns:
        print("\n✅ All columns already exist! Schema is complete.")
        cursor.close()
        conn.close()
        return

    print(f"\n📋 Need to add {len(missing_columns)} missing columns:")
    for col_name, col_type in missing_columns:
        print(f"   - {col_name} ({col_type})")

    # Add missing columns one by one
    print("\n🔧 Adding missing columns...")
    added = 0
    for col_name, col_type in missing_columns:
        try:
            cursor.execute(
                f"ALTER TABLE games ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            )
            conn.commit()
            added += 1
            print(f"   ✓ Added {col_name}")
        except Exception as e:
            print(f"   ✗ Failed to add {col_name}: {e}")
            conn.rollback()

    print(f"\n✅ Successfully added {added}/{len(missing_columns)} columns")

    # Verify final column count
    final_columns = get_existing_columns(cursor)
    print(f"\n📊 Final games table has {len(final_columns)} columns")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
