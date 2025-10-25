"""
⚠️ DEPRECATED - This file has been migrated to tests/phases/phase_0/

This file is kept for backward compatibility only.
Please use the new location: tests/phases/phase_0/test_{phase_num}_{name}.py

See docs/TEST_VALIDATOR_MIGRATION_GUIDE.md for details.

Migrated: October 23, 2025
Part of: Phase 0 Complete Reorganization
"""

# Original implementation below (deprecated)
# ===========================================

#!/usr/bin/env python3
"""
Test Suite: NBA Structured Data Extraction Framework

Recommendation ID: consolidated_rec_64_1595
Generated: 2025-10-15T23:49:50.254735
Enhanced: 2025-10-23 (Comprehensive Tests)

Tests the implementation of NBA Structured Data Extraction Framework.
"""

import unittest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implement_consolidated_rec_64_1595 import (
    StructuredDataExtractor,
    DataSource,
    DataType,
    ValidationResult,
    ExtractionResult,
)


class TestStructuredDataExtractor(unittest.TestCase):
    """Test suite for StructuredDataExtractor."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "validate_types": True,
            "strict_mode": False,
            "retry_attempts": 3,
        }
        self.implementation = StructuredDataExtractor(self.config)

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.implementation, "cleanup"):
            self.implementation.cleanup()

    def test_initialization(self):
        """Test that StructuredDataExtractor initializes correctly."""
        self.assertIsNotNone(self.implementation)
        self.assertFalse(self.implementation.setup_complete)
        self.assertEqual(self.implementation.config, self.config)
        self.assertTrue(self.implementation.validate_types)
        self.assertFalse(self.implementation.strict_mode)
        self.assertEqual(self.implementation.retry_attempts, 3)

    def test_setup(self):
        """Test setup process."""
        result = self.implementation.setup()
        self.assertTrue(result)
        self.assertTrue(self.implementation.setup_complete)
        self.assertEqual(len(self.implementation.schemas), 4)
        self.assertEqual(len(self.implementation.demo_data), 4)

    def test_validate_prerequisites(self):
        """Test prerequisite validation."""
        result = self.implementation.validate_prerequisites()
        self.assertTrue(result)

    def test_execute_without_setup(self):
        """Test that execute fails without setup."""
        with self.assertRaises(RuntimeError):
            self.implementation.execute()

    def test_execute_success(self):
        """Test successful execution."""
        self.implementation.setup()
        results = self.implementation.execute()

        self.assertIsNotNone(results)
        self.assertIn("success", results)
        self.assertTrue(results["success"])
        self.assertIn("execution_time", results)
        self.assertGreater(results["execution_time"], 0)
        self.assertEqual(results["total_extractions"], 4)
        self.assertEqual(results["successful_extractions"], 4)
        self.assertEqual(results["failed_extractions"], 0)

    def test_data_types_defined(self):
        """Test that all data types are defined."""
        self.assertEqual(DataType.GAME.value, "game")
        self.assertEqual(DataType.PLAYER_STATS.value, "player_stats")
        self.assertEqual(DataType.TEAM_STATS.value, "team_stats")
        self.assertEqual(DataType.BETTING_ODDS.value, "betting_odds")

    def test_data_sources_defined(self):
        """Test that all data sources are defined."""
        self.assertEqual(DataSource.ESPN.value, "espn")
        self.assertEqual(DataSource.BASKETBALL_REFERENCE.value, "basketball_reference")
        self.assertEqual(DataSource.NBA_API.value, "nba_api")
        self.assertEqual(DataSource.ODDS_API.value, "odds_api")

    def test_schemas_initialized(self):
        """Test that schemas are properly initialized."""
        self.implementation.setup()

        # Check GAME schema
        game_schema = self.implementation.schemas[DataType.GAME]
        self.assertIn("game_id", game_schema["required"])
        self.assertIn("date", game_schema["required"])
        self.assertIn("home_team", game_schema["required"])
        self.assertIn("away_team", game_schema["required"])

        # Check PLAYER_STATS schema
        player_schema = self.implementation.schemas[DataType.PLAYER_STATS]
        self.assertIn("player_id", player_schema["required"])
        self.assertIn("name", player_schema["required"])
        self.assertIn("points", player_schema["required"])

        # Check BETTING_ODDS schema
        odds_schema = self.implementation.schemas[DataType.BETTING_ODDS]
        self.assertIn("game_id", odds_schema["required"])
        self.assertIn("bookmaker", odds_schema["required"])
        self.assertIn("spread", odds_schema["required"])

    def test_demo_data_created(self):
        """Test that demo data is created."""
        self.implementation.setup()

        self.assertEqual(len(self.implementation.demo_data), 4)

        # Check game data
        game_data = self.implementation.demo_data[0]
        self.assertEqual(game_data["type"], DataType.GAME)
        self.assertEqual(game_data["source"], DataSource.ESPN)
        self.assertIn("game_id", game_data["data"])

        # Check player stats data
        player_data = self.implementation.demo_data[1]
        self.assertEqual(player_data["type"], DataType.PLAYER_STATS)
        self.assertEqual(player_data["source"], DataSource.BASKETBALL_REFERENCE)
        self.assertIn("player_id", player_data["data"])

        # Check betting odds data
        odds_data = self.implementation.demo_data[2]
        self.assertEqual(odds_data["type"], DataType.BETTING_ODDS)
        self.assertEqual(odds_data["source"], DataSource.ODDS_API)
        self.assertIn("spread", odds_data["data"])

    def test_validate_schema_valid_data(self):
        """Test schema validation with valid data."""
        self.implementation.setup()

        valid_game = {
            "game_id": "TEST_GAME_123",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": 110,
            "away_score": 105,
        }

        validation = self.implementation.validate_schema(valid_game, DataType.GAME)

        self.assertTrue(validation.is_valid)
        self.assertEqual(len(validation.errors), 0)
        self.assertGreater(validation.quality_score, 80)

    def test_validate_schema_missing_required(self):
        """Test schema validation with missing required fields."""
        self.implementation.setup()

        invalid_game = {
            "game_id": "TEST_GAME_123",
            "date": "2023-11-15",
            # Missing home_team, away_team, scores
        }

        validation = self.implementation.validate_schema(invalid_game, DataType.GAME)

        self.assertFalse(validation.is_valid)
        self.assertGreater(len(validation.errors), 0)
        self.assertLess(validation.quality_score, 50)

    def test_validate_schema_type_mismatch(self):
        """Test schema validation with type mismatches."""
        self.implementation.setup()

        type_mismatch_game = {
            "game_id": "TEST_GAME_123",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": "not_a_number",  # Should be int
            "away_score": 105,
        }

        validation = self.implementation.validate_schema(
            type_mismatch_game, DataType.GAME
        )

        self.assertFalse(validation.is_valid)
        self.assertGreater(len(validation.errors), 0)

    def test_validate_schema_constraint_violation(self):
        """Test schema validation with constraint violations."""
        self.implementation.setup()

        constraint_violation = {
            "game_id": "TEST_GAME_123",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": -10,  # Negative score violates constraint
            "away_score": 105,
        }

        validation = self.implementation.validate_schema(
            constraint_violation, DataType.GAME
        )

        self.assertFalse(validation.is_valid)
        self.assertGreater(len(validation.errors), 0)

    def test_coerce_types_string_to_int(self):
        """Test type coercion from string to int."""
        self.implementation.setup()

        data = {
            "game_id": "TEST",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": "110",  # String
            "away_score": "105",  # String
        }

        coerced = self.implementation.coerce_types(data, DataType.GAME)

        self.assertIsInstance(coerced["home_score"], int)
        self.assertIsInstance(coerced["away_score"], int)
        self.assertEqual(coerced["home_score"], 110)
        self.assertEqual(coerced["away_score"], 105)

    def test_coerce_types_string_to_float(self):
        """Test type coercion from string to float."""
        self.implementation.setup()

        data = {
            "game_id": "TEST",
            "bookmaker": "DraftKings",
            "spread": "-3.5",  # String
        }

        coerced = self.implementation.coerce_types(data, DataType.BETTING_ODDS)

        self.assertIsInstance(coerced["spread"], float)
        self.assertEqual(coerced["spread"], -3.5)

    def test_normalize_data_team_names(self):
        """Test data normalization for team names."""
        data = {"home_team": "LAL", "away_team": "GSW"}

        normalized = self.implementation.normalize_data(data, DataSource.ESPN)

        self.assertEqual(normalized["home_team"], "Los Angeles Lakers")
        self.assertEqual(normalized["away_team"], "Golden State Warriors")

    def test_normalize_data_player_names(self):
        """Test data normalization for player names."""
        data = {"name": "  lebron   JAMES  "}

        normalized = self.implementation.normalize_data(data, DataSource.ESPN)

        self.assertEqual(normalized["name"], "Lebron James")

    def test_normalize_data_dates(self):
        """Test data normalization for dates."""
        test_cases = [
            ("2023-11-15", "2023-11-15"),
            ("11/15/2023", "2023-11-15"),
            ("2023/11/15", "2023-11-15"),
        ]

        for input_date, expected_date in test_cases:
            data = {"date": input_date}
            normalized = self.implementation.normalize_data(data, DataSource.ESPN)
            self.assertEqual(normalized["date"], expected_date)

    def test_calculate_quality_score_perfect(self):
        """Test quality score calculation for perfect data."""
        self.implementation.setup()

        perfect_data = {
            "game_id": "TEST",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": 110,
            "away_score": 105,
            "attendance": 18000,
        }

        score = self.implementation.calculate_quality_score(
            perfect_data, DataType.GAME, errors=[], warnings=[]
        )

        self.assertEqual(score, 100.0)

    def test_calculate_quality_score_with_errors(self):
        """Test quality score calculation with errors."""
        self.implementation.setup()

        incomplete_data = {"game_id": "TEST", "date": "2023-11-15"}

        errors = [
            "Missing required field: home_team",
            "Missing required field: away_team",
        ]

        score = self.implementation.calculate_quality_score(
            incomplete_data, DataType.GAME, errors=errors, warnings=[]
        )

        self.assertLess(score, 100.0)
        self.assertGreaterEqual(score, 0.0)

    def test_extract_valid_game_data(self):
        """Test extraction of valid game data."""
        self.implementation.setup()

        game_data = {
            "game_id": "LAL_GSW_20231115",
            "date": "2023-11-15",
            "home_team": "LAL",
            "away_team": "GSW",
            "home_score": 128,
            "away_score": 121,
        }

        result = self.implementation.extract(
            raw_data=game_data, data_type=DataType.GAME, source=DataSource.ESPN
        )

        self.assertIsInstance(result, ExtractionResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertTrue(result.validation.is_valid)
        self.assertGreater(result.validation.quality_score, 80)

    def test_extract_player_stats(self):
        """Test extraction of player stats data."""
        self.implementation.setup()

        player_data = {
            "player_id": "lebron-james",
            "name": "LeBron James",
            "team": "Lakers",
            "points": 30,
            "rebounds": 8,
            "assists": 11,
        }

        result = self.implementation.extract(
            raw_data=player_data,
            data_type=DataType.PLAYER_STATS,
            source=DataSource.BASKETBALL_REFERENCE,
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertTrue(result.validation.is_valid)

    def test_extract_with_type_coercion(self):
        """Test extraction with automatic type coercion."""
        self.implementation.setup()

        game_data = {
            "game_id": "TEST",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": "110",  # String instead of int
            "away_score": "105",  # String instead of int
        }

        result = self.implementation.extract(
            raw_data=game_data, data_type=DataType.GAME, source=DataSource.ESPN
        )

        self.assertTrue(result.success)
        self.assertIsInstance(result.data["home_score"], int)
        self.assertIsInstance(result.data["away_score"], int)

    def test_extract_invalid_data_non_strict(self):
        """Test extraction of invalid data in non-strict mode."""
        self.implementation.setup()
        self.implementation.strict_mode = False

        invalid_data = {
            "game_id": "TEST",
            # Missing required fields
        }

        result = self.implementation.extract(
            raw_data=invalid_data, data_type=DataType.GAME, source=DataSource.ESPN
        )

        # Non-strict mode allows partial success
        self.assertTrue(result.success)
        self.assertFalse(result.validation.is_valid)

    def test_extract_invalid_data_strict(self):
        """Test extraction of invalid data in strict mode."""
        self.implementation.setup()
        self.implementation.strict_mode = True

        invalid_data = {
            "game_id": "TEST",
            # Missing required fields
        }

        result = self.implementation.extract(
            raw_data=invalid_data, data_type=DataType.GAME, source=DataSource.ESPN
        )

        # Strict mode fails on validation errors
        self.assertFalse(result.success)

    def test_extraction_count_tracking(self):
        """Test that extraction counts are tracked."""
        self.implementation.setup()

        initial_count = self.implementation.extraction_count

        game_data = {
            "game_id": "TEST",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": 110,
            "away_score": 105,
        }

        self.implementation.extract(game_data, DataType.GAME, DataSource.ESPN)

        self.assertEqual(self.implementation.extraction_count, initial_count + 1)

    def test_cleanup(self):
        """Test cleanup process."""
        self.implementation.setup()
        self.implementation.cleanup()
        # Cleanup should complete without errors

    # ===== TEAM_STATS Tests =====

    def test_team_stats_schema_initialized(self):
        """Test that TEAM_STATS schema is properly initialized."""
        self.implementation.setup()

        # Check TEAM_STATS schema
        team_schema = self.implementation.schemas[DataType.TEAM_STATS]
        self.assertIn("team_id", team_schema["required"])
        self.assertIn("team_name", team_schema["required"])
        self.assertIn("game_id", team_schema["required"])
        self.assertIn("points", team_schema["required"])
        self.assertIn("field_goals_made", team_schema["required"])
        self.assertIn("field_goals_attempted", team_schema["required"])

        # Check optional fields
        self.assertIn("rebounds", team_schema["optional"])
        self.assertIn("assists", team_schema["optional"])
        self.assertIn("three_pointers_made", team_schema["optional"])

    def test_team_stats_demo_data_created(self):
        """Test that TEAM_STATS demo data is created."""
        self.implementation.setup()

        self.assertEqual(len(self.implementation.demo_data), 4)

        # Check team stats data
        team_data = self.implementation.demo_data[3]
        self.assertEqual(team_data["type"], DataType.TEAM_STATS)
        self.assertEqual(team_data["source"], DataSource.NBA_API)
        self.assertIn("team_id", team_data["data"])
        self.assertIn("points", team_data["data"])
        self.assertEqual(team_data["data"]["points"], 128)

    def test_validate_schema_team_stats_valid(self):
        """Test schema validation with valid team stats."""
        self.implementation.setup()

        valid_team_stats = {
            "team_id": "lal",
            "team_name": "Lakers",
            "game_id": "TEST_GAME_123",
            "points": 110,
            "field_goals_made": 42,
            "field_goals_attempted": 88,
            "rebounds": 48,
            "assists": 25,
        }

        validation = self.implementation.validate_schema(
            valid_team_stats, DataType.TEAM_STATS
        )

        self.assertTrue(validation.is_valid)
        self.assertEqual(len(validation.errors), 0)
        self.assertGreater(validation.quality_score, 80)

    def test_extract_team_stats(self):
        """Test extraction of team stats data."""
        self.implementation.setup()

        team_data = {
            "team_id": "gsw",
            "team_name": "Warriors",
            "game_id": "LAL_GSW_20231115",
            "points": 121,
            "field_goals_made": 45,
            "field_goals_attempted": 90,
            "rebounds": 42,
            "assists": 30,
            "steals": 7,
            "blocks": 4,
        }

        result = self.implementation.extract(
            raw_data=team_data, data_type=DataType.TEAM_STATS, source=DataSource.NBA_API
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertTrue(result.validation.is_valid)
        self.assertGreater(result.validation.quality_score, 80)

    def test_team_stats_normalization(self):
        """Test team stats normalization."""
        self.implementation.setup()

        # Test with abbreviated team name
        team_data = {
            "team_id": "lal",
            "team_name": "LAL",  # Abbreviated
            "game_id": "TEST",
            "points": 110,
            "field_goals_made": 42,
            "field_goals_attempted": 88,
        }

        result = self.implementation.extract(
            raw_data=team_data, data_type=DataType.TEAM_STATS, source=DataSource.NBA_API
        )

        # Team name should be normalized
        self.assertEqual(result.data["team_name"], "Los Angeles Lakers")

    def test_team_stats_quality_score(self):
        """Test quality scoring for team stats."""
        self.implementation.setup()

        # Perfect team stats
        perfect_stats = {
            "team_id": "lal",
            "team_name": "Lakers",
            "game_id": "TEST",
            "points": 110,
            "field_goals_made": 42,
            "field_goals_attempted": 88,
            "rebounds": 45,
            "assists": 28,
            "steals": 8,
            "blocks": 5,
            "turnovers": 12,
            "fouls": 18,
        }

        # Minimal team stats
        minimal_stats = {
            "team_id": "gsw",
            "team_name": "Warriors",
            "game_id": "TEST",
            "points": 105,
            "field_goals_made": 40,
            "field_goals_attempted": 85,
        }

        perfect_result = self.implementation.extract(
            perfect_stats, DataType.TEAM_STATS, DataSource.NBA_API
        )
        minimal_result = self.implementation.extract(
            minimal_stats, DataType.TEAM_STATS, DataSource.NBA_API
        )

        # Perfect should have higher score
        self.assertGreaterEqual(
            perfect_result.validation.quality_score,
            minimal_result.validation.quality_score,
        )


class TestStructuredDataExtractorIntegration(unittest.TestCase):
    """Integration tests for StructuredDataExtractor."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.config = {
            "validate_types": True,
            "strict_mode": False,
            "retry_attempts": 3,
        }
        self.implementation = StructuredDataExtractor(self.config)

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # Validate prerequisites
        prereq_result = self.implementation.validate_prerequisites()
        self.assertTrue(prereq_result)

        # Setup
        setup_result = self.implementation.setup()
        self.assertTrue(setup_result)
        self.assertEqual(len(self.implementation.demo_data), 4)

        # Execute
        exec_result = self.implementation.execute()
        self.assertTrue(exec_result["success"])
        self.assertEqual(exec_result["total_extractions"], 4)
        self.assertEqual(exec_result["successful_extractions"], 4)

        # Cleanup
        self.implementation.cleanup()

    def test_multi_source_extraction(self):
        """Test extraction from multiple data sources."""
        self.implementation.setup()

        sources_data = [
            (
                DataSource.ESPN,
                DataType.GAME,
                {
                    "game_id": "ESPN_TEST",
                    "date": "2023-11-15",
                    "home_team": "Lakers",
                    "away_team": "Warriors",
                    "home_score": 110,
                    "away_score": 105,
                },
            ),
            (
                DataSource.BASKETBALL_REFERENCE,
                DataType.PLAYER_STATS,
                {
                    "player_id": "test-player",
                    "name": "Test Player",
                    "team": "Lakers",
                    "points": 25,
                },
            ),
            (
                DataSource.ODDS_API,
                DataType.BETTING_ODDS,
                {"game_id": "ODDS_TEST", "bookmaker": "DraftKings", "spread": -3.5},
            ),
        ]

        for source, data_type, data in sources_data:
            result = self.implementation.extract(data, data_type, source)
            self.assertTrue(result.success)
            self.assertEqual(result.source, source)

    def test_quality_score_calculation_workflow(self):
        """Test quality scoring across different data quality levels."""
        self.implementation.setup()

        # Perfect data
        perfect_game = {
            "game_id": "PERFECT",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": 110,
            "away_score": 105,
            "attendance": 18000,
            "venue": "Crypto.com Arena",
        }

        # Minimal data
        minimal_game = {
            "game_id": "MINIMAL",
            "date": "2023-11-15",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_score": 110,
            "away_score": 105,
        }

        perfect_result = self.implementation.extract(
            perfect_game, DataType.GAME, DataSource.ESPN
        )
        minimal_result = self.implementation.extract(
            minimal_game, DataType.GAME, DataSource.ESPN
        )

        # Perfect data should have higher quality score
        self.assertGreaterEqual(
            perfect_result.validation.quality_score,
            minimal_result.validation.quality_score,
        )

    def test_normalization_workflow(self):
        """Test data normalization across sources."""
        self.implementation.setup()

        # Test various team name formats
        team_variations = [
            {"home_team": "LAL", "away_team": "GSW"},
            {"home_team": "Lakers", "away_team": "Warriors"},
            {"home_team": "LA Lakers", "away_team": "GS Warriors"},
        ]

        normalized_teams = []
        for teams in team_variations:
            normalized = self.implementation.normalize_data(teams, DataSource.ESPN)
            normalized_teams.append((normalized["home_team"], normalized["away_team"]))

        # All should normalize to same format
        for home, away in normalized_teams:
            self.assertEqual(home, "Los Angeles Lakers")
            self.assertEqual(away, "Golden State Warriors")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredDataExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredDataExtractorIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
