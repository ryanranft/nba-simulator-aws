"""
3-Source Validation Workflow - Cross-Source Data Quality Checks

Replaces: scripts/workflows/overnight_3_source_validation.sh

This workflow scrapes recent data from 3 sources (ESPN, hoopR, NBA API), then
cross-validates to detect discrepancies. Features graceful degradation - continues
even if sources fail, and skips validation only if too many sources fail.

Usage:
    from validation_workflow import ValidationWorkflow

    workflow = ValidationWorkflow(config=config_dict)
    if workflow.initialize():
        success = workflow.execute()
        workflow.shutdown()

Author: NBA Simulator AWS Team
Version: 2.0.0
Created: [Date TBD]
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from nba_simulator.workflows import (
    BaseWorkflow,
    WorkflowTask,
    WorkflowPriority,
    WorkflowState,
)


class ValidationWorkflow(BaseWorkflow):
    """
    3-source cross-validation workflow.

    Tasks:
    1. Scrape ESPN data (last N days)
    2. Scrape hoopR data (last N days)
    3. Scrape NBA API data (last N days)
    4. Scrape Basketball Reference data (current season)
    5. Cross-validate all sources

    Features graceful degradation - continues even if sources fail.
    Cross-validation requires at least 2 sources to succeed.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the 3-Source Validation Workflow"""
        if config is None:
            config = {}

        config = self._merge_with_defaults(config)

        super().__init__(
            workflow_name="validation",
            workflow_type="validation",
            config=config,
            priority=WorkflowPriority.HIGH,
        )

        self.project_dir = Path(config.get("project_dir", PROJECT_ROOT))
        self.log_dir = Path(
            config.get("log_dir", self.project_dir / "logs" / "overnight")
        )
        self.reports_dir = Path(
            config.get("reports_dir", self.project_dir / "reports" / "validation")
        )

        self.days_back = config.get("scraping", {}).get("days_back", 3)

        self.dims_enabled = config.get("dims", {}).get("enabled", True)

        # Track failed sources
        self.failed_sources = []

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults"""
        defaults = {
            "project_dir": str(PROJECT_ROOT),
            "log_dir": "logs/overnight",
            "reports_dir": "reports/validation",
            "scraping": {"days_back": 3},
            "dims": {"enabled": True},
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

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_error(f"Failed to create directories: {e}")
            return False

        self.logger.info("✓ Configuration validated successfully")
        return True

    def _build_tasks(self) -> List[WorkflowTask]:
        """Build workflow task graph"""
        return [
            # Scraping tasks (parallel - no dependencies, all non-critical)
            WorkflowTask(
                task_id="espn_scrape",
                task_name="Scrape ESPN Data",
                task_type="scrape",
                params={
                    "source": "espn",
                    "days_back": self.days_back,
                    "script": "scripts/etl/espn_incremental_simple.py",
                },
                max_retries=2,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            WorkflowTask(
                task_id="hoopr_scrape",
                task_name="Scrape hoopR Data",
                task_type="scrape",
                params={
                    "source": "hoopr",
                    "days_back": self.days_back,
                    "script": "scripts/etl/hoopr_incremental_simple.py",
                },
                max_retries=2,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            WorkflowTask(
                task_id="nba_api_scrape",
                task_name="Scrape NBA API Data",
                task_type="scrape",
                params={
                    "source": "nba_api",
                    "days_back": self.days_back,
                    "script": "scripts/etl/nba_api_incremental_simple.py",
                },
                max_retries=2,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            WorkflowTask(
                task_id="bbref_scrape",
                task_name="Scrape Basketball Reference Data",
                task_type="scrape",
                params={
                    "source": "basketball_reference",
                    "script": "scripts/etl/basketball_reference_incremental_scraper.py",
                    "upload_to_s3": True,
                },
                max_retries=2,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            # Cross-validation (depends on scraping)
            WorkflowTask(
                task_id="cross_validate",
                task_name="Cross-Validate 3 Sources",
                task_type="validation",
                params={
                    "script": "scripts/validation/cross_validate_3_sources.py",
                    "days_back": self.days_back,
                    "reports_dir": str(self.reports_dir),
                },
                max_retries=1,
                dependencies=[
                    "espn_scrape",
                    "hoopr_scrape",
                    "nba_api_scrape",
                    "bbref_scrape",
                ],
                is_critical=False,  # Non-fatal (may skip if too many sources failed)
            ),
        ]

    def _execute_task(self, task: WorkflowTask) -> Any:
        """Execute a single workflow task"""
        task_type = task.task_type
        params = task.params

        self.logger.info(f"Executing {task_type} task: {task.task_name}")

        if task_type == "scrape":
            return self._execute_scrape_task(params)
        elif task_type == "validation":
            return self._execute_validation_task(params)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _execute_scrape_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scraping task"""
        source = params["source"]
        script = self.project_dir / params["script"]

        self.logger.info(f"  Running {source} scraper: {script}")

        # Build command
        cmd = [sys.executable, str(script)]

        if "days_back" in params:
            cmd.extend(["--days", str(params["days_back"])])
        if params.get("upload_to_s3"):
            cmd.append("--upload-to-s3")

        # Execute
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
            )

            if result.returncode == 0:
                self.logger.info(f"  ✓ {source} scraping complete")
                return {"status": "success", "source": source}
            else:
                self.logger.error(f"  ✗ {source} scraping failed: {result.stderr}")
                self.failed_sources.append(source)
                return {"status": "failed", "source": source, "error": result.stderr}

        except subprocess.TimeoutExpired:
            self.logger.error(f"  ✗ {source} scraping timed out")
            self.failed_sources.append(source)
            return {"status": "timeout", "source": source}
        except Exception as e:
            self.logger.error(f"  ✗ {source} scraping error: {e}")
            self.failed_sources.append(source)
            return {"status": "error", "source": source, "error": str(e)}

    def _execute_validation_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cross-validation task"""
        # Check if too many sources failed
        if len(self.failed_sources) > 2:
            self.logger.error(
                f"  ✗ Too many scraping failures ({len(self.failed_sources)}), skipping cross-validation"
            )
            return {
                "status": "skipped",
                "reason": "too_many_failures",
                "failed_sources": self.failed_sources,
            }

        script = self.project_dir / params["script"]
        reports_dir = Path(params["reports_dir"])

        self.logger.info(f"  Running 3-source cross-validation...")

        # Build command
        cmd = [sys.executable, str(script), "--days", str(params["days_back"])]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                # Find latest validation report
                report_files = sorted(
                    reports_dir.glob("cross_validation_*.json"), reverse=True
                )

                if report_files:
                    with open(report_files[0]) as f:
                        report_data = json.load(f)

                    games_checked = report_data.get("games_checked", 0)
                    discrepancies = len(report_data.get("discrepancies", []))

                    self.logger.info(f"  ✓ Cross-validation complete")
                    self.logger.info(f"    Games validated: {games_checked}")
                    self.logger.info(f"    Discrepancies found: {discrepancies}")

                    # Update DIMS metrics
                    if self.dims_enabled:
                        self.update_metric("games_validated", games_checked)
                        self.update_metric("discrepancies_found", discrepancies)

                    return {
                        "status": "success",
                        "games_checked": games_checked,
                        "discrepancies": discrepancies,
                        "report_file": str(report_files[0]),
                    }
                else:
                    self.logger.warning(f"  ⚠️  No validation report found")
                    return {"status": "success_no_report"}

            else:
                self.logger.error(f"  ✗ Cross-validation failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}

        except Exception as e:
            self.logger.error(f"  ✗ Cross-validation error: {e}")
            return {"status": "error", "error": str(e)}

    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow metadata"""
        return {
            "name": "3-Source Validation Workflow",
            "version": "2.0.0",
            "description": "Cross-validate ESPN, hoopR, and NBA API data sources",
            "schedule": "Daily at 3:00 AM",
            "migration_from": "overnight_3_source_validation.sh v2.0",
            "dependencies": [
                "scripts/etl/espn_incremental_simple.py",
                "scripts/etl/hoopr_incremental_simple.py",
                "scripts/etl/nba_api_incremental_simple.py",
                "scripts/etl/basketball_reference_incremental_scraper.py",
                "scripts/validation/cross_validate_3_sources.py",
            ],
            "outputs": [
                "Validation reports (reports/validation/cross_validation_*.json)"
            ],
            "dims_metrics": [
                "games_validated",
                "discrepancies_found",
                "failed_sources_count",
            ],
        }

    def _post_execution(self, success: bool) -> None:
        """Post-execution cleanup and reporting"""
        if success:
            self.logger.info(f"✅ 3-Source Validation Workflow completed successfully!")
            self.logger.info(f"   Failed sources: {len(self.failed_sources)}")
            if self.failed_sources:
                self.logger.info(
                    f"   Sources that failed: {', '.join(self.failed_sources)}"
                )

            # Report to DIMS
            if self.dims_enabled:
                self.update_metric("failed_sources_count", len(self.failed_sources))
        else:
            self.logger.error(f"❌ 3-Source Validation Workflow failed")


# Example usage
if __name__ == "__main__":
    import yaml

    config_file = (
        PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0024_validation_workflow"
        / "config"
        / "default_config.yaml"
    )

    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    workflow = ValidationWorkflow(config=config)

    if workflow.initialize():
        success = workflow.execute()
        report = workflow.generate_report(format="markdown")
        print(report)
        workflow.shutdown()

        sys.exit(0 if success else 1)
    else:
        print("❌ Workflow initialization failed")
        sys.exit(1)
