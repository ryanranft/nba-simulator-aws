#!/usr/bin/env python3
"""
ESPN Missing PBP Scraper - Critical Data Gap Filler

Creates async ESPN scraper specifically for missing play-by-play data:
- Targets 2022-2025 gap (3,230 games)
- Efficient missing game detection
- Progress tracking and resume capability
- Async architecture for speed
- Comprehensive error handling

Addresses the critical PBP data gaps identified in DATA_GAPS_ANALYSIS.md.

Usage:
    python scripts/etl/espn_missing_pbp_scraper.py --seasons 2022-23 2023-24 2024-25
    python scripts/etl/espn_missing_pbp_scraper.py --start-date 2022-10-01 --end-date 2025-04-30
    python scripts/etl/espn_missing_pbp_scraper.py --dry-run

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import aiofiles
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import our new async infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper, ScraperConfig
from scripts.etl.scraper_config import ScraperConfigManager


class ESPNMissingPbpScraper(AsyncBaseScraper):
    """Async ESPN scraper for missing play-by-play data"""

    def __init__(
        self,
        config: ScraperConfig,
        seasons: List[str] = None,
        start_date: str = None,
        end_date: str = None,
    ):
        super().__init__(config)
        self.seasons = seasons or []
        self.start_date = start_date
        self.end_date = end_date

        # ESPN-specific settings
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

        # Data collection settings
        self.data_types = ["schedule", "box_scores", "play_by_play"]

        # Progress tracking
        self.progress_file = self.output_dir / "missing_pbp_progress.json"
        self.completed_games: Set[str] = set()
        self.failed_games: Set[str] = set()
        self._load_progress()

        # Create subdirectories
        for data_type in self.data_types:
            (self.output_dir / data_type).mkdir(parents=True, exist_ok=True)

    def _load_progress(self) -> None:
        """Load progress from file"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, "r") as f:
                    progress_data = json.load(f)
                    self.completed_games = set(progress_data.get("completed_games", []))
                    self.failed_games = set(progress_data.get("failed_games", []))

                self.logger.info(
                    f"Loaded progress: {len(self.completed_games)} completed, {len(self.failed_games)} failed"
                )
        except Exception as e:
            self.logger.error(f"Error loading progress: {e}")
            self.completed_games = set()
            self.failed_games = set()

    async def _save_progress(self) -> None:
        """Save progress to file"""
        try:
            progress_data = {
                "completed_games": list(self.completed_games),
                "failed_games": list(self.failed_games),
                "last_updated": datetime.now().isoformat(),
                "total_completed": len(self.completed_games),
                "total_failed": len(self.failed_games),
            }

            async with aiofiles.open(self.progress_file, "w") as f:
                await f.write(json.dumps(progress_data, indent=2))

            self.logger.debug(f"Progress saved: {len(self.completed_games)} completed")
        except Exception as e:
            self.logger.error(f"Error saving progress: {e}")

    async def scrape(self) -> None:
        """Main scraping method"""
        self.logger.info("Starting ESPN missing PBP scraper")

        if self.seasons:
            await self._scrape_seasons()
        elif self.start_date and self.end_date:
            await self._scrape_date_range()
        else:
            self.logger.error("No seasons or date range specified")
            return

        self.logger.info("ESPN missing PBP scraper completed")

    async def _scrape_seasons(self) -> None:
        """Scrape missing PBP data for specific seasons"""
        for season in self.seasons:
            await self._scrape_season(season)

    async def _scrape_season(self, season: str) -> None:
        """Scrape missing PBP data for a specific season"""
        try:
            self.logger.info(f"Scraping missing PBP data for season {season}")

            # Get date range for season
            start_date, end_date = self._get_season_dates(season)

            # Get all games in season
            all_games = await self._get_season_games(start_date, end_date)

            # Filter to missing games only
            missing_games = [
                game
                for game in all_games
                if game["id"] not in self.completed_games
                and game["id"] not in self.failed_games
            ]

            self.logger.info(
                f"Found {len(missing_games)} missing games for season {season}"
            )

            if not missing_games:
                self.logger.info(f"No missing games for season {season}")
                return

            # Scrape missing games
            await self._scrape_games(missing_games)

        except Exception as e:
            self.logger.error(f"Error scraping season {season}: {e}")

    async def _scrape_date_range(self) -> None:
        """Scrape missing PBP data for date range"""
        try:
            self.logger.info(
                f"Scraping missing PBP data from {self.start_date} to {self.end_date}"
            )

            # Get all games in date range
            all_games = await self._get_date_range_games(self.start_date, self.end_date)

            # Filter to missing games only
            missing_games = [
                game
                for game in all_games
                if game["id"] not in self.completed_games
                and game["id"] not in self.failed_games
            ]

            self.logger.info(f"Found {len(missing_games)} missing games in date range")

            if not missing_games:
                self.logger.info("No missing games in date range")
                return

            # Scrape missing games
            await self._scrape_games(missing_games)

        except Exception as e:
            self.logger.error(f"Error scraping date range: {e}")

    def _get_season_dates(self, season: str) -> tuple:
        """Get start and end dates for a season"""
        year = int(season.split("-")[0])

        # NBA season typically starts in October and ends in April
        start_date = f"{year}-10-01"
        end_date = f"{year + 1}-04-30"

        return start_date, end_date

    async def _get_season_games(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get all games for a season"""
        games = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        while current_date <= end_dt:
            date_str = current_date.strftime("%Y%m%d")
            date_games = await self._get_games_for_date(date_str)
            games.extend(date_games)

            current_date += timedelta(days=1)

        return games

    async def _get_date_range_games(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get all games for a date range"""
        return await self._get_season_games(start_date, end_date)

    async def _get_games_for_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get games for a specific date"""
        try:
            url = f"{self.base_url}/scoreboard"
            params = {"dates": date_str}

            response = await self.fetch_url(url, params)
            if not response:
                return []

            data = await self.parse_json_response(response)
            if not data:
                return []

            # Extract games from ESPN response
            games = []
            events = data.get("events", [])

            for event in events:
                game_data = {
                    "id": event.get("id"),
                    "date": event.get("date"),
                    "home_team": event.get("competitions", [{}])[0]
                    .get("competitors", [{}])[0]
                    .get("team", {})
                    .get("displayName"),
                    "away_team": event.get("competitions", [{}])[0]
                    .get("competitors", [{}])[1]
                    .get("team", {})
                    .get("displayName"),
                    "status": event.get("status", {}).get("type", {}).get("name"),
                }
                games.append(game_data)

            return games

        except Exception as e:
            self.logger.error(f"Error getting games for date {date_str}: {e}")
            return []

    async def _scrape_games(self, games: List[Dict[str, Any]]) -> None:
        """Scrape multiple games"""
        self.logger.info(f"Scraping {len(games)} games")

        success_count = 0
        failure_count = 0

        for i, game in enumerate(games):
            try:
                self.logger.info(
                    f"Scraping game {i+1}/{len(games)}: {game['id']} ({game['away_team']} @ {game['home_team']})"
                )

                success = await self._scrape_single_game(game)

                if success:
                    self.completed_games.add(game["id"])
                    success_count += 1
                else:
                    self.failed_games.add(game["id"])
                    failure_count += 1

                # Save progress every 10 games
                if (i + 1) % 10 == 0:
                    await self._save_progress()
                    self.logger.info(
                        f"Progress: {success_count} success, {failure_count} failed"
                    )

            except Exception as e:
                self.logger.error(f"Error scraping game {game['id']}: {e}")
                self.failed_games.add(game["id"])
                failure_count += 1
                continue

        # Final progress save
        await self._save_progress()

        self.logger.info(
            f"Game scraping completed: {success_count} success, {failure_count} failed"
        )

    async def _scrape_single_game(self, game: Dict[str, Any]) -> bool:
        """Scrape all data for a single game"""
        game_id = game["id"]

        try:
            # Scrape different data types for the game
            tasks = [
                self._scrape_game_schedule(game_id),
                self._scrape_game_boxscore(game_id),
                self._scrape_game_playbyplay(game_id),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check if all tasks succeeded
            success = all(
                not isinstance(result, Exception) and result for result in results
            )

            if success:
                self.logger.debug(f"Successfully scraped all data for game {game_id}")
            else:
                self.logger.warning(f"Some data failed to scrape for game {game_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error scraping game {game_id}: {e}")
            return False

    async def _scrape_game_schedule(self, game_id: str) -> bool:
        """Scrape schedule data for a game"""
        try:
            url = f"{self.base_url}/summary"
            params = {"event": game_id}

            response = await self.fetch_url(url, params)
            if not response:
                return False

            data = await self.parse_json_response(response)
            if not data:
                return False

            filename = f"schedule_{game_id}.json"
            success = await self.store_data(data, filename, "schedule")
            return success

        except Exception as e:
            self.logger.error(f"Error scraping schedule for game {game_id}: {e}")
            return False

    async def _scrape_game_boxscore(self, game_id: str) -> bool:
        """Scrape box score data for a game"""
        try:
            url = f"{self.base_url}/summary"
            params = {"event": game_id}

            response = await self.fetch_url(url, params)
            if not response:
                return False

            data = await self.parse_json_response(response)
            if not data:
                return False

            filename = f"boxscore_{game_id}.json"
            success = await self.store_data(data, filename, "box_scores")
            return success

        except Exception as e:
            self.logger.error(f"Error scraping boxscore for game {game_id}: {e}")
            return False

    async def _scrape_game_playbyplay(self, game_id: str) -> bool:
        """Scrape play-by-play data for a game"""
        try:
            url = f"{self.base_url}/playbyplay"
            params = {"event": game_id}

            response = await self.fetch_url(url, params)
            if not response:
                return False

            data = await self.parse_json_response(response)
            if not data:
                return False

            filename = f"playbyplay_{game_id}.json"
            success = await self.store_data(data, filename, "play_by_play")
            return success

        except Exception as e:
            self.logger.error(f"Error scraping playbyplay for game {game_id}: {e}")
            return False

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary"""
        return {
            "completed_games": len(self.completed_games),
            "failed_games": len(self.failed_games),
            "total_processed": len(self.completed_games) + len(self.failed_games),
            "success_rate": len(self.completed_games)
            / max(1, len(self.completed_games) + len(self.failed_games)),
        }

    async def resume_scraping(self) -> None:
        """Resume scraping from where it left off"""
        self.logger.info("Resuming scraping from previous progress")
        await self.scrape()


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="ESPN Missing PBP Scraper")
    parser.add_argument(
        "--seasons",
        nargs="+",
        help="NBA seasons to scrape (e.g., 2022-23 2023-24 2024-25)",
    )
    parser.add_argument(
        "--start-date", type=str, help="Start date for scraping (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", type=str, help="End date for scraping (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no actual scraping)"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default="config/scraper_config.yaml",
        help="Configuration file path",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from previous progress"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.seasons and not (args.start_date and args.end_date):
        print("❌ Must specify either --seasons or --start-date and --end-date")
        return 1

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config("espn_missing_pbp")
        if not config:
            print("❌ ESPN Missing PBP configuration not found")
            return 1

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        print(f"✅ Loaded ESPN configuration")
        print(f"   Base URL: {config.base_url}")
        print(f"   Rate limit: {config.rate_limit.requests_per_second} req/s")
        print(f"   Max concurrent: {config.max_concurrent}")
        print(f"   Dry run: {config.dry_run}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    # Create scraper
    scraper = ESPNMissingPbpScraper(
        config, seasons=args.seasons, start_date=args.start_date, end_date=args.end_date
    )

    try:
        # Run scraper
        async with scraper:
            if args.resume:
                await scraper.resume_scraping()
            else:
                await scraper.scrape()

        # Print final statistics
        print("\n📊 Final Statistics:")
        print(f"   Requests: {scraper.stats.requests_made}")
        print(f"   Success rate: {scraper.stats.success_rate:.2%}")
        print(f"   Data items: {scraper.stats.data_items_scraped}")
        print(f"   Errors: {scraper.stats.errors}")
        print(f"   Elapsed time: {scraper.stats.elapsed_time:.2f}s")

        # Print progress summary
        progress = scraper.get_progress_summary()
        print(f"\n🎯 Progress Summary:")
        print(f"   Completed games: {progress['completed_games']}")
        print(f"   Failed games: {progress['failed_games']}")
        print(f"   Success rate: {progress['success_rate']:.2%}")

    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        print("💡 Use --resume to continue from where you left off")
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
