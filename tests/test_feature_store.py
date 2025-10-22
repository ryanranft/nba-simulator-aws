#!/usr/bin/env python3
"""
Tests for feature_store
"""

import pytest
import sys
import json
import pickle
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
from collections import OrderedDict

# Add module directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts/ml'))

# Import from the module
from feature_store import (
    FeatureType,
    FeatureStatus,
    FeatureMetadata,
    LRUCache,
    logger
)


# Fixtures

@pytest.fixture
def sample_datetime():
    """Fixture for consistent datetime."""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def feature_metadata(sample_datetime):
    """Fixture for sample feature metadata."""
    return FeatureMetadata(
        name="player_points_avg",
        version="1.0.0",
        feature_type=FeatureType.NUMERIC,
        description="Average points per game",
        created_at=sample_datetime,
        updated_at=sample_datetime,
        status=FeatureStatus.ACTIVE,
        dependencies=["player_stats"],
        tags=["player", "scoring"],
        schema={"type": "float", "min": 0, "max": 100},
        statistics={"mean": 15.5, "std": 5.2}
    )


@pytest.fixture
def feature_metadata_dict(sample_datetime):
    """Fixture for feature metadata as dictionary."""
    return {
        "name": "player_points_avg",
        "version": "1.0.0",
        "feature_type": "numeric",
        "description": "Average points per game",
        "created_at": sample_datetime.isoformat(),
        "updated_at": sample_datetime.isoformat(),
        "status": "active",
        "dependencies": ["player_stats"],
        "tags": ["player", "scoring"],
        "schema": {"type": "float", "min": 0, "max": 100},
        "statistics": {"mean": 15.5, "std": 5.2}
    }


@pytest.fixture
def lru_cache():
    """Fixture for LRU cache instance."""
    return LRUCache(capacity=5)


@pytest.fixture
def lru_cache_large():
    """Fixture for large capacity LRU cache."""
    return LRUCache(capacity=1000)


# FeatureType Tests

def test_feature_type_enum_values():
    """Test FeatureType enum has correct values."""
    assert FeatureType.NUMERIC.value == "numeric"
    assert FeatureType.CATEGORICAL.value == "categorical"
    assert FeatureType.BOOLEAN.value == "boolean"
    assert FeatureType.EMBEDDING.value == "embedding"
    assert FeatureType.TIME_SERIES.value == "time_series"


def test_feature_type_enum_members():
    """Test FeatureType enum has all expected members."""
    expected_members = {"NUMERIC", "CATEGORICAL", "BOOLEAN", "EMBEDDING", "TIME_SERIES"}
    actual_members = {member.name for member in FeatureType}
    assert actual_members == expected_members


def test_feature_type_from_value():
    """Test creating FeatureType from string value."""
    feature_type = FeatureType("numeric")
    assert feature_type == FeatureType.NUMERIC


def test_feature_type_invalid_value_raises_error():
    """Test invalid FeatureType value raises ValueError."""
    with pytest.raises(ValueError):
        FeatureType("invalid_type")


# FeatureStatus Tests

def test_feature_status_enum_values():
    """Test FeatureStatus enum has correct values."""
    assert FeatureStatus.ACTIVE.value == "active"
    assert FeatureStatus.DEPRECATED.value == "deprecated"
    assert FeatureStatus.EXPERIMENTAL.value == "experimental"
    assert FeatureStatus.ARCHIVED.value == "archived"


def test_feature_status_enum_members():
    """Test FeatureStatus enum has all expected members."""
    expected_members = {"ACTIVE", "DEPRECATED", "EXPERIMENTAL", "ARCHIVED"}
    actual_members = {member.name for member in FeatureStatus}
    assert actual_members == expected_members


def test_feature_status_from_value():
    """Test creating FeatureStatus from string value."""
    status = FeatureStatus("active")
    assert status == FeatureStatus.ACTIVE


def test_feature_status_invalid_value_raises_error():
    """Test invalid FeatureStatus value raises ValueError."""
    with pytest.raises(ValueError):
        FeatureStatus("invalid_status")


# FeatureMetadata Tests

def test_feature_metadata_initialization(feature_metadata, sample_datetime):
    """Test FeatureMetadata initialization with all fields."""
    assert feature_metadata.name == "player_points_avg"
    assert feature_metadata.version == "1.0.0"
    assert feature_metadata.feature_type == FeatureType.NUMERIC
    assert feature_metadata.description == "Average points per game"
    assert feature_metadata.created_at == sample_datetime
    assert feature_metadata.updated_at == sample_datetime
    assert feature_metadata.status == FeatureStatus.ACTIVE
    assert feature_metadata.dependencies == ["player_stats"]
    assert feature_metadata.tags == ["player", "scoring"]
    assert feature_metadata.schema == {"type": "float", "min": 0, "max": 100}
    assert feature_metadata.statistics == {"mean": 15.5, "std": 5.2}


