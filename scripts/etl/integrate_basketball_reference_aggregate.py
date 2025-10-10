#!/usr/bin/env python3
"""
Integrate Basketball Reference Aggregate Data into Unified Database

Downloads Basketball Reference aggregate data (season totals, advanced totals,
standings) from S3 and integrates into unified database with data validation.

Data types:
- Season Totals: Basic counting stats (points, rebounds, assists, etc.)
- Advanced Totals: Advanced metrics (PER, Win Shares, BPM, VORP, TS%, etc.)
- Standings: Team records by season (wins, losses, division, conference)

Usage:
    python scripts/etl/integrate_basketball_reference_aggregate.py
    python scripts/etl/integrate_basketball_reference_aggregate.py --data-type advanced
    python scripts/etl/integrate_basketball_reference_aggregate.py --validate-only

Created: October 10, 2025
"""

import sqlite3
import json
import boto3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
from collections import defaultdict

# Database paths
BBREF_AGGREGATE_DB = "/tmp/basketball_reference_aggregate.db"
UNIFIED_DB = "/tmp/unified_nba.db"

# S3 configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIXES = {
    'advanced': 'basketball_reference/advanced_totals/',
    'season': 'basketball_reference/season_totals/',
    'standings': 'basketball_reference/standings/'
}

# Local download path
DOWNLOAD_DIR = Path("/tmp/basketball_reference_aggregate")


def parse_team_name(team_str: str) -> str:
    """Parse Basketball Reference team enum to readable name."""
    if team_str is None:
        return None
    if team_str.startswith("Team."):
        return team_str.replace("Team.", "").replace("_", " ")
    return team_str


def parse_position(pos_str: str) -> str:
    """Parse Basketball Reference position enum."""
    if pos_str is None:
        return None
    if pos_str.startswith("Position."):
        return pos_str.replace("Position.", "").replace("_", " ")
    return pos_str


def download_aggregate_data_from_s3(data_type: Optional[str] = None):
    """Download Basketball Reference aggregate data from S3."""

    print("=" * 70)
    print("DOWNLOAD BASKETBALL REFERENCE AGGREGATE DATA FROM S3")
    print("=" * 70)
    print()

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client('s3')

    # Determine which data types to download
    if data_type:
        data_types = {data_type: S3_PREFIXES[data_type]}
    else:
        data_types = S3_PREFIXES

    total_downloaded = 0

    for dtype, prefix in data_types.items():
        print(f"Downloading {dtype} data...")

        # List all years
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix, Delimiter='/')

        years = []
        if 'CommonPrefixes' in response:
            for prefix_obj in response['CommonPrefixes']:
                year_str = prefix_obj['Prefix'].split('/')[-2]
                try:
                    years.append(int(year_str))
                except ValueError:
                    continue

        years.sort()
        print(f"  Found {len(years)} years: {min(years)} - {max(years)}")

        # Download files for each year
        downloaded = 0
        for year in years:
            s3_prefix = f"{prefix}{year}/"
            local_year_dir = DOWNLOAD_DIR / dtype / str(year)
            local_year_dir.mkdir(parents=True, exist_ok=True)

            # List files in year directory
            year_response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=s3_prefix)

            if 'Contents' in year_response:
                for obj in year_response['Contents']:
                    s3_key = obj['Key']
                    filename = s3_key.split('/')[-1]
                    local_path = local_year_dir / filename

                    try:
                        s3.download_file(S3_BUCKET, s3_key, str(local_path))
                        downloaded += 1
                    except Exception as e:
                        print(f"    ⚠️  Failed to download {year}/{filename}: {e}")

        print(f"  ✓ Downloaded {downloaded} files for {dtype}")
        total_downloaded += downloaded
        print()

    print(f"✓ Total files downloaded: {total_downloaded}")
    print()

    return total_downloaded


