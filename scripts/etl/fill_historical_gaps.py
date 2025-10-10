#!/usr/bin/env python3
"""
Fill Historical hoopR Gaps - One-Time Operation

Attempts to fill 2,467 missing hoopR games by scraping from hoopR API.
This is a ONE-TIME historical backfill, not for nightly automation.

Strategy:
1. Read gap list from /tmp/missing_from_hoopr.csv (2,467 games)
2. Group games by season
3. For each season, load hoopR PBP data
4. Extract games from gap list
5. Load to hoopR database
6. Document permanently unavailable games

Note: hoopR API limitations mean some gaps cannot be filled:
- Pre-2002: API doesn't support (8 games)
- Inefficiency: API loads entire seasons (not individual games)
- Some games simply unavailable in hoopR's data source

Runtime: 2-3 hours (rate-limited by hoopR API)

Usage:
    python scripts/etl/fill_historical_gaps.py
    python scripts/etl/fill_historical_gaps.py --limit 10  # Test on 10 games
    python scripts/etl/fill_historical_gaps.py --season 2003  # Specific season
    python scripts/etl/fill_historical_gaps.py --dry-run

Version: 1.0
Created: October 9, 2025
"""

import sqlite3
import csv
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import argparse
import pandas as pd

# Import sportsdataverse
try:
    from sportsdataverse.nba import load_nba_pbp, load_nba_schedule
    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse not installed")
    print("Install: pip install sportsdataverse")
    sys.exit(1)

# Paths
HOOPR_DB = "/tmp/hoopr_local.db"
GAP_LIST = "/tmp/missing_from_hoopr.csv"
UNAVAILABLE_GAMES_FILE = "/tmp/hoopr_permanently_unavailable.csv"

