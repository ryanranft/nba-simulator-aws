"""
Daily ESPN Update Workflow - Automated Data Collection and Catalog Maintenance

Replaces: scripts/workflows/daily_espn_update.sh

This workflow automates daily ESPN data collection, database updates, and
DATA_CATALOG.md maintenance with optional Slack notifications and git commits.

Usage:
    from daily_update_workflow import DailyUpdateWorkflow

    workflow = DailyUpdateWorkflow(config=config_dict)
    if workflow.initialize():
        success = workflow.execute()
        workflow.shutdown()

Author: NBA Simulator AWS Team
Version: 2.0.0
Created: [Date TBD]
"""

import sys
import json
import sqlite3
import subprocess
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from nba_simulator.workflows import (
    BaseWorkflow,
    WorkflowTask,
    WorkflowPriority,
    WorkflowState,
)


class DailyUpdateWorkflow(BaseWorkflow):
    """
    Daily ESPN update workflow.

    Tasks:
    1. Pre-flight checks
    2. Trigger ESPN scraper (optional)
    3. Update local database
    4. Update DATA_CATALOG.md
    5. Git commit (optional)
    6. Cleanup old logs
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Daily Update Workflow"""
        if config is None:
            config = {}

        config = self._merge_with_defaults(config)

        super().__init__(
            workflow_name="daily_update",
            workflow_type="etl",
            config=config,
            priority=WorkflowPriority.HIGH,
        )

        self.project_dir = Path(config.get("project_dir", PROJECT_ROOT))
        self.log_dir = Path(config.get("log_dir", "/tmp"))
        self.espn_scraper_dir = Path(
            config.get("espn_scraper_dir", Path.home() / "0espn")
        )
        self.local_db = Path(config.get("local_db", "/tmp/espn_local.db"))

        self.catalog_file = self.project_dir / config.get("catalog", {}).get(
            "file", "docs/DATA_CATALOG.md"
        )
        self.update_script = self.project_dir / config.get("catalog", {}).get(
            "update_script", "scripts/utils/update_data_catalog.py"
        )
        self.rebuild_script = self.project_dir / config.get("catalog", {}).get(
            "rebuild_script", "scripts/db/create_local_espn_database.py"
        )

        self.auto_commit = config.get("git", {}).get("auto_commit", False)

        self.slack_webhook = config.get("notification", {}).get("slack_webhook", "")

        self.log_retention_days = config.get("cleanup", {}).get("log_retention_days", 7)

        # Track database changes
        self.games_before = 0
        self.events_before = 0
        self.games_after = 0
        self.events_after = 0

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults"""
        defaults = {
            "project_dir": str(PROJECT_ROOT),
            "log_dir": "/tmp",
            "espn_scraper_dir": str(Path.home() / "0espn"),
            "local_db": "/tmp/espn_local.db",
            "catalog": {
                "file": "docs/DATA_CATALOG.md",
                "update_script": "scripts/utils/update_data_catalog.py",
                "rebuild_script": "scripts/db/create_local_espn_database.py",
            },
            "git": {"auto_commit": False},
            "notification": {"slack_webhook": ""},
            "cleanup": {"log_retention_days": 7},
        }

        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in config[key]:
                        config[key][subkey] = subvalue

        return config

    def _validate_config(self) -> bool:
        """Validate workflow configuration"""
        if not self.project_dir.exists():
            self.log_error(f"Project directory does not exist: {self.project_dir}")
            return False

        if not self.update_script.exists():
            self.log_error(f"Update script not found: {self.update_script}")
            return False

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_error(f"Failed to create log directory: {e}")
            return False

        self.logger.info("✓ Configuration validated successfully")
        return True

    def _build_tasks(self) -> List[WorkflowTask]:
        """Build workflow task graph"""
        return [
            # Pre-flight checks
            WorkflowTask(
                task_id="preflight",
                task_name="Pre-Flight Checks",
                task_type="preflight",
                params={},
                max_retries=1,
                dependencies=[],
                is_critical=True,  # Fatal if checks fail
            ),
            # Trigger ESPN scraper (optional)
            WorkflowTask(
                task_id="trigger_scraper",
                task_name="Trigger ESPN Scraper",
                task_type="scraper",
                params={"espn_scraper_dir": str(self.espn_scraper_dir)},
                max_retries=1,
                dependencies=["preflight"],
                is_critical=False,  # Non-fatal (may not run)
            ),
            # Update local database
            WorkflowTask(
                task_id="update_database",
                task_name="Update Local Database",
                task_type="database",
                params={
                    "rebuild_script": str(self.rebuild_script),
                    "local_db": str(self.local_db),
                },
                max_retries=2,
                dependencies=["preflight"],  # Can run without scraper
                is_critical=True,  # Fatal if fails
            ),
            # Update catalog
            WorkflowTask(
                task_id="update_catalog",
                task_name="Update Data Catalog",
                task_type="catalog",
                params={
                    "update_script": str(self.update_script),
                    "catalog_file": str(self.catalog_file),
                },
                max_retries=2,
                dependencies=["update_database"],
                is_critical=True,  # Fatal if fails
            ),
            # Git commit (optional)
            WorkflowTask(
                task_id="git_commit",
                task_name="Git Commit Updates",
                task_type="git",
                params={
                    "catalog_file": str(self.catalog_file),
                    "auto_commit": self.auto_commit,
                },
                max_retries=1,
                dependencies=["update_catalog"],
                is_critical=False,  # Non-fatal
            ),
            # Cleanup
            WorkflowTask(
                task_id="cleanup",
                task_name="Cleanup Old Logs",
                task_type="cleanup",
                params={
                    "log_dir": str(self.log_dir),
                    "retention_days": self.log_retention_days,
                },
                max_retries=1,
                dependencies=[],  # Can run independently
                is_critical=False,  # Non-fatal
            ),
        ]

    def _execute_task(self, task: WorkflowTask) -> Any:
        """Execute a single workflow task"""
        task_type = task.task_type
        params = task.params

        self.logger.info(f"Executing {task_type} task: {task.task_name}")

        if task_type == "preflight":
            return self._execute_preflight_task(params)
        elif task_type == "scraper":
            return self._execute_scraper_task(params)
        elif task_type == "database":
            return self._execute_database_task(params)
        elif task_type == "catalog":
            return self._execute_catalog_task(params)
        elif task_type == "git":
            return self._execute_git_task(params)
        elif task_type == "cleanup":
            return self._execute_cleanup_task(params)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _execute_preflight_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pre-flight checks"""
        self.logger.info(f"  Running pre-flight checks...")

        checks = []

        # Check ESPN scraper directory
        if self.espn_scraper_dir.exists():
            checks.append(("ESPN scraper directory", True, str(self.espn_scraper_dir)))
        else:
            checks.append(
                ("ESPN scraper directory", False, f"Not found: {self.espn_scraper_dir}")
            )
            self.logger.warning(
                f"  ESPN scraper directory not found (scraper trigger will skip)"
            )

        # Check local database
        if self.local_db.exists():
            checks.append(("Local database", True, str(self.local_db)))
        else:
            checks.append(
                ("Local database", False, f"Not found: {self.local_db} (will rebuild)")
            )
            self.logger.warning(f"  Local database not found (will rebuild)")

        # Check update script
        if self.update_script.exists():
            checks.append(("Update script", True, str(self.update_script)))
        else:
            checks.append(("Update script", False, f"Not found: {self.update_script}"))
            self.logger.error(f"  Update script not found")
            return {"status": "failed", "reason": "update_script_not_found"}

        # Check conda environment
        import os

        conda_env = os.environ.get("CONDA_DEFAULT_ENV")
        if conda_env:
            checks.append(("Conda environment", True, conda_env))
        else:
            checks.append(("Conda environment", False, "Not active"))
            self.logger.warning(f"  Conda environment not active")

        self.logger.info(f"  ✓ Pre-flight checks complete")
        for check_name, passed, detail in checks:
            status = "✓" if passed else "✗"
            self.logger.info(f"    {status} {check_name}: {detail}")

        return {"status": "success", "checks": checks}

    def _execute_scraper_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ESPN scraper trigger (optional)"""
        espn_scraper_dir = Path(params["espn_scraper_dir"])

        if not espn_scraper_dir.exists():
            self.logger.info(f"  ESPN scraper directory not found, skipping")
            return {"status": "skipped", "reason": "directory_not_found"}

        scraper_script = espn_scraper_dir / "scrape_daily.py"

        if not scraper_script.exists():
            self.logger.info(f"  ESPN scraper script not found, skipping")
            return {"status": "skipped", "reason": "script_not_found"}

        # Calculate date range (yesterday to today)
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        self.logger.info(f"  Scraping games from {yesterday} to {today}")

        cmd = [
            sys.executable,
            str(scraper_script),
            "--start-date",
            yesterday.strftime("%Y-%m-%d"),
            "--end-date",
            today.strftime("%Y-%m-%d"),
            "--upload-s3",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(espn_scraper_dir),
                capture_output=True,
                text=True,
                timeout=1800,
            )

            if result.returncode == 0:
                self.logger.info(f"  ✓ ESPN scraper completed")
                return {"status": "success"}
            else:
                self.logger.error(f"  ✗ ESPN scraper failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}

        except Exception as e:
            self.logger.error(f"  ✗ ESPN scraper error: {e}")
            return {"status": "error", "error": str(e)}

    def _execute_database_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute local database update"""
        rebuild_script = Path(params["rebuild_script"])
        local_db = Path(params["local_db"])

        self.logger.info(f"  Updating local SQLite database...")

        # Get current database stats (before update)
        if local_db.exists():
            try:
                conn = sqlite3.connect(local_db)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM games")
                self.games_before = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM pbp_events")
                self.events_before = cursor.fetchone()[0]

                conn.close()

                self.logger.info(
                    f"    Current database: {self.games_before} games, {self.events_before} events"
                )
            except Exception as e:
                self.logger.warning(f"    Could not read current database stats: {e}")

        # Rebuild database
        try:
            result = subprocess.run(
                [sys.executable, str(rebuild_script)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=1800,
            )

            if result.returncode != 0:
                self.logger.error(f"  ✗ Database rebuild failed: {result.stderr}")
                raise RuntimeError(f"Database rebuild failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"  ✗ Database rebuild error: {e}")
            raise

        # Get updated database stats (after update)
        if local_db.exists():
            try:
                conn = sqlite3.connect(local_db)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM games")
                self.games_after = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM pbp_events")
                self.events_after = cursor.fetchone()[0]

                conn.close()

                games_added = self.games_after - self.games_before
                events_added = self.events_after - self.events_before

                self.logger.info(f"  ✓ Database updated")
                self.logger.info(
                    f"    Added: +{games_added} games, +{events_added} events"
                )
                self.logger.info(
                    f"    New totals: {self.games_after} games, {self.events_after} events"
                )

                # Send Slack notification if significant data added
                if games_added > 0 and self.slack_webhook:
                    self._send_slack_notification(
                        f"Added {games_added} new games ({events_added} events) to local database",
                        level="info",
                    )

                return {
                    "status": "success",
                    "games_added": games_added,
                    "events_added": events_added,
                    "games_total": self.games_after,
                    "events_total": self.events_after,
                }
            except Exception as e:
                self.logger.warning(f"    Could not read updated database stats: {e}")

        return {"status": "success"}

    def _execute_catalog_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute DATA_CATALOG.md update"""
        update_script = Path(params["update_script"])
        catalog_file = Path(params["catalog_file"])

        self.logger.info(f"  Updating DATA_CATALOG.md...")

        # Run catalog update
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(update_script),
                    "--source",
                    "espn",
                    "--action",
                    "update",
                ],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                self.logger.error(f"  ✗ Catalog update failed: {result.stderr}")
                raise RuntimeError(f"Catalog update failed: {result.stderr}")

            self.logger.info(f"  ✓ DATA_CATALOG.md updated successfully")

        except Exception as e:
            self.logger.error(f"  ✗ Catalog update error: {e}")
            raise

        # Verify catalog consistency
        self.logger.info(f"  Verifying catalog consistency...")

        try:
            result = subprocess.run(
                [sys.executable, str(update_script), "--verify"],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                self.logger.info(f"  ✓ Catalog verification passed")
            else:
                self.logger.warning(
                    f"  ⚠ Catalog verification found inconsistencies (may be formatting differences)"
                )

        except Exception as e:
            self.logger.warning(f"  ⚠ Catalog verification error: {e}")

        return {"status": "success"}

    def _execute_git_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute git commit (optional)"""
        catalog_file = Path(params["catalog_file"])
        auto_commit = params["auto_commit"]

        if not auto_commit:
            self.logger.info(f"  Auto-commit disabled, skipping")
            return {"status": "skipped", "reason": "auto_commit_disabled"}

        self.logger.info(f"  Checking for changes to commit...")

        # Check if DATA_CATALOG.md has changes
        try:
            result = subprocess.run(
                ["git", "diff", "--quiet", str(catalog_file)],
                cwd=str(self.project_dir),
                capture_output=True,
            )

            if result.returncode == 0:
                self.logger.info(f"  No changes to DATA_CATALOG.md, skipping commit")
                return {"status": "skipped", "reason": "no_changes"}

        except Exception as e:
            self.logger.error(f"  ✗ Git diff error: {e}")
            return {"status": "error", "error": str(e)}

        # Create commit
        try:
            # Stage changes
            subprocess.run(
                ["git", "add", str(catalog_file)], cwd=str(self.project_dir), check=True
            )

            # Create commit
            commit_msg = f"""chore(data): daily ESPN catalog update {datetime.now().strftime('%Y-%m-%d')}

Automated daily update of ESPN data statistics.

🤖 Generated by daily_update_workflow.py
"""

            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(self.project_dir),
                check=True,
            )

            self.logger.info(f"  ✓ Changes committed successfully")

            return {"status": "success"}

        except Exception as e:
            self.logger.error(f"  ✗ Git commit error: {e}")
            return {"status": "error", "error": str(e)}

    def _execute_cleanup_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cleanup of old logs"""
        log_dir = Path(params["log_dir"])
        retention_days = params["retention_days"]

        self.logger.info(f"  Cleaning up old log files...")

        import time

        cutoff_time = time.time() - (retention_days * 86400)
        deleted_count = 0

        for log_file in log_dir.glob("espn_daily_update_*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"    Could not delete {log_file}: {e}")

        self.logger.info(f"  ✓ Cleanup complete (deleted {deleted_count} old logs)")

        return {"status": "success", "deleted_count": deleted_count}

    def _send_slack_notification(self, message: str, level: str = "info"):
        """Send Slack notification"""
        if not self.slack_webhook:
            return

        emoji_map = {
            "info": ":information_source:",
            "warning": ":warning:",
            "error": ":x:",
        }

        emoji = emoji_map.get(level, ":robot_face:")

        payload = {"text": f"{emoji} NBA Simulator Daily Update: {message}"}

        try:
            requests.post(self.slack_webhook, json=payload, timeout=10)
        except Exception as e:
            self.logger.warning(f"Failed to send Slack notification: {e}")

    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow metadata"""
        return {
            "name": "Daily ESPN Update Workflow",
            "version": "2.0.0",
            "description": "Automated ESPN data collection, database updates, and catalog maintenance",
            "schedule": "Daily at 3:00 AM",
            "migration_from": "daily_espn_update.sh",
            "dependencies": [
                "scripts/db/create_local_espn_database.py",
                "scripts/utils/update_data_catalog.py",
            ],
            "outputs": [
                "Local database (/tmp/espn_local.db)",
                "Data catalog (docs/DATA_CATALOG.md)",
            ],
        }

    def _post_execution(self, success: bool) -> None:
        """Post-execution cleanup and reporting"""
        if success:
            self.logger.info(f"✅ Daily ESPN Update Workflow completed successfully!")
            self.logger.info(
                f"   Games: {self.games_before} → {self.games_after} (+{self.games_after - self.games_before})"
            )
            self.logger.info(
                f"   Events: {self.events_before} → {self.events_after} (+{self.events_after - self.events_before})"
            )

            # Send Slack notification
            if self.slack_webhook:
                runtime_min = int(self.metrics.duration_seconds / 60)
                runtime_sec = int(self.metrics.duration_seconds % 60)
                self._send_slack_notification(
                    f"Daily update completed successfully (runtime: {runtime_min}m {runtime_sec}s)",
                    level="info",
                )
        else:
            self.logger.error(f"❌ Daily ESPN Update Workflow failed")

            # Send Slack notification
            if self.slack_webhook:
                self._send_slack_notification(
                    "Daily update failed - check logs for details", level="error"
                )


# Example usage
if __name__ == "__main__":
    import yaml

    config_file = (
        PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0025_daily_update"
        / "config"
        / "default_config.yaml"
    )

    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    workflow = DailyUpdateWorkflow(config=config)

    if workflow.initialize():
        success = workflow.execute()
        report = workflow.generate_report(format="markdown")
        print(report)
        workflow.shutdown()

        sys.exit(0 if success else 1)
    else:
        print("❌ Workflow initialization failed")
        sys.exit(1)
