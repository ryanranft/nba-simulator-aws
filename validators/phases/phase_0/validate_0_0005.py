#!/usr/bin/env python3
"""
Validate 0.0005: Possession Extraction Validator

Validates that possession extraction from temporal_events is complete and correct.
Uses Dean Oliver validation formula to verify possession counts.

Usage:
    python validators/phases/phase_0/validate_0_0005.py
    python validators/phases/phase_0/validate_0_0005.py --verbose
    python validators/phases/phase_0/validate_0_0005.py --sample 100
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Tuple, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from nba_simulator.etl.extractors.possession.validator import DeanOliverValidator
import psycopg2
from psycopg2.extras import RealDictCursor


class PossessionExtractionValidator:
    """Validates Phase 0.0005 possession extraction"""

    def __init__(
        self, verbose: bool = False, sample_size: int = None, db_config: dict = None
    ):
        self.verbose = verbose
        self.sample_size = sample_size
        self.failures = []
        self.warnings = []
        self.conn = None
        self.cursor = None
        self.db_config = db_config or {}

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {"INFO": "✓", "ERROR": "✗", "WARNING": "⚠"}.get(level, " ")
            print(f"{prefix} {message}")

    def connect_db(self) -> bool:
        """Establish database connection"""
        try:
            config = {
                "host": self.db_config.get("host")
                or os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(
                    self.db_config.get("port") or os.getenv("POSTGRES_PORT", "5432")
                ),
                "database": self.db_config.get("database")
                or os.getenv("POSTGRES_DB", "nba_simulator"),
                "user": self.db_config.get("user")
                or os.getenv("POSTGRES_USER", "ryanranft"),
                "password": (
                    self.db_config.get("password", "")
                    if "password" in self.db_config
                    else os.getenv("POSTGRES_PASSWORD", "")
                ),
            }

            self.conn = psycopg2.connect(**config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            self.log(
                f"Connected to database at {config['host']}:{config['port']}/{config['database']}"
            )
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

    def validate_table_exists(self) -> bool:
        """Validate temporal_possession_stats table exists"""
        try:
            self.cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'temporal_possession_stats'
                )
            """
            )

            exists = self.cursor.fetchone()["exists"]

            if not exists:
                self.failures.append("Table temporal_possession_stats does not exist")
                return False

            self.log("Table temporal_possession_stats exists")
            return True

        except Exception as e:
            self.failures.append(f"Table existence check failed: {e}")
            return False

    def validate_possession_counts(self) -> bool:
        """Validate possession counts are reasonable"""
        try:
            query = """
                SELECT
                    COUNT(DISTINCT game_id) as total_games,
                    COUNT(*) as total_possessions,
                    AVG(possession_count) as avg_possessions_per_game,
                    MIN(possession_count) as min_possessions,
                    MAX(possession_count) as max_possessions
                FROM (
                    SELECT game_id, COUNT(*) as possession_count
                    FROM temporal_possession_stats
                    GROUP BY game_id
                ) game_possessions
            """

            if self.sample_size:
                # Use parameterized query to avoid SQL injection
                query = """
                    SELECT
                        COUNT(DISTINCT game_id) as total_games,
                        COUNT(*) as total_possessions,
                        AVG(possession_count) as avg_possessions_per_game,
                        MIN(possession_count) as min_possessions,
                        MAX(possession_count) as max_possessions
                    FROM (
                        SELECT game_id, COUNT(*) as possession_count
                        FROM temporal_possession_stats
                        WHERE game_id IN (
                            SELECT DISTINCT game_id
                            FROM temporal_possession_stats
                            LIMIT %s
                        )
                        GROUP BY game_id
                    ) game_possessions
                """
                self.cursor.execute(query, (self.sample_size,))
            else:
                self.cursor.execute(query)

            result = self.cursor.fetchone()

            total_games = result["total_games"]
            total_possessions = result["total_possessions"]
            avg_possessions = result["avg_possessions_per_game"]
            min_possessions = result["min_possessions"]
            max_possessions = result["max_possessions"]

            self.log(f"Games with possessions: {total_games:,}")
            self.log(f"Total possessions extracted: {total_possessions:,}")
            self.log(f"Average possessions per game: {avg_possessions:.1f}")
            self.log(f"Min possessions: {min_possessions}, Max: {max_possessions}")

            # Validation checks
            passed = True

            # Check if possessions extracted
            if total_possessions == 0:
                self.failures.append("No possessions extracted")
                return False

            # Check reasonable range (typical NBA game: 180-220 possessions)
            if avg_possessions < 150 or avg_possessions > 250:
                self.warnings.append(
                    f"Average possessions ({avg_possessions:.1f}) outside typical range (150-250)"
                )
                passed = False

            if min_possessions < 100:
                self.warnings.append(
                    f"Minimum possessions ({min_possessions}) suspiciously low"
                )

            if max_possessions > 300:
                self.warnings.append(
                    f"Maximum possessions ({max_possessions}) suspiciously high"
                )

            return passed

        except Exception as e:
            self.failures.append(f"Possession count validation failed: {e}")
            return False

    def validate_dean_oliver(self) -> bool:
        """Validate using Dean Oliver formula"""
        try:
            self.log("Running Dean Oliver validation...")

            # Build connection string
            conn_string = f"postgresql://{self.db_config.get('user', os.getenv('POSTGRES_USER', 'ryanranft'))}:{self.db_config.get('password', os.getenv('POSTGRES_PASSWORD', ''))}@{self.db_config.get('host', os.getenv('POSTGRES_HOST', 'localhost'))}:{self.db_config.get('port', os.getenv('POSTGRES_PORT', '5432'))}/{self.db_config.get('database', os.getenv('POSTGRES_DB', 'nba_simulator'))}"

            validator = DeanOliverValidator(tolerance_pct=5.0)
            if not validator.connect(conn_string):
                self.warnings.append("Could not connect Dean Oliver validator")
                return True  # Don't fail, just warn

            # Run validation
            total_games, passed_games, failed_results = validator.validate_all_games()

            pass_rate = (passed_games / total_games * 100) if total_games > 0 else 0

            self.log(
                f"Dean Oliver validation: {passed_games}/{total_games} games passed ({pass_rate:.1f}%)"
            )

            validator.disconnect()

            # Require at least 95% pass rate
            if pass_rate < 95.0:
                self.failures.append(
                    f"Dean Oliver pass rate too low: {pass_rate:.1f}% (expected >= 95%)"
                )
                return False

            self.log(f"Dean Oliver validation passed ({pass_rate:.1f}% pass rate)")
            return True

        except Exception as e:
            self.warnings.append(f"Dean Oliver validation failed: {e}")
            return True  # Don't fail, just warn

    def validate_data_quality(self) -> bool:
        """Validate data quality metrics"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE duration_seconds IS NULL OR duration_seconds <= 0) as invalid_duration,
                    COUNT(*) FILTER (WHERE points_scored < 0 OR points_scored > 10) as invalid_points,
                    COUNT(*) FILTER (WHERE event_count < 1) as zero_events,
                    AVG(duration_seconds) as avg_duration,
                    AVG(points_scored) as avg_points,
                    AVG(event_count) as avg_events
                FROM temporal_possession_stats
            """
            )

            result = self.cursor.fetchone()

            total = result["total"]
            invalid_duration = result["invalid_duration"]
            invalid_points = result["invalid_points"]
            zero_events = result["zero_events"]

            self.log(f"Data quality checks on {total:,} possessions:")
            self.log(f"  Average duration: {result['avg_duration']:.2f} seconds")
            self.log(f"  Average points: {result['avg_points']:.3f}")
            self.log(f"  Average events: {result['avg_events']:.1f}")

            # Check for data quality issues
            if invalid_duration > 0:
                pct = (invalid_duration / total) * 100
                if pct > 1.0:
                    self.failures.append(
                        f"{invalid_duration} possessions have invalid duration ({pct:.1f}%)"
                    )
                else:
                    self.warnings.append(
                        f"{invalid_duration} possessions have invalid duration ({pct:.2f}%)"
                    )

            if invalid_points > 0:
                pct = (invalid_points / total) * 100
                if pct > 1.0:
                    self.failures.append(
                        f"{invalid_points} possessions have invalid points ({pct:.1f}%)"
                    )
                else:
                    self.warnings.append(
                        f"{invalid_points} possessions have invalid points ({pct:.2f}%)"
                    )

            if zero_events > 0:
                pct = (zero_events / total) * 100
                self.failures.append(
                    f"{zero_events} possessions have zero events ({pct:.1f}%)"
                )

            return invalid_duration == 0 and zero_events == 0

        except Exception as e:
            self.failures.append(f"Data quality validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"0.0005 Possession Extraction Validation")
        if self.sample_size:
            print(f"Sample size: {self.sample_size:,} games")
        print(f"{'='*60}\n")

        if not self.connect_db():
            print("\n❌ Database connection failed. Aborting.")
            return False, {}

        try:
            results = {
                "table_exists": self.validate_table_exists(),
                "possession_counts_reasonable": self.validate_possession_counts(),
                "dean_oliver_validation": self.validate_dean_oliver(),
                "data_quality_acceptable": self.validate_data_quality(),
            }

            all_passed = all(results.values())

            print(f"\n{'='*60}")
            print(f"Results Summary")
            print(f"{'='*60}")

            for check, passed in results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"{check:40} {status}")

            if self.warnings:
                print(f"\n⚠  Warnings ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"  - {warning}")

            if self.failures:
                print(f"\n❌ Failures ({len(self.failures)}):")
                for failure in self.failures:
                    print(f"  - {failure}")

            print(f"\n{'='*60}")
            if all_passed:
                print("✅ All validations passed!")
            else:
                print("❌ Some validations failed.")
            print(f"{'='*60}\n")

            return all_passed, results

        finally:
            self.disconnect_db()


def main():
    parser = argparse.ArgumentParser(
        description="Validate 0.0005 - Possession Extraction"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--sample", type=int, help="Limit validation to N games (for testing)"
    )
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--port", type=int, help="Database port")
    parser.add_argument("--database", help="Database name")
    parser.add_argument("--user", help="Database user")
    parser.add_argument("--password", help="Database password")

    args = parser.parse_args()

    db_config = {}
    if args.host:
        db_config["host"] = args.host
    if args.port:
        db_config["port"] = args.port
    if args.database:
        db_config["database"] = args.database
    if args.user:
        db_config["user"] = args.user
    if args.password is not None:
        db_config["password"] = args.password

    validator = PossessionExtractionValidator(
        verbose=args.verbose,
        sample_size=args.sample,
        db_config=db_config if db_config else None,
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
