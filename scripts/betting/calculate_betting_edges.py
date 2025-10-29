#!/usr/bin/env python3
"""
Calculate betting edges and expected value for all markets.

This script compares model probabilities vs market odds to identify
positive expected value (EV) betting opportunities.

Usage:
    python scripts/betting/calculate_betting_edges.py --props-file data/betting/props_odds_2025-10-28.json --min-edge 0.02
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


def american_to_probability(odds: float) -> float:
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def probability_to_american(prob: float) -> float:
    """Convert probability to American odds."""
    if prob >= 0.5:
        return -(prob / (1 - prob)) * 100
    else:
        return ((1 - prob) / prob) * 100


def calculate_ev(model_prob: float, market_odds: float) -> float:
    """
    Calculate expected value of a bet.

    EV = (Model Prob × Payout) - 1
    """
    if market_odds > 0:
        payout = (market_odds / 100) + 1
    else:
        payout = (100 / abs(market_odds)) + 1

    return (model_prob * payout) - 1


def kelly_criterion(model_prob: float, market_odds: float) -> float:
    """
    Calculate Kelly Criterion optimal bet size as fraction of bankroll.

    Kelly % = (bp - q) / b
    where b = decimal odds - 1, p = win probability, q = 1 - p
    """
    if market_odds > 0:
        b = market_odds / 100
    else:
        b = 100 / abs(market_odds)

    q = 1 - model_prob
    kelly = (model_prob * b - q) / b

    # Cap at 25% (full Kelly can be aggressive)
    return max(0.0, min(kelly, 0.25))


def calculate_confidence_level(model_prob: float, prob_std: float = 0.05) -> str:
    """Determine confidence level based on probability and uncertainty."""
    # Lower standard error = higher confidence
    if prob_std < 0.03:
        return "HIGH"
    elif prob_std < 0.06:
        return "MEDIUM"
    else:
        return "LOW"


def analyze_moneyline(game: Dict, consensus: Dict, simulation: Dict) -> List[Dict]:
    """Analyze moneyline betting opportunities."""
    opportunities = []

    if "h2h" not in consensus:
        return opportunities

    model_home_prob = simulation["win_probability"]["home"]
    model_away_prob = simulation["win_probability"]["away"]

    # Check each team
    for outcome_name, data in consensus["h2h"].items():
        if data["avg_price"] is None:
            continue

        market_odds = data["avg_price"]
        market_prob = american_to_probability(market_odds)

        # Determine which team
        is_home = "home" in outcome_name.lower() or game["home_team"] in outcome_name
        model_prob = model_home_prob if is_home else model_away_prob

        # Calculate edge
        edge = model_prob - market_prob
        ev = calculate_ev(model_prob, market_odds)
        kelly = kelly_criterion(model_prob, market_odds)

        if ev > 0:  # Positive EV
            opportunities.append(
                {
                    "market_type": "moneyline",
                    "team": game["home_team"] if is_home else game["away_team"],
                    "side": "home" if is_home else "away",
                    "recommendation": f"Bet {outcome_name}",
                    "market_odds": market_odds,
                    "model_probability": model_prob,
                    "market_probability": market_prob,
                    "edge": edge,
                    "expected_value": ev,
                    "kelly_fraction": kelly,
                    "confidence": calculate_confidence_level(model_prob),
                    "num_bookmakers": data["num_bookmakers"],
                }
            )

    return opportunities


def analyze_spread(game: Dict, consensus: Dict, simulation: Dict) -> List[Dict]:
    """Analyze spread betting opportunities."""
    opportunities = []

    if "spreads" not in consensus:
        return opportunities

    # Get model spread distribution
    spread_mean = simulation["spread_distribution"]["mean"]
    spread_std = simulation["spread_distribution"]["std"]

    for outcome_name, data in consensus["spreads"].items():
        if data["avg_point"] is None or data["avg_price"] is None:
            continue

        market_line = data["avg_point"]
        market_odds = data["avg_price"]
        market_prob = american_to_probability(market_odds)

        # Calculate probability of covering spread using normal CDF approximation
        from scipy import stats

        is_home = "home" in outcome_name.lower() or game["home_team"] in outcome_name

        if is_home:
            # Home team covers if actual spread > line
            model_prob = 1 - stats.norm.cdf(market_line, spread_mean, spread_std)
        else:
            # Away team covers if actual spread < -line
            model_prob = stats.norm.cdf(market_line, spread_mean, spread_std)

        edge = model_prob - market_prob
        ev = calculate_ev(model_prob, market_odds)
        kelly = kelly_criterion(model_prob, market_odds)

        if ev > 0:
            opportunities.append(
                {
                    "market_type": "spread",
                    "team": game["home_team"] if is_home else game["away_team"],
                    "side": "home" if is_home else "away",
                    "recommendation": f"{outcome_name} {market_line:+.1f}",
                    "line": market_line,
                    "market_odds": market_odds,
                    "model_probability": model_prob,
                    "market_probability": market_prob,
                    "edge": edge,
                    "expected_value": ev,
                    "kelly_fraction": kelly,
                    "confidence": calculate_confidence_level(
                        model_prob, prob_std=spread_std / 10
                    ),
                    "num_bookmakers": data["num_bookmakers"],
                }
            )

    return opportunities


def analyze_total(game: Dict, consensus: Dict, simulation: Dict) -> List[Dict]:
    """Analyze total (over/under) betting opportunities."""
    opportunities = []

    if "totals" not in consensus:
        return opportunities

    # Get model total distribution
    total_mean = simulation["total_distribution"]["mean"]
    total_std = simulation["total_distribution"]["std"]

    for outcome_name, data in consensus["totals"].items():
        if data["avg_point"] is None or data["avg_price"] is None:
            continue

        market_line = data["avg_point"]
        market_odds = data["avg_price"]
        market_prob = american_to_probability(market_odds)

        # Calculate probability using normal CDF
        from scipy import stats

        is_over = "over" in outcome_name.lower()

        if is_over:
            model_prob = 1 - stats.norm.cdf(market_line, total_mean, total_std)
        else:
            model_prob = stats.norm.cdf(market_line, total_mean, total_std)

        edge = model_prob - market_prob
        ev = calculate_ev(model_prob, market_odds)
        kelly = kelly_criterion(model_prob, market_odds)

        if ev > 0:
            opportunities.append(
                {
                    "market_type": "total",
                    "bet_type": "over" if is_over else "under",
                    "recommendation": f"{'OVER' if is_over else 'UNDER'} {market_line}",
                    "line": market_line,
                    "market_odds": market_odds,
                    "model_probability": model_prob,
                    "market_probability": market_prob,
                    "edge": edge,
                    "expected_value": ev,
                    "kelly_fraction": kelly,
                    "confidence": calculate_confidence_level(
                        model_prob, prob_std=total_std / 20
                    ),
                    "num_bookmakers": data["num_bookmakers"],
                }
            )

    return opportunities


def analyze_player_props(game: Dict) -> List[Dict]:
    """Analyze player prop betting opportunities using real player data."""
    opportunities = []

    # Check for new data structure with home_players and away_players
    all_players = []
    if "home_players" in game:
        all_players.extend(game["home_players"])
    if "away_players" in game:
        all_players.extend(game["away_players"])

    if not all_players:
        # Fallback to old structure if present
        if "player_props" in game:
            for player_key, props in game["player_props"].items():
                all_players.append(props)
        else:
            return opportunities

    # Analyze each player's props
    for player in all_players:
        player_name = player.get("name", player.get("player_name", "Unknown"))
        betting_lines = player.get("betting_lines", {})
        simulations = player.get("simulations", {})

        # For each stat type that has both a betting line and simulation
        for stat_type, line_value in betting_lines.items():
            if line_value is None:
                continue

            # Get simulation data for this stat type
            # Map player_assists -> assists, player_points -> points, etc.
            stat_key = stat_type.replace("player_", "")

            if stat_key not in simulations:
                continue

            sim_data = simulations[stat_key]

            # Assume market odds of -110 for both sides (standard vig)
            market_odds = -110
            market_prob = american_to_probability(market_odds)

            # Check over opportunity
            over_prob = sim_data.get("over_probability", 0.5)
            over_edge = over_prob - market_prob
            over_ev = calculate_ev(over_prob, market_odds)

            if over_ev > 0.01:  # Lower threshold for props (1% EV)
                opportunities.append(
                    {
                        "market_type": "player_prop",
                        "player": player_name,
                        "stat": stat_type,
                        "recommendation": f"{player_name} OVER {line_value:.1f} {stat_key}",
                        "line": line_value,
                        "market_odds": market_odds,
                        "model_probability": over_prob,
                        "market_probability": market_prob,
                        "edge": over_edge,
                        "expected_value": over_ev,
                        "kelly_fraction": kelly_criterion(over_prob, market_odds),
                        "confidence": calculate_confidence_level(over_prob),
                        "mean_projection": sim_data.get("mean", line_value),
                        "median_projection": sim_data.get("median", line_value),
                    }
                )

            # Check under opportunity
            under_prob = sim_data.get("under_probability", 0.5)
            under_edge = under_prob - market_prob
            under_ev = calculate_ev(under_prob, market_odds)

            if under_ev > 0.01:  # Lower threshold for props (1% EV)
                opportunities.append(
                    {
                        "market_type": "player_prop",
                        "player": player_name,
                        "stat": stat_type,
                        "recommendation": f"{player_name} UNDER {line_value:.1f} {stat_key}",
                        "line": line_value,
                        "market_odds": market_odds,
                        "model_probability": under_prob,
                        "market_probability": market_prob,
                        "edge": under_edge,
                        "expected_value": under_ev,
                        "kelly_fraction": kelly_criterion(under_prob, market_odds),
                        "confidence": calculate_confidence_level(under_prob),
                        "mean_projection": sim_data.get("mean", line_value),
                        "median_projection": sim_data.get("median", line_value),
                    }
                )

    return opportunities


def calculate_all_edges(
    games_data: Dict[str, Any], min_edge: float = 0.02
) -> Dict[str, Any]:
    """Calculate betting edges for all games."""
    print(f"\n{'='*70}")
    print(f"CALCULATING BETTING EDGES (min edge: {min_edge:.1%})")
    print(f"{'='*70}\n")

    # Import scipy if available
    try:
        from scipy import stats
    except ImportError:
        print(
            "⚠️  Warning: scipy not available, spread/total analysis will be approximate"
        )

    games = games_data["games"]
    all_opportunities = []

    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] {game['away_team']} @ {game['home_team']}")

        consensus = game.get("consensus", {})
        simulation = game.get("simulation_results", {})

        # Analyze each market type
        moneyline_opps = analyze_moneyline(game, consensus, simulation)
        spread_opps = analyze_spread(game, consensus, simulation)
        total_opps = analyze_total(game, consensus, simulation)
        prop_opps = analyze_player_props(game)

        game_opportunities = moneyline_opps + spread_opps + total_opps + prop_opps

        # Filter by minimum edge
        game_opportunities = [
            opp for opp in game_opportunities if opp["edge"] >= min_edge
        ]

        # Sort by expected value
        game_opportunities.sort(key=lambda x: x["expected_value"], reverse=True)

        print(f"   Found {len(game_opportunities)} opportunities:")
        print(f"   - Moneyline: {len(moneyline_opps)}")
        print(f"   - Spread: {len(spread_opps)}")
        print(f"   - Total: {len(total_opps)}")
        print(f"   - Props: {len(prop_opps)}")
        print()

        for opp in game_opportunities:
            opp["game"] = {
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "commence_time": game["commence_time"],
            }

        all_opportunities.extend(game_opportunities)

    # Sort all opportunities by EV
    all_opportunities.sort(key=lambda x: x["expected_value"], reverse=True)

    result = {
        "date": games_data["date"],
        "calculated_at": datetime.now().isoformat(),
        "min_edge_threshold": min_edge,
        "total_opportunities": len(all_opportunities),
        "total_games": len(games),
        "opportunities": all_opportunities,
        "summary": {
            "by_market_type": {},
            "by_confidence": {},
            "total_expected_value": sum(
                opp["expected_value"] for opp in all_opportunities
            ),
            "avg_edge": (
                sum(opp["edge"] for opp in all_opportunities) / len(all_opportunities)
                if all_opportunities
                else 0
            ),
        },
    }

    # Aggregate statistics
    for opp in all_opportunities:
        market_type = opp["market_type"]
        confidence = opp["confidence"]

        if market_type not in result["summary"]["by_market_type"]:
            result["summary"]["by_market_type"][market_type] = 0
        result["summary"]["by_market_type"][market_type] += 1

        if confidence not in result["summary"]["by_confidence"]:
            result["summary"]["by_confidence"][confidence] = 0
        result["summary"]["by_confidence"][confidence] += 1

    print(f"{'='*70}")
    print(f"EDGE CALCULATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total Opportunities: {result['total_opportunities']}")
    print(f"Average Edge: {result['summary']['avg_edge']:.2%}")
    print(f"Total Expected Value: {result['summary']['total_expected_value']:.2%}")
    print(f"\nBy Market Type:")
    for market_type, count in result["summary"]["by_market_type"].items():
        print(f"  - {market_type}: {count}")
    print(f"\nBy Confidence:")
    for confidence, count in result["summary"]["by_confidence"].items():
        print(f"  - {confidence}: {count}")
    print(f"{'='*70}\n")

    return result


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Calculate betting edges for NBA games"
    )
    parser.add_argument(
        "--props-file",
        type=str,
        required=True,
        help="Input JSON file with player props",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.02,
        help="Minimum edge threshold (default: 0.02 = 2%%)",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output JSON file path"
    )

    args = parser.parse_args()

    # Load props data
    try:
        with open(args.props_file, "r") as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading props file: {e}")
        return 1

    # Calculate edges
    try:
        result = calculate_all_edges(games_data, min_edge=args.min_edge)

        # Save to file
        if args.output:
            output_path = Path(args.output)
        else:
            input_path = Path(args.props_file)
            output_path = (
                input_path.parent / f"edges_{input_path.name.replace('props_', '')}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"✅ Betting edges saved to: {output_path}\n")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