def test_feature_metadata_default_values(sample_datetime):
    """Test FeatureMetadata initialization with default values."""
    metadata = FeatureMetadata(
        name="test_feature",
        version="1.0.0",
        feature_type=FeatureType.BOOLEAN,
        description="Test feature",
        created_at=sample_datetime,
        updated_at=sample_datetime
    )
    assert metadata.status == FeatureStatus.ACTIVE
    assert metadata.dependencies == []
    assert metadata.tags == []
    assert metadata.schema == {}
    assert metadata.statistics == {}


def test_feature_metadata_to_dict(feature_metadata, feature_metadata_dict):
    """Test converting FeatureMetadata to dictionary."""
    result = feature_metadata.to_dict()
    assert result == feature_metadata_dict


def test_feature_metadata_to_dict_converts_enums(feature_metadata):
    """Test to_dict converts enums to string values."""
    result = feature_metadata.to_dict()
    assert isinstance(result['feature_type'], str)
    assert isinstance(result['status'], str)
    assert result['feature_type'] == "numeric"
    assert result['status'] == "active"


def test_feature_metadata_to_dict_converts_datetime(feature_metadata, sample_datetime):
    """Test to_dict converts datetime to ISO format."""
    result = feature_metadata.to_dict()
    assert isinstance(result['created_at'], str)
    assert isinstance(result['updated_at'], str)
    assert result['created_at'] == sample_datetime.isoformat()
    assert result['updated_at'] == sample_datetime.isoformat()


def test_feature_metadata_from_dict(feature_metadata_dict, sample_datetime):
    """Test creating FeatureMetadata from dictionary."""
    metadata = FeatureMetadata.from_dict(feature_metadata_dict)
    assert metadata.name == "player_points_avg"
    assert metadata.version == "1.0.0"
    assert metadata.feature_type == FeatureType.NUMERIC
    assert metadata.status == FeatureStatus.ACTIVE
    assert metadata.created_at == sample_datetime
    assert metadata.updated_at == sample_datetime


def test_feature_metadata_from_dict_converts_types(feature_metadata_dict):
    """Test from_dict properly converts string types to enums and datetime."""
    metadata = FeatureMetadata.from_dict(feature_metadata_dict)
    assert isinstance(metadata.feature_type, FeatureType)
    assert isinstance(metadata.status, FeatureStatus)
    assert isinstance(metadata.created_at, datetime)
    assert isinstance(metadata.updated_at, datetime)


def test_feature_metadata_roundtrip(feature_metadata):
    """Test converting to dict and back preserves data."""
    dict_data = feature_metadata.to_dict()
    restored = FeatureMetadata.from_dict(dict_data)
    assert restored.name == feature_metadata.name
    assert restored.version == feature_metadata.version
    assert restored.feature_type == feature_metadata.feature_type
    assert restored.status == feature_metadata.status
    assert restored.created_at == feature_metadata.created_at
    assert restored.dependencies == feature_metadata.dependencies


def test_feature_metadata_with_empty_lists(sample_datetime):
    """Test FeatureMetadata with empty dependency and tag lists."""
    metadata = FeatureMetadata(
        name="test",
        version="1.0",
        feature_type=FeatureType.CATEGORICAL,
        description="Test",
        created_at=sample_datetime,
        updated_at=sample_datetime,
        dependencies=[],
        tags=[]
    )
    assert metadata.dependencies == []
    assert metadata.tags == []


def test_feature_metadata_with_complex_schema(sample_datetime):
    """Test FeatureMetadata with complex nested schema."""
    complex_schema = {
        "type": "object",
        "properties": {
            "value": {"type": "float"},
            "confidence": {"type": "float", "min": 0, "max": 1}
        }
    }
    metadata = FeatureMetadata(
        name="test",
        version="1.0",
        feature_type=FeatureType.EMBEDDING,
        description="Test",
        created_at=sample_datetime,
        updated_at=sample_datetime,
        schema=complex_schema
    )
    assert metadata.schema == complex_schema


@pytest.mark.parametrize("feature_type", [
    FeatureType.NUMERIC,
    FeatureType.CATEGORICAL,
    FeatureType.BOOLEAN,
    FeatureType.EMBEDDING,
    FeatureType.TIME_SERIES
])
def test_feature_metadata_with_all_feature_types(feature_type, sample_datetime):
    """Test FeatureMetadata with all possible feature types."""
    metadata = FeatureMetadata(
        name="test",
        version="1.0",
        feature_type=feature_type,
        description="Test",
        created_at=sample_datetime,
        updated_at=sample_datetime
    )
    assert metadata.feature_type == feature_type


