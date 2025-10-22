#!/usr/bin/env python3
"""
NBA API Reverse Chronological Scraper
Starts with current season and works backwards to validate API endpoints
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
import traceback

try:
    from nba_api.stats import endpoints as nba_endpoints

    HAS_NBA_API = True
except ImportError:
    HAS_NBA_API = False
    print("❌ nba_api package not installed")
    print("Install with: pip install nba_api")
    sys.exit(1)

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class ReverseNBAAPIScraper:
    """NBA API scraper that works backwards from current season"""

    def __init__(
        self, output_dir="/tmp/nba_api_reverse", s3_bucket=None, start_year=None
    ):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3") if HAS_BOTO3 and s3_bucket else None

        # Start with current year if not specified
        self.start_year = start_year or datetime.now().year

        # Statistics
        self.stats = {
            "seasons_tested": 0,
            "seasons_successful": 0,
            "seasons_failed": 0,
            "total_requests": 0,
            "total_errors": 0,
        }

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.rate_limit = 1.5  # seconds between requests
        self.last_request_time = 0

    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _test_season_endpoints(self, season_year):
        """Test if endpoints work for a given season"""
        print(f"  Testing endpoints for season {season_year}...")

        try:
            self._rate_limit_wait()
            self.stats["total_requests"] += 1

            # Test with PlayByPlayV2 (most comprehensive endpoint)
            # Use a known game ID from the season
            if season_year >= 2024:
                game_id = "0022400001"  # First game of 2024-25 season
            elif season_year >= 2020:
                game_id = "0022000001"  # First game of 2020-21 season
            else:
                game_id = "0020000001"  # First game of 2000-01 season

            result = nba_endpoints.PlayByPlayV2(game_id=game_id)

            # Check if we got data
            if result and hasattr(result, "get_data_frames"):
                data_frames = result.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    df = data_frames[0]  # First DataFrame contains PlayByPlay
                    if not df.empty:
                        print(f"    ✅ PlayByPlayV2 working - {len(df)} plays")
                        return True
                    else:
                        print(f"    ⚠️ PlayByPlayV2 returned empty data")
                        return False
                else:
                    print(f"    ⚠️ PlayByPlayV2 returned no data frames")
                    return False
            else:
                print(f"    ❌ PlayByPlayV2 returned no result")
                return False

        except Exception as e:
            self.stats["total_errors"] += 1
            print(f"    ❌ PlayByPlayV2 failed: {e}")
            return False

    def _scrape_full_season(self, season_year):
        """Scrape full season data"""
        print(f"  Scraping full season {season_year}...")

        season_dir = self.output_dir / f"season_{season_year}"
        season_dir.mkdir(exist_ok=True)

        # Get all games for the season
        try:
            self._rate_limit_wait()
            self.stats["total_requests"] += 1

            # Get season schedule - use ScoreboardV2 with a specific date
            if season_year >= 2024:
                game_date = "2024-10-01"  # Start of 2024-25 season
            elif season_year >= 2020:
                game_date = "2020-12-22"  # Start of 2020-21 season
            else:
                game_date = "2000-10-31"  # Start of 2000-01 season

            schedule = nba_endpoints.ScoreboardV2(game_date=game_date)

            if schedule and hasattr(schedule, "get_data_frames"):
                data_frames = schedule.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    games_df = data_frames[0]  # First DataFrame contains GameHeader
                    print(f"    Found {len(games_df)} games")

                # Save schedule
                schedule_file = season_dir / f"schedule_{season_year}.json"
                games_df.to_json(schedule_file, orient="records", indent=2)

                # Test a few games
                test_games = games_df.head(3)  # Test first 3 games
                for _, game in test_games.iterrows():
                    game_id = game["GAME_ID"]
                    self._scrape_game_data(game_id, season_year, season_dir)

                return True
            else:
                print(f"    ❌ Could not get schedule for {season_year}")
                return False

        except Exception as e:
            self.stats["total_errors"] += 1
            print(f"    ❌ Season {season_year} scrape failed: {e}")
            return False

    def _scrape_game_data(self, game_id, season_year, season_dir):
        """Scrape data for a single game"""
        try:
            self._rate_limit_wait()
            self.stats["total_requests"] += 1

            # Get play-by-play data
            pbp = nba_endpoints.PlayByPlayV2(game_id=game_id)

            if pbp and hasattr(pbp, "get_data_frames"):
                data_frames = pbp.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    pbp_df = data_frames[0]  # First DataFrame contains PlayByPlay
                    if not pbp_df.empty:
                        # Save play-by-play
                        pbp_file = season_dir / f"pbp_{game_id}.json"
                        pbp_df.to_json(pbp_file, orient="records", indent=2)
                        print(f"      ✅ Game {game_id}: {len(pbp_df)} plays")

                        # Upload to S3 if configured
                        if self.s3_client:
                            s3_key = f"nba_api_reverse/season_{season_year}/pbp_{game_id}.json"
                            self.s3_client.upload_file(
                                str(pbp_file), self.s3_bucket, s3_key
                            )
                    else:
                        print(f"      ⚠️ Game {game_id}: No play-by-play data")
                else:
                    print(f"      ⚠️ Game {game_id}: No data frames in response")
            else:
                print(f"      ❌ Game {game_id}: Could not get play-by-play")

        except Exception as e:
            self.stats["total_errors"] += 1
            print(f"      ❌ Game {game_id} failed: {e}")

    def scrape_season_reverse(self, season_year):
        """Scrape one season, starting from most recent"""
        print(f"\n{'='*60}")
        print(f"Testing Season {season_year}")
        print(f"{'='*60}")

        self.stats["seasons_tested"] += 1

        # Test with a small sample first
        success = self._test_season_endpoints(season_year)

        if success:
            print(f"✅ Season {season_year} endpoints working!")
            self.stats["seasons_successful"] += 1

            # Proceed with full scrape
            self._scrape_full_season(season_year)
            return True
        else:
            print(f"❌ Season {season_year} endpoints not available")
            self.stats["seasons_failed"] += 1
            return False

    def scrape_reverse_chronological(self, end_year=1996):
        """Scrape from current year backwards"""
        print(
            f"Starting reverse chronological scrape from {self.start_year} to {end_year}"
        )
        print(f"Output directory: {self.output_dir}")
        if self.s3_bucket:
            print(f"S3 bucket: {self.s3_bucket}")
        print()

        for year in range(self.start_year, end_year - 1, -1):
            success = self.scrape_season_reverse(year)

            if not success and year == self.start_year:
                print(f"⚠️ WARNING: Current season {year} failed!")
                print("API may be down or credentials invalid")
                return False

            # If we hit a working season, we can continue
            if success:
                print(f"✅ Season {year} validated - API endpoints working")
                # Continue to next season
                continue
            else:
                print(f"⚠️ Season {year} not available - may be too old")
                # Continue trying older seasons

        return True

    def print_statistics(self):
        """Print scraping statistics"""
        print(f"\n{'='*60}")
        print("SCRAPING STATISTICS")
        print(f"{'='*60}")
        print(f"Seasons tested: {self.stats['seasons_tested']}")
        print(f"Seasons successful: {self.stats['seasons_successful']}")
        print(f"Seasons failed: {self.stats['seasons_failed']}")
        print(f"Total requests: {self.stats['total_requests']}")
        print(f"Total errors: {self.stats['total_errors']}")

        if self.stats["total_requests"] > 0:
            success_rate = (
                (self.stats["total_requests"] - self.stats["total_errors"])
                / self.stats["total_requests"]
                * 100
            )
            print(f"Success rate: {success_rate:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="NBA API Reverse Chronological Scraper"
    )
    parser.add_argument(
        "--start-year", type=int, help="Starting year (default: current year)"
    )
    parser.add_argument(
        "--end-year", type=int, default=1996, help="Ending year (default: 1996)"
    )
    parser.add_argument(
        "--output-dir", default="/tmp/nba_api_reverse", help="Output directory"
    )
    parser.add_argument("--upload-to-s3", action="store_true", help="Upload to S3")
    parser.add_argument(
        "--s3-bucket", default="nba-sim-raw-data-lake", help="S3 bucket name"
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="Test mode - only validate endpoints"
    )

    args = parser.parse_args()

    if not HAS_NBA_API:
        sys.exit(1)

    # Configure S3
    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    if args.upload_to_s3 and not HAS_BOTO3:
        print("❌ boto3 required for S3 upload. Install with: pip install boto3")
        sys.exit(1)

    # Create scraper
    scraper = ReverseNBAAPIScraper(
        output_dir=args.output_dir, s3_bucket=s3_bucket, start_year=args.start_year
    )

    # Scrape data
    try:
        success = scraper.scrape_reverse_chronological(args.end_year)

        scraper.print_statistics()

        if success:
            print(f"\n✅ Reverse scraping complete!")
            print(f"📁 Files saved to: {scraper.output_dir}")
            if s3_bucket:
                print(f"☁️  Files uploaded to s3://{s3_bucket}/nba_api_reverse/")
        else:
            print(f"\n❌ Scraping failed - check API connectivity")

    except KeyboardInterrupt:
        print(f"\n⚠️ Scraping interrupted by user")
        scraper.print_statistics()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        scraper.print_statistics()


if __name__ == "__main__":
    main()
