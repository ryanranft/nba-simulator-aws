#!/usr/bin/env python3
"""
Test Suite for Panel Data Processing System (rec_22)

Comprehensive tests for all panel data functionality.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add path for implementation
sys.path.insert(0, os.path.dirname(__file__))

from implement_rec_22 import (
    PanelDataProcessingSystem,
    create_panel_from_dataframe,
    generate_temporal_features,
)


class TestPanelDataStructure(unittest.TestCase):
    """Test panel data structure creation."""

    def setUp(self):
        """Create test data before each test."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

        # Create simple test data
        self.test_data = pd.DataFrame(
            {
                "player_id": [1, 1, 1, 2, 2, 2],
                "game_id": ["g1", "g2", "g3", "g1", "g2", "g3"],
                "game_date": pd.date_range("2023-01-01", periods=3).tolist() * 2,
                "points": [20, 25, 22, 15, 18, 20],
                "rebounds": [5, 7, 6, 8, 9, 7],
            }
        )

    def test_panel_index_creation(self):
        """Test that multi-index is created correctly."""
        panel = self.system.create_panel_index(self.test_data)

        # Check index has 3 levels
        self.assertEqual(panel.index.nlevels, 3)

        # Check index names
        self.assertEqual(panel.index.names, ["player_id", "game_id", "timestamp"])

        # Check sorted by player_id, timestamp
        player_ids = panel.index.get_level_values("player_id")
        self.assertTrue(
            all(player_ids[i] <= player_ids[i + 1] for i in range(len(player_ids) - 1))
        )

    def test_no_duplicate_indices(self):
        """Test that duplicate indices are handled."""
        panel = self.system.create_panel_index(self.test_data)

        # No duplicates should exist
        self.assertFalse(panel.index.duplicated().any())

    def test_player_count(self):
        """Test correct number of players."""
        panel = self.system.create_panel_index(self.test_data)

        n_players = panel.index.get_level_values("player_id").nunique()
        self.assertEqual(n_players, 2)

    def test_timestamp_creation(self):
        """Test timestamp is created from game_date."""
        panel = self.system.create_panel_index(self.test_data)

        timestamps = panel.index.get_level_values("timestamp")
        self.assertIsInstance(timestamps[0], pd.Timestamp)


