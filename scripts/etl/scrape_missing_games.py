#!/usr/bin/env python3
"""
ESPN Missing Games Scraper

Scrapes specific missing games identified by the missing games analysis.
Targets only the games that are actually missing from our dataset.

Usage:
    python scripts/etl/scrape_missing_games.py --missing-games data/missing_games_report.json
    python scripts/etl/scrape_missing_games.py --game-id 401234567 --output-dir data/missing_games

Version: 1.0
Created: October 13, 2025
"""

import json
import os
import argparse
import logging
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import ssl

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/missing_games_scraper.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ESPNMissingGamesScraper:
    """Scrapes specific missing games from ESPN"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "games_attempted": 0,
            "games_successful": 0,
            "games_failed": 0,
            "total_plays": 0,
        }

        logger.info(f"Initialized ESPN Missing Games Scraper")
        logger.info(f"Output directory: {self.output_dir}")

    async def scrape_game(
        self, session: aiohttp.ClientSession, game_id: str
    ) -> Optional[Dict]:
        """Scrape a single game by ID"""
        try:
            # ESPN PBP URL format
            url = f"https://www.espn.com/nba/game/_/gameId/{game_id}"

            logger.info(f"Scraping game {game_id}")

            # Add headers to mimic browser request
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html_content = await response.text()

                    # Try to extract JSON data from the page
                    # ESPN embeds game data in script tags
                    import re

                    # Look for window.espn.gamepackageData
                    pattern = r"window\.espn\.gamepackageData\s*=\s*({.*?});"
                    match = re.search(pattern, html_content, re.DOTALL)

                    if match:
                        try:
                            game_data = json.loads(match.group(1))
                            logger.info(f"Successfully scraped game {game_id}")
                            return game_data
                        except json.JSONDecodeError as e:
                            logger.warning(
                                f"Could not parse JSON for game {game_id}: {e}"
                            )
                            return None
                    else:
                        logger.warning(f"No game data found in HTML for game {game_id}")
                        return None
                else:
                    logger.warning(f"HTTP {response.status} for game {game_id}")
                    return None

        except Exception as e:
            logger.error(f"Error scraping game {game_id}: {e}")
            return None

    async def scrape_games_batch(
        self, game_ids: List[str], max_concurrent: int = 5
    ) -> Dict:
        """Scrape multiple games concurrently"""
        logger.info(
            f"Scraping {len(game_ids)} games with max {max_concurrent} concurrent requests"
        )

        # Create SSL context for ESPN
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:

            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_semaphore(game_id):
                async with semaphore:
                    return await self.scrape_game(session, game_id)

            # Scrape all games concurrently
            tasks = [scrape_with_semaphore(game_id) for game_id in game_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful_games = []
            for i, result in enumerate(results):
                game_id = game_ids[i]
                self.stats["games_attempted"] += 1

                if isinstance(result, Exception):
                    logger.error(f"Exception scraping game {game_id}: {result}")
                    self.stats["games_failed"] += 1
                elif result is not None:
                    successful_games.append((game_id, result))
                    self.stats["games_successful"] += 1
                else:
                    self.stats["games_failed"] += 1

            return successful_games

    def save_game_data(self, game_id: str, game_data: Dict):
        """Save scraped game data to file"""
        try:
            output_file = self.output_dir / f"{game_id}.json"

            with open(output_file, "w") as f:
                json.dump(game_data, f, indent=2)

            logger.info(f"Saved game {game_id} to {output_file}")

        except Exception as e:
            logger.error(f"Error saving game {game_id}: {e}")

    async def scrape_missing_games(self, missing_games_report: str):
        """Scrape all missing games from the report"""
        logger.info(f"Loading missing games report: {missing_games_report}")

        try:
            with open(missing_games_report, "r") as f:
                report = json.load(f)
        except Exception as e:
            logger.error(f"Error loading missing games report: {e}")
            return

        # Collect all missing game IDs
        all_missing_games = []
        for season, data in report.get("seasons", {}).items():
            for game in data.get("missing_game_details", []):
                all_missing_games.append(game["game_id"])

        logger.info(f"Found {len(all_missing_games)} missing games to scrape")

        if not all_missing_games:
            logger.info("No missing games to scrape!")
            return

        # Scrape games in batches
        batch_size = 20
        for i in range(0, len(all_missing_games), batch_size):
            batch = all_missing_games[i : i + batch_size]
            logger.info(
                f"Scraping batch {i//batch_size + 1}/{(len(all_missing_games) + batch_size - 1)//batch_size}"
            )

            successful_games = await self.scrape_games_batch(batch)

            # Save successful games
            for game_id, game_data in successful_games:
                self.save_game_data(game_id, game_data)

            # Rate limiting between batches
            await asyncio.sleep(2)

        # Print final statistics
        self.print_statistics()

    def print_statistics(self):
        """Print scraping statistics"""
        logger.info("=" * 50)
        logger.info("SCRAPING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Games attempted: {self.stats['games_attempted']:,}")
        logger.info(f"Games successful: {self.stats['games_successful']:,}")
        logger.info(f"Games failed: {self.stats['games_failed']:,}")

        if self.stats["games_attempted"] > 0:
            success_rate = (
                self.stats["games_successful"] / self.stats["games_attempted"] * 100
            )
            logger.info(f"Success rate: {success_rate:.1f}%")


async def main():
    parser = argparse.ArgumentParser(description="Scrape missing NBA games from ESPN")
    parser.add_argument("--missing-games", help="Missing games report JSON file")
    parser.add_argument("--game-id", help="Single game ID to scrape")
    parser.add_argument(
        "--output-dir",
        default="data/missing_games_scraped",
        help="Output directory for scraped games",
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=5, help="Maximum concurrent requests"
    )

    args = parser.parse_args()

    # Create scraper
    scraper = ESPNMissingGamesScraper(args.output_dir)

    if args.game_id:
        # Scrape single game
        logger.info(f"Scraping single game: {args.game_id}")

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            game_data = await scraper.scrape_game(session, args.game_id)
            if game_data:
                scraper.save_game_data(args.game_id, game_data)
                logger.info(f"Successfully scraped game {args.game_id}")
            else:
                logger.error(f"Failed to scrape game {args.game_id}")

    elif args.missing_games:
        # Scrape all missing games
        await scraper.scrape_missing_games(args.missing_games)

    else:
        logger.error("Must specify either --missing-games or --game-id")


if __name__ == "__main__":
    asyncio.run(main())


