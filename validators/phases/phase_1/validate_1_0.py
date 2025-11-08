#!/usr/bin/env python3
"""
Validate 1.0: Data Completeness Checks

Validates data completeness across the raw_data schema:
- Temporal coverage (date ranges, gaps)
- Expected game counts per season
- Missing data patterns
- Source coverage

Usage:
    python validators/phases/phase_1/validate_1_0.py
    python validators/phases/phase_1/validate_1_0.py --verbose
    python validators/phases/phase_1/validate_1_0.py --host localhost --database nba_simulator --user ryanranft --password ""
"""

import sys
import os
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Tuple, Dict
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class DataCompletenessValidator:
    """Validates data completeness across raw_data schema"""

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
            self.log("Database connection closed")

    def validate_temporal_coverage(self) -> bool:
        """Validate temporal coverage of games"""
        try:
            # Get date range
            self.cursor.execute(
                """
                SELECT
                    MIN(game_date) as min_date,
                    MAX(game_date) as max_date,
                    COUNT(DISTINCT game_date) as unique_dates,
                    COUNT(*) as total_games
                FROM raw_data.nba_games
            """
            )

            result = self.cursor.fetchone()
            min_date = result["min_date"]
            max_date = result["max_date"]
            unique_dates = result["unique_dates"]
            total_games = result["total_games"]

            self.log(f"Date range: {min_date} to {max_date}")
            self.log(f"Unique dates: {unique_dates:,}, Total games: {total_games:,}")

            # Check for large gaps (>30 days without games)
            self.cursor.execute(
                """
                WITH date_gaps AS (
                    SELECT
                        game_date,
                        LEAD(game_date) OVER (ORDER BY game_date) as next_date,
                        LEAD(game_date) OVER (ORDER BY game_date) - game_date as gap_days
                    FROM (
                        SELECT DISTINCT game_date
                        FROM raw_data.nba_games
                        ORDER BY game_date
                    ) t
                )
                SELECT
                    game_date,
                    next_date,
                    gap_days
                FROM date_gaps
                WHERE gap_days > 30
                ORDER BY gap_days DESC
                LIMIT 10
            """
            )

            gaps = self.cursor.fetchall()
            if gaps:
                self.log(f"\nFound {len(gaps)} gaps > 30 days:", "WARNING")
                for gap in gaps[:5]:
                    self.log(
                        f"  {gap['game_date']} to {gap['next_date']}: {gap['gap_days']} days",
                        "WARNING",
                    )

                # Expected gaps: Off-season (Jun-Sep), lockouts
                max_gap = max(g["gap_days"] for g in gaps)
                if max_gap > 180:
                    self.warnings.append(
                        f"Largest gap is {max_gap} days (expected for off-season/lockouts)"
                    )
            else:
                self.log("No significant date gaps found")

            return True

        except Exception as e:
            self.failures.append(f"Temporal coverage validation failed: {e}")
            return False

    def validate_season_completeness(self) -> bool:
        """Validate game counts per season"""
        try:
            # Get games per season
            self.cursor.execute(
                """
                SELECT
                    season,
                    COUNT(*) as game_count,
                    MIN(game_date) as season_start,
                    MAX(game_date) as season_end
                FROM raw_data.nba_games
                GROUP BY season
                ORDER BY season
            """
            )

            seasons = self.cursor.fetchall()

            self.log(f"\nSeason completeness check ({len(seasons)} seasons):")

            incomplete_seasons = []
            for s in seasons:
                # Expected: ~1,230 games per season (82 games × 30 teams / 2)
                # Early seasons had fewer teams
                # Extract year from season string (e.g., "2004-05" → 2004)
                season_str = str(s["season"])
                try:
                    season_year = int(season_str.split("-")[0])
                except:
                    season_year = 2000  # Default

                expected = 1230 if season_year >= 2004 else 1000
                pct = (s["game_count"] / expected) * 100

                status = "✓" if pct >= 80 else "✗"
                if self.verbose or pct < 80:
                    self.log(
                        f"  {status} {s['season']}: {s['game_count']:,} games ({pct:.0f}% of expected)"
                    )

                if pct < 80:
                    incomplete_seasons.append(
                        {"season": s["season"], "count": s["game_count"], "pct": pct}
                    )

            if incomplete_seasons:
                self.warnings.append(
                    f"{len(incomplete_seasons)} seasons have < 80% expected games"
                )
                # This may be acceptable for partial seasons, lockouts, etc.

            return True

        except Exception as e:
            self.failures.append(f"Season completeness validation failed: {e}")
            return False

    def validate_source_coverage(self) -> bool:
        """Validate source coverage"""
        try:
            # Check source distribution
            self.cursor.execute(
                """
                SELECT
                    source,
                    COUNT(*) as game_count,
                    MIN(game_date) as earliest,
                    MAX(game_date) as latest
                FROM raw_data.nba_games
                GROUP BY source
                ORDER BY source
            """
            )

            sources = self.cursor.fetchall()

            self.log(f"\nSource coverage:")
            for s in sources:
                self.log(
                    f"  {s['source']}: {s['game_count']:,} games ({s['earliest']} to {s['latest']})"
                )

            # Expect ESPN as primary source
            espn_count = next(
                (s["game_count"] for s in sources if s["source"] == "ESPN"), 0
            )
            total_count = sum(s["game_count"] for s in sources)

            if espn_count == 0:
                self.failures.append("No ESPN source data found")
                return False

            espn_pct = (espn_count / total_count) * 100
            self.log(f"ESPN coverage: {espn_pct:.1f}%")

            return True

        except Exception as e:
            self.failures.append(f"Source coverage validation failed: {e}")
            return False

    def validate_play_by_play_coverage(self) -> bool:
        """Validate play-by-play data coverage"""
        try:
            # Check PBP availability
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total_games,
                    COUNT(*) FILTER (WHERE data ? 'play_by_play') as games_with_pbp,
                    COUNT(*) FILTER (
                        WHERE data ? 'play_by_play'
                        AND (data->'play_by_play'->>'total_plays')::int > 0
                    ) as games_with_plays
                FROM raw_data.nba_games
            """
            )

            result = self.cursor.fetchone()
            total = result["total_games"]
            with_pbp = result["games_with_pbp"]
            with_plays = result["games_with_plays"]

            pbp_pct = (with_pbp / total * 100) if total > 0 else 0
            plays_pct = (with_plays / total * 100) if total > 0 else 0

            self.log(f"\nPlay-by-play coverage:")
            self.log(
                f"  Games with PBP structure: {with_pbp:,}/{total:,} ({pbp_pct:.1f}%)"
            )
            self.log(
                f"  Games with actual plays: {with_plays:,}/{total:,} ({plays_pct:.1f}%)"
            )

            if pbp_pct < 90:
                self.warnings.append(
                    f"Only {pbp_pct:.1f}% of games have play-by-play data"
                )

            return True

        except Exception as e:
            self.failures.append(f"Play-by-play coverage validation failed: {e}")
            return False

    def validate_data_recency(self) -> bool:
        """Validate data recency"""
        try:
            # Check most recent game
            self.cursor.execute(
                """
                SELECT
                    MAX(game_date) as most_recent_game,
                    MAX(updated_at) as most_recent_update
                FROM raw_data.nba_games
            """
            )

            result = self.cursor.fetchone()
            most_recent_game = result["most_recent_game"]
            most_recent_update = result["most_recent_update"]

            self.log(f"\nData recency:")
            self.log(f"  Most recent game: {most_recent_game}")
            if most_recent_update:
                self.log(f"  Most recent update: {most_recent_update}")

            # Check if data is stale (no games in last 180 days)
            if most_recent_game:
                days_since = (datetime.now().date() - most_recent_game).days
                self.log(f"  Days since last game: {days_since}")

                if days_since > 180:
                    # This is expected during off-season (Jun-Sep)
                    self.warnings.append(
                        f"Data may be stale: {days_since} days since last game (check if off-season)"
                    )

            return True

        except Exception as e:
            self.failures.append(f"Data recency validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"1.0 Data Completeness Validation")
        print(f"{'='*60}\n")

        if not self.connect_db():
            print("\n❌ Database connection failed. Aborting.")
            return False, {}

        try:
            results = {
                "temporal_coverage": self.validate_temporal_coverage(),
                "season_completeness": self.validate_season_completeness(),
                "source_coverage": self.validate_source_coverage(),
                "pbp_coverage": self.validate_play_by_play_coverage(),
                "data_recency": self.validate_data_recency(),
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
    parser = argparse.ArgumentParser(description="Validate 1.0 - Data Completeness")
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

    validator = DataCompletenessValidator(
        verbose=args.verbose, db_config=db_config if db_config else None
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
