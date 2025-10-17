#!/usr/bin/env python3
"""
ESPN PBP Data Loading Script

Processes validated ESPN PBP files and loads clean data into PostgreSQL.
Only processes files that have been validated as containing valid PBP data.

This script:
1. Queries the validation table for files with valid PBP data
2. Extracts game info and plays from validated files
3. Loads data into PostgreSQL with proper schema
4. Uses batch processing and checkpoints for reliability
5. Handles duplicates with ON CONFLICT DO UPDATE
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/espn_data_load.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        dbname=os.getenv("RDS_DB_NAME", "nba_simulator"),
        user=os.getenv("RDS_USERNAME", "ryanranft"),
        password=os.getenv("RDS_PASSWORD"),
        host=os.getenv("RDS_HOSTNAME", "localhost"),
        port=os.getenv("RDS_PORT", "5432"),
    )


def init_database():
    """Initialize database schema and tables"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create master schema if it doesn't exist
                cur.execute("CREATE SCHEMA IF NOT EXISTS master;")

                # Create games table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS master.nba_games (
                        game_id VARCHAR(20) PRIMARY KEY,
                        game_date TIMESTAMP WITH TIME ZONE NOT NULL,
                        season VARCHAR(10) NOT NULL,
                        home_team VARCHAR(100),
                        away_team VARCHAR(100),
                        home_abbrev VARCHAR(10),
                        away_abbrev VARCHAR(10),
                        final_score_home INTEGER,
                        final_score_away INTEGER,
                        source VARCHAR(20) DEFAULT 'ESPN',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """
                )

                # Create plays table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS master.nba_plays (
                        id BIGSERIAL PRIMARY KEY,
                        game_id VARCHAR(20) REFERENCES master.nba_games(game_id),
                        play_id VARCHAR(50),
                        sequence_number INTEGER NOT NULL,
                        period INTEGER NOT NULL,
                        clock VARCHAR(20),
                        team_abbrev VARCHAR(10),
                        player_name VARCHAR(100),
                        event_type VARCHAR(100),
                        description TEXT,
                        score_value INTEGER,
                        home_score INTEGER,
                        away_score INTEGER,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(game_id, sequence_number)
                    );
                """
                )

                # Create indexes for performance
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nba_games_season ON master.nba_games(season);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nba_games_date ON master.nba_games(game_date);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nba_plays_game_id ON master.nba_plays(game_id);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nba_plays_sequence ON master.nba_plays(game_id, sequence_number);"
                )

                conn.commit()
                logger.info("Database schema initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def determine_nba_season(game_date: datetime) -> str:
    """Determine NBA season from game date"""
    year = game_date.year
    month = game_date.month

    if month >= 10:  # Oct-Dec = start of season
        season = f"{year}-{str(year + 1)[2:]}"
    else:  # Jan-Sep = end of previous season
        season = f"{year - 1}-{str(year)[2:]}"

    return season


def get_validated_files(input_dir: Path) -> List[Dict]:
    """Get list of validated files from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT file_name, game_id, season, league, home_team, away_team
                    FROM master.espn_file_validation
                    WHERE has_pbp_data = TRUE
                    AND has_game_info = TRUE
                    AND has_team_data = TRUE
                    AND league = 'NBA'
                    ORDER BY season, game_id
                """
                )

                results = []
                for row in cur.fetchall():
                    results.append(
                        {
                            "file_name": row[0],
                            "game_id": row[1],
                            "season": row[2],
                            "league": row[3],
                            "home_team": row[4],
                            "away_team": row[5],
                            "file_path": input_dir / row[0],
                        }
                    )

                logger.info(f"Found {len(results)} validated NBA files to process")
                return results

    except Exception as e:
        logger.error(f"Error getting validated files: {e}")
        raise


