#!/usr/bin/env python3
"""
Feature Store for NBA Analytics Platform.

This module provides a comprehensive feature store implementation for managing,
storing, and retrieving NBA analytics features. It supports feature registration,
versioning, caching, and efficient retrieval for machine learning pipelines.
"""

import logging
import json
import hashlib
import pickle  # nosec B403 - pickle used for feature serialization
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from collections import OrderedDict
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Enumeration of supported feature types."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    EMBEDDING = "embedding"
    TIME_SERIES = "time_series"


class FeatureStatus(Enum):
    """Enumeration of feature statuses."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    ARCHIVED = "archived"


@dataclass
class FeatureMetadata:
    """Metadata for a feature in the feature store."""

    name: str
    version: str
    feature_type: FeatureType
    description: str
    created_at: datetime
    updated_at: datetime
    status: FeatureStatus = FeatureStatus.ACTIVE
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    schema: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data["feature_type"] = self.feature_type.value
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureMetadata":
        """Create metadata from dictionary."""
        data["feature_type"] = FeatureType(data["feature_type"])
        data["status"] = FeatureStatus(data["status"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class LRUCache:
    """Thread-safe LRU cache for feature values."""

    def __init__(self, capacity: int = 1000):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items to cache
        """
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.Lock()
        logger.info(f"Initialized LRU cache with capacity {capacity}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        """
        Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached items."""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")

    def size(self) -> int:
        """Get current cache size."""
        with self.lock:
            return len(self.cache)


class FeatureStore:
    """
    Feature store for NBA analytics platform.

    Manages feature registration, storage, retrieval, and versioning.
    """

    def __init__(
        self,
        storage_path: Union[str, Path],
        cache_size: int = 1000,
        enable_cache: bool = True,
    ):
        """
        Initialize feature store.

        Args:
            storage_path: Path to storage directory
            cache_size: Size of LRU cache
            enable_cache: Whether to enable caching

        Raises:
            ValueError: If storage_path is invalid
        """
        self.storage_path = Path(storage_path)
        self.enable_cache = enable_cache

        if not self.storage_path:
            raise ValueError("storage_path cannot be empty")

        # Create storage directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.storage_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
        self.features_path = self.storage_path / "features"
        self.features_path.mkdir(exist_ok=True)

        # Initialize cache
        self.cache = LRUCache(capacity=cache_size) if enable_cache else None

        # Initialize metadata database
        self.db_path = self.storage_path / "feature_store.db"
        self._init_database()

        # Feature computation functions
        self.feature_functions: Dict[str, Callable] = {}

        logger.info(f"Initialized FeatureStore at {self.storage_path}")

    def _init_database(self) -> None:
        """Initialize SQLite database for metadata."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS features (
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    feature_type TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    dependencies TEXT,
                    tags TEXT,
                    schema TEXT,
                    statistics TEXT,
                    PRIMARY KEY (name, version)
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feature_name 
                ON features(name)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feature_status 
                ON features(status)
            """
            )

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def register_feature(
        self,
        name: str,
        version: str,
        feature_type: FeatureType,
        description: str,
        computation_fn: Optional[Callable] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> FeatureMetadata:
        """
        Register a new feature in the store.

        Args:
            name: Feature name
            version: Feature version
            feature_type: Type of feature
            description: Feature description
            computation_fn: Optional function to compute feature
            dependencies: List of dependent features
            tags: List of tags for categorization
            schema: Feature schema definition

        Returns:
            FeatureMetadata object

        Raises:
            ValueError: If feature already exists or invalid parameters
        """
        if not name or not version:
            raise ValueError("Feature name and version are required")

        if self.feature_exists(name, version):
            raise ValueError(f"Feature {name} version {version} already exists")

        now = datetime.utcnow()
        metadata = FeatureMetadata(
            name=name,
            version=version,
            feature_type=feature_type,
            description=description,
            created_at=now,
            updated_at=now,
            dependencies=dependencies or [],
            tags=tags or [],
            schema=schema or {},
        )

        try:
            # Save metadata to database
            self._save_metadata(metadata)

            # Register computation function if provided
            if computation_fn:
                feature_key = f"{name}:{version}"
                self.feature_functions[feature_key] = computation_fn

            logger.info(f"Registered feature {name} version {version}")
            return metadata
        except Exception as e:
            logger.error(f"Failed to register feature {name}: {e}")
            raise

    def _save_metadata(self, metadata: FeatureMetadata) -> None:
        """Save feature metadata to database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO features 
                (name, version, feature_type, description, created_at, 
                 updated_at, status, dependencies, tags, schema, statistics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metadata.name,
                    metadata.version,
                    metadata.feature_type.value,
                    metadata.description,
                    metadata.created_at.isoformat(),
                    metadata.updated_at.isoformat(),
                    metadata.status.value,
                    json.dumps(metadata.dependencies),
                    json.dumps(metadata.tags),
                    json.dumps(metadata.schema),
                    json.dumps(metadata.statistics),
                ),
            )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise

    def feature_exists(self, name: str, version: str) -> bool:
        """
        Check if a feature exists.

        Args:
            name: Feature name
            version: Feature version

        Returns:
            True if feature exists, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM features WHERE name = ? AND version = ?",
                (name, version),
            )
            count = cursor.fetchone()[0]
            conn.close()

            return count > 0
        except Exception as e:
            logger.error(f"Error checking feature existence: {e}")
            return False

    def get_metadata(self, name: str, version: str) -> Optional[FeatureMetadata]:
        """
        Get feature metadata.

        Args:
            name: Feature name
            version: Feature version

        Returns:
            FeatureMetadata or None if not found
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM features WHERE name = ? AND version = ?", (name, version)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return FeatureMetadata(
                name=row[0],
                version=row[1],
                feature_type=FeatureType(row[2]),
                description=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                status=FeatureStatus(row[6]),
                dependencies=json.loads(row[7]),
                tags=json.loads(row[8]),
                schema=json.loads(row[9]),
                statistics=json.loads(row[10]),
            )
        except Exception as e:
            logger.error(f"Failed to get metadata for {name}:{version}: {e}")
            return None

    def store_feature(
        self,
        name: str,
        version: str,
        entity_id: str,
        value: Any,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Store a feature value.

        Args:
            name: Feature name
            version: Feature version
            entity_id: Entity identifier (e.g., player_id, game_id)
            value: Feature value
            timestamp: Optional timestamp for the feature

        Returns:
            True if successful, False otherwise
        """
        if not self.feature_exists(name, version):
            logger.error(f"Feature {name}:{version} not registered")
            return False

        try:
            feature_key = self._get_feature_key(name, version, entity_id)
            feature_data = {
                "value": value,
                "timestamp": (timestamp or datetime.utcnow()).isoformat(),
                "entity_id": entity_id,
            }

            # Store to disk
            feature_file = self.features_path / f"{feature_key}.pkl"
            with open(feature_file, "wb") as f:
                pickle.dump(feature_data, f)

            # Update cache
            if self.cache:
                self.cache.put(feature_key, feature_data)

            logger.debug(f"Stored feature {name}:{version} for entity {entity_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store feature: {e}")
            return False

    def get_feature(
        self, name: str, version: str, entity_id: str, compute_if_missing: bool = True
    ) -> Optional[Any]:
        """
        Retrieve a feature value.

        Args:
            name: Feature name
            version: Feature version
            entity_id: Entity identifier
            compute_if_missing: Whether to compute feature if not found

        Returns:
            Feature value or None if not found
        """
        feature_key = self._get_feature_key(name, version, entity_id)

        # Check cache first
        if self.cache:
            cached_value = self.cache.get(feature_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {feature_key}")
                return cached_value["value"]

        # Check disk storage
        feature_file = self.features_path / f"{feature_key}.pkl"
        if feature_file.exists():
            try:
                with open(feature_file, "rb") as f:
                    feature_data = pickle.load(f)  # nosec B301 - controlled data source

                if self.cache:
                    self.cache.put(feature_key, feature_data)

                return feature_data["value"]
            except Exception as e:
                logger.error(f"Failed to load feature from disk: {e}")

        # Compute if missing and function available
        if compute_if_missing:
            fn_key = f"{name}:{version}"
            if fn_key in self.feature_functions:
                try:
                    logger.info(f"Computing feature {name}:{version} for {entity_id}")
                    value = self.feature_functions[fn_key](entity_id)
                    self.store_feature(name, version, entity_id, value)
                    return value
                except Exception as e:
                    logger.error(f"Failed to compute feature: {e}")

        return None

    def get_features_batch(
        self,
        name: str,
        version: str,
        entity_ids: List[str],
        compute_if_missing: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve multiple feature values.

        Args:
            name: Feature name
            version: Feature version
            entity_ids: List of entity identifiers
            compute_if_missing: Whether to compute missing features

        Returns:
            Dictionary mapping entity_id to feature value
        """
        results = {}

        for entity_id in entity_ids:
            try:
                value = self.get_feature(name, version, entity_id, compute_if_missing)
                if value is not None:
                    results[entity_id] = value
            except Exception as e:
                logger.error(f"Failed to get feature for {entity_id}: {e}")

        return results

    def list_features(
        self, status: Optional[FeatureStatus] = None, tags: Optional[List[str]] = None
    ) -> List[FeatureMetadata]:
        """
        List all features in the store.

        Args:
            status: Filter by status
            tags: Filter by tags

        Returns:
            List of FeatureMetadata objects
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            query = "SELECT * FROM features"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status.value)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            features = []
            for row in rows:
                metadata = FeatureMetadata(
                    name=row[0],
                    version=row[1],
                    feature_type=FeatureType(row[2]),
                    description=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5]),
                    status=FeatureStatus(row[6]),
                    dependencies=json.loads(row[7]),
                    tags=json.loads(row[8]),
                    schema=json.loads(row[9]),
                    statistics=json.loads(row[10]),
                )

                # Filter by tags if specified
                if tags:
                    if any(tag in metadata.tags for tag in tags):
                        features.append(metadata)
                else:
                    features.append(metadata)

            return features
        except Exception as e:
            logger.error(f"Failed to list features: {e}")
            return []

    def update_feature_status(
        self, name: str, version: str, status: FeatureStatus
    ) -> bool:
        """
        Update feature status.

        Args:
            name: Feature name
            version: Feature version
            status: New status

        Returns:
            True if successful, False otherwise
        """
        metadata = self.get_metadata(name, version)
        if not metadata:
            logger.error(f"Feature {name}:{version} not found")
            return False

        try:
            metadata.status = status
            metadata.updated_at = datetime.utcnow()
            self._save_metadata(metadata)
            logger.info(f"Updated status of {name}:{version} to {status.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update feature status: {e}")
            return False

    def delete_feature(self, name: str, version: str) -> bool:
        """
        Delete a feature from the store.

        Args:
            name: Feature name
            version: Feature version

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM features WHERE name = ? AND version = ?", (name, version)
            )
            conn.commit()
            conn.close()

            # Remove computation function
            fn_key = f"{name}:{version}"
            if fn_key in self.feature_functions:
                del self.feature_functions[fn_key]

            # Clear cache entries
            if self.cache:
                self.cache.clear()

            logger.info(f"Deleted feature {name}:{version}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete feature: {e}")
            return False

    def compute_statistics(
        self, name: str, version: str, entity_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compute statistics for a feature across entities.

        Args:
            name: Feature name
            version: Feature version
            entity_ids: List of entity identifiers

        Returns:
            Dictionary of statistics
        """
        values = []
        for entity_id in entity_ids:
            value = self.get_feature(name, version, entity_id, compute_if_missing=False)
            if value is not None:
                values.append(value)

        if not values:
            return {}

        try:
            # Compute basic statistics for numeric features
            if isinstance(values[0], (int, float)):
                import statistics

                stats = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values),
                }
            else:
                stats = {
                    "count": len(values),
                    "unique_count": len(set(str(v) for v in values)),
                }

            # Update metadata with statistics
            metadata = self.get_metadata(name, version)
            if metadata:
                metadata.statistics = stats
                metadata.updated_at = datetime.utcnow()
                self._save_metadata(metadata)

            return stats
        except Exception as e:
            logger.error(f"Failed to compute statistics: {e}")
            return {}

    def _get_feature_key(self, name: str, version: str, entity_id: str) -> str:
        """Generate a unique key for a feature."""
        key_string = f"{name}:{version}:{entity_id}"
        return hashlib.md5(
            key_string.encode(), usedforsecurity=False
        ).hexdigest()  # nosec B324

    def clear_cache(self) -> None:
        """Clear the feature cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Feature cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache:
            return {"enabled": False}

        return {
            "enabled": True,
            "size": self.cache.size(),
            "capacity": self.cache.capacity,
        }


if __name__ == "__main__":
    # Example usage and testing
    import tempfile

    # Create temporary storage
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize feature store
        store = FeatureStore(storage_path=tmpdir, cache_size=100)

        # Register a feature
        def compute_player_ppg(player_id: str) -> float:
            """Compute points per game for a player."""
            # Mock computation
            return 25.5

        metadata = store.register_feature(
            name="player_ppg",
            version="v1",
            feature_type=FeatureType.NUMERIC,
            description="Player points per game",
            computation_fn=compute_player_ppg,
            tags=["player", "scoring"],
        )

        print(f"Registered feature: {metadata.name} v{metadata.version}")

        # Store feature values
        store.store_feature("player_ppg", "v1", "player_123", 28.5)
        store.store_feature("player_ppg", "v1", "player_456", 22.3)

        # Retrieve feature
        value = store.get_feature("player_ppg", "v1", "player_123")
        print(f"Retrieved value: {value}")

        # Batch retrieval
        batch_values = store.get_features_batch(
            "player_ppg", "v1", ["player_123", "player_456", "player_789"]
        )
        print(f"Batch values: {batch_values}")

        # List features
        features = store.list_features()
        print(f"Total features: {len(features)}")

        # Compute statistics
        stats = store.compute_statistics(
            "player_ppg", "v1", ["player_123", "player_456"]
        )
        print(f"Statistics: {stats}")

        # Cache stats
        cache_stats = store.get_cache_stats()
        print(f"Cache stats: {cache_stats}")

        print("\nFeature store demo completed successfully!")
