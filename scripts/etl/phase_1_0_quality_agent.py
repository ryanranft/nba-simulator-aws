#!/usr/bin/env python3
"""
Phase 1.0 Data Quality Checks Agent
Analyzes S3 data coverage, identifies gaps, validates data quality
Runs as background agent for comprehensive data quality assessment
"""

import asyncio
import aiohttp
import ssl
import logging
import json
import time
import boto3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
import os
from collections import defaultdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/phase_1_0_quality_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Phase1DataQualityAgent:
    def __init__(
        self,
        output_dir="/tmp/phase_1_0_quality",
        config_file="config/scraper_config.yaml",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # AWS S3 configuration
        self.s3_client = boto3.client("s3")
        self.s3_bucket = "nba-sim-raw-data-lake"

        # Statistics
        self.stats = {
            "s3_files_analyzed": 0,
            "local_files_analyzed": 0,
            "gaps_identified": 0,
            "quality_issues": 0,
            "start_time": datetime.now(),
        }

        # Data quality metrics
        self.quality_metrics = {
            "coverage_by_source": defaultdict(int),
            "coverage_by_season": defaultdict(int),
            "file_size_distribution": defaultdict(int),
            "date_range_coverage": {},
            "missing_data_patterns": defaultdict(int),
            "duplicate_files": [],
            "corrupted_files": [],
        }

        logger.info("Phase 1.0 Data Quality Agent initialized")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"S3 bucket: {self.s3_bucket}")

    async def analyze_s3_coverage(self) -> Dict:
        """Analyze S3 data coverage and identify patterns"""
        logger.info("Analyzing S3 data coverage...")

        try:
            # List all objects in S3 bucket
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket)

            s3_analysis = {
                "total_files": 0,
                "total_size": 0,
                "files_by_prefix": defaultdict(int),
                "files_by_extension": defaultdict(int),
                "date_patterns": defaultdict(int),
                "size_distribution": defaultdict(int),
            }

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    size = obj["Size"]

                    s3_analysis["total_files"] += 1
                    s3_analysis["total_size"] += size
                    self.stats["s3_files_analyzed"] += 1

                    # Analyze by prefix (data source)
                    prefix = key.split("/")[0] if "/" in key else "root"
                    s3_analysis["files_by_prefix"][prefix] += 1

                    # Analyze by extension
                    ext = Path(key).suffix.lower()
                    s3_analysis["files_by_extension"][ext] += 1

                    # Analyze date patterns (if filename contains dates)
                    if any(char.isdigit() for char in key):
                        # Extract potential date patterns
                        import re

                        date_patterns = re.findall(r"\d{4}", key)
                        for pattern in date_patterns:
                            s3_analysis["date_patterns"][pattern] += 1

                    # Size distribution
                    size_mb = size / (1024 * 1024)
                    if size_mb < 1:
                        s3_analysis["size_distribution"]["<1MB"] += 1
                    elif size_mb < 10:
                        s3_analysis["size_distribution"]["1-10MB"] += 1
                    elif size_mb < 100:
                        s3_analysis["size_distribution"]["10-100MB"] += 1
                    else:
                        s3_analysis["size_distribution"][">100MB"] += 1

                    # Update quality metrics
                    self.quality_metrics["coverage_by_source"][prefix] += 1
                    self.quality_metrics["file_size_distribution"][
                        f"{size_mb:.1f}MB"
                    ] += 1

            logger.info(
                f"S3 analysis complete: {s3_analysis['total_files']} files, {s3_analysis['total_size']/(1024**3):.2f}GB"
            )
            return s3_analysis

        except Exception as e:
            logger.error(f"Error analyzing S3 coverage: {e}")
            self.stats["quality_issues"] += 1
            return {}

    async def analyze_local_data(self) -> Dict:
        """Analyze local data files and identify patterns"""
        logger.info("Analyzing local data files...")

        try:
            local_analysis = {
                "total_files": 0,
                "total_size": 0,
                "files_by_directory": defaultdict(int),
                "files_by_extension": defaultdict(int),
                "date_patterns": defaultdict(int),
                "size_distribution": defaultdict(int),
            }

            # Analyze local data directories
            local_dirs = [
                "data/nba_pbp",
                "data/nba_box_score",
                "data/nba_schedule_json",
                "data/nba_team_stats",
                "data/kaggle",
                "data/ml_quality",
            ]

            for dir_path in local_dirs:
                if not os.path.exists(dir_path):
                    continue

                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_path)

                            local_analysis["total_files"] += 1
                            local_analysis["total_size"] += size
                            self.stats["local_files_analyzed"] += 1

                            # Analyze by directory
                            rel_dir = os.path.relpath(root, "data")
                            local_analysis["files_by_directory"][rel_dir] += 1

                            # Analyze by extension
                            ext = Path(file).suffix.lower()
                            local_analysis["files_by_extension"][ext] += 1

                            # Analyze date patterns
                            if any(char.isdigit() for char in file):
                                import re

                                date_patterns = re.findall(r"\d{4}", file)
                                for pattern in date_patterns:
                                    local_analysis["date_patterns"][pattern] += 1
                                    self.quality_metrics["coverage_by_season"][
                                        pattern
                                    ] += 1

                            # Size distribution
                            size_mb = size / (1024 * 1024)
                            if size_mb < 1:
                                local_analysis["size_distribution"]["<1MB"] += 1
                            elif size_mb < 10:
                                local_analysis["size_distribution"]["1-10MB"] += 1
                            elif size_mb < 100:
                                local_analysis["size_distribution"]["10-100MB"] += 1
                            else:
                                local_analysis["size_distribution"][">100MB"] += 1

                        except Exception as e:
                            logger.warning(f"Error analyzing file {file_path}: {e}")
                            self.quality_metrics["corrupted_files"].append(file_path)

            logger.info(
                f"Local analysis complete: {local_analysis['total_files']} files, {local_analysis['total_size']/(1024**3):.2f}GB"
            )
            return local_analysis

        except Exception as e:
            logger.error(f"Error analyzing local data: {e}")
            self.stats["quality_issues"] += 1
            return {}

    async def identify_data_gaps(self, s3_analysis: Dict, local_analysis: Dict) -> Dict:
        """Identify data gaps and missing coverage"""
        logger.info("Identifying data gaps...")

        gaps = {
            "missing_seasons": [],
            "missing_sources": [],
            "size_anomalies": [],
            "date_gaps": [],
            "coverage_issues": [],
        }

        try:
            # Analyze season coverage
            all_seasons = set()
            all_seasons.update(s3_analysis.get("date_patterns", {}).keys())
            all_seasons.update(local_analysis.get("date_patterns", {}).keys())

            # Expected seasons (1993-2025)
            expected_seasons = set(str(year) for year in range(1993, 2026))
            missing_seasons = expected_seasons - all_seasons

            if missing_seasons:
                gaps["missing_seasons"] = sorted(missing_seasons)
                self.stats["gaps_identified"] += len(missing_seasons)
                logger.warning(f"Missing seasons: {sorted(missing_seasons)}")

            # Analyze source coverage
            expected_sources = [
                "espn",
                "basketball_reference",
                "nba_api",
                "kaggle",
                "hoopr",
            ]
            s3_sources = set(s3_analysis.get("files_by_prefix", {}).keys())
            local_sources = set(local_analysis.get("files_by_directory", {}).keys())
            all_sources = s3_sources.union(local_sources)

            missing_sources = set(expected_sources) - all_sources
            if missing_sources:
                gaps["missing_sources"] = list(missing_sources)
                self.stats["gaps_identified"] += len(missing_sources)
                logger.warning(f"Missing sources: {missing_sources}")

            # Analyze size anomalies
            for source, count in s3_analysis.get("files_by_prefix", {}).items():
                if count < 10:  # Suspiciously low file count
                    gaps["size_anomalies"].append(f"S3 {source}: only {count} files")

            for dir_name, count in local_analysis.get("files_by_directory", {}).items():
                if count < 10:  # Suspiciously low file count
                    gaps["size_anomalies"].append(
                        f"Local {dir_name}: only {count} files"
                    )

            logger.info(
                f"Gap analysis complete: {self.stats['gaps_identified']} gaps identified"
            )
            return gaps

        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")
            self.stats["quality_issues"] += 1
            return gaps

    async def validate_data_quality(self) -> Dict:
        """Validate data quality and identify issues"""
        logger.info("Validating data quality...")

        quality_report = {
            "file_integrity": {"passed": 0, "failed": 0},
            "data_completeness": {"passed": 0, "failed": 0},
            "format_consistency": {"passed": 0, "failed": 0},
            "schema_validation": {"passed": 0, "failed": 0},
        }

        try:
            # Sample files for validation
            sample_files = []

            # Get sample files from local data
            for root, dirs, files in os.walk("data"):
                for file in files[:5]:  # Sample first 5 files from each directory
                    if file.endswith((".json", ".csv")):
                        sample_files.append(os.path.join(root, file))

            # Validate sample files
            for file_path in sample_files[:50]:  # Limit to 50 files for performance
                try:
                    # File integrity check
                    if os.path.getsize(file_path) > 0:
                        quality_report["file_integrity"]["passed"] += 1
                    else:
                        quality_report["file_integrity"]["failed"] += 1
                        self.quality_metrics["corrupted_files"].append(file_path)

                    # Format consistency check
                    if file_path.endswith(".json"):
                        with open(file_path, "r") as f:
                            json.load(f)  # Test JSON parsing
                        quality_report["format_consistency"]["passed"] += 1
                    elif file_path.endswith(".csv"):
                        pd.read_csv(file_path, nrows=1)  # Test CSV parsing
                        quality_report["format_consistency"]["passed"] += 1

                except Exception as e:
                    logger.warning(f"Quality validation failed for {file_path}: {e}")
                    quality_report["format_consistency"]["failed"] += 1
                    self.stats["quality_issues"] += 1

            logger.info(
                f"Quality validation complete: {quality_report['file_integrity']['passed']} files validated"
            )
            return quality_report

        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            self.stats["quality_issues"] += 1
            return quality_report

    def generate_quality_report(
        self, s3_analysis: Dict, local_analysis: Dict, gaps: Dict, quality_report: Dict
    ) -> Dict:
        """Generate comprehensive quality report"""
        logger.info("Generating quality report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_analyzed": self.stats["s3_files_analyzed"]
                + self.stats["local_files_analyzed"],
                "total_size_gb": (
                    s3_analysis.get("total_size", 0)
                    + local_analysis.get("total_size", 0)
                )
                / (1024**3),
                "gaps_identified": self.stats["gaps_identified"],
                "quality_issues": self.stats["quality_issues"],
                "analysis_duration": str(datetime.now() - self.stats["start_time"]),
            },
            "s3_analysis": s3_analysis,
            "local_analysis": local_analysis,
            "gaps": gaps,
            "quality_report": quality_report,
            "recommendations": self._generate_recommendations(gaps, quality_report),
        }

        # Save report
        report_file = self.output_dir / "data_quality_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Quality report saved to {report_file}")
        return report

    def _generate_recommendations(self, gaps: Dict, quality_report: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        if gaps.get("missing_seasons"):
            recommendations.append(f"Fill missing seasons: {gaps['missing_seasons']}")

        if gaps.get("missing_sources"):
            recommendations.append(
                f"Implement missing data sources: {gaps['missing_sources']}"
            )

        if gaps.get("size_anomalies"):
            recommendations.append(
                f"Investigate size anomalies: {len(gaps['size_anomalies'])} issues found"
            )

        if quality_report.get("format_consistency", {}).get("failed", 0) > 0:
            recommendations.append("Fix format consistency issues in data files")

        if self.quality_metrics["corrupted_files"]:
            recommendations.append(
                f"Repair {len(self.quality_metrics['corrupted_files'])} corrupted files"
            )

        return recommendations

    def log_progress(self):
        """Log current progress"""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("PHASE 1.0 DATA QUALITY AGENT PROGRESS")
        logger.info("=" * 60)
        logger.info(f"S3 files analyzed: {self.stats['s3_files_analyzed']}")
        logger.info(f"Local files analyzed: {self.stats['local_files_analyzed']}")
        logger.info(f"Gaps identified: {self.stats['gaps_identified']}")
        logger.info(f"Quality issues: {self.stats['quality_issues']}")
        logger.info(f"Elapsed time: {elapsed}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution method"""
        logger.info("Starting Phase 1.0 Data Quality Agent")

        try:
            # Analyze S3 coverage
            s3_analysis = await self.analyze_s3_coverage()

            # Analyze local data
            local_analysis = await self.analyze_local_data()

            # Identify gaps
            gaps = await self.identify_data_gaps(s3_analysis, local_analysis)

            # Validate quality
            quality_report = await self.validate_data_quality()

            # Generate report
            report = self.generate_quality_report(
                s3_analysis, local_analysis, gaps, quality_report
            )

            # Log progress
            self.log_progress()

            logger.info("Phase 1.0 Data Quality Agent completed successfully")
            logger.info(f"Report saved to: {self.output_dir}/data_quality_report.json")

        except Exception as e:
            logger.error(f"Phase 1.0 Data Quality Agent failed: {e}")
            self.stats["quality_issues"] += 1


def main():
    """Main entry point"""
    agent = Phase1DataQualityAgent()

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Phase 1.0 Data Quality Agent interrupted by user")
    except Exception as e:
        logger.error(f"Phase 1.0 Data Quality Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
