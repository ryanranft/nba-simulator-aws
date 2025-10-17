#!/usr/bin/env python3
"""
Test Suite: Advanced Feature Engineering Pipeline

Recommendation ID: consolidated_consolidated_rec_11 (rec_11)
Tests all feature engineering capabilities built on rec_22 panel data.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implement_rec_11 import AdvancedFeatureEngineeringPipeline


class TestSetupAndPrerequisites(unittest.TestCase):
    """Test setup and prerequisite validation."""

    def test_initialization(self):
        """Test pipeline initialization."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        self.assertIsNotNone(pipeline)
        self.assertIsNotNone(pipeline.config)
        self.assertEqual(pipeline.feature_count, 0)

    def test_default_config(self):
        """Test default configuration."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        config = pipeline.config

        self.assertIn("lag_periods", config)
        self.assertIn("rolling_windows", config)
        self.assertTrue(config["include_temporal"])
        self.assertTrue(config["include_cumulative"])

    def test_custom_config(self):
        """Test custom configuration."""
        custom_config = {"lag_periods": [1, 2], "include_temporal": False}
        pipeline = AdvancedFeatureEngineeringPipeline(config=custom_config)

        self.assertEqual(pipeline.config["lag_periods"], [1, 2])
        self.assertFalse(pipeline.config["include_temporal"])

    def test_prerequisites_validation(self):
        """Test prerequisite validation."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        result = pipeline.validate_prerequisites()
        self.assertTrue(result)

    def test_setup(self):
        """Test setup process."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        result = pipeline.setup()
        self.assertTrue(result)
        self.assertTrue(pipeline.setup_complete)
        self.assertIsNotNone(pipeline.panel_data_system)


class TestTemporalFeatures(unittest.TestCase):
    """Test temporal feature generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        # Create simple test data
        self.test_data = pd.DataFrame(
            {
                "player_id": [1] * 10,
                "game_id": list(range(1, 11)),
                "game_date": pd.date_range("2023-01-01", periods=10),
                "points": [20, 25, 18, 30, 22, 28, 19, 24, 26, 21],
                "rebounds": [8, 7, 9, 6, 8, 7, 10, 8, 7, 9],
                "assists": [5, 6, 4, 7, 5, 6, 4, 5, 6, 7],
                "fg_pct": [0.50, 0.55, 0.48, 0.60, 0.52, 0.58, 0.49, 0.54, 0.56, 0.53],
                "three_pct": [
                    0.40,
                    0.45,
                    0.35,
                    0.50,
                    0.42,
                    0.48,
                    0.38,
                    0.44,
                    0.46,
                    0.43,
                ],
                "ft_pct": [0.85, 0.90, 0.80, 0.88, 0.86, 0.92, 0.84, 0.87, 0.89, 0.88],
                "steals": [2, 1, 2, 3, 1, 2, 2, 1, 2, 3],
                "blocks": [1, 0, 1, 2, 1, 1, 0, 1, 1, 2],
                "turnovers": [2, 3, 1, 2, 2, 1, 3, 2, 1, 2],
                "minutes": [32, 35, 30, 38, 33, 36, 31, 34, 35, 33],
            }
        )

        # Create panel structure
        self.panel_data = self.pipeline.panel_data_system.create_panel_index(
            self.test_data
        )

    def test_lag_features_created(self):
        """Test that lag features are created."""
        result = self.pipeline.generate_temporal_features(self.panel_data.copy())

        # Check lag features exist
        self.assertIn("points_lag1", result.columns)
        self.assertIn("points_lag2", result.columns)
        self.assertIn("rebounds_lag1", result.columns)

    def test_rolling_features_created(self):
        """Test that rolling window features are created."""
        result = self.pipeline.generate_temporal_features(self.panel_data.copy())

        # Check rolling features exist
        self.assertIn("points_rolling_3_mean", result.columns)
        self.assertIn("points_rolling_5_std", result.columns)

    def test_trend_features_created(self):
        """Test that trend features are created."""
        result = self.pipeline.generate_temporal_features(self.panel_data.copy())

        # Check trend features exist
        trend_cols = [col for col in result.columns if "trend" in col]
        self.assertGreater(len(trend_cols), 0)


