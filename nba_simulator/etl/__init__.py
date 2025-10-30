"""
ETL Framework Module

Consolidated ETL scrapers organized by data source with unified interfaces.

Phase 2 delivers:
- Base infrastructure (async scrapers, rate limiting, retry, error handling)
- Extractors by source (ESPN, Basketball Reference, hoopR, NBA API)
- Transformers for data normalization
- Loaders for database/S3 persistence
- Validation framework

Version: 0.2.0 (Phase 2: ETL Framework)
"""

__version__ = "0.2.0"
__phase__ = "Phase 2: ETL Framework"

__all__ = []