class TestLagGeneration(unittest.TestCase):
    """Test lag variable generation."""

    def setUp(self):
        """Create panel data for testing."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

        # Create sequential data for one player
        self.panel = pd.DataFrame(
            {
                "player_id": [1] * 5,
                "game_id": ["g1", "g2", "g3", "g4", "g5"],
                "game_date": pd.date_range("2023-01-01", periods=5),
                "points": [10, 20, 30, 40, 50],
            }
        )
        self.panel = self.system.create_panel_index(self.panel)

    def test_lag1_values(self):
        """Test that lag=1 values match previous game."""
        panel = self.system.generate_lags(self.panel, ["points"], [1])

        # Lag1 should equal previous game's points
        self.assertTrue(pd.isna(panel["points_lag1"].iloc[0]))  # First game has no lag
        self.assertEqual(panel["points_lag1"].iloc[1], 10)  # Game 2 lag = game 1
        self.assertEqual(panel["points_lag1"].iloc[2], 20)  # Game 3 lag = game 2

    def test_lag_multiple_periods(self):
        """Test multiple lag periods."""
        panel = self.system.generate_lags(self.panel, ["points"], [1, 2, 3])

        # Check all lag columns created
        self.assertIn("points_lag1", panel.columns)
        self.assertIn("points_lag2", panel.columns)
        self.assertIn("points_lag3", panel.columns)

        # Check lag2 values
        self.assertTrue(pd.isna(panel["points_lag2"].iloc[0]))
        self.assertTrue(pd.isna(panel["points_lag2"].iloc[1]))
        self.assertEqual(panel["points_lag2"].iloc[2], 10)  # Game 3 lag2 = game 1

    def test_lag_multiple_variables(self):
        """Test lagging multiple variables."""
        self.panel["rebounds"] = [5, 6, 7, 8, 9]
        panel = self.system.generate_lags(self.panel, ["points", "rebounds"], [1])

        self.assertIn("points_lag1", panel.columns)
        self.assertIn("rebounds_lag1", panel.columns)

        self.assertEqual(panel["rebounds_lag1"].iloc[1], 5)

    def test_lag_multiple_players(self):
        """Test lags are computed within each player."""
        # Add second player
        player2_data = pd.DataFrame(
            {
                "player_id": [2] * 3,
                "game_id": ["g1", "g2", "g3"],
                "game_date": pd.date_range("2023-01-01", periods=3),
                "points": [15, 25, 35],
            }
        )

        combined = pd.concat([self.panel.reset_index(), player2_data])
        panel = self.system.create_panel_index(combined)
        panel = self.system.generate_lags(panel, ["points"], [1])

        # Player 1's lag should not include player 2's data
        player1_data = panel.xs(1, level="player_id")
        self.assertEqual(player1_data["points_lag1"].iloc[1], 10)

        # Player 2's first game should have NaN lag
        player2_panel = panel.xs(2, level="player_id")
        self.assertTrue(pd.isna(player2_panel["points_lag1"].iloc[0]))


class TestRollingWindows(unittest.TestCase):
    """Test rolling window statistics."""

    def setUp(self):
        """Create panel data with constant values."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

        # Create data with constant values for easy testing
        self.panel = pd.DataFrame(
            {
                "player_id": [1] * 10,
                "game_id": [f"g{i}" for i in range(1, 11)],
                "game_date": pd.date_range("2023-01-01", periods=10),
                "points": [10] * 10,  # Constant value
            }
        )
        self.panel = self.system.create_panel_index(self.panel)

    def test_rolling_mean_constant(self):
        """Test rolling mean with constant values."""
        panel = self.system.generate_rolling_stats(
            self.panel, ["points"], [5], ["mean"]
        )

        # All rolling means should equal 10 (after 5 games)
        rolling_means = panel["points_rolling_5_mean"].iloc[4:]  # Skip first 4
        self.assertTrue(all(abs(v - 10) < 0.001 for v in rolling_means))

    def test_rolling_std_constant(self):
        """Test rolling std with constant values."""
        panel = self.system.generate_rolling_stats(self.panel, ["points"], [5], ["std"])

        # Std of constant values should be 0
        rolling_stds = panel["points_rolling_5_std"].iloc[4:]
        self.assertTrue(all(abs(v) < 0.001 for v in rolling_stds if not pd.isna(v)))

    def test_rolling_variable_values(self):
        """Test rolling stats with variable values."""
        self.panel = self.panel.reset_index()
        self.panel["points"] = [10, 20, 30, 20, 10, 20, 30, 20, 10, 20]
        self.panel = self.system.create_panel_index(self.panel)

        panel = self.system.generate_rolling_stats(
            self.panel, ["points"], [3], ["mean"]
        )

        # Check specific rolling mean
        # Games 1-3: [10, 20, 30] → mean = 20
        self.assertAlmostEqual(panel["points_rolling_3_mean"].iloc[2], 20.0)

    def test_rolling_multiple_windows(self):
        """Test multiple window sizes."""
        panel = self.system.generate_rolling_stats(
            self.panel, ["points"], [3, 5, 10], ["mean"]
        )

        self.assertIn("points_rolling_3_mean", panel.columns)
        self.assertIn("points_rolling_5_mean", panel.columns)
        self.assertIn("points_rolling_10_mean", panel.columns)

    def test_rolling_min_periods(self):
        """Test that partial windows are allowed."""
        panel = self.system.generate_rolling_stats(
            self.panel, ["points"], [5], ["mean"]
        )

        # First row should have value (min_periods=1)
        self.assertFalse(pd.isna(panel["points_rolling_5_mean"].iloc[0]))