def extract_game_info(data: Dict, game_id: str) -> Optional[Dict]:
    """Extract game metadata from ESPN data"""
    try:
        gamepackage = data["page"]["content"]["gamepackage"]

        # Get game date
        gm_info = gamepackage.get("gmInfo", {})
        game_date_str = gm_info.get("dtTm", "")

        if not game_date_str:
            logger.warning(f"No game date found for {game_id}")
            return None

        # Parse date
        try:
            game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            season = determine_nba_season(game_date)
        except Exception as e:
            logger.warning(f"Could not parse date {game_date_str} for {game_id}: {e}")
            return None

        # Get teams from PBP data
        pbp_data = gamepackage.get("pbp", {})
        teams_data = pbp_data.get("tms", {})
        home_team_data = teams_data.get("home", {})
        away_team_data = teams_data.get("away", {})

        if not home_team_data or not away_team_data:
            logger.warning(f"No team data found for {game_id}")
            return None

        home_team = home_team_data.get("displayName")
        away_team = away_team_data.get("displayName")
        home_abbrev = home_team_data.get("abbrev")
        away_abbrev = away_team_data.get("abbrev")
        final_score_home = home_team_data.get("score")
        final_score_away = away_team_data.get("score")

        return {
            "game_id": game_id,
            "game_date": game_date,
            "season": season,
            "home_team": home_team,
            "away_team": away_team,
            "home_abbrev": home_abbrev,
            "away_abbrev": away_abbrev,
            "final_score_home": final_score_home,
            "final_score_away": final_score_away,
        }

    except Exception as e:
        logger.error(f"Error extracting game info for {game_id}: {e}")
        return None


def extract_plays(gamepackage_data: Dict, game_info: Dict) -> List[Dict]:
    """Extract play-by-play events from ESPN data"""
    plays = []
    pbp_data = gamepackage_data.get("pbp", {})
    play_grps = pbp_data.get("playGrps", [])

    if not play_grps:
        logger.warning(f"No play groups found for {game_info['game_id']}")
        return []

    sequence_number = 0
    for period_index, period_plays in enumerate(play_grps):
        if not isinstance(period_plays, list):
            continue

        period_number = period_index + 1  # ESPN periods are 1-indexed

        for play_data in period_plays:
            if not isinstance(play_data, dict):
                continue

            sequence_number += 1

            play_id = play_data.get("id")
            clock = (
                play_data.get("clock", {}).get("displayValue")
                if isinstance(play_data.get("clock"), dict)
                else play_data.get("clock")
            )
            text = play_data.get("text", "")

            # Extract team info from text (ESPN format)
            team_abbrev = None
            player_name = None
            event_type = None

            # Try to parse team and player from text
            if text:
                # Common patterns in ESPN play text
                if "makes" in text or "misses" in text:
                    parts = text.split()
                    if len(parts) >= 2:
                        player_name = (
                            parts[0] + " " + parts[1] if len(parts) > 1 else parts[0]
                        )
                        if "makes" in text:
                            event_type = "Made Shot"
                        elif "misses" in text:
                            event_type = "Missed Shot"
                elif "rebound" in text.lower():
                    event_type = "Rebound"
                elif "assist" in text.lower():
                    event_type = "Assist"
                elif "turnover" in text.lower():
                    event_type = "Turnover"
                elif "foul" in text.lower():
                    event_type = "Foul"
                elif "substitution" in text.lower():
                    event_type = "Substitution"
                elif "timeout" in text.lower():
                    event_type = "Timeout"
                else:
                    event_type = "Other"

            score_value = None
            home_score = play_data.get("homeScore")
            away_score = play_data.get("awayScore")

            # Calculate score value if scores changed
            if (
                sequence_number > 1
                and home_score is not None
                and away_score is not None
            ):
                # This is a simplified calculation - in reality we'd need to track previous scores
                pass

            plays.append(
                {
                    "game_id": game_info["game_id"],
                    "play_id": play_id,
                    "sequence_number": sequence_number,
                    "period": period_number,
                    "clock": clock,
                    "team_abbrev": team_abbrev,
                    "player_name": player_name,
                    "event_type": event_type,
                    "description": text,
                    "score_value": score_value,
                    "home_score": home_score,
                    "away_score": away_score,
                }
            )

    return plays


