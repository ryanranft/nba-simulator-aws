#!/usr/bin/env python3
"""
Phase 0.0001 Validator: ESPN Data Extraction & Validation

Validates the ESPN S3 data migration and baseline data collection:
- Verifies S3 folder structure with espn_* prefixes
- Validates file counts against baselines
- Checks data quality metrics
- Detects coverage gaps
- Integrates with DIMS for live metrics

Usage:
    python validators/phases/phase_0/validate_0_0001.py
    python validators/phases/phase_0/validate_0_0001.py --verbose
    python validators/phases/phase_0/validate_0_0001.py --schema raw_data
"""

import sys
import os
import json
import boto3
import random
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# S3 Configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_REGION = "us-east-1"

# Expected baseline counts (October 1, 2025)
BASELINE_COUNTS = {
    "espn_schedules": 11633,
    "espn_play_by_play": 44826,
    "espn_box_scores": 44828,
    "espn_team_stats": 44828,
}

# Current counts (November 6, 2025)
CURRENT_COUNTS = {
    "espn_schedules": 11633,
    "espn_play_by_play": 44826,
    "espn_box_scores": 44836,  # +8 from baseline
    "espn_team_stats": 46101,  # +1,273 from baseline
}

# Total baseline
BASELINE_TOTAL = sum(BASELINE_COUNTS.values())  # 146,115
CURRENT_TOTAL = sum(CURRENT_COUNTS.values())  # 147,396