def create_aggregate_database():
    """Create Basketball Reference aggregate database."""

    print("=" * 70)
    print("CREATE BASKETBALL REFERENCE AGGREGATE DATABASE")
    print("=" * 70)
    print()

    conn = sqlite3.connect(BBREF_AGGREGATE_DB)
    cursor = conn.cursor()

    # Create player_season_totals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_season_totals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            player_slug TEXT NOT NULL,
            player_name TEXT,
            position TEXT,
            age INTEGER,
            team TEXT,
            games_played INTEGER,
            games_started INTEGER,
            minutes_played INTEGER,
            made_field_goals INTEGER,
            attempted_field_goals INTEGER,
            made_three_point_field_goals INTEGER,
            attempted_three_point_field_goals INTEGER,
            made_free_throws INTEGER,
            attempted_free_throws INTEGER,
            offensive_rebounds INTEGER,
            defensive_rebounds INTEGER,
            total_rebounds INTEGER,
            assists INTEGER,
            steals INTEGER,
            blocks INTEGER,
            turnovers INTEGER,
            personal_fouls INTEGER,
            points INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, player_slug, team)
        )
    """)

    # Create player_advanced_totals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_advanced_totals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            player_slug TEXT NOT NULL,
            player_name TEXT,
            position TEXT,
            age INTEGER,
            team TEXT,
            games_played INTEGER,
            minutes_played INTEGER,
            player_efficiency_rating REAL,
            true_shooting_percentage REAL,
            three_point_attempt_rate REAL,
            free_throw_attempt_rate REAL,
            offensive_rebound_percentage REAL,
            defensive_rebound_percentage REAL,
            total_rebound_percentage REAL,
            assist_percentage REAL,
            steal_percentage REAL,
            block_percentage REAL,
            turnover_percentage REAL,
            usage_percentage REAL,
            offensive_win_shares REAL,
            defensive_win_shares REAL,
            win_shares REAL,
            win_shares_per_48_minutes REAL,
            offensive_box_plus_minus REAL,
            defensive_box_plus_minus REAL,
            box_plus_minus REAL,
            value_over_replacement_player REAL,
            is_combined_totals BOOLEAN,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, player_slug, team)
        )
    """)

    # Create team_standings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_standings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER NOT NULL,
            team TEXT NOT NULL,
            wins INTEGER,
            losses INTEGER,
            win_percentage REAL,
            division TEXT,
            conference TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(season, team)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_season_totals_season ON player_season_totals(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_season_totals_player ON player_season_totals(player_slug)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_advanced_totals_season ON player_advanced_totals(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_advanced_totals_player ON player_advanced_totals(player_slug)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_standings_season ON team_standings(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_standings_team ON team_standings(team)")

    conn.commit()
    print("✓ Created tables: player_season_totals, player_advanced_totals, team_standings")
    print("✓ Created indexes for fast lookups")
    print()

    return conn


def load_season_totals_to_database(conn):
    """Load player season totals into database."""

    print("=" * 70)
    print("LOAD SEASON TOTALS TO DATABASE")
    print("=" * 70)
    print()

    cursor = conn.cursor()

    season_dirs = sorted((DOWNLOAD_DIR / 'season').glob('*'))

    if not season_dirs:
        print("⚠️  No season totals files found.")
        return 0

    print(f"Found {len(season_dirs)} seasons")
    print()

    total_players = 0

    for season_dir in season_dirs:
        if not season_dir.is_dir():
            continue

        season = int(season_dir.name)
        json_file = season_dir / 'player_season_totals.json'

        if not json_file.exists():
            continue

        with open(json_file) as f:
            players = json.load(f)

        for player in players:
            cursor.execute("""
                INSERT OR REPLACE INTO player_season_totals (
                    season, player_slug, player_name, position, age, team,
                    games_played, games_started, minutes_played,
                    made_field_goals, attempted_field_goals,
                    made_three_point_field_goals, attempted_three_point_field_goals,
                    made_free_throws, attempted_free_throws,
                    offensive_rebounds, defensive_rebounds, total_rebounds,
                    assists, steals, blocks, turnovers, personal_fouls, points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                season,
                player.get('slug'),
                player.get('name'),
                ','.join([parse_position(p) for p in player.get('positions', [])]),
                player.get('age'),
                parse_team_name(player.get('team', '')),
                player.get('games_played'),
                player.get('games_started'),
                player.get('minutes_played'),
                player.get('made_field_goals'),
                player.get('attempted_field_goals'),
                player.get('made_three_point_field_goals'),
                player.get('attempted_three_point_field_goals'),
                player.get('made_free_throws'),
                player.get('attempted_free_throws'),
                player.get('offensive_rebounds'),
                player.get('defensive_rebounds'),
                player.get('total_rebounds'),
                player.get('assists'),
                player.get('steals'),
                player.get('blocks'),
                player.get('turnovers'),
                player.get('personal_fouls'),
                player.get('points')
            ))

            total_players += 1

        if (season_dirs.index(season_dir) + 1) % 10 == 0:
            print(f"  Processed {season_dirs.index(season_dir) + 1}/{len(season_dirs)} seasons...", end='\r')

    conn.commit()
    print(f"\n✓ Loaded {total_players:,} player season records from {len(season_dirs)} seasons")
    print()

    return total_players


def load_advanced_totals_to_database(conn):
    """Load player advanced totals into database."""

    print("=" * 70)
    print("LOAD ADVANCED TOTALS TO DATABASE")
    print("=" * 70)
    print()

    cursor = conn.cursor()

    advanced_dirs = sorted((DOWNLOAD_DIR / 'advanced').glob('*'))

    if not advanced_dirs:
        print("⚠️  No advanced totals files found.")
        return 0

    print(f"Found {len(advanced_dirs)} seasons")
    print()

    total_players = 0

    for advanced_dir in advanced_dirs:
        if not advanced_dir.is_dir():
            continue

        season = int(advanced_dir.name)
        json_file = advanced_dir / 'player_advanced_totals.json'

        if not json_file.exists():
            continue

        with open(json_file) as f:
            players = json.load(f)

        for player in players:
            cursor.execute("""
                INSERT OR REPLACE INTO player_advanced_totals (
                    season, player_slug, player_name, position, age, team,
                    games_played, minutes_played,
                    player_efficiency_rating, true_shooting_percentage,
                    three_point_attempt_rate, free_throw_attempt_rate,
                    offensive_rebound_percentage, defensive_rebound_percentage, total_rebound_percentage,
                    assist_percentage, steal_percentage, block_percentage,
                    turnover_percentage, usage_percentage,
                    offensive_win_shares, defensive_win_shares, win_shares, win_shares_per_48_minutes,
                    offensive_box_plus_minus, defensive_box_plus_minus, box_plus_minus,
                    value_over_replacement_player, is_combined_totals
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                season,
                player.get('slug'),
                player.get('name'),
                ','.join([parse_position(p) for p in player.get('positions', [])]),
                player.get('age'),
                parse_team_name(player.get('team', '')),
                player.get('games_played'),
                player.get('minutes_played'),
                player.get('player_efficiency_rating'),
                player.get('true_shooting_percentage'),
                player.get('three_point_attempt_rate'),
                player.get('free_throw_attempt_rate'),
                player.get('offensive_rebound_percentage'),
                player.get('defensive_rebound_percentage'),
                player.get('total_rebound_percentage'),
                player.get('assist_percentage'),
                player.get('steal_percentage'),
                player.get('block_percentage'),
                player.get('turnover_percentage'),
                player.get('usage_percentage'),
                player.get('offensive_win_shares'),
                player.get('defensive_win_shares'),
                player.get('win_shares'),
                player.get('win_shares_per_48_minutes'),
                player.get('offensive_box_plus_minus'),
                player.get('defensive_box_plus_minus'),
                player.get('box_plus_minus'),
                player.get('value_over_replacement_player'),
                player.get('is_combined_totals')
            ))

            total_players += 1

        if (advanced_dirs.index(advanced_dir) + 1) % 10 == 0:
            print(f"  Processed {advanced_dirs.index(advanced_dir) + 1}/{len(advanced_dirs)} seasons...", end='\r')

    conn.commit()
    print(f"\n✓ Loaded {total_players:,} player advanced records from {len(advanced_dirs)} seasons")
    print()

    return total_players


def load_standings_to_database(conn):
    """Load team standings into database."""

    print("=" * 70)
    print("LOAD STANDINGS TO DATABASE")
    print("=" * 70)
    print()

    cursor = conn.cursor()

    standings_dirs = sorted((DOWNLOAD_DIR / 'standings').glob('*'))

    if not standings_dirs:
        print("⚠️  No standings files found.")
        return 0

    print(f"Found {len(standings_dirs)} seasons")
    print()

    total_teams = 0

    for standings_dir in standings_dirs:
        if not standings_dir.is_dir():
            continue

        season = int(standings_dir.name)
        json_file = standings_dir / 'standings.json'

        if not json_file.exists():
            continue

        with open(json_file) as f:
            teams = json.load(f)

        for team in teams:
            team_name = parse_team_name(team.get('team'))

            # Skip if no team name (invalid record)
            if not team_name:
                continue

            wins = team.get('wins', 0)
            losses = team.get('losses', 0)
            win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0

            cursor.execute("""
                INSERT OR REPLACE INTO team_standings (
                    season, team, wins, losses, win_percentage, division, conference
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                season,
                team_name,
                wins,
                losses,
                win_pct,
                team.get('division', '').replace('Division.', '').replace('_', ' ') if team.get('division') else None,
                team.get('conference', '').replace('Conference.', '').replace('_', ' ') if team.get('conference') else None
            ))

            total_teams += 1

    conn.commit()
    print(f"✓ Loaded {total_teams:,} team standings from {len(standings_dirs)} seasons")
    print()

    return total_teams


def run_data_quality_checks(conn):
    """Run data quality checks on Basketball Reference aggregate data."""

    print("=" * 70)
    print("DATA QUALITY CHECKS")
    print("=" * 70)
    print()

    cursor = conn.cursor()

    # Season totals checks
    print("📊 SEASON TOTALS:")
    cursor.execute("SELECT COUNT(*) FROM player_season_totals")
    total_season = cursor.fetchone()[0]
    print(f"  Total player-seasons: {total_season:,}")

    cursor.execute("SELECT COUNT(DISTINCT season) FROM player_season_totals")
    seasons_count = cursor.fetchone()[0]
    print(f"  Seasons covered: {seasons_count}")

    cursor.execute("SELECT MIN(season), MAX(season) FROM player_season_totals")
    min_season, max_season = cursor.fetchone()
    print(f"  Season range: {min_season} - {max_season}")

    cursor.execute("SELECT COUNT(DISTINCT player_slug) FROM player_season_totals")
    unique_players = cursor.fetchone()[0]
    print(f"  Unique players: {unique_players:,}")

    # Advanced totals checks
    print(f"\n📊 ADVANCED TOTALS:")
    cursor.execute("SELECT COUNT(*) FROM player_advanced_totals")
    total_advanced = cursor.fetchone()[0]
    print(f"  Total player-seasons: {total_advanced:,}")

    cursor.execute("SELECT COUNT(DISTINCT season) FROM player_advanced_totals")
    seasons_count_adv = cursor.fetchone()[0]
    print(f"  Seasons covered: {seasons_count_adv}")

    cursor.execute("SELECT MIN(season), MAX(season) FROM player_advanced_totals")
    min_season_adv, max_season_adv = cursor.fetchone()
    print(f"  Season range: {min_season_adv} - {max_season_adv}")

    # Standings checks
    print(f"\n📊 STANDINGS:")
    cursor.execute("SELECT COUNT(*) FROM team_standings")
    total_standings = cursor.fetchone()[0]
    print(f"  Total team-seasons: {total_standings:,}")

    cursor.execute("SELECT COUNT(DISTINCT season) FROM team_standings")
    seasons_count_stand = cursor.fetchone()[0]
    print(f"  Seasons covered: {seasons_count_stand}")

    cursor.execute("SELECT MIN(season), MAX(season) FROM team_standings")
    min_season_stand, max_season_stand = cursor.fetchone()
    print(f"  Season range: {min_season_stand} - {max_season_stand}")

    print()

    return {
        'season_totals': total_season,
        'advanced_totals': total_advanced,
        'standings': total_standings,
        'seasons_season': seasons_count,
        'seasons_advanced': seasons_count_adv,
        'seasons_standings': seasons_count_stand
    }


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Integrate Basketball Reference aggregate data into unified database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--data-type',
        choices=['advanced', 'season', 'standings'],
        help='Process specific data type only'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only run data quality checks, do not download or integrate'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not args.validate_only:
        # Step 1: Download aggregate data from S3
        downloaded = download_aggregate_data_from_s3(data_type=args.data_type)

        # Step 2: Create local database
        bbref_conn = create_aggregate_database()

        # Step 3: Load data to database
        if not args.data_type or args.data_type == 'season':
            load_season_totals_to_database(bbref_conn)

        if not args.data_type or args.data_type == 'advanced':
            load_advanced_totals_to_database(bbref_conn)

        if not args.data_type or args.data_type == 'standings':
            load_standings_to_database(bbref_conn)

        # Step 4: Run data quality checks
        stats = run_data_quality_checks(bbref_conn)

        bbref_conn.close()
    else:
        # Validate only mode
        bbref_conn = sqlite3.connect(BBREF_AGGREGATE_DB)
        stats = run_data_quality_checks(bbref_conn)
        bbref_conn.close()

    print("=" * 70)
    print("✓ INTEGRATION COMPLETE!")
    print("=" * 70)
    print(f"Basketball Reference aggregate database: {BBREF_AGGREGATE_DB}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
