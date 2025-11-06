"""
Phase 0.0005: Possession Extraction - Configuration Module

This module loads and validates the possession extraction configuration from YAML.
Provides type-safe access to configuration settings through dataclasses.

Author: NBA Simulator AWS Team
Created: November 5, 2025
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
import yaml


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str
    port: int
    dbname: str
    user: str
    password: Optional[str] = None

    def __post_init__(self):
        """Load password from environment if not provided."""
        if self.password is None:
            self.password = os.getenv("NBA_DB_PASSWORD", "")

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


@dataclass
class PossessionDetectionConfig:
    """Rules for detecting possession boundaries."""

    min_duration: float
    max_duration: float
    start_events: List[str]
    end_events: List[str]
    continuation_events: List[str]
    edge_cases: Dict[str, bool]
    merge_offensive_rebounds: bool = (
        True  # Whether to merge possessions separated by offensive rebounds
    )

    def is_start_event(self, event_type: str) -> bool:
        """Check if event type starts a new possession."""
        return event_type in self.start_events

    def is_end_event(self, event_type: str) -> bool:
        """Check if event type ends a possession."""
        return event_type in self.end_events

    def is_continuation_event(self, event_type: str) -> bool:
        """Check if event type continues current possession."""
        return event_type in self.continuation_events


@dataclass
class ValidationConfig:
    """Validation rules for possession extraction."""

    enable_oliver_validation: bool
    oliver_tolerance_pct: float
    oliver_formula_coefficients: Dict[str, float]
    check_duration_bounds: bool
    warn_if_duration_outlier: bool
    outlier_threshold_seconds: float
    verify_possession_chains: bool
    check_orphaned_events: bool
    max_orphaned_events_pct: float
    verify_score_progression: bool
    check_impossible_scores: bool

    @property
    def oliver_fta_coefficient(self) -> float:
        """Get FTA coefficient for Dean Oliver formula."""
        return self.oliver_formula_coefficients.get("fta_coefficient", 0.44)


@dataclass
class ProcessingConfig:
    """Processing and performance configuration."""

    batch_size: int
    parallel_games: int
    max_retries: int
    retry_delay_seconds: int
    retry_backoff_multiplier: float
    max_events_in_memory: int
    clear_cache_every_n_games: int


@dataclass
class OutputConfig:
    """Output and logging configuration."""

    save_reports: bool
    report_format: str
    report_details: str
    detailed_logging: bool
    log_level: str
    log_rotation: bool
    log_retention_days: int
    show_progress_bar: bool
    progress_update_interval: int


@dataclass
class ContextDetectionConfig:
    """Context flag detection configuration."""

    clutch_time: Dict[str, Any]
    garbage_time: Dict[str, Any]
    fastbreak: Dict[str, Any]
    timeout_detection: Dict[str, bool]

    @property
    def clutch_enabled(self) -> bool:
        """Check if clutch time detection is enabled."""
        return self.clutch_time.get("enabled", False)

    @property
    def fastbreak_enabled(self) -> bool:
        """Check if fastbreak detection is enabled."""
        return self.fastbreak.get("enabled", False)

    @property
    def fastbreak_max_duration(self) -> float:
        """Get max duration for fastbreak classification."""
        return self.fastbreak.get("max_duration_seconds", 8.0)

    @property
    def clutch_time_threshold(self) -> float:
        """Get time threshold for clutch time (seconds remaining in period)."""
        return self.clutch_time.get(
            "time_remaining_seconds", 300.0
        )  # Default 5 minutes

    @property
    def clutch_score_margin(self) -> int:
        """Get score margin for clutch time classification."""
        return self.clutch_time.get("score_margin", 5)  # Default 5 points


@dataclass
class DIMSConfig:
    """DIMS (Data Inventory Management System) integration configuration."""

    enabled: bool
    report_metrics: bool
    metrics: List[str]
    health_check_interval_seconds: int
    report_interval_seconds: int


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""

    connection_pool_size: int
    connection_pool_overflow: int
    use_prepared_statements: bool
    enable_query_cache: bool
    verify_indexes_on_startup: bool
    create_indexes_if_missing: bool


@dataclass
class FeatureFlags:
    """Feature flags for phased rollout."""

    advanced_context: bool
    player_attribution: bool
    shot_quality: bool
    real_time_processing: bool


class PossessionConfig:
    """
    Main configuration class for possession extraction.

    Loads configuration from YAML and provides type-safe access through dataclasses.

    Usage:
        config = PossessionConfig.from_yaml("config/default_config.yaml")

        # Access database config
        db_conn = config.database.connection_string

        # Access detection rules
        if config.possession_detection.is_start_event(event_type):
            # Start new possession
            pass
    """

    def __init__(
        self,
        project_dir: str,
        log_dir: str,
        reports_dir: str,
        database: DatabaseConfig,
        source_table: str,
        target_table: str,
        possession_detection: PossessionDetectionConfig,
        validation: ValidationConfig,
        processing: ProcessingConfig,
        output: OutputConfig,
        context_detection: ContextDetectionConfig,
        dims: DIMSConfig,
        performance: PerformanceConfig,
        features: FeatureFlags,
    ):
        self.project_dir = Path(project_dir)
        self.log_dir = Path(log_dir)
        self.reports_dir = Path(reports_dir)
        self.database = database
        self.source_table = source_table
        self.target_table = target_table
        self.possession_detection = possession_detection
        self.validation = validation
        self.processing = processing
        self.output = output
        self.context_detection = context_detection
        self.dims = dims
        self.performance = performance
        self.features = features

    @classmethod
    def from_yaml(cls, config_path: str) -> "PossessionConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            PossessionConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r") as f:
            raw_config = yaml.safe_load(f)

        # Validate required top-level keys
        required_keys = [
            "project_dir",
            "database",
            "source_table",
            "target_table",
            "possession_detection",
            "validation",
            "processing",
            "output",
        ]
        missing_keys = [key for key in required_keys if key not in raw_config]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")

        # Create dataclass instances
        database_config = DatabaseConfig(**raw_config["database"])

        possession_detection_config = PossessionDetectionConfig(
            min_duration=raw_config["possession_detection"]["min_duration"],
            max_duration=raw_config["possession_detection"]["max_duration"],
            start_events=raw_config["possession_detection"]["start_events"],
            end_events=raw_config["possession_detection"]["end_events"],
            continuation_events=raw_config["possession_detection"][
                "continuation_events"
            ],
            edge_cases=raw_config["possession_detection"]["edge_cases"],
        )

        validation_config = ValidationConfig(**raw_config["validation"])
        processing_config = ProcessingConfig(**raw_config["processing"])
        output_config = OutputConfig(**raw_config["output"])
        context_config = ContextDetectionConfig(**raw_config["context_detection"])
        dims_config = DIMSConfig(**raw_config["dims"])
        performance_config = PerformanceConfig(**raw_config["performance"])
        features_config = FeatureFlags(**raw_config["features"])

        return cls(
            project_dir=raw_config["project_dir"],
            log_dir=raw_config["log_dir"],
            reports_dir=raw_config["reports_dir"],
            database=database_config,
            source_table=raw_config["source_table"],
            target_table=raw_config["target_table"],
            possession_detection=possession_detection_config,
            validation=validation_config,
            processing=processing_config,
            output=output_config,
            context_detection=context_config,
            dims=dims_config,
            performance=performance_config,
            features=features_config,
        )

    @classmethod
    def from_default(cls) -> "PossessionConfig":
        """
        Load configuration from default location.

        Returns:
            PossessionConfig instance with default configuration
        """
        default_path = Path(__file__).parent / "config" / "default_config.yaml"
        return cls.from_yaml(str(default_path))

    def validate(self) -> None:
        """
        Validate configuration settings.

        Raises:
            ValueError: If any configuration values are invalid
        """
        errors = []

        # Validate duration bounds
        if self.possession_detection.min_duration < 0:
            errors.append("min_duration must be >= 0")

        if (
            self.possession_detection.max_duration
            <= self.possession_detection.min_duration
        ):
            errors.append("max_duration must be > min_duration")

        # Validate tolerance
        if (
            self.validation.oliver_tolerance_pct <= 0
            or self.validation.oliver_tolerance_pct > 100
        ):
            errors.append("oliver_tolerance_pct must be between 0 and 100")

        # Validate batch size
        if self.processing.batch_size < 1:
            errors.append("batch_size must be >= 1")

        # Validate parallel games
        if self.processing.parallel_games < 1:
            errors.append("parallel_games must be >= 1")

        # Validate retry settings
        if self.processing.max_retries < 0:
            errors.append("max_retries must be >= 0")

        if errors:
            raise ValueError(
                f"Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

    def ensure_directories(self) -> None:
        """Create log and report directories if they don't exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"PossessionConfig(\n"
            f"  project_dir={self.project_dir},\n"
            f"  source={self.source_table},\n"
            f"  target={self.target_table},\n"
            f"  oliver_validation={'enabled' if self.validation.enable_oliver_validation else 'disabled'},\n"
            f"  batch_size={self.processing.batch_size},\n"
            f"  parallel_games={self.processing.parallel_games}\n"
            f")"
        )


# Module-level convenience function
def load_config(config_path: Optional[str] = None) -> PossessionConfig:
    """
    Load possession extraction configuration.

    Args:
        config_path: Path to YAML config file. If None, uses default.

    Returns:
        PossessionConfig instance
    """
    if config_path is None:
        return PossessionConfig.from_default()
    return PossessionConfig.from_yaml(config_path)
