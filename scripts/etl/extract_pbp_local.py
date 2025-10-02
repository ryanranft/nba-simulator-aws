#!/usr/bin/env python3
"""
Local ETL Script: Extract NBA Play-by-Play Data from S3 to RDS

Extracts 10% of relevant fields from ESPN JSON pbp files.
Reads directly from S3 and writes to RDS PostgreSQL (no Glue required).

Input: s3://nba-sim-raw-data-lake/pbp/*.json
Output: RDS PostgreSQL table: play_by_play

Usage:
    python scripts/etl/extract_pbp_local.py --year 1997
    python scripts/etl/extract_pbp_local.py --year-range 1997-2025

Prerequisites:
    - source /Users/ryanranft/nba-sim-credentials.env
    - pip install boto3 psycopg2-binary

Author: Ryan Ranft
Date: 2025-10-02
Phase: 2.3 - Local ETL for PBP data
"""

import json
import os
import sys
import argparse
from typing import List, Dict
import boto3
import psycopg2
from psycopg2.extras import execute_values

# Configuration from environment
S3_BUCKET = os.environ.get('S3_RAW_DATA_BUCKET', 'nba-sim-raw-data-lake')
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', '5432')

def validate_environment():
    """Ensure all required environment variables are set"""
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print("ERROR: Required environment variables not set:")
        for var in missing:
            print(f"  - {var}")
        print("\nRun: source /Users/ryanranft/nba-sim-credentials.env")
        sys.exit(1)

def get_game_ids_for_year(year: int, cursor) -> List[str]:
    """Get list of game IDs for a specific year from database"""
    # Query games table for game IDs from this year
    query = """
        SELECT game_id
        FROM games
        WHERE game_date >= %s AND game_date < %s
        ORDER BY game_date
    """
    cursor.execute(query, (f'{year}-01-01', f'{year+1}-01-01'))
    return [row[0] for row in cursor.fetchall()]

def extract_pbp_data(json_content: dict, game_id: str) -> List[Dict]:
    """
    Extract play-by-play data from ESPN JSON structure

    Returns list of play records
    """
    plays_list = []

    try:
        # Navigate to gamepackage.pbp
        if 'page' not in json_content:
            return plays_list

        page = json_content['page']
        content = page.get('content', {})
        gamepackage = content.get('gamepackage', {})
        pbp = gamepackage.get('pbp', {})

        play_groups = pbp.get('playGrps', [])

        if not play_groups:
            return plays_list

        # Each play_group is a list of plays for a period (quarter)
        for period_plays in play_groups:
            if not isinstance(period_plays, list):
                continue

            for play in period_plays:
                play_id = play.get('id')
                if not play_id:
                    continue

                period = play.get('period', {})
                period_number = period.get('number')
                period_display = period.get('displayValue')

                clock = play.get('clock', {})
                clock_display = clock.get('displayValue')

                play_record = {
                    'play_id': str(play_id),
                    'game_id': str(game_id),
                    'period_number': period_number,
                    'period_display': period_display,
                    'clock_display': clock_display,
                    'play_text': play.get('text'),
                    'home_away': play.get('homeAway'),
                    'scoring_play': play.get('scoringPlay', False),
                    'away_score': play.get('awayScore'),
                    'home_score': play.get('homeScore'),
                }
                plays_list.append(play_record)

    except Exception as e:
        print(f"  Warning: Error extracting PBP data from game {game_id}: {e}")

    return plays_list

