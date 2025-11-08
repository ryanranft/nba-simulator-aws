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
        """
        Load database config from multiple sources with priority order:
        1. Hierarchical secrets (SECRETS_STRUCTURE.md format)
        2. Legacy .env file
        3. Environment variables
        4. Default values
        """
        # Try to load hierarchical secrets first
        try:
            # Check if UnifiedSecretsManager exists
            mcp_server_path = self.project_root / "mcp_server"
            if mcp_server_path.exists():
                import sys

                sys.path.insert(0, str(mcp_server_path))

                try:
                    from unified_secrets_manager import load_secrets_hierarchical

                    # Auto-detect context: DEVELOPMENT for local, WORKFLOW for production
                    context = (
                        "DEVELOPMENT"
                        if os.getenv("ENVIRONMENT", "development").lower()
                        in ["development", "dev", "local"]
                        else "WORKFLOW"
                    )
                    load_secrets_hierarchical("nba-simulator-aws", "NBA", context)
                    logger.info(f"Loaded hierarchical secrets for context: {context}")
                except Exception as e:
                    logger.debug(f"Could not load hierarchical secrets: {e}")
        except Exception as e:
            logger.debug(f"UnifiedSecretsManager not available: {e}")

        # Try loading from .env file
        try:
            from dotenv import load_dotenv

            env_file = self.project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"Loaded config from {env_file}")
            else:
                logger.debug("No .env file found. Using environment variables only.")
        except ImportError:
            logger.debug(
                "python-dotenv not installed. Using environment variables only."
            )

        # Priority order for each setting:
        # 1. Hierarchical names (context-specific)
        # 2. Legacy DB_* names
        # 3. Legacy RDS_* names
        # 4. POSTGRES_* names (for local development)
        # 5. Default values

        def get_with_fallback(*keys, default=None):
            """Try each key in order, return first non-None value"""
            for key in keys:
                value = os.getenv(key)
                if value is not None:
                    return value
            return default

        host = get_with_fallback(
            "RDS_HOST_NBA_SIMULATOR_AWS_WORKFLOW",
            "RDS_HOST_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_HOST_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_HOST_NBA_SIMULATOR_AWS_TEST",
            "DB_HOST",
            "RDS_HOST",
            "POSTGRES_HOST",
            default="localhost",
        )

        port_str = get_with_fallback(
            "RDS_PORT_NBA_SIMULATOR_AWS_WORKFLOW",
            "RDS_PORT_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_PORT_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_PORT_NBA_SIMULATOR_AWS_TEST",
            "DB_PORT",
            "RDS_PORT",
            "POSTGRES_PORT",
            default="5432",
        )
        port = int(port_str) if port_str else 5432

        database = get_with_fallback(
            "RDS_DATABASE_NBA_SIMULATOR_AWS_WORKFLOW",
            "RDS_DATABASE_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_DB_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_DB_NBA_SIMULATOR_AWS_TEST",
            "DB_NAME",
            "RDS_DB_NAME",
            "POSTGRES_DB",
            default="nba_simulator",
        )

        user = get_with_fallback(
            "RDS_USERNAME_NBA_SIMULATOR_AWS_WORKFLOW",
            "RDS_USERNAME_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_USER_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_USER_NBA_SIMULATOR_AWS_TEST",
            "DB_USER",
            "RDS_USERNAME",
            "POSTGRES_USER",
        )

        password = get_with_fallback(
            "RDS_PASSWORD_NBA_SIMULATOR_AWS_WORKFLOW",
            "RDS_PASSWORD_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_PASSWORD_NBA_SIMULATOR_AWS_DEVELOPMENT",
            "POSTGRES_PASSWORD_NBA_SIMULATOR_AWS_TEST",
            "DB_PASSWORD",
            "RDS_PASSWORD",
            "POSTGRES_PASSWORD",
            default="",
        )

        config = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }

        logger.info(
            f"Database config: host={host}, port={port}, database={database}, user={user}"
        )
        return config

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
