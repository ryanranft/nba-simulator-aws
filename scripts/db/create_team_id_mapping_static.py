#!/usr/bin/env python3
"""
Create team_id_mapping table using static NBA team ID mappings.

ESPN uses short team IDs (1-30) while NBA API uses long IDs (1610612xxx).
This script creates the authoritative mapping between these two systems.
"""

import psycopg2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Static mapping: ESPN team_id → (NBA API team_id, team_name, team_abbr)
# Source: https://github.com/swar/nba_api/blob/master/docs/table_of_contents.md
TEAM_MAPPINGS = {
    "1": ("1610612737", "Atlanta Hawks", "ATL"),
    "2": ("1610612738", "Boston Celtics", "BOS"),
    "3": ("1610612739", "Cleveland Cavaliers", "CLE"),
    "4": ("1610612740", "New Orleans Pelicans", "NOP"),  # formerly Hornets
    "5": ("1610612741", "Chicago Bulls", "CHI"),
    "6": ("1610612742", "Dallas Mavericks", "DAL"),
    "7": ("1610612743", "Denver Nuggets", "DEN"),
    "8": ("1610612745", "Houston Rockets", "HOU"),
    "9": ("1610612744", "Golden State Warriors", "GSW"),
    "10": ("1610612746", "LA Clippers", "LAC"),
    "11": ("1610612747", "Los Angeles Lakers", "LAL"),
    "12": ("1610612748", "Miami Heat", "MIA"),
    "13": ("1610612749", "Milwaukee Bucks", "MIL"),
    "14": ("1610612750", "Minnesota Timberwolves", "MIN"),
    "15": ("1610612751", "Brooklyn Nets", "BKN"),  # formerly NJ Nets
    "16": ("1610612752", "New York Knicks", "NYK"),
    "17": ("1610612753", "Orlando Magic", "ORL"),
    "18": ("1610612754", "Indiana Pacers", "IND"),
    "19": ("1610612755", "Philadelphia 76ers", "PHI"),
    "20": ("1610612756", "Phoenix Suns", "PHX"),
    "21": ("1610612757", "Portland Trail Blazers", "POR"),
    "22": ("1610612758", "Sacramento Kings", "SAC"),
    "23": ("1610612759", "San Antonio Spurs", "SAS"),
    "24": ("1610612760", "Oklahoma City Thunder", "OKC"),  # formerly Seattle
    "25": ("1610612761", "Toronto Raptors", "TOR"),
    "26": ("1610612762", "Utah Jazz", "UTA"),
    "27": ("1610612763", "Memphis Grizzlies", "MEM"),  # formerly Vancouver
    "28": ("1610612764", "Washington Wizards", "WAS"),
    "29": ("1610612765", "Detroit Pistons", "DET"),
    "30": ("1610612766", "Charlotte Hornets", "CHA"),  # expansion team
}


def get_db_connection():
    """Connect to local PostgreSQL database."""
    return psycopg2.connect(
        host="localhost", database="nba_simulator", user="ryanranft"
    )


def create_mapping_table(conn):
    """Create team_id_mapping table if it doesn't exist."""
    cursor = conn.cursor()

    # Drop if exists (for clean rebuild)
    cursor.execute("DROP TABLE IF EXISTS team_id_mapping CASCADE;")

    # Create table
    cursor.execute(
        """
        CREATE TABLE team_id_mapping (
            espn_team_id VARCHAR(10) PRIMARY KEY,
            nba_api_team_id VARCHAR(20) NOT NULL,
            team_name VARCHAR(100),
            team_abbr VARCHAR(5),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    conn.commit()
    cursor.close()
    logger.info("✓ Created team_id_mapping table")


def insert_mappings(conn):
    """Insert static team mappings into database."""
    cursor = conn.cursor()

    for espn_id, (nba_id, team_name, team_abbr) in TEAM_MAPPINGS.items():
        cursor.execute(
            """
            INSERT INTO team_id_mapping (espn_team_id, nba_api_team_id, team_name, team_abbr)
            VALUES (%s, %s, %s, %s)
        """,
            (espn_id, nba_id, team_name, team_abbr),
        )

    conn.commit()
    cursor.close()
    logger.info(f"✓ Inserted {len(TEAM_MAPPINGS)} team mappings")


def verify_mapping(conn):
    """Verify the mapping table and show results."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT espn_team_id, nba_api_team_id, team_name, team_abbr
        FROM team_id_mapping
        ORDER BY espn_team_id::integer
    """
    )

    mappings = cursor.fetchall()

    print("\n" + "=" * 80)
    print("TEAM ID MAPPING TABLE (ESPN ↔ NBA API)")
    print("=" * 80)
    print(f"{'ESPN ID':<12} {'NBA API ID':<15} {'Abbr':<6} {'Team Name':<40}")
    print("-" * 80)

    for espn_id, nba_id, team_name, team_abbr in mappings:
        print(f"{espn_id:<12} {nba_id:<15} {team_abbr:<6} {team_name:<40}")

    print("-" * 80)
    print(f"Total teams mapped: {len(mappings)}/30")
    print("=" * 80 + "\n")

    cursor.close()


def test_known_matchup(conn):
    """Test mapping with known game (2022-06-16 Finals Game 6)."""
    cursor = conn.cursor()

    print("Testing with known matchup: 2022 NBA Finals Game 6")
    print("-" * 60)

    # Get hoopR teams (ESPN IDs)
    cursor.execute(
        """
        SELECT DISTINCT team_id
        FROM hoopr_player_box
        WHERE game_date = '2022-06-16'
        ORDER BY team_id
    """
    )
    hoopr_teams = [row[0] for row in cursor.fetchall()]

    # Get Kaggle teams (NBA API IDs)
    cursor.execute(
        """
        SELECT home_team_id, away_team_id
        FROM games
        WHERE game_date = '2022-06-16'
    """
    )
    kaggle_result = cursor.fetchone()

    if kaggle_result:
        kaggle_home, kaggle_away = kaggle_result
        kaggle_teams = sorted([kaggle_home, kaggle_away])

        print(f"hoopR teams (ESPN):  {hoopr_teams}")
        print(f"Kaggle teams (NBA API): {kaggle_teams}")
        print()

        # Map ESPN to NBA API
        for espn_id in hoopr_teams:
            cursor.execute(
                """
                SELECT nba_api_team_id, team_name, team_abbr
                FROM team_id_mapping
                WHERE espn_team_id = %s
            """,
                (espn_id,),
            )
            result = cursor.fetchone()
            if result:
                nba_id, team_name, abbr = result
                status = "✓" if nba_id in kaggle_teams else "✗"
                print(
                    f"{status} ESPN {espn_id} → NBA API {nba_id} ({abbr} {team_name})"
                )

    cursor.close()
    print("-" * 60 + "\n")


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("Creating Team ID Mapping Table (Static)")
    logger.info("=" * 60)

    conn = get_db_connection()

    try:
        # Step 1: Create mapping table
        create_mapping_table(conn)

        # Step 2: Insert static mappings
        insert_mappings(conn)

        # Step 3: Verify results
        verify_mapping(conn)

        # Step 4: Test with known matchup
        test_known_matchup(conn)

        logger.info("✓ Team ID mapping complete!")

    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
