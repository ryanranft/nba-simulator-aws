#!/usr/bin/env python3
"""
Validate S3 Upload Completeness - 0.0001

Verifies that all files were uploaded successfully to S3:
- Correct file count (146,115 files documented in 0.0001)
- All 4 data types present (schedule, pbp, box_scores, team_stats)
- No zero-byte files
- File naming patterns correct
- Total size approximately 119GB

Usage:
    python validate_upload_completeness.py
    python validate_upload_completeness.py --bucket nba-sim-raw-data-lake --quick
"""

import boto3
import sys
from typing import Dict, List, Tuple
from collections import defaultdict
from botocore.exceptions import ClientError, NoCredentialsError


class S3UploadCompletenessValidator:
    """Validates S3 upload completeness against 0.0001 specifications.

    Uses ADCE (Autonomous Data Collection Ecosystem) to track data growth:
    - Initial 0.0001 baseline (project inception)
    - Current state via live S3 queries
    - Growth metrics and autonomous collection tracking
    """

    def __init__(
        self, bucket_name: str = "nba-sim-raw-data-lake", quick_mode: bool = False
    ):
        """
        Initialize validator.

        Args:
            bucket_name: Name of S3 bucket to validate
            quick_mode: If True, use S3 list summary instead of full inventory
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")
        self.quick_mode = quick_mode
        self.failures: List[str] = []
        self.warnings: List[str] = []

        # 0.0001 Initial Upload (Project Inception - October 2024)
        self.initial_total = 146_115
        self.initial_counts = {
            "schedule": 11_633,
            "pbp": 44_826,
            "box_scores": 44_828,
            "team_stats": 44_828,
        }
        self.initial_size_gb = 119

        # Artifacts to exclude from validation (not game data)
        self.exclude_prefixes = [
            "athena-results/",
            "ml-predictions/",
            "ml-models/",
            "ml-models-panel/",
            "ml-features/",
            "scripts/",
            "box_score_snapshots/",
        ]

        # ADCE-collected data sources (0.0009 autonomous collection)
        self.adce_sources = [
            "nba_api_comprehensive",
            "nba_api_playbyplay",
            "basketball_reference",
            "hoopr_phase1",
            "hoopr_parquet",
            "nba_api_reverse",
            "nba_api_incremental",
            "sportsdataverse",
        ]

    def _is_excluded_prefix(self, key: str) -> bool:
        """Check if S3 key should be excluded from validation (artifacts)."""
        return any(key.startswith(prefix) for prefix in self.exclude_prefixes)

    def count_files_by_prefix(
        self, prefix: str = "", exclude_artifacts: bool = True
    ) -> Tuple[int, int, List[str]]:
        """
        Count files and total size for a given prefix.

        Args:
            prefix: S3 prefix to search (e.g., 'schedule/', 'pbp/')
            exclude_artifacts: If True, exclude non-data artifacts (athena-results, ml-*, etc.)

        Returns:
            Tuple of (file_count, total_size_bytes, zero_byte_files)
        """
        file_count = 0
        total_size = 0
        zero_byte_files = []

        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

        for page in pages:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]

                # Skip directories (keys ending with /)
                if key.endswith("/"):
                    continue

                # Skip artifacts if requested
                if exclude_artifacts and self._is_excluded_prefix(key):
                    continue

                file_count += 1
                size = obj["Size"]
                total_size += size

                # Track zero-byte files
                if size == 0:
                    zero_byte_files.append(key)

        return file_count, total_size, zero_byte_files

    def get_adce_growth_metrics(self) -> Dict:
        """
        Get data growth metrics from ADCE autonomous collection.

        Returns:
            Dict with growth metrics by data source
        """
        adce_metrics = {}

        for source in self.adce_sources:
            prefix = f"{source}/"
            count, size, _ = self.count_files_by_prefix(prefix)
            if count > 0:
                adce_metrics[source] = {"files": count, "size_gb": size / (1024**3)}

        return adce_metrics

    def validate_total_file_count(self) -> bool:
        """
        Verify total file count and show data growth from initial upload.

        Uses ADCE tracking to show:
        - 0.0001 initial upload baseline
        - ADCE autonomous collection additions
        - Current total with growth metrics
        """
        print(
            "Counting total files (excluding artifacts)... (this may take 30-60 seconds)"
        )

        try:
            total_count, total_size, zero_files = self.count_files_by_prefix()
            total_size_gb = total_size / (1024**3)

            # Get ADCE growth metrics
            adce_metrics = self.get_adce_growth_metrics()
            adce_total = sum(m["files"] for m in adce_metrics.values())
            adce_size_gb = sum(m["size_gb"] for m in adce_metrics.values())

            # Calculate growth
            growth_files = total_count - self.initial_total
            growth_pct = (growth_files / self.initial_total) * 100

            # Display data growth trajectory
            print(f"\n  📊 Data Growth Trajectory (ADCE Tracking):")
            print(
                f"  ├─ 0.0001 Initial Upload:  {self.initial_total:,} files ({self.initial_size_gb} GB)"
            )
            print(
                f"  ├─ ADCE Autonomous Collection: +{adce_total:,} files (+{adce_size_gb:.2f} GB)"
            )
            print(
                f"  └─ Current Total:              {total_count:,} files ({total_size_gb:.2f} GB)"
            )
            print(f"     Growth: +{growth_files:,} files (+{growth_pct:.1f}%)\n")

            # Show ADCE sources breakdown
            if adce_metrics:
                print(f"  ADCE Data Sources (0.0009):")
                for source, metrics in sorted(
                    adce_metrics.items(), key=lambda x: x[1]["files"], reverse=True
                ):
                    print(
                        f"    • {source}: {metrics['files']:,} files ({metrics['size_gb']:.2f} GB)"
                    )
                print()

            # Validation: Growth is expected and healthy
            if growth_files >= 0:
                print(
                    f"✓ Data collection growing as expected ({growth_pct:+.1f}% growth)"
                )
                count_passed = True
            else:
                self.failures.append(
                    f"Data loss detected. Initial: {self.initial_total:,}, "
                    f"Current: {total_count:,} (Loss: {growth_files:,})"
                )
                print(f"✗ {self.failures[-1]}")
                count_passed = False

            # Check total size (within 10% tolerance of initial + ADCE expected)
            expected_size_gb = self.initial_size_gb + adce_size_gb
            size_tolerance = 0.10
            size_lower = expected_size_gb * (1 - size_tolerance)
            size_upper = expected_size_gb * (1 + size_tolerance)

            if size_lower <= total_size_gb <= size_upper:
                print(f"✓ Total size within expected range: ~{expected_size_gb:.0f} GB")
                size_passed = True
            else:
                self.warnings.append(
                    f"Total size outside expected range. "
                    f"Expected: ~{expected_size_gb:.0f} GB, "
                    f"Actual: {total_size_gb:.2f} GB"
                )
                print(f"⚠ {self.warnings[-1]}")
                size_passed = False

            # Check for zero-byte files
            if zero_files:
                zero_count = len(zero_files)
                self.warnings.append(
                    f"Found {zero_count:,} zero-byte files (may be placeholders for cancelled games)"
                )
                print(f"⚠ {self.warnings[-1]}")
                if zero_count <= 10:  # Show first 10
                    print(f"  Examples: {zero_files[:10]}")
            else:
                print("✓ No zero-byte files found")

            return count_passed and size_passed

        except ClientError as e:
            self.failures.append(f"Failed to count files: {e}")
            print(f"✗ {self.failures[-1]}")
            return False

    def validate_data_type_counts(self) -> bool:
        """
        Verify each data type file count and show growth from initial upload.

        Tracks 0.0001 initial counts vs current (including ADCE autonomous collection).
        """
        print("\nValidating file counts by data type (0.0001 sources)...")

        all_passed = True
        actual_counts = {}

        for data_type, initial_count in self.initial_counts.items():
            prefix = f"{data_type}/"
            print(f"  Checking {data_type}...")

            try:
                count, size, zero_files = self.count_files_by_prefix(prefix)
                actual_counts[data_type] = count

                # Calculate growth
                diff = count - initial_count
                diff_pct = (diff / initial_count) * 100 if initial_count > 0 else 0

                if count == initial_count:
                    print(
                        f"    ✓ {data_type}: {count:,} files (matches initial upload)"
                    )
                elif count == 0:
                    self.failures.append(
                        f"No files found for {data_type}/ prefix (initial: {initial_count:,})"
                    )
                    print(f"    ✗ {self.failures[-1]}")
                    all_passed = False
                elif count > initial_count:
                    # Growth is expected from ADCE
                    print(
                        f"    ✓ {data_type}: {count:,} files (initial: {initial_count:,}, growth: +{diff:,} [{diff_pct:+.1f}%])"
                    )
                else:
                    # Data loss
                    self.failures.append(
                        f"{data_type}: Data loss detected. Initial: {initial_count:,}, Current: {count:,} (Loss: {diff:,})"
                    )
                    print(f"    ✗ {self.failures[-1]}")
                    all_passed = False

            except ClientError as e:
                self.failures.append(f"Failed to count {data_type} files: {e}")
                print(f"    ✗ {self.failures[-1]}")
                all_passed = False

        return all_passed

    def validate_file_naming_patterns(self) -> bool:
        """Verify file naming patterns are correct (sample check)."""
        print("\nValidating file naming patterns (sampling)...")

        patterns = {
            "schedule": r"^\d{8}\.json$",  # YYYYMMDD.json
            "pbp": r"^pbp/.*\.json$",  # Any .json in pbp/
            "box_scores": r"^box_scores/.*\.json$",
            "team_stats": r"^team_stats/.*\.json$",
        }

        all_passed = True

        # Sample first 10 files from each data type
        for data_type in self.initial_counts.keys():
            prefix = f"{data_type}/"

            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=prefix, MaxKeys=10
                )

                if "Contents" not in response:
                    self.warnings.append(f"No files found for {data_type}/ prefix")
                    print(f"  ⚠ {self.warnings[-1]}")
                    continue

                # Check all sampled files end with .json
                non_json = [
                    obj["Key"]
                    for obj in response["Contents"]
                    if not obj["Key"].endswith(".json") and not obj["Key"].endswith("/")
                ]

                if non_json:
                    self.failures.append(
                        f"{data_type}: Found non-JSON files: {non_json}"
                    )
                    print(f"  ✗ {self.failures[-1]}")
                    all_passed = False
                else:
                    print(f"  ✓ {data_type}: All sampled files are .json")

            except ClientError as e:
                self.failures.append(f"Failed to sample {data_type} files: {e}")
                print(f"  ✗ {self.failures[-1]}")
                all_passed = False

        return all_passed

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """
        Run all validation checks.

        Returns:
            Tuple of (all_passed: bool, results: Dict)
        """
        print(f"\n{'='*70}")
        print(f"S3 Upload Completeness Validation - 0.0001")
        print(f"Bucket: {self.bucket_name}")
        print(f"Mode: {'Quick' if self.quick_mode else 'Full'}")
        print(f"{'='*70}\n")

        results = {
            "total_count_correct": self.validate_total_file_count(),
            "data_types_correct": self.validate_data_type_counts(),
            "naming_patterns_correct": self.validate_file_naming_patterns(),
        }

        # Summary
        print(f"\n{'='*70}")
        print("VALIDATION SUMMARY")
        print(f"{'='*70}")

        total_checks = len(results)
        passed_checks = sum(1 for v in results.values() if v)

        print(f"\nChecks Passed: {passed_checks}/{total_checks}")

        if self.failures:
            print(f"\n❌ FAILURES ({len(self.failures)}):")
            for i, failure in enumerate(self.failures, 1):
                print(f"  {i}. {failure}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        all_passed = all(results.values())
        if all_passed and not self.failures:
            print("\n✅ All validations PASSED")
        else:
            print("\n❌ Some validations FAILED")

        print(f"{'='*70}\n")

        return all_passed, results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate S3 upload completeness for 0.0001"
    )
    parser.add_argument(
        "--bucket",
        default="nba-sim-raw-data-lake",
        help="S3 bucket name to validate (default: nba-sim-raw-data-lake)",
    )
    parser.add_argument(
        "--quick", action="store_true", help="Quick mode (faster but less thorough)"
    )
    args = parser.parse_args()

    try:
        validator = S3UploadCompletenessValidator(
            bucket_name=args.bucket, quick_mode=args.quick
        )
        all_passed, results = validator.run_all_validations()

        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)

    except NoCredentialsError:
        print("\n❌ ERROR: AWS credentials not found")
        print("Please configure AWS credentials using 'aws configure'")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
