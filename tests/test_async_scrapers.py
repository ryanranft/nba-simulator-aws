#!/usr/bin/env python3
"""
Test Suite for Async Scraper Infrastructure

Comprehensive test suite for the new async scraping infrastructure:
- AsyncBaseScraper functionality
- Error handling and retry logic
- Telemetry and metrics collection
- Configuration management
- ESPN async scraper

Usage:
    python -m pytest tests/test_async_scrapers.py -v
    python -m pytest tests/test_async_scrapers.py::TestAsyncBaseScraper -v
    python -m pytest tests/test_async_scrapers.py -k "test_rate_limiting" -v

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.etl.async_scraper_base import AsyncBaseScraper, ScraperConfig, ScraperStats
from scripts.etl.scraper_error_handler import (
    ScraperErrorHandler,
    NetworkError,
    RateLimitError,
    ServerError,
    ClientError,
    ContentError,
    CircuitBreaker,
)
from scripts.etl.scraper_telemetry import (
    ScraperTelemetry,
    MetricsCollector,
    TelemetryEvent,
)
from scripts.etl.scraper_config import ScraperConfigManager, ScraperConfig
from scripts.etl.espn_async_scraper import ESPNAsyncScraper


class TestScraperConfig:
    """Test ScraperConfig functionality"""

    def test_config_creation(self):
        """Test basic config creation"""
        config = ScraperConfig(
            name="test", base_url="https://example.com", rate_limit=0.5, timeout=60
        )

        assert config.name == "test"
        assert config.base_url == "https://example.com"
        assert config.rate_limit == 0.5
        assert config.timeout == 60
        assert config.max_concurrent == 10
        assert config.dry_run is False

    def test_config_defaults(self):
        """Test config default values"""
        config = ScraperConfig(name="test", base_url="https://example.com")

        assert config.user_agent == "NBA-Simulator-Scraper/1.0"
        assert config.timeout == 30
        assert config.max_concurrent == 10
        assert config.dry_run is False
        assert config.rate_limit == 1.0


class TestScraperStats:
    """Test ScraperStats functionality"""

    def test_stats_initialization(self):
        """Test stats initialization"""
        stats = ScraperStats()

        assert stats.requests_made == 0
        assert stats.requests_successful == 0
        assert stats.requests_failed == 0
        assert stats.success_rate == 0.0
        assert stats.elapsed_time >= 0

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stats = ScraperStats()

        # No requests
        assert stats.success_rate == 0.0

        # Some successful requests
        stats.requests_made = 10
        stats.requests_successful = 8
        assert stats.success_rate == 0.8

        # All failed requests
        stats.requests_successful = 0
        stats.requests_failed = 10
        assert stats.success_rate == 0.0


class TestAsyncBaseScraper:
    """Test AsyncBaseScraper functionality"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return ScraperConfig(
            name="test_scraper",
            base_url="https://httpbin.org",
            rate_limit=1.0,
            timeout=10,
            max_concurrent=5,
            dry_run=True,
        )

    @pytest.fixture
    def scraper(self, config):
        """Test scraper instance"""

        class TestScraper(AsyncBaseScraper):
            async def scrape(self):
                pass

        return TestScraper(config)

    @pytest.mark.asyncio
    async def test_scraper_initialization(self, scraper):
        """Test scraper initialization"""
        assert scraper.config.name == "test_scraper"
        assert scraper.config.base_url == "https://httpbin.org"
        assert scraper.stats.requests_made == 0
        assert scraper._session is None

    @pytest.mark.asyncio
    async def test_scraper_start_stop(self, scraper):
        """Test scraper start and stop"""
        await scraper.start()
        assert scraper._session is not None

        await scraper.stop()
        assert scraper._session.closed

    @pytest.mark.asyncio
    async def test_context_manager(self, scraper):
        """Test scraper as context manager"""
        async with scraper:
            assert scraper._session is not None
            assert not scraper._session.closed

        assert scraper._session.closed

    @pytest.mark.asyncio
    async def test_fetch_url_success(self, scraper):
        """Test successful URL fetch"""
        await scraper.start()

        response = await scraper.fetch_url("https://httpbin.org/json")
        assert response is not None
        assert response.status == 200
        assert scraper.stats.requests_made == 1
        assert scraper.stats.requests_successful == 1

    @pytest.mark.asyncio
    async def test_fetch_url_failure(self, scraper):
        """Test failed URL fetch"""
        await scraper.start()

        response = await scraper.fetch_url("https://httpbin.org/status/404")
        assert response is None
        assert scraper.stats.requests_made == 1
        assert scraper.stats.requests_failed == 1

    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraper):
        """Test rate limiting functionality"""
        await scraper.start()

        start_time = time.time()

        # Make two requests quickly
        await scraper.fetch_url("https://httpbin.org/json")
        await scraper.fetch_url("https://httpbin.org/json")

        elapsed = time.time() - start_time

        # Should take at least 1 second due to rate limiting
        assert elapsed >= 0.9  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_parse_json_response(self, scraper):
        """Test JSON response parsing"""
        await scraper.start()

        response = await scraper.fetch_url("https://httpbin.org/json")
        assert response is not None

        data = await scraper.parse_json_response(response)
        assert data is not None
        assert isinstance(data, dict)
        assert scraper.stats.data_items_scraped == 1

    @pytest.mark.asyncio
    async def test_store_data(self, scraper):
        """Test data storage"""
        test_data = {"test": "data", "number": 42}

        success = await scraper.store_data(test_data, "test.json")
        assert success
        assert scraper.stats.data_items_stored == 1

        # Check file was created
        file_path = scraper.output_dir / "test.json"
        assert file_path.exists()

        # Check content
        with open(file_path, "r") as f:
            stored_data = json.load(f)
        assert stored_data == test_data

    @pytest.mark.asyncio
    async def test_content_hash_generation(self, scraper):
        """Test content hash generation"""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}  # Same data, different order
        data3 = {"a": 1, "b": 3}  # Different data

        hash1 = scraper.generate_content_hash(data1)
        hash2 = scraper.generate_content_hash(data2)
        hash3 = scraper.generate_content_hash(data3)

        assert hash1 == hash2  # Same content, different order
        assert hash1 != hash3  # Different content


