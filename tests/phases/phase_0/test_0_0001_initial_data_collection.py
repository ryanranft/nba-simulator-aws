#!/usr/bin/env python3
"""
Pytest Suite for 0.0001: Initial Data Collection

Tests all validation components for 0.0001 to ensure S3 bucket
configuration and data upload meet specifications.

Usage:
    pytest test_phase_0_1.py -v
    pytest test_phase_0_1.py -v --bucket nba-sim-raw-data-lake
    pytest test_phase_0_1.py -v -k "bucket_config"  # Run only config tests
"""

import pytest
import boto3
import sys
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

# Add validators directory to path
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_0"
)
sys.path.insert(0, str(validators_path))

from validate_0_1_s3_bucket_config import S3BucketConfigValidator
from validate_0_1_upload_completeness import S3UploadCompletenessValidator


# Configuration
DEFAULT_BUCKET = "nba-sim-raw-data-lake"


@pytest.fixture(scope="session")
def bucket_name(request):
    """Get bucket name from command line or use default."""
    try:
        return request.config.getoption("--bucket")
    except (ValueError, AttributeError):
        # Fallback to default if option not available
        return DEFAULT_BUCKET


@pytest.fixture(scope="session")
def s3_client():
    """Create S3 client for tests."""
    try:
        return boto3.client("s3")
    except NoCredentialsError:
        pytest.skip("AWS credentials not configured")


@pytest.fixture(scope="session")
def bucket_config_validator(bucket_name):
    """Create bucket config validator instance."""
    return S3BucketConfigValidator(bucket_name=bucket_name)


@pytest.fixture(scope="session")
def upload_validator(bucket_name):
    """Create upload completeness validator instance."""
    return S3UploadCompletenessValidator(bucket_name=bucket_name, quick_mode=True)


# ============================================================================
# BUCKET CONFIGURATION TESTS
# ============================================================================


class TestS3BucketConfiguration:
    """Test S3 bucket configuration per 0.0001 specs."""

    def test_bucket_exists(self, bucket_config_validator):
        """Test that bucket exists and is accessible."""
        assert (
            bucket_config_validator.validate_bucket_exists()
        ), f"Bucket '{bucket_config_validator.bucket_name}' does not exist or is not accessible"

    def test_bucket_region(self, bucket_config_validator):
        """Test that bucket is in correct region (us-east-1)."""
        assert (
            bucket_config_validator.validate_region()
        ), "Bucket is not in the expected region (us-east-1)"

    def test_encryption_enabled(self, bucket_config_validator):
        """Test that encryption is enabled (SSE-S3)."""
        assert (
            bucket_config_validator.validate_encryption()
        ), "Bucket encryption is not enabled or incorrect algorithm"

    def test_public_access_blocked(self, bucket_config_validator):
        """Test that public access is fully blocked."""
        assert (
            bucket_config_validator.validate_public_access_block()
        ), "Public access is not fully blocked on bucket"

    def test_versioning_disabled(self, bucket_config_validator):
        """Test that versioning is disabled (cost optimization)."""
        assert (
            bucket_config_validator.validate_versioning_disabled()
        ), "Versioning should be disabled for cost optimization"

    def test_all_bucket_config_validations(self, bucket_config_validator):
        """Run all bucket configuration validations together."""
        all_passed, results = bucket_config_validator.run_all_validations()

        # Check individual results
        assert results.get("bucket_exists"), "Bucket does not exist"
        assert results.get("correct_region"), "Bucket in wrong region"
        assert results.get("encryption_enabled"), "Encryption not enabled"
        assert results.get("public_access_blocked"), "Public access not blocked"
        assert results.get("versioning_disabled"), "Versioning not disabled"

        # Overall pass
        assert (
            all_passed
        ), f"Some bucket configuration checks failed: {bucket_config_validator.failures}"


# ============================================================================
# UPLOAD COMPLETENESS TESTS
# ============================================================================


