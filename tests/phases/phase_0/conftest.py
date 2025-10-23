#!/usr/bin/env python3
"""
Pytest configuration for Phase 0 tests.

Provides shared fixtures for all Phase 0 sub-phases including:
- S3 client and bucket configuration
- RDS database connection (optional)
- Common test utilities
"""

import pytest
import boto3
import psycopg2
import os


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--bucket",
        action="store",
        default="nba-sim-raw-data-lake",
        help="S3 bucket name to test",
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


# S3 Fixtures


@pytest.fixture(scope="module")
def s3_client():
    """Provide S3 client for tests."""
    return boto3.client("s3")


@pytest.fixture(scope="module")
def bucket_name():
    """Provide S3 bucket name."""
    return os.getenv("S3_BUCKET", "nba-sim-raw-data-lake")


# RDS Fixtures


@pytest.fixture(scope="module")
def rds_connection():
    """
    Provide RDS database connection.

    Returns None if RDS credentials not available.
    Tests should skip gracefully if connection is None.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("RDS_HOST"),
            database=os.getenv("RDS_DATABASE", "nba_simulator"),
            user=os.getenv("RDS_USER"),
            password=os.getenv("RDS_PASSWORD"),
        )
        yield conn
        conn.close()
    except Exception:
        # RDS not available - tests should skip
        yield None


@pytest.fixture(scope="module")
def rds_available(rds_connection):
    """Check if RDS connection is available."""
    return rds_connection is not None


# hoopR-specific Fixtures


@pytest.fixture(scope="module")
def hoopr_tables():
    """Provide list of hoopR table names."""
    return [
        "hoopr_play_by_play",
        "hoopr_player_box",
        "hoopr_team_box",
        "hoopr_schedule",
    ]


@pytest.fixture(scope="module")
def hoopr_s3_prefixes():
    """Provide list of hoopR S3 prefixes."""
    return [
        "hoopr_parquet/play_by_play/",
        "hoopr_parquet/player_box/",
        "hoopr_parquet/schedule/",
        "hoopr_parquet/team_box/",
        "hoopr_phase1/",
    ]
