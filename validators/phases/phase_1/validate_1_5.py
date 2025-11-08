#!/usr/bin/env python3
"""
Validate 1.5: Statistical Framework Validation

Validates that statistical analysis can be performed on raw_data schema.
Tests basic statistical computations, aggregations, and data access patterns
needed for ML feature engineering.

Usage:
    python validators/phases/phase_1/validate_1_5.py
    python validators/phases/phase_1/validate_1_5.py --verbose
    python validators/phases/phase_1/validate_1_5.py --host localhost --database nba_simulator --user ryanranft --password ""
"""

import sys
import os
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Tuple, Dict, Any
from pathlib import Path
from collections import defaultdict
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class StatisticalFrameworkValidator:
    """Validates statistical analysis framework on raw_data schema"""

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

    def validate_basic_aggregations(self) -> bool:
        """Validate basic statistical aggregations work"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total_games,
                    AVG((data->'teams'->'home'->>'score')::int) as avg_home_score,
                    STDDEV((data->'teams'->'home'->>'score')::int) as std_home_score,
                    MIN((data->'teams'->'home'->>'score')::int) as min_home_score,
                    MAX((data->'teams'->'home'->>'score')::int) as max_home_score
                FROM raw_data.nba_games
                WHERE data->'teams'->'home' ? 'score'
            """
            )

            result = self.cursor.fetchone()
            avg_score = result["avg_home_score"]
            std_score = result["std_home_score"]

            self.log(
                f"Basic aggregations working: AVG={avg_score:.1f}, STD={std_score:.1f}"
            )

            # Sanity checks on results
            if not (80 <= avg_score <= 130):
                self.warnings.append(
                    f"Average score ({avg_score:.1f}) outside expected range"
                )
            if not (10 <= std_score <= 30):
                self.warnings.append(
                    f"Score std dev ({std_score:.1f}) outside expected range"
                )

            return True
        except Exception as e:
            self.failures.append(f"Basic aggregation validation failed: {e}")
            return False

    def validate_groupby_operations(self) -> bool:
        """Validate GROUP BY operations work correctly"""
        try:
            self.cursor.execute(
                """
                SELECT
                    EXTRACT(YEAR FROM game_date) as year,
                    COUNT(*) as game_count,
                    AVG((data->'teams'->'home'->>'score')::int +
                        (data->'teams'->'away'->>'score')::int) as avg_total_score
                FROM raw_data.nba_games
                WHERE data->'teams'->'home' ? 'score'
                  AND data->'teams'->'away' ? 'score'
                GROUP BY year
                ORDER BY year DESC
                LIMIT 10
            """
            )

            years = self.cursor.fetchall()

            if not years:
                self.failures.append("GROUP BY operation returned no results")
                return False

            self.log(f"GROUP BY working: {len(years)} years with data")

            # Check for reasonable results
            for year_data in years[:3]:
                year = year_data["year"]
                count = year_data["game_count"]
                avg = year_data["avg_total_score"]

                if self.verbose:
                    self.log(
                        f"  {int(year)}: {count:,} games, avg total score {avg:.1f}"
                    )

                if count < 100:
                    self.warnings.append(f"Year {int(year)} has only {count} games")

            return True
        except Exception as e:
            self.failures.append(f"GROUP BY validation failed: {e}")
            return False

    def validate_window_functions(self) -> bool:
        """Validate window functions work correctly"""
        try:
            self.cursor.execute(
                """
                SELECT
                    game_id,
                    game_date,
                    (data->'teams'->'home'->>'score')::int as score,
                    AVG((data->'teams'->'home'->>'score')::int)
                        OVER (ORDER BY game_date ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) as rolling_avg
                FROM raw_data.nba_games
                WHERE data->'teams'->'home' ? 'score'
                ORDER BY game_date DESC
                LIMIT 100
            """
            )

            results = self.cursor.fetchall()

            if not results:
                self.failures.append("Window function query returned no results")
                return False

            # Check rolling average makes sense
            rolling_avgs = [
                r["rolling_avg"] for r in results if r["rolling_avg"] is not None
            ]
            if rolling_avgs:
                avg_of_rolling = statistics.mean(rolling_avgs)
                self.log(
                    f"Window functions working: rolling avg = {avg_of_rolling:.1f}"
                )

                if not (80 <= avg_of_rolling <= 130):
                    self.warnings.append(
                        f"Rolling average ({avg_of_rolling:.1f}) outside expected range"
                    )
            else:
                self.warnings.append("No rolling averages calculated")

            return True
        except Exception as e:
            self.failures.append(f"Window function validation failed: {e}")
            return False

    def validate_jsonb_aggregations(self) -> bool:
        """Validate JSONB-specific aggregations work"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE (data->'play_by_play'->>'total_plays')::int > 400) as high_play_count,
                    AVG((data->'play_by_play'->>'total_plays')::int) as avg_plays
                FROM raw_data.nba_games
                WHERE data ? 'play_by_play'
            """
            )

            result = self.cursor.fetchone()
            avg_plays = result["avg_plays"]

            self.log(f"JSONB aggregations working: avg_plays = {avg_plays:.0f}")

            if not (350 <= avg_plays <= 550):
                self.warnings.append(
                    f"Average play count ({avg_plays:.0f}) outside expected range"
                )

            return True
        except Exception as e:
            self.failures.append(f"JSONB aggregation validation failed: {e}")
            return False

    def validate_join_operations(self) -> bool:
        """Validate self-joins work (for team matchup analysis)"""
        try:
            # Self-join to find games between same teams
            self.cursor.execute(
                """
                SELECT
                    g1.game_id as game1_id,
                    g2.game_id as game2_id,
                    g1.game_date as date1,
                    g2.game_date as date2
                FROM raw_data.nba_games g1
                JOIN raw_data.nba_games g2
                  ON g1.data->'teams'->'home'->>'name' = g2.data->'teams'->'home'->>'name'
                  AND g1.data->'teams'->'away'->>'name' = g2.data->'teams'->'away'->>'name'
                  AND g1.game_id < g2.game_id
                WHERE g1.data->'teams'->'home' ? 'name'
                  AND g2.data->'teams'->'away' ? 'name'
                LIMIT 10
            """
            )

            joins = self.cursor.fetchall()

            if joins:
                self.log(
                    f"JOIN operations working: found {len(joins)} matchup examples"
                )
            else:
                self.log("JOIN operations work but found no repeat matchups in sample")

            return True
        except Exception as e:
            self.failures.append(f"JOIN operation validation failed: {e}")
            return False

    def validate_subqueries(self) -> bool:
        """Validate subqueries work correctly"""
        try:
            self.cursor.execute(
                """
                SELECT
                    season,
                    game_count,
                    avg_score
                FROM (
                    SELECT
                        season,
                        COUNT(*) as game_count,
                        AVG((data->'teams'->'home'->>'score')::int) as avg_score
                    FROM raw_data.nba_games
                    WHERE data->'teams'->'home' ? 'score'
                    GROUP BY season
                ) subq
                WHERE game_count > 100
                ORDER BY season DESC
                LIMIT 5
            """
            )

            results = self.cursor.fetchall()

            if not results:
                self.failures.append("Subquery returned no results")
                return False

            self.log(f"Subqueries working: {len(results)} seasons with >100 games")

            return True
        except Exception as e:
            self.failures.append(f"Subquery validation failed: {e}")
            return False

    def validate_temporal_queries(self) -> bool:
        """Validate temporal/date-based queries work"""
        try:
            self.cursor.execute(
                """
                SELECT
                    DATE_TRUNC('month', game_date) as month,
                    COUNT(*) as game_count
                FROM raw_data.nba_games
                WHERE game_date >= '2023-01-01'
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """
            )

            months = self.cursor.fetchall()

            if not months:
                self.failures.append("Temporal query returned no results")
                return False

            self.log(f"Temporal queries working: {len(months)} months of data")

            return True
        except Exception as e:
            self.failures.append(f"Temporal query validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"1.5 Statistical Framework Validation")
        print(f"{'='*60}\n")

        if not self.connect_db():
            print("\n❌ Database connection failed. Aborting.")
            return False, {}

        try:
            results = {
                "basic_aggregations_work": self.validate_basic_aggregations(),
                "groupby_operations_work": self.validate_groupby_operations(),
                "window_functions_work": self.validate_window_functions(),
                "jsonb_aggregations_work": self.validate_jsonb_aggregations(),
                "join_operations_work": self.validate_join_operations(),
                "subqueries_work": self.validate_subqueries(),
                "temporal_queries_work": self.validate_temporal_queries(),
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
    parser = argparse.ArgumentParser(description="Validate 1.5 - Statistical Framework")
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

    validator = StatisticalFrameworkValidator(
        verbose=args.verbose, db_config=db_config if db_config else None
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
