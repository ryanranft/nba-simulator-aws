#!/usr/bin/env python3
"""
Scrape Failed Games by Game ID

This script scrapes specific games that failed during the ESPN PBP extraction
by directly using their game IDs with the ESPN API.
"""

import asyncio
import aiohttp
import json
import logging
import os
import ssl
from pathlib import Path
from typing import List, Dict, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FailedGamesScraper:
    def __init__(self, output_dir: str = "data/scraped_failed_games"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Failed game IDs from the extraction log
        self.failed_game_ids = [
            "201024017",
            "131207019",
            "400223639",
            "401734908",
            "400232028",
            "151112012",
            "401705756",
            "180116011",
            "400216824",
            "190408025",
            "151216004",
            "171107013",
            "400228075",
            "400232881",
            "210213024",
            "271009013",
            "180106011",
            "171213005",
            "400228425",
            "140325021",
            "131215024",
            "180501010",
            "190307011",
            "170111029",
            "170113014",
            "180317022",
            "200427011",
            "200117001",
            "211207023",
            "160310029",
            "190329006",
            "211111008",
            "200107001",
            "401705243",
            "150325012",
            "131123006",
            "151228013",
            "400234810",
            "210125006",
            "210415016",
            "401705613",
            "400224543",
            "140307015",
            "151120026",
            "190210009",
            "180124025",
            "161226006",
            "180205003",
            "140111022",
            "201023013",
            "191115021",
            "400233951",
            "401705097",
            "190227004",
            "151115016",
            "150131018",
            "400226600",
            "190310015",
            "140407100",
            "200226027",
            "160327024",
            "200412021",
            "210208003",
            "400225186",
            "210214020",
            "161228018",
            "400227441",
            "191119002",
            "150524024",
            "170305023",
            "140322025",
            "171208022",
            "140209017",
            "140217009",
            "160104023",
            "211011014",
            "170114010",
            "400234328",
            "160222001",
            "400222706",
            "210311005",
            "220115004",
            "200204013",
            "201222020",
            "191223003",
            "150421001",
            "160418019",
            "400234778",
            "190219013",
            "170104010",
            "400226315",
            "191127015",
            "210301005",
            "141105025",
            "400231829",
            "401705078",
            "141119006",
            "400219456",
            "401705582",
            "150322016",
            "160126017",
            "400235493",
            "180123021",
            "151127022",
            "401705428",
            "220105004",
            "400235169",
            "190322021",
            "211118012",
            "400224282",
            "131230014",
            "400236196",
            "400225240",
            "131109005",
            "160201018",
            "151202010",
            "210113026",
            "400220412",
            "140204019",
            "400237787",
        ]

        # ESPN API configuration
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
        self.rate_limit_delay = 1.0  # 1 second between requests

        # Create SSL context to handle certificate issues
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with SSL context"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)

        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
            },
        )

    async def fetch_game_data(
        self, session: aiohttp.ClientSession, game_id: str
    ) -> Optional[Dict]:
        """Fetch play-by-play data for a specific game ID"""
        url = f"{self.base_url}/playbyplay/{game_id}"

        try:
            logger.info(f"Fetching game {game_id}...")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Successfully fetched game {game_id}")
                    return data
                else:
                    logger.warning(f"⚠️ Game {game_id}: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Game {game_id}: {str(e)}")
            return None

    async def scrape_all_failed_games(self):
        """Scrape all failed games with rate limiting"""
        logger.info(f"Starting to scrape {len(self.failed_game_ids)} failed games...")

        async with await self.create_session() as session:
            successful_games = 0
            failed_games = 0

            for i, game_id in enumerate(self.failed_game_ids):
                logger.info(
                    f"Processing game {i+1}/{len(self.failed_game_ids)}: {game_id}"
                )

                # Fetch game data
                game_data = await self.fetch_game_data(session, game_id)

                if game_data:
                    # Save game data
                    output_file = self.output_dir / f"{game_id}.json"
                    with open(output_file, "w") as f:
                        json.dump(game_data, f, indent=2)

                    successful_games += 1
                    logger.info(f"✅ Saved game {game_id} to {output_file}")
                else:
                    failed_games += 1
                    logger.warning(f"❌ Failed to fetch game {game_id}")

                # Rate limiting
                if i < len(self.failed_game_ids) - 1:  # Don't delay after last request
                    await asyncio.sleep(self.rate_limit_delay)

            # Summary
            logger.info("=" * 50)
            logger.info("SCRAPING SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Total games attempted: {len(self.failed_game_ids)}")
            logger.info(f"Successful: {successful_games}")
            logger.info(f"Failed: {failed_games}")
            logger.info(
                f"Success rate: {(successful_games/len(self.failed_game_ids)*100):.1f}%"
            )
            logger.info(f"Output directory: {self.output_dir}")

            return successful_games, failed_games


def main():
    """Main function"""
    scraper = FailedGamesScraper()

    logger.info("Starting failed games scraper...")
    logger.info(f"Target games: {len(scraper.failed_game_ids)}")
    logger.info(f"Output directory: {scraper.output_dir}")

    # Run the scraper
    successful, failed = asyncio.run(scraper.scrape_all_failed_games())

    if successful > 0:
        logger.info(f"✅ Successfully scraped {successful} games!")
    else:
        logger.error("❌ No games were successfully scraped")

    return successful, failed


if __name__ == "__main__":
    main()


