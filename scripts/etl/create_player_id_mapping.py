#!/usr/bin/env python3
"""
Create Player ID Mapping: ESPN ↔ NBA API

Matches players across data sources by:
1. Finding overlapping games (by date + teams)
2. Matching player names within those games
3. Building a mapping table

Usage:
    python scripts/etl/create_player_id_mapping.py --limit 100  # Test on 100 games
    python scripts/etl/create_player_id_mapping.py              # Process all overlapping games
"""

import os
import sys
import json
import psycopg2
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import logging
from difflib import SequenceMatcher


def string_similarity(a, b):
    """Calculate similarity between two strings (0-100)"""
    return int(SequenceMatcher(None, a, b).ratio() * 100)


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database config
DB_CONFIG = {
    "host": "localhost",
    "database": "nba_simulator",
    "user": "ryanranft",
    "port": 5432,
}

# ESPN data paths
ESPN_BOX_SCORE_DIR = Path("/Users/ryanranft/nba-simulator-aws/data/nba_box_score")


def normalize_name(name):
    """Normalize player name for matching"""
    if not name:
        return ""

    # Remove Jr., Sr., III, etc.
    name = (
        name.replace(" Jr.", "")
        .replace(" Sr.", "")
        .replace(" III", "")
        .replace(" II", "")
    )

    # Lowercase and strip
    name = name.lower().strip()

    # Remove periods (for initials)
    name = name.replace(".", "")

    return name


def extract_espn_players(box_score_path):
    """Extract player roster from ESPN box score JSON"""
    players = []

    try:
        with open(box_score_path, "r") as f:
            data = json.load(f)

        # Navigate to gamepackage
        gp = data.get("page", {}).get("content", {}).get("gamepackage", {})

        # Get game date and teams
        game_date = gp.get("gmStrp", {}).get("dt")
        espn_game_id = str(gp.get("gmStrp", {}).get("gid", ""))

        # Extract players from box score
        bxscr = gp.get("bxscr", [])

        # bxscr can be either a dict with 'tms' key or a list of team objects
        if isinstance(bxscr, list):
            # New format: list of team objects with 'tm' and 'stats' keys
            for team_data in bxscr:
                team = team_data.get("tm", {})
                team_id = team.get("id")
                team_abbr = team.get("abbrev")

                stats = team_data.get("stats", [])
                for stats_section in stats:
                    # Each stats section has an 'athlts' (athletes) list
                    athletes = stats_section.get("athlts", [])
                    for athlete_data in athletes:
                        athlete = athlete_data.get("athlt", {})
                        player_id = athlete.get("id")
                        full_name = athlete.get("dspNm")

                        if player_id and full_name:
                            players.append(
                                {
                                    "espn_player_id": str(player_id),
                                    "player_name": full_name,
                                    "normalized_name": normalize_name(full_name),
                                    "team_id_espn": team_id,
                                    "team_abbr": team_abbr,
                                    "espn_game_id": espn_game_id,
                                    "game_date": game_date,
                                }
                            )

        elif isinstance(bxscr, dict) and "tms" in bxscr:
            # Old format: dict with 'tms' key
            for team in bxscr["tms"]:
                team_id = team.get("id")
                team_abbr = team.get("abbrev")

                if "plrs" in team:
                    for player_section in team["plrs"]:
                        if "stats" in player_section:
                            for player_data in player_section["stats"]:
                                athlete = player_data.get("athlete", {})

                                player_id = athlete.get("id")
                                full_name = athlete.get("displayName")

                                if player_id and full_name:
                                    players.append(
                                        {
                                            "espn_player_id": str(player_id),
                                            "player_name": full_name,
                                            "normalized_name": normalize_name(
                                                full_name
                                            ),
                                            "team_id_espn": team_id,
                                            "team_abbr": team_abbr,
                                            "espn_game_id": espn_game_id,
                                            "game_date": game_date,
                                        }
                                    )

        return players, game_date, espn_game_id

    except Exception as e:
        logger.error(f"Error extracting from {box_score_path.name}: {e}")
        return [], None, None


def get_nba_api_games_with_players(conn, limit=None):
    """Get NBA API games with player rosters from box scores"""

    # Try hoopr_player_box first (if available)
    query = """
        WITH game_players AS (
            SELECT DISTINCT
                bs.game_id,
                bs.game_date,
                bs.player_id as nba_player_id,
                bs.player_name,
                bs.team_id as nba_team_id,
                bs.team_id as team_abbreviation
            FROM hoopr_player_box bs
            WHERE bs.player_name IS NOT NULL
        )
        SELECT
            game_id,
            game_date,
            nba_player_id,
            player_name,
            nba_team_id,
            team_abbreviation
        FROM game_players
        ORDER BY game_date DESC, game_id
    """

    if limit:
        query += f" LIMIT {limit * 20}"  # Assume ~20 players per game

    try:
        df = pd.read_sql(query, conn)
        logger.info(f"Found {len(df):,} player-game records from hoopr/NBA API")
        return df
    except Exception as e:
        logger.warning(f"Could not load NBA API data: {e}")
        logger.info("Returning empty DataFrame - will skip NBA API mapping")
        return pd.DataFrame(
            columns=[
                "game_id",
                "game_date",
                "nba_player_id",
                "player_name",
                "nba_team_id",
                "team_abbreviation",
            ]
        )


