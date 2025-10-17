#!/usr/bin/env python3
"""
Build Unified Multi-Source NBA Database

Combines ESPN and hoopR data sources into comprehensive unified database.
Handles gaps by using available source, tracks quality, maintains data integrity.

Strategy:
1. Read from pure source databases (ESPN, hoopR)
2. Combine with source tracking
3. Handle gaps (use ESPN when hoopR unavailable, vice versa)
4. Calculate quality scores
5. Load to unified database

Key Principles:
- Source databases remain PURE (no modifications)
- Unified database is SEPARATE
- Quality tracking for ML

Usage:
    python scripts/etl/build_unified_database.py
    python scripts/etl/build_unified_database.py --limit 1000  # Test
    python scripts/etl/build_unified_database.py --year 2024  # Specific year

Version: 1.0
Created: October 9, 2025
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse
from collections import defaultdict

# Database paths
ESPN_DB = "/tmp/espn_local.db"
HOOPR_DB = "/tmp/hoopr_local.db"
UNIFIED_DB = "/tmp/unified_nba.db"

# Game ID mapping
MAPPING_FILE = Path(__file__).parent.parent / "mapping" / "espn_hoopr_game_mapping.json"


def load_game_mapping() -> Dict:
    """Load ESPN-to-hoopR game ID mapping."""

    print("=" * 70)
    print("LOAD GAME ID MAPPING")
    print("=" * 70)
    print()

    with open(MAPPING_FILE) as f:
        data = json.load(f)

    print(f"✓ Loaded {data['metadata']['total_mappings']:,} game ID mappings")
    print()

    return data["espn_to_hoopr"], data["hoopr_to_espn"]


def get_all_unique_games(
    espn_conn, hoopr_conn, espn_to_hoopr, year: Optional[int] = None
) -> List[Dict]:
    """Get all unique games from both sources."""

    print("=" * 70)
    print("IDENTIFY ALL UNIQUE GAMES")
    print("=" * 70)
    print()

    unique_games = {}

    # Get ESPN games
    print("Reading ESPN games...")
    espn_cursor = espn_conn.cursor()

    query = "SELECT game_id, game_date, home_team, away_team, pbp_event_count FROM games WHERE has_pbp = 1"
    if year:
        query += f" AND strftime('%Y', game_date) = '{year}'"

    espn_cursor.execute(query)

    for row in espn_cursor.fetchall():
        game_id, game_date, home_team, away_team, event_count = row
        unique_games[game_id] = {
            "espn_game_id": game_id,
            "hoopr_game_id": espn_to_hoopr.get(game_id),
            "game_date": game_date,
            "home_team": home_team or "Unknown",
            "away_team": away_team or "Unknown",
            "has_espn": True,
            "has_hoopr": False,
            "espn_event_count": event_count,
        }

    print(f"✓ Found {len(unique_games):,} ESPN games")

    # Get hoopR games
    print("Reading hoopR games...")
    hoopr_cursor = hoopr_conn.cursor()

    query = """
        SELECT s.game_id, s.game_date, s.home_display_name, s.away_display_name, COUNT(pbp.id)
        FROM schedule s
        LEFT JOIN play_by_play pbp ON s.game_id = pbp.game_id
        GROUP BY s.game_id, s.game_date, s.home_display_name, s.away_display_name
        HAVING COUNT(pbp.id) > 0
    """
    if year:
        query = query.replace(
            "GROUP BY", f"WHERE strftime('%Y', s.game_date) = '{year}' GROUP BY"
        )

    hoopr_cursor.execute(query)

    hoopr_only_count = 0
    for row in hoopr_cursor.fetchall():
        hoopr_game_id, game_date, home_team, away_team, event_count = row
        hoopr_game_id_str = str(hoopr_game_id)

        # Try to find ESPN game ID
        espn_game_id = None
        for mapping in espn_to_hoopr.items():
            if mapping[1] == hoopr_game_id_str:
                espn_game_id = mapping[0]
                break

        if espn_game_id and espn_game_id in unique_games:
            # Update existing entry
            unique_games[espn_game_id]["has_hoopr"] = True
            unique_games[espn_game_id]["hoopr_event_count"] = event_count
        else:
            # hoopR-only game
            unique_games[hoopr_game_id_str] = {
                "espn_game_id": espn_game_id,
                "hoopr_game_id": hoopr_game_id_str,
                "game_date": game_date,
                "home_team": home_team or "Unknown",
                "away_team": away_team or "Unknown",
                "has_espn": False,
                "has_hoopr": True,
                "hoopr_event_count": event_count,
            }
            hoopr_only_count += 1

    print(f"✓ Found {hoopr_only_count:,} hoopR-only games")
    print(f"✓ Total unique games: {len(unique_games):,}")
    print()

    # Summary
    both = sum(1 for g in unique_games.values() if g["has_espn"] and g["has_hoopr"])
    espn_only = sum(
        1 for g in unique_games.values() if g["has_espn"] and not g["has_hoopr"]
    )
    hoopr_only = sum(
        1 for g in unique_games.values() if not g["has_espn"] and g["has_hoopr"]
    )

    print(f"Coverage summary:")
    print(f"  Both sources:  {both:,}")
    print(f"  ESPN only:     {espn_only:,}")
    print(f"  hoopR only:    {hoopr_only:,}")
    print()

    return list(unique_games.values())


def calculate_quality_score(game: Dict) -> Dict:
    """Calculate quality score for a game."""

    has_espn = game["has_espn"]
    has_hoopr = game["has_hoopr"]

    # Both sources = highest quality
    if has_espn and has_hoopr:
        quality_score = 95
        uncertainty = "LOW"
        recommended_source = "hoopR"  # Prefer hoopR (richer schema)
        notes = "Both sources available - hoopR preferred for richer schema"

    # hoopR only
    elif has_hoopr:
        quality_score = 90
        uncertainty = "MEDIUM"
        recommended_source = "hoopR"
        notes = "hoopR only - ESPN unavailable"

    # ESPN only
    elif has_espn:
        quality_score = 85
        uncertainty = "MEDIUM"
        recommended_source = "ESPN"
        notes = "ESPN only - hoopR unavailable"

    else:
        # This shouldn't happen
        quality_score = 0
        uncertainty = "HIGH"
        recommended_source = None
        notes = "No sources available"

    return {
        "quality_score": quality_score,
        "uncertainty": uncertainty,
        "recommended_source": recommended_source,
        "ml_notes": notes,
    }


def populate_source_coverage(unified_conn, games: List[Dict]):
    """Populate source_coverage table."""

    print("=" * 70)
    print("POPULATE SOURCE COVERAGE")
    print("=" * 70)
    print()

    cursor = unified_conn.cursor()

    for game in games:
        # Use ESPN game ID as primary key
        game_id = game["espn_game_id"] or game["hoopr_game_id"]

        # Calculate quality
        quality = calculate_quality_score(game)

        cursor.execute(
            """
            INSERT OR REPLACE INTO source_coverage (
                game_id, game_date,
                has_espn, has_hoopr,
                espn_event_count, hoopr_event_count,
                primary_source, total_sources,
                has_discrepancies, overall_quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                game_id,
                game["game_date"],
                game["has_espn"],
                game["has_hoopr"],
                game.get("espn_event_count"),
                game.get("hoopr_event_count"),
                quality["recommended_source"],
                (1 if game["has_espn"] else 0) + (1 if game["has_hoopr"] else 0),
                False,  # Will be updated by discrepancy detection
                quality["quality_score"],
            ),
        )

    unified_conn.commit()
    print(f"✓ Populated source_coverage for {len(games):,} games")
    print()


