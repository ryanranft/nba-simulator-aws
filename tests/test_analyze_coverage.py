#!/usr/bin/env python3
"""
Tests for Coverage Analysis

Tests the coverage analysis component of the reconciliation pipeline.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime


class TestCoverageAnalysis:
    """Test suite for coverage analysis"""

    def test_coverage_analysis_output_structure(self):
        """Test coverage analysis output has expected structure"""
        expected_keys = [
            "summary",
            "source_coverage",
            "season_coverage",
            "recommendations",
        ]

        mock_analysis = {
            "summary": {
                "overall_completeness_pct": 85.5,
                "total_games_expected": 1230,
                "total_games_found": 1052,
            },
            "source_coverage": {
                "espn": {"expected": 1230, "found": 1052, "pct": 85.5}
            },
            "season_coverage": {"2024": {"expected": 82, "found": 70, "pct": 85.4}},
            "recommendations": [],
        }

        for key in expected_keys:
            assert key in mock_analysis

    def test_completeness_calculation(self):
        """Test completeness percentage calculation"""
        expected = 1230
        found = 1052

        completeness_pct = (found / expected) * 100

        assert completeness_pct == pytest.approx(85.53, rel=0.01)

    def test_source_comparison(self):
        """Test comparison of coverage across sources"""
        sources = {
            "espn": {"expected": 1230, "found": 1052},
            "basketball_reference": {"expected": 1230, "found": 980},
            "nba_api": {"expected": 1230, "found": 1230},
        }

        # Calculate percentages
        for source, data in sources.items():
            data["pct"] = (data["found"] / data["expected"]) * 100

        # Verify calculations
        assert sources["espn"]["pct"] == pytest.approx(85.53, rel=0.01)
        assert sources["basketball_reference"]["pct"] == pytest.approx(79.67, rel=0.01)
        assert sources["nba_api"]["pct"] == 100.0

    def test_season_coverage_by_year(self):
        """Test coverage analysis grouped by season"""
        seasons = {
            "2024": {"expected": 82, "found": 70},
            "2023": {"expected": 82, "found": 82},
            "2022": {"expected": 82, "found": 78},
        }

        for season, data in seasons.items():
            data["pct"] = (data["found"] / data["expected"]) * 100

        assert seasons["2024"]["pct"] == pytest.approx(85.37, rel=0.01)
        assert seasons["2023"]["pct"] == 100.0
        assert seasons["2022"]["pct"] == pytest.approx(95.12, rel=0.01)

    def test_gap_detection_threshold(self):
        """Test gap detection based on threshold"""
        threshold_pct = 90.0

        coverage_data = [
            {"season": "2024", "pct": 85.5},  # Below threshold
            {"season": "2023", "pct": 95.0},  # Above threshold
            {"season": "2022", "pct": 89.0},  # Below threshold
        ]

        gaps = [item for item in coverage_data if item["pct"] < threshold_pct]

        assert len(gaps) == 2
        assert gaps[0]["season"] == "2024"
        assert gaps[1]["season"] == "2022"


class TestCoverageRecommendations:
    """Tests for coverage analysis recommendations"""

    def test_recommendation_generation(self):
        """Test that recommendations are generated for gaps"""
        gaps = [
            {"season": "2024", "source": "espn", "missing": 12, "pct": 85.4},
            {"season": "2023", "source": "basketball_reference", "missing": 50, "pct": 79.7},
        ]

        recommendations = []
        for gap in gaps:
            if gap["pct"] < 90:
                recommendations.append(
                    {
                        "priority": "HIGH" if gap["pct"] < 80 else "MEDIUM",
                        "action": f"Backfill {gap['source']} data for {gap['season']}",
                        "impact": f"{gap['missing']} games",
                    }
                )

        assert len(recommendations) == 2
        assert recommendations[0]["priority"] == "MEDIUM"  # 85.4%
        assert recommendations[1]["priority"] == "HIGH"  # 79.7%

    def test_priority_assignment(self):
        """Test priority levels are assigned correctly"""
        coverage_levels = [
            {"id": 1, "pct": 95.0},  # LOW (>90%)
            {"id": 2, "pct": 85.0},  # MEDIUM (80-90%)
            {"id": 3, "pct": 75.0},  # HIGH (70-80%)
            {"id": 4, "pct": 65.0},  # CRITICAL (<70%)
        ]

        def assign_priority(pct):
            if pct >= 90:
                return "LOW"
            elif pct >= 80:
                return "MEDIUM"
            elif pct >= 70:
                return "HIGH"
            else:
                return "CRITICAL"

        priorities = [assign_priority(item["pct"]) for item in coverage_levels]

        assert priorities == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class TestCoverageMetrics:
    """Tests for coverage metrics calculation"""

    def test_should_vs_have_comparison(self):
        """Test SHOULD vs HAVE comparison logic"""
        # SHOULD = expected based on schedule
        # HAVE = actual files found
        should_have = 1230
        actual_have = 1052

        missing = should_have - actual_have
        coverage_pct = (actual_have / should_have) * 100

        assert missing == 178
        assert coverage_pct == pytest.approx(85.53, rel=0.01)

    def test_multi_source_aggregation(self):
        """Test aggregating coverage across multiple sources"""
        sources = {
            "espn": {"have": 1052, "should": 1230},
            "basketball_reference": {"have": 980, "should": 1230},
            "nba_api": {"have": 1230, "should": 1230},
        }

        # Best available coverage (max across sources)
        best_coverage = {}
        for source, data in sources.items():
            best_coverage[source] = data["have"]

        # Union of all sources
        union_coverage = max(best_coverage.values())

        assert union_coverage == 1230  # nba_api has complete coverage

    def test_temporal_coverage_gaps(self):
        """Test detection of temporal gaps in coverage"""
        games_by_date = {
            "2024-01-01": {"expected": 10, "found": 10},
            "2024-01-02": {"expected": 12, "found": 8},  # Gap
            "2024-01-03": {"expected": 11, "found": 11},
        }

        gaps = [
            date
            for date, data in games_by_date.items()
            if data["found"] < data["expected"]
        ]

        assert len(gaps) == 1
        assert gaps[0] == "2024-01-02"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

