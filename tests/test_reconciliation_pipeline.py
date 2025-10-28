#!/usr/bin/env python3
"""
Unit and Integration Tests for Reconciliation Pipeline

Tests the enhanced reconciliation pipeline with error recovery,
health checks, and performance monitoring.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.reconciliation.run_reconciliation import ReconciliationPipeline


class TestReconciliationPipeline:
    """Test suite for ReconciliationPipeline"""

    def test_initialization_with_config(self, tmp_path):
        """Test pipeline initializes with config file"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
s3:
  bucket: test-bucket
  sample_rate: 0.1
performance:
  full_cycle_max_minutes: 5
"""
        )

        pipeline = ReconciliationPipeline(str(config_file))

        assert pipeline.config["s3"]["bucket"] == "test-bucket"
        assert pipeline.config["s3"]["sample_rate"] == 0.1

    def test_initialization_without_config(self):
        """Test pipeline uses defaults when config missing"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        assert pipeline.config["s3"]["bucket"] == "nba-sim-raw-data-lake"
        assert "retry" in pipeline.config
        assert "health_checks" in pipeline.config

    def test_default_config_structure(self):
        """Test default config has all required keys"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")
        config = pipeline.config

        # Check all required sections exist
        assert "s3" in config
        assert "performance" in config
        assert "dry_run" in config
        assert "retry" in config
        assert "health_checks" in config

        # Check retry configuration
        assert config["retry"]["max_attempts"] == 3
        assert config["retry"]["backoff_seconds"] == 5

        # Check health check configuration
        assert config["health_checks"]["enabled"] is True
        assert config["health_checks"]["fail_fast"] is False

    @patch("scripts.reconciliation.run_reconciliation.boto3")
    @patch("scripts.reconciliation.run_reconciliation.psutil")
    def test_health_checks_all_pass(self, mock_psutil, mock_boto3):
        """Test health checks when all checks pass"""
        # Mock AWS credentials check
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789"}
        mock_boto3.client.return_value = mock_sts

        # Mock disk usage
        mock_disk = MagicMock()
        mock_disk.free = 10 * (1024**3)  # 10 GB free
        mock_psutil.disk_usage.return_value = mock_disk

        pipeline = ReconciliationPipeline("nonexistent.yaml")
        success, issues = pipeline._run_health_checks()

        assert success is True
        assert len(issues) == 0

    @patch("scripts.reconciliation.run_reconciliation.boto3")
    @patch("scripts.reconciliation.run_reconciliation.psutil")
    def test_health_checks_low_disk_space(self, mock_psutil, mock_boto3):
        """Test health checks detect low disk space"""
        # Mock AWS credentials check
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789"}
        mock_boto3.client.return_value = mock_sts

        # Mock low disk space (500 MB)
        mock_disk = MagicMock()
        mock_disk.free = 0.5 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        pipeline = ReconciliationPipeline("nonexistent.yaml")
        success, issues = pipeline._run_health_checks()

        assert success is False
        assert any("Low disk space" in issue for issue in issues)

    @patch("scripts.reconciliation.run_reconciliation.boto3")
    def test_health_checks_s3_failure(self, mock_boto3):
        """Test health checks detect S3 access failure"""
        # Mock AWS STS success
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789"}

        # Mock S3 failure
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = Exception("Access denied")

        def boto3_client(service_name):
            if service_name == "sts":
                return mock_sts
            elif service_name == "s3":
                return mock_s3

        mock_boto3.client.side_effect = boto3_client

        pipeline = ReconciliationPipeline("nonexistent.yaml")
        success, issues = pipeline._run_health_checks()

        assert success is False
        assert any("S3 bucket access failed" in issue for issue in issues)

    def test_retry_with_backoff_success_first_attempt(self):
        """Test retry logic succeeds on first attempt"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        mock_func = Mock(return_value="success")
        result = pipeline._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_with_backoff_success_second_attempt(self):
        """Test retry logic succeeds on second attempt"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        mock_func = Mock(side_effect=[Exception("Transient error"), "success"])
        result = pipeline._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_with_backoff_exhausted(self):
        """Test retry logic fails after max attempts"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        mock_func = Mock(side_effect=Exception("Permanent error"))

        with pytest.raises(Exception, match="Permanent error"):
            pipeline._retry_with_backoff(mock_func)

        assert mock_func.call_count == 3  # Default max_attempts

    def test_run_with_health_check_failure_fail_fast(self):
        """Test pipeline aborts when health checks fail with fail_fast=True"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")
        pipeline.config["health_checks"]["fail_fast"] = True

        with patch.object(
            pipeline, "_run_health_checks", return_value=(False, ["Test failure"])
        ):
            result = pipeline.run()

            assert result["success"] is False
            assert result["error"] == "Health checks failed"
            assert "issues" in result

    @patch("scripts.reconciliation.run_reconciliation.subprocess")
    @patch.object(ReconciliationPipeline, "_run_health_checks")
    def test_run_pipeline_success(self, mock_health_checks, mock_subprocess):
        """Test successful pipeline execution"""
        mock_health_checks.return_value = (True, [])

        # Mock successful subprocess calls
        mock_subprocess.run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Mock cache loading
        cache_file = Path("inventory/cache/current_inventory.json")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"metadata": {"total_objects_scanned": 100}})
        )

        # Mock analysis output
        analysis_file = Path("inventory/cache/coverage_analysis.json")
        analysis_file.write_text(
            json.dumps({"summary": {"overall_completeness_pct": 95}})
        )

        # Mock gaps output
        gaps_file = Path("inventory/cache/detected_gaps.json")
        gaps_file.write_text(json.dumps({"summary": {"total_gaps": 5}}))

        pipeline = ReconciliationPipeline("nonexistent.yaml")

        try:
            result = pipeline.run(use_cache=True, dry_run=True)

            assert result["success"] is True
            assert "pipeline_duration_seconds" in result
            assert "performance" in result
            assert "step_times" in result["performance"]
        finally:
            # Cleanup
            if cache_file.exists():
                cache_file.unlink()
            if analysis_file.exists():
                analysis_file.unlink()
            if gaps_file.exists():
                gaps_file.unlink()

    def test_performance_tracking_included(self):
        """Test that performance metrics are tracked"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        with patch.object(pipeline, "_run_health_checks", return_value=(True, [])):
            with patch.object(
                pipeline, "_load_cached_inventory", return_value={"metadata": {}}
            ):
                with patch.object(
                    pipeline, "_analyze_coverage", return_value={"summary": {}}
                ):
                    with patch.object(
                        pipeline, "_detect_gaps", return_value={"summary": {}}
                    ):
                        with patch.object(
                            pipeline, "_generate_tasks", return_value={}
                        ):
                            result = pipeline.run()

                            # Check performance metrics exist
                            assert "performance" in result
                            perf = result["performance"]
                            assert "total_seconds" in perf
                            assert "step_times" in perf
                            assert "memory_used_mb" in perf
                            assert "peak_memory_mb" in perf


