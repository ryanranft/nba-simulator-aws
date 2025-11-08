"""
DIMS Core Module
Handles all metric CRUD operations, configuration loading, and command execution.

Migrated to: nba_simulator.monitoring.dims
Original: scripts/monitoring/dims/core.py
"""

import os
import yaml
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# Phase 2 imports (optional - only if enabled)
try:
    from .database import DatabaseBackend

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Database backend not available")

try:
    from .approval import ApprovalManager

    APPROVAL_AVAILABLE = True
except ImportError:
    APPROVAL_AVAILABLE = False
    logger.warning("Approval manager not available")

try:
    from .events import EventHandler

    EVENTS_AVAILABLE = True
except ImportError:
    EVENTS_AVAILABLE = False
    logger.warning("Event handler not available")


class DIMSCore:
    """Core class for Data Inventory Management System operations."""

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize DIMS Core.

        Args:
            project_root: Path to project root. If None, auto-detects.
        """
        if project_root is None:
            # Auto-detect project root (look for inventory/ directory)
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "inventory").exists():
                    project_root = str(current)
                    break
                current = current.parent

        self.project_root = Path(project_root or os.getcwd())
        self.config_path = self.project_root / "inventory" / "config.yaml"
        self.metrics_path = self.project_root / "inventory" / "metrics.yaml"

        # Load configuration
        self.config = self._load_config()
        self.metrics = self._load_metrics()

        # Initialize Phase 2 modules (if enabled)
        self.database = None
        self.approval = None
        self.events = None

        features = self.config.get("features", {})

        # Database backend
        if features.get("database_backend", False) and DATABASE_AVAILABLE:
            try:
                db_config = self.config.get("database", {})
                self.database = DatabaseBackend(db_config)
                logger.info("Database backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database backend: {e}")

        # Approval workflow
        if features.get("approval_workflow", False) and APPROVAL_AVAILABLE:
            try:
                self.approval = ApprovalManager(self.config, self.database)
                logger.info("Approval workflow initialized")
            except Exception as e:
                logger.error(f"Failed to initialize approval workflow: {e}")

        # Event handler
        if features.get("event_driven", False) and EVENTS_AVAILABLE:
            try:
                self.events = EventHandler(self.config, self.database)
                logger.info("Event handler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize event handler: {e}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {self.config_path}")
        return config

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from metrics.yaml."""
        if not self.metrics_path.exists():
            logger.warning(f"Metrics file not found: {self.metrics_path}")
            return {}

        with open(self.metrics_path, "r") as f:
            metrics = yaml.safe_load(f)

        logger.info(f"Loaded metrics from {self.metrics_path}")
        return metrics

    def save_metrics(self, metrics: Optional[Dict[str, Any]] = None) -> None:
        """
        Save metrics to metrics.yaml.

        Args:
            metrics: Metrics dict to save. If None, saves current self.metrics.
        """
        if metrics is None:
            metrics = self.metrics

        # Update metadata
        if "metadata" not in metrics:
            metrics["metadata"] = {}

        metrics["metadata"]["last_updated"] = datetime.now().isoformat() + "Z"
        metrics["metadata"]["version"] = self.config.get("version", "1.0.0")

        # Write to file
        with open(self.metrics_path, "w") as f:
            yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved metrics to {self.metrics_path}")

    def execute_command(
        self, command: str, timeout: int = 30
    ) -> Tuple[bool, Optional[str]]:
        """
        Execute a shell command and return its output.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success: bool, output: Optional[str])
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root),
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                return (True, output)
            else:
                logger.error(f"Command failed: {command}")
                logger.error(f"Error: {result.stderr}")
                return (False, None)

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return (False, None)
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return (False, None)

    def get_metric_value(
        self, metric_path: str, use_cache: bool = True
    ) -> Optional[Any]:
        """
        Get current value of a metric from metrics.yaml.

        Args:
            metric_path: Dot-separated path to metric (e.g., 's3_storage.total_objects')
            use_cache: Whether to use cached value

        Returns:
            Metric value or None if not found
        """
        parts = metric_path.split(".")
        current = self.metrics

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        # Extract value if it's in standard format
        if isinstance(current, dict) and "value" in current:
            return current["value"]

        return current

    def calculate_metric(self, metric_category: str, metric_name: str) -> Optional[Any]:
        """
        Calculate current value of a metric by executing its command.

        Args:
            metric_category: Metric category (e.g., 's3_storage')
            metric_name: Metric name (e.g., 'total_objects')

        Returns:
            Calculated value or None if calculation failed
        """
        # Get metric definition from config
        metric_def = (
            self.config.get("metrics", {}).get(metric_category, {}).get(metric_name)
        )

        if not metric_def:
            logger.error(
                f"Metric definition not found: {metric_category}.{metric_name}"
            )
            return None

        # Check if metric is enabled
        if not metric_def.get("enabled", True):
            logger.info(f"Metric disabled: {metric_category}.{metric_name}")
            return None

        # Get command
        command = metric_def.get("command")
        if not command:
            logger.error(
                f"No command defined for metric: {metric_category}.{metric_name}"
            )
            return None

        # Execute command
        success, output = self.execute_command(command)

        if not success or output is None:
            return None

        # Parse output based on parse_type
        parse_type = metric_def.get("parse_type", "string")

        try:
            if parse_type == "integer":
                return int(output)
            elif parse_type == "float":
                precision = metric_def.get("precision", 2)
                return round(float(output), precision)
            elif parse_type == "string":
                return output
            elif parse_type == "boolean":
                return output.lower() in ("true", "yes", "1")
            else:
                return output
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to parse output '{output}' as {parse_type}: {e}")
            return None

    def update_metric(
        self,
        metric_category: str,
        metric_name: str,
        new_value: Any,
        verification_method: str = "automated",
        verified_by: str = "dims_core",
    ) -> bool:
        """
        Update a metric value in metrics.yaml (and database if enabled).

        Args:
            metric_category: Metric category
            metric_name: Metric name
            new_value: New value to set
            verification_method: How the value was verified
            verified_by: Who/what verified the value

        Returns:
            True if successful, False otherwise
        """
        # Navigate to metric location
        if metric_category not in self.metrics:
            self.metrics[metric_category] = {}

        if metric_name not in self.metrics[metric_category]:
            self.metrics[metric_category][metric_name] = {}

        metric = self.metrics[metric_category][metric_name]

        # Store old value for logging
        old_value = metric.get("value") if isinstance(metric, dict) else metric

        # Update metric in YAML
        if isinstance(metric, dict):
            metric["value"] = new_value
            metric["last_verified"] = datetime.now().isoformat() + "Z"
            metric["verification_method"] = verification_method
            metric["cached"] = False
            metric["cache_expires"] = None
        else:
            # Create new metric structure
            self.metrics[metric_category][metric_name] = {
                "value": new_value,
                "last_verified": datetime.now().isoformat() + "Z",
                "verification_method": verification_method,
                "cached": False,
                "cache_expires": None,
            }

        logger.info(
            f"Updated metric {metric_category}.{metric_name}: "
            f"{old_value} → {new_value}"
        )

        # Also save to database if enabled
        if self.database:
            # Determine value type
            value_type = "string"
            if isinstance(new_value, bool):
                value_type = "boolean"
            elif isinstance(new_value, int):
                value_type = "integer"
            elif isinstance(new_value, float):
                value_type = "float"

            self.database.save_metric(
                metric_category=metric_category,
                metric_name=metric_name,
                value=new_value,
                value_type=value_type,
                verification_method=verification_method,
                verified_by=verified_by,
            )

        return True

    def verify_metric(self, metric_category: str, metric_name: str) -> Dict[str, Any]:
        """
        Verify a single metric by comparing documented vs actual value.

        Args:
            metric_category: Metric category
            metric_name: Metric name

        Returns:
            Dict with verification results
        """
        result = {
            "metric": f"{metric_category}.{metric_name}",
            "documented": None,
            "actual": None,
            "drift": None,
            "drift_pct": None,
            "status": "ok",
            "severity": "none",
            "message": "",
        }

        # Get documented value
        documented = self.get_metric_value(f"{metric_category}.{metric_name}")
        result["documented"] = documented

        # Calculate actual value
        actual = self.calculate_metric(metric_category, metric_name)
        result["actual"] = actual

        if actual is None:
            result["status"] = "error"
            result["severity"] = "high"
            result["message"] = "Failed to calculate actual value"
            return result

        if documented is None:
            result["status"] = "new"
            result["severity"] = "low"
            result["message"] = "No documented value found (new metric)"
            return result

        # Calculate drift
        try:
            if isinstance(documented, (int, float)) and isinstance(
                actual, (int, float)
            ):
                drift = actual - documented
                result["drift"] = drift

                if documented != 0:
                    drift_pct = abs((drift / documented) * 100)
                    result["drift_pct"] = round(drift_pct, 2)
                else:
                    drift_pct = 0 if drift == 0 else 100
                    result["drift_pct"] = drift_pct

                # Determine status based on thresholds
                thresholds = self.config.get("verification", {}).get("thresholds", {})
                minor_threshold = thresholds.get("minor_drift_pct", 5)
                moderate_threshold = thresholds.get("moderate_drift_pct", 15)

                if drift == 0:
                    result["status"] = "ok"
                    result["severity"] = "none"
                    result["message"] = "Values match exactly"
                elif drift_pct < minor_threshold:
                    result["status"] = "minor"
                    result["severity"] = "low"
                    result["message"] = f"Minor drift: {drift_pct:.1f}%"
                elif drift_pct < moderate_threshold:
                    result["status"] = "moderate"
                    result["severity"] = "medium"
                    result["message"] = f"Moderate drift: {drift_pct:.1f}%"
                else:
                    result["status"] = "major"
                    result["severity"] = "high"
                    result["message"] = f"Major drift: {drift_pct:.1f}%"

            else:
                # Non-numeric comparison
                if documented == actual:
                    result["status"] = "ok"
                    result["message"] = "Values match"
                else:
                    result["status"] = "different"
                    result["severity"] = "medium"
                    result["message"] = "Values differ"
                    result["drift"] = f"{documented} → {actual}"

        except Exception as e:
            result["status"] = "error"
            result["severity"] = "high"
            result["message"] = f"Error comparing values: {e}"

        return result

    def verify_all_metrics(self, triggered_by: str = "manual") -> Dict[str, Any]:
        """
        Verify all metrics defined in config.

        Args:
            triggered_by: What triggered this verification

        Returns:
            Dict with verification results
        """
        start_time = datetime.now()

        results = {
            "timestamp": start_time.isoformat() + "Z",
            "total_metrics": 0,
            "verified": 0,
            "drift_detected": False,
            "discrepancies": [],
            "approvals_required": [],
            "summary": {
                "ok": 0,
                "minor": 0,
                "moderate": 0,
                "major": 0,
                "error": 0,
                "new": 0,
            },
        }

        metrics_config = self.config.get("metrics", {})

        for category, metrics in metrics_config.items():
            for metric_name, metric_def in metrics.items():
                results["total_metrics"] += 1

                # Skip if disabled
                if not metric_def.get("enabled", True):
                    continue

                logger.info(f"Verifying {category}.{metric_name}...")

                verification = self.verify_metric(category, metric_name)
                results["verified"] += 1

                # Update summary
                status = verification["status"]
                if status in results["summary"]:
                    results["summary"][status] += 1

                # Add to discrepancies if not OK
                if status != "ok":
                    results["discrepancies"].append(verification)

                if status in ("minor", "moderate", "major"):
                    results["drift_detected"] = True

        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(
            f"Verification complete: {results['verified']}/{results['total_metrics']} metrics verified in {execution_time_ms}ms"
        )

        # Save verification run to database if enabled
        if self.database:
            run_id = self.database.save_verification_run(
                results=results,
                triggered_by=triggered_by,
                execution_time_ms=execution_time_ms,
            )
            results["verification_run_id"] = run_id

        return results

    def get_metric_history(
        self, metric_path: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical values of a metric from snapshots.

        Args:
            metric_path: Dot-separated metric path
            days: Number of days to look back

        Returns:
            List of {date: str, value: Any} dicts
        """
        history = []
        historical_dir = self.project_root / "inventory" / "historical"

        if not historical_dir.exists():
            return history

        # Get snapshot files from last N days
        cutoff_date = datetime.now() - timedelta(days=days)

        for snapshot_file in sorted(historical_dir.glob("*.yaml")):
            try:
                # Parse date from filename (YYYY-MM-DD.yaml)
                date_str = snapshot_file.stem
                snapshot_date = datetime.strptime(date_str, "%Y-%m-%d")

                if snapshot_date < cutoff_date:
                    continue

                # Load snapshot
                with open(snapshot_file, "r") as f:
                    snapshot = yaml.safe_load(f)

                # Extract metric value
                parts = metric_path.split(".")
                current = snapshot
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break

                if current is not None:
                    if isinstance(current, dict) and "value" in current:
                        value = current["value"]
                    else:
                        value = current

                    history.append({"date": date_str, "value": value})

            except Exception as e:
                logger.warning(f"Error reading snapshot {snapshot_file}: {e}")
                continue

        return history

    def create_snapshot(self) -> bool:
        """
        Create a snapshot of current metrics (file and database).

        Returns:
            True if successful, False otherwise
        """
        try:
            historical_dir = self.project_root / "inventory" / "historical"
            historical_dir.mkdir(parents=True, exist_ok=True)

            # Create snapshot filename (YYYY-MM-DD.yaml)
            today = datetime.now()
            snapshot_file = historical_dir / f"{today.strftime('%Y-%m-%d')}.yaml"

            # Write current metrics to file
            with open(snapshot_file, "w") as f:
                yaml.dump(self.metrics, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Created snapshot: {snapshot_file}")

            # Also save to database if enabled
            if self.database:
                self.database.save_snapshot(today, self.metrics)

            return True

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get DIMS system information.

        Returns:
            Dict with system info
        """
        return {
            "version": self.config.get("version", "unknown"),
            "system_name": self.config.get("system_name", "DIMS"),
            "project_root": str(self.project_root),
            "config_path": str(self.config_path),
            "metrics_path": str(self.metrics_path),
            "features": self.config.get("features", {}),
            "cache_enabled": self.config.get("cache", {}).get("enabled", False),
            "verification_enabled": self.config.get("verification", {}).get(
                "enabled", False
            ),
            "total_metrics_defined": sum(
                len(metrics) for metrics in self.config.get("metrics", {}).values()
            ),
            "total_metrics_documented": len(self.metrics) - 1,  # Exclude metadata
        }
