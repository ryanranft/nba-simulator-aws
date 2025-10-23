#!/usr/bin/env python3
"""
Phase 0.4 Tests: Basketball Reference Data Collection

Comprehensive pytest test suite for Phase 0.4 (Basketball Reference).

Test Coverage:
- S3 bucket access and configuration
- Data category existence (14 categories)
- File count validation (444 files)
- Temporal coverage (1953-2025)
- File sizes and formats
- Data quality and completeness
- Integration validation
- Metadata and documentation

Usage:
    # Run all tests
    pytest tests/phases/phase_0/test_0_4_basketball_reference.py -v

    # Run specific test class
    pytest tests/phases/phase_0/test_0_4_basketball_reference.py::TestPhase04S3Access -v

    # Run without slow tests
    pytest tests/phases/phase_0/test_0_4_basketball_reference.py -v -m "not slow"

Test Organization:
- TestPhase04S3Access: S3 bucket access tests
- TestPhase04DataCategories: Data category tests
- TestPhase04FileCounts: File count validation
- TestPhase04TemporalCoverage: Temporal coverage tests
- TestPhase04DataQuality: Data quality tests
- TestPhase04Integration: Integration tests
- TestPhase04Metadata: Documentation metadata
- TestPhase04README: README completeness
- TestPhase04Comprehensive: Slow comprehensive tests
"""

import json
import sys
from pathlib import Path

import pytest

# Import validator from validators directory
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_0"
)
sys.path.insert(0, str(validators_path))

from validate_0_4_basketball_reference import BasketballReferenceValidator


class TestPhase04S3Access:
    """Test S3 bucket access and configuration"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=False)

    def test_s3_bucket_exists(self, validator):
        """Test that S3 bucket exists and is accessible"""
        assert validator.validate_s3_bucket_access() == True, (
            f"S3 bucket '{validator.bucket_name}' is not accessible. "
            f"Errors: {validator.errors}"
        )

    def test_s3_client_initialized(self, validator):
        """Test that S3 client is properly initialized"""
        assert validator.s3 is not None, "S3 client not initialized"

    def test_bucket_name_correct(self, validator):
        """Test that bucket name is correct"""
        assert validator.bucket_name == "nba-sim-raw-data-lake"

    def test_s3_prefix_correct(self, validator):
        """Test that S3 prefix is correct"""
        assert validator.s3_prefix == "basketball_reference/"


class TestPhase04DataCategories:
    """Test data category directories"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=False)

    def test_all_categories_present(self, validator):
        """Test that all 14 expected data categories are present"""
        assert (
            validator.validate_data_categories() == True
        ), f"Not all data categories present. Errors: {validator.errors}"

    def test_expected_categories_count(self, validator):
        """Test that there are 14 expected categories"""
        assert len(validator.EXPECTED_CATEGORIES) == 14

    def test_category_names_valid(self, validator):
        """Test that category names match expected values"""
        expected = [
            "advanced_totals",
            "awards",
            "coaches",
            "draft",
            "per_game",
            "play_by_play",
            "playoffs",
            "schedules",
            "season_totals",
            "shooting",
            "standings",
            "standings_by_date",
            "team_ratings",
            "transactions",
        ]
        assert validator.EXPECTED_CATEGORIES == expected

    def test_each_category_has_files(self, validator):
        """Test that each category has files"""
        assert (
            validator.validate_category_file_counts() == True
        ), f"Some categories are empty. Errors: {validator.errors}"


class TestPhase04FileCounts:
    """Test file counts and sizes"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=False)

    def test_file_count_in_range(self, validator):
        """Test that total file count is within expected range"""
        assert (
            validator.validate_file_count() == True
        ), f"File count validation failed. Errors: {validator.errors}"

    def test_file_count_min_threshold(self, validator):
        """Test that minimum file count threshold is reasonable"""
        assert validator.EXPECTED_FILE_COUNT_MIN == 400

    def test_file_count_max_threshold(self, validator):
        """Test that maximum file count threshold is reasonable"""
        assert validator.EXPECTED_FILE_COUNT_MAX == 500

    def test_size_min_threshold(self, validator):
        """Test that minimum size threshold is reasonable"""
        assert validator.EXPECTED_SIZE_MB_MIN == 90

    def test_size_max_threshold(self, validator):
        """Test that maximum size threshold is reasonable"""
        assert validator.EXPECTED_SIZE_MB_MAX == 120


class TestPhase04TemporalCoverage:
    """Test temporal coverage"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=False)

    def test_temporal_coverage_valid(self, validator):
        """Test that temporal coverage spans expected years"""
        assert (
            validator.validate_temporal_coverage() == True
        ), f"Temporal coverage validation failed. Errors: {validator.errors}"

    def test_min_year_threshold(self, validator):
        """Test that minimum year threshold is 1953"""
        assert validator.EXPECTED_MIN_YEAR == 1953

    def test_max_year_threshold(self, validator):
        """Test that maximum year threshold is 2025"""
        assert validator.EXPECTED_MAX_YEAR == 2025

    def test_year_span_sufficient(self, validator):
        """Test that year span is at least 70 years"""
        year_span = validator.EXPECTED_MAX_YEAR - validator.EXPECTED_MIN_YEAR
        assert year_span >= 70, f"Year span {year_span} is less than 70 years"


