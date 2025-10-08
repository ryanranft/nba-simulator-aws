#!/usr/bin/env python3
"""
Scrape NBA.com lineup data using the leaguedashlineups endpoint.

This script fetches official 5-man lineup combinations for each season,
which can be used to fill gaps in possession panel lineup tracking.

Usage:
    python scrape_nba_lineups.py --season 1996-97 --season-type Regular Season
    python scrape_nba_lineups.py --all-seasons  # Scrape 1996-2025
    python scrape_nba_lineups.py --game-id 0029600001  # Specific game
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
import argparse

from nba_api.stats.endpoints import leaguedashlineups
from nba_api.stats.library.parameters import SeasonTypeAllStar

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path('/tmp/nba_api_lineups')
OUTPUT_DIR.mkdir(exist_ok=True)

# Rate limiting
RATE_LIMIT_SECONDS = 0.6  # 600ms between requests


def scrape_season_lineups(season, season_type='Regular Season', output_dir=OUTPUT_DIR):
    """
    Scrape all lineup combinations for a given season.

    Args:
        season: Season string (e.g., '1996-97', '2023-24')
        season_type: Season type (Regular Season, Playoffs, Pre Season)
        output_dir: Directory to save JSON files

    Returns:
        dict: Lineup data or None if error
    """
    try:
        logger.info(f"Scraping lineups for {season} {season_type}...")

        # Call NBA API
        lineups = leaguedashlineups.LeagueDashLineups(
            season=season,
            season_type_all_star=season_type,
            group_quantity=5,  # 5-man lineups
            per_mode_detailed='PerGame'
        )

        # Get data
        data = lineups.get_dict()

        # Save to file
        season_clean = season.replace('-', '_')
        season_type_clean = season_type.replace(' ', '_').lower()
        output_file = output_dir / f'lineups_{season_clean}_{season_type_clean}.json'

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Count lineups
        result_sets = data.get('resultSets', [])
        if result_sets:
            lineup_count = len(result_sets[0].get('rowSet', []))
            logger.info(f"  ✓ Scraped {lineup_count} lineups for {season} {season_type}")
            logger.info(f"  Saved to: {output_file}")

        return data

    except Exception as e:
        logger.error(f"  ✗ Error scraping {season} {season_type}: {e}")
        return None


def scrape_all_seasons(start_season=1996, end_season=2025, season_types=None):
    """
    Scrape lineup data for all seasons.

    Args:
        start_season: First year to scrape (e.g., 1996)
        end_season: Last year to scrape (e.g., 2025)
        season_types: List of season types to scrape
    """
    if season_types is None:
        season_types = ['Regular Season', 'Playoffs']

    logger.info("="*60)
    logger.info("NBA LINEUP SCRAPER - ALL SEASONS")
    logger.info("="*60)
    logger.info(f"Seasons: {start_season}-{end_season}")
    logger.info(f"Season types: {', '.join(season_types)}")
    logger.info(f"Output: {OUTPUT_DIR}")
    logger.info("="*60)
    logger.info("")

    total_scraped = 0
    total_failed = 0

    # Generate season strings (e.g., "1996-97", "1997-98", ...)
    for year in range(start_season, end_season):
        season_str = f"{year}-{str(year + 1)[-2:]}"

        for season_type in season_types:
            # Scrape
            data = scrape_season_lineups(season_str, season_type)

            if data:
                total_scraped += 1
            else:
                total_failed += 1

            # Rate limit
            time.sleep(RATE_LIMIT_SECONDS)

    logger.info("")
    logger.info("="*60)
    logger.info("SCRAPING COMPLETE")
    logger.info("="*60)
    logger.info(f"Successfully scraped: {total_scraped}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Total files: {len(list(OUTPUT_DIR.glob('*.json')))}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("="*60)


def get_game_lineups(game_id):
    """
    Extract lineups for a specific game from season lineup data.

    This function finds which season the game belongs to and extracts
    the relevant lineup combinations.

    Args:
        game_id: NBA game ID (e.g., '0029600001')

    Returns:
        list: List of lineup dicts with player IDs and team IDs
    """
    # Parse season from game ID
    # Game ID format: 00296XXXXX where 296 = 1996-97 season
    if len(game_id) < 5:
        logger.error(f"Invalid game ID: {game_id}")
        return []

    # Extract season code (e.g., "296" from "0029600001")
    season_code = game_id[3:5]  # "96" from "002 96 00001"
    year = 1900 + int(season_code)
    season_str = f"{year}-{str(year + 1)[-2:]}"

    # Load season lineup data
    season_clean = season_str.replace('-', '_')
    lineup_file = OUTPUT_DIR / f'lineups_{season_clean}_regular_season.json'

    if not lineup_file.exists():
        logger.warning(f"No lineup data found for {season_str}")
        return []

    try:
        with open(lineup_file, 'r') as f:
            data = json.load(f)

        # Parse lineup data
        # Note: This returns all lineups for the season, not just this game
        # You'd need to match by team_id or use play-by-play to filter
        result_sets = data.get('resultSets', [])
        if not result_sets:
            return []

        headers = result_sets[0]['headers']
        rows = result_sets[0]['rowSet']

        lineups = []
        for row in rows:
            lineup_dict = dict(zip(headers, row))
            lineups.append(lineup_dict)

        logger.info(f"Found {len(lineups)} season lineups for game {game_id}")
        return lineups

    except Exception as e:
        logger.error(f"Error loading lineup data: {e}")
        return []


def parse_lineup_string(lineup_str):
    """
    Parse lineup string into list of player IDs.

    Args:
        lineup_str: String like "James - Wade - Bosh - Haslem - Anthony"

    Returns:
        list: List of player names (IDs require separate lookup)
    """
    if not lineup_str:
        return []

    # Split by dash and clean
    players = [p.strip() for p in lineup_str.split('-')]
    return players


def main():
    parser = argparse.ArgumentParser(description='Scrape NBA lineup combinations')
    parser.add_argument('--season', type=str, help='Season (e.g., 1996-97)')
    parser.add_argument('--season-type', type=str, default='Regular Season',
                       choices=['Regular Season', 'Playoffs', 'Pre Season'],
                       help='Season type')
    parser.add_argument('--all-seasons', action='store_true',
                       help='Scrape all seasons from 1996-2025')
    parser.add_argument('--start-year', type=int, default=1996,
                       help='Start year for --all-seasons')
    parser.add_argument('--end-year', type=int, default=2025,
                       help='End year for --all-seasons')
    parser.add_argument('--game-id', type=str, help='Get lineups for specific game')

    args = parser.parse_args()

    if args.all_seasons:
        # Scrape all seasons
        scrape_all_seasons(
            start_season=args.start_year,
            end_season=args.end_year
        )
    elif args.game_id:
        # Get lineups for specific game
        lineups = get_game_lineups(args.game_id)

        if lineups:
            print(f"\nFound {len(lineups)} lineups for game {args.game_id}:")
            for i, lineup in enumerate(lineups[:5], 1):  # Show first 5
                print(f"\n{i}. {lineup.get('GROUP_NAME', 'Unknown')}")
                print(f"   Team: {lineup.get('TEAM_NAME', 'Unknown')}")
                print(f"   Minutes: {lineup.get('MIN', 0)}")
                print(f"   +/-: {lineup.get('PLUS_MINUS', 0)}")
    elif args.season:
        # Scrape single season
        scrape_season_lineups(args.season, args.season_type)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
