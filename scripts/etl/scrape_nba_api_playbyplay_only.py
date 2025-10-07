#!/usr/bin/env python3
"""
NBA API Play-by-Play Scraper (Play-by-Play Only)

Focused scraper for ONLY play-by-play data for possession panel generation.
Much faster than comprehensive scraper (3-4 hours vs 750+ hours).

Coverage: 1996-2024 (NBA Stats API availability)
Focus: PlayByPlayV2 endpoint only

Usage:
    # Scrape single season
    python scripts/etl/scrape_nba_api_playbyplay_only.py --season 2024

    # Scrape multiple seasons
    python scripts/etl/scrape_nba_api_playbyplay_only.py --start-season 2020 --end-season 2024

    # Upload to S3
    python scripts/etl/scrape_nba_api_playbyplay_only.py --season 2024 --upload-to-s3
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
import traceback

try:
    from nba_api.stats.endpoints import LeagueGameFinder, PlayByPlayV2
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


class PlayByPlayScraper:
    """Scrape NBA API play-by-play data for possession panel generation"""

    def __init__(self, output_dir="/tmp/nba_api_playbyplay", s3_bucket=None, rate_limit=0.6):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None
        self.rate_limit = rate_limit  # seconds between requests

        # Create output directory
        self.pbp_dir = self.output_dir / 'play_by_play'
        self.pbp_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏱️  Rate limit: {self.rate_limit}s between requests")

    def get_season_games(self, season):
        """
        Get all game IDs for a season

        Args:
            season: int (e.g., 2024 for 2023-24 season)

        Returns:
            list of game IDs
        """
        season_str = f"{season}-{str(season+1)[-2:]}"  # e.g., "2023-24"
        print(f"\n🔍 Finding games for {season_str} season...")

        try:
            time.sleep(self.rate_limit)
            finder = LeagueGameFinder(
                season_nullable=season_str,
                season_type_nullable='Regular Season',
                league_id_nullable='00'
            )

            games_df = finder.get_data_frames()[0]

            # Get unique game IDs
            game_ids = games_df['GAME_ID'].unique().tolist()

            print(f"✅ Found {len(game_ids)} games for {season_str}")
            return game_ids

        except Exception as e:
            print(f"❌ Error finding games for {season_str}: {e}")
            traceback.print_exc()
            return []

    def scrape_play_by_play(self, game_id):
        """
        Scrape play-by-play data for a single game

        Args:
            game_id: str (e.g., "0029600001")

        Returns:
            dict with play-by-play data or None on error
        """
        try:
            time.sleep(self.rate_limit)
            pbp = PlayByPlayV2(game_id=game_id)

            # Get raw JSON response
            pbp_data = pbp.get_dict()

            return pbp_data

        except Exception as e:
            print(f"  ❌ Error scraping {game_id}: {e}")
            return None

    def save_play_by_play(self, game_id, data):
        """Save play-by-play data to JSON file"""
        output_file = self.pbp_dir / f"play_by_play_{game_id}.json"

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        return output_file

    def upload_to_s3(self, local_file, s3_key):
        """Upload file to S3"""
        if not self.s3_client:
            return False

        try:
            self.s3_client.upload_file(
                str(local_file),
                self.s3_bucket,
                s3_key
            )
            return True
        except Exception as e:
            print(f"  ⚠️  S3 upload failed: {e}")
            return False

    def scrape_season(self, season, upload_to_s3=False):
        """
        Scrape all play-by-play data for a season

        Args:
            season: int (e.g., 2024)
            upload_to_s3: bool, upload files to S3

        Returns:
            dict with stats
        """
        print(f"\n{'='*60}")
        print(f"🏀 Scraping Season {season}")
        print(f"{'='*60}")

        # Get all games for season
        game_ids = self.get_season_games(season)

        if not game_ids:
            print(f"⚠️  No games found for season {season}")
            return {
                'season': season,
                'games_found': 0,
                'games_scraped': 0,
                'errors': 0
            }

        # Scrape each game
        stats = {
            'season': season,
            'games_found': len(game_ids),
            'games_scraped': 0,
            'errors': 0,
            'uploaded': 0
        }

        print(f"\n📥 Scraping {len(game_ids)} games...")

        for i, game_id in enumerate(game_ids, 1):
            print(f"  [{i}/{len(game_ids)}] {game_id}...", end=' ')

            # Scrape play-by-play
            pbp_data = self.scrape_play_by_play(game_id)

            if pbp_data:
                # Save locally
                local_file = self.save_play_by_play(game_id, pbp_data)
                stats['games_scraped'] += 1
                print("✅", end='')

                # Upload to S3
                if upload_to_s3 and self.s3_client:
                    s3_key = f"nba_api_playbyplay/season_{season}/play_by_play_{game_id}.json"
                    if self.upload_to_s3(local_file, s3_key):
                        stats['uploaded'] += 1
                        print(" 📤", end='')

                print()
            else:
                stats['errors'] += 1
                print("❌")

            # Progress update every 50 games
            if i % 50 == 0:
                print(f"\n  Progress: {i}/{len(game_ids)} games ({100*i/len(game_ids):.1f}%)")

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Season {season} Complete")
        print(f"{'='*60}")
        print(f"  Games found: {stats['games_found']}")
        print(f"  Games scraped: {stats['games_scraped']}")
        print(f"  Errors: {stats['errors']}")
        if upload_to_s3:
            print(f"  Uploaded to S3: {stats['uploaded']}")
        print()

        return stats


def main():
    parser = argparse.ArgumentParser(description='Scrape NBA API play-by-play data')
    parser.add_argument('--season', type=int, help='Single season to scrape (e.g., 2024)')
    parser.add_argument('--start-season', type=int, help='Start season for range (e.g., 1996)')
    parser.add_argument('--end-season', type=int, help='End season for range (e.g., 2024)')
    parser.add_argument('--output-dir', default='/tmp/nba_api_playbyplay',
                       help='Output directory')
    parser.add_argument('--upload-to-s3', action='store_true',
                       help='Upload files to S3')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake',
                       help='S3 bucket name')
    parser.add_argument('--rate-limit', type=float, default=0.6,
                       help='Seconds between API requests')
    args = parser.parse_args()

    # Determine seasons to scrape
    if args.season:
        seasons = [args.season]
    elif args.start_season and args.end_season:
        seasons = list(range(args.start_season, args.end_season + 1))
    else:
        print("❌ Must specify --season OR --start-season and --end-season")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"NBA API Play-by-Play Scraper")
    print(f"{'='*60}")
    print(f"Seasons to scrape: {seasons}")
    print(f"Total seasons: {len(seasons)}")
    print(f"Output directory: {args.output_dir}")
    if args.upload_to_s3:
        print(f"S3 bucket: {args.s3_bucket}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper
    scraper = PlayByPlayScraper(
        output_dir=args.output_dir,
        s3_bucket=args.s3_bucket if args.upload_to_s3 else None,
        rate_limit=args.rate_limit
    )

    # Scrape each season
    all_stats = []
    for season in seasons:
        stats = scraper.scrape_season(season, upload_to_s3=args.upload_to_s3)
        all_stats.append(stats)

    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 All Seasons Complete")
    print(f"{'='*60}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_games = sum(s['games_found'] for s in all_stats)
    total_scraped = sum(s['games_scraped'] for s in all_stats)
    total_errors = sum(s['errors'] for s in all_stats)

    print(f"📊 Summary:")
    print(f"  Seasons processed: {len(seasons)}")
    print(f"  Total games found: {total_games:,}")
    print(f"  Total games scraped: {total_scraped:,}")
    print(f"  Total errors: {total_errors}")
    print(f"  Success rate: {100*total_scraped/total_games:.1f}%")

    if args.upload_to_s3:
        total_uploaded = sum(s.get('uploaded', 0) for s in all_stats)
        print(f"  Uploaded to S3: {total_uploaded:,}")


if __name__ == '__main__':
    main()
