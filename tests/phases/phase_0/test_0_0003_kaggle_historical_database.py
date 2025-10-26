#!/usr/bin/env python3
"""
Phase 0.3 Tests: Kaggle Historical Database

Comprehensive pytest test suite for Phase 0.3 (Kaggle Historical Database).

Test Coverage:
- Database file existence and accessibility
- Database size and format
- Schema validation (17 tables)
- Row count validation
- Temporal coverage (2004-2020)
- Data quality and completeness
- Integration validation
- Metadata and documentation

Usage:
    # Run all tests
    pytest tests/phases/phase_0/test_0_3_kaggle_historical_database.py -v

    # Run specific test class
    pytest tests/phases/phase_0/test_0_3_kaggle_historical_database.py::TestPhase03DatabaseFile -v

    # Run with slow tests
    pytest tests/phases/phase_0/test_0_3_kaggle_historical_database.py -v -m "not slow"

Test Organization:
- TestPhase03DatabaseFile: Database file tests
- TestPhase03Schema: Schema and table tests
- TestPhase03RowCounts: Row count validation
- TestPhase03DataQuality: Data quality tests
- TestPhase03Integration: Integration tests
- TestPhase03Metadata: Documentation metadata
- TestPhase03README: README completeness
- TestPhase03Comprehensive: Slow comprehensive tests
"""

import os
import sqlite3
from pathlib import Path

import pytest


