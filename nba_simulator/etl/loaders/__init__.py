"""
ETL Loaders

Data loading layer for writing transformed data to:
- PostgreSQL RDS (54 tables across 4 schemas)
- AWS S3 data lake (raw data storage)

Features:
- Bulk loading with COPY command (100K+ rows/sec)
- Upsert support (INSERT ... ON CONFLICT)
- Multipart S3 uploads
- Transaction management
- Retry logic with exponential backoff
- Progress tracking and metrics

Usage Examples:

    # Load to PostgreSQL
    from nba_simulator.etl.loaders import RDSLoader
    
    loader = RDSLoader(
        table_name='games',
        schema='public',
        upsert=True
    )
    metrics = await loader.load(game_data)
    print(f"Loaded {metrics.records_loaded} records")
    
    # Load temporal events
    from nba_simulator.etl.loaders import TemporalEventsLoader
    
    loader = TemporalEventsLoader()
    await loader.load(temporal_events)
    await loader.create_temporal_indexes()
    
    # Upload to S3
    from nba_simulator.etl.loaders import ESPNLoader
    
    loader = ESPNLoader()
    await loader.load({
        'game_401360853.json': game_data,
        'game_401360854.json': game_data2
    })
"""

from .base_loader import BaseLoader, TransactionManager, transaction_manager, LoadStatus, LoadMetrics
from .rds_loader import RDSLoader, TemporalEventsLoader
from .s3_loader import S3Loader, ESPNLoader, BasketballReferenceLoader

__all__ = [
    # Base classes
    "BaseLoader",
    "TransactionManager",
    "transaction_manager",
    "LoadStatus",
    "LoadMetrics",
    # RDS loaders
    "RDSLoader",
    "TemporalEventsLoader",
    # S3 loaders
    "S3Loader",
    "ESPNLoader",
    "BasketballReferenceLoader",
]
