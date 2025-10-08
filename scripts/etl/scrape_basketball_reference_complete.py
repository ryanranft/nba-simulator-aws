#!/usr/bin/env python3
"""
Basketball Reference Complete Historical Scraper

Scrapes ALL available data from Basketball Reference (1946-2025):
- Schedules
- Player box scores
- Team box scores
- Player season totals
- Player advanced season totals
- Play-by-play
- Standings

Rate Limit: 3 seconds between requests (Basketball Reference courtesy guideline)
"""

import argparse
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys

try:
    from basketball_reference_web_scraper import client
    from basketball_reference_web_scraper.data import OutputType
    HAS_BBREF = True
except ImportError:
    HAS_BBREF = False
    print("basketball_reference_web_scraper not installed")
    print("Install: pip install basketball_reference_web_scraper")
    sys.exit(1)

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("Warning: boto3 not installed, S3 upload will be disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class BasketballReferenceCompleteHistoricalScraper:
    """Scrape complete historical data from Basketball Reference"""

    def __init__(self, output_dir: str, s3_bucket: Optional[str] = None, rate_limit: float = 3.0):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None
        self.rate_limit = rate_limit
        self.last_request_time = 0

        # Statistics
        self.stats = {
            'requests': 0,
            'successes': 0,
            'errors': 0,
            'retries': 0,
        }

    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            logging.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _exponential_backoff(self, attempt: int):
        """Exponential backoff on errors"""
        wait_time = min(60, (2 ** attempt))  # Max 60 seconds
        logging.warning(f"Backing off for {wait_time}s (attempt {attempt})")
        time.sleep(wait_time)

    def _save_json(self, data: Any, filepath: Path):
        """Save data to JSON file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logging.debug(f"Saved: {filepath}")

    def _upload_to_s3(self, local_path: Path, s3_key: str) -> bool:
        """Upload file to S3"""
        if not self.s3_client:
            return False
        try:
            self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
            logging.debug(f"Uploaded to S3: {s3_key}")
            return True
        except Exception as e:
            logging.error(f"S3 upload failed: {e}")
            return False

    def _load_checkpoint(self, checkpoint_file: Path) -> Optional[Dict]:
        """Load checkpoint file"""
        if checkpoint_file and checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logging.info(f"Loaded checkpoint: {checkpoint}")
                return checkpoint
            except Exception as e:
                logging.error(f"Failed to load checkpoint: {e}")
        return None

    def _save_checkpoint(self, checkpoint_file: Path, checkpoint_data: Dict):
        """Save checkpoint file"""
        if checkpoint_file:
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            logging.debug(f"Saved checkpoint: {checkpoint_file}")

    def _make_request_with_retry(self, func, *args, max_retries: int = 3, **kwargs):
        """Make API request with retry logic"""
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                self.stats['requests'] += 1
                result = func(*args, **kwargs)
                self.stats['successes'] += 1
                return result
            except Exception as e:
                self.stats['errors'] += 1
                if attempt < max_retries - 1:
                    self.stats['retries'] += 1
                    logging.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    self._exponential_backoff(attempt)
                else:
                    logging.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
        return None

    def scrape_schedules(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape season schedules for all seasons"""
        logging.info(f"Starting schedule scrape: {season_start}-{season_end}")

        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Scraping schedule for {season-1}-{season} season (end year: {season})")

                # Get schedule data
                schedule = self._make_request_with_retry(
                    client.season_schedule,
                    season_end_year=season
                )

                if schedule:
                    # Save locally
                    local_path = self.output_dir / 'schedules' / str(season) / 'schedule.json'
                    self._save_json(schedule, local_path)

                    # Upload to S3
                    if self.s3_client:
                        s3_key = f'basketball_reference/schedules/{season}/schedule.json'
                        self._upload_to_s3(local_path, s3_key)

                    logging.info(f"✓ Season {season}: {len(schedule)} games")

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'schedules',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to scrape schedule for season {season}: {e}")
                continue

        logging.info(f"Schedule scrape complete. Stats: {self.stats}")

    def scrape_player_box_scores(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape player box scores for all games"""
        logging.info(f"Starting player box scores scrape: {season_start}-{season_end}")

        # First, we need schedules to know which dates to scrape
        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Getting player box scores for {season-1}-{season} season")

                # Get schedule first to know game dates
                schedule = self._make_request_with_retry(
                    client.season_schedule,
                    season_end_year=season
                )

                if not schedule:
                    logging.warning(f"No schedule found for season {season}, skipping")
                    continue

                # Extract unique dates from schedule
                unique_dates = set()
                for game in schedule:
                    if hasattr(game, 'start_time'):
                        unique_dates.add(game.start_time.date())

                logging.info(f"Season {season}: {len(unique_dates)} unique game dates")

                # Scrape each date
                for game_date in sorted(unique_dates):
                    try:
                        day = game_date.day
                        month = game_date.month
                        year = game_date.year

                        logging.info(f"Scraping player box scores for {year}-{month:02d}-{day:02d}")

                        # Get player box scores
                        box_scores = self._make_request_with_retry(
                            client.player_box_scores,
                            day=day,
                            month=month,
                            year=year
                        )

                        if box_scores:
                            # Save locally
                            date_str = f"{year}{month:02d}{day:02d}"
                            local_path = self.output_dir / 'player_box_scores' / str(season) / f'{date_str}_player_box_scores.json'
                            self._save_json(box_scores, local_path)

                            # Upload to S3
                            if self.s3_client:
                                s3_key = f'basketball_reference/player_box_scores/{season}/{date_str}_player_box_scores.json'
                                self._upload_to_s3(local_path, s3_key)

                            logging.info(f"✓ {date_str}: {len(box_scores)} player records")

                    except Exception as e:
                        logging.error(f"Failed to scrape player box scores for {game_date}: {e}")
                        continue

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'player_box_scores',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to process season {season}: {e}")
                continue

        logging.info(f"Player box scores scrape complete. Stats: {self.stats}")

    def scrape_team_box_scores(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape team box scores for all games"""
        logging.info(f"Starting team box scores scrape: {season_start}-{season_end}")

        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Getting team box scores for {season-1}-{season} season")

                # Get schedule first
                schedule = self._make_request_with_retry(
                    client.season_schedule,
                    season_end_year=season
                )

                if not schedule:
                    logging.warning(f"No schedule found for season {season}, skipping")
                    continue

                # Extract unique dates
                unique_dates = set()
                for game in schedule:
                    if hasattr(game, 'start_time'):
                        unique_dates.add(game.start_time.date())

                logging.info(f"Season {season}: {len(unique_dates)} unique game dates")

                # Scrape each date
                for game_date in sorted(unique_dates):
                    try:
                        day = game_date.day
                        month = game_date.month
                        year = game_date.year

                        logging.info(f"Scraping team box scores for {year}-{month:02d}-{day:02d}")

                        # Get team box scores
                        box_scores = self._make_request_with_retry(
                            client.team_box_scores,
                            day=day,
                            month=month,
                            year=year
                        )

                        if box_scores:
                            # Save locally
                            date_str = f"{year}{month:02d}{day:02d}"
                            local_path = self.output_dir / 'team_box_scores' / str(season) / f'{date_str}_team_box_scores.json'
                            self._save_json(box_scores, local_path)

                            # Upload to S3
                            if self.s3_client:
                                s3_key = f'basketball_reference/team_box_scores/{season}/{date_str}_team_box_scores.json'
                                self._upload_to_s3(local_path, s3_key)

                            logging.info(f"✓ {date_str}: {len(box_scores)} team records")

                    except Exception as e:
                        logging.error(f"Failed to scrape team box scores for {game_date}: {e}")
                        continue

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'team_box_scores',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to process season {season}: {e}")
                continue

        logging.info(f"Team box scores scrape complete. Stats: {self.stats}")

    def scrape_season_totals(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape player season totals"""
        logging.info(f"Starting season totals scrape: {season_start}-{season_end}")

        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Scraping season totals for {season-1}-{season} season (end year: {season})")

                # Get season totals
                totals = self._make_request_with_retry(
                    client.players_season_totals,
                    season_end_year=season
                )

                if totals:
                    # Save locally
                    local_path = self.output_dir / 'season_totals' / str(season) / 'player_season_totals.json'
                    self._save_json(totals, local_path)

                    # Upload to S3
                    if self.s3_client:
                        s3_key = f'basketball_reference/season_totals/{season}/player_season_totals.json'
                        self._upload_to_s3(local_path, s3_key)

                    logging.info(f"✓ Season {season}: {len(totals)} player season records")

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'season_totals',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to scrape season totals for season {season}: {e}")
                continue

        logging.info(f"Season totals scrape complete. Stats: {self.stats}")

    def scrape_advanced_totals(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape player advanced season totals"""
        logging.info(f"Starting advanced totals scrape: {season_start}-{season_end}")

        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Scraping advanced totals for {season-1}-{season} season (end year: {season})")

                # Get advanced totals with combined values for traded players
                totals = self._make_request_with_retry(
                    client.players_advanced_season_totals,
                    season_end_year=season,
                    include_combined_values=True
                )

                if totals:
                    # Save locally
                    local_path = self.output_dir / 'advanced_totals' / str(season) / 'player_advanced_totals.json'
                    self._save_json(totals, local_path)

                    # Upload to S3
                    if self.s3_client:
                        s3_key = f'basketball_reference/advanced_totals/{season}/player_advanced_totals.json'
                        self._upload_to_s3(local_path, s3_key)

                    logging.info(f"✓ Season {season}: {len(totals)} player advanced records")

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'advanced_totals',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to scrape advanced totals for season {season}: {e}")
                continue

        logging.info(f"Advanced totals scrape complete. Stats: {self.stats}")

    def scrape_standings(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape standings for all seasons"""
        logging.info(f"Starting standings scrape: {season_start}-{season_end}")

        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Scraping standings for {season-1}-{season} season (end year: {season})")

                # Get standings
                standings = self._make_request_with_retry(
                    client.standings,
                    season_end_year=season
                )

                if standings:
                    # Save locally
                    local_path = self.output_dir / 'standings' / str(season) / 'standings.json'
                    self._save_json(standings, local_path)

                    # Upload to S3
                    if self.s3_client:
                        s3_key = f'basketball_reference/standings/{season}/standings.json'
                        self._upload_to_s3(local_path, s3_key)

                    logging.info(f"✓ Season {season}: {len(standings)} team standings")

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'standings',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to scrape standings for season {season}: {e}")
                continue

        logging.info(f"Standings scrape complete. Stats: {self.stats}")

    def scrape_play_by_play(self, season_start: int, season_end: int, checkpoint_file: Optional[Path] = None):
        """Scrape play-by-play data (modern era only - likely 2000+)"""
        logging.info(f"Starting play-by-play scrape: {season_start}-{season_end}")
        logging.info("Note: Play-by-play data is only available for modern era games")

        checkpoint = self._load_checkpoint(checkpoint_file) if checkpoint_file else None
        start_season = checkpoint.get('current_season', season_start) if checkpoint else season_start

        for season in range(start_season, season_end + 1):
            try:
                logging.info(f"Getting play-by-play for {season-1}-{season} season")

                # Get schedule first
                schedule = self._make_request_with_retry(
                    client.season_schedule,
                    season_end_year=season
                )

                if not schedule:
                    logging.warning(f"No schedule found for season {season}, skipping")
                    continue

                # For play-by-play, we need home team and date
                games_processed = 0
                games_skipped = 0

                for game in schedule:
                    try:
                        if not hasattr(game, 'start_time') or not hasattr(game, 'home_team'):
                            games_skipped += 1
                            continue

                        game_date = game.start_time.date()
                        day = game_date.day
                        month = game_date.month
                        year = game_date.year
                        home_team = game.home_team

                        logging.info(f"Scraping play-by-play for {year}-{month:02d}-{day:02d} ({home_team.name})")

                        # Get play-by-play
                        pbp = self._make_request_with_retry(
                            client.play_by_play,
                            home_team=home_team,
                            day=day,
                            month=month,
                            year=year
                        )

                        if pbp:
                            # Save locally
                            date_str = f"{year}{month:02d}{day:02d}"
                            team_abbr = home_team.name.replace(' ', '_')
                            local_path = self.output_dir / 'play_by_play' / str(season) / f'{date_str}_{team_abbr}_play_by_play.json'
                            self._save_json(pbp, local_path)

                            # Upload to S3
                            if self.s3_client:
                                s3_key = f'basketball_reference/play_by_play/{season}/{date_str}_{team_abbr}_play_by_play.json'
                                self._upload_to_s3(local_path, s3_key)

                            logging.info(f"✓ {date_str} {team_abbr}: {len(pbp)} play-by-play events")
                            games_processed += 1
                        else:
                            games_skipped += 1

                    except Exception as e:
                        # Play-by-play may not be available for older games - this is expected
                        logging.debug(f"Play-by-play not available for game: {e}")
                        games_skipped += 1
                        continue

                logging.info(f"Season {season}: {games_processed} games with play-by-play, {games_skipped} skipped")

                # Update checkpoint
                if checkpoint_file:
                    self._save_checkpoint(checkpoint_file, {
                        'data_type': 'play_by_play',
                        'start_season': season_start,
                        'end_season': season_end,
                        'current_season': season + 1,
                        'games_processed': games_processed,
                        'last_updated': datetime.now().isoformat()
                    })

            except Exception as e:
                logging.error(f"Failed to process season {season}: {e}")
                continue

        logging.info(f"Play-by-play scrape complete. Stats: {self.stats}")


def main():
    parser = argparse.ArgumentParser(
        description='Basketball Reference Complete Historical Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all schedules 1947-2025
  python scrape_basketball_reference_complete.py --data-type schedules --start-season 1947 --end-season 2025

  # Scrape player box scores for one season
  python scrape_basketball_reference_complete.py --data-type player-box-scores --start-season 2024 --end-season 2024

  # Scrape all data types with S3 upload
  python scrape_basketball_reference_complete.py --data-type schedules --start-season 1947 --end-season 2025 --upload-to-s3

Data types:
  - schedules: Season game schedules
  - player-box-scores: Player stats per game
  - team-box-scores: Team stats per game
  - season-totals: Player season aggregates
  - advanced-totals: Player advanced metrics
  - play-by-play: Play-by-play events (modern era only)
  - standings: Final season standings
        """
    )

    parser.add_argument('--data-type', required=True,
                       choices=['schedules', 'player-box-scores', 'team-box-scores',
                               'season-totals', 'advanced-totals', 'play-by-play', 'standings'],
                       help='Type of data to scrape')
    parser.add_argument('--start-season', type=int, required=True,
                       help='Starting season end year (e.g., 1947 for 1946-47 season)')
    parser.add_argument('--end-season', type=int, required=True,
                       help='Ending season end year (e.g., 2025 for 2024-25 season)')
    parser.add_argument('--upload-to-s3', action='store_true',
                       help='Upload scraped data to S3')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake',
                       help='S3 bucket name (default: nba-sim-raw-data-lake)')
    parser.add_argument('--output-dir', default='/tmp/basketball_reference_complete',
                       help='Local output directory (default: /tmp/basketball_reference_complete)')
    parser.add_argument('--checkpoint-file',
                       help='Path to checkpoint file for resume capability')
    parser.add_argument('--rate-limit', type=float, default=3.0,
                       help='Seconds between requests (default: 3.0)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create scraper instance
    scraper = BasketballReferenceCompleteHistoricalScraper(
        output_dir=args.output_dir,
        s3_bucket=args.s3_bucket if args.upload_to_s3 else None,
        rate_limit=args.rate_limit
    )

    # Prepare checkpoint file path
    checkpoint_file = Path(args.checkpoint_file) if args.checkpoint_file else None

    # Execute scraping based on data type
    logging.info(f"Starting Basketball Reference scraper")
    logging.info(f"Data type: {args.data_type}")
    logging.info(f"Seasons: {args.start_season}-{args.end_season}")
    logging.info(f"Rate limit: {args.rate_limit}s")
    logging.info(f"S3 upload: {args.upload_to_s3}")

    start_time = time.time()

    if args.data_type == 'schedules':
        scraper.scrape_schedules(args.start_season, args.end_season, checkpoint_file)
    elif args.data_type == 'player-box-scores':
        scraper.scrape_player_box_scores(args.start_season, args.end_season, checkpoint_file)
    elif args.data_type == 'team-box-scores':
        scraper.scrape_team_box_scores(args.start_season, args.end_season, checkpoint_file)
    elif args.data_type == 'season-totals':
        scraper.scrape_season_totals(args.start_season, args.end_season, checkpoint_file)
    elif args.data_type == 'advanced-totals':
        scraper.scrape_advanced_totals(args.start_season, args.end_season, checkpoint_file)
    elif args.data_type == 'play-by-play':
        scraper.scrape_play_by_play(args.start_season, args.end_season, checkpoint_file)
    elif args.data_type == 'standings':
        scraper.scrape_standings(args.start_season, args.end_season, checkpoint_file)

    elapsed_time = time.time() - start_time

    logging.info(f"Scraping complete!")
    logging.info(f"Total time: {elapsed_time:.1f}s")
    logging.info(f"Final stats: {scraper.stats}")


if __name__ == "__main__":
    main()
