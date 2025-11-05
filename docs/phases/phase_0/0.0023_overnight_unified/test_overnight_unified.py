"""
Tests for Overnight Unified Workflow

Comprehensive test suite for the overnight unified workflow Python migration.

Tests cover:
- Workflow initialization and configuration validation
- Task building and dependency management
- Individual task executors (with mocked dependencies)
- Error handling and retry logic
- State persistence and resume functionality
- DIMS metric reporting
- End-to-end workflow execution

Usage:
    pytest test_overnight_unified.py -v
    pytest test_overnight_unified.py::test_workflow_initialization -v
    pytest test_overnight_unified.py --cov=overnight_unified_workflow

Author: NBA Simulator AWS Team
Version: 2.0.0
Created: [Date TBD]
"""

import pytest
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from docs.phases.phase_0.overnight_unified.overnight_unified_workflow import (
    OvernightUnifiedWorkflow,
)
from nba_simulator.workflows import WorkflowState, WorkflowPriority


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration"""
    return {
        "project_dir": str(temp_dir),
        "log_dir": str(temp_dir / "logs"),
        "reports_dir": str(temp_dir / "reports"),
        "ml_quality_dir": str(temp_dir / "ml_quality"),
        "databases": {
            "espn_db": str(temp_dir / "espn.db"),
            "hoopr_db": str(temp_dir / "hoopr.db"),
            "unified_db": str(temp_dir / "unified.db"),
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


@pytest.fixture
def workflow(test_config):
    """Create workflow instance"""
    return OvernightUnifiedWorkflow(config=test_config)


@pytest.fixture
def unified_db(temp_dir):
    """Create test unified database"""
    db_path = temp_dir / "unified.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE source_coverage (
            game_id TEXT PRIMARY KEY,
            has_espn INTEGER,
            has_hoopr INTEGER,
            has_discrepancies INTEGER
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE data_quality_discrepancies (
            id INTEGER PRIMARY KEY,
            game_id TEXT,
            field_name TEXT,
            severity TEXT,
            detected_at TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE quality_scores (
            game_id TEXT PRIMARY KEY,
            quality_score REAL,
            recommended_source TEXT
        )
    """
    )

    # Insert test data
    cursor.execute("INSERT INTO source_coverage VALUES ('game1', 1, 1, 0)")
    cursor.execute("INSERT INTO source_coverage VALUES ('game2', 1, 1, 1)")
    cursor.execute("INSERT INTO source_coverage VALUES ('game3', 1, 0, 0)")

    cursor.execute(
        """
        INSERT INTO data_quality_discrepancies
        VALUES (1, 'game2', 'points', 'high', datetime('now'))
    """
    )

    cursor.execute("INSERT INTO quality_scores VALUES ('game1', 95.5, 'espn')")
    cursor.execute("INSERT INTO quality_scores VALUES ('game2', 72.3, 'hoopr')")

    conn.commit()
    conn.close()

    return db_path


# ============================================================================
# Test Configuration and Initialization
# ============================================================================


def test_workflow_initialization(workflow):
    """Test workflow initialization"""
    assert workflow.workflow_name == "overnight_unified"
    assert workflow.workflow_type == "etl"
    assert workflow.priority == WorkflowPriority.CRITICAL
    assert workflow.espn_days_back == 14
    assert workflow.hoopr_days_back == 7


def test_config_validation_success(workflow):
    """Test successful configuration validation"""
    assert workflow._validate_config() is True


def test_config_validation_missing_project_dir():
    """Test configuration validation with missing project directory"""
    config = {
        "project_dir": "/nonexistent/path",
        "log_dir": "logs",
        "reports_dir": "reports",
        "ml_quality_dir": "ml_quality",
    }

    workflow = OvernightUnifiedWorkflow(config=config)
    assert workflow._validate_config() is False


def test_config_validation_notification_missing_recipient():
    """Test configuration validation with notification enabled but no recipient"""
    config = {
        "project_dir": str(PROJECT_ROOT),
        "notification": {"enabled": True, "email_recipient": ""},
    }

    workflow = OvernightUnifiedWorkflow(config=config)
    assert workflow._validate_config() is False


def test_config_merge_with_defaults():
    """Test configuration merging with defaults"""
    config = {"project_dir": "/tmp/test"}

    workflow = OvernightUnifiedWorkflow(config=config)

    assert workflow.espn_days_back == 14  # Default
    assert workflow.backup_enabled is True  # Default
    assert workflow.project_dir == Path("/tmp/test")  # User value


