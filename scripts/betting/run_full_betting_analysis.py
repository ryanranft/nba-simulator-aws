#!/usr/bin/env python3
"""
Master orchestrator for comprehensive betting analysis.

This script runs the entire betting analysis pipeline:
1. Fetch odds from database
2. Fetch simulation features
3. Generate ML predictions
4. Run Monte Carlo simulations
5. Simulate player props
6. Calculate betting edges
7. Generate comprehensive reports

Usage:
    python scripts/betting/run_full_betting_analysis.py --date 2025-10-28
    python scripts/betting/run_full_betting_analysis.py --date 2025-10-28 --n-simulations 10000 --min-edge 0.02
"""

import os
import sys
import json
import argparse
import subprocess  # nosec B404 - Running trusted local scripts only
from pathlib import Path
from datetime import datetime
import time


class BettingAnalysisPipeline:
    """Orchestrate the complete betting analysis pipeline."""

    def __init__(self, date: str, n_simulations: int = 10000, min_edge: float = 0.02):
        self.date = date
        self.n_simulations = n_simulations
        self.min_edge = min_edge

        # File paths
        self.data_dir = Path("data/betting")
        self.reports_dir = Path("reports/betting")
        self.scripts_dir = Path("scripts/betting")

        self.odds_file = self.data_dir / f"odds_{date}.json"
        self.features_file = self.data_dir / f"features_odds_{date}.json"
        self.predictions_file = self.data_dir / f"predictions_odds_{date}.json"
        self.simulations_file = self.data_dir / f"simulations_odds_{date}.json"
        self.props_file = self.data_dir / f"props_odds_{date}.json"
        self.edges_file = self.data_dir / f"edges_odds_{date}.json"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.start_time = None
        self.step_times = {}

    def run_step(self, step_name: str, command: list) -> bool:
        """Run a pipeline step and track timing."""
        print(f"\n{'='*70}")
        print(f"STEP: {step_name}")
        print(f"{'='*70}")
        print(f"Command: {' '.join(command)}\n")

        step_start = time.time()

        try:
            result = subprocess.run(  # nosec B603
                command, check=True, capture_output=False, text=True
            )
            step_duration = time.time() - step_start
            self.step_times[step_name] = step_duration

            print(f"\n✅ {step_name} completed in {step_duration:.1f}s\n")
            return True

        except subprocess.CalledProcessError as e:
            step_duration = time.time() - step_start
            self.step_times[step_name] = step_duration

            print(f"\n❌ {step_name} failed after {step_duration:.1f}s")
            print(f"Error: {e}\n")
            return False

    def run(self) -> bool:
        """Run the complete pipeline."""
        self.start_time = time.time()

        print(f"\n{'#'*70}")
        print(f"# NBA BETTING ANALYSIS PIPELINE")
        print(f"# Date: {self.date}")
        print(f"# Simulations per game: {self.n_simulations:,}")
        print(f"# Minimum edge: {self.min_edge:.1%}")
        print(f"{'#'*70}\n")

        # Step 1: Fetch odds
        if not self.run_step(
            "1. Fetch Odds from Database",
            [
                "python",
                str(self.scripts_dir / "fetch_todays_odds.py"),
                "--date",
                self.date,
                "--output",
                str(self.odds_file),
            ],
        ):
            return False

        # Step 2: Fetch features
        if not self.run_step(
            "2. Fetch Simulation Features",
            [
                "python",
                str(self.scripts_dir / "fetch_simulation_features.py"),
                "--games-file",
                str(self.odds_file),
                "--output",
                str(self.features_file),
            ],
        ):
            return False

        # Step 3: Generate ML predictions
        if not self.run_step(
            "3. Generate ML Predictions",
            [
                "python",
                str(self.scripts_dir / "generate_ml_predictions.py"),
                "--features-file",
                str(self.features_file),
                "--output",
                str(self.predictions_file),
            ],
        ):
            return False

        # Step 4: Run Monte Carlo simulations
        if not self.run_step(
            "4. Run Monte Carlo Simulations",
            [
                "python",
                str(self.scripts_dir / "run_game_simulations.py"),
                "--predictions-file",
                str(self.predictions_file),
                "--n-simulations",
                str(self.n_simulations),
                "--output",
                str(self.simulations_file),
            ],
        ):
            return False

        # Step 5: Simulate player props
        if not self.run_step(
            "5. Simulate Player Props",
            [
                "python",
                str(self.scripts_dir / "simulate_player_props.py"),
                "--simulations-file",
                str(self.simulations_file),
                "--n-simulations",
                str(self.n_simulations),
                "--output",
                str(self.props_file),
            ],
        ):
            return False

        # Step 6: Calculate betting edges
        if not self.run_step(
            "6. Calculate Betting Edges",
            [
                "python",
                str(self.scripts_dir / "calculate_betting_edges.py"),
                "--props-file",
                str(self.props_file),
                "--min-edge",
                str(self.min_edge),
                "--output",
                str(self.edges_file),
            ],
        ):
            return False

        # Step 7: Generate reports
        if not self.run_step(
            "7. Generate Reports",
            [
                "python",
                str(self.scripts_dir / "generate_betting_report.py"),
                "--edges-file",
                str(self.edges_file),
                "--output-dir",
                str(self.reports_dir),
            ],
        ):
            return False

        # Pipeline complete
        total_duration = time.time() - self.start_time

        print(f"\n{'#'*70}")
        print(f"# PIPELINE COMPLETE")
        print(f"{'#'*70}\n")
        print(
            f"Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)\n"
        )
        print(f"Step Timings:")
        for step, duration in self.step_times.items():
            print(f"  {step}: {duration:.1f}s")
        print()

        # Show output files
        print(f"Output Files:")
        print(f"  - Odds: {self.odds_file}")
        print(f"  - Features: {self.features_file}")
        print(f"  - Predictions: {self.predictions_file}")
        print(f"  - Simulations: {self.simulations_file}")
        print(f"  - Props: {self.props_file}")
        print(f"  - Edges: {self.edges_file}")
        print(f"  - Reports: {self.reports_dir}/")
        print()

        # Load final results
        try:
            with open(self.edges_file, "r") as f:
                edges_data = json.load(f)

            print(f"Final Results:")
            print(f"  - Games Analyzed: {edges_data['total_games']}")
            print(f"  - Opportunities Found: {edges_data['total_opportunities']}")
            print(f"  - Average Edge: {edges_data['summary']['avg_edge']:.2%}")
            print(
                f"  - Total Expected Value: {edges_data['summary']['total_expected_value']:.2%}"
            )
            print()

            print(f"View full report:")
            print(f"  {self.reports_dir}/betting_recommendations_{self.date}.md")
            print()
        except Exception as e:
            print(f"⚠️  Could not load final results: {e}\n")

        print(f"{'#'*70}\n")

        return True


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Run complete NBA betting analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run analysis for October 28, 2025
  python scripts/betting/run_full_betting_analysis.py --date 2025-10-28

  # Run with 20,000 simulations per game
  python scripts/betting/run_full_betting_analysis.py --date 2025-10-28 --n-simulations 20000

  # Run with custom minimum edge
  python scripts/betting/run_full_betting_analysis.py --date 2025-10-28 --min-edge 0.05
        """,
    )
    parser.add_argument(
        "--date", type=str, required=True, help="Date to analyze (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--n-simulations",
        type=int,
        default=10000,
        help="Number of simulations per game (default: 10000)",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.02,
        help="Minimum edge threshold (default: 0.02 = 2%%)",
    )

    args = parser.parse_args()

    # Run pipeline
    try:
        pipeline = BettingAnalysisPipeline(
            date=args.date, n_simulations=args.n_simulations, min_edge=args.min_edge
        )

        success = pipeline.run()

        return 0 if success else 1

    except KeyboardInterrupt:
        print(f"\n\n⚠️  Pipeline interrupted by user\n")
        return 130
    except Exception as e:
        print(f"\n\n❌ Pipeline failed with error: {e}\n")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
