#!/usr/bin/env python3
"""
Local ETL Script: Extract NBA Box Score Data from S3 to RDS

Extracts comprehensive box score data (team + player stats) from ESPN JSON files.
Reads directly from S3 and writes to RDS PostgreSQL (no Glue required).

Input: s3://nba-sim-raw-data-lake/box_scores/*.json
Output: RDS PostgreSQL tables: box_score_teams, box_score_players

Usage:
    python scripts/etl/extract_boxscores_local.py --year 1997
    python scripts/etl/extract_boxscores_local.py --year-range 1997-2025

Prerequisites:
    - source /Users/ryanranft/nba-sim-credentials.env
    - pip install boto3 psycopg2-binary

Author: Ryan Ranft
Date: 2025-10-02
Phase: 2.3 - Local ETL for Box Score data
Based on: Original box score extraction script
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import boto3
import psycopg2
from psycopg2.extras import execute_batch

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


def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        if isinstance(value, str):
            value = "".join(c for c in value if c.isdigit() or c == "-")
        return int(value) if value != "" else default
    except (ValueError, TypeError):
        return default


def parse_percentage(pct_str):
    """Parse percentage string to float"""
    try:
        if not pct_str or pct_str == "":
            return 0
        return float(str(pct_str).strip("%"))
    except (ValueError, AttributeError):
        return 0


def parse_minutes(minutes_str):
    """Parse minutes from 'MM:SS' or integer format"""
    try:
        if ":" in str(minutes_str):
            mins, secs = minutes_str.split(":")
            return int(mins)
        else:
            return safe_int(minutes_str, 0)
    except (ValueError, AttributeError):
        return 0


def parse_datetime(dt_str):
    """Parse datetime string"""
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M%z")
    except ValueError:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%MZ")
        except ValueError:
            return None


def get_team_stats(team_data):
    """Extract team totals from stats array"""
    for stat_group in team_data.get("stats", []):
        if stat_group.get("type") == "totals":
            totals = stat_group.get("ttls", [])
            pcts = stat_group.get("pcts", [])

            if not totals or len(totals) < 14:
                return {
                    "score": 0,
                    "field_goals": "0-0",
                    "field_goals_pct": 0,
                    "three_pointers": "0-0",
                    "three_pointers_pct": 0,
                    "free_throws": "0-0",
                    "free_throws_pct": 0,
                    "offensive_rebounds": 0,
                    "defensive_rebounds": 0,
                    "total_rebounds": 0,
                    "assists": 0,
                    "steals": 0,
                    "blocks": 0,
                    "turnovers": 0,
                    "fouls": 0,
                }

            return {
                "score": safe_int(totals[13]),
                "field_goals": totals[1] or "0-0",
                "field_goals_pct": parse_percentage(pcts[1]) if len(pcts) > 1 else 0,
                "three_pointers": totals[2] or "0-0",
                "three_pointers_pct": parse_percentage(pcts[2]) if len(pcts) > 2 else 0,
                "free_throws": totals[3] or "0-0",
                "free_throws_pct": parse_percentage(pcts[3]) if len(pcts) > 3 else 0,
                "offensive_rebounds": safe_int(totals[4]),
                "defensive_rebounds": safe_int(totals[5]),
                "total_rebounds": safe_int(totals[6]),
                "assists": safe_int(totals[7]),
                "steals": safe_int(totals[8]),
                "blocks": safe_int(totals[9]),
                "turnovers": safe_int(totals[10]),
                "fouls": safe_int(totals[11]),
            }

    return None


def extract_game_info(data, game_id) -> Optional[Dict]:
    """Extract game-level information and team stats"""
    try:
        gamepackage = data["page"]["content"]["gamepackage"]
        gmInfo = gamepackage["gmInfo"]
        refs = gmInfo.get("refs", [])

        # Initialize variables
        home_team = away_team = None
        home_stats = away_stats = None

        # Find home and away teams and their stats from box score data
        for team_data in gamepackage.get("bxscr", []):
            if isinstance(team_data, dict) and "tm" in team_data:
                team = team_data["tm"]
                stats = get_team_stats(team_data)

                if team.get("hm"):
                    home_team = team
                    home_stats = stats
                else:
                    away_team = team
                    away_stats = stats

        # Create referee information dictionary
        referee_info = {}
        for i, ref in enumerate(refs[:3], 1):
            referee_info[f"referee{i}_name"] = ref.get("dspNm", "")
            referee_info[f"referee{i}_position"] = ref.get("pos", "")

        # Fill in missing referee slots
        for i in range(len(refs) + 1, 4):
            referee_info[f"referee{i}_name"] = ""
            referee_info[f"referee{i}_position"] = ""

        return {
            "game_id": str(game_id),
            "game_date": parse_datetime(gmInfo.get("dtTm", "")),
            "home_team_id": (
                str(home_team["id"]) if home_team and "id" in home_team else None
            ),
            "home_team_abbrev": home_team.get("abbrev", "") if home_team else "",
            "home_stats": home_stats or {},
            "away_team_id": (
                str(away_team["id"]) if away_team and "id" in away_team else None
            ),
            "away_team_abbrev": away_team.get("abbrev", "") if away_team else "",
            "away_stats": away_stats or {},
            "attendance": safe_int(gmInfo.get("attnd", 0)),
            "game_state": gmInfo.get("gameState", ""),
            **referee_info,
        }
    except (KeyError, TypeError) as e:
        print(f"  Warning: Error extracting game info from {game_id}: {e}")
        return None


def extract_player_stats(data, game_id) -> List[Tuple]:
    """Extract player-level box score stats"""
    players_data = []

    try:
        gamepackage = data["page"]["content"]["gamepackage"]
        box_score = gamepackage.get("bxscr", [])

        if not box_score:
            return []

        for team_data in box_score:
            if not isinstance(team_data, dict) or "tm" not in team_data:
                continue

            team = team_data["tm"]
            team_id = str(team.get("id", ""))
            team_abbrev = team.get("abbrev", "")

            for stat_group in team_data.get("stats", []):
                if "athlts" not in stat_group:
                    continue

                is_starter = stat_group.get("type") == "starters"
                stat_keys = stat_group.get("keys", [])

                for player in stat_group.get("athlts", []):
                    try:
                        player_stats_values = player.get("stats", [])
                        player_info = player.get("athlt", {})

                        # Create dict mapping stat keys to values
                        stats_dict = dict(zip(stat_keys, player_stats_values))

                        players_data.append(
                            (
                                str(game_id),
                                str(player_info.get("id", "")),
                                team_id,
                                team_abbrev,
                                is_starter,
                                parse_minutes(stats_dict.get("minutes", 0)),
                                str(
                                    stats_dict.get(
                                        "fieldGoalsMade-fieldGoalsAttempted", "0-0"
                                    )
                                ),
                                str(
                                    stats_dict.get(
                                        "threePointFieldGoalsMade-threePointFieldGoalsAttempted",
                                        "0-0",
                                    )
                                ),
                                str(
                                    stats_dict.get(
                                        "freeThrowsMade-freeThrowsAttempted", "0-0"
                                    )
                                ),
                                safe_int(stats_dict.get("offensiveRebounds")),
                                safe_int(stats_dict.get("defensiveRebounds")),
                                safe_int(stats_dict.get("rebounds")),
                                safe_int(stats_dict.get("assists")),
                                safe_int(stats_dict.get("steals")),
                                safe_int(stats_dict.get("blocks")),
                                safe_int(stats_dict.get("turnovers")),
                                safe_int(stats_dict.get("fouls")),
                                safe_int(stats_dict.get("plusMinus")),
                                safe_int(stats_dict.get("points")),
                            )
                        )
                    except (KeyError, IndexError) as e:
                        print(
                            f"  Warning: Error processing player in game {game_id}: {e}"
                        )
                        continue

    except KeyError as e:
        print(f"  Warning: Error extracting player stats from {game_id}: {e}")

    return players_data


def get_game_ids_for_year(year: int, cursor) -> List[str]:
    """Get list of game IDs for a specific year from database"""
    query = """
        SELECT game_id
        FROM games
        WHERE game_date >= %s AND game_date < %s
        ORDER BY game_date
    """
    cursor.execute(query, (f"{year}-01-01", f"{year+1}-01-01"))
    return [row[0] for row in cursor.fetchall()]


def process_year(year: int, dry_run: bool = False) -> Dict:
    """
    Process all box score files for games in a given year

    Returns: {'processed': int, 'inserted_teams': int, 'inserted_players': int, 'skipped': int, 'errors': int}
    """
    print(f"\n{'='*80}")
    print(f"Processing Year: {year}")
    print(f"{'='*80}\n")

    # Connect to database first
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
            return {
                "processed": 0,
                "inserted_teams": 0,
                "inserted_players": 0,
                "skipped": 0,
                "errors": 0,
            }

    # Get game IDs for this year
    print("Fetching game IDs from database...")
    game_ids = get_game_ids_for_year(year, cursor)

    if not game_ids:
        print(f"⚠️  No games found for year {year}")
        if not dry_run:
            cursor.close()
            conn.close()
        return {
            "processed": 0,
            "inserted_teams": 0,
            "inserted_players": 0,
            "skipped": 0,
            "errors": 0,
        }

    print(f"Found {len(game_ids)} games for year {year}")

    # Connect to S3
    s3 = boto3.client("s3")

    # Process each game
    stats = {
        "processed": 0,
        "inserted_teams": 0,
        "inserted_players": 0,
        "skipped": 0,
        "errors": 0,
    }

    for i, game_id in enumerate(game_ids, 1):
        s3_key = f"box_scores/{game_id}.json"

        try:
            # Download and parse JSON
            response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            json_content = json.loads(response["Body"].read())

            # Extract game info
            game_info = extract_game_info(json_content, game_id)

            if game_info and not dry_run:
                home_stats = game_info["home_stats"]
                away_stats = game_info["away_stats"]

                cursor.execute(
                    """
                    INSERT INTO box_score_teams (
                        game_id, game_date,
                        home_team_id, home_team_abbrev,
                        home_team_score, home_team_field_goals, home_team_field_goals_pct,
                        home_team_three_pointers, home_team_three_pointers_pct,
                        home_team_free_throws, home_team_free_throws_pct,
                        home_team_offensive_rebounds, home_team_defensive_rebounds,
                        home_team_total_rebounds, home_team_assists, home_team_steals,
                        home_team_blocks, home_team_turnovers, home_team_fouls,
                        away_team_id, away_team_abbrev,
                        away_team_score, away_team_field_goals, away_team_field_goals_pct,
                        away_team_three_pointers, away_team_three_pointers_pct,
                        away_team_free_throws, away_team_free_throws_pct,
                        away_team_offensive_rebounds, away_team_defensive_rebounds,
                        away_team_total_rebounds, away_team_assists, away_team_steals,
                        away_team_blocks, away_team_turnovers, away_team_fouls,
                        attendance, game_state,
                        referee1_name, referee1_position,
                        referee2_name, referee2_position,
                        referee3_name, referee3_position
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (game_id) DO UPDATE SET
                        home_team_score = EXCLUDED.home_team_score,
                        away_team_score = EXCLUDED.away_team_score,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        game_info["game_id"],
                        game_info["game_date"],
                        game_info["home_team_id"],
                        game_info["home_team_abbrev"],
                        home_stats.get("score", 0),
                        home_stats.get("field_goals", "0-0"),
                        home_stats.get("field_goals_pct", 0),
                        home_stats.get("three_pointers", "0-0"),
                        home_stats.get("three_pointers_pct", 0),
                        home_stats.get("free_throws", "0-0"),
                        home_stats.get("free_throws_pct", 0),
                        home_stats.get("offensive_rebounds", 0),
                        home_stats.get("defensive_rebounds", 0),
                        home_stats.get("total_rebounds", 0),
                        home_stats.get("assists", 0),
                        home_stats.get("steals", 0),
                        home_stats.get("blocks", 0),
                        home_stats.get("turnovers", 0),
                        home_stats.get("fouls", 0),
                        game_info["away_team_id"],
                        game_info["away_team_abbrev"],
                        away_stats.get("score", 0),
                        away_stats.get("field_goals", "0-0"),
                        away_stats.get("field_goals_pct", 0),
                        away_stats.get("three_pointers", "0-0"),
                        away_stats.get("three_pointers_pct", 0),
                        away_stats.get("free_throws", "0-0"),
                        away_stats.get("free_throws_pct", 0),
                        away_stats.get("offensive_rebounds", 0),
                        away_stats.get("defensive_rebounds", 0),
                        away_stats.get("total_rebounds", 0),
                        away_stats.get("assists", 0),
                        away_stats.get("steals", 0),
                        away_stats.get("blocks", 0),
                        away_stats.get("turnovers", 0),
                        away_stats.get("fouls", 0),
                        game_info["attendance"],
                        game_info["game_state"],
                        game_info["referee1_name"],
                        game_info["referee1_position"],
                        game_info["referee2_name"],
                        game_info["referee2_position"],
                        game_info["referee3_name"],
                        game_info["referee3_position"],
                    ),
                )
                stats["inserted_teams"] += 1

            # Extract player stats
            player_stats = extract_player_stats(json_content, game_id)

            if player_stats and not dry_run:
                execute_batch(
                    cursor,
                    """
                    INSERT INTO box_score_players (
                        game_id, player_id, team_id, team_abbrev,
                        is_starter, minutes, field_goals, three_pointers,
                        free_throws, offensive_rebounds, defensive_rebounds,
                        total_rebounds, assists, steals, blocks, turnovers,
                        fouls, plus_minus, points
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (game_id, player_id) DO UPDATE SET
                        minutes = EXCLUDED.minutes,
                        points = EXCLUDED.points,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    player_stats,
                )
                stats["inserted_players"] += len(player_stats)

            if not dry_run:
                conn.commit()

            stats["processed"] += 1

            # Progress update every 100 games
            if i % 100 == 0:
                print(
                    f"  Progress: {i}/{len(game_ids)} games | {stats['inserted_players']} players extracted"
                )

        except Exception as e:
            if "NoSuchKey" not in str(e):
                print(f"  ❌ Error processing {s3_key}: {e}")
            stats["errors"] += 1
            if not dry_run:
                conn.rollback()

    print(f"\n✅ Extraction complete:")
    print(f"   Games processed: {stats['processed']}")
    print(f"   Team stats inserted: {stats['inserted_teams']}")
    print(f"   Player stats inserted: {stats['inserted_players']}")

    if not dry_run:
        cursor.close()
        conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Extract NBA box score data from S3 to RDS PostgreSQL"
    )
    parser.add_argument("--year", type=int, help="Process single year (e.g., 1997)")
    parser.add_argument(
        "--year-range", type=str, help="Process year range (e.g., 1997-2025)"
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
    total_stats = {
        "processed": 0,
        "inserted_teams": 0,
        "inserted_players": 0,
        "skipped": 0,
        "errors": 0,
    }

    for year in years:
        stats = process_year(year, dry_run=args.dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]

    # Summary
    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"Years processed: {len(years)}")
    print(f"Games processed: {total_stats['processed']}")
    print(f"Team stats inserted: {total_stats['inserted_teams']}")
    print(f"Player stats inserted: {total_stats['inserted_players']}")
    print(f"Errors: {total_stats['errors']}")
    print()


if __name__ == "__main__":
    main()