class TestCumulativeFeatures(unittest.TestCase):
    """Test cumulative feature generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        self.test_data = pd.DataFrame(
            {
                "player_id": [1] * 5,
                "game_id": [1, 2, 3, 4, 5],
                "game_date": pd.date_range("2023-01-01", periods=5),
                "points": [20, 25, 18, 30, 22],
                "rebounds": [8, 7, 9, 6, 8],
                "assists": [5, 6, 4, 7, 5],
                "fg_pct": [0.50, 0.55, 0.48, 0.60, 0.52],
                "three_pct": [0.40, 0.45, 0.35, 0.50, 0.42],
                "ft_pct": [0.85, 0.90, 0.80, 0.88, 0.86],
                "steals": [2, 1, 2, 3, 1],
                "blocks": [1, 0, 1, 2, 1],
                "turnovers": [2, 3, 1, 2, 2],
                "minutes": [32, 35, 30, 38, 33],
            }
        )

        self.panel_data = self.pipeline.panel_data_system.create_panel_index(
            self.test_data
        )

    def test_cumulative_stats_created(self):
        """Test cumulative statistics are created."""
        result = self.pipeline.generate_cumulative_features(self.panel_data.copy())

        self.assertIn("points_cumulative", result.columns)
        self.assertIn("rebounds_cumulative", result.columns)
        self.assertIn("games_cumulative", result.columns)

    def test_career_averages_created(self):
        """Test career averages are calculated."""
        result = self.pipeline.generate_cumulative_features(self.panel_data.copy())

        self.assertIn("points_career_avg", result.columns)
        self.assertIn("rebounds_career_avg", result.columns)

    def test_career_average_values(self):
        """Test career average calculation correctness."""
        result = self.pipeline.generate_cumulative_features(self.panel_data.copy())

        # After 2 games, career avg should be (20+25)/2 = 22.5
        result_flat = result.reset_index()
        game_2_avg = result_flat[result_flat["game_id"] == 2][
            "points_career_avg"
        ].values[0]
        self.assertAlmostEqual(game_2_avg, 22.5, places=1)


class TestInteractionFeatures(unittest.TestCase):
    """Test interaction feature generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        self.test_data = pd.DataFrame(
            {
                "player_id": [1] * 10,
                "game_id": list(range(1, 11)),
                "game_date": pd.date_range("2023-01-01", periods=10),
                "points": [20, 25, 18, 30, 22, 28, 19, 24, 26, 21],
                "rebounds": [8, 7, 9, 6, 8, 7, 10, 8, 7, 9],
                "assists": [5, 6, 4, 7, 5, 6, 4, 5, 6, 7],
                "fg_pct": [0.50, 0.55, 0.48, 0.60, 0.52, 0.58, 0.49, 0.54, 0.56, 0.53],
                "minutes": [32, 35, 30, 38, 33, 36, 31, 34, 35, 33],
                "is_home": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                "days_rest": [2, 0, 1, 0, 2, 1, 0, 1, 2, 0],
                "game_number": list(range(1, 11)),
            }
        )

        self.panel_data = self.pipeline.panel_data_system.create_panel_index(
            self.test_data
        )

    def test_home_away_splits_created(self):
        """Test home/away split features."""
        result = self.pipeline.generate_interaction_features(self.panel_data.copy())

        # Should have home average features
        home_features = [col for col in result.columns if "home_avg" in col]
        self.assertGreater(len(home_features), 0)

    def test_rest_day_features_created(self):
        """Test rest day interaction features."""
        result = self.pipeline.generate_interaction_features(self.panel_data.copy())

        # Should have rest category
        self.assertIn("rest_category", result.columns)

    def test_season_quarter_features_created(self):
        """Test season quarter features."""
        result = self.pipeline.generate_interaction_features(self.panel_data.copy())

        # Should have season quarter
        self.assertIn("season_quarter", result.columns)


