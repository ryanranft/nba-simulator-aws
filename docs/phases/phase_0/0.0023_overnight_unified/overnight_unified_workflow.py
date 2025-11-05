"""
Overnight Unified Workflow - Multi-Source Data Collection and Quality Tracking

Replaces: scripts/archive/pre_python_migration/overnight_multi_source_unified.sh

This workflow automates nightly data collection from multiple sources (ESPN, hoopR,
Basketball Reference), rebuilds a unified database with quality scores, detects
discrepancies, exports ML-ready datasets, and generates quality reports.

Usage:
    from overnight_unified_workflow import OvernightUnifiedWorkflow

    workflow = OvernightUnifiedWorkflow(config=config_dict)
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
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from nba_simulator.workflows import (
    BaseWorkflow,
    WorkflowTask,
    WorkflowPriority,
    WorkflowState,
)


class OvernightUnifiedWorkflow(BaseWorkflow):
    """
    Nightly multi-source data collection and quality tracking workflow.

    Tasks:
    1. Scrape ESPN data (incremental, last N days)
    2. Scrape hoopR data (incremental, last N days)
    3. Scrape Basketball Reference data (current season)
    4. Update game ID mappings (ESPN ↔ hoopR)
    5. Rebuild unified database with quality scores
    6. Detect data discrepancies across sources
    7. Export ML-ready quality dataset
    8. Generate quality reports (Markdown)
    9. Backup databases
    10. Send notifications (optional)
    11. Check/recover long-running scrapers
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Overnight Unified Workflow.

        Args:
            config: Workflow configuration dictionary
        """
        # Set defaults
        if config is None:
            config = {}

        # Merge with defaults
        config = self._merge_with_defaults(config)

        super().__init__(
            workflow_name="overnight_unified",
            workflow_type="etl",
            config=config,
            priority=WorkflowPriority.CRITICAL,  # Nightly run
        )

        # Workflow-specific attributes
        self.project_dir = Path(config.get("project_dir", PROJECT_ROOT))
        self.log_dir = Path(
            config.get("log_dir", self.project_dir / "logs" / "overnight")
        )
        self.reports_dir = Path(config.get("reports_dir", self.project_dir / "reports"))
        self.ml_quality_dir = Path(
            config.get("ml_quality_dir", self.project_dir / "data" / "ml_quality")
        )

        # Database paths
        self.espn_db = Path(
            config.get("databases", {}).get("espn_db", "/tmp/espn_local.db")
        )
        self.hoopr_db = Path(
            config.get("databases", {}).get("hoopr_db", "/tmp/hoopr_local.db")
        )
        self.unified_db = Path(
            config.get("databases", {}).get("unified_db", "/tmp/unified_nba.db")
        )

        # Scraping parameters
        self.espn_days_back = config.get("scraping", {}).get("espn_days_back", 14)
        self.hoopr_days_back = config.get("scraping", {}).get("hoopr_days_back", 7)
        self.bbref_season = config.get("scraping", {}).get(
            "basketball_reference_season", "current"
        )

        # Notification settings
        self.notification_enabled = config.get("notification", {}).get("enabled", False)
        self.email_recipient = config.get("notification", {}).get("email_recipient", "")

        # Backup settings
        self.backup_enabled = config.get("backup", {}).get("enabled", True)
        self.backup_retention_days = config.get("backup", {}).get("retention_days", 7)

        # Cleanup settings
        self.log_retention_days = config.get("cleanup", {}).get(
            "log_retention_days", 30
        )

        # DIMS integration
        self.dims_enabled = config.get("dims", {}).get("enabled", True)
        self.dims_report_metrics = config.get("dims", {}).get("report_metrics", True)

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with default configuration"""
        defaults = {
            "project_dir": str(PROJECT_ROOT),
            "log_dir": "logs/overnight",
            "reports_dir": "reports",
            "ml_quality_dir": "data/ml_quality",
            "databases": {
                "espn_db": "/tmp/espn_local.db",
                "hoopr_db": "/tmp/hoopr_local.db",
                "unified_db": "/tmp/unified_nba.db",
            },
            "scraping": {
                "espn_days_back": 14,
                "hoopr_days_back": 7,
                "basketball_reference_season": "current",
            },
            "notification": {"enabled": False, "email_recipient": ""},
            "backup": {"enabled": True, "retention_days": 7},
            "cleanup": {"log_retention_days": 30},
            "dims": {"enabled": True, "report_metrics": True},
        }

        # Deep merge
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in config[key]:
                        config[key][subkey] = subvalue

        return config

    def _validate_config(self) -> bool:
        """
        Validate workflow configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required paths exist
        if not self.project_dir.exists():
            self.log_error(f"Project directory does not exist: {self.project_dir}")
            return False

        # Create directories if they don't exist
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            self.ml_quality_dir.mkdir(parents=True, exist_ok=True)
            (self.project_dir / "backups").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_error(f"Failed to create directories: {e}")
            return False

        # Check required scripts exist
        required_scripts = [
            "scripts/etl/espn_incremental_scraper.py",
            "scripts/etl/hoopr_incremental_scraper.py",
            "scripts/etl/basketball_reference_incremental_scraper.py",
            "scripts/mapping/extract_espn_hoopr_game_mapping.py",
            "scripts/etl/build_unified_database.py",
            "scripts/validation/detect_data_discrepancies.py",
            "scripts/validation/export_ml_quality_dataset.py",
        ]

        for script in required_scripts:
            script_path = self.project_dir / script
            if not script_path.exists():
                self.log_warning(f"Required script not found: {script}")
                # Note: We log a warning but don't fail validation
                # Scripts may be reorganized or renamed

        # Validate notification config
        if self.notification_enabled and not self.email_recipient:
            self.log_error("Notification enabled but no email recipient configured")
            return False

        self.logger.info("✓ Configuration validated successfully")
        return True

    def _build_tasks(self) -> List[WorkflowTask]:
        """
        Build workflow task graph.

        Returns:
            List of WorkflowTask objects with dependencies
        """
        return [
            # Scraping tasks (parallel - no dependencies)
            WorkflowTask(
                task_id="espn_scrape",
                task_name="Scrape ESPN Data",
                task_type="scrape",
                params={
                    "source": "espn",
                    "days_back": self.espn_days_back,
                    "script": "scripts/etl/espn_incremental_scraper.py",
                },
                max_retries=3,
                retry_delay_seconds=60,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            WorkflowTask(
                task_id="hoopr_scrape",
                task_name="Scrape hoopR Data",
                task_type="scrape",
                params={
                    "source": "hoopr",
                    "days_back": self.hoopr_days_back,
                    "script": "scripts/etl/hoopr_incremental_scraper.py",
                },
                max_retries=3,
                retry_delay_seconds=60,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            WorkflowTask(
                task_id="bbref_scrape",
                task_name="Scrape Basketball Reference Data",
                task_type="scrape",
                params={
                    "source": "basketball_reference",
                    "season": self.bbref_season,
                    "script": "scripts/etl/basketball_reference_incremental_scraper.py",
                    "upload_to_s3": True,
                },
                max_retries=3,
                retry_delay_seconds=60,
                dependencies=[],
                is_critical=False,  # Non-fatal
            ),
            # Mapping task (depends on scraping)
            WorkflowTask(
                task_id="update_mappings",
                task_name="Update Game ID Mappings",
                task_type="mapping",
                params={
                    "script": "scripts/mapping/extract_espn_hoopr_game_mapping.py",
                    "output": "scripts/mapping/espn_hoopr_game_mapping.json",
                },
                max_retries=2,
                dependencies=["espn_scrape", "hoopr_scrape"],
                is_critical=True,  # Fatal error
            ),
            # Database rebuild (depends on mapping)
            WorkflowTask(
                task_id="rebuild_unified",
                task_name="Rebuild Unified Database",
                task_type="database",
                params={
                    "script": "scripts/etl/build_unified_database.py",
                    "source_dbs": [str(self.espn_db), str(self.hoopr_db)],
                    "unified_db": str(self.unified_db),
                },
                max_retries=2,
                dependencies=["update_mappings"],
                is_critical=True,  # Fatal error
            ),
            # Discrepancy detection (depends on unified DB)
            WorkflowTask(
                task_id="detect_discrepancies",
                task_name="Detect Data Discrepancies",
                task_type="validation",
                params={
                    "script": "scripts/validation/detect_data_discrepancies.py",
                    "unified_db": str(self.unified_db),
                },
                max_retries=2,
                dependencies=["rebuild_unified"],
                is_critical=True,  # Fatal error
            ),
            # Export ML dataset (depends on discrepancies)
            WorkflowTask(
                task_id="export_ml_dataset",
                task_name="Export ML Quality Dataset",
                task_type="export",
                params={
                    "script": "scripts/validation/export_ml_quality_dataset.py",
                    "output_dir": str(self.ml_quality_dir),
                },
                max_retries=2,
                dependencies=["detect_discrepancies"],
                is_critical=True,  # Fatal error
            ),
            # Generate reports (depends on discrepancies)
            WorkflowTask(
                task_id="generate_reports",
                task_name="Generate Quality Reports",
                task_type="reporting",
                params={
                    "reports_dir": str(self.reports_dir),
                    "unified_db": str(self.unified_db),
                    "espn_db": str(self.espn_db),
                    "hoopr_db": str(self.hoopr_db),
                },
                max_retries=1,
                dependencies=["detect_discrepancies"],
                is_critical=False,  # Non-fatal
            ),
            # Backup databases (depends on rebuild)
            WorkflowTask(
                task_id="backup_databases",
                task_name="Backup Databases",
                task_type="backup",
                params={
                    "unified_db": str(self.unified_db),
                    "backup_dir": str(self.project_dir / "backups"),
                    "retention_days": self.backup_retention_days,
                    "enabled": self.backup_enabled,
                },
                max_retries=1,
                dependencies=["rebuild_unified"],
                is_critical=False,  # Non-fatal
            ),
            # Send notification (depends on ML dataset and reports)
            WorkflowTask(
                task_id="send_notification",
                task_name="Send Completion Notification",
                task_type="notification",
                params={
                    "enabled": self.notification_enabled,
                    "email_recipient": self.email_recipient,
                    "unified_db": str(self.unified_db),
                },
                max_retries=1,
                dependencies=["export_ml_dataset", "generate_reports"],
                is_critical=False,  # Non-fatal
            ),
            # Check long-running scrapers (final task)
            WorkflowTask(
                task_id="check_scrapers",
                task_name="Check Long-Running Scrapers",
                task_type="monitoring",
                params={"script": "scripts/monitoring/check_and_recover_scrapers.sh"},
                max_retries=1,
                dependencies=["send_notification", "backup_databases"],
                is_critical=False,  # Non-fatal
            ),
        ]

    def _execute_task(self, task: WorkflowTask) -> Any:
        """
        Execute a single workflow task.

        Args:
            task: WorkflowTask to execute

        Returns:
            Task execution result (dict with status, output, etc.)
        """
        task_type = task.task_type
        params = task.params

        self.logger.info(f"Executing {task_type} task: {task.task_name}")

        if task_type == "scrape":
            return self._execute_scrape_task(params)
        elif task_type == "mapping":
            return self._execute_mapping_task(params)
        elif task_type == "database":
            return self._execute_database_task(params)
        elif task_type == "validation":
            return self._execute_validation_task(params)
        elif task_type == "export":
            return self._execute_export_task(params)
        elif task_type == "reporting":
            return self._execute_reporting_task(params)
        elif task_type == "backup":
            return self._execute_backup_task(params)
        elif task_type == "notification":
            return self._execute_notification_task(params)
        elif task_type == "monitoring":
            return self._execute_monitoring_task(params)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _execute_scrape_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scraping task by calling Python scrapers.

        Args:
            params: Task parameters (source, days_back, script)

        Returns:
            Dict with status, games_scraped, etc.
        """
        source = params["source"]
        script = self.project_dir / params["script"]

        self.logger.info(f"  Running {source} scraper: {script}")

        # Build command
        cmd = [sys.executable, str(script)]

        # Add arguments
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
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode == 0:
                # Parse output for metrics
                games_scraped = self._parse_scraper_output(result.stdout)

                self.logger.info(
                    f"  ✓ {source} scraping complete ({games_scraped} games)"
                )
                self.update_metric("items_processed", games_scraped)

                return {
                    "status": "success",
                    "source": source,
                    "games_scraped": games_scraped,
                    "output": result.stdout,
                }
            else:
                self.logger.error(f"  ✗ {source} scraping failed: {result.stderr}")
                return {"status": "failed", "source": source, "error": result.stderr}

        except subprocess.TimeoutExpired:
            self.logger.error(f"  ✗ {source} scraping timed out (>1 hour)")
            return {"status": "timeout", "source": source}
        except Exception as e:
            self.logger.error(f"  ✗ {source} scraping error: {e}")
            return {"status": "error", "source": source, "error": str(e)}

    def _parse_scraper_output(self, output: str) -> int:
        """
        Parse scraper output to extract games scraped count.

        Args:
            output: Scraper stdout

        Returns:
            Number of games scraped (0 if not found)
        """
        # Look for patterns like "Scraped 42 games" or "42 games scraped"
        import re

        patterns = [
            r"Scraped (\d+) games",
            r"(\d+) games scraped",
            r"Total games: (\d+)",
            r"Games processed: (\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    def _execute_mapping_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute game ID mapping extraction"""
        script = self.project_dir / params["script"]

        self.logger.info(f"  Extracting ESPN-hoopR game ID mappings...")

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                # Read mapping file
                mapping_file = self.project_dir / params["output"]
                with open(mapping_file) as f:
                    mapping_data = json.load(f)

                mapping_count = mapping_data.get("metadata", {}).get(
                    "total_mappings", 0
                )

                self.logger.info(
                    f"  ✓ Mapping extraction complete ({mapping_count} mappings)"
                )

                return {"status": "success", "mapping_count": mapping_count}
            else:
                self.logger.error(f"  ✗ Mapping extraction failed: {result.stderr}")
                raise RuntimeError(f"Mapping extraction failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"  ✗ Mapping extraction error: {e}")
            raise

    def _execute_database_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute unified database rebuild"""
        script = self.project_dir / params["script"]
        unified_db = params["unified_db"]

        self.logger.info(f"  Rebuilding unified database...")

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
            )

            if result.returncode == 0:
                # Query game count
                conn = sqlite3.connect(unified_db)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM source_coverage")
                game_count = cursor.fetchone()[0]
                conn.close()

                self.logger.info(f"  ✓ Unified database rebuilt ({game_count} games)")

                return {"status": "success", "game_count": game_count}
            else:
                self.logger.error(f"  ✗ Database rebuild failed: {result.stderr}")
                raise RuntimeError(f"Database rebuild failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"  ✗ Database rebuild error: {e}")
            raise

    def _execute_validation_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discrepancy detection"""
        script = self.project_dir / params["script"]
        unified_db = params["unified_db"]

        self.logger.info(f"  Detecting data discrepancies...")

        try:
            # Clear existing discrepancies
            conn = sqlite3.connect(unified_db)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM data_quality_discrepancies")
            conn.commit()
            conn.close()

            self.logger.info(f"  Cleared existing discrepancies")

            # Run discrepancy detection
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes
            )

            if result.returncode == 0:
                # Query discrepancy counts
                conn = sqlite3.connect(unified_db)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM data_quality_discrepancies")
                disc_count = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(DISTINCT game_id) FROM data_quality_discrepancies"
                )
                games_with_disc = cursor.fetchone()[0]

                conn.close()

                self.logger.info(f"  ✓ Discrepancy detection complete")
                self.logger.info(f"    Total discrepancies: {disc_count}")
                self.logger.info(f"    Games with discrepancies: {games_with_disc}")

                # Update DIMS metrics
                if self.dims_enabled:
                    self.update_metric("discrepancy_count", disc_count)

                return {
                    "status": "success",
                    "disc_count": disc_count,
                    "games_with_disc": games_with_disc,
                }
            else:
                self.logger.error(f"  ✗ Discrepancy detection failed: {result.stderr}")
                raise RuntimeError(f"Discrepancy detection failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"  ✗ Discrepancy detection error: {e}")
            raise

    def _execute_export_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ML quality dataset export"""
        script = self.project_dir / params["script"]
        output_dir = Path(params["output_dir"])

        self.logger.info(f"  Exporting ML quality dataset...")

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                # Find most recent output files
                json_files = sorted(
                    output_dir.glob("ml_quality_dataset_*.json"), reverse=True
                )
                csv_files = sorted(
                    output_dir.glob("ml_quality_dataset_*.csv"), reverse=True
                )

                json_size = json_files[0].stat().st_size if json_files else 0
                csv_size = csv_files[0].stat().st_size if csv_files else 0

                self.logger.info(f"  ✓ ML quality dataset exported")
                self.logger.info(f"    JSON: {json_size / 1024:.1f} KB")
                self.logger.info(f"    CSV: {csv_size / 1024:.1f} KB")

                # Update DIMS metrics
                if self.dims_enabled:
                    self.update_metric("ml_dataset_size", json_size + csv_size)

                return {
                    "status": "success",
                    "json_size": json_size,
                    "csv_size": csv_size,
                }
            else:
                self.logger.error(f"  ✗ ML dataset export failed: {result.stderr}")
                raise RuntimeError(f"ML dataset export failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"  ✗ ML dataset export error: {e}")
            raise

    def _execute_reporting_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quality reports (Markdown)"""
        reports_dir = Path(params["reports_dir"])
        unified_db = params["unified_db"]
        espn_db = params["espn_db"]
        hoopr_db = params["hoopr_db"]

        self.logger.info(f"  Generating quality report...")

        try:
            report_file = (
                reports_dir
                / f"daily_quality_report_{datetime.now().strftime('%Y%m%d')}.md"
            )

            # Connect to databases
            unified_conn = sqlite3.connect(unified_db)
            espn_conn = sqlite3.connect(espn_db) if Path(espn_db).exists() else None
            hoopr_conn = sqlite3.connect(hoopr_db) if Path(hoopr_db).exists() else None

            # Generate report content
            report_content = self._generate_report_content(
                unified_conn, espn_conn, hoopr_conn
            )

            # Write report
            with open(report_file, "w") as f:
                f.write(report_content)

            # Close connections
            unified_conn.close()
            if espn_conn:
                espn_conn.close()
            if hoopr_conn:
                hoopr_conn.close()

            self.logger.info(f"  ✓ Quality report generated: {report_file}")

            return {"status": "success", "report_file": str(report_file)}

        except Exception as e:
            self.logger.error(f"  ✗ Report generation error: {e}")
            # Non-fatal - log but continue
            return {"status": "failed", "error": str(e)}

    def _generate_report_content(
        self,
        unified_conn: sqlite3.Connection,
        espn_conn: Optional[sqlite3.Connection],
        hoopr_conn: Optional[sqlite3.Connection],
    ) -> str:
        """Generate Markdown report content"""

        # Query statistics
        cursor = unified_conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM source_coverage")
        total_games = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 1"
        )
        dual_source_games = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM source_coverage WHERE has_discrepancies = 1"
        )
        games_with_disc = cursor.fetchone()[0]

        # ESPN games
        espn_games = "N/A"
        if espn_conn:
            cursor = espn_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM games WHERE has_pbp = 1")
            espn_games = cursor.fetchone()[0]

        # hoopR games
        hoopr_games = "N/A"
        if hoopr_conn:
            cursor = hoopr_conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT game_id) FROM play_by_play")
            hoopr_games = cursor.fetchone()[0]

        # Quality distribution
        cursor = unified_conn.cursor()
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN quality_score >= 90 THEN 'High (90-100)'
                    WHEN quality_score >= 70 THEN 'Medium (70-89)'
                    ELSE 'Low (<70)'
                END as quality,
                COUNT(*) as games,
                ROUND(AVG(quality_score), 1) as avg_score
            FROM quality_scores
            GROUP BY quality
            ORDER BY avg_score DESC
        """
        )
        quality_dist = cursor.fetchall()

        # Recent discrepancies
        cursor.execute(
            """
            SELECT
                field_name,
                COUNT(*) as count,
                severity
            FROM data_quality_discrepancies
            WHERE detected_at > datetime('now', '-1 day')
            GROUP BY field_name, severity
            ORDER BY count DESC
            LIMIT 10
        """
        )
        recent_disc = cursor.fetchall()

        # Source recommendations
        cursor.execute(
            """
            SELECT
                recommended_source,
                COUNT(*) as games
            FROM quality_scores
            GROUP BY recommended_source
            ORDER BY games DESC
        """
        )
        source_recs = cursor.fetchall()

        # Build report
        report = f"""# Daily Data Quality Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Database Statistics

