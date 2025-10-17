#!/usr/bin/env python3
"""
Phase 1C Historical Data Collection Agent
Collects NBA data for 1997-2001 from ESPN and Basketball Reference
Runs as background agent to fill historical gaps
"""

import asyncio
import aiohttp
import ssl
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

try:
    from config.scraper_config import ScraperConfig
except ImportError:
    # Fallback configuration if ScraperConfig is not available
    class ScraperConfig:
        def __init__(self, config_file=None):
            self.espn = type(
                "obj",
                (object,),
                {
                    "base_url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
                    "user_agent": "NBA-Simulator-Scraper/1.0",
                    "timeout": 30,
                    "rate_limit": type(
                        "obj", (object,), {"requests_per_second": 1.0}
                    )(),
                },
            )()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/phase_1c_agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Phase1CHistoricalAgent:
    def __init__(
        self,
        output_dir="/tmp/phase_1c_historical",
        config_file="config/scraper_config.yaml",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = ScraperConfig(config_file=config_file)

        # ESPN configuration
        self.espn_config = self.config.espn
        self.espn_base_url = self.espn_config.base_url
        self.espn_headers = {
            "User-Agent": self.espn_config.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # SSL context for ESPN
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Target seasons
        self.target_seasons = [1997, 1998, 1999, 2000, 2001]

        # Statistics
        self.stats = {
            "seasons_processed": 0,
            "games_collected": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        logger.info("Phase 1C Historical Agent initialized")
        logger.info(f"Target seasons: {self.target_seasons}")
        logger.info(f"Output directory: {self.output_dir}")

    async def _fetch_espn_data(
        self, session: aiohttp.ClientSession, url: str, params: Dict = None
    ) -> Optional[Dict]:
        """Fetch data from ESPN API with error handling"""
        try:
            async with session.get(
                url,
                headers=self.espn_headers,
                params=params,
                ssl=self.ssl_context,
                timeout=self.espn_config.timeout,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"ESPN API returned status {response.status} for {url}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error fetching ESPN data from {url}: {e}")
            self.stats["errors"] += 1
            return None

    async def collect_season_schedule(
        self, session: aiohttp.ClientSession, season: int
    ) -> List[Dict]:
        """Collect schedule for a specific season"""
        logger.info(f"Collecting schedule for season {season}")

        # ESPN season format: 1997-98, 1998-99, etc.
        season_str = f"{season}-{str(season+1)[-2:]}"

        # Try different ESPN endpoints for historical seasons
        endpoints = [
            f"/scoreboard?dates={season}-{season+1}",
            f"/scoreboard?dates={season}",
            f"/scoreboard?dates={season_str}",
        ]

        games = []

        for endpoint in endpoints:
            url = f"{self.espn_base_url}{endpoint}"
            data = await self._fetch_espn_data(session, url)

            if data and "events" in data:
                games.extend(data["events"])
                logger.info(f"Found {len(data['events'])} games via {endpoint}")
                break

        # If no games found via scoreboard, try season schedule endpoint
        if not games:
            schedule_url = f"{self.espn_base_url}/schedule?dates={season}-{season+1}"
            data = await self._fetch_espn_data(session, schedule_url)

            if data and "events" in data:
                games.extend(data["events"])
                logger.info(f"Found {len(data['events'])} games via schedule endpoint")

        return games

    async def collect_game_data(
        self, session: aiohttp.ClientSession, game_id: str, season: int
    ) -> Optional[Dict]:
        """Collect detailed data for a specific game"""
        try:
            # Try play-by-play endpoint
            pbp_url = f"{self.espn_base_url}/events/{game_id}/playbyplay"
            pbp_data = await self._fetch_espn_data(session, pbp_url)

            # Try box score endpoint
            box_url = f"{self.espn_base_url}/events/{game_id}/boxscore"
            box_data = await self._fetch_espn_data(session, box_url)

            # Combine data
            game_data = {
                "game_id": game_id,
                "season": season,
                "playbyplay": pbp_data,
                "boxscore": box_data,
                "collected_at": datetime.now().isoformat(),
            }

            return game_data

        except Exception as e:
            logger.error(f"Error collecting game data for {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    async def process_season(self, session: aiohttp.ClientSession, season: int):
        """Process a complete season"""
        logger.info(f"Processing season {season}")

        # Create season directory
        season_dir = self.output_dir / f"season_{season}"
        season_dir.mkdir(exist_ok=True)

        # Collect schedule
        games = await self.collect_season_schedule(session, season)

        if not games:
            logger.warning(f"No games found for season {season}")
            return

        logger.info(f"Found {len(games)} games for season {season}")

        # Collect detailed data for each game
        successful_games = 0

        for i, game in enumerate(games):
            game_id = game.get("id")
            if not game_id:
                continue

            logger.info(f"Processing game {i+1}/{len(games)}: {game_id}")

            game_data = await self.collect_game_data(session, game_id, season)

            if game_data:
                # Save game data
                game_file = season_dir / f"game_{game_id}.json"
                with open(game_file, "w") as f:
                    json.dump(game_data, f, indent=2)

                successful_games += 1
                self.stats["games_collected"] += 1

            # Rate limiting
            await asyncio.sleep(self.espn_config.rate_limit.requests_per_second)

        logger.info(
            f"Season {season} complete: {successful_games}/{len(games)} games collected"
        )
        self.stats["seasons_processed"] += 1

    async def collect_basketball_reference_data(self, season: int):
        """Collect Basketball Reference data for historical seasons"""
        logger.info(f"Collecting Basketball Reference data for season {season}")

        try:
            # This would use the basketball_reference_web_scraper package
            # For now, we'll create a placeholder
            br_dir = self.output_dir / f"basketball_reference_{season}"
            br_dir.mkdir(exist_ok=True)

            # Placeholder for Basketball Reference collection
            placeholder_data = {
                "season": season,
                "source": "basketball_reference",
                "status": "placeholder",
                "note": "Basketball Reference collection to be implemented",
                "collected_at": datetime.now().isoformat(),
            }

            placeholder_file = br_dir / "placeholder.json"
            with open(placeholder_file, "w") as f:
                json.dump(placeholder_data, f, indent=2)

            logger.info(f"Basketball Reference placeholder created for season {season}")

        except Exception as e:
            logger.error(
                f"Error collecting Basketball Reference data for season {season}: {e}"
            )
            self.stats["errors"] += 1

    def log_progress(self):
        """Log current progress"""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("PHASE 1C HISTORICAL AGENT PROGRESS")
        logger.info("=" * 60)
        logger.info(
            f"Seasons processed: {self.stats['seasons_processed']}/{len(self.target_seasons)}"
        )
        logger.info(f"Games collected: {self.stats['games_collected']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Elapsed time: {elapsed}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution method"""
        logger.info("Starting Phase 1C Historical Agent")
        logger.info(f"Target seasons: {self.target_seasons}")

        async with aiohttp.ClientSession() as session:
            for season in self.target_seasons:
                try:
                    # Process ESPN data
                    await self.process_season(session, season)

                    # Process Basketball Reference data
                    await self.collect_basketball_reference_data(season)

                    # Log progress
                    self.log_progress()

                except Exception as e:
                    logger.error(f"Error processing season {season}: {e}")
                    self.stats["errors"] += 1
                    continue

        # Final summary
        logger.info("Phase 1C Historical Agent completed")
        self.log_progress()


def main():
    """Main entry point"""
    agent = Phase1CHistoricalAgent()

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Phase 1C Historical Agent interrupted by user")
    except Exception as e:
        logger.error(f"Phase 1C Historical Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
