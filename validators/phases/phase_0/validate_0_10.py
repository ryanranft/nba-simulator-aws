#!/usr/bin/env python3
"""
Validate Phase 0.10: PostgreSQL JSONB Storage

Comprehensive validator for JSONB storage implementation.

Usage:
    python validators/phases/phase_0/validate_0_10.py
    python validators/phases/phase_0/validate_0_10.py --verbose
    python validators/phases/phase_0/validate_0_10.py --check-only
"""

import sys
import os
import argparse
import psycopg2
from typing import List, Tuple, Dict
from pathlib import Path


class Phase010Validator:
    """Validates Phase 0.10 PostgreSQL JSONB Storage implementation"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.conn = None
        self.cursor = None

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose is enabled"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = "✓" if level == "INFO" else "✗" if level == "ERROR" else "⚠"
            print(f"{prefix} {message}")

    def connect_db(self) -> bool:
        """Establish database connection"""
        try:
            config = {
                "host": os.getenv("RDS_HOST", os.getenv("POSTGRES_HOST", "localhost")),
                "port": int(os.getenv("RDS_PORT", os.getenv("POSTGRES_PORT", "5432"))),
                "database": os.getenv(
                    "RDS_DATABASE", os.getenv("POSTGRES_DB", "nba_data")
                ),
                "user": os.getenv("RDS_USER", os.getenv("POSTGRES_USER", "postgres")),
                "password": os.getenv(
                    "RDS_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")
                ),
            }

            if not config["password"]:
                self.failures.append("Database password not found in environment")
                return False

            self.conn = psycopg2.connect(
                host=config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"],
                connect_timeout=10,
            )
            self.cursor = self.conn.cursor()
            self.log(f"Connected to database at {config['host']}")
            return True

        except Exception as e:
            self.failures.append(f"Database connection failed: {e}")
            return False

    def disconnect_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

    # ========================================================================
    # Schema Validation
    # ========================================================================

    def validate_schema_exists(self) -> bool:
        """Validate raw_data schema exists"""
        try:
            self.cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'raw_data';
            """
            )

            exists = self.cursor.fetchone() is not None

            if exists:
                self.log("Schema 'raw_data' exists")
                return True
            else:
                self.failures.append("Schema 'raw_data' does not exist")
                return False

        except Exception as e:
            self.failures.append(f"Schema validation failed: {e}")
            return False

    def validate_tables_exist(self) -> bool:
        """Validate all required tables exist"""
        expected_tables = [
            "nba_games",
            "nba_players",
            "nba_teams",
            "nba_misc",
            "schema_version",
        ]
        all_exist = True

        try:
            for table in expected_tables:
                self.cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'raw_data'
                      AND table_name = %s;
                """,
                    (table,),
                )

                exists = self.cursor.fetchone() is not None

                if exists:
                    self.log(f"Table '{table}' exists")
                else:
                    self.failures.append(f"Table '{table}' does not exist")
                    all_exist = False

            return all_exist

        except Exception as e:
            self.failures.append(f"Table validation failed: {e}")
            return False

    def validate_table_columns(self) -> bool:
        """Validate table columns are correct"""
        expected_columns = {
            "nba_games": [
                "id",
                "game_id",
                "source",
                "season",
                "game_date",
                "collected_at",
                "updated_at",
                "data",
                "metadata",
            ],
            "nba_players": [
                "id",
                "player_id",
                "player_name",
                "source",
                "season",
                "collected_at",
                "updated_at",
                "data",
                "metadata",
            ],
            "nba_teams": [
                "id",
                "team_id",
                "team_name",
                "source",
                "season",
                "collected_at",
                "updated_at",
                "data",
                "metadata",
            ],
        }

        all_valid = True

        try:
            for table, columns in expected_columns.items():
                self.cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'raw_data'
                      AND table_name = %s
                    ORDER BY ordinal_position;
                """,
                    (table,),
                )

                actual_columns = [row[0] for row in self.cursor.fetchall()]

                for col in columns:
                    if col in actual_columns:
                        self.log(f"Column '{table}.{col}' exists")
                    else:
                        self.failures.append(f"Column '{table}.{col}' missing")
                        all_valid = False

            return all_valid

        except Exception as e:
            self.failures.append(f"Column validation failed: {e}")
            return False

    # ========================================================================
    # Index Validation
    # ========================================================================

    def validate_indexes_exist(self) -> bool:
        """Validate indexes exist"""
        all_valid = True

        try:
            # Check GIN indexes
            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'raw_data'
                  AND indexdef LIKE '%USING gin%';
            """
            )

            gin_count = self.cursor.fetchone()[0]

            if gin_count >= 8:
                self.log(f"Found {gin_count} GIN indexes (≥8 required)")
            else:
                self.failures.append(f"Only {gin_count} GIN indexes found, expected ≥8")
                all_valid = False

            # Check B-tree indexes
            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'raw_data'
                  AND indexdef LIKE '%USING btree%';
            """
            )

            btree_count = self.cursor.fetchone()[0]
            self.log(f"Found {btree_count} B-tree indexes")

            # Check specific indexes
            required_indexes = [
                "idx_games_data_gin",
                "idx_players_data_gin",
                "idx_teams_data_gin",
                "idx_games_source",
                "idx_games_season",
            ]

            for index in required_indexes:
                self.cursor.execute(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'raw_data'
                      AND indexname = %s;
                """,
                    (index,),
                )

                exists = self.cursor.fetchone() is not None

                if exists:
                    self.log(f"Index '{index}' exists")
                else:
                    self.failures.append(f"Index '{index}' missing")
                    all_valid = False

            return all_valid

        except Exception as e:
            self.failures.append(f"Index validation failed: {e}")
            return False

    # ========================================================================
    # View Validation
    # ========================================================================

    def validate_views_exist(self) -> bool:
        """Validate materialized views exist"""
        expected_views = ["games_summary", "players_summary"]
        all_exist = True

        try:
            for view in expected_views:
                self.cursor.execute(
                    """
                    SELECT matviewname
                    FROM pg_matviews
                    WHERE schemaname = 'raw_data'
                      AND matviewname = %s;
                """,
                    (view,),
                )

                exists = self.cursor.fetchone() is not None

                if exists:
                    self.log(f"Materialized view '{view}' exists")
                else:
                    self.failures.append(f"Materialized view '{view}' missing")
                    all_exist = False

            # Check regular views
            helper_views = ["data_source_stats", "season_coverage"]

            for view in helper_views:
                self.cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.views
                    WHERE table_schema = 'raw_data'
                      AND table_name = %s;
                """,
                    (view,),
                )

                exists = self.cursor.fetchone() is not None

                if exists:
                    self.log(f"View '{view}' exists")
                else:
                    self.warnings.append(f"Helper view '{view}' missing")

            return all_exist

        except Exception as e:
            self.failures.append(f"View validation failed: {e}")
            return False

    # ========================================================================
    # Trigger Validation
    # ========================================================================

    def validate_triggers_exist(self) -> bool:
        """Validate triggers exist"""
        expected_triggers = [
            "update_games_updated_at",
            "update_players_updated_at",
            "update_teams_updated_at",
            "update_misc_updated_at",
        ]

        all_exist = True

        try:
            for trigger in expected_triggers:
                self.cursor.execute(
                    """
                    SELECT trigger_name
                    FROM information_schema.triggers
                    WHERE trigger_schema = 'raw_data'
                      AND trigger_name = %s;
                """,
                    (trigger,),
                )

                exists = self.cursor.fetchone() is not None

                if exists:
                    self.log(f"Trigger '{trigger}' exists")
                else:
                    self.failures.append(f"Trigger '{trigger}' missing")
                    all_exist = False

            return all_exist

        except Exception as e:
            self.failures.append(f"Trigger validation failed: {e}")
            return False

    # ========================================================================
    # File Validation
    # ========================================================================

    def validate_implementation_files(self) -> bool:
        """Validate implementation files exist"""
        base_path = Path(__file__).parent.parent.parent.parent

        required_files = [
            "scripts/db/migrations/0_10_schema.sql",
            "scripts/db/0_10_init.py",
            "scripts/data/0_10_s3_handler.py",
            "scripts/0_10/main.py",
            "tests/phases/phase_0/test_0_10.py",
            "validators/phases/phase_0/validate_0_10.py",
        ]

        all_exist = True

        for file_path in required_files:
            full_path = base_path / file_path

            if full_path.exists():
                size = full_path.stat().st_size
                self.log(f"File exists: {file_path} ({size} bytes)")
            else:
                self.failures.append(f"Missing file: {file_path}")
                all_exist = False

        return all_exist

    # ========================================================================
    # Data Validation
    # ========================================================================

    def validate_schema_version(self) -> bool:
        """Validate schema version table"""
        try:
            self.cursor.execute(
                """
                SELECT version, applied_at, description
                FROM raw_data.schema_version
                ORDER BY applied_at DESC
                LIMIT 1;
            """
            )

            result = self.cursor.fetchone()

            if result:
                version, applied_at, description = result
                self.log(f"Schema version: {version} (applied {applied_at})")
                return True
            else:
                self.failures.append("No schema version found")
                return False

        except Exception as e:
            self.failures.append(f"Schema version validation failed: {e}")
            return False

    def validate_data_exists(self) -> bool:
        """Check if any data has been migrated (optional)"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM raw_data.nba_games;")
            games_count = self.cursor.fetchone()[0]

            if games_count > 0:
                self.log(f"Found {games_count} games in database")
            else:
                self.warnings.append("No games found in database (migration pending)")

            return True

        except Exception as e:
            self.warnings.append(f"Data check failed: {e}")
            return True  # Not a critical failure

    # ========================================================================
    # Main Validation
    # ========================================================================

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*70}")
        print(f"Phase 0.10 Validation: PostgreSQL JSONB Storage")
        print(f"{'='*70}\n")

        # Connect to database
        if not self.connect_db():
            print(f"\n❌ Cannot connect to database. Validation failed.\n")
            return False, {}

        try:
            # Run all validations
            results = {
                "implementation_files": self.validate_implementation_files(),
                "schema_exists": self.validate_schema_exists(),
                "tables_exist": self.validate_tables_exist(),
                "columns_valid": self.validate_table_columns(),
                "indexes_exist": self.validate_indexes_exist(),
                "views_exist": self.validate_views_exist(),
                "triggers_exist": self.validate_triggers_exist(),
                "schema_version": self.validate_schema_version(),
                "data_check": self.validate_data_exists(),
            }

            all_passed = all(results.values())

            # Print results
            print(f"\n{'='*70}")
            print(f"Validation Results")
            print(f"{'='*70}")

            for check, passed in results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                check_name = check.replace("_", " ").title()
                print(f"{check_name:40} {status}")

            if self.failures:
                print(f"\n❌ Failures ({len(self.failures)}):")
                for failure in self.failures:
                    print(f"  - {failure}")

            if self.warnings:
                print(f"\n⚠ Warnings ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"  - {warning}")

            print(f"\n{'='*70}")
            if all_passed:
                print("✅ All validations passed!")
            else:
                print("❌ Some validations failed.")
            print(f"{'='*70}\n")

            return all_passed, results

        finally:
            self.disconnect_db()


def main():
    parser = argparse.ArgumentParser(description="Validate Phase 0.10 implementation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--check-only", "-c", action="store_true", help="Only check database connection"
    )

    args = parser.parse_args()

    validator = Phase010Validator(verbose=args.verbose)

    if args.check_only:
        print("\nChecking database connection...")
        if validator.connect_db():
            print("✅ Database connection successful!\n")
            validator.disconnect_db()
            sys.exit(0)
        else:
            print("❌ Database connection failed.\n")
            sys.exit(1)

    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