### Source Databases
- **ESPN:** {espn_games} games
- **hoopR:** {hoopr_games} games

### Unified Database
- **Total games:** {total_games}
- **Dual-source games:** {dual_source_games}
- **Games with discrepancies:** {games_with_disc}

## Quality Distribution

```
{"Quality Level".ljust(20)} {"Games".ljust(10)} {"Avg Score".ljust(10)}
{"-" * 40}
"""

        for quality, games, avg_score in quality_dist:
            report += f"{quality.ljust(20)} {str(games).ljust(10)} {str(avg_score).ljust(10)}\n"

        report += """```

## Recent Discrepancies

```
{"Field Name".ljust(25)} {"Count".ljust(10)} {"Severity".ljust(10)}
{"-" * 45}
"""

        for field, count, severity in recent_disc:
            report += f"{field.ljust(25)} {str(count).ljust(10)} {severity.ljust(10)}\n"

        report += """```

## Source Recommendations

```
{"Source".ljust(20)} {"Games".ljust(10)}
{"-" * 30}
"""

        for source, games in source_recs:
            report += f"{source.ljust(20)} {str(games).ljust(10)}\n"

        report += f"""```

---

**Next Steps:**
- Review discrepancies in high-severity games
- Monitor quality score trends
- Validate new data additions

