#!/usr/bin/env python3
"""
ESPN Incremental Scraper - Async Version

Async implementation of ESPN incremental scraper using AsyncBaseScraper framework.
Scrapes last N days of ESPN data and uploads to S3 with proper folder structure.

Features:
- Async HTTP requests with aiohttp
- Built-in rate limiting (token bucket)
- Retry logic with exponential backoff
- Progress tracking and telemetry
- S3 upload management
- DIMS integration via event hooks

Usage:
    python scripts/etl/espn_incremental_async.py --days 3              # Last 3 days
    python scripts/etl/espn_incremental_async.py --days 7 --dry-run    # Test mode

    # ADCE autonomous mode
    from espn_incremental_async import ESPNIncrementalScraperAsync
    scraper = ESPNIncrementalScraperAsync(config_name='espn_incremental_simple')
    await scraper.scrape()

Version: 1.0 (AsyncBaseScraper Integration)
Created: November 6, 2025
Phase: 0.0001 - Active Data Collection
"""

import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba_simulator.etl.base.async_scraper import AsyncScraper, ScraperConfig
from scripts.etl.scraper_config import (
    ScraperConfigManager,
    RateLimitConfig,
    RetryConfig,
    StorageConfig,
    MonitoringConfig,
)

# ESPN API Configuration
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

# S3 folder structure (Phase 0.0001 ESPN-prefixed naming)
S3_PREFIX_PBP = "espn_play_by_play"
S3_PREFIX_BOX = "espn_box_scores"
S3_PREFIX_SCHEDULE = "espn_schedules"
S3_PREFIX_TEAM = "espn_team_stats"


