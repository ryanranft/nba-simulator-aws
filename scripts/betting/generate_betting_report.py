#!/usr/bin/env python3
"""
Generate comprehensive betting recommendations report.

This script consolidates all analysis into formatted reports (Markdown, JSON, CSV).

Usage:
    python scripts/betting/generate_betting_report.py --edges-file data/betting/edges_odds_2025-10-28.json
"""

import os
import sys
import json
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def format_confidence_stars(confidence: str) -> str:
    """Convert confidence level to star rating."""
    if confidence == "HIGH":
        return "⭐⭐⭐"
    elif confidence == "MEDIUM":
        return "⭐⭐"
    else:
        return "⭐"


def generate_markdown_report(edges_data: Dict[str, Any], output_path: Path):
    """Generate Markdown report."""
    print(f"   Generating Markdown report...")

    with open(output_path, "w") as f:
        # Header
        f.write(f"# NBA Betting Recommendations - {edges_data['date']}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Games Analyzed:** {edges_data['total_games']}\n")
        f.write(f"- **Betting Opportunities:** {edges_data['total_opportunities']}\n")
        f.write(f"- **Average Edge:** {edges_data['summary']['avg_edge']:.2%}\n")
        f.write(
            f"- **Total Expected Value:** {edges_data['summary']['total_expected_value']:.2%}\n"
        )
        f.write(
            f"- **Minimum Edge Threshold:** {edges_data['min_edge_threshold']:.1%}\n\n"
        )

        # Market Type Breakdown
        f.write("### Opportunities by Market Type\n\n")
        for market_type, count in edges_data["summary"]["by_market_type"].items():
            f.write(f"- **{market_type.replace('_', ' ').title()}:** {count}\n")
        f.write("\n")

        # Confidence Breakdown
        f.write("### Opportunities by Confidence Level\n\n")
        for confidence, count in edges_data["summary"]["by_confidence"].items():
            stars = format_confidence_stars(confidence)
            f.write(f"- **{confidence} {stars}:** {count}\n")
        f.write("\n---\n\n")

        # High-Confidence Recommendations
        f.write("## High-Confidence Recommendations\n\n")

        high_conf_opps = [
            opp for opp in edges_data["opportunities"] if opp["confidence"] == "HIGH"
        ]

        if high_conf_opps:
            for i, opp in enumerate(high_conf_opps[:10], 1):  # Top 10
                game = opp["game"]
                f.write(f"### {i}. {game['away_team']} @ {game['home_team']}\n\n")
                f.write(f"**Game Time:** {game['commence_time']}\n\n")
                f.write(f"**Recommendation:** {opp['recommendation']}\n\n")
                f.write(
                    f"- **Market Type:** {opp['market_type'].replace('_', ' ').title()}\n"
                )
                f.write(f"- **Market Odds:** {opp['market_odds']:+.0f}\n")
                f.write(f"- **Model Probability:** {opp['model_probability']:.1%}\n")
                f.write(
                    f"- **Market Implied Probability:** {opp['market_probability']:.1%}\n"
                )
                f.write(f"- **Edge:** +{opp['edge']:.1%}\n")
                f.write(f"- **Expected Value:** {opp['expected_value']:.2%}\n")
                f.write(f"- **Kelly Fraction:** {opp['kelly_fraction']:.2%}\n")
                f.write(
                    f"- **Confidence:** {opp['confidence']} {format_confidence_stars(opp['confidence'])}\n\n"
                )
                f.write("---\n\n")
        else:
            f.write("*No high-confidence opportunities found.*\n\n")

        # All Opportunities by Game
        f.write("## All Opportunities by Game\n\n")

        # Group by game
        games_dict = {}
        for opp in edges_data["opportunities"]:
            game_key = f"{opp['game']['away_team']} @ {opp['game']['home_team']}"
            if game_key not in games_dict:
                games_dict[game_key] = {"game": opp["game"], "opportunities": []}
            games_dict[game_key]["opportunities"].append(opp)

        for game_key, game_data in games_dict.items():
            f.write(f"### {game_key}\n\n")
            f.write(f"**Time:** {game_data['game']['commence_time']}\n\n")

            if game_data["opportunities"]:
                for opp in game_data["opportunities"]:
                    f.write(
                        f"#### {opp['recommendation']} ({opp['market_type'].replace('_', ' ').title()})\n\n"
                    )
                    f.write(f"- Edge: +{opp['edge']:.1%}\n")
                    f.write(f"- EV: {opp['expected_value']:.2%}\n")
                    f.write(f"- Kelly: {opp['kelly_fraction']:.2%}\n")
                    f.write(
                        f"- Confidence: {opp['confidence']} {format_confidence_stars(opp['confidence'])}\n\n"
                    )
            else:
                f.write("*No opportunities found for this game.*\n\n")

        # Risk Warning
        f.write("---\n\n")
        f.write("## Risk Considerations\n\n")
        f.write(
            "- **Model Limitations:** Predictions based on historical data; unexpected events can affect outcomes\n"
        )
        f.write(
            "- **Bankroll Management:** Never bet more than Kelly Criterion suggests\n"
        )
        f.write(
            "- **Conservative Approach:** Consider using 1/4 Kelly for reduced variance\n"
        )
        f.write("- **Vig Impact:** Bookmaker juice reduces edges\n")
        f.write("- **Data Freshness:** Ensure odds are current before placing bets\n\n")

        f.write("---\n\n")
        f.write("*Report generated by NBA Simulator AWS betting analysis system*\n")

    print(f"   ✓ Markdown report saved")