**Log File:** {self.log_dir / f"overnight_unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"}
"""

        return report

    def _execute_backup_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Backup databases"""
        if not params.get("enabled"):
            self.logger.info(f"  Backup disabled, skipping")
            return {"status": "skipped"}

        unified_db = Path(params["unified_db"])
        backup_dir = Path(params["backup_dir"]) / datetime.now().strftime("%Y%m%d")
        retention_days = params["retention_days"]

        self.logger.info(f"  Backing up databases to: {backup_dir}")

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup unified database
            if unified_db.exists():
                import shutil

                shutil.copy2(unified_db, backup_dir / "unified_nba.db")
                self.logger.info(f"  ✓ Unified database backed up")

            # Clean old backups
            import time

            cutoff_time = time.time() - (retention_days * 86400)

            for backup_subdir in backup_dir.parent.glob("*"):
                if (
                    backup_subdir.is_dir()
                    and backup_subdir.stat().st_mtime < cutoff_time
                ):
                    import shutil

                    shutil.rmtree(backup_subdir)

            self.logger.info(
                f"  ✓ Old backups cleaned (kept last {retention_days} days)"
            )

            # Calculate backup size
            backup_size = sum(
                f.stat().st_size for f in backup_dir.glob("*") if f.is_file()
            )

            # Update DIMS metrics
            if self.dims_enabled:
                self.update_metric("backup_size", backup_size)

            return {
                "status": "success",
                "backup_dir": str(backup_dir),
                "backup_size": backup_size,
            }

        except Exception as e:
            self.logger.error(f"  ✗ Backup error: {e}")
            # Non-fatal - log but continue
            return {"status": "failed", "error": str(e)}

    def _execute_notification_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send completion notification via email"""
        if not params.get("enabled"):
            self.logger.info(f"  Email notification disabled, skipping")
            return {"status": "skipped"}

        email_recipient = params["email_recipient"]
        unified_db = params["unified_db"]

        self.logger.info(f"  Sending email notification to: {email_recipient}")

        try:
            # Query summary statistics
            conn = sqlite3.connect(unified_db)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM source_coverage")
            total_games = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 1"
            )
            dual_source = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT game_id) FROM data_quality_discrepancies"
            )
            discrepancies = cursor.fetchone()[0]

            conn.close()

            # Build email
            subject = f"NBA Simulator: Overnight Workflow Complete - {datetime.now().strftime('%Y-%m-%d')}"
            body = f"""Overnight multi-source unified database workflow completed successfully.

