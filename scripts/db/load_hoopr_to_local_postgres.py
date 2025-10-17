#!/usr/bin/env python3
"""
Load hoopR Phase 1 Data to Local PostgreSQL

Loads all hoopR CSV files from /tmp/hoopr_phase1/ to local PostgreSQL database.
Creates separate tables for each data category.

Usage:
    python scripts/db/load_hoopr_to_local_postgres.py [--test]

Options:
    --test    Load only 1000 rows per file for testing
"""

import os
import sys
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "nba_simulator",
    "user": "ryanranft",
    "port": 5432,
}

# Data directory
DATA_DIR = "/tmp/hoopr_phase1"

# Test mode flag
TEST_MODE = "--test" in sys.argv
BATCH_SIZE = 10000


def log(message):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def create_tables(conn):
    """Create tables for hoopR data"""
    cur = conn.cursor()

    log("Creating hoopR tables...")

    # hoopR play-by-play (will be very large - same schema as temporal_events)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_play_by_play (
            id SERIAL PRIMARY KEY,
            game_id VARCHAR(50),
            season INTEGER,
            game_date DATE,
            event_num INTEGER,
            period INTEGER,
            clock VARCHAR(20),
            team_id VARCHAR(20),
            player_id VARCHAR(20),
            event_type VARCHAR(100),
            description TEXT,
            score_home INTEGER,
            score_away INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_game ON hoopr_play_by_play(game_id);
        CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_season ON hoopr_play_by_play(season);
    """
    )

    # hoopR player box scores
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
            fg_pct DECIMAL(5,3),
            fg3m INTEGER,
            fg3a INTEGER,
            fg3_pct DECIMAL(5,3),
            ftm INTEGER,
            fta INTEGER,
            ft_pct DECIMAL(5,3),
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

    # hoopR team box scores
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_team_box (
            id SERIAL PRIMARY KEY,
            game_id VARCHAR(50),
            season INTEGER,
            game_date DATE,
            team_id VARCHAR(20),
            team_name VARCHAR(200),
            fgm INTEGER,
            fga INTEGER,
            fg_pct DECIMAL(5,3),
            fg3m INTEGER,
            fg3a INTEGER,
            fg3_pct DECIMAL(5,3),
            ftm INTEGER,
            fta INTEGER,
            ft_pct DECIMAL(5,3),
            oreb INTEGER,
            dreb INTEGER,
            reb INTEGER,
            ast INTEGER,
            stl INTEGER,
            blk INTEGER,
            tov INTEGER,
            pf INTEGER,
            pts INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_team_box_game ON hoopr_team_box(game_id);
        CREATE INDEX IF NOT EXISTS idx_hoopr_team_box_season ON hoopr_team_box(season);
    """
    )

    # hoopR schedule
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_schedule (
            id SERIAL PRIMARY KEY,
            game_id VARCHAR(50) UNIQUE,
            season INTEGER,
            game_date DATE,
            home_team_id VARCHAR(20),
            away_team_id VARCHAR(20),
            home_team_name VARCHAR(200),
            away_team_name VARCHAR(200),
            home_score INTEGER,
            away_score INTEGER,
            game_status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_schedule_season ON hoopr_schedule(season);
        CREATE INDEX IF NOT EXISTS idx_hoopr_schedule_date ON hoopr_schedule(game_date);
    """
    )

    # hoopR league player stats (per season aggregated stats)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_league_player_stats (
            id SERIAL PRIMARY KEY,
            season INTEGER,
            player_id VARCHAR(20),
            player_name VARCHAR(200),
            team_id VARCHAR(20),
            games_played INTEGER,
            minutes DECIMAL(8,2),
            pts DECIMAL(8,2),
            reb DECIMAL(8,2),
            ast DECIMAL(8,2),
            stl DECIMAL(8,2),
            blk DECIMAL(8,2),
            tov DECIMAL(8,2),
            fg_pct DECIMAL(5,3),
            fg3_pct DECIMAL(5,3),
            ft_pct DECIMAL(5,3),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_league_player_season ON hoopr_league_player_stats(season);
        CREATE INDEX IF NOT EXISTS idx_hoopr_league_player_id ON hoopr_league_player_stats(player_id);
    """
    )

    # hoopR league team stats (per season aggregated stats)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_league_team_stats (
            id SERIAL PRIMARY KEY,
            season INTEGER,
            team_id VARCHAR(20),
            team_name VARCHAR(200),
            games_played INTEGER,
            wins INTEGER,
            losses INTEGER,
            win_pct DECIMAL(5,3),
            pts DECIMAL(8,2),
            opp_pts DECIMAL(8,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_league_team_season ON hoopr_league_team_stats(season);
    """
    )

    # hoopR lineups (5-man lineups)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_lineups (
            id SERIAL PRIMARY KEY,
            season INTEGER,
            team_id VARCHAR(20),
            lineup VARCHAR(500),
            minutes DECIMAL(8,2),
            pts DECIMAL(8,2),
            opp_pts DECIMAL(8,2),
            plus_minus DECIMAL(8,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_lineups_season ON hoopr_lineups(season);
    """
    )

    # hoopR standings
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hoopr_standings (
            id SERIAL PRIMARY KEY,
            season INTEGER,
            team_id VARCHAR(20),
            team_name VARCHAR(200),
            wins INTEGER,
            losses INTEGER,
            win_pct DECIMAL(5,3),
            conference_rank INTEGER,
            division_rank INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_hoopr_standings_season ON hoopr_standings(season);
    """
    )

    conn.commit()
    log("✅ Tables created successfully")


def load_csv_to_table(conn, csv_path, table_name, season=None):
    """Load a single CSV file into a table"""
    try:
        # Read CSV
        df = pd.read_csv(csv_path, low_memory=False)

        if TEST_MODE:
            df = df.head(1000)

        if len(df) == 0:
            log(f"  ⚠️  Empty file: {os.path.basename(csv_path)}")
            return 0

        # Add season column if provided
        if season is not None and "season" not in df.columns:
            df["season"] = season

        # Clean column names (lowercase, replace spaces with underscores)
        df.columns = [
            col.lower().replace(" ", "_").replace(".", "_") for col in df.columns
        ]

        # Table-specific column mappings
        if table_name == "hoopr_play_by_play":
            # Map hoopR CSV columns to database schema
            column_map = {
                "sequence_number": "event_num",
                "type_text": "event_type",
                "text": "description",
                "period": "period",
                "clock_display_value": "clock",
                "athlete_id_1": "player_id",
                "home_score": "score_home",
                "away_score": "score_away",
            }
            df.rename(columns=column_map, inplace=True)

            # Convert IDs to string
            for col in ["game_id", "team_id", "player_id"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace("nan", None)

            # Select only columns that exist in schema
            keep_cols = [
                "game_id",
                "season",
                "game_date",
                "event_num",
                "period",
                "clock",
                "team_id",
                "player_id",
                "event_type",
                "description",
                "score_home",
                "score_away",
            ]
            df = df[[col for col in keep_cols if col in df.columns]]

        elif table_name == "hoopr_player_box":
            # Map hoopR column names to our database schema
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

            # Clean data quality issues - Replace "--" with None
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

            # Calculate percentages from made/attempted if not present
            if (
                "fg_pct" not in df.columns
                and "fgm" in df.columns
                and "fga" in df.columns
            ):
                df["fg_pct"] = (df["fgm"] / df["fga"]).where(df["fga"] > 0, None)
            if (
                "fg3_pct" not in df.columns
                and "fg3m" in df.columns
                and "fg3a" in df.columns
            ):
                df["fg3_pct"] = (df["fg3m"] / df["fg3a"]).where(df["fg3a"] > 0, None)
            if (
                "ft_pct" not in df.columns
                and "ftm" in df.columns
                and "fta" in df.columns
            ):
                df["ft_pct"] = (df["ftm"] / df["fta"]).where(df["fta"] > 0, None)

            # Convert IDs to string (handle large integers)
            for col in ["player_id", "team_id", "game_id"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace("nan", None)

            # Convert starter to boolean
            if "starter" in df.columns:
                df["starter"] = df["starter"].fillna(False).astype(bool)

            # Select only columns that exist in our schema
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
                "fg_pct",
                "fg3m",
                "fg3a",
                "fg3_pct",
                "ftm",
                "fta",
                "ft_pct",
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

        elif table_name == "hoopr_team_box":
            # Map hoopR column names to database schema
            column_map = {
                "field_goals_made": "fgm",
                "field_goals_attempted": "fga",
                "field_goal_pct": "fg_pct",
                "three_point_field_goals_made": "fg3m",
                "three_point_field_goals_attempted": "fg3a",
                "three_point_field_goal_pct": "fg3_pct",
                "free_throws_made": "ftm",
                "free_throws_attempted": "fta",
                "free_throw_pct": "ft_pct",
                "offensive_rebounds": "oreb",
                "defensive_rebounds": "dreb",
                "total_rebounds": "reb",
                "assists": "ast",
                "steals": "stl",
                "blocks": "blk",
                "turnovers": "tov",
                "fouls": "pf",
                "team_score": "pts",
            }
            df.rename(columns=column_map, inplace=True)

            # Convert IDs to string
            for col in ["game_id", "team_id"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace("nan", None)

            # Select only columns that exist in schema
            keep_cols = [
                "game_id",
                "season",
                "game_date",
                "team_id",
                "team_name",
                "fgm",
                "fga",
                "fg_pct",
                "fg3m",
                "fg3a",
                "fg3_pct",
                "ftm",
                "fta",
                "ft_pct",
                "oreb",
                "dreb",
                "reb",
                "ast",
                "stl",
                "blk",
                "tov",
                "pf",
                "pts",
            ]
            df = df[[col for col in keep_cols if col in df.columns]]

        elif table_name == "hoopr_schedule":
            # Map hoopR column names to database schema
            column_map = {
                "id": "game_id",
                "date": "game_date",
                "home_id": "home_team_id",
                "away_id": "away_team_id",
                "home_name": "home_team_name",
                "away_name": "away_team_name",
                "home_score": "home_score",
                "away_score": "away_score",
                "status_type_name": "game_status",
            }
            df.rename(columns=column_map, inplace=True)

            # Convert IDs to string
            for col in ["game_id", "home_team_id", "away_team_id"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace("nan", None)

            # Select only columns that exist in schema
            keep_cols = [
                "game_id",
                "season",
                "game_date",
                "home_team_id",
                "away_team_id",
                "home_team_name",
                "away_team_name",
                "home_score",
                "away_score",
                "game_status",
            ]
            df = df[[col for col in keep_cols if col in df.columns]]

        # Convert DataFrame to native Python types (psycopg2 can't handle numpy types)
        df = df.astype(object).where(pd.notnull(df), None)

        # Insert data in batches
        cur = conn.cursor()
        columns = df.columns.tolist()

        # Prepare values
        values = [tuple(row) for row in df.values]

        # Build INSERT query
        cols_str = ", ".join(columns)
        insert_query = (
            f"INSERT INTO {table_name} ({cols_str}) VALUES %s ON CONFLICT DO NOTHING"
        )

        # Execute in batches
        for i in range(0, len(values), BATCH_SIZE):
            batch = values[i : i + BATCH_SIZE]
            execute_values(cur, insert_query, batch)

        conn.commit()
        return len(df)

    except Exception as e:
        log(f"  ❌ Error loading {csv_path}: {e}")
        conn.rollback()
        return 0


def main():
    """Main loading function"""
    log("=" * 80)
    log("hoopR Data Loader - Local PostgreSQL")
    log("=" * 80)
    log(f"Data directory: {DATA_DIR}")
    log(f"Test mode: {TEST_MODE}")
    log("")

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        log("✅ Connected to PostgreSQL")
    except Exception as e:
        log(f"❌ Failed to connect to database: {e}")
        return

    # Create tables
    create_tables(conn)

    # Load data by category
    total_rows = 0

    # 1. Play-by-play (bulk_pbp/)
    log("\n" + "=" * 80)
    log("Loading play-by-play data...")
    log("=" * 80)
    pbp_files = sorted(glob.glob(os.path.join(DATA_DIR, "bulk_pbp", "*.csv")))
    for pbp_file in pbp_files:
        season = int(os.path.basename(pbp_file).replace("pbp_", "").replace(".csv", ""))
        rows = load_csv_to_table(conn, pbp_file, "hoopr_play_by_play", season)
        log(f"  ✅ Season {season}: {rows:,} events")
        total_rows += rows

    # 2. Player box scores (bulk_player_box/)
    log("\n" + "=" * 80)
    log("Loading player box scores...")
    log("=" * 80)
    player_box_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "bulk_player_box", "*.csv"))
    )
    for pbox_file in player_box_files:
        season = int(
            os.path.basename(pbox_file).replace("player_box_", "").replace(".csv", "")
        )
        rows = load_csv_to_table(conn, pbox_file, "hoopr_player_box", season)
        log(f"  ✅ Season {season}: {rows:,} player-games")
        total_rows += rows

    # 3. Team box scores (bulk_team_box/)
    log("\n" + "=" * 80)
    log("Loading team box scores...")
    log("=" * 80)
    team_box_files = sorted(glob.glob(os.path.join(DATA_DIR, "bulk_team_box", "*.csv")))
    for tbox_file in team_box_files:
        season = int(
            os.path.basename(tbox_file).replace("team_box_", "").replace(".csv", "")
        )
        rows = load_csv_to_table(conn, tbox_file, "hoopr_team_box", season)
        log(f"  ✅ Season {season}: {rows:,} team-games")
        total_rows += rows

    # 4. Schedule (bulk_schedule/)
    log("\n" + "=" * 80)
    log("Loading schedule...")
    log("=" * 80)
    schedule_files = sorted(glob.glob(os.path.join(DATA_DIR, "bulk_schedule", "*.csv")))
    for sched_file in schedule_files:
        season = int(
            os.path.basename(sched_file).replace("schedule_", "").replace(".csv", "")
        )
        rows = load_csv_to_table(conn, sched_file, "hoopr_schedule", season)
        log(f"  ✅ Season {season}: {rows:,} games")
        total_rows += rows

    # 5. League player stats (league_dashboards/player_stats_*)
    log("\n" + "=" * 80)
    log("Loading league player stats...")
    log("=" * 80)
    player_stats_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "league_dashboards", "player_stats_*.csv"))
    )
    for pstats_file in player_stats_files:
        season = int(
            os.path.basename(pstats_file)
            .replace("player_stats_", "")
            .replace(".csv", "")
        )
        rows = load_csv_to_table(conn, pstats_file, "hoopr_league_player_stats", season)
        log(f"  ✅ Season {season}: {rows:,} players")
        total_rows += rows

    # 6. League team stats (league_dashboards/team_stats_*)
    log("\n" + "=" * 80)
    log("Loading league team stats...")
    log("=" * 80)
    team_stats_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "league_dashboards", "team_stats_*.csv"))
    )
    for tstats_file in team_stats_files:
        season = int(
            os.path.basename(tstats_file).replace("team_stats_", "").replace(".csv", "")
        )
        rows = load_csv_to_table(conn, tstats_file, "hoopr_league_team_stats", season)
        log(f"  ✅ Season {season}: {rows:,} teams")
        total_rows += rows

    # 7. Lineups (league_dashboards/lineups_5man_*)
    log("\n" + "=" * 80)
    log("Loading lineups...")
    log("=" * 80)
    lineup_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "league_dashboards", "lineups_5man_*.csv"))
    )
    for lineup_file in lineup_files:
        season = int(
            os.path.basename(lineup_file)
            .replace("lineups_5man_", "")
            .replace(".csv", "")
        )
        rows = load_csv_to_table(conn, lineup_file, "hoopr_lineups", season)
        log(f"  ✅ Season {season}: {rows:,} lineups")
        total_rows += rows

    # 8. Standings (standings/standings_*)
    log("\n" + "=" * 80)
    log("Loading standings...")
    log("=" * 80)
    standings_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "standings", "standings_*.csv"))
    )
    for standings_file in standings_files:
        season = int(
            os.path.basename(standings_file)
            .replace("standings_", "")
            .replace(".csv", "")
        )
        rows = load_csv_to_table(conn, standings_file, "hoopr_standings", season)
        log(f"  ✅ Season {season}: {rows:,} teams")
        total_rows += rows

    # Summary
    log("\n" + "=" * 80)
    log("✅ LOAD COMPLETE")
    log("=" * 80)
    log(f"Total rows loaded: {total_rows:,}")
    log("")

    conn.close()


if __name__ == "__main__":
    main()
