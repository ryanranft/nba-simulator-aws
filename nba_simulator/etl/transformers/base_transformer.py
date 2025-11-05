"""
Base Transformer - Abstract Base Class for All Data Transformers

Provides common functionality for transforming data from various sources:
- Schema mapping (source → target)
- Data type conversion
- Validation
- Deduplication
- Normalization
- Error handling
- Progress tracking

Design Pattern: Template Method
- Define common transformation lifecycle
- Subclasses implement source-specific logic
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import hashlib

from ...utils import setup_logging


class TransformStatus(Enum):
    """Transform operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class TransformMetrics:
    """Metrics for a transform operation"""
    transformer_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Counts
    records_input: int = 0
    records_output: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    records_deduplicated: int = 0
    
    # Details
    status: TransformStatus = TransformStatus.PENDING
    error_message: Optional[str] = None
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['status'] = self.status.value
        result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result


class BaseTransformer(ABC):
    """
    Abstract base class for all data transformers.
    
    Implements the Template Method pattern:
    1. Validate input
    2. Transform data
    3. Validate output
    4. Collect metrics
    """
    
    def __init__(
        self,
        source_name: str,
        deduplicate: bool = True,
        validate: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize transformer.
        
        Args:
            source_name: Data source identifier (espn, basketball_reference, etc.)
            deduplicate: Enable deduplication
            validate: Enable output validation
            logger: Optional logger instance
        """
        self.source_name = source_name
        self.deduplicate = deduplicate
        self.validate_output = validate
        
        # Setup logging
        if logger:
            self.logger = logger
        else:
            self.logger = setup_logging(
                f'nba_simulator.etl.transformers.{self.__class__.__name__}'
            )
        
        # Metrics
        self.metrics = TransformMetrics(
            transformer_name=self.__class__.__name__,
            start_time=datetime.now(timezone.utc)
        )
        
        # Deduplication tracking
        self._seen_hashes: Set[str] = set()
        
        self.logger.info(f"Initialized {self.__class__.__name__} for {source_name}")
    
    def transform(self, data: Any) -> Tuple[List[Dict[str, Any]], TransformMetrics]:
        """
        Main transformation method (Template Method).
        
        Args:
            data: Raw input data (format depends on source)
            
        Returns:
            Tuple of (transformed_data, metrics)
        """
        self.logger.info(f"Starting transformation of {self.source_name} data")
        self.metrics.start_time = datetime.now(timezone.utc)
        self.metrics.status = TransformStatus.IN_PROGRESS
        
        try:
            # Step 1: Validate input
            is_valid, error_msg = self.validate_input(data)
            if not is_valid:
                self.metrics.status = TransformStatus.FAILED
                self.metrics.error_message = error_msg
                self.logger.error(f"Input validation failed: {error_msg}")
                return [], self.metrics
            
            # Step 2: Count input records
            self.metrics.records_input = self._count_input_records(data)
            self.logger.info(f"Input: {self.metrics.records_input} records")
            
            # Step 3: Transform data (source-specific implementation)
            transformed = self._transform_data(data)
            self.logger.info(f"Transformed: {len(transformed)} records")
            
            # Step 4: Deduplicate if enabled
            if self.deduplicate:
                transformed = self._deduplicate(transformed)
                self.logger.info(f"After deduplication: {len(transformed)} records")
            
            # Step 5: Validate output if enabled
            if self.validate_output:
                transformed = self._validate_transformed(transformed)
                self.logger.info(f"After validation: {len(transformed)} records")
            
            # Step 6: Update metrics
            self.metrics.records_output = len(transformed)
            self.metrics.status = TransformStatus.COMPLETED
            self.metrics.end_time = datetime.now(timezone.utc)
            self.metrics.duration_seconds = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
            
            self.logger.info(
                f"Transformation complete: {self.metrics.records_output} records "
                f"in {self.metrics.duration_seconds:.2f}s"
            )
            
            return transformed, self.metrics
            
        except Exception as e:
            self.metrics.status = TransformStatus.FAILED
            self.metrics.error_message = str(e)
            self.metrics.end_time = datetime.now(timezone.utc)
            self.logger.error(f"Transformation failed: {e}", exc_info=True)
            return [], self.metrics
    
    @abstractmethod
    def validate_input(self, data: Any) -> Tuple[bool, str]:
        """
        Validate input data format (source-specific).
        
        Args:
            data: Raw input data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def _transform_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Transform data from source format to target format (source-specific).
        
        This is the core transformation logic that subclasses must implement.
        
        Args:
            data: Validated input data
            
        Returns:
            List of transformed records as dictionaries
        """
        pass
    
    def _count_input_records(self, data: Any) -> int:
        """
        Count input records.
        
        Override in subclass if data format is not a simple list.
        
        Args:
            data: Input data
            
        Returns:
            Number of input records
        """
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Assume dict has a list of records
            for key in ['data', 'records', 'items', 'results']:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
        return 0
    
    def _deduplicate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate records based on content hash.
        
        Args:
            records: List of records
            
        Returns:
            Deduplicated list
        """
        deduplicated = []
        
        for record in records:
            # Create deterministic hash of record content
            record_hash = self._hash_record(record)
            
            if record_hash not in self._seen_hashes:
                self._seen_hashes.add(record_hash)
                deduplicated.append(record)
            else:
                self.metrics.records_deduplicated += 1
        
        return deduplicated
    
    def _hash_record(self, record: Dict[str, Any]) -> str:
        """
        Create deterministic hash of record content.
        
        Args:
            record: Record to hash
            
        Returns:
            MD5 hash string
        """
        # Sort keys for deterministic JSON
        record_json = json.dumps(record, sort_keys=True, default=str)
        return hashlib.md5(record_json.encode()).hexdigest()
    
    def _validate_transformed(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate transformed records.
        
        Override in subclass for custom validation logic.
        
        Args:
            records: Transformed records
            
        Returns:
            Valid records (invalid ones removed)
        """
        valid_records = []
        
        for i, record in enumerate(records):
            try:
                # Basic validation - record should be a dict
                if not isinstance(record, dict):
                    raise ValueError(f"Record {i} is not a dictionary")
                
                # Record should have at least one field
                if not record:
                    raise ValueError(f"Record {i} is empty")
                
                valid_records.append(record)
                
            except Exception as e:
                self.metrics.records_failed += 1
                self.metrics.validation_errors.append(str(e))
                self.logger.warning(f"Record {i} failed validation: {e}")
        
        return valid_records
    
    def map_field(
        self,
        source: Dict[str, Any],
        source_field: str,
        target_field: Optional[str] = None,
        default: Any = None,
        transform_fn: Optional[callable] = None
    ) -> Any:
        """
        Map a field from source to target format.
        
        Args:
            source: Source record
            source_field: Source field name (supports nested: 'player.name')
            target_field: Target field name (if different from source)
            default: Default value if field missing
            transform_fn: Optional transformation function
            
        Returns:
            Transformed field value
        """
        # Handle nested fields (e.g., 'player.name')
        value = source
        for key in source_field.split('.'):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        
        # Use default if missing
        if value is None:
            value = default
        
        # Apply transformation function
        if transform_fn and value is not None:
            try:
                value = transform_fn(value)
            except Exception as e:
                self.logger.warning(
                    f"Transform function failed for {source_field}: {e}"
                )
                value = default
        
        return value
    
    def get_metrics(self) -> TransformMetrics:
        """Get transformation metrics"""
        return self.metrics
    
    def reset(self):
        """Reset transformer state for reuse"""
        self._seen_hashes.clear()
        self.metrics = TransformMetrics(
            transformer_name=self.__class__.__name__,
            start_time=datetime.now(timezone.utc)
        )
        self.logger.info("Transformer reset")