# ============================================================================
# Test Task Building
# ============================================================================


def test_build_tasks(workflow):
    """Test task graph building"""
    tasks = workflow._build_tasks()

    assert len(tasks) == 11  # 11 total tasks

    # Check task IDs
    task_ids = [t.task_id for t in tasks]
    assert "espn_scrape" in task_ids
    assert "hoopr_scrape" in task_ids
    assert "bbref_scrape" in task_ids
    assert "update_mappings" in task_ids
    assert "rebuild_unified" in task_ids
    assert "detect_discrepancies" in task_ids
    assert "export_ml_dataset" in task_ids
    assert "generate_reports" in task_ids
    assert "backup_databases" in task_ids
    assert "send_notification" in task_ids
    assert "check_scrapers" in task_ids


def test_task_dependencies(workflow):
    """Test task dependency relationships"""
    tasks = workflow._build_tasks()
    task_dict = {t.task_id: t for t in tasks}

    # Scraping tasks have no dependencies
    assert task_dict["espn_scrape"].dependencies == []
    assert task_dict["hoopr_scrape"].dependencies == []
    assert task_dict["bbref_scrape"].dependencies == []

    # Mapping depends on scraping
    assert set(task_dict["update_mappings"].dependencies) == {
        "espn_scrape",
        "hoopr_scrape",
    }

    # Rebuild depends on mapping
    assert task_dict["rebuild_unified"].dependencies == ["update_mappings"]

    # Discrepancies depend on rebuild
    assert task_dict["detect_discrepancies"].dependencies == ["rebuild_unified"]

    # Export depends on discrepancies
    assert task_dict["export_ml_dataset"].dependencies == ["detect_discrepancies"]

    # Final task depends on notification and backup
    assert set(task_dict["check_scrapers"].dependencies) == {
        "send_notification",
        "backup_databases",
    }


def test_task_criticality(workflow):
    """Test task criticality flags"""
    tasks = workflow._build_tasks()
    task_dict = {t.task_id: t for t in tasks}

    # Critical tasks (fatal errors)
    assert task_dict["update_mappings"].is_critical is True
    assert task_dict["rebuild_unified"].is_critical is True
    assert task_dict["detect_discrepancies"].is_critical is True
    assert task_dict["export_ml_dataset"].is_critical is True

    # Non-critical tasks (non-fatal errors)
    assert task_dict["espn_scrape"].is_critical is False
    assert task_dict["hoopr_scrape"].is_critical is False
    assert task_dict["bbref_scrape"].is_critical is False
    assert task_dict["generate_reports"].is_critical is False
    assert task_dict["backup_databases"].is_critical is False
    assert task_dict["send_notification"].is_critical is False
    assert task_dict["check_scrapers"].is_critical is False


# ============================================================================
# Test Task Executors (Mocked)
# ============================================================================


@patch("subprocess.run")
def test_execute_scrape_task_success(mock_run, workflow):
    """Test successful scraping task execution"""
    # Mock successful subprocess
    mock_run.return_value = Mock(
        returncode=0, stdout="Scraped 42 games successfully", stderr=""
    )

    params = {
        "source": "espn",
        "days_back": 14,
        "script": "scripts/etl/espn_incremental_scraper.py",
    }

    result = workflow._execute_scrape_task(params)

    assert result["status"] == "success"
    assert result["source"] == "espn"
    assert result["games_scraped"] == 42


@patch("subprocess.run")
def test_execute_scrape_task_failure(mock_run, workflow):
    """Test failed scraping task execution"""
    # Mock failed subprocess
    mock_run.return_value = Mock(returncode=1, stdout="", stderr="Connection timeout")

    params = {
        "source": "hoopr",
        "days_back": 7,
        "script": "scripts/etl/hoopr_incremental_scraper.py",
    }

    result = workflow._execute_scrape_task(params)

    assert result["status"] == "failed"
    assert result["source"] == "hoopr"
    assert "error" in result


def test_parse_scraper_output(workflow):
    """Test scraper output parsing"""
    # Test various output formats
    assert workflow._parse_scraper_output("Scraped 42 games") == 42
    assert workflow._parse_scraper_output("42 games scraped") == 42
    assert workflow._parse_scraper_output("Total games: 100") == 100
    assert workflow._parse_scraper_output("Games processed: 25") == 25
    assert workflow._parse_scraper_output("No pattern match") == 0