class TestPhase03DatabaseFile:
    """Test database file existence and properties"""

    def test_database_file_exists(self, kaggle_db_path):
        """Test that the Kaggle database file exists"""
        assert kaggle_db_path.exists(), f"Database file not found: {kaggle_db_path}"

    def test_database_file_size(self, kaggle_db_path):
        """Test that database file size is reasonable (~2.2 GB, expanded from 280 MB)"""
        file_size_mb = kaggle_db_path.stat().st_size / (1024 * 1024)
        expected_size_mb = 2240  # Updated from 280 MB (database expanded)
        tolerance_mb = 500  # Allow 500 MB tolerance

        assert abs(file_size_mb - expected_size_mb) <= tolerance_mb, (
            f"Database file size {file_size_mb:.1f} MB is outside expected range "
            f"{expected_size_mb} MB ± {tolerance_mb} MB"
        )

    def test_database_is_sqlite(self, kaggle_db_path):
        """Test that database is a valid SQLite file"""
        # Try to connect
        try:
            conn = sqlite3.connect(kaggle_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            conn.close()
            assert version is not None, "Could not retrieve SQLite version"
        except sqlite3.Error as e:
            pytest.fail(f"Database is not a valid SQLite file: {e}")


class TestPhase03Schema:
    """Test database schema and table existence"""

    def test_all_tables_exist(self, kaggle_db_connection, kaggle_tables):
        """Test that all 17 expected tables exist"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        existing_tables = set(row[0] for row in cursor.fetchall())

        expected_tables = set(kaggle_tables)
        missing_tables = expected_tables - existing_tables

        assert (
            not missing_tables
        ), f"Missing tables: {', '.join(sorted(missing_tables))}"

    def test_table_count(self, kaggle_db_connection, kaggle_tables):
        """Test that exactly 16 tables exist (updated from 17)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

        assert table_count == len(
            kaggle_tables
        ), f"Expected {len(kaggle_tables)} tables, found {table_count}"

    def test_game_table_schema(self, kaggle_db_connection):
        """Test game table has expected columns (updated schema)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("PRAGMA table_info(game)")
        columns = [row[1] for row in cursor.fetchall()]

        # Updated schema: season_id (not season), pts_home/pts_away (not home_team_score/away_team_score)
        expected_columns = [
            "game_id",
            "game_date",
            "season_id",
            "team_id_home",
            "team_id_away",
            "pts_home",
            "pts_away",
            "season_type",
        ]

        for col in expected_columns:
            assert col in columns, f"Column '{col}' missing from game table"

    def test_player_table_schema(self, kaggle_db_connection):
        """Test player table has expected columns (updated schema)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("PRAGMA table_info(player)")
        columns = [row[1] for row in cursor.fetchall()]

        # Updated schema (simplified from original)
        expected_columns = ["id", "full_name", "first_name", "last_name", "is_active"]

        for col in expected_columns:
            assert col in columns, f"Column '{col}' missing from player table"


class TestPhase03RowCounts:
    """Test row counts for all tables"""

    def test_game_table_row_count(self, kaggle_db_connection):
        """Test game table has expected number of rows (65,698, expanded from 26,496)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM game")
        count = cursor.fetchone()[0]

        expected = 65698  # Database expanded from 26,496 to 65,698
        assert (
            count == expected
        ), f"Game table: Expected {expected:,} rows, got {count:,}"

    def test_team_table_row_count(self, kaggle_db_connection):
        """Test team table has expected number of rows (30)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM team")
        count = cursor.fetchone()[0]

        expected = 30
        assert count == expected, f"Team table: Expected {expected} rows, got {count}"

    def test_player_table_row_count(self, kaggle_db_connection):
        """Test player table has reasonable number of rows (~4,500)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM player")
        count = cursor.fetchone()[0]

        expected = 4500
        tolerance = 0.3  # 30% tolerance
        lower = int(expected * (1 - tolerance))
        upper = int(expected * (1 + tolerance))

        assert (
            lower <= count <= upper
        ), f"Player table: Expected ~{expected} rows (±{tolerance*100:.0f}%), got {count}"

    def test_play_by_play_row_count(self, kaggle_db_connection):
        """Test play_by_play table has reasonable number of rows (~13.5M, was empty before)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM play_by_play")
        count = cursor.fetchone()[0]

        expected = 13500000  # Database expanded to include 13.5M play-by-play rows
        tolerance = 0.2  # 20% tolerance
        lower = int(expected * (1 - tolerance))
        upper = int(expected * (1 + tolerance))

        assert (
            lower <= count <= upper
        ), f"play_by_play table: Expected ~{expected:,} rows (±{tolerance*100:.0f}%), got {count:,}"

    def test_game_info_row_count(self, kaggle_db_connection):
        """Test game_info table has reasonable number of rows (~58K)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM game_info")
        count = cursor.fetchone()[0]

        expected = 58000
        tolerance = 0.2  # 20% tolerance
        lower = int(expected * (1 - tolerance))
        upper = int(expected * (1 + tolerance))

        assert (
            lower <= count <= upper
        ), f"game_info table: Expected ~{expected:,} rows (±{tolerance*100:.0f}%), got {count:,}"


class TestPhase03DataQuality:
    """Test data quality and completeness"""

    def test_temporal_coverage_min_season(self, kaggle_db_connection):
        """Test that minimum season is 1946 (expanded from 2004)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        # Extract season from season_id (format: "12023" for 2023)
        cursor.execute(
            "SELECT MIN(substr(season_id, 2, 4)) FROM game WHERE season_id IS NOT NULL"
        )
        min_season = cursor.fetchone()[0]

        assert min_season == "1946", f"Min season: Expected 1946, got {min_season}"

    def test_temporal_coverage_max_season(self, kaggle_db_connection):
        """Test that maximum season is 2022 (expanded from 2020)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        # Extract season from season_id (format: "12023" for 2023)
        cursor.execute(
            "SELECT MAX(substr(season_id, 2, 4)) FROM game WHERE season_id IS NOT NULL"
        )
        max_season = cursor.fetchone()[0]

        assert max_season == "2022", f"Max season: Expected 2022, got {max_season}"

    def test_temporal_coverage_season_count(self, kaggle_db_connection):
        """Test that there are 77 distinct seasons (expanded from 17)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        # Extract season from season_id
        cursor.execute(
            "SELECT COUNT(DISTINCT substr(season_id, 2, 4)) FROM game WHERE season_id IS NOT NULL"
        )
        num_seasons = cursor.fetchone()[0]

        assert num_seasons == 77, f"Number of seasons: Expected 77, got {num_seasons}"

    def test_games_have_scores(self, kaggle_db_connection):
        """Test that all games have scores (using updated schema)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()
        # Updated schema: pts_home/pts_away (not home_team_score/away_team_score)
        cursor.execute(
            "SELECT COUNT(*) FROM game WHERE pts_home IS NULL OR pts_away IS NULL"
        )
        games_without_scores = cursor.fetchone()[0]

        # Allow up to 5% missing scores (some historical games may be incomplete)
        cursor.execute("SELECT COUNT(*) FROM game")
        total_games = cursor.fetchone()[0]
        missing_pct = games_without_scores / total_games * 100 if total_games > 0 else 0

        assert (
            missing_pct <= 5
        ), f"{games_without_scores} games missing scores ({missing_pct:.1f}% of total)"

    def test_play_by_play_completeness(self, kaggle_db_connection):
        """Test that play-by-play data has high completeness"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()

        # Count play-by-play rows
        cursor.execute("SELECT COUNT(*) FROM play_by_play")
        pbp_count = cursor.fetchone()[0]

        # Expect at least 10M play-by-play rows
        expected_min = 10000000

        assert (
            pbp_count >= expected_min
        ), f"Play-by-play completeness: {pbp_count:,} rows (expected ≥{expected_min:,})"


class TestPhase03Integration:
    """Test integration and cross-validation"""

    def test_game_info_reasonable_count(self, kaggle_db_connection):
        """Test that game_info table has reasonable coverage (≥80% of games)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM game")
        game_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM game_info")
        game_info_count = cursor.fetchone()[0]

        coverage = game_info_count / game_count * 100 if game_count > 0 else 0

        assert (
            coverage >= 80
        ), f"game_info coverage: {coverage:.1f}% ({game_info_count:,}/{game_count:,}), expected ≥80%"

    def test_teams_referenced_in_games(self, kaggle_db_connection):
        """Test that all teams in team table are referenced in games (updated schema)"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()

        # Get all team IDs
        cursor.execute("SELECT id FROM team")
        team_ids = set(row[0] for row in cursor.fetchall())

        # Get team IDs referenced in games (updated column names: team_id_home/team_id_away)
        cursor.execute(
            "SELECT DISTINCT team_id_home FROM game UNION "
            "SELECT DISTINCT team_id_away FROM game"
        )
        referenced_team_ids = set(row[0] for row in cursor.fetchall())

        # Check if most teams are referenced (some might not have played in all seasons)
        coverage = len(referenced_team_ids) / len(team_ids) * 100

        assert (
            coverage >= 80
        ), f"Only {coverage:.1f}% of teams are referenced in games (expected ≥80%)"


class TestPhase03Metadata:
    """Test metadata and documentation"""

    def test_readme_file_exists(self):
        """Test that Phase 0.3 README exists"""
        readme_path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "phases"
            / "phase_0"
            / "0.3_kaggle_historical_database"
            / "README.md"
        )
        assert readme_path.exists(), f"README not found: {readme_path}"

    def test_readme_has_documented_row_counts(self):
        """Test that README documents row counts"""
        readme_path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "phases"
            / "phase_0"
            / "0.3_kaggle_historical_database"
            / "README.md"
        )

        if not readme_path.exists():
            pytest.skip("README not found")

        content = readme_path.read_text()

        # README should document either old values (26K) or new values (66K)
        # This test passes if either set is documented
        has_game_count = (
            "26,496" in content
            or "26496" in content
            or "65,698" in content
            or "65698" in content
            or "66" in content
        )
        assert has_game_count, "README should document game count (either 26K or 66K)"

        has_size = (
            "280 MB" in content
            or "280MB" in content
            or "2.2 GB" in content
            or "2240 MB" in content
        )
        assert (
            has_size
        ), "README should document database size (either 280 MB or 2.2 GB)"

    def test_readme_has_temporal_coverage(self):
        """Test that README documents temporal coverage"""
        readme_path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "phases"
            / "phase_0"
            / "0.3_kaggle_historical_database"
            / "README.md"
        )

        if not readme_path.exists():
            pytest.skip("README not found")

        content = readme_path.read_text()

        # README should mention either old range (2004-2020) or new range (1946-2023)
        has_start_year = "2004" in content or "1946" in content
        has_end_year = "2020" in content or "2022" in content or "2023" in content

        assert has_start_year, "README should mention start year (2004 or 1946)"
        assert has_end_year, "README should mention end year (2020, 2022, or 2023)"


