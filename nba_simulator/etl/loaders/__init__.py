"""
ETL Loaders

Data loading layer for writing transformed data to:
- PostgreSQL RDS (54 tables across 4 schemas)
- AWS S3 data lake (raw data storage)
"""

from .base_loader import BaseLoader, TransactionManager, transaction_manager
from .rds_loader import RDSLoader, TemporalEventsLoader
from .s3_loader import (
    S3Loader,
    ESPNLoader,
    BasketballReferenceLoader
)

__all__ = [
    # Base classes
    'BaseLoader',
    'TransactionManager',
    'transaction_manager',
    
    # RDS loaders
    'RDSLoader',
    'TemporalEventsLoader',
    
    # S3 loaders
    'S3Loader',
    'ESPNLoader',
    'BasketballReferenceLoader',
]
