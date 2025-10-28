#!/usr/bin/env python3
"""
Simulate player props using historical statistics.

This script generates probability distributions for player prop bets
(points, rebounds, assists, etc.) using historical data and Monte Carlo simulation.

Usage:
    python scripts/betting/simulate_player_props.py --simulations-file data/betting/simulations_odds_2025-10-28.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from datetime import datetime


class PlayerPropsSimulator:
    """Simulate player performance for prop betting."""

    def __init__(self, n_simulations: int = 10000):
        self.n_simulations = n_simulations

    def get_player_projections(self, team_name: str) -> List[Dict[str, Any]]:
        """Get top player projections for a team (placeholder)."""
        # In production, would query database for actual player stats
        # For now, return sample projections
        return [
            {
                "name": f"{team_name} Star Player",
                "position": "G",
                "minutes_avg": 36.0,
                "points_avg": 27.5,
                "points_std": 6.2,
                "rebounds_avg": 5.3,
                "rebounds_std": 2.1,
                "assists_avg": 7.2,
                "assists_std": 2.5,
                "threes_avg": 3.2,
                "threes_std": 1.8,
            },
            {
                "name": f"{team_name} Forward",
                "position": "F",
                "minutes_avg": 32.0,
                "points_avg": 19.3,
                "points_std": 5.1,
                "rebounds_avg": 8.7,
                "rebounds_std": 2.8,
                "assists_avg": 3.1,
                "assists_std": 1.4,
                "threes_avg": 1.8,
                "threes_std": 1.3,
            },
        ]

    def simulate_player_performance(
        self, player_stats: Dict[str, Any]
    ) -> Dict[str, float]:
        """Simulate a single game performance for a player."""
        # Use normal distribution around historical averages
        points = max(
            0, np.random.normal(player_stats["points_avg"], player_stats["points_std"])
        )
        rebounds = max(
            0,
            np.random.normal(
                player_stats["rebounds_avg"], player_stats["rebounds_std"]
            ),
        )
        assists = max(
            0,
            np.random.normal(player_stats["assists_avg"], player_stats["assists_std"]),
        )
        threes = max(
            0, np.random.normal(player_stats["threes_avg"], player_stats["threes_std"])
        )

        return {
            "points": points,
            "rebounds": rebounds,
            "assists": assists,
            "threes": threes,
            "pra": points + rebounds + assists,  # Points + Rebounds + Assists combo
        }

    def calculate_prop_probabilities(
        self, simulations: List[Dict], line: float, stat: str
    ) -> Dict[str, float]:
        """Calculate over/under probabilities for a prop line."""
        values = [s[stat] for s in simulations]
        over_count = sum(1 for v in values if v > line)
        under_count = sum(1 for v in values if v < line)

        return {
            "line": line,
            "stat": stat,
            "over_probability": over_count / len(simulations),
            "under_probability": under_count / len(simulations),
            "push_probability": (len(simulations) - over_count - under_count)
            / len(simulations),
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
        }

    def simulate_game_props(self, game_data: Dict) -> Dict[str, Any]:
        """Simulate player props for a game."""
        home_team = game_data["home_team"]
        away_team = game_data["away_team"]

        # Get player projections
        home_players = self.get_player_projections(home_team)
        away_players = self.get_player_projections(away_team)

        all_props = {}

        for players, team_type in [(home_players, "home"), (away_players, "away")]:
            for player in players:
                player_key = f"{player['name']}_{team_type}"

                # Run simulations
                simulations = []
                for _ in range(self.n_simulations):
                    sim = self.simulate_player_performance(player)
                    simulations.append(sim)

                # Calculate probabilities for common lines
                props = {
                    "player_name": player["name"],
                    "team": team_type,
                    "position": player["position"],
                    "projections": {
                        "points": self.calculate_prop_probabilities(
                            simulations, player["points_avg"], "points"
                        ),
                        "rebounds": self.calculate_prop_probabilities(
                            simulations, player["rebounds_avg"], "rebounds"
                        ),
                        "assists": self.calculate_prop_probabilities(
                            simulations, player["assists_avg"], "assists"
                        ),
                        "threes": self.calculate_prop_probabilities(
                            simulations, player["threes_avg"], "threes"
                        ),
                        "pra": self.calculate_prop_probabilities(
                            simulations,
                            player["points_avg"]
                            + player["rebounds_avg"]
                            + player["assists_avg"],
                            "pra",
                        ),
                    },
                }

                all_props[player_key] = props

        return all_props


def simulate_all_player_props(
    games_data: Dict[str, Any], n_simulations: int = 10000
) -> Dict[str, Any]:
    """Simulate player props for all games."""
    print(f"\n{'='*70}")
    print(f"SIMULATING PLAYER PROPS ({n_simulations:,} per player)")
    print(f"{'='*70}\n")

    simulator = PlayerPropsSimulator(n_simulations=n_simulations)
    games = games_data["games"]
    games_with_props = []

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['away_team']} @ {game['home_team']}")
        print(f"   Simulating player props...")

        # Simulate props
        props = simulator.simulate_game_props(game)

        print(f"   ✓ Generated props for {len(props)} players\n")

        games_with_props.append(
            {
                **game,
                "player_props": props,
            }
        )

    result = {
        "date": games_data["date"],
        "simulated_at": datetime.now().isoformat(),
        "n_simulations_per_player": n_simulations,
        "total_games": len(games_with_props),
        "games": games_with_props,
    }

    print(f"{'='*70}")
    print(f"✅ Player props simulated for all {len(games)} games")
    print(f"{'='*70}\n")

    return result


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Simulate player props for NBA games")
    parser.add_argument(
        "--simulations-file",
        type=str,
        required=True,
        help="Input JSON file with game simulations",
    )
    parser.add_argument(
        "--n-simulations",
        type=int,
        default=10000,
        help="Number of simulations per player",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output JSON file path"
    )

    args = parser.parse_args()

    # Load simulations data
    try:
        with open(args.simulations_file, "r") as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading simulations file: {e}")
        return 1

    # Simulate props
    try:
        result = simulate_all_player_props(games_data, n_simulations=args.n_simulations)

        # Save to file
        if args.output:
            output_path = Path(args.output)
        else:
            input_path = Path(args.simulations_file)
            output_path = (
                input_path.parent
                / f"props_{input_path.name.replace('simulations_', '')}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"✅ Player props saved to: {output_path}\n")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
