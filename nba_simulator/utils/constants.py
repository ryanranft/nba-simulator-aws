"""
System-wide Constants

Centralized constants for the NBA Simulator system.
"""

# Database
DEFAULT_DB_PORT = 5432
DEFAULT_DB_NAME = "nba_simulator"

# S3
DEFAULT_S3_BUCKET = "nba-sim-raw-data-lake"
DEFAULT_S3_REGION = "us-east-1"

# NBA
NBA_FOUNDING_YEAR = 1946
CURRENT_SEASON = 2024  # 2024-25 season

# Data Sources
DATA_SOURCES = ["espn", "basketball_reference", "nba_api", "hoopr", "betting"]

# Table Names
TABLES = {
    "games": "games",
    "play_by_play": "play_by_play",
    "box_scores": "box_scores",
    "players": "players",
    "teams": "teams",
    "box_score_snapshots": "box_score_snapshots",
}

# File Limits
MAX_FILE_SIZE_MB = 100
MAX_JSON_DEPTH = 10

# Performance
DEFAULT_BATCH_SIZE = 1000
MAX_WORKERS = 10

