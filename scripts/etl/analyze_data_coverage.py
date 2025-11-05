#!/usr/bin/env python3
"""
ESPN PBP Data Coverage Analyzer

Analyzes extracted ESPN PBP data to identify coverage gaps and missing games.
Compares against expected NBA season schedules.

Usage:
    python scripts/etl/analyze_data_coverage.py --input-dir data/extracted_pbp_recent
    python scripts/etl/analyze_data_coverage.py --detailed-analysis --output-report

Version: 1.0
Created: October 13, 2025
"""

import json
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import statistics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/data_coverage_analysis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DataCoverageAnalyzer:
    """Analyzes ESPN PBP data coverage and identifies gaps"""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)

        # Analysis results
        self.coverage_stats = defaultdict(
            lambda: {
                "games_found": 0,
                "total_plays": 0,
                "date_range": {"min": None, "max": None},
                "game_ids": set(),
                "teams": set(),
                "avg_plays_per_game": 0,
            }
        )

        logger.info(f"Initialized Data Coverage Analyzer")
        logger.info(f"Input directory: {self.input_dir}")

    def analyze_extracted_data(self) -> Dict:
        """Analyze all extracted data files"""
        logger.info("Analyzing extracted data files...")

        game_files = list(self.input_dir.glob("*_game.json"))
        logger.info(f"Found {len(game_files)} game files to analyze")

        for i, game_file in enumerate(game_files):
            if i % 500 == 0:
                logger.info(f"Analyzed {i}/{len(game_files)} games...")

            try:
                with open(game_file, "r") as f:
                    game_data = json.load(f)

                season = game_data.get("season", "unknown")
                game_id = game_data.get("game_id", "unknown")
                game_date = game_data.get("game_date", "")
                total_plays = game_data.get("total_plays", 0)

                # Update season stats
                stats = self.coverage_stats[season]
                stats["games_found"] += 1
                stats["total_plays"] += total_plays
                stats["game_ids"].add(game_id)

                # Update date range
                if game_date:
                    try:
                        parsed_date = datetime.fromisoformat(
                            game_date.replace("Z", "+00:00")
                        )
                        if (
                            stats["date_range"]["min"] is None
                            or parsed_date < stats["date_range"]["min"]
                        ):
                            stats["date_range"]["min"] = parsed_date
                        if (
                            stats["date_range"]["max"] is None
                            or parsed_date > stats["date_range"]["max"]
                        ):
                            stats["date_range"]["max"] = parsed_date
                    except:
                        pass

                # Collect teams
                home_team = game_data.get("home_abbrev", "")
                away_team = game_data.get("away_abbrev", "")
                if home_team:
                    stats["teams"].add(home_team)
                if away_team:
                    stats["teams"].add(away_team)

            except Exception as e:
                logger.warning(f"Error analyzing {game_file}: {e}")
                continue

        # Calculate averages
        for season, stats in self.coverage_stats.items():
            if stats["games_found"] > 0:
                stats["avg_plays_per_game"] = (
                    stats["total_plays"] / stats["games_found"]
                )

        logger.info("Data analysis completed!")
        return dict(self.coverage_stats)

    def get_expected_games_per_season(self) -> Dict[str, int]:
        """Get expected number of games per season based on NBA schedule"""
        # NBA regular season typically has:
        # 30 teams × 82 games ÷ 2 = 1,230 games per season
        # Plus playoffs (~100 games)
        return {
            "2022-23": 1330,  # Regular season + playoffs
            "2023-24": 1330,
            "2024-25": 1330,
            "2025-26": 1330,
        }

    def identify_coverage_gaps(self) -> Dict:
        """Identify coverage gaps by comparing found vs expected games"""
        logger.info("Identifying coverage gaps...")

        expected_games = self.get_expected_games_per_season()
        gaps = {}

        for season, stats in self.coverage_stats.items():
            expected = expected_games.get(season, 0)
            found = stats["games_found"]
            missing = max(0, expected - found)
            coverage_pct = (found / expected * 100) if expected > 0 else 0

            gaps[season] = {
                "expected_games": expected,
                "found_games": found,
                "missing_games": missing,
                "coverage_percentage": coverage_pct,
                "date_range": stats["date_range"],
                "teams_covered": len(stats["teams"]),
                "avg_plays_per_game": stats["avg_plays_per_game"],
            }

        return gaps

    def analyze_date_distribution(self) -> Dict:
        """Analyze distribution of games by month/date"""
        logger.info("Analyzing date distribution...")

        monthly_distribution = defaultdict(lambda: defaultdict(int))

        for season, stats in self.coverage_stats.items():
            for game_id in stats["game_ids"]:
                # Extract date from game_id (ESPN format: YYYYMMDD + sequence)
                try:
                    if len(game_id) >= 8:
                        date_str = game_id[:8]
                        year = int(date_str[:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])

                        monthly_distribution[season][month] += 1
                except:
                    continue

        return dict(monthly_distribution)

    def analyze_team_coverage(self) -> Dict:
        """Analyze which teams are covered in the data"""
        logger.info("Analyzing team coverage...")

        team_coverage = {}

        for season, stats in self.coverage_stats.items():
            team_coverage[season] = {
                "teams_found": sorted(list(stats["teams"])),
                "total_teams": len(stats["teams"]),
                "expected_teams": 30,  # NBA has 30 teams
            }

        return team_coverage

    def generate_coverage_report(self, output_file: str):
        """Generate comprehensive coverage report"""
        logger.info(f"Generating coverage report: {output_file}")

        # Run all analyses
        coverage_stats = self.analyze_extracted_data()
        gaps = self.identify_coverage_gaps()
        date_dist = self.analyze_date_distribution()
        team_coverage = self.analyze_team_coverage()

        report = {
            "analysis_date": datetime.now().isoformat(),
            "total_seasons_analyzed": len(coverage_stats),
            "coverage_statistics": coverage_stats,
            "coverage_gaps": gaps,
            "date_distribution": date_dist,
            "team_coverage": team_coverage,
            "summary": self._generate_summary(gaps, coverage_stats),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Coverage report saved to {output_file}")
        return report

    def _generate_summary(self, gaps: Dict, stats: Dict) -> Dict:
        """Generate summary statistics"""
        total_expected = sum(gap["expected_games"] for gap in gaps.values())
        total_found = sum(gap["found_games"] for gap in gaps.values())
        total_missing = sum(gap["missing_games"] for gap in gaps.values())
        overall_coverage = (
            (total_found / total_expected * 100) if total_expected > 0 else 0
        )

        return {
            "total_expected_games": total_expected,
            "total_found_games": total_found,
            "total_missing_games": total_missing,
            "overall_coverage_percentage": overall_coverage,
            "seasons_with_complete_coverage": len(
                [g for g in gaps.values() if g["missing_games"] == 0]
            ),
            "seasons_with_gaps": len(
                [g for g in gaps.values() if g["missing_games"] > 0]
            ),
        }

    def print_coverage_summary(self, gaps: Dict):
        """Print coverage summary to console"""
        print("\n" + "=" * 70)
        print("ESPN PBP DATA COVERAGE ANALYSIS")
        print("=" * 70)

        total_expected = 0
        total_found = 0
        total_missing = 0

        for season, gap in gaps.items():
            expected = gap["expected_games"]
            found = gap["found_games"]
            missing = gap["missing_games"]
            coverage = gap["coverage_percentage"]

            print(f"\n{season}:")
            print(f"  Expected games: {expected:,}")
            print(f"  Found games: {found:,}")
            print(f"  Missing games: {missing:,}")
            print(f"  Coverage: {coverage:.1f}%")

            if gap["date_range"]["min"] and gap["date_range"]["max"]:
                print(
                    f"  Date range: {gap['date_range']['min'].strftime('%Y-%m-%d')} to {gap['date_range']['max'].strftime('%Y-%m-%d')}"
                )

            print(f"  Teams covered: {gap['teams_covered']}/30")
            print(f"  Avg plays per game: {gap['avg_plays_per_game']:.1f}")

            total_expected += expected
            total_found += found
            total_missing += missing

        print(f"\n" + "=" * 70)
        print(f"OVERALL SUMMARY:")
        print(f"  Total expected games: {total_expected:,}")
        print(f"  Total found games: {total_found:,}")
        print(f"  Total missing games: {total_missing:,}")
        print(f"  Overall coverage: {(total_found/total_expected*100):.1f}%")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Analyze ESPN PBP data coverage")
    parser.add_argument(
        "--input-dir",
        default="data/extracted_pbp_recent",
        help="Input directory with extracted data",
    )
    parser.add_argument(
        "--output-report",
        default="data/coverage_analysis_report.json",
        help="Output file for coverage report",
    )
    parser.add_argument(
        "--detailed-analysis",
        action="store_true",
        help="Run detailed analysis with date/team breakdown",
    )

    args = parser.parse_args()

    # Create analyzer
    analyzer = DataCoverageAnalyzer(args.input_dir)

    try:
        # Generate coverage report
        report = analyzer.generate_coverage_report(args.output_report)

        # Print summary
        analyzer.print_coverage_summary(report["coverage_gaps"])

        logger.info("Coverage analysis completed successfully!")

    except Exception as e:
        logger.error(f"Coverage analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
