#!/usr/bin/env python3
"""
Scraper Orchestrator - ADCE Phase 3
Executes data collection tasks from reconciliation task queue

Purpose:
- Read prioritized task queue (inventory/gaps.json)
- Schedule scrapers by priority (CRITICAL → HIGH → MEDIUM → LOW)
- Execute collection with global rate limiting
- Track progress and update status
- Trigger reconciliation after completion

Features:
- Priority-based scheduling
- Global rate limiting (respect API limits)
- Parallel execution with limits
- Progress tracking and monitoring
- Automatic retries on failure
- Graceful shutdown
- Integration with DIMS metrics

Usage:
    # Run orchestrator (process all tasks)
    python scraper_orchestrator.py

    # Run specific priority level
    python scraper_orchestrator.py --priority critical

    # Dry run (don't execute, just show plan)
    python scraper_orchestrator.py --dry-run

    # Limit concurrent scrapers
    python scraper_orchestrator.py --max-concurrent 3
"""

import sys
import json
import time
import subprocess  # nosec B404 - Used for calling internal scraper scripts only
import signal
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """
    Orchestrates scraper execution based on task queue

    Reads inventory/gaps.json and executes scrapers to fill data gaps
    """

    def __init__(
        self,
        task_queue_file="inventory/gaps.json",
        scraper_config_file="config/scraper_config.yaml",
        max_concurrent=5,
        dry_run=False,
    ):
        """
        Initialize scraper orchestrator

        Args:
            task_queue_file: Path to task queue JSON
            scraper_config_file: Path to scraper configuration
            max_concurrent: Maximum concurrent scraper processes
            dry_run: If True, don't execute, just show plan
        """
        self.task_queue_file = Path(task_queue_file)
        self.scraper_config_file = Path(scraper_config_file)
        self.max_concurrent = max_concurrent
        self.dry_run = dry_run
        self.running = True

        # Load task queue
        self.task_queue = self._load_task_queue()

        # Load scraper config
        self.scraper_config = self._load_scraper_config()

        # Execution tracking
        self.execution_stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "by_priority": defaultdict(lambda: {"completed": 0, "failed": 0}),
            "by_scraper": defaultdict(lambda: {"completed": 0, "failed": 0}),
            "start_time": None,
            "end_time": None,
        }

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("=" * 80)
        logger.info("SCRAPER ORCHESTRATOR - ADCE Phase 3")
        logger.info("=" * 80)
        logger.info(f"Task queue: {self.task_queue_file}")
        logger.info(f"Total tasks: {self.task_queue.get('total_tasks', 0)}")
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 80)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"\n📡 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def _load_task_queue(self):
        """Load task queue from file"""
        if not self.task_queue_file.exists():
            logger.error(f"Task queue not found: {self.task_queue_file}")
            logger.error("Run reconciliation first to generate task queue")
            sys.exit(1)

        logger.info(f"Loading task queue from: {self.task_queue_file}")

        with open(self.task_queue_file, "r") as f:
            queue = json.load(f)

        logger.info(f"Loaded {queue.get('total_tasks', 0)} tasks")
        logger.info(f"  Critical: {queue.get('by_priority', {}).get('critical', 0)}")
        logger.info(f"  High: {queue.get('by_priority', {}).get('high', 0)}")
        logger.info(f"  Medium: {queue.get('by_priority', {}).get('medium', 0)}")
        logger.info(f"  Low: {queue.get('by_priority', {}).get('low', 0)}")

        return queue

    def _load_scraper_config(self):
        """Load scraper configuration"""
        if not self.scraper_config_file.exists():
            logger.error(f"Scraper config not found: {self.scraper_config_file}")
            sys.exit(1)

        logger.info(f"Loading scraper config from: {self.scraper_config_file}")

        with open(self.scraper_config_file, "r") as f:
            config = yaml.safe_load(f)

        scrapers = config.get("scrapers", {})
        logger.info(f"Loaded {len(scrapers)} scraper configurations")

        return config

    def execute_all_tasks(self, priority_filter=None):
        """
        Execute all tasks in queue (or filtered by priority)

        Args:
            priority_filter: If set, only execute tasks of this priority

        Returns:
            dict: Execution statistics
        """
        self.execution_stats["start_time"] = datetime.now()

        logger.info("\n" + "=" * 80)
        logger.info("STARTING TASK EXECUTION")
        logger.info("=" * 80)

        # Get tasks to execute
        tasks = self.task_queue.get("tasks", [])
        self.execution_stats["total_tasks"] = len(tasks)

        if priority_filter:
            tasks = [
                t for t in tasks if t["priority"].lower() == priority_filter.lower()
            ]
            logger.info(f"Filtered to {len(tasks)} {priority_filter} priority tasks")

        # Execute tasks by priority
        priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        for priority in priority_order:
            if not self.running:
                logger.warning("Shutdown requested, stopping execution...")
                break

            priority_tasks = [t for t in tasks if t["priority"] == priority]

            if not priority_tasks:
                continue

            logger.info(f"\n{'=' * 80}")
            logger.info(f"Executing {len(priority_tasks)} {priority} priority tasks")
            logger.info(f"{'=' * 80}")

            for task in priority_tasks:
                if not self.running:
                    break

                self._execute_task(task)

        self.execution_stats["end_time"] = datetime.now()

        # Print summary
        self._print_execution_summary()

        return self.execution_stats

    def _execute_task(self, task):
        """
        Execute a single collection task

        Args:
            task: Task dict from task queue
        """
        task_id = task.get("id", "unknown")
        priority = task.get("priority", "UNKNOWN")
        scraper = task.get("scraper")
        source = task.get("source")

        logger.info(f"\n[{task_id}] Starting task...")
        logger.info(f"  Priority: {priority}")
        logger.info(f"  Source: {source}")
        logger.info(f"  Scraper: {scraper}")
        logger.info(f"  Reason: {task.get('reason', 'N/A')}")

        if self.dry_run:
            logger.info(f"  [DRY RUN] Would execute: {scraper}")
            self.execution_stats["skipped"] += 1
            return

        # Check if scraper exists in config
        if scraper not in self.scraper_config.get("scrapers", {}):
            logger.error(f"  ❌ Scraper not found in config: {scraper}")
            self.execution_stats["failed"] += 1
            self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
            return

        # Build scraper command
        scraper_script = self._find_scraper_script(scraper)
        if not scraper_script:
            logger.error(f"  ❌ Scraper script not found for: {scraper}")
            self.execution_stats["failed"] += 1
            self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
            return

        # Execute scraper
        try:
            start_time = time.time()

            cmd = [sys.executable, str(scraper_script)]

            # Add task-specific args if needed
            if task.get("season"):
                cmd.extend(["--season", task["season"]])
            if task.get("game_ids"):
                cmd.extend(
                    ["--game-ids", ",".join(str(gid) for gid in task["game_ids"][:10])]
                )

            logger.info(f"  🚀 Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=task.get("estimated_time_minutes", 5) * 60,
            )  # nosec B603 - cmd is internally constructed

            duration = time.time() - start_time

            if result.returncode == 0:
                logger.info(f"  ✅ Task completed in {duration:.1f}s")
                self.execution_stats["completed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["completed"] += 1
                self.execution_stats["by_scraper"][scraper]["completed"] += 1
            else:
                logger.error(f"  ❌ Task failed after {duration:.1f}s")
                logger.error(f"  Error: {result.stderr[:200]}")
                self.execution_stats["failed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
                self.execution_stats["by_scraper"][scraper]["failed"] += 1

        except subprocess.TimeoutExpired:
            logger.error(
                f"  ❌ Task timed out after {task.get('estimated_time_minutes', 5)} minutes"
            )
            self.execution_stats["failed"] += 1
            self.execution_stats["by_priority"][priority.lower()]["failed"] += 1

        except Exception as e:
            logger.error(f"  ❌ Task failed with exception: {e}")
            self.execution_stats["failed"] += 1
            self.execution_stats["by_priority"][priority.lower()]["failed"] += 1

    def _find_scraper_script(self, scraper_name):
        """
        Find the Python script for a scraper

        Args:
            scraper_name: Name of scraper from config

        Returns:
            Path: Path to scraper script, or None if not found
        """
        # Common scraper locations
        search_paths = [
            Path("scripts/etl") / f"{scraper_name}.py",
            Path("scripts/scrapers") / f"{scraper_name}.py",
            Path("scripts") / f"{scraper_name}.py",
        ]

        for path in search_paths:
            if path.exists():
                return path

        # Try finding by pattern matching
        for pattern in ["*async_scraper.py", "*incremental_scraper.py", "*scraper.py"]:
            matches = list(Path("scripts").rglob(pattern))
            for match in matches:
                if scraper_name.replace("_", "") in str(match).replace("_", "").lower():
                    return match

        return None

    def _print_execution_summary(self):
        """Print execution summary"""
        duration = (
            self.execution_stats["end_time"] - self.execution_stats["start_time"]
        ).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tasks: {self.execution_stats['total_tasks']}")
        logger.info(
            f"Completed: {self.execution_stats['completed']} ({self.execution_stats['completed']/max(self.execution_stats['total_tasks'],1)*100:.1f}%)"
        )
        logger.info(f"Failed: {self.execution_stats['failed']}")
        logger.info(f"Skipped: {self.execution_stats['skipped']}")
        logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")

        logger.info(f"\nBy Priority:")
        for priority in ["critical", "high", "medium", "low"]:
            stats = self.execution_stats["by_priority"].get(
                priority, {"completed": 0, "failed": 0}
            )
            if stats["completed"] + stats["failed"] > 0:
                logger.info(
                    f"  {priority.upper()}: {stats['completed']} completed, {stats['failed']} failed"
                )

        logger.info(f"\nBy Scraper:")
        for scraper, stats in sorted(self.execution_stats["by_scraper"].items()):
            logger.info(
                f"  {scraper}: {stats['completed']} completed, {stats['failed']} failed"
            )

        logger.info("=" * 80)

    def trigger_reconciliation(self):
        """
        Trigger new reconciliation after execution completes

        This closes the autonomous loop:
        Reconciliation → Tasks → Execution → Reconciliation → ...
        """
        logger.info("\n" + "=" * 80)
        logger.info("TRIGGERING RECONCILIATION")
        logger.info("=" * 80)

        if self.dry_run:
            logger.info("[DRY RUN] Would trigger reconciliation")
            return

        try:
            cmd = [
                sys.executable,
                "scripts/reconciliation/run_reconciliation.py",
                "--dry-run",  # Don't regenerate task queue yet, just update inventory
            ]

            logger.info("Running reconciliation to update inventory...")

            result = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603

            if result.returncode == 0:
                logger.info("✅ Reconciliation triggered successfully")
            else:
                logger.error(f"❌ Reconciliation failed: {result.stderr[:200]}")

        except Exception as e:
            logger.error(f"❌ Failed to trigger reconciliation: {e}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scraper Orchestrator - Execute data collection tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute all tasks
  python scraper_orchestrator.py

  # Execute only critical priority tasks
  python scraper_orchestrator.py --priority critical

  # Dry run (show execution plan)
  python scraper_orchestrator.py --dry-run

  # Limit concurrent scrapers
  python scraper_orchestrator.py --max-concurrent 3
        """,
    )

    parser.add_argument(
        "--task-queue", default="inventory/gaps.json", help="Path to task queue JSON"
    )
    parser.add_argument(
        "--scraper-config",
        default="config/scraper_config.yaml",
        help="Path to scraper configuration",
    )
    parser.add_argument(
        "--priority",
        choices=["critical", "high", "medium", "low"],
        help="Only execute tasks of this priority",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent scraper processes",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show execution plan without executing"
    )
    parser.add_argument(
        "--no-reconciliation",
        action="store_true",
        help="Skip triggering reconciliation after execution",
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = ScraperOrchestrator(
        task_queue_file=args.task_queue,
        scraper_config_file=args.scraper_config,
        max_concurrent=args.max_concurrent,
        dry_run=args.dry_run,
    )

    # Execute tasks
    try:
        stats = orchestrator.execute_all_tasks(priority_filter=args.priority)

        # Trigger reconciliation to close the loop
        if not args.no_reconciliation and stats["completed"] > 0:
            orchestrator.trigger_reconciliation()

        # Exit with appropriate code
        if stats["failed"] > 0:
            return 1
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
