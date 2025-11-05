"""
DIMS Cache Module - Intelligent Caching Layer

Provides caching for frequently accessed metrics with TTL support.

Features:
- In-memory caching with TTL
- Configurable cache sizes
- Cache invalidation strategies
- Statistics and monitoring

Based on: scripts/monitoring/dims/cache.py
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from ...utils import setup_logging


class DIMSCache:
    """
    Intelligent caching layer for DIMS metrics.
    
    Reduces load on metric calculation commands by caching results.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize DIMS cache.
        
        Args:
            config: Cache configuration
            logger: Optional logger instance
        """
        self.config = config or {}
        self.logger = logger or setup_logging('nba_simulator.monitoring.dims.cache')
        
        # Cache storage
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.default_ttl = self.config.get('default_ttl', 3600)  # 1 hour
        self.max_size = self.config.get('max_size', 1000)
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        self.logger.info("DIMS Cache initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self.misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry['expires_at'] < datetime.now(timezone.utc):
            del self._cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry['value']
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = use default)
            
        Returns:
            True if successful
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Evict if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()
        
        self._cache[key] = {
            'value': value,
            'expires_at': datetime.now(timezone.utc) + timedelta(seconds=ttl),
            'created_at': datetime.now(timezone.utc)
        }
        
        return True
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was removed
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        self.logger.info(f"Cleared {count} cache entries")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry['expires_at'] < now
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        # Find oldest entry by created_at
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['created_at']
        )
        
        del self._cache[oldest_key]
        self.evictions += 1
        self.logger.debug(f"Evicted LRU entry: {oldest_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def info(self) -> str:
        """Get cache info as string"""
        stats = self.get_stats()
        return (
            f"Cache Stats:\n"
            f"  Size: {stats['size']}/{stats['max_size']}\n"
            f"  Hit Rate: {stats['hit_rate']}%\n"
            f"  Hits: {stats['hits']}\n"
            f"  Misses: {stats['misses']}\n"
            f"  Evictions: {stats['evictions']}"
        )