class TestScraperErrorHandler:
    """Test ScraperErrorHandler functionality"""

    @pytest.fixture
    def error_handler(self):
        """Test error handler"""
        return ScraperErrorHandler()

    def test_error_handler_initialization(self, error_handler):
        """Test error handler initialization"""
        assert error_handler.error_stats == {}
        assert error_handler.circuit_breakers == {}
        assert len(error_handler.retry_strategies) > 0

    @pytest.mark.asyncio
    async def test_network_error_handling(self, error_handler):
        """Test network error handling"""
        error = NetworkError("Connection timeout")

        # First attempt should retry
        should_retry = await error_handler.handle_network_error(error)
        assert should_retry is True

        # Update retry count
        error.context.retry_count = 3

        # After max attempts, should not retry
        should_retry = await error_handler.handle_network_error(error)
        assert should_retry is False

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, error_handler):
        """Test rate limit error handling"""
        error = RateLimitError("Too many requests", retry_after=60)

        should_retry = await error_handler.handle_rate_limit_error(error)
        assert should_retry is True

    @pytest.mark.asyncio
    async def test_client_error_handling(self, error_handler):
        """Test client error handling (no retry)"""
        error = ClientError("Bad request")

        should_retry = await error_handler.handle_client_error(error)
        assert should_retry is False

    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        # Initially closed
        assert cb.can_execute() is True

        # Record failures
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute() is True

        # Third failure should open circuit
        cb.record_failure()
        assert cb.can_execute() is False

        # Record success should close circuit
        cb.record_success()
        assert cb.can_execute() is True


class TestScraperTelemetry:
    """Test ScraperTelemetry functionality"""

    @pytest.fixture
    def telemetry(self):
        """Test telemetry instance"""
        return ScraperTelemetry("test_scraper")

    def test_telemetry_initialization(self, telemetry):
        """Test telemetry initialization"""
        assert telemetry.scraper_name == "test_scraper"
        assert telemetry.metrics is not None
        assert telemetry.events == []

    def test_log_event(self, telemetry):
        """Test event logging"""
        telemetry.log_event("test_operation", "Test message", data={"key": "value"})

        assert len(telemetry.events) == 1
        event = telemetry.events[0]
        assert event.operation == "test_operation"
        assert event.message == "Test message"
        assert event.data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_track_operation_success(self, telemetry):
        """Test operation tracking (success)"""
        async with telemetry.track_operation("test_op"):
            await asyncio.sleep(0.01)  # Small delay

        assert len(telemetry.events) >= 1
        # Should have start and completion events
        assert any(
            e.operation == "test_op" and e.success is True for e in telemetry.events
        )

    @pytest.mark.asyncio
    async def test_track_operation_failure(self, telemetry):
        """Test operation tracking (failure)"""
        with pytest.raises(ValueError):
            async with telemetry.track_operation("test_op"):
                raise ValueError("Test error")

        # Should have error event
        assert any(
            e.operation == "test_op" and e.success is False for e in telemetry.events
        )

    def test_health_status(self, telemetry):
        """Test health status calculation"""
        health = telemetry.get_health_status()

        assert "scraper_name" in health
        assert "status" in health
        assert "timestamp" in health
        assert health["scraper_name"] == "test_scraper"


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    @pytest.fixture
    def metrics(self):
        """Test metrics collector"""
        return MetricsCollector()

    def test_metrics_initialization(self, metrics):
        """Test metrics initialization"""
        assert metrics.performance.requests_total == 0
        assert metrics.data_quality.total_items_validated == 0
        assert metrics.custom_metrics == {}

    def test_record_request(self, metrics):
        """Test request recording"""
        metrics.record_request(success=True, duration_ms=100.0, scraper_name="test")

        assert metrics.performance.requests_total == 1
        assert metrics.performance.requests_successful == 1
        assert metrics.performance.average_response_time_ms == 100.0

    def test_record_data_item(self, metrics):
        """Test data item recording"""
        metrics.record_data_item("test_type", "test_scraper")

        assert metrics.performance.data_items_scraped == 1

    def test_record_validation(self, metrics):
        """Test validation recording"""
        metrics.record_validation(passed=True)
        metrics.record_validation(passed=False, error_type="schema")

        assert metrics.data_quality.total_items_validated == 2
        assert metrics.data_quality.items_passed_validation == 1
        assert metrics.data_quality.items_failed_validation == 1
        assert metrics.data_quality.schema_validation_errors == 1