def match_games_by_date_teams(espn_players_df, nba_players_df):
    """Match games across sources by date and teams"""

    # Group ESPN players by game
    espn_games = (
        espn_players_df.groupby(["espn_game_id", "game_date"])
        .agg({"team_abbr": lambda x: set(x)})
        .reset_index()
    )

    # Group NBA players by game
    nba_games = (
        nba_players_df.groupby(["game_id", "game_date"])
        .agg({"team_abbreviation": lambda x: set(x)})
        .reset_index()
    )

    matches = []

    for _, espn_game in espn_games.iterrows():
        espn_date = (
            pd.to_datetime(espn_game["game_date"]).date()
            if espn_game["game_date"]
            else None
        )

        if not espn_date:
            continue

        # Find NBA games on same date
        nba_same_date = nba_games[nba_games["game_date"] == espn_date]

        for _, nba_game in nba_same_date.iterrows():
            # Check if teams match (allow for abbreviation differences)
            espn_teams = espn_game["team_abbr"]
            nba_teams = nba_game["team_abbreviation"]

            # Simple team match (can be improved)
            if len(espn_teams & nba_teams) >= 1:  # At least one team matches
                matches.append(
                    {
                        "espn_game_id": espn_game["espn_game_id"],
                        "nba_game_id": nba_game["game_id"],
                        "game_date": espn_date,
                    }
                )

    logger.info(f"Matched {len(matches):,} games across data sources")

    return pd.DataFrame(matches)


def match_players_within_games(espn_players_df, nba_players_df, game_matches_df):
    """Match players by name within matched games"""

    player_mappings = []

    for _, game_match in game_matches_df.iterrows():
        espn_game_id = game_match["espn_game_id"]
        nba_game_id = game_match["nba_game_id"]

        # Get players for this game from each source
        espn_players = espn_players_df[espn_players_df["espn_game_id"] == espn_game_id]
        nba_players = nba_players_df[nba_players_df["game_id"] == nba_game_id]

        # Match players by normalized name
        for _, espn_player in espn_players.iterrows():
            espn_norm = espn_player["normalized_name"]

            for _, nba_player in nba_players.iterrows():
                nba_norm = normalize_name(nba_player["player_name"])

                # String similarity match (allow for slight variations)
                similarity = string_similarity(espn_norm, nba_norm)

                if similarity >= 85:  # 85% similarity threshold
                    player_mappings.append(
                        {
                            "espn_player_id": espn_player["espn_player_id"],
                            "nba_player_id": str(nba_player["nba_player_id"]),
                            "player_name_espn": espn_player["player_name"],
                            "player_name_nba": nba_player["player_name"],
                            "normalized_name": espn_norm,
                            "similarity_score": similarity,
                            "espn_game_id": espn_game_id,
                            "nba_game_id": nba_game_id,
                            "game_date": game_match["game_date"],
                        }
                    )
                    break  # Found match, move to next ESPN player

    logger.info(f"Matched {len(player_mappings):,} players across data sources")

    return pd.DataFrame(player_mappings)


