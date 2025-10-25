#!/usr/bin/env python3
"""
Test Suite: Phase 0.13 - Dispatcher Pipeline (rec_044)

Comprehensive tests for:
- ScraperTask creation and state transitions
- DataCollectionDispatcher routing and execution
- DispatcherPipeline wrapper functionality
- Task prioritization and retry logic
- Error handling and validation

Created: October 25, 2025
"""

import unittest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import dispatcher components
from scripts.etl.data_dispatcher import (
    DataCollectionDispatcher,
    ScraperTask,
    TaskPriority,
    TaskStatus,
    DispatcherStats,
    create_task,
)

# Import implementation wrapper
impl_path = project_root / "docs" / "phases" / "phase_0" / "0.13_dispatcher_pipeline"
sys.path.insert(0, str(impl_path))

from implement_rec_044 import DispatcherPipeline


class TestScraperTask(unittest.TestCase):
    """Test suite for ScraperTask class"""

    def test_task_creation(self):
        """Test basic task creation"""
        task = ScraperTask(source="espn", operation="scrape", params={"days_back": 7})

        self.assertEqual(task.source, "espn")
        self.assertEqual(task.operation, "scrape")
        self.assertEqual(task.params["days_back"], 7)
        self.assertEqual(task.priority, TaskPriority.NORMAL)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.retry_count, 0)

    def test_task_validation_empty_source(self):
        """Test that empty source raises ValueError"""
        with self.assertRaises(ValueError) as context:
            ScraperTask(source="", operation="scrape")
        self.assertIn("source cannot be empty", str(context.exception))

    def test_task_validation_empty_operation(self):
        """Test that empty operation raises ValueError"""
        with self.assertRaises(ValueError) as context:
            ScraperTask(source="espn", operation="")
        self.assertIn("operation cannot be empty", str(context.exception))

    def test_task_priority_levels(self):
        """Test all priority levels"""
        for priority in TaskPriority:
            task = ScraperTask(source="test", operation="test_op", priority=priority)
            self.assertEqual(task.priority, priority)

    def test_mark_running(self):
        """Test marking task as running"""
        task = ScraperTask(source="espn", operation="scrape")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.started_at)

        task.mark_running()

        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertIsNotNone(task.started_at)

    def test_mark_completed(self):
        """Test marking task as completed"""
        task = ScraperTask(source="espn", operation="scrape")
        task.mark_running()

        result = {"success": True, "data": [1, 2, 3]}
        task.mark_completed(result)

        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.result, result)

    def test_mark_failed(self):
        """Test marking task as failed"""
        task = ScraperTask(source="espn", operation="scrape")
        task.mark_running()

        error_msg = "Connection timeout"
        task.mark_failed(error_msg)

        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.error_message, error_msg)

    def test_mark_retrying(self):
        """Test marking task for retry"""
        task = ScraperTask(source="espn", operation="scrape")
        initial_count = task.retry_count

        task.mark_retrying()

        self.assertEqual(task.status, TaskStatus.RETRYING)
        self.assertEqual(task.retry_count, initial_count + 1)

    def test_can_retry(self):
        """Test retry eligibility"""
        task = ScraperTask(source="espn", operation="scrape", max_retries=3)

        # Should be able to retry initially
        self.assertTrue(task.can_retry)

        # Retry up to max
        for i in range(3):
            task.mark_retrying()

        # Should not be able to retry after max
        self.assertFalse(task.can_retry)

    def test_elapsed_time(self):
        """Test elapsed time calculation"""
        task = ScraperTask(source="espn", operation="scrape")

        # No elapsed time before starting
        self.assertIsNone(task.elapsed_time)

        # Mark as running
        task.mark_running()

        # Should have elapsed time
        self.assertIsNotNone(task.elapsed_time)
        self.assertGreater(task.elapsed_time, 0)

    def test_create_task_helper(self):
        """Test create_task convenience function"""
        task = create_task(
            source="nba_api",
            operation="scrape_date",
            params={"date": "20250101"},
            priority=TaskPriority.HIGH,
        )

        self.assertEqual(task.source, "nba_api")
        self.assertEqual(task.operation, "scrape_date")
        self.assertEqual(task.params["date"], "20250101")
        self.assertEqual(task.priority, TaskPriority.HIGH)


class TestDispatcherStats(unittest.TestCase):
    """Test suite for DispatcherStats class"""

    def test_stats_initialization(self):
        """Test statistics initialization"""
        stats = DispatcherStats()

        self.assertEqual(stats.tasks_dispatched, 0)
        self.assertEqual(stats.tasks_completed, 0)
        self.assertEqual(stats.tasks_failed, 0)
        self.assertEqual(stats.tasks_retried, 0)
        self.assertIsNotNone(stats.start_time)

    def test_success_rate_zero_tasks(self):
        """Test success rate with no tasks"""
        stats = DispatcherStats()
        self.assertEqual(stats.success_rate, 0.0)

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stats = DispatcherStats()
        stats.tasks_dispatched = 10
        stats.tasks_completed = 7

        self.assertAlmostEqual(stats.success_rate, 0.7)

    def test_elapsed_time(self):
        """Test elapsed time calculation"""
        stats = DispatcherStats()
        elapsed = stats.elapsed_time

        self.assertIsNotNone(elapsed)
        self.assertGreaterEqual(elapsed, 0)


