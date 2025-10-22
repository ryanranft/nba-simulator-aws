#!/usr/bin/env python3
"""
Phase 1.7 NBA.com Stats Integration Agent
Integrates NBA.com Stats API as primary verification source
Runs as background agent for comprehensive NBA Stats API integration
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

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/phase_1_7_nba_stats_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Phase1NBAStatsIntegrationAgent:
    def __init__(
        self,
        output_dir="/tmp/phase_1_7_nba_stats",
        config_file="config/scraper_config.yaml",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # NBA Stats API configuration
        self.base_url = "https://stats.nba.com/stats"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true",
            "Referer": "https://stats.nba.com/",
        }

        # SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Rate limiting
        self.rate_limit_delay = 0.6  # 600ms between requests (NBA Stats requirement)

        # Statistics
        self.stats = {
            "scoreboards_collected": 0,
            "game_details_collected": 0,
            "player_stats_collected": 0,
            "team_stats_collected": 0,
            "playbyplay_collected": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        # Integration metrics
        self.integration_metrics = {
            "games_by_season": defaultdict(int),
            "players_by_game": defaultdict(int),
            "data_types_collected": defaultdict(int),
            "processing_times": defaultdict(float),
            "error_patterns": defaultdict(int),
        }

        logger.info("Phase 1.7 NBA Stats Integration Agent initialized")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Rate limit: {self.rate_limit_delay}s between requests")

    async def _fetch_nba_stats(
        self, session: aiohttp.ClientSession, endpoint: str, params: Dict = None
    ) -> Optional[Dict]:
        """Fetch data from NBA Stats API with error handling"""
        try:
            url = f"{self.base_url}/{endpoint}"

            async with session.get(
                url,
                headers=self.headers,
                params=params,
                ssl=self.ssl_context,
                timeout=30,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(
                        f"NBA Stats API returned status {response.status} for {endpoint}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error fetching NBA Stats data from {endpoint}: {e}")
            self.stats["errors"] += 1
            return None

    async def collect_scoreboard_data(
        self, session: aiohttp.ClientSession, game_date: str
    ) -> Dict:
        """Collect scoreboard data for a specific date"""
        logger.info(f"Collecting scoreboard data for {game_date}")

        try:
            # Fetch scoreboard
            scoreboard_data = await self._fetch_nba_stats(
                session, "scoreboardV2", {"GameDate": game_date}
            )

            if not scoreboard_data:
                logger.warning(f"No scoreboard data for {game_date}")
                return {}

            # Process scoreboard data
            games = []
            if (
                "resultSets" in scoreboard_data
                and len(scoreboard_data["resultSets"]) > 0
            ):
                game_header = scoreboard_data["resultSets"][0]
                if "rowSet" in game_header:
                    for game_row in game_header["rowSet"]:
                        game_data = {
                            "game_id": game_row[0] if len(game_row) > 0 else "",
                            "game_date": game_date,
                            "home_team_id": game_row[6] if len(game_row) > 6 else "",
                            "away_team_id": game_row[7] if len(game_row) > 7 else "",
                            "home_team_score": game_row[8] if len(game_row) > 8 else "",
                            "away_team_score": game_row[9] if len(game_row) > 9 else "",
                            "game_status": game_row[3] if len(game_row) > 3 else "",
                            "collected_at": datetime.now().isoformat(),
                        }
                        games.append(game_data)

            # Save scoreboard data
            if games:
                scoreboard_file = self.output_dir / f"scoreboard_{game_date}.json"
                with open(scoreboard_file, "w") as f:
                    json.dump(games, f, indent=2)

                logger.info(f"Saved {len(games)} games for {game_date}")
                self.stats["scoreboards_collected"] += len(games)

            return {
                "date": game_date,
                "games_collected": len(games),
                "file_saved": str(scoreboard_file) if games else None,
            }

        except Exception as e:
            logger.error(f"Error collecting scoreboard for {game_date}: {e}")
            self.stats["errors"] += 1
            return {}

    async def collect_game_details(
        self, session: aiohttp.ClientSession, game_id: str
    ) -> Dict:
        """Collect detailed game data for a specific game"""
        logger.info(f"Collecting game details for {game_id}")

        try:
            # Fetch game details
            game_data = await self._fetch_nba_stats(
                session, "boxscoretraditionalv2", {"GameID": game_id}
            )

            if not game_data:
                logger.warning(f"No game details for {game_id}")
                return {}

            # Process game details
            game_details = {
                "game_id": game_id,
                "collected_at": datetime.now().isoformat(),
            }

            # Extract player stats
            if "resultSets" in game_data and len(game_data["resultSets"]) > 0:
                for result_set in game_data["resultSets"]:
                    if result_set.get("name") == "PlayerStats":
                        player_stats = []
                        for player_row in result_set.get("rowSet", []):
                            if len(player_row) > 20:  # Ensure we have enough columns
                                player_data = {
                                    "game_id": game_id,
                                    "player_id": (
                                        player_row[0] if len(player_row) > 0 else ""
                                    ),
                                    "player_name": (
                                        player_row[1] if len(player_row) > 1 else ""
                                    ),
                                    "team_id": (
                                        player_row[3] if len(player_row) > 3 else ""
                                    ),
                                    "minutes": (
                                        player_row[8] if len(player_row) > 8 else ""
                                    ),
                                    "points": (
                                        player_row[26] if len(player_row) > 26 else ""
                                    ),
                                    "rebounds": (
                                        player_row[20] if len(player_row) > 20 else ""
                                    ),
                                    "assists": (
                                        player_row[21] if len(player_row) > 21 else ""
                                    ),
                                    "steals": (
                                        player_row[22] if len(player_row) > 22 else ""
                                    ),
                                    "blocks": (
                                        player_row[23] if len(player_row) > 23 else ""
                                    ),
                                    "turnovers": (
                                        player_row[24] if len(player_row) > 24 else ""
                                    ),
                                    "field_goals_made": (
                                        player_row[9] if len(player_row) > 9 else ""
                                    ),
                                    "field_goals_attempted": (
                                        player_row[10] if len(player_row) > 10 else ""
                                    ),
                                    "three_pointers_made": (
                                        player_row[11] if len(player_row) > 11 else ""
                                    ),
                                    "three_pointers_attempted": (
                                        player_row[12] if len(player_row) > 12 else ""
                                    ),
                                    "free_throws_made": (
                                        player_row[13] if len(player_row) > 13 else ""
                                    ),
                                    "free_throws_attempted": (
                                        player_row[14] if len(player_row) > 14 else ""
                                    ),
                                    "collected_at": datetime.now().isoformat(),
                                }
                                player_stats.append(player_data)

                        game_details["player_stats"] = player_stats
                        self.stats["player_stats_collected"] += len(player_stats)

            # Save game details
            if game_details.get("player_stats"):
                game_file = self.output_dir / f"game_details_{game_id}.json"
                with open(game_file, "w") as f:
                    json.dump(game_details, f, indent=2)

                logger.info(f"Saved game details for {game_id}")
                self.stats["game_details_collected"] += 1

            return {
                "game_id": game_id,
                "player_stats_collected": len(game_details.get("player_stats", [])),
                "file_saved": (
                    str(game_file) if game_details.get("player_stats") else None
                ),
            }

        except Exception as e:
            logger.error(f"Error collecting game details for {game_id}: {e}")
            self.stats["errors"] += 1
            return {}

    async def collect_playbyplay_data(
        self, session: aiohttp.ClientSession, game_id: str
    ) -> Dict:
        """Collect play-by-play data for a specific game"""
        logger.info(f"Collecting play-by-play data for {game_id}")

        try:
            # Fetch play-by-play data
            pbp_data = await self._fetch_nba_stats(
                session, "playbyplayv2", {"GameID": game_id}
            )

            if not pbp_data:
                logger.warning(f"No play-by-play data for {game_id}")
                return {}

            # Process play-by-play data
            plays = []
            if "resultSets" in pbp_data and len(pbp_data["resultSets"]) > 0:
                playbyplay = pbp_data["resultSets"][0]
                if "rowSet" in playbyplay:
                    for play_row in playbyplay["rowSet"]:
                        if len(play_row) > 10:  # Ensure we have enough columns
                            play_data = {
                                "game_id": game_id,
                                "event_num": play_row[0] if len(play_row) > 0 else "",
                                "period": play_row[1] if len(play_row) > 1 else "",
                                "time_remaining": (
                                    play_row[2] if len(play_row) > 2 else ""
                                ),
                                "description": play_row[9] if len(play_row) > 9 else "",
                                "player1_id": play_row[4] if len(play_row) > 4 else "",
                                "player2_id": play_row[5] if len(play_row) > 5 else "",
                                "team_id": play_row[3] if len(play_row) > 3 else "",
                                "collected_at": datetime.now().isoformat(),
                            }
                            plays.append(play_data)

            # Save play-by-play data
            if plays:
                pbp_file = self.output_dir / f"playbyplay_{game_id}.json"
                with open(pbp_file, "w") as f:
                    json.dump(plays, f, indent=2)

                logger.info(f"Saved {len(plays)} plays for {game_id}")
                self.stats["playbyplay_collected"] += len(plays)

            return {
                "game_id": game_id,
                "plays_collected": len(plays),
                "file_saved": str(pbp_file) if plays else None,
            }

        except Exception as e:
            logger.error(f"Error collecting play-by-play for {game_id}: {e}")
            self.stats["errors"] += 1
            return {}

    async def process_recent_games(
        self, session: aiohttp.ClientSession, days_back: int = 7
    ):
        """Process recent games for the last N days"""
        logger.info(f"Processing recent games for the last {days_back} days")

        try:
            current_date = datetime.now()
            total_games_processed = 0

            for i in range(days_back):
                game_date = current_date - timedelta(days=i)
                date_str = game_date.strftime("%Y-%m-%d")

                # Collect scoreboard for this date
                scoreboard_result = await self.collect_scoreboard_data(
                    session, date_str
                )

                if scoreboard_result.get("games_collected", 0) > 0:
                    # Load the scoreboard file to get game IDs
                    scoreboard_file = self.output_dir / f"scoreboard_{date_str}.json"
                    if scoreboard_file.exists():
                        with open(scoreboard_file, "r") as f:
                            games = json.load(f)

                        # Process each game
                        for game in games:
                            game_id = game.get("game_id")
                            if game_id:
                                # Collect game details
                                await self.collect_game_details(session, game_id)
                                await asyncio.sleep(self.rate_limit_delay)

                                # Collect play-by-play
                                await self.collect_playbyplay_data(session, game_id)
                                await asyncio.sleep(self.rate_limit_delay)

                                total_games_processed += 1

                # Rate limiting between dates
                await asyncio.sleep(self.rate_limit_delay)

            logger.info(
                f"Processed {total_games_processed} games over {days_back} days"
            )
            return total_games_processed

        except Exception as e:
            logger.error(f"Error processing recent games: {e}")
            self.stats["errors"] += 1
            return 0

    def generate_integration_report(self) -> Dict:
        """Generate comprehensive integration report"""
        logger.info("Generating integration report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "scoreboards_collected": self.stats["scoreboards_collected"],
                "game_details_collected": self.stats["game_details_collected"],
                "player_stats_collected": self.stats["player_stats_collected"],
                "team_stats_collected": self.stats["team_stats_collected"],
                "playbyplay_collected": self.stats["playbyplay_collected"],
                "total_errors": self.stats["errors"],
                "integration_duration": str(datetime.now() - self.stats["start_time"]),
            },
            "integration_metrics": dict(self.integration_metrics),
            "recommendations": self._generate_recommendations(),
        }

        # Save report
        report_file = self.output_dir / "nba_stats_integration_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Integration report saved to {report_file}")
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on integration results"""
        recommendations = []

        if self.stats["errors"] > 0:
            recommendations.append(f"Address {self.stats['errors']} integration errors")

        if self.stats["scoreboards_collected"] == 0:
            recommendations.append("Investigate scoreboard data collection")

        if self.stats["player_stats_collected"] == 0:
            recommendations.append("Investigate player stats collection")

        if self.stats["playbyplay_collected"] == 0:
            recommendations.append("Investigate play-by-play data collection")

        recommendations.append("Proceed to Phase 1.8 Kaggle Database Integration")
        recommendations.append("Implement Phase 1.11 Multi-Source Deduplication")

        return recommendations

    def log_progress(self):
        """Log current progress"""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("PHASE 1.7 NBA STATS INTEGRATION AGENT PROGRESS")
        logger.info("=" * 60)
        logger.info(f"Scoreboards collected: {self.stats['scoreboards_collected']}")
        logger.info(f"Game details collected: {self.stats['game_details_collected']}")
        logger.info(f"Player stats collected: {self.stats['player_stats_collected']}")
        logger.info(f"Team stats collected: {self.stats['team_stats_collected']}")
        logger.info(f"Play-by-play collected: {self.stats['playbyplay_collected']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Elapsed time: {elapsed}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution method"""
        logger.info("Starting Phase 1.7 NBA Stats Integration Agent")

        try:
            async with aiohttp.ClientSession() as session:
                # Process recent games
                games_processed = await self.process_recent_games(session, days_back=7)

                # Log progress
                self.log_progress()

                # Generate final report
                report = self.generate_integration_report()

                logger.info(
                    "Phase 1.7 NBA Stats Integration Agent completed successfully"
                )
                logger.info(
                    f"Report saved to: {self.output_dir}/nba_stats_integration_report.json"
                )

        except Exception as e:
            logger.error(f"Phase 1.7 NBA Stats Integration Agent failed: {e}")


def main():
    """Main entry point"""
    agent = Phase1NBAStatsIntegrationAgent()

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Phase 1.7 NBA Stats Integration Agent interrupted by user")
    except Exception as e:
        logger.error(f"Phase 1.7 NBA Stats Integration Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





