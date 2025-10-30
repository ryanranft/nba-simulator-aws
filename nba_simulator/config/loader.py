"""
Configuration Loader

Backward-compatible configuration loading from existing sources:
- /Users/ryanranft/nba-sim-credentials.env (database credentials)
- config/*.yaml (project configuration files)
- Environment variables

This module wraps existing configuration without breaking current scripts.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """
    Backward-compatible configuration loader.

    Loads configuration from existing sources without requiring code changes
    in existing scripts.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration loader.

        Args:
            project_root: Path to project root (defaults to auto-detection)
        """
        if project_root is None:
            # Auto-detect project root
            project_root = Path(__file__).parent.parent.parent

        self.project_root = Path(project_root)
        self.config_dir = self.project_root / "config"
        self.credentials_file = Path("/Users/ryanranft/nba-sim-credentials.env")

        self._config = {}
        self._load_all()

    def _load_all(self):
        """Load all configuration sources"""
        # Load database credentials from existing .env file
        if self.credentials_file.exists():
            load_dotenv(self.credentials_file)

        # Load YAML configuration files from config/ directory
        if self.config_dir.exists():
            for yaml_file in self.config_dir.glob("*.yaml"):
                key = yaml_file.stem  # filename without extension
                self._config[key] = self._load_yaml(yaml_file)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        # Try environment variable first
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value

        # Try nested key in loaded config
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def get_database_url(self) -> str:
        """
        Get database URL from environment.

        Returns:
            DATABASE_URL from credentials file
        """
        return os.getenv("DATABASE_URL", "")

    def get_database_config(self) -> Dict[str, str]:
        """
        Get database configuration.

        Returns:
            Dictionary with database connection parameters
        """
        return {
            "host": os.getenv("RDS_HOST", ""),
            "port": os.getenv("RDS_PORT", "5432"),
            "database": os.getenv("RDS_DATABASE", ""),
            "user": os.getenv("RDS_USERNAME", ""),
            "password": os.getenv("RDS_PASSWORD", ""),
            "url": os.getenv("DATABASE_URL", ""),
        }

    def get_aws_config(self) -> Dict[str, str]:
        """
        Get AWS configuration.

        Returns:
            Dictionary with AWS credentials and settings
        """
        return {
            "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            "s3_bucket": os.getenv("S3_BUCKET", "nba-sim-raw-data-lake"),
        }

    def get_config_file(self, name: str) -> Dict[str, Any]:
        """
        Get loaded YAML configuration file.

        Args:
            name: Configuration file name (without .yaml extension)

        Returns:
            Configuration dictionary
        """
        return self._config.get(name, {})


# Global instance for convenient access
_global_config = None


def load_config(project_root: Optional[Path] = None) -> ConfigLoader:
    """
    Load or get global configuration instance.

    Args:
        project_root: Path to project root (defaults to auto-detection)

    Returns:
        Global ConfigLoader instance
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader(project_root)

    return _global_config


def get_config() -> ConfigLoader:
    """
    Get global configuration instance (loads if not already loaded).

    Returns:
        Global ConfigLoader instance
    """
    return load_config()
