#!/usr/bin/env python3
"""
Test ESPN Feature Extraction

Tests the new ESPN feature extractor on sample games from S3.
Validates that all 58 features can be extracted correctly.

Usage:
    python scripts/test_espn_feature_extraction.py
    python scripts/test_espn_feature_extraction.py --sample 10  # Test on 10 games
"""

import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nba_simulator.etl.extractors.espn import ESPNFeatureExtractor, ESPNJSONReader


def test_single_game(game_id: str = "131105001"):
    """Test extraction on a single game"""
    print(f"\n{'='*60}")
    print(f"Testing Feature Extraction on Game: {game_id}")
    print(f"{'='*60}\n")

    extractor = ESPNFeatureExtractor()

    # Extract features
    print(f"Extracting features from S3...")
    features = extractor.extract_game_features(game_id=game_id)

    if not features:
        print(f"❌ Failed to extract features for game {game_id}")
        return False

    print(f"✓ Features extracted successfully!\n")

    # Display results
    print(f"{'='*60}")
    print(f"GAME INFO ({len(features.get('game_info', {}))} fields)")
    print(f"{'='*60}")
    for key, value in features.get("game_info", {}).items():
        print(f"  {key}: {value}")

    print(f"\n{'='*60}")
    print(f"SCORING")
    print(f"{'='*60}")
    scoring = features.get("scoring", {})
    print(f"  Home quarters: {scoring.get('home', {}).get('quarters')}")
    print(f"  Home total: {scoring.get('home', {}).get('total')}")
    print(f"  Away quarters: {scoring.get('away', {}).get('quarters')}")
    print(f"  Away total: {scoring.get('away', {}).get('total')}")

    print(f"\n{'='*60}")
    print(f"VENUE")
    print(f"{'='*60}")
    venue = features.get("venue", {})
    print(f"  Name: {venue.get('name')}")
    print(f"  City: {venue.get('city')}, {venue.get('state')}")

    print(f"\n{'='*60}")
    print(f"OFFICIALS ({len(features.get('officials', []))} referees)")
    print(f"{'='*60}")
    for i, ref in enumerate(features.get("officials", [])[:3], 1):
        print(f"  {i}. {ref.get('name')} (#{ref.get('number', 'N/A')})")

    print(f"\n{'='*60}")
    print(f"BOX SCORE")
    print(f"{'='*60}")
    box_score = features.get("box_score", {})
    home_players = box_score.get("home", {}).get("players", [])
    away_players = box_score.get("away", {}).get("players", [])

    print(f"  Home: {len(home_players)} players")
    print(f"  Away: {len(away_players)} players")

    # Show top scorer from each team
    if home_players:
        top_home = max(
            home_players, key=lambda p: p.get("stats", {}).get("points") or 0
        )
        stats = top_home.get("stats", {})
        print(f"\n  Top Home Scorer: {top_home.get('name')}")
        print(f"    Points: {stats.get('points')}")
        print(f"    Rebounds: {stats.get('rebounds')}")
        print(f"    Assists: {stats.get('assists')}")
        print(f"    FG%: {stats.get('field_goal_pct')}")
        print(f"    3P%: {stats.get('three_point_pct')}")
        print(f"    Double-double: {stats.get('double_double')}")

    if away_players:
        top_away = max(
            away_players, key=lambda p: p.get("stats", {}).get("points") or 0
        )
        stats = top_away.get("stats", {})
        print(f"\n  Top Away Scorer: {top_away.get('name')}")
        print(f"    Points: {stats.get('points')}")
        print(f"    Rebounds: {stats.get('rebounds')}")
        print(f"    Assists: {stats.get('assists')}")
        print(f"    FG%: {stats.get('field_goal_pct')}")
        print(f"    3P%: {stats.get('three_point_pct')}")
        print(f"    Double-double: {stats.get('double_double')}")

    print(f"\n{'='*60}")
    print(f"PLAY-BY-PLAY SUMMARY")
    print(f"{'='*60}")
    pbp = features.get("plays_summary", {})
    print(f"  Total plays: {pbp.get('total_plays')}")
    print(f"  Periods: {pbp.get('periods')}")
    print(f"  Event types: {len(pbp.get('event_types', {}))}")

    print(f"\n✅ Feature extraction successful!")
    print(f"{'='*60}\n")

    return True


