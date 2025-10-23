#!/usr/bin/env python3
"""
Phase 0.4 Validator: Basketball Reference Data Collection

Validates Phase 0.4 (Basketball Reference) completeness and quality.

Validation Checks:
- S3 bucket exists and is accessible
- All 14 data category directories present
- File count meets expectations (~444 files)
- Temporal coverage verified (1953-2025)
- File sizes reasonable (~99.9 MB total)
- JSON format validity (sample files)
- Data categories match documentation

Usage:
    python validators/phases/phase_0/validate_0_4_basketball_reference.py
    python validators/phases/phase_0/validate_0_4_basketball_reference.py --verbose

Exit Codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import boto3
from botocore.exceptions import ClientError

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))


class BasketballReferenceValidator:
    """Validator for Phase 0.4: Basketball Reference Data Collection"""

    # Expected data categories in S3
    EXPECTED_CATEGORIES = [
        "advanced_totals",
        "awards",
        "coaches",
        "draft",
        "per_game",
        "play_by_play",
        "playoffs",
        "schedules",
        "season_totals",
        "shooting",
        "standings",
        "standings_by_date",
        "team_ratings",
        "transactions",
    ]

    # Expected file count (as of Oct 2025: 444 files)
    EXPECTED_FILE_COUNT_MIN = 400  # Minimum acceptable
    EXPECTED_FILE_COUNT_MAX = 500  # Maximum expected (allows for growth)

    # Expected total size (~99.9 MB as of Oct 2025)
    EXPECTED_SIZE_MB_MIN = 90  # Minimum acceptable
    EXPECTED_SIZE_MB_MAX = 120  # Maximum expected

    # Temporal coverage
    EXPECTED_MIN_YEAR = 1953
    EXPECTED_MAX_YEAR = 2025

    def __init__(self, verbose: bool = False):
        """
        Initialize validator

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.bucket_name = "nba-sim-raw-data-lake"
        self.s3_prefix = "basketball_reference/"
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors: List[str] = []

        # Initialize S3 client
        try:
            self.s3 = boto3.client("s3")
        except Exception as e:
            self.errors.append(f"Failed to initialize S3 client: {e}")
            self.s3 = None

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log message if verbose enabled

        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        if self.verbose or level != "INFO":
            prefix = "  " if level == "INFO" else f"[{level}] "
            print(f"{prefix}{message}")

    def validate_s3_bucket_access(self) -> bool:
        """
        Validate S3 bucket exists and is accessible

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking S3 bucket access...")

        if self.s3 is None:
            self.errors.append("S3 client not initialized")
            return False

        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            self.log(f"✓ S3 bucket '{self.bucket_name}' is accessible")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                self.errors.append(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == "403":
                self.errors.append(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                self.errors.append(
                    f"Error accessing S3 bucket '{self.bucket_name}': {e}"
                )
            return False

    def validate_data_categories(self) -> bool:
        """
        Validate all expected data category directories exist

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking data category directories...")

        if self.s3 is None:
            self.errors.append("S3 client not initialized")
            return False

        try:
            # List top-level prefixes
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name, Prefix=self.s3_prefix, Delimiter="/"
            )

            # Extract directory names
            existing_dirs = set()
            if "CommonPrefixes" in response:
                for prefix in response["CommonPrefixes"]:
                    dir_name = prefix["Prefix"].replace(self.s3_prefix, "").rstrip("/")
                    existing_dirs.add(dir_name)

            # Check for expected categories
            missing_categories = set(self.EXPECTED_CATEGORIES) - existing_dirs
            extra_categories = existing_dirs - set(self.EXPECTED_CATEGORIES)

            all_passed = True

            if missing_categories:
                self.errors.append(
                    f"Missing data categories: {', '.join(sorted(missing_categories))}"
                )
                all_passed = False
            else:
                self.log(
                    f"✓ All {len(self.EXPECTED_CATEGORIES)} expected data categories present"
                )

            if extra_categories:
                # Extra categories are not necessarily errors, just warnings
                if self.verbose:
                    print(
                        f"  Note: Found additional categories: {', '.join(sorted(extra_categories))}"
                    )

            return all_passed

        except Exception as e:
            self.errors.append(f"Error listing data categories: {e}")
            return False

    def validate_file_count(self) -> bool:
        """
        Validate total file count is within expected range

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking file count...")

        if self.s3 is None:
            self.errors.append("S3 client not initialized")
            return False

        try:
            # Count all files under basketball_reference/
            paginator = self.s3.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name, Prefix=self.s3_prefix
            )

            total_files = 0
            total_size_bytes = 0

            for page in page_iterator:
                if "Contents" in page:
                    total_files += len(page["Contents"])
                    total_size_bytes += sum(obj["Size"] for obj in page["Contents"])

            total_size_mb = total_size_bytes / (1024 * 1024)

            # Check file count
            if total_files < self.EXPECTED_FILE_COUNT_MIN:
                self.errors.append(
                    f"File count {total_files} is below minimum {self.EXPECTED_FILE_COUNT_MIN}"
                )
                return False
            elif total_files > self.EXPECTED_FILE_COUNT_MAX:
                self.errors.append(
                    f"File count {total_files} exceeds maximum {self.EXPECTED_FILE_COUNT_MAX}"
                )
                return False
            else:
                self.log(
                    f"✓ File count: {total_files} (expected {self.EXPECTED_FILE_COUNT_MIN}-{self.EXPECTED_FILE_COUNT_MAX})"
                )

            # Check total size
            if total_size_mb < self.EXPECTED_SIZE_MB_MIN:
                self.errors.append(
                    f"Total size {total_size_mb:.1f} MB is below minimum {self.EXPECTED_SIZE_MB_MIN} MB"
                )
                return False
            elif total_size_mb > self.EXPECTED_SIZE_MB_MAX:
                self.errors.append(
                    f"Total size {total_size_mb:.1f} MB exceeds maximum {self.EXPECTED_SIZE_MB_MAX} MB"
                )
                return False
            else:
                self.log(
                    f"✓ Total size: {total_size_mb:.1f} MB (expected {self.EXPECTED_SIZE_MB_MIN}-{self.EXPECTED_SIZE_MB_MAX} MB)"
                )

            return True

        except Exception as e:
            self.errors.append(f"Error counting files: {e}")
            return False

    def validate_temporal_coverage(self) -> bool:
        """
        Validate temporal coverage spans expected years (1953-2025)

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking temporal coverage...")

        if self.s3 is None:
            self.errors.append("S3 client not initialized")
            return False

        try:
            # Check advanced_totals for year range (has files from 1953 onwards)
            paginator = self.s3.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=f"{self.s3_prefix}advanced_totals/",
            )

            years_found = set()

            for page in page_iterator:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        # Extract year from path like "basketball_reference/advanced_totals/1953/"
                        parts = key.split("/")
                        if len(parts) >= 3:
                            year_str = parts[2]
                            if year_str.isdigit():
                                years_found.add(int(year_str))

            if not years_found:
                self.errors.append("No years found in advanced_totals data")
                return False

            min_year = min(years_found)
            max_year = max(years_found)
            year_count = len(years_found)

            # Check if coverage meets expectations
            if min_year > self.EXPECTED_MIN_YEAR:
                self.errors.append(
                    f"Earliest year {min_year} is later than expected {self.EXPECTED_MIN_YEAR}"
                )
                return False

            if max_year < self.EXPECTED_MAX_YEAR - 1:  # Allow 1 year tolerance
                self.errors.append(
                    f"Latest year {max_year} is earlier than expected {self.EXPECTED_MAX_YEAR}"
                )
                return False

            self.log(f"✓ Temporal coverage: {min_year}-{max_year} ({year_count} years)")
            return True

        except Exception as e:
            self.errors.append(f"Error checking temporal coverage: {e}")
            return False

    def validate_json_format(self) -> bool:
        """
        Validate JSON format of sample files

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking JSON format (sample files)...")

        if self.s3 is None:
            self.errors.append("S3 client not initialized")
            return False

        try:
            # Get a few sample JSON files to validate format
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{self.s3_prefix}advanced_totals/2025/",
                MaxKeys=1,
            )

            if "Contents" not in response or not response["Contents"]:
                self.errors.append("No sample files found in advanced_totals/2025/")
                return False

            sample_key = response["Contents"][0]["Key"]

            # Download and parse JSON
            obj = self.s3.get_object(Bucket=self.bucket_name, Key=sample_key)
            content = obj["Body"].read().decode("utf-8")

            try:
                data = json.loads(content)
                if not isinstance(data, (dict, list)):
                    self.errors.append(
                        f"JSON file {sample_key} does not contain dict or list"
                    )
                    return False

                self.log(f"✓ Sample JSON file valid: {sample_key}")
                return True

            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {sample_key}: {e}")
                return False

        except Exception as e:
            self.errors.append(f"Error validating JSON format: {e}")
            return False

    def validate_category_file_counts(self) -> bool:
        """
        Validate each data category has files

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking file counts per category...")

        if self.s3 is None:
            self.errors.append("S3 client not initialized")
            return False

        try:
            empty_categories = []

            for category in self.EXPECTED_CATEGORIES:
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=f"{self.s3_prefix}{category}/",
                    MaxKeys=1,
                )

                if "Contents" not in response or not response["Contents"]:
                    empty_categories.append(category)

            if empty_categories:
                self.errors.append(
                    f"Empty categories (no files): {', '.join(empty_categories)}"
                )
                return False
            else:
                self.log(f"✓ All {len(self.EXPECTED_CATEGORIES)} categories have files")
                return True

        except Exception as e:
            self.errors.append(f"Error checking category file counts: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """
        Run all validations and return results

        Returns:
            Tuple of (all_passed, results_dict)
        """
        print(f"\n{'=' * 60}")
        print(f"Phase 0.4: Basketball Reference Validation")
        print(f"{'=' * 60}\n")

        results = {
            "s3_bucket_access": self.validate_s3_bucket_access(),
            "data_categories": self.validate_data_categories(),
            "file_count": self.validate_file_count(),
            "temporal_coverage": self.validate_temporal_coverage(),
            "json_format": self.validate_json_format(),
            "category_file_counts": self.validate_category_file_counts(),
        }

        all_passed = all(results.values())

        print(f"\n{'=' * 60}")
        print(f"Results Summary")
        print(f"{'=' * 60}")

        for check, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{check:40} {status}")

        if self.errors:
            print(f"\n❌ Failures:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n⚠️  Warnings: {self.warnings} warnings encountered")

        print(f"\n{'=' * 60}")
        if all_passed:
            print("✅ All validations passed!")
        else:
            print("❌ Some validations failed. See details above.")
        print(f"{'=' * 60}\n")

        return all_passed, results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Phase 0.4 Basketball Reference data collection"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    validator = BasketballReferenceValidator(verbose=args.verbose)
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