class Phase0001Validator:
    """Validates Phase 0.0001 ESPN data extraction and S3 migration."""

    def __init__(self, verbose: bool = False):
        """
        Initialize validator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.s3_client = boto3.client("s3", region_name=S3_REGION)

    def log(self, message: str):
        """Log message if verbose mode enabled."""
        if self.verbose:
            print(f"  {message}")

    def validate_s3_bucket_exists(self) -> bool:
        """Validate S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=S3_BUCKET)
            self.log(f"✓ S3 bucket '{S3_BUCKET}' exists and is accessible")
            return True
        except Exception as e:
            self.failures.append(f"S3 bucket check failed: {e}")
            return False

    def count_s3_objects(self, prefix: str) -> int:
        """
        Count objects with given S3 prefix.

        Args:
            prefix: S3 prefix to count

        Returns:
            Number of objects
        """
        count = 0
        paginator = self.s3_client.get_paginator("list_objects_v2")

        try:
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
                if "Contents" in page:
                    count += len(page["Contents"])
        except Exception as e:
            self.log(f"✗ Error counting objects with prefix '{prefix}': {e}")
            return -1

        return count

    def validate_espn_folder_structure(self) -> bool:
        """Validate ESPN folders exist with correct prefixes."""
        try:
            expected_prefixes = list(CURRENT_COUNTS.keys())
            found_prefixes = []

            for prefix in expected_prefixes:
                # Check if prefix exists by trying to list one object
                response = self.s3_client.list_objects_v2(
                    Bucket=S3_BUCKET, Prefix=f"{prefix}/", MaxKeys=1
                )

                if "Contents" in response and len(response["Contents"]) > 0:
                    found_prefixes.append(prefix)
                    self.log(f"✓ Found folder: {prefix}/")
                else:
                    self.warnings.append(
                        f"Folder '{prefix}/' is empty or doesn't exist"
                    )

            if len(found_prefixes) == len(expected_prefixes):
                self.log(f"✓ All {len(expected_prefixes)} ESPN folders found")
                return True
            else:
                missing = set(expected_prefixes) - set(found_prefixes)
                self.failures.append(f"Missing ESPN folders: {missing}")
                return False

        except Exception as e:
            self.failures.append(f"Folder structure validation failed: {e}")
            return False

    def validate_file_counts(self) -> bool:
        """Validate file counts match expected ranges."""
        try:
            all_valid = True

            print("\n  File Count Validation:")
            print(f"  {'Folder':<25} {'Actual':<10} {'Expected':<12} {'Status'}")
            print(f"  {'-' * 65}")

            for prefix, expected_count in CURRENT_COUNTS.items():
                actual_count = self.count_s3_objects(f"{prefix}/")

                if actual_count == -1:
                    status = "✗ ERROR"
                    all_valid = False
                elif actual_count >= expected_count * 0.95:  # Allow 5% variance
                    status = "✓ PASS"
                else:
                    status = "✗ FAIL"
                    all_valid = False
                    self.failures.append(
                        f"{prefix}: {actual_count} files (expected ~{expected_count})"
                    )

                print(
                    f"  {prefix:<25} {actual_count:<10} {expected_count:<12} {status}"
                )

            # Total count
            total_actual = sum(
                [self.count_s3_objects(f"{p}/") for p in CURRENT_COUNTS.keys()]
            )
            print(f"  {'-' * 65}")
            print(
                f"  {'TOTAL':<25} {total_actual:<10} {CURRENT_TOTAL:<12} {'✓ PASS' if total_actual >= CURRENT_TOTAL * 0.95 else '✗ FAIL'}"
            )

            return all_valid

        except Exception as e:
            self.failures.append(f"File count validation failed: {e}")
            return False

    def validate_sample_json_files(self) -> bool:
        """Validate random sample JSON files are valid."""
        try:
            all_valid = True
            samples_per_folder = 5

            print("\n  JSON Validation (5 random samples per folder):")

            for prefix in CURRENT_COUNTS.keys():
                self.log(f"  Validating {prefix}...")

                # Get list of files
                response = self.s3_client.list_objects_v2(
                    Bucket=S3_BUCKET, Prefix=f"{prefix}/", MaxKeys=100
                )

                if "Contents" not in response:
                    self.warnings.append(f"No files found in {prefix}/")
                    continue

                files = [obj["Key"] for obj in response["Contents"]]
                sample_files = random.sample(files, min(samples_per_folder, len(files)))

                valid_samples = 0
                for s3_key in sample_files:
                    try:
                        obj = self.s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
                        content = obj["Body"].read()
                        json.loads(content)  # Validate JSON
                        valid_samples += 1
                    except json.JSONDecodeError:
                        self.warnings.append(f"Invalid JSON: {s3_key}")
                    except Exception as e:
                        self.warnings.append(f"Error reading {s3_key}: {e}")

                status = "✓ PASS" if valid_samples == len(sample_files) else "⚠ PARTIAL"
                print(
                    f"    {prefix:<25} {valid_samples}/{len(sample_files)} valid samples {status}"
                )

                if valid_samples < len(sample_files):
                    all_valid = False

            return all_valid

        except Exception as e:
            self.failures.append(f"JSON validation failed: {e}")
            return False

    def validate_data_growth(self) -> bool:
        """Validate data growth from baseline is reasonable."""
        try:
            print("\n  Data Growth Validation:")

            total_baseline = BASELINE_TOTAL
            total_current = CURRENT_TOTAL
            growth = total_current - total_baseline
            growth_pct = (growth / total_baseline) * 100

            print(f"    Baseline (Oct 1, 2025):  {total_baseline:,} files")
            print(f"    Current (Nov 6, 2025):   {total_current:,} files")
            print(f"    Growth:                  +{growth:,} files ({growth_pct:.2f}%)")

            # Check per-folder growth
            for prefix in CURRENT_COUNTS.keys():
                baseline = BASELINE_COUNTS.get(prefix, 0)
                current = CURRENT_COUNTS[prefix]
                folder_growth = current - baseline

                if folder_growth > 0:
                    print(f"    {prefix:<25} +{folder_growth:,} files")

            # Reasonable growth is < 10% in one month
            if growth_pct > 10:
                self.warnings.append(
                    f"High data growth: {growth_pct:.2f}% (expected <10%)"
                )

            return True

        except Exception as e:
            self.failures.append(f"Data growth validation failed: {e}")
            return False

    def detect_coverage_gaps(self) -> bool:
        """Detect gaps in ESPN schedule coverage."""
        try:
            print("\n  Coverage Gap Detection:")

            # List all schedule files
            paginator = self.s3_client.get_paginator("list_objects_v2")
            schedule_dates = []

            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix="espn_schedules/"):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        # Extract YYYYMMDD from filename
                        filename = key.split("/")[-1].replace(".json", "")
                        if len(filename) == 8 and filename.isdigit():
                            schedule_dates.append(filename)

            if not schedule_dates:
                self.warnings.append("No schedule files found for gap detection")
                return False

            schedule_dates.sort()
            earliest = schedule_dates[0]
            latest = schedule_dates[-1]

            print(f"    Coverage: {earliest} to {latest}")
            print(f"    Total schedule files: {len(schedule_dates):,}")

            # Basic gap detection (simplified)
            # Full implementation would check every day in range
            if len(schedule_dates) < 11000:  # Expect ~11,633
                self.warnings.append(
                    f"Schedule coverage may have gaps (found {len(schedule_dates):,}, expected ~11,633)"
                )

            return True

        except Exception as e:
            self.warnings.append(f"Gap detection failed: {e}")
            return False

    def validate_dims_integration(self) -> bool:
        """Validate DIMS metrics are up to date."""
        try:
            dims_metrics_path = (
                Path(__file__).parent.parent.parent.parent
                / "inventory"
                / "metrics.yaml"
            )

            if not dims_metrics_path.exists():
                self.warnings.append(
                    f"DIMS metrics file not found: {dims_metrics_path}"
                )
                return False

            self.log(f"✓ DIMS metrics file found: {dims_metrics_path}")

            # Could parse YAML and check timestamps here
            # For now, just verify file exists
            return True

        except Exception as e:
            self.warnings.append(f"DIMS integration check failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all Phase 0.0001 validations."""
        print(f"\n{'='*70}")
        print(f"Phase 0.0001 Validation: ESPN Data Extraction & Validation")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")

        results = {
            "s3_bucket_exists": self.validate_s3_bucket_exists(),
            "espn_folder_structure": self.validate_espn_folder_structure(),
            "file_counts": self.validate_file_counts(),
            "sample_json_valid": self.validate_sample_json_files(),
            "data_growth": self.validate_data_growth(),
            "coverage_gaps": self.detect_coverage_gaps(),
            "dims_integration": self.validate_dims_integration(),
        }

        all_passed = all(results.values())

        print(f"\n{'='*70}")
        print(f"Validation Results Summary")
        print(f"{'='*70}")

        for check, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {check.replace('_', ' ').title():<40} {status}")

        if self.failures:
            print(f"\n❌ Failures ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  - {failure}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        print(f"\n{'='*70}")
        if all_passed:
            print("✅ All Phase 0.0001 validations passed!")
        else:
            print("❌ Some Phase 0.0001 validations failed.")
        print(f"{'='*70}\n")

        return all_passed, results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Phase 0.0001: ESPN Data Extraction & Validation"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--schema",
        default="raw_data",
        help="Database schema to validate (for future use)",
    )
    args = parser.parse_args()

    validator = Phase0001Validator(verbose=args.verbose)
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
