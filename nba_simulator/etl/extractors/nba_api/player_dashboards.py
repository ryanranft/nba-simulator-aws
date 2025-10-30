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

Version: 2.0 (Migrated to AsyncBaseScraper framework)
Migration Date: October 22, 2025
"""

import asyncio
import json
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

# AsyncBaseScraper imports
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

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


class NBAAPIPlayerDashboardsScraper(AsyncBaseScraper):
    def __init__(
        self,
        config=None,
        output_dir=None,
        use_mlflow=None,
        scraper_name="nba_api_player_dashboards",
    ):
        # Load configuration from scraper_config.yaml if not provided
        if config is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "scraper_config.yaml"
            )
            config_manager = ScraperConfigManager(str(config_path))
            config = config_manager.get_scraper_config(scraper_name)

        # Store config before calling super().__init__
        self._raw_config = config

        # Initialize parent AsyncBaseScraper
        super().__init__(config)

        # Override output_dir if provided
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(self._raw_config.storage.local_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.dashboard_endpoints = [
            ("clutch", PlayerDashboardByClutch),
            ("general_splits", PlayerDashboardByGeneralSplits),
            ("shooting_splits", PlayerDashboardByShootingSplits),
            ("last_n_games", PlayerDashboardByLastNGames),
            ("team_performance", PlayerDashboardByTeamPerformance),
            ("year_over_year", PlayerDashboardByYearOverYear),
        ]

        # MLflow tracking setup (ml_systems_1)
        if use_mlflow is not None:
            self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        else:
            self.use_mlflow = (
                self._raw_config.custom_settings.get("use_mlflow", True)
                and MLFLOW_AVAILABLE
            )

        if self.use_mlflow:
            experiment_name = self._raw_config.custom_settings.get(
                "mlflow_experiment", "nba_api_player_dashboards_scraper"
            )
            mlflow.set_experiment(experiment_name)
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

        logger.info(
            "NBA API Player Dashboards Scraper initialized (AsyncBaseScraper framework)"
        )

    async def scrape(self):
        """Required by AsyncBaseScraper - delegates to run()"""
        pass

    async def get_all_players(self, season="2023-24"):
        """Get all players for a season (async wrapper for nba_api)"""
        try:

            def _get_players_sync():
                players_info = CommonAllPlayers(season=season)
                players_df = players_info.get_data_frames()[0]
                logger.info(f"Found {len(players_df)} total players for {season}")
                return players_df["PERSON_ID"].tolist()

            players = await asyncio.to_thread(_get_players_sync)
            return players
        except Exception as e:
            logger.error(f"Error getting players for {season}: {e}")
            return []

    async def scrape_player_dashboards(self, player_id, season="2023-24"):
        """Scrape all dashboard endpoints for a player with panel data structure (async)"""
        player_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")
                self.metrics["api_calls"] += 1

                # Rate limiting via AsyncBaseScraper
                await self.rate_limiter.acquire()

                # Wrap synchronous nba_api call in asyncio.to_thread
                def _scrape_endpoint_sync():
                    if endpoint_name == "last_n_games":
                        endpoint = endpoint_class(
                            player_id=player_id, season=season, last_n_games=5
                        )
                    else:
                        endpoint = endpoint_class(player_id=player_id, season=season)
                    return endpoint.get_data_frames()

                data_frames = await asyncio.to_thread(_scrape_endpoint_sync)

                if data_frames and len(data_frames) > 0:
                    records = data_frames[0].to_dict("records")

                    # Add panel data structure (rec_22)
                    for record in records:
                        record["player_id"] = player_id
                        record["season"] = season
                        record["endpoint"] = endpoint_name
                        record["event_timestamp"] = datetime.now().isoformat()
                        record["scraped_at"] = datetime.now().isoformat()
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

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for player {player_id}: {e}"
                )
                player_data[endpoint_name] = []
                self.metrics["api_failures"] += 1

        self.metrics["players_processed"] += 1
        return player_data

    async def run(self, start_season=None, end_season=None):
        """Run the scraper for multiple seasons with MLflow tracking (async)"""
        if start_season is None:
            start_season = self._raw_config.custom_settings.get(
                "default_start_season", "2020-21"
            )
        if end_season is None:
            end_season = self._raw_config.custom_settings.get(
                "default_end_season", "2024-25"
            )

        start_time = datetime.now()

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

                players = await self.get_all_players(season)
                logger.info(f"Found {len(players)} players for {season}")

                for i, player_id in enumerate(players):
                    logger.info(f"Processing player {i+1}/{len(players)}: {player_id}")

                    player_data = await self.scrape_player_dashboards(player_id, season)

                    full_player_data = {
                        "player_id": player_id,
                        "season": season,
                        "scraped_at": datetime.now().isoformat(),
                        "data": player_data,
                        "panel_structure": {
                            "multi_index": ["player_id", "game_id", "event_timestamp"],
                            "temporal_features_ready": True,
                        },
                        "features": {"generated": False, "version": "1.0"},
                    }

                    # Save player data locally
                    player_file = season_dir / f"player_{player_id}.json"
                    with open(player_file, "w") as f:
                        json.dump(full_player_data, f, indent=2)

                    logger.info(f"Saved player {player_id} data to {player_file}")

                    # Optional: Upload to S3 via AsyncBaseScraper
                    if self._raw_config.storage.upload_to_s3:
                        s3_key = f"{season}/player_{player_id}.json"
                        await self.store_data(full_player_data, s3_key)
                        logger.info(f"Uploaded player {player_id} to S3: {s3_key}")

                    if (i + 1) % 50 == 0:
                        logger.info(f"Progress: {i+1}/{len(players)} players completed")
                        if self.use_mlflow:
                            mlflow.log_metrics(self.metrics, step=i + 1)

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


async def main():
    """Main entry point for the scraper"""
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
    await scraper.run(start_season=args.start_season, end_season=args.end_season)


if __name__ == "__main__":
    asyncio.run(main())
