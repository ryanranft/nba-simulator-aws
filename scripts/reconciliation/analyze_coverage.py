#!/usr/bin/env python3
"""
Coverage Analyzer - ADCE Phase 2A MVP
Compares expected coverage (SHOULD have) vs actual inventory (HAVE)

Purpose:
- Load expected coverage from data_inventory.yaml
- Load actual inventory from S3 scan
- Compare and calculate completeness
- Identify missing data
- Detect stale files

Usage:
    python analyze_coverage.py
    python analyze_coverage.py --expected inventory/data_inventory.yaml --inventory inventory/cache/current_inventory.json
"""

import yaml
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """
    Analyzes data coverage by comparing expected vs actual inventory

    Answers the question: Do we have the data we should have?
    """

    def __init__(self, expected_file, inventory_file):
        """
        Initialize coverage analyzer

        Args:
            expected_file: Path to data_inventory.yaml (SHOULD have)
            inventory_file: Path to S3 inventory JSON (HAVE)
        """
        self.expected_file = Path(expected_file)
        self.inventory_file = Path(inventory_file)

        logger.info(f"Loading expected coverage from: {expected_file}")
        self.expected = self._load_yaml(expected_file)

        logger.info(f"Loading actual inventory from: {inventory_file}")
        self.inventory = self._load_json(inventory_file)

        # Extract config
        self.expected_game_counts = self.expected.get("expected_game_counts", {})
        self.quality_requirements = self.expected.get("quality_requirements", {})
        self.priority_rules = self.expected.get("priority_rules", {})

    def _load_yaml(self, file_path):
        """Load YAML file"""
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    def _load_json(self, file_path):
        """Load JSON file"""
        with open(file_path, "r") as f:
            return json.load(f)

    def analyze(self):
        """
        Compare expected vs. actual coverage

        Returns:
            dict: Complete coverage analysis
        """
        logger.info("Starting coverage analysis...")
        start_time = datetime.now()

        analysis = {
            "timestamp": start_time.isoformat(),
            "expected_file": str(self.expected_file),
            "inventory_file": str(self.inventory_file),
            "inventory_metadata": self.inventory.get("metadata", {}),
            "summary": {
                "total_sources": 0,
                "sources_complete": 0,
                "sources_incomplete": 0,
                "critical_gaps": 0,
                "total_missing_files": 0,
                "total_stale_files": 0,
                "overall_completeness_pct": 0.0,
            },
            "by_source": {},
        }

        # Analyze each source
        for source, config in self.expected["expected_coverage"].items():
            logger.info(f"Analyzing source: {source}")
            source_analysis = self.analyze_source(source, config)
            analysis["by_source"][source] = source_analysis
            analysis["summary"]["total_sources"] += 1

            # Update summary
            if source_analysis["completeness_pct"] >= 95:
                analysis["summary"]["sources_complete"] += 1
            else:
                analysis["summary"]["sources_incomplete"] += 1

            analysis["summary"]["critical_gaps"] += source_analysis["critical_gaps"]
            analysis["summary"]["total_missing_files"] += source_analysis[
                "missing_files"
            ]
            analysis["summary"]["total_stale_files"] += source_analysis["stale_files"]

        # Calculate overall completeness
        total_expected = sum(
            s["expected_files"] for s in analysis["by_source"].values()
        )
        total_actual = sum(s["actual_files"] for s in analysis["by_source"].values())
        if total_expected > 0:
            analysis["summary"]["overall_completeness_pct"] = (
                total_actual / total_expected
            ) * 100

        duration = (datetime.now() - start_time).total_seconds()
        analysis["analysis_duration_seconds"] = duration

        logger.info(f"Coverage analysis complete in {duration:.1f}s")
        logger.info(
            f"Overall completeness: {analysis['summary']['overall_completeness_pct']:.1f}%"
        )
        logger.info(
            f"Sources complete: {analysis['summary']['sources_complete']}/{analysis['summary']['total_sources']}"
        )
        logger.info(
            f"Total missing files: {analysis['summary']['total_missing_files']:,}"
        )
        logger.info(f"Critical gaps: {analysis['summary']['critical_gaps']}")

        return analysis

    def analyze_source(self, source, config):
        """
        Analyze coverage for a specific source

        Args:
            source: Source name (e.g., 'espn')
            config: Expected coverage config for this source

        Returns:
            dict: Source-specific analysis
        """
        # Get actual data from inventory
        actual_data = self.inventory.get("by_source", {}).get(
            source, {"count": 0, "total_size": 0, "files": []}
        )

        analysis = {
            "expected_files": 0,
            "actual_files": actual_data["count"],
            "missing_files": 0,
            "stale_files": 0,
            "critical_gaps": 0,
            "completeness_pct": 0.0,
            "total_size_bytes": actual_data.get("total_size", 0),
            "by_season": {},
            "by_type": {},
        }

        # Analyze each season
        for season in config.get("seasons", []):
            season_analysis = self.analyze_season(
                source, season, config, actual_data["files"]
            )
            analysis["by_season"][season] = season_analysis

            # Aggregate to source level
            analysis["expected_files"] += season_analysis["expected_files"]
            analysis["missing_files"] += season_analysis["missing_files"]
            analysis["stale_files"] += season_analysis["stale_files"]

            if season_analysis["is_critical"]:
                analysis["critical_gaps"] += 1

        # Analyze each data type
        for data_type, type_config in config.get("data_types", {}).items():
            type_analysis = self.analyze_data_type(
                source, data_type, type_config, actual_data["files"]
            )
            analysis["by_type"][data_type] = type_analysis

        # Calculate completeness percentage
        if analysis["expected_files"] > 0:
            actual_good = analysis["actual_files"] - analysis["missing_files"]
            analysis["completeness_pct"] = (
                actual_good / analysis["expected_files"]
            ) * 100

        return analysis

    def analyze_season(self, source, season, config, actual_files):
        """Analyze coverage for a specific season"""
        # Filter files for this season
        season_files = [f for f in actual_files if f.get("season") == season]

        # Get expected counts for each data type
        expected_count = 0
        for data_type, type_config in config.get("data_types", {}).items():
            if type_config.get("required"):
                # Use expected game counts
                expected_count += self.expected_game_counts.get("total_max", 1320)

        analysis = {
            "expected_files": expected_count,
            "actual_files": len(season_files),
            "missing_files": max(0, expected_count - len(season_files)),
            "stale_files": 0,
            "completeness_pct": 0.0,
            "is_critical": self._is_current_season(season),
        }

        # Check for stale files if current season
        if self._is_current_season(season):
            stale_count = self._count_stale_files(
                season_files, freshness_days=7  # Default critical threshold
            )
            analysis["stale_files"] = stale_count

        # Calculate completeness
        if analysis["expected_files"] > 0:
            analysis["completeness_pct"] = (
                analysis["actual_files"] / analysis["expected_files"]
            ) * 100

        return analysis

    def analyze_data_type(self, source, data_type, type_config, actual_files):
        """Analyze coverage for a specific data type"""
        # Filter files for this data type
        type_files = [f for f in actual_files if f.get("data_type") == data_type]

        analysis = {
            "required": type_config.get("required", False),
            "actual_files": len(type_files),
            "completeness_threshold": type_config.get("completeness_threshold", 0.95),
            "freshness_days": type_config.get("freshness_days", 30),
            "path_patterns": type_config.get("path_patterns", []),
            "stale_files": 0,
            "small_files": 0,
            "issues": [],
        }

        # Check file quality
        min_size = self.quality_requirements.get("min_file_size_bytes", 100)
        for file_meta in type_files:
            # Check file size
            if file_meta.get("size_bytes", 0) < min_size:
                analysis["small_files"] += 1
                analysis["issues"].append(f"Small file: {file_meta.get('s3_key')}")

        # Check freshness
        stale_count = self._count_stale_files(
            type_files, type_config.get("freshness_days", 30)
        )
        analysis["stale_files"] = stale_count

        return analysis

    def _is_current_season(self, season):
        """Check if season is current (2024-25)"""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # NBA season runs Oct-Jun, so current season depends on month
        if current_month >= 10:  # Oct-Dec
            current_season = f"{current_year}-{str(current_year + 1)[-2:]}"
        else:  # Jan-Sep
            current_season = f"{current_year - 1}-{str(current_year)[-2:]}"

        return season == current_season

    def _count_stale_files(self, files, freshness_days):
        """Count files older than freshness threshold"""
        cutoff_date = datetime.now() - timedelta(days=freshness_days)
        stale_count = 0

        for file_meta in files:
            last_modified_str = file_meta.get("last_modified")
            if last_modified_str:
                try:
                    last_modified = datetime.fromisoformat(
                        last_modified_str.replace("Z", "+00:00")
                    )
                    if last_modified < cutoff_date:
                        stale_count += 1
                except (ValueError, AttributeError):  # nosec B110
                    pass  # Skip if can't parse date - legitimate error handling

        return stale_count

    def save_analysis(self, analysis, output_file="coverage_analysis.json"):
        """Save analysis to file"""
        output_dir = Path("inventory/cache")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_file

        logger.info(f"Saving analysis to {output_path}")

        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        logger.info("Analysis saved successfully")
        return output_path


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze data coverage (SHOULD vs HAVE)"
    )
    parser.add_argument(
        "--expected",
        default="inventory/data_inventory.yaml",
        help="Path to expected coverage YAML",
    )
    parser.add_argument(
        "--inventory",
        default="inventory/cache/current_inventory.json",
        help="Path to S3 inventory JSON",
    )
    parser.add_argument(
        "--output", default="coverage_analysis.json", help="Output filename"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze but don't save results"
    )

    args = parser.parse_args()

    # Check files exist
    if not Path(args.expected).exists():
        print(f"❌ Expected coverage file not found: {args.expected}")
        return 1

    if not Path(args.inventory).exists():
        print(f"❌ Inventory file not found: {args.inventory}")
        print("Run scan_s3_inventory.py first to create inventory")
        return 1

    # Initialize analyzer
    analyzer = CoverageAnalyzer(
        expected_file=args.expected, inventory_file=args.inventory
    )

    # Run analysis
    analysis = analyzer.analyze()

    # Save results
    if not args.dry_run:
        output_path = analyzer.save_analysis(analysis, args.output)
        print(f"\n✅ Analysis saved: {output_path}")
    else:
        print("\n🔍 DRY RUN - Results not saved")

    # Print summary
    summary = analysis["summary"]
    print(f"\n📊 Coverage Analysis Summary:")
    print(f"  Overall completeness: {summary['overall_completeness_pct']:.1f}%")
    print(
        f"  Sources complete: {summary['sources_complete']}/{summary['total_sources']}"
    )
    print(f"  Sources incomplete: {summary['sources_incomplete']}")
    print(f"  Missing files: {summary['total_missing_files']:,}")
    print(f"  Stale files: {summary['total_stale_files']:,}")
    print(f"  Critical gaps: {summary['critical_gaps']}")

    # Print per-source details
    print(f"\n📋 By Source:")
    for source, source_data in analysis["by_source"].items():
        print(f"  {source}:")
        print(f"    Completeness: {source_data['completeness_pct']:.1f}%")
        print(f"    Expected: {source_data['expected_files']:,}")
        print(f"    Actual: {source_data['actual_files']:,}")
        print(f"    Missing: {source_data['missing_files']:,}")

    return 0


if __name__ == "__main__":
    exit(main())
