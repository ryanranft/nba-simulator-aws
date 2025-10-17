#!/usr/bin/env python3
"""
Phase 1.0: Data Quality Validation Framework

This script performs comprehensive data quality checks on our S3 data:
- File count and size analysis
- Date range coverage
- JSON validity checks
- Data completeness analysis
- Quality metrics and reporting

Created: October 13, 2025
Phase: 1.0 (Data Quality Checks)
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import boto3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging
from collections import defaultdict, Counter
import random

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Comprehensive data quality validation for NBA simulator data"""

    def __init__(self, s3_bucket: str = "nba-sim-raw-data-lake"):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3")
        self.results = {
            "file_counts": {},
            "date_coverage": {},
            "quality_metrics": {},
            "issues": [],
            "recommendations": [],
        }

    def analyze_file_counts(self) -> Dict[str, Any]:
        """Analyze file counts by data type"""
        print("📊 Analyzing file counts by data type...")

        file_counts = {}
        total_size = 0

        # Get all objects in S3
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.s3_bucket)

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    size = obj["Size"]

                    # Extract data type from path
                    if "/" in key:
                        data_type = key.split("/")[0]
                    else:
                        data_type = "root"

                    if data_type not in file_counts:
                        file_counts[data_type] = {"count": 0, "size": 0}

                    file_counts[data_type]["count"] += 1
                    file_counts[data_type]["size"] += size
                    total_size += size

        # Convert bytes to human readable
        for data_type in file_counts:
            size_bytes = file_counts[data_type]["size"]
            file_counts[data_type]["size_mb"] = round(size_bytes / (1024 * 1024), 2)
            file_counts[data_type]["size_gb"] = round(
                size_bytes / (1024 * 1024 * 1024), 2
            )

        self.results["file_counts"] = file_counts
        self.results["total_files"] = sum(fc["count"] for fc in file_counts.values())
        self.results["total_size_gb"] = round(total_size / (1024 * 1024 * 1024), 2)

        print(
            f"✅ Found {self.results['total_files']} files ({self.results['total_size_gb']} GB)"
        )
        for data_type, counts in file_counts.items():
            print(f"   {data_type}: {counts['count']} files ({counts['size_gb']} GB)")

        return file_counts

    def analyze_date_coverage(self) -> Dict[str, Any]:
        """Analyze date coverage and identify gaps"""
        print("📅 Analyzing date coverage...")

        # Get all schedule files (they contain date information)
        schedule_files = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.s3_bucket, Prefix="schedule/")

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    if obj["Key"].endswith(".json"):
                        schedule_files.append(obj["Key"])

        # Extract dates from filenames
        dates = []
        for file_path in schedule_files:
            filename = Path(file_path).stem
            try:
                # Extract date from filename (format: YYYYMMDD)
                if len(filename) == 8 and filename.isdigit():
                    date = datetime.strptime(filename, "%Y%m%d")
                    dates.append(date)
            except ValueError:
                continue

        dates.sort()

        if not dates:
            print("❌ No valid dates found in schedule files")
            return {}

        # Calculate coverage metrics
        start_date = dates[0]
        end_date = dates[-1]
        total_days = (end_date - start_date).days + 1
        actual_days = len(dates)
        coverage_percent = round((actual_days / total_days) * 100, 2)

        # Find gaps > 7 days
        gaps = []
        for i in range(len(dates) - 1):
            diff = (dates[i + 1] - dates[i]).days
            if diff > 7:
                gaps.append({"start": dates[i], "end": dates[i + 1], "gap_days": diff})

        coverage_info = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_days": total_days,
            "actual_days": actual_days,
            "coverage_percent": coverage_percent,
            "gaps": gaps,
            "gap_count": len(gaps),
        }

        self.results["date_coverage"] = coverage_info

        print(
            f"✅ Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
        print(f"   Coverage: {coverage_percent}% ({actual_days}/{total_days} days)")
        print(f"   Gaps > 7 days: {len(gaps)}")

        if gaps:
            print("   Major gaps:")
            for gap in gaps[:5]:  # Show first 5 gaps
                print(
                    f"     {gap['start'].strftime('%Y-%m-%d')} to {gap['end'].strftime('%Y-%m-%d')} ({gap['gap_days']} days)"
                )

        return coverage_info

    def validate_json_quality(self, sample_size: int = 100) -> Dict[str, Any]:
        """Validate JSON quality by sampling files"""
        print(f"🔍 Validating JSON quality (sampling {sample_size} files)...")

        # Get random sample of files
        all_files = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.s3_bucket)

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    if obj["Key"].endswith(".json"):
                        all_files.append(obj["Key"])

        if len(all_files) < sample_size:
            sample_files = all_files
        else:
            sample_files = random.sample(all_files, sample_size)

        # Validate each file
        validation_results = {
            "valid_json": 0,
            "invalid_json": 0,
            "empty_files": 0,
            "small_files": 0,
            "large_files": 0,
            "errors": [],
        }

        for file_path in sample_files:
            try:
                # Download file content
                response = self.s3_client.get_object(
                    Bucket=self.s3_bucket, Key=file_path
                )
                content = response["Body"].read()

                # Check file size
                file_size = len(content)
                if file_size == 0:
                    validation_results["empty_files"] += 1
                    validation_results["errors"].append(f"Empty file: {file_path}")
                    continue
                elif file_size < 100:
                    validation_results["small_files"] += 1
                elif file_size > 10 * 1024 * 1024:  # 10MB
                    validation_results["large_files"] += 1

                # Validate JSON
                try:
                    json_data = json.loads(content.decode("utf-8"))
                    validation_results["valid_json"] += 1
                except json.JSONDecodeError as e:
                    validation_results["invalid_json"] += 1
                    validation_results["errors"].append(
                        f"Invalid JSON in {file_path}: {str(e)}"
                    )
                except UnicodeDecodeError as e:
                    validation_results["invalid_json"] += 1
                    validation_results["errors"].append(
                        f"Encoding error in {file_path}: {str(e)}"
                    )

            except Exception as e:
                validation_results["errors"].append(
                    f"Error processing {file_path}: {str(e)}"
                )

        # Calculate percentages
        total_sampled = len(sample_files)
        validation_results["valid_percent"] = round(
            (validation_results["valid_json"] / total_sampled) * 100, 2
        )
        validation_results["invalid_percent"] = round(
            (validation_results["invalid_json"] / total_sampled) * 100, 2
        )
        validation_results["empty_percent"] = round(
            (validation_results["empty_files"] / total_sampled) * 100, 2
        )

        self.results["quality_metrics"] = validation_results

        print(f"✅ JSON validation results:")
        print(
            f"   Valid JSON: {validation_results['valid_json']}/{total_sampled} ({validation_results['valid_percent']}%)"
        )
        print(
            f"   Invalid JSON: {validation_results['invalid_json']} ({validation_results['invalid_percent']}%)"
        )
        print(
            f"   Empty files: {validation_results['empty_files']} ({validation_results['empty_percent']}%)"
        )
        print(f"   Small files (<100B): {validation_results['small_files']}")
        print(f"   Large files (>10MB): {validation_results['large_files']}")

        if validation_results["errors"]:
            print(f"   Errors found: {len(validation_results['errors'])}")
            print("   First 5 errors:")
            for error in validation_results["errors"][:5]:
                print(f"     - {error}")

        return validation_results

    def analyze_data_completeness(self) -> Dict[str, Any]:
        """Analyze data completeness by examining key fields"""
        print("📋 Analyzing data completeness...")

        # Sample files from different data types
        data_types = ["schedule", "box_score", "pbp"]
        completeness_results = {}

        for data_type in data_types:
            print(f"   Analyzing {data_type} data...")

            # Get sample files for this data type
            files = []
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=f"{data_type}/")

            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        if obj["Key"].endswith(".json"):
                            files.append(obj["Key"])

            if not files:
                completeness_results[data_type] = {
                    "status": "no_files",
                    "sample_size": 0,
                }
                continue

            # Sample up to 10 files
            sample_files = random.sample(files, min(10, len(files)))

            field_analysis = defaultdict(int)
            total_records = 0

            for file_path in sample_files:
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.s3_bucket, Key=file_path
                    )
                    content = response["Body"].read()
                    data = json.loads(content.decode("utf-8"))

                    # Analyze fields based on data type
                    if data_type == "schedule":
                        if isinstance(data, list):
                            total_records += len(data)
                            for game in data:
                                for field in ["gameId", "date", "homeTeam", "awayTeam"]:
                                    if field in game and game[field]:
                                        field_analysis[field] += 1

                    elif data_type == "box_score":
                        for field in ["gameId", "homeTeam", "awayTeam", "players"]:
                            if field in data and data[field]:
                                field_analysis[field] += 1

                    elif data_type == "pbp":
                        if "plays" in data and isinstance(data["plays"], list):
                            total_records += len(data["plays"])
                            for play in data["plays"]:
                                for field in [
                                    "playId",
                                    "period",
                                    "clock",
                                    "description",
                                ]:
                                    if field in play and play[field]:
                                        field_analysis[field] += 1

                except Exception as e:
                    continue

            # Calculate completeness percentages
            completeness = {}
            for field, count in field_analysis.items():
                completeness[field] = (
                    round((count / total_records) * 100, 2) if total_records > 0 else 0
                )

            completeness_results[data_type] = {
                "status": "analyzed",
                "sample_size": len(sample_files),
                "total_records": total_records,
                "completeness": completeness,
            }

        self.results["completeness"] = completeness_results

        print("✅ Data completeness analysis:")
        for data_type, results in completeness_results.items():
            if results["status"] == "analyzed":
                print(
                    f"   {data_type}: {results['sample_size']} files, {results['total_records']} records"
                )
                for field, percent in results["completeness"].items():
                    print(f"     {field}: {percent}%")
            else:
                print(f"   {data_type}: No files found")

        return completeness_results

    def generate_quality_report(self) -> str:
        """Generate comprehensive quality report"""
        print("📝 Generating quality report...")

        report = f"""
# NBA Simulator Data Quality Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Phase:** 1.0 (Data Quality Checks)

## Executive Summary

**Total Data Volume:**
- Files: {self.results['total_files']:,}
- Size: {self.results['total_size_gb']:.2f} GB

**Data Coverage:**
- Date Range: {self.results['date_coverage'].get('start_date', 'N/A')} to {self.results['date_coverage'].get('end_date', 'N/A')}
- Coverage: {self.results['date_coverage'].get('coverage_percent', 0):.2f}%
- Major Gaps: {self.results['date_coverage'].get('gap_count', 0)}

**Data Quality:**
- Valid JSON: {self.results['quality_metrics'].get('valid_percent', 0):.2f}%
- Invalid JSON: {self.results['quality_metrics'].get('invalid_percent', 0):.2f}%
- Empty Files: {self.results['quality_metrics'].get('empty_percent', 0):.2f}%

## Detailed Analysis

### File Counts by Data Type
"""

        for data_type, counts in self.results["file_counts"].items():
            report += f"- **{data_type}**: {counts['count']:,} files ({counts['size_gb']:.2f} GB)\n"

        report += f"""
### Quality Issues Found
"""

        if self.results["quality_metrics"].get("errors"):
            report += f"- **{len(self.results['quality_metrics']['errors'])} validation errors**\n"
            for error in self.results["quality_metrics"]["errors"][:10]:
                report += f"  - {error}\n"

        if self.results["date_coverage"].get("gaps"):
            report += (
                f"- **{len(self.results['date_coverage']['gaps'])} major date gaps**\n"
            )
            for gap in self.results["date_coverage"]["gaps"][:5]:
                report += f"  - {gap['start'].strftime('%Y-%m-%d')} to {gap['end'].strftime('%Y-%m-%d')} ({gap['gap_days']} days)\n"

        report += f"""
## Recommendations

1. **Data Quality**: {self.results['quality_metrics'].get('valid_percent', 0):.1f}% valid JSON is {'excellent' if self.results['quality_metrics'].get('valid_percent', 0) > 95 else 'good' if self.results['quality_metrics'].get('valid_percent', 0) > 90 else 'needs improvement'}

2. **Coverage**: {self.results['date_coverage'].get('coverage_percent', 0):.1f}% date coverage is {'excellent' if self.results['date_coverage'].get('coverage_percent', 0) > 95 else 'good' if self.results['date_coverage'].get('coverage_percent', 0) > 85 else 'needs improvement'}

3. **Next Steps**:
   - Fix invalid JSON files
   - Fill major date gaps
   - Implement ongoing quality monitoring
"""

        return report

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete data quality analysis"""
        print("🚀 Starting Phase 1.0 Data Quality Analysis")
        print("=" * 50)

        # Run all analyses
        self.analyze_file_counts()
        print()

        self.analyze_date_coverage()
        print()

        self.validate_json_quality()
        print()

        self.analyze_data_completeness()
        print()

        # Generate report
        report = self.generate_quality_report()

        # Save report
        report_path = Path("docs/DATA_QUALITY_BASELINE.md")
        with open(report_path, "w") as f:
            f.write(report)

        print(f"✅ Quality report saved to: {report_path}")
        print("\n🎉 Phase 1.0 Data Quality Analysis Complete!")

        return self.results


def main():
    """Main execution function"""
    validator = DataQualityValidator()
    results = validator.run_full_analysis()

    # Print summary
    print("\n📊 SUMMARY:")
    print(f"   Total files: {results['total_files']:,}")
    print(f"   Total size: {results['total_size_gb']:.2f} GB")
    print(
        f"   Date coverage: {results['date_coverage'].get('coverage_percent', 0):.2f}%"
    )
    print(f"   Valid JSON: {results['quality_metrics'].get('valid_percent', 0):.2f}%")

    if results["quality_metrics"].get("errors"):
        print(f"   Issues found: {len(results['quality_metrics']['errors'])}")

    print("\n✅ Ready for Phase 1.1 Multi-Source Integration!")


if __name__ == "__main__":
    main()
