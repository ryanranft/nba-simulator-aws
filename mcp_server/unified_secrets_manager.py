#!/usr/bin/env python3
"""
Unified Secrets Manager with Hierarchical Loading and Context-Rich Naming Convention

This module provides a comprehensive secrets management system that:
- Loads secrets from hierarchical directory structure
- Enforces context-rich naming conventions (e.g., GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW)
- Creates backward-compatible aliases for short names
- Supports AWS Secrets Manager fallback
- Tracks secret provenance and provides audit logging
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SecretInfo:
    """Information about a loaded secret"""

    name: str
    value: str
    level: str
    context: str
    loaded_at: datetime
    source: str  # 'file' or 'aws'


@dataclass
class LoadingResult:
    """Result of secret loading operation"""

    success: bool
    secrets_loaded: int
    errors: List[str]
    warnings: List[str]
    provenance: Dict[str, SecretInfo]


class UnifiedSecretsManager:
    """
    Unified secrets manager with hierarchical loading and naming convention enforcement
    """

    def __init__(
        self, base_path: str = "/Users/ryanranft/Desktop/++/big_cat_bets_assets"
    ):
        self.base_path = Path(base_path)
        self.secrets: Dict[str, str] = {}
        self.aliases: Dict[str, str] = {}
        self.provenance: Dict[str, SecretInfo] = {}
        self.loading_order = [
            "global",
            "simulator_global",
            "sport",
            "project_group",
            "project",
        ]

    def load_secrets_hierarchical(
        self, project: str = None, sport: str = None, context: str = None
    ) -> LoadingResult:
        """
        Load secrets from hierarchical structure with naming convention enforcement

        Args:
            project: Project name (e.g., 'nba-mcp-synthesis')
            sport: Sport name (e.g., 'NBA')
            context: Context (e.g., 'production', 'development', 'test')

        Returns:
            LoadingResult with success status and details
        """
        # Auto-detect parameters if not provided
        project = project or os.getenv("PROJECT_NAME", "nba-mcp-synthesis")
        sport = sport or os.getenv("SPORT_NAME", "NBA")
        context = context or os.getenv("NBA_MCP_CONTEXT", "production")

        logger.info(
            f"Loading secrets for project={project}, sport={sport}, context={context}"
        )

        result = LoadingResult(
            success=True, secrets_loaded=0, errors=[], warnings=[], provenance={}
        )

        # Define hierarchy levels and their paths
        hierarchy_levels = self._get_hierarchy_levels(project, sport, context)

        # Load secrets from each level in priority order
        for level_name, level_path in hierarchy_levels.items():
            if level_path.exists():
                level_secrets = self._load_secrets_from_level(
                    level_path, level_name, context
                )

                # Merge secrets (later levels override earlier ones)
                for secret_name, secret_value in level_secrets.items():
                    if secret_name in self.secrets:
                        result.warnings.append(
                            f"Secret {secret_name} overridden by {level_name} level"
                        )

                    self.secrets[secret_name] = secret_value
                    result.provenance[secret_name] = SecretInfo(
                        name=secret_name,
                        value=secret_value,
                        level=level_name,
                        context=context,
                        loaded_at=datetime.now(),
                        source="file",
                    )
                    result.secrets_loaded += 1

                logger.info(
                    f"Loaded {len(level_secrets)} secrets from {level_name} level"
                )
            else:
                logger.debug(
                    f"Skipping {level_name} level - path not found: {level_path}"
                )

        # Create backward-compatible aliases
        self._create_aliases(project, context)

        # Check for AWS fallback if local secrets are insufficient
        if (
            result.secrets_loaded == 0
            and os.getenv("USE_AWS_SECRETS_MANAGER", "").lower() == "true"
        ):
            logger.warning(
                "No local secrets found, attempting AWS Secrets Manager fallback"
            )
            aws_secrets = self._load_from_aws_secrets_manager(context)
            if aws_secrets:
                self.secrets.update(aws_secrets)
                result.secrets_loaded += len(aws_secrets)
                result.warnings.append("Using AWS Secrets Manager fallback")
            else:
                result.errors.append(
                    "No secrets found locally or in AWS Secrets Manager"
                )
                result.success = False

        # Validate naming convention compliance
        naming_issues = self._validate_naming_convention()
        if naming_issues:
            result.warnings.extend(naming_issues)

        logger.info(f"Secret loading complete: {result.secrets_loaded} secrets loaded")
        return result

    def _get_hierarchy_levels(
        self, project: str, sport: str, context: str
    ) -> Dict[str, Path]:
        """Get hierarchy level paths for the given project/sport/context"""

        # Convert context to directory naming
        context_dir_map = {
            "production": "production",
            "workflow": "production",
            "development": "development",
            "test": "test",
        }
        context_dir = context_dir_map.get(context.lower(), "production")

        # Convert project name to directory format
        project_dir = project.replace("-", "_")

        return {
            "global": self.base_path
            / "sports_assets"
            / "big_cat_bets_global"
            / f".env.global.{context_dir}",
            "simulator_global": self.base_path
            / "sports_assets"
            / "big_cat_bets_simulators"
            / "_config_placeholder"
            / f".env.simulator_global.{context_dir}",
            "sport": self.base_path
            / "sports_assets"
            / "big_cat_bets_simulators"
            / sport
            / "_config_placeholder"
            / f".env.{sport.lower()}_sport.{context_dir}",
            "project_group": self.base_path
            / "sports_assets"
            / "big_cat_bets_simulators"
            / sport
            / f"{project_dir}_global"
            / f".env.{project_dir}_global.{context_dir}",
            "project": self.base_path
            / "sports_assets"
            / "big_cat_bets_simulators"
            / sport
            / project
            / f".env.{project_dir}.{context_dir}",
        }

    def _load_secrets_from_level(
        self, level_path: Path, level_name: str, context: str
    ) -> Dict[str, str]:
        """Load secrets from a specific hierarchy level"""
        secrets = {}

        if not level_path.exists():
            return secrets

        # Load all .env files in the level directory
        for env_file in level_path.glob("*.env"):
            try:
                with open(env_file, "r") as f:
                    secret_value = f.read().strip()
                    secret_name = env_file.stem.upper()

                    # Validate naming convention
                    if self._is_valid_naming_convention(secret_name):
                        secrets[secret_name] = secret_value
                        logger.debug(f"Loaded {secret_name} from {level_name}")
                    else:
                        logger.warning(
                            f"Invalid naming convention for {secret_name} in {level_name}"
                        )

            except Exception as e:
                logger.error(f"Error loading secret from {env_file}: {e}")

        return secrets

    def _is_valid_naming_convention(self, secret_name: str) -> bool:
        """
        Validate that secret name follows convention: SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT
        """
        parts = secret_name.split("_")

        # Must have at least 4 parts: SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT
        # Exception: GLOBAL secrets can have 3 parts: SERVICE_RESOURCE_TYPE_CONTEXT
        if len(parts) < 3:
            return False

        # Special case for GLOBAL secrets (3 parts: SERVICE_RESOURCE_TYPE_CONTEXT)
        if len(parts) == 3 and "GLOBAL" in parts:
            has_service = any(
                part
                in [
                    "GOOGLE",
                    "ANTHROPIC",
                    "OPENAI",
                    "DEEPSEEK",
                    "SLACK",
                    "LINEAR",
                    "DB",
                    "AWS",
                    "REDIS",
                    "RDS",
                    "S3",
                    "GLUE",
                    "NBA",
                    "SPORTSDATA",
                    "TIMEZONE",
                ]
                for part in parts
            )
            resource_type_patterns = [
                "API_KEY",
                "SECRET_KEY",
                "ACCESS_KEY",
                "PASSWORD",
                "TOKEN",
                "WEBHOOK_URL",
                "HOST",
                "PORT",
                "DATABASE",
                "BUCKET",
                "USERNAME",
                "REGION",
                "TIMEZONE",
            ]
            has_resource_type = any(
                pattern in secret_name for pattern in resource_type_patterns
            )
            has_context = any(
                part in ["WORKFLOW", "DEVELOPMENT", "TEST", "PRODUCTION"]
                for part in parts
            )

            # Special case: TIMEZONE can be both service and resource type
            if "TIMEZONE" in secret_name:
                has_service = True
                has_resource_type = True

            return has_service and has_resource_type and has_context

        # Check for required components
        has_service = any(
            part
            in [
                "GOOGLE",
                "ANTHROPIC",
                "OPENAI",
                "DEEPSEEK",
                "SLACK",
                "LINEAR",
                "DB",
                "AWS",
                "REDIS",
                "RDS",
                "S3",
                "GLUE",
                "NBA",
                "SPORTSDATA",
                "TIMEZONE",
            ]
            for part in parts
        )

        # Check for resource types (can be multi-part like API_KEY)
        resource_type_patterns = [
            "API_KEY",
            "SECRET_KEY",
            "ACCESS_KEY",
            "PASSWORD",
            "TOKEN",
            "WEBHOOK_URL",
            "HOST",
            "PORT",
            "DATABASE",
            "BUCKET",
            "USERNAME",
            "REGION",
            "TIMEZONE",
        ]
        has_resource_type = any(
            pattern in secret_name for pattern in resource_type_patterns
        )

        # Special case: TIMEZONE can be both service and resource type
        if "TIMEZONE" in secret_name:
            has_service = True
            has_resource_type = True

        has_context = any(
            part in ["WORKFLOW", "DEVELOPMENT", "TEST", "PRODUCTION"] for part in parts
        )

        return has_service and has_resource_type and has_context

    def _create_aliases(self, project: str, context: str):
        """Create backward-compatible aliases for short names"""

        # Map common short names to full names
        short_name_mappings = {
            "GOOGLE_API_KEY": f'GOOGLE_API_KEY_{project.upper().replace("-", "_")}_{context.upper()}',
            "ANTHROPIC_API_KEY": f'ANTHROPIC_API_KEY_{project.upper().replace("-", "_")}_{context.upper()}',
            "OPENAI_API_KEY": f'OPENAI_API_KEY_{project.upper().replace("-", "_")}_{context.upper()}',
            "DEEPSEEK_API_KEY": f'DEEPSEEK_API_KEY_{project.upper().replace("-", "_")}_{context.upper()}',
            "DB_PASSWORD": f'DB_PASSWORD_{project.upper().replace("-", "_")}_{context.upper()}',
            "DB_HOST": f'DB_HOST_{project.upper().replace("-", "_")}_{context.upper()}',
            "SLACK_WEBHOOK_URL": f"SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_{context.upper()}",
            "LINEAR_API_KEY": f"LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_{context.upper()}",
        }

        for short_name, full_name in short_name_mappings.items():
            if full_name in self.secrets:
                self.aliases[short_name] = full_name
                logger.debug(f"Created alias: {short_name} -> {full_name}")

    def _load_from_aws_secrets_manager(self, context: str) -> Dict[str, str]:
        """Load secrets from AWS Secrets Manager as fallback"""
        try:
            session = boto3.Session()
            client = session.client("secretsmanager")

            secret_name = f"nba-mcp-synthesis/{context}"
            response = client.get_secret_value(SecretId=secret_name)

            secret_data = json.loads(response["SecretString"])
            logger.info(f"Loaded {len(secret_data)} secrets from AWS Secrets Manager")

            return secret_data

        except ClientError as e:
            logger.error(f"Failed to load secrets from AWS: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading from AWS: {e}")
            return {}

    def _validate_naming_convention(self) -> List[str]:
        """Validate naming convention compliance and return issues"""
        issues = []

        for secret_name in self.secrets.keys():
            if not self._is_valid_naming_convention(secret_name):
                issues.append(f"Secret {secret_name} does not follow naming convention")

        return issues

    def get_secret(self, name: str) -> Optional[str]:
        """
        Get a secret by name, supporting both full names and aliases

        Args:
            name: Secret name (full name or alias)

        Returns:
            Secret value or None if not found
        """
        # Try direct lookup first
        if name in self.secrets:
            logger.debug(f"Retrieved secret {name} (direct)")
            return self.secrets[name]

        # Try alias lookup
        if name in self.aliases:
            full_name = self.aliases[name]
            logger.debug(f"Retrieved secret {name} via alias -> {full_name}")
            return self.secrets.get(full_name)

        logger.warning(f"Secret {name} not found")
        return None

    def get_all_secrets(self) -> Dict[str, str]:
        """Get all loaded secrets"""
        return self.secrets.copy()

    def get_aliases(self) -> Dict[str, str]:
        """Get all aliases"""
        return self.aliases.copy()

    def get_provenance(self) -> Dict[str, SecretInfo]:
        """Get secret provenance information"""
        return self.provenance.copy()

    def verify_secrets_loaded(self) -> bool:
        """Verify that secrets have been loaded successfully"""
        return len(self.secrets) > 0

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the secrets manager"""
        return {
            "secrets_loaded": len(self.secrets),
            "aliases_created": len(self.aliases),
            "provenance_tracked": len(self.provenance),
            "naming_compliance": len(self._validate_naming_convention()) == 0,
            "last_loaded": datetime.now().isoformat() if self.secrets else None,
        }