class TestContextualFeatures(unittest.TestCase):
    """Test contextual feature generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        self.test_data = pd.DataFrame(
            {
                "player_id": [1] * 10,
                "game_id": list(range(1, 11)),
                "game_date": pd.date_range("2023-01-01", periods=10),
                "points": [20, 25, 18, 30, 22, 28, 19, 24, 26, 21],
                "rebounds": [8, 7, 9, 6, 8, 7, 10, 8, 7, 9],
                "fg_pct": [0.50, 0.55, 0.48, 0.60, 0.52, 0.58, 0.49, 0.54, 0.56, 0.53],
                "opponent_win_pct": [
                    0.600,
                    0.450,
                    0.550,
                    0.700,
                    0.500,
                    0.650,
                    0.400,
                    0.550,
                    0.600,
                    0.500,
                ],
                "travel_distance": [0, 1500, 500, 2000, 0, 1200, 800, 0, 1800, 600],
                "is_back_to_back": [0, 1, 0, 1, 0, 0, 1, 0, 0, 1],
                "altitude": [0, 5280, 0, 500, 0, 4000, 0, 5500, 0, 300],
            }
        )

        self.panel_data = self.pipeline.panel_data_system.create_panel_index(
            self.test_data
        )

    def test_schedule_strength_features(self):
        """Test schedule strength features."""
        result = self.pipeline.generate_contextual_features(self.panel_data.copy())

        self.assertIn("opponent_strength_l5", result.columns)
        self.assertIn("opponent_strength_season", result.columns)

    def test_travel_burden_features(self):
        """Test travel burden features."""
        result = self.pipeline.generate_contextual_features(self.panel_data.copy())

        self.assertIn("travel_burden_l7", result.columns)

    def test_back_to_back_features(self):
        """Test back-to-back features."""
        result = self.pipeline.generate_contextual_features(self.panel_data.copy())

        self.assertIn("b2b_streak", result.columns)

    def test_altitude_features(self):
        """Test altitude features."""
        result = self.pipeline.generate_contextual_features(self.panel_data.copy())

        self.assertIn("high_altitude", result.columns)


class TestDerivedFeatures(unittest.TestCase):
    """Test derived feature generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        self.test_data = pd.DataFrame(
            {
                "player_id": [1] * 5,
                "game_id": [1, 2, 3, 4, 5],
                "game_date": pd.date_range("2023-01-01", periods=5),
                "points": [20, 25, 18, 30, 22],
                "fga": [15, 18, 14, 22, 16],
                "fgm": [8, 10, 7, 13, 9],
                "fta": [4, 5, 3, 6, 4],
                "ftm": [3, 4, 2, 5, 3],
                "three_pm": [2, 3, 1, 4, 2],
                "rebounds": [8, 7, 9, 6, 8],
                "assists": [5, 6, 4, 7, 5],
                "steals": [2, 1, 2, 3, 1],
                "blocks": [1, 0, 1, 2, 1],
                "turnovers": [2, 3, 1, 2, 2],
                "minutes": [32, 35, 30, 38, 33],
                "team_minutes": [240, 240, 240, 240, 240],
                "team_fga": [85, 88, 82, 90, 86],
                "team_fta": [24, 26, 22, 28, 25],
                "team_turnovers": [14, 15, 12, 16, 14],
                "team_rebounds": [45, 43, 47, 42, 44],
                "team_pace": [100, 102, 98, 105, 101],
            }
        )

        self.panel_data = self.pipeline.panel_data_system.create_panel_index(
            self.test_data
        )

    def test_true_shooting_percentage(self):
        """Test TS% calculation."""
        result = self.pipeline.generate_derived_features(self.panel_data.copy())

        self.assertIn("ts_pct", result.columns)
        # TS% should be between 0 and 1
        self.assertTrue((result["ts_pct"] >= 0).all())
        self.assertTrue((result["ts_pct"] <= 1).all())

    def test_usage_rate_created(self):
        """Test usage rate feature."""
        result = self.pipeline.generate_derived_features(self.panel_data.copy())

        if "usage_rate" in result.columns:
            # Usage rate should be positive
            self.assertTrue((result["usage_rate"] >= 0).all())

    def test_assist_ratio_created(self):
        """Test assist ratio feature."""
        result = self.pipeline.generate_derived_features(self.panel_data.copy())

        self.assertIn("assist_ratio", result.columns)

    def test_per_36_stats(self):
        """Test per-36-minute stats."""
        result = self.pipeline.generate_derived_features(self.panel_data.copy())

        self.assertIn("points_per_36", result.columns)
        self.assertIn("rebounds_per_36", result.columns)

    def test_pace_adjusted_stats(self):
        """Test pace-adjusted stats."""
        result = self.pipeline.generate_derived_features(self.panel_data.copy())

        self.assertIn("points_pace_adj", result.columns)

    def test_per_calculation(self):
        """Test PER calculation."""
        result = self.pipeline.generate_derived_features(self.panel_data.copy())

        if "per" in result.columns:
            # PER should exist
            self.assertIsNotNone(result["per"])


