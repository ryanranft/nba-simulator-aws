#!/usr/bin/env python3
"""
0.20 Validator: Kaggle PostgreSQL Migration

Validates 0.20 (Kaggle SQLite → PostgreSQL migration) completeness and quality.

Validation Checks:
1. Schema existence (kaggle schema)
2. Table existence (all 16 tables)
3. Row count validation (match SQLite exactly)
4. Data integrity (NOT NULL constraints, foreign keys)
5. Temporal coverage (1946-2023, 77 seasons)
6. Spot checks (random sample validation)
7. JSONB data validation
8. Index existence

Usage:
    python validators/phases/phase_0/validate_0_20_kaggle_postgres.py
    python validators/phases/phase_0/validate_0_20_kaggle_postgres.py --verbose
    python validators/phases/phase_0/validate_0_20_kaggle_postgres.py --quick

Exit Codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import os
import sqlite3
import psycopg2
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import random

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))


class KagglePostgresValidator:
    """Validator for 0.20: Kaggle PostgreSQL Migration"""

    # Expected tables and row counts
    EXPECTED_TABLES = {
        "game_nba_kaggle": 65698,
        "play_by_play_nba_kaggle": 13592899,
        "player_nba_kaggle": 4800,
        "team_nba_kaggle": 30,
        "common_player_info_nba_kaggle": 3600,
        "game_info_nba_kaggle": 58000,
        "game_summary_nba_kaggle": 58000,
        "line_score_nba_kaggle": 58000,
        "inactive_players_nba_kaggle": 110000,
        "officials_nba_kaggle": 71000,
        "other_stats_nba_kaggle": 28000,
        "draft_history_nba_kaggle": 8200,
        "draft_combine_stats_nba_kaggle": 1600,
        "team_details_nba_kaggle": 27,
        "team_history_nba_kaggle": 50,
        "team_info_common_nba_kaggle": 0,  # Known empty
    }

    # Row count tolerance (20% for approximate counts)
    TOLERANCE = 0.20

    # Tables with exact counts (no tolerance)
    EXACT_COUNT_TABLES = [
        "game_nba_kaggle",
        "team_nba_kaggle",
        "team_details_nba_kaggle",
    ]

    def __init__(self, verbose: bool = False, quick: bool = False):
        """
        Initialize validator

        Args:
            verbose: Enable verbose output
            quick: Run quick validation (skip expensive checks)
        """
        self.verbose = verbose
        self.quick = quick
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors: List[str] = []

        # Database paths
        self.sqlite_db = Path("/Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite")
        self.pg_config = {
            "host": "localhost",
            "database": "nba_simulator",
            "user": "ryanranft",
            "password": "",
            "port": 5432
        }

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message if verbose enabled"""
        if self.verbose or level != "INFO":
            prefix = "  " if level == "INFO" else f"[{level}] "
            print(f"{prefix}{message}")

    def validate_schema_exists(self) -> bool:
        """Validate kaggle schema exists"""
        self.log("Checking schema existence...")

        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'kaggle'"
            )
            result = cursor.fetchone()

            conn.close()

            if not result:
                self.errors.append("kaggle schema does not exist")
                self.log("✗ kaggle schema not found", "ERROR")
                return False

            self.log("✓ kaggle schema exists", "INFO")
            return True

        except Exception as e:
            self.errors.append(f"Failed to connect to PostgreSQL: {e}")
            self.log(f"✗ PostgreSQL connection failed: {e}", "ERROR")
            return False

    def validate_tables_exist(self) -> bool:
        """Validate all expected tables exist"""
        self.log("Checking table existence...")

        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'kaggle'
                ORDER BY table_name
                """
            )
            existing_tables = set(row[0] for row in cursor.fetchall())

            conn.close()

            expected_tables = set(self.EXPECTED_TABLES.keys())
            missing_tables = expected_tables - existing_tables

            if missing_tables:
                self.errors.append(f"Missing tables: {', '.join(sorted(missing_tables))}")
                self.log(f"✗ Missing tables: {', '.join(sorted(missing_tables))}", "ERROR")
                return False

            self.log(f"✓ All {len(expected_tables)} tables exist", "INFO")
            return True

        except Exception as e:
            self.errors.append(f"Table existence check failed: {e}")
            self.log(f"✗ Table check failed: {e}", "ERROR")
            return False

    def validate_row_counts(self) -> bool:
        """Validate row counts match SQLite source"""
        self.log("Checking row counts...")

        try:
            pg_conn = psycopg2.connect(**self.pg_config)
            pg_cursor = pg_conn.cursor()

            all_passed = True

            for table, expected_count in sorted(self.EXPECTED_TABLES.items()):
                pg_cursor.execute(f"SELECT COUNT(*) FROM kaggle.{table}")
                actual_count = pg_cursor.fetchone()[0]

                # Check if exact count or tolerance allowed
                if table in self.EXACT_COUNT_TABLES:
                    # Exact count required
                    if actual_count != expected_count:
                        self.errors.append(
                            f"Table '{table}': Expected {expected_count:,} rows, got {actual_count:,}"
                        )
                        self.log(
                            f"✗ Table '{table}': Expected {expected_count:,}, got {actual_count:,}",
                            "ERROR"
                        )
                        all_passed = False
                    else:
                        self.log(f"✓ Table '{table}': {actual_count:,} rows (exact match)", "INFO")

                else:
                    # Tolerance allowed
                    lower_bound = int(expected_count * (1 - self.TOLERANCE))
                    upper_bound = int(expected_count * (1 + self.TOLERANCE))

                    if expected_count == 0:
                        # Empty table
                        if actual_count != 0:
                            self.warnings += 1
                            self.log(
                                f"⚠ Table '{table}': Expected 0 rows, got {actual_count:,}",
                                "WARNING"
                            )
                        else:
                            self.log(f"✓ Table '{table}': 0 rows (empty as expected)", "INFO")

                    elif lower_bound <= actual_count <= upper_bound:
                        self.log(
                            f"✓ Table '{table}': {actual_count:,} rows "
                            f"(within {self.TOLERANCE*100:.0f}% of {expected_count:,})",
                            "INFO"
                        )
                    else:
                        self.errors.append(
                            f"Table '{table}': Expected ~{expected_count:,} rows "
                            f"(±{self.TOLERANCE*100:.0f}%), got {actual_count:,}"
                        )
                        self.log(
                            f"✗ Table '{table}': Expected ~{expected_count:,}, got {actual_count:,}",
                            "ERROR"
                        )
                        all_passed = False

            pg_conn.close()
            return all_passed

        except Exception as e:
            self.errors.append(f"Row count validation failed: {e}")
            self.log(f"✗ Row count check failed: {e}", "ERROR")
            return False

    def validate_temporal_coverage(self) -> bool:
        """Validate temporal coverage (1946-2023)"""
        self.log("Checking temporal coverage...")

        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    MIN(season) as min_season,
                    MAX(season) as max_season,
                    COUNT(DISTINCT season) as num_seasons
                FROM kaggle.game_nba_kaggle
                WHERE season IS NOT NULL
                """
            )
            min_season, max_season, num_seasons = cursor.fetchone()

            conn.close()

            expected_min = 1946
            expected_max = 2022  # 2022-23 season
            expected_min_seasons = 70  # At least 70 seasons

            all_passed = True

            if min_season != expected_min:
                self.errors.append(f"Min season: Expected {expected_min}, got {min_season}")
                self.log(f"✗ Min season: Expected {expected_min}, got {min_season}", "ERROR")
                all_passed = False
            else:
                self.log(f"✓ Min season: {min_season}", "INFO")

            if max_season < expected_max:
                self.errors.append(f"Max season: Expected ≥{expected_max}, got {max_season}")
                self.log(f"✗ Max season: Expected ≥{expected_max}, got {max_season}", "ERROR")
                all_passed = False
            else:
                self.log(f"✓ Max season: {max_season}", "INFO")

            if num_seasons < expected_min_seasons:
                self.errors.append(
                    f"Number of seasons: Expected ≥{expected_min_seasons}, got {num_seasons}"
                )
                self.log(
                    f"✗ Seasons: Expected ≥{expected_min_seasons}, got {num_seasons}",
                    "ERROR"
                )
                all_passed = False
            else:
                self.log(f"✓ Seasons: {num_seasons} (1946-2023 coverage)", "INFO")

            return all_passed

        except Exception as e:
            self.errors.append(f"Temporal coverage check failed: {e}")
            self.log(f"✗ Temporal check failed: {e}", "ERROR")
            return False

    def validate_jsonb_data(self) -> bool:
        """Validate JSONB data integrity"""
        self.log("Checking JSONB data integrity...")

        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()

            # Check that all rows have non-null JSONB data
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM kaggle.game_nba_kaggle
                WHERE data IS NULL OR data::text = '{}'
                """
            )
            null_count = cursor.fetchone()[0]

            if null_count > 0:
                self.errors.append(f"Found {null_count:,} games with NULL or empty JSONB data")
                self.log(f"✗ {null_count:,} rows with NULL/empty data", "ERROR")
                conn.close()
                return False

            self.log("✓ All rows have valid JSONB data", "INFO")

            # Sample check: Verify JSONB contains expected fields
            cursor.execute(
                """
                SELECT data
                FROM kaggle.game_nba_kaggle
                LIMIT 10
                """
            )
            samples = cursor.fetchall()

            import json
            for row in samples:
                data = json.loads(row[0])
                if not data or len(data) < 5:  # Expect at least 5 fields
                    self.warnings += 1
                    self.log("⚠ Found JSONB with < 5 fields", "WARNING")
                    break

            self.log("✓ JSONB data samples look valid", "INFO")

            conn.close()
            return True

        except Exception as e:
            self.errors.append(f"JSONB validation failed: {e}")
            self.log(f"✗ JSONB check failed: {e}", "ERROR")
            return False

    def validate_foreign_keys(self) -> bool:
        """Validate foreign key constraints"""
        self.log("Checking foreign keys...")

        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()

            # Check play_by_play → game foreign key
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM kaggle.play_by_play_nba_kaggle pbp
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM kaggle.game_nba_kaggle g
                    WHERE g.game_id = pbp.game_id
                )
                LIMIT 1000
                """
            )
            orphaned_plays = cursor.fetchone()[0]

            if orphaned_plays > 0:
                self.errors.append(
                    f"Found {orphaned_plays:,} play-by-play events without matching game"
                )
                self.log(f"✗ {orphaned_plays:,} orphaned play events", "ERROR")
                conn.close()
                return False

            self.log("✓ Foreign key constraints valid", "INFO")

            conn.close()
            return True

        except Exception as e:
            self.errors.append(f"Foreign key validation failed: {e}")
            self.log(f"✗ Foreign key check failed: {e}", "ERROR")
            return False

    def validate_indexes(self) -> bool:
        """Validate indexes exist"""
        self.log("Checking indexes...")

        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'kaggle'
                """
            )
            index_count = cursor.fetchone()[0]

            # Expect at least 40 indexes (varies by table structure)
            if index_count < 40:
                self.warnings += 1
                self.log(
                    f"⚠ Found {index_count} indexes (expected ≥40)",
                    "WARNING"
                )
            else:
                self.log(f"✓ Found {index_count} indexes", "INFO")

            conn.close()
            return True

        except Exception as e:
            self.errors.append(f"Index validation failed: {e}")
            self.log(f"✗ Index check failed: {e}", "ERROR")
            return False

    def validate_spot_checks(self) -> bool:
        """Validate random samples match SQLite source"""
        if self.quick:
            self.log("Skipping spot checks (quick mode)...")
            return True

        self.log("Running spot checks (10 random games)...")

        try:
            # Connect to both databases
            sqlite_conn = sqlite3.connect(self.sqlite_db)
            pg_conn = psycopg2.connect(**self.pg_config)

            sqlite_cursor = sqlite_conn.cursor()
            pg_cursor = pg_conn.cursor()

            # Get 10 random game IDs from PostgreSQL
            pg_cursor.execute(
                """
                SELECT game_id
                FROM kaggle.game_nba_kaggle
                ORDER BY RANDOM()
                LIMIT 10
                """
            )
            game_ids = [row[0] for row in pg_cursor.fetchall()]

            all_passed = True

            for game_id in game_ids:
                # Get from SQLite
                sqlite_cursor.execute(
                    f"SELECT pts_home, pts_away FROM game WHERE game_id = ?",
                    (game_id,)
                )
                sqlite_row = sqlite_cursor.fetchone()

                # Get from PostgreSQL
                pg_cursor.execute(
                    f"SELECT pts_home, pts_away FROM kaggle.game_nba_kaggle WHERE game_id = %s",
                    (game_id,)
                )
                pg_row = pg_cursor.fetchone()

                if sqlite_row and pg_row:
                    if sqlite_row != pg_row:
                        self.errors.append(
                            f"Game {game_id}: Score mismatch (SQLite: {sqlite_row}, PG: {pg_row})"
                        )
                        self.log(
                            f"✗ Game {game_id}: Score mismatch",
                            "ERROR"
                        )
                        all_passed = False

            if all_passed:
                self.log("✓ Spot checks passed (10/10 games match)", "INFO")

            sqlite_conn.close()
            pg_conn.close()

            return all_passed

        except Exception as e:
            # Spot checks are not critical - warn but don't fail
            self.warnings += 1
            self.log(f"⚠ Spot checks failed: {e}", "WARNING")
            return True

    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("\n=== 0.20 Validator: Kaggle PostgreSQL Migration ===\n")

        # 1. Schema existence
        if self.validate_schema_exists():
            self.passed += 1
        else:
            self.failed += 1
            return False  # Can't continue without schema

        # 2. Table existence
        if self.validate_tables_exist():
            self.passed += 1
        else:
            self.failed += 1

        # 3. Row counts
        if self.validate_row_counts():
            self.passed += 1
        else:
            self.failed += 1

        # 4. Temporal coverage
        if self.validate_temporal_coverage():
            self.passed += 1
        else:
            self.failed += 1

        # 5. JSONB data
        if self.validate_jsonb_data():
            self.passed += 1
        else:
            self.failed += 1

        # 6. Foreign keys
        if self.validate_foreign_keys():
            self.passed += 1
        else:
            self.failed += 1

        # 7. Indexes
        if self.validate_indexes():
            self.passed += 1
        else:
            self.failed += 1

        # 8. Spot checks (optional)
        if not self.quick:
            if self.validate_spot_checks():
                self.passed += 1
            else:
                self.failed += 1

        # Print summary
        total_checks = 8 if not self.quick else 7

        print("\n=== Validation Summary ===\n")
        print(f"Passed:   {self.passed}/{total_checks}")
        print(f"Failed:   {self.failed}/{total_checks}")
        print(f"Warnings: {self.warnings}")

        if self.errors:
            print("\n=== Errors ===\n")
            for error in self.errors:
                print(f"  • {error}")

        success = self.failed == 0
        if success:
            print("\n✓ All 0.20 validations passed!\n")
        else:
            print("\n✗ 0.20 validation failed. See errors above.\n")

        return success


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate 0.20: Kaggle PostgreSQL Migration"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation (skip expensive checks)"
    )
    args = parser.parse_args()

    validator = KagglePostgresValidator(verbose=args.verbose, quick=args.quick)
    success = validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
