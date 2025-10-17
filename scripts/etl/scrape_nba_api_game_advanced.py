#!/usr/bin/env python3
"""
NBA API Game-Level Advanced Stats Scraper
Collects 4 game-level endpoints for rotation, win probability, etc.
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    GameRotation,
    WinProbabilityPBP,
    GLAlumBoxScoreSimilarityScore,
    LeagueGameFinder,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBAAPIGameAdvancedScraper:
    def __init__(self, output_dir="/tmp/nba_api_game_advanced"):
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
            ("win_probability", WinProbabilityPBP),
            ("similarity", GLAlumBoxScoreSimilarityScore),
        ]

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
        """Scrape all advanced endpoints for a game"""
        game_data = {}

        for endpoint_name, endpoint_class in self.game_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for game {game_id}")

                endpoint = endpoint_class(game_id=game_id)
                data_frames = endpoint.get_data_frames()

                if data_frames and len(data_frames) > 0:
                    game_data[endpoint_name] = data_frames[0].to_dict("records")
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    game_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for game {game_id}: {e}"
                )
                game_data[endpoint_name] = []

        return game_data

    def run(self, start_season="2020-21", end_season="2024-25"):
        """Run the scraper for multiple seasons"""
        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

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

                # Save game data
                game_file = season_dir / f"game_{game_id}.json"
                with open(game_file, "w") as f:
                    json.dump(
                        {
                            "game_id": game_id,
                            "season": season,
                            "scraped_at": datetime.now().isoformat(),
                            "data": game_data,
                        },
                        f,
                        indent=2,
                    )

                logger.info(f"Saved game {game_id} data to {game_file}")

                # Progress checkpoint
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i+1}/{len(games)} games completed")


if __name__ == "__main__":
    scraper = NBAAPIGameAdvancedScraper()
    scraper.run()
