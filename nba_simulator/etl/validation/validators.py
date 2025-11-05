"""
Data Validators for ETL Pipeline

Provides comprehensive validation for NBA data from multiple sources.
Ensures data quality before loading into database.

Migrated from: scripts/validation/ (various validators)
Enhanced with: Source-specific validation, multi-schema support
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from nba_simulator.utils import logger


class ValidationLevel(Enum):
    """Validation severity levels"""

    INFO = "info"  # Informational, doesn't block
    WARNING = "warning"  # Warning, logs but continues
    ERROR = "error"  # Error, blocks data loading
    CRITICAL = "critical"  # Critical error, stops pipeline


class DataSource(Enum):
    """Supported data sources"""

    ESPN = "espn"
    BASKETBALL_REFERENCE = "basketball_reference"
    NBA_API = "nba_api"
    HOOPR = "hoopr"
    BETTING = "betting"


@dataclass
class ValidationResult:
    """Result of a validation check"""

    is_valid: bool
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    expected: Any = None
    actual: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation of validation result"""
        msg = f"[{self.level.value.upper()}] {self.message}"
        if self.field:
            msg += f" | Field: {self.field}"
        if self.expected is not None:
            msg += f" | Expected: {self.expected}, Got: {self.actual}"
        return msg


@dataclass
class ValidationReport:
    """Collection of validation results"""

    results: List[ValidationResult] = field(default_factory=list)
    source: Optional[DataSource] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if all validations passed (no errors or critical)"""
        return not any(
            r.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
            for r in self.results
        )

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return any(r.level == ValidationLevel.WARNING for r in self.results)

    @property
    def error_count(self) -> int:
        """Count of error-level validations"""
        return sum(
            1
            for r in self.results
            if r.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
        )

    @property
    def warning_count(self) -> int:
        """Count of warning-level validations"""
        return sum(1 for r in self.results if r.level == ValidationLevel.WARNING)

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result"""
        self.results.append(result)

    def log_results(self) -> None:
        """Log all validation results"""
        if not self.results:
            logger.info("No validation results to log")
            return

        logger.info(
            f"Validation Report - {self.source.value if self.source else 'Unknown'}"
        )
        logger.info(
            f"Valid: {self.is_valid} | Errors: {self.error_count} | Warnings: {self.warning_count}"
        )

        for result in self.results:
            if result.level == ValidationLevel.CRITICAL:
                logger.error(str(result))
            elif result.level == ValidationLevel.ERROR:
                logger.error(str(result))
            elif result.level == ValidationLevel.WARNING:
                logger.warning(str(result))
            else:
                logger.info(str(result))


class BaseValidator:
    """
    Base validator class for all data validators.

    Provides common validation patterns and utilities.
    """

    def __init__(self, source: Optional[DataSource] = None):
        """
        Initialize validator.

        Args:
            source: Data source being validated
        """
        self.source = source
        self.report = ValidationReport(source=source)

    def validate(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Main validation entry point. Override in subclasses.

        Args:
            data: Data to validate

        Returns:
            ValidationReport with results
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def _add_result(
        self,
        is_valid: bool,
        level: ValidationLevel,
        message: str,
        field: Optional[str] = None,
        expected: Any = None,
        actual: Any = None,
        **metadata,
    ) -> None:
        """Helper to add validation result"""
        result = ValidationResult(
            is_valid=is_valid,
            level=level,
            message=message,
            field=field,
            expected=expected,
            actual=actual,
            metadata=metadata,
        )
        self.report.add_result(result)

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> bool:
        """
        Validate that all required fields are present.

        Args:
            data: Data dictionary to check
            required_fields: List of required field names

        Returns:
            True if all fields present
        """
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Missing required fields: {', '.join(missing_fields)}",
                expected=required_fields,
                actual=list(data.keys()),
            )
            return False

        return True

    def validate_field_type(
        self,
        data: Dict[str, Any],
        field: str,
        expected_type: type,
        required: bool = True,
    ) -> bool:
        """
        Validate field has expected type.

        Args:
            data: Data dictionary
            field: Field name to check
            expected_type: Expected Python type
            required: Whether field is required

        Returns:
            True if validation passes
        """
        if field not in data:
            if required:
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Required field missing",
                    field=field,
                )
                return False
            return True

        value = data[field]
        if not isinstance(value, expected_type):
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid type",
                field=field,
                expected=expected_type.__name__,
                actual=type(value).__name__,
            )
            return False

        return True

    def validate_range(
        self,
        value: float,
        field: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> bool:
        """
        Validate numeric value is within range.

        Args:
            value: Value to check
            field: Field name
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            True if in range
        """
        if min_val is not None and value < min_val:
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Value below minimum",
                field=field,
                expected=f">= {min_val}",
                actual=value,
            )
            return False

        if max_val is not None and value > max_val:
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Value above maximum",
                field=field,
                expected=f"<= {max_val}",
                actual=value,
            )
            return False

        return True


