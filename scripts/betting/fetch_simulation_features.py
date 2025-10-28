#!/usr/bin/env python3
"""
Fetch historical team and player statistics for game simulations.

This script queries the database to build feature matrices needed for
ML predictions and Monte Carlo simulations.

Usage:
    python scripts/betting/fetch_simulation_features.py --games-file data/betting/odds_2025-10-28.json
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import pandas as pd

# Load credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"),
    "database": os.getenv("DB_NAME", "nba_simulator"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}


def normalize_team_name(team_name: str) -> str:
    """Normalize team names for database matching."""
    # Common mappings from odds API to database
    mappings = {
        "Los Angeles Lakers": "Lakers",
        "Los Angeles Clippers": "Clippers",
        "Golden State Warriors": "Warriors",
        "Boston Celtics": "Celtics",
        "Brooklyn Nets": "Nets",
        "New York Knicks": "Knicks",
        "Philadelphia 76ers": "76ers",
        "Milwaukee Bucks": "Bucks",
        "Miami Heat": "Heat",
        "Chicago Bulls": "Bulls",
        "Cleveland Cavaliers": "Cavaliers",
        "Toronto Raptors": "Raptors",
        "Atlanta Hawks": "Hawks",
        "Charlotte Hornets": "Hornets",
        "Washington Wizards": "Wizards",
        "Indiana Pacers": "Pacers",
        "Detroit Pistons": "Pistons",
        "Orlando Magic": "Magic",
        "Dallas Mavericks": "Mavericks",
        "Houston Rockets": "Rockets",
        "San Antonio Spurs": "Spurs",
        "Memphis Grizzlies": "Grizzlies",
        "New Orleans Pelicans": "Pelicans",
        "Denver Nuggets": "Nuggets",
        "Utah Jazz": "Jazz",
        "Phoenix Suns": "Suns",
        "Portland Trail Blazers": "Trail Blazers",
        "Sacramento Kings": "Kings",
        "Oklahoma City Thunder": "Thunder",
        "Minnesota Timberwolves": "Timberwolves",
    }

    # Try exact match first
    if team_name in mappings:
        return mappings[team_name]

    # Try extracting last word (team nickname)
    parts = team_name.split()
    if len(parts) > 1:
        return parts[-1]

    return team_name


def fetch_team_recent_stats(
    conn, team_name: str, before_date: datetime, n_games: int = 10
) -> Dict[str, float]:
    """Fetch recent rolling statistics for a team."""
    normalized_name = normalize_team_name(team_name)

    # Try to find team stats from recent games
    # This is a simplified version - in production would use master_team_game_stats
    query = """
        SELECT
            AVG(CASE WHEN team_id = %s THEN points ELSE 0 END) as avg_points,
            AVG(CASE WHEN team_id = %s THEN rebounds ELSE 0 END) as avg_rebounds,
            AVG(CASE WHEN team_id = %s THEN assists ELSE 0 END) as avg_assists,
            COUNT(DISTINCT game_id) as games_played
        FROM player_game_stats
        WHERE team_id LIKE %s
          AND created_at < %s
        LIMIT %s
    """

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    normalized_name,
                    normalized_name,
                    normalized_name,
                    f"%{normalized_name}%",
                    before_date,
                    n_games * 15,
                ),
            )  # 15 players per game
            result = cursor.fetchone()

            if result and result["games_played"] > 0:
                return dict(result)
    except Exception as e:
        print(f"   Warning: Could not fetch stats for {team_name}: {e}")

    # Return default stats if no data found
    return {
        "avg_points": 110.0,  # League average
        "avg_rebounds": 45.0,
        "avg_assists": 25.0,
        "games_played": 0,
    }


def calculate_derived_features(
    home_stats: Dict, away_stats: Dict, game_date: datetime
) -> Dict[str, float]:
    """Calculate derived features for ML model."""
    features = {}

    # Rolling averages
    features["home_rolling_ppg"] = home_stats.get("avg_points", 110.0)
    features["away_rolling_ppg"] = away_stats.get("avg_points", 110.0)
    features["home_rolling_rpg"] = home_stats.get("avg_rebounds", 45.0)
    features["away_rolling_rpg"] = away_stats.get("avg_rebounds", 45.0)
    features["home_rolling_apg"] = home_stats.get("avg_assists", 25.0)
    features["away_rolling_apg"] = away_stats.get("avg_assists", 25.0)

    # Offensive/defensive ratings (simplified)
    features["home_offensive_rating"] = features["home_rolling_ppg"]
    features["away_offensive_rating"] = features["away_rolling_ppg"]
    features["home_defensive_rating"] = 110.0  # Would calculate from opponent stats
    features["away_defensive_rating"] = 110.0

    # Pace (possessions per 48 minutes)
    features["home_pace"] = 100.0  # League average
    features["away_pace"] = 100.0

    # Efficiency (points per 100 possessions)
    features["home_efficiency"] = features["home_offensive_rating"]
    features["away_efficiency"] = features["away_offensive_rating"]

    # Home court advantage
    features["home_court_advantage"] = 3.5  # Historical NBA average

    # Temporal features
    features["month"] = game_date.month
    features["day_of_week"] = game_date.weekday()
    features["is_weekend"] = int(game_date.weekday() >= 5)

    # Season phase (early: 0, mid: 1, late: 2, playoffs: 3)
    if game_date.month in [10, 11]:
        features["season_phase"] = 0  # Early season
    elif game_date.month in [12, 1, 2]:
        features["season_phase"] = 1  # Mid season
    else:
        features["season_phase"] = 2  # Late season

    # Rest days (default to 2 for now - would calculate from schedule)
    features["home_rest_days"] = 2
    features["away_rest_days"] = 2
    features["home_back_to_back"] = 0
    features["away_back_to_back"] = 0

    # Win percentages (would calculate from actual records)
    features["home_win_pct"] = 0.500
    features["away_win_pct"] = 0.500

    return features


def fetch_features_for_games(games_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch simulation features for all games."""
    print(f"\n{'='*70}")
    print(f"FETCHING SIMULATION FEATURES")
    print(f"{'='*70}\n")

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        games = games_data["games"]
        print(f"Processing {len(games)} games...\n")

        games_with_features = []

        for i, game in enumerate(games, 1):
            print(f"[{i}/{len(games)}] {game['away_team']} @ {game['home_team']}")

            game_date = datetime.fromisoformat(game["commence_time"])

            # Fetch team statistics
            print(f"   Fetching home team stats...")
            home_stats = fetch_team_recent_stats(conn, game["home_team"], game_date)

            print(f"   Fetching away team stats...")
            away_stats = fetch_team_recent_stats(conn, game["away_team"], game_date)

            # Calculate features
            print(f"   Calculating derived features...")
            features = calculate_derived_features(home_stats, away_stats, game_date)

            games_with_features.append(
                {
                    **game,
                    "home_stats": home_stats,
                    "away_stats": away_stats,
                    "features": features,
                }
            )

            print(f"   ✓ Features calculated\n")

        result = {
            "date": games_data["date"],
            "fetched_at": datetime.now().isoformat(),
            "total_games": len(games_with_features),
            "games": games_with_features,
        }

        print(f"{'='*70}")
        print(f"✅ Features fetched for all {len(games)} games")
        print(f"{'='*70}\n")

        return result

    finally:
        conn.close()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Fetch simulation features for NBA games"
    )
    parser.add_argument(
        "--games-file",
        type=str,
        required=True,
        help="Input JSON file with games and odds",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output JSON file path"
    )

    args = parser.parse_args()

    # Load games data
    try:
        with open(args.games_file, "r") as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading games file: {e}")
        return 1

    # Fetch features
    try:
        result = fetch_features_for_games(games_data)

        # Save to file
        if args.output:
            output_path = Path(args.output)
        else:
            input_path = Path(args.games_file)
            output_path = input_path.parent / f"features_{input_path.name}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"✅ Features saved to: {output_path}\n")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
