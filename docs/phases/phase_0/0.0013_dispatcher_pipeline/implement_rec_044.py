#!/usr/bin/env python3
"""
Implementation: Dispatcher Pipeline for Data Collection (rec_044)

Implements Phase 0.0013: Data Collection Pipeline with Dispatcher and Crawlers

This implementation creates a modular data collection pipeline that uses a dispatcher
to route data to specific crawlers based on the data source. This facilitates the
integration of new data sources and maintains a standardized data format.

Recommendation ID: rec_044
Source: LLM Engineers Handbook
Priority: IMPORTANT
Phase: 0.13

Architecture:
- Dispatcher class routes tasks to appropriate scrapers
- Registry pattern for scraper management
- Factory pattern for scraper instantiation
- ETL pattern: Extract (scrape) → Transform (parse) → Load (S3/PostgreSQL)

Usage:
    from implement_rec_044 import DispatcherPipeline

    # Initialize pipeline
    pipeline = DispatcherPipeline()
    await pipeline.setup()

    # Dispatch tasks
    result = await pipeline.dispatch_task("espn", "scrape", {"days_back": 7})

    # Cleanup
    await pipeline.cleanup()

"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports
# From docs/phases/phase_0/0.0013_dispatcher_pipeline/ go up 4 levels to project root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our dispatcher implementation
from scripts.etl.data_dispatcher import (
    DataCollectionDispatcher,
    ScraperTask,
    TaskPriority,
    create_task,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DispatcherPipeline:
    """
    Implementation of Phase 0.0013: Dispatcher Pipeline

    Provides a unified interface for dispatching data collection tasks across
    multiple NBA data sources (ESPN, NBA API, Basketball Reference, hoopR, etc.)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Dispatcher Pipeline.

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.dispatcher: Optional[DataCollectionDispatcher] = None
        self.initialized = False
        logger.info(f"Initialized {self.__class__.__name__}")

    async def setup(self) -> Dict[str, Any]:
        """
        Set up the dispatcher pipeline.

        Returns:
            Setup results
        """
        logger.info("Setting up dispatcher pipeline...")

        try:
            # Initialize data collection dispatcher
            config_file = self.config.get("config_file")
            self.dispatcher = DataCollectionDispatcher(config_file=config_file)

            # Get available sources
            sources = self.dispatcher.get_available_sources()
            logger.info(f"Dispatcher initialized with {len(sources)} data sources")
            logger.info(f"Available sources: {', '.join(sources)}")

            self.initialized = True
            logger.info("✅ Setup complete")

            return {
                "success": True,
                "message": "Dispatcher pipeline setup complete",
                "sources": sources,
            }

        except Exception as e:
            error_msg = f"Setup failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    async def dispatch_task(
        self,
        source: str,
        operation: str = "scrape",
        params: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> ScraperTask:
        """
        Dispatch a single data collection task.

        Args:
            source: Data source (espn, nba_api, basketball_reference, etc.)
            operation: Operation to perform (scrape, scrape_date, etc.)
            params: Parameters for the operation
            priority: Task priority level

        Returns:
            Completed task with results

        Raises:
            RuntimeError: If dispatcher not initialized
        """
        if not self.initialized or not self.dispatcher:
            raise RuntimeError("Must call setup() before dispatching tasks")

        logger.info(f"Dispatching task: {source}.{operation}")

        # Create task
        task = create_task(source, operation, params, priority)

        # Dispatch task
        result_task = await self.dispatcher.dispatch(task)

        return result_task

    async def dispatch_batch(
        self, tasks_config: List[Dict[str, Any]]
    ) -> List[ScraperTask]:
        """
        Dispatch multiple tasks concurrently.

        Args:
            tasks_config: List of task configurations, each with:
                - source: Data source
                - operation: Operation name
                - params: Parameters dict
                - priority: Task priority (optional)

        Returns:
            List of completed tasks
        """
        if not self.initialized or not self.dispatcher:
            raise RuntimeError("Must call setup() before dispatching tasks")

        logger.info(f"Dispatching batch of {len(tasks_config)} tasks")

        # Create tasks
        tasks = []
        for task_cfg in tasks_config:
            task = create_task(
                source=task_cfg["source"],
                operation=task_cfg.get("operation", "scrape"),
                params=task_cfg.get("params", {}),
                priority=task_cfg.get("priority", TaskPriority.NORMAL),
            )
            tasks.append(task)

        # Dispatch all tasks concurrently
        results = await self.dispatcher.dispatch_batch(tasks)

        return results

    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        if not self.dispatcher:
            return []
        return self.dispatcher.get_available_sources()

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        if not self.dispatcher:
            return {}
        return self.dispatcher.get_stats()

    def validate(self) -> bool:
        """
        Validate the dispatcher pipeline.

        Returns:
            True if validation passes
        """
        logger.info("Validating dispatcher pipeline...")

        if not self.initialized:
            logger.error("Pipeline not initialized")
            return False

        if not self.dispatcher:
            logger.error("Dispatcher not created")
            return False

        # Check that at least one scraper is registered
        sources = self.get_available_sources()
        if not sources:
            logger.error("No scrapers registered")
            return False

        logger.info(f"✅ Validation complete ({len(sources)} sources available)")
        return True

    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up dispatcher pipeline...")

        if self.dispatcher:
            await self.dispatcher.cleanup()

        self.initialized = False
        logger.info("✅ Cleanup complete")


async def main():
    """Main execution function"""
    print("=" * 80)
    print("Phase 0.0013: Dispatcher Pipeline Implementation (rec_044)")
    print("=" * 80)

    # Initialize pipeline
    pipeline = DispatcherPipeline()

    # Setup
    setup_result = await pipeline.setup()
    print(f"\nSetup: {setup_result['message']}")

    if setup_result["success"]:
        print(f"Available sources: {', '.join(setup_result['sources'])}")

        # Example: Dispatch sample tasks (dry run - won't actually scrape)
        print("\nExample: Creating sample tasks (dry run)")

        # Get available sources
        sources = pipeline.get_available_sources()

        if sources:
            # Create one example task per available source
            tasks_config = []
            for source in sources:
                tasks_config.append(
                    {
                        "source": source,
                        "operation": "scrape",
                        "params": {},
                        "priority": TaskPriority.NORMAL,
                    }
                )

            print(f"Created {len(tasks_config)} example tasks")

            # Note: Actual dispatching commented out to avoid running scrapers
            # Uncomment below to actually run scrapers:
            # results = await pipeline.dispatch_batch(tasks_config)
            # for task in results:
            #     print(f"  - {task.source}: {task.status.value}")

    # Validate
    is_valid = pipeline.validate()
    print(f"\nValidation: {'✅ Passed' if is_valid else '❌ Failed'}")

    # Show statistics
    stats = pipeline.get_stats()
    print(f"\nStatistics:")
    print(f"  Tasks dispatched: {stats.get('tasks_dispatched', 0)}")
    print(f"  Tasks completed: {stats.get('tasks_completed', 0)}")
    print(f"  Success rate: {stats.get('success_rate', 0):.1%}")

    # Cleanup
    await pipeline.cleanup()

    print(f"\n✅ Phase 0.0013 implementation complete!")
    print("\nNext steps:")
    print("  1. Integrate with ADCE autonomous loop")
    print("  2. Add DIMS tracking for dispatcher operations")
    print("  3. Create comprehensive tests")


if __name__ == "__main__":
    asyncio.run(main())
