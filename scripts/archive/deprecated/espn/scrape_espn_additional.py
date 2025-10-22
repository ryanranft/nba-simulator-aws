#!/usr/bin/env python3
"""
ESPN Additional Endpoints Scraper
Collects missing ESPN endpoints for rosters, teams, calendar
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ESPNAdditionalScraper:
    def __init__(self, output_dir="/tmp/espn_additional"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )

        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

        logger.info("ESPN Additional Scraper initialized")

    def scrape_espn_endpoints(self, season="2023-24"):
        """Scrape additional ESPN endpoints"""
        try:
            # Convert season format (2023-24 -> 2024)
            year = int(season.split("-")[1])

            espn_data = {}

            # Calendar endpoint
            calendar_url = f"{self.base_url}/calendar"
            logger.info(f"Scraping calendar: {calendar_url}")

            try:
                response = self.session.get(calendar_url, timeout=30)
                response.raise_for_status()
                calendar_data = response.json()
                espn_data["calendar"] = calendar_data
                logger.info("✅ Successfully scraped calendar")
            except Exception as e:
                logger.error(f"❌ Error scraping calendar: {e}")
                espn_data["calendar"] = {"error": str(e)}

            time.sleep(1.5)

            # Teams endpoint
            teams_url = f"{self.base_url}/teams"
            logger.info(f"Scraping teams: {teams_url}")

            try:
                response = self.session.get(teams_url, timeout=30)
                response.raise_for_status()
                teams_data = response.json()
                espn_data["teams"] = teams_data
                logger.info("✅ Successfully scraped teams")
            except Exception as e:
                logger.error(f"❌ Error scraping teams: {e}")
                espn_data["teams"] = {"error": str(e)}

            time.sleep(1.5)

            # Try to get some game rosters (sample games)
            try:
                # Get recent games to sample rosters
                scoreboard_url = f"{self.base_url}/scoreboard"
                response = self.session.get(scoreboard_url, timeout=30)
                response.raise_for_status()
                scoreboard_data = response.json()

                espn_data["scoreboard"] = scoreboard_data

                # Sample a few games for rosters
                if "events" in scoreboard_data:
                    sample_games = scoreboard_data["events"][:3]  # Sample first 3 games
                    espn_data["sample_rosters"] = {}

                    for game in sample_games:
                        game_id = game.get("id")
                        if game_id:
                            roster_url = f"{self.base_url}/events/{game_id}/roster"
                            try:
                                response = self.session.get(roster_url, timeout=30)
                                response.raise_for_status()
                                roster_data = response.json()
                                espn_data["sample_rosters"][game_id] = roster_data
                                logger.info(
                                    f"✅ Successfully scraped roster for game {game_id}"
                                )
                            except Exception as e:
                                logger.error(
                                    f"❌ Error scraping roster for game {game_id}: {e}"
                                )
                                espn_data["sample_rosters"][game_id] = {"error": str(e)}

                            time.sleep(1.5)

                logger.info("✅ Successfully scraped sample rosters")

            except Exception as e:
                logger.error(f"❌ Error scraping rosters: {e}")
                espn_data["rosters"] = {"error": str(e)}

            return espn_data

        except Exception as e:
            logger.error(f"❌ Error scraping ESPN endpoints for {season}: {e}")
            return {}

    def run(self, start_season="2020-21", end_season="2024-25"):
        """Run the scraper for multiple seasons"""
        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            espn_data = self.scrape_espn_endpoints(season)

            # Save ESPN data
            espn_file = season_dir / f"espn_additional_{season}.json"
            with open(espn_file, "w") as f:
                json.dump(
                    {
                        "season": season,
                        "scraped_at": datetime.now().isoformat(),
                        "data": espn_data,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"Saved ESPN additional data for {season} to {espn_file}")


if __name__ == "__main__":
    scraper = ESPNAdditionalScraper()
    scraper.run()
