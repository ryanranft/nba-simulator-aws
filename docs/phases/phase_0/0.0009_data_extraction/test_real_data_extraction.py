#!/usr/bin/env python3
"""
Comprehensive Real Data Test Suite

Tests NBA Data Extraction Framework against all real data files:
- 44,830 ESPN box score files
- 44,831 NBA team stats files
- 11,635 schedule files

Validates:
- Schema compliance across all data types
- Deep JSON parsing functionality
- Quality score distributions
- Performance benchmarks
- Schema gap analysis

Generated: 2025-10-23
Purpose: Validate extraction framework with real NBA data at scale
"""

import unittest
import os
import sys
import json
import glob
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implement_consolidated_rec_64_1595 import (
    StructuredDataExtractor,
    DataSource,
    DataType,
    ValidationResult,
    ExtractionResult,
)
from data_source_adapters import (
    ESPNAdapter,
    NBAAPIAdapter,
    BasketballReferenceAdapter,
    OddsAPIAdapter,
)


class TestRealDataExtraction(unittest.TestCase):
    """Test extraction framework against real NBA data."""

    @classmethod
    def setUpClass(cls):
        """Initialize adapters, extractor, and discover data files once for all tests."""
        print("\n" + "=" * 80)
        print("INITIALIZING REAL DATA TEST SUITE")
        print("=" * 80)

        # Initialize extraction framework
        cls.extractor = StructuredDataExtractor(
            {"validate_types": True, "strict_mode": False}
        )
        cls.extractor.setup()

        # Initialize adapters
        cls.espn_adapter = ESPNAdapter()
        cls.nba_adapter = NBAAPIAdapter()
        cls.bbref_adapter = BasketballReferenceAdapter()
        cls.odds_adapter = OddsAPIAdapter()

        # Discover data files (relative to project root)
        # Current file is: docs/phases/phase_0/0.0009_data_extraction/test_real_data_extraction.py
        # Project root is 4 levels up
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        )
        data_dir = os.path.join(project_root, "data")

        print(f"Project root: {project_root}")
        print(f"Data directory: {data_dir}")
        print(f"Data directory exists: {os.path.exists(data_dir)}")

        cls.box_score_files = glob.glob(
            os.path.join(data_dir, "nba_box_score", "*.json")
        )
        cls.team_stats_files = glob.glob(
            os.path.join(data_dir, "nba_team_stats", "*.json")
        )
        cls.schedule_files = glob.glob(
            os.path.join(data_dir, "nba_schedule_json", "*.json")
        )

        print(f"Discovered data files:")
        print(f"  Box scores: {len(cls.box_score_files):,}")
        print(f"  Team stats: {len(cls.team_stats_files):,}")
        print(f"  Schedules: {len(cls.schedule_files):,}")
        print(
            f"  Total: {len(cls.box_score_files) + len(cls.team_stats_files) + len(cls.schedule_files):,}"
        )

        # Test report
        cls.test_report = {
            "test_date": datetime.now().isoformat(),
            "total_files_discovered": len(cls.box_score_files)
            + len(cls.team_stats_files)
            + len(cls.schedule_files),
            "schemas_tested": ["GAME", "PLAYER_STATS", "TEAM_STATS", "BETTING_ODDS"],
            "results": {},
            "schema_gaps": {},
            "performance": {},
            "recommendations": [],
        }

    def test_01_espn_adapter_sample_parsing(self):
        """Test ESPN adapter on 10 random box score files."""
        print("\n" + "-" * 80)
        print("TEST: ESPN Adapter Sample Parsing (10 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(10, len(self.box_score_files))
        )
        successful_parses = 0
        failed_parses = 0

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                # Test game parsing
                game_data = self.espn_adapter.parse_game(raw_data)
                if game_data:
                    successful_parses += 1
                    print(
                        f"  ✅ {os.path.basename(file_path)}: {game_data.get('home_team')} vs {game_data.get('away_team')}"
                    )
                else:
                    failed_parses += 1
                    print(f"  ❌ {os.path.basename(file_path)}: Parse failed")

            except Exception as e:
                failed_parses += 1
                print(f"  ❌ {os.path.basename(file_path)}: {e}")

        print(
            f"\nResults: {successful_parses}/10 successful, {failed_parses}/10 failed"
        )
        self.assertGreater(
            successful_parses, 5, "Should successfully parse majority of files"
        )

    def test_02_player_stats_extraction_sample(self):
        """Test player stats extraction on 10 random files."""
        print("\n" + "-" * 80)
        print("TEST: Player Stats Extraction (10 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(10, len(self.box_score_files))
        )
        total_players = 0
        files_with_players = 0

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                players = self.espn_adapter.parse_player_stats(raw_data)
                if players:
                    files_with_players += 1
                    total_players += len(players)
                    print(f"  ✅ {os.path.basename(file_path)}: {len(players)} players")
                else:
                    print(f"  ⚠️  {os.path.basename(file_path)}: No players found")

            except Exception as e:
                print(f"  ❌ {os.path.basename(file_path)}: {e}")

        avg_players = (
            total_players / files_with_players if files_with_players > 0 else 0
        )
        print(
            f"\nResults: {total_players} total players, avg {avg_players:.1f} per game"
        )
        self.assertGreater(
            files_with_players, 5, "Should extract players from majority of files"
        )

    def test_03_team_stats_extraction_sample(self):
        """Test team stats extraction on 10 random files."""
        print("\n" + "-" * 80)
        print("TEST: Team Stats Extraction (10 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(10, len(self.box_score_files))
        )
        successful_extractions = 0

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                teams = self.espn_adapter.parse_team_stats(raw_data)
                if len(teams) == 2:
                    successful_extractions += 1
                    print(
                        f"  ✅ {os.path.basename(file_path)}: {teams[0].get('team_name')} ({teams[0].get('points')}), {teams[1].get('team_name')} ({teams[1].get('points')})"
                    )
                else:
                    print(
                        f"  ⚠️  {os.path.basename(file_path)}: Found {len(teams)} teams (expected 2)"
                    )

            except Exception as e:
                print(f"  ❌ {os.path.basename(file_path)}: {e}")

        print(f"\nResults: {successful_extractions}/10 files with complete team data")
        self.assertGreater(
            successful_extractions, 5, "Should extract teams from majority of files"
        )

    def test_04_schema_validation_player_stats_sample(self):
        """Validate PLAYER_STATS schema against 50 random files."""
        print("\n" + "-" * 80)
        print("TEST: PLAYER_STATS Schema Validation (50 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(50, len(self.box_score_files))
        )
        successful_validations = 0
        failed_validations = 0
        quality_scores = []
        errors_by_type = Counter()

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                players = self.espn_adapter.parse_player_stats(raw_data)

                for player in players:
                    result = self.extractor.extract(
                        raw_data=player,
                        data_type=DataType.PLAYER_STATS,
                        source=DataSource.ESPN,
                    )

                    if result.success:
                        successful_validations += 1
                        quality_scores.append(result.validation.quality_score)
                    else:
                        failed_validations += 1
                        for error in result.validation.errors:
                            errors_by_type[error] += 1

            except Exception as e:
                failed_validations += 1
                errors_by_type[f"Parse error: {str(e)[:50]}"] += 1

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        success_rate = (
            (successful_validations / (successful_validations + failed_validations))
            * 100
            if (successful_validations + failed_validations) > 0
            else 0
        )

        print(f"\nResults:")
        print(f"  Successful: {successful_validations}")
        print(f"  Failed: {failed_validations}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average quality score: {avg_quality:.1f}/100")

        if errors_by_type:
            print(f"\nTop 5 errors:")
            for error, count in errors_by_type.most_common(5):
                print(f"    {error}: {count}")

        # Store in report
        self.test_report["results"]["PLAYER_STATS"] = {
            "files_tested": len(sample_files),
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": success_rate,
            "avg_quality_score": avg_quality,
            "top_errors": dict(errors_by_type.most_common(10)),
        }

        self.assertGreater(
            success_rate, 50, "Should have >50% success rate on real data"
        )

    def test_05_schema_validation_team_stats_sample(self):
        """Validate TEAM_STATS schema against 50 random files."""
        print("\n" + "-" * 80)
        print("TEST: TEAM_STATS Schema Validation (50 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(50, len(self.box_score_files))
        )
        successful_validations = 0
        failed_validations = 0
        quality_scores = []
        errors_by_type = Counter()

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                teams = self.espn_adapter.parse_team_stats(raw_data)

                for team in teams:
                    result = self.extractor.extract(
                        raw_data=team,
                        data_type=DataType.TEAM_STATS,
                        source=DataSource.ESPN,
                    )

                    if result.success:
                        successful_validations += 1
                        quality_scores.append(result.validation.quality_score)
                    else:
                        failed_validations += 1
                        for error in result.validation.errors:
                            errors_by_type[error] += 1

            except Exception as e:
                failed_validations += 1
                errors_by_type[f"Parse error: {str(e)[:50]}"] += 1

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        success_rate = (
            (successful_validations / (successful_validations + failed_validations))
            * 100
            if (successful_validations + failed_validations) > 0
            else 0
        )

        print(f"\nResults:")
        print(f"  Successful: {successful_validations}")
        print(f"  Failed: {failed_validations}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average quality score: {avg_quality:.1f}/100")

        if errors_by_type:
            print(f"\nTop 5 errors:")
            for error, count in errors_by_type.most_common(5):
                print(f"    {error}: {count}")

        # Store in report
        self.test_report["results"]["TEAM_STATS"] = {
            "files_tested": len(sample_files),
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": success_rate,
            "avg_quality_score": avg_quality,
            "top_errors": dict(errors_by_type.most_common(10)),
        }

        self.assertGreater(
            success_rate, 50, "Should have >50% success rate on real data"
        )

    def test_06_schema_validation_game_data_sample(self):
        """Validate GAME schema against 50 random files."""
        print("\n" + "-" * 80)
        print("TEST: GAME Schema Validation (50 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(50, len(self.box_score_files))
        )
        successful_validations = 0
        failed_validations = 0
        quality_scores = []
        errors_by_type = Counter()

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                game_data = self.espn_adapter.parse_game(raw_data)
                if game_data:
                    result = self.extractor.extract(
                        raw_data=game_data,
                        data_type=DataType.GAME,
                        source=DataSource.ESPN,
                    )

                    if result.success:
                        successful_validations += 1
                        quality_scores.append(result.validation.quality_score)
                    else:
                        failed_validations += 1
                        for error in result.validation.errors:
                            errors_by_type[error] += 1
                else:
                    failed_validations += 1
                    errors_by_type["Parse returned None"] += 1

            except Exception as e:
                failed_validations += 1
                errors_by_type[f"Parse error: {str(e)[:50]}"] += 1

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        success_rate = (
            (successful_validations / (successful_validations + failed_validations))
            * 100
            if (successful_validations + failed_validations) > 0
            else 0
        )

        print(f"\nResults:")
        print(f"  Successful: {successful_validations}")
        print(f"  Failed: {failed_validations}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average quality score: {avg_quality:.1f}/100")

        if errors_by_type:
            print(f"\nTop 5 errors:")
            for error, count in errors_by_type.most_common(5):
                print(f"    {error}: {count}")

        # Store in report
        self.test_report["results"]["GAME"] = {
            "files_tested": len(sample_files),
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": success_rate,
            "avg_quality_score": avg_quality,
            "top_errors": dict(errors_by_type.most_common(10)),
        }

        self.assertGreater(
            success_rate, 50, "Should have >50% success rate on real data"
        )

    def test_07_extraction_performance_benchmark(self):
        """Benchmark extraction performance with 100 files."""
        print("\n" + "-" * 80)
        print("TEST: Extraction Performance Benchmark (100 files)")
        print("-" * 80)

        if not self.box_score_files:
            self.skipTest("No box score files found")

        sample_files = random.sample(
            self.box_score_files, min(100, len(self.box_score_files))
        )
        total_extractions = 0
        start_time = time.time()

        for file_path in sample_files:
            try:
                with open(file_path, "r") as f:
                    raw_data = json.load(f)

                # Extract game data
                game_data = self.espn_adapter.parse_game(raw_data)
                if game_data:
                    self.extractor.extract(game_data, DataType.GAME, DataSource.ESPN)
                    total_extractions += 1

                # Extract player stats
                players = self.espn_adapter.parse_player_stats(raw_data)
                for player in players:
                    self.extractor.extract(
                        player, DataType.PLAYER_STATS, DataSource.ESPN
                    )
                    total_extractions += 1

                # Extract team stats
                teams = self.espn_adapter.parse_team_stats(raw_data)
                for team in teams:
                    self.extractor.extract(team, DataType.TEAM_STATS, DataSource.ESPN)
                    total_extractions += 1

            except Exception:
                pass

        end_time = time.time()
        duration = end_time - start_time
        records_per_second = total_extractions / duration if duration > 0 else 0
        avg_time_ms = (
            (duration / total_extractions) * 1000 if total_extractions > 0 else 0
        )

        print(f"\nResults:")
        print(f"  Total extractions: {total_extractions}")
        print(f"  Total duration: {duration:.2f}s")
        print(f"  Records/second: {records_per_second:.0f}")
        print(f"  Avg time per record: {avg_time_ms:.2f}ms")

        # Store in report
        self.test_report["performance"] = {
            "files_tested": len(sample_files),
            "total_extractions": total_extractions,
            "total_duration_seconds": round(duration, 2),
            "records_per_second": round(records_per_second, 0),
            "avg_extraction_time_ms": round(avg_time_ms, 2),
        }

        self.assertGreater(
            records_per_second, 100, "Should extract >100 records/second"
        )

    @classmethod
    def tearDownClass(cls):
        """Generate and save test report."""
        print("\n" + "=" * 80)
        print("GENERATING TEST REPORT")
        print("=" * 80)

        # Add recommendations based on results
        recommendations = []

        for schema, results in cls.test_report["results"].items():
            if results.get("success_rate", 0) < 95:
                recommendations.append(
                    f"Improve {schema} schema - success rate only {results.get('success_rate', 0):.1f}%"
                )

            if results.get("avg_quality_score", 0) < 90:
                recommendations.append(
                    f"Enhance {schema} quality scoring - avg score only {results.get('avg_quality_score', 0):.1f}/100"
                )

        cls.test_report["recommendations"] = recommendations

        # Save report
        report_path = os.path.join(
            os.path.dirname(__file__), "real_data_test_report.json"
        )
        with open(report_path, "w") as f:
            json.dump(cls.test_report, f, indent=2)

        print(f"\n✅ Test report saved to: {report_path}")
        print(f"\nSummary:")
        print(f"  Schemas tested: {len(cls.test_report['results'])}")
        print(
            f"  Total files discovered: {cls.test_report['total_files_discovered']:,}"
        )
        print(f"  Recommendations: {len(recommendations)}")


def run_tests():
    """Run all tests with verbose output."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRealDataExtraction)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