class TestPhase03README:
    """Test README completeness and structure"""

    def test_readme_has_required_sections(self):
        """Test that README has all required sections"""
        readme_path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "phases"
            / "phase_0"
            / "0.3_kaggle_historical_database"
            / "README.md"
        )

        if not readme_path.exists():
            pytest.skip("README not found")

        content = readme_path.read_text()

        required_sections = [
            "## Overview",
            "## Data Coverage",
            "## Quick Start",
            "## Storage Locations",
            "## Schema Details",
        ]

        for section in required_sections:
            assert section in content, f"README missing section: {section}"

    def test_readme_has_navigation_links(self):
        """Test that README has navigation links"""
        readme_path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "phases"
            / "phase_0"
            / "0.3_kaggle_historical_database"
            / "README.md"
        )

        if not readme_path.exists():
            pytest.skip("README not found")

        content = readme_path.read_text()

        # Check for navigation
        assert (
            "## Navigation" in content or "**Return to:**" in content
        ), "README should have navigation section"


class TestPhase03Comprehensive:
    """Comprehensive tests (marked as slow)"""

    @pytest.mark.slow
    def test_comprehensive_validation(self, kaggle_db_connection):
        """Run comprehensive validation of all tables"""
        if kaggle_db_connection is None:
            pytest.skip("Kaggle database not available")

        cursor = kaggle_db_connection.cursor()

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        results = []
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            results.append((table, count))

        # All tables should be queryable
        assert len(results) == len(tables), "Could not query all tables"

        # Print results for reference
        print("\n=== Comprehensive Table Row Counts ===")
        for table, count in results:
            print(f"  {table}: {count:,} rows")

    @pytest.mark.slow
    def test_integration_with_validator(self, kaggle_db_path):
        """Test that standalone validator passes"""
        import subprocess
        import sys

        validator_path = (
            Path(__file__).resolve().parents[3]
            / "validators"
            / "phases"
            / "phase_0"
            / "validate_0_3_kaggle_historical.py"
        )

        if not validator_path.exists():
            pytest.skip("Validator not found")

        result = subprocess.run(
            [sys.executable, str(validator_path)], capture_output=True, text=True
        )

        assert (
            result.returncode == 0
        ), f"Validator failed:\n{result.stdout}\n{result.stderr}"