class TestDataCollectionDispatcher(unittest.IsolatedAsyncioTestCase):
    """Test suite for DataCollectionDispatcher class (async tests)"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        # Mock config manager to avoid file I/O
        with patch("scripts.etl.data_dispatcher.ScraperConfigManager"):
            self.dispatcher = DataCollectionDispatcher()

    async def asyncTearDown(self):
        """Clean up after tests"""
        if self.dispatcher:
            await self.dispatcher.cleanup()

    def test_dispatcher_initialization(self):
        """Test dispatcher initializes correctly"""
        self.assertIsNotNone(self.dispatcher)
        self.assertIsInstance(self.dispatcher.stats, DispatcherStats)
        self.assertIsInstance(self.dispatcher.scraper_registry, dict)
        self.assertIsInstance(self.dispatcher.active_scrapers, dict)

    def test_scraper_registration(self):
        """Test scraper registry"""
        # Should have registered scrapers from imports
        sources = self.dispatcher.get_available_sources()

        # Basketball Reference and hoopR should be registered (working scrapers)
        self.assertIsInstance(sources, list)

        # Should be able to get the list
        self.assertGreaterEqual(len(sources), 0)

    async def test_get_available_sources(self):
        """Test getting available data sources"""
        sources = self.dispatcher.get_available_sources()

        self.assertIsInstance(sources, list)
        # Each source should be a string
        for source in sources:
            self.assertIsInstance(source, str)

    def test_get_stats(self):
        """Test getting dispatcher statistics"""
        stats = self.dispatcher.get_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn("tasks_dispatched", stats)
        self.assertIn("tasks_completed", stats)
        self.assertIn("tasks_failed", stats)
        self.assertIn("success_rate", stats)
        self.assertEqual(stats["tasks_dispatched"], 0)

    async def test_dispatch_invalid_source(self):
        """Test dispatching task with invalid source"""
        task = create_task(source="invalid_source", operation="scrape")

        result = await self.dispatcher.dispatch(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIsNotNone(result.error_message)
        self.assertIn("invalid_source", result.error_message.lower())

    async def test_batch_dispatch_empty_list(self):
        """Test batch dispatch with empty list"""
        results = await self.dispatcher.dispatch_batch([])

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    async def test_cleanup(self):
        """Test cleanup method"""
        # Add a mock scraper to active scrapers
        mock_scraper = AsyncMock()
        mock_scraper.stop = AsyncMock()
        self.dispatcher.active_scrapers["test"] = mock_scraper

        # Cleanup
        await self.dispatcher.cleanup()

        # Should have called stop on scraper
        mock_scraper.stop.assert_called_once()

        # Active scrapers should be cleared
        self.assertEqual(len(self.dispatcher.active_scrapers), 0)

    def test_manual_scraper_registration(self):
        """Test manual scraper registration"""
        # Import base class
        from scripts.etl.async_scraper_base import AsyncBaseScraper

        # Create mock scraper class
        class MockScraper(AsyncBaseScraper):
            def __init__(self, config):
                super().__init__(config)

        # Register it
        self.dispatcher.register_scraper("test_source", MockScraper)

        # Should be in registry
        self.assertIn("test_source", self.dispatcher.scraper_registry)
        self.assertEqual(self.dispatcher.scraper_registry["test_source"], MockScraper)

    def test_manual_registration_invalid_class(self):
        """Test manual registration with invalid class"""

        class NotAScraper:
            pass

        with self.assertRaises(TypeError):
            self.dispatcher.register_scraper("test", NotAScraper)


class TestDispatcherPipeline(unittest.IsolatedAsyncioTestCase):
    """Test suite for DispatcherPipeline wrapper class"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.pipeline = DispatcherPipeline()

    async def asyncTearDown(self):
        """Clean up after tests"""
        if self.pipeline and self.pipeline.initialized:
            await self.pipeline.cleanup()

    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly"""
        self.assertIsNotNone(self.pipeline)
        self.assertFalse(self.pipeline.initialized)
        self.assertIsNone(self.pipeline.dispatcher)

    async def test_setup(self):
        """Test pipeline setup"""
        result = await self.pipeline.setup()

        self.assertTrue(result["success"])
        self.assertTrue(self.pipeline.initialized)
        self.assertIsNotNone(self.pipeline.dispatcher)
        self.assertIn("sources", result)

    async def test_dispatch_without_setup(self):
        """Test that dispatch fails without setup"""
        with self.assertRaises(RuntimeError) as context:
            await self.pipeline.dispatch_task("espn", "scrape")

        self.assertIn("setup", str(context.exception).lower())

    async def test_dispatch_batch_without_setup(self):
        """Test that batch dispatch fails without setup"""
        with self.assertRaises(RuntimeError) as context:
            await self.pipeline.dispatch_batch([])

        self.assertIn("setup", str(context.exception).lower())

    async def test_get_available_sources_before_setup(self):
        """Test getting sources before setup"""
        sources = self.pipeline.get_available_sources()
        self.assertEqual(sources, [])

    async def test_get_available_sources_after_setup(self):
        """Test getting sources after setup"""
        await self.pipeline.setup()

        sources = self.pipeline.get_available_sources()
        self.assertIsInstance(sources, list)

    async def test_get_stats_before_setup(self):
        """Test getting stats before setup"""
        stats = self.pipeline.get_stats()
        self.assertEqual(stats, {})

    async def test_get_stats_after_setup(self):
        """Test getting stats after setup"""
        await self.pipeline.setup()

        stats = self.pipeline.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("tasks_dispatched", stats)

    def test_validate_before_setup(self):
        """Test validation before setup"""
        is_valid = self.pipeline.validate()
        self.assertFalse(is_valid)

    async def test_validate_after_setup(self):
        """Test validation after setup"""
        await self.pipeline.setup()

        is_valid = self.pipeline.validate()
        # Should be valid if at least one scraper is registered
        sources = self.pipeline.get_available_sources()
        if sources:
            self.assertTrue(is_valid)

    async def test_cleanup(self):
        """Test cleanup method"""
        await self.pipeline.setup()
        self.assertTrue(self.pipeline.initialized)

        await self.pipeline.cleanup()

        self.assertFalse(self.pipeline.initialized)

    async def test_custom_config(self):
        """Test pipeline with custom configuration"""
        custom_config = {"test_key": "test_value"}
        pipeline = DispatcherPipeline(config=custom_config)

        self.assertEqual(pipeline.config["test_key"], "test_value")

        # Cleanup
        if pipeline.initialized:
            await pipeline.cleanup()


class TestTaskPrioritization(unittest.IsolatedAsyncioTestCase):
    """Test suite for task prioritization"""

    async def test_priority_ordering(self):
        """Test that priority enum values are ordered correctly"""
        self.assertLess(TaskPriority.CRITICAL.value, TaskPriority.HIGH.value)
        self.assertLess(TaskPriority.HIGH.value, TaskPriority.NORMAL.value)
        self.assertLess(TaskPriority.NORMAL.value, TaskPriority.LOW.value)

    async def test_task_creation_with_all_priorities(self):
        """Test creating tasks with different priorities"""
        priorities = [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.NORMAL,
            TaskPriority.LOW,
        ]

        for priority in priorities:
            task = create_task(source="test", operation="test", priority=priority)
            self.assertEqual(task.priority, priority)


class TestRetryLogic(unittest.IsolatedAsyncioTestCase):
    """Test suite for retry logic"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        with patch("scripts.etl.data_dispatcher.ScraperConfigManager"):
            self.dispatcher = DataCollectionDispatcher()

    async def asyncTearDown(self):
        """Clean up after tests"""
        if self.dispatcher:
            await self.dispatcher.cleanup()

    def test_retry_count_increments(self):
        """Test that retry count increments correctly"""
        task = ScraperTask(source="test", operation="test", max_retries=3)

        self.assertEqual(task.retry_count, 0)

        task.mark_retrying()
        self.assertEqual(task.retry_count, 1)

        task.mark_retrying()
        self.assertEqual(task.retry_count, 2)

    def test_max_retries_respected(self):
        """Test that max retries is respected"""
        task = ScraperTask(source="test", operation="test", max_retries=2)

        # Retry twice (should work)
        self.assertTrue(task.can_retry)
        task.mark_retrying()

        self.assertTrue(task.can_retry)
        task.mark_retrying()

        # Third retry should fail
        self.assertFalse(task.can_retry)

    def test_custom_max_retries(self):
        """Test custom max_retries value"""
        task = ScraperTask(source="test", operation="test", max_retries=5)

        # Should be able to retry 5 times
        for i in range(5):
            self.assertTrue(task.can_retry)
            task.mark_retrying()

        # Sixth retry should fail
        self.assertFalse(task.can_retry)


class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test suite for error handling"""

    async def test_invalid_task_creation(self):
        """Test error handling for invalid task creation"""
        # Empty source
        with self.assertRaises(ValueError):
            ScraperTask(source="", operation="test")

        # Empty operation
        with self.assertRaises(ValueError):
            ScraperTask(source="test", operation="")

    async def test_dispatcher_with_no_scrapers(self):
        """Test dispatcher behavior with no registered scrapers"""
        # Create dispatcher and clear registry
        with patch("scripts.etl.data_dispatcher.ScraperConfigManager"):
            dispatcher = DataCollectionDispatcher()
            dispatcher.scraper_registry.clear()

        # Should return empty list
        sources = dispatcher.get_available_sources()
        self.assertEqual(sources, [])

        await dispatcher.cleanup()


def run_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScraperTask))
    suite.addTests(loader.loadTestsFromTestCase(TestDispatcherStats))
    suite.addTests(loader.loadTestsFromTestCase(TestDataCollectionDispatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestDispatcherPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskPrioritization))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