@pytest.mark.parametrize("status", [
    FeatureStatus.ACTIVE,
    FeatureStatus.DEPRECATED,
    FeatureStatus.EXPERIMENTAL,
    FeatureStatus.ARCHIVED
])
def test_feature_metadata_with_all_statuses(status, sample_datetime):
    """Test FeatureMetadata with all possible statuses."""
    metadata = FeatureMetadata(
        name="test",
        version="1.0",
        feature_type=FeatureType.NUMERIC,
        description="Test",
        created_at=sample_datetime,
        updated_at=sample_datetime,
        status=status
    )
    assert metadata.status == status


# LRUCache Tests

def test_lru_cache_initialization():
    """Test LRUCache initialization with default capacity."""
    cache = LRUCache()
    assert cache.capacity == 1000
    assert cache.size() == 0


def test_lru_cache_initialization_custom_capacity():
    """Test LRUCache initialization with custom capacity."""
    cache = LRUCache(capacity=100)
    assert cache.capacity == 100
    assert cache.size() == 0


def test_lru_cache_put_and_get(lru_cache):
    """Test putting and getting values from cache."""
    lru_cache.put("key1", "value1")
    result = lru_cache.get("key1")
    assert result == "value1"


def test_lru_cache_get_nonexistent_key(lru_cache):
    """Test getting non-existent key returns None."""
    result = lru_cache.get("nonexistent")
    assert result is None


def test_lru_cache_put_updates_existing_key(lru_cache):
    """Test putting value with existing key updates the value."""
    lru_cache.put("key1", "value1")
    lru_cache.put("key1", "value2")
    result = lru_cache.get("key1")
    assert result == "value2"
    assert lru_cache.size() == 1


def test_lru_cache_eviction_when_full(lru_cache):
    """Test LRU eviction when cache reaches capacity."""
    # Fill cache to capacity (5)
    for i in range(5):
        lru_cache.put(f"key{i}", f"value{i}")
    
    # Add one more item, should evict key0
    lru_cache.put("key5", "value5")
    
    assert lru_cache.size() == 5
    assert lru_cache.get("key0") is None
    assert lru_cache.get("key5") == "value5"


def test_lru_cache_get_updates_access_order(lru_cache):
    """Test that getting a key updates its access order."""
    # Fill cache
    for i in range(5):
        lru_cache.put(f"key{i}", f"value{i}")
    
    # Access key0 to make it most recently used
    lru_cache.get("key0")
    
    # Add new item, should evict key1 (least recently used)
    lru_cache.put("key5", "value5")
    
    assert lru_cache.get("key0") == "value0"
    assert lru_cache.get("key1") is None


def test_lru_cache_clear(lru_cache):
    """Test clearing all items from cache."""
    lru_cache.put("key1", "value1")
    lru_cache.put("key2", "value2")
    assert lru_cache.size() == 2
    
    lru_cache.clear()
    
    assert lru_cache.size() == 0
    assert lru_cache.get("key1") is None
    assert lru_cache.get("key2") is None


def test_lru_cache_size(lru_cache):
    """Test size method returns correct count."""
    assert lru_cache.size() == 0
    
    lru_cache.put("key1", "value1")
    assert lru_cache.size() == 1
    
    lru_cache.put("key2", "value2")
    assert lru_cache.size() == 2
    
    lru_cache.clear()
    assert lru_cache.size() == 0


def test_lru_cache_with_none_value(lru_cache):
    """Test caching None as a value."""
    lru_cache.put("key1", None)
    result = lru_cache.get("key1")
    assert result is None
    assert lru_cache.size() == 1


def test_lru_cache_with_complex_objects(lru_cache):
    """Test caching complex objects."""
    complex_obj = {"nested": {"data": [1, 2, 3]}, "value": 42}
    lru_cache.put("key1", complex_obj)
    result = lru_cache.get("key1")
    assert result == complex_obj


def test_lru_cache_with_list_values(lru_cache):
    """Test caching list values."""
    list_value = [1, 2, 3, 4, 5]
    lru_cache.put("key1", list_value)
    result = lru_cache.get("key1")
    assert result == list_value


def test_lru_cache_with_dict_values(lru_cache):
    """Test caching dictionary values."""
    dict_value = {"a": 1, "b": 2, "c": 3}
    lru_cache.put("key1", dict_value)
    result = lru_cache.get("key1")
    assert result == dict_value


