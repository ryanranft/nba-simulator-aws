#!/usr/bin/env python3
"""
Comprehensive Test Suite for New Scraper Components

Tests all new async scraping infrastructure components:
- Data validators (ESPN, Basketball Reference, completeness)
- Deduplication manager and checkpoint system
- Smart retry strategies and circuit breaker
- Adaptive rate limiting
- Data provenance tracking
- Integration tests

Usage:
    python test_new_scraper_components.py
    pytest test_new_scraper_components.py -v

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import json
import logging
import pytest
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the components to test
from scripts.etl.data_validators import (
    ESPNSchemaValidator,
    BasketballReferenceValidator,
    DataCompletenessChecker,
    CrossSourceValidator,
    ValidationManager,
)
from scripts.etl.deduplication_manager import (
    DeduplicationManager,
    CheckpointManager,
    IncrementalUpdateManager,
)
from scripts.etl.smart_retry_strategies import (
    SmartRetryManager,
    CircuitBreaker,
    AdaptiveRetryManager,
    ErrorType,
)
from scripts.etl.adaptive_rate_limiter import (
    AdaptiveRateLimiter,
    TokenBucket,
    MultiDomainRateLimiter,
    RateLimitMonitor,
)
from scripts.etl.provenance_tracker import (
    ProvenanceTracker,
    DataLineage,
    ProvenanceManager,
)


class TestDataValidators:
    """Test data validation components"""

    @pytest.fixture
    def espn_validator(self):
        return ESPNSchemaValidator()

    @pytest.fixture
    def bref_validator(self):
        return BasketballReferenceValidator()

    @pytest.fixture
    def completeness_checker(self):
        return DataCompletenessChecker()

    @pytest.fixture
    def validation_manager(self):
        return ValidationManager()

    @pytest.mark.asyncio
    async def test_espn_game_validation(self, espn_validator):
        """Test ESPN game data validation"""
        # Valid game data
        valid_game = {
            "id": "12345",
            "date": "2024-10-13",
            "competitions": [
                {
                    "competitors": [
                        {"team": {"displayName": "Lakers"}, "score": "110"},
                        {"team": {"displayName": "Warriors"}, "score": "108"},
                    ]
                }
            ],
        }

        result = await espn_validator.validate_game_data(valid_game)
        assert result.is_valid
        assert result.quality_score > 0.8
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_espn_invalid_game(self, espn_validator):
        """Test ESPN invalid game data"""
        # Invalid game data (missing required fields)
        invalid_game = {
            "id": "12345"
            # Missing date and competitions
        }

        result = await espn_validator.validate_game_data(invalid_game)
        assert not result.is_valid
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_basketball_reference_player_stats(self, bref_validator):
        """Test Basketball Reference player stats validation"""
        valid_stats = {
            "players": [
                {
                    "player": "LeBron James",
                    "season": "2024-25",
                    "stats": {
                        "games": 10,
                        "points": 250,
                        "rebounds": 80,
                        "assists": 60,
                        "field_goals": 100,
                        "field_goal_attempts": 150,
                        "field_goal_percentage": 0.667,
                    },
                }
            ]
        }

        result = await bref_validator.validate_player_stats(valid_stats)
        assert result.is_valid
        assert result.quality_score > 0.8

    @pytest.mark.asyncio
    async def test_completeness_checker(self, completeness_checker):
        """Test data completeness checking"""
        complete_data = {
            "players": [
                {
                    "player": "LeBron James",
                    "stats": {
                        "games": 10,
                        "points": 250,
                        "rebounds": 80,
                        "assists": 60,
                    },
                }
            ]
        }

        result = await completeness_checker.check_completeness(
            complete_data, "player_stats"
        )
        assert result.is_valid
        assert len(result.errors) == 0

        # Test incomplete data
        incomplete_data = {"players": []}  # No players

        result = await completeness_checker.check_completeness(
            incomplete_data, "player_stats"
        )
        assert not result.is_valid
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validation_manager(self, validation_manager):
        """Test validation manager"""
        espn_data = {
            "id": "12345",
            "date": "2024-10-13",
            "competitions": [
                {
                    "competitors": [
                        {"team": {"displayName": "Lakers"}, "score": "110"},
                        {"team": {"displayName": "Warriors"}, "score": "108"},
                    ]
                }
            ],
        }

        result = await validation_manager.validate_data(
            espn_data, "espn", "game_summary"
        )
        assert result.is_valid


class TestDeduplicationManager:
    """Test deduplication and checkpoint components"""

    @pytest.fixture
    def dedup_manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield DeduplicationManager(local_db_path=f"{temp_dir}/test.db")

    @pytest.fixture
    def checkpoint_manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield CheckpointManager(checkpoint_dir=f"{temp_dir}/checkpoints")

    @pytest.mark.asyncio
    async def test_content_hashing(self, dedup_manager):
        """Test content hashing"""
        content = '{"game_id": "123", "score": "110-108"}'
        hash1 = dedup_manager.calculate_hash(content)
        hash2 = dedup_manager.calculate_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 length

        # Different content should have different hash
        different_content = '{"game_id": "124", "score": "110-108"}'
        hash3 = dedup_manager.calculate_hash(different_content)
        assert hash1 != hash3

    @pytest.mark.asyncio
    async def test_duplicate_detection(self, dedup_manager):
        """Test duplicate detection"""
        content = '{"game_id": "123", "score": "110-108"}'

        # First check should not be duplicate
        is_duplicate, existing = await dedup_manager.check_duplicate(
            content, "game_data"
        )
        assert not is_duplicate
        assert existing is None

        # Record the content
        await dedup_manager.record_content(content, "game_data")

        # Second check should be duplicate
        is_duplicate, existing = await dedup_manager.check_duplicate(
            content, "game_data"
        )
        assert is_duplicate
        assert existing is not None
        assert existing.content_type == "game_data"

    @pytest.mark.asyncio
    async def test_checkpoint_save_load(self, checkpoint_manager):
        """Test checkpoint save and load"""
        checkpoint_id = "test_scraper"
        test_data = {"last_date": "2024-10-13", "processed_games": 150, "errors": []}

        # Save checkpoint
        success = await checkpoint_manager.save_checkpoint(checkpoint_id, test_data)
        assert success

        # Load checkpoint
        loaded_data = await checkpoint_manager.load_checkpoint(checkpoint_id)
        assert loaded_data is not None
        assert loaded_data.data == test_data
        assert loaded_data.checkpoint_id == checkpoint_id

    @pytest.mark.asyncio
    async def test_incremental_update_manager(self, dedup_manager, checkpoint_manager):
        """Test incremental update manager"""
        update_manager = IncrementalUpdateManager(dedup_manager, checkpoint_manager)

        content = '{"game_id": "123", "score": "110-108"}'

        # First update should proceed
        should_update, existing = await update_manager.should_update(
            content, "game_data"
        )
        assert should_update
        assert existing is None

        # Record update
        content_hash = await update_manager.record_update(content, "game_data")
        assert content_hash.content_type == "game_data"

        # Second update should be skipped
        should_update, existing = await update_manager.should_update(
            content, "game_data"
        )
        assert not should_update
        assert existing is not None


class TestSmartRetryStrategies:
    """Test smart retry strategies and circuit breaker"""

    @pytest.fixture
    def retry_manager(self):
        return SmartRetryManager()

    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(failure_threshold=3, timeout=5)

    def test_error_classification(self, retry_manager):
        """Test error classification"""
        # Network error
        network_error = ConnectionError("Connection refused")
        assert retry_manager.classify_error(network_error) == ErrorType.NETWORK_ERROR

        # Rate limit error
        rate_limit_error = Exception("Rate limit exceeded")
        assert (
            retry_manager.classify_error(rate_limit_error) == ErrorType.RATE_LIMIT_ERROR
        )

        # Server error
        server_error = Exception("500 Internal Server Error")
        assert retry_manager.classify_error(server_error) == ErrorType.SERVER_ERROR

        # Client error
        client_error = Exception("404 Not Found")
        assert retry_manager.classify_error(client_error) == ErrorType.CLIENT_ERROR

    def test_delay_calculation(self, retry_manager):
        """Test delay calculation"""
        config = retry_manager.retry_configs[ErrorType.NETWORK_ERROR]

        # First retry should have base delay
        delay1 = retry_manager.calculate_delay(1, ErrorType.NETWORK_ERROR, config)
        assert delay1 > 0

        # Second retry should have exponential delay
        delay2 = retry_manager.calculate_delay(2, ErrorType.NETWORK_ERROR, config)
        assert delay2 > delay1

        # Delay should be capped at max delay
        delay10 = retry_manager.calculate_delay(10, ErrorType.NETWORK_ERROR, config)
        assert delay10 <= config.max_delay

    @pytest.mark.asyncio
    async def test_retry_execution(self, retry_manager):
        """Test retry execution"""
        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = await retry_manager.execute_with_retry(
            failing_function, max_retries=5, error_context="test"
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, circuit_breaker):
        """Test circuit breaker functionality"""
        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Service unavailable")

        # First few calls should fail but not open circuit
        for i in range(3):
            try:
                await circuit_breaker.call(failing_function)
            except Exception:
                pass

        # Circuit should be open now
        state = circuit_breaker.get_state()
        assert state["state"] == "OPEN"

        # Next call should be rejected immediately
        try:
            await circuit_breaker.call(failing_function)
            assert False, "Should have been rejected"
        except Exception as e:
            assert "Circuit breaker is OPEN" in str(e)


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiting"""

    @pytest.fixture
    def rate_limiter(self):
        return AdaptiveRateLimiter(initial_rate=10.0, max_rate=50.0)

    @pytest.fixture
    def token_bucket(self):
        return TokenBucket(capacity=100, refill_rate=10.0)

    @pytest.mark.asyncio
    async def test_token_bucket(self, token_bucket):
        """Test token bucket functionality"""
        # Should be able to consume tokens initially
        assert await token_bucket.consume(10)
        assert await token_bucket.consume(20)

        # Should not be able to consume more than capacity
        assert not await token_bucket.consume(100)

        # Wait for refill
        await asyncio.sleep(0.2)
        assert await token_bucket.consume(2)

    @pytest.mark.asyncio
    async def test_rate_limiter_429_handling(self, rate_limiter):
        """Test rate limiter 429 handling"""
        # Simulate successful requests
        for i in range(5):
            await rate_limiter.acquire()
            await rate_limiter.record_response(200, {})

        # Simulate 429 response
        await rate_limiter.acquire()
        await rate_limiter.record_response(429, {"Retry-After": "10"})

        info = rate_limiter.get_rate_limit_info()
        assert info.state.value == "rate_limited"
        assert info.consecutive_429s == 1
        assert info.current_rate < rate_limiter.initial_rate

    @pytest.mark.asyncio
    async def test_multi_domain_rate_limiter(self):
        """Test multi-domain rate limiter"""
        multi_limiter = MultiDomainRateLimiter()

        domains = ["espn.com", "basketball-reference.com"]

        for domain in domains:
            await multi_limiter.acquire(domain)
            await multi_limiter.record_response(domain, 200, {})

        stats = multi_limiter.get_domain_stats()
        assert len(stats) == 2
        assert "espn.com" in stats
        assert "basketball-reference.com" in stats