class TestReconciliationHealthChecks:
    """Focused tests for health check functionality"""

    @patch("scripts.reconciliation.run_reconciliation.boto3")
    def test_aws_credentials_invalid(self, mock_boto3):
        """Test AWS credentials validation failure"""
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.side_effect = Exception("Invalid credentials")
        mock_boto3.client.return_value = mock_sts

        pipeline = ReconciliationPipeline("nonexistent.yaml")
        success, issues = pipeline._run_health_checks()

        assert success is False
        assert any("AWS credentials" in issue for issue in issues)

    def test_cache_directory_creation(self, tmp_path):
        """Test cache directory is created if missing"""
        # Use temporary path
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            pipeline = ReconciliationPipeline("nonexistent.yaml")

            with patch("scripts.reconciliation.run_reconciliation.boto3"):
                with patch("scripts.reconciliation.run_reconciliation.psutil"):
                    pipeline._run_health_checks()

            cache_dir = tmp_path / "inventory" / "cache"
            assert cache_dir.exists()
        finally:
            os.chdir(original_cwd)


class TestReconciliationPerformance:
    """Tests for performance monitoring features"""

    def test_step_timing_tracking(self):
        """Test individual step timing is tracked"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        with patch.object(pipeline, "_run_health_checks", return_value=(True, [])):
            with patch.object(
                pipeline, "_load_cached_inventory", return_value={"metadata": {}}
            ):
                with patch.object(
                    pipeline, "_analyze_coverage", return_value={"summary": {}}
                ):
                    result = pipeline.run(steps="analyze")

                    assert "performance" in result
                    assert "step_times" in result["performance"]
                    assert "analyze" in result["performance"]["step_times"]
                    assert result["performance"]["step_times"]["analyze"] > 0

    def test_memory_tracking(self):
        """Test memory usage tracking"""
        pipeline = ReconciliationPipeline("nonexistent.yaml")

        with patch.object(pipeline, "_run_health_checks", return_value=(True, [])):
            with patch.object(
                pipeline, "_load_cached_inventory", return_value={"metadata": {}}
            ):
                result = pipeline.run(steps="scan", use_cache=True)

                assert "performance" in result
                assert "memory_used_mb" in result["performance"]
                assert "peak_memory_mb" in result["performance"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