class TestCumulativeStats(unittest.TestCase):
    """Test cumulative statistics."""

    def setUp(self):
        """Create panel data for cumulative testing."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

        self.panel = pd.DataFrame(
            {
                "player_id": [1] * 5,
                "game_id": ["g1", "g2", "g3", "g4", "g5"],
                "game_date": pd.date_range("2023-01-01", periods=5),
                "points": [10, 20, 15, 25, 30],
            }
        )
        self.panel = self.system.create_panel_index(self.panel)

    def test_cumulative_sum(self):
        """Test cumulative sum is correct."""
        panel = self.system.generate_cumulative_stats(self.panel, ["points"])

        # Check cumulative values
        self.assertEqual(panel["points_cumulative"].iloc[0], 10)
        self.assertEqual(panel["points_cumulative"].iloc[1], 30)  # 10 + 20
        self.assertEqual(panel["points_cumulative"].iloc[2], 45)  # 10 + 20 + 15
        self.assertEqual(panel["points_cumulative"].iloc[4], 100)  # Total

    def test_cumulative_games(self):
        """Test cumulative games counter."""
        panel = self.system.generate_cumulative_stats(self.panel, ["games"])

        # Should create games column if not exists
        self.assertIn("games", panel.columns)
        self.assertIn("games_cumulative", panel.columns)

        # Check game count
        self.assertEqual(panel["games_cumulative"].iloc[0], 1)
        self.assertEqual(panel["games_cumulative"].iloc[4], 5)

    def test_cumulative_multiple_players(self):
        """Test cumulative stats are per-player."""
        # Add second player
        player2 = pd.DataFrame(
            {
                "player_id": [2] * 3,
                "game_id": ["g1", "g2", "g3"],
                "game_date": pd.date_range("2023-01-01", periods=3),
                "points": [20, 30, 40],
            }
        )

        combined = pd.concat([self.panel.reset_index(), player2])
        panel = self.system.create_panel_index(combined)
        panel = self.system.generate_cumulative_stats(panel, ["points"])

        # Player 1's cumulative should not include player 2
        player1 = panel.xs(1, level="player_id")
        self.assertEqual(player1["points_cumulative"].iloc[-1], 100)

        # Player 2's cumulative
        player2_panel = panel.xs(2, level="player_id")
        self.assertEqual(player2_panel["points_cumulative"].iloc[-1], 90)


class TestTemporalQueries(unittest.TestCase):
    """Test temporal query functionality."""

    def setUp(self):
        """Create panel data with known timestamps."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

        # Create data with specific timestamps
        self.panel = pd.DataFrame(
            {
                "player_id": [1, 1, 1],
                "game_id": ["g1", "g2", "g3"],
                "game_date": [
                    datetime(2023, 1, 1, 19, 0),
                    datetime(2023, 1, 5, 19, 0),
                    datetime(2023, 1, 10, 19, 0),
                ],
                "points": [20, 25, 30],
            }
        )
        self.panel = self.system.create_panel_index(self.panel)
        self.panel = self.system.generate_cumulative_stats(self.panel, ["points"])
        self.system.panel_data = self.panel

    def test_query_at_exact_game_time(self):
        """Test query at exact game timestamp."""
        query_time = datetime(2023, 1, 5, 19, 0)  # Exactly game 2
        result = self.system.query_stats_at_time(1, query_time)

        # Should include games 1 and 2
        self.assertEqual(result["points_cumulative"], 45)  # 20 + 25

    def test_query_between_games(self):
        """Test query between games."""
        query_time = datetime(2023, 1, 7, 12, 0)  # Between game 2 and 3
        result = self.system.query_stats_at_time(1, query_time)

        # Should include up through game 2
        self.assertEqual(result["points_cumulative"], 45)

    def test_query_before_first_game(self):
        """Test query before player's first game."""
        query_time = datetime(2022, 12, 1)
        result = self.system.query_stats_at_time(1, query_time)

        # Should return error
        self.assertIn("error", result)

    def test_query_after_all_games(self):
        """Test query after all games."""
        query_time = datetime(2023, 12, 31)
        result = self.system.query_stats_at_time(1, query_time)

        # Should include all games
        self.assertEqual(result["points_cumulative"], 75)  # All 3 games

    def test_query_nonexistent_player(self):
        """Test query for non-existent player."""
        query_time = datetime(2023, 1, 5)
        result = self.system.query_stats_at_time(999, query_time)

        # Should return error
        self.assertIn("error", result)


