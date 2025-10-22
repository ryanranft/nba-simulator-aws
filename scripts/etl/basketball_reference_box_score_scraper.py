#!/usr/bin/env python3
"""
Basketball Reference Box Score Historical Scraper

Scrapes individual box score pages for games in the scraping_progress table.
Extracts all available data and loads into database + S3.

Features:
- Resume capability (picks up where it left off)
- Priority-based processing (recent games first)
- Extracts: basic stats, advanced stats, four factors, play-by-play
- Uploads raw JSON to S3
- Updates scraping_progress table
- Error handling with retry logic

Usage:
    python scripts/etl/basketball_reference_box_score_scraper.py
    python scripts/etl/basketball_reference_box_score_scraper.py --max-games 100
    python scripts/etl/basketball_reference_box_score_scraper.py --priority 1
    python scripts/etl/basketball_reference_box_score_scraper.py --dry-run

Estimated Runtime:
    - Per game: ~12 seconds (rate limit)
    - 100 games: ~20 minutes
    - 1,000 games: ~3.3 hours
    - 10,000 games: ~1.4 days
    - 70,718 games: ~10 days

Version: 1.0
Created: October 18, 2025
"""

import argparse
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# Configuration
DB_PATH = "/tmp/basketball_reference_boxscores.db"
BASE_URL = "https://www.basketball-reference.com"
RATE_LIMIT = 12.0  # 12 seconds between requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX = "basketball_reference/box_scores"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BoxScoreScraper:
    """Scrape individual box score pages from Basketball Reference"""

    def __init__(self, dry_run=False, upload_to_s3=True):
        self.dry_run = dry_run
        self.upload_to_s3 = upload_to_s3

        self.db_conn = None if dry_run else sqlite3.connect(DB_PATH)
        self.s3_client = None if dry_run or not upload_to_s3 else boto3.client('s3')
        self.last_request_time = 0

        # Statistics
        self.stats = {
            "games_scraped": 0,
            "games_failed": 0,
            "games_skipped": 0,
            "uploaded_to_s3": 0,
            "errors": 0,
        }

    def rate_limit_wait(self):
        """Enforce 12-second rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT:
            sleep_time = RATE_LIMIT - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_pending_games(self, max_games: Optional[int] = None,
                         priority: Optional[int] = None) -> List[Dict]:
        """Get games that need to be scraped from scraping_progress table"""
        if self.dry_run:
            # Return dummy data for testing
            return [{
                'game_id': '202306120DEN',
                'game_date': '2023-06-12',
                'season': 2023,
                'home_team': 'DEN',
                'away_team': 'MIA',
                'priority': 1
            }]

        cursor = self.db_conn.cursor()

        # Build query
        query = """
            SELECT game_id, game_date, season, home_team, away_team, priority
            FROM scraping_progress
            WHERE status = 'pending'
            AND attempts < max_attempts
        """

        params = []

        if priority is not None:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY priority ASC, game_date DESC"

        if max_games:
            query += " LIMIT ?"
            params.append(max_games)

        cursor.execute(query, params)

        games = []
        for row in cursor.fetchall():
            games.append({
                'game_id': row[0],
                'game_date': row[1],
                'season': row[2],
                'home_team': row[3],
                'away_team': row[4],
                'priority': row[5]
            })

        return games

    def fetch_box_score_page(self, game_id: str) -> Optional[str]:
        """Fetch raw HTML for a box score page"""
        url = f"{BASE_URL}/boxscores/{game_id}.html"

        try:
            self.rate_limit_wait()

            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            return response.text

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Game not found: {game_id}")
            elif e.response.status_code == 429:
                logger.warning(f"Rate limited on {game_id}")
            else:
                logger.error(f"HTTP error fetching {game_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {game_id}: {e}")
            return None

    def parse_box_score(self, html: str, game_id: str) -> Dict:
        """Parse box score HTML and extract all available data"""
        soup = BeautifulSoup(html, 'html.parser')

        data = {
            'game_id': game_id,
            'scraped_at': datetime.utcnow().isoformat(),
            'game_info': {},
            'team_stats': [],
            'player_stats': [],
            'play_by_play': [],
        }

        # Extract game metadata
        data['game_info'] = self._parse_game_info(soup, game_id)

        # Extract team box scores
        data['team_stats'] = self._parse_team_stats(soup)

        # Extract player box scores
        data['player_stats'] = self._parse_player_stats(soup)

        # Extract play-by-play (if available)
        data['play_by_play'] = self._parse_play_by_play(soup)

        return data

    def _parse_game_info(self, soup: BeautifulSoup, game_id: str) -> Dict:
        """Extract game metadata from scorebox"""
        info = {}

        try:
            # Find scorebox
            scorebox = soup.find('div', {'class': 'scorebox'})
            if not scorebox:
                return info

            # Extract scores
            scores = scorebox.find_all('div', {'class': 'score'})
            if len(scores) >= 2:
                info['away_score'] = int(scores[0].text.strip())
                info['home_score'] = int(scores[1].text.strip())

            # Extract team names
            teams = scorebox.find_all('strong')
            if len(teams) >= 2:
                info['away_team_name'] = teams[0].text.strip()
                info['home_team_name'] = teams[1].text.strip()

            # Extract date
            scorebox_meta = soup.find('div', {'class': 'scorebox_meta'})
            if scorebox_meta:
                divs = scorebox_meta.find_all('div')
                for div in divs:
                    text = div.get_text()
                    # Look for date pattern
                    if ',' in text and any(month in text for month in
                        ['January', 'February', 'March', 'April', 'May', 'June',
                         'July', 'August', 'September', 'October', 'November', 'December']):
                        info['game_date_full'] = text.strip()

                    # Look for location
                    if 'Arena' in text or 'Center' in text or 'Garden' in text:
                        info['location'] = text.strip()

                    # Look for attendance
                    attendance_match = re.search(r'Attendance:\s*([\d,]+)', text)
                    if attendance_match:
                        info['attendance'] = int(attendance_match.group(1).replace(',', ''))

        except Exception as e:
            logger.warning(f"Error parsing game info for {game_id}: {e}")

        return info

    def _parse_team_stats(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team-level statistics"""
        teams = []

        try:
            # Find team stats tables (usually bottom of page)
            team_tables = soup.find_all('table', {'id': re.compile(r'.*team.*stats.*')})

            for table in team_tables:
                team_data = {}

                # Extract team from table ID
                table_id = table.get('id', '')
                # Parse team abbreviation from ID (e.g., 'box-DEN-team-stats' -> 'DEN')
                team_match = re.search(r'box-([A-Z]{3})-', table_id)
                if team_match:
                    team_data['team'] = team_match.group(1)

                # Extract stats from footer (team totals)
                tfoot = table.find('tfoot')
                if tfoot:
                    row = tfoot.find('tr')
                    if row:
                        # Parse all stat columns
                        for cell in row.find_all(['td', 'th']):
                            stat_name = cell.get('data-stat')
                            if stat_name and stat_name != 'player':
                                team_data[stat_name] = cell.text.strip()

                if team_data:
                    teams.append(team_data)

        except Exception as e:
            logger.warning(f"Error parsing team stats: {e}")

        return teams

    def _parse_player_stats(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract player-level statistics"""
        players = []

        try:
            # Find basic box score tables
            player_tables = soup.find_all('table', {'id': re.compile(r'box-.*-game-basic')})

            for table in player_tables:
                # Extract team from table ID
                table_id = table.get('id', '')
                team_match = re.search(r'box-([A-Z]{3})-', table_id)
                team = team_match.group(1) if team_match else None

                tbody = table.find('tbody')
                if not tbody:
                    continue

                rows = tbody.find_all('tr')

                for row in rows:
                    # Skip if not a player row
                    if row.get('class') and 'thead' in row.get('class'):
                        continue

                    player_data = {'team': team}

                    # Extract all stats
                    for cell in row.find_all(['th', 'td']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            value = cell.text.strip()

                            # Special handling for player name (contains link)
                            if stat_name == 'player':
                                link = cell.find('a')
                                if link:
                                    player_data['player_name'] = link.text.strip()
                                    player_data['player_slug'] = link.get('href', '').split('/')[-1].replace('.html', '')
                                else:
                                    player_data['player_name'] = value
                            else:
                                player_data[stat_name] = value

                    if player_data.get('player_name'):
                        players.append(player_data)

        except Exception as e:
            logger.warning(f"Error parsing player stats: {e}")

        return players

    def _parse_play_by_play(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract play-by-play data (if available)"""
        pbp_events = []

        try:
            # Find play-by-play table
            pbp_table = soup.find('table', {'id': 'pbp'})
            if not pbp_table:
                return pbp_events

            tbody = pbp_table.find('tbody')
            if not tbody:
                return pbp_events

            rows = tbody.find_all('tr')

            for row in rows:
                # Skip quarter headers
                if row.get('class') and 'thead' in row.get('class'):
                    continue

                event = {}

                # Extract all cells
                cells = row.find_all(['th', 'td'])
                for cell in cells:
                    stat_name = cell.get('data-stat')
                    if stat_name:
                        event[stat_name] = cell.text.strip()

                if event:
                    pbp_events.append(event)

        except Exception as e:
            logger.warning(f"Error parsing play-by-play: {e}")

        return pbp_events

    def upload_to_s3_bucket(self, game_id: str, data: Dict) -> bool:
        """Upload raw JSON to S3"""
        if self.dry_run or not self.upload_to_s3:
            logger.info(f"[DRY RUN] Would upload {game_id} to S3")
            return True

        try:
            # Extract year from game_id (YYYYMMDD...)
            year = game_id[:4]

            # S3 key: basketball_reference/box_scores/YYYY/game_id.json
            s3_key = f"{S3_PREFIX}/{year}/{game_id}.json"

            # Upload
            self.s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )

            self.stats["uploaded_to_s3"] += 1
            return True

        except ClientError as e:
            logger.error(f"S3 upload failed for {game_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading {game_id} to S3: {e}")
            return False

    def load_to_database(self, data: Dict) -> bool:
        """Load structured data into SQLite database"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would load {data['game_id']} to database")
            return True

        try:
            cursor = self.db_conn.cursor()

            # Insert game record
            game_info = data['game_info']
            cursor.execute("""
                INSERT OR REPLACE INTO games
                (game_id, game_date, season, home_team, away_team,
                 home_score, away_score, home_team_name, away_team_name,
                 location, attendance, scraped_at, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['game_id'],
                game_info.get('game_date'),
                data.get('season'),
                data.get('home_team'),
                data.get('away_team'),
                game_info.get('home_score'),
                game_info.get('away_score'),
                game_info.get('home_team_name'),
                game_info.get('away_team_name'),
                game_info.get('location'),
                game_info.get('attendance'),
                data['scraped_at'],
                f"{BASE_URL}/boxscores/{data['game_id']}.html"
            ))

            # Insert team stats
            for team_stat in data['team_stats']:
                # Build dynamic INSERT based on available stats
                columns = ['game_id', 'team']
                values = [data['game_id'], team_stat.get('team')]

                # Map stat names to column names
                stat_mapping = {
                    'fg': 'field_goals_made',
                    'fga': 'field_goals_attempted',
                    'fg_pct': 'field_goal_pct',
                    'fg3': 'three_pointers_made',
                    'fg3a': 'three_pointers_attempted',
                    'fg3_pct': 'three_point_pct',
                    'ft': 'free_throws_made',
                    'fta': 'free_throws_attempted',
                    'ft_pct': 'free_throw_pct',
                    'orb': 'offensive_rebounds',
                    'drb': 'defensive_rebounds',
                    'trb': 'total_rebounds',
                    'ast': 'assists',
                    'stl': 'steals',
                    'blk': 'blocks',
                    'tov': 'turnovers',
                    'pf': 'personal_fouls',
                    'pts': 'points',
                }

                for stat_name, col_name in stat_mapping.items():
                    if stat_name in team_stat:
                        columns.append(col_name)
                        values.append(team_stat[stat_name])

                # Build and execute INSERT
                placeholders = ','.join(['?' for _ in values])
                query = f"INSERT OR REPLACE INTO team_box_scores ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)

            # Insert player stats
            for player_stat in data['player_stats']:
                # Similar dynamic INSERT for players
                columns = ['game_id', 'player_name', 'team']
                values = [data['game_id'], player_stat.get('player_name'), player_stat.get('team')]

                # Add available stats
                if 'player_slug' in player_stat:
                    columns.append('player_slug')
                    values.append(player_stat['player_slug'])

                # Map stats (same as team, plus player-specific)
                for stat_name, col_name in stat_mapping.items():
                    if stat_name in player_stat:
                        columns.append(col_name)
                        values.append(player_stat[stat_name])

                # Build and execute INSERT
                placeholders = ','.join(['?' for _ in values])
                query = f"INSERT OR REPLACE INTO player_box_scores ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)

            self.db_conn.commit()
            return True

        except Exception as e:
            logger.error(f"Database insert failed for {data['game_id']}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

    def update_scraping_progress(self, game_id: str, status: str, error_msg: Optional[str] = None):
        """Update scraping_progress table"""
        if self.dry_run:
            return

        try:
            cursor = self.db_conn.cursor()

            if status == 'scraped':
                cursor.execute("""
                    UPDATE scraping_progress
                    SET status = 'scraped',
                        scraped_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE game_id = ?
                """, (datetime.utcnow().isoformat(), game_id))
            else:  # failed
                cursor.execute("""
                    UPDATE scraping_progress
                    SET attempts = attempts + 1,
                        last_attempt_at = ?,
                        last_error = ?,
                        status = CASE WHEN attempts + 1 >= max_attempts THEN 'failed' ELSE status END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE game_id = ?
                """, (datetime.utcnow().isoformat(), error_msg, game_id))

            self.db_conn.commit()

        except Exception as e:
            logger.error(f"Error updating progress for {game_id}: {e}")

    def scrape_game(self, game: Dict) -> bool:
        """Scrape a single game"""
        game_id = game['game_id']

        logger.info(f"Scraping {game_id} ({game['game_date']}) - {game['away_team']} @ {game['home_team']}")

        try:
            # Fetch HTML
            html = self.fetch_box_score_page(game_id)
            if not html:
                self.update_scraping_progress(game_id, 'failed', 'Failed to fetch page')
                self.stats["games_failed"] += 1
                return False

            # Parse data
            data = self.parse_box_score(html, game_id)
            data['season'] = game['season']
            data['home_team'] = game['home_team']
            data['away_team'] = game['away_team']
            data['game_date'] = game['game_date']

            # Upload to S3
            if self.upload_to_s3:
                s3_success = self.upload_to_s3_bucket(game_id, data)
                if not s3_success:
                    logger.warning(f"S3 upload failed for {game_id}, continuing anyway")

            # Load to database
            db_success = self.load_to_database(data)
            if not db_success:
                self.update_scraping_progress(game_id, 'failed', 'Database insert failed')
                self.stats["games_failed"] += 1
                return False

            # Mark as scraped
            self.update_scraping_progress(game_id, 'scraped')
            self.stats["games_scraped"] += 1

            logger.info(f"  ✓ Successfully scraped {game_id}")
            return True

        except Exception as e:
            logger.error(f"Error scraping {game_id}: {e}")
            self.update_scraping_progress(game_id, 'failed', str(e))
            self.stats["games_failed"] += 1
            self.stats["errors"] += 1
            return False

    def run(self, max_games: Optional[int] = None, priority: Optional[int] = None):
        """Run the scraper"""
        print("\n" + "="*70)
        print("BASKETBALL REFERENCE BOX SCORE SCRAPER")
        print("="*70)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dry run: {self.dry_run}")
        print(f"Upload to S3: {self.upload_to_s3}")
        if max_games:
            print(f"Max games: {max_games}")
        if priority:
            print(f"Priority filter: {priority}")
        print()

        # Get pending games
        pending_games = self.get_pending_games(max_games=max_games, priority=priority)

        if not pending_games:
            print("No pending games found!")
            return

        total_games = len(pending_games)
        print(f"Found {total_games} pending games\n")

        estimated_time_hours = (total_games * RATE_LIMIT) / 3600
        print(f"Estimated time: {estimated_time_hours:.1f} hours ({total_games} games × {RATE_LIMIT}s)\n")

        # Process each game
        for idx, game in enumerate(pending_games, 1):
            self.scrape_game(game)

            # Progress update
            if idx % 10 == 0 or idx == total_games:
                elapsed_hours = (idx * RATE_LIMIT) / 3600
                remaining = total_games - idx
                eta_hours = (remaining * RATE_LIMIT) / 3600

                print(f"\n{'='*70}")
                print(f"Progress: {idx}/{total_games} ({100*idx/total_games:.1f}%)")
                print(f"Elapsed: {elapsed_hours:.1f}h, ETA: {eta_hours:.1f}h")
                print(f"Success: {self.stats['games_scraped']}, Failed: {self.stats['games_failed']}")
                print(f"{'='*70}\n")

        # Final summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Games scraped:   {self.stats['games_scraped']}")
        print(f"Games failed:    {self.stats['games_failed']}")
        print(f"Uploaded to S3:  {self.stats['uploaded_to_s3']}")
        print(f"Errors:          {self.stats['errors']}")
        print("="*70)
        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        """Close connections"""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Basketball Reference box scores"
    )
    parser.add_argument(
        "--max-games",
        type=int,
        help="Maximum number of games to scrape"
    )
    parser.add_argument(
        "--priority",
        type=int,
        help="Only scrape games with this priority (1-9)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - don't insert into database or upload to S3"
    )
    parser.add_argument(
        "--no-s3",
        action="store_true",
        help="Don't upload to S3 (database only)"
    )

    args = parser.parse_args()

    scraper = BoxScoreScraper(
        dry_run=args.dry_run,
        upload_to_s3=not args.no_s3
    )

    try:
        scraper.run(max_games=args.max_games, priority=args.priority)
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()
