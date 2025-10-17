#!/usr/bin/env python3
"""
NBA API Player Dashboards Scraper
Collects 7 player dashboard endpoints with situational metrics
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    PlayerDashboardByClutch,
    PlayerDashboardByGeneralSplits,
    PlayerDashboardByShootingSplits,
    PlayerDashboardByLastNGames,
    PlayerDashboardByTeamPerformance,
    PlayerDashboardByYearOverYear,
    CommonAllPlayers,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBAAPIPlayerDashboardsScraper:
    def __init__(self, output_dir="/tmp/nba_api_player_dashboards"):
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

        logger.info("NBA API Player Dashboards Scraper initialized")

    def get_all_players(self, season="2023-24"):
        """Get all players for a season"""
        try:
            players_info = CommonAllPlayers(season=season)
            players_df = players_info.get_data_frames()[0]
            return players_df["PERSON_ID"].tolist()
        except Exception as e:
            logger.error(f"Error getting players for {season}: {e}")
            return []

    def scrape_player_dashboards(self, player_id, season="2023-24"):
        """Scrape all dashboard endpoints for a player"""
        player_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")

                if endpoint_name == "last_n_games":
                    endpoint = endpoint_class(
                        player_id=player_id, season=season, last_n_games=5
                    )
                else:
                    endpoint = endpoint_class(player_id=player_id, season=season)

                data_frames = endpoint.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    player_data[endpoint_name] = data_frames[0].to_dict("records")
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    player_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for player {player_id}: {e}"
                )
                player_data[endpoint_name] = []

        return player_data

    def run(self, start_season="2020-21", end_season="2024-25"):
        """Run the scraper for multiple seasons"""
        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

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

                # Save player data
                player_file = season_dir / f"player_{player_id}.json"
                with open(player_file, "w") as f:
                    json.dump(
                        {
                            "player_id": player_id,
                            "season": season,
                            "scraped_at": datetime.now().isoformat(),
                            "data": player_data,
                        },
                        f,
                        indent=2,
                    )

                logger.info(f"Saved player {player_id} data to {player_file}")

                # Progress checkpoint
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(players)} players completed")


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
