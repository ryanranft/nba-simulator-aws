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
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


class PlayerPropsSimulator:
    """Simulate player performance for prop betting."""

    def __init__(self, n_simulations: int = 10000, db_conn=None):
        self.n_simulations = n_simulations
        self.conn = db_conn

    def get_player_recent_stats(
        self, player_name: str, n_games: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Get recent statistics for a specific player from database."""
        if not self.conn:
            return None

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Query last N games for this player
                cursor.execute(
                    """
                    SELECT
                        athlete_display_name as player_name,
                        AVG(points) as points_avg,
                        STDDEV(points) as points_std,
                        AVG(rebounds) as rebounds_avg,
                        STDDEV(rebounds) as rebounds_std,
                        AVG(assists) as assists_avg,
                        STDDEV(assists) as assists_std,
                        AVG(three_point_field_goals_made) as threes_avg,
                        STDDEV(three_point_field_goals_made) as threes_std,
                        AVG(minutes) as minutes_avg,
                        COUNT(*) as games_played
                    FROM (
                        SELECT * FROM hoopr_player_box
                        WHERE athlete_display_name = %s
                        AND game_date < CURRENT_DATE
                        AND minutes > 0
                        ORDER BY game_date DESC
                        LIMIT %s
                    ) recent_games
                    GROUP BY athlete_display_name
                    """,
                    (player_name, n_games),
                )
                result = cursor.fetchone()

                if result and result["games_played"] >= 3:  # Need at least 3 games
                    return {
                        "name": player_name,
                        "games_played": int(result["games_played"]),
                        "minutes_avg": float(result["minutes_avg"] or 0),
                        "points_avg": float(result["points_avg"] or 0),
                        "points_std": max(3.0, float(result["points_std"] or 5.0)),
                        "rebounds_avg": float(result["rebounds_avg"] or 0),
                        "rebounds_std": max(1.5, float(result["rebounds_std"] or 2.0)),
                        "assists_avg": float(result["assists_avg"] or 0),
                        "assists_std": max(1.0, float(result["assists_std"] or 1.5)),
                        "threes_avg": float(result["threes_avg"] or 0),
                        "threes_std": max(0.5, float(result["threes_std"] or 1.0)),
                    }
        except Exception as e:
            print(f"   ⚠️  Could not fetch stats for {player_name}: {e}")

        return None

    def get_players_with_odds(
        self, event_id: str, home_team: str, away_team: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get all players who have betting lines for this game."""
        if not self.conn:
            return {"home": [], "away": []}

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all unique players with prop bets for this game
                query = """
                    SELECT DISTINCT
                        REGEXP_REPLACE(os.outcome_name, ' (Over|Under)$$', '') as player_name,
                        mt.market_key,
                        os.point
                    FROM odds.odds_snapshots os
                    JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
                    WHERE os.event_id = %s
                      AND mt.market_key LIKE 'player_%%'
                      AND os.outcome_name LIKE '%%Over'
                      AND os.is_latest = true
                    ORDER BY player_name, mt.market_key
                """
                cursor.execute(query, (event_id,))
                odds_players = cursor.fetchall()

                if not odds_players:
                    return {"home": [], "away": []}

                players_data = {"home": [], "away": []}

                for row in odds_players:
                    player_name = row.get("player_name")
                    market_key = row.get("market_key")
                    line = float(row["point"]) if row.get("point") else None

                    if not player_name:
                        continue

                    # Get player stats
                    stats = self.get_player_recent_stats(player_name)

                    if stats:
                        # Try to determine team (simplified - could enhance with team lookup)
                        player_data = {
                            "name": player_name,
                            "stats": stats,
                            "lines": {market_key: line} if line else {},
                        }

                        # Simple heuristic: alternate teams for display
                        # In production: query player's actual team
                        if len(players_data["home"]) <= len(players_data["away"]):
                            players_data["home"].append(player_data)
                        else:
                            players_data["away"].append(player_data)

                return players_data

        except Exception as e:
            print(f"   ⚠️  Error fetching players with odds: {e}")
            import traceback

            traceback.print_exc()
            return {"home": [], "away": []}

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
        """Simulate player props for a game using real NBA player data."""
        event_id = game_data.get("event_id")
        home_team = game_data["home_team"]
        away_team = game_data["away_team"]

        if not event_id or not self.conn:
            print(f"   ⚠️  No event_id or database connection - skipping player props")
            return {"home_players": [], "away_players": []}

        # Get players with betting lines for this game
        players_by_team = self.get_players_with_odds(event_id, home_team, away_team)

        home_props = []
        away_props = []

        # Simulate home team players
        for player_data in players_by_team.get("home", []):
            player_stats = player_data["stats"]
            betting_lines = player_data.get("lines", {})

            # Run simulations
            simulations = []
            for _ in range(self.n_simulations):
                sim = self.simulate_player_performance(player_stats)
                simulations.append(sim)

            # Calculate probabilities ONLY for stats with betting lines, using actual betting lines
            sim_results = {}
            for market_key, line_value in betting_lines.items():
                # Map player_points -> points, player_assists -> assists, etc.
                stat_key = market_key.replace("player_", "")

                # Map combo props to our simulation keys
                if stat_key == "points_rebounds_assists":
                    stat_key = "pra"
                elif stat_key in [
                    "points_rebounds",
                    "points_assists",
                    "rebounds_assists",
                ]:
                    # Skip combo props we don't have simulations for
                    continue
                elif stat_key in ["double_double", "triple_double", "blocks", "steals"]:
                    # Skip props we don't simulate
                    continue

                # Only calculate if we have this stat type in simulations
                if stat_key not in ["points", "rebounds", "assists", "threes", "pra"]:
                    continue

                # Calculate probabilities against the ACTUAL betting line
                sim_results[stat_key] = self.calculate_prop_probabilities(
                    simulations, line_value, stat_key
                )

            # Calculate projections
            props = {
                "name": player_data["name"],
                "games_played": player_stats["games_played"],
                "projections": {
                    "points": player_stats["points_avg"],
                    "rebounds": player_stats["rebounds_avg"],
                    "assists": player_stats["assists_avg"],
                    "threes": player_stats["threes_avg"],
                },
                "simulations": sim_results,
                "betting_lines": betting_lines,
            }
            home_props.append(props)

        # Simulate away team players
        for player_data in players_by_team.get("away", []):
            player_stats = player_data["stats"]
            betting_lines = player_data.get("lines", {})

            # Run simulations
            simulations = []
            for _ in range(self.n_simulations):
                sim = self.simulate_player_performance(player_stats)
                simulations.append(sim)

            # Calculate probabilities ONLY for stats with betting lines, using actual betting lines
            sim_results = {}
            for market_key, line_value in betting_lines.items():
                # Map player_points -> points, player_assists -> assists, etc.
                stat_key = market_key.replace("player_", "")

                # Map combo props to our simulation keys
                if stat_key == "points_rebounds_assists":
                    stat_key = "pra"
                elif stat_key in [
                    "points_rebounds",
                    "points_assists",
                    "rebounds_assists",
                ]:
                    # Skip combo props we don't have simulations for
                    continue
                elif stat_key in ["double_double", "triple_double", "blocks", "steals"]:
                    # Skip props we don't simulate
                    continue

                # Only calculate if we have this stat type in simulations
                if stat_key not in ["points", "rebounds", "assists", "threes", "pra"]:
                    continue

                # Calculate probabilities against the ACTUAL betting line
                sim_results[stat_key] = self.calculate_prop_probabilities(
                    simulations, line_value, stat_key
                )

            # Calculate projections
            props = {
                "name": player_data["name"],
                "games_played": player_stats["games_played"],
                "projections": {
                    "points": player_stats["points_avg"],
                    "rebounds": player_stats["rebounds_avg"],
                    "assists": player_stats["assists_avg"],
                    "threes": player_stats["threes_avg"],
                },
                "simulations": sim_results,
                "betting_lines": betting_lines,
            }
            away_props.append(props)

        return {"home_players": home_props, "away_players": away_props}


def simulate_all_player_props(
    games_data: Dict[str, Any], n_simulations: int = 10000, db_conn=None
) -> Dict[str, Any]:
    """Simulate player props for all games using real NBA player data."""
    print(f"\n{'='*70}")
    print(f"SIMULATING PLAYER PROPS ({n_simulations:,} per player)")
    print(f"{'='*70}\n")

    simulator = PlayerPropsSimulator(n_simulations=n_simulations, db_conn=db_conn)
    games = games_data["games"]
    games_with_props = []

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['away_team']} @ {game['home_team']}")
        print(f"   Fetching real player stats and simulating props...")

        # Simulate props with real player data
        props = simulator.simulate_game_props(game)

        home_count = len(props.get("home_players", []))
        away_count = len(props.get("away_players", []))
        total_players = home_count + away_count

        if total_players > 0:
            print(
                f"   ✓ Generated props for {total_players} players ({home_count} home, {away_count} away)\n"
            )
        else:
            print(f"   ⚠️  No player props data available\n")

        games_with_props.append(
            {
                # Keep compatible with existing pipeline structure
                "event_id": game.get("event_id"),
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "commence_time": game.get("commence_time"),
                # Add player props data
                "home_players": props.get("home_players", []),
                "away_players": props.get("away_players", []),
            }
        )

    total_players = sum(
        len(g["home_players"]) + len(g["away_players"]) for g in games_with_props
    )

    result = {
        "date": games_data["date"],
        "simulated_at": datetime.now().isoformat(),
        "n_simulations_per_player": n_simulations,
        "total_games": len(games_with_props),
        "total_players": total_players,
        "games": games_with_props,
    }

    print(f"{'='*70}")
    print(f"✅ Player props simulated for {len(games)} games")
    print(f"   Total players with props: {total_players}")
    print(f"{'='*70}\n")

    return result


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Simulate player props for NBA games using real player data"
    )
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

    # Load environment variables
    load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

    # Connect to database
    db_conn = None
    try:
        db_conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            sslmode="require",
        )
        print("✓ Connected to RDS database")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to database: {e}")
        print("   Will generate generic player projections without real data\n")

    # Load simulations data
    try:
        with open(args.simulations_file, "r") as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading simulations file: {e}")
        if db_conn:
            db_conn.close()
        return 1

    # Simulate props
    try:
        result = simulate_all_player_props(
            games_data, n_simulations=args.n_simulations, db_conn=db_conn
        )

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

        # Close database connection
        if db_conn:
            db_conn.close()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

        # Close database connection
        if db_conn:
            db_conn.close()

        return 1


if __name__ == "__main__":
    sys.exit(main())
