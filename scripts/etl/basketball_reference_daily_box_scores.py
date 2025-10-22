#!/usr/bin/env python3
"""
Basketball Reference Daily Box Score Scraper

Scrapes box scores for games from yesterday (or specified date).
Designed for nightly automation to keep box score database current.

How it works:
1. Get yesterday's date (or user-specified date)
2. Query ESPN/NBA API for games on that date
3. Convert to Basketball Reference game IDs
4. Insert into scraping_progress table (if not already there)
5. Run box score scraper on just those games

Usage:
    # Scrape yesterday's games
    python scripts/etl/basketball_reference_daily_box_scores.py

    # Scrape specific date
    python scripts/etl/basketball_reference_daily_box_scores.py --date 2023-06-12

    # Scrape last N days
    python scripts/etl/basketball_reference_daily_box_scores.py --days 3

    # Dry run (don't scrape, just show what would be scraped)
    python scripts/etl/basketball_reference_daily_box_scores.py --dry-run

Typical usage in overnight workflow:
    - Run daily at 3 AM
    - Scrapes previous day's games
    - Adds to S3 and database
    - Takes ~2-3 minutes for typical game day (10-15 games)

Version: 1.0
Created: October 18, 2025
"""

import argparse
import sqlite3
import requests
from datetime import datetime, timedelta
import logging
import subprocess
import sys

# Configuration
DB_PATH = "/tmp/basketball_reference_boxscores.db"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_yesterday():
    """Get yesterday's date"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def get_games_from_espn(date_str):
    """Get games for a specific date from ESPN API"""
    try:
        # ESPN scoreboard API
        # Date format: YYYYMMDD
        date_formatted = date_str.replace('-', '')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_formatted}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        games = []
        for event in data.get('events', []):
            # Extract teams
            competitions = event.get('competitions', [])
            if not competitions:
                continue

            competition = competitions[0]
            competitors = competition.get('competitors', [])

            if len(competitors) != 2:
                continue

            # Find home and away teams
            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), None)

            if not home_team or not away_team:
                continue

            # Get abbreviations
            home_abbr = home_team.get('team', {}).get('abbreviation', '')
            away_abbr = away_team.get('team', {}).get('abbreviation', '')

            # Get date
            game_date = event.get('date', '')[:10]  # Extract YYYY-MM-DD

            # Build Basketball Reference game ID
            # Format: YYYYMMDD0{HOME_TEAM_CODE}
            date_code = game_date.replace('-', '')
            game_id = f"{date_code}0{home_abbr}"

            games.append({
                'game_id': game_id,
                'game_date': game_date,
                'home_team': home_abbr,
                'away_team': away_abbr
            })

        return games

    except Exception as e:
        logger.error(f"Error fetching games from ESPN for {date_str}: {e}")
        return []


def determine_season(date_str):
    """Determine NBA season from date (e.g., '2023-01-15' -> 2023)"""
    date = datetime.strptime(date_str, '%Y-%m-%d')

    # NBA season typically runs Oct-Jun
    # If month is Jul-Sep, it's offseason (use next year's season)
    # If month is Oct-Dec, season = next year
    # If month is Jan-Jun, season = current year

    year = date.year
    month = date.month

    if month >= 10:  # October, November, December
        return year + 1
    elif month <= 6:  # January - June
        return year
    else:  # July, August, September (offseason)
        return year + 1


def insert_games_to_progress_table(games, dry_run=False):
    """Insert games into scraping_progress table"""
    if dry_run:
        logger.info(f"[DRY RUN] Would insert {len(games)} games:")
        for game in games:
            logger.info(f"  {game['game_id']}: {game['away_team']} @ {game['home_team']} on {game['game_date']}")
        return

    if not games:
        logger.info("No games to insert")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        inserted = 0
        already_exists = 0

        for game in games:
            # Determine season
            season = determine_season(game['game_date'])

            # Check if already exists
            cursor.execute("SELECT game_id FROM scraping_progress WHERE game_id = ?", (game['game_id'],))
            if cursor.fetchone():
                already_exists += 1
                logger.debug(f"Game {game['game_id']} already in progress table")
                continue

            # Insert
            cursor.execute("""
                INSERT INTO scraping_progress
                (game_id, game_date, season, home_team, away_team, priority, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (
                game['game_id'],
                game['game_date'],
                season,
                game['home_team'],
                game['away_team'],
                1  # High priority for recent games
            ))

            inserted += 1
            logger.info(f"Added game: {game['game_id']} ({game['away_team']} @ {game['home_team']})")

        conn.commit()
        conn.close()

        logger.info(f"Inserted {inserted} new games, {already_exists} already existed")

    except Exception as e:
        logger.error(f"Error inserting games to database: {e}")
        raise


def run_box_score_scraper(max_games, dry_run=False):
    """Run the box score scraper on pending games"""
    if dry_run:
        logger.info(f"[DRY RUN] Would run box score scraper on {max_games} games")
        return

    logger.info(f"Running box score scraper on up to {max_games} games...")

    try:
        cmd = [
            sys.executable,
            "scripts/etl/basketball_reference_box_score_scraper.py",
            "--max-games", str(max_games),
            "--priority", "1"  # Only recent games
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Log output
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")

        logger.info("✓ Box score scraper completed")

    except subprocess.CalledProcessError as e:
        logger.error(f"Box score scraper failed: {e}")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Scrape daily box scores from Basketball Reference"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to scrape (YYYY-MM-DD), defaults to yesterday"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Scrape last N days instead of single date"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be scraped without actually scraping"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("BASKETBALL REFERENCE DAILY BOX SCORE SCRAPER")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dry run: {args.dry_run}\n")

    # Determine dates to scrape
    if args.days:
        dates = []
        for i in range(args.days):
            date = datetime.now() - timedelta(days=i+1)
            dates.append(date.strftime('%Y-%m-%d'))
        logger.info(f"Scraping last {args.days} days: {dates}")
    elif args.date:
        dates = [args.date]
        logger.info(f"Scraping specific date: {args.date}")
    else:
        dates = [get_yesterday()]
        logger.info(f"Scraping yesterday: {dates[0]}")

    # Get games for each date
    all_games = []
    for date in dates:
        logger.info(f"\nFetching games for {date}...")
        games = get_games_from_espn(date)

        if games:
            logger.info(f"  Found {len(games)} games")
            all_games.extend(games)
        else:
            logger.info(f"  No games found (offseason or no games scheduled)")

    if not all_games:
        logger.info("\n✓ No games to scrape")
        return

    logger.info(f"\nTotal games found: {len(all_games)}")

    # Insert into database
    logger.info("\nInserting games into scraping_progress table...")
    insert_games_to_progress_table(all_games, dry_run=args.dry_run)

    # Run box score scraper
    if not args.dry_run:
        logger.info("\nRunning box score scraper...")
        run_box_score_scraper(max_games=len(all_games), dry_run=args.dry_run)

    print("\n" + "="*70)
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
