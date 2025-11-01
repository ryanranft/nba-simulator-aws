"""
Configuration Management Module

Provides centralized configuration loading for:
- Database connections
- AWS services (S3, Glue, RDS)
- Application settings

Backward compatible with legacy .env format.
"""

from .loader import ConfigLoader, config

__all__ = ["ConfigLoader", "config"]
