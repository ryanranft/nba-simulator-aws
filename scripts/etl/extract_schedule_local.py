#!/usr/bin/env python3
"""
Local ETL Script: Extract NBA Schedule Data from S3 to RDS

Extracts 10% of relevant fields from ESPN JSON schedule files.
Reads directly from S3 and writes to RDS PostgreSQL (no Glue required).

Input: s3://nba-sim-raw-data-lake/espn_schedules/*.json
Output: RDS PostgreSQL table: games

Usage:
    python scripts/etl/extract_schedule_local.py --year 1993
    python scripts/etl/extract_schedule_local.py --year-range 1993-2025

Prerequisites:
    - source /Users/ryanranft/nba-sim-credentials.env
    - pip install boto3 psycopg2-binary

Author: Ryan Ranft
Date: 2025-10-02
Phase: 2.2 - Local ETL (Alternative to Glue)
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional
import boto3
import psycopg2
from psycopg2.extras import execute_values

# Configuration from environment
S3_BUCKET = os.environ.get("S3_RAW_DATA_BUCKET", "nba-sim-raw-data-lake")
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")


def validate_environment():
    """Ensure all required environment variables are set"""
    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print("ERROR: Required environment variables not set:")
        for var in missing:
            print(f"  - {var}")
        print("\nRun: source /Users/ryanranft/nba-sim-credentials.env")
        sys.exit(1)


def get_s3_files_for_year(year: int) -> List[str]:
    """Get list of schedule JSON files for a specific year from S3"""
    s3 = boto3.client("s3")
    prefix = "espn_schedules/"

    # List all schedule files
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)

    files = []
    year_str = str(year)  # e.g., "1993"

    for page in pages:
        if "Contents" not in page:
            continue

        for obj in page["Contents"]:
            key = obj["Key"]
            # Schedule files are named like "YYYYMMDD.json" or "19931105.json"
            # Filter by year prefix
            filename = key.split("/")[-1]
            if filename.startswith(year_str) and filename.endswith(".json"):
                files.append(key)

    return sorted(files)


def extract_teams_data(json_content: dict) -> List[Dict]:
    """
    Extract team data from ESPN JSON structure

    Returns list of team dicts
    """
    teams = []
    try:
        if "page" not in json_content:
            return teams

        page = json_content["page"]

        # Try different JSON structures
        events = None
        if "content" in page and "schedule" in page["content"]:
            events = page["content"]["schedule"]
        elif "content" in page and "events" in page["content"]:
            events = page["content"]["events"]

        if not events:
            return teams

        # Events may be dict by date or list
        if isinstance(events, dict):
            for date_key, date_games in events.items():
                if isinstance(date_games, list) and len(date_games) > 0:
                    events = date_games
                    break

        if not isinstance(events, list) or len(events) == 0:
            return teams

        game = events[0]
        competitors = game.get("competitors", [])

        for team in competitors:
            team_data = {
                "team_id": str(team.get("id", "")),
                "team_name": team.get("displayName", ""),
                "team_abbrev": team.get("abbreviation", ""),
                "team_city": None,  # Not always available in schedule files
                "team_conference": None,
                "team_division": None,
            }
            if team_data["team_id"]:
                teams.append(team_data)

    except Exception as e:
        pass  # Silently skip extraction errors for teams

    return teams


def extract_game_data(json_content: dict) -> List[Dict]:
    """
    Extract ALL game data from ESPN JSON structure

    Returns list of game record dicts (may be empty if no valid data)
    """
    games_list = []

    try:
        # Navigate to page.content.schedule (for schedule files)
        if "page" not in json_content:
            return games_list

        page = json_content["page"]

        # Try different JSON structures (ESPN format varies)
        events = None
        if "content" in page and "schedule" in page["content"]:
            # Schedule file structure
            events = page["content"]["schedule"]
        elif "content" in page and "events" in page["content"]:
            # Alternative structure
            events = page["content"]["events"]

        if not events:
            return games_list

        # Events may be dict by date or list
        all_games = []
        if isinstance(events, dict):
            # Loop through ALL dates and collect ALL games
            for date_key, date_games in events.items():
                if isinstance(date_games, list):
                    all_games.extend(date_games)
        elif isinstance(events, list):
            all_games = events

        if len(all_games) == 0:
            return games_list

        # Extract ALL games (not just first one)
        for game in all_games:
            # Extract basic game info
            game_id = game.get("id")
            if not game_id:
                continue  # Skip games without ID

            game_date = game.get("date")

            # Extract teams
            competitors = game.get("competitors", [])
            if len(competitors) < 2:
                continue  # Skip games without both teams

            # Find home and away teams
            home_team = None
            away_team = None

            for team in competitors:
                if team.get("homeAway") == "home" or team.get("isHome"):
                    home_team = team
                else:
                    away_team = team

            if not home_team or not away_team:
                # Fallback: assume first is home, second is away
                home_team = competitors[0]
                away_team = competitors[1]

            # Extract venue
            venue = game.get("venue", {})
            venue_name = venue.get("fullName")

            # Extract scores (may be None if game not played yet)
            home_score = None
            away_score = None

            if "score" in home_team and home_team["score"]:
                home_score = int(home_team["score"])
            if "score" in away_team and away_team["score"]:
                away_score = int(away_team["score"])

            # Extract status
            status = game.get("status", {})
            game_status = status.get("type", {}).get("detail", "Unknown")

            # Determine season (year from game_id or date)
            season = None
            if game_date:
                try:
                    date_obj = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
                    # NBA season typically spans Oct-June, use start year
                    season_year = (
                        date_obj.year if date_obj.month >= 10 else date_obj.year - 1
                    )
                    season = f"{season_year}-{str(season_year + 1)[2:]}"
                except:
                    pass

            # Parse game time
            game_time = None
            if game_date:
                try:
                    game_time = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
                except:
                    pass

            # Extract broadcast info
            broadcasts = game.get("broadcasts", [])
            broadcast_name = None
            broadcast_market = None
            broadcast_type = None
            if broadcasts:
                # Prioritize National > Home > any
                national = next(
                    (b for b in broadcasts if b.get("market") == "National"), None
                )
                home_broadcast = next(
                    (b for b in broadcasts if b.get("market") == "Home"), None
                )
                selected = national or home_broadcast or broadcasts[0]
                broadcast_name = selected.get("name")
                broadcast_market = selected.get("market")
                broadcast_type = selected.get("type")

            # Extract home team leader
            home_leader = home_team.get("leader", {})
            home_leader_name = home_leader.get("name")
            home_leader_stat = home_leader.get("displayValue")

            # Extract away team leader
            away_leader = away_team.get("leader", {})
            away_leader_name = away_leader.get("name")
            away_leader_stat = away_leader.get("displayValue")

            # Extract venue details
            venue_address = venue.get("address", {})

            game_record = {
                "game_id": str(game_id),
                "game_date": game_date.split("T")[0] if game_date else None,
                "game_time": game_time,
                "season": season,
                # Home team fields
                "home_team_id": str(home_team.get("id", "")),
                "home_team_abbrev": home_team.get("abbrev"),
                "home_team_name": home_team.get("displayName"),
                "home_team_short_name": home_team.get("shortDisplayName"),
                "home_team_logo": home_team.get("logo"),
                "home_team_color": home_team.get("teamColor"),
                "home_team_alt_color": home_team.get("altColor"),
                "home_team_uid": home_team.get("uid"),
                "home_team_record_summary": home_team.get("recordSummary"),
                "home_team_standing_summary": home_team.get("standingSummary"),
                "home_team_location": home_team.get("location"),
                "home_score": home_score,
                "home_team_is_winner": home_team.get("winner", False),
                "home_team_leader_name": home_leader_name,
                "home_team_leader_stat": home_leader_stat,
                # Away team fields
                "away_team_id": str(away_team.get("id", "")),
                "away_team_abbrev": away_team.get("abbrev"),
                "away_team_name": away_team.get("displayName"),
                "away_team_short_name": away_team.get("shortDisplayName"),
                "away_team_logo": away_team.get("logo"),
                "away_team_color": away_team.get("teamColor"),
                "away_team_alt_color": away_team.get("altColor"),
                "away_team_uid": away_team.get("uid"),
                "away_team_record_summary": away_team.get("recordSummary"),
                "away_team_standing_summary": away_team.get("standingSummary"),
                "away_team_location": away_team.get("location"),
                "away_score": away_score,
                "away_team_is_winner": away_team.get("winner", False),
                "away_team_leader_name": away_leader_name,
                "away_team_leader_stat": away_leader_stat,
                # Venue fields
                "venue": venue_name,
                "venue_id": str(venue.get("id", "")),
                "venue_city": venue_address.get("city"),
                "venue_state": venue_address.get("state"),
                "venue_country": venue_address.get("country"),
                "venue_indoor": venue.get("indoor"),
                # Status fields
                "game_status": game_status,
                "status_id": str(status.get("id", "")),
                "status_state": status.get("state"),
                "status_detail": status.get("type", {}).get("detail"),
                # Broadcast fields
                "broadcast_name": broadcast_name,
                "broadcast_market": broadcast_market,
                "broadcast_type": broadcast_type,
                "broadcast_count": len(broadcasts),
                # Metadata fields
                "completed": game.get("completed"),
                "is_tie": game.get("isTie"),
                "periods": game.get("format", {})
                .get("regulation", {})
                .get("periods", 4),
                "time_valid": game.get("timeValid", True),
                "game_link": game.get("link"),
                "header_postfix": game.get("headerPostfix", ""),
                "has_tickets": bool(game.get("tickets")),
            }
            games_list.append(game_record)

    except Exception as e:
        print(f"  Warning: Error extracting game data: {e}")

    return games_list


def process_year(year: int, dry_run: bool = False) -> Dict:
    """
    Process all schedule files for a given year

    Returns: {'processed': int, 'inserted': int, 'skipped': int, 'errors': int}
    """
    print(f"\n{'='*80}")
    print(f"Processing Year: {year}")
    print(f"{'='*80}\n")

    # Get S3 files for this year
    print("Fetching S3 file list...")
    s3_files = get_s3_files_for_year(year)

    if not s3_files:
        print(f"⚠️  No schedule files found for year {year}")
        return {"processed": 0, "inserted": 0, "skipped": 0, "errors": 0}

    print(f"Found {len(s3_files)} schedule files for year {year}")

    # Connect to S3 and database
    s3 = boto3.client("s3")

    if not dry_run:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
            )
            cursor = conn.cursor()
            print(f"✅ Connected to database: {DB_HOST}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return {"processed": 0, "inserted": 0, "skipped": 0, "errors": 0}

    # Process each file
    stats = {"processed": 0, "inserted": 0, "skipped": 0, "errors": 0}
    games_to_insert = []

    for i, s3_key in enumerate(s3_files, 1):
        try:
            # Download and parse JSON
            response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            json_content = json.loads(response["Body"].read())

            # Extract game data (returns list of games)
            games_from_file = extract_game_data(json_content)

            if games_from_file:
                games_to_insert.extend(games_from_file)  # Extend, not append
                stats["processed"] += len(games_from_file)
            else:
                stats["skipped"] += 1

            # Progress update every 100 files
            if i % 100 == 0:
                print(
                    f"  Progress: {i}/{len(s3_files)} files | {len(games_to_insert)} games extracted"
                )

        except Exception as e:
            print(f"  ❌ Error processing {s3_key}: {e}")
            stats["errors"] += 1

    print(f"\nExtraction complete: {len(games_to_insert)} games ready to insert")

    # Deduplicate games by game_id (keep first occurrence)
    seen_ids = set()
    unique_games = []
    for game in games_to_insert:
        if game["game_id"] not in seen_ids:
            seen_ids.add(game["game_id"])
            unique_games.append(game)

    if len(games_to_insert) != len(unique_games):
        print(
            f"⚠️  Removed {len(games_to_insert) - len(unique_games)} duplicate game_ids"
        )
        games_to_insert = unique_games

    # Auto-insert missing team IDs before inserting games
    if not dry_run and games_to_insert:
        try:
            # Collect all unique team IDs from games
            team_ids = set()
            for game in games_to_insert:
                if game["home_team_id"]:
                    team_ids.add(game["home_team_id"])
                if game["away_team_id"]:
                    team_ids.add(game["away_team_id"])

            # Insert missing teams (ON CONFLICT DO NOTHING to skip existing)
            for team_id in team_ids:
                cursor.execute(
                    """
                    INSERT INTO teams (team_id, team_name, team_abbreviation)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (team_id) DO NOTHING
                """,
                    (team_id, f"Team {team_id}", f"T{team_id}"),
                )

            conn.commit()
            print(f"  ✓ Ensured {len(team_ids)} team IDs exist in teams table")

        except Exception as e:
            print(f"  ⚠️  Warning: Could not auto-insert teams: {e}")
            conn.rollback()

    # Insert into database (batch) with ALL 53 fields
    if not dry_run and games_to_insert:
        try:
            insert_query = """
                INSERT INTO games (
                    game_id, game_date, game_time, season,
                    home_team_id, home_team_abbrev, home_team_name, home_team_short_name,
                    home_team_logo, home_team_color, home_team_alt_color, home_team_uid,
                    home_team_record_summary, home_team_standing_summary, home_team_location,
                    home_score, home_team_is_winner, home_team_leader_name, home_team_leader_stat,
                    away_team_id, away_team_abbrev, away_team_name, away_team_short_name,
                    away_team_logo, away_team_color, away_team_alt_color, away_team_uid,
                    away_team_record_summary, away_team_standing_summary, away_team_location,
                    away_score, away_team_is_winner, away_team_leader_name, away_team_leader_stat,
                    venue, venue_id, venue_city, venue_state, venue_country, venue_indoor,
                    game_status, status_id, status_state, status_detail,
                    broadcast_name, broadcast_market, broadcast_type, broadcast_count,
                    completed, is_tie, periods, time_valid, game_link, header_postfix, has_tickets
                )
                VALUES %s
                ON CONFLICT (game_id) DO UPDATE SET
                    game_date = EXCLUDED.game_date,
                    game_time = EXCLUDED.game_time,
                    season = EXCLUDED.season,
                    home_team_abbrev = EXCLUDED.home_team_abbrev,
                    home_team_name = EXCLUDED.home_team_name,
                    home_score = EXCLUDED.home_score,
                    away_team_abbrev = EXCLUDED.away_team_abbrev,
                    away_team_name = EXCLUDED.away_team_name,
                    away_score = EXCLUDED.away_score,
                    venue = EXCLUDED.venue,
                    game_status = EXCLUDED.game_status,
                    broadcast_name = EXCLUDED.broadcast_name,
                    completed = EXCLUDED.completed,
                    updated_at = CURRENT_TIMESTAMP
            """

            values = [
                (
                    game["game_id"],
                    game["game_date"],
                    game["game_time"],
                    game["season"],
                    game["home_team_id"],
                    game["home_team_abbrev"],
                    game["home_team_name"],
                    game["home_team_short_name"],
                    game["home_team_logo"],
                    game["home_team_color"],
                    game["home_team_alt_color"],
                    game["home_team_uid"],
                    game["home_team_record_summary"],
                    game["home_team_standing_summary"],
                    game["home_team_location"],
                    game["home_score"],
                    game["home_team_is_winner"],
                    game["home_team_leader_name"],
                    game["home_team_leader_stat"],
                    game["away_team_id"],
                    game["away_team_abbrev"],
                    game["away_team_name"],
                    game["away_team_short_name"],
                    game["away_team_logo"],
                    game["away_team_color"],
                    game["away_team_alt_color"],
                    game["away_team_uid"],
                    game["away_team_record_summary"],
                    game["away_team_standing_summary"],
                    game["away_team_location"],
                    game["away_score"],
                    game["away_team_is_winner"],
                    game["away_team_leader_name"],
                    game["away_team_leader_stat"],
                    game["venue"],
                    game["venue_id"],
                    game["venue_city"],
                    game["venue_state"],
                    game["venue_country"],
                    game["venue_indoor"],
                    game["game_status"],
                    game["status_id"],
                    game["status_state"],
                    game["status_detail"],
                    game["broadcast_name"],
                    game["broadcast_market"],
                    game["broadcast_type"],
                    game["broadcast_count"],
                    game["completed"],
                    game["is_tie"],
                    game["periods"],
                    game["time_valid"],
                    game["game_link"],
                    game["header_postfix"],
                    game["has_tickets"],
                )
                for game in games_to_insert
            ]

            execute_values(cursor, insert_query, values)
            conn.commit()

            stats["inserted"] = len(games_to_insert)
            print(
                f"✅ Inserted {stats['inserted']} games with full metadata into database"
            )

        except Exception as e:
            print(f"❌ Database insert failed: {e}")
            conn.rollback()
            stats["errors"] += stats["processed"]
            stats["inserted"] = 0
        finally:
            cursor.close()
            conn.close()

    elif dry_run:
        print(f"🔍 DRY RUN: Would insert {len(games_to_insert)} games")
        if games_to_insert:
            print("\nSample game data:")
            print(json.dumps(games_to_insert[0], indent=2))

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Extract NBA schedule data from S3 to RDS PostgreSQL"
    )
    parser.add_argument("--year", type=int, help="Process single year (e.g., 1993)")
    parser.add_argument(
        "--year-range", type=str, help="Process year range (e.g., 1993-2025)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without inserting",
    )

    args = parser.parse_args()

    # Validate environment
    validate_environment()

    # Determine years to process
    years = []
    if args.year:
        years = [args.year]
    elif args.year_range:
        start_year, end_year = map(int, args.year_range.split("-"))
        years = list(range(start_year, end_year + 1))
    else:
        print("ERROR: Must specify --year or --year-range")
        sys.exit(1)

    # Process each year
    total_stats = {"processed": 0, "inserted": 0, "skipped": 0, "errors": 0}

    for year in years:
        stats = process_year(year, dry_run=args.dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]

    # Summary
    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"Years processed: {len(years)}")
    print(f"Files processed: {total_stats['processed']}")
    print(f"Games inserted: {total_stats['inserted']}")
    print(f"Files skipped: {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")
    print()


if __name__ == "__main__":
    main()
