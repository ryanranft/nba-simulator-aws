"""
Shared fixtures for Phase tests.
"""

import pytest
import boto3
import os


@pytest.fixture(scope="module")
def s3_client():
    """Provide S3 client for tests."""
    return boto3.client("s3")


@pytest.fixture(scope="module")
def bucket_name():
    """Provide S3 bucket name."""
    return os.getenv("S3_BUCKET", "nba-sim-raw-data-lake")