class TestProvenanceTracker:
    """Test data provenance tracking"""

    @pytest.fixture
    def provenance_tracker(self):
        return ProvenanceTracker()

    @pytest.fixture
    def data_lineage(self):
        return DataLineage()

    @pytest.mark.asyncio
    async def test_metadata_creation(self, provenance_tracker):
        """Test metadata creation"""
        metadata = await provenance_tracker.create_metadata(
            source_name="test_scraper",
            source_version="v1.0.0",
            source_url="https://example.com/data",
            content='{"test": "data"}',
            tags=["test", "example"],
            custom_metadata={"environment": "test"},
        )

        assert metadata.source_name == "test_scraper"
        assert metadata.source_version == "v1.0.0"
        assert metadata.source_url == "https://example.com/data"
        assert metadata.content_hash is not None
        assert "test" in metadata.tags
        assert metadata.custom_metadata["environment"] == "test"

    @pytest.mark.asyncio
    async def test_metadata_embedding(self, provenance_tracker):
        """Test metadata embedding in content"""
        metadata = await provenance_tracker.create_metadata(
            source_name="test_scraper",
            source_version="v1.0.0",
            content='{"test": "data"}',
        )

        content = '{"test": "data"}'
        embedded_content = await provenance_tracker.embed_metadata_in_content(
            content, metadata
        )

        # Should contain provenance metadata
        assert (
            "_provenance" in embedded_content
            or "PROVENANCE_METADATA" in embedded_content
        )

    @pytest.mark.asyncio
    async def test_data_lineage(self, data_lineage):
        """Test data lineage functionality"""
        # Create source metadata
        source_metadata = await ProvenanceTracker().create_metadata(
            source_name="source_scraper", source_version="v1.0.0"
        )

        # Add source node
        source_node = await data_lineage.add_source("source_001", source_metadata)
        assert source_node.node_type == "source"

        # Add transformation node
        transform_metadata = await ProvenanceTracker().create_metadata(
            source_name="transform_001", source_version="v1.0.0"
        )

        transform_node = await data_lineage.add_transformation(
            "transform_001", transform_metadata, ["source_001"]
        )
        assert transform_node.node_type == "transformation"
        assert "source_001" in transform_node.parent_nodes

        # Add output node
        output_metadata = await ProvenanceTracker().create_metadata(
            source_name="output_001", source_version="v1.0.0"
        )

        output_node = await data_lineage.add_output(
            "output_001", output_metadata, ["transform_001"]
        )
        assert output_node.node_type == "output"

        # Test lineage path
        path = data_lineage.get_lineage_path("output_001")
        assert len(path) == 3
        assert path[0].node_id == "source_001"
        assert path[1].node_id == "transform_001"
        assert path[2].node_id == "output_001"


