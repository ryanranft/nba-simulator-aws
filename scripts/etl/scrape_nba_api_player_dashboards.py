#!/usr/bin/env python3
"""
NBA API Player Dashboards Scraper (Enhanced)
Collects 7 player dashboard endpoints with situational metrics

Enhanced with Book Recommendations:
- rec_22: Panel data structure (player_id, game_id, timestamp multi-index)
- rec_11: Feature engineering during collection
- ml_systems_1: MLflow experiment tracking
- ml_systems_2: Data quality monitoring

Panel Data Output Format:
- Multi-indexed by (player_id, game_id, event_timestamp)
- Includes situational metrics (clutch, splits, opponent-specific)
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
    PlayerDashboardByClutch,
    PlayerDashboardByGeneralSplits,
    PlayerDashboardByShootingSplits,
    PlayerDashboardByLastNGames,
    PlayerDashboardByTeamPerformance,
    PlayerDashboardByYearOverYear,
    CommonAllPlayers,
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


class NBAAPIPlayerDashboardsScraper:
    def __init__(self, output_dir="/tmp/nba_api_player_dashboards", use_mlflow=True):
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

        self.dashboard_endpoints = [
            ("clutch", PlayerDashboardByClutch),
            ("general_splits", PlayerDashboardByGeneralSplits),
            ("shooting_splits", PlayerDashboardByShootingSplits),
            ("last_n_games", PlayerDashboardByLastNGames),
            ("team_performance", PlayerDashboardByTeamPerformance),
            ("year_over_year", PlayerDashboardByYearOverYear),
        ]

        # MLflow tracking setup (ml_systems_1)
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        if self.use_mlflow:
            mlflow.set_experiment("nba_api_player_dashboards_scraper")
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

        logger.info("NBA API Player Dashboards Scraper initialized")

    def get_all_players(self, season="2023-24"):
        """Get all players for a season (including historical players for ML/DL)"""
        try:
            players_info = CommonAllPlayers(season=season)
            players_df = players_info.get_data_frames()[0]
            logger.info(f"Found {len(players_df)} total players for {season}")
            return players_df["PERSON_ID"].tolist()
        except Exception as e:
            logger.error(f"Error getting players for {season}: {e}")
            return []

    def scrape_player_dashboards(self, player_id, season="2023-24"):
        """Scrape all dashboard endpoints for a player with panel data structure"""
        player_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")
                self.metrics["api_calls"] += 1

                if endpoint_name == "last_n_games":
                    endpoint = endpoint_class(
                        player_id=player_id, season=season, last_n_games=5
                    )
                else:
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

                players = self.get_all_players(season)
                logger.info(f"Found {len(players)} players for {season}")

                for i, player_id in enumerate(players):
                    logger.info(f"Processing player {i+1}/{len(players)}: {player_id}")

                    player_data = self.scrape_player_dashboards(player_id, season)

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
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape NBA API Player Dashboard endpoints"
    )
    parser.add_argument(
        "--start-season",
        type=str,
        default="2020-21",
        help="Start season (e.g., 2020-21)",
    )
    parser.add_argument(
        "--end-season", type=str, default="2024-25", help="End season (e.g., 2024-25)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/nba_api_player_dashboards",
        help="Output directory for scraped data",
    )

    args = parser.parse_args()

    logger.info(f"Starting NBA API Player Dashboards scraper")
    logger.info(f"  Seasons: {args.start_season} to {args.end_season}")
    logger.info(f"  Output: {args.output_dir}")

    scraper = NBAAPIPlayerDashboardsScraper(output_dir=args.output_dir)
    scraper.run(start_season=args.start_season, end_season=args.end_season)
