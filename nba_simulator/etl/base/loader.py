"""
Base Loader Class

Abstract base class for data loaders (database, file, etc.).
"""

from abc import abstractmethod
from typing import Any, List, Dict
from .scraper import BaseScraper


class BaseLoader(BaseScraper):
    """
    Base class for data loaders.

    Extends BaseScraper for loading data to destinations (database, S3, etc.).

    Usage:
        class PostgresLoader(BaseLoader):
            def __init__(self):
                super().__init__("postgres")

            def extract(self, data):
                # Load to database
                return self.load_to_postgres(data)

            def validate(self, data):
                return len(data) > 0
    """

    @abstractmethod
    def load(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Load data to destination.

        Args:
            data: Data to load
            **kwargs: Additional load options

        Returns:
            Dictionary with load results (records_loaded, errors, etc.)
        """
        pass

    def extract(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Implement extract as load operation for consistency with BaseScraper.

        Args:
            data: Data to load
            **kwargs: Additional options

        Returns:
            Load results
        """
        return self.load(data, **kwargs)

    def validate(self, data: Any) -> bool:
        """
        Validate data before loading.

        Args:
            data: Data to validate

        Returns:
            True if data is valid for loading
        """
        if data is None:
            self.logger.warning(f"{self.name}: Cannot load None data")
            return False

        if isinstance(data, (list, tuple)) and len(data) == 0:
            self.logger.warning(f"{self.name}: Cannot load empty list")
            return False

        return True

    def batch_load(
        self,
        data: List[Any],
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Load data in batches for better performance.

        Args:
            data: List of items to load
            batch_size: Number of items per batch

        Returns:
            Dictionary with aggregated load results
        """
        total_loaded = 0
        total_errors = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            self.logger.info(
                f"{self.name}: Loading batch {i//batch_size + 1} "
                f"({len(batch)} items)"
            )

            try:
                result = self.load(batch)
                total_loaded += result.get('records_loaded', 0)
                total_errors += result.get('errors', 0)
            except Exception as e:
                self.logger.error(f"{self.name}: Batch load failed: {e}")
                total_errors += len(batch)

        return {
            'records_loaded': total_loaded,
            'errors': total_errors,
            'batches': (len(data) + batch_size - 1) // batch_size
        }