class TestIntegration:
    """Integration tests for all components"""

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self):
        """Test complete scraping workflow with all components"""
        # Create all managers
        validation_manager = ValidationManager()
        dedup_manager = DeduplicationManager(local_db_path=":memory:")
        checkpoint_manager = CheckpointManager(checkpoint_dir=":memory:")
        retry_manager = SmartRetryManager()
        rate_limiter = AdaptiveRateLimiter(initial_rate=5.0)
        provenance_manager = ProvenanceManager()

        # Simulate scraping workflow
        content = '{"game_id": "123", "score": "110-108"}'

        # 1. Validate data
        validation_result = await validation_manager.validate_data(
            content, "espn", "game_summary"
        )
        assert validation_result.is_valid

        # 2. Check for duplicates
        update_manager = IncrementalUpdateManager(dedup_manager, checkpoint_manager)
        should_update, existing = await update_manager.should_update(
            content, "game_data"
        )
        assert should_update

        # 3. Record provenance
        metadata = await provenance_manager.track_data_creation(
            source_name="integration_test", source_version="v1.0.0", content=content
        )
        assert metadata.data_id is not None

        # 4. Save checkpoint
        checkpoint_data = {"last_processed": "2024-10-13", "total_games": 1}
        await checkpoint_manager.save_checkpoint("integration_test", checkpoint_data)

        # 5. Test retry with rate limiting
        async def mock_request():
            await rate_limiter.acquire()
            return "success"

        result = await retry_manager.execute_with_retry(mock_request)
        assert result == "success"

        # 6. Verify all components worked together
        checkpoint = await checkpoint_manager.load_checkpoint("integration_test")
        assert checkpoint.data == checkpoint_data

        stats = await update_manager.get_update_stats()
        assert stats["deduplication"]["total_hashes"] > 0


