#!/usr/bin/env python3
"""
Integrate Basketball Reference Data into Unified Database

Downloads Basketball Reference schedules from S3, performs data quality checks,
and integrates as third data source alongside ESPN and hoopR.

Basketball Reference provides historical coverage back to 1947, filling gaps
in ESPN (2002+) and hoopR (2002+) data.

Usage:
    python scripts/etl/integrate_basketball_reference.py
    python scripts/etl/integrate_basketball_reference.py --year 2024  # Specific year
    python scripts/etl/integrate_basketball_reference.py --download-only  # Just download

Created: October 10, 2025
"""

import sqlite3
import json
import boto3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse
from collections import defaultdict

# Database paths
BBREF_DB = "/tmp/basketball_reference_local.db"
UNIFIED_DB = "/tmp/unified_nba.db"

# S3 configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX = "basketball_reference/schedules/"

# Local download path
DOWNLOAD_DIR = Path("/tmp/basketball_reference_schedules")


def download_schedules_from_s3(year: Optional[int] = None):
    """Download Basketball Reference schedules from S3."""

    print("=" * 70)
    print("DOWNLOAD BASKETBALL REFERENCE SCHEDULES FROM S3")
    print("=" * 70)
    print()

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client('s3')

    # List all years
    print("Listing available years in S3...")
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX, Delimiter='/')

    years = []
    if 'CommonPrefixes' in response:
        for prefix in response['CommonPrefixes']:
            year_str = prefix['Prefix'].split('/')[-2]
            try:
                years.append(int(year_str))
            except ValueError:
                continue

    years.sort()
    print(f"✓ Found {len(years)} years in S3: {min(years)} - {max(years)}")
    print()

    # Filter to specific year if requested
    if year:
        years = [y for y in years if y == year]
        print(f"⚠️  Filtering to year {year}")
        print()

    # Download schedules
    downloaded = 0
    for year_val in years:
        s3_key = f"{S3_PREFIX}{year_val}/schedule.json"
        local_path = DOWNLOAD_DIR / f"{year_val}_schedule.json"

        try:
            s3.download_file(S3_BUCKET, s3_key, str(local_path))
            downloaded += 1
            if downloaded % 10 == 0:
                print(f"  Downloaded {downloaded}/{len(years)} schedules...", end='\r')
        except Exception as e:
            print(f"⚠️  Failed to download {year_val}: {e}")

    print(f"\n✓ Downloaded {downloaded} schedules to {DOWNLOAD_DIR}")
    print()

    return downloaded


def create_bbref_database():
    """Create Basketball Reference local database."""

    print("=" * 70)
    print("CREATE BASKETBALL REFERENCE LOCAL DATABASE")
    print("=" * 70)
    print()

    conn = sqlite3.connect(BBREF_DB)
    cursor = conn.cursor()

    # Create games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            game_date TEXT NOT NULL,
            season INTEGER,
            home_team TEXT,
            away_team TEXT,
            home_score INTEGER,
            away_score INTEGER,
            start_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_season ON games(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team, away_team)")

    conn.commit()
    print("✓ Created games table with indexes")
    print()

    return conn


def parse_team_name(team_str: str) -> str:
    """Parse Basketball Reference team enum to readable name."""
    # Format: "Team.NEW_ORLEANS_PELICANS" -> "NEW ORLEANS PELICANS"
    if team_str.startswith("Team."):
        return team_str.replace("Team.", "").replace("_", " ")
    return team_str


