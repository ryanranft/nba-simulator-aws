#!/usr/bin/env python3
"""
Load hoopR Player Box Scores Only - Quick Fix for Player ID Mapping

Loads only player box score data (skips play-by-play, team box, etc.)
This gets us the NBA API player rosters needed for creating player ID mappings.

Usage:
    python scripts/db/load_hoopr_player_box_only.py --test  # Test with limited data
    python scripts/db/load_hoopr_player_box_only.py         # Full load
"""

import os
import sys
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Database config
DB_CONFIG = {
    "host": "localhost",
    "dbname": "nba_simulator",
    "user": "ryanranft",
    "password": "",
    "port": 5432,
}

# Data directory
DATA_DIR = "/tmp/hoopr_phase1"
BATCH_SIZE = 5000
TEST_MODE = "--test" in sys.argv


def log(message):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def create_player_box_table(conn):
    """Create hoopr_player_box table with correct schema"""
    cur = conn.cursor()

    cur.execute(
        """
        DROP TABLE IF EXISTS hoopr_player_box CASCADE;

        CREATE TABLE hoopr_player_box (
            id SERIAL PRIMARY KEY,
            game_id VARCHAR(50),
            season INTEGER,
            season_type VARCHAR(20),
            game_date DATE,
            team_id VARCHAR(20),
            player_id VARCHAR(20),
            player_name VARCHAR(200),
            minutes VARCHAR(20),
            fgm INTEGER,
            fga INTEGER,
            fg3m INTEGER,
            fg3a INTEGER,
            ftm INTEGER,
            fta INTEGER,
            oreb INTEGER,
            dreb INTEGER,
            reb INTEGER,
            ast INTEGER,
            stl INTEGER,
            blk INTEGER,
            tov INTEGER,
            pf INTEGER,
            pts INTEGER,
            plus_minus INTEGER,
            starter BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_hoopr_player_box_game ON hoopr_player_box(game_id);
        CREATE INDEX idx_hoopr_player_box_player ON hoopr_player_box(player_id);
        CREATE INDEX idx_hoopr_player_box_season ON hoopr_player_box(season);
    """
    )

    conn.commit()
    log("✅ Created hoopr_player_box table")


def load_player_box_csv(conn, csv_path):
    """Load a single player box CSV file"""
    try:
        # Read CSV
        df = pd.read_csv(csv_path, low_memory=False)

        if TEST_MODE:
            df = df.head(1000)

        if len(df) == 0:
            return 0

        # Clean column names
        df.columns = [
            col.lower().replace(" ", "_").replace(".", "_") for col in df.columns
        ]

        # Map hoopR column names to our schema
        column_map = {
            "athlete_id": "player_id",
            "athlete_display_name": "player_name",
            "field_goals_made": "fgm",
            "field_goals_attempted": "fga",
            "three_point_field_goals_made": "fg3m",
            "three_point_field_goals_attempted": "fg3a",
            "free_throws_made": "ftm",
            "free_throws_attempted": "fta",
            "offensive_rebounds": "oreb",
            "defensive_rebounds": "dreb",
            "rebounds": "reb",
            "assists": "ast",
            "steals": "stl",
            "blocks": "blk",
            "turnovers": "tov",
            "fouls": "pf",
            "points": "pts",
        }
        df.rename(columns=column_map, inplace=True)

        # Clean data quality issues
        # Replace "--" and empty strings with None for numeric columns
        numeric_cols = [
            "fgm",
            "fga",
            "fg3m",
            "fg3a",
            "ftm",
            "fta",
            "oreb",
            "dreb",
            "reb",
            "ast",
            "stl",
            "blk",
            "tov",
            "pf",
            "pts",
            "plus_minus",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].replace(["--", "", "NA", "N/A"], None)
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Convert player_id and team_id to string (handle large integers)
        if "player_id" in df.columns:
            df["player_id"] = df["player_id"].astype(str).replace("nan", None)
        if "team_id" in df.columns:
            df["team_id"] = df["team_id"].astype(str).replace("nan", None)
        if "game_id" in df.columns:
            df["game_id"] = df["game_id"].astype(str).replace("nan", None)

        # Convert starter to boolean
        if "starter" in df.columns:
            df["starter"] = df["starter"].fillna(False).astype(bool)

        # Select only columns we need
        keep_cols = [
            "game_id",
            "season",
            "season_type",
            "game_date",
            "team_id",
            "player_id",
            "player_name",
            "minutes",
            "fgm",
            "fga",
            "fg3m",
            "fg3a",
            "ftm",
            "fta",
            "oreb",
            "dreb",
            "reb",
            "ast",
            "stl",
            "blk",
            "tov",
            "pf",
            "pts",
            "plus_minus",
            "starter",
        ]
        df = df[[col for col in keep_cols if col in df.columns]]

        # Drop rows with no player_id or game_id
        df = df.dropna(subset=["player_id", "game_id"])

        # Convert DataFrame to native Python types (psycopg2 can't handle numpy types)
        df = df.astype(object).where(pd.notnull(df), None)

        # Insert data in batches
        cur = conn.cursor()
        columns = df.columns.tolist()
        values = [tuple(row) for row in df.values]

        cols_str = ", ".join(columns)
        insert_query = f"INSERT INTO hoopr_player_box ({cols_str}) VALUES %s ON CONFLICT DO NOTHING"

        for i in range(0, len(values), BATCH_SIZE):
            batch = values[i : i + BATCH_SIZE]
            execute_values(cur, insert_query, batch)

        conn.commit()
        return len(df)

    except Exception as e:
        log(f"  ❌ Error loading {os.path.basename(csv_path)}: {e}")
        conn.rollback()
        return 0


def main():
    """Main loading function"""
    log("=" * 80)
    log("hoopR Player Box Scores Loader")
    log("=" * 80)
    log(f"Test mode: {TEST_MODE}")
    log("")

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        log("✅ Connected to PostgreSQL")
    except Exception as e:
        log(f"❌ Failed to connect: {e}")
        return

    # Create table
    create_player_box_table(conn)

    # Load player box scores
    log("\n" + "=" * 80)
    log("Loading player box scores...")
    log("=" * 80)

    player_box_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "bulk_player_box", "*.csv"))
    )
    total_rows = 0

    for csv_file in player_box_files:
        season = (
            os.path.basename(csv_file).replace("player_box_", "").replace(".csv", "")
        )
        rows = load_player_box_csv(conn, csv_file)
        total_rows += rows
        log(f"  ✅ Season {season}: {rows:,} player-games")

    # Summary
    log("\n" + "=" * 80)
    log("✅ LOAD COMPLETE")
    log("=" * 80)
    log(f"Total player-game records loaded: {total_rows:,}")
    log("")
    log("Verify with:")
    log("  SELECT COUNT(*) FROM hoopr_player_box;")
    log("  SELECT COUNT(DISTINCT game_id) FROM hoopr_player_box;")
    log("  SELECT COUNT(DISTINCT player_id) FROM hoopr_player_box;")
    log("")

    conn.close()


if __name__ == "__main__":
    main()
