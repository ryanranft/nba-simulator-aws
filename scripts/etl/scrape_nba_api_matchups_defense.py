#!/usr/bin/env python3
"""
NBA API Matchups & Defense Scraper
Collects 5 matchup and defensive tracking endpoints
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    LeagueDashPlayerPtShot,
    LeagueDashPlayerShotLocations,
    LeagueDashTeamPtShot,
    LeagueDashTeamShotLocations,
    BoxScoreMatchupsV3,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBAAPIMatchupsDefenseScraper:
    def __init__(self, output_dir="/tmp/nba_api_matchups_defense"):
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

        self.matchup_endpoints = [
            ("player_pt_shot", LeagueDashPlayerPtShot),
            ("player_shot_locations", LeagueDashPlayerShotLocations),
            ("team_pt_shot", LeagueDashTeamPtShot),
            ("team_shot_locations", LeagueDashTeamShotLocations),
        ]

        logger.info("NBA API Matchups & Defense Scraper initialized")

    def scrape_league_endpoints(self, season="2023-24"):
        """Scrape league-wide endpoints"""
        league_data = {}

        for endpoint_name, endpoint_class in self.matchup_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for {season}")

                endpoint = endpoint_class(season=season)
                data_frames = endpoint.get_data_frames()

                if data_frames and len(data_frames) > 0:
                    league_data[endpoint_name] = data_frames[0].to_dict("records")
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    league_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error scraping {endpoint_name}: {e}")
                league_data[endpoint_name] = []

        return league_data

    def run(self, start_season="2020-21", end_season="2024-25"):
        """Run the scraper for multiple seasons"""
        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            league_data = self.scrape_league_endpoints(season)

            # Save league data
            league_file = season_dir / f"league_matchups_defense.json"
            with open(league_file, "w") as f:
                json.dump(
                    {
                        "season": season,
                        "scraped_at": datetime.now().isoformat(),
                        "data": league_data,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"Saved league data for {season} to {league_file}")


if __name__ == "__main__":
    scraper = NBAAPIMatchupsDefenseScraper()
    scraper.run()