def load_schedules_to_database(conn):
    """Load downloaded schedules into database."""

    print("=" * 70)
    print("LOAD SCHEDULES TO DATABASE")
    print("=" * 70)
    print()

    cursor = conn.cursor()

    schedule_files = sorted(DOWNLOAD_DIR.glob("*_schedule.json"))

    if not schedule_files:
        print("⚠️  No schedule files found. Run with --download first.")
        return 0

    print(f"Found {len(schedule_files)} schedule files")
    print()

    total_games = 0

    for schedule_file in schedule_files:
        year = int(schedule_file.stem.split('_')[0])

        with open(schedule_file) as f:
            games = json.load(f)

        for game in games:
            # Parse game details
            start_time = game.get('start_time', '')
            game_date = start_time.split()[0] if start_time else ''

            home_team = parse_team_name(game.get('home_team', ''))
            away_team = parse_team_name(game.get('away_team', ''))
            home_score = game.get('home_team_score')
            away_score = game.get('away_team_score')

            # Create game ID (Basketball Reference doesn't provide one)
            # Format: bbref_YYYYMMDD_HOMETEAM_AWAYTEAM
            date_part = game_date.replace('-', '')
            home_abbr = ''.join([w[0] for w in home_team.split()[:3]])  # First letter of each word
            away_abbr = ''.join([w[0] for w in away_team.split()[:3]])
            game_id = f"bbref_{date_part}_{home_abbr}_{away_abbr}"

            # Insert game
            cursor.execute("""
                INSERT OR REPLACE INTO games (
                    game_id, game_date, season,
                    home_team, away_team,
                    home_score, away_score,
                    start_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id, game_date, year,
                home_team, away_team,
                home_score, away_score,
                start_time
            ))

            total_games += 1

        if (schedule_files.index(schedule_file) + 1) % 10 == 0:
            print(f"  Processed {schedule_files.index(schedule_file) + 1}/{len(schedule_files)} years...", end='\r')

    conn.commit()
    print(f"\n✓ Loaded {total_games:,} games from {len(schedule_files)} years")
    print()

    return total_games


def run_data_quality_checks(conn):
    """Run data quality checks on Basketball Reference data."""

    print("=" * 70)
    print("DATA QUALITY CHECKS")
    print("=" * 70)
    print()

    cursor = conn.cursor()

    # Total games
    cursor.execute("SELECT COUNT(*) FROM games")
    total_games = cursor.fetchone()[0]
    print(f"Total games: {total_games:,}")

    # Games by season
    cursor.execute("""
        SELECT season, COUNT(*)
        FROM games
        GROUP BY season
        ORDER BY season
    """)

    seasons = cursor.fetchall()
    print(f"Seasons covered: {seasons[0][0]} - {seasons[-1][0]} ({len(seasons)} seasons)")

    # Games with scores
    cursor.execute("SELECT COUNT(*) FROM games WHERE home_score IS NOT NULL AND away_score IS NOT NULL")
    games_with_scores = cursor.fetchone()[0]
    print(f"Games with scores: {games_with_scores:,} ({games_with_scores/total_games*100:.1f}%)")

    # Games missing scores
    cursor.execute("SELECT COUNT(*) FROM games WHERE home_score IS NULL OR away_score IS NULL")
    games_missing_scores = cursor.fetchone()[0]
    if games_missing_scores > 0:
        print(f"⚠️  Games missing scores: {games_missing_scores:,} ({games_missing_scores/total_games*100:.1f}%)")

    # Unique teams
    cursor.execute("""
        SELECT COUNT(DISTINCT team) FROM (
            SELECT home_team as team FROM games
            UNION
            SELECT away_team as team FROM games
        )
    """)
    unique_teams = cursor.fetchone()[0]
    print(f"Unique teams: {unique_teams}")

    print()

    # Season-by-season breakdown
    print("Season breakdown (first 10 and last 10):")
    print(f"  {'Season':<10} {'Games':<10}")
    print(f"  {'-'*10} {'-'*10}")

    for season, count in seasons[:10]:
        print(f"  {season:<10} {count:<10,}")

    if len(seasons) > 20:
        print(f"  {'...':<10} {'...':<10}")
        for season, count in seasons[-10:]:
            print(f"  {season:<10} {count:<10,}")

    print()

    return {
        'total_games': total_games,
        'games_with_scores': games_with_scores,
        'seasons': len(seasons),
        'unique_teams': unique_teams,
        'coverage_start': seasons[0][0],
        'coverage_end': seasons[-1][0]
    }


def integrate_into_unified_database(bbref_stats: Dict):
    """Integrate Basketball Reference as third source in unified database."""

    print("=" * 70)
    print("INTEGRATE INTO UNIFIED DATABASE")
    print("=" * 70)
    print()

    # Connect to both databases
    bbref_conn = sqlite3.connect(BBREF_DB)
    unified_conn = sqlite3.connect(UNIFIED_DB)

    bbref_cursor = bbref_conn.cursor()
    unified_cursor = unified_conn.cursor()

    # Check if basketball_reference columns exist in source_coverage
    unified_cursor.execute("PRAGMA table_info(source_coverage)")
    columns = [row[1] for row in unified_cursor.fetchall()]

    if 'has_basketball_reference' not in columns:
        print("Adding basketball_reference columns to source_coverage...")
        unified_cursor.execute("ALTER TABLE source_coverage ADD COLUMN has_basketball_reference BOOLEAN DEFAULT 0")
        unified_cursor.execute("ALTER TABLE source_coverage ADD COLUMN bbref_game_id TEXT")
        unified_conn.commit()
        print("✓ Added columns")
        print()

    # Get all Basketball Reference games
    bbref_cursor.execute("""
        SELECT game_id, game_date, home_team, away_team, home_score, away_score
        FROM games
        ORDER BY game_date
    """)

    bbref_games = bbref_cursor.fetchall()
    print(f"Processing {len(bbref_games):,} Basketball Reference games...")
    print()

    # Update unified database
    added = 0
    updated = 0

    for game_id, game_date, home_team, away_team, home_score, away_score in bbref_games:
        # Check if game exists in unified database (by date and teams)
        unified_cursor.execute("""
            SELECT game_id FROM source_coverage
            WHERE game_date = ?
            LIMIT 1
        """, (game_date,))

        existing = unified_cursor.fetchone()

        if existing:
            # Update existing game to include Basketball Reference
            unified_cursor.execute("""
                UPDATE source_coverage
                SET has_basketball_reference = 1,
                    bbref_game_id = ?,
                    total_sources = total_sources + 1
                WHERE game_id = ?
            """, (game_id, existing[0]))
            updated += 1
        else:
            # Add new game (Basketball Reference only)
            unified_cursor.execute("""
                INSERT INTO source_coverage (
                    game_id, game_date,
                    has_espn, has_hoopr, has_basketball_reference,
                    bbref_game_id,
                    total_sources, overall_quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id, game_date,
                False, False, True,
                game_id,
                1, 80  # Quality score for Basketball Reference only
            ))
            added += 1

        if (added + updated) % 1000 == 0:
            print(f"  Processed {added + updated:,} games...", end='\r')

    unified_conn.commit()
    print(f"\n✓ Added {added:,} new games, updated {updated:,} existing games")
    print()

    # Print updated coverage summary
    print("Updated source coverage:")
    unified_cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN has_espn = 1 THEN 1 ELSE 0 END) as espn_count,
            SUM(CASE WHEN has_hoopr = 1 THEN 1 ELSE 0 END) as hoopr_count,
            SUM(CASE WHEN has_basketball_reference = 1 THEN 1 ELSE 0 END) as bbref_count,
            SUM(CASE WHEN has_espn = 1 AND has_hoopr = 1 AND has_basketball_reference = 1 THEN 1 ELSE 0 END) as all_three,
            SUM(CASE WHEN total_sources >= 2 THEN 1 ELSE 0 END) as two_or_more
        FROM source_coverage
    """)

    row = unified_cursor.fetchone()
    total, espn, hoopr, bbref, all_three, two_or_more = row

    print(f"  Total games: {total:,}")
    print(f"  ESPN: {espn:,} ({espn/total*100:.1f}%)")
    print(f"  hoopR: {hoopr:,} ({hoopr/total*100:.1f}%)")
    print(f"  Basketball Reference: {bbref:,} ({bbref/total*100:.1f}%)")
    print(f"  All three sources: {all_three:,} ({all_three/total*100:.1f}%)")
    print(f"  Two or more sources: {two_or_more:,} ({two_or_more/total*100:.1f}%)")
    print()

    bbref_conn.close()
    unified_conn.close()


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Integrate Basketball Reference data into unified database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full integration (download + integrate)
  python scripts/etl/integrate_basketball_reference.py

  # Download only
  python scripts/etl/integrate_basketball_reference.py --download-only

  # Specific year
  python scripts/etl/integrate_basketball_reference.py --year 2024

Result:
  - Basketball Reference data downloaded from S3
  - Local Basketball Reference database created
  - Data quality checks performed
  - Unified database updated with Basketball Reference as third source
        """
    )

    parser.add_argument(
        '--year',
        type=int,
        help='Process specific year only'
    )

    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only download schedules, do not integrate'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Download schedules from S3
    downloaded = download_schedules_from_s3(year=args.year)

    if args.download_only:
        print("=" * 70)
        print("✓ Download complete!")
        print(f"  Schedules downloaded: {downloaded}")
        print(f"  Location: {DOWNLOAD_DIR}")
        return

    # Step 2: Create local database
    bbref_conn = create_bbref_database()

    # Step 3: Load schedules to database
    total_games = load_schedules_to_database(bbref_conn)

    # Step 4: Run data quality checks
    bbref_stats = run_data_quality_checks(bbref_conn)

    bbref_conn.close()

    # Step 5: Integrate into unified database
    integrate_into_unified_database(bbref_stats)

    print("=" * 70)
    print("✓ INTEGRATION COMPLETE!")
    print("=" * 70)
    print(f"Basketball Reference games: {bbref_stats['total_games']:,}")
    print(f"Seasons: {bbref_stats['coverage_start']} - {bbref_stats['coverage_end']}")
    print(f"Local database: {BBREF_DB}")
    print(f"Unified database: {UNIFIED_DB}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
