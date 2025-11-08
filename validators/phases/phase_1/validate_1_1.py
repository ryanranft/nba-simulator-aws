#!/usr/bin/env python3
"""
Validate 1.1: Feature Extraction Validator

Validates ESPN features can be extracted from JSONB in raw_data schema.
Tests JSONB field accessibility, data type correctness, value ranges,
and extraction helper compatibility.

Based on ESPN Feature Coverage Analysis (58 features mapped).

Usage:
    python validators/phases/phase_1/validate_1_1.py
    python validators/phases/phase_1/validate_1_1.py --verbose
    python validators/phases/phase_1/validate_1_1.py --sample 100
    python validators/phases/phase_1/validate_1_1.py --host localhost --database nba_simulator --user ryanranft --password ""
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
    get_game_score,
    get_team_info,
    get_game_info,
    get_play_summary,
    get_source_data,
    get_complete_game_data,
    navigate_jsonb_path,
    check_jsonb_path_exists,
    # ESPN enrichment helpers
    get_espn_game_info,
    get_espn_box_score,
    get_espn_venue,
    get_espn_officials,
    get_quarter_scores,
    get_player_stats,
    get_top_scorer,
)


class FeatureExtractionValidator:
    """Validates ESPN feature extraction from JSONB"""

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
    # JSONB Field Accessibility
    # ========================================================================

    def validate_extraction_helpers(self) -> bool:
        """Validate all extraction helper functions work"""
        try:
            # Get sample games
            query = "SELECT * FROM raw_data.nba_games ORDER BY game_id"
            if self.sample_size:
                query += f" LIMIT {self.sample_size}"

            self.cursor.execute(query)
            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.failures.append("No games found to test extraction helpers")
                return False

            self.log(f"Testing extraction helpers on {len(games):,} games")

            # Test each helper function
            helper_results = defaultdict(
                lambda: {"success": 0, "failure": 0, "errors": []}
            )

            for game in games:
                game_id = game["game_id"]

                # Test get_game_score
                try:
                    scores = get_game_score(game)
                    if (
                        scores.get("home") is not None
                        and scores.get("away") is not None
                    ):
                        helper_results["get_game_score"]["success"] += 1
                    else:
                        helper_results["get_game_score"]["failure"] += 1
                except Exception as e:
                    helper_results["get_game_score"]["failure"] += 1
                    helper_results["get_game_score"]["errors"].append(f"{game_id}: {e}")

                # Test get_team_info
                try:
                    teams = get_team_info(game)
                    if teams.get("home", {}).get("name") and teams.get("away", {}).get(
                        "name"
                    ):
                        helper_results["get_team_info"]["success"] += 1
                    else:
                        helper_results["get_team_info"]["failure"] += 1
                except Exception as e:
                    helper_results["get_team_info"]["failure"] += 1
                    helper_results["get_team_info"]["errors"].append(f"{game_id}: {e}")

                # Test get_game_info
                try:
                    info = get_game_info(game)
                    if info.get("game_id") and info.get("game_date"):
                        helper_results["get_game_info"]["success"] += 1
                    else:
                        helper_results["get_game_info"]["failure"] += 1
                except Exception as e:
                    helper_results["get_game_info"]["failure"] += 1
                    helper_results["get_game_info"]["errors"].append(f"{game_id}: {e}")

                # Test get_play_summary
                try:
                    pbp = get_play_summary(game)
                    if pbp.get("total_plays") is not None:
                        helper_results["get_play_summary"]["success"] += 1
                    else:
                        helper_results["get_play_summary"]["failure"] += 1
                except Exception as e:
                    helper_results["get_play_summary"]["failure"] += 1
                    helper_results["get_play_summary"]["errors"].append(
                        f"{game_id}: {e}"
                    )

                # Test get_source_data
                try:
                    source = get_source_data(game)
                    if source.get("source"):
                        helper_results["get_source_data"]["success"] += 1
                    else:
                        helper_results["get_source_data"]["failure"] += 1
                except Exception as e:
                    helper_results["get_source_data"]["failure"] += 1
                    helper_results["get_source_data"]["errors"].append(
                        f"{game_id}: {e}"
                    )

            # Report results
            total_games = len(games)
            all_passed = True

            self.log("\nExtraction helper results:")
            for helper_name, stats in sorted(helper_results.items()):
                success_pct = (
                    (stats["success"] / total_games * 100) if total_games > 0 else 0
                )
                status = "✓" if success_pct >= 95.0 else "✗"

                self.log(
                    f"  {status} {helper_name}: {stats['success']:,}/{total_games:,} ({success_pct:.1f}%)"
                )

                if success_pct < 95.0:
                    all_passed = False
                    self.failures.append(
                        f"{helper_name} only succeeded {success_pct:.1f}% of the time"
                    )

                    # Show sample errors
                    if self.verbose and stats["errors"]:
                        self.log(f"    Sample errors:", "WARNING")
                        for error in stats["errors"][:3]:
                            self.log(f"      {error}", "WARNING")

            return all_passed

        except Exception as e:
            self.failures.append(f"Extraction helper validation failed: {e}")
            return False

    # ========================================================================
    # Data Type Correctness
    # ========================================================================

    def validate_data_types(self) -> bool:
        """Validate extracted data has correct types"""
        try:
            query = "SELECT * FROM raw_data.nba_games ORDER BY game_id"
            if self.sample_size:
                query += f" LIMIT {self.sample_size}"

            self.cursor.execute(query)
            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.failures.append("No games found to validate data types")
                return False

            self.log(f"Validating data types for {len(games):,} games")

            type_mismatches = defaultdict(int)
            total_games = len(games)

            for game in games:
                # Check scores are integers (or None)
                scores = get_game_score(game)
                if scores["home"] is not None and not isinstance(scores["home"], int):
                    type_mismatches["home_score_not_int"] += 1
                if scores["away"] is not None and not isinstance(scores["away"], int):
                    type_mismatches["away_score_not_int"] += 1

                # Check team names are strings
                teams = get_team_info(game)
                if teams["home"]["name"] is not None and not isinstance(
                    teams["home"]["name"], str
                ):
                    type_mismatches["home_name_not_str"] += 1
                if teams["away"]["name"] is not None and not isinstance(
                    teams["away"]["name"], str
                ):
                    type_mismatches["away_name_not_str"] += 1

                # Check game_id is string
                info = get_game_info(game)
                if info["game_id"] is not None and not isinstance(info["game_id"], str):
                    type_mismatches["game_id_not_str"] += 1

                # Check total_plays is integer
                pbp = get_play_summary(game)
                if pbp["total_plays"] is not None and not isinstance(
                    pbp["total_plays"], int
                ):
                    type_mismatches["total_plays_not_int"] += 1

            # Report mismatches
            if type_mismatches:
                self.log("\nData type mismatches found:", "WARNING")
                for field, count in sorted(
                    type_mismatches.items(), key=lambda x: x[1], reverse=True
                ):
                    pct = (count / total_games) * 100
                    self.log(f"  {field}: {count:,} games ({pct:.1f}%)", "WARNING")
                    self.warnings.append(f"{field}: {count} games have wrong type")

                return False
            else:
                self.log("All data types correct")
                return True

        except Exception as e:
            self.failures.append(f"Data type validation failed: {e}")
            return False

    # ========================================================================
    # Value Range Validation
    # ========================================================================

    def validate_value_ranges(self) -> bool:
        """Validate extracted values are in reasonable ranges"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    -- Score ranges
                    COUNT(*) FILTER (
                        WHERE (data->'teams'->'home'->>'score')::int < 50
                           OR (data->'teams'->'away'->>'score')::int < 50
                    ) as low_scores,
                    COUNT(*) FILTER (
                        WHERE (data->'teams'->'home'->>'score')::int > 200
                           OR (data->'teams'->'away'->>'score')::int > 200
                    ) as high_scores,
                    -- Play counts
                    COUNT(*) FILTER (
                        WHERE data ? 'play_by_play'
                          AND (data->'play_by_play'->>'total_plays')::int < 300
                    ) as low_play_counts,
                    COUNT(*) FILTER (
                        WHERE data ? 'play_by_play'
                          AND (data->'play_by_play'->>'total_plays')::int > 600
                    ) as high_play_counts,
                    -- Averages
                    AVG((data->'teams'->'home'->>'score')::int) as avg_home_score,
                    AVG((data->'teams'->'away'->>'score')::int) as avg_away_score,
                    AVG((data->'play_by_play'->>'total_plays')::int) FILTER (WHERE data ? 'play_by_play') as avg_plays
                FROM raw_data.nba_games
                WHERE data->'teams'->'home' ? 'score'
                  AND data->'teams'->'away' ? 'score'
            """
            )

            result = self.cursor.fetchone()
            total = result["total"]

            self.log(f"Validating value ranges for {total:,} games")

            # Check scores
            low_scores = result["low_scores"]
            high_scores = result["high_scores"]
            avg_home = result["avg_home_score"]
            avg_away = result["avg_away_score"]

            self.log(f"  Average scores: Home {avg_home:.1f}, Away {avg_away:.1f}")

            outliers_found = False

            if low_scores > 0:
                low_pct = (low_scores / total) * 100
                if low_pct > 1.0:  # More than 1% is concerning
                    self.warnings.append(
                        f"{low_scores} games have scores < 50 ({low_pct:.1f}%)"
                    )
                    outliers_found = True
                else:
                    self.log(
                        f"  {low_scores} games with scores < 50 ({low_pct:.2f}%) - acceptable"
                    )

            if high_scores > 0:
                high_pct = (high_scores / total) * 100
                if high_pct > 0.1:  # More than 0.1% is concerning
                    self.warnings.append(
                        f"{high_scores} games have scores > 200 ({high_pct:.1f}%)"
                    )
                    outliers_found = True

            # Check play counts
            low_plays = result["low_play_counts"]
            high_plays = result["high_play_counts"]
            avg_plays = result["avg_plays"]

            if avg_plays:
                self.log(f"  Average plays per game: {avg_plays:.0f}")

                if avg_plays < 350 or avg_plays > 550:
                    self.warnings.append(
                        f"Average plays ({avg_plays:.0f}) outside normal range (350-550)"
                    )
                    outliers_found = True

            # Check if averages are reasonable for NBA
            if avg_home and (avg_home < 80 or avg_home > 130):
                self.warnings.append(
                    f"Average home score ({avg_home:.1f}) outside normal NBA range (80-130)"
                )
                outliers_found = True

            if avg_away and (avg_away < 80 or avg_away > 130):
                self.warnings.append(
                    f"Average away score ({avg_away:.1f}) outside normal NBA range (80-130)"
                )
                outliers_found = True

            if not outliers_found:
                self.log("All value ranges reasonable")

            return True  # Warnings only, not failures

        except Exception as e:
            self.failures.append(f"Value range validation failed: {e}")
            return False

    # ========================================================================
    # ESPN Feature Coverage
    # ========================================================================

    def validate_espn_feature_coverage(self) -> bool:
        """Validate ESPN features currently available in database"""
        try:
            # Based on ESPN Feature Coverage doc: 7 features currently in database
            expected_features = {
                "game_id": "data.game_info.game_id",
                "game_date": "data.game_info.game_date",
                "season": "data.game_info.season",
                "season_year": "data.game_info.season_year",
                "home_name": "data.teams.home.name",
                "away_name": "data.teams.away.name",
                "home_score": "data.teams.home.score",
                "away_score": "data.teams.away.score",
                "total_plays": "data.play_by_play.total_plays",
            }

            query = "SELECT * FROM raw_data.nba_games ORDER BY game_id"
            if self.sample_size:
                query += f" LIMIT {self.sample_size}"

            self.cursor.execute(query)
            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.failures.append("No games found to validate ESPN features")
                return False

            self.log(f"Validating ESPN feature coverage for {len(games):,} games")

            total_games = len(games)
            feature_coverage = {}

            for feature_name, jsonb_path in expected_features.items():
                present_count = sum(
                    1 for game in games if check_jsonb_path_exists(game, jsonb_path)
                )
                coverage_pct = (present_count / total_games) * 100
                feature_coverage[feature_name] = {
                    "present": present_count,
                    "coverage_pct": coverage_pct,
                }

            # Report results
            self.log("\nESPN feature coverage:")
            all_critical_present = True

            for feature_name, stats in sorted(
                feature_coverage.items(),
                key=lambda x: x[1]["coverage_pct"],
                reverse=True,
            ):
                pct = stats["coverage_pct"]
                status = "✓" if pct >= 95.0 else "✗"
                self.log(
                    f"  {status} {feature_name}: {stats['present']:,}/{total_games:,} ({pct:.1f}%)"
                )

                # Critical features must be >95%
                critical_features = [
                    "game_id",
                    "game_date",
                    "home_score",
                    "away_score",
                    "home_name",
                    "away_name",
                ]
                if feature_name in critical_features and pct < 95.0:
                    all_critical_present = False
                    self.failures.append(
                        f"Critical feature '{feature_name}' only present in {pct:.1f}% of games"
                    )

            return all_critical_present

        except Exception as e:
            self.failures.append(f"ESPN feature coverage validation failed: {e}")
            return False

    # ========================================================================
    # ESPN Enrichment Validation (NEW - for enriched features)
    # ========================================================================

    def validate_enrichment_coverage(self) -> bool:
        """Validate all games have been enriched with ESPN features"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total_games,
                    COUNT(*) FILTER (WHERE data ? 'espn_features') as enriched_games,
                    COUNT(*) FILTER (WHERE data->'espn_features' ? 'game_info') as has_game_info,
                    COUNT(*) FILTER (WHERE data->'espn_features' ? 'box_score') as has_box_score,
                    COUNT(*) FILTER (WHERE data->'espn_features' ? 'scoring') as has_scoring,
                    COUNT(*) FILTER (WHERE data->'espn_features' ? 'venue') as has_venue,
                    COUNT(*) FILTER (WHERE data->'espn_features' ? 'officials') as has_officials,
                    COUNT(*) FILTER (WHERE data->'metadata' ? 'enrichment') as has_metadata
                FROM raw_data.nba_games
            """
            )

            result = self.cursor.fetchone()
            total = result["total_games"]
            enriched = result["enriched_games"]

            self.log(f"Checking enrichment coverage for {total:,} games")

            # Report enrichment status
            sections = {
                "enriched_games": enriched,
                "has_game_info": result["has_game_info"],
                "has_box_score": result["has_box_score"],
                "has_scoring": result["has_scoring"],
                "has_venue": result["has_venue"],
                "has_officials": result["has_officials"],
                "has_metadata": result["has_metadata"],
            }

            # Check if enrichment is in progress or complete
            if enriched == 0:
                self.warnings.append(
                    "No games enriched yet - enrichment may be in progress"
                )
                return True  # Don't fail, just warn
            elif enriched < total:
                self.warnings.append(
                    f"Enrichment in progress: {enriched}/{total} ({enriched/total*100:.1f}%)"
                )
                # During enrichment, only warn about coverage, don't fail
                for section, count in sections.items():
                    pct = (count / total * 100) if total > 0 else 0
                    status = "⏳" if pct > 0 else "⚠"
                    self.log(f"  {status} {section}: {count:,}/{total:,} ({pct:.1f}%)")
                return True  # Don't fail during enrichment
            else:
                # Enrichment complete, check coverage
                self.log("✓ All games enriched!")
                all_covered = True
                for section, count in sections.items():
                    pct = (count / total * 100) if total > 0 else 0
                    status = "✓" if pct >= 95.0 else "✗"
                    self.log(f"  {status} {section}: {count:,}/{total:,} ({pct:.1f}%)")

                    if pct < 95.0:
                        all_covered = False
                        self.failures.append(
                            f"{section} coverage incomplete: {pct:.1f}%"
                        )

                return all_covered

        except Exception as e:
            self.failures.append(f"Enrichment coverage validation failed: {e}")
            return False

    def validate_enrichment_metadata(self) -> bool:
        """Validate enrichment metadata is present and correct"""
        try:
            self.cursor.execute(
                """
                SELECT
                    COUNT(*) as total_enriched,
                    COUNT(*) FILTER (WHERE data->'metadata'->'enrichment' ? 'enriched_at') as has_timestamp,
                    COUNT(*) FILTER (WHERE data->'metadata'->'enrichment' ? 'feature_count') as has_feature_count,
                    COUNT(*) FILTER (WHERE data->'metadata'->'enrichment' ? 'format_version') as has_format,
                    MIN((data->'metadata'->'enrichment'->>'feature_count')::int) as min_features,
                    MAX((data->'metadata'->'enrichment'->>'feature_count')::int) as max_features,
                    AVG((data->'metadata'->'enrichment'->>'feature_count')::int) as avg_features,
                    COUNT(*) FILTER (WHERE (data->'espn_features'->'source_data'->>'format')::int = 1) as format_1,
                    COUNT(*) FILTER (WHERE (data->'espn_features'->'source_data'->>'format')::int = 2) as format_2
                FROM raw_data.nba_games
                WHERE data ? 'espn_features'
            """
            )

            result = self.cursor.fetchone()
            total_enriched = result["total_enriched"]

            if total_enriched == 0:
                self.warnings.append("No enriched games found to validate metadata")
                return True  # Don't fail, enrichment may not be done

            self.log(
                f"Validating enrichment metadata for {total_enriched:,} enriched games"
            )

            # Check metadata fields
            has_timestamp = result["has_timestamp"]
            has_feature_count = result["has_feature_count"]
            has_format = result["has_format"]

            metadata_present = True
            for field, count in [
                ("timestamp", has_timestamp),
                ("feature_count", has_feature_count),
                ("format_version", has_format),
            ]:
                pct = (count / total_enriched * 100) if total_enriched > 0 else 0
                status = "✓" if pct >= 95.0 else "✗"
                self.log(
                    f"  {status} {field}: {count:,}/{total_enriched:,} ({pct:.1f}%)"
                )

                if pct < 95.0:
                    metadata_present = False
                    self.failures.append(
                        f"Enrichment metadata '{field}' missing in {100-pct:.1f}% of games"
                    )

            # Check feature counts
            min_features = result["min_features"]
            max_features = result["max_features"]
            avg_features = result["avg_features"]

            if avg_features:
                self.log(
                    f"  Feature counts: min={min_features}, max={max_features}, avg={avg_features:.0f}"
                )

                # Expect at least 50 base features (game info + scoring + venue)
                # and up to 500+ with full box scores
                if min_features and min_features < 50:
                    self.warnings.append(
                        f"Some games have very few features: min={min_features}"
                    )

                if avg_features < 200:
                    self.warnings.append(
                        f"Average feature count seems low: {avg_features:.0f} (expected >200 with box scores)"
                    )

            # Check format distribution
            format_1 = result["format_1"]
            format_2 = result["format_2"]

            self.log(f"  Format distribution:")
            self.log(
                f"    Format 1: {format_1:,} games ({format_1/total_enriched*100 if total_enriched else 0:.1f}%)"
            )
            self.log(
                f"    Format 2: {format_2:,} games ({format_2/total_enriched*100 if total_enriched else 0:.1f}%)"
            )

            return metadata_present

        except Exception as e:
            self.failures.append(f"Enrichment metadata validation failed: {e}")
            return False

    def validate_espn_enrichment_helpers(self) -> bool:
        """Validate ESPN enrichment helper functions work on enriched data"""
        try:
            # Get sample of enriched games only
            query = """
                SELECT * FROM raw_data.nba_games
                WHERE data ? 'espn_features'
                ORDER BY game_id
            """
            if self.sample_size:
                query += f" LIMIT {self.sample_size}"

            self.cursor.execute(query)
            games = [dict(row) for row in self.cursor.fetchall()]

            if not games:
                self.warnings.append("No enriched games found to test ESPN helpers")
                return True  # Don't fail, enrichment may not be done

            self.log(
                f"Testing ESPN enrichment helpers on {len(games):,} enriched games"
            )

            helper_results = defaultdict(
                lambda: {"success": 0, "failure": 0, "errors": []}
            )

            for game in games:
                game_id = game["game_id"]

                # Test get_espn_game_info
                try:
                    info = get_espn_game_info(game)
                    if info.get("game_id") and info.get("season"):
                        helper_results["get_espn_game_info"]["success"] += 1
                    else:
                        helper_results["get_espn_game_info"]["failure"] += 1
                except Exception as e:
                    helper_results["get_espn_game_info"]["failure"] += 1
                    helper_results["get_espn_game_info"]["errors"].append(
                        f"{game_id}: {e}"
                    )

                # Test get_espn_box_score
                try:
                    home_players = get_espn_box_score(game, "home")
                    away_players = get_espn_box_score(game, "away")
                    if isinstance(home_players, list) and isinstance(
                        away_players, list
                    ):
                        helper_results["get_espn_box_score"]["success"] += 1
                    else:
                        helper_results["get_espn_box_score"]["failure"] += 1
                except Exception as e:
                    helper_results["get_espn_box_score"]["failure"] += 1
                    helper_results["get_espn_box_score"]["errors"].append(
                        f"{game_id}: {e}"
                    )

                # Test get_espn_venue
                try:
                    venue = get_espn_venue(game)
                    if isinstance(venue, dict):
                        helper_results["get_espn_venue"]["success"] += 1
                    else:
                        helper_results["get_espn_venue"]["failure"] += 1
                except Exception as e:
                    helper_results["get_espn_venue"]["failure"] += 1
                    helper_results["get_espn_venue"]["errors"].append(f"{game_id}: {e}")

                # Test get_espn_officials
                try:
                    officials = get_espn_officials(game)
                    if isinstance(officials, list):
                        helper_results["get_espn_officials"]["success"] += 1
                    else:
                        helper_results["get_espn_officials"]["failure"] += 1
                except Exception as e:
                    helper_results["get_espn_officials"]["failure"] += 1
                    helper_results["get_espn_officials"]["errors"].append(
                        f"{game_id}: {e}"
                    )

                # Test get_quarter_scores
                try:
                    home_quarters = get_quarter_scores(game, "home")
                    away_quarters = get_quarter_scores(game, "away")
                    if isinstance(home_quarters, list) and isinstance(
                        away_quarters, list
                    ):
                        helper_results["get_quarter_scores"]["success"] += 1
                    else:
                        helper_results["get_quarter_scores"]["failure"] += 1
                except Exception as e:
                    helper_results["get_quarter_scores"]["failure"] += 1
                    helper_results["get_quarter_scores"]["errors"].append(
                        f"{game_id}: {e}"
                    )

                # Test get_top_scorer
                try:
                    home_top = get_top_scorer(game, "home")
                    away_top = get_top_scorer(game, "away")
                    # Can be None if no box score, but should not raise exception
                    helper_results["get_top_scorer"]["success"] += 1
                except Exception as e:
                    helper_results["get_top_scorer"]["failure"] += 1
                    helper_results["get_top_scorer"]["errors"].append(f"{game_id}: {e}")

            # Report results
            total_games = len(games)
            all_passed = True

            self.log("\nESPN enrichment helper results:")
            for helper_name, stats in sorted(helper_results.items()):
                success_pct = (
                    (stats["success"] / total_games * 100) if total_games > 0 else 0
                )
                status = "✓" if success_pct >= 95.0 else "✗"

                self.log(
                    f"  {status} {helper_name}: {stats['success']:,}/{total_games:,} ({success_pct:.1f}%)"
                )

                if success_pct < 95.0:
                    all_passed = False
                    self.failures.append(
                        f"{helper_name} only succeeded {success_pct:.1f}% of the time on enriched data"
                    )

                    # Show sample errors
                    if self.verbose and stats["errors"]:
                        self.log(f"    Sample errors:", "WARNING")
                        for error in stats["errors"][:3]:
                            self.log(f"      {error}", "WARNING")

            return all_passed

        except Exception as e:
            self.failures.append(f"ESPN enrichment helper validation failed: {e}")
            return False

    # ========================================================================
    # Main Validation Runner
    # ========================================================================

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"1.1 Feature Extraction Validation")
        if self.sample_size:
            print(f"Sample size: {self.sample_size:,} games")
        print(f"{'='*60}\n")

        if not self.connect_db():
            print("\n❌ Database connection failed. Aborting.")
            return False, {}

        try:
            results = {
                "extraction_helpers_work": self.validate_extraction_helpers(),
                "data_types_correct": self.validate_data_types(),
                "value_ranges_reasonable": self.validate_value_ranges(),
                "espn_features_accessible": self.validate_espn_feature_coverage(),
                # NEW: Enrichment validations
                "enrichment_coverage": self.validate_enrichment_coverage(),
                "enrichment_metadata": self.validate_enrichment_metadata(),
                "espn_enrichment_helpers_work": self.validate_espn_enrichment_helpers(),
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
    parser = argparse.ArgumentParser(description="Validate 1.1 - Feature Extraction")
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

    validator = FeatureExtractionValidator(
        verbose=args.verbose,
        sample_size=args.sample,
        db_config=db_config if db_config else None,
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
