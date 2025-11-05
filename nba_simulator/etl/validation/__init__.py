"""
ETL Validation Module

Provides data validation for all ETL pipelines.

Components:
- BaseValidator: Abstract base class for validators
- GameValidator: Validates game data
- PlayByPlayValidator: Validates play-by-play data
- BoxScoreValidator: Validates box score data
- ValidationReport: Validation results container
- Convenience functions for quick validation
"""

from .validators import (
    # Base classes
    BaseValidator,
    ValidationLevel,
    ValidationResult,
    ValidationReport,
    DataSource,
    # Specific validators
    GameValidator,
    PlayByPlayValidator,
    BoxScoreValidator,
    # Convenience functions
    validate_game,
    validate_play_by_play,
    validate_box_score,
    validate_batch,
)

__all__ = [
    # Base classes
    "BaseValidator",
    "ValidationLevel",
    "ValidationResult",
    "ValidationReport",
    "DataSource",
    # Validators
    "GameValidator",
    "PlayByPlayValidator",
    "BoxScoreValidator",
    # Functions
    "validate_game",
    "validate_play_by_play",
    "validate_box_score",
    "validate_batch",
]