class ESPNIncrementalScraperAsync(AsyncScraper):
    """
    Async ESPN incremental scraper.

    Inherits from AsyncScraper for:
    - Rate limiting
    - Retry logic
    - Progress tracking
    - S3 uploads
    """

    def __init__(
        self,
        config_name: str = "espn_incremental_simple",
        days_back: int = 3,
        save_local: bool = False,
        local_data_dir: Optional[Path] = None,
    ):
        """
        Initialize ESPN scraper.

        Args:
            config_name: Name of config in scraper_config.yaml
            days_back: Number of days to scrape back from today
            save_local: If True, save JSON files locally in addition to S3
            local_data_dir: Directory to save local files (default: /Users/ryanranft/nba-simulator-aws/data/)
        """
        # Load config from YAML
        config_file = (
            Path(__file__).parent.parent.parent / "config" / "scraper_config.yaml"
        )
        config_manager = ScraperConfigManager(str(config_file))
        yaml_config = config_manager.get_scraper_config(config_name)

        # Convert ScraperConfigManager's config to AsyncScraper's ScraperConfig
        # Rate limit conversion: requests_per_second -> seconds between requests
        seconds_between_requests = 1.0 / yaml_config.rate_limit.requests_per_second

        scraper_config = ScraperConfig(
            base_url=yaml_config.base_url,
            rate_limit=seconds_between_requests,  # Convert to seconds between requests
            timeout=yaml_config.timeout,
            retry_attempts=yaml_config.retry.max_attempts,
            max_concurrent=yaml_config.max_concurrent,
            user_agent=yaml_config.user_agent,
            s3_bucket=yaml_config.storage.s3_bucket,
            output_dir=yaml_config.storage.local_output_dir,
            dry_run=yaml_config.dry_run,
        )

        super().__init__(scraper_config)

        self.days_back = days_back
        self.base_url = BASE_URL
        self.save_local = save_local

        # Local data directories
        if local_data_dir is None:
            self.local_data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.local_data_dir = local_data_dir

        # Create subdirectories for each data type
        if self.save_local:
            self.local_box_score_dir = self.local_data_dir / "nba_box_score"
            self.local_pbp_dir = self.local_data_dir / "nba_pbp"
            self.local_team_stats_dir = self.local_data_dir / "nba_team_stats"
            self.local_schedule_dir = self.local_data_dir / "nba_schedule_json"

            # Create directories
            for dir_path in [
                self.local_box_score_dir,
                self.local_pbp_dir,
                self.local_team_stats_dir,
                self.local_schedule_dir,
            ]:
                dir_path.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Local file saving enabled: {self.local_data_dir}")

        # Stats specific to ESPN scraper
        self.games_scraped = 0
        self.schedules_scraped = 0
        self.local_files_saved = 0

        self.logger.info(
            f"ESPN Incremental Scraper initialized (days_back={days_back}, save_local={save_local})"
        )

    def get_date_range(self) -> List[str]:
        """
        Get list of dates to scrape (YYYYMMDD format).

        Returns:
            List of date strings in YYYYMMDD format
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        return dates

    async def fetch_schedule(self, date_str: str) -> Optional[Dict]:
        """
        Fetch schedule for a specific date.

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            Schedule data dict or None if error
        """
        url = f"{self.base_url}/scoreboard"
        params = {"dates": date_str, "limit": 100}

        # Fetch with rate limiting
        await self.rate_limiter.acquire()

        try:
            # Increment request counter
            self.stats.requests_made += 1

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    # Read JSON inside the context manager
                    data = await response.json()
                    self.stats.requests_successful += 1
                    self.stats.data_items_scraped += 1
                    return data
                else:
                    self.logger.error(
                        f"Error fetching schedule for {date_str}: HTTP {response.status}"
                    )
                    self.stats.requests_failed += 1
                    self.stats.errors += 1
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching schedule for {date_str}: {e}")
            self.stats.requests_failed += 1
            self.stats.errors += 1
            return None

    async def fetch_game_data(self, game_id: str) -> Optional[Dict]:
        """
        Fetch complete game data (PBP, box score, team stats).

        Args:
            game_id: ESPN game ID

        Returns:
            Game data dict or None if error
        """
        url = f"{self.base_url}/summary"
        params = {"event": game_id}

        # Fetch with rate limiting
        await self.rate_limiter.acquire()

        try:
            # Increment request counter
            self.stats.requests_made += 1

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    # Read JSON inside the context manager
                    data = await response.json()
                    self.stats.requests_successful += 1
                    self.stats.data_items_scraped += 1
                    return data
                else:
                    self.logger.error(
                        f"Error fetching game {game_id}: HTTP {response.status}"
                    )
                    self.stats.requests_failed += 1
                    self.stats.errors += 1
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching game {game_id}: {e}")
            self.stats.requests_failed += 1
            self.stats.errors += 1
            return None

    async def file_exists_in_s3(self, s3_key: str) -> bool:
        """
        Check if file already exists in S3.

        Args:
            s3_key: S3 key to check (e.g., 'espn_play_by_play/401810037.json')

        Returns:
            True if file exists, False otherwise
        """
        if self.config.dry_run:
            # In dry-run mode, assume files don't exist
            return False

        try:
            # Use head_object to check existence without downloading
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(
                    Bucket=self.config.s3_bucket, Key=s3_key
                ),
            )
            return True
        except Exception as e:
            # File doesn't exist or error occurred (most likely NoSuchKey)
            return False

    async def save_local_file(self, data: Dict, filepath: Path) -> bool:
        """
        Save JSON data to local file.

        Args:
            data: Data dict to save
            filepath: Full path to save file

        Returns:
            True if successful, False otherwise
        """
        if not self.save_local or self.config.dry_run:
            return True  # Skip in dry-run mode

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            self.local_files_saved += 1
            return True
        except Exception as e:
            self.logger.error(f"Error saving local file {filepath}: {e}")
            return False

    async def store_schedule(self, schedule_data: Dict, date_str: str) -> bool:
        """
        Store schedule data to S3 and optionally local file.

        Args:
            schedule_data: Schedule data dict
            date_str: Date in YYYYMMDD format

        Returns:
            True if successful, False otherwise
        """
        filename = f"{date_str}.json"

        # Save to S3
        success = await self.store_data(schedule_data, filename, S3_PREFIX_SCHEDULE)

        # Save to local file if enabled
        if self.save_local:
            local_path = self.local_schedule_dir / filename
            await self.save_local_file(schedule_data, local_path)

        if success:
            self.schedules_scraped += 1
        return success

    async def store_game_data(self, game_data: Dict, game_id: str) -> int:
        """
        Store game data to all three S3 folders (PBP, box scores, team stats) and optionally local files.

        ESPN summary endpoint returns all data, so we upload to all folders.
        Includes duplicate checking to avoid re-uploading existing games.

        Args:
            game_data: Game data dict
            game_id: ESPN game ID

        Returns:
            Number of successful uploads (0-3), or -1 if skipped (duplicate)
        """
        filename = f"{game_id}.json"

        # Check if game already exists in S3 (check play-by-play as representative)
        pbp_key = f"{S3_PREFIX_PBP}/{filename}"
        if await self.file_exists_in_s3(pbp_key):
            self.logger.info(f"    ⏭️  Game {game_id} already exists in S3, skipping")
            return -1  # Indicate skip

        uploads_successful = 0

        # Upload to play-by-play folder
        if await self.store_data(game_data, filename, S3_PREFIX_PBP):
            uploads_successful += 1

        # Upload to box scores folder
        if await self.store_data(game_data, filename, S3_PREFIX_BOX):
            uploads_successful += 1

        # Upload to team stats folder
        if await self.store_data(game_data, filename, S3_PREFIX_TEAM):
            uploads_successful += 1

        # Save to local files if enabled
        if self.save_local:
            await self.save_local_file(game_data, self.local_box_score_dir / filename)
            await self.save_local_file(game_data, self.local_pbp_dir / filename)
            await self.save_local_file(game_data, self.local_team_stats_dir / filename)

        if uploads_successful > 0:
            self.games_scraped += 1

        return uploads_successful

    async def scrape_date(self, date_str: str) -> Dict[str, int]:
        """
        Scrape all games for a specific date.

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            Dict with stats: {'games': N, 'uploads': M}
        """
        self.logger.info(f"Scraping ESPN data for {date_str}...")

        stats = {"games": 0, "uploads": 0}

        # Fetch schedule
        schedule_data = await self.fetch_schedule(date_str)
        if not schedule_data:
            self.logger.warning(f"No schedule data for {date_str}")
            return stats

        # Store schedule
        await self.store_schedule(schedule_data, date_str)

        # Extract games
        events = schedule_data.get("events", [])
        if not events:
            self.logger.info(f"  No games found for {date_str}")
            return stats

        self.logger.info(f"  Found {len(events)} games for {date_str}")

        # Process games concurrently
        game_ids = [event.get("id") for event in events if event.get("id")]

        for game_id in game_ids:
            self.logger.info(f"  Processing game {game_id}...")

            # Fetch game data
            game_data = await self.fetch_game_data(game_id)

            if game_data:
                # Store to all three folders
                uploads = await self.store_game_data(game_data, game_id)

                if uploads == -1:
                    # Game was skipped (already exists)
                    continue
                elif uploads > 0:
                    stats["games"] += 1
                    stats["uploads"] += uploads

                    if uploads == 3:
                        self.logger.info(f"    ✓ Uploaded {game_id} to all folders")
                    else:
                        self.logger.warning(
                            f"    ⚠ Only {uploads}/3 uploads succeeded for {game_id}"
                        )

        return stats

    async def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Remove temp files older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours before deletion (default: 24)

        Returns:
            Number of files deleted
        """
        import time

        if self.config.dry_run:
            self.logger.info("Dry run: Skipping temp file cleanup")
            return 0

        deleted_count = 0
        now = time.time()

        try:
            # Scan output directory for JSON files
            for file_path in self.output_dir.rglob("*.json"):
                try:
                    # Calculate file age in hours
                    age_seconds = now - file_path.stat().st_mtime
                    age_hours = age_seconds / 3600

                    if age_hours > max_age_hours:
                        file_path.unlink()
                        deleted_count += 1
                        self.logger.debug(
                            f"Deleted old temp file: {file_path} (age: {age_hours:.1f}h)"
                        )
                except Exception as e:
                    self.logger.warning(f"Could not delete {file_path}: {e}")

            if deleted_count > 0:
                self.logger.info(
                    f"Cleaned up {deleted_count} temp files older than {max_age_hours} hours"
                )

        except Exception as e:
            self.logger.error(f"Error during temp file cleanup: {e}")

        return deleted_count

    async def scrape(self) -> Dict[str, Any]:
        """
        Main scrape method - scrapes last N days of ESPN data.

        This is the entry point for ADCE autonomous execution.

        Returns:
            Dict with scraping statistics
        """
        self.logger.info(f"\n{'='*70}")
        self.logger.info("ESPN INCREMENTAL SCRAPER (Async)")
        self.logger.info("=" * 70)
        self.logger.info(f"Scraping last {self.days_back} days")
        self.logger.info(f"Dry run: {self.config.dry_run}")
        self.logger.info(f"S3 bucket: {self.config.s3_bucket}")
        self.logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get date range
        dates = self.get_date_range()
        self.logger.info(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")

        # Scrape each date
        total_games = 0
        total_uploads = 0

        for date_str in dates:
            stats = await self.scrape_date(date_str)
            total_games += stats["games"]
            total_uploads += stats["uploads"]

        # Print summary
        self.logger.info(f"\n{'='*70}")
        self.logger.info("SCRAPING SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Games scraped:   {total_games}")
        self.logger.info(f"Files uploaded:  {total_uploads}")
        if self.save_local:
            self.logger.info(f"Local files:     {self.local_files_saved}")
        self.logger.info(f"Schedules:       {self.schedules_scraped}")
        self.logger.info(f"Errors:          {self.stats.errors}")
        self.logger.info(f"Success rate:    {self.stats.success_rate:.1%}")
        self.logger.info("=" * 70)
        self.logger.info(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Cleanup old temp files (24-hour retention)
        self.logger.info("")
        deleted = await self.cleanup_old_temp_files(max_age_hours=24)
        if deleted > 0:
            self.logger.info(f"Cleaned up {deleted} old temp files")

        # Return stats for ADCE
        return {
            "games_scraped": total_games,
            "files_uploaded": total_uploads,
            "schedules_scraped": self.schedules_scraped,
            "errors": self.stats.errors,
            "success_rate": self.stats.success_rate,
            "elapsed_time": self.stats.elapsed_time,
            "requests_made": self.stats.requests_made,
        }


async def main_async(args):
    """Async main function"""
    config_name = "espn_incremental_simple"

    # Determine local data directory
    local_data_dir = None
    if args.local_data_dir:
        local_data_dir = Path(args.local_data_dir)

    scraper = ESPNIncrementalScraperAsync(
        config_name=config_name,
        days_back=args.days,
        save_local=args.save_local,
        local_data_dir=local_data_dir,
    )

    # Set dry_run if specified
    if args.dry_run:
        scraper.config.dry_run = True

    # Use async context manager for automatic cleanup
    async with scraper:
        await scraper.scrape()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ESPN incremental scraper (async version)"
    )
    parser.add_argument(
        "--days", type=int, default=3, help="Number of days to scrape back (default: 3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test mode - don't upload to S3"
    )
    parser.add_argument(
        "--save-local",
        action="store_true",
        help="Save JSON files locally to data/ directories",
    )
    parser.add_argument(
        "--local-data-dir",
        type=str,
        help="Local data directory (default: /Users/ryanranft/nba-simulator-aws/data/)",
    )

    args = parser.parse_args()

    # Run async main
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
