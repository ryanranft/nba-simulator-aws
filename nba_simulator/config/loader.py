"""
Configuration Loader - Backward Compatible

Supports both legacy .env format and new YAML config format.
Ensures existing scripts continue working during migration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Backward-compatible configuration loader.

    Supports:
    - Legacy .env file format (existing scripts)
    - New YAML config format (future)
    """

    def __init__(self, legacy_mode: bool = True):
        """
        Initialize configuration loader.

        Args:
            legacy_mode: If True, use .env format. If False, use YAML.
        """
        self.legacy_mode = legacy_mode
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"

    def load_database_config(self) -> Dict[str, Any]:
        """
        Load database configuration.

        Returns:
            Dict with keys: host, port, database, user, password
        """
        if self.legacy_mode:
            return self._load_legacy_db_config()
        else:
            return self._load_new_db_config()

    def _load_legacy_db_config(self) -> Dict[str, Any]:
        """Load from existing .env format"""
        try:
            from dotenv import load_dotenv

            # Load from .env file if it exists
            env_file = self.project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"Loaded config from {env_file}")
            else:
                logger.warning("No .env file found. Using environment variables only.")
        except ImportError:
            logger.warning(
                "python-dotenv not installed. Using environment variables only."
            )

        return {
            "host": os.getenv("DB_HOST", os.getenv("RDS_HOST")),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", os.getenv("RDS_DB_NAME", "nba_simulator")),
            "user": os.getenv("DB_USER", os.getenv("RDS_USERNAME")),
            "password": os.getenv("DB_PASSWORD", os.getenv("RDS_PASSWORD")),
        }

    def _load_new_db_config(self) -> Dict[str, Any]:
        """Load from new config/database.yaml (future)"""
        try:
            import yaml

            config_file = self.config_dir / "database.yaml"

            if not config_file.exists():
                logger.warning("New config not found, falling back to legacy")
                return self._load_legacy_db_config()

            with open(config_file) as f:
                return yaml.safe_load(f)
        except ImportError:
            logger.warning("PyYAML not installed, falling back to legacy")
            return self._load_legacy_db_config()

    def load_s3_config(self) -> Dict[str, str]:
        """
        Get S3 bucket configuration.

        Returns:
            Dict with keys: bucket, region, prefix
        """
        return {
            "bucket": os.getenv("S3_BUCKET", "nba-sim-raw-data-lake"),
            "region": os.getenv("AWS_REGION", "us-east-1"),
            "prefix": os.getenv("S3_PREFIX", ""),
        }

    def load_aws_config(self) -> Dict[str, str]:
        """
        Get general AWS configuration.

        Returns:
            Dict with keys: region, profile
        """
        return {
            "region": os.getenv("AWS_REGION", "us-east-1"),
            "profile": os.getenv("AWS_PROFILE", "default"),
        }


# Singleton instance for easy import
config = ConfigLoader(legacy_mode=True)