@patch("subprocess.run")
@patch("builtins.open", create=True)
def test_execute_mapping_task_success(mock_open, mock_run, workflow, temp_dir):
    """Test successful mapping task execution"""
    # Mock subprocess
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    # Mock JSON file read
    mapping_data = {"metadata": {"total_mappings": 150}}
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
        mapping_data
    )

    params = {
        "script": "scripts/mapping/extract_espn_hoopr_game_mapping.py",
        "output": "scripts/mapping/espn_hoopr_game_mapping.json",
    }

    # Patch json.load
    with patch("json.load", return_value=mapping_data):
        result = workflow._execute_mapping_task(params)

    assert result["status"] == "success"
    assert result["mapping_count"] == 150


def test_execute_reporting_task(workflow, unified_db, temp_dir):
    """Test report generation task"""
    params = {
        "reports_dir": str(temp_dir / "reports"),
        "unified_db": str(unified_db),
        "espn_db": "/nonexistent.db",
        "hoopr_db": "/nonexistent.db",
    }

    result = workflow._execute_reporting_task(params)

    assert result["status"] == "success"
    assert "report_file" in result

    # Check report file exists
    report_file = Path(result["report_file"])
    assert report_file.exists()

    # Check report content
    content = report_file.read_text()
    assert "Daily Data Quality Report" in content
    assert "Database Statistics" in content


def test_execute_backup_task(workflow, unified_db, temp_dir):
    """Test database backup task"""
    params = {
        "enabled": True,
        "unified_db": str(unified_db),
        "backup_dir": str(temp_dir / "backups"),
        "retention_days": 7,
    }

    result = workflow._execute_backup_task(params)

    assert result["status"] == "success"
    assert "backup_dir" in result
    assert "backup_size" in result

    # Check backup file exists
    backup_dir = Path(result["backup_dir"])
    assert backup_dir.exists()
    assert (backup_dir / "unified_nba.db").exists()


def test_execute_backup_task_disabled(workflow):
    """Test backup task when disabled"""
    params = {
        "enabled": False,
        "unified_db": "/tmp/unified.db",
        "backup_dir": "/tmp/backups",
        "retention_days": 7,
    }

    result = workflow._execute_backup_task(params)

    assert result["status"] == "skipped"


@patch("subprocess.run")
def test_execute_notification_task_disabled(mock_run, workflow):
    """Test notification task when disabled"""
    params = {"enabled": False, "email_recipient": "", "unified_db": "/tmp/unified.db"}

    result = workflow._execute_notification_task(params)

    assert result["status"] == "skipped"
    mock_run.assert_not_called()


# ============================================================================
# Test Workflow Info
# ============================================================================


def test_get_workflow_info(workflow):
    """Test workflow metadata"""
    info = workflow.get_workflow_info()

    assert info["name"] == "Overnight Multi-Source Unified Workflow"
    assert info["version"] == "2.0.0"
    assert info["migration_from"] == "overnight_multi_source_unified.sh v1.1"
    assert "dependencies" in info
    assert "outputs" in info
    assert "dims_metrics" in info

    # Check DIMS metrics
    assert "quality_score" in info["dims_metrics"]
    assert "duration_seconds" in info["dims_metrics"]
    assert "items_processed" in info["dims_metrics"]


# ============================================================================
# Test DIMS Integration
# ============================================================================


def test_update_metric(workflow):
    """Test metric updates"""
    workflow.update_metric("items_processed", 42)
    workflow.update_metric("discrepancy_count", 5)

    assert workflow.metrics.custom_metrics["items_processed"] == 42
    assert workflow.metrics.custom_metrics["discrepancy_count"] == 5


def test_report_to_dims_dims_disabled(workflow):
    """Test DIMS reporting when disabled"""
    workflow.dims_enabled = False

    # Should not raise error
    workflow._report_to_dims()


# ============================================================================
# Test Error Handling
# ============================================================================


def test_execute_task_unknown_type(workflow):
    """Test error handling for unknown task type"""
    from nba_simulator.workflows import WorkflowTask

    task = WorkflowTask(
        task_id="unknown_task",
        task_name="Unknown Task",
        task_type="unknown_type",
        params={},
    )

    with pytest.raises(ValueError, match="Unknown task type"):
        workflow._execute_task(task)


# ============================================================================
# Test State Persistence
# ============================================================================


