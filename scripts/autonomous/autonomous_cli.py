#!/usr/bin/env python3
"""
Autonomous CLI - ADCE Phase 4
Command-line interface for managing the autonomous loop

Commands:
    autonomous start    - Start autonomous loop
    autonomous stop     - Graceful shutdown
    autonomous status   - Show current status
    autonomous restart  - Restart the loop
    autonomous health   - Check component health
    autonomous logs     - View recent logs
    autonomous tasks    - Show current task queue

Usage:
    # Start autonomous loop
    python autonomous_cli.py start

    # Check status
    python autonomous_cli.py status

    # View logs
    python autonomous_cli.py logs --tail 50
"""

import sys
import subprocess  # nosec B404 - Used for managing autonomous loop process
import json
import logging
from pathlib import Path
from datetime import datetime
import argparse
import time
import signal
import requests

logging.basicConfig(
    level=logging.INFO, format="%(message)s"  # Simple format for CLI output
)
logger = logging.getLogger(__name__)


class AutonomousCLI:
    """
    CLI for managing autonomous loop
    """

    def __init__(self):
        """Initialize CLI"""
        self.pid_file = Path("logs/autonomous_loop.pid")
        self.log_file = Path("logs/autonomous_loop.log")
        self.health_port = 8080

    def start(self, dry_run=False, test_mode=False):
        """
        Start autonomous loop

        Args:
            dry_run: If True, start in dry-run mode
            test_mode: If True, start in test mode (no reconciliation)
        """
        # Check if already running
        if self.is_running():
            logger.info("❌ Autonomous loop is already running")
            pid = self._read_pid()
            logger.info(f"   PID: {pid}")
            return False

        logger.info("🚀 Starting autonomous loop...")

        cmd = [sys.executable, "scripts/autonomous/autonomous_loop.py"]

        if dry_run:
            cmd.append("--dry-run")

        if test_mode:
            cmd.append("--test-mode")

        # Start in background
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Detach from parent
            )  # nosec B603 - cmd is internally constructed

            # Save PID
            self._write_pid(process.pid)

            # Give it a moment to start
            time.sleep(2)

            # Check if still running
            if process.poll() is not None:
                logger.error("❌ Autonomous loop failed to start")
                return False

            logger.info(f"✅ Autonomous loop started")
            logger.info(f"   PID: {process.pid}")
            logger.info(f"   Log: {self.log_file}")
            logger.info(f"   Health: http://localhost:{self.health_port}/health")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to start autonomous loop: {e}")
            return False

    def stop(self):
        """Stop autonomous loop gracefully"""
        if not self.is_running():
            logger.info("❌ Autonomous loop is not running")
            return False

        logger.info("🛑 Stopping autonomous loop...")

        pid = self._read_pid()

        try:
            # Send SIGTERM for graceful shutdown
            process = subprocess.run(
                ["kill", "-TERM", str(pid)], capture_output=True
            )  # nosec B603 B607 - Sending signal to known PID

            # Wait for shutdown
            logger.info("   Waiting for graceful shutdown...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if not self.is_running():
                    break

            if self.is_running():
                logger.warning("⚠️  Process did not stop gracefully, forcing...")
                subprocess.run(["kill", "-KILL", str(pid)])  # nosec B603 B607
                time.sleep(1)

            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

            logger.info("✅ Autonomous loop stopped")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to stop autonomous loop: {e}")
            return False

    def status(self):
        """Show current status"""
        logger.info("=" * 80)
        logger.info("AUTONOMOUS LOOP STATUS")
        logger.info("=" * 80)

        # Check if running
        running = self.is_running()

        if running:
            logger.info("Status: ✅ RUNNING")
            pid = self._read_pid()
            logger.info(f"PID: {pid}")
        else:
            logger.info("Status: ⏹️  STOPPED")
            logger.info("=" * 80)
            return False

        # Get health status
        try:
            response = requests.get(
                f"http://localhost:{self.health_port}/status", timeout=5
            )
            if response.status_code == 200:
                status = response.json()

                logger.info(
                    f"\nOverall Health: {status.get('status', 'unknown').upper()}"
                )
                logger.info(f"Last Check: {status.get('timestamp', 'N/A')}")

                logger.info("\nComponents:")
                for component, info in status.get("components", {}).items():
                    status_emoji = (
                        "✅"
                        if info["status"] in ["healthy", "idle", "running", "available"]
                        else "❌"
                    )
                    logger.info(f"  {status_emoji} {component}: {info['status']}")
                    if "message" in info:
                        logger.info(f"      {info['message']}")
            else:
                logger.warning(
                    "\n⚠️  Could not get health status (health monitor may not be running)"
                )
        except requests.exceptions.ConnectionError:
            logger.warning("\n⚠️  Could not connect to health monitor")
        except Exception as e:
            logger.warning(f"\n⚠️  Error getting health status: {e}")

        # Get metrics
        try:
            response = requests.get(
                f"http://localhost:{self.health_port}/metrics", timeout=5
            )
            if response.status_code == 200:
                metrics = response.json()

                if "tasks" in metrics:
                    logger.info("\nTask Queue:")
                    logger.info(f"  Total: {metrics['tasks']['total']}")
                    logger.info(f"  By Priority: {metrics['tasks']['by_priority']}")

                if "s3_inventory" in metrics:
                    logger.info("\nS3 Inventory:")
                    logger.info(
                        f"  Objects: {metrics['s3_inventory']['total_objects']:,}"
                    )
                    logger.info(
                        f"  Size: {metrics['s3_inventory']['total_size_gb']:.2f} GB"
                    )
        except Exception as e:  # nosec B110 - Metrics are optional, not critical
            pass  # Metrics are optional

        logger.info("=" * 80)
        return True

    def restart(self):
        """Restart autonomous loop"""
        logger.info("🔄 Restarting autonomous loop...")

        if self.is_running():
            if not self.stop():
                return False
            time.sleep(2)

        return self.start()

    def health(self):
        """Check component health"""
        try:
            response = requests.get(
                f"http://localhost:{self.health_port}/health", timeout=5
            )

            logger.info("=" * 80)
            logger.info("HEALTH CHECK")
            logger.info("=" * 80)

            if response.status_code == 200:
                health = response.json()
                logger.info(f"Overall Status: ✅ {health['status'].upper()}")

                logger.info("\nComponent Health:")
                for component, info in health.get("components", {}).items():
                    status_emoji = (
                        "✅"
                        if info["status"] in ["healthy", "idle", "running", "available"]
                        else "❌"
                    )
                    logger.info(f"  {status_emoji} {component}: {info['status']}")
                    if "message" in info:
                        logger.info(f"      {info['message']}")

                logger.info("=" * 80)
                return True
            else:
                logger.error(f"❌ Health check failed (HTTP {response.status_code})")
                return False

        except requests.exceptions.ConnectionError:
            logger.error("❌ Could not connect to health monitor")
            logger.error("   Is the autonomous loop running?")
            return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    def logs(self, tail=50, follow=False):
        """
        View logs

        Args:
            tail: Number of lines to show
            follow: If True, follow log file (like tail -f)
        """
        if not self.log_file.exists():
            logger.error(f"❌ Log file not found: {self.log_file}")
            return False

        try:
            if follow:
                # Follow log file
                subprocess.run(["tail", "-f", str(self.log_file)])  # nosec B603 B607
            else:
                # Show last N lines
                result = subprocess.run(
                    ["tail", "-n", str(tail), str(self.log_file)],
                    capture_output=True,
                    text=True,
                )  # nosec B603 B607
                print(result.stdout)

            return True
        except Exception as e:
            logger.error(f"❌ Error reading logs: {e}")
            return False

    def tasks(self):
        """Show current task queue"""
        try:
            response = requests.get(
                f"http://localhost:{self.health_port}/tasks", timeout=5
            )

            logger.info("=" * 80)
            logger.info("TASK QUEUE")
            logger.info("=" * 80)

            if response.status_code == 200:
                tasks = response.json()

                logger.info(f"Total Tasks: {tasks.get('total_tasks', 0)}")
                logger.info(f"Generated: {tasks.get('generated_at', 'N/A')}")

                by_priority = tasks.get("by_priority", {})
                logger.info("\nBy Priority:")
                logger.info(f"  🔴 Critical: {by_priority.get('critical', 0)}")
                logger.info(f"  🟡 High: {by_priority.get('high', 0)}")
                logger.info(f"  🟢 Medium: {by_priority.get('medium', 0)}")
                logger.info(f"  ⚪ Low: {by_priority.get('low', 0)}")

                by_source = tasks.get("by_source", {})
                if by_source:
                    logger.info("\nBy Source:")
                    for source, count in by_source.items():
                        logger.info(f"  {source}: {count}")

                logger.info(
                    f"\nEstimated Time: {tasks.get('estimated_total_minutes', 0)} minutes"
                )

                logger.info("=" * 80)
                return True
            else:
                logger.error("❌ Could not get task queue")
                return False

        except requests.exceptions.ConnectionError:
            # Try reading file directly
            logger.warning(
                "⚠️  Could not connect to health monitor, reading file directly..."
            )

            task_queue_file = Path("inventory/gaps.json")
            if not task_queue_file.exists():
                logger.error("❌ Task queue file not found")
                return False

            try:
                with open(task_queue_file, "r") as f:
                    tasks = json.load(f)

                logger.info("=" * 80)
                logger.info("TASK QUEUE (from file)")
                logger.info("=" * 80)
                logger.info(f"Total Tasks: {tasks.get('total_tasks', 0)}")
                logger.info(f"By Priority: {tasks.get('by_priority', {})}")
                logger.info("=" * 80)
                return True
            except Exception as e:
                logger.error(f"❌ Error reading task queue: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

    def is_running(self):
        """
        Check if autonomous loop is running

        Returns:
            bool: True if running
        """
        if not self.pid_file.exists():
            return False

        pid = self._read_pid()
        if pid is None:
            return False

        try:
            # Check if process exists
            result = subprocess.run(
                ["ps", "-p", str(pid)], capture_output=True
            )  # nosec B603 B607 - Checking if PID exists

            return result.returncode == 0
        except Exception:
            return False

    def _read_pid(self):
        """Read PID from file"""
        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except Exception:
            return None

    def _write_pid(self, pid):
        """Write PID to file"""
        try:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pid_file, "w") as f:
                f.write(str(pid))
        except Exception as e:
            logger.error(f"Warning: Could not write PID file: {e}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Autonomous Loop CLI - Manage 24/7 Data Collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  start     Start autonomous loop
  stop      Stop autonomous loop gracefully
  status    Show current status
  restart   Restart autonomous loop
  health    Check component health
  logs      View recent logs
  tasks     Show current task queue

Examples:
  # Start autonomous loop
  python autonomous_cli.py start

  # Check status
  python autonomous_cli.py status

  # View logs
  python autonomous_cli.py logs --tail 100

  # Follow logs
  python autonomous_cli.py logs --follow
        """,
    )

    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "restart", "health", "logs", "tasks"],
        help="Command to execute",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Start in dry-run mode (for start command)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Start in test mode - skip reconciliation (for start command)",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=50,
        help="Number of log lines to show (for logs command)",
    )
    parser.add_argument(
        "--follow", action="store_true", help="Follow log file (for logs command)"
    )

    args = parser.parse_args()

    cli = AutonomousCLI()

    try:
        if args.command == "start":
            success = cli.start(dry_run=args.dry_run, test_mode=args.test_mode)
        elif args.command == "stop":
            success = cli.stop()
        elif args.command == "status":
            success = cli.status()
        elif args.command == "restart":
            success = cli.restart()
        elif args.command == "health":
            success = cli.health()
        elif args.command == "logs":
            success = cli.logs(tail=args.tail, follow=args.follow)
        elif args.command == "tasks":
            success = cli.tasks()
        else:
            parser.print_help()
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted")
        return 130
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
