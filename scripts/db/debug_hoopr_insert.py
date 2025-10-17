#!/usr/bin/env python3
"""
Debug hoopR Player Box Insert - Single Row Testing

Tries to insert a single row with detailed logging to identify integer overflow issue.
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Database config
DB_CONFIG = {
    "host": "localhost",
    "dbname": "nba_simulator",
    "user": "ryanranft",
    "password": "",
    "port": 5432,
}


def debug_single_row():
    """Load and inspect a single row with detailed logging"""

    # Read just first row
    csv_path = "/tmp/hoopr_phase1/bulk_player_box/player_box_2024.csv"
    df = pd.read_csv(csv_path, low_memory=False, nrows=1)

    print("=" * 80)
    print("ORIGINAL CSV DATA (first row)")
    print("=" * 80)
    print(df.iloc[0].to_dict())
    print()

    # Clean column names
    df.columns = [col.lower().replace(" ", "_").replace(".", "_") for col in df.columns]

    # Map column names
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

    # Clean numeric columns
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

    # Convert IDs to string
    if "player_id" in df.columns:
        df["player_id"] = df["player_id"].astype(str).replace("nan", None)
    if "team_id" in df.columns:
        df["team_id"] = df["team_id"].astype(str).replace("nan", None)
    if "game_id" in df.columns:
        df["game_id"] = df["game_id"].astype(str).replace("nan", None)

    # Convert starter to boolean
    if "starter" in df.columns:
        df["starter"] = df["starter"].fillna(False).astype(bool)

    # Select columns
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

    print("=" * 80)
    print("CLEANED DATA (ready for insert)")
    print("=" * 80)
    columns = df.columns.tolist()
    row = df.iloc[0]

    for col in columns:
        value = row[col]
        value_type = type(value).__name__

        # Check if this could cause integer overflow
        warning = ""
        if value_type in ["int64", "float64"] and pd.notna(value):
            if abs(value) > 2147483647:  # PostgreSQL INTEGER max
                warning = " ⚠️  OVERFLOW - exceeds INTEGER range!"

        print(f"{col:20} = {value!r:30} (type: {value_type}){warning}")

    print()
    print("=" * 80)
    print("ATTEMPTING DATABASE INSERT")
    print("=" * 80)

    # Try to insert
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Build insert query
        cols_str = ", ".join(columns)
        insert_query = f"INSERT INTO hoopr_player_box ({cols_str}) VALUES %s"

        print(f"Query: {insert_query}")
        print()

        values = [tuple(row)]
        print(f"Values to insert: {values}")
        print()

        execute_values(cur, insert_query, values)
        conn.commit()

        print("✅ SUCCESS - Row inserted!")

        # Verify
        cur.execute("SELECT * FROM hoopr_player_box ORDER BY id DESC LIMIT 1")
        result = cur.fetchone()
        print()
        print("Inserted row:")
        print(result)

        conn.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Error details:")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_single_row()
