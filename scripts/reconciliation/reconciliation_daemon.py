#!/usr/bin/env python3
"""
Reconciliation Daemon - ADCE Phase 2B
Automated continuous reconciliation loop

Features:
- Run reconciliation on schedule (hourly, daily, etc.)
- Trigger on events (scraper_complete, manual trigger)
- Graceful shutdown on SIGINT/SIGTERM
- Health checks and monitoring
- DIMS integration for metrics tracking

Usage:
    # Run with default config (every hour)
    python reconciliation_daemon.py

    # Run with custom interval
    python reconciliation_daemon.py --interval-hours 2

    # Run once and exit (for testing)
    python reconciliation_daemon.py --run-once

    # Dry run mode (no task queue generation)
    python reconciliation_daemon.py --dry-run
"""

import sys
import time
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path
import subprocess  # nosec B404 - Used for calling internal scripts only
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReconciliationDaemon:
    """
    Automated reconciliation daemon

    Runs reconciliation on schedule and responds to events
    """

    def __init__(self, interval_hours=1, dry_run=False, use_aws_inventory=False):
        """
        Initialize reconciliation daemon

        Args:
            interval_hours: How often to run reconciliation (default: 1 hour)
            dry_run: If True, don't generate task queue (just report)
            use_aws_inventory: If True, use AWS S3 Inventory instead of sampling
        """
        self.interval_seconds = interval_hours * 3600
        self.dry_run = dry_run
        self.use_aws_inventory = use_aws_inventory
        self.running = False
        self.last_run_time = None
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("=" * 80)
        logger.info("RECONCILIATION DAEMON - ADCE Phase 2B")
        logger.info("=" * 80)
        logger.info(f"Interval: {interval_hours} hour(s)")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"AWS Inventory: {use_aws_inventory}")
        logger.info(f"Next run: Immediate")
        logger.info("=" * 80)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"\n📡 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def run_reconciliation_cycle(self):
        """
        Run a single reconciliation cycle

        Returns:
            dict: Results from reconciliation
        """
        cycle_start = datetime.now()
        logger.info("\n" + "=" * 80)
        logger.info(f"🔄 RECONCILIATION CYCLE #{self.total_runs + 1}")
        logger.info(f"Started: {cycle_start.isoformat()}")
        logger.info("=" * 80)

        try:
            # Build command
            cmd = [sys.executable, "scripts/reconciliation/run_reconciliation.py"]

            # Add flags
            if self.last_run_time:
                # Use cached inventory if recent
                cache_age_hours = (
                    datetime.now() - self.last_run_time
                ).total_seconds() / 3600
                if cache_age_hours < 1:  # Cache valid for 1 hour
                    cmd.append("--use-cache")
                    logger.info("Using cached S3 inventory (< 1 hour old)")

            if self.dry_run:
                cmd.append("--dry-run")

            # Run reconciliation
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd()
            )  # nosec B603 - cmd is internally constructed

            duration = (datetime.now() - cycle_start).total_seconds()

            if result.returncode == 0:
                self.successful_runs += 1
                logger.info(f"\n✅ CYCLE COMPLETE - Duration: {duration:.1f}s")

                # Parse and log summary
                self._log_cycle_summary(result.stdout)

                return {
                    "success": True,
                    "duration": duration,
                    "timestamp": cycle_start.isoformat(),
                }
            else:
                self.failed_runs += 1
                logger.error(f"\n❌ CYCLE FAILED - Duration: {duration:.1f}s")
                logger.error(f"Error: {result.stderr}")

                return {
                    "success": False,
                    "duration": duration,
                    "timestamp": cycle_start.isoformat(),
                    "error": result.stderr,
                }

        except Exception as e:
            self.failed_runs += 1
            logger.error(f"\n❌ CYCLE EXCEPTION: {e}", exc_info=True)
            return {
                "success": False,
                "timestamp": cycle_start.isoformat(),
                "error": str(e),
            }

        finally:
            self.total_runs += 1
            self.last_run_time = datetime.now()

    def _log_cycle_summary(self, output):
        """Parse and log key metrics from reconciliation output"""
        try:
            # Extract key metrics from output
            lines = output.split("\n")

            for line in lines:
                # Log important summary lines
                if any(
                    keyword in line
                    for keyword in [
                        "Objects scanned",
                        "Overall completeness",
                        "Total gaps",
                        "Critical:",
                        "Pipeline Duration",
                    ]
                ):
                    logger.info(f"  {line.strip()}")

        except Exception as e:
            logger.debug(f"Could not parse summary: {e}")

    def _update_dims_metrics(self, cycle_result):
        """
        Update DIMS with reconciliation metrics

        Args:
            cycle_result: Results from reconciliation cycle
        """
        try:
            # Load gaps file if exists
            gaps_file = Path("inventory/gaps.json")
            if gaps_file.exists():
                with open(gaps_file, "r") as f:
                    gaps = json.load(f)

                # Update DIMS metrics (if DIMS CLI is available)
                dims_cli = Path("scripts/monitoring/dims_cli.py")
                if dims_cli.exists():
                    logger.info("Updating DIMS metrics...")

                    metrics = {
                        "reconciliation_last_run": datetime.now().isoformat(),
                        "reconciliation_total_gaps": gaps.get("total_tasks", 0),
                        "reconciliation_critical_gaps": gaps.get("by_priority", {}).get(
                            "critical", 0
                        ),
                        "reconciliation_task_queue_size": gaps.get("total_tasks", 0),
                    }

                    for key, value in metrics.items():
                        subprocess.run(
                            [sys.executable, str(dims_cli), "set", key, str(value)],
                            capture_output=True,
                        )  # nosec B603

                    logger.info("✅ DIMS metrics updated")

        except Exception as e:
            logger.warning(f"Could not update DIMS metrics: {e}")

    def run(self, run_once=False):
        """
        Run daemon loop

        Args:
            run_once: If True, run one cycle and exit (for testing)
        """
        self.running = True

        while self.running:
            # Run reconciliation cycle
            cycle_result = self.run_reconciliation_cycle()

            # Update DIMS
            self._update_dims_metrics(cycle_result)

            # Log daemon status
            logger.info("\n" + "=" * 80)
            logger.info("DAEMON STATUS")
            logger.info("=" * 80)
            logger.info(f"Total runs: {self.total_runs}")
            logger.info(
                f"Successful: {self.successful_runs} ({self.successful_runs/max(self.total_runs,1)*100:.1f}%)"
            )
            logger.info(f"Failed: {self.failed_runs}")
            logger.info(
                f"Last run: {self.last_run_time.isoformat() if self.last_run_time else 'N/A'}"
            )

            if run_once:
                logger.info("Run-once mode, exiting...")
                break

            # Calculate next run time
            next_run = datetime.now() + timedelta(seconds=self.interval_seconds)
            logger.info(
                f"Next run: {next_run.isoformat()} ({self.interval_seconds/3600:.1f}h from now)"
            )
            logger.info("=" * 80)

            # Sleep until next cycle
            try:
                logger.info(
                    f"💤 Sleeping for {self.interval_seconds/3600:.1f} hours..."
                )
                time.sleep(self.interval_seconds)
            except KeyboardInterrupt:
                logger.info("\n⚠️  Sleep interrupted, shutting down...")
                break

        # Shutdown
        logger.info("\n" + "=" * 80)
        logger.info("DAEMON SHUTDOWN")
        logger.info("=" * 80)
        logger.info(f"Total cycles completed: {self.total_runs}")
        logger.info(
            f"Success rate: {self.successful_runs/max(self.total_runs,1)*100:.1f}%"
        )
        logger.info("Goodbye! 👋")
        logger.info("=" * 80)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated reconciliation daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run daemon with default 1-hour interval
  python reconciliation_daemon.py
  
  # Run with 2-hour interval
  python reconciliation_daemon.py --interval-hours 2
  
  # Run once and exit (for testing)
  python reconciliation_daemon.py --run-once
  
  # Dry run mode (don't generate task queue)
  python reconciliation_daemon.py --dry-run
  
  # Use AWS S3 Inventory instead of sampling
  python reconciliation_daemon.py --use-aws-inventory
        """,
    )

    parser.add_argument(
        "--interval-hours",
        type=float,
        default=1.0,
        help="Hours between reconciliation runs (default: 1.0)",
    )
    parser.add_argument(
        "--run-once", action="store_true", help="Run one cycle and exit (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run reconciliation but don't generate task queue",
    )
    parser.add_argument(
        "--use-aws-inventory",
        action="store_true",
        help="Use AWS S3 Inventory instead of sampling",
    )

    args = parser.parse_args()

    # Initialize daemon
    daemon = ReconciliationDaemon(
        interval_hours=args.interval_hours,
        dry_run=args.dry_run,
        use_aws_inventory=args.use_aws_inventory,
    )

    # Run daemon
    try:
        daemon.run(run_once=args.run_once)
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