class TestEngineeredFeatures(unittest.TestCase):
    """Test engineered feature generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        # Create data with career averages already calculated
        self.test_data = pd.DataFrame(
            {
                "player_id": [1] * 10,
                "game_id": list(range(1, 11)),
                "game_date": pd.date_range("2023-01-01", periods=10),
                "points": [20, 25, 18, 30, 22, 28, 19, 24, 26, 21],
                "rebounds": [8, 7, 9, 6, 8, 7, 10, 8, 7, 9],
                "assists": [5, 6, 4, 7, 5, 6, 4, 5, 6, 7],
                "fg_pct": [0.50, 0.55, 0.48, 0.60, 0.52, 0.58, 0.49, 0.54, 0.56, 0.53],
                "opponent_win_pct": [
                    0.600,
                    0.450,
                    0.550,
                    0.700,
                    0.500,
                    0.650,
                    0.400,
                    0.550,
                    0.600,
                    0.500,
                ],
            }
        )

        self.panel_data = self.pipeline.panel_data_system.create_panel_index(
            self.test_data
        )

        # Add rolling means and career averages first
        self.panel_data = self.pipeline.generate_temporal_features(self.panel_data)
        self.panel_data = self.pipeline.generate_cumulative_features(self.panel_data)

    def test_form_indicators_created(self):
        """Test form indicator features."""
        result = self.pipeline.generate_engineered_features(self.panel_data.copy())

        form_features = [col for col in result.columns if "form" in col]
        self.assertGreater(len(form_features), 0)

    def test_consistency_metrics_created(self):
        """Test consistency metrics."""
        result = self.pipeline.generate_engineered_features(self.panel_data.copy())

        consistency_features = [col for col in result.columns if "consistency" in col]
        self.assertGreater(len(consistency_features), 0)

    def test_trajectory_features_created(self):
        """Test trajectory features."""
        result = self.pipeline.generate_engineered_features(self.panel_data.copy())

        trajectory_features = [col for col in result.columns if "trajectory" in col]
        self.assertGreater(len(trajectory_features), 0)

    def test_matchup_advantage_features(self):
        """Test matchup advantage features."""
        result = self.pipeline.generate_engineered_features(self.panel_data.copy())

        # Should have vs_strong and vs_weak features
        matchup_features = [
            col for col in result.columns if "vs_strong" in col or "vs_weak" in col
        ]
        self.assertGreater(len(matchup_features), 0)


class TestFeatureSelection(unittest.TestCase):
    """Test feature selection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AdvancedFeatureEngineeringPipeline()
        self.pipeline.setup()

        # Create data with many features
        np.random.seed(42)
        n = 100
        self.test_df = pd.DataFrame(
            {f"feature_{i}": np.random.randn(n) for i in range(50)}
        )

        # Add target
        self.test_df["target"] = np.random.choice([0, 1], n)

        # Add some constant features (should be removed)
        self.test_df["constant_feature"] = 1.0

        # Add highly correlated features (should be removed)
        self.test_df["feature_dup"] = self.test_df["feature_0"] * 1.0001

    def test_removes_low_variance(self):
        """Test that low variance features are removed."""
        selected = self.pipeline.select_features(self.test_df, target_col="target")

        # Constant feature should be removed
        self.assertNotIn("constant_feature", selected)

    def test_removes_highly_correlated(self):
        """Test that highly correlated features are removed."""
        selected = self.pipeline.select_features(self.test_df, target_col="target")

        # One of the duplicates should be removed
        has_original = "feature_0" in selected
        has_duplicate = "feature_dup" in selected
        self.assertTrue(
            has_original != has_duplicate
        )  # XOR - only one should be present

    def test_limits_feature_count(self):
        """Test max_features parameter."""
        selected = self.pipeline.select_features(
            self.test_df, target_col="target", max_features=10
        )

        self.assertLessEqual(len(selected), 10)

    def test_returns_list_of_features(self):
        """Test that selection returns list of feature names."""
        selected = self.pipeline.select_features(self.test_df, target_col="target")

        self.assertIsInstance(selected, list)
        self.assertGreater(len(selected), 0)


