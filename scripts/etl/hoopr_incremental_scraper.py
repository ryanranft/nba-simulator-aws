#!/usr/bin/env python3
"""
hoopR Incremental Scraper - Daily Updates Only

Scrapes only recent hoopR games (last 7 days) and loads to local database.
Designed for nightly automation - NOT for historical backfills.

Strategy:
1. Query hoopR DB for latest game date
2. Use sportsdataverse to fetch recent season games
3. Load only NEW games to hoopR local database
4. Typically processes 50-100 games during NBA season

Runtime: ~5 minutes during season, <1 minute off-season

Usage:
    python scripts/etl/hoopr_incremental_scraper.py
    python scripts/etl/hoopr_incremental_scraper.py --days-back 3
    python scripts/etl/hoopr_incremental_scraper.py --dry-run

Version: 1.0
Created: October 9, 2025
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Import sportsdataverse (hoopR Python wrapper)
try:
    from sportsdataverse.nba import load_nba_pbp, load_nba_schedule
    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse not installed")
    print("Install: pip install sportsdataverse")
    sys.exit(1)

# Database path
HOOPR_DB = "/tmp/hoopr_local.db"

class HoopRIncrementalScraper:
    """Incremental scraper for hoopR NBA data"""

    def __init__(self, db_path=HOOPR_DB, days_back=7, dry_run=False):
        self.db_path = db_path
        self.days_back = days_back
        self.dry_run = dry_run

        self.stats = {
            'games_found': 0,
            'games_new': 0,
            'games_skipped': 0,
            'events_loaded': 0,
            'errors': 0
        }

    def get_latest_game_date(self):
        """Get the latest game date in hoopR database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(game_date)
            FROM schedule
        """)

        latest_date = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        if latest_date:
            return datetime.strptime(latest_date, "%Y-%m-%d")
        else:
            # If no games, start from 7 days ago
            return datetime.now() - timedelta(days=7)

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

        if self.dry_run:
            print(f"[DRY RUN] Would load {len(schedule_df)} schedule records")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for _, row in schedule_df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO schedule (
                        game_id, game_date, season, season_type,
                        home_team_id, home_display_name, home_score,
                        away_team_id, away_display_name, away_score,
                        status, uid, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    str(row.get('game_id')),
                    row.get('game_date'),
                    row.get('season'),
                    row.get('season_type'),
                    row.get('home_team_id'),
                    row.get('home_display_name'),
                    row.get('home_score'),
                    row.get('away_team_id'),
                    row.get('away_display_name'),
                    row.get('away_score'),
                    row.get('status'),
                    row.get('uid')
                ))

            conn.commit()

        except Exception as e:
            print(f"  ❌ Error loading schedule: {e}")
            self.stats['errors'] += 1
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def load_pbp_to_db(self, pbp_df, game_id):
        """Load play-by-play data to hoopR database."""

        if self.dry_run:
            self.stats['events_loaded'] += len(pbp_df)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear existing PBP for this game
            cursor.execute("DELETE FROM play_by_play WHERE game_id = ?", (str(game_id),))

            # Insert new PBP
            for _, row in pbp_df.iterrows():
                cursor.execute("""
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
                """, (
                    row.get('id'),
                    str(row.get('game_id')),
                    row.get('sequence_number'),
                    row.get('type_id'),
                    row.get('type_text'),
                    row.get('period_number'),
                    row.get('clock_display_value'),
                    row.get('clock_value'),
                    row.get('home_score'),
                    row.get('away_score'),
                    row.get('scoring_play'),
                    row.get('score_value'),
                    row.get('team_id'),
                    str(row.get('participants_json')) if row.get('participants_json') else None,
                    row.get('wallclock'),
                    row.get('shooting_play'),
                    row.get('text'),
                    row.get('away_score_before'),
                    row.get('home_score_before'),
                    row.get('coordinate_x'),
                    row.get('coordinate_y'),
                    row.get('season'),
                    row.get('season_type'),
                    row.get('game_date')
                ))

            conn.commit()
            self.stats['events_loaded'] += len(pbp_df)

        except Exception as e:
            print(f"    ❌ Error loading PBP: {e}")
            self.stats['errors'] += 1
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def scrape_incremental(self):
        """Scrape recent games and load to database."""

        print("=" * 70)
        print("HOOPR INCREMENTAL SCRAPER")
        print("=" * 70)
        print()

        # Get latest date from database
        latest_date = self.get_latest_game_date()
        target_date = datetime.now() - timedelta(days=self.days_back)

        # Determine which season(s) to scrape
        current_season = self.get_current_season()

        print(f"Database: {self.db_path}")
        print(f"Latest game in DB: {latest_date.strftime('%Y-%m-%d')}")
        print(f"Target date: {target_date.strftime('%Y-%m-%d')}")
        print(f"Current season: {current_season}")
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made to database")
        print()

        print(f"Loading hoopR schedule for season {current_season}...")

        try:
            # Load schedule for current season
            schedule_df = load_nba_schedule(seasons=[current_season])

            if schedule_df is None or len(schedule_df) == 0:
                print("❌ No schedule data returned from hoopR")
                return

            print(f"✓ Loaded {len(schedule_df):,} games from hoopR schedule")

            # Filter to recent games only
            schedule_df['game_date_parsed'] = schedule_df['game_date'].apply(
                lambda x: datetime.strptime(x, "%Y-%m-%d") if isinstance(x, str) else x
            )

            recent_games = schedule_df[schedule_df['game_date_parsed'] >= target_date]

            print(f"✓ Filtered to {len(recent_games):,} games from last {self.days_back} days")
            print()

            if len(recent_games) == 0:
                print("No new games to scrape")
                return

            # Load schedule to database
            print("Loading schedule to database...")
            self.load_schedule_to_db(recent_games)
            print(f"✓ Schedule loaded")
            print()

            # Process each game for play-by-play
            print("Loading play-by-play data...")

            self.stats['games_found'] = len(recent_games)

            for _, game in recent_games.iterrows():
                game_id = str(game['game_id'])
                game_date = game['game_date']
                matchup = f"{game.get('away_display_name', 'UNK')} @ {game.get('home_display_name', 'UNK')}"

                # Check if we already have PBP for this game
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM play_by_play WHERE game_id = ?", (game_id,))
                pbp_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                if pbp_count > 0 and not self.dry_run:
                    print(f"  ⏭️  {matchup} ({game_date}) - PBP exists ({pbp_count} events), skipping")
                    self.stats['games_skipped'] += 1
                    continue

                print(f"  🏀 {matchup} ({game_date})")

                try:
                    # Load play-by-play for this specific season
                    # Note: hoopR loads entire season PBP, so we filter after
                    pbp_df = load_nba_pbp(seasons=[current_season])

                    if pbp_df is not None and len(pbp_df) > 0:
                        # Filter to this game
                        game_pbp = pbp_df[pbp_df['game_id'] == int(game_id)]

                        if len(game_pbp) > 0:
                            print(f"    ✓ Found {len(game_pbp):,} PBP events")
                            self.load_pbp_to_db(game_pbp, game_id)
                            self.stats['games_new'] += 1
                        else:
                            print(f"    ⚠️  No PBP data available")
                    else:
                        print(f"    ⚠️  PBP load failed")

                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    self.stats['errors'] += 1

            # Print summary
            print()
            print("=" * 70)
            print("SCRAPING SUMMARY")
            print("=" * 70)
            print(f"Games found:    {self.stats['games_found']:,}")
            print(f"Games new:      {self.stats['games_new']:,}")
            print(f"Games skipped:  {self.stats['games_skipped']:,}")
            print(f"Events loaded:  {self.stats['events_loaded']:,}")
            print(f"Errors:         {self.stats['errors']:,}")
            print("=" * 70)

        except Exception as e:
            print(f"❌ Error loading hoopR data: {e}")
            self.stats['errors'] += 1


def main():
    parser = argparse.ArgumentParser(
        description="hoopR Incremental Scraper - Daily updates only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape last 7 days (default)
  python scripts/etl/hoopr_incremental_scraper.py

  # Scrape last 3 days
  python scripts/etl/hoopr_incremental_scraper.py --days-back 3

  # Dry run (don't modify database)
  python scripts/etl/hoopr_incremental_scraper.py --dry-run

Purpose:
  Designed for nightly automation. Only fetches recent games, NOT historical seasons.
  For historical backfills, use: scripts/etl/run_hoopr_comprehensive_overnight.sh
        """
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - don\'t modify database'
    )

    parser.add_argument(
        '--db-path',
        default=HOOPR_DB,
        help=f'hoopR database path (default: {HOOPR_DB})'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper and run
    scraper = HoopRIncrementalScraper(
        db_path=args.db_path,
        days_back=args.days_back,
        dry_run=args.dry_run
    )

    scraper.scrape_incremental()

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
