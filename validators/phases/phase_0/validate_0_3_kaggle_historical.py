#!/usr/bin/env python3
"""
0.0003 Validator: Kaggle Historical Database

Validates 0.0003 (Kaggle Historical Database) completeness and quality.

Validation Checks:
- Database file exists and is accessible
- Database file size (~280 MB expected)
- SQLite format and version
- All 17 tables exist with expected schemas
- Row counts match documented values
- Temporal coverage (2004-2020, 17 seasons)
- Data quality and completeness

Usage:
    python validators/phases/phase_0/validate_0_3_kaggle_historical.py
    python validators/phases/phase_0/validate_0_3_kaggle_historical.py --verbose

Exit Codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))


class KaggleDatabaseValidator:
    """Validator for 0.0003: Kaggle Historical Database"""

    # Expected row counts (ACTUAL database as of Oct 2025)
    # Note: Database expanded significantly from original 2004-2020 (26K games)
    # to comprehensive 1946-2023 coverage (66K games, 13.5M play-by-play rows)
    EXPECTED_ROW_COUNTS = {
        "game": 65698,  # 1946-2023 (expanded from 26,496)
        "team": 30,
        "player": 4800,  # Approximate
        "play_by_play": 13500000,  # ~13.5M rows (was empty in old database)
        "game_info": 58000,  # Approximate
        "game_summary": 58000,  # Approximate
        "line_score": 58000,  # Approximate
        "inactive_players": 110000,  # Approximate
        "officials": 71000,  # Approximate
        "other_stats": 28000,  # Approximate
        "draft_history": 8200,  # Approximate
        "draft_combine_stats": 1600,  # Approximate
        "common_player_info": 3600,  # Approximate
        "team_details": 27,
        "team_history": 50,
        "team_info_common": 0,  # Known to be empty
    }

    # Tolerance for approximate counts (20%)
    TOLERANCE = 0.2

    def __init__(self, verbose: bool = False):
        """
        Initialize validator

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.db_path = project_root / "data" / "kaggle" / "nba.sqlite"
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors: List[str] = []

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

    def validate_database_file(self) -> bool:
        """
        Validate database file exists and is accessible

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking database file existence...")

        if not self.db_path.exists():
            self.errors.append(f"Database file not found: {self.db_path}")
            self.log(f"✗ Database file not found: {self.db_path}", "ERROR")
            return False

        # Check file size (database expanded from 280 MB to 2.2 GB)
        file_size_mb = self.db_path.stat().st_size / (1024 * 1024)
        expected_size_mb = 2240  # Updated from 280 MB
        tolerance_mb = 500  # 500 MB tolerance

        if abs(file_size_mb - expected_size_mb) > tolerance_mb:
            self.warnings += 1
            self.log(
                f"⚠ Database file size: {file_size_mb:.1f} MB "
                f"(expected ~{expected_size_mb} MB ± {tolerance_mb} MB)",
                "WARNING",
            )
        else:
            self.log(
                f"✓ Database file size: {file_size_mb:.1f} MB "
                f"(within expected range)",
                "INFO",
            )

        self.log(f"✓ Database file exists: {self.db_path}", "INFO")
        return True

    def validate_database_connection(self) -> Tuple[bool, sqlite3.Connection]:
        """
        Validate database connection and format

        Returns:
            Tuple of (validation passed, connection)
        """
        self.log("Checking database connection...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check SQLite version
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            self.log(f"✓ SQLite version: {version}", "INFO")

            return True, conn

        except sqlite3.Error as e:
            self.errors.append(f"Database connection failed: {e}")
            self.log(f"✗ Database connection failed: {e}", "ERROR")
            return False, None

    def validate_table_existence(self, conn: sqlite3.Connection) -> bool:
        """
        Validate all expected tables exist

        Args:
            conn: Database connection

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking table existence...")

        cursor = conn.cursor()

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"  # nosec B608
        )
        existing_tables = set(row[0] for row in cursor.fetchall())

        expected_tables = set(self.EXPECTED_ROW_COUNTS.keys())
        missing_tables = expected_tables - existing_tables

        if missing_tables:
            self.errors.append(f"Missing tables: {', '.join(sorted(missing_tables))}")
            self.log(f"✗ Missing tables: {', '.join(sorted(missing_tables))}", "ERROR")
            return False

        self.log(f"✓ All {len(expected_tables)} expected tables exist", "INFO")
        return True

    def validate_row_counts(self, conn: sqlite3.Connection) -> bool:
        """
        Validate row counts for all tables

        Args:
            conn: Database connection

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking row counts...")

        cursor = conn.cursor()
        all_passed = True

        for table, expected_count in sorted(self.EXPECTED_ROW_COUNTS.items()):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")  # nosec B608
                actual_count = cursor.fetchone()[0]

                # Handle exact counts vs. approximate counts
                if table in ["game", "team", "team_details", "team_history"]:
                    # Exact count expected
                    if actual_count != expected_count:
                        self.errors.append(
                            f"Table '{table}': Expected {expected_count} rows, "
                            f"got {actual_count}"
                        )
                        self.log(
                            f"✗ Table '{table}': Expected {expected_count} rows, "
                            f"got {actual_count}",
                            "ERROR",
                        )
                        all_passed = False
                    else:
                        self.log(
                            f"✓ Table '{table}': {actual_count:,} rows (exact match)",
                            "INFO",
                        )
                else:
                    # Approximate count with tolerance
                    tolerance = self.TOLERANCE
                    lower_bound = int(expected_count * (1 - tolerance))
                    upper_bound = int(expected_count * (1 + tolerance))

                    if expected_count == 0:
                        # Empty tables - exact match required
                        if actual_count != 0:
                            # Warning only for empty tables (might have been populated)
                            self.warnings += 1
                            self.log(
                                f"⚠ Table '{table}': Expected 0 rows (known empty), "
                                f"got {actual_count}",
                                "WARNING",
                            )
                        else:
                            self.log(
                                f"✓ Table '{table}': {actual_count} rows (empty as expected)",
                                "INFO",
                            )
                    elif lower_bound <= actual_count <= upper_bound:
                        self.log(
                            f"✓ Table '{table}': {actual_count:,} rows "
                            f"(within {tolerance*100:.0f}% of {expected_count:,})",
                            "INFO",
                        )
                    else:
                        self.errors.append(
                            f"Table '{table}': Expected ~{expected_count:,} rows "
                            f"(±{tolerance*100:.0f}%), got {actual_count:,}"
                        )
                        self.log(
                            f"✗ Table '{table}': Expected ~{expected_count:,} rows "
                            f"(±{tolerance*100:.0f}%), got {actual_count:,}",
                            "ERROR",
                        )
                        all_passed = False

            except sqlite3.Error as e:
                self.errors.append(f"Error querying table '{table}': {e}")
                self.log(f"✗ Error querying table '{table}': {e}", "ERROR")
                all_passed = False

        return all_passed

    def validate_temporal_coverage(self, conn: sqlite3.Connection) -> bool:
        """
        Validate temporal coverage (1946-2023, expanded from 2004-2020)

        Args:
            conn: Database connection

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking temporal coverage...")

        cursor = conn.cursor()

        try:
            # Get season range from season_id (format: "12023" for 2023)
            cursor.execute(
                """
                SELECT
                    MIN(substr(season_id, 2, 4)) as min_season,
                    MAX(substr(season_id, 2, 4)) as max_season,
                    COUNT(DISTINCT substr(season_id, 2, 4)) as num_seasons
                FROM game
                WHERE season_id IS NOT NULL
                """  # nosec B608
            )
            min_season, max_season, num_seasons = cursor.fetchone()

            # Database expanded from 2004-2020 (17 seasons) to 1946-2023 (77 seasons)
            expected_min = "1946"
            expected_max = "2022"  # 2022-23 season
            expected_min_seasons = 70  # At least 70 seasons

            all_passed = True

            if min_season != expected_min:
                self.errors.append(
                    f"Min season: Expected {expected_min}, got {min_season}"
                )
                self.log(
                    f"✗ Min season: Expected {expected_min}, got {min_season}", "ERROR"
                )
                all_passed = False
            else:
                self.log(f"✓ Min season: {min_season}", "INFO")

            if max_season != expected_max:
                self.errors.append(
                    f"Max season: Expected {expected_max}, got {max_season}"
                )
                self.log(
                    f"✗ Max season: Expected {expected_max}, got {max_season}", "ERROR"
                )
                all_passed = False
            else:
                self.log(f"✓ Max season: {max_season}", "INFO")

            if num_seasons < expected_min_seasons:
                self.errors.append(
                    f"Number of seasons: Expected ≥{expected_min_seasons}, "
                    f"got {num_seasons}"
                )
                self.log(
                    f"✗ Number of seasons: Expected ≥{expected_min_seasons}, "
                    f"got {num_seasons}",
                    "ERROR",
                )
                all_passed = False
            else:
                self.log(f"✓ Number of seasons: {num_seasons} (1946-2023)", "INFO")

            return all_passed

        except sqlite3.Error as e:
            self.errors.append(f"Error checking temporal coverage: {e}")
            self.log(f"✗ Error checking temporal coverage: {e}", "ERROR")
            return False

    def validate_data_completeness(self, conn: sqlite3.Connection) -> bool:
        """
        Validate data completeness

        Args:
            conn: Database connection

        Returns:
            True if validation passed, False otherwise
        """
        self.log("Checking data completeness...")

        cursor = conn.cursor()
        all_passed = True

        try:
            # Check for games with scores (using updated schema: pts_home/pts_away)
            cursor.execute(
                "SELECT COUNT(*) FROM game WHERE pts_home IS NOT NULL "  # nosec B608
                "AND pts_away IS NOT NULL"
            )
            games_with_scores = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM game")  # nosec B608
            total_games = cursor.fetchone()[0]

            completeness_pct = (
                games_with_scores / total_games * 100 if total_games > 0 else 0
            )

            if completeness_pct < 95:
                self.warnings += 1
                self.log(
                    f"⚠ Games with scores: {games_with_scores}/{total_games} "
                    f"({completeness_pct:.1f}%)",
                    "WARNING",
                )
            else:
                self.log(
                    f"✓ Games with scores: {games_with_scores}/{total_games} "
                    f"({completeness_pct:.1f}%)",
                    "INFO",
                )

            # Check play_by_play data completeness
            cursor.execute("SELECT COUNT(*) FROM play_by_play")  # nosec B608
            pbp_count = cursor.fetchone()[0]

            # Expect millions of play-by-play rows
            expected_min_pbp = 10000000  # At least 10M rows

            if pbp_count < expected_min_pbp:
                self.warnings += 1
                self.log(
                    f"⚠ Play-by-play rows: {pbp_count:,} (expected ≥{expected_min_pbp:,})",
                    "WARNING",
                )
            else:
                self.log(
                    f"✓ Play-by-play rows: {pbp_count:,} (comprehensive coverage)",
                    "INFO",
                )

            return all_passed

        except sqlite3.Error as e:
            self.errors.append(f"Error checking data completeness: {e}")
            self.log(f"✗ Error checking data completeness: {e}", "ERROR")
            return False

    def run_all_validations(self) -> bool:
        """
        Run all 0.0003 validations

        Returns:
            True if all validations passed, False otherwise
        """
        print("\n=== 0.0003 Validator: Kaggle Historical Database ===\n")

        conn = None
        try:
            # 1. Database file validation
            if self.validate_database_file():
                self.passed += 1
            else:
                self.failed += 1
                return False  # Can't continue without database file

            # 2. Database connection validation
            result, conn = self.validate_database_connection()
            if result:
                self.passed += 1
            else:
                self.failed += 1
                return False  # Can't continue without connection

            # 3. Table existence validation
            if self.validate_table_existence(conn):
                self.passed += 1
            else:
                self.failed += 1

            # 4. Row counts validation
            if self.validate_row_counts(conn):
                self.passed += 1
            else:
                self.failed += 1

            # 5. Temporal coverage validation
            if self.validate_temporal_coverage(conn):
                self.passed += 1
            else:
                self.failed += 1

            # 6. Data completeness validation
            if self.validate_data_completeness(conn):
                self.passed += 1
            else:
                self.failed += 1

        finally:
            if conn:
                conn.close()

        # Print summary
        print("\n=== Validation Summary ===\n")
        print(f"Passed:   {self.passed}/6")
        print(f"Failed:   {self.failed}/6")
        print(f"Warnings: {self.warnings}")

        if self.errors:
            print("\n=== Errors ===\n")
            for error in self.errors:
                print(f"  • {error}")

        success = self.failed == 0
        if success:
            print("\n✓ All 0.0003 validations passed!\n")
        else:
            print("\n✗ 0.0003 validation failed. See errors above.\n")

        return success


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate 0.0003: Kaggle Historical Database"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    validator = KaggleDatabaseValidator(verbose=args.verbose)
    success = validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
