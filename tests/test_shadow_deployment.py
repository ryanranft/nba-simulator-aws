#!/usr/bin/env python3
"""
Tests for shadow_deployment
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from concurrent.futures import TimeoutError as FuturesTimeoutError
import time

# Add module directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts/deployment"))

# Import from the module
from shadow_deployment import (
    DeploymentStatus,
    ComparisonResult,
    ShadowResult,
    ShadowMetrics,
)


# Fixtures


@pytest.fixture
def sample_timestamp():
    """Fixture for consistent timestamp"""
    return datetime(2024, 1, 15, 12, 0, 0)


@pytest.fixture
def sample_shadow_result(sample_timestamp):
    """Fixture for a successful shadow result"""
    return ShadowResult(
        deployment_id="test-123",
        timestamp=sample_timestamp,
        primary_output={"prediction": 0.85},
        shadow_output={"prediction": 0.85},
        primary_duration_ms=100.5,
        shadow_duration_ms=105.2,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
        error_message=None,
        metadata={"model_version": "v1.0"},
    )


@pytest.fixture
def mismatch_shadow_result(sample_timestamp):
    """Fixture for a mismatched shadow result"""
    return ShadowResult(
        deployment_id="test-456",
        timestamp=sample_timestamp,
        primary_output={"prediction": 0.85},
        shadow_output={"prediction": 0.75},
        primary_duration_ms=100.5,
        shadow_duration_ms=105.2,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MISMATCH,
        error_message=None,
        metadata={},
    )


@pytest.fixture
def error_shadow_result(sample_timestamp):
    """Fixture for an error shadow result"""
    return ShadowResult(
        deployment_id="test-789",
        timestamp=sample_timestamp,
        primary_output={"prediction": 0.85},
        shadow_output=None,
        primary_duration_ms=100.5,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.FAILURE,
        comparison_result=ComparisonResult.ERROR,
        error_message="Shadow model failed to load",
        metadata={},
    )


@pytest.fixture
def shadow_metrics():
    """Fixture for shadow metrics"""
    return ShadowMetrics()


# Tests for DeploymentStatus Enum


def test_deployment_status_enum_values():
    """Test that DeploymentStatus enum has correct values"""
    assert DeploymentStatus.SUCCESS.value == "success"
    assert DeploymentStatus.FAILURE.value == "failure"
    assert DeploymentStatus.TIMEOUT.value == "timeout"
    assert DeploymentStatus.PARTIAL.value == "partial"


def test_deployment_status_enum_members():
    """Test that DeploymentStatus enum has all expected members"""
    expected_members = {"SUCCESS", "FAILURE", "TIMEOUT", "PARTIAL"}
    actual_members = {member.name for member in DeploymentStatus}
    assert actual_members == expected_members


# Tests for ComparisonResult Enum


def test_comparison_result_enum_values():
    """Test that ComparisonResult enum has correct values"""
    assert ComparisonResult.MATCH.value == "match"
    assert ComparisonResult.MISMATCH.value == "mismatch"
    assert ComparisonResult.ERROR.value == "error"


def test_comparison_result_enum_members():
    """Test that ComparisonResult enum has all expected members"""
    expected_members = {"MATCH", "MISMATCH", "ERROR"}
    actual_members = {member.name for member in ComparisonResult}
    assert actual_members == expected_members


# Tests for ShadowResult


def test_shadow_result_initialization_with_all_fields(sample_timestamp):
    """Test ShadowResult initialization with all fields"""
    result = ShadowResult(
        deployment_id="test-001",
        timestamp=sample_timestamp,
        primary_output={"value": 1},
        shadow_output={"value": 2},
        primary_duration_ms=50.0,
        shadow_duration_ms=60.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
        error_message="test error",
        metadata={"key": "value"},
    )

    assert result.deployment_id == "test-001"
    assert result.timestamp == sample_timestamp
    assert result.primary_output == {"value": 1}
    assert result.shadow_output == {"value": 2}
    assert result.primary_duration_ms == 50.0
    assert result.shadow_duration_ms == 60.0
    assert result.primary_status == DeploymentStatus.SUCCESS
    assert result.shadow_status == DeploymentStatus.SUCCESS
    assert result.comparison_result == ComparisonResult.MATCH
    assert result.error_message == "test error"
    assert result.metadata == {"key": "value"}


def test_shadow_result_initialization_with_defaults(sample_timestamp):
    """Test ShadowResult initialization with default values"""
    result = ShadowResult(
        deployment_id="test-002",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output=None,
        primary_duration_ms=0.0,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.FAILURE,
        shadow_status=DeploymentStatus.FAILURE,
        comparison_result=ComparisonResult.ERROR,
    )

    assert result.error_message is None
    assert result.metadata == {}


def test_shadow_result_to_dict_complete(sample_shadow_result):
    """Test ShadowResult.to_dict() with complete data"""
    result_dict = sample_shadow_result.to_dict()

    assert result_dict["deployment_id"] == "test-123"
    assert result_dict["timestamp"] == "2024-01-15T12:00:00"
    assert result_dict["primary_output"] == {"prediction": 0.85}
    assert result_dict["shadow_output"] == {"prediction": 0.85}
    assert result_dict["primary_duration_ms"] == 100.5
    assert result_dict["shadow_duration_ms"] == 105.2
    assert result_dict["primary_status"] == "success"
    assert result_dict["shadow_status"] == "success"
    assert result_dict["comparison_result"] == "match"
    assert result_dict["error_message"] is None
    assert result_dict["metadata"] == {"model_version": "v1.0"}


def test_shadow_result_to_dict_with_none_values(sample_timestamp):
    """Test ShadowResult.to_dict() with None values"""
    result = ShadowResult(
        deployment_id="test-003",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output=None,
        primary_duration_ms=0.0,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.TIMEOUT,
        shadow_status=DeploymentStatus.TIMEOUT,
        comparison_result=ComparisonResult.ERROR,
    )

    result_dict = result.to_dict()

    assert result_dict["primary_output"] is None
    assert result_dict["shadow_output"] is None
    assert result_dict["error_message"] is None
    assert result_dict["metadata"] == {}


def test_shadow_result_to_dict_with_error_message(error_shadow_result):
    """Test ShadowResult.to_dict() with error message"""
    result_dict = error_shadow_result.to_dict()

    assert result_dict["error_message"] == "Shadow model failed to load"
    assert result_dict["shadow_status"] == "failure"
    assert result_dict["comparison_result"] == "error"


def test_shadow_result_to_dict_serializable(sample_shadow_result):
    """Test that ShadowResult.to_dict() returns JSON-serializable data"""
    import json

    result_dict = sample_shadow_result.to_dict()

    # Should not raise exception
    json_str = json.dumps(result_dict)
    assert isinstance(json_str, str)
    assert len(json_str) > 0


# Tests for ShadowMetrics


def test_shadow_metrics_initialization():
    """Test ShadowMetrics initialization with default values"""
    metrics = ShadowMetrics()

    assert metrics.total_requests == 0
    assert metrics.successful_comparisons == 0
    assert metrics.mismatches == 0
    assert metrics.primary_errors == 0
    assert metrics.shadow_errors == 0
    assert metrics.timeouts == 0
    assert metrics.avg_primary_duration_ms == 0.0
    assert metrics.avg_shadow_duration_ms == 0.0
    assert metrics.match_rate == 0.0


def test_shadow_metrics_update_with_successful_match(
    shadow_metrics, sample_shadow_result
):
    """Test ShadowMetrics.update() with successful match"""
    shadow_metrics.update(sample_shadow_result)

    assert shadow_metrics.total_requests == 1
    assert shadow_metrics.successful_comparisons == 1
    assert shadow_metrics.mismatches == 0
    assert shadow_metrics.primary_errors == 0
    assert shadow_metrics.shadow_errors == 0
    assert shadow_metrics.timeouts == 0
    assert shadow_metrics.avg_primary_duration_ms == 100.5
    assert shadow_metrics.avg_shadow_duration_ms == 105.2


def test_shadow_metrics_update_with_mismatch(shadow_metrics, mismatch_shadow_result):
    """Test ShadowMetrics.update() with mismatch"""
    shadow_metrics.update(mismatch_shadow_result)

    assert shadow_metrics.total_requests == 1
    assert shadow_metrics.successful_comparisons == 0
    assert shadow_metrics.mismatches == 1
    assert shadow_metrics.primary_errors == 0
    assert shadow_metrics.shadow_errors == 0


def test_shadow_metrics_update_with_error(shadow_metrics, error_shadow_result):
    """Test ShadowMetrics.update() with error"""
    shadow_metrics.update(error_shadow_result)

    assert shadow_metrics.total_requests == 1
    assert shadow_metrics.successful_comparisons == 0
    assert shadow_metrics.mismatches == 0
    assert shadow_metrics.primary_errors == 0
    assert shadow_metrics.shadow_errors == 1


def test_shadow_metrics_update_with_primary_error(shadow_metrics, sample_timestamp):
    """Test ShadowMetrics.update() with primary error"""
    result = ShadowResult(
        deployment_id="test-primary-error",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output={"prediction": 0.85},
        primary_duration_ms=0.0,
        shadow_duration_ms=105.2,
        primary_status=DeploymentStatus.FAILURE,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.ERROR,
    )

    shadow_metrics.update(result)

    assert shadow_metrics.primary_errors == 1
    assert shadow_metrics.shadow_errors == 0


def test_shadow_metrics_update_with_timeout(shadow_metrics, sample_timestamp):
    """Test ShadowMetrics.update() with timeout"""
    result = ShadowResult(
        deployment_id="test-timeout",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output=None,
        primary_duration_ms=0.0,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.TIMEOUT,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.ERROR,
    )

    shadow_metrics.update(result)

    assert shadow_metrics.timeouts == 1


def test_shadow_metrics_update_with_shadow_timeout(shadow_metrics, sample_timestamp):
    """Test ShadowMetrics.update() with shadow timeout"""
    result = ShadowResult(
        deployment_id="test-shadow-timeout",
        timestamp=sample_timestamp,
        primary_output={"prediction": 0.85},
        shadow_output=None,
        primary_duration_ms=100.0,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.TIMEOUT,
        comparison_result=ComparisonResult.ERROR,
    )

    shadow_metrics.update(result)

    assert shadow_metrics.timeouts == 1


def test_shadow_metrics_update_multiple_results(
    shadow_metrics, sample_shadow_result, mismatch_shadow_result, error_shadow_result
):
    """Test ShadowMetrics.update() with multiple results"""
    shadow_metrics.update(sample_shadow_result)
    shadow_metrics.update(mismatch_shadow_result)
    shadow_metrics.update(error_shadow_result)

    assert shadow_metrics.total_requests == 3
    assert shadow_metrics.successful_comparisons == 1
    assert shadow_metrics.mismatches == 1
    assert shadow_metrics.shadow_errors == 1


def test_shadow_metrics_average_duration_calculation(shadow_metrics, sample_timestamp):
    """Test ShadowMetrics average duration calculation"""
    result1 = ShadowResult(
        deployment_id="test-1",
        timestamp=sample_timestamp,
        primary_output={"value": 1},
        shadow_output={"value": 1},
        primary_duration_ms=100.0,
        shadow_duration_ms=200.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
    )

    result2 = ShadowResult(
        deployment_id="test-2",
        timestamp=sample_timestamp,
        primary_output={"value": 2},
        shadow_output={"value": 2},
        primary_duration_ms=200.0,
        shadow_duration_ms=300.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
    )

    shadow_metrics.update(result1)
    shadow_metrics.update(result2)

    assert shadow_metrics.avg_primary_duration_ms == 150.0
    assert shadow_metrics.avg_shadow_duration_ms == 250.0


def test_shadow_metrics_average_duration_with_zero_initial(
    shadow_metrics, sample_shadow_result
):
    """Test ShadowMetrics average duration calculation from zero"""
    shadow_metrics.update(sample_shadow_result)

    assert shadow_metrics.avg_primary_duration_ms == 100.5
    assert shadow_metrics.avg_shadow_duration_ms == 105.2


def test_shadow_metrics_multiple_updates_preserves_accuracy(
    shadow_metrics, sample_timestamp
):
    """Test that multiple updates maintain calculation accuracy"""
    for i in range(10):
        result = ShadowResult(
            deployment_id=f"test-{i}",
            timestamp=sample_timestamp,
            primary_output={"value": i},
            shadow_output={"value": i},
            primary_duration_ms=float(i * 10),
            shadow_duration_ms=float(i * 20),
            primary_status=DeploymentStatus.SUCCESS,
            shadow_status=DeploymentStatus.SUCCESS,
            comparison_result=ComparisonResult.MATCH,
        )
        shadow_metrics.update(result)

    assert shadow_metrics.total_requests == 10
    assert shadow_metrics.successful_comparisons == 10
    # Average of 0, 10, 20, ..., 90 is 45
    assert shadow_metrics.avg_primary_duration_ms == 45.0
    # Average of 0, 20, 40, ..., 180 is 90
    assert shadow_metrics.avg_shadow_duration_ms == 90.0


@pytest.mark.parametrize(
    "primary_status,shadow_status,expected_primary_errors,expected_shadow_errors",
    [
        (DeploymentStatus.SUCCESS, DeploymentStatus.SUCCESS, 0, 0),
        (DeploymentStatus.FAILURE, DeploymentStatus.SUCCESS, 1, 0),
        (DeploymentStatus.SUCCESS, DeploymentStatus.FAILURE, 0, 1),
        (DeploymentStatus.FAILURE, DeploymentStatus.FAILURE, 1, 1),
        (DeploymentStatus.TIMEOUT, DeploymentStatus.SUCCESS, 0, 0),
        (DeploymentStatus.SUCCESS, DeploymentStatus.TIMEOUT, 0, 0),
    ],
)
def test_shadow_metrics_error_counting(
    shadow_metrics,
    sample_timestamp,
    primary_status,
    shadow_status,
    expected_primary_errors,
    expected_shadow_errors,
):
    """Test ShadowMetrics error counting with various status combinations"""
    result = ShadowResult(
        deployment_id="test-error-count",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output=None,
        primary_duration_ms=0.0,
        shadow_duration_ms=0.0,
        primary_status=primary_status,
        shadow_status=shadow_status,
        comparison_result=ComparisonResult.ERROR,
    )

    shadow_metrics.update(result)

    assert shadow_metrics.primary_errors == expected_primary_errors
    assert shadow_metrics.shadow_errors == expected_shadow_errors


@pytest.mark.parametrize(
    "comparison_result,expected_matches,expected_mismatches",
    [
        (ComparisonResult.MATCH, 1, 0),
        (ComparisonResult.MISMATCH, 0, 1),
        (ComparisonResult.ERROR, 0, 0),
    ],
)
def test_shadow_metrics_comparison_counting(
    shadow_metrics,
    sample_timestamp,
    comparison_result,
    expected_matches,
    expected_mismatches,
):
    """Test ShadowMetrics comparison result counting"""
    result = ShadowResult(
        deployment_id="test-comparison",
        timestamp=sample_timestamp,
        primary_output={"value": 1},
        shadow_output={"value": 2},
        primary_duration_ms=100.0,
        shadow_duration_ms=100.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=comparison_result,
    )

    shadow_metrics.update(result)

    assert shadow_metrics.successful_comparisons == expected_matches
    assert shadow_metrics.mismatches == expected_mismatches


def test_shadow_result_with_complex_output_types(sample_timestamp):
    """Test ShadowResult with complex output types"""
    complex_output = {
        "predictions": [0.1, 0.2, 0.3],
        "metadata": {"model": "v2", "confidence": 0.95},
        "nested": {"deep": {"value": 42}},
    }

    result = ShadowResult(
        deployment_id="test-complex",
        timestamp=sample_timestamp,
        primary_output=complex_output,
        shadow_output=complex_output.copy(),
        primary_duration_ms=150.0,
        shadow_duration_ms=160.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
    )

    assert result.primary_output == complex_output
    assert result.shadow_output == complex_output


def test_shadow_result_with_large_metadata(sample_timestamp):
    """Test ShadowResult with large metadata dictionary"""
    large_metadata = {f"key_{i}": f"value_{i}" for i in range(100)}

    result = ShadowResult(
        deployment_id="test-large-metadata",
        timestamp=sample_timestamp,
        primary_output={"value": 1},
        shadow_output={"value": 1},
        primary_duration_ms=100.0,
        shadow_duration_ms=100.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
        metadata=large_metadata,
    )

    assert len(result.metadata) == 100
    assert result.metadata["key_0"] == "value_0"
    assert result.metadata["key_99"] == "value_99"


def test_shadow_metrics_with_zero_requests():
    """Test ShadowMetrics behavior with zero requests"""
    metrics = ShadowMetrics()

    assert metrics.total_requests == 0
    assert metrics.match_rate == 0.0
    assert metrics.avg_primary_duration_ms == 0.0
    assert metrics.avg_shadow_duration_ms == 0.0


def test_shadow_result_timestamp_preservation(sample_timestamp):
    """Test that timestamp is preserved correctly in ShadowResult"""
    result = ShadowResult(
        deployment_id="test-timestamp",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output=None,
        primary_duration_ms=0.0,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
    )

    assert result.timestamp == sample_timestamp
    assert result.timestamp.year == 2024
    assert result.timestamp.month == 1
    assert result.timestamp.day == 15


def test_shadow_result_to_dict_timestamp_format(sample_timestamp):
    """Test that timestamp is formatted correctly in to_dict()"""
    result = ShadowResult(
        deployment_id="test-timestamp-format",
        timestamp=sample_timestamp,
        primary_output=None,
        shadow_output=None,
        primary_duration_ms=0.0,
        shadow_duration_ms=0.0,
        primary_status=DeploymentStatus.SUCCESS,
        shadow_status=DeploymentStatus.SUCCESS,
        comparison_result=ComparisonResult.MATCH,
    )

    result_dict = result.to_dict()
    assert result_dict["timestamp"] == "2024-01-15T12:00:00"
    assert isinstance(result_dict["timestamp"], str)
