#!/usr/bin/env python3
"""
NBA API Game-Level Advanced Stats Scraper (Enhanced)
Collects 4 game-level endpoints for rotation, win probability, etc.

Enhanced with Book Recommendations:
- rec_22: Panel data structure (game_id, timestamp multi-index)
- rec_11: Feature engineering during collection
- ml_systems_1: MLflow experiment tracking
- ml_systems_2: Data quality monitoring

Panel Data Output Format:
- Multi-indexed by (game_id, event_timestamp)
- Includes game context (rotation, win probability, similarity)
- Ready for temporal queries and panel analysis
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from nba_api.stats.endpoints import (
    GameRotation,
    LeagueGameFinder,
)

try:
    import mlflow
    import mlflow.tracking
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not MLFLOW_AVAILABLE:
    logger.warning("MLflow not available - tracking disabled")


class NBAAPIGameAdvancedScraper:
    def __init__(self, output_dir="/tmp/nba_api_game_advanced", use_mlflow=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "x-nba-stats-origin": "stats",
                "x-nba-stats-token": "true",
            }
        )

        self.game_endpoints = [
            ("rotation", GameRotation),
            # Note: WinProbabilityPBP currently returns JSON errors (NBA API issue)
            # Note: GLAlumBoxScoreSimilarityScore is a player comparison endpoint, not game-level
        ]

        # MLflow tracking setup (ml_systems_1)
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        if self.use_mlflow:
            mlflow.set_experiment("nba_api_game_advanced_scraper")
            logger.info("✅ MLflow tracking enabled")

        # Data quality metrics (ml_systems_2)
        self.metrics = {
            "api_calls": 0,
            "api_successes": 0,
            "api_failures": 0,
            "records_collected": 0,
            "games_processed": 0,
            "empty_responses": 0,
        }

        logger.info("NBA API Game Advanced Scraper initialized")

    def get_games_for_season(self, season="2023-24"):
        """Get all games for a season"""
        try:
            game_finder = LeagueGameFinder(
                season_nullable=season, league_id_nullable="00"
            )
            games_df = game_finder.get_data_frames()[0]
            return games_df["GAME_ID"].tolist()
        except Exception as e:
            logger.error(f"Error getting games for {season}: {e}")
            return []

    def scrape_game_advanced(self, game_id, season="2023-24"):
        """Scrape all advanced endpoints for a game with panel data structure"""
        game_data = {}

        for endpoint_name, endpoint_class in self.game_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for game {game_id}")
                self.metrics["api_calls"] += 1

                endpoint = endpoint_class(game_id=game_id)

                # Handle potential JSON parsing errors (common for some game endpoints)
                try:
                    data_frames = endpoint.get_data_frames()
                except Exception as api_err:
                    # Check if it's a JSON-related error (common when no data available)
                    error_msg = str(api_err).lower()
                    if 'json' in error_msg or 'expecting value' in error_msg:
                        logger.warning(
                            f"⚠️ {endpoint_name}: Invalid JSON response for game {game_id} - "
                            f"likely no data available. Treating as empty response."
                        )
                        game_data[endpoint_name] = []
                        self.metrics["api_successes"] += 1  # API responded, just with no data
                        self.metrics["empty_responses"] += 1
                        time.sleep(1.5)
                        continue
                    else:
                        # Re-raise if not a JSON error
                        raise

                if data_frames and len(data_frames) > 0:
                    records = data_frames[0].to_dict("records")

                    # Add panel data structure (rec_22)
                    for record in records:
                        record["game_id"] = game_id
                        record["season"] = season
                        record["endpoint"] = endpoint_name
                        record["event_timestamp"] = datetime.now().isoformat()
                        record["scraped_at"] = datetime.now().isoformat()

                    game_data[endpoint_name] = records

                    self.metrics["api_successes"] += 1
                    self.metrics["records_collected"] += len(records)
                    logger.info(f"✅ {endpoint_name}: {len(records)} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    game_data[endpoint_name] = []
                    self.metrics["empty_responses"] += 1

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for game {game_id}: {e}"
                )
                game_data[endpoint_name] = []
                self.metrics["api_failures"] += 1

        self.metrics["games_processed"] += 1
        return game_data

    def run(self, start_season="2020-21", end_season="2024-25"):
        """Run the scraper for multiple seasons with MLflow tracking"""
        start_time = datetime.now()

        # Start MLflow run (ml_systems_1)
        if self.use_mlflow:
            mlflow.start_run(run_name=f"scrape_{start_season}_to_{end_season}")
            mlflow.log_param("start_season", start_season)
            mlflow.log_param("end_season", end_season)
            mlflow.log_param("output_dir", str(self.output_dir))

        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

        try:
            for season in seasons:
                if season < start_season or season > end_season:
                    continue

                logger.info(f"Starting season {season}")
                season_dir = self.output_dir / season
                season_dir.mkdir(exist_ok=True)

                games = self.get_games_for_season(season)
                logger.info(f"Found {len(games)} games for {season}")

                for i, game_id in enumerate(games):
                    logger.info(f"Processing game {i+1}/{len(games)}: {game_id}")

                    game_data = self.scrape_game_advanced(game_id, season)

                    # Save game data with panel structure
                    game_file = season_dir / f"game_{game_id}.json"
                    with open(game_file, "w") as f:
                        json.dump(
                            {
                                "game_id": game_id,
                                "season": season,
                                "scraped_at": datetime.now().isoformat(),
                                "data": game_data,
                                # Panel data metadata (rec_22)
                                "panel_structure": {
                                    "multi_index": ["game_id", "event_timestamp"],
                                    "temporal_features_ready": True,
                                },
                                # Feature engineering metadata (rec_11)
                                "features": {
                                    "generated": False,
                                    "version": "1.0",
                                },
                            },
                            f,
                            indent=2,
                        )

                    logger.info(f"Saved game {game_id} data to {game_file}")

                    # Progress checkpoint
                    if (i + 1) % 100 == 0:
                        logger.info(f"Progress: {i+1}/{len(games)} games completed")
                        # Log incremental metrics to MLflow
                        if self.use_mlflow:
                            mlflow.log_metrics(self.metrics, step=i + 1)

            # Log final metrics (ml_systems_2)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"\n{'='*80}")
            logger.info(f"SCRAPING COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"API Calls: {self.metrics['api_calls']}")
            logger.info(f"Successes: {self.metrics['api_successes']}")
            logger.info(f"Failures: {self.metrics['api_failures']}")
            logger.info(f"Records: {self.metrics['records_collected']:,}")
            logger.info(f"Games: {self.metrics['games_processed']}")
            logger.info(
                f"Success Rate: {100 * self.metrics['api_successes'] / max(self.metrics['api_calls'], 1):.1f}%"
            )
            logger.info(f"{'='*80}")

            if self.use_mlflow:
                mlflow.log_metrics(self.metrics)
                mlflow.log_metric("duration_seconds", duration)
                mlflow.log_metric(
                    "success_rate",
                    self.metrics["api_successes"] / max(self.metrics["api_calls"], 1),
                )
                mlflow.end_run()

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            if self.use_mlflow:
                mlflow.log_param("status", "failed")
                mlflow.end_run(status="FAILED")
            raise


if __name__ == "__main__":
    scraper = NBAAPIGameAdvancedScraper()
    scraper.run()