class GameValidator(BaseValidator):
    """
    Validator for game data.

    Validates game records across all sources.
    """

    REQUIRED_FIELDS = ["game_id", "game_date", "home_team", "away_team", "season"]

    def validate(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Validate game data.

        Args:
            data: Game data dictionary

        Returns:
            ValidationReport with results
        """
        # Reset report
        self.report = ValidationReport(source=self.source)

        # Required fields
        if not self.validate_required_fields(data, self.REQUIRED_FIELDS):
            return self.report

        # Game ID format
        self._validate_game_id(data["game_id"])

        # Date validation
        self._validate_date(data["game_date"])

        # Team codes
        self._validate_team_code(data["home_team"])
        self._validate_team_code(data["away_team"])

        # Season format
        self._validate_season(data["season"])

        # Score validation (if present)
        if "home_score" in data and "away_score" in data:
            self._validate_scores(data["home_score"], data["away_score"])

        return self.report

    def _validate_game_id(self, game_id: str) -> None:
        """Validate game ID format"""
        if not isinstance(game_id, str):
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Game ID must be string",
                field="game_id",
                actual=type(game_id).__name__,
            )
            return

        if not game_id:
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Game ID cannot be empty",
                field="game_id",
            )

    def _validate_date(self, date_value: Any) -> None:
        """Validate date format"""
        # Accept datetime, date, or ISO string
        valid_types = (datetime, str)
        if not isinstance(date_value, valid_types):
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Invalid date format",
                field="game_date",
                actual=type(date_value).__name__,
            )

    def _validate_team_code(self, team_code: str) -> None:
        """Validate team code"""
        if not isinstance(team_code, str):
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Team code must be string",
                field="team_code",
                actual=type(team_code).__name__,
            )
            return

        # Team codes should be 2-3 uppercase letters
        if not (2 <= len(team_code) <= 3):
            self._add_result(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Team code should be 2-3 characters",
                field="team_code",
                actual=team_code,
            )

    def _validate_season(self, season: Any) -> None:
        """Validate season format"""
        # Season should be integer (e.g., 2024 for 2024-25 season)
        if isinstance(season, int):
            if not (1946 <= season <= 2100):  # NBA founded 1946
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="Season year out of valid range",
                    field="season",
                    expected="1946-2100",
                    actual=season,
                )
        else:
            self._add_result(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Season must be integer",
                field="season",
                actual=type(season).__name__,
            )

    def _validate_scores(self, home_score: Any, away_score: Any) -> None:
        """Validate game scores"""
        for score, label in [(home_score, "home_score"), (away_score, "away_score")]:
            if not isinstance(score, (int, float)):
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="Score must be numeric",
                    field=label,
                    actual=type(score).__name__,
                )
                continue

            # Reasonable score range (0-200)
            if not (0 <= score <= 200):
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="Score outside typical range",
                    field=label,
                    expected="0-200",
                    actual=score,
                )


class PlayByPlayValidator(BaseValidator):
    """
    Validator for play-by-play data.

    Validates individual plays across all sources.
    """

    REQUIRED_FIELDS = ["game_id", "period", "time_remaining", "description"]

    def validate(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Validate play-by-play data.

        Args:
            data: Play data dictionary

        Returns:
            ValidationReport with results
        """
        self.report = ValidationReport(source=self.source)

        # Required fields
        if not self.validate_required_fields(data, self.REQUIRED_FIELDS):
            return self.report

        # Period validation (1-4 regulation, 5+ overtime)
        self.validate_field_type(data, "period", int)
        if isinstance(data.get("period"), int):
            if data["period"] < 1 or data["period"] > 20:  # Sanity check
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="Unusual period number",
                    field="period",
                    actual=data["period"],
                )

        # Time remaining format
        self._validate_time_remaining(data.get("time_remaining"))

        # Description should not be empty
        if not data.get("description", "").strip():
            self._add_result(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Empty play description",
                field="description",
            )

        return self.report

    def _validate_time_remaining(self, time_value: Any) -> None:
        """Validate time remaining format"""
        if isinstance(time_value, str):
            # Should be in format "MM:SS" or "M:SS"
            parts = time_value.split(":")
            if len(parts) != 2:
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="Invalid time format",
                    field="time_remaining",
                    expected="MM:SS",
                    actual=time_value,
                )
        elif isinstance(time_value, (int, float)):
            # Seconds remaining
            if time_value < 0 or time_value > 12 * 60:  # 12 minutes max per period
                self._add_result(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="Time remaining out of range",
                    field="time_remaining",
                    actual=time_value,
                )


