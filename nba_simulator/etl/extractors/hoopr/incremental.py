#!/usr/bin/env python3
"""
hoopR Incremental Scraper - Daily Updates Only

Migrated to AsyncBaseScraper framework

Scrapes only recent hoopR games (last 7 days) and loads to local database + S3.
Designed for nightly automation - NOT for historical backfills.

Strategy:
1. Query hoopR DB for latest game date
2. Use sportsdataverse to fetch recent season games
3. Load NEW games to hoopR local database + backup to S3
4. Typically processes 50-100 games during NBA season

Runtime: ~5 minutes during season, <1 minute off-season

Usage:
    python scripts/etl/hoopr_incremental_scraper.py
    python scripts/etl/hoopr_incremental_scraper.py --days-back 3
    python scripts/etl/hoopr_incremental_scraper.py --dry-run

Version: 2.0 (Migrated to AsyncBaseScraper)
Created: October 9, 2025
Migrated: October 22, 2025

Features:
- Async framework with synchronous sportsdataverse library
- Automatic rate limiting and retry logic
- S3 backup in addition to SQLite database
- Telemetry and monitoring
"""

import asyncio
import sqlite3
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import pandas as pd

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

# Import sportsdataverse (hoopR Python wrapper)
try:
    from sportsdataverse.nba import load_nba_pbp, load_nba_schedule

    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse not installed")
    print("Install: pip install sportsdataverse")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HoopRIncrementalScraper(AsyncBaseScraper):
    """
    Incremental scraper for hoopR NBA data

    Migrated to AsyncBaseScraper framework for:
    - Automatic rate limiting and retry logic
    - S3 backup storage in addition to SQLite
    - Telemetry and monitoring

    Note: Uses sportsdataverse library (synchronous)
    wrapped in async methods for compatibility with AsyncBaseScraper.
    """

    def __init__(self, config, days_back: int = 7):
        """Initialize incremental scraper with configuration"""
        super().__init__(config)

        # Custom settings from config
        self.db_path = config.custom_settings.get(
            "database_path", "/tmp/hoopr_local.db"
        )
        self.days_back = days_back or config.custom_settings.get("default_days_back", 7)
        self.load_to_database = config.custom_settings.get("load_to_database", True)
        self.backup_to_s3 = config.custom_settings.get("backup_to_s3", True)

        # Statistics tracking
        self.scrape_stats = {
            "games_found": 0,
            "games_new": 0,
            "games_skipped": 0,
            "events_loaded": 0,
            "errors": 0,
        }

        logger.info(f"Initialized {self.__class__.__name__}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Days back: {self.days_back}")
        logger.info(f"Load to database: {self.load_to_database}")
        logger.info(f"Backup to S3: {self.backup_to_s3}")

    def get_latest_game_date(self):
        """Get the latest game date in hoopR database."""

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT MAX(game_date)
                FROM schedule
            """
            )

            latest_date = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            if latest_date:
                return datetime.strptime(latest_date, "%Y-%m-%d")
            else:
                # If no games, start from default days back
                self.logger.info(
                    f"No games in database, using default lookback: {self.days_back} days"
                )
                return datetime.now() - timedelta(days=self.days_back)

        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            # Database or table doesn't exist yet
            self.logger.warning(
                f"Database not initialized (this is expected for first run): {e}"
            )
            self.logger.info(f"Using default lookback: {self.days_back} days")
            return datetime.now() - timedelta(days=self.days_back)

    def get_current_season(self):
        """Get current NBA season year."""

        now = datetime.now()

        # NBA season starts in October
        # If we're in Oct-Dec, it's the current year's season
        # If we're in Jan-Sep, it's the previous year's season
        if now.month >= 10:
            return now.year
        else:
            return now.year - 1

    def game_exists(self, game_id):
        """Check if game already exists in database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM schedule WHERE game_id = ?", (str(game_id),))
        exists = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        return exists

    def load_schedule_to_db(self, schedule_df):
        """Load schedule data to hoopR database."""

        if self.config.dry_run:
            self.logger.info(
                f"[DRY RUN] Would load {len(schedule_df)} schedule records"
            )
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for _, row in schedule_df.iterrows():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO schedule (
                        game_id, game_date, season, season_type,
                        home_team_id, home_display_name, home_score,
                        away_team_id, away_display_name, away_score,
                        status, uid, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                    (
                        str(row.get("game_id")),
                        row.get("game_date"),
                        row.get("season"),
                        row.get("season_type"),
                        row.get("home_team_id"),
                        row.get("home_display_name"),
                        row.get("home_score"),
                        row.get("away_team_id"),
                        row.get("away_display_name"),
                        row.get("away_score"),
                        row.get("status"),
                        row.get("uid"),
                    ),
                )

            conn.commit()

        except Exception as e:
            self.logger.error(f"  ❌ Error loading schedule: {e}")
            self.scrape_stats["errors"] += 1
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def load_pbp_to_db(self, pbp_df, game_id):
        """Load play-by-play data to hoopR database."""

        if self.config.dry_run:
            self.scrape_stats["events_loaded"] += len(pbp_df)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear existing PBP for this game
            cursor.execute(
                "DELETE FROM play_by_play WHERE game_id = ?", (str(game_id),)
            )

            # Insert new PBP
            for _, row in pbp_df.iterrows():
                cursor.execute(
                    """
                    INSERT INTO play_by_play (
                        id, game_id, sequence_number, type_id, type_text,
                        period_number, clock_display_value, clock_value,
                        home_score, away_score, scoring_play,
                        score_value, team_id, participants_json,
                        wallclock, shooting_play, text,
                        away_score_before, home_score_before,
                        coordinate_x, coordinate_y, season, season_type,
                        game_date, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                    (
                        row.get("id"),
                        str(row.get("game_id")),
                        row.get("sequence_number"),
                        row.get("type_id"),
                        row.get("type_text"),
                        row.get("period_number"),
                        row.get("clock_display_value"),
                        row.get("clock_value"),
                        row.get("home_score"),
                        row.get("away_score"),
                        row.get("scoring_play"),
                        row.get("score_value"),
                        row.get("team_id"),
                        (
                            str(row.get("participants_json"))
                            if row.get("participants_json")
                            else None
                        ),
                        row.get("wallclock"),
                        row.get("shooting_play"),
                        row.get("text"),
                        row.get("away_score_before"),
                        row.get("home_score_before"),
                        row.get("coordinate_x"),
                        row.get("coordinate_y"),
                        row.get("season"),
                        row.get("season_type"),
                        row.get("game_date"),
                    ),
                )

            conn.commit()
            self.scrape_stats["events_loaded"] += len(pbp_df)

        except Exception as e:
            self.logger.error(f"    ❌ Error loading PBP: {e}")
            self.scrape_stats["errors"] += 1
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    async def _backup_schedule_to_s3(self, schedule_df, season):
        """Backup schedule data to S3"""
        try:
            filename = f"hoopr_schedule_{season}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            schedule_json = schedule_df.to_json(orient="records")
            success = await self.store_data(
                json.loads(schedule_json), filename, "schedule"
            )
            if success:
                self.logger.info(f"  ✓ Schedule backed up to S3: {filename}")
        except Exception as e:
            self.logger.error(f"  ❌ Error backing up schedule to S3: {e}")

    async def _backup_pbp_to_s3(self, pbp_df, game_id, game_date):
        """Backup play-by-play data to S3"""
        try:
            filename = f"hoopr_pbp_{game_id}_{game_date}.json"
            pbp_json = pbp_df.to_json(orient="records")
            success = await self.store_data(
                json.loads(pbp_json), filename, "play_by_play"
            )
            if success:
                self.logger.debug(f"    ✓ PBP backed up to S3: {filename}")
        except Exception as e:
            self.logger.error(f"    ❌ Error backing up PBP to S3: {e}")

    async def scrape(self):
        """Scrape recent games and load to database + S3 (AsyncBaseScraper abstract method)."""

        self.logger.info("=" * 70)
        self.logger.info("HOOPR INCREMENTAL SCRAPER")
        self.logger.info("=" * 70)

        # Get latest date from database
        latest_date = self.get_latest_game_date()
        target_date = datetime.now() - timedelta(days=self.days_back)

        # Determine which season(s) to scrape
        current_season = self.get_current_season()

        self.logger.info(f"Database: {self.db_path}")
        self.logger.info(f"Latest game in DB: {latest_date.strftime('%Y-%m-%d')}")
        self.logger.info(f"Target date: {target_date.strftime('%Y-%m-%d')}")
        self.logger.info(f"Current season: {current_season}")
        if self.config.dry_run:
            self.logger.warning("⚠️  DRY RUN MODE - No changes will be made to database")

        self.logger.info(f"Loading hoopR schedule for season {current_season}...")

        try:
            # Load schedule for current season (wrap sync library call in async)
            schedule_df = await asyncio.to_thread(
                load_nba_schedule, seasons=[current_season]
            )

            if schedule_df is None or len(schedule_df) == 0:
                self.logger.error("❌ No schedule data returned from hoopR")
                return

            # Convert to pandas if it's a Polars DataFrame
            if hasattr(schedule_df, "to_pandas"):
                schedule_df = schedule_df.to_pandas()

            self.logger.info(f"✓ Loaded {len(schedule_df):,} games from hoopR schedule")

            # Filter to recent games only
            schedule_df["game_date_parsed"] = schedule_df["game_date"].apply(
                lambda x: datetime.strptime(x, "%Y-%m-%d") if isinstance(x, str) else x
            )

            recent_games = schedule_df[schedule_df["game_date_parsed"] >= target_date]

            self.logger.info(
                f"✓ Filtered to {len(recent_games):,} games from last {self.days_back} days"
            )

            if len(recent_games) == 0:
                self.logger.info("No new games to scrape")
                return

            # Load schedule to database
            self.logger.info("Loading schedule to database...")
            self.load_schedule_to_db(recent_games)
            self.logger.info(f"✓ Schedule loaded")

            # Backup schedule to S3 if enabled
            if self.backup_to_s3:
                await self._backup_schedule_to_s3(recent_games, current_season)

            # Process each game for play-by-play
            self.logger.info("Loading play-by-play data...")

            self.scrape_stats["games_found"] = len(recent_games)

            for _, game in recent_games.iterrows():
                game_id = str(game["game_id"])
                game_date = game["game_date"]
                matchup = f"{game.get('away_display_name', 'UNK')} @ {game.get('home_display_name', 'UNK')}"

                # Check if we already have PBP for this game
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM play_by_play WHERE game_id = ?", (game_id,)
                )
                pbp_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                if pbp_count > 0 and not self.config.dry_run:
                    self.logger.info(
                        f"  ⏭️  {matchup} ({game_date}) - PBP exists ({pbp_count} events), skipping"
                    )
                    self.scrape_stats["games_skipped"] += 1
                    continue

                self.logger.info(f"  🏀 {matchup} ({game_date})")

                try:
                    # Load play-by-play for this specific season (wrap sync library call in async)
                    # Note: hoopR loads entire season PBP, so we filter after
                    pbp_df = await asyncio.to_thread(
                        load_nba_pbp, seasons=[current_season]
                    )

                    if pbp_df is not None and len(pbp_df) > 0:
                        # Convert to pandas if it's a Polars DataFrame
                        if hasattr(pbp_df, "to_pandas"):
                            pbp_df = pbp_df.to_pandas()

                        # Filter to this game
                        game_pbp = pbp_df[pbp_df["game_id"] == int(game_id)]

                        if len(game_pbp) > 0:
                            self.logger.info(
                                f"    ✓ Found {len(game_pbp):,} PBP events"
                            )
                            self.load_pbp_to_db(game_pbp, game_id)

                            # Backup PBP to S3 if enabled
                            if self.backup_to_s3:
                                await self._backup_pbp_to_s3(
                                    game_pbp, game_id, game_date
                                )

                            self.scrape_stats["games_new"] += 1
                        else:
                            self.logger.warning(f"    ⚠️  No PBP data available")
                    else:
                        self.logger.warning(f"    ⚠️  PBP load failed")

                except Exception as e:
                    self.logger.error(f"    ❌ Error: {e}")
                    self.scrape_stats["errors"] += 1

            # Print summary
            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info("SCRAPING SUMMARY")
            self.logger.info("=" * 70)
            self.logger.info(f"Games found:    {self.scrape_stats['games_found']:,}")
            self.logger.info(f"Games new:      {self.scrape_stats['games_new']:,}")
            self.logger.info(f"Games skipped:  {self.scrape_stats['games_skipped']:,}")
            self.logger.info(f"Events loaded:  {self.scrape_stats['events_loaded']:,}")
            self.logger.info(f"Errors:         {self.scrape_stats['errors']:,}")
            self.logger.info("=" * 70)

        except Exception as e:
            self.logger.error(f"❌ Error loading hoopR data: {e}")
            self.scrape_stats["errors"] += 1


async def main():
    parser = argparse.ArgumentParser(
        description="hoopR Incremental Scraper - Daily updates only (Migrated to AsyncBaseScraper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape last 7 days (default)
  python scripts/etl/hoopr_incremental_scraper.py

  # Scrape last 3 days
  python scripts/etl/hoopr_incremental_scraper.py --days-back 3

  # Dry run (don't modify database or S3)
  python scripts/etl/hoopr_incremental_scraper.py --dry-run

Purpose:
  Designed for nightly automation. Only fetches recent games, NOT historical seasons.
  Loads to SQLite database + backs up to S3 for redundancy.
  For historical backfills, use: scripts/etl/run_hoopr_comprehensive_overnight.sh
        """,
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=None,
        help="Number of days to look back (default: from config, usually 7)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't modify database or S3",
    )

    parser.add_argument(
        "--config-file",
        type=str,
        default="config/scraper_config.yaml",
        help="Configuration file path",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config("hoopr_incremental")
        if not config:
            print("❌ hoopR Incremental configuration not found")
            return 1

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        logger.info(f"✅ Loaded hoopR Incremental configuration")
        logger.info(f"   Database: {config.custom_settings.get('database_path')}")
        logger.info(
            f"   Days back: {args.days_back or config.custom_settings.get('default_days_back')}"
        )
        logger.info(f"   S3 bucket: {config.storage.s3_bucket}")
        logger.info(f"   Dry run: {config.dry_run}")
        logger.info("")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create scraper and run
    scraper = HoopRIncrementalScraper(config, days_back=args.days_back)

    try:
        # Run scraper with context manager
        async with scraper:
            await scraper.scrape()

        # Print final statistics
        logger.info("")
        logger.info("📊 Final Statistics:")
        logger.info(f"   Requests: {scraper.stats.requests_made}")
        logger.info(f"   Success rate: {scraper.stats.success_rate:.2%}")
        logger.info(f"   Elapsed time: {scraper.stats.elapsed_time:.2f}s")

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        return 1

    logger.info("")
    logger.info(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
