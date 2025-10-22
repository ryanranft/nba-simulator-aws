#!/usr/bin/env python3
"""
Master Database ETL Pipeline
Merges all NBA data sources into unified master database schema.

Data Sources:
1. ESPN (S3: s3://nba-sim-raw-data-lake/pbp/, box_scores/, team_stats/, schedule/)
2. NBA.com Stats (S3: s3://nba-sim-raw-data-lake/nba_api_comprehensive/)
3. hoopR (S3: s3://nba-sim-raw-data-lake/hoopr_parquet/, hoopr_csv/)
4. Basketball Reference (S3: s3://nba-sim-raw-data-lake/basketball_reference/)
5. Kaggle (Local: data/kaggle/nba.sqlite)

Usage:
    python scripts/etl/merge_all_sources.py --season 2023-24 --dry-run
    python scripts/etl/merge_all_sources.py --all-seasons
    python scripts/etl/merge_all_sources.py --all-seasons --batch-size 1000
"""

import json
import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3
    import psycopg2
    from psycopg2.extras import execute_values

    HAS_DB_LIBS = True
except ImportError:
    HAS_DB_LIBS = False
    print("⚠️  Required libraries not available - install boto3 and psycopg2")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/master_etl.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """Configuration for each data source"""

    name: str
    s3_prefix: str
    local_path: Optional[str] = None
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True


