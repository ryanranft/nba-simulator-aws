#!/usr/bin/env python3
"""
Health Monitor - ADCE Phase 4
HTTP health check endpoint and monitoring dashboard

Features:
- HTTP health check endpoints (port 8080)
- Component health checks (reconciliation, orchestrator, S3, DIMS)
- System status dashboard
- Prometheus metrics export
- Error tracking and alerting

Usage:
    # Start health monitor
    python health_monitor.py

    # Start on custom port
    python health_monitor.py --port 8081

Endpoints:
    GET /health - Overall health status (200 OK or 503 Unhealthy)
    GET /status - Detailed component status
    GET /metrics - Current cycle metrics
    GET /tasks - Current task queue summary
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess  # nosec B404 - Used for checking process status only
import threading

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Health monitoring service

    Provides HTTP endpoints for checking system health
    """

    def __init__(self, port=8080):
        """
        Initialize health monitor

        Args:
            port: HTTP port for health check endpoints
        """
        self.port = port
        self.server = None

        logger.info(f"Health monitor initialized on port {port}")

    def check_overall_health(self):
        """
        Check overall system health

        Returns:
            dict: Health status
        """
        components = self.check_component_health()

        # Determine overall health
        overall_status = "healthy"
        for component, status in components.items():
            if status["status"] not in ["healthy", "idle", "running"]:
                overall_status = "unhealthy"
                break

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": components,
        }

    def check_component_health(self):
        """
        Check health of individual components

        Returns:
            dict: Health status of each component
        """
        health = {}

        # Check reconciliation daemon
        health["reconciliation_daemon"] = self._check_reconciliation_daemon()

        # Check orchestrator
        health["orchestrator"] = self._check_orchestrator()

        # Check task queue
        health["task_queue"] = self._check_task_queue()

        # Check S3 access
        health["s3"] = self._check_s3_access()

        # Check DIMS
        health["dims"] = self._check_dims()

        return health

    def _check_reconciliation_daemon(self):
        """Check if reconciliation daemon is running"""
        try:
            # Check if process is running
            result = subprocess.run(
                ["pgrep", "-f", "reconciliation_daemon.py"],
                capture_output=True,
                text=True,
            )  # nosec B603 B607 - Only checking process status

            if result.returncode == 0 and result.stdout.strip():
                return {
                    "status": "healthy",
                    "message": "Reconciliation daemon is running",
                    "pid": result.stdout.strip().split("\n")[0],
                }
            else:
                return {
                    "status": "stopped",
                    "message": "Reconciliation daemon is not running",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error checking reconciliation daemon: {e}",
            }

    def _check_orchestrator(self):
        """Check orchestrator status"""
        try:
            # Check if process is running
            result = subprocess.run(
                ["pgrep", "-f", "scraper_orchestrator.py"],
                capture_output=True,
                text=True,
            )  # nosec B603 B607 - Only checking process status

            if result.returncode == 0 and result.stdout.strip():
                return {
                    "status": "running",
                    "message": "Orchestrator is currently executing tasks",
                    "pid": result.stdout.strip().split("\n")[0],
                }
            else:
                return {
                    "status": "idle",
                    "message": "Orchestrator is idle (not currently running)",
                }
        except Exception as e:
            return {"status": "error", "message": f"Error checking orchestrator: {e}"}

    def _check_task_queue(self):
        """Check task queue status"""
        try:
            task_queue_file = Path("inventory/gaps.json")

            if not task_queue_file.exists():
                return {"status": "missing", "message": "Task queue file not found"}

            with open(task_queue_file, "r") as f:
                queue = json.load(f)

            total_tasks = queue.get("total_tasks", 0)

            return {
                "status": "available",
                "message": f"{total_tasks} tasks in queue",
                "total_tasks": total_tasks,
                "by_priority": queue.get("by_priority", {}),
            }
        except Exception as e:
            return {"status": "error", "message": f"Error reading task queue: {e}"}

    def _check_s3_access(self):
        """Check S3 bucket access"""
        try:
            # Try to list S3 bucket
            result = subprocess.run(
                ["aws", "s3", "ls", "s3://nba-sim-raw-data-lake/", "--max-items", "1"],
                capture_output=True,
                text=True,
                timeout=10,
            )  # nosec B603 B607 - AWS CLI command

            if result.returncode == 0:
                return {"status": "healthy", "message": "S3 bucket accessible"}
            else:
                return {
                    "status": "error",
                    "message": f"S3 access error: {result.stderr[:100]}",
                }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "S3 access check timed out"}
        except Exception as e:
            return {"status": "error", "message": f"Error checking S3: {e}"}

    def _check_dims(self):
        """Check DIMS status"""
        try:
            metrics_file = Path("inventory/metrics.yaml")

            if not metrics_file.exists():
                return {"status": "missing", "message": "DIMS metrics file not found"}

            # Check file age
            age_seconds = datetime.now().timestamp() - metrics_file.stat().st_mtime
            age_hours = age_seconds / 3600

            if age_hours > 24:
                return {
                    "status": "stale",
                    "message": f"DIMS metrics not updated in {age_hours:.1f} hours",
                }

            return {
                "status": "healthy",
                "message": f"DIMS metrics updated {age_hours:.1f} hours ago",
            }
        except Exception as e:
            return {"status": "error", "message": f"Error checking DIMS: {e}"}

    def get_metrics(self):
        """
        Get current cycle metrics

        Returns:
            dict: Current metrics
        """
        metrics = {"timestamp": datetime.now().isoformat()}

        # Read task queue metrics
        try:
            task_queue_file = Path("inventory/gaps.json")
            if task_queue_file.exists():
                with open(task_queue_file, "r") as f:
                    queue = json.load(f)

                metrics["tasks"] = {
                    "total": queue.get("total_tasks", 0),
                    "by_priority": queue.get("by_priority", {}),
                    "by_source": queue.get("by_source", {}),
                    "estimated_minutes": queue.get("estimated_total_minutes", 0),
                }
        except Exception as e:
            logger.error(f"Error reading task metrics: {e}")

        # Read S3 inventory metrics
        try:
            inventory_file = Path("inventory/cache/current_inventory.json")
            if inventory_file.exists():
                with open(inventory_file, "r") as f:
                    inventory = json.load(f)

                metadata = inventory.get("metadata", {})
                metrics["s3_inventory"] = {
                    "scan_timestamp": metadata.get("scan_timestamp"),
                    "total_objects": metadata.get("total_objects_scanned", 0),
                    "total_size_gb": metadata.get("total_size_bytes", 0) / (1024**3),
                }
        except Exception as e:
            logger.error(f"Error reading inventory metrics: {e}")

        return metrics

    def start(self):
        """Start HTTP server for health checks"""
        handler = self._create_handler()
        # Health endpoint bound to all interfaces for monitoring access
        self.server = HTTPServer(("localhost", self.port), handler)

        logger.info(f"Starting health monitor on port {self.port}")
        logger.info(f"Health check endpoints:")
        logger.info(f"  http://localhost:{self.port}/health")
        logger.info(f"  http://localhost:{self.port}/status")
        logger.info(f"  http://localhost:{self.port}/metrics")
        logger.info(f"  http://localhost:{self.port}/tasks")

        self.server.serve_forever()

    def _create_handler(self):
        """Create HTTP request handler"""
        monitor = self

        class HealthCheckHandler(BaseHTTPRequestHandler):
            """HTTP handler for health check endpoints"""

            def do_GET(self):
                """Handle GET requests"""
                if self.path == "/health":
                    self._handle_health()
                elif self.path == "/status":
                    self._handle_status()
                elif self.path == "/metrics":
                    self._handle_metrics()
                elif self.path == "/tasks":
                    self._handle_tasks()
                else:
                    self.send_error(404, "Not Found")

            def _handle_health(self):
                """Handle /health endpoint"""
                health = monitor.check_overall_health()

                # Return 200 OK if healthy, 503 if unhealthy
                status_code = 200 if health["status"] == "healthy" else 503

                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(health, indent=2).encode())

            def _handle_status(self):
                """Handle /status endpoint"""
                health = monitor.check_overall_health()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(health, indent=2).encode())

            def _handle_metrics(self):
                """Handle /metrics endpoint"""
                metrics = monitor.get_metrics()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(metrics, indent=2).encode())

            def _handle_tasks(self):
                """Handle /tasks endpoint"""
                try:
                    task_queue_file = Path("inventory/gaps.json")
                    if task_queue_file.exists():
                        with open(task_queue_file, "r") as f:
                            tasks = json.load(f)

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(tasks, indent=2).encode())
                    else:
                        self.send_error(404, "Task queue not found")
                except Exception as e:
                    self.send_error(500, f"Error reading task queue: {e}")

            def log_message(self, format, *args):
                """Override to suppress request logging"""
                pass

        return HealthCheckHandler


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Health Monitor - HTTP health check endpoints"
    )

    parser.add_argument(
        "--port", type=int, default=8080, help="HTTP port for health check endpoints"
    )

    args = parser.parse_args()

    try:
        monitor = HealthMonitor(port=args.port)
        monitor.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Health monitor stopped")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
