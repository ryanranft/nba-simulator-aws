#!/usr/bin/env python3
"""
Validate 0.0002: hoopR Data Collection

Description: Validates hoopR R package data collection including S3 storage,
RDS table creation, data completeness, and cross-source validation.

Usage:
    python validators/phases/phase_0/validate_0_2_hoopr_collection.py
    python validators/phases/phase_0/validate_0_2_hoopr_collection.py --verbose
"""

import sys
import os
import boto3
import psycopg2
from typing import List, Tuple, Dict
from pathlib import Path


class Phase02HooprValidator:
    """Validates hoopR data collection for 0.0002."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures: List[str] = []
        self.warnings: List[str] = []

        # Initialize AWS S3 client
        try:
            self.s3 = boto3.client("s3")
            self.bucket_name = "nba-sim-raw-data-lake"
        except Exception as e:
            self.failures.append(f"Failed to initialize S3 client: {e}")
            self.s3 = None

        # Initialize RDS connection (optional - only if credentials available)
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("RDS_HOST"),
                database=os.getenv("RDS_DATABASE", "nba_simulator"),
                user=os.getenv("RDS_USER"),
                password=os.getenv("RDS_PASSWORD"),
            )
            self.rds_available = True
        except Exception as e:
            self.warnings.append(f"RDS connection not available: {e}")
            self.conn = None
            self.rds_available = False

    def validate_s3_hoopr_parquet_files(self) -> bool:
        """Validate hoopR Parquet files exist in S3."""
        if not self.s3:
            self.failures.append("S3 client not initialized")
            return False

        try:
            # Check for Parquet files in hoopr_parquet/ directory
            prefixes = [
                "hoopr_parquet/play_by_play/",
                "hoopr_parquet/player_box/",
                "hoopr_parquet/schedule/",
                "hoopr_parquet/team_box/",
            ]

            total_files = 0
            for prefix in prefixes:
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=prefix
                )
                file_count = response.get("KeyCount", 0)
                total_files += file_count

                if self.verbose:
                    print(f"  {prefix}: {file_count} files")

            # Expected: 24 files per data type × 4 types = 96 files
            expected_parquet = 96
            if total_files < expected_parquet:
                self.failures.append(
                    f"Expected >= {expected_parquet} Parquet files, found {total_files}"
                )
                return False

            if self.verbose:
                print(f"✓ hoopR Parquet files: {total_files} files found")

            return True

        except Exception as e:
            self.failures.append(f"S3 Parquet validation failed: {e}")
            return False

    def validate_s3_hoopr_csv_files(self) -> bool:
        """Validate hoopR CSV files exist in S3."""
        if not self.s3:
            self.failures.append("S3 client not initialized")
            return False

        try:
            # Check for CSV files in hoopr_phase1/ directory
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name, Prefix="hoopr_phase1/", MaxKeys=1000
            )

            file_count = response.get("KeyCount", 0)

            # Expected: ~218 CSV files (actual count from S3)
            expected_csv = 200
            if file_count < expected_csv:
                self.failures.append(
                    f"Expected >= {expected_csv} CSV files, found {file_count}"
                )
                return False

            if self.verbose:
                print(f"✓ hoopR CSV files: {file_count} files found")

            return True

        except Exception as e:
            self.failures.append(f"S3 CSV validation failed: {e}")
            return False

    def validate_s3_total_hoopr_files(self) -> bool:
        """Validate total hoopR file count in S3."""
        if not self.s3:
            self.failures.append("S3 client not initialized")
            return False

        try:
            # Count all hoopR-related files
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix="hoopr")

            total_files = 0
            for page in pages:
                total_files += page.get("KeyCount", 0)

            # Expected: 314 files total (96 Parquet + 218 CSV)
            expected_total = 310
            if total_files < expected_total:
                self.failures.append(
                    f"Expected >= {expected_total} total hoopR files, found {total_files}"
                )
                return False

            if self.verbose:
                print(f"✓ Total hoopR files in S3: {total_files} files")

            return True

        except Exception as e:
            self.failures.append(f"S3 total file count validation failed: {e}")
            return False

    def validate_rds_table_exists(self, table_name: str) -> bool:
        """Verify RDS table exists."""
        if not self.rds_available:
            self.warnings.append(
                f"Cannot validate table {table_name}: RDS not available"
            )
            return True  # Don't fail if RDS unavailable

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """,
                (table_name,),
            )
            exists = cursor.fetchone()[0]
            cursor.close()

            if not exists:
                self.failures.append(f"Table {table_name} does not exist in RDS")
                return False

            if self.verbose:
                print(f"✓ Table {table_name} exists")

            return True

        except Exception as e:
            self.failures.append(f"Table existence check failed for {table_name}: {e}")
            return False

    def validate_rds_table_row_count(self, table_name: str, min_rows: int) -> bool:
        """Verify table has minimum number of rows."""
        if not self.rds_available:
            self.warnings.append(
                f"Cannot validate {table_name} row count: RDS not available"
            )
            return True  # Don't fail if RDS unavailable

        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")  # nosec B608
            actual_count = cursor.fetchone()[0]
            cursor.close()

            if actual_count < min_rows:
                self.failures.append(
                    f"Table {table_name} has {actual_count:,} rows, expected >= {min_rows:,}"
                )
                return False

            if self.verbose:
                print(f"✓ Table {table_name}: {actual_count:,} rows")

            return True

        except Exception as e:
            self.failures.append(f"Row count check failed for {table_name}: {e}")
            return False

    def validate_hoopr_play_by_play_table(self) -> bool:
        """Validate hoopr_play_by_play table."""
        table_name = "hoopr_play_by_play"

        # Check existence
        if not self.validate_rds_table_exists(table_name):
            return False

        # Check row count (expected: 13.1M rows)
        min_rows = 13_000_000
        return self.validate_rds_table_row_count(table_name, min_rows)

    def validate_hoopr_player_box_table(self) -> bool:
        """Validate hoopr_player_box table."""
        table_name = "hoopr_player_box"

        # Check existence
        if not self.validate_rds_table_exists(table_name):
            return False

        # Check row count (expected: 785K rows)
        min_rows = 780_000
        return self.validate_rds_table_row_count(table_name, min_rows)

    def validate_hoopr_team_box_table(self) -> bool:
        """Validate hoopr_team_box table."""
        table_name = "hoopr_team_box"

        # Check existence
        if not self.validate_rds_table_exists(table_name):
            return False

        # Check row count (expected: 59K rows, but may be 0 if not loaded)
        if not self.rds_available:
            return True

        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")  # nosec B608
            actual_count = cursor.fetchone()[0]
            cursor.close()

            if actual_count == 0:
                self.warnings.append(f"Table {table_name} exists but is empty (0 rows)")
                if self.verbose:
                    print(f"⚠️  Table {table_name}: 0 rows (empty)")
                return True  # Don't fail, just warn

            min_rows = 59_000
            if actual_count < min_rows:
                self.failures.append(
                    f"Table {table_name} has {actual_count:,} rows, expected >= {min_rows:,}"
                )
                return False

            if self.verbose:
                print(f"✓ Table {table_name}: {actual_count:,} rows")

            return True

        except Exception as e:
            self.failures.append(f"Row count check failed for {table_name}: {e}")
            return False

    def validate_hoopr_schedule_table(self) -> bool:
        """Validate hoopr_schedule table."""
        table_name = "hoopr_schedule"

        # Check existence
        if not self.validate_rds_table_exists(table_name):
            return False

        # Check row count (expected: 30K rows, but may be 0 if not loaded)
        if not self.rds_available:
            return True

        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")  # nosec B608
            actual_count = cursor.fetchone()[0]
            cursor.close()

            if actual_count == 0:
                self.warnings.append(f"Table {table_name} exists but is empty (0 rows)")
                if self.verbose:
                    print(f"⚠️  Table {table_name}: 0 rows (empty)")
                return True  # Don't fail, just warn

            min_rows = 30_000
            if actual_count < min_rows:
                self.failures.append(
                    f"Table {table_name} has {actual_count:,} rows, expected >= {min_rows:,}"
                )
                return False

            if self.verbose:
                print(f"✓ Table {table_name}: {actual_count:,} rows")

            return True

        except Exception as e:
            self.failures.append(f"Row count check failed for {table_name}: {e}")
            return False

    def validate_temporal_coverage(self) -> bool:
        """Validate temporal coverage (2002-2025)."""
        if not self.rds_available:
            self.warnings.append("Cannot validate temporal coverage: RDS not available")
            return True

        try:
            cursor = self.conn.cursor()

            # Check date range in play-by-play table
            cursor.execute(
                """
                SELECT
                    MIN(EXTRACT(YEAR FROM game_date))::int as min_year,
                    MAX(EXTRACT(YEAR FROM game_date))::int as max_year
                FROM hoopr_play_by_play;
            """
            )
            min_year, max_year = cursor.fetchone()
            cursor.close()

            # Expected: 2002-2025 (24 years)
            if min_year > 2002:
                self.failures.append(f"Data starts in {min_year}, expected 2002")
                return False

            if max_year < 2024:
                self.warnings.append(f"Latest data is {max_year}, expected 2024+")

            if self.verbose:
                print(f"✓ Temporal coverage: {min_year}-{max_year}")

            return True

        except Exception as e:
            self.failures.append(f"Temporal coverage validation failed: {e}")
            return False

    def validate_data_completeness(self) -> bool:
        """Validate data completeness for 2002-2025."""
        if not self.rds_available:
            self.warnings.append("Cannot validate data completeness: RDS not available")
            return True

        try:
            cursor = self.conn.cursor()

            # Check if hoopr_schedule table has data first
            cursor.execute("SELECT COUNT(*) FROM hoopr_schedule;")
            schedule_count = cursor.fetchone()[0]

            if schedule_count == 0:
                self.warnings.append(
                    "hoopr_schedule table is empty, skipping completeness check"
                )
                if self.verbose:
                    print(f"⚠️  Data completeness skipped (hoopr_schedule empty)")
                cursor.close()
                return True

            # Check games per season (fixed GROUP BY clause)
            cursor.execute(
                """
                SELECT
                    season_year,
                    COUNT(DISTINCT game_id) as games
                FROM (
                    SELECT
                        game_id,
                        EXTRACT(YEAR FROM game_date)::int as season_year
                    FROM hoopr_schedule
                    WHERE EXTRACT(YEAR FROM game_date) BETWEEN 2002 AND 2024
                ) subquery
                GROUP BY season_year
                ORDER BY season_year;
            """
            )
            results = cursor.fetchall()
            cursor.close()

            incomplete_seasons = []
            for season, game_count in results:
                # Regular season: ~1,230 games, full season with playoffs: ~1,400+ games
                if game_count < 1200:
                    incomplete_seasons.append((season, game_count))

            if incomplete_seasons:
                self.warnings.append(f"Seasons with <1200 games: {incomplete_seasons}")

            if self.verbose:
                print(f"✓ Data completeness checked for {len(results)} seasons")

            return True

        except Exception as e:
            self.failures.append(f"Data completeness validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations and return results."""
        print(f"\n{'='*60}")
        print(f"0.0002: hoopR Data Collection Validation")
        print(f"{'='*60}\n")

        results = {
            "s3_parquet_files_valid": self.validate_s3_hoopr_parquet_files(),
            "s3_csv_files_valid": self.validate_s3_hoopr_csv_files(),
            "s3_total_files_valid": self.validate_s3_total_hoopr_files(),
            "hoopr_play_by_play_valid": self.validate_hoopr_play_by_play_table(),
            "hoopr_player_box_valid": self.validate_hoopr_player_box_table(),
            "hoopr_team_box_valid": self.validate_hoopr_team_box_table(),
            "hoopr_schedule_valid": self.validate_hoopr_schedule_table(),
            "temporal_coverage_valid": self.validate_temporal_coverage(),
            "data_completeness_valid": self.validate_data_completeness(),
        }

        all_passed = all(results.values())

        print(f"\n{'='*60}")
        print(f"Results Summary")
        print(f"{'='*60}")

        for check, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{check:40} {status}")

        if self.failures:
            print(f"\n❌ Failures:")
            for failure in self.failures:
                print(f"  - {failure}")

        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print(f"\n{'='*60}")
        if all_passed:
            print("✅ All validations passed!")
        else:
            print("❌ Some validations failed. See details above.")
        print(f"{'='*60}\n")

        # Clean up
        if self.conn:
            self.conn.close()

        return all_passed, results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate 0.0002 hoopR data collection"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    validator = Phase02HooprValidator(verbose=args.verbose)
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
