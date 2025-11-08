#!/usr/bin/env python3
"""
Load ESPN Games from Local JSON Files into PostgreSQL

This script loads games from local ESPN JSON files (collected via scraper)
into the PostgreSQL database using enrichment pipeline. Supports both legacy
raw_data schema and new espn schema.

Usage:
    # Load ALL local files into espn schema (new default)
    python scripts/etl/load_from_local_espn.py --all-local-files

    # Load ALL files with force update (reload existing games)
    python scripts/etl/load_from_local_espn.py --all-local-files --force

    # Load specific game IDs
    python scripts/etl/load_from_local_espn.py --game-ids 400237975,400237981

    # Load all missing games for a season
    python scripts/etl/load_from_local_espn.py --season 2011

    # Load from missing games report
    python scripts/etl/load_from_local_espn.py --missing-games-file game_coverage_report.json --season 2011

    # Dry run (don't insert)
    python scripts/etl/load_from_local_espn.py --all-local-files --dry-run

    # Load into raw_data schema (legacy)
    python scripts/etl/load_from_local_espn.py --all-local-files --target-schema raw_data --target-table nba_games

    # Load with custom target
    python scripts/etl/load_from_local_espn.py --game-ids 400828893 --target-schema espn --target-table espn_games

Examples:
    # Full ESPN data load (44,828 files into espn.espn_games)
    python scripts/etl/load_from_local_espn.py --all-local-files --force

    # Quick test with dry-run
    python scripts/etl/load_from_local_espn.py --game-ids 400828893,401654655 --dry-run

Options:
    --all-local-files       Load all JSON files from /Users/ryanranft/0espn/data/nba/nba_box_score/
    --game-ids             Comma-separated list of specific game IDs to load
    --season               Load all games for a specific season (requires --missing-games-file)
    --missing-games-file   Path to missing games JSON report (used with --season)
    --force                Force reload even if game exists (UPSERT mode)
    --dry-run              Preview without inserting to database
    --target-schema        Target database schema (default: espn)
    --target-table         Target table name (default: espn_games)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba_simulator.etl.extractors.espn.feature_extractor import ESPNFeatureExtractor
from nba_simulator.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocalESPNLoader:
    """Load ESPN games from local JSON files into PostgreSQL."""

    # Local ESPN data directories (support both old and new locations)
    LOCAL_BOXSCORE_DIR_OLD = Path("/Users/ryanranft/0espn/data/nba/nba_box_score")
    LOCAL_PBP_DIR_OLD = Path("/Users/ryanranft/0espn/data/nba/nba_pbp")

    LOCAL_BOXSCORE_DIR_NEW = Path(
        "/Users/ryanranft/nba-simulator-aws/data/nba_box_score"
    )
    LOCAL_PBP_DIR_NEW = Path("/Users/ryanranft/nba-simulator-aws/data/nba_pbp")

    def __init__(
        self,
        dry_run: bool = False,
        target_schema: str = "espn",
        target_table: str = "espn_games",
        local_data_dir: Optional[Path] = None,
    ):
        """
        Initialize loader.

        Args:
            dry_run: If True, don't insert into database
            target_schema: Database schema to load into (default: 'espn')
            target_table: Table name within schema (default: 'espn_games')
            local_data_dir: Base directory for local files (default: tries new location first, falls back to old)
        """
        self.dry_run = dry_run
        self.target_schema = target_schema
        self.target_table = target_table
        self.full_table_name = f"{target_schema}.{target_table}"
        self.db_config = self._load_db_config()
        self.feature_extractor = ESPNFeatureExtractor()

        # Determine which local directories to use
        if local_data_dir:
            self.LOCAL_BOXSCORE_DIR = local_data_dir / "nba_box_score"
            self.LOCAL_PBP_DIR = local_data_dir / "nba_pbp"
        elif self.LOCAL_BOXSCORE_DIR_NEW.exists():
            # Prefer new location
            self.LOCAL_BOXSCORE_DIR = self.LOCAL_BOXSCORE_DIR_NEW
            self.LOCAL_PBP_DIR = self.LOCAL_PBP_DIR_NEW
            logger.info(
                f"Using new data directory: {self.LOCAL_BOXSCORE_DIR_NEW.parent}"
            )
        else:
            # Fall back to old location
            self.LOCAL_BOXSCORE_DIR = self.LOCAL_BOXSCORE_DIR_OLD
            self.LOCAL_PBP_DIR = self.LOCAL_PBP_DIR_OLD
            logger.info(
                f"Using old data directory: {self.LOCAL_BOXSCORE_DIR_OLD.parent}"
            )

        logger.info(
            f"Initialized LocalESPNLoader (dry_run={dry_run}, target={self.full_table_name})"
        )

    def _load_db_config(self) -> Dict[str, str]:
        """Load database configuration from environment."""
        return {
            "dbname": os.getenv("POSTGRES_DB", "nba_simulator"),
            "user": os.getenv("POSTGRES_USER", "ryanranft"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    def get_db_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)

    def check_game_exists(self, game_id: str) -> bool:
        """Check if game already exists in database."""
        query = (
            f"SELECT EXISTS(SELECT 1 FROM {self.full_table_name} WHERE game_id = %s)"
        )

        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (game_id,))
                return cur.fetchone()[0]

    def load_local_json(self, game_id: str, file_type: str) -> Optional[Dict]:
        """
        Load JSON from local file.

        Args:
            game_id: ESPN game ID
            file_type: 'boxscore' or 'pbp'

        Returns:
            Parsed JSON dict, or None if not found
        """
        if file_type == "boxscore":
            file_path = self.LOCAL_BOXSCORE_DIR / f"{game_id}.json"
        elif file_type == "pbp":
            file_path = self.LOCAL_PBP_DIR / f"{game_id}.json"
        else:
            raise ValueError(f"Invalid file_type: {file_type}")

        if not file_path.exists():
            logger.debug(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def extract_game_data(self, game_id: str) -> Optional[Dict]:
        """
        Extract game data from local JSON files using ESPN feature extractor.

        Args:
            game_id: ESPN game ID

        Returns:
            Enriched game data dict, or None if files not found
        """
        # Load both boxscore and play-by-play
        boxscore = self.load_local_json(game_id, "boxscore")
        pbp = self.load_local_json(game_id, "pbp")

        if not boxscore:
            logger.warning(f"Boxscore not found for {game_id}")
            return None

        # Extract game info from boxscore
        try:
            game_package = (
                boxscore.get("page", {}).get("content", {}).get("gamepackage", {})
            )
            header = game_package.get("gmStrp", {}) or game_package.get("header", {})

            # Get game date
            game_date_str = header.get("dt", "")
            if game_date_str:
                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            else:
                logger.error(f"No game date found for {game_id}")
                return None

            # Extract season year from game date
            # NBA season spans two calendar years (Oct-June), so:
            # - Games Oct-Dec belong to season starting that year
            # - Games Jan-Jun belong to season starting previous year
            if game_date.month >= 10:  # October, November, December
                season_year = game_date.year
            else:  # January through September
                season_year = game_date.year - 1

            # Extract season type (1=Preseason, 2=Regular, 3=Playoffs, 5=Play-In)
            season_type = header.get("seasonType", None)

            # Get teams from gmStrp
            teams = header.get("tms", [])
            if len(teams) < 2:
                logger.error(f"Insufficient teams found for {game_id}")
                return None

            # Find home and away teams
            home_team = next((t for t in teams if t.get("isHome")), {})
            away_team = next((t for t in teams if not t.get("isHome")), {})

            if not home_team or not away_team:
                logger.error(f"Could not identify home/away teams for {game_id}")
                return None

            home_abbrev = home_team.get("abbrev", "")
            away_abbrev = away_team.get("abbrev", "")
            home_name = home_team.get("displayName", "")
            away_name = away_team.get("displayName", "")

            # Get scores
            home_score = int(home_team.get("score", 0))
            away_score = int(away_team.get("score", 0))

            # Use feature extractor to enrich (passing raw data)
            # Note: The feature extractor expects S3 data, but we can adapt it
            # For now, create a simplified enriched structure
            enriched_data = {
                "teams": {
                    "home": {
                        "name": home_name,
                        "abbreviation": home_abbrev,
                        "score": home_score,
                    },
                    "away": {
                        "name": away_name,
                        "abbreviation": away_abbrev,
                        "score": away_score,
                    },
                },
                "game_info": {
                    "game_id": game_id,
                    "season_year": season_year,
                    "season": f"{season_year}-{str(season_year + 1)[-2:]}",
                    "game_date": game_date.isoformat(),
                    "season_type": season_type,
                    "season_type_label": {
                        1: "Preseason",
                        2: "Regular Season",
                        3: "Playoffs",
                        5: "Play-In Tournament",
                    }.get(season_type, "Unknown"),
                },
                "source_data": {
                    "source": "ESPN",
                    "original_game_id": game_id,
                    "loaded_from": "local_files",
                    "loaded_at": datetime.now().isoformat(),
                },
                "metadata": {
                    "enrichment": {
                        "enriched_at": datetime.now().isoformat(),
                        "format_version": 1,
                        "feature_count": 0,  # Will be updated if we add full extraction
                    }
                },
            }

            # Add simplified ESPN features from boxscore
            if "gamepackage" in boxscore.get("page", {}).get("content", {}):
                game_pkg = boxscore["page"]["content"]["gamepackage"]

                # Add box score data
                if "bxscr" in game_pkg:
                    enriched_data["espn_features"] = {"box_score": game_pkg["bxscr"]}

                # Add venue info
                if "gmInfo" in game_pkg:
                    venue_info = game_pkg["gmInfo"].get("ven", {})
                    if not enriched_data.get("espn_features"):
                        enriched_data["espn_features"] = {}
                    enriched_data["espn_features"]["venue"] = {
                        "name": venue_info.get("fullName", ""),
                        "city": venue_info.get("address", {}).get("city", ""),
                        "state": venue_info.get("address", {}).get("state", ""),
                    }

            # Add play-by-play summary if available
            if pbp:
                try:
                    pbp_package = (
                        pbp.get("page", {}).get("content", {}).get("gamepackage", {})
                    )
                    plays = pbp_package.get("pbp", {}).get("plays", [])

                    if plays:
                        # Count event types
                        event_types = {}
                        for play in plays:
                            event_type = play.get("type", {}).get("text", "Unknown")
                            event_types[event_type] = event_types.get(event_type, 0) + 1

                        enriched_data["play_by_play"] = {
                            "total_plays": len(plays),
                            "summary": {
                                "event_types": event_types,
                                "periods": len(
                                    set(
                                        p.get("period", {}).get("number", 1)
                                        for p in plays
                                    )
                                ),
                            },
                        }
                except Exception as e:
                    logger.warning(f"Error processing PBP for {game_id}: {e}")

            return enriched_data

        except Exception as e:
            logger.error(
                f"Error extracting game data for {game_id}: {e}", exc_info=True
            )
            return None

    def insert_game(self, game_id: str, game_data: Dict) -> bool:
        """
        Insert game into database.

        Args:
            game_id: ESPN game ID
            game_data: Enriched game data dict

        Returns:
            True if inserted successfully, False otherwise
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert game {game_id}")
            return True

        # Extract fields for database
        season_year = game_data["game_info"]["season_year"]
        game_date_str = game_data["game_info"]["game_date"]
        game_date_obj = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
        season_type = game_data["game_info"].get("season_type")

        # Extract team info
        home_team = game_data["teams"]["home"]["name"]
        away_team = game_data["teams"]["away"]["name"]
        home_score = game_data["teams"]["home"]["score"]
        away_score = game_data["teams"]["away"]["score"]

        # Choose appropriate insert query based on target schema
        if self.target_schema == "espn":
            # ESPN schema has more columns
            insert_query = f"""
            INSERT INTO {self.full_table_name}
                (game_id, season, season_type, game_date, home_team, away_team,
                 home_score, away_score, collected_at, updated_at, data, metadata)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id) DO UPDATE
            SET
                season_type = EXCLUDED.season_type,
                home_team = EXCLUDED.home_team,
                away_team = EXCLUDED.away_team,
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                updated_at = EXCLUDED.updated_at,
                data = EXCLUDED.data,
                metadata = EXCLUDED.metadata
            """

            params = (
                game_id,
                season_year,
                season_type,
                game_date_obj,
                home_team,
                away_team,
                home_score,
                away_score,
                datetime.now(),
                datetime.now(),
                Json(game_data),
                Json(game_data.get("metadata", {})),
            )
        else:
            # raw_data schema (legacy, for backwards compatibility)
            source = game_data["source_data"]["source"]
            insert_query = f"""
            INSERT INTO {self.full_table_name}
                (game_id, source, season, game_date, collected_at, updated_at, data, metadata)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id) DO UPDATE
            SET
                updated_at = EXCLUDED.updated_at,
                data = EXCLUDED.data,
                metadata = EXCLUDED.metadata
            """

            params = (
                game_id,
                source,
                season_year,
                game_date_obj.date(),
                datetime.now(),
                datetime.now(),
                Json(game_data),
                Json(game_data.get("metadata", {})),
            )

        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(insert_query, params)
                    conn.commit()
                    logger.info(
                        f"✓ Inserted game {game_id} (season {season_year}, seasonType {season_type}, date {game_date_obj.date()})"
                    )
                    return True

        except Exception as e:
            logger.error(f"Error inserting game {game_id}: {e}")
            return False

    def load_game(self, game_id: str, skip_if_exists: bool = True) -> bool:
        """
        Load a single game from local files into database.

        Args:
            game_id: ESPN game ID
            skip_if_exists: If True, skip if game already in database

        Returns:
            True if loaded successfully, False otherwise
        """
        # Check if exists
        if skip_if_exists and self.check_game_exists(game_id):
            logger.info(f"⊗ Game {game_id} already exists in database, skipping")
            return False

        # Extract game data
        game_data = self.extract_game_data(game_id)
        if not game_data:
            logger.error(f"✗ Failed to extract game data for {game_id}")
            return False

        # Insert into database
        return self.insert_game(game_id, game_data)

    def get_all_local_game_ids(self) -> List[str]:
        """
        Get all game IDs from local boxscore directory.

        Returns:
            List of game IDs (filenames without .json extension)
        """
        if not self.LOCAL_BOXSCORE_DIR.exists():
            logger.error(
                f"Local boxscore directory does not exist: {self.LOCAL_BOXSCORE_DIR}"
            )
            return []

        json_files = list(self.LOCAL_BOXSCORE_DIR.glob("*.json"))
        game_ids = [f.stem for f in json_files]

        logger.info(f"Found {len(game_ids)} JSON files in {self.LOCAL_BOXSCORE_DIR}")
        return game_ids

    def load_games(
        self, game_ids: List[str], skip_if_exists: bool = True
    ) -> Dict[str, int]:
        """
        Load multiple games from local files.

        Args:
            game_ids: List of ESPN game IDs
            skip_if_exists: If True, skip games that already exist

        Returns:
            Dict with counts: loaded, skipped, failed
        """
        results = {"loaded": 0, "skipped": 0, "failed": 0}

        total = len(game_ids)
        logger.info(
            f"Loading {total} games from local files into {self.full_table_name}..."
        )

        for i, game_id in enumerate(game_ids, 1):
            logger.info(f"[{i}/{total}] Processing {game_id}...")

            try:
                if skip_if_exists and self.check_game_exists(game_id):
                    results["skipped"] += 1
                    logger.info(f"  ⊗ Already exists, skipping")
                    continue

                game_data = self.extract_game_data(game_id)
                if not game_data:
                    results["failed"] += 1
                    logger.error(f"  ✗ Failed to extract data")
                    continue

                if self.insert_game(game_id, game_data):
                    results["loaded"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"  ✗ Error processing {game_id}: {e}")
                results["failed"] += 1

        logger.info(f"\nLoad complete:")
        logger.info(f"  Loaded:  {results['loaded']}")
        logger.info(f"  Skipped: {results['skipped']}")
        logger.info(f"  Failed:  {results['failed']}")

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load ESPN games from local JSON files"
    )
    parser.add_argument("--game-ids", type=str, help="Comma-separated list of game IDs")
    parser.add_argument(
        "--season", type=int, help="Load all missing games for a season"
    )
    parser.add_argument(
        "--missing-games-file", type=str, help="Path to missing games JSON report"
    )
    parser.add_argument(
        "--all-local-files",
        action="store_true",
        help="Load ALL JSON files from local directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't insert)")
    parser.add_argument(
        "--force", action="store_true", help="Force load even if game exists"
    )
    parser.add_argument(
        "--target-schema",
        type=str,
        default="espn",
        help="Target database schema (default: espn)",
    )
    parser.add_argument(
        "--target-table",
        type=str,
        default="espn_games",
        help="Target table name (default: espn_games)",
    )
    parser.add_argument(
        "--local-data-dir", type=str, help="Local data directory (default: auto-detect)"
    )

    args = parser.parse_args()

    # Determine local data directory
    local_data_dir = None
    if args.local_data_dir:
        local_data_dir = Path(args.local_data_dir)

    # Initialize loader with target schema/table
    loader = LocalESPNLoader(
        dry_run=args.dry_run,
        target_schema=args.target_schema,
        target_table=args.target_table,
        local_data_dir=local_data_dir,
    )

    # Determine which games to load
    game_ids = []

    if args.all_local_files:
        # Load ALL files from local directory
        game_ids = loader.get_all_local_game_ids()
        logger.info(f"Loading ALL {len(game_ids)} local files")
    elif args.game_ids:
        game_ids = [gid.strip() for gid in args.game_ids.split(",")]
    elif args.season and args.missing_games_file:
        # Load from missing games report
        with open(args.missing_games_file) as f:
            report = json.load(f)

        season_data = report.get("seasons", {}).get(str(args.season))
        if not season_data:
            logger.error(f"Season {args.season} not found in report")
            return 1

        game_ids = [g["game_id"] for g in season_data.get("missing_games", [])]
        logger.info(f"Found {len(game_ids)} missing games for season {args.season}")
    else:
        logger.error(
            "Must specify one of: --all-local-files, --game-ids, or both --season and --missing-games-file"
        )
        return 1

    if not game_ids:
        logger.warning("No games to load")
        return 0

    # Load games
    results = loader.load_games(game_ids, skip_if_exists=not args.force)

    # Return exit code based on results
    if results["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
