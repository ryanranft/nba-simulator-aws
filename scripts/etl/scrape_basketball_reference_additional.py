#!/usr/bin/env python3
"""
Basketball Reference Additional Functions Scraper
Collects additional BR endpoints for splits, team stats, standings
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import random

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BasketballReferenceAdditionalScraper:
    def __init__(self, output_dir="/tmp/bbref_additional"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        # Rotating user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        ]

        self.base_url = "https://www.basketball-reference.com"

        logger.info("Basketball Reference Additional Scraper initialized")

    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({"User-Agent": user_agent})

    def scrape_additional_endpoints(self, year):
        """Scrape additional Basketball Reference endpoints"""
        try:
            self.rotate_user_agent()

            # Additional endpoints to try
            endpoints = [
                f"/leagues/NBA_{year}_standings.html",  # Standings
                f"/leagues/NBA_{year}_misc_stats.html",  # Miscellaneous stats
                f"/leagues/NBA_{year}_opp_per_game.html",  # Opponent stats
                f"/leagues/NBA_{year}_ratings.html",  # Team ratings
                f"/leagues/NBA_{year}_roster_stats.html",  # Roster stats
            ]

            additional_data = {}

            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"Scraping {url}")

                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()

                    if (
                        len(response.text) > 1000
                        and "basketball-reference.com" in response.text
                    ):
                        additional_data[endpoint.split("/")[-1]] = {
                            "url": url,
                            "content_length": len(response.text),
                            "scraped_at": datetime.now().isoformat(),
                            "status": "success",
                        }
                        logger.info(f"✅ Successfully scraped {endpoint}")
                    else:
                        logger.warning(f"⚠️ {endpoint}: Content too short or invalid")
                        additional_data[endpoint.split("/")[-1]] = {
                            "url": url,
                            "status": "failed",
                            "reason": "content_too_short",
                        }

                    time.sleep(random.uniform(20, 40))

                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Error scraping {endpoint}: {e}")
                    additional_data[endpoint.split("/")[-1]] = {
                        "url": url,
                        "status": "failed",
                        "error": str(e),
                    }
                    time.sleep(random.uniform(40, 80))

            return additional_data

        except Exception as e:
            logger.error(f"❌ Error scraping additional endpoints for {year}: {e}")
            return {}

    def run(self, start_year=2016, end_year=2025):
        """Run the scraper for multiple years"""
        years = list(range(start_year, end_year + 1))

        for year in years:
            logger.info(f"Starting year {year}")
            year_dir = self.output_dir / str(year)
            year_dir.mkdir(exist_ok=True)

            additional_data = self.scrape_additional_endpoints(year)

            # Save additional data
            additional_file = year_dir / f"bbref_additional_{year}.json"
            with open(additional_file, "w") as f:
                json.dump(
                    {
                        "year": year,
                        "scraped_at": datetime.now().isoformat(),
                        "data": additional_data,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"Saved additional data for {year} to {additional_file}")


if __name__ == "__main__":
    scraper = BasketballReferenceAdditionalScraper()
    scraper.run()
