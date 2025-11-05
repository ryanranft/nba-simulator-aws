#!/usr/bin/env python3
"""
Gap Detection Engine - ADCE Phase 2A MVP
Identifies missing/stale data and assigns priorities

Migrated from scripts/reconciliation/detect_data_gaps.py during Phase 6 refactoring.

Purpose:
- Read coverage analysis (output of analyze_coverage.py)
- Identify specific missing data
- Assign priorities (CRITICAL, HIGH, MEDIUM, LOW)
- Generate structured gap report

Priority Levels:
- CRITICAL: Recent games (< 7 days), required data
- HIGH: Current season incomplete (< 95%)
- MEDIUM: Recent season incomplete (2023-24)
- LOW: Historical backfill

Usage:
    from nba_simulator.adce import GapDetector
    
    detector = GapDetector(coverage_analysis_file="inventory/cache/coverage_analysis.json")
    gap_report = detector.detect_gaps()
    detector.save_gaps(gap_report)
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from ..utils import setup_logging

logger = setup_logging(__name__)


class Priority(Enum):
    """Gap priority levels"""

    CRITICAL = 1  # Recent games (< 7 days), urgent
    HIGH = 2  # Current season incomplete
    MEDIUM = 3  # Recent seasons (< 2 years)
    LOW = 4  # Historical backfill


class GapDetector:
    """
    Detects data gaps and assigns priorities

    Converts coverage analysis into actionable gap report
    """

    def __init__(self, coverage_analysis_file):
        """
        Initialize gap detector

        Args:
            coverage_analysis_file: Path to coverage analysis JSON
        """
        self.analysis_file = Path(coverage_analysis_file)

        logger.info(f"Loading coverage analysis from: {coverage_analysis_file}")
        with open(self.analysis_file, "r") as f:
            self.analysis = json.load(f)

        self.current_season = self._get_current_season()
        logger.info(f"Current season: {self.current_season}")

    def detect_gaps(self):
        """
        Detect all gaps and assign priorities

        Returns:
            dict: Structured gap report with priorities
        """
        logger.info("Starting gap detection...")
        start_time = datetime.now()

        gap_report = {
            "timestamp": start_time.isoformat(),
            "analysis_file": str(self.analysis_file),
            "current_season": self.current_season,
            "summary": {
                "total_gaps": 0,
                "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            },
            "gaps": {"critical": [], "high": [], "medium": [], "low": []},
        }

        # Process each source
        for source, source_data in self.analysis["by_source"].items():
            logger.info(f"Detecting gaps for source: {source}")
            source_gaps = self.detect_source_gaps(source, source_data)

            # Add to gap report
            for gap in source_gaps:
                priority_key = gap["priority"].lower()
                gap_report["gaps"][priority_key].append(gap)
                gap_report["summary"]["by_priority"][priority_key] += 1
                gap_report["summary"]["total_gaps"] += 1

        duration = (datetime.now() - start_time).total_seconds()
        gap_report["detection_duration_seconds"] = duration

        logger.info(f"Gap detection complete in {duration:.1f}s")
        logger.info(f"Total gaps detected: {gap_report['summary']['total_gaps']}")
        logger.info(f"  Critical: {gap_report['summary']['by_priority']['critical']}")
        logger.info(f"  High: {gap_report['summary']['by_priority']['high']}")
        logger.info(f"  Medium: {gap_report['summary']['by_priority']['medium']}")
        logger.info(f"  Low: {gap_report['summary']['by_priority']['low']}")

        return gap_report

    def detect_source_gaps(self, source, source_data):
        """
        Detect gaps for a specific source

        Args:
            source: Source name (e.g., 'espn')
            source_data: Coverage analysis data for this source

        Returns:
            list: List of gap dicts
        """
        gaps = []

        # Check each season
        for season, season_data in source_data.get("by_season", {}).items():
            if season_data["missing_files"] > 0 or season_data["stale_files"] > 0:
                gap = self._create_season_gap(
                    source=source, season=season, season_data=season_data
                )
                gaps.append(gap)

        # Check each data type
        for data_type, type_data in source_data.get("by_type", {}).items():
            if type_data["required"] and (
                type_data["stale_files"] > 0 or type_data["small_files"] > 0
            ):
                gap = self._create_datatype_gap(
                    source=source, data_type=data_type, type_data=type_data
                )
                gaps.append(gap)

        # General completeness check
        if source_data["completeness_pct"] < 95.0:
            gap = self._create_completeness_gap(source=source, source_data=source_data)
            gaps.append(gap)

        return gaps

    def _create_season_gap(self, source, season, season_data):
        """Create gap record for a season"""
        # Determine priority
        if season == self.current_season:
            if season_data["stale_files"] > 0:
                priority = Priority.CRITICAL
                reason = f"Current season has {season_data['stale_files']} stale files (>7 days old)"
            elif season_data["missing_files"] > 0:
                priority = Priority.HIGH
                reason = f"Current season missing {season_data['missing_files']} files"
            else:
                priority = Priority.HIGH
                reason = "Current season incomplete"
        elif season == self._get_previous_season():
            priority = Priority.MEDIUM
            reason = f"Recent season missing {season_data['missing_files']} files"
        else:
            priority = Priority.LOW
            reason = f"Historical season missing {season_data['missing_files']} files"

        return {
            "gap_type": "season_incomplete",
            "priority": priority.name,
            "source": source,
            "season": season,
            "missing_files": season_data["missing_files"],
            "stale_files": season_data["stale_files"],
            "completeness_pct": season_data["completeness_pct"],
            "reason": reason,
            "detected_at": datetime.now().isoformat(),
        }

    def _create_datatype_gap(self, source, data_type, type_data):
        """Create gap record for a data type"""
        # Data type gaps are generally CRITICAL if required
        if type_data["required"]:
            if type_data["stale_files"] > 0:
                priority = Priority.CRITICAL
                reason = (
                    f"Required data type has {type_data['stale_files']} stale files"
                )
            else:
                priority = Priority.HIGH
                reason = f"Required data type has {type_data['small_files']} small/suspicious files"
        else:
            priority = Priority.MEDIUM
            reason = f"Optional data type has quality issues"

        return {
            "gap_type": "datatype_quality",
            "priority": priority.name,
            "source": source,
            "data_type": data_type,
            "stale_files": type_data["stale_files"],
            "small_files": type_data["small_files"],
            "issues": type_data.get("issues", [])[:5],  # First 5 issues
            "reason": reason,
            "detected_at": datetime.now().isoformat(),
        }

    def _create_completeness_gap(self, source, source_data):
        """Create gap record for overall completeness"""
        completeness_pct = source_data["completeness_pct"]
        missing_files = source_data["missing_files"]

        # Determine priority based on completeness
        if completeness_pct < 50:
            priority = Priority.CRITICAL
            reason = f"Source only {completeness_pct:.1f}% complete - major gaps"
        elif completeness_pct < 80:
            priority = Priority.HIGH
            reason = f"Source only {completeness_pct:.1f}% complete - significant gaps"
        elif completeness_pct < 95:
            priority = Priority.MEDIUM
            reason = f"Source {completeness_pct:.1f}% complete - minor gaps"
        else:
            priority = Priority.LOW
            reason = f"Source {completeness_pct:.1f}% complete - small gaps"

        return {
            "gap_type": "overall_completeness",
            "priority": priority.name,
            "source": source,
            "completeness_pct": completeness_pct,
            "missing_files": missing_files,
            "expected_files": source_data["expected_files"],
            "actual_files": source_data["actual_files"],
            "reason": reason,
            "detected_at": datetime.now().isoformat(),
        }

    def _get_current_season(self):
        """Get current NBA season (e.g., '2024-25')"""
        now = datetime.now()
        year = now.year
        month = now.month

        # NBA season runs Oct-Jun
        if month >= 10:  # Oct-Dec
            return f"{year}-{str(year + 1)[-2:]}"
        else:  # Jan-Sep
            return f"{year - 1}-{str(year)[-2:]}"

    def _get_previous_season(self):
        """Get previous NBA season"""
        current_season_start = int(self.current_season.split("-")[0])
        prev_season_start = current_season_start - 1
        return f"{prev_season_start}-{str(prev_season_start + 1)[-2:]}"

    def save_gaps(self, gap_report, output_file="detected_gaps.json"):
        """
        Save gap report to file
        
        Args:
            gap_report: Gap report dictionary
            output_file: Output filename (will be saved to inventory/cache/)
            
        Returns:
            Path: Path to saved file
        """
        output_dir = Path("inventory/cache")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_file

        logger.info(f"Saving gap report to {output_path}")

        with open(output_path, "w") as f:
            json.dump(gap_report, f, indent=2, default=str)

        logger.info("Gap report saved successfully")
        return output_path


def main():
    """CLI entry point for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect data gaps and assign priorities"
    )
    parser.add_argument(
        "--analysis",
        default="inventory/cache/coverage_analysis.json",
        help="Path to coverage analysis JSON",
    )
    parser.add_argument(
        "--output", default="detected_gaps.json", help="Output filename"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Detect gaps but don't save results"
    )

    args = parser.parse_args()

    # Check file exists
    if not Path(args.analysis).exists():
        print(f"❌ Coverage analysis file not found: {args.analysis}")
        print("Run analyze_coverage.py first")
        return 1

    # Initialize detector
    detector = GapDetector(coverage_analysis_file=args.analysis)

    # Detect gaps
    gap_report = detector.detect_gaps()

    # Save results
    if not args.dry_run:
        output_path = detector.save_gaps(gap_report, args.output)
        print(f"\n✅ Gap report saved: {output_path}")
    else:
        print("\n🔍 DRY RUN - Results not saved")

    # Print summary
    summary = gap_report["summary"]
    print(f"\n📊 Gap Detection Summary:")
    print(f"  Total gaps: {summary['total_gaps']}")
    print(f"  🔴 Critical: {summary['by_priority']['critical']}")
    print(f"  🟡 High: {summary['by_priority']['high']}")
    print(f"  🟢 Medium: {summary['by_priority']['medium']}")
    print(f"  ⚪ Low: {summary['by_priority']['low']}")

    # Show critical gaps
    if gap_report["gaps"]["critical"]:
        print(f"\n🚨 Critical Gaps (Top 5):")
        for i, gap in enumerate(gap_report["gaps"]["critical"][:5], 1):
            print(f"  {i}. [{gap['source']}] {gap['reason']}")

    return 0


if __name__ == "__main__":
    exit(main())
