#!/usr/bin/env python3
"""
Validate Phase 0.7: Odds API Data Integration

Description: Validates betting odds data integration from odds-api scraper,
including database schema, reference data, data quality, and integration capability.

Note: This validator checks the nba-simulator-aws side of the integration.
The actual scraper runs in /Users/ryanranft/odds-api/ (separate project).

Usage:
    python validators/phases/phase_0/validate_0_7_odds_api.py
    python validators/phases/phase_0/validate_0_7_odds_api.py --verbose
"""

import sys
import os
import psycopg2
from typing import List, Tuple, Dict
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")


class Phase07OddsAPIValidator:
    """Validates betting odds data integration for Phase 0.7."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures: List[str] = []
        self.warnings: List[str] = []

        # Initialize RDS connection
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME", "nba_simulator"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT", 5432),
                sslmode="require",
            )
            self.rds_available = True
        except Exception as e:
            self.failures.append(f"RDS connection failed: {e}")
            self.conn = None
            self.rds_available = False

    def validate_schema_exists(self) -> bool:
        """Validate odds schema exists in RDS."""
        if not self.rds_available:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'odds'
            """
            )
            result = cursor.fetchone()

            if not result:
                self.failures.append("odds schema does not exist")
                return False

            if self.verbose:
                print("✓ odds schema exists")

            return True

        except Exception as e:
            self.failures.append(f"Schema validation failed: {e}")
            return False

    def validate_core_tables(self) -> bool:
        """Validate core tables exist in odds schema."""
        if not self.rds_available:
            return False

        expected_tables = [
            "events",
            "bookmakers",
            "market_types",
            "odds_snapshots",
            "scores",
        ]

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'odds'
                ORDER BY table_name
            """
            )
            found_tables = [row[0] for row in cursor.fetchall()]

            missing = set(expected_tables) - set(found_tables)
            if missing:
                self.failures.append(f"Missing tables: {', '.join(missing)}")
                return False

            if self.verbose:
                print(f"✓ Core tables exist: {', '.join(expected_tables)}")

            return True

        except Exception as e:
            self.failures.append(f"Table validation failed: {e}")
            return False

    def validate_reference_data(self) -> bool:
        """Validate reference data is populated (bookmakers, market types)."""
        if not self.rds_available:
            return False

        try:
            cursor = self.conn.cursor()

            # Check bookmakers
            cursor.execute("SELECT COUNT(*) FROM odds.bookmakers")
            bookmaker_count = cursor.fetchone()[0]

            if bookmaker_count < 5:
                self.failures.append(
                    f"Expected >= 5 bookmakers, found {bookmaker_count}"
                )
                return False

            # Check market types
            cursor.execute("SELECT COUNT(*) FROM odds.market_types")
            market_count = cursor.fetchone()[0]

            if market_count < 3:
                self.failures.append(
                    f"Expected >= 3 market types, found {market_count}"
                )
                return False

            if self.verbose:
                print(
                    f"✓ Reference data: {bookmaker_count} bookmakers, {market_count} market types"
                )

            return True

        except Exception as e:
            self.failures.append(f"Reference data validation failed: {e}")
            return False

    def validate_data_presence(self) -> bool:
        """Validate odds data exists (lenient check - scraper may not have run yet)."""
        if not self.rds_available:
            return False

        try:
            cursor = self.conn.cursor()

            # Check for events
            cursor.execute("SELECT COUNT(*) FROM odds.events")
            event_count = cursor.fetchone()[0]

            # Check for odds snapshots
            cursor.execute("SELECT COUNT(*) FROM odds.odds_snapshots")
            snapshot_count = cursor.fetchone()[0]

            if event_count == 0:
                self.warnings.append(
                    "No events found - odds-api scraper may not have run yet"
                )
            elif snapshot_count == 0:
                self.warnings.append(
                    "Events exist but no odds snapshots - scraper may be in progress"
                )

            if self.verbose:
                print(
                    f"✓ Data presence: {event_count:,} events, {snapshot_count:,} snapshots"
                )

            # Pass validation even if no data (scraper runs separately)
            return True

        except Exception as e:
            self.failures.append(f"Data presence check failed: {e}")
            return False

    def validate_data_freshness(self) -> bool:
        """Validate odds data is recent (if data exists)."""
        if not self.rds_available:
            return False

        try:
            cursor = self.conn.cursor()

            # Check most recent event
            cursor.execute(
                """
                SELECT MAX(commence_time) as latest_event
                FROM odds.events
            """
            )
            latest_event = cursor.fetchone()[0]

            if not latest_event:
                # No data yet - this is okay
                if self.verbose:
                    print("✓ Data freshness: No events yet (scraper will populate)")
                return True

            # Check if we have upcoming events
            cursor.execute(
                """
                SELECT COUNT(*) FROM odds.events
                WHERE commence_time > NOW()
            """
            )
            upcoming_count = cursor.fetchone()[0]

            # Check most recent odds fetch
            cursor.execute(
                """
                SELECT MAX(fetched_at) as latest_fetch
                FROM odds.odds_snapshots
            """
            )
            latest_fetch = cursor.fetchone()[0]

            if latest_fetch:
                age = datetime.now() - latest_fetch.replace(tzinfo=None)
                if age > timedelta(hours=24):
                    self.warnings.append(
                        f"Last odds fetch was {age.days} days ago - scraper may be paused"
                    )

            if self.verbose:
                print(f"✓ Data freshness: {upcoming_count} upcoming events")
                if latest_fetch:
                    print(f"  Last fetch: {latest_fetch}")

            return True

        except Exception as e:
            self.failures.append(f"Data freshness check failed: {e}")
            return False

    def validate_data_quality(self) -> bool:
        """Validate odds data quality (if data exists)."""
        if not self.rds_available:
            return False

        try:
            cursor = self.conn.cursor()

            # Check for NULL values in critical fields
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM odds.odds_snapshots
                WHERE price IS NULL OR outcome_name IS NULL
            """
            )
            null_count = cursor.fetchone()[0]

            if null_count > 0:
                self.warnings.append(
                    f"Found {null_count} odds snapshots with NULL price/outcome"
                )

            # Check for invalid price ranges (American odds typically -10000 to +10000)
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM odds.odds_snapshots
                WHERE price NOT BETWEEN -10000 AND 10000
            """
            )
            invalid_price_count = cursor.fetchone()[0]

            if invalid_price_count > 0:
                self.warnings.append(
                    f"Found {invalid_price_count} odds with invalid price ranges"
                )

            # Check that latest odds have bookmaker coverage
            cursor.execute(
                """
                SELECT e.event_id, e.home_team, e.away_team,
                       COUNT(DISTINCT os.bookmaker_id) as bookmaker_count
                FROM odds.events e
                LEFT JOIN odds.odds_snapshots os
                    ON e.event_id = os.event_id AND os.is_latest = true
                WHERE e.commence_time > NOW()
                GROUP BY e.event_id, e.home_team, e.away_team
                HAVING COUNT(DISTINCT os.bookmaker_id) < 3
            """
            )
            low_coverage = cursor.fetchall()

            if low_coverage:
                self.warnings.append(
                    f"Found {len(low_coverage)} events with < 3 bookmakers"
                )

            if self.verbose:
                print("✓ Data quality checks passed")

            return True

        except Exception as e:
            self.failures.append(f"Data quality validation failed: {e}")
            return False

    def validate_integration_capability(self) -> bool:
        """Validate ability to query odds data from nba-simulator-aws."""
        if not self.rds_available:
            return False

        try:
            cursor = self.conn.cursor()

            # Test query: Get latest odds for upcoming games
            test_query = """
            SELECT
                e.event_id,
                e.home_team,
                e.away_team,
                e.commence_time,
                b.bookmaker_title,
                mt.market_name,
                os.outcome_name,
                os.price,
                os.point
            FROM odds.events e
            LEFT JOIN odds.odds_snapshots os ON e.event_id = os.event_id
            LEFT JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
            LEFT JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
            WHERE e.commence_time > NOW()
              AND os.is_latest = true
            LIMIT 10
            """

            cursor.execute(test_query)
            results = cursor.fetchall()

            if self.verbose:
                print(
                    f"✓ Integration test: Successfully queried {len(results)} odds records"
                )

            return True

        except Exception as e:
            self.failures.append(f"Integration test failed: {e}")
            return False

    def run(self) -> Tuple[int, int]:
        """
        Run all validation checks.

        Returns:
            Tuple of (passed_count, failed_count)
        """
        print("=" * 70)
        print("PHASE 0.7: ODDS API DATA INTEGRATION VALIDATOR")
        print("=" * 70)
        print()

        checks = [
            ("Schema Existence", self.validate_schema_exists),
            ("Core Tables", self.validate_core_tables),
            ("Reference Data", self.validate_reference_data),
            ("Data Presence", self.validate_data_presence),
            ("Data Freshness", self.validate_data_freshness),
            ("Data Quality", self.validate_data_quality),
            ("Integration Capability", self.validate_integration_capability),
        ]

        passed = 0
        failed = 0

        for name, check_func in checks:
            print(f"Checking {name}...", end=" ")
            try:
                if check_func():
                    print("✓ PASS")
                    passed += 1
                else:
                    print("✗ FAIL")
                    failed += 1
            except Exception as e:
                print(f"✗ FAIL (exception: {e})")
                failed += 1

        print()
        print("=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Passed: {passed}/{len(checks)}")
        print(f"Failed: {failed}/{len(checks)}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.failures:
            print(f"\n✗ Failures ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  - {failure}")

        print()

        if failed == 0:
            print("✅ Phase 0.7 validation PASSED")
            print()
            print(
                "Note: odds-api scraper runs separately at /Users/ryanranft/odds-api/"
            )
            print(
                "Odds data will be populated as the scraper collects from The Odds API."
            )
            return passed, failed
        else:
            print("❌ Phase 0.7 validation FAILED")
            return passed, failed


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Phase 0.7: Odds API Data Integration"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    validator = Phase07OddsAPIValidator(verbose=args.verbose)
    passed, failed = validator.run()

    # Return exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