class MasterDatabaseETL:
    """ETL pipeline for merging all NBA data sources into master database"""

    def __init__(
        self,
        s3_bucket: str = "nba-sim-raw-data-lake",
        local_cache_dir: str = "/tmp/nba_data_cache",
        db_config: Optional[Dict] = None,
    ):
        self.s3_bucket = s3_bucket
        self.local_cache_dir = Path(local_cache_dir)
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)

        # Database configuration
        self.db_config = db_config or self._load_db_config()

        # S3 client
        self.s3_client = boto3.client("s3") if HAS_DB_LIBS else None

        # Data source configurations
        self.data_sources = {
            "espn": DataSourceConfig("espn", "pbp/", priority=2),
            "nba_stats": DataSourceConfig(
                "nba_stats", "nba_api_comprehensive/", priority=1
            ),
            "hoopr": DataSourceConfig("hoopr", "hoopr_parquet/", priority=3),
            "basketball_reference": DataSourceConfig(
                "basketball_reference", "basketball_reference/", priority=4
            ),
            "kaggle": DataSourceConfig(
                "kaggle", None, local_path="data/kaggle/nba.sqlite", priority=5
            ),
        }

        # Statistics tracking
        self.stats = {
            "games_processed": 0,
            "players_processed": 0,
            "teams_processed": 0,
            "player_stats_processed": 0,
            "team_stats_processed": 0,
            "pbp_events_processed": 0,
            "conflicts_resolved": 0,
            "errors": 0,
        }

        logger.info(
            f"MasterDatabaseETL initialized. S3 Bucket: {self.s3_bucket}, Cache: {self.local_cache_dir}"
        )

    def _load_db_config(self) -> Dict[str, str]:
        """Load database configuration from environment"""
        try:
            # Load from credentials file
            creds_file = Path("/Users/ryanranft/nba-sim-credentials.env")
            if creds_file.exists():
                with open(creds_file, "r") as f:
                    lines = f.readlines()
                    config = {}
                    for line in lines:
                        if "=" in line and not line.startswith("#"):
                            key, value = line.strip().split("=", 1)
                            config[key] = value
                    return config
        except Exception as e:
            logger.warning(f"Could not load DB config: {e}")

        # Fallback to environment variables
        return {
            "DB_HOST": os.getenv("DB_HOST", "localhost"),
            "DB_PORT": os.getenv("DB_PORT", "5432"),
            "DB_NAME": os.getenv("DB_NAME", "nba_simulator"),
            "DB_USER": os.getenv("DB_USER", "postgres"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
        }

    def _get_db_connection(self):
        """Get database connection"""
        if not HAS_DB_LIBS:
            raise ImportError("Required database libraries not available")

        return psycopg2.connect(
            host=self.db_config["DB_HOST"],
            port=self.db_config["DB_PORT"],
            database=self.db_config["DB_NAME"],
            user=self.db_config["DB_USER"],
            password=self.db_config["DB_PASSWORD"],
            sslmode="require",
        )

    def _load_json_from_s3_or_cache(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Load JSON file from S3 with local caching"""
        local_path = self.local_cache_dir / s3_key

        # Check cache first
        if local_path.exists():
            try:
                with open(local_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cached file {local_path}: {e}")

        # Download from S3
        if not self.s3_client:
            logger.error("S3 client not available")
            return None

        try:
            obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            data = json.loads(obj["Body"].read().decode("utf-8"))

            # Save to cache
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "w") as f:
                json.dump(data, f, indent=2)

            return data
        except Exception as e:
            logger.warning(f"Failed to load {s3_key} from S3: {e}")
            return None

    def _load_parquet_from_s3(self, s3_key: str) -> Optional[pd.DataFrame]:
        """Load Parquet file from S3"""
        if not self.s3_client:
            logger.error("S3 client not available")
            return None

        try:
            obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            return pd.read_parquet(obj["Body"])
        except Exception as e:
            logger.warning(f"Failed to load Parquet {s3_key}: {e}")
            return None

    def _load_kaggle_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """Load data from Kaggle SQLite database"""
        kaggle_path = Path("data/kaggle/nba.sqlite")
        if not kaggle_path.exists():
            logger.warning(f"Kaggle database not found at {kaggle_path}")
            return None

        try:
            conn = sqlite3.connect(kaggle_path)
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            return df
        except Exception as e:
            logger.warning(f"Failed to load Kaggle table {table_name}: {e}")
            return None

    def extract_espn_data(self, season: str) -> Dict[str, Any]:
        """Extract ESPN data for a season"""
        logger.info(f"Extracting ESPN data for season {season}")

        espn_data = {
            "games": [],
            "player_stats": [],
            "team_stats": [],
            "play_by_play": [],
        }

        # List ESPN files for the season
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket, Prefix="pbp/", MaxKeys=1000
            )

            for obj in response.get("Contents", []):
                if season in obj["Key"]:
                    data = self._load_json_from_s3_or_cache(obj["Key"])
                    if data:
                        espn_data["play_by_play"].append(data)

            logger.info(f"Extracted {len(espn_data['play_by_play'])} ESPN PBP files")

        except Exception as e:
            logger.error(f"Error extracting ESPN data: {e}")
            self.stats["errors"] += 1

        return espn_data

    def extract_nba_stats_data(self, season: str) -> Dict[str, Any]:
        """Extract NBA.com Stats data for a season"""
        logger.info(f"Extracting NBA.com Stats data for season {season}")

        nba_stats_data = {
            "player_tracking": [],
            "hustle_stats": [],
            "defense_stats": [],
        }

        # List NBA Stats files for the season
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket, Prefix="nba_api_comprehensive/", MaxKeys=1000
            )

            for obj in response.get("Contents", []):
                if season in obj["Key"]:
                    data = self._load_json_from_s3_or_cache(obj["Key"])
                    if data:
                        # Categorize by data type
                        if "tracking" in obj["Key"]:
                            nba_stats_data["player_tracking"].append(data)
                        elif "hustle" in obj["Key"]:
                            nba_stats_data["hustle_stats"].append(data)
                        elif "defense" in obj["Key"]:
                            nba_stats_data["defense_stats"].append(data)

            logger.info(
                f"Extracted NBA Stats data: {sum(len(v) for v in nba_stats_data.values())} files"
            )

        except Exception as e:
            logger.error(f"Error extracting NBA Stats data: {e}")
            self.stats["errors"] += 1

        return nba_stats_data

    def extract_hoopr_data(self, season: str) -> Dict[str, Any]:
        """Extract hoopR data for a season"""
        logger.info(f"Extracting hoopR data for season {season}")

        hoopr_data = {
            "player_box": None,
            "team_box": None,
            "schedule": None,
            "play_by_play": None,
        }

        # Load hoopR Parquet files
        try:
            # Player box scores
            player_box_key = f"hoopr_parquet/nba_player_box_{season}.parquet"
            hoopr_data["player_box"] = self._load_parquet_from_s3(player_box_key)

            # Team box scores
            team_box_key = f"hoopr_parquet/nba_team_box_{season}.parquet"
            hoopr_data["team_box"] = self._load_parquet_from_s3(team_box_key)

            logger.info(f"Extracted hoopR data for season {season}")

        except Exception as e:
            logger.error(f"Error extracting hoopR data: {e}")
            self.stats["errors"] += 1

        return hoopr_data

    def extract_basketball_reference_data(self, season: str) -> Dict[str, Any]:
        """Extract Basketball Reference data for a season"""
        logger.info(f"Extracting Basketball Reference data for season {season}")

        bref_data = {"per_game": [], "advanced": [], "shooting": [], "team_ratings": []}

        # List Basketball Reference files for the season
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket, Prefix="basketball_reference/", MaxKeys=1000
            )

            for obj in response.get("Contents", []):
                if season in obj["Key"]:
                    data = self._load_json_from_s3_or_cache(obj["Key"])
                    if data:
                        # Categorize by data type
                        if "per_game" in obj["Key"]:
                            bref_data["per_game"].append(data)
                        elif "advanced" in obj["Key"]:
                            bref_data["advanced"].append(data)
                        elif "shooting" in obj["Key"]:
                            bref_data["shooting"].append(data)
                        elif "team_ratings" in obj["Key"]:
                            bref_data["team_ratings"].append(data)

            logger.info(
                f"Extracted Basketball Reference data: {sum(len(v) for v in bref_data.values())} files"
            )

        except Exception as e:
            logger.error(f"Error extracting Basketball Reference data: {e}")
            self.stats["errors"] += 1

        return bref_data

    def extract_kaggle_data(self, season: str) -> Dict[str, Any]:
        """Extract Kaggle data for a season"""
        logger.info(f"Extracting Kaggle data for season {season}")

        kaggle_data = {"games": None, "players": None, "teams": None}

        try:
            # Load games data
            games_df = self._load_kaggle_data("games")
            if games_df is not None:
                # Filter by season
                season_year = int(season.split("-")[0])
                kaggle_data["games"] = games_df[games_df["season"] == season_year]

            # Load players data
            kaggle_data["players"] = self._load_kaggle_data("players")

            # Load teams data
            kaggle_data["teams"] = self._load_kaggle_data("teams")

            logger.info(f"Extracted Kaggle data for season {season}")

        except Exception as e:
            logger.error(f"Error extracting Kaggle data: {e}")
            self.stats["errors"] += 1

        return kaggle_data

    def transform_and_load_players(self, all_data: Dict[str, Dict[str, Any]]) -> None:
        """Transform and load player data from all sources"""
        logger.info("Transforming and loading player data")

        players_by_id = {}

        # Process each data source
        for source_name, source_data in all_data.items():
            if source_name == "espn":
                # Extract players from ESPN data
                for pbp_data in source_data.get("play_by_play", []):
                    # Extract player info from PBP events
                    # This is a simplified example - would need full implementation
                    pass

            elif source_name == "hoopr":
                player_box = source_data.get("player_box")
                if player_box is not None:
                    for _, row in player_box.iterrows():
                        player_id = str(row.get("player_id", ""))
                        if player_id and player_id not in players_by_id:
                            players_by_id[player_id] = {
                                "player_id": player_id,
                                "player_name": row.get("player_name", ""),
                                "team_id": str(row.get("team_id", "")),
                                "source_player_ids": {source_name: player_id},
                                "data_sources": [source_name],
                            }

            elif source_name == "kaggle":
                players_df = source_data.get("players")
                if players_df is not None:
                    for _, row in players_df.iterrows():
                        player_id = f"kaggle_{row.get('id', '')}"
                        if player_id not in players_by_id:
                            players_by_id[player_id] = {
                                "player_id": player_id,
                                "player_name": row.get("name", ""),
                                "position": row.get("position", ""),
                                "height_inches": row.get("height_inches"),
                                "weight_lbs": row.get("weight_lbs"),
                                "source_player_ids": {
                                    source_name: str(row.get("id", ""))
                                },
                                "data_sources": [source_name],
                            }

        # Load to database
        if players_by_id:
            self._load_players_to_db(list(players_by_id.values()))
            self.stats["players_processed"] += len(players_by_id)

    def transform_and_load_teams(self, all_data: Dict[str, Dict[str, Any]]) -> None:
        """Transform and load team data from all sources"""
        logger.info("Transforming and loading team data")

        teams_by_id = {}

        # Process each data source
        for source_name, source_data in all_data.items():
            if source_name == "kaggle":
                teams_df = source_data.get("teams")
                if teams_df is not None:
                    for _, row in teams_df.iterrows():
                        team_id = f"kaggle_{row.get('id', '')}"
                        if team_id not in teams_by_id:
                            teams_by_id[team_id] = {
                                "team_id": team_id,
                                "team_name": row.get("name", ""),
                                "team_abbreviation": row.get("abbreviation", ""),
                                "conference": row.get("conference", ""),
                                "division": row.get("division", ""),
                                "source_team_ids": {
                                    source_name: str(row.get("id", ""))
                                },
                                "data_sources": [source_name],
                            }

        # Load to database
        if teams_by_id:
            self._load_teams_to_db(list(teams_by_id.values()))
            self.stats["teams_processed"] += len(teams_by_id)

    def _load_players_to_db(self, players: List[Dict[str, Any]]) -> None:
        """Load players to master database"""
        if not players:
            return

        conn = self._get_db_connection()
        try:
            with conn.cursor() as cur:
                # Use execute_values for bulk insert
                columns = [
                    "player_id",
                    "player_name",
                    "first_name",
                    "last_name",
                    "position",
                    "height_inches",
                    "weight_lbs",
                    "source_player_ids",
                    "data_sources",
                ]

                values = []
                for player in players:
                    # Split name into first/last
                    name_parts = player.get("player_name", "").split(" ", 1)
                    first_name = name_parts[0] if name_parts else ""
                    last_name = name_parts[1] if len(name_parts) > 1 else ""

                    values.append(
                        (
                            player["player_id"],
                            player["player_name"],
                            first_name,
                            last_name,
                            player.get("position"),
                            player.get("height_inches"),
                            player.get("weight_lbs"),
                            json.dumps(player.get("source_player_ids", {})),
                            player.get("data_sources", []),
                        )
                    )

                execute_values(
                    cur,
                    f"""
                    INSERT INTO master_players ({', '.join(columns)})
                    VALUES %s
                    ON CONFLICT (player_id) DO UPDATE SET
                        player_name = EXCLUDED.player_name,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        position = EXCLUDED.position,
                        height_inches = EXCLUDED.height_inches,
                        weight_lbs = EXCLUDED.weight_lbs,
                        source_player_ids = EXCLUDED.source_player_ids,
                        data_sources = EXCLUDED.data_sources,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    values,
                    template=None,
                    page_size=1000,
                )

                conn.commit()
                logger.info(f"Loaded {len(players)} players to master database")

        except Exception as e:
            logger.error(f"Error loading players to database: {e}")
            conn.rollback()
            self.stats["errors"] += 1
        finally:
            conn.close()

    def _load_teams_to_db(self, teams: List[Dict[str, Any]]) -> None:
        """Load teams to master database"""
        if not teams:
            return

        conn = self._get_db_connection()
        try:
            with conn.cursor() as cur:
                columns = [
                    "team_id",
                    "team_name",
                    "team_abbreviation",
                    "conference",
                    "division",
                    "source_team_ids",
                    "data_sources",
                ]

                values = []
                for team in teams:
                    values.append(
                        (
                            team["team_id"],
                            team["team_name"],
                            team["team_abbreviation"],
                            team.get("conference"),
                            team.get("division"),
                            json.dumps(team.get("source_team_ids", {})),
                            team.get("data_sources", []),
                        )
                    )

                execute_values(
                    cur,
                    f"""
                    INSERT INTO master_teams ({', '.join(columns)})
                    VALUES %s
                    ON CONFLICT (team_id) DO UPDATE SET
                        team_name = EXCLUDED.team_name,
                        team_abbreviation = EXCLUDED.team_abbreviation,
                        conference = EXCLUDED.conference,
                        division = EXCLUDED.division,
                        source_team_ids = EXCLUDED.source_team_ids,
                        data_sources = EXCLUDED.data_sources,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    values,
                    template=None,
                    page_size=1000,
                )

                conn.commit()
                logger.info(f"Loaded {len(teams)} teams to master database")

        except Exception as e:
            logger.error(f"Error loading teams to database: {e}")
            conn.rollback()
            self.stats["errors"] += 1
        finally:
            conn.close()

    def process_season(self, season: str, dry_run: bool = False) -> Dict[str, Any]:
        """Process a single season from all data sources"""
        logger.info(f"Processing season {season}")

        if dry_run:
            logger.info("DRY RUN MODE - No data will be written to database")

        # Extract data from all sources
        all_data = {}

        for source_name, config in self.data_sources.items():
            if not config.enabled:
                continue

            try:
                if source_name == "espn":
                    all_data[source_name] = self.extract_espn_data(season)
                elif source_name == "nba_stats":
                    all_data[source_name] = self.extract_nba_stats_data(season)
                elif source_name == "hoopr":
                    all_data[source_name] = self.extract_hoopr_data(season)
                elif source_name == "basketball_reference":
                    all_data[source_name] = self.extract_basketball_reference_data(
                        season
                    )
                elif source_name == "kaggle":
                    all_data[source_name] = self.extract_kaggle_data(season)

            except Exception as e:
                logger.error(f"Error extracting {source_name} data: {e}")
                self.stats["errors"] += 1

        if not dry_run:
            # Transform and load data
            self.transform_and_load_players(all_data)
            self.transform_and_load_teams(all_data)
            # TODO: Add more transform/load methods for games, stats, etc.

        return all_data

    def process_all_seasons(self, dry_run: bool = False, batch_size: int = 100) -> None:
        """Process all available seasons"""
        logger.info("Processing all seasons")

        # Get list of seasons from ESPN data (most comprehensive)
        seasons = []
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket, Prefix="pbp/", MaxKeys=1000
            )

            for obj in response.get("Contents", []):
                # Extract season from filename
                filename = obj["Key"].split("/")[-1]
                if filename.endswith(".json"):
                    # Assume filename format includes season info
                    # This would need to be adapted based on actual filename format
                    pass

            # For now, use hardcoded seasons
            seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

        except Exception as e:
            logger.error(f"Error getting season list: {e}")
            seasons = ["2023-24"]  # Fallback to single season

        logger.info(f"Processing {len(seasons)} seasons: {seasons}")

        for i, season in enumerate(seasons):
            logger.info(f"Processing season {season} ({i+1}/{len(seasons)})")

            try:
                self.process_season(season, dry_run)

                # Batch processing checkpoint
                if (i + 1) % batch_size == 0:
                    logger.info(f"Processed {i + 1} seasons, checkpoint reached")

            except Exception as e:
                logger.error(f"Error processing season {season}: {e}")
                self.stats["errors"] += 1
                continue

        # Print final statistics
        self._print_statistics()

    def _print_statistics(self) -> None:
        """Print processing statistics"""
        logger.info("=" * 60)
        logger.info("ETL PROCESSING STATISTICS")
        logger.info("=" * 60)

        for key, value in self.stats.items():
            logger.info(f"{key.replace('_', ' ').title()}: {value}")

        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Master Database ETL Pipeline")
    parser.add_argument("--season", help="Single season to process (e.g., 2023-24)")
    parser.add_argument(
        "--all-seasons", action="store_true", help="Process all available seasons"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no database writes)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for processing"
    )
    parser.add_argument(
        "--s3-bucket", default="nba-sim-raw-data-lake", help="S3 bucket name"
    )
    parser.add_argument(
        "--cache-dir", default="/tmp/nba_data_cache", help="Local cache directory"
    )

    args = parser.parse_args()

    if not HAS_DB_LIBS:
        logger.error("Required libraries not available. Install boto3 and psycopg2.")
        return 1

    # Initialize ETL pipeline
    etl = MasterDatabaseETL(s3_bucket=args.s3_bucket, local_cache_dir=args.cache_dir)

    try:
        if args.season:
            logger.info(f"Processing single season: {args.season}")
            etl.process_season(args.season, args.dry_run)
        elif args.all_seasons:
            logger.info("Processing all seasons")
            etl.process_all_seasons(args.dry_run, args.batch_size)
        else:
            logger.error("Must specify either --season or --all-seasons")
            return 1

        logger.info("ETL pipeline completed successfully")
        return 0

    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())





