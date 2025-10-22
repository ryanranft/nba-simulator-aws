"""
DIMS Cache Module
Implements TTL-based caching for metric values with multiple backend support.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base class for cache backends."""

    def get(self, key: str) -> Optional[Tuple[Any, datetime]]:
        """Get cached value and expiration time."""
        raise NotImplementedError

    def set(self, key: str, value: Any, expires: datetime) -> bool:
        """Set cached value with expiration time."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete cached value."""
        raise NotImplementedError

    def clear(self) -> bool:
        """Clear all cached values."""
        raise NotImplementedError


class FileBackend(CacheBackend):
    """File-based cache backend."""

    def __init__(self, cache_dir: Path):
        """Initialize file backend."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file cache backend: {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Replace dots and special chars with underscores for safe filenames
        safe_key = key.replace('.', '_').replace('/', '_')
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Tuple[Any, datetime]]:
        """Get cached value and expiration time."""
        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            value = data.get('value')
            expires_str = data.get('expires')

            if expires_str:
                expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                return (value, expires)

            return None

        except Exception as e:
            logger.error(f"Error reading cache file {cache_file}: {e}")
            return None

    def set(self, key: str, value: Any, expires: datetime) -> bool:
        """Set cached value with expiration time."""
        cache_file = self._get_cache_path(key)

        try:
            data = {
                'value': value,
                'expires': expires.isoformat() + 'Z',
                'cached_at': datetime.now().isoformat() + 'Z'
            }

            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached {key} until {expires.isoformat()}")
            return True

        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cached value."""
        cache_file = self._get_cache_path(key)

        try:
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Deleted cache for {key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting cache file {cache_file}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cached values."""
        try:
            count = 0
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
                count += 1

            logger.info(f"Cleared {count} cache files")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        count = 0
        now = datetime.now()

        try:
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)

                    expires_str = data.get('expires')
                    if expires_str:
                        expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))

                        if expires < now:
                            cache_file.unlink()
                            count += 1
                            logger.debug(f"Removed expired cache: {cache_file.name}")

                except Exception as e:
                    logger.warning(f"Error processing cache file {cache_file}: {e}")
                    continue

            if count > 0:
                logger.info(f"Cleaned up {count} expired cache entries")

            return count

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return count


class MemoryBackend(CacheBackend):
    """In-memory cache backend."""

    def __init__(self):
        """Initialize memory backend."""
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        logger.info("Initialized memory cache backend")

    def get(self, key: str) -> Optional[Tuple[Any, datetime]]:
        """Get cached value and expiration time."""
        return self._cache.get(key)

    def set(self, key: str, value: Any, expires: datetime) -> bool:
        """Set cached value with expiration time."""
        self._cache[key] = (value, expires)
        logger.debug(f"Cached {key} until {expires.isoformat()}")
        return True

    def delete(self, key: str) -> bool:
        """Delete cached value."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Deleted cache for {key}")
            return True
        return False

    def clear(self) -> bool:
        """Clear all cached values."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return True

    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        count = 0
        now = datetime.now()

        expired_keys = [
            key for key, (value, expires) in self._cache.items()
            if expires < now
        ]

        for key in expired_keys:
            del self._cache[key]
            count += 1
            logger.debug(f"Removed expired cache: {key}")

        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")

        return count


class DIMSCache:
    """High-level cache manager for DIMS."""

    def __init__(self, config: Dict[str, Any], project_root: Path):
        """
        Initialize DIMS cache.

        Args:
            config: DIMS configuration dict
            project_root: Project root path
        """
        self.config = config
        self.project_root = project_root
        self.cache_config = config.get('cache', {})

        # Check if caching is enabled
        self.enabled = self.cache_config.get('enabled', True)

        if not self.enabled:
            logger.info("Caching is disabled")
            self.backend = None
            return

        # Initialize backend
        backend_type = self.cache_config.get('backend', 'file')

        if backend_type == 'file':
            cache_dir = project_root / self.cache_config.get('cache_dir', 'inventory/cache')
            self.backend = FileBackend(cache_dir)
        elif backend_type == 'memory':
            self.backend = MemoryBackend()
        elif backend_type == 'redis':
            # TODO: Implement Redis backend
            logger.warning("Redis backend not yet implemented, falling back to file")
            cache_dir = project_root / self.cache_config.get('cache_dir', 'inventory/cache')
            self.backend = FileBackend(cache_dir)
        else:
            logger.warning(f"Unknown backend type '{backend_type}', using file")
            cache_dir = project_root / self.cache_config.get('cache_dir', 'inventory/cache')
            self.backend = FileBackend(cache_dir)

        # Get TTL configuration
        self.default_ttl_hours = self.cache_config.get('default_ttl_hours', 24)
        self.ttl_overrides = self.cache_config.get('ttl_overrides', {})

        logger.info(f"Cache initialized (enabled={self.enabled}, backend={backend_type}, default_ttl={self.default_ttl_hours}h)")

    def _get_ttl_hours(self, metric_path: str) -> int:
        """Get TTL hours for a metric."""
        # Check for specific override first
        if metric_path in self.ttl_overrides:
            return self.ttl_overrides[metric_path]

        # Check for category override (e.g., 's3_storage' from 's3_storage.total_objects')
        parts = metric_path.split('.')
        if len(parts) > 1:
            category = parts[0]
            if category in self.ttl_overrides:
                return self.ttl_overrides[category]

        # Use default
        return self.default_ttl_hours

    def _make_key(self, metric_category: str, metric_name: str) -> str:
        """Create cache key from metric category and name."""
        return f"{metric_category}.{metric_name}"

    def get(self, metric_category: str, metric_name: str) -> Optional[Any]:
        """
        Get cached metric value if not expired.

        Args:
            metric_category: Metric category
            metric_name: Metric name

        Returns:
            Cached value if valid, None otherwise
        """
        if not self.enabled or not self.backend:
            return None

        key = self._make_key(metric_category, metric_name)
        result = self.backend.get(key)

        if result is None:
            logger.debug(f"Cache miss: {key}")
            return None

        value, expires = result
        now = datetime.now()

        if expires < now:
            # Expired
            logger.debug(f"Cache expired: {key}")
            self.backend.delete(key)
            return None

        logger.debug(f"Cache hit: {key} (expires {expires.isoformat()})")
        return value

    def set(self, metric_category: str, metric_name: str, value: Any) -> bool:
        """
        Cache a metric value with TTL.

        Args:
            metric_category: Metric category
            metric_name: Metric name
            value: Value to cache

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.backend:
            return False

        key = self._make_key(metric_category, metric_name)
        ttl_hours = self._get_ttl_hours(key)
        expires = datetime.now() + timedelta(hours=ttl_hours)

        return self.backend.set(key, value, expires)

    def invalidate(self, metric_category: str, metric_name: str) -> bool:
        """
        Invalidate (delete) a cached metric.

        Args:
            metric_category: Metric category
            metric_name: Metric name

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.backend:
            return False

        key = self._make_key(metric_category, metric_name)
        return self.backend.delete(key)

    def clear_all(self) -> bool:
        """Clear all cached values."""
        if not self.enabled or not self.backend:
            return False

        return self.backend.clear()

    def cleanup(self) -> int:
        """Remove expired cache entries."""
        if not self.enabled or not self.backend:
            return 0

        if hasattr(self.backend, 'cleanup_expired'):
            return self.backend.cleanup_expired()

        return 0

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics and information."""
        if not self.enabled:
            return {
                'enabled': False,
                'backend': None,
                'entries': 0
            }

        backend_type = self.cache_config.get('backend', 'file')

        # Count cache entries
        entries = 0
        if isinstance(self.backend, FileBackend):
            entries = len(list(self.backend.cache_dir.glob('*.json')))
        elif isinstance(self.backend, MemoryBackend):
            entries = len(self.backend._cache)

        return {
            'enabled': True,
            'backend': backend_type,
            'entries': entries,
            'default_ttl_hours': self.default_ttl_hours,
            'ttl_overrides': self.ttl_overrides
        }
