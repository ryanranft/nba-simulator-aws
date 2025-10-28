"""
Base Scraper Class

Abstract base class for all data scrapers.
Provides common functionality: retry logic, rate limiting, error handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging
from ...utils.logging import setup_logging


class BaseScraper(ABC):
    """
    Abstract base class for data scrapers.
    
    Provides:
    - Retry logic with exponential backoff
    - Rate limiting
    - Error handling and logging
    - Health checks
    - Configuration management
    
    Usage:
        class MyScr aper(BaseScraper):
            def __init__(self):
                super().__init__("my_scraper")
            
            def extract(self):
                # Implementation
                pass
            
            def validate(self, data):
                # Validation logic
                return True
    """
    
    def __init__(
        self, 
        name: str, 
        config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize base scraper.
        
        Args:
            name: Scraper name for logging
            config: Optional configuration dictionary
            max_retries: Maximum retry attempts for failed operations
            rate_limit_delay: Delay between requests (seconds)
        """
        self.name = name
        self.config = config or {}
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.logger = setup_logging(f"etl.{name}")
        self._last_request_time = 0
        self._setup()
    
    def _setup(self):
        """
        Setup hook called after initialization.
        Override in subclasses for custom setup.
        """
        self.logger.info(f"Initialized {self.name} scraper")
    
    @abstractmethod
    def extract(self, *args, **kwargs) -> Any:
        """
        Extract data from source.
        
        Must be implemented by subclasses.
        
        Returns:
            Extracted data in appropriate format
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        Validate extracted data.
        
        Args:
            data: Data to validate
        
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    def run_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute function with retry logic and exponential backoff.
        
        Args:
            func: Function to execute
            *args: Function positional arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If all retries exhausted
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self._rate_limit()
                result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                if attempt == self.max_retries:
                    self.logger.error(
                        f"{self.name}: Failed after {self.max_retries} attempts: {e}"
                    )
                    raise
                
                wait_time = self.rate_limit_delay * (2 ** (attempt - 1))
                self.logger.warning(
                    f"{self.name}: Attempt {attempt}/{self.max_retries} failed: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
    
    def _rate_limit(self):
        """
        Enforce rate limiting between requests.
        """
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if scraper is operational.
        
        Returns:
            Dictionary with health check results
        """
        return {
            "name": self.name,
            "status": "operational",
            "config": bool(self.config),
            "last_request": self._last_request_time
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraper statistics.
        
        Returns:
            Dictionary with scraper stats
        """
        return {
            "name": self.name,
            "max_retries": self.max_retries,
            "rate_limit_delay": self.rate_limit_delay
        }

