#!/usr/bin/env python3
"""
hoopR Daily Data Collector
Autonomously collect yesterday's NBA games from hoopR and load into databases

This script is designed to run daily (via cron or ADCE) to keep hoopR data current.

Usage:
    # Collect yesterday's games (default)
    python scripts/etl/collect_hoopr_daily.py

    # Collect last N days
    python scripts/etl/collect_hoopr_daily.py --days 3

    # Collect specific date
    python scripts/etl/collect_hoopr_daily.py --date 2025-11-09

    # Dry run (no database loading)
    python scripts/etl/collect_hoopr_daily.py --dry-run

    # Save to parquet only (no database)
    python scripts/etl/collect_hoopr_daily.py --parquet-only

Created: November 9, 2025
Purpose: Daily autonomous hoopR data collection and loading
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HooprDailyCollector:
    """Collect and load daily hoopR data"""

    # Backup directory for parquet files
    BACKUP_DIR = Path.home() / "Desktop/sports_data_backup/hoopR/nba"

    def __init__(self, days_back: int = 1, dry_run: bool = False, parquet_only: bool = False):
        """
        Initialize daily collector

        Args:
            days_back: Number of days to look back (default: 1 = yesterday)
            dry_run: If True, don't save or load data
            parquet_only: If True, save to parquet but don't load to database
        """
        self.days_back = days_back
        self.dry_run = dry_run
        self.parquet_only = parquet_only

        # Import hoopR (lazy import to check availability)
        try:
            from sportsdataverse.nba import (
                nba_pbp,
                nba_schedule,
                load_nba_player_boxscore,
                load_nba_team_boxscore
            )
            self.nba_pbp = nba_pbp
            self.nba_schedule = nba_schedule
            self.load_player_box = load_nba_player_boxscore
            self.load_team_box = load_nba_team_boxscore
        except ImportError:
            logger.error("hoopR (sportsdataverse) not installed")
            logger.error("Install: pip install sportsdataverse")
            sys.exit(1)

        # Stats
        self.stats = {
            'games_found': 0,
            'games_collected': 0,
            'pbp_rows': 0,
            'player_box_rows': 0,
            'team_box_rows': 0,
            'schedule_rows': 0,
            'errors': []
        }

        logger.info(f"HooprDailyCollector initialized (days_back={days_back}, dry_run={dry_run}, parquet_only={parquet_only})")

    def get_date_range(self) -> List[str]:
        """Get list of dates to collect"""
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=self.days_back - 1)

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return dates

    def get_games_for_date(self, date_str: str) -> List[int]:
        """
        Get list of game IDs for a specific date

        Args:
            date_str: Date in format 'YYYY-MM-DD'

        Returns:
            List of game IDs
        """
        try:
            # Parse date to get season
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            season = date_obj.year if date_obj.month >= 10 else date_obj.year - 1

            logger.info(f"Fetching schedule for {date_str} (season {season})...")

            # Get schedule
            schedule_df = self.nba_schedule(season)

            if schedule_df is None or schedule_df.empty:
                logger.warning(f"No schedule data for season {season}")
                return []

            # Filter to specific date
            schedule_df['game_date'] = pd.to_datetime(schedule_df['date']).dt.strftime('%Y-%m-%d')
            date_games = schedule_df[schedule_df['game_date'] == date_str]

            if date_games.empty:
                logger.info(f"No games found for {date_str}")
                return []

            game_ids = date_games['id'].tolist()
            logger.info(f"Found {len(game_ids)} games for {date_str}")

            # Save schedule data
            if not self.dry_run:
                self.save_schedule_data(date_games, season)

            self.stats['games_found'] += len(game_ids)
            self.stats['schedule_rows'] += len(date_games)

            return game_ids

        except Exception as e:
            logger.error(f"Error getting schedule for {date_str}: {e}")
            self.stats['errors'].append(f"Schedule {date_str}: {str(e)}")
            return []

    def collect_game_data(self, game_id: int, season: int) -> Dict[str, pd.DataFrame]:
        """
        Collect all data types for a single game

        Args:
            game_id: Game ID
            season: Season year

        Returns:
            Dictionary with DataFrames for each data type
        """
        data = {
            'pbp': None,
            'player_box': None,
            'team_box': None
        }

        try:
            logger.info(f"  Collecting game {game_id}...")

            # Play-by-play
            try:
                pbp_df = self.nba_pbp(game_id)
                if pbp_df is not None and not pbp_df.empty:
                    data['pbp'] = pbp_df
                    self.stats['pbp_rows'] += len(pbp_df)
                    logger.info(f"    ✅ PBP: {len(pbp_df)} plays")
            except Exception as e:
                logger.warning(f"    ❌ PBP error: {e}")

            # Player box scores
            try:
                player_box_df = self.load_player_box([season])
                if player_box_df is not None and not player_box_df.empty:
                    # Filter to this game
                    game_players = player_box_df[player_box_df['game_id'] == game_id]
                    if not game_players.empty:
                        data['player_box'] = game_players
                        self.stats['player_box_rows'] += len(game_players)
                        logger.info(f"    ✅ Player box: {len(game_players)} players")
            except Exception as e:
                logger.warning(f"    ❌ Player box error: {e}")

            # Team box scores
            try:
                team_box_df = self.load_team_box([season])
                if team_box_df is not None and not team_box_df.empty:
                    # Filter to this game
                    game_teams = team_box_df[team_box_df['game_id'] == game_id]
                    if not game_teams.empty:
                        data['team_box'] = game_teams
                        self.stats['team_box_rows'] += len(game_teams)
                        logger.info(f"    ✅ Team box: {len(game_teams)} teams")
            except Exception as e:
                logger.warning(f"    ❌ Team box error: {e}")

            self.stats['games_collected'] += 1
            return data

        except Exception as e:
            logger.error(f"Error collecting game {game_id}: {e}")
            self.stats['errors'].append(f"Game {game_id}: {str(e)}")
            return data

    def save_schedule_data(self, schedule_df: pd.DataFrame, season: int):
        """Save schedule data to parquet"""
        if schedule_df.empty:
            return

        output_dir = self.BACKUP_DIR / "schedule" / "parquet"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"nba_data_{season}.parquet"

        # Load existing data if exists
        if output_file.exists():
            existing_df = pd.read_parquet(output_file)
            # Combine and deduplicate
            combined_df = pd.concat([existing_df, schedule_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['id'], keep='last')
        else:
            combined_df = schedule_df

        # Save
        combined_df.to_parquet(output_file, index=False)
        logger.info(f"Saved schedule data to {output_file} ({len(combined_df)} games)")

    def save_game_data(self, data: Dict[str, pd.DataFrame], season: int):
        """
        Save game data to parquet files

        Args:
            data: Dictionary of DataFrames
            season: Season year
        """
        for data_type, df in data.items():
            if df is None or df.empty:
                continue

            # Determine output directory
            output_dir = self.BACKUP_DIR / data_type / "parquet"
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"nba_data_{season}.parquet"

            # Load existing data if exists
            if output_file.exists():
                existing_df = pd.read_parquet(output_file)
                # Combine and deduplicate
                combined_df = pd.concat([existing_df, df], ignore_index=True)

                # Deduplicate based on key columns
                if data_type == 'pbp':
                    combined_df = combined_df.drop_duplicates(subset=['id'], keep='last')
                elif data_type == 'player_box':
                    combined_df = combined_df.drop_duplicates(subset=['game_id', 'athlete_id'], keep='last')
                elif data_type == 'team_box':
                    combined_df = combined_df.drop_duplicates(subset=['game_id', 'team_id'], keep='last')
            else:
                combined_df = df

            # Save
            combined_df.to_parquet(output_file, index=False)
            logger.info(f"Saved {data_type} to {output_file} ({len(combined_df)} rows)")

    def load_to_databases(self, season: int):
        """
        Load parquet files to databases using load_hoopr_parquet.py

        Args:
            season: Season to load
        """
        if self.dry_run or self.parquet_only:
            logger.info("Skipping database load (dry_run or parquet_only mode)")
            return

        logger.info(f"\n{'='*60}")
        logger.info("Loading data to databases...")
        logger.info(f"{'='*60}")

        # Import and run loader
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from load_hoopr_parquet import HooprParquetLoader

            loader = HooprParquetLoader(parquet_dir=self.BACKUP_DIR)
            loader.load_all(season=season)

            logger.info("✅ Database loading complete")

        except Exception as e:
            logger.error(f"Error loading to databases: {e}")
            self.stats['errors'].append(f"Database load: {str(e)}")

    def collect_daily(self, specific_date: Optional[str] = None):
        """
        Run daily collection

        Args:
            specific_date: Optional specific date to collect (format: YYYY-MM-DD)
        """
        logger.info(f"\n{'='*80}")
        logger.info("HOOPR DAILY COLLECTION")
        logger.info(f"{'='*80}")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        logger.info(f"Save: {'Parquet only' if self.parquet_only else 'Parquet + Database'}")
        logger.info(f"{'='*80}\n")

        # Get dates to collect
        if specific_date:
            dates = [specific_date]
        else:
            dates = self.get_date_range()

        logger.info(f"Collecting dates: {', '.join(dates)}")

        # Collect each date
        seasons_collected = set()

        for date_str in dates:
            logger.info(f"\n📅 Processing {date_str}")

            # Get games for date
            game_ids = self.get_games_for_date(date_str)

            if not game_ids:
                continue

            # Determine season
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            season = date_obj.year if date_obj.month >= 10 else date_obj.year - 1
            seasons_collected.add(season)

            # Collect each game
            for game_id in game_ids:
                game_data = self.collect_game_data(game_id, season)

                # Save to parquet
                if not self.dry_run:
                    self.save_game_data(game_data, season)

        # Load to databases
        if seasons_collected:
            for season in sorted(seasons_collected):
                self.load_to_databases(season)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print collection summary"""
        logger.info(f"\n{'='*80}")
        logger.info("COLLECTION SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Games found:     {self.stats['games_found']:,}")
        logger.info(f"Games collected: {self.stats['games_collected']:,}")
        logger.info(f"PBP rows:        {self.stats['pbp_rows']:,}")
        logger.info(f"Player box rows: {self.stats['player_box_rows']:,}")
        logger.info(f"Team box rows:   {self.stats['team_box_rows']:,}")
        logger.info(f"Schedule rows:   {self.stats['schedule_rows']:,}")

        if self.stats['errors']:
            logger.error(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                logger.error(f"  - {error}")
        else:
            logger.info("\n✅ No errors!")

        logger.info(f"{'='*80}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Daily hoopR data collection')
    parser.add_argument('--days', type=int, default=1, help='Number of days to look back (default: 1)')
    parser.add_argument('--date', type=str, help='Specific date to collect (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no saving)')
    parser.add_argument('--parquet-only', action='store_true', help='Save to parquet only (skip database)')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create collector
    collector = HooprDailyCollector(
        days_back=args.days,
        dry_run=args.dry_run,
        parquet_only=args.parquet_only
    )

    # Run collection
    collector.collect_daily(specific_date=args.date)

    # Exit with error code if there were errors
    if collector.stats['errors']:
        sys.exit(1)


if __name__ == '__main__':
    main()