def process_year(year: int, dry_run: bool = False) -> Dict:
    """
    Process all pbp files for games in a given year

    Returns: {'processed': int, 'inserted': int, 'skipped': int, 'errors': int}
    """
    print(f"\n{'='*80}")
    print(f"Processing Year: {year}")
    print(f"{'='*80}\n")

    # Connect to database first to get game IDs
    if not dry_run:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            cursor = conn.cursor()
            print(f"✅ Connected to database: {DB_HOST}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return {'processed': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}

    # Get game IDs for this year from database
    print("Fetching game IDs from database...")
    game_ids = get_game_ids_for_year(year, cursor)

    if not game_ids:
        print(f"⚠️  No games found for year {year}")
        if not dry_run:
            cursor.close()
            conn.close()
        return {'processed': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}

    print(f"Found {len(game_ids)} games for year {year}")

    # Connect to S3
    s3 = boto3.client('s3')

    # Process each game's PBP file
    stats = {'processed': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}
    plays_to_insert = []

    for i, game_id in enumerate(game_ids, 1):
        s3_key = f"pbp/{game_id}.json"

        try:
            # Download and parse JSON
            response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            json_content = json.loads(response['Body'].read())

            # Extract play-by-play data
            plays_from_game = extract_pbp_data(json_content, game_id)

            if plays_from_game:
                plays_to_insert.extend(plays_from_game)
                stats['processed'] += len(plays_from_game)
            else:
                stats['skipped'] += 1

            # Progress update every 100 games
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(game_ids)} games | {len(plays_to_insert)} plays extracted")

        except Exception as e:
            if "NoSuchKey" not in str(e):
                print(f"  ❌ Error processing {s3_key}: {e}")
            stats['errors'] += 1

    print(f"\nExtraction complete: {len(plays_to_insert)} plays ready to insert")

    # Deduplicate plays by play_id
    seen_ids = set()
    unique_plays = []
    for play in plays_to_insert:
        if play['play_id'] not in seen_ids:
            seen_ids.add(play['play_id'])
            unique_plays.append(play)

    if len(plays_to_insert) != len(unique_plays):
        print(f"⚠️  Removed {len(plays_to_insert) - len(unique_plays)} duplicate play_ids")
        plays_to_insert = unique_plays

    # Insert into database (batch)
    if not dry_run and plays_to_insert:
        try:
            insert_query = """
                INSERT INTO play_by_play (play_id, game_id, period_number, period_display,
                                         clock_display, play_text, home_away, scoring_play,
                                         away_score, home_score)
                VALUES %s
                ON CONFLICT (play_id) DO UPDATE SET
                    period_number = EXCLUDED.period_number,
                    period_display = EXCLUDED.period_display,
                    clock_display = EXCLUDED.clock_display,
                    play_text = EXCLUDED.play_text,
                    home_away = EXCLUDED.home_away,
                    scoring_play = EXCLUDED.scoring_play,
                    away_score = EXCLUDED.away_score,
                    home_score = EXCLUDED.home_score,
                    updated_at = CURRENT_TIMESTAMP
            """

            values = [
                (
                    play['play_id'],
                    play['game_id'],
                    play['period_number'],
                    play['period_display'],
                    play['clock_display'],
                    play['play_text'],
                    play['home_away'],
                    play['scoring_play'],
                    play['away_score'],
                    play['home_score']
                )
                for play in plays_to_insert
            ]

            execute_values(cursor, insert_query, values)
            conn.commit()

            stats['inserted'] = len(plays_to_insert)
            print(f"✅ Inserted {stats['inserted']} plays into database")

        except Exception as e:
            print(f"❌ Database insert failed: {e}")
            conn.rollback()
            stats['errors'] += stats['processed']
            stats['inserted'] = 0
        finally:
            cursor.close()
            conn.close()

    elif dry_run:
        print(f"🔍 DRY RUN: Would insert {len(plays_to_insert)} plays")
        if plays_to_insert:
            print("\nSample play data:")
            print(json.dumps(plays_to_insert[0], indent=2))

    return stats

def main():
    parser = argparse.ArgumentParser(description='Extract NBA play-by-play data from S3 to RDS PostgreSQL')
    parser.add_argument('--year', type=int, help='Process single year (e.g., 1997)')
    parser.add_argument('--year-range', type=str, help='Process year range (e.g., 1997-2025)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without inserting')

    args = parser.parse_args()

    # Validate environment
    validate_environment()

    # Determine years to process
    years = []
    if args.year:
        years = [args.year]
    elif args.year_range:
        start_year, end_year = map(int, args.year_range.split('-'))
        years = list(range(start_year, end_year + 1))
    else:
        print("ERROR: Must specify --year or --year-range")
        sys.exit(1)

    # Process each year
    total_stats = {'processed': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}

    for year in years:
        stats = process_year(year, dry_run=args.dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]

    # Summary
    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"Years processed: {len(years)}")
    print(f"Plays processed: {total_stats['processed']}")
    print(f"Plays inserted: {total_stats['inserted']}")
    print(f"Games skipped: {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")
    print()

if __name__ == '__main__':
    main()