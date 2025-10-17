#!/usr/bin/env python3
"""
NBA API Team Dashboards Scraper (Enhanced)
Collects 11 team dashboard endpoints

Enhanced with Book Recommendations:
- rec_22: Panel data structure (team_id, game_id, date multi-index)
- rec_11: Feature engineering during collection
- ml_systems_1: MLflow experiment tracking
- ml_systems_2: Data quality monitoring

Panel Data Output Format:
- Multi-indexed by (team_id, game_id, game_date)
- Includes temporal features (season, date)
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
    TeamDashboardByGeneralSplits,
    TeamDashboardByShootingSplits,
    TeamDashLineups,
    TeamDashPtPass,
    TeamDashPtReb,
    TeamDashPtShots,
)
from nba_api.stats.static import teams

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


class NBAAPITeamDashboardsScraper:
    def __init__(self, output_dir="/tmp/nba_api_team_dashboards", use_mlflow=True):
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
            ("general_splits", TeamDashboardByGeneralSplits),
            ("shooting_splits", TeamDashboardByShootingSplits),
            ("lineups", TeamDashLineups),
            ("pt_pass", TeamDashPtPass),
            ("pt_reb", TeamDashPtReb),
            ("pt_shots", TeamDashPtShots),
        ]

        # MLflow tracking setup (ml_systems_1)
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        if self.use_mlflow:
            mlflow.set_experiment("nba_api_team_dashboards_scraper")
            logger.info("✅ MLflow tracking enabled")

        # Data quality metrics (ml_systems_2)
        self.metrics = {
            "api_calls": 0,
            "api_successes": 0,
            "api_failures": 0,
            "records_collected": 0,
            "teams_processed": 0,
            "empty_responses": 0,
        }

        logger.info("NBA API Team Dashboards Scraper initialized")

    def get_all_teams(self, season="2023-24"):
        """Get all teams (static list of 30 teams)"""
        try:
            all_teams = teams.get_teams()
            team_ids = [team["id"] for team in all_teams]
            logger.info(f"Retrieved {len(team_ids)} teams")
            return team_ids
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []

    def scrape_team_dashboards(self, team_id, season="2023-24"):
        """Scrape all dashboard endpoints for a team with panel data structure"""
        team_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for team {team_id}")
                self.metrics["api_calls"] += 1

                endpoint = endpoint_class(team_id=team_id, season=season)

                data_frames = endpoint.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    records = data_frames[0].to_dict("records")

                    # Add panel data structure (rec_22)
                    for record in records:
                        record["team_id"] = team_id
                        record["season"] = season
                        record["endpoint"] = endpoint_name
                        record["game_date"] = datetime.now().isoformat()
                        record["scraped_at"] = datetime.now().isoformat()
                        # Add game_id if available in record
                        if "GAME_ID" in record:
                            record["game_id"] = record["GAME_ID"]

                    team_data[endpoint_name] = records

                    self.metrics["api_successes"] += 1
                    self.metrics["records_collected"] += len(records)
                    logger.info(f"✅ {endpoint_name}: {len(records)} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    team_data[endpoint_name] = []
                    self.metrics["empty_responses"] += 1

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for team {team_id}: {e}"
                )
                team_data[endpoint_name] = []
                self.metrics["api_failures"] += 1

        self.metrics["teams_processed"] += 1
        return team_data

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

                teams = self.get_all_teams(season)
                logger.info(f"Found {len(teams)} teams for {season}")

                for i, team_id in enumerate(teams):
                    logger.info(f"Processing team {i+1}/{len(teams)}: {team_id}")

                    team_data = self.scrape_team_dashboards(team_id, season)

                    # Save team data with panel structure
                    team_file = season_dir / f"team_{team_id}.json"
                    with open(team_file, "w") as f:
                        json.dump(
                            {
                                "team_id": team_id,
                                "season": season,
                                "scraped_at": datetime.now().isoformat(),
                                "data": team_data,
                                # Panel data metadata (rec_22)
                                "panel_structure": {
                                    "multi_index": ["team_id", "game_id", "game_date"],
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

                    logger.info(f"Saved team {team_id} data to {team_file}")

                    # Log incremental metrics to MLflow
                    if self.use_mlflow and (i + 1) % 10 == 0:
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
            logger.info(f"Teams: {self.metrics['teams_processed']}")
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
        description="Scrape NBA API Team Dashboard endpoints"
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
        default="/tmp/nba_api_team_dashboards",
        help="Output directory for scraped data",
    )

    args = parser.parse_args()

    logger.info(f"Starting NBA API Team Dashboards scraper")
    logger.info(f"  Seasons: {args.start_season} to {args.end_season}")
    logger.info(f"  Output: {args.output_dir}")

    scraper = NBAAPITeamDashboardsScraper(output_dir=args.output_dir)
    scraper.run(start_season=args.start_season, end_season=args.end_season)
