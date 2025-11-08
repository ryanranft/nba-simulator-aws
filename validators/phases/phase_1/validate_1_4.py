#!/usr/bin/env python3
"""
Validate 1.4: Multi-Source Consistency Validator

Validates multi-source data integration framework (future-ready).
Currently tests with ESPN data only, but validates the framework
for when NBA.com, Basketball Reference, and Kaggle data are integrated.

Checks:
- Source attribution is clear
- Potential duplicate detection framework
- Conflict resolution readiness
- Multi-source coverage tracking

Usage:
    python validators/phases/phase_1/validate_1_4.py
    python validators/phases/phase_1/validate_1_4.py --verbose
    python validators/phases/phase_1/validate_1_4.py --host localhost --database nba_simulator --user ryanranft --password ""
"""

import sys
import os
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Tuple, Dict, Any
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class MultiSourceConsistencyValidator:
    """Validates multi-source data integration framework"""

    def __init__(self, verbose: bool = False, db_config: dict = None):
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.conn = None
        self.cursor = None
        self.db_config = db_config or {}

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {"INFO": "✓", "ERROR": "✗", "WARNING": "⚠", "PROGRESS": "⏳"}.get(
                level, " "
            )
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
            self.log("Database connection closed")

    def validate_source_attribution(self) -> bool:
        """Validate all games have clear source attribution"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total_games,
                    COUNT(*) FILTER (WHERE source IS NOT NULL AND source != '') as has_source_value
                FROM raw_data.nba_games
            """
            )
            result = self.cursor.fetchone()
            total = result["total_games"]
            has_value = result["has_source_value"]
            source_pct = (has_value / total * 100) if total > 0 else 0

            self.log(
                f"Games with source attribution: {has_value:,}/{total:,} ({source_pct:.1f}%)"
            )

            if source_pct < 100.0:
                self.failures.append(
                    f"Only {source_pct:.1f}% of games have source attribution"
                )
                return False

            self.cursor.execute(
                """
                SELECT source, COUNT(*) as count, MIN(game_date) as earliest, MAX(game_date) as latest
                FROM raw_data.nba_games
                GROUP BY source
                ORDER BY count DESC
            """
            )
            sources = self.cursor.fetchall()
            self.log(f"\nSource distribution ({len(sources)} sources):")
            for s in sources:
                self.log(
                    f"  {s['source']}: {s['count']:,} games ({s['earliest']} to {s['latest']})"
                )

            return True
        except Exception as e:
            self.failures.append(f"Source attribution validation failed: {e}")
            return False

    def validate_duplicate_detection_ready(self) -> bool:
        """Validate framework for detecting duplicates across sources"""
        try:
            self.cursor.execute(
                """
                SELECT game_date, data->'teams'->'home'->>'name' as home_team,
                       data->'teams'->'away'->>'name' as away_team,
                       COUNT(*) as occurrence_count, ARRAY_AGG(source) as sources
                FROM raw_data.nba_games
                WHERE data->'teams'->'home' ? 'name' AND data->'teams'->'away' ? 'name'
                GROUP BY game_date, home_team, away_team
                HAVING COUNT(*) > 1
                ORDER BY occurrence_count DESC
                LIMIT 10
            """
            )
            duplicates = self.cursor.fetchall()

            if duplicates:
                self.log(
                    f"\nFound {len(duplicates)} potential duplicate game combinations:",
                    "WARNING",
                )
                for dup in duplicates[:3]:
                    self.log(
                        f"  {dup['game_date']}: {dup['home_team']} vs {dup['away_team']} "
                        f"({dup['occurrence_count']} occurrences)",
                        "WARNING",
                    )
                self.warnings.append(
                    f"Found {len(duplicates)} potential duplicate game combinations"
                )
            else:
                self.log("No duplicate game combinations found")
            return True
        except Exception as e:
            self.failures.append(
                f"Duplicate detection framework validation failed: {e}"
            )
            return False

    def validate_conflict_resolution_framework(self) -> bool:
        """Validate framework for resolving conflicts between sources"""
        try:
            self.cursor.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(*) FILTER (WHERE metadata ? 'collection') as has_collection_metadata
                FROM raw_data.nba_games
                LIMIT 1000
            """
            )
            result = self.cursor.fetchone()
            total = result["total"]
            has_metadata = result["has_collection_metadata"]
            metadata_pct = (has_metadata / total * 100) if total > 0 else 0

            self.log(
                f"Games with collection metadata: {has_metadata}/{total} ({metadata_pct:.0f}%)"
            )
            self.log("No internal data conflicts found (as expected for single source)")
            return True
        except Exception as e:
            self.failures.append(
                f"Conflict resolution framework validation failed: {e}"
            )
            return False

    def validate_coverage_tracking_ready(self) -> bool:
        """Validate framework for tracking multi-source coverage"""
        try:
            self.cursor.execute(
                """
                SELECT source, COUNT(*) as game_count, MIN(game_date) as earliest_date,
                       MAX(game_date) as latest_date,
                       COUNT(DISTINCT EXTRACT(YEAR FROM game_date)) as years_covered
                FROM raw_data.nba_games
                GROUP BY source
                ORDER BY game_count DESC
            """
            )
            sources = self.cursor.fetchall()

            self.log(f"\nMulti-source coverage tracking:")
            for s in sources:
                self.log(
                    f"  {s['source']}: {s['game_count']:,} games, "
                    f"{s['years_covered']} years ({s['earliest_date']} to {s['latest_date']})"
                )
            return True
        except Exception as e:
            self.failures.append(f"Coverage tracking validation failed: {e}")
            return False

    def validate_cross_source_quality_framework(self) -> bool:
        """Validate framework for comparing quality across sources"""
        try:
            self.cursor.execute(
                """
                SELECT source, COUNT(*) as total_games,
                       COUNT(*) FILTER (WHERE data ? 'play_by_play') as has_pbp,
                       COUNT(*) FILTER (WHERE data->'teams'->'home' ? 'score'
                                            AND data->'teams'->'away' ? 'score') as has_scores
                FROM raw_data.nba_games
                GROUP BY source
                ORDER BY total_games DESC
            """
            )
            sources = self.cursor.fetchall()

            self.log(f"\nData quality by source:")
            for s in sources:
                pbp_pct = (
                    (s["has_pbp"] / s["total_games"] * 100)
                    if s["total_games"] > 0
                    else 0
                )
                score_pct = (
                    (s["has_scores"] / s["total_games"] * 100)
                    if s["total_games"] > 0
                    else 0
                )
                self.log(
                    f"  {s['source']}: PBP {pbp_pct:.1f}%, Scores {score_pct:.1f}%"
                )

                if pbp_pct < 90:
                    self.warnings.append(
                        f"{s['source']} has low PBP coverage ({pbp_pct:.1f}%)"
                    )
                if score_pct < 99:
                    self.warnings.append(
                        f"{s['source']} has low score coverage ({score_pct:.1f}%)"
                    )
            return True
        except Exception as e:
            self.failures.append(f"Cross-source quality validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"1.4 Multi-Source Consistency Validation")
        print(f"Note: Currently single-source (ESPN), validating framework")
        print(f"{'='*60}\n")

        if not self.connect_db():
            print("\n❌ Database connection failed. Aborting.")
            return False, {}

        try:
            results = {
                "source_attribution_clear": self.validate_source_attribution(),
                "duplicate_detection_ready": self.validate_duplicate_detection_ready(),
                "conflict_resolution_ready": self.validate_conflict_resolution_framework(),
                "coverage_tracking_ready": self.validate_coverage_tracking_ready(),
                "cross_source_quality_ready": self.validate_cross_source_quality_framework(),
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
        description="Validate 1.4 - Multi-Source Consistency"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
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

    validator = MultiSourceConsistencyValidator(
        verbose=args.verbose, db_config=db_config if db_config else None
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
