"""
NBA Simulator AWS - Root pytest Configuration
Shared fixtures and test utilities for all test suites
"""

import pytest
import os
from pathlib import Path


# Project Root
@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


# AWS Configuration Fixtures
@pytest.fixture(scope="session")
def aws_region():
    """Default AWS region for tests."""
    return os.getenv("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def s3_bucket_name():
    """S3 bucket name for tests."""
    return os.getenv("S3_BUCKET", "nba-sim-raw-data-lake")


# Database Configuration Fixtures
@pytest.fixture(scope="session")
def rds_config():
    """RDS database configuration for integration tests."""
    return {
        "host": os.getenv("RDS_HOST", "localhost"),
        "port": int(os.getenv("RDS_PORT", "5432")),
        "database": os.getenv("RDS_DATABASE", "nba_simulator"),
        "username": os.getenv("RDS_USERNAME", "postgres"),
        "password": os.getenv("RDS_PASSWORD", ""),
    }


# Test Data Fixtures
@pytest.fixture(scope="session")
def sample_game_id():
    """Sample game ID for testing."""
    return "401584876"  # Known game in test data


@pytest.fixture(scope="session")
def sample_season():
    """Sample season for testing."""
    return "2023-24"


# Skip Markers for Integration Tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring AWS resources"
    )
    config.addinivalue_line("markers", "slow: Tests that take >1 second to run")


# Skip integration tests if AWS credentials not configured
def pytest_collection_modifyitems(config, items):
    """Automatically skip integration tests if AWS not configured."""
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        skip_integration = pytest.mark.skip(reason="AWS credentials not configured")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