class HistoricalGapFiller:
    """Fill historical hoopR gaps from hoopR API"""

    def __init__(self, db_path=HOOPR_DB, dry_run=False):
        self.db_path = db_path
        self.dry_run = dry_run

        self.stats = {
            'gaps_total': 0,
            'gaps_attempted': 0,
            'gaps_filled': 0,
            'gaps_unavailable': 0,
            'events_loaded': 0,
            'errors': 0
        }

        self.unavailable_games = []

    def load_gap_list(self, limit=None, season_filter=None):
        """Load list of games missing from hoopR."""

        print("=" * 70)
        print("LOAD GAP LIST")
        print("=" * 70)
        print()

        if not Path(GAP_LIST).exists():
            print(f"❌ Gap list not found: {GAP_LIST}")
            print("Run cross-validation first:")
            print("  python scripts/utils/cross_validate_espn_hoopr_with_mapping.py")
            sys.exit(1)

        print(f"Reading: {GAP_LIST}")

        gaps = []
        with open(GAP_LIST, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by season if specified
                if season_filter:
                    game_year = int(row['game_date'].split('-')[0])
                    if game_year != season_filter:
                        continue

                gaps.append(row)

                if limit and len(gaps) >= limit:
                    break

        self.stats['gaps_total'] = len(gaps)

        print(f"✓ Loaded {len(gaps):,} missing games")
        print()

        # Group by season
        by_season = defaultdict(list)
        for gap in gaps:
            game_year = int(gap['game_date'].split('-')[0])
            # NBA season logic: Oct-June spans two years
            month = int(gap['game_date'].split('-')[1])
            season = game_year if month >= 10 else game_year - 1
            by_season[season].append(gap)

        print("Gaps by season:")
        for season in sorted(by_season.keys()):
            print(f"  {season}: {len(by_season[season]):,} games")
        print()

        return gaps, by_season

    def check_hoopr_api_availability(self, season):
        """Check if hoopR API supports this season."""

        # hoopR doesn't support pre-2002
        if season < 2002:
            return False, "hoopR API doesn't support seasons before 2002"

        return True, None

    def load_season_from_hoopr(self, season):
        """Load entire season PBP from hoopR API."""

        print(f"Loading hoopR data for {season} season...")

        try:
            # Check API availability
            available, reason = self.check_hoopr_api_availability(season)
            if not available:
                print(f"  ⚠️  {reason}")
                return None, reason

            # Load schedule
            print(f"  Loading schedule...")
            schedule_df = load_nba_schedule(seasons=[season])

            if schedule_df is None or len(schedule_df) == 0:
                reason = "No schedule data returned from hoopR API"
                print(f"  ⚠️  {reason}")
                return None, reason

            # Convert to pandas if it's a Polars DataFrame
            if hasattr(schedule_df, 'to_pandas'):
                schedule_df = schedule_df.to_pandas()

            print(f"  ✓ Loaded {len(schedule_df):,} games in schedule")

            # Load play-by-play
            print(f"  Loading play-by-play...")
            pbp_df = load_nba_pbp(seasons=[season])

            if pbp_df is None or len(pbp_df) == 0:
                reason = "No PBP data returned from hoopR API"
                print(f"  ⚠️  {reason}")
                return None, reason

            # Convert to pandas if it's a Polars DataFrame
            if hasattr(pbp_df, 'to_pandas'):
                pbp_df = pbp_df.to_pandas()

            print(f"  ✓ Loaded {len(pbp_df):,} PBP events")
            print()

            return {'schedule': schedule_df, 'pbp': pbp_df}, None

        except Exception as e:
            reason = f"Error loading from hoopR API: {e}"
            print(f"  ❌ {reason}")
            return None, reason

    def load_schedule_to_db(self, schedule_df, game_ids):
        """Load schedule data for specific games to database."""

        if self.dry_run:
            return

        # Filter to only games we want
        schedule_df = schedule_df[schedule_df['game_id'].isin(game_ids)]

        if len(schedule_df) == 0:
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
            print(f"    ❌ Error loading schedule: {e}")
            self.stats['errors'] += 1
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def load_pbp_to_db(self, pbp_df, game_id):
        """Load play-by-play data for a specific game to database."""

        if self.dry_run:
            self.stats['events_loaded'] += len(pbp_df)
            return len(pbp_df)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear existing PBP for this game
            cursor.execute("DELETE FROM play_by_play WHERE game_id = ?", (str(game_id),))

            # Insert new PBP
            events_loaded = 0
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
                events_loaded += 1

            conn.commit()
            self.stats['events_loaded'] += events_loaded
            return events_loaded

        except Exception as e:
            print(f"    ❌ Error loading PBP: {e}")
            self.stats['errors'] += 1
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()

    def fill_gaps_for_season(self, season, gaps_in_season):
        """Fill all gaps for a specific season."""

        print(f"{'=' * 70}")
        print(f"SEASON {season}: {len(gaps_in_season):,} gaps to fill")
        print(f"{'=' * 70}")
        print()

        # Load season data from hoopR API
        season_data, unavailable_reason = self.load_season_from_hoopr(season)

        if not season_data:
            # Season unavailable - mark all games as unavailable
            print(f"⚠️  Season {season} unavailable from hoopR API")
            print(f"   Reason: {unavailable_reason}")
            print(f"   Marking {len(gaps_in_season):,} games as permanently unavailable")
            print()

            for gap in gaps_in_season:
                self.unavailable_games.append({
                    'game_id': gap['hoopr_game_id'],
                    'game_date': gap['game_date'],
                    'matchup': f"{gap['away_team']} @ {gap['home_team']}",
                    'reason': unavailable_reason
                })
                self.stats['gaps_unavailable'] += 1

            return

        # Extract schedule and PBP data
        schedule_df = season_data['schedule']
        pbp_df = season_data['pbp']

        # Process each gap
        game_ids_to_load = []
        for i, gap in enumerate(gaps_in_season, 1):
            hoopr_game_id = gap['hoopr_game_id']
            game_date = gap['game_date']
            matchup = f"{gap['away_team']} @ {gap['home_team']}"

            print(f"[{i}/{len(gaps_in_season)}] {matchup} ({game_date})")

            # Skip games without hoopR mapping
            if not hoopr_game_id or hoopr_game_id.strip() == '':
                print(f"  ⚠️  No hoopR game ID (no mapping exists)")
                self.unavailable_games.append({
                    'game_id': gap['espn_game_id'],
                    'game_date': game_date,
                    'matchup': matchup,
                    'reason': 'No ESPN-hoopR game ID mapping exists'
                })
                self.stats['gaps_unavailable'] += 1
                continue

            self.stats['gaps_attempted'] += 1

            # Check if game exists in hoopR data
            game_pbp = pbp_df[pbp_df['game_id'] == int(hoopr_game_id)]

            if len(game_pbp) == 0:
                print(f"  ⚠️  Not available in hoopR API")
                self.unavailable_games.append({
                    'game_id': hoopr_game_id,
                    'game_date': game_date,
                    'matchup': matchup,
                    'reason': f'Not in hoopR API data for season {season}'
                })
                self.stats['gaps_unavailable'] += 1
                continue

            # Game found!
            print(f"  ✓ Found {len(game_pbp):,} PBP events")

            if self.dry_run:
                print(f"  [DRY RUN] Would load to database")
                self.stats['gaps_filled'] += 1
                self.stats['events_loaded'] += len(game_pbp)
            else:
                # Load to database
                events_loaded = self.load_pbp_to_db(game_pbp, hoopr_game_id)
                if events_loaded > 0:
                    game_ids_to_load.append(int(hoopr_game_id))
                    self.stats['gaps_filled'] += 1
                    print(f"  ✓ Loaded to database")

        # Load schedule for all successfully loaded games
        if not self.dry_run and game_ids_to_load:
            print()
            print(f"Loading schedule for {len(game_ids_to_load):,} games...")
            self.load_schedule_to_db(schedule_df, game_ids_to_load)
            print(f"✓ Schedule loaded")

        print()

    def export_unavailable_games(self):
        """Export list of permanently unavailable games."""

        if not self.unavailable_games:
            return

        print(f"Exporting {len(self.unavailable_games):,} unavailable games...")

        with open(UNAVAILABLE_GAMES_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['game_id', 'game_date', 'matchup', 'reason'])
            writer.writeheader()
            writer.writerows(self.unavailable_games)

        print(f"✓ Exported to: {UNAVAILABLE_GAMES_FILE}")

    def fill_all_gaps(self, gaps, by_season):
        """Fill all historical gaps."""

        print("=" * 70)
        print("FILL HISTORICAL GAPS")
        print("=" * 70)
        print()

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made to database")
            print()

        # Process each season
        for season in sorted(by_season.keys()):
            gaps_in_season = by_season[season]
            self.fill_gaps_for_season(season, gaps_in_season)

        # Export unavailable games
        if self.unavailable_games:
            print()
            self.export_unavailable_games()

        # Print summary
        print()
        print("=" * 70)
        print("GAP FILLING SUMMARY")
        print("=" * 70)
        print(f"Total gaps:             {self.stats['gaps_total']:,}")
        print(f"Gaps attempted:         {self.stats['gaps_attempted']:,}")
        print(f"Gaps filled:            {self.stats['gaps_filled']:,}")
        print(f"Gaps unavailable:       {self.stats['gaps_unavailable']:,}")
        print(f"Events loaded:          {self.stats['events_loaded']:,}")
        print(f"Errors:                 {self.stats['errors']:,}")
        print("=" * 70)

        if self.stats['gaps_filled'] > 0:
            coverage_before = 28779
            coverage_after = coverage_before + self.stats['gaps_filled']
            total_games = 31243
            pct_before = coverage_before / total_games * 100
            pct_after = coverage_after / total_games * 100

            print()
            print(f"hoopR Coverage:")
            print(f"  Before: {coverage_before:,}/{total_games:,} ({pct_before:.1f}%)")
            print(f"  After:  {coverage_after:,}/{total_games:,} ({pct_after:.1f}%)")
            print(f"  Gain:   {self.stats['gaps_filled']:,} games (+{pct_after - pct_before:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Fill historical hoopR gaps - One-time operation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fill all gaps (2,467 games, ~2-3 hours)
  python scripts/etl/fill_historical_gaps.py

  # Test on 10 games
  python scripts/etl/fill_historical_gaps.py --limit 10

  # Fill specific season
  python scripts/etl/fill_historical_gaps.py --season 2003

  # Dry run (no database changes)
  python scripts/etl/fill_historical_gaps.py --dry-run

Purpose:
  One-time historical backfill for 2,467 missing hoopR games.
  NOT for nightly automation (use incremental scrapers instead).

Note:
  Some gaps cannot be filled due to hoopR API limitations:
  - Pre-2002 seasons not supported
  - Some games simply unavailable in hoopR's data
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of gaps to attempt (for testing)'
    )

    parser.add_argument(
        '--season',
        type=int,
        help='Fill gaps for specific season only'
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

    # Create gap filler
    filler = HistoricalGapFiller(db_path=args.db_path, dry_run=args.dry_run)

    # Load gap list
    gaps, by_season = filler.load_gap_list(limit=args.limit, season_filter=args.season)

    if not gaps:
        print("No gaps to fill!")
        return

    # Fill gaps
    filler.fill_all_gaps(gaps, by_season)

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
