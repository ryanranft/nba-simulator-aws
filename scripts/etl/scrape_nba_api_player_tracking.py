#!/usr/bin/env python3
"""
NBA API Player Tracking Scraper (Fixed)
Collects 4 player tracking endpoints with SportVU data
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    PlayerDashPtPass,
    PlayerDashPtReb,
    PlayerDashPtShotDefend,
    PlayerDashPtShots,
    CommonAllPlayers,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBAAPIPlayerTrackingScraper:
    def __init__(self, output_dir="/tmp/nba_api_player_tracking"):
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
        """Scrape all tracking endpoints for a player"""
        player_data = {}

        for endpoint_name, endpoint_class in self.tracking_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")

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

    def run(self, start_season="2014-15", end_season="2024-25"):
        """Run the scraper for SportVU era seasons"""
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
    scraper = NBAAPIPlayerTrackingScraper()
    scraper.run()