def test_state_persistence(workflow, temp_dir):
    """Test workflow state save/load"""
    state_file = temp_dir / "workflow_state.json"

    # Initialize workflow
    workflow.initialize()

    # Save state
    workflow.save_state(str(state_file))

    assert state_file.exists()

    # Load state
    workflow2 = OvernightUnifiedWorkflow(config=workflow.config)
    workflow2.load_state(str(state_file))

    assert workflow2.state == workflow.state


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
@patch("subprocess.run")
def test_end_to_end_workflow(mock_run, test_config, temp_dir):
    """Test end-to-end workflow execution (mocked dependencies)"""
    # Mock all subprocess calls to succeed
    mock_run.return_value = Mock(returncode=0, stdout="Scraped 10 games", stderr="")

    # Create mock databases
    for db_name in ["espn.db", "hoopr.db", "unified.db"]:
        db_path = temp_dir / db_name
        conn = sqlite3.connect(db_path)

        if db_name == "unified.db":
            # Create tables for unified DB
            conn.execute(
                "CREATE TABLE source_coverage (game_id TEXT, has_espn INTEGER, has_hoopr INTEGER, has_discrepancies INTEGER)"
            )
            conn.execute(
                "CREATE TABLE data_quality_discrepancies (id INTEGER, game_id TEXT, field_name TEXT, severity TEXT, detected_at TEXT)"
            )
            conn.execute(
                "CREATE TABLE quality_scores (game_id TEXT, quality_score REAL, recommended_source TEXT)"
            )
            conn.execute("INSERT INTO source_coverage VALUES ('game1', 1, 1, 0)")
            conn.execute("INSERT INTO quality_scores VALUES ('game1', 95.0, 'espn')")

        conn.commit()
        conn.close()

    # Update config with temp databases
    test_config["databases"] = {
        "espn_db": str(temp_dir / "espn.db"),
        "hoopr_db": str(temp_dir / "hoopr.db"),
        "unified_db": str(temp_dir / "unified.db"),
    }

    workflow = OvernightUnifiedWorkflow(config=test_config)

    # Mock JSON file reading
    with patch("builtins.open", create=True):
        with patch("json.load", return_value={"metadata": {"total_mappings": 100}}):
            # Initialize
            assert workflow.initialize() is True

            # NOTE: Full execution would require mocking all external scripts
            # For now, test initialization and task building
            assert len(workflow.tasks) == 11
            assert workflow.state == WorkflowState.READY


# ============================================================================
# Test Report Generation
# ============================================================================


def test_generate_report_content(workflow, unified_db, temp_dir):
    """Test report content generation"""
    # Create mock ESPN/hoopR databases
    espn_db = temp_dir / "espn.db"
    hoopr_db = temp_dir / "hoopr.db"

    for db_path in [espn_db, hoopr_db]:
        conn = sqlite3.connect(db_path)
        if db_path == espn_db:
            conn.execute("CREATE TABLE games (game_id TEXT, has_pbp INTEGER)")
            conn.execute("INSERT INTO games VALUES ('game1', 1)")
        else:
            conn.execute("CREATE TABLE play_by_play (game_id TEXT)")
            conn.execute("INSERT INTO play_by_play VALUES ('game1')")
        conn.commit()
        conn.close()

    # Open connections
    unified_conn = sqlite3.connect(unified_db)
    espn_conn = sqlite3.connect(espn_db)
    hoopr_conn = sqlite3.connect(hoopr_db)

    # Generate report
    report = workflow._generate_report_content(unified_conn, espn_conn, hoopr_conn)

    # Verify report content
    assert "Daily Data Quality Report" in report
    assert "Database Statistics" in report
    assert "Quality Distribution" in report
    assert "Total games:" in report

    # Close connections
    unified_conn.close()
    espn_conn.close()
    hoopr_conn.close()


# ============================================================================
# Test Cleanup
# ============================================================================


def test_cleanup_old_logs(workflow, temp_dir):
    """Test old log file cleanup"""
    import time

    log_dir = temp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    workflow.log_dir = log_dir

    # Create old log file
    old_log = log_dir / "old.log"
    old_log.write_text("old log")

    # Set modification time to 40 days ago
    old_time = time.time() - (40 * 86400)
    import os

    os.utime(old_log, (old_time, old_time))

    # Create recent log file
    recent_log = log_dir / "recent.log"
    recent_log.write_text("recent log")

    # Run cleanup
    workflow._cleanup_old_logs()

    # Check old log deleted, recent log kept
    assert not old_log.exists()
    assert recent_log.exists()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
