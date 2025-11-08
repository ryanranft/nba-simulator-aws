#!/usr/bin/env python3
"""
Migration Validation Script

Validates that data migrated correctly from master to raw_data schema.

Usage:
    python scripts/migration/validate_migration.py
    python scripts/migration/validate_migration.py --verbose
    python scripts/migration/validate_migration.py --host localhost --database nba_simulator --user ryanranft --password ""
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba_simulator.config import config


class MigrationValidator:
    """Validate master → raw_data migration"""

    def __init__(self, verbose: bool = False, db_config: dict = None):
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.conn = None
        self.cursor = None

        # Load database config
        if db_config:
            self.db_config = db_config
        else:
            self.db_config = config.load_database_config()

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if self.verbose or level in ["ERROR", "WARNING", "SUCCESS"]:
            prefix = {
                "INFO": "ℹ️ ",
                "SUCCESS": "✅",
                "ERROR": "❌",
                "WARNING": "⚠️ ",
            }.get(level, "  ")
            print(f"{prefix} {message}")

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        self.log("Connected to database")
        if self.verbose:
            self.log(
                f"Database: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )

    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def validate_row_counts(self) -> bool:
        """Validate row counts match"""
        self.log("\n=== Row Count Validation ===")

        all_valid = True

        # Games
        self.cursor.execute("SELECT COUNT(*) FROM master.nba_games")
        master_games = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM raw_data.nba_games")
        raw_data_games = self.cursor.fetchone()[0]

        if master_games == raw_data_games:
            self.log(
                f"✓ Games: {master_games:,} (master) = {raw_data_games:,} (raw_data)",
                "SUCCESS",
            )
        else:
            self.log(
                f"✗ Games mismatch: {master_games:,} (master) vs {raw_data_games:,} (raw_data)",
                "ERROR",
            )
            self.failures.append(
                f"Game count mismatch: {master_games} vs {raw_data_games}"
            )
            all_valid = False

        # File validations
        self.cursor.execute("SELECT COUNT(*) FROM master.espn_file_validation")
        master_validations = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT COUNT(*) FROM raw_data.nba_misc
            WHERE entity_type = 'file_validation'
        """
        )
        raw_data_validations = self.cursor.fetchone()[0]

        if master_validations == raw_data_validations:
            self.log(
                f"✓ Validations: {master_validations:,} (master) = {raw_data_validations:,} (raw_data)",
                "SUCCESS",
            )
        else:
            self.log(
                f"✗ Validations mismatch: {master_validations:,} (master) vs {raw_data_validations:,} (raw_data)",
                "ERROR",
            )
            self.failures.append(
                f"Validation count mismatch: {master_validations} vs {raw_data_validations}"
            )
            all_valid = False

        return all_valid

    def validate_data_quality(self) -> bool:
        """Validate data quality in raw_data"""
        self.log("\n=== Data Quality Validation ===")

        all_valid = True

        # Check for NULL data
        self.cursor.execute(
            "SELECT COUNT(*) FROM raw_data.nba_games WHERE data IS NULL"
        )
        null_data = self.cursor.fetchone()[0]

        if null_data == 0:
            self.log("✓ No NULL data columns", "SUCCESS")
        else:
            self.log(f"✗ Found {null_data} games with NULL data", "ERROR")
            self.failures.append(f"{null_data} games have NULL data")
            all_valid = False

        # Check for NULL metadata
        self.cursor.execute(
            "SELECT COUNT(*) FROM raw_data.nba_games WHERE metadata IS NULL"
        )
        null_metadata = self.cursor.fetchone()[0]

        if null_metadata == 0:
            self.log("✓ No NULL metadata columns", "SUCCESS")
        else:
            self.log(f"✗ Found {null_metadata} games with NULL metadata", "ERROR")
            self.failures.append(f"{null_metadata} games have NULL metadata")
            all_valid = False

        # Check required JSONB fields
        self.cursor.execute(
            """
            SELECT COUNT(*) FROM raw_data.nba_games
            WHERE NOT (data ? 'game_info' AND data ? 'teams')
        """
        )
        missing_fields = self.cursor.fetchone()[0]

        if missing_fields == 0:
            self.log("✓ All games have required JSONB fields", "SUCCESS")
        else:
            self.log(
                f"✗ Found {missing_fields} games missing required JSONB fields", "ERROR"
            )
            self.failures.append(f"{missing_fields} games missing required fields")
            all_valid = False

        return all_valid

    def validate_play_counts(self) -> bool:
        """Validate play counts match"""
        self.log("\n=== Play Count Validation ===")

        # Get sample of 100 games
        self.cursor.execute(
            """
            SELECT
                g.game_id,
                COUNT(p.id) as master_play_count,
                COALESCE((g.data->'play_by_play'->>'total_plays')::int, 0) as raw_data_play_count
            FROM raw_data.nba_games g
            LEFT JOIN master.nba_plays p ON g.game_id = p.game_id
            GROUP BY g.game_id, g.data
            LIMIT 100
        """
        )

        mismatches = 0
        for row in self.cursor.fetchall():
            game_id, master_count, raw_data_count = row
            if master_count != raw_data_count:
                mismatches += 1
                if self.verbose:
                    self.log(
                        f"Game {game_id}: {master_count} (master) vs {raw_data_count} (raw_data)",
                        "WARNING",
                    )

        if mismatches == 0:
            self.log("✓ All sampled games have matching play counts", "SUCCESS")
            return True
        else:
            self.log(
                f"⚠  Found {mismatches}/100 games with play count mismatches", "WARNING"
            )
            self.warnings.append(
                f"{mismatches}/100 sampled games have play count mismatches"
            )
            return False

    def spot_check_data(self, sample_size: int = 10) -> bool:
        """Spot check random games"""
        self.log(f"\n=== Spot Check ({sample_size} random games) ===")

        self.cursor.execute(
            f"""  # nosec B608
            SELECT
                m.game_id,
                m.home_team as master_home,
                r.data->'teams'->'home'->>'name' as raw_data_home,
                m.final_score_home as master_score,
                (r.data->'teams'->'home'->>'score')::int as raw_data_score
            FROM master.nba_games m
            JOIN raw_data.nba_games r ON m.game_id = r.game_id
            ORDER BY RANDOM()
            LIMIT {sample_size}
        """
        )

        mismatches = 0
        for row in self.cursor.fetchall():
            game_id, master_home, raw_data_home, master_score, raw_data_score = row

            if master_home != raw_data_home:
                self.log(f"Game {game_id}: Home team mismatch", "ERROR")
                mismatches += 1
            elif master_score != raw_data_score:
                self.log(f"Game {game_id}: Score mismatch", "ERROR")
                mismatches += 1
            else:
                if self.verbose:
                    self.log(f"✓ Game {game_id}: Data matches")

        if mismatches == 0:
            self.log(f"✓ All {sample_size} sampled games match", "SUCCESS")
            return True
        else:
            self.log(
                f"✗ Found {mismatches}/{sample_size} games with data mismatches",
                "ERROR",
            )
            self.failures.append(
                f"{mismatches}/{sample_size} spot-checked games have mismatches"
            )
            return False

    def run_validation(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*70}")
        print("Migration Validation Report")
        print(f"{'='*70}")

        try:
            self.connect()

            results = {
                "row_counts": self.validate_row_counts(),
                "data_quality": self.validate_data_quality(),
                "play_counts": self.validate_play_counts(),
                "spot_check": self.spot_check_data(),
            }

            all_passed = all(results.values())

            # Print summary
            print(f"\n{'='*70}")
            print("Validation Summary")
            print(f"{'='*70}\n")

            for check, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                check_name = check.replace("_", " ").title()
                print(f"{check_name:30} {status}")

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
                print("✅ All validations passed!")
            else:
                print("❌ Some validations failed.")
            print(f"{'='*70}\n")

            return all_passed, results

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Validate migration from master to raw_data"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--host", help="Database host (overrides config)")
    parser.add_argument("--port", type=int, help="Database port (overrides config)")
    parser.add_argument("--database", help="Database name (overrides config)")
    parser.add_argument("--user", help="Database user (overrides config)")
    parser.add_argument("--password", help="Database password (overrides config)")

    args = parser.parse_args()

    # Build database config from CLI args or environment
    db_config = None
    if any([args.host, args.port, args.database, args.user, args.password]):
        db_config = {
            "host": args.host or os.getenv("POSTGRES_HOST", "localhost"),
            "port": args.port or int(os.getenv("POSTGRES_PORT", "5432")),
            "database": args.database or os.getenv("POSTGRES_DB", "nba_simulator"),
            "user": args.user or os.getenv("POSTGRES_USER", "ryanranft"),
            "password": (
                args.password
                if args.password is not None
                else os.getenv("POSTGRES_PASSWORD", "")
            ),
        }

    validator = MigrationValidator(verbose=args.verbose, db_config=db_config)
    all_passed, results = validator.run_validation()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