class TestS3UploadCompleteness:
    """Test S3 upload completeness per 0.0001 specs."""

    @pytest.mark.slow
    def test_total_file_count(self, upload_validator):
        """
        Test that total file count shows healthy growth from 0.0001 baseline.

        Uses ADCE tracking to validate:
        - No data loss (current >= initial)
        - Growth trajectory is positive
        - Excludes artifacts from count
        """
        assert (
            upload_validator.validate_total_file_count()
        ), f"Data validation failed. Failures: {upload_validator.failures}"

    @pytest.mark.slow
    def test_data_type_counts(self, upload_validator):
        """
        Test that each data type shows no data loss from 0.0001 baseline.

        Validates:
        - No data loss (current >= initial for all types)
        - Growth tracking per data type
        """
        assert (
            upload_validator.validate_data_type_counts()
        ), f"Data type validation failed. Failures: {upload_validator.failures}"

    def test_file_naming_patterns(self, upload_validator):
        """Test that file naming patterns are correct (sample)."""
        assert (
            upload_validator.validate_file_naming_patterns()
        ), f"File naming patterns incorrect. Failures: {upload_validator.failures}"

    @pytest.mark.slow
    def test_all_upload_validations(self, upload_validator):
        """Run all upload completeness validations together."""
        all_passed, results = upload_validator.run_all_validations()

        # Check individual results
        assert results.get("total_count_correct"), "Total file count incorrect"
        assert results.get("data_types_correct"), "Data type counts incorrect"
        assert results.get("naming_patterns_correct"), "File naming patterns incorrect"

        # Overall pass
        assert all_passed, f"Some upload checks failed: {upload_validator.failures}"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestPhase01Integration:
    """Integration tests for complete 0.0001 validation."""

    def test_phase_01_complete_validation(
        self, bucket_config_validator, upload_validator
    ):
        """
        Complete 0.0001 validation - all checks must pass.

        This is the comprehensive test that validates 0.0001 is fully complete.
        """
        # Run bucket config validations
        config_passed, config_results = bucket_config_validator.run_all_validations()

        # Run upload validations (quick mode for speed)
        upload_passed, upload_results = upload_validator.run_all_validations()

        # Both must pass
        assert (
            config_passed
        ), f"Bucket configuration failed: {bucket_config_validator.failures}"
        assert upload_passed, f"Upload validation failed: {upload_validator.failures}"

        print("\n" + "=" * 70)
        print("✅ PHASE 0.1 COMPLETE VALIDATION: PASSED")
        print("=" * 70)
        print("\nBucket Configuration:")
        for check, result in config_results.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")

        print("\nUpload Completeness:")
        for check, result in upload_results.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")
        print("=" * 70)


# ============================================================================
# PERFORMANCE/METADATA TESTS
# ============================================================================


class TestPhase01Metadata:
    """Tests for 0.0001 metadata and documentation accuracy."""

    def test_documented_file_count_matches_actual(
        self, bucket_name, s3_client, upload_validator
    ):
        """
        Verify actual S3 count shows growth from 0.0001 baseline.

        ADCE Tracking:
        - 0.0001 initial: 146,115 files
        - ADCE autonomous collection adds new data sources
        - Current count should be >= initial (no data loss)
        """
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)

        # Count excluding artifacts
        actual_count = 0
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/") and not upload_validator._is_excluded_prefix(
                    key
                ):
                    actual_count += 1

        # 0.0001 initial baseline
        initial_count = upload_validator.initial_total

        # Verify no data loss (growth expected from ADCE)
        assert actual_count >= initial_count, (
            f"Data loss detected! Current ({actual_count:,}) < Initial ({initial_count:,}). "
            f"Loss: {actual_count - initial_count:,} files"
        )

        # Log growth for visibility
        growth = actual_count - initial_count
        growth_pct = (growth / initial_count) * 100
        print(
            f"\n✓ Data growth validated: {actual_count:,} files (initial: {initial_count:,}, "
            f"growth: +{growth:,} [{growth_pct:+.1f}%])"
        )

    @pytest.mark.slow
    def test_storage_costs_within_budget(self, bucket_name, s3_client):
        """
        Verify storage size is within 0.0001 budget (~119 GB, $2.74/month).

        Alerts if costs are significantly above budget.
        """
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)

        total_bytes = sum(
            sum(
                obj["Size"]
                for obj in page.get("Contents", [])
                if not obj["Key"].endswith("/")
            )
            for page in pages
        )

        total_gb = total_bytes / (1024**3)
        estimated_monthly_cost = total_gb * 0.023  # S3 Standard pricing $0.023/GB

        # 0.0001 documented budget
        budgeted_cost = 2.74
        max_acceptable_cost = budgeted_cost * 1.20  # 20% over budget threshold

        assert estimated_monthly_cost <= max_acceptable_cost, (
            f"Storage costs (${estimated_monthly_cost:.2f}/month) exceed budget "
            f"(${budgeted_cost}/month). Current size: {total_gb:.2f} GB"
        )

        print(
            f"\n✓ Storage costs within budget: ${estimated_monthly_cost:.2f}/month ({total_gb:.2f} GB)"
        )


# ============================================================================
# TEST SUMMARY
# ============================================================================

if __name__ == "__main__":
    """Allow running as script."""
    import sys

    # Run with verbose output
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
