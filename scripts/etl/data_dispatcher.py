#!/usr/bin/env python3
"""
Data Collection Dispatcher - Unified Routing for NBA Data Scrapers

Provides centralized dispatcher pattern for routing data collection tasks to
appropriate scrapers based on data source. Implements the ETL pattern with:
- Registry-based scraper routing
- Factory pattern for scraper instantiation
- Task prioritization and queuing
- Error handling and retry logic
- Integration with ADCE autonomous system

Based on Phase 0.13 (rec_044) requirements.

Usage:
    from data_dispatcher import DataCollectionDispatcher, ScraperTask

    # Initialize dispatcher
    dispatcher = DataCollectionDispatcher()

    # Create task
    task = ScraperTask(
        source="espn",
        operation="scrape_date",
        params={"date": "20250101"}
    )

    # Dispatch task
    result = await dispatcher.dispatch(task)

Version: 1.0
Created: October 25, 2025
Implements: Phase 0.13 - Dispatcher Pipeline (rec_044)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import base scraper and configuration
from scripts.etl.async_scraper_base import AsyncBaseScraper, ScraperStats
from scripts.etl.scraper_config import ScraperConfig, ScraperConfigManager

# Import concrete scraper implementations
try:
    from scripts.etl.espn_async_scraper import ESPNAsyncScraper
except ImportError:
    ESPNAsyncScraper = None

try:
    from scripts.etl.nba_api_async_scraper import NBAAPIAsyncScraper
except ImportError:
    NBAAPIAsyncScraper = None

try:
    from scripts.etl.basketball_reference_comprehensive_scraper import (
        BasketballReferenceComprehensiveScraper,
    )
except ImportError:
    BasketballReferenceComprehensiveScraper = None

try:
    from scripts.etl.hoopr_incremental_scraper import HoopRIncrementalScraper
except ImportError:
    HoopRIncrementalScraper = None


class TaskPriority(Enum):
    """Priority levels for scraper tasks"""

    CRITICAL = 1  # Immediate execution (e.g., live games)
    HIGH = 2  # High priority (e.g., recent games, missing data)
    NORMAL = 3  # Normal priority (e.g., scheduled scrapes)
    LOW = 4  # Low priority (e.g., historical backfill)


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ScraperTask:
    """Represents a data collection task"""

    source: str  # Data source (espn, nba_api, basketball_reference, etc.)
    operation: str  # Operation to perform (scrape, scrape_date, etc.)
    params: Dict[str, Any] = field(default_factory=dict)  # Parameters for the operation
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Any] = None

    def __post_init__(self):
        """Validate task after initialization"""
        if not self.source:
            raise ValueError("Task source cannot be empty")
        if not self.operation:
            raise ValueError("Task operation cannot be empty")

    def mark_running(self):
        """Mark task as running"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, result: Any = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error

    def mark_retrying(self):
        """Mark task as retrying"""
        self.status = TaskStatus.RETRYING
        self.retry_count += 1

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries

    @property
    def elapsed_time(self) -> Optional[float]:
        """Calculate elapsed time in seconds"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()


@dataclass
class DispatcherStats:
    """Statistics for dispatcher operations"""

    tasks_dispatched: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    total_scraper_requests: int = 0
    total_scraper_successes: int = 0
    total_scraper_failures: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        if self.tasks_dispatched == 0:
            return 0.0
        return self.tasks_completed / self.tasks_dispatched

    @property
    def elapsed_time(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()


class DataCollectionDispatcher:
    """
    Dispatcher for routing data collection tasks to appropriate scrapers.

    Implements registry pattern for scraper management and factory pattern
    for scraper instantiation. Provides centralized error handling and retry logic.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize dispatcher.

        Args:
            config_file: Path to scraper configuration YAML file
        """
        self.logger = logging.getLogger(__name__)
        self.stats = DispatcherStats()

        # Initialize configuration manager
        if config_file:
            self.config_manager = ScraperConfigManager(config_file)
        else:
            # Use default config path
            default_config = (
                Path(__file__).parent.parent.parent / "config" / "scraper_config.yaml"
            )
            if default_config.exists():
                self.config_manager = ScraperConfigManager(str(default_config))
            else:
                self.logger.warning("No configuration file found, using defaults")
                self.config_manager = None

        # Scraper registry: maps source name -> scraper class
        self.scraper_registry: Dict[str, Type[AsyncBaseScraper]] = {}

        # Active scrapers: maps source name -> scraper instance
        self.active_scrapers: Dict[str, AsyncBaseScraper] = {}

        # Task queue (priority-based)
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # Register available scrapers
        self._register_scrapers()

        self.logger.info(
            f"Dispatcher initialized with {len(self.scraper_registry)} scrapers"
        )

    def _register_scrapers(self):
        """Register all available scraper implementations"""
        # ESPN scraper
        if ESPNAsyncScraper:
            self.scraper_registry["espn"] = ESPNAsyncScraper
            self.logger.debug("Registered ESPN scraper")

        # NBA API scraper
        if NBAAPIAsyncScraper:
            self.scraper_registry["nba_api"] = NBAAPIAsyncScraper
            self.logger.debug("Registered NBA API scraper")

        # Basketball Reference scraper
        if BasketballReferenceComprehensiveScraper:
            self.scraper_registry["basketball_reference"] = (
                BasketballReferenceComprehensiveScraper
            )
            self.logger.debug("Registered Basketball Reference scraper")

        # hoopR scraper
        if HoopRIncrementalScraper:
            self.scraper_registry["hoopr"] = HoopRIncrementalScraper
            self.logger.debug("Registered hoopR scraper")

        if not self.scraper_registry:
            self.logger.warning("No scrapers registered! Check scraper imports")

    def register_scraper(
        self, source: str, scraper_class: Type[AsyncBaseScraper]
    ) -> None:
        """
        Manually register a scraper.

        Args:
            source: Data source identifier
            scraper_class: Scraper class (must extend AsyncBaseScraper)
        """
        if not issubclass(scraper_class, AsyncBaseScraper):
            raise TypeError(f"{scraper_class} must extend AsyncBaseScraper")

        self.scraper_registry[source] = scraper_class
        self.logger.info(f"Registered scraper for source: {source}")

    def get_scraper_config(self, source: str) -> Optional[ScraperConfig]:
        """Get configuration for a specific scraper"""
        if not self.config_manager:
            return None

        try:
            return self.config_manager.get_scraper_config(source)
        except Exception as e:
            self.logger.error(f"Error getting config for {source}: {e}")
            return None

    async def get_scraper(self, source: str) -> Optional[AsyncBaseScraper]:
        """
        Get or create scraper instance for source.

        Args:
            source: Data source identifier

        Returns:
            Scraper instance or None if not available
        """
        # Check if already active
        if source in self.active_scrapers:
            return self.active_scrapers[source]

        # Check if registered
        if source not in self.scraper_registry:
            self.logger.error(f"No scraper registered for source: {source}")
            return None

        # Get scraper class
        scraper_class = self.scraper_registry[source]

        # Get configuration
        config = self.get_scraper_config(source)
        if not config:
            self.logger.error(f"No configuration found for source: {source}")
            return None

        # Create scraper instance
        try:
            scraper = scraper_class(config)
            self.active_scrapers[source] = scraper
            self.logger.info(f"Created scraper instance for: {source}")
            return scraper
        except Exception as e:
            self.logger.error(f"Error creating scraper for {source}: {e}")
            return None

    async def dispatch(self, task: ScraperTask) -> ScraperTask:
        """
        Dispatch a single task to appropriate scraper.

        Args:
            task: ScraperTask to execute

        Returns:
            Task with updated status and result
        """
        self.stats.tasks_dispatched += 1
        self.logger.info(
            f"Dispatching task: {task.source}.{task.operation} (priority={task.priority.name})"
        )

        # Mark task as running
        task.mark_running()

        try:
            # Get scraper for source
            scraper = await self.get_scraper(task.source)
            if not scraper:
                raise ValueError(f"No scraper available for source: {task.source}")

            # Execute operation
            result = await self._execute_task(scraper, task)

            # Update stats from scraper
            if hasattr(scraper, "stats"):
                self._update_stats_from_scraper(scraper.stats)

            # Mark task as completed
            task.mark_completed(result)
            self.stats.tasks_completed += 1
            self.logger.info(
                f"Task completed: {task.source}.{task.operation} (elapsed={task.elapsed_time:.2f}s)"
            )

        except Exception as e:
            # Handle failure
            error_msg = f"Task failed: {str(e)}"
            self.logger.error(error_msg)

            if task.can_retry:
                task.mark_retrying()
                self.stats.tasks_retried += 1
                self.logger.info(
                    f"Retrying task ({task.retry_count}/{task.max_retries})"
                )
                # Retry task
                return await self.dispatch(task)
            else:
                task.mark_failed(error_msg)
                self.stats.tasks_failed += 1

        return task

    async def _execute_task(self, scraper: AsyncBaseScraper, task: ScraperTask) -> Any:
        """
        Execute task operation on scraper.

        Args:
            scraper: Scraper instance
            task: Task to execute

        Returns:
            Result from scraper operation
        """
        operation = task.operation
        params = task.params

        # Check if operation exists
        if not hasattr(scraper, operation):
            raise AttributeError(f"Scraper has no operation: {operation}")

        # Get operation method
        operation_method = getattr(scraper, operation)

        # Execute operation
        if asyncio.iscoroutinefunction(operation_method):
            result = await operation_method(**params)
        else:
            result = operation_method(**params)

        return result

    def _update_stats_from_scraper(self, scraper_stats: ScraperStats):
        """Update dispatcher stats from scraper stats"""
        self.stats.total_scraper_requests += scraper_stats.requests_made
        self.stats.total_scraper_successes += scraper_stats.requests_successful
        self.stats.total_scraper_failures += scraper_stats.requests_failed

    async def dispatch_batch(self, tasks: List[ScraperTask]) -> List[ScraperTask]:
        """
        Dispatch multiple tasks concurrently.

        Args:
            tasks: List of tasks to execute

        Returns:
            List of tasks with results
        """
        self.logger.info(f"Dispatching batch of {len(tasks)} tasks")

        # Execute tasks concurrently
        results = await asyncio.gather(
            *[self.dispatch(task) for task in tasks], return_exceptions=True
        )

        # Handle exceptions
        completed_tasks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tasks[i].mark_failed(str(result))
                self.stats.tasks_failed += 1
            else:
                completed_tasks.append(result)

        self.logger.info(
            f"Batch completed: {len(completed_tasks)}/{len(tasks)} successful"
        )

        return completed_tasks

    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        return list(self.scraper_registry.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        return {
            "tasks_dispatched": self.stats.tasks_dispatched,
            "tasks_completed": self.stats.tasks_completed,
            "tasks_failed": self.stats.tasks_failed,
            "tasks_retried": self.stats.tasks_retried,
            "success_rate": self.stats.success_rate,
            "elapsed_time": self.stats.elapsed_time,
            "scraper_requests": self.stats.total_scraper_requests,
            "scraper_successes": self.stats.total_scraper_successes,
            "scraper_failures": self.stats.total_scraper_failures,
        }

    async def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up dispatcher resources")

        # Stop all active scrapers
        for source, scraper in self.active_scrapers.items():
            try:
                await scraper.stop()
                self.logger.debug(f"Stopped scraper: {source}")
            except Exception as e:
                self.logger.error(f"Error stopping scraper {source}: {e}")

        self.active_scrapers.clear()


# Convenience functions
def create_task(
    source: str,
    operation: str = "scrape",
    params: Optional[Dict[str, Any]] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> ScraperTask:
    """Create a scraper task"""
    return ScraperTask(
        source=source, operation=operation, params=params or {}, priority=priority
    )


# Example usage
if __name__ == "__main__":

    async def main():
        """Example dispatcher usage"""
        # Initialize dispatcher
        dispatcher = DataCollectionDispatcher()

        print("=" * 80)
        print("Data Collection Dispatcher Example")
        print("=" * 80)

        # Show available sources
        sources = dispatcher.get_available_sources()
        print(f"\nAvailable data sources: {', '.join(sources)}")

        # Create sample tasks
        tasks = [
            create_task("espn", "scrape", {"days_back": 7}, TaskPriority.HIGH),
            create_task("nba_api", "scrape", {}, TaskPriority.NORMAL),
            create_task(
                "basketball_reference", "scrape", {"tier": 1}, TaskPriority.LOW
            ),
        ]

        print(f"\nCreated {len(tasks)} tasks")

        # Dispatch tasks (dry run)
        # results = await dispatcher.dispatch_batch(tasks)

        # Show statistics
        stats = dispatcher.get_stats()
        print(f"\nDispatcher Statistics:")
        print(f"  Tasks dispatched: {stats['tasks_dispatched']}")
        print(f"  Tasks completed: {stats['tasks_completed']}")
        print(f"  Tasks failed: {stats['tasks_failed']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")

        # Cleanup
        await dispatcher.cleanup()

        print("\n✅ Dispatcher example complete")

    # Run example
    asyncio.run(main())