# Global instance
_secrets_manager = None


def get_secrets_manager() -> UnifiedSecretsManager:
    """Get the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = UnifiedSecretsManager()
    return _secrets_manager


def load_secrets_hierarchical(
    project: str = None, sport: str = None, context: str = None
) -> bool:
    """
    Load secrets hierarchically and return success status

    Args:
        project: Project name
        sport: Sport name
        context: Context

    Returns:
        True if successful, False otherwise
    """
    manager = get_secrets_manager()
    result = manager.load_secrets_hierarchical(project, sport, context)

    if result.success:
        # Set environment variables
        for name, value in manager.get_all_secrets().items():
            os.environ[name] = value

        # Set aliases
        for alias, full_name in manager.get_aliases().items():
            if full_name in os.environ:
                os.environ[alias] = os.environ[full_name]

    return result.success


def verify_secrets_loaded() -> bool:
    """Verify that secrets have been loaded"""
    manager = get_secrets_manager()
    return manager.verify_secrets_loaded()


def get_secret(name: str) -> Optional[str]:
    """Get a secret by name"""
    manager = get_secrets_manager()
    return manager.get_secret(name)


def get_health_status() -> Dict[str, Any]:
    """Get health status"""
    manager = get_secrets_manager()
    return manager.get_health_status()


# Convenience functions for backward compatibility
def get_database_config() -> Dict[str, Any]:
    """Get database configuration (backward compatibility)"""
    return {
        "host": get_secret("DB_HOST")
        or get_secret("DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW"),
        "port": get_secret("DB_PORT")
        or get_secret("DB_PORT_NBA_MCP_SYNTHESIS_WORKFLOW"),
        "database": get_secret("DB_NAME")
        or get_secret("DB_NAME_NBA_MCP_SYNTHESIS_WORKFLOW"),
        "user": get_secret("DB_USER")
        or get_secret("DB_USER_NBA_MCP_SYNTHESIS_WORKFLOW"),
        "password": get_secret("DB_PASSWORD")
        or get_secret("DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW"),
    }


def get_s3_bucket() -> str:
    """Get S3 bucket name (backward compatibility)"""
    return (
        get_secret("S3_BUCKET")
        or get_secret("S3_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW")
        or "nba-mcp-books-20251011"
    )


if __name__ == "__main__":
    # Test the secrets manager
    import sys

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Load secrets
    success = load_secrets_hierarchical()

    if success:
        print("✅ Secrets loaded successfully")
        health = get_health_status()
        print(f"📊 Health Status: {health}")

        # Show some example secrets (without values)
        secrets = get_secrets_manager().get_all_secrets()
        print(f"🔐 Loaded {len(secrets)} secrets:")
        for name in sorted(secrets.keys())[:5]:  # Show first 5
            print(f"  - {name}")
        if len(secrets) > 5:
            print(f"  ... and {len(secrets) - 5} more")
    else:
        print("❌ Failed to load secrets")
        sys.exit(1)
