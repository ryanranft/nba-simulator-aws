#!/usr/bin/env python3
"""
Test Suite for Recommendation Implementation System

Tests the automation scripts and infrastructure for implementing
book recommendations.

Usage:
    pytest tests/test_recommendation_implementation_system.py -v
"""

import os
import json
import pytest
from pathlib import Path
import sys

# Add scripts directory to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "automation"))

from map_recommendations_to_phases import RecommendationMapper
from check_recommendation_status import RecommendationStatusChecker


class TestRecommendationMapper:
    """Test the recommendation mapper functionality."""

    def test_mapper_initialization(self):
        """Test that mapper initializes correctly."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        assert mapper.workspace_root == WORKSPACE_ROOT
        assert mapper.phases_dir == WORKSPACE_ROOT / "docs" / "phases"

    def test_scan_phase_directories(self):
        """Test scanning phase directories for recommendations."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapping = mapper.scan_phase_directories()

        # Should find recommendations
        assert len(mapping) > 0, "No recommendations found"

        # Check structure of mapping
        for rec_id, info in mapping.items():
            assert rec_id.startswith("rec_"), f"Invalid rec_id: {rec_id}"
            assert "phase" in info
            assert "directory" in info
            assert "title" in info
            assert "has_readme" in info

    def test_recommendation_count(self):
        """Test that we find the expected number of recommendations."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapping = mapper.scan_phase_directories()

        # Should be close to 218 (may vary during implementation)
        assert len(mapping) >= 50, f"Too few recommendations found: {len(mapping)}"
        assert len(mapping) <= 300, f"Too many recommendations found: {len(mapping)}"

    def test_save_and_load_mapping(self, tmp_path):
        """Test saving and loading mapping to JSON."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))

        # Save to temporary file
        output_path = tmp_path / "test_mapping.json"
        saved_path = mapper.save_mapping(output_path=str(output_path))

        assert Path(saved_path).exists()

        # Load and verify
        with open(saved_path) as f:
            loaded_mapping = json.load(f)

        assert len(loaded_mapping) > 0
        assert all(k.startswith("rec_") for k in loaded_mapping.keys())

    def test_get_recommendation_path(self):
        """Test getting path to specific recommendation."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapper.scan_phase_directories()

        # Get first recommendation
        if mapper.mapping:
            first_rec = list(mapper.mapping.keys())[0]
            path = mapper.get_recommendation_path(first_rec)

            assert path is not None
            assert path.exists()
            assert path.is_dir()

    def test_get_recommendation_info(self):
        """Test getting info for specific recommendation."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapper.scan_phase_directories()

        if mapper.mapping:
            first_rec = list(mapper.mapping.keys())[0]
            info = mapper.get_recommendation_info(first_rec)

            assert info is not None
            assert "phase" in info
            assert "directory" in info
            assert "title" in info

    def test_list_recommendations_by_phase(self):
        """Test listing recommendations in specific phase."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapper.scan_phase_directories()

        # Test phase 0
        phase_0_recs = mapper.list_recommendations_by_phase(0)
        assert len(phase_0_recs) > 0, "No recommendations in phase 0"
        assert all(rec.startswith("rec_") for rec in phase_0_recs)

    def test_generate_report(self):
        """Test generating human-readable report."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapper.scan_phase_directories()

        report = mapper.generate_report()

        assert len(report) > 0
        assert "RECOMMENDATION MAPPING REPORT" in report
        assert "Total Recommendations Found:" in report
        assert "Distribution by Phase:" in report


