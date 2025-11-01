"""
NBA Simulator AWS - Production Data Pipeline & Simulation System

A comprehensive basketball analytics platform combining:
- Multi-source ETL pipelines (ESPN, Basketball Reference, NBA API, hoopR)
- PostgreSQL data warehouse (40+ tables, 20M+ records)
- S3 data lake (146,115+ files, 119+ GB)
- Machine learning prediction models
- Historical game simulation engine (1946-2025)
- Phase 8: Box score snapshot generation system

Author: Ryan Ranft
Created: 2025
Refactored: October 2025
"""

__version__ = '2.0.0-alpha'
__author__ = 'Ryan Ranft'

# Package metadata
__all__ = [
    'config',
    'database', 
    'utils'
]

# Import submodules for convenient access
from . import config
from . import database
from . import utils