def test_batch_games(sample_size: int = 10):
    """Test extraction on multiple games"""
    print(f"\n{'='*60}")
    print(f"Testing Batch Feature Extraction ({sample_size} games)")
    print(f"{'='*60}\n")

    # Get sample game IDs from database
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import os

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "nba_simulator"),
        user=os.getenv("POSTGRES_USER", "ryanranft"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        f"""
        SELECT game_id
        FROM raw_data.nba_games
        ORDER BY game_date DESC
        LIMIT {sample_size}
    """
    )

    game_ids = [row["game_id"] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    print(f"Testing on {len(game_ids)} games...")

    extractor = ESPNFeatureExtractor()
    results = extractor.batch_extract_games(game_ids)

    # Analyze results
    success_count = sum(1 for f in results.values() if f is not None)
    feature_coverage = defaultdict(int)

    for game_id, features in results.items():
        if features:
            # Count features present
            if features.get("game_info"):
                feature_coverage["game_info"] += 1
            if features.get("scoring"):
                feature_coverage["scoring"] += 1
            if features.get("venue", {}).get("name"):
                feature_coverage["venue"] += 1
            if features.get("officials"):
                feature_coverage["officials"] += 1
            if features.get("box_score", {}).get("home", {}).get("players"):
                feature_coverage["box_score"] += 1
            if features.get("plays_summary", {}).get("total_plays", 0) > 0:
                feature_coverage["play_by_play"] += 1

    # Report results
    print(f"\n{'='*60}")
    print(f"BATCH EXTRACTION RESULTS")
    print(f"{'='*60}")
    print(f"  Total games tested: {len(game_ids)}")
    print(
        f"  Successful extractions: {success_count}/{len(game_ids)} ({success_count/len(game_ids)*100:.1f}%)"
    )

    print(f"\n  Feature Coverage:")
    for feature_name, count in sorted(feature_coverage.items()):
        pct = count / len(game_ids) * 100
        status = "✓" if pct >= 95 else "⚠"
        print(f"    {status} {feature_name}: {count}/{len(game_ids)} ({pct:.1f}%)")

    if success_count == len(game_ids):
        print(f"\n✅ All games extracted successfully!")
    else:
        print(f"\n⚠️  Some games failed extraction")

    print(f"{'='*60}\n")

    return success_count == len(game_ids)


def count_features(features: dict) -> dict:
    """Count how many features are present"""
    counts = {"game_level": 0, "player_stats": 0, "play_by_play": 0, "derived": 0}

    # Game-level features
    game_info = features.get("game_info", {})
    if game_info.get("season_type"):
        counts["game_level"] += 1
    if game_info.get("attendance"):
        counts["game_level"] += 1
    if game_info.get("overtime") is not None:
        counts["derived"] += 1
    if game_info.get("margin_of_victory") is not None:
        counts["derived"] += 1

    # Scoring features
    scoring = features.get("scoring", {})
    if scoring.get("home", {}).get("quarters"):
        counts["game_level"] += len(scoring["home"]["quarters"])
    if scoring.get("away", {}).get("quarters"):
        counts["game_level"] += len(scoring["away"]["quarters"])

    # Venue
    venue = features.get("venue", {})
    if venue.get("name"):
        counts["game_level"] += 1

    # Box score
    box_score = features.get("box_score", {})
    for team in ["home", "away"]:
        players = box_score.get(team, {}).get("players", [])
        for player in players:
            stats = player.get("stats", {})
            counts["player_stats"] += len([v for v in stats.values() if v is not None])

            # Count derived stats
            if stats.get("field_goal_pct") is not None:
                counts["derived"] += 1
            if stats.get("three_point_pct") is not None:
                counts["derived"] += 1
            if stats.get("free_throw_pct") is not None:
                counts["derived"] += 1
            if stats.get("double_double") is not None:
                counts["derived"] += 1
            if stats.get("triple_double") is not None:
                counts["derived"] += 1

    # Play-by-play
    pbp = features.get("plays_summary", {})
    if pbp.get("total_plays", 0) > 0:
        counts["play_by_play"] += 1

    return counts


def main():
    parser = argparse.ArgumentParser(description="Test ESPN Feature Extraction")
    parser.add_argument("--game-id", help="Test specific game ID")
    parser.add_argument("--sample", type=int, help="Test on N games")
    parser.add_argument("--single", action="store_true", help="Test single game only")

    args = parser.parse_args()

    if args.game_id:
        success = test_single_game(args.game_id)
    elif args.single:
        success = test_single_game()
    elif args.sample:
        success = test_batch_games(args.sample)
    else:
        # Default: test single game then batch
        success1 = test_single_game()
        success2 = test_batch_games(10)
        success = success1 and success2

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
