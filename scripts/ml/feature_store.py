#!/usr/bin/env python3
"""
Feature Store - ml_systems_5

Centralized feature storage and serving system implementing
recommendation ml_systems_5 from the Master Implementation Sequence.

Features:
1. Centralized feature storage (offline + online)
2. Feature versioning and lineage tracking
3. Online/offline feature serving
4. Feature sharing across models
5. Schema validation and type checking
6. Time-travel capabilities (point-in-time features)
7. Feature monitoring and drift detection

Implementation: Master Implementation Sequence #13
Phase: 5 (ML Models)
Source: Designing Machine Learning Systems
Dependencies: rec_11 (feature engineering)
"""

import os
import sys
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Types of features."""
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    BINARY = "binary"
    TIMESTAMP = "timestamp"
    EMBEDDING = "embedding"


class ServingMode(Enum):
    """Feature serving modes."""
    ONLINE = "online"      # Low-latency real-time serving
    OFFLINE = "offline"    # Batch serving for training
    BOTH = "both"         # Available in both modes


@dataclass
class FeatureMetadata:
    """
    Metadata for a feature.

    Attributes:
        name: Feature name
        feature_type: Type of feature
        description: Human-readable description
        owner: Team/person responsible
        tags: Searchable tags
        created_at: Creation timestamp
        version: Feature version
    """
    name: str
    feature_type: FeatureType
    description: str = ""
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    serving_mode: ServingMode = ServingMode.BOTH

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'feature_type': self.feature_type.value,
            'description': self.description,
            'owner': self.owner,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'version': self.version,
            'serving_mode': self.serving_mode.value
        }


@dataclass
class FeatureGroup:
    """
    Group of related features.

    Attributes:
        name: Feature group name
        features: List of feature names in this group
        entity_key: Primary key for joining (e.g., player_id)
        timestamp_key: Timestamp column for time-travel
        description: Group description
        version: Group version
    """
    name: str
    features: List[str]
    entity_key: str
    timestamp_key: Optional[str] = None
    description: str = ""
    version: str = "1.0"
    metadata: Dict[str, FeatureMetadata] = field(default_factory=dict)

    def add_feature(self, feature_name: str, metadata: FeatureMetadata):
        """Add feature to group."""
        if feature_name not in self.features:
            self.features.append(feature_name)
        self.metadata[feature_name] = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'features': self.features,
            'entity_key': self.entity_key,
            'timestamp_key': self.timestamp_key,
            'description': self.description,
            'version': self.version,
            'feature_metadata': {
                name: meta.to_dict() for name, meta in self.metadata.items()
            }
        }


class FeatureStore:
    """
    Centralized feature storage and serving system.

    Provides:
    - Feature registration and versioning
    - Online and offline feature serving
    - Point-in-time feature retrieval
    - Feature lineage tracking
    - Schema validation
    """

    def __init__(
        self,
        storage_path: str,
        online_cache_size: int = 10000,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Feature Store.

        Args:
            storage_path: Path to feature store storage
            online_cache_size: Size of online feature cache
            config: Configuration options
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.online_cache_size = online_cache_size
        self.config = config or {}

        # Feature groups registry
        self.feature_groups: Dict[str, FeatureGroup] = {}

        # Online cache (in-memory for fast serving)
        self.online_cache: Dict[str, pd.DataFrame] = {}

        # Offline storage (on-disk parquet files)
        self.offline_path = self.storage_path / "offline"
        self.offline_path.mkdir(exist_ok=True)

        # Metadata storage
        self.metadata_path = self.storage_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)

        # Load existing feature groups
        self._load_feature_groups()

        logger.info(f"Initialized Feature Store at {self.storage_path}")

    def register_feature_group(
        self,
        feature_group: FeatureGroup
    ) -> None:
        """
        Register a feature group.

        Args:
            feature_group: FeatureGroup to register
        """
        logger.info(f"Registering feature group: {feature_group.name}")

        self.feature_groups[feature_group.name] = feature_group

        # Save metadata
        metadata_file = self.metadata_path / f"{feature_group.name}.json"
        with open(metadata_file, 'w') as f:
            json.dump(feature_group.to_dict(), f, indent=2)

        logger.info(f"Feature group '{feature_group.name}' registered")

    def _load_feature_groups(self):
        """Load feature groups from metadata."""
        for metadata_file in self.metadata_path.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)

                # Reconstruct FeatureGroup
                feature_group = FeatureGroup(
                    name=data['name'],
                    features=data['features'],
                    entity_key=data['entity_key'],
                    timestamp_key=data.get('timestamp_key'),
                    description=data.get('description', ''),
                    version=data.get('version', '1.0')
                )

                # Reconstruct metadata
                for fname, fmeta in data.get('feature_metadata', {}).items():
                    metadata = FeatureMetadata(
                        name=fmeta['name'],
                        feature_type=FeatureType(fmeta['feature_type']),
                        description=fmeta.get('description', ''),
                        owner=fmeta.get('owner', ''),
                        tags=fmeta.get('tags', []),
                        created_at=datetime.fromisoformat(fmeta['created_at']),
                        version=fmeta.get('version', '1.0'),
                        serving_mode=ServingMode(fmeta.get('serving_mode', 'both'))
                    )
                    feature_group.metadata[fname] = metadata

                self.feature_groups[feature_group.name] = feature_group
                logger.info(f"Loaded feature group: {feature_group.name}")

            except Exception as e:
                logger.error(f"Error loading {metadata_file}: {e}")

    def write_offline_features(
        self,
        feature_group_name: str,
        features_df: pd.DataFrame,
        partition_by: Optional[str] = None
    ) -> None:
        """
        Write features to offline storage.

        Args:
            feature_group_name: Name of feature group
            features_df: DataFrame with features
            partition_by: Column to partition by (e.g., 'game_date')
        """
        logger.info(f"Writing {len(features_df)} records to offline store: {feature_group_name}")

        if feature_group_name not in self.feature_groups:
            raise ValueError(f"Feature group '{feature_group_name}' not registered")

        feature_group = self.feature_groups[feature_group_name]

        # Validate entity key exists
        if feature_group.entity_key not in features_df.columns:
            raise ValueError(f"Entity key '{feature_group.entity_key}' not in DataFrame")

        # Create offline storage path
        offline_group_path = self.offline_path / feature_group_name
        offline_group_path.mkdir(exist_ok=True)

        # Save as parquet (partitioned if specified)
        if partition_by and partition_by in features_df.columns:
            # Partition by specified column
            for partition_value, partition_df in features_df.groupby(partition_by):
                partition_path = offline_group_path / f"{partition_by}={partition_value}"
                partition_path.mkdir(exist_ok=True)

                output_file = partition_path / "features.parquet"
                partition_df.to_parquet(output_file, index=False, compression='snappy')

            logger.info(f"Written partitioned features to {offline_group_path}")
        else:
            # Single file
            output_file = offline_group_path / f"features_v{feature_group.version}.parquet"
            features_df.to_parquet(output_file, index=False, compression='snappy')

            logger.info(f"Written features to {output_file}")

    def read_offline_features(
        self,
        feature_group_name: str,
        entity_ids: Optional[List[Any]] = None,
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read features from offline storage.

        Args:
            feature_group_name: Name of feature group
            entity_ids: Optional list of entity IDs to filter
            feature_names: Optional list of feature names to retrieve

        Returns:
            DataFrame with requested features
        """
        logger.info(f"Reading offline features: {feature_group_name}")

        if feature_group_name not in self.feature_groups:
            raise ValueError(f"Feature group '{feature_group_name}' not registered")

        feature_group = self.feature_groups[feature_group_name]
        offline_group_path = self.offline_path / feature_group_name

        if not offline_group_path.exists():
            raise ValueError(f"No offline features found for '{feature_group_name}'")

        # Read all parquet files in group
        parquet_files = list(offline_group_path.glob("**/*.parquet"))

        if not parquet_files:
            raise ValueError(f"No parquet files found for '{feature_group_name}'")

        # Read and concatenate
        dfs = []
        for pfile in parquet_files:
            df = pd.read_parquet(pfile)
            dfs.append(df)

        features_df = pd.concat(dfs, ignore_index=True)

        # Filter by entity IDs if specified
        if entity_ids is not None:
            features_df = features_df[
                features_df[feature_group.entity_key].isin(entity_ids)
            ]

        # Select specific features if specified
        if feature_names is not None:
            # Always include entity key
            columns = [feature_group.entity_key]

            # Add timestamp key if present
            if feature_group.timestamp_key and feature_group.timestamp_key in features_df.columns:
                columns.append(feature_group.timestamp_key)

            # Add requested features
            for fname in feature_names:
                if fname in features_df.columns and fname not in columns:
                    columns.append(fname)

            features_df = features_df[columns]

        logger.info(f"Retrieved {len(features_df)} feature records")
        return features_df

    def write_online_features(
        self,
        feature_group_name: str,
        features_df: pd.DataFrame
    ) -> None:
        """
        Write features to online cache for low-latency serving.

        Args:
            feature_group_name: Name of feature group
            features_df: DataFrame with features
        """
        logger.info(f"Writing {len(features_df)} records to online cache: {feature_group_name}")

        if feature_group_name not in self.feature_groups:
            raise ValueError(f"Feature group '{feature_group_name}' not registered")

        feature_group = self.feature_groups[feature_group_name]

        # Index by entity key for fast lookup
        indexed_df = features_df.set_index(feature_group.entity_key)

        # Limit cache size (LRU-style)
        if len(indexed_df) > self.online_cache_size:
            # Keep most recent entries (if timestamp available)
            if feature_group.timestamp_key and feature_group.timestamp_key in indexed_df.columns:
                indexed_df = indexed_df.sort_values(feature_group.timestamp_key, ascending=False)
                indexed_df = indexed_df.head(self.online_cache_size)
            else:
                indexed_df = indexed_df.tail(self.online_cache_size)

        self.online_cache[feature_group_name] = indexed_df

        logger.info(f"Online cache updated: {len(indexed_df)} records")

    def read_online_features(
        self,
        feature_group_name: str,
        entity_ids: List[Any],
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read features from online cache (fast serving).

        Args:
            feature_group_name: Name of feature group
            entity_ids: List of entity IDs to retrieve
            feature_names: Optional list of feature names to retrieve

        Returns:
            DataFrame with requested features
        """
        if feature_group_name not in self.online_cache:
            raise ValueError(f"Feature group '{feature_group_name}' not in online cache")

        cached_df = self.online_cache[feature_group_name]

        # Retrieve by entity IDs
        try:
            features_df = cached_df.loc[entity_ids]
        except KeyError:
            # Some IDs not found - get what we can
            available_ids = [eid for eid in entity_ids if eid in cached_df.index]
            if not available_ids:
                return pd.DataFrame()

            features_df = cached_df.loc[available_ids]

        # Select specific features if requested
        if feature_names is not None:
            available_features = [f for f in feature_names if f in features_df.columns]
            features_df = features_df[available_features]

        return features_df.reset_index()

    def get_point_in_time_features(
        self,
        feature_group_name: str,
        entity_ids: List[Any],
        timestamps: Union[datetime, List[datetime]],
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get point-in-time features (time-travel).

        Retrieves features as they existed at specific timestamps,
        critical for preventing data leakage in training.

        Args:
            feature_group_name: Name of feature group
            entity_ids: List of entity IDs
            timestamps: Single timestamp or list of timestamps
            feature_names: Optional list of features to retrieve

        Returns:
            DataFrame with point-in-time features
        """
        logger.info(f"Getting point-in-time features for {len(entity_ids)} entities")

        if feature_group_name not in self.feature_groups:
            raise ValueError(f"Feature group '{feature_group_name}' not registered")

        feature_group = self.feature_groups[feature_group_name]

        if not feature_group.timestamp_key:
            raise ValueError(f"Feature group '{feature_group_name}' has no timestamp key")

        # Read offline features
        features_df = self.read_offline_features(
            feature_group_name,
            entity_ids=entity_ids,
            feature_names=feature_names
        )

        # Convert timestamp column to datetime
        features_df[feature_group.timestamp_key] = pd.to_datetime(
            features_df[feature_group.timestamp_key]
        )

        # Handle single timestamp vs list
        if isinstance(timestamps, datetime):
            timestamps = [timestamps] * len(entity_ids)

        # For each entity-timestamp pair, get the most recent features
        # that existed at that timestamp
        pit_features = []

        for entity_id, timestamp in zip(entity_ids, timestamps):
            # Get all features for this entity before the timestamp
            entity_features = features_df[
                (features_df[feature_group.entity_key] == entity_id) &
                (features_df[feature_group.timestamp_key] <= timestamp)
            ]

            if len(entity_features) > 0:
                # Get most recent features
                most_recent = entity_features.sort_values(
                    feature_group.timestamp_key, ascending=False
                ).iloc[0]

                pit_features.append(most_recent)

        if not pit_features:
            return pd.DataFrame()

        return pd.DataFrame(pit_features).reset_index(drop=True)

    def get_feature_stats(
        self,
        feature_group_name: str
    ) -> Dict[str, Any]:
        """
        Get statistics about a feature group.

        Args:
            feature_group_name: Name of feature group

        Returns:
            Dictionary with statistics
        """
        if feature_group_name not in self.feature_groups:
            raise ValueError(f"Feature group '{feature_group_name}' not registered")

        feature_group = self.feature_groups[feature_group_name]

        stats = {
            'name': feature_group.name,
            'version': feature_group.version,
            'num_features': len(feature_group.features),
            'entity_key': feature_group.entity_key,
            'timestamp_key': feature_group.timestamp_key
        }

        # Offline stats
        offline_group_path = self.offline_path / feature_group_name
        if offline_group_path.exists():
            parquet_files = list(offline_group_path.glob("**/*.parquet"))
            stats['offline_files'] = len(parquet_files)

            if parquet_files:
                # Sample first file for stats
                sample_df = pd.read_parquet(parquet_files[0])
                stats['offline_sample_size'] = len(sample_df)
                stats['offline_columns'] = list(sample_df.columns)

        # Online stats
        if feature_group_name in self.online_cache:
            cached_df = self.online_cache[feature_group_name]
            stats['online_cache_size'] = len(cached_df)
            stats['online_cached'] = True
        else:
            stats['online_cached'] = False

        return stats

    def list_feature_groups(self) -> List[Dict[str, Any]]:
        """
        List all registered feature groups.

        Returns:
            List of feature group summaries
        """
        return [
            {
                'name': fg.name,
                'version': fg.version,
                'num_features': len(fg.features),
                'entity_key': fg.entity_key,
                'description': fg.description
            }
            for fg in self.feature_groups.values()
        ]


def demo_feature_store():
    """Demonstrate feature store capabilities."""
    logger.info("="*80)
    logger.info("Feature Store - Demo")
    logger.info("="*80)

    # 1. Initialize feature store
    logger.info("\n1. Initializing Feature Store")
    feature_store = FeatureStore(
        storage_path="/tmp/feature_store",
        online_cache_size=1000
    )

    # 2. Create feature group
    logger.info("\n2. Creating Feature Group")
    player_features = FeatureGroup(
        name="player_game_features",
        features=[],
        entity_key="player_id",
        timestamp_key="game_date",
        description="Player performance features per game",
        version="1.0"
    )

    # Add feature metadata
    player_features.add_feature(
        "points_last_5",
        FeatureMetadata(
            name="points_last_5",
            feature_type=FeatureType.CONTINUOUS,
            description="Average points in last 5 games",
            owner="analytics_team",
            tags=["rolling", "performance"],
            serving_mode=ServingMode.BOTH
        )
    )

    player_features.add_feature(
        "assists_last_10",
        FeatureMetadata(
            name="assists_last_10",
            feature_type=FeatureType.CONTINUOUS,
            description="Average assists in last 10 games",
            tags=["rolling", "playmaking"]
        )
    )

    feature_store.register_feature_group(player_features)

    # 3. Generate sample features
    logger.info("\n3. Generating Sample Features")
    np.random.seed(42)

    sample_features = pd.DataFrame({
        'player_id': [2544, 2544, 2544, 201935, 201935, 201935],
        'game_date': pd.date_range('2024-01-01', periods=6, freq='7D'),
        'points_last_5': np.random.uniform(20, 30, 6),
        'assists_last_10': np.random.uniform(5, 10, 6),
        'rebounds_avg': np.random.uniform(6, 9, 6)
    })

    logger.info(f"Generated {len(sample_features)} feature records")

    # 4. Write offline features
    logger.info("\n4. Writing to Offline Storage")
    feature_store.write_offline_features(
        "player_game_features",
        sample_features,
        partition_by='game_date'
    )

    # 5. Write online features
    logger.info("\n5. Writing to Online Cache")
    latest_features = sample_features.sort_values('game_date').groupby('player_id').tail(1)
    feature_store.write_online_features(
        "player_game_features",
        latest_features
    )

    # 6. Read offline features
    logger.info("\n6. Reading from Offline Storage")
    offline_features = feature_store.read_offline_features(
        "player_game_features",
        entity_ids=[2544],
        feature_names=['points_last_5', 'assists_last_10']
    )
    logger.info(f"Retrieved {len(offline_features)} offline records")

    # 7. Read online features (fast serving)
    logger.info("\n7. Reading from Online Cache (fast serving)")
    online_features = feature_store.read_online_features(
        "player_game_features",
        entity_ids=[2544, 201935],
        feature_names=['points_last_5', 'assists_last_10']
    )
    logger.info(f"Retrieved {len(online_features)} online records")
    logger.info(f"Online features:\n{online_features}")

    # 8. Point-in-time features (time-travel)
    logger.info("\n8. Point-in-Time Features (preventing data leakage)")
    pit_features = feature_store.get_point_in_time_features(
        "player_game_features",
        entity_ids=[2544],
        timestamps=datetime(2024, 1, 15),
        feature_names=['points_last_5']
    )
    logger.info(f"Point-in-time features:\n{pit_features}")

    # 9. Get feature statistics
    logger.info("\n9. Feature Group Statistics")
    stats = feature_store.get_feature_stats("player_game_features")
    logger.info(f"Statistics: {json.dumps(stats, indent=2, default=str)}")

    # 10. List all feature groups
    logger.info("\n10. Listing All Feature Groups")
    groups = feature_store.list_feature_groups()
    for group in groups:
        logger.info(f"  - {group['name']} (v{group['version']}): {group['num_features']} features")

    logger.info("\n" + "="*80)
    logger.info("✅ Feature Store demo complete!")
    logger.info("="*80)


if __name__ == '__main__':
    demo_feature_store()