# Performance tests
class TestPerformance:
    """Performance tests for new components"""

    @pytest.mark.asyncio
    async def test_validation_performance(self):
        """Test validation performance with large datasets"""
        validator = ESPNSchemaValidator()

        # Create large dataset
        large_data = {
            "id": "12345",
            "date": "2024-10-13",
            "competitions": [
                {
                    "competitors": [
                        {"team": {"displayName": "Lakers"}, "score": "110"},
                        {"team": {"displayName": "Warriors"}, "score": "108"},
                    ]
                }
            ],
        }

        # Test multiple validations
        start_time = time.time()
        for i in range(100):
            await validator.validate_game_data(large_data)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete 100 validations in reasonable time
        assert duration < 5.0  # Less than 5 seconds
        assert duration / 100 < 0.05  # Less than 50ms per validation

    @pytest.mark.asyncio
    async def test_deduplication_performance(self):
        """Test deduplication performance"""
        dedup_manager = DeduplicationManager(local_db_path=":memory:")

        # Test with many content items
        start_time = time.time()

        for i in range(1000):
            content = f'{{"game_id": "{i}", "score": "110-108"}}'
            await dedup_manager.record_content(content, "game_data")

        end_time = time.time()
        duration = end_time - start_time

        # Should handle 1000 records efficiently
        assert duration < 10.0  # Less than 10 seconds
        assert duration / 1000 < 0.01  # Less than 10ms per record


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])