def load_game_batch(conn, games: List[Dict]):
    """Load batch of games into PostgreSQL"""
    if not games:
        return

    with conn.cursor() as cur:
        execute_batch(
            cur,
            """
            INSERT INTO master.nba_games
            (game_id, game_date, season, home_team, away_team,
             home_abbrev, away_abbrev, final_score_home, final_score_away)
            VALUES (%(game_id)s, %(game_date)s, %(season)s, %(home_team)s,
                    %(away_team)s, %(home_abbrev)s, %(away_abbrev)s,
                    %(final_score_home)s, %(final_score_away)s)
            ON CONFLICT (game_id) DO UPDATE SET
                game_date = EXCLUDED.game_date,
                season = EXCLUDED.season,
                home_team = EXCLUDED.home_team,
                away_team = EXCLUDED.away_team,
                home_abbrev = EXCLUDED.home_abbrev,
                away_abbrev = EXCLUDED.away_abbrev,
                final_score_home = EXCLUDED.final_score_home,
                final_score_away = EXCLUDED.final_score_away,
                updated_at = CURRENT_TIMESTAMP
        """,
            games,
            page_size=1000,
        )
    conn.commit()


def load_plays_batch(conn, plays: List[Dict]):
    """Load batch of plays into PostgreSQL"""
    if not plays:
        return

    with conn.cursor() as cur:
        execute_batch(
            cur,
            """
            INSERT INTO master.nba_plays
            (game_id, play_id, sequence_number, period, clock, team_abbrev,
             player_name, event_type, description, score_value,
             home_score, away_score)
            VALUES (%(game_id)s, %(play_id)s, %(sequence_number)s, %(period)s,
                    %(clock)s, %(team_abbrev)s, %(player_name)s, %(event_type)s,
                    %(description)s, %(score_value)s, %(home_score)s, %(away_score)s)
            ON CONFLICT (game_id, sequence_number) DO NOTHING
        """,
            plays,
            page_size=1000,
        )
    conn.commit()


def save_checkpoint(checkpoint_file: Path, stats: Dict):
    """Save progress checkpoint"""
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_file, "w") as f:
        json.dump(stats, f, indent=2, default=str)


def load_checkpoint(checkpoint_file: Path) -> Dict:
    """Load progress checkpoint"""
    if checkpoint_file.exists():
        with open(checkpoint_file, "r") as f:
            return json.load(f)
    return {
        "games_processed": 0,
        "plays_loaded": 0,
        "errors_encountered": 0,
        "last_processed_file": None,
    }


