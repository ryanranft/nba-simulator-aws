"""
System-Wide Constants

Centralized constants for paths, configurations, and settings.
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# AWS Configuration
S3_BUCKET = "nba-sim-raw-data-lake"
AWS_REGION = "us-east-1"

# Database Configuration
DATABASE_SCHEMA = "public"

# Data Sources
DATA_SOURCES = {
    "espn": "ESPN",
    "basketball_ref": "Basketball Reference",
    "hoopr": "hoopR",
    "nba_api": "NBA API",
    "kaggle": "Kaggle",
}

# Supported Seasons
SEASON_START_YEAR = 1946  # First NBA season
SEASON_END_YEAR = 2025  # Current season

# Game Constants
QUARTERS_PER_GAME = 4
MINUTES_PER_QUARTER = 12
SECONDS_PER_QUARTER = 720

# Table Names (most frequently used)
TABLES = {
    "games": "games",
    "players": "players",
    "teams": "teams",
    "play_by_play": "play_by_play",
    "box_score_players": "box_score_players",
    "box_score_teams": "box_score_teams",
    "temporal_events": "temporal_events",
    "hoopr_play_by_play": "hoopr_play_by_play",
}

# Status Constants
STATUS_SCHEDULED = "scheduled"
STATUS_IN_PROGRESS = "in_progress"
STATUS_FINAL = "final"
STATUS_POSTPONED = "postponed"
STATUS_CANCELLED = "cancelled"