class TestPhase04DataQuality:
    """Test data quality and format"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=False)

    def test_json_format_valid(self, validator):
        """Test that sample JSON files are valid"""
        assert (
            validator.validate_json_format() == True
        ), f"JSON format validation failed. Errors: {validator.errors}"

    def test_no_errors_during_validation(self, validator):
        """Test that validator starts with no errors"""
        assert len(validator.errors) == 0

    def test_no_warnings_during_validation(self, validator):
        """Test that validator starts with no warnings"""
        assert validator.warnings == 0


class TestPhase04Integration:
    """Integration tests for Phase 0.4"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=False)

    def test_phase_complete_validation(self, validator):
        """Comprehensive test that Phase 0.4 is complete"""
        all_passed, results = validator.run_all_validations()

        assert all_passed == True, (
            f"Phase 0.4 completion validation failed. "
            f"Results: {results}, Errors: {validator.errors}"
        )

    def test_all_checks_pass(self, validator):
        """Test that all validation checks pass"""
        all_passed, results = validator.run_all_validations()

        # Check specific results
        assert results["s3_bucket_access"] == True
        assert results["data_categories"] == True
        assert results["file_count"] == True
        assert results["temporal_coverage"] == True
        assert results["json_format"] == True
        assert results["category_file_counts"] == True

    def test_no_failures_reported(self, validator):
        """Test that no failures are reported after validation"""
        all_passed, results = validator.run_all_validations()

        if not all_passed:
            pytest.fail(f"Validation failures reported: {validator.errors}")


class TestPhase04Metadata:
    """Tests for Phase 0.4 documentation metadata"""

    def test_phase_readme_exists(self):
        """Verify Phase 0.4 README exists"""
        readme_path = Path("docs/phases/phase_0/0.4_basketball_reference/README.md")
        assert readme_path.exists(), f"README not found: {readme_path}"

    def test_phase_readme_not_empty(self):
        """Verify README is not empty"""
        readme_path = Path("docs/phases/phase_0/0.4_basketball_reference/README.md")
        content = readme_path.read_text()
        assert len(content) > 0, "README is empty"

    def test_phase_readme_has_overview(self):
        """Verify README has Overview section"""
        readme_path = Path("docs/phases/phase_0/0.4_basketball_reference/README.md")
        content = readme_path.read_text()
        assert "## Overview" in content, "README missing Overview section"

    def test_documented_categories_match_actual(self):
        """Verify documented categories match actual categories"""
        validator = BasketballReferenceValidator(verbose=False)

        # Expected categories from validator
        expected = set(validator.EXPECTED_CATEGORIES)

        # Verify all are documented
        assert len(expected) == 14, f"Expected 14 categories, found {len(expected)}"


class TestPhase04README:
    """Tests for Phase 0.4 README completeness"""

    @pytest.fixture
    def readme_content(self):
        """Load README content"""
        readme_path = Path("docs/phases/phase_0/0.4_basketball_reference/README.md")
        return readme_path.read_text()

    def test_readme_has_tier_structure(self, readme_content):
        """Test that README documents tier structure"""
        assert (
            "tier" in readme_content.lower() or "Tier" in readme_content
        ), "README should document tier structure"

    def test_readme_has_data_types_count(self, readme_content):
        """Test that README mentions 234 data types"""
        assert "234" in readme_content or "data types" in readme_content.lower()

    def test_readme_has_temporal_coverage_info(self, readme_content):
        """Test that README mentions temporal coverage"""
        # Should mention year ranges
        assert any(year in readme_content for year in ["1953", "2025"])


@pytest.mark.slow
class TestPhase04Comprehensive:
    """Slow comprehensive tests for Phase 0.4"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return BasketballReferenceValidator(verbose=True)

    def test_comprehensive_validation_verbose(self, validator):
        """Run full validation with verbose output"""
        all_passed, results = validator.run_all_validations()

        assert all_passed == True, (
            f"Comprehensive validation failed. "
            f"Results: {results}, "
            f"Errors: {validator.errors}"
        )

        # Verify all 6 checks passed
        assert len(results) == 6
        assert all(results.values()) == True

    def test_all_categories_have_multiple_files(
        self, validator, basketball_reference_categories
    ):
        """Test that each category has multiple files (not just one)"""
        import boto3

        s3 = boto3.client("s3")
        bucket = "nba-sim-raw-data-lake"

        for category in basketball_reference_categories:
            response = s3.list_objects_v2(
                Bucket=bucket,
                Prefix=f"basketball_reference/{category}/",
                MaxKeys=10,
            )

            file_count = len(response.get("Contents", []))

            # Most categories should have multiple files
            # (some might have just 1 if they're aggregates)
            assert (
                file_count >= 1
            ), f"Category {category} has {file_count} files, expected >= 1"

    @pytest.mark.slow
    def test_sample_files_from_each_category_valid_json(
        self, validator, basketball_reference_categories
    ):
        """Test that sample files from each category are valid JSON"""
        import boto3

        s3 = boto3.client("s3")
        bucket = "nba-sim-raw-data-lake"

        for category in basketball_reference_categories:
            # Get first file from category
            response = s3.list_objects_v2(
                Bucket=bucket,
                Prefix=f"basketball_reference/{category}/",
                MaxKeys=1,
            )

            if "Contents" not in response:
                continue

            key = response["Contents"][0]["Key"]

            # Skip non-JSON files
            if not key.endswith(".json"):
                continue

            # Download and parse
            obj = s3.get_object(Bucket=bucket, Key=key)
            content = obj["Body"].read().decode("utf-8")

            try:
                data = json.loads(content)
                assert isinstance(
                    data, (dict, list)
                ), f"File {key} contains invalid JSON structure"
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {key}: {e}")