class BoxScoreValidator(BaseValidator):
    """
    Validator for box score data.

    Validates player and team statistics.
    """

    REQUIRED_FIELDS = ["game_id", "player_id", "team"]

    def validate(self, data: Dict[str, Any]) -> ValidationReport:
        """
        Validate box score data.

        Args:
            data: Box score data dictionary

        Returns:
            ValidationReport with results
        """
        self.report = ValidationReport(source=self.source)

        # Required fields
        if not self.validate_required_fields(data, self.REQUIRED_FIELDS):
            return self.report

        # Validate statistics ranges
        stat_fields = {
            "points": (0, 100),
            "rebounds": (0, 50),
            "assists": (0, 30),
            "steals": (0, 15),
            "blocks": (0, 15),
            "turnovers": (0, 20),
            "minutes": (0, 60),
        }

        for field, (min_val, max_val) in stat_fields.items():
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    self.validate_range(value, field, min_val, max_val)

        # Shooting percentages
        percentage_fields = ["fg_pct", "fg3_pct", "ft_pct"]
        for field in percentage_fields:
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    if not (0 <= value <= 1):
                        self._add_result(
                            is_valid=False,
                            level=ValidationLevel.ERROR,
                            message="Percentage out of range",
                            field=field,
                            expected="0.0-1.0",
                            actual=value,
                        )

        return self.report


# Convenience functions


def validate_game(
    data: Dict[str, Any], source: Optional[DataSource] = None
) -> ValidationReport:
    """
    Validate game data.

    Args:
        data: Game data to validate
        source: Data source (optional)

    Returns:
        ValidationReport with results
    """
    validator = GameValidator(source=source)
    return validator.validate(data)


def validate_play_by_play(
    data: Dict[str, Any], source: Optional[DataSource] = None
) -> ValidationReport:
    """
    Validate play-by-play data.

    Args:
        data: Play data to validate
        source: Data source (optional)

    Returns:
        ValidationReport with results
    """
    validator = PlayByPlayValidator(source=source)
    return validator.validate(data)


def validate_box_score(
    data: Dict[str, Any], source: Optional[DataSource] = None
) -> ValidationReport:
    """
    Validate box score data.

    Args:
        data: Box score data to validate
        source: Data source (optional)

    Returns:
        ValidationReport with results
    """
    validator = BoxScoreValidator(source=source)
    return validator.validate(data)


def validate_batch(
    data_list: List[Dict[str, Any]],
    validator_class: type,
    source: Optional[DataSource] = None,
) -> List[ValidationReport]:
    """
    Validate a batch of data items.

    Args:
        data_list: List of data items to validate
        validator_class: Validator class to use
        source: Data source (optional)

    Returns:
        List of ValidationReports
    """
    validator = validator_class(source=source)
    return [validator.validate(item) for item in data_list]
