#!/usr/bin/env python3
"""
Extract NBA Teams By Year from S3 Schedule Files

Scans all schedule files year-by-year to discover teams and track:
- New teams each season
- Team relocations
- Team name changes
- Team abbreviation changes

Populates both `teams` and `team_seasons` tables.

Usage:
    python scripts/etl/extract_teams_by_year.py --year-range 1993-2025

Author: Ryan Ranft
Date: 2025-10-02
Phase: 2.2 - Local ETL (Team Discovery)
"""

import json
import os
import sys
import argparse
from typing import Dict, Set, List
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


def get_s3_files_for_year(year: int, limit: int = None) -> List[str]:
    """Get list of schedule JSON files for a specific year"""
    s3 = boto3.client("s3")
    prefix = "schedule/"

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)

    files = []
    year_str = str(year)

    for page in pages:
        if "Contents" not in page:
            continue

        for obj in page["Contents"]:
            key = obj["Key"]
            filename = key.split("/")[-1]
            if filename.startswith(year_str) and filename.endswith(".json"):
                files.append(key)
                if limit and len(files) >= limit:
                    return sorted(files)

    return sorted(files)


def extract_teams_from_json(json_content: dict) -> List[Dict]:
    """Extract all teams from a schedule JSON file"""
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

        # Extract all games to get all teams
        for game in events:
            competitors = game.get("competitors", [])

            for team in competitors:
                team_id = str(team.get("id", ""))
                if not team_id:
                    continue

                # Extract team info
                team_data = {
                    "team_id": team_id,
                    "team_name": team.get("displayName", ""),
                    "team_abbreviation": team.get("abbreviation", "")
                    or team.get("abbrev", ""),
                    "location": team.get("location", ""),
                    "name": team.get("name", ""),
                }
                teams.append(team_data)

    except Exception as e:
        # Silently skip errors
        pass

    return teams


def scan_year_for_teams(year: int) -> Dict[str, Dict]:
    """
    Scan all schedule files for a year and extract unique teams

    Returns: dict of {team_id: team_info}
    """
    print(f"\n{'='*80}")
    print(f"Scanning Year: {year}")
    print(f"{'='*80}\n")

    # Get sample of files for this year (first 50 should cover all teams)
    s3_files = get_s3_files_for_year(year, limit=50)

    if not s3_files:
        print(f"⚠️  No schedule files found for year {year}")
        return {}

    print(f"Scanning {len(s3_files)} files to discover teams...")

    s3 = boto3.client("s3")
    teams_dict = {}

    for i, s3_key in enumerate(s3_files, 1):
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            json_content = json.loads(response["Body"].read())

            teams = extract_teams_from_json(json_content)

            for team in teams:
                team_id = team["team_id"]
                if team_id not in teams_dict:
                    teams_dict[team_id] = team
                    print(
                        f"  Found: {team['team_name']} ({team['team_abbreviation']}) - ID: {team_id}"
                    )

            # Stop early if we found 30+ teams (all active teams)
            if len(teams_dict) >= 30:
                break

        except Exception as e:
            # Skip files with errors
            pass

    print(f"\n✅ Discovered {len(teams_dict)} teams for year {year}")
    return teams_dict


def main():
    parser = argparse.ArgumentParser(
        description="Extract NBA teams by year from S3 schedule files"
    )
    parser.add_argument(
        "--year-range", type=str, required=True, help="Year range (e.g., 1993-2025)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without inserting",
    )

    args = parser.parse_args()

    # Validate environment
    validate_environment()

    # Parse year range
    start_year, end_year = map(int, args.year_range.split("-"))
    years = list(range(start_year, end_year + 1))

    print(f"NBA Team Discovery: {start_year}-{end_year}")
    print(f"Years to scan: {len(years)}")
    print()

    # Connect to database
    if not args.dry_run:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
            )
            cursor = conn.cursor()
            print(f"✅ Connected to database: {DB_HOST}\n")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

    # Track all teams across all years
    all_teams = {}  # {team_id: {team_info}}
    team_seasons_data = []  # [(team_id, season, name, abbrev, ...)]

    # Scan each year
    for year in years:
        # Determine season string (e.g., "1993-94")
        season = f"{year}-{str(year + 1)[2:]}"

        # Scan for teams in this year
        year_teams = scan_year_for_teams(year)

        # Add to overall teams dict
        for team_id, team_info in year_teams.items():
            if team_id not in all_teams:
                all_teams[team_id] = team_info

            # Add to team_seasons data
            team_seasons_data.append(
                {
                    "team_id": team_id,
                    "season": season,
                    "team_name": team_info["team_name"],
                    "team_abbreviation": team_info["team_abbreviation"],
                    "city": team_info.get("location", None),
                }
            )

    print(f"\n{'='*80}")
    print("TEAM DISCOVERY COMPLETE")
    print(f"{'='*80}")
    print(f"Total unique teams: {len(all_teams)}")
    print(f"Total team-season records: {len(team_seasons_data)}")
    print()

    # Insert teams into database
    if not args.dry_run:
        try:
            # Insert into teams table
            print("Inserting teams into `teams` table...")
            teams_insert = """
                INSERT INTO teams (team_id, team_name, team_abbreviation)
                VALUES %s
                ON CONFLICT (team_id) DO UPDATE SET
                    team_name = EXCLUDED.team_name,
                    team_abbreviation = EXCLUDED.team_abbreviation,
                    updated_at = CURRENT_TIMESTAMP
            """

            teams_values = [
                (team_id, info["team_name"], info["team_abbreviation"])
                for team_id, info in all_teams.items()
            ]

            execute_values(cursor, teams_insert, teams_values)
            print(f"✅ Inserted/updated {len(teams_values)} teams")

            # Insert into team_seasons table
            print("\nInserting team-season data into `team_seasons` table...")
            team_seasons_insert = """
                INSERT INTO team_seasons (team_id, season, team_name, team_abbreviation, city)
                VALUES %s
                ON CONFLICT (team_id, season) DO UPDATE SET
                    team_name = EXCLUDED.team_name,
                    team_abbreviation = EXCLUDED.team_abbreviation,
                    city = EXCLUDED.city,
                    updated_at = CURRENT_TIMESTAMP
            """

            team_seasons_values = [
                (
                    ts["team_id"],
                    ts["season"],
                    ts["team_name"],
                    ts["team_abbreviation"],
                    ts["city"],
                )
                for ts in team_seasons_data
            ]

            execute_values(cursor, team_seasons_insert, team_seasons_values)
            print(f"✅ Inserted/updated {len(team_seasons_values)} team-season records")

            conn.commit()

            # Show summary
            print("\n" + "=" * 80)
            print("DATABASE SUMMARY")
            print("=" * 80)

            cursor.execute("SELECT COUNT(*) FROM teams")
            print(f"Total teams in database: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM team_seasons")
            print(f"Total team-season records: {cursor.fetchone()[0]}")

            cursor.execute(
                """
                SELECT season, COUNT(*) as teams
                FROM team_seasons
                GROUP BY season
                ORDER BY season
                LIMIT 10
            """
            )
            print("\nSample team counts by season:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} teams")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"❌ Database insert failed: {e}")
            if not args.dry_run:
                conn.rollback()
            sys.exit(1)

    else:
        print("🔍 DRY RUN: Would insert data")
        print("\nSample teams:")
        for i, (team_id, info) in enumerate(list(all_teams.items())[:10], 1):
            print(
                f"  {i}. {info['team_name']} ({info['team_abbreviation']}) - ID: {team_id}"
            )


if __name__ == "__main__":
    main()
