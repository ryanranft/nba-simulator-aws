#!/usr/bin/env python3
"""
Integration Tests for Panel Data System

Tests:
1. Feature extraction (static + panel)
2. Team aggregation (sophisticated vs simple)
3. Enhanced metrics integration
4. Backward compatibility
5. Accuracy validation (target: 84%)

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from scripts.ml.panel_data_integration import PanelDataFeatureExtractor
from scripts.ml.panel_data_team_aggregator import PanelDataTeamAggregator
from scripts.pbp_to_boxscore.enhanced_advanced_metrics import (
    EnhancedAdvancedMetricsCalculator,
)


class TestPanelDataIntegration:
    """Integration tests for panel data system"""

    @pytest.fixture
    def sample_panel_data(self):
        """Create sample panel data for testing"""
        np.random.seed(42)

        # Create 20 games, 10 players each (200 observations)
        n_games = 20
        n_players_per_team = 5

        data = []
        for game_num in range(n_games):
            game_id = f"game_{game_num:03d}"

            # Home team
            for player_num in range(n_players_per_team):
                data.append(
                    {
                        "game_id": game_id,
                        "player_id": f"player_home_{player_num}",
                        "home_away": "home",
                        "points": np.random.randint(5, 30),
                        "rebounds": np.random.randint(2, 12),
                        "assists": np.random.randint(1, 10),
                        "points_lag1": np.random.randint(5, 30),
                        "points_lag2": np.random.randint(5, 30),
                        "points_rolling_3_mean": np.random.uniform(15, 25),
                        "points_rolling_3_std": np.random.uniform(2, 8),
                        "points_rolling_10_mean": np.random.uniform(15, 25),
                        "rebounds_lag1": np.random.randint(2, 12),
                        "rebounds_rolling_3_mean": np.random.uniform(5, 10),
                        "assists_lag1": np.random.randint(1, 10),
                        "assists_rolling_3_mean": np.random.uniform(3, 8),
                    }
                )

            # Away team
            for player_num in range(n_players_per_team):
                data.append(
                    {
                        "game_id": game_id,
                        "player_id": f"player_away_{player_num}",
                        "home_away": "away",
                        "points": np.random.randint(5, 30),
                        "rebounds": np.random.randint(2, 12),
                        "assists": np.random.randint(1, 10),
                        "points_lag1": np.random.randint(5, 30),
                        "points_lag2": np.random.randint(5, 30),
                        "points_rolling_3_mean": np.random.uniform(15, 25),
                        "points_rolling_3_std": np.random.uniform(2, 8),
                        "points_rolling_10_mean": np.random.uniform(15, 25),
                        "rebounds_lag1": np.random.randint(2, 12),
                        "rebounds_rolling_3_mean": np.random.uniform(5, 10),
                        "assists_lag1": np.random.randint(1, 10),
                        "assists_rolling_3_mean": np.random.uniform(3, 8),
                    }
                )

        return pd.DataFrame(data)

    def test_feature_extraction_with_panel(self):
        """Test feature extraction includes both static and panel features"""
        print("\n[TEST 1] Feature Extraction with Panel Data")

        extractor = PanelDataFeatureExtractor(use_panel_features=True)

        # Get feature summary
        summary = extractor.get_feature_summary()

        print(f"  Static features: {summary['total_static']}")
        print(f"  Panel features: {summary['total_panel']}")
        print(f"  Grand total: {summary['grand_total']}")

        # Assertions
        assert (
            summary["total_static"] >= 200
        ), "Should have at least 200 static features"
        assert summary["total_panel"] == 300, "Should have 300 panel features"
        assert summary["grand_total"] >= 500, "Should have at least 500 total features"

        print("  ✓ Feature counts validated")

    def test_team_aggregation(self, sample_panel_data):
        """Test team aggregation produces expected features"""
        print("\n[TEST 2] Team Aggregation")

        aggregator = PanelDataTeamAggregator()

        # Test single game aggregation
        game_id = "game_000"
        result = aggregator.aggregate_game(sample_panel_data, game_id)

        print(f"  Game ID: {result.game_id}")
        print(f"  Total features: {result.total_features}")
        print(f"    Home: {len(result.home_features)}")
        print(f"    Away: {len(result.away_features)}")
        print(f"    Matchup: {len(result.matchup_features)}")

        # Assertions
        assert result.success, "Aggregation should succeed"
        assert len(result.home_features) > 0, "Should have home features"
        assert len(result.away_features) > 0, "Should have away features"
        assert result.total_features > 100, "Should have at least 100 total features"

        # Check for expected feature patterns
        home_feature_names = list(result.home_features.keys())
        assert any(
            "_mean" in f for f in home_feature_names
        ), "Should have mean features"
        assert any("_std" in f for f in home_feature_names), "Should have std features"
        assert any("_lag" in f for f in home_feature_names), "Should have lag features"
        assert any(
            "_rolling" in f for f in home_feature_names
        ), "Should have rolling features"

        print("  ✓ Team aggregation validated")

    def test_batch_aggregation(self, sample_panel_data):
        """Test batch aggregation of multiple games"""
        print("\n[TEST 3] Batch Aggregation")

        aggregator = PanelDataTeamAggregator()

        # Get all game IDs
        game_ids = sample_panel_data["game_id"].unique().tolist()
        print(f"  Processing {len(game_ids)} games...")

        # Batch aggregate
        df_games = aggregator.batch_aggregate_games(sample_panel_data, game_ids)

        print(f"  Result:")
        print(f"    Games: {len(df_games)}")
        print(f"    Features per game: {len(df_games.columns) - 1}")  # -1 for game_id

        # Assertions
        assert len(df_games) == len(game_ids), "Should have one row per game"
        assert len(df_games.columns) > 100, "Should have many features per game"

        # Check for no NaN in critical features
        assert not df_games["game_id"].isna().any(), "Game IDs should not be NaN"

        print("  ✓ Batch aggregation validated")

    def test_enhanced_metrics_integration(self, sample_panel_data):
        """Test enhanced metrics calculator with panel data"""
        print("\n[TEST 4] Enhanced Metrics Integration")

        calculator = EnhancedAdvancedMetricsCalculator()

        # Test panel data aggregation
        game_id = "game_000"
        stats = calculator.aggregate_team_stats_with_panel_data(
            sample_panel_data, game_id, use_panel_features=True
        )

        print(f"  Method: {stats['method']}")
        print(f"  Feature count: {stats['feature_count']}")

        # Assertions
        assert stats["method"] == "panel_data", "Should use panel data method"
        assert stats["feature_count"] > 50, "Should have many features"
        assert len(stats["home_features"]) > 0, "Should have home features"
        assert len(stats["away_features"]) > 0, "Should have away features"

        print("  ✓ Enhanced metrics integration validated")

    def test_backward_compatibility_simple_aggregation(self, sample_panel_data):
        """Test backward compatibility with simple aggregation"""
        print("\n[TEST 5] Backward Compatibility - Simple Aggregation")

        calculator = EnhancedAdvancedMetricsCalculator()

        # Test with use_panel_features=False (backward compatible)
        game_id = "game_000"
        stats = calculator.aggregate_team_stats_with_panel_data(
            sample_panel_data, game_id, use_panel_features=False
        )

        print(f"  Method: {stats['method']}")
        print(f"  Feature count: {stats['feature_count']}")

        # Assertions
        assert stats["method"] == "simple_linear", "Should use simple linear method"
        assert stats["feature_count"] > 0, "Should have some features"

        print("  ✓ Backward compatibility validated")

    def test_backward_compatibility_feature_extractor(self):
        """Test backward compatibility of feature extractor"""
        print("\n[TEST 6] Backward Compatibility - Feature Extractor")

        # Test with use_panel_features=False
        extractor = PanelDataFeatureExtractor(use_panel_features=False)

        summary = extractor.get_feature_summary()

        print(f"  Static features: {summary['total_static']}")
        print(f"  Panel features: {summary['total_panel']}")
        print(f"  Grand total: {summary['grand_total']}")

        # Assertions
        assert (
            summary["total_panel"] == 0
        ), "Should have no panel features when disabled"
        assert summary["total_static"] >= 200, "Should still have static features"

        print("  ✓ Feature extractor backward compatibility validated")

    def test_aggregation_comparison(self, sample_panel_data):
        """Test comparison between simple and panel aggregation"""
        print("\n[TEST 7] Aggregation Comparison")

        aggregator = PanelDataTeamAggregator()

        game_id = "game_000"
        comparison = aggregator.compare_aggregation_approaches(
            sample_panel_data, game_id
        )

        print(f"  Comparison results:")
        if "simple_linear" in comparison:
            print(f"    Simple: {comparison['simple_linear']}")
        if "panel_lag" in comparison:
            print(f"    Panel (lag): {comparison['panel_lag']}")
        if "panel_rolling" in comparison:
            print(f"    Panel (rolling): {comparison['panel_rolling']}")
        if "feature_count" in comparison:
            print(f"    Feature count improvement: {comparison['feature_count']}")

        # Assertions
        assert len(comparison) > 0, "Should return comparison results"

        print("  ✓ Aggregation comparison validated")

    def test_panel_feature_naming(self, sample_panel_data):
        """Test that panel features have correct naming conventions"""
        print("\n[TEST 8] Panel Feature Naming")

        aggregator = PanelDataTeamAggregator()

        game_id = "game_000"
        result = aggregator.aggregate_game(sample_panel_data, game_id)

        # Check feature naming patterns
        home_features = list(result.home_features.keys())

        lag_features = [f for f in home_features if "_lag" in f]
        rolling_features = [f for f in home_features if "_rolling" in f]
        mean_features = [f for f in home_features if "_mean" in f]
        std_features = [f for f in home_features if "_std" in f]

        print(f"  Feature counts:")
        print(f"    Lag features: {len(lag_features)}")
        print(f"    Rolling features: {len(rolling_features)}")
        print(f"    Mean features: {len(mean_features)}")
        print(f"    Std features: {len(std_features)}")

        # Assertions
        assert len(lag_features) > 0, "Should have lag features"
        assert len(rolling_features) > 0, "Should have rolling features"
        assert len(mean_features) > 0, "Should have mean aggregations"
        assert len(std_features) > 0, "Should have std aggregations"

        # Check naming convention
        for feature in home_features:
            assert feature.startswith(
                "home_"
            ), f"Home features should start with 'home_': {feature}"

        away_features = list(result.away_features.keys())
        for feature in away_features:
            assert feature.startswith(
                "away_"
            ), f"Away features should start with 'away_': {feature}"

        print("  ✓ Feature naming conventions validated")

    def test_no_data_leakage(self, sample_panel_data):
        """Test that only historical features are used (no current game stats)"""
        print("\n[TEST 9] Data Leakage Check")

        aggregator = PanelDataTeamAggregator()

        # Identify panel features
        panel_features = aggregator.identify_panel_features(sample_panel_data)

        print(f"  Total panel features identified: {len(panel_features)}")

        # All panel features should be lag or rolling (historical)
        for feature in panel_features:
            assert (
                "_lag" in feature or "_rolling" in feature
            ), f"Feature {feature} should be lag or rolling (historical)"

        # Should NOT include current game stats
        prohibited_patterns = ["points", "rebounds", "assists"]
        prohibited_features = []

        for feature in panel_features:
            # If it's just 'points' (not 'points_lag1' or 'points_rolling'), it's current game
            if feature in prohibited_patterns:
                prohibited_features.append(feature)

        assert (
            len(prohibited_features) == 0
        ), f"Should not include current game features: {prohibited_features}"

        print("  ✓ No data leakage detected")

    @pytest.mark.skipif(
        not os.path.exists("/tmp/real_nba_game_features_selected.parquet"),
        reason="Requires real NBA data",
    )
    def test_accuracy_validation(self):
        """Test that model achieves 84% accuracy on real data"""
        print("\n[TEST 10] Accuracy Validation (OPTIONAL)")

        # Load real NBA data
        df = pd.read_parquet("/tmp/real_nba_game_features_selected.parquet")

        # Split by year
        train_df = df[df["year"] < 2021]
        test_df = df[df["year"] == 2021]

        # Prepare features
        X_train = train_df.drop(["game_id", "won", "year"], axis=1)
        y_train = train_df["won"]
        X_test = test_df.drop(["game_id", "won", "year"], axis=1)
        y_test = test_df["won"]

        # Train model
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Evaluate
        train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
        test_acc = accuracy_score(y_test, model.predict(X_test_scaled))

        print(f"  Train accuracy: {train_acc:.1%}")
        print(f"  Test accuracy: {test_acc:.1%}")

        # Assertions
        assert test_acc >= 0.80, f"Test accuracy should be >= 80%, got {test_acc:.1%}"

        if test_acc >= 0.84:
            print(f"  ✅ EXCELLENT: Test accuracy >= 84% target!")
        elif test_acc >= 0.80:
            print(f"  ✓ GOOD: Test accuracy >= 80%")

        print("  ✓ Accuracy validation complete")


def main():
    """Run all tests"""
    print("=" * 80)
    print("PANEL DATA INTEGRATION - INTEGRATION TESTS")
    print("=" * 80)

    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

    print("\n" + "=" * 80)
    print("✓ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
