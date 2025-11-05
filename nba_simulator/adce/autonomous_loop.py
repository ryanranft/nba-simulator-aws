#!/usr/bin/env python3
"""
Autonomous Loop Controller - ADCE Phase 4
Master controller for 24/7 self-healing data collection

Migrated from scripts/autonomous/autonomous_loop.py during Phase 6 refactoring.

Features:
- Manages reconciliation daemon lifecycle
- Monitors task queue for new tasks
- Auto-triggers orchestrator when tasks available
- Handles completion and restart cycle
- Graceful shutdown on signals
- Health monitoring and status reporting
- Comprehensive logging and error handling

Usage:
    from nba_simulator.adce import AutonomousLoop
    
    loop = AutonomousLoop(config_file="config/autonomous_config.yaml")
    loop.start()
"""

import sys
import os
import time
import signal
import subprocess  # nosec B404 - Used for calling internal scripts only
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import yaml
import threading
from collections import defaultdict

from ..utils import setup_logging

# Setup logging
logger = setup_logging(__name__)


class AutonomousLoop:
    """
    Master controller for autonomous 24/7 data collection

    Coordinates reconciliation (gap detection) and orchestration (gap filling)
    in a continuous self-healing loop with zero manual intervention.
    """

    def __init__(
        self,
        config_file="config/autonomous_config.yaml",
        dry_run=False,
        test_mode=False,
    ):
        """
        Initialize autonomous loop

        Args:
            config_file: Path to configuration file
            dry_run: If True, don't execute, just simulate
            test_mode: If True, skip reconciliation daemon
        """
        self.config_file = Path(config_file)
        self.dry_run = dry_run
        self.running = True

        # Component processes
        self.reconciliation_daemon = None
        self.orchestrator_process = None
        self.health_monitor = None
        self.health_monitor_thread = None

        # Load configuration
        self.config = self._load_config()

        # Test mode configuration
        self.test_mode = self.config.get("test_mode", {})

        # Override config if CLI flag provided
        if test_mode:
            self.test_mode["enabled"] = True

        # State tracking
        self.state = {
            "start_time": datetime.now(),
            "cycles_completed": 0,
            "tasks_executed": 0,
            "last_reconciliation": None,
            "last_orchestration": None,
            "errors": [],
            "status": "initializing",
        }

        # Statistics
        self.stats = defaultdict(int)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Create log directory
        Path("logs").mkdir(exist_ok=True)

        # Calculate reconciliation interval (support both minutes and hours for backward compat)
        if "reconciliation_interval_minutes" in self.config:
            self.reconciliation_interval_seconds = (
                self.config["reconciliation_interval_minutes"] * 60
            )
            interval_display = f"{self.config['reconciliation_interval_minutes']}min"
        else:
            # Legacy: hours-based interval
            self.reconciliation_interval_seconds = (
                self.config.get("reconciliation_interval_hours", 1) * 3600
            )
            interval_display = f"{self.config.get('reconciliation_interval_hours', 1)}h"

        logger.info("=" * 80)
        logger.info("AUTONOMOUS LOOP CONTROLLER - ADCE Phase 4")
        logger.info("=" * 80)
        logger.info(f"Config: {self.config_file}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Reconciliation interval: {interval_display}")
        logger.info(
            f"Min tasks to trigger orchestrator: {self.config['min_tasks_to_trigger']}"
        )
        logger.info("=" * 80)

    def _load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}, using defaults")
            return self._default_config()

        try:
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._default_config()

    def _default_config(self):
        """Return default configuration"""
        return {
            "enabled": True,
            "reconciliation_interval_hours": 1,
            "min_tasks_to_trigger": 1,
            "max_orchestrator_runtime_minutes": 120,
            "task_queue_file": "inventory/gaps.json",
            "health_check_port": 8080,
            "max_retries": 3,
            "alert_on_failure": False,
        }

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"\n📡 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        self.state["status"] = "shutting_down"

    def start(self):
        """
        Start the autonomous loop

        Main control loop that coordinates all components
        """
        logger.info("\n🚀 Starting Autonomous Loop...")
        self.state["status"] = "running"

        try:
            # Import health monitor from this package
            from .health_monitor import HealthMonitor

            health_port = self.config.get("health_check_port", 8080)
            self.health_monitor = HealthMonitor(port=health_port, loop_state=self.state)
            self.health_monitor_thread = threading.Thread(
                target=self.health_monitor.start, daemon=True
            )
            self.health_monitor_thread.start()
            logger.info(f"✅ Health monitor HTTP server started on port {health_port}")

            # Give it a moment to start
            time.sleep(1)

            # Check if test mode is enabled
            if self.test_mode.get("enabled", False):
                logger.warning("=" * 80)
                logger.warning("⚠️  TEST MODE ENABLED - Reconciliation daemon disabled")
                logger.warning("⚠️  Will only process existing task queue")
                logger.warning("=" * 80)
            else:
                # Start reconciliation daemon in normal mode
                if not self._start_reconciliation_daemon():
                    logger.error("❌ Failed to start reconciliation daemon")
                    return False

                logger.info("✅ Reconciliation daemon started")

            # Main control loop
            logger.info("\n🔄 Entering main control loop...")
            self._main_loop()

        except Exception as e:
            logger.error(f"❌ Fatal error in autonomous loop: {e}", exc_info=True)
            self.state["errors"].append(str(e))
            return False

        finally:
            self._shutdown()

        return True

    def _start_reconciliation_daemon(self):
        """
        Start the reconciliation daemon in background

        Returns:
            bool: True if started successfully
        """
        if self.dry_run:
            logger.info("[DRY RUN] Would start reconciliation daemon")
            return True

        try:
            # Use new package structure
            from .reconciliation import ReconciliationDaemon
            
            # Calculate interval in hours
            if "reconciliation_interval_minutes" in self.config:
                interval_hours = self.config["reconciliation_interval_minutes"] / 60.0
            else:
                interval_hours = self.config.get("reconciliation_interval_hours", 1)
            
            # Create and start daemon in separate thread
            self.reconciliation_daemon = ReconciliationDaemon(
                interval_hours=interval_hours,
                dry_run=self.dry_run
            )
            
            # Start daemon in background thread
            daemon_thread = threading.Thread(
                target=self.reconciliation_daemon.run, 
                daemon=True
            )
            daemon_thread.start()
            
            logger.info(f"Reconciliation daemon started (interval: {interval_hours}h)")
            return True

        except Exception as e:
            logger.error(f"Failed to start reconciliation daemon: {e}")
            return False

    def _main_loop(self):
        """
        Main control loop

        Monitors task queue and triggers orchestrator when needed
        """
        check_interval = 10  # Check every 10 seconds
        last_check = datetime.now() - timedelta(seconds=check_interval)

        while self.running:
            try:
                # Check task queue periodically
                if (datetime.now() - last_check).total_seconds() >= check_interval:
                    tasks_available = self._check_task_queue()

                    if tasks_available >= self.config["min_tasks_to_trigger"]:
                        logger.info(f"\n📋 Found {tasks_available} tasks in queue")

                        # Trigger orchestrator if not already running
                        if not self._is_orchestrator_running():
                            self._trigger_orchestrator()
                        else:
                            logger.info("⏳ Orchestrator already running, waiting...")

                    last_check = datetime.now()

                # Sleep to avoid busy waiting
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("\n🛑 Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                self.state["errors"].append(str(e))
                time.sleep(5)  # Back off on error

        logger.info("\n🔄 Main loop exited")

    def _check_task_queue(self):
        """
        Check task queue for available tasks

        Returns:
            int: Number of tasks available, or 0 if error/no tasks
        """
        task_queue_file = Path(self.config["task_queue_file"])

        if not task_queue_file.exists():
            return 0

        try:
            with open(task_queue_file, "r") as f:
                queue = json.load(f)

            total_tasks = queue.get("total_tasks", 0)

            if total_tasks > 0:
                logger.debug(f"Task queue: {total_tasks} tasks available")

            return total_tasks

        except Exception as e:
            logger.error(f"Error reading task queue: {e}")
            return 0

    def _is_orchestrator_running(self):
        """
        Check if orchestrator is currently running

        Returns:
            bool: True if orchestrator process is running
        """
        if self.orchestrator_process is None:
            return False

        # Check if process has exited
        return self.orchestrator_process.poll() is None

    def _trigger_orchestrator(self):
        """
        Trigger the scraper orchestrator to execute tasks

        Returns:
            bool: True if triggered successfully
        """
        if self.dry_run:
            logger.info("[DRY RUN] Would trigger orchestrator")
            return True

        try:
            cmd = [sys.executable, "scripts/orchestration/scraper_orchestrator.py"]

            logger.info(f"\n🚀 Triggering orchestrator: {' '.join(cmd)}")

            # Start orchestrator (will run to completion)
            self.orchestrator_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )  # nosec B603 - cmd is internally constructed

            self.state["last_orchestration"] = datetime.now()

            # Wait for completion with timeout
            max_runtime = self.config["max_orchestrator_runtime_minutes"] * 60

            try:
                stdout, stderr = self.orchestrator_process.communicate(
                    timeout=max_runtime
                )

                if self.orchestrator_process.returncode == 0:
                    logger.info("✅ Orchestrator completed successfully")
                    self.state["cycles_completed"] += 1
                    self.stats["orchestrator_success"] += 1
                    return True
                else:
                    logger.error(
                        f"❌ Orchestrator failed with code {self.orchestrator_process.returncode}"
                    )
                    logger.error(f"stderr: {stderr[:500]}")
                    self.stats["orchestrator_failure"] += 1
                    return False

            except subprocess.TimeoutExpired:
                logger.error(f"⏰ Orchestrator timed out after {max_runtime}s")
                self.orchestrator_process.kill()
                self.stats["orchestrator_timeout"] += 1
                return False

        except Exception as e:
            logger.error(f"Failed to trigger orchestrator: {e}")
            self.stats["orchestrator_error"] += 1
            return False

    def _shutdown(self):
        """
        Graceful shutdown of all components
        """
        logger.info("\n🛑 Shutting down autonomous loop...")
        self.state["status"] = "stopped"

        # Stop health monitor HTTP server
        if self.health_monitor and self.health_monitor.server:
            logger.info("Stopping health monitor...")
            try:
                self.health_monitor.server.shutdown()
                self.health_monitor_thread.join(timeout=5)
                logger.info("✅ Health monitor stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping health monitor: {e}")

        # Stop reconciliation daemon (if using subprocess version)
        if isinstance(self.reconciliation_daemon, subprocess.Popen):
            if self.reconciliation_daemon.poll() is None:
                logger.info("Stopping reconciliation daemon...")
                self.reconciliation_daemon.terminate()
                try:
                    self.reconciliation_daemon.wait(timeout=10)
                    logger.info("✅ Reconciliation daemon stopped")
                except subprocess.TimeoutExpired:
                    logger.warning("⏰ Reconciliation daemon did not stop, killing...")
                    self.reconciliation_daemon.kill()

        # Stop orchestrator if running
        if self.orchestrator_process and self.orchestrator_process.poll() is None:
            logger.info("Stopping orchestrator...")
            self.orchestrator_process.terminate()
            try:
                self.orchestrator_process.wait(timeout=10)
                logger.info("✅ Orchestrator stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⏰ Orchestrator did not stop, killing...")
                self.orchestrator_process.kill()

        # Print final statistics
        self._print_statistics()

        logger.info("=" * 80)
        logger.info("✅ AUTONOMOUS LOOP SHUTDOWN COMPLETE")
        logger.info("=" * 80)

    def _print_statistics(self):
        """Print final statistics"""
        runtime = datetime.now() - self.state["start_time"]

        logger.info("\n" + "=" * 80)
        logger.info("AUTONOMOUS LOOP STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Runtime: {runtime}")
        logger.info(f"Cycles completed: {self.state['cycles_completed']}")
        logger.info(f"Orchestrator successes: {self.stats['orchestrator_success']}")
        logger.info(f"Orchestrator failures: {self.stats['orchestrator_failure']}")
        logger.info(f"Orchestrator timeouts: {self.stats['orchestrator_timeout']}")
        logger.info(f"Errors encountered: {len(self.state['errors'])}")

        if self.state["last_reconciliation"]:
            logger.info(f"Last reconciliation: {self.state['last_reconciliation']}")
        if self.state["last_orchestration"]:
            logger.info(f"Last orchestration: {self.state['last_orchestration']}")

        logger.info("=" * 80)


def main():
    """CLI entry point for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Autonomous Loop Controller - 24/7 Self-Healing Data Collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start autonomous loop
  python -m nba_simulator.adce.autonomous_loop

  # Start with custom config
  python -m nba_simulator.adce.autonomous_loop --config my_config.yaml

  # Dry run mode
  python -m nba_simulator.adce.autonomous_loop --dry-run
        """,
    )

    parser.add_argument(
        "--config",
        default="config/autonomous_config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no actual execution)"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Test mode (skip reconciliation, for component testing)",
    )

    args = parser.parse_args()

    # Initialize and start autonomous loop
    try:
        loop = AutonomousLoop(
            config_file=args.config, dry_run=args.dry_run, test_mode=args.test_mode
        )

        success = loop.start()

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
