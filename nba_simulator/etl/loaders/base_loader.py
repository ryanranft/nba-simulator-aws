"""
Base Loader - Abstract Base Class for All Data Loaders

Provides common functionality for loading data to various destinations:
- PostgreSQL RDS (54 tables across 4 schemas)
- AWS S3 (data lake storage)
- Batch processing with progress tracking
- Transaction management
- Error handling and retry logic
- Metrics collection

Design Pattern: Template Method
- Define common loading lifecycle
- Subclasses implement destination-specific logic
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import time

from ...database import get_db_connection
from ...utils import setup_logging


class LoadStatus(Enum):
    """Load operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class LoadMetrics:
    """Metrics for a load operation"""
    loader_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Counts
    records_attempted: int = 0
    records_loaded: int = 0
    records_failed: int = 0
    batches_processed: int = 0
    batches_failed: int = 0
    
    # Performance
    records_per_second: float = 0.0
    bytes_processed: int = 0
    
    # Status
    status: LoadStatus = LoadStatus.PENDING
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    def update_duration(self):
        """Update duration and rate calculations"""
        if self.end_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
            if self.duration_seconds > 0:
                self.records_per_second = self.records_loaded / self.duration_seconds


class TransactionManager:
    """
    Context manager for database transactions.
    
    Provides:
    - Automatic commit on success
    - Automatic rollback on failure
    - Savepoints for nested transactions
    - Transaction timing
    
    Usage:
        async with TransactionManager(conn) as txn:
            await txn.execute("INSERT INTO table ...")
            await txn.execute("UPDATE table ...")
            # Auto-commits on exit
    """
    
    def __init__(self, connection):
        self.conn = connection
        self.start_time = None
        self.savepoints = []
        
    async def __aenter__(self):
        """Begin transaction"""
        self.start_time = datetime.now(timezone.utc)
        # Connection already in transaction by default with asyncpg
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction"""
        if exc_type is None:
            # Success - commit
            await self.conn.commit() if hasattr(self.conn, 'commit') else None
        else:
            # Failure - rollback
            await self.conn.rollback() if hasattr(self.conn, 'rollback') else None
        return False  # Propagate exceptions
    
    async def execute(self, query: str, *args):
        """Execute query within transaction"""
        return await self.conn.execute(query, *args)
    
    async def executemany(self, query: str, args_list: List[Tuple]):
        """Execute many within transaction"""
        return await self.conn.executemany(query, args_list)
    
    async def savepoint(self, name: str):
        """Create savepoint"""
        await self.conn.execute(f"SAVEPOINT {name}")
        self.savepoints.append(name)
    
    async def rollback_to_savepoint(self, name: str):
        """Rollback to savepoint"""
        await self.conn.execute(f"ROLLBACK TO SAVEPOINT {name}")


class BaseLoader(ABC):
    """
    Abstract base class for all data loaders.
    
    Template Method Pattern:
    1. validate_input() - Check input data
    2. prepare_data() - Transform for loading
    3. load_batch() - Load single batch
    4. verify_load() - Verify loaded data
    5. cleanup() - Post-load cleanup
    
    Subclasses must implement destination-specific logic.
    """
    
    def __init__(
        self,
        batch_size: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base loader.
        
        Args:
            batch_size: Records per batch
            max_retries: Maximum retry attempts
            retry_delay: Seconds between retries
            config: Additional configuration
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.config = config or {}
        
        # Setup logging
        self.logger = setup_logging(
            name=self.__class__.__name__,
            level=self.config.get('log_level', 'INFO')
        )
        
        # Metrics
        self.metrics = LoadMetrics(
            loader_name=self.__class__.__name__,
            start_time=datetime.now(timezone.utc)
        )
        
        self.logger.info(f"Initialized {self.__class__.__name__}")
        self.logger.info(f"Batch size: {self.batch_size:,}")
        self.logger.info(f"Max retries: {self.max_retries}")
    
    @abstractmethod
    async def validate_input(self, data: Any) -> Tuple[bool, str]:
        """
        Validate input data before loading.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    async def prepare_data(self, data: Any) -> List[Any]:
        """
        Prepare data for loading (transform, clean, batch).
        
        Args:
            data: Raw input data
            
        Returns:
            List of prepared records
        """
        pass
    
    @abstractmethod
    async def load_batch(self, batch: List[Any]) -> Tuple[int, int]:
        """
        Load a single batch of data.
        
        Args:
            batch: List of records to load
            
        Returns:
            Tuple of (records_loaded, records_failed)
        """
        pass
    
    async def verify_load(self, expected_count: int) -> bool:
        """
        Verify loaded data (optional).
        
        Args:
            expected_count: Expected number of records
            
        Returns:
            True if verification passed
        """
        return True
    
    async def cleanup(self):
        """Cleanup resources after loading (optional)"""
        pass
    
    async def load(self, data: Any) -> LoadMetrics:
        """
        Main loading workflow (Template Method).
        
        Args:
            data: Data to load
            
        Returns:
            LoadMetrics with results
        """
        self.metrics.start_time = datetime.now(timezone.utc)
        self.metrics.status = LoadStatus.IN_PROGRESS
        
        try:
            # Step 1: Validate input
            self.logger.info("Validating input data...")
            is_valid, error_msg = await self.validate_input(data)
            if not is_valid:
                self.metrics.status = LoadStatus.FAILED
                self.metrics.error_message = f"Validation failed: {error_msg}"
                self.logger.error(self.metrics.error_message)
                return self.metrics
            
            # Step 2: Prepare data
            self.logger.info("Preparing data for loading...")
            prepared_data = await self.prepare_data(data)
            self.metrics.records_attempted = len(prepared_data)
            self.logger.info(f"Prepared {len(prepared_data):,} records")
            
            # Step 3: Load in batches
            self.logger.info("Loading data in batches...")
            await self._load_batches(prepared_data)
            
            # Step 4: Verify load
            if self.config.get('verify', True):
                self.logger.info("Verifying loaded data...")
                verification_passed = await self.verify_load(self.metrics.records_loaded)
                if not verification_passed:
                    self.logger.warning("Verification failed!")
                    self.metrics.status = LoadStatus.PARTIAL
            
            # Step 5: Cleanup
            await self.cleanup()
            
            # Finalize metrics
            self.metrics.end_time = datetime.now(timezone.utc)
            self.metrics.update_duration()
            
            if self.metrics.records_failed == 0:
                self.metrics.status = LoadStatus.COMPLETED
            else:
                self.metrics.status = LoadStatus.PARTIAL
            
            self._log_summary()
            return self.metrics
            
        except Exception as e:
            self.metrics.end_time = datetime.now(timezone.utc)
            self.metrics.status = LoadStatus.FAILED
            self.metrics.error_message = str(e)
            self.logger.error(f"Load failed: {e}", exc_info=True)
            return self.metrics
    
    async def _load_batches(self, data: List[Any]):
        """Load data in batches with retry logic"""
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(data), self.batch_size):
            batch_num = i // self.batch_size + 1
            batch = data[i:i + self.batch_size]
            
            self.logger.info(f"Loading batch {batch_num}/{total_batches} ({len(batch)} records)...")
            
            # Retry logic
            for attempt in range(1, self.max_retries + 1):
                try:
                    loaded, failed = await self.load_batch(batch)
                    self.metrics.records_loaded += loaded
                    self.metrics.records_failed += failed
                    self.metrics.batches_processed += 1
                    
                    if failed > 0:
                        self.logger.warning(f"Batch {batch_num}: {failed} records failed")
                    
                    # Success - break retry loop
                    break
                    
                except Exception as e:
                    self.logger.error(f"Batch {batch_num} attempt {attempt} failed: {e}")
                    
                    if attempt == self.max_retries:
                        # Final attempt failed
                        self.metrics.batches_failed += 1
                        self.metrics.records_failed += len(batch)
                        self.logger.error(f"Batch {batch_num} failed after {self.max_retries} attempts")
                    else:
                        # Retry after delay
                        await self._async_sleep(self.retry_delay * attempt)
            
            # Log progress every 10 batches
            if batch_num % 10 == 0:
                self._log_progress(batch_num, total_batches)
    
    def _log_progress(self, batch_num: int, total_batches: int):
        """Log loading progress"""
        pct = (batch_num / total_batches) * 100
        elapsed = (datetime.now(timezone.utc) - self.metrics.start_time).total_seconds()
        rate = self.metrics.records_loaded / elapsed if elapsed > 0 else 0
        eta = (self.metrics.records_attempted - self.metrics.records_loaded) / rate if rate > 0 else 0
        
        self.logger.info(
            f"Progress: {batch_num}/{total_batches} ({pct:.1f}%) | "
            f"Loaded: {self.metrics.records_loaded:,} | "
            f"Failed: {self.metrics.records_failed:,} | "
            f"Rate: {rate:.0f} rec/sec | "
            f"ETA: {eta/60:.1f} min"
        )
    
    def _log_summary(self):
        """Log final summary"""
        self.logger.info("=" * 70)
        self.logger.info("LOAD SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Status: {self.metrics.status.value}")
        self.logger.info(f"Records attempted: {self.metrics.records_attempted:,}")
        self.logger.info(f"Records loaded: {self.metrics.records_loaded:,}")
        self.logger.info(f"Records failed: {self.metrics.records_failed:,}")
        self.logger.info(f"Batches processed: {self.metrics.batches_processed:,}")
        self.logger.info(f"Batches failed: {self.metrics.batches_failed:,}")
        self.logger.info(f"Duration: {self.metrics.duration_seconds:.1f} seconds")
        self.logger.info(f"Rate: {self.metrics.records_per_second:.0f} records/second")
        
        success_rate = (self.metrics.records_loaded / self.metrics.records_attempted * 100) if self.metrics.records_attempted > 0 else 0
        self.logger.info(f"Success rate: {success_rate:.2f}%")
        self.logger.info("=" * 70)
    
    async def _async_sleep(self, seconds: float):
        """Async sleep for retry delays"""
        import asyncio
        await asyncio.sleep(seconds)


# Singleton transaction manager for convenience
transaction_manager = TransactionManager


__all__ = [
    'BaseLoader',
    'TransactionManager',
    'transaction_manager',
    'LoadStatus',
    'LoadMetrics',
]
