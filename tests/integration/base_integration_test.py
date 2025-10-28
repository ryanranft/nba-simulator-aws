"""
Base Integration Test Class

Provides utilities for testing extractors with real data.
"""

import unittest
import time
import psutil
import os
from typing import Any, Dict, Callable
from nba_simulator.database.connection import execute_query
from nba_simulator.config.loader import config


class BaseIntegrationTest(unittest.TestCase):
    """
    Base class for integration tests.

    Provides:
    - Database connection utilities
    - Data comparison methods
    - Performance measurement
    - Test data validation
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.db_available = cls._check_database_connection()
        if not cls.db_available:
            raise unittest.SkipTest("Database not available for integration tests")

        # Store process for memory tracking
        cls.process = psutil.Process(os.getpid())

    @classmethod
    def _check_database_connection(cls) -> bool:
        """
        Check if database is accessible.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            result = execute_query("SELECT 1 as test;")
            return result is not None and len(result) > 0 and result[0].get('test') == 1
        except Exception as e:
            print(f"Database connection check failed: {e}")
            return False

    def get_sample_games(self, limit: int = 10) -> list:
        """
        Get sample game IDs from database for testing.

        Args:
            limit: Number of games to retrieve

        Returns:
            List of game IDs
        """
        try:
            query = f"""
                SELECT DISTINCT game_id
                FROM games
                ORDER BY game_date DESC
                LIMIT {limit};
            """
            results = execute_query(query)
            return [row['game_id'] for row in results] if results else []
        except Exception as e:
            self.skipTest(f"Could not retrieve sample games: {e}")

    def compare_record_counts(
        self,
        extractor_count: int,
        database_count: int,
        tolerance: float = 0.05
    ) -> bool:
        """
        Compare record counts with tolerance.

        Args:
            extractor_count: Count from extractor
            database_count: Count from database
            tolerance: Acceptable difference (0.05 = 5%)

        Returns:
            True if counts match within tolerance
        """
        if database_count == 0:
            return extractor_count == 0

        diff = abs(extractor_count - database_count) / database_count
        return diff <= tolerance

    def measure_performance(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Measure execution time and memory usage of a function.

        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Dictionary with performance metrics and function result
        """
        # Get initial memory
        mem_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Measure execution time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # Get final memory
        mem_after = self.process.memory_info().rss / 1024 / 1024  # MB

        return {
            'result': result,
            'execution_time_seconds': end_time - start_time,
            'memory_used_mb': mem_after - mem_before,
            'memory_before_mb': mem_before,
            'memory_after_mb': mem_after
        }

    def validate_output_structure(
        self,
        output: Dict[str, Any],
        required_keys: list
    ) -> bool:
        """
        Validate output has required structure.

        Args:
            output: Output dictionary to validate
            required_keys: List of required keys

        Returns:
            True if all required keys present
        """
        if not isinstance(output, dict):
            return False

        return all(key in output for key in required_keys)

    def assert_performance_acceptable(
        self,
        performance: Dict[str, Any],
        max_time_seconds: float = 300,
        max_memory_mb: float = 1000
    ):
        """
        Assert performance is within acceptable bounds.

        Args:
            performance: Performance metrics from measure_performance
            max_time_seconds: Maximum acceptable execution time
            max_memory_mb: Maximum acceptable memory usage
        """
        exec_time = performance['execution_time_seconds']
        memory_used = performance['memory_used_mb']

        self.assertLess(
            exec_time,
            max_time_seconds,
            f"Execution time {exec_time:.2f}s exceeds max {max_time_seconds}s"
        )

        self.assertLess(
            memory_used,
            max_memory_mb,
            f"Memory usage {memory_used:.2f}MB exceeds max {max_memory_mb}MB"
        )