def populate_quality_scores(unified_conn, games: List[Dict]):
    """Populate quality_scores table."""

    print("=" * 70)
    print("POPULATE QUALITY SCORES")
    print("=" * 70)
    print()

    cursor = unified_conn.cursor()

    for game in games:
        game_id = game["espn_game_id"] or game["hoopr_game_id"]
        quality = calculate_quality_score(game)

        cursor.execute(
            """
            INSERT OR REPLACE INTO quality_scores (
                game_id, game_date,
                recommended_source, quality_score, uncertainty,
                has_event_count_issue, has_coordinate_issue,
                has_score_issue, has_timing_issue,
                use_for_training, ml_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                game_id,
                game["game_date"],
                quality["recommended_source"],
                quality["quality_score"],
                quality["uncertainty"],
                False,  # Will be updated by discrepancy detection
                False,
                False,
                False,
                True,  # All games usable for training
                quality["ml_notes"],
            ),
        )

    unified_conn.commit()
    print(f"✓ Populated quality_scores for {len(games):,} games")
    print()


def print_summary(unified_conn):
    """Print summary of unified database."""

    print("=" * 70)
    print("UNIFIED DATABASE SUMMARY")
    print("=" * 70)
    print()

    cursor = unified_conn.cursor()

    # Source coverage
    cursor.execute("SELECT COUNT(*) FROM source_coverage;")
    total_games = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 1;"
    )
    both_sources = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 0;"
    )
    espn_only = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 0 AND has_hoopr = 1;"
    )
    hoopr_only = cursor.fetchone()[0]

    print(f"Total games: {total_games:,}")
    print(f"  Both sources:  {both_sources:,} ({both_sources/total_games*100:.1f}%)")
    print(f"  ESPN only:     {espn_only:,} ({espn_only/total_games*100:.1f}%)")
    print(f"  hoopR only:    {hoopr_only:,} ({hoopr_only/total_games*100:.1f}%)")
    print()

    # Quality distribution
    cursor.execute(
        """
        SELECT quality_score, COUNT(*)
        FROM quality_scores
        GROUP BY quality_score
        ORDER BY quality_score DESC;
    """
    )

    print("Quality score distribution:")
    for score, count in cursor.fetchall():
        print(f"  Score {score}: {count:,} games")

    print()

    # Uncertainty
    cursor.execute(
        """
        SELECT uncertainty, COUNT(*)
        FROM quality_scores
        GROUP BY uncertainty
        ORDER BY uncertainty;
    """
    )

    print("Uncertainty distribution:")
    for unc, count in cursor.fetchall():
        print(f"  {unc}: {count:,} games")

    print()
    cursor.close()


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Build unified multi-source NBA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build full unified database
  python scripts/etl/build_unified_database.py

  # Test with limited games
  python scripts/etl/build_unified_database.py --limit 1000

  # Build for specific year
  python scripts/etl/build_unified_database.py --year 2024

Result:
  - Unified database with all games from ESPN + hoopR
  - Quality scores for ML training
  - Source availability tracking
  - Gap handling (use available source)
        """,
    )

    parser.add_argument("--limit", type=int, help="Limit number of games (for testing)")

    parser.add_argument("--year", type=int, help="Build for specific year only")

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load game mapping
    espn_to_hoopr, hoopr_to_espn = load_game_mapping()

    # Connect to databases
    print("Connecting to databases...")
    espn_conn = sqlite3.connect(ESPN_DB)
    hoopr_conn = sqlite3.connect(HOOPR_DB)
    unified_conn = sqlite3.connect(UNIFIED_DB)
    print("✓ Connected to ESPN, hoopR, and Unified databases")
    print()

    # Get all unique games
    games = get_all_unique_games(espn_conn, hoopr_conn, espn_to_hoopr, year=args.year)

    # Limit if requested
    if args.limit:
        games = games[: args.limit]
        print(f"⚠️  Limited to {len(games):,} games for testing")
        print()

    # Populate unified database
    populate_source_coverage(unified_conn, games)
    populate_quality_scores(unified_conn, games)

    # Print summary
    print_summary(unified_conn)

    # Close connections
    espn_conn.close()
    hoopr_conn.close()
    unified_conn.close()

    print("=" * 70)
    print(f"✓ Unified database built successfully!")
    print(f"  Database: {UNIFIED_DB}")
    print(f"  Games: {len(games):,}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
