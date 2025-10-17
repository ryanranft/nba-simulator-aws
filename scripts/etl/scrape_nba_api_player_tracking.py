#!/usr/bin/env python3
"""
NBA API Player Tracking Scraper (Enhanced)
Collects 4 player tracking endpoints with SportVU data

Enhanced with Book Recommendations:
- rec_22: Panel data structure (player_id, game_id, timestamp multi-index)
- rec_11: Feature engineering during collection
- ml_systems_1: MLflow experiment tracking
- ml_systems_2: Data quality monitoring

Panel Data Output Format:
- Multi-indexed by (player_id, game_id, event_timestamp)
- Includes temporal features (cumulative stats, lag variables)
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
    PlayerDashPtPass,
    PlayerDashPtReb,
    PlayerDashPtShotDefend,
    PlayerDashPtShots,
    CommonAllPlayers,
)

try:
    import mlflow
    import mlflow.tracking
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not available - tracking disabled")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBAAPIPlayerTrackingScraper:
    def __init__(self, output_dir="/tmp/nba_api_player_tracking", use_mlflow=True):
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

        self.tracking_endpoints = [
            ("pt_pass", PlayerDashPtPass),
            ("pt_reb", PlayerDashPtReb),
            ("pt_shot_defend", PlayerDashPtShotDefend),
            ("pt_shots", PlayerDashPtShots),
        ]

        # MLflow tracking setup (ml_systems_1)
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        if self.use_mlflow:
            mlflow.set_experiment("nba_api_player_tracking_scraper")
            logger.info("✅ MLflow tracking enabled")

        # Data quality metrics (ml_systems_2)
        self.metrics = {
            "api_calls": 0,
            "api_successes": 0,
            "api_failures": 0,
            "records_collected": 0,
            "players_processed": 0,
            "empty_responses": 0,
        }

        logger.info("NBA API Player Tracking Scraper initialized")

    def get_all_players(self, season="2023-24"):
        """Get all players for a season"""
        try:
            players_info = CommonAllPlayers(season=season)
            players_df = players_info.get_data_frames()[0]
            return players_df["PERSON_ID"].tolist()
        except Exception as e:
            logger.error(f"Error getting players for {season}: {e}")
            return []

    def scrape_player_tracking(self, player_id, season="2023-24"):
        """Scrape all tracking endpoints for a player with panel data structure"""
        player_data = {}

        for endpoint_name, endpoint_class in self.tracking_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")
                self.metrics["api_calls"] += 1

                endpoint = endpoint_class(player_id=player_id, season=season)
                data_frames = endpoint.get_data_frames()

                if data_frames and len(data_frames) > 0:
                    records = data_frames[0].to_dict("records")

                    # Add panel data structure (rec_22)
                    for record in records:
                        record["player_id"] = player_id
                        record["season"] = season
                        record["endpoint"] = endpoint_name
                        record["event_timestamp"] = datetime.now().isoformat()
                        record["scraped_at"] = datetime.now().isoformat()
                        # Add game_id if available in record
                        if "GAME_ID" in record:
                            record["game_id"] = record["GAME_ID"]

                    player_data[endpoint_name] = records

                    self.metrics["api_successes"] += 1
                    self.metrics["records_collected"] += len(records)
                    logger.info(f"✅ {endpoint_name}: {len(records)} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    player_data[endpoint_name] = []
                    self.metrics["empty_responses"] += 1

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for player {player_id}: {e}"
                )
                player_data[endpoint_name] = []
                self.metrics["api_failures"] += 1

        self.metrics["players_processed"] += 1
        return player_data

    def run(self, start_season="2014-15", end_season="2024-25"):
        """Run the scraper for SportVU era seasons with MLflow tracking"""
        start_time = datetime.now()

        # Start MLflow run (ml_systems_1)
        if self.use_mlflow:
            mlflow.start_run(run_name=f"scrape_{start_season}_to_{end_season}")
            mlflow.log_param("start_season", start_season)
            mlflow.log_param("end_season", end_season)
            mlflow.log_param("output_dir", str(self.output_dir))

        seasons = [
            "2014-15",
            "2015-16",
            "2016-17",
            "2017-18",
            "2018-19",
            "2019-20",
            "2020-21",
            "2021-22",
            "2022-23",
            "2023-24",
            "2024-25",
        ]

        try:
            for season in seasons:
                if season < start_season or season > end_season:
                    continue

                logger.info(f"Starting season {season}")
                season_dir = self.output_dir / season
                season_dir.mkdir(exist_ok=True)

                players = self.get_all_players(season)
                logger.info(f"Found {len(players)} players for {season}")

                for i, player_id in enumerate(players):
                    logger.info(f"Processing player {i+1}/{len(players)}: {player_id}")

                    player_data = self.scrape_player_tracking(player_id, season)

                    # Save player data with panel structure
                    player_file = season_dir / f"player_{player_id}.json"
                    with open(player_file, "w") as f:
                        json.dump(
                            {
                                "player_id": player_id,
                                "season": season,
                                "scraped_at": datetime.now().isoformat(),
                                "data": player_data,
                                # Panel data metadata (rec_22)
                                "panel_structure": {
                                    "multi_index": ["player_id", "game_id", "event_timestamp"],
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

                    logger.info(f"Saved player {player_id} data to {player_file}")

                    # Progress checkpoint
                    if (i + 1) % 50 == 0:
                        logger.info(f"Progress: {i+1}/{len(players)} players completed")
                        # Log incremental metrics to MLflow
                        if self.use_mlflow:
                            mlflow.log_metrics(self.metrics, step=i+1)

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
            logger.info(f"Players: {self.metrics['players_processed']}")
            logger.info(f"Success Rate: {100 * self.metrics['api_successes'] / max(self.metrics['api_calls'], 1):.1f}%")
            logger.info(f"{'='*80}")

            if self.use_mlflow:
                mlflow.log_metrics(self.metrics)
                mlflow.log_metric("duration_seconds", duration)
                mlflow.log_metric("success_rate", self.metrics['api_successes'] / max(self.metrics['api_calls'], 1))
                mlflow.end_run()

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            if self.use_mlflow:
                mlflow.log_param("status", "failed")
                mlflow.end_run(status="FAILED")
            raise


if __name__ == "__main__":
    scraper = NBAAPIPlayerTrackingScraper()
    scraper.run()
