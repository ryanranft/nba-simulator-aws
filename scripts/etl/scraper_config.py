#!/usr/bin/env python3
"""
Scraper Configuration Management - YAML-based Configuration System

Provides centralized configuration management for NBA data scrapers with:
- YAML-based configuration files
- Environment variable overrides
- Configuration validation
- Runtime configuration updates
- Multi-scraper configuration support

Based on Crawl4AI MCP server configuration patterns.

Usage:
    from scraper_config import ScraperConfigManager, load_config

    # Load configuration
    config_manager = ScraperConfigManager("config/scraper_config.yaml")
    espn_config = config_manager.get_scraper_config("espn")

    # Use in scraper
    scraper = ESPNScraper(espn_config)

Version: 1.0
Created: October 13, 2025
"""

import os
import yaml
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_second: float = 1.0
    burst_size: int = 10
    adaptive: bool = False
    retry_after_header: bool = True


@dataclass
class RetryConfig:
    """Retry configuration"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True


@dataclass
class StorageConfig:
    """Storage configuration"""

    s3_bucket: Optional[str] = None
    local_output_dir: str = (
        "/tmp/scraper_output"  # nosec B108 - Standard temp directory for scraper output
    )
    upload_to_s3: bool = True
    compression: bool = False
    deduplication: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""

    enable_telemetry: bool = True
    log_level: str = "INFO"
    log_file: Optional[str] = None
    metrics_port: int = 8000
    health_check_interval: int = 60
    alert_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class ScraperConfig:
    """Complete scraper configuration"""

    name: str
    base_url: str
    user_agent: str = "NBA-Simulator-Scraper/1.0"
    timeout: int = 30
    max_concurrent: int = 10
    dry_run: bool = False

    # Sub-configurations
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Scraper-specific settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ScraperConfigManager:
    """Manages configurations for multiple scrapers"""

    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.configs: Dict[str, ScraperConfig] = {}
        self.logger = logging.getLogger(__name__)

        if not self.config_file.exists():
            self._create_default_config()

        self.load_configs()

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        default_config = {
            "scrapers": {
                "espn": {
                    "name": "espn",
                    "base_url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
                    "user_agent": "NBA-Simulator-Scraper/1.0",
                    "timeout": 30,
                    "max_concurrent": 10,
                    "rate_limit": {"requests_per_second": 1.0, "adaptive": True},
                    "retry": {
                        "max_attempts": 3,
                        "base_delay": 1.0,
                        "exponential_backoff": True,
                    },
                    "storage": {
                        "s3_bucket": "nba-sim-raw-data-lake",
                        "local_output_dir": "/tmp/espn_data",  # nosec B108
                        "upload_to_s3": True,
                        "deduplication": True,
                    },
                    "monitoring": {
                        "enable_telemetry": True,
                        "log_level": "INFO",
                        "log_file": "/tmp/espn_scraper.log",  # nosec B108
                    },
                },
                "basketball_reference": {
                    "name": "basketball_reference",
                    "base_url": "https://www.basketball-reference.com",
                    "user_agent": "NBA-Simulator-Scraper/1.0",
                    "timeout": 30,
                    "max_concurrent": 5,
                    "rate_limit": {
                        "requests_per_second": 0.083,  # 12 seconds between requests
                        "adaptive": True,
                    },
                    "retry": {
                        "max_attempts": 5,
                        "base_delay": 2.0,
                        "exponential_backoff": True,
                    },
                    "storage": {
                        "s3_bucket": "nba-sim-raw-data-lake",
                        "local_output_dir": "/tmp/basketball_reference_data",  # nosec B108
                        "upload_to_s3": True,
                        "deduplication": True,
                    },
                    "monitoring": {
                        "enable_telemetry": True,
                        "log_level": "INFO",
                        "log_file": "/tmp/bref_scraper.log",  # nosec B108
                    },
                    "custom_settings": {
                        "tier": 1,
                        "data_types": ["player_stats", "team_stats", "schedule"],
                    },
                },
                "nba_api": {
                    "name": "nba_api",
                    "base_url": "https://stats.nba.com/stats",
                    "user_agent": "NBA-Simulator-Scraper/1.0",
                    "timeout": 30,
                    "max_concurrent": 8,
                    "rate_limit": {
                        "requests_per_second": 1.67,  # 0.6 seconds between requests
                        "adaptive": True,
                    },
                    "retry": {
                        "max_attempts": 5,
                        "base_delay": 1.0,
                        "exponential_backoff": True,
                    },
                    "storage": {
                        "s3_bucket": "nba-sim-raw-data-lake",
                        "local_output_dir": "/tmp/nba_api_data",  # nosec B108
                        "upload_to_s3": True,
                        "deduplication": True,
                    },
                    "monitoring": {
                        "enable_telemetry": True,
                        "log_level": "INFO",
                        "log_file": "/tmp/nba_api_scraper.log",  # nosec B108
                        "alert_thresholds": {
                            "error_rate": 0.1,
                            "response_time_ms": 5000,
                        },
                    },
                    "custom_settings": {
                        "endpoints": ["playbyplay", "boxscore", "scoreboard"],
                        "seasons": [
                            "2020-21",
                            "2021-22",
                            "2022-23",
                            "2023-24",
                            "2024-25",
                        ],
                    },
                },
            },
            "global": {
                "aws_region": "us-east-1",
                "default_timeout": 30,
                "default_max_concurrent": 10,
                "telemetry_s3_bucket": "nba-sim-raw-data-lake",
                "environment": "production",
            },
        }

        # Create directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write default config
        with open(self.config_file, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)

        self.logger.info(f"Created default configuration file: {self.config_file}")

    def load_configs(self) -> None:
        """Load configurations from file"""
        try:
            with open(self.config_file, "r") as f:
                config_data = yaml.safe_load(f)

            # Load global settings
            global_settings = config_data.get("global", {})

            # Load scraper configurations
            scrapers_data = config_data.get("scrapers", {})

            for scraper_name, scraper_data in scrapers_data.items():
                config = self._create_scraper_config(
                    scraper_name, scraper_data, global_settings
                )
                self.configs[scraper_name] = config

            self.logger.info(f"Loaded {len(self.configs)} scraper configurations")

        except Exception as e:
            self.logger.error(f"Error loading configuration file: {e}")
            raise

    def _create_scraper_config(
        self, name: str, data: Dict[str, Any], global_settings: Dict[str, Any]
    ) -> ScraperConfig:
        """Create ScraperConfig from dictionary data"""

        # Rate limit config
        rate_limit_data = data.get("rate_limit", {})
        rate_limit = RateLimitConfig(
            requests_per_second=rate_limit_data.get("requests_per_second", 1.0),
            burst_size=rate_limit_data.get("burst_size", 10),
            adaptive=rate_limit_data.get("adaptive", False),
            retry_after_header=rate_limit_data.get("retry_after_header", True),
        )

        # Retry config
        retry_data = data.get("retry", {})
        retry = RetryConfig(
            max_attempts=retry_data.get("max_attempts", 3),
            base_delay=retry_data.get("base_delay", 1.0),
            max_delay=retry_data.get("max_delay", 60.0),
            exponential_backoff=retry_data.get("exponential_backoff", True),
            jitter=retry_data.get("jitter", True),
        )

        # Storage config
        storage_data = data.get("storage", {})
        storage = StorageConfig(
            s3_bucket=storage_data.get("s3_bucket"),
            local_output_dir=storage_data.get(
                "local_output_dir", "/tmp/scraper_output"  # nosec B108
            ),
            upload_to_s3=storage_data.get("upload_to_s3", True),
            compression=storage_data.get("compression", False),
            deduplication=storage_data.get("deduplication", True),
        )

        # Monitoring config
        monitoring_data = data.get("monitoring", {})
        monitoring = MonitoringConfig(
            enable_telemetry=monitoring_data.get("enable_telemetry", True),
            log_level=monitoring_data.get("log_level", "INFO"),
            log_file=monitoring_data.get("log_file"),
            metrics_port=monitoring_data.get("metrics_port", 8000),
            health_check_interval=monitoring_data.get("health_check_interval", 60),
            alert_thresholds=monitoring_data.get("alert_thresholds", {}),
        )

        # Main config
        config = ScraperConfig(
            name=name,
            base_url=data.get("base_url", ""),
            user_agent=data.get("user_agent", "NBA-Simulator-Scraper/1.0"),
            timeout=data.get("timeout", global_settings.get("default_timeout", 30)),
            max_concurrent=data.get(
                "max_concurrent", global_settings.get("default_max_concurrent", 10)
            ),
            dry_run=data.get("dry_run", False),
            rate_limit=rate_limit,
            retry=retry,
            storage=storage,
            monitoring=monitoring,
            custom_settings=data.get("custom_settings", {}),
        )

        return config

    def get_scraper_config(self, scraper_name: str) -> Optional[ScraperConfig]:
        """Get configuration for a specific scraper"""
        return self.configs.get(scraper_name)

    def get_all_scraper_names(self) -> List[str]:
        """Get list of all configured scraper names"""
        return list(self.configs.keys())

    def update_scraper_config(self, scraper_name: str, updates: Dict[str, Any]) -> None:
        """Update configuration for a specific scraper"""
        if scraper_name not in self.configs:
            raise ValueError(f"Scraper '{scraper_name}' not found in configuration")

        # Update the configuration
        config = self.configs[scraper_name]

        # Update simple fields
        for field_name in [
            "base_url",
            "user_agent",
            "timeout",
            "max_concurrent",
            "dry_run",
        ]:
            if field_name in updates:
                setattr(config, field_name, updates[field_name])

        # Update sub-configurations
        if "rate_limit" in updates:
            for key, value in updates["rate_limit"].items():
                if hasattr(config.rate_limit, key):
                    setattr(config.rate_limit, key, value)

        if "retry" in updates:
            for key, value in updates["retry"].items():
                if hasattr(config.retry, key):
                    setattr(config.retry, key, value)

        if "storage" in updates:
            for key, value in updates["storage"].items():
                if hasattr(config.storage, key):
                    setattr(config.storage, key, value)

        if "monitoring" in updates:
            for key, value in updates["monitoring"].items():
                if hasattr(config.monitoring, key):
                    setattr(config.monitoring, key, value)

        if "custom_settings" in updates:
            config.custom_settings.update(updates["custom_settings"])

        self.logger.info(f"Updated configuration for scraper '{scraper_name}'")

    def save_configs(self) -> None:
        """Save current configurations back to file"""
        try:
            config_data = {
                "scrapers": {},
                "global": {
                    "aws_region": "us-east-1",
                    "default_timeout": 30,
                    "default_max_concurrent": 10,
                    "telemetry_s3_bucket": "nba-sim-raw-data-lake",
                    "environment": "production",
                },
            }

            for name, config in self.configs.items():
                config_data["scrapers"][name] = {
                    "name": config.name,
                    "base_url": config.base_url,
                    "user_agent": config.user_agent,
                    "timeout": config.timeout,
                    "max_concurrent": config.max_concurrent,
                    "dry_run": config.dry_run,
                    "rate_limit": {
                        "requests_per_second": config.rate_limit.requests_per_second,
                        "burst_size": config.rate_limit.burst_size,
                        "adaptive": config.rate_limit.adaptive,
                        "retry_after_header": config.rate_limit.retry_after_header,
                    },
                    "retry": {
                        "max_attempts": config.retry.max_attempts,
                        "base_delay": config.retry.base_delay,
                        "max_delay": config.retry.max_delay,
                        "exponential_backoff": config.retry.exponential_backoff,
                        "jitter": config.retry.jitter,
                    },
                    "storage": {
                        "s3_bucket": config.storage.s3_bucket,
                        "local_output_dir": config.storage.local_output_dir,
                        "upload_to_s3": config.storage.upload_to_s3,
                        "compression": config.storage.compression,
                        "deduplication": config.storage.deduplication,
                    },
                    "monitoring": {
                        "enable_telemetry": config.monitoring.enable_telemetry,
                        "log_level": config.monitoring.log_level,
                        "log_file": config.monitoring.log_file,
                        "metrics_port": config.monitoring.metrics_port,
                        "health_check_interval": config.monitoring.health_check_interval,
                        "alert_thresholds": config.monitoring.alert_thresholds,
                    },
                    "custom_settings": config.custom_settings,
                }

            with open(self.config_file, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            self.logger.info(f"Saved configurations to {self.config_file}")

        except Exception as e:
            self.logger.error(f"Error saving configuration file: {e}")
            raise

    def validate_config(self, scraper_name: str) -> List[str]:
        """Validate configuration for a specific scraper"""
        errors = []

        if scraper_name not in self.configs:
            errors.append(f"Scraper '{scraper_name}' not found")
            return errors

        config = self.configs[scraper_name]

        # Validate required fields
        if not config.base_url:
            errors.append("base_url is required")

        if config.timeout <= 0:
            errors.append("timeout must be positive")

        if config.max_concurrent <= 0:
            errors.append("max_concurrent must be positive")

        if config.rate_limit.requests_per_second <= 0:
            errors.append("rate_limit.requests_per_second must be positive")

        if config.retry.max_attempts < 0:
            errors.append("retry.max_attempts must be non-negative")

        if config.retry.base_delay < 0:
            errors.append("retry.base_delay must be non-negative")

        # Validate storage configuration
        if config.storage.upload_to_s3 and not config.storage.s3_bucket:
            errors.append("s3_bucket is required when upload_to_s3 is True")

        return errors


def load_config(
    config_file: str = "config/scraper_config.yaml",
) -> ScraperConfigManager:
    """Load configuration manager from file"""
    return ScraperConfigManager(config_file)


def get_scraper_config(
    scraper_name: str, config_file: str = "config/scraper_config.yaml"
) -> Optional[ScraperConfig]:
    """Get configuration for a specific scraper"""
    manager = ScraperConfigManager(config_file)
    return manager.get_scraper_config(scraper_name)


def create_config_from_env(scraper_name: str) -> ScraperConfig:
    """Create configuration from environment variables"""
    prefix = f"SCRAPER_{scraper_name.upper()}_"

    config = ScraperConfig(
        name=scraper_name,
        base_url=os.getenv(f"{prefix}BASE_URL", ""),
        user_agent=os.getenv(f"{prefix}USER_AGENT", "NBA-Simulator-Scraper/1.0"),
        timeout=int(os.getenv(f"{prefix}TIMEOUT", "30")),
        max_concurrent=int(os.getenv(f"{prefix}MAX_CONCURRENT", "10")),
        dry_run=os.getenv(f"{prefix}DRY_RUN", "false").lower() == "true",
    )

    # Rate limit from env
    rate_limit_rps = float(os.getenv(f"{prefix}RATE_LIMIT", "1.0"))
    config.rate_limit.requests_per_second = rate_limit_rps
    config.rate_limit.adaptive = (
        os.getenv(f"{prefix}RATE_LIMIT_ADAPTIVE", "false").lower() == "true"
    )

    # Retry from env
    config.retry.max_attempts = int(os.getenv(f"{prefix}RETRY_ATTEMPTS", "3"))
    config.retry.base_delay = float(os.getenv(f"{prefix}RETRY_DELAY", "1.0"))
    config.retry.exponential_backoff = (
        os.getenv(f"{prefix}RETRY_EXPONENTIAL", "true").lower() == "true"
    )

    # Storage from env
    config.storage.s3_bucket = os.getenv(f"{prefix}S3_BUCKET")
    config.storage.local_output_dir = os.getenv(
        f"{prefix}OUTPUT_DIR", "/tmp/scraper_output"  # nosec B108
    )
    config.storage.upload_to_s3 = (
        os.getenv(f"{prefix}UPLOAD_S3", "true").lower() == "true"
    )
    config.storage.deduplication = (
        os.getenv(f"{prefix}DEDUPLICATION", "true").lower() == "true"
    )

    # Monitoring from env
    config.monitoring.enable_telemetry = (
        os.getenv(f"{prefix}TELEMETRY", "true").lower() == "true"
    )
    config.monitoring.log_level = os.getenv(f"{prefix}LOG_LEVEL", "INFO")
    config.monitoring.log_file = os.getenv(f"{prefix}LOG_FILE")

    return config


# Example usage
if __name__ == "__main__":
    # Create configuration manager
    manager = ScraperConfigManager("config/scraper_config.yaml")

    # Get ESPN configuration
    espn_config = manager.get_scraper_config("espn")
    if espn_config:
        print(f"ESPN Config: {espn_config.base_url}")
        print(f"Rate limit: {espn_config.rate_limit.requests_per_second} req/s")
        print(f"Max concurrent: {espn_config.max_concurrent}")
        print(f"S3 bucket: {espn_config.storage.s3_bucket}")

    # Get Basketball Reference configuration
    bref_config = manager.get_scraper_config("basketball_reference")
    if bref_config:
        print(f"Basketball Reference Config: {bref_config.base_url}")
        print(f"Rate limit: {bref_config.rate_limit.requests_per_second} req/s")
        print(f"Custom settings: {bref_config.custom_settings}")

    # Validate configurations
    for scraper_name in manager.get_all_scraper_names():
        errors = manager.validate_config(scraper_name)
        if errors:
            print(f"Validation errors for {scraper_name}: {errors}")
        else:
            print(f"Configuration for {scraper_name} is valid")