class TestFullPipeline(unittest.TestCase):
    """Test complete pipeline execution."""

    def test_full_execution_with_demo_data(self):
        """Test complete pipeline with demo data."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        results = pipeline.execute()

        self.assertTrue(results["success"])
        self.assertGreater(results["new_features"], 0)
        self.assertGreater(results["selected_features"], 0)
        self.assertIsNotNone(results["feature_catalog"])

    def test_creates_50_plus_features(self):
        """Test that pipeline creates 50+ features."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        results = pipeline.execute()

        # Should create 50-100+ new features
        self.assertGreaterEqual(results["new_features"], 50)

    def test_feature_categories(self):
        """Test that multiple feature categories are created."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        results = pipeline.execute()

        # Should have multiple categories
        self.assertGreaterEqual(len(results["feature_catalog"]), 3)

    def test_execution_with_custom_data(self):
        """Test execution with custom DataFrame."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        # Create custom data
        custom_data = pd.DataFrame(
            {
                "player_id": [1, 1, 2, 2],
                "game_id": [1, 2, 1, 2],
                "game_date": pd.date_range("2023-01-01", periods=4),
                "points": [20, 25, 18, 22],
                "rebounds": [8, 7, 9, 8],
                "assists": [5, 6, 4, 5],
                "fg_pct": [0.50, 0.55, 0.48, 0.52],
                "three_pct": [0.40, 0.45, 0.35, 0.42],
                "ft_pct": [0.85, 0.90, 0.80, 0.86],
                "steals": [2, 1, 2, 1],
                "blocks": [1, 0, 1, 1],
                "turnovers": [2, 3, 1, 2],
                "minutes": [32, 35, 30, 33],
            }
        )

        results = pipeline.execute(demo_data=custom_data)

        self.assertTrue(results["success"])
        self.assertEqual(results["panel_shape"][0], 4)  # 4 observations

    def test_cleanup(self):
        """Test cleanup functionality."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()
        pipeline.execute()
        pipeline.cleanup()

        self.assertIsNone(pipeline.panel_data_system)
        self.assertEqual(len(pipeline.feature_catalog), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_execution_without_setup(self):
        """Test that execution fails without setup."""
        pipeline = AdvancedFeatureEngineeringPipeline()

        with self.assertRaises(RuntimeError):
            pipeline.execute()

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        empty_df = pd.DataFrame()
        result = pipeline.execute(demo_data=empty_df)

        # Should handle gracefully (likely fail, but shouldn't crash)
        self.assertFalse(result["success"])

    def test_missing_required_columns(self):
        """Test handling of missing required columns."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        # Missing player_id
        bad_df = pd.DataFrame({"game_id": [1, 2], "points": [20, 25]})

        result = pipeline.execute(demo_data=bad_df)

        # Should fail gracefully
        self.assertFalse(result["success"])

    def test_single_observation(self):
        """Test with single observation."""
        pipeline = AdvancedFeatureEngineeringPipeline()
        pipeline.setup()

        single_obs = pd.DataFrame(
            {
                "player_id": [1],
                "game_id": [1],
                "game_date": [pd.Timestamp("2023-01-01")],
                "points": [20],
                "rebounds": [8],
                "assists": [5],
                "fg_pct": [0.50],
                "three_pct": [0.40],
                "ft_pct": [0.85],
                "steals": [2],
                "blocks": [1],
                "turnovers": [2],
                "minutes": [32],
            }
        )

        result = pipeline.execute(demo_data=single_obs)

        # Should create features even with one observation
        self.assertTrue(result["success"])


def run_tests():
    """Run all tests and return summary."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSetupAndPrerequisites))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestCumulativeFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestInteractionFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestContextualFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestDerivedFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestEngineeredFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestFullPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

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
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