class TestRecommendationStatusChecker:
    """Test the recommendation status checker functionality."""

    def test_checker_initialization(self):
        """Test that checker initializes correctly."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        assert checker.workspace_root == WORKSPACE_ROOT
        assert checker.phases_dir == WORKSPACE_ROOT / "docs" / "phases"

    def test_scan_statuses(self):
        """Test scanning STATUS.md files."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        statuses = checker.scan_statuses()

        # Should find statuses
        assert len(statuses) > 0, "No statuses found"

        # Check structure
        for rec_id, info in statuses.items():
            assert rec_id.startswith("rec_"), f"Invalid rec_id: {rec_id}"
            assert "status" in info
            assert "phase" in info
            assert info["status"] in [
                "PLANNED",
                "IN_PROGRESS",
                "COMPLETE",
                "BLOCKED",
                "MISSING",
                "UNKNOWN",
                "ERROR",
            ]

    def test_get_summary(self):
        """Test getting summary statistics."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        checker.scan_statuses()

        summary = checker.get_summary()

        assert "total" in summary
        assert "COMPLETE" in summary
        assert "IN_PROGRESS" in summary
        assert "BLOCKED" in summary
        assert "PLANNED" in summary
        assert "remaining" in summary

        # Validate counts
        assert summary["total"] > 0
        assert summary["total"] == (
            summary["COMPLETE"]
            + summary["IN_PROGRESS"]
            + summary["BLOCKED"]
            + summary["PLANNED"]
            + summary["MISSING"]
            + summary["UNKNOWN"]
            + summary["ERROR"]
        )

    def test_get_next_available(self):
        """Test getting next available recommendations."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        checker.scan_statuses()

        next_recs = checker.get_next_available(count=5)

        # Should be list of tuples
        assert isinstance(next_recs, list)

        # Each item should be (rec_id, info)
        for rec_id, info in next_recs:
            assert rec_id.startswith("rec_")
            assert "status" in info
            assert info["status"] not in ["COMPLETE", "IN_PROGRESS", "BLOCKED"]

    def test_get_blocked_recommendations(self):
        """Test getting blocked recommendations."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        checker.scan_statuses()

        blocked = checker.get_blocked_recommendations()

        assert isinstance(blocked, list)

        # All should have status BLOCKED
        for rec_id, info in blocked:
            assert info["status"] == "BLOCKED"

    def test_generate_report(self):
        """Test generating status report."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        checker.scan_statuses()

        report = checker.generate_report(verbose=False)

        assert len(report) > 0
        assert "BOOK RECOMMENDATIONS STATUS REPORT" in report
        assert "SUMMARY" in report
        assert "NEXT AVAILABLE" in report

    def test_generate_verbose_report(self):
        """Test generating verbose status report."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        checker.scan_statuses()

        report = checker.generate_report(verbose=True)

        assert len(report) > 0
        assert "DETAILED STATUS BY PHASE" in report


class TestRecommendationFiles:
    """Test that recommendation files are properly structured."""

    def test_all_recommendations_have_required_files(self):
        """Test that each recommendation has all required files."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapping = mapper.scan_phase_directories()

        required_files = [
            "README.md",
            "STATUS.md",
            "IMPLEMENTATION_GUIDE.md",
            "RECOMMENDATIONS_FROM_BOOKS.md",
        ]

        incomplete = []

        for rec_id, info in mapping.items():
            rec_path = WORKSPACE_ROOT / info["directory"]

            for filename in required_files:
                file_path = rec_path / filename
                if not file_path.exists():
                    incomplete.append((rec_id, filename))

        # Allow some missing files during development
        # but flag if > 10% are incomplete
        if incomplete:
            missing_pct = len(incomplete) / (len(mapping) * len(required_files)) * 100
            if missing_pct > 10:
                pytest.fail(
                    f"{missing_pct:.1f}% of required files missing. "
                    f"Examples: {incomplete[:5]}"
                )

    def test_readme_has_title(self):
        """Test that README files have proper titles."""
        mapper = RecommendationMapper(workspace_root=str(WORKSPACE_ROOT))
        mapping = mapper.scan_phase_directories()

        missing_titles = []

        for rec_id, info in mapping.items():
            if not info.get("has_readme"):
                continue

            if info.get("title") == "Unknown":
                missing_titles.append(rec_id)

        # Allow some missing titles but flag if excessive
        if missing_titles and len(missing_titles) > len(mapping) * 0.1:
            pytest.fail(
                f"{len(missing_titles)} recommendations missing titles. "
                f"Examples: {missing_titles[:5]}"
            )

    def test_status_files_have_valid_status(self):
        """Test that STATUS.md files have valid status markers."""
        checker = RecommendationStatusChecker(workspace_root=str(WORKSPACE_ROOT))
        statuses = checker.scan_statuses()

        invalid_statuses = [
            rec_id
            for rec_id, info in statuses.items()
            if info.get("status") in ["UNKNOWN", "ERROR", "MISSING"]
        ]

        # Allow some invalid but flag if excessive
        if invalid_statuses and len(invalid_statuses) > len(statuses) * 0.1:
            pytest.fail(
                f"{len(invalid_statuses)} recommendations with invalid status. "
                f"Examples: {invalid_statuses[:5]}"
            )


class TestProgressTracking:
    """Test progress tracking functionality."""

    def test_progress_file_exists(self):
        """Test that progress tracking file exists."""
        progress_file = WORKSPACE_ROOT / "BOOK_RECOMMENDATIONS_PROGRESS.md"
        assert progress_file.exists(), "Progress file not found"

    def test_progress_file_has_summary_table(self):
        """Test that progress file has summary table."""
        progress_file = WORKSPACE_ROOT / "BOOK_RECOMMENDATIONS_PROGRESS.md"

        with open(progress_file) as f:
            content = f.read()

        assert "## Summary" in content
        assert "Total Recommendations" in content
        assert "Completed" in content
        assert "Remaining" in content


class TestWorkflowFile:
    """Test workflow file exists and is complete."""

    def test_workflow_54_exists(self):
        """Test that workflow #54 file exists."""
        workflow_file = (
            WORKSPACE_ROOT
            / "docs"
            / "claude_workflows"
            / "workflow_descriptions"
            / "54_autonomous_recommendation_implementation.md"
        )
        assert workflow_file.exists(), "Workflow #54 not found"

    def test_workflow_54_has_required_sections(self):
        """Test that workflow #54 has all required sections."""
        workflow_file = (
            WORKSPACE_ROOT
            / "docs"
            / "claude_workflows"
            / "workflow_descriptions"
            / "54_autonomous_recommendation_implementation.md"
        )

        with open(workflow_file) as f:
            content = f.read()

        required_sections = [
            "## Overview",
            "## Mission Statement",
            "## Implementation Process",
            "## Escalation Criteria",
            "## Safety Protocols",
            "## Command Reference",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"


class TestScriptExecution:
    """Test that scripts can be executed (dry run)."""

    def test_mapper_script_runs(self):
        """Test that mapper script runs without error."""
        import subprocess

        result = subprocess.run(
            [
                "python3",
                "scripts/automation/map_recommendations_to_phases.py",
                "--help",
            ],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "usage:" in result.stdout.lower() or "Usage:" in result.stdout

    def test_checker_script_runs(self):
        """Test that checker script runs without error."""
        import subprocess

        result = subprocess.run(
            ["python3", "scripts/automation/check_recommendation_status.py", "--help"],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "usage:" in result.stdout.lower() or "Usage:" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