Summary:
- Total games: {total_games}
- Dual-source: {dual_source}
- Discrepancies: {discrepancies}

Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Log file: {self.log_dir}
"""

            # Send email using mail command (macOS)
            subprocess.run(
                ["mail", "-s", subject, email_recipient],
                input=body.encode(),
                timeout=30,
            )

            self.logger.info(f"  ✓ Email sent")

            return {"status": "success", "recipient": email_recipient}

        except Exception as e:
            self.logger.error(f"  ✗ Email notification error: {e}")
            # Non-fatal - log but continue
            return {"status": "failed", "error": str(e)}

    def _execute_monitoring_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check and recover long-running scrapers"""
        script = self.project_dir / params["script"]

        if not script.exists():
            self.logger.warning(f"  Scraper health check script not found, skipping")
            return {"status": "skipped"}

        self.logger.info(f"  Checking health of long-running scrapers...")

        try:
            result = subprocess.run(
                ["bash", str(script)],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                self.logger.info(f"  ✓ All long-running scrapers healthy or recovered")
                return {"status": "success", "output": result.stdout}
            else:
                self.logger.warning(
                    f"  ⚠️ Some scraper recovery attempts failed (non-fatal)"
                )
                return {
                    "status": "partial",
                    "output": result.stdout,
                    "error": result.stderr,
                }

        except Exception as e:
            self.logger.error(f"  ✗ Scraper health check error: {e}")
            # Non-fatal - log but continue
            return {"status": "failed", "error": str(e)}

    def get_workflow_info(self) -> Dict[str, Any]:
        """Get workflow metadata"""
        return {
            "name": "Overnight Multi-Source Unified Workflow",
            "version": "2.0.0",
            "description": "Nightly data collection, quality tracking, and unified database maintenance",
            "schedule": "Daily at 3:00 AM",
            "migration_from": "overnight_multi_source_unified.sh v1.1",
            "dependencies": [
                "scripts/etl/espn_incremental_scraper.py",
                "scripts/etl/hoopr_incremental_scraper.py",
                "scripts/etl/basketball_reference_incremental_scraper.py",
                "scripts/mapping/extract_espn_hoopr_game_mapping.py",
                "scripts/etl/build_unified_database.py",
                "scripts/validation/detect_data_discrepancies.py",
                "scripts/validation/export_ml_quality_dataset.py",
            ],
            "outputs": [
                "Unified database (/tmp/unified_nba.db)",
                "Quality reports (reports/daily_quality_report_YYYYMMDD.md)",
                "ML datasets (data/ml_quality/ml_quality_dataset_*)",
                "Database backups (backups/YYYYMMDD/)",
            ],
            "dims_metrics": [
                "quality_score",
                "duration_seconds",
                "items_processed",
                "discrepancy_count",
                "ml_dataset_size",
                "backup_size",
            ],
        }

    def _post_execution(self, success: bool) -> None:
        """Post-execution cleanup and reporting"""
        if success:
            self.logger.info(f"✅ Overnight Unified Workflow completed successfully!")
            self.logger.info(f"   Quality score: {self.metrics.quality_score:.1f}%")
            self.logger.info(f"   Duration: {self.metrics.duration_seconds:.2f}s")
            self.logger.info(
                f"   Items processed: {self.metrics.custom_metrics.get('items_processed', 0)}"
            )

            # Report to DIMS
            if self.dims_enabled and self.dims_report_metrics:
                self._report_to_dims()
        else:
            self.logger.error(f"❌ Overnight Unified Workflow failed")
            self.logger.error(f"   Check logs for details: {self.log_dir}")

        # Cleanup old logs
        self._cleanup_old_logs()

    def _report_to_dims(self) -> None:
        """Report metrics to DIMS"""
        try:
            # Import DIMS CLI
            dims_cli = self.project_dir / "scripts" / "monitoring" / "dims_cli.py"

            if dims_cli.exists():
                # Build metrics payload
                metrics = {
                    "workflow_name": "overnight_unified",
                    "timestamp": datetime.now().isoformat(),
                    "quality_score": self.metrics.quality_score,
                    "duration_seconds": self.metrics.duration_seconds,
                    "success_rate": self.metrics.success_rate,
                    "items_processed": self.metrics.custom_metrics.get(
                        "items_processed", 0
                    ),
                    "discrepancy_count": self.metrics.custom_metrics.get(
                        "discrepancy_count", 0
                    ),
                    "ml_dataset_size": self.metrics.custom_metrics.get(
                        "ml_dataset_size", 0
                    ),
                    "backup_size": self.metrics.custom_metrics.get("backup_size", 0),
                }

                # Call DIMS CLI (placeholder - actual implementation depends on DIMS interface)
                self.logger.info(f"  Reporting metrics to DIMS: {metrics}")

                # TODO: Implement actual DIMS metric reporting
                # subprocess.run([sys.executable, str(dims_cli), "report", json.dumps(metrics)])

        except Exception as e:
            self.logger.warning(f"  Failed to report metrics to DIMS: {e}")

    def _cleanup_old_logs(self) -> None:
        """Clean up old log files"""
        try:
            import time

            cutoff_time = time.time() - (self.log_retention_days * 86400)

            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()

            self.logger.info(
                f"  ✓ Old logs cleaned (kept last {self.log_retention_days} days)"
            )

        except Exception as e:
            self.logger.warning(f"  Failed to clean old logs: {e}")


# Example usage
if __name__ == "__main__":
    import yaml

    # Load configuration
    config_file = (
        PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0023_overnight_unified"
        / "config"
        / "default_config.yaml"
    )

    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    # Create workflow
    workflow = OvernightUnifiedWorkflow(config=config)

    # Run workflow
    if workflow.initialize():
        success = workflow.execute()
        report = workflow.generate_report(format="markdown")
        print(report)
        workflow.shutdown()

        sys.exit(0 if success else 1)
    else:
        print("❌ Workflow initialization failed")
        sys.exit(1)
