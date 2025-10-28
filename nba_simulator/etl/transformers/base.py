"""
Base Transformer Class

Abstract base class for data transformers.
Transforms raw data from extractors into standardized format.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
from ...utils.logging import setup_logging


class BaseTransformer(ABC):
    """
    Abstract base class for data transformers.
    
    Transforms raw data from extractors into standardized unified format.
    Provides validation, quality checks, and error handling.
    
    Usage:
        class MyTransformer(BaseTransformer):
            def transform(self, data):
                # Transform logic
                return standardized_data
            
            def validate_schema(self, data):
                # Validation logic
                return True
    """
    
    def __init__(self, name: str, source: str):
        """
        Initialize transformer.
        
        Args:
            name: Transformer name for logging
            source: Data source (hoopr, espn, basketball_reference, nba_api)
        """
        self.name = name
        self.source = source
        self.logger = setup_logging(f"transformer.{name}")
        self._setup()
    
    def _setup(self):
        """Setup hook called after initialization"""
        self.logger.info(f"Initialized {self.name} transformer for {self.source}")
    
    @abstractmethod
    def transform(self, data: Any) -> Dict[str, Any]:
        """
        Transform data to standardized format.
        
        Must be implemented by subclasses.
        
        Args:
            data: Raw data from extractor
        
        Returns:
            Transformed data in unified format
        """
        pass
    
    @abstractmethod
    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate transformed data against schema.
        
        Args:
            data: Transformed data
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def transform_batch(self, data_list: List[Any]) -> List[Dict[str, Any]]:
        """
        Transform a batch of data items.
        
        Args:
            data_list: List of raw data items
        
        Returns:
            List of transformed data items
        """
        results = []
        errors = 0
        
        for i, item in enumerate(data_list):
            try:
                transformed = self.transform(item)
                if self.validate_schema(transformed):
                    results.append(transformed)
                else:
                    self.logger.warning(f"Item {i} failed schema validation")
                    errors += 1
            except Exception as e:
                self.logger.error(f"Error transforming item {i}: {e}")
                errors += 1
        
        self.logger.info(
            f"Batch transform complete: {len(results)} success, {errors} errors"
        )
        
        return results
    
    def get_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate data quality metrics.
        
        Args:
            data: Transformed data
        
        Returns:
            Dictionary of quality metrics
        """
        return {
            'completeness': self._check_completeness(data),
            'consistency': self._check_consistency(data),
            'validity': self.validate_schema(data),
            'source': self.source
        }
    
    def _check_completeness(self, data: Dict[str, Any]) -> float:
        """
        Check data completeness (% of required fields present).
        
        Args:
            data: Data to check
        
        Returns:
            Completeness score (0.0 to 1.0)
        """
        required_fields = self._get_required_fields()
        if not required_fields:
            return 1.0
        
        present = sum(1 for field in required_fields if data.get(field) is not None)
        return present / len(required_fields)
    
    def _check_consistency(self, data: Dict[str, Any]) -> bool:
        """
        Check data consistency (internal logical consistency).
        
        Args:
            data: Data to check
        
        Returns:
            True if consistent
        """
        # Base implementation - override in subclasses for specific checks
        return True
    
    def _get_required_fields(self) -> List[str]:
        """
        Get list of required fields for this transformer.
        
        Override in subclasses.
        
        Returns:
            List of required field names
        """
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get transformer statistics.
        
        Returns:
            Dictionary with transformer stats
        """
        return {
            'name': self.name,
            'source': self.source
        }

