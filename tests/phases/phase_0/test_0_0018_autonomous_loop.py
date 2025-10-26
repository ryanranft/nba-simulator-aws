#!/usr/bin/env python3
"""
Test Suite: 0.0018 - Autonomous Loop Controller

Tests for ADCE autonomous loop controller (scripts/autonomous/autonomous_loop.py)

Test Coverage:
- Initialization & configuration: 6 tests
- Signal handling: 2 tests
- Task queue monitoring: 4 tests
- Health checking: 4 tests
- Orchestrator triggering: 4 tests
- Lifecycle management: 4 tests
Total: 24 tests
"""

import sys
import unittest
import tempfile
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.autonomous.autonomous_loop import AutonomousLoop


class TestAutonomousLoopInitialization(unittest.TestCase):
    """Test AutonomousLoop initialization and configuration."""

    def test_initialization_with_defaults(self):
        """Test initialization with default configuration."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            self.assertTrue(loop.dry_run)
            self.assertTrue(loop.running)
            self.assertIsNotNone(loop.config)
            self.assertEqual(loop.state["cycles_completed"], 0)

    def test_initialization_with_custom_config(self):
        """Test initialization with custom config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                "enabled: true\n"
                "reconciliation_interval_hours: 2\n"
                "min_tasks_to_trigger: 1\n"
                "max_orchestrator_runtime_minutes: 120\n"
                "task_queue_file: inventory/gaps.json\n"
                "health_check_port: 8080\n"
            )
            config_path = f.name

        try:
            loop = AutonomousLoop(config_file=config_path, dry_run=True)
            self.assertEqual(loop.config["reconciliation_interval_hours"], 2)
        finally:
            Path(config_path).unlink()

    def test_default_config_values(self):
        """Test default configuration values."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            config = loop.config

            self.assertTrue(config["enabled"])
            self.assertEqual(config["reconciliation_interval_hours"], 1)
            self.assertEqual(config["min_tasks_to_trigger"], 1)
            self.assertEqual(config["max_orchestrator_runtime_minutes"], 120)
            self.assertEqual(config["task_queue_file"], "inventory/gaps.json")
            self.assertEqual(config["health_check_port"], 8080)

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML falls back to defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: :")
            config_path = f.name

        try:
            loop = AutonomousLoop(config_file=config_path, dry_run=True)
            # Should fall back to defaults
            self.assertEqual(loop.config["reconciliation_interval_hours"], 1)
        finally:
            Path(config_path).unlink()

    def test_state_initialization(self):
        """Test initial state structure."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

            self.assertIn("start_time", loop.state)
            self.assertIn("cycles_completed", loop.state)
            self.assertIn("tasks_executed", loop.state)
            self.assertIn("errors", loop.state)
            self.assertIn("status", loop.state)
            self.assertEqual(loop.state["status"], "initializing")
            self.assertEqual(loop.state["cycles_completed"], 0)
            self.assertIsInstance(loop.state["errors"], list)

    def test_stats_initialization(self):
        """Test statistics tracking initialization."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

            # Stats should be defaultdict(int)
            self.assertEqual(loop.stats["orchestrator_success"], 0)
            self.assertEqual(loop.stats["orchestrator_failure"], 0)


class TestSignalHandling(unittest.TestCase):
    """Test signal handling for graceful shutdown."""

    def test_signal_handler_sets_running_false(self):
        """Test signal handler stops the loop."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            self.assertTrue(loop.running)

            # Simulate signal
            loop._signal_handler(15, None)  # SIGTERM

            self.assertFalse(loop.running)
            self.assertEqual(loop.state["status"], "shutting_down")

    def test_signal_handler_updates_state(self):
        """Test signal handler updates state correctly."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.state["status"] = "running"

            loop._signal_handler(2, None)  # SIGINT

            self.assertEqual(loop.state["status"], "shutting_down")


class TestTaskQueueMonitoring(unittest.TestCase):
    """Test task queue monitoring functionality."""

    def test_check_task_queue_file_not_found(self):
        """Test checking task queue when file doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            count = loop._check_task_queue()
            self.assertEqual(count, 0)

    def test_check_task_queue_with_tasks(self):
        """Test checking task queue with tasks available."""
        queue_data = {
            "total_tasks": 5,
            "tasks": ["task1", "task2", "task3", "task4", "task5"],
        }

        # Mock Path.exists() for both initialization and task queue check
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(queue_data))):
                count = loop._check_task_queue()
                self.assertEqual(count, 5)

    def test_check_task_queue_empty(self):
        """Test checking empty task queue."""
        queue_data = {"total_tasks": 0, "tasks": []}

        # Mock Path.exists() for both initialization and task queue check
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(queue_data))):
                count = loop._check_task_queue()
                self.assertEqual(count, 0)

    def test_check_task_queue_invalid_json(self):
        """Test checking task queue with invalid JSON."""
        # Mock Path.exists() for both initialization and task queue check
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                count = loop._check_task_queue()
                self.assertEqual(count, 0)


