"""
Configuration Management Module

Provides backward-compatible configuration loading from existing .env files
and config/ directory without disrupting current infrastructure.
"""

from nba_simulator.config.loader import ConfigLoader, load_config
from nba_simulator.config.database import DatabaseConfig
from nba_simulator.config.aws_services import AWSConfig

__all__ = [
    "ConfigLoader",
    "load_config",
    "DatabaseConfig",
    "AWSConfig",
]