class TestScraperConfigManager:
    """Test ScraperConfigManager functionality"""

    @pytest.fixture
    def temp_config_file(self):
        """Temporary config file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "scrapers": {
                    "test_scraper": {
                        "name": "test_scraper",
                        "base_url": "https://example.com",
                        "rate_limit": {"requests_per_second": 2.0},
                        "retry": {"max_attempts": 5},
                        "storage": {"s3_bucket": "test-bucket"},
                        "monitoring": {"log_level": "DEBUG"},
                    }
                },
                "global": {"default_timeout": 60},
            }
            import yaml

            yaml.dump(config_data, f)
            return f.name

    def test_config_manager_initialization(self, temp_config_file):
        """Test config manager initialization"""
        manager = ScraperConfigManager(temp_config_file)

        assert len(manager.configs) == 1
        assert "test_scraper" in manager.configs

    def test_get_scraper_config(self, temp_config_file):
        """Test getting scraper config"""
        manager = ScraperConfigManager(temp_config_file)

        config = manager.get_scraper_config("test_scraper")
        assert config is not None
        assert config.name == "test_scraper"
        assert config.base_url == "https://example.com"
        assert config.rate_limit.requests_per_second == 2.0
        assert config.retry.max_attempts == 5

    def test_config_validation(self, temp_config_file):
        """Test config validation"""
        manager = ScraperConfigManager(temp_config_file)

        errors = manager.validate_config("test_scraper")
        assert len(errors) == 0  # Should be valid

    def test_invalid_config_validation(self, temp_config_file):
        """Test invalid config validation"""
        manager = ScraperConfigManager(temp_config_file)

        # Test non-existent scraper
        errors = manager.validate_config("nonexistent")
        assert len(errors) > 0


class TestESPNAsyncScraper:
    """Test ESPNAsyncScraper functionality"""

    @pytest.fixture
    def espn_config(self):
        """ESPN scraper configuration"""
        return ScraperConfig(
            name="espn",
            base_url="https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
            rate_limit=1.0,
            timeout=30,
            max_concurrent=5,
            dry_run=True,
        )

    @pytest.fixture
    def espn_scraper(self, espn_config):
        """ESPN scraper instance"""
        return ESPNAsyncScraper(espn_config, days_back=1)

    def test_espn_scraper_initialization(self, espn_scraper):
        """Test ESPN scraper initialization"""
        assert espn_scraper.config.name == "espn"
        assert espn_scraper.days_back == 1
        assert espn_scraper.error_handler is not None
        assert espn_scraper.telemetry is not None

    def test_extract_game_ids(self, espn_scraper):
        """Test game ID extraction"""
        schedule_data = {
            "events": [
                {"id": "12345", "name": "Game 1"},
                {"id": "67890", "name": "Game 2"},
                {"name": "Game 3"},  # No ID
            ]
        }

        game_ids = espn_scraper._extract_game_ids(schedule_data)
        assert len(game_ids) == 2
        assert "12345" in game_ids
        assert "67890" in game_ids

    def test_extract_game_ids_empty(self, espn_scraper):
        """Test game ID extraction with empty data"""
        schedule_data = {"events": []}

        game_ids = espn_scraper._extract_game_ids(schedule_data)
        assert len(game_ids) == 0

    @pytest.mark.asyncio
    async def test_scraper_context_manager(self, espn_scraper):
        """Test ESPN scraper as context manager"""
        async with espn_scraper:
            assert espn_scraper._session is not None
            assert not espn_scraper._session.closed

        assert espn_scraper._session.closed


# Integration tests
class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_full_scraper_workflow(self):
        """Test complete scraper workflow"""
        config = ScraperConfig(
            name="integration_test",
            base_url="https://httpbin.org",
            rate_limit=2.0,
            timeout=10,
            max_concurrent=3,
            dry_run=True,
        )

        class IntegrationScraper(AsyncBaseScraper):
            async def scrape(self):
                # Test basic functionality
                response = await self.fetch_url("https://httpbin.org/json")
                if response:
                    data = await self.parse_json_response(response)
                    if data:
                        await self.store_data(data, "test.json")

        async with IntegrationScraper(config) as scraper:
            await scraper.scrape()

        # Verify results
        assert scraper.stats.requests_made > 0
        assert scraper.stats.requests_successful > 0
        assert scraper.stats.data_items_scraped > 0
        assert scraper.stats.data_items_stored > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])





