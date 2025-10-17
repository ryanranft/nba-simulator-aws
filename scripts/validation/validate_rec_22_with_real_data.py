#!/usr/bin/env python3
"""
Validate Panel Data System (rec_22) with Real NBA Data

Purpose:
- Test rec_22 implementation with 76,943 real player-game records
- Validate all panel features work with production data
- Measure performance and data quality

Phase: 1 of Re-Implementation Plan
Expected: All 33 tests pass + real data validation

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings

warnings.filterwarnings("ignore")

# Add path for implementation
sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws")
sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws/docs/phases/phase_0")

from implement_rec_22 import (
    PanelDataProcessingSystem,
    create_panel_from_dataframe,
    generate_temporal_features,
)


class RealDataValidator:
    """Validates panel data system with real NBA data"""

    def __init__(self):
        self.system = PanelDataProcessingSystem()
        self.system.setup()
        self.results = {
            "success": False,
            "tests_passed": [],
            "tests_failed": [],
            "performance": {},
            "data_quality": {},
        }

    def load_real_nba_data(self) -> pd.DataFrame:
        """Load real player data from S3 (76,943 records)"""
        print("\n" + "=" * 80)
        print("STEP 1: Loading Real NBA Data")
        print("=" * 80)

        start_time = time.time()

        # Load from parquet
        df = pd.read_parquet("/tmp/recent_player_data.parquet")

        load_time = time.time() - start_time

        print(f"\n✓ Loaded {len(df):,} player-game records")
        print(f"  Players: {df['athlete_id'].nunique():,}")
        print(f"  Games: {df['game_id'].nunique():,}")
        if "season" in df.columns:
            print(f"  Seasons: {sorted(df['season'].unique())}")
        elif "season_type" in df.columns:
            print(f"  Season types: {df['season_type'].unique()}")
        print(f"  Load time: {load_time:.2f}s")

        self.results["performance"]["load_time"] = load_time
        self.results["data_quality"]["total_records"] = len(df)
        self.results["data_quality"]["unique_players"] = df["athlete_id"].nunique()
        self.results["data_quality"]["unique_games"] = df["game_id"].nunique()

        return df

    def prepare_for_panel(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for panel structure"""
        print("\n" + "=" * 80)
        print("STEP 2: Preparing Data for Panel Structure")
        print("=" * 80)

        # Rename columns to match panel expectations
        df_panel = df.copy()

        # Map to expected column names
        column_mapping = {
            "athlete_id": "player_id",
            "game_id": "game_id",
            "game_date": "game_date",
            "points": "points",
            "rebounds": "rebounds",
            "assists": "assists",
            "steals": "steals",
            "blocks": "blocks",
            "turnovers": "turnovers",
            "minutes": "minutes",
        }

        # Rename columns that exist
        rename_dict = {k: v for k, v in column_mapping.items() if k in df_panel.columns}
        df_panel = df_panel.rename(columns=rename_dict)

        # Ensure required columns exist
        required_cols = ["player_id", "game_id", "game_date"]
        missing = [col for col in required_cols if col not in df_panel.columns]
        if missing:
            print(f"  ⚠️  Missing columns: {missing}")
            return pd.DataFrame()

        # Convert game_date to datetime
        if "game_date" in df_panel.columns:
            df_panel["game_date"] = pd.to_datetime(df_panel["game_date"])

        print(f"\n✓ Prepared {len(df_panel):,} records for panel processing")
        print(f"  Columns: {list(df_panel.columns[:10])}...")

        return df_panel

    def test_panel_index_creation(self, df: pd.DataFrame) -> bool:
        """Test 1: Panel index creation with real data"""
        print("\n" + "=" * 80)
        print("TEST 1: Panel Index Creation")
        print("=" * 80)

        try:
            start_time = time.time()

            panel = self.system.create_panel_index(df)

            creation_time = time.time() - start_time

            # Validate
            assert panel.index.nlevels == 3, "Index should have 3 levels"
            assert panel.index.names == [
                "player_id",
                "game_id",
                "timestamp",
            ], "Index names incorrect"
            assert not panel.index.duplicated().any(), "Duplicate indices found"

            n_players = panel.index.get_level_values("player_id").nunique()
            n_games = panel.index.get_level_values("game_id").nunique()

            print(f"\n✓ Panel index created successfully")
            print(f"  Shape: {panel.shape}")
            print(f"  Players: {n_players:,}")
            print(f"  Games: {n_games:,}")
            print(f"  Time: {creation_time:.2f}s")

            self.results["performance"]["index_creation_time"] = creation_time
            self.results["tests_passed"].append("panel_index_creation")

            return True, panel

        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            self.results["tests_failed"].append(("panel_index_creation", str(e)))
            return False, None

    def test_lag_generation(self, panel: pd.DataFrame) -> bool:
        """Test 2: Lag variable generation"""
        print("\n" + "=" * 80)
        print("TEST 2: Lag Variable Generation")
        print("=" * 80)

        try:
            start_time = time.time()

            # Test with real stats
            lags = [1, 2, 3, 5, 10]
            variables = ["points", "rebounds", "assists"]

            panel_with_lags = self.system.generate_lags(panel, variables, lags)

            lag_time = time.time() - start_time

            # Validate
            expected_cols = [f"{var}_lag{lag}" for var in variables for lag in lags]
            for col in expected_cols:
                assert col in panel_with_lags.columns, f"Missing lag column: {col}"

            # Check a specific lag value for first player
            first_player = panel_with_lags.index.get_level_values("player_id").unique()[
                0
            ]
            player_data = panel_with_lags.xs(first_player, level="player_id")

            if len(player_data) >= 2:
                # Second game's lag1 should equal first game's value
                points_game1 = player_data["points"].iloc[0]
                points_lag1_game2 = player_data["points_lag1"].iloc[1]

                if not pd.isna(points_lag1_game2):
                    assert (
                        abs(points_game1 - points_lag1_game2) < 0.01
                    ), "Lag values incorrect"

            print(f"\n✓ Lag generation successful")
            print(f"  Variables: {len(variables)}")
            print(f"  Lags: {lags}")
            print(f"  Features created: {len(expected_cols)}")
            print(f"  Time: {lag_time:.2f}s")

            self.results["performance"]["lag_generation_time"] = lag_time
            self.results["tests_passed"].append("lag_generation")

            return True, panel_with_lags

        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            self.results["tests_failed"].append(("lag_generation", str(e)))
            return False, None

    def test_rolling_windows(self, panel: pd.DataFrame) -> bool:
        """Test 3: Rolling window statistics"""
        print("\n" + "=" * 80)
        print("TEST 3: Rolling Window Statistics")
        print("=" * 80)

        try:
            start_time = time.time()

            windows = [3, 5, 10, 20]
            variables = ["points", "rebounds", "assists"]
            stats = ["mean", "std"]

            panel_with_rolling = self.system.generate_rolling_stats(
                panel, variables, windows, stats
            )

            rolling_time = time.time() - start_time

            # Validate
            expected_cols = [
                f"{var}_rolling_{window}_{stat}"
                for var in variables
                for window in windows
                for stat in stats
            ]

            for col in expected_cols:
                assert (
                    col in panel_with_rolling.columns
                ), f"Missing rolling column: {col}"

            print(f"\n✓ Rolling window generation successful")
            print(f"  Variables: {len(variables)}")
            print(f"  Windows: {windows}")
            print(f"  Stats: {stats}")
            print(f"  Features created: {len(expected_cols)}")
            print(f"  Time: {rolling_time:.2f}s")

            self.results["performance"]["rolling_generation_time"] = rolling_time
            self.results["tests_passed"].append("rolling_windows")

            return True, panel_with_rolling

        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            self.results["tests_failed"].append(("rolling_windows", str(e)))
            return False, None

    def test_cumulative_stats(self, panel: pd.DataFrame) -> bool:
        """Test 4: Cumulative statistics"""
        print("\n" + "=" * 80)
        print("TEST 4: Cumulative Statistics")
        print("=" * 80)

        try:
            start_time = time.time()

            variables = ["points", "rebounds", "assists", "games"]

            panel_with_cumulative = self.system.generate_cumulative_stats(
                panel, variables
            )

            cumulative_time = time.time() - start_time

            # Validate
            expected_cols = [f"{var}_cumulative" for var in variables]

            for col in expected_cols:
                assert (
                    col in panel_with_cumulative.columns
                ), f"Missing cumulative column: {col}"

            # Check that cumulative increases
            first_player = panel_with_cumulative.index.get_level_values(
                "player_id"
            ).unique()[0]
            player_data = panel_with_cumulative.xs(first_player, level="player_id")

            if len(player_data) >= 2:
                points_cum1 = player_data["points_cumulative"].iloc[0]
                points_cum2 = player_data["points_cumulative"].iloc[1]
                assert points_cum2 >= points_cum1, "Cumulative should increase"

            print(f"\n✓ Cumulative statistics successful")
            print(f"  Variables: {len(variables)}")
            print(f"  Features created: {len(expected_cols)}")
            print(f"  Time: {cumulative_time:.2f}s")

            self.results["performance"]["cumulative_generation_time"] = cumulative_time
            self.results["tests_passed"].append("cumulative_stats")

            return True, panel_with_cumulative

        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            self.results["tests_failed"].append(("cumulative_stats", str(e)))
            return False, None

    def test_temporal_query(self, panel: pd.DataFrame) -> bool:
        """Test 5: Temporal query functionality"""
        print("\n" + "=" * 80)
        print("TEST 5: Temporal Query Functionality")
        print("=" * 80)

        try:
            # Store panel for queries
            self.system.panel_data = panel

            # Query first player at latest timestamp
            first_player = panel.index.get_level_values("player_id").unique()[0]
            latest_time = panel.index.get_level_values("timestamp").max()

            result = self.system.query_stats_at_time(first_player, latest_time)

            # Validate
            assert "error" not in result, "Query returned error"
            assert "points_cumulative" in result, "Missing cumulative stats"

            print(f"\n✓ Temporal query successful")
            print(f"  Player ID: {first_player}")
            print(f"  Query time: {latest_time}")
            print(f"  Points cumulative: {result.get('points_cumulative', 'N/A')}")
            print(f"  Games played: {result.get('games_cumulative', 'N/A')}")

            self.results["tests_passed"].append("temporal_query")

            return True

        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            self.results["tests_failed"].append(("temporal_query", str(e)))
            return False

    def test_data_quality(self, panel: pd.DataFrame) -> bool:
        """Test 6: Data quality checks"""
        print("\n" + "=" * 80)
        print("TEST 6: Data Quality Checks")
        print("=" * 80)

        try:
            # Check for data leakage (lags should not look forward)
            lag_cols = [col for col in panel.columns if "_lag" in col]
            if lag_cols:
                # First observation of each player should have NaN lags
                for player_id in panel.index.get_level_values("player_id").unique()[:5]:
                    player_data = panel.xs(player_id, level="player_id")
                    first_game_lags = player_data[lag_cols].iloc[0]
                    # All lags in first game should be NaN
                    assert (
                        first_game_lags.isna().all()
                    ), f"Data leakage detected for player {player_id}"

            # Check temporal ordering
            for player_id in panel.index.get_level_values("player_id").unique()[:10]:
                player_data = panel.xs(player_id, level="player_id")
                timestamps = player_data.index.get_level_values("timestamp")
                assert (
                    timestamps.is_monotonic_increasing
                ), f"Temporal ordering violated for player {player_id}"

            print(f"\n✓ Data quality checks passed")
            print(f"  ✓ No data leakage detected")
            print(f"  ✓ Temporal ordering maintained")
            print(f"  ✓ Index structure valid")

            self.results["tests_passed"].append("data_quality")

            return True

        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            self.results["tests_failed"].append(("data_quality", str(e)))
            return False

    def count_features_generated(self, panel: pd.DataFrame) -> int:
        """Count total panel features generated"""
        lag_cols = [col for col in panel.columns if "_lag" in col]
        rolling_cols = [col for col in panel.columns if "_rolling_" in col]
        cumulative_cols = [col for col in panel.columns if "_cumulative" in col]

        total = len(lag_cols) + len(rolling_cols) + len(cumulative_cols)

        print(f"\n" + "=" * 80)
        print("FEATURE COUNT")
        print("=" * 80)
        print(f"  Lag features: {len(lag_cols)}")
        print(f"  Rolling features: {len(rolling_cols)}")
        print(f"  Cumulative features: {len(cumulative_cols)}")
        print(f"  Total panel features: {total}")

        self.results["data_quality"]["total_features"] = total
        self.results["data_quality"]["lag_features"] = len(lag_cols)
        self.results["data_quality"]["rolling_features"] = len(rolling_cols)
        self.results["data_quality"]["cumulative_features"] = len(cumulative_cols)

        return total

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT: rec_22 with Real NBA Data")
        print("=" * 80)

        print(f"\nTests Passed: {len(self.results['tests_passed'])}")
        for test in self.results["tests_passed"]:
            print(f"  ✓ {test}")

        if self.results["tests_failed"]:
            print(f"\nTests Failed: {len(self.results['tests_failed'])}")
            for test, error in self.results["tests_failed"]:
                print(f"  ✗ {test}: {error}")

        print(f"\nPerformance:")
        for metric, value in self.results["performance"].items():
            print(f"  {metric}: {value:.2f}s")

        print(f"\nData Quality:")
        for metric, value in self.results["data_quality"].items():
            print(f"  {metric}: {value:,}")

        total_time = sum(self.results["performance"].values())
        print(f"\nTotal validation time: {total_time:.2f}s")

        # Success determination
        self.results["success"] = len(self.results["tests_failed"]) == 0

        if self.results["success"]:
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED - rec_22 validated with real NBA data")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("❌ SOME TESTS FAILED - See errors above")
            print("=" * 80)

        return self.results

    def run_full_validation(self):
        """Run complete validation suite"""
        print("\n" + "=" * 80)
        print("VALIDATING rec_22 (Panel Data System) WITH REAL NBA DATA")
        print("=" * 80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data source: /tmp/recent_player_data.parquet")

        overall_start = time.time()

        # Load data
        df = self.load_real_nba_data()
        if df.empty:
            print("\n❌ Failed to load data")
            return self.results

        # Prepare for panel
        df_panel = self.prepare_for_panel(df)
        if df_panel.empty:
            print("\n❌ Failed to prepare data")
            return self.results

        # Run tests
        success, panel = self.test_panel_index_creation(df_panel)
        if not success:
            return self.generate_report()

        success, panel = self.test_lag_generation(panel)
        if not success:
            return self.generate_report()

        success, panel = self.test_rolling_windows(panel)
        if not success:
            return self.generate_report()

        success, panel = self.test_cumulative_stats(panel)
        if not success:
            return self.generate_report()

        success = self.test_temporal_query(panel)
        if not success:
            return self.generate_report()

        success = self.test_data_quality(panel)
        if not success:
            return self.generate_report()

        # Count features
        self.count_features_generated(panel)

        # Total time
        total_time = time.time() - overall_start
        self.results["performance"]["total_validation_time"] = total_time

        # Generate report
        return self.generate_report()


def main():
    """Main execution"""
    validator = RealDataValidator()
    results = validator.run_full_validation()

    # Exit code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
