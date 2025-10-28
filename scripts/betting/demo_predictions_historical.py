#!/usr/bin/env python3
"""
Generate predictions for historical games (without betting odds).

This demonstrates the ML predictions and Monte Carlo simulations
using historical game data from the games table.

Usage:
    python scripts/betting/demo_predictions_historical.py --date 2024-10-28
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import numpy as np

# Load credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}


def fetch_games_from_db(target_date: str):
    """Fetch games from the games table."""
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    game_id,
                    game_date,
                    home_team_id,
                    away_team_id,
                    home_score,
                    away_score,
                    venue
                FROM games
                WHERE game_date = %s
                ORDER BY game_id
            """, (target_date,))

            games = cursor.fetchall()
            return [dict(game) for game in games]
    finally:
        conn.close()


def generate_predictions(game):
    """Generate ML prediction for a game (heuristic)."""
    # Simple heuristic: slight home court advantage
    home_win_prob = 0.55
    home_score = 110.0
    away_score = 107.0

    return {
        "game_id": game["game_id"],
        "home_team": game["home_team_id"],
        "away_team": game["away_team_id"],
        "home_win_probability": home_win_prob,
        "away_win_probability": 1 - home_win_prob,
        "predicted_home_score": home_score,
        "predicted_away_score": away_score,
        "predicted_spread": home_score - away_score,
        "predicted_total": home_score + away_score,
        "actual_home_score": game.get("home_score"),
        "actual_away_score": game.get("away_score"),
    }


def run_monte_carlo(n_simulations=10000):
    """Run Monte Carlo simulation for a game."""
    results = []

    for _ in range(n_simulations):
        # Simulate scores
        home_score = int(np.random.normal(110, 10))
        away_score = int(np.random.normal(107, 10))

        results.append({
            "home_score": home_score,
            "away_score": away_score,
            "home_won": home_score > away_score,
            "spread": home_score - away_score,
            "total": home_score + away_score,
        })

    # Aggregate
    home_wins = sum(1 for r in results if r["home_won"])
    spreads = [r["spread"] for r in results]
    totals = [r["total"] for r in results]

    return {
        "n_simulations": n_simulations,
        "win_probability_home": home_wins / n_simulations,
        "expected_spread": np.mean(spreads),
        "spread_std": np.std(spreads),
        "expected_total": np.mean(totals),
        "total_std": np.std(totals),
        "spread_percentiles": {
            "5th": np.percentile(spreads, 5),
            "25th": np.percentile(spreads, 25),
            "50th": np.percentile(spreads, 50),
            "75th": np.percentile(spreads, 75),
            "95th": np.percentile(spreads, 95),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate predictions for historical NBA games"
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--n-simulations",
        type=int,
        default=10000,
        help="Number of simulations per game"
    )

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"NBA GAME PREDICTIONS FOR {args.date}")
    print(f"{'='*70}\n")

    # Fetch games
    print(f"Fetching games from database...")
    games = fetch_games_from_db(args.date)
    print(f"✓ Found {len(games)} games\n")

    if not games:
        print(f"❌ No games found for {args.date}")
        return 1

    # Process each game
    results = []

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['away_team_id']} @ {game['home_team_id']}")

        # Generate prediction
        prediction = generate_predictions(game)

        # Run Monte Carlo
        print(f"   Running {args.n_simulations:,} simulations...")
        simulation = run_monte_carlo(args.n_simulations)

        # Combine
        result = {
            **prediction,
            "simulation": simulation,
        }

        results.append(result)

        # Print summary
        print(f"   ML Prediction: {prediction['predicted_home_score']:.1f} - {prediction['predicted_away_score']:.1f}")
        print(f"   Simulation: {simulation['expected_spread']:+.1f} spread, {simulation['expected_total']:.1f} total")

        if game.get("home_score"):
            actual_spread = game["home_score"] - game["away_score"]
            actual_total = game["home_score"] + game["away_score"]
            print(f"   Actual: {game['home_score']} - {game['away_score']} ({actual_spread:+.0f} spread, {actual_total} total)")

        print()

    # Save results
    output_path = Path(f"data/betting/predictions_demo_{args.date}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({
            "date": args.date,
            "generated_at": datetime.now().isoformat(),
            "n_simulations": args.n_simulations,
            "games": results,
        }, f, indent=2, default=str)

    print(f"{'='*70}")
    print(f"✅ Predictions saved to: {output_path}")
    print(f"{'='*70}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

