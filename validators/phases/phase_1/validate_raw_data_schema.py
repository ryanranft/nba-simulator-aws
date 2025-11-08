#!/usr/bin/env python3
"""
Validate Raw Data Schema Completeness

Validates the raw_data schema JSONB structure and data quality.
Checks that all migrated games have required fields and proper structure.

Usage:
    python validators/phases/phase_1/validate_raw_data_schema.py
    python validators/phases/phase_1/validate_raw_data_schema.py --verbose
    python validators/phases/phase_1/validate_raw_data_schema.py --sample 100
    python validators/phases/phase_1/validate_raw_data_schema.py --host localhost --database nba_simulator --user ryanranft --password ""
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

from nba_simulator.utils.raw_data_helpers import (
    validate_required_fields,
    check_data_completeness,
    get_play_summary,
    check_jsonb_path_exists,
    extract_all_jsonb_keys,
)


class RawDataSchemaValidator:
    """Validates raw_data schema JSONB structure and data quality"""

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
        """Log message if verbose or if it's a warning/error"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {"INFO": "✓", "ERROR": "✗", "WARNING": "⚠", "PROGRESS": "⏳"}.get(
                level, " "
            )
            print(f"{prefix} {message}")

    # ========================================================================
    # Database Connection
    # ========================================================================

    def connect_db(self) -> bool:
        """Establish database connection"""
        try:
            # Build config from CLI args or environment
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

    # ========================================================================
    # Schema Structure Validation
    # ========================================================================

    def validate_schema_exists(self) -> bool:
        """Validate raw_data schema exists"""
        try:
            self.cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'raw_data'
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
        """Validate required tables exist"""
        expected_tables = ["nba_games", "nba_misc"]
        all_exist = True

        try:
            for table in expected_tables:
                self.cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'raw_data'
                      AND table_name = %s
                """,
                    (table,),
                )

                exists = self.cursor.fetchone() is not None

                if exists:
                    self.log(f"Table 'raw_data.{table}' exists")
                else:
                    self.failures.append(f"Table 'raw_data.{table}' does not exist")
                    all_exist = False

            return all_exist

        except Exception as e:
            self.failures.append(f"Table validation failed: {e}")
            return False

    def validate_row_counts(self) -> bool:
        """Validate tables have data"""
        try:
            # Check nba_games
            self.cursor.execute("SELECT COUNT(*) as count FROM raw_data.nba_games")
            game_count = self.cursor.fetchone()["count"]

            if game_count > 0:
                self.log(f"raw_data.nba_games has {game_count:,} rows")
            else:
                self.failures.append("raw_data.nba_games has no data")
                return False

            # Check nba_misc
            self.cursor.execute("SELECT COUNT(*) as count FROM raw_data.nba_misc")
            misc_count = self.cursor.fetchone()["count"]

            if misc_count > 0:
                self.log(f"raw_data.nba_misc has {misc_count:,} rows")
            else:
                self.warnings.append(
                    "raw_data.nba_misc has no data (may be acceptable)"
                )

            return True

        except Exception as e:
            self.failures.append(f"Row count validation failed: {e}")
            return False

    # ========================================================================
    # JSONB Structure Validation
    # ========================================================================

    def validate_jsonb_structure(self) -> bool:
        """Validate JSONB structure in sample of games"""
        try:
            # Build query
            query = "SELECT * FROM raw_data.nba_games ORDER BY game_id"
            if self.sample_size:
                query += f" LIMIT {self.sample_size}"

            self.cursor.execute(query)
            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.failures.append("No games found to validate")
                return False

            self.log(f"Validating JSONB structure for {len(games):,} games")

            # Track statistics
            total_games = len(games)
            valid_games = 0
            games_with_issues = []
            missing_fields_count = defaultdict(int)

            for game in games:
                # Validate required fields
                is_valid, missing = validate_required_fields(game)

                if is_valid:
                    valid_games += 1
                else:
                    games_with_issues.append(
                        {"game_id": game["game_id"], "missing": missing}
                    )
                    for field in missing:
                        missing_fields_count[field] += 1

            # Calculate percentages
            valid_pct = (valid_games / total_games) * 100
            self.log(f"Valid games: {valid_games:,}/{total_games:,} ({valid_pct:.1f}%)")

            # Report issues
            if games_with_issues:
                self.warnings.append(
                    f"{len(games_with_issues)} games have missing required fields"
                )

                # Show top 5 most common missing fields
                if missing_fields_count:
                    self.log("\nTop missing fields:", "WARNING")
                    for field, count in sorted(
                        missing_fields_count.items(), key=lambda x: x[1], reverse=True
                    )[:5]:
                        pct = (count / total_games) * 100
                        self.log(f"  {field}: {count:,} games ({pct:.1f}%)", "WARNING")

                # Show first 3 problematic games
                if self.verbose and len(games_with_issues) > 0:
                    self.log("\nSample games with issues:", "WARNING")
                    for issue in games_with_issues[:3]:
                        self.log(
                            f"  Game {issue['game_id']}: {', '.join(issue['missing'])}",
                            "WARNING",
                        )

            # Pass if > 95% valid
            if valid_pct >= 95.0:
                return True
            else:
                self.failures.append(
                    f"Only {valid_pct:.1f}% of games have complete required fields (threshold: 95%)"
                )
                return False

        except Exception as e:
            self.failures.append(f"JSONB structure validation failed: {e}")
            return False

    def validate_data_completeness(self) -> bool:
        """Validate data completeness across all games"""
        try:
            # Build query
            query = "SELECT * FROM raw_data.nba_games ORDER BY game_id"
            if self.sample_size:
                query += f" LIMIT {self.sample_size}"

            self.cursor.execute(query)
            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.failures.append("No games found to validate")
                return False

            self.log(f"Checking data completeness for {len(games):,} games")

            # Track completeness metrics
            total_games = len(games)
            completeness_stats = defaultdict(int)

            for game in games:
                completeness = check_data_completeness(game)
                for key, value in completeness.items():
                    if value:
                        completeness_stats[key] += 1

            # Calculate percentages and report
            self.log("\nData completeness:")
            all_complete = True
            for key, count in sorted(completeness_stats.items()):
                pct = (count / total_games) * 100
                status = "✓" if pct >= 95.0 else "✗"
                self.log(f"  {status} {key}: {count:,}/{total_games:,} ({pct:.1f}%)")

                if pct < 95.0:
                    all_complete = False
                    if key in ["has_game_info", "has_teams", "has_scores"]:
                        # Critical fields
                        self.failures.append(
                            f"Critical field '{key}' only present in {pct:.1f}% of games"
                        )
                    else:
                        # Non-critical fields
                        self.warnings.append(
                            f"Field '{key}' only present in {pct:.1f}% of games"
                        )

            return all_complete or len(self.failures) == 0

        except Exception as e:
            self.failures.append(f"Data completeness validation failed: {e}")
            return False

    def validate_play_by_play_summaries(self) -> bool:
        """Validate play-by-play summaries are present and reasonable"""
        try:
            # Check games with PBP summaries
            self.cursor.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(*) FILTER (WHERE data ? 'play_by_play') as has_pbp,
                       AVG((data->'play_by_play'->>'total_plays')::int) FILTER (WHERE data ? 'play_by_play') as avg_plays
                FROM raw_data.nba_games
            """
            )

            result = self.cursor.fetchone()
            total = result["total"]
            has_pbp = result["has_pbp"]
            avg_plays = result["avg_plays"]

            pbp_pct = (has_pbp / total * 100) if total > 0 else 0

            self.log(f"Games with play-by-play: {has_pbp:,}/{total:,} ({pbp_pct:.1f}%)")

            if avg_plays:
                self.log(f"Average plays per game: {avg_plays:.0f}")

            # Reasonable range: 350-550 plays per game
            if avg_plays and (avg_plays < 350 or avg_plays > 550):
                self.warnings.append(
                    f"Average plays per game ({avg_plays:.0f}) outside normal range (350-550)"
                )

            # Check for games with suspiciously few plays
            if has_pbp > 0:
                self.cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM raw_data.nba_games
                    WHERE data ? 'play_by_play'
                      AND (data->'play_by_play'->>'total_plays')::int < 100
                """
                )

                few_plays = self.cursor.fetchone()["count"]
                if few_plays > 0:
                    few_pct = few_plays / has_pbp * 100
                    self.warnings.append(
                        f"{few_plays} games have < 100 plays ({few_pct:.1f}%)"
                    )

            return True

        except Exception as e:
            self.failures.append(f"Play-by-play validation failed: {e}")
            return False

    def validate_jsonb_keys_consistency(self) -> bool:
        """Validate that JSONB keys are consistent across games"""
        try:
            # Sample games to check key consistency
            sample = min(100, self.sample_size) if self.sample_size else 100

            self.cursor.execute(
                f"""
                SELECT data, metadata
                FROM raw_data.nba_games
                ORDER BY game_id
                LIMIT {sample}
            """
            )

            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.failures.append("No games found for key consistency check")
                return False

            self.log(f"Checking JSONB key consistency across {len(games)} games")

            # Collect all keys from data and metadata
            data_keys_per_game = []
            metadata_keys_per_game = []

            for game in games:
                data_keys = set(game["data"].keys()) if game.get("data") else set()
                metadata_keys = (
                    set(game["metadata"].keys()) if game.get("metadata") else set()
                )

                data_keys_per_game.append(data_keys)
                metadata_keys_per_game.append(metadata_keys)

            # Find most common key sets
            from collections import Counter

            # Data keys
            data_key_counter = Counter(
                tuple(sorted(keys)) for keys in data_keys_per_game
            )
            most_common_data_keys = data_key_counter.most_common(1)[0][0]
            data_consistency_pct = (
                data_key_counter.most_common(1)[0][1] / len(games)
            ) * 100

            self.log(f"Data key consistency: {data_consistency_pct:.1f}%")
            self.log(f"  Common data keys: {', '.join(most_common_data_keys)}")

            # Metadata keys
            metadata_key_counter = Counter(
                tuple(sorted(keys)) for keys in metadata_keys_per_game
            )
            most_common_metadata_keys = metadata_key_counter.most_common(1)[0][0]
            metadata_consistency_pct = (
                metadata_key_counter.most_common(1)[0][1] / len(games)
            ) * 100

            self.log(f"Metadata key consistency: {metadata_consistency_pct:.1f}%")
            self.log(f"  Common metadata keys: {', '.join(most_common_metadata_keys)}")

            # Warn if consistency is low
            if data_consistency_pct < 80:
                self.warnings.append(
                    f"Data key consistency is only {data_consistency_pct:.1f}%"
                )

            if metadata_consistency_pct < 80:
                self.warnings.append(
                    f"Metadata key consistency is only {metadata_consistency_pct:.1f}%"
                )

            return True

        except Exception as e:
            self.failures.append(f"JSONB key consistency check failed: {e}")
            return False

    # ========================================================================
    # Data Quality Validation
    # ========================================================================

    def validate_no_null_jsonb(self) -> bool:
        """Validate no games have NULL JSONB columns"""
        try:
            self.cursor.execute(
                """
                SELECT COUNT(*) as null_data_count
                FROM raw_data.nba_games
                WHERE data IS NULL
            """
            )
            null_data = self.cursor.fetchone()["null_data_count"]

            self.cursor.execute(
                """
                SELECT COUNT(*) as null_metadata_count
                FROM raw_data.nba_games
                WHERE metadata IS NULL
            """
            )
            null_metadata = self.cursor.fetchone()["null_metadata_count"]

            if null_data > 0:
                self.failures.append(f"{null_data} games have NULL data column")
                return False

            if null_metadata > 0:
                self.failures.append(f"{null_metadata} games have NULL metadata column")
                return False

            self.log("No NULL JSONB columns found")
            return True

        except Exception as e:
            self.failures.append(f"NULL JSONB validation failed: {e}")
            return False

    def validate_scores_reasonable(self) -> bool:
        """Validate game scores are in reasonable ranges"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (
                        WHERE (data->'teams'->'home'->>'score')::int < 50
                           OR (data->'teams'->'away'->>'score')::int < 50
                    ) as low_scores,
                    COUNT(*) FILTER (
                        WHERE (data->'teams'->'home'->>'score')::int > 200
                           OR (data->'teams'->'away'->>'score')::int > 200
                    ) as high_scores,
                    AVG((data->'teams'->'home'->>'score')::int) as avg_home_score,
                    AVG((data->'teams'->'away'->>'score')::int) as avg_away_score
                FROM raw_data.nba_games
                WHERE data->'teams'->'home' ? 'score'
                  AND data->'teams'->'away' ? 'score'
            """
            )

            result = self.cursor.fetchone()
            total = result["total"]
            low_scores = result["low_scores"]
            high_scores = result["high_scores"]
            avg_home = result["avg_home_score"]
            avg_away = result["avg_away_score"]

            self.log(f"Average scores: Home {avg_home:.1f}, Away {avg_away:.1f}")

            # Check for outliers
            if low_scores > 0:
                low_pct = low_scores / total * 100
                self.warnings.append(
                    f"{low_scores} games have scores < 50 ({low_pct:.1f}%)"
                )

            if high_scores > 0:
                high_pct = high_scores / total * 100
                self.warnings.append(
                    f"{high_scores} games have scores > 200 ({high_pct:.1f}%)"
                )

            # Average NBA score should be around 100-115
            if avg_home < 80 or avg_home > 130:
                self.warnings.append(
                    f"Average home score ({avg_home:.1f}) outside normal range (80-130)"
                )

            if avg_away < 80 or avg_away > 130:
                self.warnings.append(
                    f"Average away score ({avg_away:.1f}) outside normal range (80-130)"
                )

            return True

        except Exception as e:
            self.failures.append(f"Score validation failed: {e}")
            return False

    # ========================================================================
    # Main Validation Runner
    # ========================================================================

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"Raw Data Schema Validation")
        if self.sample_size:
            print(f"Sample size: {self.sample_size:,} games")
        print(f"{'='*60}\n")

        # Connect to database
        if not self.connect_db():
            print("\n❌ Database connection failed. Aborting.")
            return False, {}

        try:
            results = {
                "schema_exists": self.validate_schema_exists(),
                "tables_exist": self.validate_tables_exist(),
                "row_counts_ok": self.validate_row_counts(),
                "jsonb_structure_valid": self.validate_jsonb_structure(),
                "data_completeness_ok": self.validate_data_completeness(),
                "play_summaries_ok": self.validate_play_by_play_summaries(),
                "jsonb_keys_consistent": self.validate_jsonb_keys_consistency(),
                "no_null_jsonb": self.validate_no_null_jsonb(),
                "scores_reasonable": self.validate_scores_reasonable(),
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
        description="Validate raw_data schema JSONB structure and data quality"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--sample", type=int, help="Limit validation to N games (for testing)"
    )
    parser.add_argument("--host", help="Database host (overrides environment)")
    parser.add_argument(
        "--port", type=int, help="Database port (overrides environment)"
    )
    parser.add_argument("--database", help="Database name (overrides environment)")
    parser.add_argument("--user", help="Database user (overrides environment)")
    parser.add_argument("--password", help="Database password (overrides environment)")

    args = parser.parse_args()

    # Build database config from CLI args
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

    validator = RawDataSchemaValidator(
        verbose=args.verbose,
        sample_size=args.sample,
        db_config=db_config if db_config else None,
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