def create_mapping_table(conn, mappings_df):
    """Create player ID mapping table in database"""

    cur = conn.cursor()

    # Create table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_id_mapping (
            espn_player_id VARCHAR(50),
            nba_player_id VARCHAR(50),
            player_name_espn VARCHAR(200),
            player_name_nba VARCHAR(200),
            normalized_name VARCHAR(200),
            similarity_score INTEGER,
            first_seen_game_id VARCHAR(50),
            first_seen_date DATE,
            match_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (espn_player_id, nba_player_id)
        );

        CREATE INDEX IF NOT EXISTS idx_player_mapping_espn ON player_id_mapping(espn_player_id);
        CREATE INDEX IF NOT EXISTS idx_player_mapping_nba ON player_id_mapping(nba_player_id);
    """
    )

    conn.commit()

    # Group by player IDs (deduplicate across multiple games)
    unique_mappings = (
        mappings_df.groupby(["espn_player_id", "nba_player_id"])
        .agg(
            {
                "player_name_espn": "first",
                "player_name_nba": "first",
                "normalized_name": "first",
                "similarity_score": "max",
                "espn_game_id": "first",
                "game_date": "min",
                "nba_game_id": "count",  # Count number of games matched
            }
        )
        .reset_index()
    )

    unique_mappings.columns = [
        "espn_player_id",
        "nba_player_id",
        "player_name_espn",
        "player_name_nba",
        "normalized_name",
        "similarity_score",
        "first_seen_game_id",
        "first_seen_date",
        "match_count",
    ]

    logger.info(f"Inserting {len(unique_mappings):,} unique player mappings...")

    # Insert mappings
    for _, row in unique_mappings.iterrows():
        cur.execute(
            """
            INSERT INTO player_id_mapping (
                espn_player_id, nba_player_id, player_name_espn, player_name_nba,
                normalized_name, similarity_score, first_seen_game_id, first_seen_date, match_count
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (espn_player_id, nba_player_id)
            DO UPDATE SET
                match_count = player_id_mapping.match_count + EXCLUDED.match_count,
                similarity_score = GREATEST(player_id_mapping.similarity_score, EXCLUDED.similarity_score)
        """,
            (
                row["espn_player_id"],
                row["nba_player_id"],
                row["player_name_espn"],
                row["player_name_nba"],
                row["normalized_name"],
                row["similarity_score"],
                row["first_seen_game_id"],
                row["first_seen_date"],
                row["match_count"],
            ),
        )

    conn.commit()

    logger.info(
        f"✅ Created mapping table with {len(unique_mappings):,} unique player pairs"
    )

    return unique_mappings


def main():
    parser = argparse.ArgumentParser(
        description="Create ESPN ↔ NBA API player ID mapping"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of ESPN box scores to process"
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Player ID Mapping Creator: ESPN ↔ NBA API")
    logger.info("=" * 80)

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)

    # Step 1: Get NBA API players
    logger.info("\nStep 1: Loading NBA API player-game data...")
    nba_players_df = get_nba_api_games_with_players(conn, limit=args.limit)

    # Step 2: Load ESPN players from box scores
    logger.info("\nStep 2: Loading ESPN player-game data from box scores...")

    box_score_files = sorted(list(ESPN_BOX_SCORE_DIR.glob("*.json")))

    if args.limit:
        box_score_files = box_score_files[: args.limit]

    logger.info(f"Processing {len(box_score_files):,} ESPN box scores...")

    all_espn_players = []

    for i, box_score_file in enumerate(box_score_files):
        if (i + 1) % 1000 == 0:
            logger.info(f"  Processed {i+1:,}/{len(box_score_files):,} files...")

        players, game_date, espn_game_id = extract_espn_players(box_score_file)
        all_espn_players.extend(players)

    espn_players_df = pd.DataFrame(all_espn_players)

    logger.info(f"Found {len(espn_players_df):,} ESPN player-game records")

    # Step 3: Match games by date and teams
    logger.info("\nStep 3: Matching games across data sources...")
    game_matches_df = match_games_by_date_teams(espn_players_df, nba_players_df)

    # Step 4: Match players within matched games
    logger.info("\nStep 4: Matching players within games...")
    player_mappings_df = match_players_within_games(
        espn_players_df, nba_players_df, game_matches_df
    )

    # Step 5: Create database mapping table
    logger.info("\nStep 5: Creating player_id_mapping table...")

    if len(player_mappings_df) == 0:
        logger.warning("No player mappings found - skipping table creation")
        logger.warning(
            "This likely means no overlapping games were found between ESPN and NBA API data"
        )
        unique_mappings = pd.DataFrame()
    else:
        unique_mappings = create_mapping_table(conn, player_mappings_df)

    # Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("MAPPING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"ESPN box scores processed: {len(box_score_files):,}")
    logger.info(f"ESPN player-games found: {len(espn_players_df):,}")
    logger.info(f"NBA API player-games found: {len(nba_players_df):,}")
    logger.info(f"Games matched across sources: {len(game_matches_df):,}")
    logger.info(f"Total player matches: {len(player_mappings_df):,}")
    logger.info(f"Unique players mapped: {len(unique_mappings):,}")
    logger.info(
        f"Average similarity score: {unique_mappings['similarity_score'].mean():.1f}%"
    )
    logger.info("")
    logger.info("Sample mappings:")
    print(
        unique_mappings[
            [
                "espn_player_id",
                "nba_player_id",
                "player_name_espn",
                "player_name_nba",
                "similarity_score",
            ]
        ].head(10)
    )

    conn.close()

    logger.info("\n✅ Player ID mapping complete!")
    logger.info("\nQuery to test mapping:")
    logger.info("  SELECT * FROM player_id_mapping LIMIT 10;")


if __name__ == "__main__":
    main()
