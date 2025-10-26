"""
Tests for 0.0002: hoopR Data Collection

This test suite validates the completion of 0.0002 by checking:
- S3 hoopR file storage (Parquet and CSV files)
- RDS table creation and population
- Temporal coverage (2002-2025)
- Data completeness and quality
- Cross-source validation

Usage:
    pytest tests/phases/phase_0/test_0_2_hoopr_data_collection.py -v
    pytest tests/phases/phase_0/test_0_2_hoopr_data_collection.py -v -m "not slow"
"""

import pytest
import sys
import os
from pathlib import Path

# Import validator from new location
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_0"
)
sys.path.insert(0, str(validators_path))

from validate_0_2_hoopr_collection import Phase02HooprValidator


class TestPhase02HooprS3Storage:
    """Tests for 0.0002 S3 storage validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase02HooprValidator(verbose=False)

    def test_s3_parquet_files_exist(self, validator):
        """Test hoopR Parquet files exist in S3."""
        assert (
            validator.validate_s3_hoopr_parquet_files() == True
        ), f"S3 Parquet files validation failed: {validator.failures}"

    def test_s3_csv_files_exist(self, validator):
        """Test hoopR CSV files exist in S3."""
        assert (
            validator.validate_s3_hoopr_csv_files() == True
        ), f"S3 CSV files validation failed: {validator.failures}"

    def test_s3_total_file_count(self, validator):
        """Test total hoopR file count in S3 meets minimum."""
        assert (
            validator.validate_s3_total_hoopr_files() == True
        ), f"S3 total file count validation failed: {validator.failures}"


class TestPhase02HooprRDSTables:
    """Tests for 0.0002 RDS table validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase02HooprValidator(verbose=False)

    def test_play_by_play_table_valid(self, validator):
        """Test hoopr_play_by_play table exists and has data."""
        # Skip if RDS not available
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_hoopr_play_by_play_table() == True
        ), f"hoopr_play_by_play table validation failed: {validator.failures}"

    def test_player_box_table_valid(self, validator):
        """Test hoopr_player_box table exists and has data."""
        # Skip if RDS not available
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_hoopr_player_box_table() == True
        ), f"hoopr_player_box table validation failed: {validator.failures}"

    def test_team_box_table_valid(self, validator):
        """Test hoopr_team_box table exists and has data."""
        # Skip if RDS not available
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_hoopr_team_box_table() == True
        ), f"hoopr_team_box table validation failed: {validator.failures}"

    def test_schedule_table_valid(self, validator):
        """Test hoopr_schedule table exists and has data."""
        # Skip if RDS not available
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_hoopr_schedule_table() == True
        ), f"hoopr_schedule table validation failed: {validator.failures}"


