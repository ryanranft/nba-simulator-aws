#!/usr/bin/env python3
"""
Run Monte Carlo simulations for NBA games.

This script runs 10,000 possession-by-possession simulations per game to generate
probability distributions for all betting markets.

Usage:
    python scripts/betting/run_game_simulations.py --predictions-file data/betting/predictions_odds_2025-10-28.json --n-simulations 10000
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from datetime import datetime
from collections import Counter


class GameSimulator:
    """Monte Carlo game simulator."""

    def __init__(self, n_simulations: int = 10000):
        self.n_simulations = n_simulations

    def simulate_possession(
        self, offensive_rating: float, defensive_rating: float, pace: float
    ) -> Tuple[int, int]:
        """
        Simulate a single possession.

        Returns:
            (points_scored, possession_duration_seconds)
        """
        # Points per possession (PPP) based on ratings
        expected_ppp = (offensive_rating / 100.0) * (
            100.0 / max(defensive_rating, 90.0)
        )

        # Outcome probabilities
        # Shot made (2pt): 40%, (3pt): 15%, FT: 10%, Turnover: 15%, Miss: 20%
        outcome = np.random.choice(
            ["2pt", "3pt", "ft", "turnover", "miss"], p=[0.40, 0.15, 0.10, 0.15, 0.20]
        )

        if outcome == "2pt":
            points = 2
        elif outcome == "3pt":
            points = 3
        elif outcome == "ft":
            points = np.random.choice([0, 1, 2], p=[0.2, 0.3, 0.5])  # FT attempts
        else:
            points = 0

        # Possession duration (10-24 seconds, mode at 18)
        duration = int(np.random.triangular(10, 18, 24))

        return points, duration

    def simulate_quarter(
        self,
        home_rating: float,
        away_rating: float,
        home_pace: float,
        away_pace: float,
        quarter_minutes: int = 12,
    ) -> Dict[str, int]:
        """Simulate a single quarter."""
        # Average pace between teams
        avg_pace = (home_pace + away_pace) / 2.0

        # Expected possessions in quarter
        possessions_per_48 = avg_pace
        expected_possessions = int(possessions_per_48 * quarter_minutes / 48.0)

        # Simulate possessions
        home_score = 0
        away_score = 0
        time_remaining = quarter_minutes * 60
        possession_count = 0

        while time_remaining > 0 and possession_count < expected_possessions * 2:
            # Alternate possessions
            if possession_count % 2 == 0:
                # Home possession
                points, duration = self.simulate_possession(
                    home_rating, away_rating, avg_pace
                )
                home_score += points
            else:
                # Away possession
                points, duration = self.simulate_possession(
                    away_rating, home_rating, avg_pace
                )
                away_score += points

            time_remaining -= duration
            possession_count += 1

        return {
            "home_score": home_score,
            "away_score": away_score,
            "possessions": possession_count,
        }

    def simulate_game(self, home_features: Dict, away_features: Dict) -> Dict[str, Any]:
        """Simulate a complete game."""
        # Extract features
        home_rating = home_features.get("home_offensive_rating", 110.0)
        away_rating = away_features.get("away_offensive_rating", 110.0)
        home_pace = home_features.get("home_pace", 100.0)
        away_pace = home_features.get("away_pace", 100.0)

        # Simulate 4 quarters
        quarters = []
        total_home = 0
        total_away = 0

        for q in range(4):
            quarter_result = self.simulate_quarter(
                home_rating, away_rating, home_pace, away_pace
            )
            quarters.append(quarter_result)
            total_home += quarter_result["home_score"]
            total_away += quarter_result["away_score"]

        # Overtime if tied (simplified - just one OT)
        if total_home == total_away:
            ot_result = self.simulate_quarter(
                home_rating, away_rating, home_pace, away_pace, quarter_minutes=5
            )
            quarters.append(ot_result)
            total_home += ot_result["home_score"]
            total_away += ot_result["away_score"]

        return {
            "home_score": total_home,
            "away_score": total_away,
            "quarters": quarters,
            "home_won": total_home > total_away,
            "spread": total_home - total_away,
            "total": total_home + total_away,
        }

    def run_simulations(self, game_data: Dict) -> Dict[str, Any]:
        """Run N simulations for a game and aggregate results."""
        print(f"   Running {self.n_simulations:,} simulations...")

        home_features = game_data["features"]
        away_features = game_data["features"]  # Would separate in production

        # Run simulations
        results = []
        for _ in range(self.n_simulations):
            sim_result = self.simulate_game(home_features, away_features)
            results.append(sim_result)

        # Aggregate results
        home_wins = sum(1 for r in results if r["home_won"])
        home_scores = [r["home_score"] for r in results]
        away_scores = [r["away_score"] for r in results]
        spreads = [r["spread"] for r in results]
        totals = [r["total"] for r in results]

        # Calculate probabilities and distributions
        aggregated = {
            "n_simulations": self.n_simulations,
            "win_probability": {
                "home": home_wins / self.n_simulations,
                "away": (self.n_simulations - home_wins) / self.n_simulations,
            },
            "score_distribution": {
                "home": {
                    "mean": np.mean(home_scores),
                    "median": np.median(home_scores),
                    "std": np.std(home_scores),
                    "min": np.min(home_scores),
                    "max": np.max(home_scores),
                    "percentiles": {
                        "5": np.percentile(home_scores, 5),
                        "25": np.percentile(home_scores, 25),
                        "75": np.percentile(home_scores, 75),
                        "95": np.percentile(home_scores, 95),
                    },
                },
                "away": {
                    "mean": np.mean(away_scores),
                    "median": np.median(away_scores),
                    "std": np.std(away_scores),
                    "min": np.min(away_scores),
                    "max": np.max(away_scores),
                    "percentiles": {
                        "5": np.percentile(away_scores, 5),
                        "25": np.percentile(away_scores, 25),
                        "75": np.percentile(away_scores, 75),
                        "95": np.percentile(away_scores, 95),
                    },
                },
            },
            "spread_distribution": {
                "mean": np.mean(spreads),
                "median": np.median(spreads),
                "std": np.std(spreads),
                "percentiles": {
                    "5": np.percentile(spreads, 5),
                    "25": np.percentile(spreads, 25),
                    "75": np.percentile(spreads, 75),
                    "95": np.percentile(spreads, 95),
                },
            },
            "total_distribution": {
                "mean": np.mean(totals),
                "median": np.median(totals),
                "std": np.std(totals),
                "percentiles": {
                    "5": np.percentile(totals, 5),
                    "25": np.percentile(totals, 25),
                    "75": np.percentile(totals, 75),
                    "95": np.percentile(totals, 95),
                },
            },
            "raw_results": results[:100],  # Store first 100 for inspection
        }

        return aggregated


def calculate_betting_probabilities(
    sim_results: Dict, consensus: Dict
) -> Dict[str, Any]:
    """Calculate probabilities for specific betting lines."""
    probabilities = {}

    # Spread probabilities
    if "spreads" in consensus:
        for team, data in consensus["spreads"].items():
            if data["avg_point"] is not None:
                line = data["avg_point"]
                # Calculate probability of covering
                spreads = [r["spread"] for r in sim_results["raw_results"]]
                if "home" in team.lower():
                    covers = sum(1 for s in spreads if s > line) / len(spreads)
                else:
                    covers = sum(1 for s in spreads if s < line) / len(spreads)

                probabilities[f"spread_{team}_{line}"] = {
                    "line": line,
                    "probability": covers,
                    "edge_type": "spread",
                }

    # Total probabilities
    if "totals" in consensus:
        for outcome, data in consensus["totals"].items():
            if data["avg_point"] is not None:
                line = data["avg_point"]
                totals = [r["total"] for r in sim_results["raw_results"]]

                if "over" in outcome.lower():
                    over_prob = sum(1 for t in totals if t > line) / len(totals)
                    probabilities[f"total_over_{line}"] = {
                        "line": line,
                        "probability": over_prob,
                        "edge_type": "total",
                    }
                elif "under" in outcome.lower():
                    under_prob = sum(1 for t in totals if t < line) / len(totals)
                    probabilities[f"total_under_{line}"] = {
                        "line": line,
                        "probability": under_prob,
                        "edge_type": "total",
                    }

    return probabilities


def run_all_simulations(
    games_data: Dict[str, Any], n_simulations: int = 10000
) -> Dict[str, Any]:
    """Run simulations for all games."""
    print(f"\n{'='*70}")
    print(f"RUNNING MONTE CARLO SIMULATIONS ({n_simulations:,} per game)")
    print(f"{'='*70}\n")

    simulator = GameSimulator(n_simulations=n_simulations)
    games = games_data["games"]
    games_with_simulations = []

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['away_team']} @ {game['home_team']}")

        # Run simulations
        sim_results = simulator.run_simulations(game)

        # Calculate betting probabilities
        betting_probs = calculate_betting_probabilities(
            sim_results, game.get("consensus", {})
        )

        # Print summary
        print(
            f"   Win Probability: {sim_results['win_probability']['home']:.1%} (home)"
        )
        print(
            f"   Expected Score: {sim_results['score_distribution']['home']['mean']:.1f} - {sim_results['score_distribution']['away']['mean']:.1f}"
        )
        print(f"   Expected Spread: {sim_results['spread_distribution']['mean']:+.1f}")
        print(f"   Expected Total: {sim_results['total_distribution']['mean']:.1f}")
        print(f"   ✓ Simulations complete\n")

        games_with_simulations.append(
            {
                **game,
                "simulation_results": sim_results,
                "betting_probabilities": betting_probs,
            }
        )

    result = {
        "date": games_data["date"],
        "simulated_at": datetime.now().isoformat(),
        "n_simulations_per_game": n_simulations,
        "total_games": len(games_with_simulations),
        "games": games_with_simulations,
    }

    print(f"{'='*70}")
    print(f"✅ Simulations complete for all {len(games)} games")
    print(f"   Total simulations run: {n_simulations * len(games):,}")
    print(f"{'='*70}\n")

    return result


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Run Monte Carlo simulations for NBA games"
    )
    parser.add_argument(
        "--predictions-file",
        type=str,
        required=True,
        help="Input JSON file with ML predictions",
    )
    parser.add_argument(
        "--n-simulations",
        type=int,
        default=10000,
        help="Number of simulations per game",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output JSON file path"
    )

    args = parser.parse_args()

    # Load predictions data
    try:
        with open(args.predictions_file, "r") as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading predictions file: {e}")
        return 1

    # Run simulations
    try:
        result = run_all_simulations(games_data, n_simulations=args.n_simulations)

        # Save to file
        if args.output:
            output_path = Path(args.output)
        else:
            input_path = Path(args.predictions_file)
            output_path = (
                input_path.parent
                / f"simulations_{input_path.name.replace('predictions_', '')}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"✅ Simulation results saved to: {output_path}\n")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
