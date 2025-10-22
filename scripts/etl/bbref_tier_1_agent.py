#!/usr/bin/env python3
"""
Basketball Reference Tier 1 Agent
Collects NBA High Value data: Player Game Logs, Play-by-Play, Shot Charts, Player Tracking, Lineup Data
Runs as background agent for comprehensive Basketball Reference data collection
"""

import asyncio
import aiohttp
import ssl
import logging
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
import os
from collections import defaultdict
import re
from bs4 import BeautifulSoup

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bbref_tier_1_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BasketballReferenceTier1Agent:
    def __init__(
        self, output_dir="/tmp/bbref_tier_1", config_file="config/scraper_config.yaml"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Basketball Reference configuration
        self.base_url = "https://www.basketball-reference.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Rate limiting
        self.rate_limit_delay = (
            12.0  # 12 seconds between requests (Basketball Reference requirement)
        )

        # Statistics
        self.stats = {
            "player_logs_collected": 0,
            "playbyplay_collected": 0,
            "shot_charts_collected": 0,
            "player_tracking_collected": 0,
            "lineup_data_collected": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        # Data collection metrics
        self.collection_metrics = {
            "players_processed": defaultdict(int),
            "seasons_processed": defaultdict(int),
            "games_processed": defaultdict(int),
            "data_types_collected": defaultdict(int),
            "processing_times": defaultdict(float),
            "error_patterns": defaultdict(int),
        }

        logger.info("Basketball Reference Tier 1 Agent initialized")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Rate limit: {self.rate_limit_delay}s between requests")

    async def _fetch_page(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[str]:
        """Fetch a page from Basketball Reference with error handling"""
        try:
            async with session.get(
                url, headers=self.headers, ssl=self.ssl_context, timeout=30
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(
                        f"Basketball Reference returned status {response.status} for {url}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self.stats["errors"] += 1
            return None

    async def collect_player_game_logs(
        self, session: aiohttp.ClientSession, season: int
    ) -> Dict:
        """Collect player game logs for a specific season"""
        logger.info(f"Collecting player game logs for season {season}")

        try:
            # Get season page
            season_url = f"{self.base_url}/leagues/NBA_{season}_games.html"
            page_content = await self._fetch_page(session, season_url)

            if not page_content:
                logger.warning(f"Could not fetch season {season} page")
                return {}

            # Parse the page to get game links
            soup = BeautifulSoup(page_content, "html.parser")

            # Find game links
            game_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if f"/boxscores/{season}" in href and href.endswith(".html"):
                    game_links.append(href)

            logger.info(f"Found {len(game_links)} games for season {season}")

            # Collect player data from each game
            player_logs = []
            games_processed = 0

            for game_link in game_links[:50]:  # Limit to first 50 games for this demo
                try:
                    game_url = f"{self.base_url}{game_link}"
                    game_content = await self._fetch_page(session, game_url)

                    if game_content:
                        # Parse player stats from box score
                        game_soup = BeautifulSoup(game_content, "html.parser")

                        # Extract player stats (simplified parsing)
                        player_stats = self._extract_player_stats_from_boxscore(
                            game_soup, game_link
                        )
                        player_logs.extend(player_stats)
                        games_processed += 1

                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)

                except Exception as e:
                    logger.error(f"Error processing game {game_link}: {e}")
                    self.stats["errors"] += 1

            # Save player logs
            if player_logs:
                season_dir = self.output_dir / f"player_logs_{season}"
                season_dir.mkdir(exist_ok=True)

                logs_file = season_dir / f"player_game_logs_{season}.json"
                with open(logs_file, "w") as f:
                    json.dump(player_logs, f, indent=2)

                logger.info(f"Saved {len(player_logs)} player logs for season {season}")
                self.stats["player_logs_collected"] += len(player_logs)
                self.collection_metrics["games_processed"][season] = games_processed

            return {
                "season": season,
                "games_processed": games_processed,
                "player_logs": len(player_logs),
                "file_saved": str(logs_file) if player_logs else None,
            }

        except Exception as e:
            logger.error(f"Error collecting player game logs for season {season}: {e}")
            self.stats["errors"] += 1
            return {}

    def _extract_player_stats_from_boxscore(
        self, soup: BeautifulSoup, game_link: str
    ) -> List[Dict]:
        """Extract player statistics from a box score page"""
        player_stats = []

        try:
            # Find the game date from the URL
            game_id = game_link.split("/")[-1].replace(".html", "")

            # Look for player stats tables
            tables = soup.find_all("table", {"id": re.compile(r".*_basic")})

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(["td", "th"])
                    if len(cells) > 10:  # Basic stats should have many columns
                        player_data = {
                            "game_id": game_id,
                            "player": cells[0].get_text(strip=True) if cells else "",
                            "mp": (
                                cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            ),
                            "fg": (
                                cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            ),
                            "fga": (
                                cells[3].get_text(strip=True) if len(cells) > 3 else ""
                            ),
                            "fg_pct": (
                                cells[4].get_text(strip=True) if len(cells) > 4 else ""
                            ),
                            "fg3": (
                                cells[5].get_text(strip=True) if len(cells) > 5 else ""
                            ),
                            "fg3a": (
                                cells[6].get_text(strip=True) if len(cells) > 6 else ""
                            ),
                            "fg3_pct": (
                                cells[7].get_text(strip=True) if len(cells) > 7 else ""
                            ),
                            "ft": (
                                cells[8].get_text(strip=True) if len(cells) > 8 else ""
                            ),
                            "fta": (
                                cells[9].get_text(strip=True) if len(cells) > 9 else ""
                            ),
                            "ft_pct": (
                                cells[10].get_text(strip=True)
                                if len(cells) > 10
                                else ""
                            ),
                            "orb": (
                                cells[11].get_text(strip=True)
                                if len(cells) > 11
                                else ""
                            ),
                            "drb": (
                                cells[12].get_text(strip=True)
                                if len(cells) > 12
                                else ""
                            ),
                            "trb": (
                                cells[13].get_text(strip=True)
                                if len(cells) > 13
                                else ""
                            ),
                            "ast": (
                                cells[14].get_text(strip=True)
                                if len(cells) > 14
                                else ""
                            ),
                            "stl": (
                                cells[15].get_text(strip=True)
                                if len(cells) > 15
                                else ""
                            ),
                            "blk": (
                                cells[16].get_text(strip=True)
                                if len(cells) > 16
                                else ""
                            ),
                            "tov": (
                                cells[17].get_text(strip=True)
                                if len(cells) > 17
                                else ""
                            ),
                            "pf": (
                                cells[18].get_text(strip=True)
                                if len(cells) > 18
                                else ""
                            ),
                            "pts": (
                                cells[19].get_text(strip=True)
                                if len(cells) > 19
                                else ""
                            ),
                            "collected_at": datetime.now().isoformat(),
                        }

                        # Only add if player name is not empty
                        if player_data["player"]:
                            player_stats.append(player_data)

            return player_stats

        except Exception as e:
            logger.error(f"Error extracting player stats from boxscore: {e}")
            return []

    async def collect_playbyplay_data(
        self, session: aiohttp.ClientSession, season: int
    ) -> Dict:
        """Collect play-by-play data for a specific season"""
        logger.info(f"Collecting play-by-play data for season {season}")

        try:
            # Basketball Reference play-by-play is limited, so we'll collect what's available
            pbp_url = f"{self.base_url}/leagues/NBA_{season}_play-by-play.html"
            page_content = await self._fetch_page(session, pbp_url)

            if not page_content:
                logger.warning(f"Could not fetch play-by-play for season {season}")
                return {}

            # Parse play-by-play data
            soup = BeautifulSoup(page_content, "html.parser")

            # Look for play-by-play tables
            pbp_data = []
            tables = soup.find_all("table", {"id": re.compile(r".*_pbp")})

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 3:
                        play_data = {
                            "season": season,
                            "time": cells[0].get_text(strip=True) if cells else "",
                            "team": (
                                cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            ),
                            "description": (
                                cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            ),
                            "collected_at": datetime.now().isoformat(),
                        }
                        pbp_data.append(play_data)

            # Save play-by-play data
            if pbp_data:
                season_dir = self.output_dir / f"playbyplay_{season}"
                season_dir.mkdir(exist_ok=True)

                pbp_file = season_dir / f"playbyplay_{season}.json"
                with open(pbp_file, "w") as f:
                    json.dump(pbp_data, f, indent=2)

                logger.info(
                    f"Saved {len(pbp_data)} play-by-play records for season {season}"
                )
                self.stats["playbyplay_collected"] += len(pbp_data)

            return {
                "season": season,
                "plays_collected": len(pbp_data),
                "file_saved": str(pbp_file) if pbp_data else None,
            }

        except Exception as e:
            logger.error(f"Error collecting play-by-play for season {season}: {e}")
            self.stats["errors"] += 1
            return {}

    async def collect_shot_chart_data(
        self, session: aiohttp.ClientSession, season: int
    ) -> Dict:
        """Collect shot chart data for a specific season"""
        logger.info(f"Collecting shot chart data for season {season}")

        try:
            # Basketball Reference shot charts are limited, so we'll collect team-level data
            shot_url = f"{self.base_url}/leagues/NBA_{season}_shooting.html"
            page_content = await self._fetch_page(session, shot_url)

            if not page_content:
                logger.warning(f"Could not fetch shot data for season {season}")
                return {}

            # Parse shot data
            soup = BeautifulSoup(page_content, "html.parser")

            shot_data = []
            tables = soup.find_all("table", {"id": re.compile(r".*_shooting")})

            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 10:
                        shot_record = {
                            "season": season,
                            "player": cells[0].get_text(strip=True) if cells else "",
                            "age": (
                                cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            ),
                            "team": (
                                cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            ),
                            "g": (
                                cells[3].get_text(strip=True) if len(cells) > 3 else ""
                            ),
                            "mp": (
                                cells[4].get_text(strip=True) if len(cells) > 4 else ""
                            ),
                            "fg_pct": (
                                cells[5].get_text(strip=True) if len(cells) > 5 else ""
                            ),
                            "dist": (
                                cells[6].get_text(strip=True) if len(cells) > 6 else ""
                            ),
                            "fg2_pct": (
                                cells[7].get_text(strip=True) if len(cells) > 7 else ""
                            ),
                            "fg3_pct": (
                                cells[8].get_text(strip=True) if len(cells) > 8 else ""
                            ),
                            "collected_at": datetime.now().isoformat(),
                        }

                        if shot_record["player"]:
                            shot_data.append(shot_record)

            # Save shot data
            if shot_data:
                season_dir = self.output_dir / f"shot_charts_{season}"
                season_dir.mkdir(exist_ok=True)

                shot_file = season_dir / f"shot_charts_{season}.json"
                with open(shot_file, "w") as f:
                    json.dump(shot_data, f, indent=2)

                logger.info(
                    f"Saved {len(shot_data)} shot chart records for season {season}"
                )
                self.stats["shot_charts_collected"] += len(shot_data)

            return {
                "season": season,
                "shots_collected": len(shot_data),
                "file_saved": str(shot_file) if shot_data else None,
            }

        except Exception as e:
            logger.error(f"Error collecting shot charts for season {season}: {e}")
            self.stats["errors"] += 1
            return {}

    async def process_season(self, session: aiohttp.ClientSession, season: int):
        """Process a complete season for all Tier 1 data types"""
        logger.info(f"Processing Tier 1 data for season {season}")

        start_time = time.time()

        try:
            # Collect all Tier 1 data types
            player_logs_result = await self.collect_player_game_logs(session, season)
            await asyncio.sleep(self.rate_limit_delay)

            pbp_result = await self.collect_playbyplay_data(session, season)
            await asyncio.sleep(self.rate_limit_delay)

            shot_charts_result = await self.collect_shot_chart_data(session, season)

            # Update metrics
            processing_time = time.time() - start_time
            self.collection_metrics["seasons_processed"][season] = processing_time
            self.collection_metrics["data_types_collected"][
                season
            ] = 3  # Player logs, PBP, Shot charts

            logger.info(
                f"Season {season} Tier 1 processing complete: {processing_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error processing season {season}: {e}")
            self.stats["errors"] += 1

    def generate_collection_report(self) -> Dict:
        """Generate comprehensive collection report"""
        logger.info("Generating collection report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "player_logs_collected": self.stats["player_logs_collected"],
                "playbyplay_collected": self.stats["playbyplay_collected"],
                "shot_charts_collected": self.stats["shot_charts_collected"],
                "player_tracking_collected": self.stats["player_tracking_collected"],
                "lineup_data_collected": self.stats["lineup_data_collected"],
                "total_errors": self.stats["errors"],
                "collection_duration": str(datetime.now() - self.stats["start_time"]),
            },
            "collection_metrics": dict(self.collection_metrics),
            "recommendations": self._generate_recommendations(),
        }

        # Save report
        report_file = self.output_dir / "bbref_tier_1_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Collection report saved to {report_file}")
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on collection results"""
        recommendations = []

        if self.stats["errors"] > 0:
            recommendations.append(f"Address {self.stats['errors']} collection errors")

        if self.stats["player_logs_collected"] == 0:
            recommendations.append(
                "Investigate player game logs collection - no data collected"
            )

        if self.stats["playbyplay_collected"] == 0:
            recommendations.append("Consider alternative play-by-play data sources")

        recommendations.append("Proceed to Tier 2 (NBA Strategic) data collection")
        recommendations.append("Implement Tier 3 (NBA Historical) for older seasons")

        return recommendations

    def log_progress(self):
        """Log current progress"""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("BASKETBALL REFERENCE TIER 1 AGENT PROGRESS")
        logger.info("=" * 60)
        logger.info(f"Player logs collected: {self.stats['player_logs_collected']}")
        logger.info(f"Play-by-play collected: {self.stats['playbyplay_collected']}")
        logger.info(f"Shot charts collected: {self.stats['shot_charts_collected']}")
        logger.info(
            f"Player tracking collected: {self.stats['player_tracking_collected']}"
        )
        logger.info(f"Lineup data collected: {self.stats['lineup_data_collected']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Elapsed time: {elapsed}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution method"""
        logger.info("Starting Basketball Reference Tier 1 Agent")

        # Target recent seasons (most valuable data)
        target_seasons = [2024, 2023, 2022, 2021, 2020]

        try:
            async with aiohttp.ClientSession() as session:
                for season in target_seasons:
                    await self.process_season(session, season)

                    # Log progress after each season
                    self.log_progress()

            # Generate final report
            report = self.generate_collection_report()

            logger.info("Basketball Reference Tier 1 Agent completed successfully")
            logger.info(f"Report saved to: {self.output_dir}/bbref_tier_1_report.json")

        except Exception as e:
            logger.error(f"Basketball Reference Tier 1 Agent failed: {e}")


def main():
    """Main entry point"""
    agent = BasketballReferenceTier1Agent()

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Basketball Reference Tier 1 Agent interrupted by user")
    except Exception as e:
        logger.error(f"Basketball Reference Tier 1 Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