def test_lru_cache_thread_safety():
    """Test LRUCache thread safety with concurrent access."""
    cache = LRUCache(capacity=100)
    results = []
    
    def worker(thread_id):
        for i in range(10):
            cache.put(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")
            value = cache.get(f"key_{thread_id}_{i}")
            results.append(value is not None)
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # All puts and gets should succeed
    assert all(results)


def test_lru_cache_concurrent_put_operations():
    """Test concurrent put operations don't corrupt cache."""
    cache = LRUCache(capacity=50)
    
    def put_worker(start_idx):
        for i in range(start_idx, start_idx + 10):
            cache.put(f"key{i}", f"value{i}")
    
    threads = [threading.Thread(target=put_worker, args=(i * 10,)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Cache should have items and not be corrupted
    assert cache.size() > 0
    assert cache.size() <= 50


def test_lru_cache_empty_string_key(lru_cache):
    """Test caching with empty string as key."""
    lru_cache.put("", "empty_key_value")
    result = lru_cache.get("")
    assert result == "empty_key_value"


def test_lru_cache_numeric_string_keys(lru_cache):
    """Test caching with numeric string keys."""
    lru_cache.put("123", "numeric_string")
    result = lru_cache.get("123")
    assert result == "numeric_string"


def test_lru_cache_special_character_keys(lru_cache):
    """Test caching with special characters in keys."""
    special_key = "key!@#$%^&*()"
    lru_cache.put(special_key, "special_value")
    result = lru_cache.get(special_key)
    assert result == "special_value"


def test_lru_cache_capacity_one():
    """Test LRUCache with capacity of 1."""
    cache = LRUCache(capacity=1)
    cache.put("key1", "value1")
    assert cache.get("key1") == "value1"
    
    cache.put("key2", "value2")
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.size() == 1


def test_lru_cache_large_capacity(lru_cache_large):
    """Test LRUCache with large capacity."""
    for i in range(500):
        lru_cache_large.put(f"key{i}", f"value{i}")
    
    assert lru_cache_large.size() == 500
    assert lru_cache_large.get("key0") == "value0"
    assert lru_cache_large.get("key499") == "value499"


def test_lru_cache_overwrite_maintains_size(lru_cache):
    """Test overwriting keys doesn't increase cache size."""
    lru_cache.put("key1", "value1")
    lru_cache.put("key2", "value2")
    assert lru_cache.size() == 2
    
    lru_cache.put("key1", "new_value1")
    assert lru_cache.size() == 2
    assert lru_cache.get("key1") == "new_value1"


@pytest.mark.parametrize("capacity", [1, 5, 10, 100, 1000])
def test_lru_cache_various_capacities(capacity):
    """Test LRUCache with various capacity values."""
    cache = LRUCache(capacity=capacity)
    assert cache.capacity == capacity
    
    # Fill to capacity
    for i in range(capacity):
        cache.put(f"key{i}", f"value{i}")
    
    assert cache.size() == capacity


def test_lru_cache_get_after_clear(lru_cache):
    """Test getting values after clearing cache."""
    lru_cache.put("key1", "value1")
    lru_cache.clear()
    result = lru_cache.get("key1")
    assert result is None


def test_lru_cache_multiple_clears(lru_cache):
    """Test multiple clear operations."""
    lru_cache.put("key1", "value1")
    lru_cache.clear()
    lru_cache.clear()  # Clear again
    assert lru_cache.size() == 0


def test_lru_cache_put_after_clear(lru_cache):
    """Test putting values after clearing cache."""
    lru_cache.put("key1", "value1")
    lru_cache.clear()
    lru_cache.put("key2", "value2")
    
    assert lru_cache.get("key1") is None
    assert lru_cache.get("key2") == "value2"
    assert lru_cache.size() == 1


def test_lru_cache_boolean_values(lru_cache):
    """Test caching boolean values."""
    lru_cache.put("true_key", True)
    lru_cache.put("false_key", False)
    
    assert lru_cache.get("true_key") is True
    assert lru_cache.get("false_key") is False


def test_lru_cache_numeric_values(lru_cache):
    """Test caching numeric values."""
    lru_cache.put("int_key", 42)
    lru_cache.put("float_key", 3.14)
    lru_cache.put("negative_key", -100)
    
    assert lru_cache.get("int_key") == 42
    assert lru_cache.get("float_key") == 3.14
    assert lru_cache.get("negative_key") == -100


def test_lru_cache_zero_value(lru_cache):
    """Test caching zero as a value."""
    lru_cache.put("zero_key", 0)
    result = lru_cache.get("zero_key")
    assert result == 0
    assert result is not None


def test_lru_cache_empty_list_value(lru_cache):
    """Test caching empty list as value."""
    lru_cache.put("empty_list", [])
    result = lru_cache.get("empty_list")
    assert result == []
    assert isinstance(result, list)


def test_lru_cache_empty_dict_value(lru_cache):
    """Test caching empty dict as value."""
    lru_cache.put("empty_dict", {})
    result = lru_cache.get("empty_dict")
    assert result == {}
    assert isinstance(result, dict)