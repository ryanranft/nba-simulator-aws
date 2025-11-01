"""
ETL Pipeline Module

Comprehensive ETL infrastructure for NBA data collection:
- Base classes for scrapers with rate limiting, retry logic, error handling
- Extractors for all data sources (ESPN, Basketball Reference, hoopR, NBA API, Kaggle)
- Transformers for data normalization and temporal event generation
- Loaders for multi-schema database loading (public, odds, rag, raw_data)
- Validation framework for data quality assurance

Author: Ryan Ranft
Phase: 2 - ETL Pipeline Migration
"""

__version__ = '2.0.0-alpha'

__all__ = [
    'base',
    'extractors',
    'transformers',
    'loaders',
    'validation'
]

# Import submodules for convenient access
from . import base
from . import extractors
from . import transformers
from . import loaders
from . import validation
