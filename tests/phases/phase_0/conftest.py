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


# Kaggle-specific Fixtures


@pytest.fixture(scope="module")
def kaggle_db_path():
    """Provide path to Kaggle SQLite database."""
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[3]
    return project_root / "data" / "kaggle" / "nba.sqlite"


@pytest.fixture(scope="module")
def kaggle_db_connection(kaggle_db_path):
    """
    Provide Kaggle SQLite database connection.

    Returns None if database file not available.
    Tests should skip gracefully if connection is None.
    """
    import sqlite3

    if not kaggle_db_path.exists():
        # Database file not found - tests should skip
        yield None
        return

    try:
        conn = sqlite3.connect(kaggle_db_path)
        yield conn
        conn.close()
    except Exception:
        # Database connection failed - tests should skip
        yield None


@pytest.fixture(scope="module")
def kaggle_tables():
    """Provide list of Kaggle database table names (updated schema, 16 tables)."""
    return [
        "game",
        "team",
        "player",
        "play_by_play",
        "game_info",
        "game_summary",
        "line_score",
        "inactive_players",
        "officials",
        "other_stats",
        "draft_history",
        "draft_combine_stats",
        "common_player_info",
        "team_details",
        "team_history",
        "team_info_common",
    ]


# Basketball Reference-specific Fixtures


@pytest.fixture(scope="module")
def basketball_reference_categories():
    """Provide list of Basketball Reference data category names."""
    return [
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


@pytest.fixture(scope="module")
def basketball_reference_s3_prefix():
    """Provide Basketball Reference S3 prefix."""
    return "basketball_reference/"


@pytest.fixture(scope="module")
def basketball_reference_expected_file_count():
    """Provide expected Basketball Reference file count range."""
    return {"min": 400, "max": 500}


@pytest.fixture(scope="module")
def basketball_reference_expected_years():
    """Provide expected Basketball Reference year range."""
    return {"min": 1953, "max": 2025}
