"""
NBA Simulator AWS - Python Package

Version: 0.1.0 (Phase 1: Core Infrastructure)
Created: October 29, 2025
Status: Development

This package provides a structured interface to the NBA Simulator production system.
It is designed to coexist with existing scripts/ directory without breaking functionality.

Phase 1 Goals:
- Backward-compatible configuration management
- Database connection pooling
- Common utilities (logging, constants, helpers)

Design Principle: Parallel Coexistence
- Existing scripts/ directory remains intact
- New package provides structured interface
- Zero breaking changes to production code
"""

__version__ = "0.1.0"
__status__ = "Phase 1 - Core Infrastructure"
__created__ = "2025-10-29"

# Phase 1 exports
from nba_simulator.config import ConfigLoader, load_config, DatabaseConfig, AWSConfig
from nba_simulator.database import (
    DatabaseConnection,
    get_connection,
    execute_query,
    execute_many,
)
from nba_simulator.utils import setup_logging, get_logger, ensure_dir, get_timestamp

__all__ = [
    # Config
    "ConfigLoader",
    "load_config",
    "DatabaseConfig",
    "AWSConfig",
    # Database
    "DatabaseConnection",
    "get_connection",
    "execute_query",
    "execute_many",
    # Utils
    "setup_logging",
    "get_logger",
    "ensure_dir",
    "get_timestamp",
]
