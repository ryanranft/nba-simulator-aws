#!/usr/bin/env python3
"""
ESPN Incremental Scraper - Daily Updates Only

Scrapes only recent ESPN games (last 14 days) and loads to local database.
Designed for nightly automation - NOT for historical backfills.

Strategy:
1. Query ESPN DB for latest game date
2. Scrape from (latest_date - 14 days) to today
3. Load new games to ESPN local database
4. Typically processes 50-100 games during NBA season

Runtime: ~5 minutes during season, <1 minute off-season

Usage:
    python scripts/etl/espn_incremental_scraper.py
    python scripts/etl/espn_incremental_scraper.py --days-back 7
    python scripts/etl/espn_incremental_scraper.py --dry-run

Version: 1.0
Created: October 9, 2025
"""

import sqlite3
import requests
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Database path
ESPN_DB = "/tmp/espn_local.db"

class ESPNIncrementalScraper:
    """Incremental scraper for ESPN NBA data"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

    def __init__(self, db_path=ESPN_DB, days_back=14, dry_run=False):
        self.db_path = db_path
        self.days_back = days_back
        self.dry_run = dry_run

        self.stats = {
            'games_found': 0,
            'games_new': 0,
            'games_updated': 0,
            'games_skipped': 0,
            'errors': 0
        }

    def get_latest_game_date(self):
        """Get the latest game date in ESPN database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(game_date)
            FROM games
            WHERE has_pbp = 1
        """)

        latest_date = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        if latest_date:
            return datetime.strptime(latest_date, "%Y-%m-%d")
        else:
            # If no games, start from 14 days ago
            return datetime.now() - timedelta(days=14)

    def get_schedule(self, date_str):
        """Get schedule for a specific date from ESPN API."""

        url = f"{self.BASE_URL}/scoreboard"
        params = {
            'dates': date_str,
            'limit': 100
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ❌ Error fetching schedule for {date_str}: {e}")
            self.stats['errors'] += 1
            return None

    def get_play_by_play(self, game_id):
        """Get play-by-play for a game from ESPN API."""

        url = f"{self.BASE_URL}/playbyplay"
        params = {'event': game_id}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"    ❌ Error fetching PBP for game {game_id}: {e}")
            self.stats['errors'] += 1
            return None

    def game_exists(self, game_id):
        """Check if game already exists in database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM games WHERE game_id = ?", (game_id,))
        exists = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        return exists

    def load_game_to_db(self, game_data, pbp_data):
        """Load game and play-by-play data to ESPN database."""

        if self.dry_run:
            print(f"    [DRY RUN] Would load game {game_data['game_id']}")
            self.stats['games_new'] += 1
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Extract game info
            game_id = game_data['game_id']
            game_date = game_data['game_date']
            competitions = game_data.get('competitions', [{}])[0]
            competitors = competitions.get('competitors', [])

            # Get home/away teams
            home_team = None
            away_team = None
            home_score = None
            away_score = None

            for comp in competitors:
                team_info = comp.get('team', {})
                team_name = team_info.get('displayName', 'Unknown')
                score = comp.get('score')

                if comp.get('homeAway') == 'home':
                    home_team = team_name
                    home_score = int(score) if score else 0
                else:
                    away_team = team_name
                    away_score = int(score) if score else 0

            # Count PBP events
            pbp_event_count = 0
            if pbp_data:
                plays = pbp_data.get('plays', [])
                pbp_event_count = len(plays)

            # Insert or update game
            cursor.execute("""
                INSERT OR REPLACE INTO games (
                    game_id, game_date, home_team, away_team,
                    home_score, away_score, has_pbp, pbp_event_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                game_id, game_date, home_team, away_team,
                home_score, away_score,
                1 if pbp_event_count > 0 else 0,
                pbp_event_count
            ))

            # Load play-by-play if available
            if pbp_data and pbp_event_count > 0:
                # Clear existing PBP for this game
                cursor.execute("DELETE FROM play_by_play WHERE game_id = ?", (game_id,))

                plays = pbp_data.get('plays', [])
                for play in plays:
                    cursor.execute("""
                        INSERT INTO play_by_play (
                            game_id, sequence_number, period, clock_display,
                            clock_seconds, home_score, away_score,
                            team_id, scoring_play, event_type,
                            description, coordinate_x, coordinate_y,
                            raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        game_id,
                        play.get('sequenceNumber'),
                        play.get('period', {}).get('number'),
                        play.get('clock', {}).get('displayValue'),
                        play.get('clock', {}).get('value'),
                        play.get('homeScore'),
                        play.get('awayScore'),
                        play.get('team', {}).get('id'),
                        play.get('scoringPlay', False),
                        play.get('type', {}).get('text'),
                        play.get('text'),
                        play.get('coordinate', {}).get('x'),
                        play.get('coordinate', {}).get('y'),
                        json.dumps(play)
                    ))

            conn.commit()
            self.stats['games_new'] += 1

        except Exception as e:
            print(f"    ❌ Error loading game {game_data.get('game_id')}: {e}")
            self.stats['errors'] += 1
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def scrape_incremental(self):
        """Scrape recent games (last N days) and load to database."""

        print("=" * 70)
        print("ESPN INCREMENTAL SCRAPER")
        print("=" * 70)
        print()

        # Get latest date from database
        latest_date = self.get_latest_game_date()
        start_date = latest_date - timedelta(days=self.days_back)
        end_date = datetime.now()

        total_days = (end_date - start_date).days + 1

        print(f"Database: {self.db_path}")
        print(f"Latest game in DB: {latest_date.strftime('%Y-%m-%d')}")
        print(f"Scraping range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({total_days} days)")
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made to database")
        print()

        # Scrape each day
        current_date = start_date
        day_count = 0

        while current_date <= end_date:
            day_count += 1
            date_str = current_date.strftime("%Y%m%d")
            date_display = current_date.strftime("%Y-%m-%d")

            print(f"[{day_count}/{total_days}] {date_display}...", end=" ")

            # Get schedule for this date
            schedule_data = self.get_schedule(date_str)
            if not schedule_data:
                print("(error)")
                current_date += timedelta(days=1)
                continue

            # Extract games
            events = schedule_data.get('events', [])
            if not events:
                print("(no games)")
                current_date += timedelta(days=1)
                continue

            print(f"({len(events)} games)")
            self.stats['games_found'] += len(events)

            # Process each game
            for event in events:
                game_id = event.get('id')
                if not game_id:
                    continue

                # Get game name
                competitions = event.get('competitions', [])
                if competitions:
                    home_abbr = competitions[0].get('competitors', [{}])[0].get('team', {}).get('abbreviation', 'UNK')
                    away_abbr = competitions[0].get('competitors', [{}])[1].get('team', {}).get('abbreviation', 'UNK')
                    game_name = f"{away_abbr} @ {home_abbr}"
                else:
                    game_name = f"Game {game_id}"

                # Check if game exists
                if self.game_exists(game_id) and not self.dry_run:
                    print(f"  ⏭️  {game_name} (ID: {game_id}) - already exists, skipping")
                    self.stats['games_skipped'] += 1
                    continue

                print(f"  🏀 {game_name} (ID: {game_id})")

                # Get play-by-play
                pbp_data = self.get_play_by_play(game_id)

                # Prepare game data
                game_data = {
                    'game_id': game_id,
                    'game_date': date_display,
                    'competitions': competitions
                }

                # Load to database
                self.load_game_to_db(game_data, pbp_data)

                # Rate limiting
                time.sleep(0.5)

            # Rate limiting between dates
            time.sleep(1)
            current_date += timedelta(days=1)

        # Print summary
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Games found:    {self.stats['games_found']:,}")
        print(f"Games new:      {self.stats['games_new']:,}")
        print(f"Games skipped:  {self.stats['games_skipped']:,}")
        print(f"Errors:         {self.stats['errors']:,}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="ESPN Incremental Scraper - Daily updates only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape last 14 days (default)
  python scripts/etl/espn_incremental_scraper.py

  # Scrape last 7 days
  python scripts/etl/espn_incremental_scraper.py --days-back 7

  # Dry run (don't modify database)
  python scripts/etl/espn_incremental_scraper.py --dry-run

Purpose:
  Designed for nightly automation. Only fetches recent games, NOT historical seasons.
  For historical backfills, use: scripts/etl/scrape_missing_espn_data.py
        """
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=14,
        help='Number of days to look back (default: 14)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - don\'t modify database'
    )

    parser.add_argument(
        '--db-path',
        default=ESPN_DB,
        help=f'ESPN database path (default: {ESPN_DB})'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper and run
    scraper = ESPNIncrementalScraper(
        db_path=args.db_path,
        days_back=args.days_back,
        dry_run=args.dry_run
    )

    scraper.scrape_incremental()

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