class TestPanelTransformations(unittest.TestCase):
    """Test panel data transformations."""

    def setUp(self):
        """Create panel data with known means."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

        # Player 1: mean = 20, Player 2: mean = 30
        self.panel = pd.DataFrame(
            {
                "player_id": [1, 1, 1, 2, 2, 2],
                "game_id": ["g1", "g2", "g3", "g1", "g2", "g3"],
                "game_date": pd.date_range("2023-01-01", periods=3).tolist() * 2,
                "points": [10, 20, 30, 20, 30, 40],
            }
        )
        self.panel = self.system.create_panel_index(self.panel)

    def test_within_transform_mean_zero(self):
        """Test within transform produces mean ≈ 0."""
        demeaned = self.system.within_transform(self.panel, "points")

        # Mean should be approximately 0
        self.assertAlmostEqual(demeaned.mean(), 0.0, places=10)

    def test_within_transform_values(self):
        """Test within transform subtracts player mean."""
        demeaned = self.system.within_transform(self.panel, "points")

        # Player 1 values: [10, 20, 30] - 20 = [-10, 0, 10]
        player1 = demeaned.xs(1, level="player_id")
        self.assertAlmostEqual(player1.iloc[0], -10.0)
        self.assertAlmostEqual(player1.iloc[1], 0.0)
        self.assertAlmostEqual(player1.iloc[2], 10.0)

    def test_between_transform(self):
        """Test between transform returns player means."""
        means = self.system.between_transform(self.panel, "points")

        # Player 1 mean = 20
        player1_mean = means.xs(1, level="player_id").iloc[0]
        self.assertAlmostEqual(player1_mean, 20.0)

        # Player 2 mean = 30
        player2_mean = means.xs(2, level="player_id").iloc[0]
        self.assertAlmostEqual(player2_mean, 30.0)

    def test_first_difference(self):
        """Test first-difference transformation."""
        diff = self.system.first_difference(self.panel, "points")

        # Player 1: [10, 20, 30] → diff = [NaN, 10, 10]
        player1_diff = diff.xs(1, level="player_id")
        self.assertTrue(pd.isna(player1_diff.iloc[0]))
        self.assertAlmostEqual(player1_diff.iloc[1], 10.0)
        self.assertAlmostEqual(player1_diff.iloc[2], 10.0)

        # Player 2: [20, 30, 40] → diff = [NaN, 10, 10]
        player2_diff = diff.xs(2, level="player_id")
        self.assertTrue(pd.isna(player2_diff.iloc[0]))
        self.assertAlmostEqual(player2_diff.iloc[1], 10.0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def setUp(self):
        """Create test data."""
        self.test_data = pd.DataFrame(
            {
                "player_id": [1, 1, 1],
                "game_id": ["g1", "g2", "g3"],
                "game_date": pd.date_range("2023-01-01", periods=3),
                "points": [20, 25, 22],
                "rebounds": [5, 7, 6],
                "assists": [3, 4, 5],
            }
        )

    def test_create_panel_from_dataframe(self):
        """Test convenience function for panel creation."""
        panel = create_panel_from_dataframe(self.test_data)

        # Should be multi-indexed
        self.assertEqual(panel.index.nlevels, 3)

    def test_generate_temporal_features(self):
        """Test convenience function for feature generation."""
        panel = create_panel_from_dataframe(self.test_data)
        panel = generate_temporal_features(
            panel, base_vars=["points", "rebounds"], lags=[1], windows=[2]
        )

        # Check features created
        self.assertIn("points_lag1", panel.columns)
        self.assertIn("points_rolling_2_mean", panel.columns)
        self.assertIn("points_cumulative", panel.columns)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Create system."""
        self.system = PanelDataProcessingSystem()
        self.system.setup()

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()

        # Should raise error
        with self.assertRaises(ValueError):
            self.system.create_panel_index(empty_df)

    def test_missing_required_columns(self):
        """Test error when required columns missing."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})

        with self.assertRaises(ValueError):
            self.system.create_panel_index(df)

    def test_lag_nonexistent_variable(self):
        """Test error when lagging non-existent variable."""
        panel = self.system._create_demo_panel_data(2, 5)
        panel = self.system.create_panel_index(panel)

        with self.assertRaises(ValueError):
            self.system.generate_lags(panel, ["nonexistent"], [1])

    def test_single_game_player(self):
        """Test player with only one game."""
        df = pd.DataFrame(
            {
                "player_id": [1],
                "game_id": ["g1"],
                "game_date": [datetime(2023, 1, 1)],
                "points": [20],
            }
        )
        panel = self.system.create_panel_index(df)
        panel = self.system.generate_lags(panel, ["points"], [1])

        # Lag1 should be NaN (no previous game)
        self.assertTrue(pd.isna(panel["points_lag1"].iloc[0]))


class TestSystemExecution(unittest.TestCase):
    """Test complete system execution."""

    def test_full_execution(self):
        """Test complete execute() workflow."""
        system = PanelDataProcessingSystem()
        results = system.execute()

        # Check success
        self.assertTrue(results["success"])

        # Check steps completed
        self.assertGreater(len(results["steps_completed"]), 5)

        # Check features created
        self.assertGreater(results["features_created"], 10)

        # Check panel shape
        self.assertIsNotNone(results["panel_shape"])
        self.assertEqual(len(results["panel_shape"]), 2)  # (rows, cols)

    def test_execute_creates_features(self):
        """Test that execute creates expected features."""
        system = PanelDataProcessingSystem()
        results = system.execute()

        # Should create lags, rolling stats, cumulative stats
        self.assertGreater(results["features_created"], 0)


def run_all_tests():
    """Run all test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPanelDataStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestLagGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestRollingWindows))
    suite.addTests(loader.loadTestsFromTestCase(TestCumulativeStats))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalQueries))
    suite.addTests(loader.loadTestsFromTestCase(TestPanelTransformations))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemExecution))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    # Run all tests
    result = run_all_tests()

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
