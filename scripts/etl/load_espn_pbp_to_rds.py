#!/usr/bin/env python3
"""
ESPN PBP Data Pipeline

Loads extracted ESPN PBP data into RDS PostgreSQL database.
Creates temporal tables optimized for millisecond-precision queries.

Usage:
    python scripts/etl/load_espn_pbp_to_rds.py --input-dir data/extracted_pbp_recent
    python scripts/etl/load_espn_pbp_to_rds.py --batch-size 1000 --create-tables

Version: 1.0
Created: October 13, 2025
"""

import json
import os
import argparse
import logging
import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/espn_pbp_pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ESPNPBPPipeline:
    """Pipeline for loading ESPN PBP data into RDS"""

    def __init__(self, input_dir: str, db_config: Dict):
        self.input_dir = Path(input_dir)
        self.db_config = db_config

        # Statistics
        self.stats = {
            "games_loaded": 0,
            "plays_loaded": 0,
            "games_failed": 0,
            "plays_failed": 0,
        }

        logger.info(f"Initialized ESPN PBP Pipeline")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Database: {db_config.get('database', 'nba_sim')}")

    async def create_tables(self):
        """Create temporal tables for PBP data"""
        logger.info("Creating temporal tables...")

        conn = await asyncpg.connect(**self.db_config)

        try:
            # Create games table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS espn_games (
                    game_id VARCHAR(20) PRIMARY KEY,
                    game_date TIMESTAMPTZ NOT NULL,
                    season VARCHAR(10) NOT NULL,
                    home_team VARCHAR(100) NOT NULL,
                    away_team VARCHAR(100) NOT NULL,
                    home_abbrev VARCHAR(10) NOT NULL,
                    away_abbrev VARCHAR(10) NOT NULL,
                    final_score_home INTEGER NOT NULL,
                    final_score_away INTEGER NOT NULL,
                    total_plays INTEGER NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """
            )

            # Create plays table with temporal indexing
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS espn_plays (
                    id SERIAL PRIMARY KEY,
                    game_id VARCHAR(20) NOT NULL,
                    event_id VARCHAR(50) NOT NULL,
                    period INTEGER NOT NULL,
                    clock VARCHAR(10),
                    text TEXT NOT NULL,
                    home_away VARCHAR(10),
                    away_score INTEGER NOT NULL,
                    home_score INTEGER NOT NULL,
                    game_date TIMESTAMPTZ NOT NULL,
                    season VARCHAR(10) NOT NULL,
                    team_abbrev VARCHAR(10),
                    player_name VARCHAR(100),
                    event_type VARCHAR(50),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(game_id, event_id)
                )
            """
            )

            # Create temporal indexes for millisecond-precision queries
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_espn_plays_game_date
                ON espn_plays (game_date, period, clock)
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_espn_plays_season
                ON espn_plays (season, game_id)
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_espn_plays_game_id
                ON espn_plays (game_id, period)
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_espn_games_season
                ON espn_games (season, game_date)
            """
            )

            logger.info("Tables and indexes created successfully")

        finally:
            await conn.close()

    async def load_game_data(self, game_file: Path) -> bool:
        """Load a single game's data into the database"""
        try:
            # Load game info
            game_info_file = game_file
            plays_file = (
                game_file.parent / f"{game_file.stem.replace('_game', '_plays')}"
            )

            if not plays_file.exists():
                logger.warning(f"Plays file not found: {plays_file}")
                return False

            with open(game_info_file, "r") as f:
                game_info = json.load(f)

            with open(plays_file, "r") as f:
                plays_data = json.load(f)

            conn = await asyncpg.connect(**self.db_config)

            try:
                # Insert game info
                await conn.execute(
                    """
                    INSERT INTO espn_games (
                        game_id, game_date, season, home_team, away_team,
                        home_abbrev, away_abbrev, final_score_home, final_score_away, total_plays
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (game_id) DO UPDATE SET
                        game_date = EXCLUDED.game_date,
                        season = EXCLUDED.season,
                        home_team = EXCLUDED.home_team,
                        away_team = EXCLUDED.away_team,
                        home_abbrev = EXCLUDED.home_abbrev,
                        away_abbrev = EXCLUDED.away_abbrev,
                        final_score_home = EXCLUDED.final_score_home,
                        final_score_away = EXCLUDED.final_score_away,
                        total_plays = EXCLUDED.total_plays
                """,
                    game_info["game_id"],
                    game_info["game_date"],
                    game_info["season"],
                    game_info["home_team"],
                    game_info["away_team"],
                    game_info["home_abbrev"],
                    game_info["away_abbrev"],
                    game_info["final_score_home"],
                    game_info["final_score_away"],
                    game_info["total_plays"],
                )

                # Insert plays data
                if plays_data:
                    await conn.executemany(
                        """
                        INSERT INTO espn_plays (
                            game_id, event_id, period, clock, text, home_away,
                            away_score, home_score, game_date, season,
                            team_abbrev, player_name, event_type
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (game_id, event_id) DO UPDATE SET
                            period = EXCLUDED.period,
                            clock = EXCLUDED.clock,
                            text = EXCLUDED.text,
                            home_away = EXCLUDED.home_away,
                            away_score = EXCLUDED.away_score,
                            home_score = EXCLUDED.home_score,
                            game_date = EXCLUDED.game_date,
                            season = EXCLUDED.season,
                            team_abbrev = EXCLUDED.team_abbrev,
                            player_name = EXCLUDED.player_name,
                            event_type = EXCLUDED.event_type
                    """,
                        [
                            (
                                play["game_id"],
                                play["event_id"],
                                play["period"],
                                play["clock"],
                                play["text"],
                                play["home_away"],
                                play["away_score"],
                                play["home_score"],
                                play["game_date"],
                                play["season"],
                                play.get("team_abbrev"),
                                play.get("player_name"),
                                play.get("event_type"),
                            )
                            for play in plays_data
                        ],
                    )

                self.stats["games_loaded"] += 1
                self.stats["plays_loaded"] += len(plays_data)

                return True

            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"Error loading game {game_file}: {e}")
            self.stats["games_failed"] += 1
            return False

    async def load_all_data(self, batch_size: int = 100):
        """Load all extracted data into the database"""
        logger.info("Starting data loading process...")

        # Get all game files
        game_files = list(self.input_dir.glob("*_game.json"))
        logger.info(f"Found {len(game_files)} game files to load")

        # Process in batches
        for i in range(0, len(game_files), batch_size):
            batch = game_files[i : i + batch_size]
            logger.info(
                f"Loading batch {i//batch_size + 1}/{(len(game_files) + batch_size - 1)//batch_size}"
            )

            # Load batch concurrently
            tasks = [self.load_game_data(game_file) for game_file in batch]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Log progress
            if (i + batch_size) % 1000 == 0:
                logger.info(
                    f"Loaded {self.stats['games_loaded']} games, {self.stats['plays_loaded']} plays"
                )

        logger.info("Data loading completed!")
        self.print_statistics()

    def print_statistics(self):
        """Print loading statistics"""
        logger.info("=" * 50)
        logger.info("DATA LOADING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Games loaded: {self.stats['games_loaded']:,}")
        logger.info(f"Plays loaded: {self.stats['plays_loaded']:,}")
        logger.info(f"Games failed: {self.stats['games_failed']:,}")
        logger.info(f"Plays failed: {self.stats['plays_failed']:,}")

        if self.stats["games_loaded"] > 0:
            avg_plays = self.stats["plays_loaded"] / self.stats["games_loaded"]
            logger.info(f"Average plays per game: {avg_plays:.1f}")


async def main():
    parser = argparse.ArgumentParser(description="Load ESPN PBP data into RDS")
    parser.add_argument(
        "--input-dir",
        default="data/extracted_pbp_recent",
        help="Input directory with extracted data",
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for loading"
    )
    parser.add_argument(
        "--create-tables", action="store_true", help="Create tables before loading"
    )
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--db-port", type=int, default=5432, help="Database port")
    parser.add_argument("--db-name", default="nba_sim", help="Database name")
    parser.add_argument("--db-user", default="postgres", help="Database user")
    parser.add_argument("--db-password", help="Database password")

    args = parser.parse_args()

    # Database configuration
    db_config = {
        "host": args.db_host,
        "port": args.db_port,
        "database": args.db_name,
        "user": args.db_user,
        "password": args.db_password or os.getenv("DB_PASSWORD", ""),
    }

    # Create pipeline
    pipeline = ESPNPBPPipeline(args.input_dir, db_config)

    try:
        # Create tables if requested
        if args.create_tables:
            await pipeline.create_tables()

        # Load data
        await pipeline.load_all_data(args.batch_size)

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