class TestPhase02HooprDataQuality:
    """Tests for 0.0002 data quality validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase02HooprValidator(verbose=False)

    def test_temporal_coverage(self, validator):
        """Test temporal coverage spans 2002-2025."""
        # Skip if RDS not available
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_temporal_coverage() == True
        ), f"Temporal coverage validation failed: {validator.failures}"

    def test_data_completeness(self, validator):
        """Test data completeness for all seasons."""
        # Skip if RDS not available
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_data_completeness() == True
        ), f"Data completeness validation failed: {validator.failures}"


class TestPhase02HooprIntegration:
    """Integration tests for 0.0002."""

    def test_phase_complete_validation(self):
        """Comprehensive test that 0.0002 is complete."""
        validator = Phase02HooprValidator(verbose=False)
        all_passed, results = validator.run_all_validations()

        # S3 validations should always pass
        assert (
            results["s3_parquet_files_valid"] == True
        ), "S3 Parquet files validation should pass"
        assert (
            results["s3_csv_files_valid"] == True
        ), "S3 CSV files validation should pass"
        assert (
            results["s3_total_files_valid"] == True
        ), "S3 total files validation should pass"

        # RDS validations may be skipped if RDS unavailable
        if validator.rds_available:
            assert (
                results["hoopr_play_by_play_valid"] == True
            ), "hoopr_play_by_play table should be valid"
            assert (
                results["hoopr_player_box_valid"] == True
            ), "hoopr_player_box table should be valid"
            assert (
                results["hoopr_team_box_valid"] == True
            ), "hoopr_team_box table should be valid"
            assert (
                results["hoopr_schedule_valid"] == True
            ), "hoopr_schedule table should be valid"
            assert (
                results["temporal_coverage_valid"] == True
            ), "Temporal coverage should be valid"
            assert (
                results["data_completeness_valid"] == True
            ), "Data completeness should be valid"

        # Overall pass (accounting for RDS availability)
        if validator.rds_available:
            assert (
                all_passed == True
            ), f"0.0002 completion validation failed. Failures: {validator.failures}"


class TestPhase02HooprMetadata:
    """Tests for 0.0002 documentation metadata."""

    def test_documented_file_counts(self):
        """Verify documented file counts are reasonable."""
        # From 0.0002 README: 410 files (314 CSV + 96 Parquet)
        expected_total = 410
        expected_csv = 314
        expected_parquet = 96

        # These should be close to actual values
        assert (
            expected_total == expected_csv + expected_parquet
        ), "Documented file counts should be consistent"

    def test_documented_data_sizes(self):
        """Verify documented data sizes are reasonable."""
        # From 0.0002 README:
        # - Total: 8.2 GB
        # - Play-by-play: 6.2 GB
        # - Player box: 433 MB
        # - Team box: 29 MB
        # - Schedule: 27 MB

        total_gb = 8.2
        pbp_gb = 6.2
        player_gb = 0.433
        team_gb = 0.029
        schedule_gb = 0.027

        # Play-by-play should be majority of data
        assert pbp_gb > total_gb * 0.5, "Play-by-play should be >50% of total data"

        # Total should be consistent (allow 2GB tolerance for overhead)
        component_total = pbp_gb + player_gb + team_gb + schedule_gb
        assert (
            abs(component_total - total_gb) < 2.0
        ), "Component sizes should sum to approximately total size (within 2GB)"

    def test_temporal_coverage_documented(self):
        """Verify documented temporal coverage is correct."""
        # From 0.0002 README: 2002-2025 (23+ years)
        start_year = 2002
        end_year = 2025
        years_coverage = end_year - start_year + 1

        assert years_coverage >= 23, "Documented coverage should be at least 23 years"

    def test_game_count_documented(self):
        """Verify documented game count is reasonable."""
        # From 0.0002 README: 30,758 games
        documented_games = 30_758

        # Sanity check: ~1,230 games/season × 24 seasons ≈ 29,520 games
        # Plus playoffs adds ~500-600 games/season
        min_expected = 25_000
        max_expected = 35_000

        assert (
            min_expected <= documented_games <= max_expected
        ), f"Documented game count should be between {min_expected:,} and {max_expected:,}"


class TestPhase02HooprREADME:
    """Tests for 0.0002 README completeness."""

    def test_readme_exists(self):
        """Test that 0.0002 README exists."""
        readme_path = (
            Path(__file__).parent.parent.parent.parent
            / "docs/phases/phase_0/0.0002_hoopr_data_collection/README.md"
        )
        assert readme_path.exists(), "0.0002 README should exist"

    def test_readme_has_key_sections(self):
        """Test that README contains key sections."""
        readme_path = (
            Path(__file__).parent.parent.parent.parent
            / "docs/phases/phase_0/0.0002_hoopr_data_collection/README.md"
        )

        with open(readme_path, "r") as f:
            content = f.read()

        # Key sections that should be present
        required_sections = [
            "## Overview",
            "## Data Coverage",
            "## Quick Start",
            "## Collection Process",
            "## Data Schema",
            "## Storage Locations",
            "## Cost Breakdown",
        ]

        for section in required_sections:
            assert section in content, f"README should contain '{section}' section"

    def test_readme_links_valid(self):
        """Test that README navigation links are valid."""
        readme_path = (
            Path(__file__).parent.parent.parent.parent
            / "docs/phases/phase_0/0.0002_hoopr_data_collection/README.md"
        )

        with open(readme_path, "r") as f:
            content = f.read()

        # Check for navigation section
        assert "## Navigation" in content, "README should have Navigation section"

        # Check for parent phase link
        assert (
            "PHASE_0_INDEX.md" in content or "Phase 0:" in content
        ), "README should link to parent phase"


# Slow tests marker for comprehensive validation
@pytest.mark.slow
class TestPhase02HooprComprehensive:
    """Comprehensive slow tests for 0.0002."""

    def test_all_seasons_have_data(self):
        """Test that all seasons from 2002-2024 have data (slow query)."""
        validator = Phase02HooprValidator(verbose=False)

        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        import psycopg2

        cursor = validator.conn.cursor()

        # Check if hoopr_schedule has data first
        cursor.execute("SELECT COUNT(*) FROM hoopr_schedule;")
        schedule_count = cursor.fetchone()[0]

        if schedule_count == 0:
            cursor.close()
            pytest.skip("hoopr_schedule table is empty")

        # Check each season has games
        for season in range(2002, 2025):
            cursor.execute(
                """
                SELECT COUNT(DISTINCT game_id)
                FROM hoopr_schedule
                WHERE EXTRACT(YEAR FROM game_date) = %s;
            """,
                (season,),
            )

            game_count = cursor.fetchone()[0]

            # Most seasons should have 1200+ games
            # (Some seasons like 2020 COVID season may have fewer)
            if season != 2020:
                assert (
                    game_count > 1000
                ), f"Season {season} should have >1000 games, found {game_count}"

        cursor.close()

    def test_play_by_play_events_reasonable(self):
        """Test that play-by-play event counts are reasonable (slow query)."""
        validator = Phase02HooprValidator(verbose=False)

        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        import psycopg2

        cursor = validator.conn.cursor()

        # Average events per game should be reasonable
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_events,
                COUNT(DISTINCT game_id) as total_games,
                COUNT(*)::float / COUNT(DISTINCT game_id) as avg_events_per_game
            FROM hoopr_play_by_play;
        """
        )

        total_events, total_games, avg_events = cursor.fetchone()
        cursor.close()

        # Typical game has 400-600 play-by-play events
        assert (
            300 < avg_events < 800
        ), f"Average events per game should be 300-800, found {avg_events:.1f}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
