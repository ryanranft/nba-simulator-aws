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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import rate limit coordinator
from scripts.orchestration.rate_limit_coordinator import RateLimitCoordinator

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
        autonomous_config_file="config/autonomous_config.yaml",
        max_concurrent=5,
        dry_run=False,
    ):
        """
        Initialize scraper orchestrator

        Args:
            task_queue_file: Path to task queue JSON
            scraper_config_file: Path to scraper configuration
            autonomous_config_file: Path to autonomous configuration (for priority weighting)
            max_concurrent: Maximum concurrent scraper processes
            dry_run: If True, don't execute, just show plan
        """
        self.task_queue_file = Path(task_queue_file)
        self.scraper_config_file = Path(scraper_config_file)
        self.autonomous_config_file = Path(autonomous_config_file)
        self.max_concurrent = max_concurrent
        self.dry_run = dry_run
        self.running = True

        # Load task queue
        self.task_queue = self._load_task_queue()

        # Load scraper config
        self.scraper_config = self._load_scraper_config()

        # Load autonomous config (for priority weighting)
        self.autonomous_config = self._load_autonomous_config()

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

        # Thread-safe stats updates
        self.stats_lock = threading.Lock()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Check if weighted priority scoring is enabled
        self.use_weighted_scoring = self._check_weighted_scoring_enabled()

        # Initialize rate limit coordinator
        rate_limit_config = self.autonomous_config.get(
            "rate_limiting", {"enabled": False}
        )
        self.rate_limiter = RateLimitCoordinator(rate_limit_config)

        logger.info("=" * 80)
        logger.info("SCRAPER ORCHESTRATOR - ADCE Phase 3")
        logger.info("=" * 80)
        logger.info(f"Task queue: {self.task_queue_file}")
        logger.info(f"Total tasks: {self.task_queue.get('total_tasks', 0)}")
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"Weighted scoring: {self.use_weighted_scoring}")
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

    def _load_autonomous_config(self):
        """Load autonomous configuration (for priority weighting)"""
        if not self.autonomous_config_file.exists():
            logger.warning(
                f"Autonomous config not found: {self.autonomous_config_file}"
            )
            logger.warning("Using default priority weighting settings")
            return {}

        logger.info(f"Loading autonomous config from: {self.autonomous_config_file}")

        with open(self.autonomous_config_file, "r") as f:
            config = yaml.safe_load(f)

        return config

    def _check_weighted_scoring_enabled(self):
        """Check if weighted priority scoring is enabled"""
        task_processing = self.autonomous_config.get("task_processing", {})
        priority_weighting = task_processing.get("priority_weighting", {})
        return priority_weighting.get("enabled", False)

    def _calculate_task_score(self, task):
        """Calculate weighted priority score for a task.

        Combines multiple factors to create a numeric score:
        - Base priority (CRITICAL=1000, HIGH=100, MEDIUM=10, LOW=1)
        - Task age (+0.5 points per hour since detection)
        - Source importance (multiplier: ESPN=1.5x, NBA_API=1.3x, etc.)
        - Gap size (smaller gaps = higher priority, -0.1 per file)
        - Historical success rate (+20 points for 100% success)

        Args:
            task: Task dictionary from task queue

        Returns:
            float: Weighted priority score (higher = execute sooner)
        """
        if not self.use_weighted_scoring:
            # Fall back to simple priority ordering
            priority_values = {"CRITICAL": 1000, "HIGH": 100, "MEDIUM": 10, "LOW": 1}
            return priority_values.get(task.get("priority", "LOW"), 1)

        # Get weighting configuration
        task_processing = self.autonomous_config.get("task_processing", {})
        weighting = task_processing.get("priority_weighting", {})

        # Base score from priority
        base_scores = weighting.get(
            "base_scores", {"CRITICAL": 1000, "HIGH": 100, "MEDIUM": 10, "LOW": 1}
        )
        score = base_scores.get(task.get("priority", "LOW"), 1)

        # Age factor: older tasks get higher priority
        age_weight = weighting.get("age_weight", 0.5)
        if "detected_at" in task:
            try:
                detected = datetime.fromisoformat(task["detected_at"])
                age_hours = (datetime.now() - detected).total_seconds() / 3600
                score += age_hours * age_weight
            except (ValueError, TypeError):
                pass  # Skip if timestamp invalid

        # Source importance multiplier
        source_multipliers = weighting.get(
            "source_multipliers",
            {
                "espn": 1.5,
                "nba_api": 1.3,
                "basketball_reference": 1.2,
                "hoopr": 1.1,
                "default": 1.0,
            },
        )
        source = task.get("source", "").lower()
        multiplier = source_multipliers.get(
            source, source_multipliers.get("default", 1.0)
        )
        score *= multiplier

        # Gap size factor: smaller gaps = higher priority
        gap_size_weight = weighting.get("gap_size_weight", -0.1)
        max_gap_penalty = weighting.get("max_gap_size_penalty", 10)
        if "gap_size" in task:
            gap_size = task["gap_size"]
            penalty = gap_size * gap_size_weight
            penalty = max(penalty, -max_gap_penalty)  # Cap penalty
            score += penalty

        # Historical success rate boost
        success_weight = weighting.get("success_rate_weight", 20)
        if "success_rate" in task:
            success_rate = task["success_rate"]
            score += success_rate * success_weight

        return score

    def execute_all_tasks(self, priority_filter=None):
        """
        Execute all tasks in queue (or filtered by priority)

        Uses weighted priority scoring if enabled, otherwise uses simple
        priority grouping (CRITICAL → HIGH → MEDIUM → LOW).

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

        if not tasks:
            logger.info("No tasks to execute")
            self.execution_stats["end_time"] = datetime.now()
            return self.execution_stats

        # Execute tasks using weighted scoring or simple priority grouping
        if self.use_weighted_scoring:
            logger.info("Using weighted priority scoring")
            self._execute_tasks_weighted(tasks)
        else:
            logger.info("Using simple priority grouping")
            self._execute_tasks_by_priority(tasks)

        self.execution_stats["end_time"] = datetime.now()

        # Print summary
        self._print_execution_summary()

        return self.execution_stats

    def _execute_tasks_weighted(self, tasks):
        """Execute tasks sorted by weighted priority score.

        Uses ThreadPoolExecutor for parallel execution with max_concurrent limit.

        Args:
            tasks: List of task dictionaries
        """
        # Calculate scores for all tasks
        logger.info("Calculating weighted priority scores...")
        for task in tasks:
            task["_score"] = self._calculate_task_score(task)

        # Sort by score (descending)
        tasks_sorted = sorted(tasks, key=lambda t: t["_score"], reverse=True)

        # Log scoring summary
        if tasks_sorted:
            logger.info("\nTop 5 tasks by score:")
            for i, task in enumerate(tasks_sorted[:5], 1):
                logger.info(
                    f"  {i}. [{task.get('priority')}] {task.get('scraper')} "
                    f"(score: {task['_score']:.2f})"
                )

        logger.info(f"\n{'=' * 80}")
        logger.info(
            f"Executing {len(tasks_sorted)} tasks in weighted score order "
            f"(max {self.max_concurrent} concurrent)"
        )
        logger.info(f"{'=' * 80}")

        # Execute in parallel with score order priority
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit tasks in score order
            future_to_task = {
                executor.submit(self._execute_task, task): task for task in tasks_sorted
            }

            # Process completed tasks
            for future in as_completed(future_to_task):
                if not self.running:
                    logger.warning("Shutdown requested, cancelling remaining tasks...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                task = future_to_task[future]
                try:
                    future.result()  # Get result to propagate exceptions
                except Exception as e:
                    logger.error(
                        f"Task {task.get('id', 'unknown')} raised exception: {e}"
                    )

    def _execute_tasks_by_priority(self, tasks):
        """Execute tasks grouped by priority (legacy method).

        Uses ThreadPoolExecutor for parallel execution with max_concurrent limit.

        Args:
            tasks: List of task dictionaries
        """
        priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        for priority in priority_order:
            if not self.running:
                logger.warning("Shutdown requested, stopping execution...")
                break

            priority_tasks = [t for t in tasks if t["priority"] == priority]

            if not priority_tasks:
                continue

            logger.info(f"\n{'=' * 80}")
            logger.info(
                f"Executing {len(priority_tasks)} {priority} priority tasks "
                f"(max {self.max_concurrent} concurrent)"
            )
            logger.info(f"{'=' * 80}")

            # Execute priority group in parallel
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                future_to_task = {
                    executor.submit(self._execute_task, task): task
                    for task in priority_tasks
                }

                for future in as_completed(future_to_task):
                    if not self.running:
                        logger.warning(
                            "Shutdown requested, cancelling remaining tasks..."
                        )
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    task = future_to_task[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(
                            f"Task {task.get('id', 'unknown')} raised exception: {e}"
                        )

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
            with self.stats_lock:
                self.execution_stats["skipped"] += 1
            return

        # Check if scraper exists in config
        if scraper not in self.scraper_config.get("scrapers", {}):
            logger.error(f"  ❌ Scraper not found in config: {scraper}")
            with self.stats_lock:
                self.execution_stats["failed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
            return

        # Build scraper command
        scraper_script = self._find_scraper_script(scraper)
        if not scraper_script:
            logger.error(f"  ❌ Scraper script not found for: {scraper}")
            with self.stats_lock:
                self.execution_stats["failed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
            return

        # Execute scraper
        try:
            # Acquire rate limit permission
            if not self.rate_limiter.acquire(source):
                logger.warning(f"  ⚠️ Rate limit exceeded for {source}, skipping task")
                with self.stats_lock:
                    self.execution_stats["skipped"] += 1
                return

            start_time = time.time()

            # Build command with parameter validation
            cmd = self._build_scraper_command(scraper, scraper_script, task)

            logger.info(f"  🚀 Executing: {' '.join(cmd)}")

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=task.get("estimated_time_minutes", 5) * 60,
                )  # nosec B603 - cmd is internally constructed

                duration = time.time() - start_time
            finally:
                # Always release rate limit (even if scraper failed)
                self.rate_limiter.release(source)

            if result.returncode == 0:
                logger.info(f"  ✅ Task completed in {duration:.1f}s")
                with self.stats_lock:
                    self.execution_stats["completed"] += 1
                    self.execution_stats["by_priority"][priority.lower()][
                        "completed"
                    ] += 1
                    self.execution_stats["by_scraper"][scraper]["completed"] += 1
            else:
                logger.error(f"  ❌ Task failed after {duration:.1f}s")
                logger.error(f"  Error: {result.stderr[:200]}")
                with self.stats_lock:
                    self.execution_stats["failed"] += 1
                    self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
                    self.execution_stats["by_scraper"][scraper]["failed"] += 1

        except subprocess.TimeoutExpired:
            logger.error(
                f"  ❌ Task timed out after {task.get('estimated_time_minutes', 5)} minutes"
            )
            with self.stats_lock:
                self.execution_stats["failed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["failed"] += 1

        except Exception as e:
            logger.error(f"  ❌ Task failed with exception: {e}")
            with self.stats_lock:
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

    def _build_scraper_command(self, scraper, scraper_script, task):
        """
        Build scraper command with validated parameters

        Args:
            scraper: Scraper name
            scraper_script: Path to scraper script
            task: Task dict from queue

        Returns:
            list: Command to execute
        """
        cmd = [sys.executable, str(scraper_script)]

        # Get accepted parameters for this scraper
        scraper_config = self.scraper_config.get("scrapers", {}).get(scraper, {})
        accepted_params = scraper_config.get("accepted_parameters", [])

        # If no accepted_parameters defined, use default common parameters
        if not accepted_params:
            accepted_params = [
                "season",
                "game_ids",
                "start_date",
                "end_date",
                "dry_run",
            ]

        # Parameter mapping: task_key -> (cli_arg, formatter)
        param_mapping = {
            "season": ("--season", lambda v: str(v)),
            "game_ids": (
                "--game-ids",
                lambda v: ",".join(str(gid) for gid in v[:10]),
            ),
            "days": ("--days", lambda v: str(v)),
            "start_date": ("--start-date", lambda v: str(v)),
            "end_date": ("--end-date", lambda v: str(v)),
            "player_id": ("--player-id", lambda v: str(v)),
            "team_id": ("--team-id", lambda v: str(v)),
            "dry_run": ("--dry-run", None),  # Flag, no value
        }

        # Add parameters that scraper accepts and task provides
        for param_key, (cli_arg, formatter) in param_mapping.items():
            if param_key in accepted_params and task.get(param_key):
                if formatter:
                    cmd.extend([cli_arg, formatter(task[param_key])])
                else:
                    cmd.append(cli_arg)

        return cmd

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

        # Rate limiting stats
        rate_stats = self.rate_limiter.get_stats()
        if rate_stats.get("enabled"):
            logger.info(f"\nRate Limiting:")
            global_stats = rate_stats["global"]
            logger.info(
                f"  Global: {global_stats['requests_last_minute']}/{global_stats['limit_rpm']} req/min, "
                f"{global_stats['requests_last_hour']}/{global_stats['limit_rph']} req/hour"
            )

            if rate_stats.get("sources"):
                logger.info(f"  By Source:")
                for source, stats in sorted(rate_stats["sources"].items()):
                    logger.info(
                        f"    {source}: {stats['requests_last_minute']}/{stats['limit_rpm']} req/min, "
                        f"tokens={stats['tokens_available']:.1f}"
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
