"""
Utilities Module

Common utilities for logging, constants, and helper functions.
"""

from .logging import setup_logging, logger
from .constants import *
from .raw_data_helpers import (
    # Game data extraction
    get_game_score,
    get_team_info,
    get_game_info,
    get_play_summary,
    get_source_data,
    # Metadata extraction
    get_collection_info,
    get_validation_status,
    get_migration_info,
    # File validation extraction
    get_file_validation_info,
    get_game_reference,
    # Composite functions
    get_complete_game_data,
    get_game_summary_string,
    # JSONB path navigation
    navigate_jsonb_path,
    check_jsonb_path_exists,
    extract_all_jsonb_keys,
    # Data quality helpers
    validate_required_fields,
    check_data_completeness,
)

__all__ = [
    "setup_logging",
    "logger",
    # Constants
    "DEFAULT_DB_PORT",
    "DEFAULT_DB_NAME",
    "DEFAULT_S3_BUCKET",
    "DEFAULT_S3_REGION",
    "NBA_FOUNDING_YEAR",
    "CURRENT_SEASON",
    "DATA_SOURCES",
    "TABLES",
    "MAX_FILE_SIZE_MB",
    "MAX_JSON_DEPTH",
    "DEFAULT_BATCH_SIZE",
    "MAX_WORKERS",
    # Raw data helpers
    "get_game_score",
    "get_team_info",
    "get_game_info",
    "get_play_summary",
    "get_source_data",
    "get_collection_info",
    "get_validation_status",
    "get_migration_info",
    "get_file_validation_info",
    "get_game_reference",
    "get_complete_game_data",
    "get_game_summary_string",
    "navigate_jsonb_path",
    "check_jsonb_path_exists",
    "extract_all_jsonb_keys",
    "validate_required_fields",
    "check_data_completeness",
]
