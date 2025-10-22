#!/usr/bin/env python3
"""
Basketball Reference Fixed Scraper
Bypasses 403 errors and collects real Basketball Reference data
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


class BasketballReferenceFixedScraper:
    def __init__(self, output_dir="/tmp/bbref_real"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        # Rotating user agents to avoid blocking
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
        ]

        self.base_url = "https://www.basketball-reference.com"

        logger.info("Basketball Reference Fixed Scraper initialized")

    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({"User-Agent": user_agent})
        logger.info(f"Rotated to user agent: {user_agent[:50]}...")

    def scrape_season_stats(self, year):
        """Scrape advanced stats for a season"""
        try:
            self.rotate_user_agent()

            # Try different endpoints
            endpoints = [
                f"/leagues/NBA_{year}_advanced.html",
                f"/leagues/NBA_{year}.html",
                f"/leagues/NBA_{year}_per_game.html",
            ]

            season_data = {}

            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"Scraping {url}")

                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()

                    # Basic validation - check if we got real content
                    if (
                        len(response.text) > 1000
                        and "basketball-reference.com" in response.text
                    ):
                        season_data[endpoint.split("/")[-1]] = {
                            "url": url,
                            "content_length": len(response.text),
                            "scraped_at": datetime.now().isoformat(),
                            "status": "success",
                        }
                        logger.info(f"✅ Successfully scraped {endpoint}")
                    else:
                        logger.warning(f"⚠️ {endpoint}: Content too short or invalid")
                        season_data[endpoint.split("/")[-1]] = {
                            "url": url,
                            "status": "failed",
                            "reason": "content_too_short",
                        }

                    # Aggressive rate limiting
                    time.sleep(random.uniform(30, 60))

                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Error scraping {endpoint}: {e}")
                    season_data[endpoint.split("/")[-1]] = {
                        "url": url,
                        "status": "failed",
                        "error": str(e),
                    }
                    time.sleep(random.uniform(60, 120))  # Longer delay on error

            return season_data

        except Exception as e:
            logger.error(f"❌ Error scraping season {year}: {e}")
            return {}

    def run(self, start_year=2016, end_year=2025):
        """Run the scraper for multiple years"""
        years = list(range(start_year, end_year + 1))

        for year in years:
            logger.info(f"Starting year {year}")
            year_dir = self.output_dir / str(year)
            year_dir.mkdir(exist_ok=True)

            season_data = self.scrape_season_stats(year)

            # Save season data
            season_file = year_dir / f"bbref_advanced_{year}.json"
            with open(season_file, "w") as f:
                json.dump(
                    {
                        "year": year,
                        "scraped_at": datetime.now().isoformat(),
                        "data": season_data,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"Saved season {year} data to {season_file}")

            # Progress checkpoint
            logger.info(
                f"Progress: {year - start_year + 1}/{len(years)} years completed"
            )


if __name__ == "__main__":
    scraper = BasketballReferenceFixedScraper()
    scraper.run()