class TestHealthMonitoring(unittest.TestCase):
    """Test health monitoring functionality."""

    def test_check_health_all_healthy(self):
        """Test health check when all components healthy."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.reconciliation_daemon = Mock()
            loop.reconciliation_daemon.poll.return_value = None  # Still running

            with patch.object(Path, "exists", return_value=True):
                health = loop._check_health()

            self.assertEqual(health["overall_health"], "healthy")
            self.assertIn("components", health)
            self.assertIn("timestamp", health)

    def test_check_health_daemon_stopped(self):
        """Test health check when reconciliation daemon stopped."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.reconciliation_daemon = Mock()
            loop.reconciliation_daemon.poll.return_value = 1  # Exited

            health = loop._check_health()

            self.assertEqual(health["overall_health"], "degraded")
            self.assertEqual(health["components"]["reconciliation_daemon"], "stopped")

    def test_check_health_no_daemon(self):
        """Test health check when daemon not started."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.reconciliation_daemon = None

            health = loop._check_health()

            self.assertEqual(health["overall_health"], "degraded")
            self.assertEqual(
                health["components"]["reconciliation_daemon"], "not_started"
            )

    def test_check_health_orchestrator_running(self):
        """Test health check with orchestrator running."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.orchestrator_process = Mock()
            loop.orchestrator_process.poll.return_value = None  # Still running

            health = loop._check_health()

            self.assertEqual(health["components"]["orchestrator"], "running")


class TestOrchestratorTriggering(unittest.TestCase):
    """Test orchestrator triggering functionality."""

    def test_is_orchestrator_running_none(self):
        """Test orchestrator running check when None."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.orchestrator_process = None
            self.assertFalse(loop._is_orchestrator_running())

    def test_is_orchestrator_running_active(self):
        """Test orchestrator running check when active."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.orchestrator_process = Mock()
            loop.orchestrator_process.poll.return_value = None  # Still running
            self.assertTrue(loop._is_orchestrator_running())

    def test_is_orchestrator_running_finished(self):
        """Test orchestrator running check when finished."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            loop.orchestrator_process = Mock()
            loop.orchestrator_process.poll.return_value = 0  # Exited
            self.assertFalse(loop._is_orchestrator_running())

    def test_trigger_orchestrator_dry_run(self):
        """Test triggering orchestrator in dry run mode."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)
            result = loop._trigger_orchestrator()
            self.assertTrue(result)
            self.assertIsNone(loop.orchestrator_process)


class TestLifecycleManagement(unittest.TestCase):
    """Test autonomous loop lifecycle management."""

    @patch("subprocess.Popen")
    def test_start_reconciliation_daemon_success(self, mock_popen):
        """Test starting reconciliation daemon successfully."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=False)
            result = loop._start_reconciliation_daemon()

            self.assertTrue(result)
            self.assertIsNotNone(loop.reconciliation_daemon)
            self.assertEqual(loop.reconciliation_daemon.pid, 12345)

    @patch("subprocess.Popen")
    def test_start_reconciliation_daemon_fails_immediately(self, mock_popen):
        """Test starting reconciliation daemon that exits immediately."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Exited
        mock_popen.return_value = mock_process

        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=False)
            result = loop._start_reconciliation_daemon()

            self.assertFalse(result)

    def test_shutdown_cleans_up_processes(self):
        """Test shutdown terminates all processes."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

            # Create mock processes
            loop.reconciliation_daemon = Mock()
            loop.reconciliation_daemon.poll.return_value = None  # Running
            loop.orchestrator_process = Mock()
            loop.orchestrator_process.poll.return_value = None  # Running

            loop._shutdown()

            # Verify processes were terminated
            loop.reconciliation_daemon.terminate.assert_called_once()
            loop.orchestrator_process.terminate.assert_called_once()
            self.assertEqual(loop.state["status"], "stopped")

    def test_shutdown_kills_stuck_processes(self):
        """Test shutdown kills processes that don't terminate."""
        with patch.object(Path, "exists", return_value=False):
            loop = AutonomousLoop(dry_run=True)

            # Create mock process that doesn't terminate
            mock_process = Mock()
            mock_process.poll.return_value = None  # Running
            mock_process.wait.side_effect = subprocess.TimeoutExpired(
                "wait", timeout=10
            )  # Simulate timeout
            loop.reconciliation_daemon = mock_process

            loop._shutdown()

            # Verify kill was called
            mock_process.kill.assert_called_once()


def run_tests():
    """Run all test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAutonomousLoopInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskQueueMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestHealthMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestOrchestratorTriggering))
    suite.addTests(loader.loadTestsFromTestCase(TestLifecycleManagement))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