def process_file(file_info: Dict) -> Tuple[Optional[Dict], List[Dict], Optional[str]]:
    """Process a single file and return game info, plays, and error message"""
    try:
        with open(file_info["file_path"], "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract game info
        game_info = extract_game_info(data, file_info["game_id"])
        if not game_info:
            return None, [], f"No game info extracted for {file_info['game_id']}"

        # Navigate to gamepackage for plays
        gamepackage = data["page"]["content"]["gamepackage"]

        # Extract plays
        plays = extract_plays(gamepackage, game_info)

        return game_info, plays, None

    except Exception as e:
        return None, [], f"Error processing {file_info['file_path']}: {str(e)}"


def main():
    parser = argparse.ArgumentParser(
        description="Load validated ESPN PBP data into PostgreSQL"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/nba_pbp",
        help="Directory containing ESPN PBP JSON files",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of records to process per batch",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=100,
        help="Save checkpoint every N games",
    )
    parser.add_argument(
        "--checkpoint-file",
        type=str,
        default="data/load_checkpoint.json",
        help="Checkpoint file path",
    )
    parser.add_argument(
        "--stats-file",
        type=str,
        default="data/load_statistics.json",
        help="Statistics file path",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    checkpoint_file = Path(args.checkpoint_file)
    stats_file = Path(args.stats_file)

    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        sys.exit(1)

    # Initialize database
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    # Get validated files
    try:
        validated_files = get_validated_files(input_dir)
    except Exception as e:
        logger.error(f"Failed to get validated files: {e}")
        sys.exit(1)

    if not validated_files:
        logger.warning("No validated files found to process")
        return

    # Load checkpoint
    checkpoint = load_checkpoint(checkpoint_file)
    start_index = checkpoint["games_processed"]

    logger.info(f"Starting from checkpoint: {start_index} games processed")
    logger.info(f"Processing {len(validated_files) - start_index} remaining files")

    # Initialize statistics
    stats = {
        "total_files": len(validated_files),
        "games_processed": checkpoint["games_processed"],
        "plays_loaded": checkpoint["plays_loaded"],
        "errors_encountered": checkpoint["errors_encountered"],
        "start_time": datetime.now().isoformat(),
        "season_breakdown": {},
    }

    # Process files
    games_batch = []
    plays_batch = []

    try:
        with get_db_connection() as conn:
            for i, file_info in enumerate(validated_files[start_index:], start_index):
                try:
                    # Process file
                    game_info, plays, error = process_file(file_info)

                    if error:
                        logger.warning(
                            f"Error processing {file_info['file_name']}: {error}"
                        )
                        stats["errors_encountered"] += 1
                        continue

                    if game_info:
                        games_batch.append(game_info)
                        plays_batch.extend(plays)

                        # Update season breakdown
                        season = game_info["season"]
                        if season not in stats["season_breakdown"]:
                            stats["season_breakdown"][season] = {"games": 0, "plays": 0}
                        stats["season_breakdown"][season]["games"] += 1
                        stats["season_breakdown"][season]["plays"] += len(plays)

                    # Load batches when they reach batch size
                    if len(games_batch) >= args.batch_size:
                        load_game_batch(conn, games_batch)
                        load_plays_batch(conn, plays_batch)

                        stats["games_processed"] += len(games_batch)
                        stats["plays_loaded"] += len(plays_batch)

                        logger.info(
                            f"Loaded batch: {len(games_batch)} games, {len(plays_batch)} plays"
                        )

                        games_batch = []
                        plays_batch = []

                    # Save checkpoint
                    if (i + 1) % args.checkpoint_interval == 0:
                        checkpoint = {
                            "games_processed": stats["games_processed"],
                            "plays_loaded": stats["plays_loaded"],
                            "errors_encountered": stats["errors_encountered"],
                            "last_processed_file": file_info["file_name"],
                        }
                        save_checkpoint(checkpoint_file, checkpoint)
                        logger.info(
                            f"Checkpoint saved: {i + 1}/{len(validated_files)} files processed"
                        )

                except Exception as e:
                    logger.error(
                        f"Unexpected error processing {file_info['file_name']}: {e}"
                    )
                    stats["errors_encountered"] += 1
                    continue

            # Load remaining batches
            if games_batch:
                load_game_batch(conn, games_batch)
                load_plays_batch(conn, plays_batch)

                stats["games_processed"] += len(games_batch)
                stats["plays_loaded"] += len(plays_batch)

                logger.info(
                    f"Loaded final batch: {len(games_batch)} games, {len(plays_batch)} plays"
                )

    except Exception as e:
        logger.error(f"Database error during processing: {e}")
        sys.exit(1)

    # Final statistics
    stats["end_time"] = datetime.now().isoformat()
    stats["duration_minutes"] = (
        datetime.fromisoformat(stats["end_time"])
        - datetime.fromisoformat(stats["start_time"])
    ).total_seconds() / 60

    # Save final statistics
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2, default=str)

    # Print summary
    logger.info("=" * 60)
    logger.info("LOAD SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {stats['total_files']:,}")
    logger.info(f"Games loaded: {stats['games_processed']:,}")
    logger.info(f"Plays loaded: {stats['plays_loaded']:,}")
    logger.info(f"Errors encountered: {stats['errors_encountered']:,}")
    logger.info(f"Duration: {stats['duration_minutes']:.1f} minutes")

    if stats["games_processed"] > 0:
        logger.info(
            f"Average plays per game: {stats['plays_loaded']/stats['games_processed']:.1f}"
        )

    logger.info("\nSeason breakdown:")
    for season in sorted(stats["season_breakdown"].keys()):
        season_stats = stats["season_breakdown"][season]
        logger.info(
            f"  {season}: {season_stats['games']:,} games, {season_stats['plays']:,} plays"
        )

    logger.info(f"\nStatistics saved to: {stats_file}")
    logger.info(
        "Data loaded into PostgreSQL tables: master.nba_games, master.nba_plays"
    )


if __name__ == "__main__":
    main()
