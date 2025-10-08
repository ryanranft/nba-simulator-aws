#!/usr/bin/env python3
"""
Create team_id_mapping table by matching games across hoopR (ESPN IDs) and Kaggle (NBA API IDs).

Strategy:
1. Find games that appear in both sources (by date)
2. Match home/away teams to map ESPN team_id ↔ NBA API team_id
3. Build comprehensive 30-team mapping table
"""

import psycopg2
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Connect to local PostgreSQL database."""
    return psycopg2.connect(
        host="localhost",
        database="nba_simulator",
        user="ryanranft"
    )

def create_mapping_table(conn):
    """Create team_id_mapping table if it doesn't exist."""
    cursor = conn.cursor()

    # Drop if exists (for clean rebuild)
    cursor.execute("DROP TABLE IF EXISTS team_id_mapping CASCADE;")

    # Create table
    cursor.execute("""
        CREATE TABLE team_id_mapping (
            espn_team_id VARCHAR(10) PRIMARY KEY,
            nba_api_team_id VARCHAR(20) NOT NULL,
            team_name VARCHAR(100),
            team_abbr VARCHAR(5),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()
    logger.info("✓ Created team_id_mapping table")

def build_mapping(conn):
    """
    Build team ID mappings by matching games across data sources.

    Logic:
    - Find games on same date
    - Match home/away team pairs
    - Map ESPN team_id ↔ NBA API team_id
    """
    cursor = conn.cursor()

    # Query to match games by date and extract team ID pairs
    query = """
    WITH kaggle_games AS (
        SELECT DISTINCT
            game_date,
            home_team_id as kaggle_home,
            away_team_id as kaggle_away
        FROM games
        WHERE game_date >= '2002-01-01'  -- hoopR data starts 2002
    ),
    hoopr_games AS (
        SELECT DISTINCT
            game_date,
            game_id,
            array_agg(DISTINCT team_id ORDER BY team_id) as hoopr_teams
        FROM hoopr_player_box
        WHERE starter = true
        GROUP BY game_date, game_id
        HAVING COUNT(DISTINCT team_id) = 2  -- Exactly 2 teams
    )
    SELECT
        kg.game_date,
        kg.kaggle_home,
        kg.kaggle_away,
        hg.hoopr_teams[1] as hoopr_team_1,
        hg.hoopr_teams[2] as hoopr_team_2
    FROM kaggle_games kg
    JOIN hoopr_games hg ON kg.game_date = hg.game_date
    ORDER BY kg.game_date
    LIMIT 1000;  -- Sample for mapping (should cover all 30 teams)
    """

    cursor.execute(query)
    games = cursor.fetchall()

    logger.info(f"Found {len(games)} matching games for mapping")

    if not games:
        logger.error("No matching games found!")
        return {}

    # Build mapping dictionaries
    espn_to_nba = {}
    nba_to_espn = {}

    for game_date, kaggle_home, kaggle_away, hoopr_team_1, hoopr_team_2 in games:
        # ESPN teams (always 2)
        espn_teams = sorted([str(hoopr_team_1), str(hoopr_team_2)])
        # NBA API teams (always 2)
        nba_teams = sorted([str(kaggle_home), str(kaggle_away)])

        # Map each ESPN ID to NBA API ID
        for espn_id, nba_id in zip(espn_teams, nba_teams):
            if espn_id not in espn_to_nba:
                espn_to_nba[espn_id] = nba_id
                nba_to_espn[nba_id] = espn_id
                logger.debug(f"Mapped: ESPN {espn_id} → NBA API {nba_id}")
            else:
                # Verify consistency
                if espn_to_nba[espn_id] != nba_id:
                    logger.warning(
                        f"Inconsistent mapping on {game_date}: "
                        f"ESPN {espn_id} mapped to both {espn_to_nba[espn_id]} and {nba_id}"
                    )

    logger.info(f"✓ Built mapping for {len(espn_to_nba)} teams")
    cursor.close()

    return espn_to_nba

def insert_mappings(conn, mapping):
    """Insert team mappings into database."""
    cursor = conn.cursor()

    # Get team names from hoopr_player_box (sample one game per team)
    for espn_id, nba_id in mapping.items():
        cursor.execute("""
            SELECT player_name
            FROM hoopr_player_box
            WHERE team_id = %s
            LIMIT 1
        """, (espn_id,))

        result = cursor.fetchone()
        team_name = None  # We'll populate this later if needed

        cursor.execute("""
            INSERT INTO team_id_mapping (espn_team_id, nba_api_team_id, team_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (espn_team_id) DO UPDATE
            SET nba_api_team_id = EXCLUDED.nba_api_team_id
        """, (espn_id, nba_id, team_name))

    conn.commit()
    cursor.close()
    logger.info(f"✓ Inserted {len(mapping)} team mappings")

def verify_mapping(conn):
    """Verify the mapping table and show results."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT espn_team_id, nba_api_team_id, team_name
        FROM team_id_mapping
        ORDER BY espn_team_id::integer
    """)

    mappings = cursor.fetchall()

    print("\n" + "="*60)
    print("TEAM ID MAPPING TABLE")
    print("="*60)
    print(f"{'ESPN ID':<12} {'NBA API ID':<15} {'Team Name':<30}")
    print("-"*60)

    for espn_id, nba_id, team_name in mappings:
        team_name_str = team_name if team_name else "N/A"
        print(f"{espn_id:<12} {nba_id:<15} {team_name_str:<30}")

    print("-"*60)
    print(f"Total teams mapped: {len(mappings)}")
    print("="*60 + "\n")

    cursor.close()

def main():
    """Main execution."""
    logger.info("="*60)
    logger.info("Creating Team ID Mapping Table")
    logger.info("="*60)

    conn = get_db_connection()

    try:
        # Step 1: Create mapping table
        create_mapping_table(conn)

        # Step 2: Build mappings from game data
        mapping = build_mapping(conn)

        if not mapping:
            logger.error("Failed to build mapping - no matching games found")
            return

        # Step 3: Insert mappings
        insert_mappings(conn, mapping)

        # Step 4: Verify results
        verify_mapping(conn)

        logger.info("✓ Team ID mapping complete!")

    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    main()