def generate_csv_report(edges_data: Dict[str, Any], output_path: Path):
    """Generate CSV report."""
    print(f"   Generating CSV report...")

    with open(output_path, "w", newline="") as f:
        fieldnames = [
            "game",
            "commence_time",
            "market_type",
            "recommendation",
            "market_odds",
            "model_probability",
            "market_probability",
            "edge",
            "expected_value",
            "kelly_fraction",
            "confidence",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for opp in edges_data["opportunities"]:
            writer.writerow(
                {
                    "game": f"{opp['game']['away_team']} @ {opp['game']['home_team']}",
                    "commence_time": opp["game"]["commence_time"],
                    "market_type": opp["market_type"],
                    "recommendation": opp["recommendation"],
                    "market_odds": opp["market_odds"],
                    "model_probability": f"{opp['model_probability']:.3f}",
                    "market_probability": f"{opp['market_probability']:.3f}",
                    "edge": f"{opp['edge']:.3f}",
                    "expected_value": f"{opp['expected_value']:.3f}",
                    "kelly_fraction": f"{opp['kelly_fraction']:.3f}",
                    "confidence": opp["confidence"],
                }
            )

    print(f"   ✓ CSV report saved")


def generate_reports(edges_data: Dict[str, Any], output_dir: Path):
    """Generate all report formats."""
    print(f"\n{'='*70}")
    print(f"GENERATING BETTING REPORTS")
    print(f"{'='*70}\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = edges_data["date"]

    # Generate reports
    markdown_path = output_dir / f"betting_recommendations_{date_str}.md"
    generate_markdown_report(edges_data, markdown_path)

    csv_path = output_dir / f"betting_edges_{date_str}.csv"
    generate_csv_report(edges_data, csv_path)

    # Also save complete JSON
    json_path = output_dir / f"betting_analysis_{date_str}.json"
    with open(json_path, "w") as f:
        json.dump(edges_data, f, indent=2, default=str)
    print(f"   ✓ JSON data saved")

    print(f"\n{'='*70}")
    print(f"✅ REPORTS GENERATED")
    print(f"{'='*70}")
    print(f"Markdown: {markdown_path}")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"{'='*70}\n")

    return {
        "markdown": str(markdown_path),
        "csv": str(csv_path),
        "json": str(json_path),
    }


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Generate betting recommendations report"
    )
    parser.add_argument(
        "--edges-file",
        type=str,
        required=True,
        help="Input JSON file with betting edges",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/betting",
        help="Output directory for reports",
    )

    args = parser.parse_args()

    # Load edges data
    try:
        with open(args.edges_file, "r") as f:
            edges_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading edges file: {e}")
        return 1

    # Generate reports
    try:
        output_dir = Path(args.output_dir)
        report_paths = generate_reports(edges_data, output_dir)

        print(f"✅ All reports generated successfully!\n")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
