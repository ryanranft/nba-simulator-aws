#!/usr/bin/env python3
"""
Implementation Script: Advanced Feature Engineering Pipeline

Recommendation ID: consolidated_consolidated_rec_11 (rec_11)
Priority: CRITICAL (#2 in master sequence)
Source Books: Designing ML Systems, Hands-On ML, Econometrics, Stats 601, Elements of Stats
Dependencies: rec_22 (Panel Data Processing System)
Generated: 2025-10-16

Description:
Advanced feature engineering pipeline that builds on panel data infrastructure to create
50-100+ features across multiple categories: temporal, interaction, contextual, derived, and engineered.

Expected Impact: HIGH - Improve model accuracy from 63% to 68-71% (+5-8%)
Time Estimate: 1 week
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AdvancedFeatureEngineeringPipeline:
    """
    Implementation of: Advanced Feature Engineering Pipeline

    Builds on rec_22 (Panel Data) to create 50-100+ features across categories:
    - Temporal features (lags, rolling windows, trends)
    - Cumulative features (season-to-date, career totals)
    - Interaction features (player×opponent, home×rest)
    - Contextual features (schedule strength, travel, fatigue)
    - Derived features (efficiency metrics, advanced stats)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AdvancedFeatureEngineeringPipeline.

        Args:
            config: Configuration dictionary with feature settings
        """
        self.config = config or self._default_config()
        self.setup_complete = False
        self.panel_data_system = None
        self.feature_count = 0
        self.feature_catalog = []
        logger.info("AdvancedFeatureEngineeringPipeline initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for feature engineering."""
        return {
            # Temporal features
            "lag_periods": [1, 2, 3, 5, 10],  # games to lag
            "rolling_windows": [3, 5, 10, 20],  # game windows
            "trend_windows": [5, 10],  # for trend calculation
            # Feature categories to include
            "include_temporal": True,
            "include_cumulative": True,
            "include_interaction": True,
            "include_contextual": True,
            "include_derived": True,
            # Stat types to engineer
            "base_stats": [
                "points",
                "rebounds",
                "assists",
                "fg_pct",
                "three_pct",
                "ft_pct",
                "steals",
                "blocks",
                "turnovers",
                "minutes",
            ],
            # Advanced metrics
            "calculate_efficiency": True,
            "calculate_usage": True,
            "calculate_pace_adjusted": True,
        }

    def setup(self) -> bool:
        """
        Set up necessary infrastructure and dependencies.

        Returns:
            bool: True if setup successful
        """
        try:
            logger.info("Setting up AdvancedFeatureEngineeringPipeline...")

            # Import panel data system from rec_22
            try:
                from implement_rec_22 import PanelDataProcessingSystem

                self.panel_data_system = PanelDataProcessingSystem()
                self.panel_data_system.setup()
                logger.info("✓ Panel data system (rec_22) loaded")
            except ImportError:
                logger.error(
                    "✗ Cannot import rec_22 - ensure implement_rec_22.py is available"
                )
                return False

            # Validate pandas and numpy
            logger.info(f"✓ pandas {pd.__version__} available")
            logger.info(f"✓ numpy {np.__version__} available")

            self.setup_complete = True
            logger.info("✓ Advanced feature engineering pipeline ready")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    def validate_prerequisites(self) -> bool:
        """
        Validate that all prerequisites are met.

        Returns:
            bool: True if all prerequisites met
        """
        logger.info("Validating prerequisites...")

        checks = []

        # Check pandas
        try:
            import pandas as pd

            logger.info(f"✓ pandas {pd.__version__} available")
            checks.append(True)
        except ImportError:
            logger.error("✗ pandas not available")
            checks.append(False)

        # Check numpy
        try:
            import numpy as np

            logger.info(f"✓ numpy {np.__version__} available")
            checks.append(True)
        except ImportError:
            logger.error("✗ numpy not available")
            checks.append(False)

        # Check rec_22 availability
        try:
            from implement_rec_22 import PanelDataProcessingSystem

            logger.info("✓ rec_22 (Panel Data System) available")
            checks.append(True)
        except ImportError:
            logger.error("✗ rec_22 not available - implement rec_22 first")
            checks.append(False)

        return all(checks)

    def generate_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate temporal features using panel data lags and rolling windows.

        Args:
            df: Panel DataFrame with multi-index (player_id, game_id, timestamp)

        Returns:
            DataFrame with added temporal features
        """
        logger.info("\nGenerating temporal features...")
        feature_count_start = len(df.columns)

        base_stats = self.config["base_stats"]
        lag_periods = self.config["lag_periods"]
        rolling_windows = self.config["rolling_windows"]

        # 1. Lag features (previous game stats)
        for stat in base_stats:
            if stat in df.columns:
                df = self.panel_data_system.generate_lags(
                    df, variables=[stat], lags=lag_periods
                )

        # 2. Rolling window features (recent form)
        for stat in base_stats:
            if stat in df.columns:
                df = self.panel_data_system.generate_rolling_stats(
                    df, variables=[stat], windows=rolling_windows, stats=["mean", "std"]
                )

        # 3. Trend features (improving vs declining)
        for stat in base_stats:
            if stat in df.columns:
                for window in self.config["trend_windows"]:
                    # Calculate trend as difference between recent and older averages
                    recent_col = f"{stat}_rolling_{window}_mean"
                    if recent_col in df.columns:
                        older_window = window * 2
                        older_col = f"{stat}_rolling_{older_window}_mean"
                        if older_col not in df.columns:
                            # Calculate older window
                            df = self.panel_data_system.generate_rolling_stats(
                                df,
                                variables=[stat],
                                windows=[older_window],
                                stats=["mean"],
                            )

                        # Trend = recent - older (positive = improving)
                        df[f"{stat}_trend_{window}"] = df[recent_col] - df[older_col]

        feature_count_end = len(df.columns)
        features_added = feature_count_end - feature_count_start
        logger.info(f"✓ Added {features_added} temporal features")
        self.feature_catalog.append(("temporal", features_added))

        return df

    def generate_cumulative_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate cumulative features (season-to-date, career totals).

        Args:
            df: Panel DataFrame

        Returns:
            DataFrame with cumulative features
        """
        logger.info("\nGenerating cumulative features...")
        feature_count_start = len(df.columns)

        base_stats = self.config["base_stats"]

        # Career cumulative stats
        df = self.panel_data_system.generate_cumulative_stats(
            df, variables=base_stats + ["games"]  # includes games counter
        )

        # Per-game averages (career)
        for stat in base_stats:
            cumulative_col = f"{stat}_cumulative"
            if cumulative_col in df.columns and "games_cumulative" in df.columns:
                df[f"{stat}_career_avg"] = df[cumulative_col] / df[
                    "games_cumulative"
                ].replace(0, 1)

        feature_count_end = len(df.columns)
        features_added = feature_count_end - feature_count_start
        logger.info(f"✓ Added {features_added} cumulative features")
        self.feature_catalog.append(("cumulative", features_added))

        return df

    def generate_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate interaction features (player×opponent, home×rest, etc.).

        Args:
            df: Panel DataFrame

        Returns:
            DataFrame with interaction features
        """
        logger.info("\nGenerating interaction features...")
        feature_count_start = len(df.columns)

        # 1. Home vs Away splits
        if "is_home" in df.columns:
            for stat in ["points", "rebounds", "assists"]:
                if stat in df.columns:
                    # Home performance
                    df[f"{stat}_home_avg"] = df.groupby(["player_id", "is_home"])[
                        stat
                    ].transform(lambda x: x.expanding().mean())

        # 2. Rest days interaction
        if "days_rest" in df.columns:
            for stat in ["points", "minutes"]:
                if stat in df.columns:
                    # Performance by rest category
                    df["rest_category"] = pd.cut(
                        df["days_rest"],
                        bins=[-1, 0, 1, 2, 10],
                        labels=["b2b", "1day", "2day", "3plus"],
                    )
                    df[f"{stat}_by_rest"] = df.groupby(["player_id", "rest_category"])[
                        stat
                    ].transform(lambda x: x.expanding().mean())

        # 3. Month/Season interaction (fatigue over season)
        if "game_number" in df.columns:
            df["season_quarter"] = pd.cut(
                df["game_number"],
                bins=[0, 20, 41, 61, 82],
                labels=["early", "mid", "late", "playoff_push"],
            )

            for stat in ["minutes", "points"]:
                if stat in df.columns:
                    df[f"{stat}_by_season_quarter"] = df.groupby(
                        ["player_id", "season_quarter"]
                    )[stat].transform(lambda x: x.expanding().mean())

        feature_count_end = len(df.columns)
        features_added = feature_count_end - feature_count_start
        logger.info(f"✓ Added {features_added} interaction features")
        self.feature_catalog.append(("interaction", features_added))

        return df

    def generate_contextual_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate contextual features (schedule strength, travel, etc.).

        Args:
            df: Panel DataFrame

        Returns:
            DataFrame with contextual features
        """
        logger.info("\nGenerating contextual features...")
        feature_count_start = len(df.columns)

        # 1. Schedule strength (opponent win percentage)
        if "opponent_win_pct" in df.columns:
            # Recent opponent strength (last 5 games)
            df["opponent_strength_l5"] = (
                df.groupby("player_id")["opponent_win_pct"]
                .rolling(window=5, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )

            # Season opponent strength average
            df["opponent_strength_season"] = (
                df.groupby("player_id")["opponent_win_pct"]
                .expanding()
                .mean()
                .reset_index(level=0, drop=True)
            )

        # 2. Travel/fatigue indicators
        if "travel_distance" in df.columns:
            # Recent travel burden (last 7 games)
            df["travel_burden_l7"] = (
                df.groupby("player_id")["travel_distance"]
                .rolling(window=7, min_periods=1)
                .sum()
                .reset_index(level=0, drop=True)
            )

        # 3. Back-to-back indicator and streak
        if "is_back_to_back" in df.columns:
            # Consecutive back-to-backs
            df["b2b_streak"] = (
                df.groupby("player_id")["is_back_to_back"]
                .rolling(window=5, min_periods=1)
                .sum()
                .reset_index(level=0, drop=True)
            )

        # 4. Altitude adjustment (for Denver, Utah, etc.)
        if "altitude" in df.columns:
            df["high_altitude"] = (df["altitude"] > 5000).astype(int)

            # Performance at altitude
            for stat in ["points", "rebounds"]:
                if stat in df.columns:
                    df[f"{stat}_at_altitude"] = df.groupby(
                        ["player_id", "high_altitude"]
                    )[stat].transform(lambda x: x.expanding().mean())

        feature_count_end = len(df.columns)
        features_added = feature_count_end - feature_count_start
        logger.info(f"✓ Added {features_added} contextual features")
        self.feature_catalog.append(("contextual", features_added))

        return df

    def generate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate derived features (efficiency metrics, advanced stats).

        Args:
            df: Panel DataFrame

        Returns:
            DataFrame with derived features
        """
        logger.info("\nGenerating derived features...")
        feature_count_start = len(df.columns)

        # 1. True Shooting Percentage (TS%)
        if all(col in df.columns for col in ["points", "fga", "fta"]):
            df["ts_pct"] = df["points"] / (2 * (df["fga"] + 0.44 * df["fta"])).replace(
                0, 1
            )

            # Rolling TS% (form)
            df["ts_pct_rolling_10"] = (
                df.groupby("player_id")["ts_pct"]
                .rolling(window=10, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )

        # 2. Usage Rate
        if all(
            col in df.columns
            for col in ["fga", "fta", "turnovers", "minutes", "team_minutes"]
        ):
            df["usage_rate"] = (
                100
                * (
                    (df["fga"] + 0.44 * df["fta"] + df["turnovers"])
                    * (df["team_minutes"] / 5)
                )
                / (
                    df["minutes"]
                    * (df["team_fga"] + 0.44 * df["team_fta"] + df["team_turnovers"])
                ).replace(0, 1)
            )

        # 3. Assist Ratio
        if all(col in df.columns for col in ["assists", "fga", "fta", "turnovers"]):
            df["assist_ratio"] = (
                100
                * df["assists"]
                / (
                    df["fga"] + 0.44 * df["fta"] + df["assists"] + df["turnovers"]
                ).replace(0, 1)
            )

        # 4. Rebound Rate
        if all(
            col in df.columns
            for col in ["rebounds", "minutes", "team_rebounds", "team_minutes"]
        ):
            df["rebound_rate"] = (df["rebounds"] * df["team_minutes"]) / (
                df["minutes"] * df["team_rebounds"]
            ).replace(0, 1)

        # 5. Per-36-minute stats
        if "minutes" in df.columns:
            for stat in ["points", "rebounds", "assists"]:
                if stat in df.columns:
                    df[f"{stat}_per_36"] = df[stat] * 36 / df["minutes"].replace(0, 1)

        # 6. Pace-adjusted stats
        if "team_pace" in df.columns:
            league_avg_pace = 100.0  # Typical NBA pace
            for stat in ["points", "rebounds", "assists"]:
                if stat in df.columns:
                    df[f"{stat}_pace_adj"] = df[stat] * (
                        league_avg_pace / df["team_pace"].replace(0, 1)
                    )

        # 7. Player Efficiency Rating (PER) - simplified
        if all(
            col in df.columns
            for col in [
                "points",
                "fgm",
                "ftm",
                "three_pm",
                "rebounds",
                "assists",
                "steals",
                "blocks",
                "fga",
                "fta",
                "turnovers",
                "minutes",
            ]
        ):
            df["per"] = (
                df["points"]
                + df["rebounds"]
                + df["assists"]
                + df["steals"]
                + df["blocks"]
                - (df["fga"] - df["fgm"])
                - (df["fta"] - df["ftm"])
                - df["turnovers"]
            ) / df["minutes"].replace(0, 1)

        feature_count_end = len(df.columns)
        features_added = feature_count_end - feature_count_start
        logger.info(f"✓ Added {features_added} derived features")
        self.feature_catalog.append(("derived", features_added))

        return df

    def generate_engineered_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate engineered features (form indicators, clutch stats, etc.).

        Args:
            df: Panel DataFrame

        Returns:
            DataFrame with engineered features
        """
        logger.info("\nGenerating engineered features...")
        feature_count_start = len(df.columns)

        # 1. Form indicators (hot/cold streaks)
        for stat in ["points", "fg_pct"]:
            if stat in df.columns:
                # Recent vs season average
                recent_col = f"{stat}_rolling_5_mean"
                season_col = f"{stat}_career_avg"

                if recent_col in df.columns and season_col in df.columns:
                    df[f"{stat}_form"] = df[recent_col] - df[season_col]

                    # Binary hot/cold indicator
                    df[f"{stat}_is_hot"] = (df[f"{stat}_form"] > 0).astype(int)

        # 2. Consistency metric (standard deviation of recent games)
        for stat in ["points", "rebounds", "assists"]:
            std_col = f"{stat}_rolling_10_std"
            if std_col in df.columns:
                # Lower std = more consistent
                df[f"{stat}_consistency"] = 1 / (
                    df[std_col] + 1
                )  # +1 to avoid division by zero

        # 3. Improvement trajectory (linear trend)
        for stat in ["points", "fg_pct"]:
            if stat in df.columns:
                # Slope of last 10 games (positive = improving)
                df[f"{stat}_trajectory"] = (
                    df.groupby("player_id")[stat]
                    .rolling(window=10, min_periods=5)
                    .apply(
                        lambda x: (
                            np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 5 else 0
                        )
                    )
                    .reset_index(level=0, drop=True)
                )

        # 4. Clutch performance indicator (if 4Q/OT stats available)
        if "points_4q" in df.columns and "points" in df.columns:
            df["clutch_scoring_rate"] = df["points_4q"] / df["points"].replace(0, 1)

            # Clutch performer indicator (top 25% in clutch rate)
            df["is_clutch_performer"] = (
                df["clutch_scoring_rate"]
                > df.groupby("player_id")["clutch_scoring_rate"].transform(
                    "quantile", 0.75
                )
            ).astype(int)

        # 5. Matchup advantage (vs. strong/weak opponents)
        if "opponent_win_pct" in df.columns:
            # Performance vs winning teams (>0.500)
            strong_opp = df["opponent_win_pct"] > 0.500
            for stat in ["points", "fg_pct"]:
                if stat in df.columns:
                    df[f"{stat}_vs_strong"] = df[stat].where(strong_opp, 0)
                    df[f"{stat}_vs_weak"] = df[stat].where(~strong_opp, 0)

                    # Average vs strong/weak (expanding mean)
                    df[f"{stat}_avg_vs_strong"] = (
                        df.groupby("player_id")[f"{stat}_vs_strong"]
                        .expanding()
                        .mean()
                        .reset_index(level=0, drop=True)
                    )

        feature_count_end = len(df.columns)
        features_added = feature_count_end - feature_count_start
        logger.info(f"✓ Added {features_added} engineered features")
        self.feature_catalog.append(("engineered", features_added))

        return df

    def select_features(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        max_features: Optional[int] = None,
    ) -> List[str]:
        """
        Select most important features using correlation and variance thresholds.

        Args:
            df: DataFrame with all features
            target_col: Target column for correlation analysis
            max_features: Maximum number of features to select

        Returns:
            List of selected feature names
        """
        logger.info("\nSelecting features...")

        # Identify numeric columns (exclude index)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Remove target from feature list
        if target_col and target_col in numeric_cols:
            numeric_cols.remove(target_col)

        # 1. Remove low variance features (constant or near-constant)
        low_variance_threshold = 0.01
        variances = df[numeric_cols].var()
        high_variance_features = variances[
            variances > low_variance_threshold
        ].index.tolist()

        logger.info(
            f"✓ Removed {len(numeric_cols) - len(high_variance_features)} low-variance features"
        )

        # 2. Remove highly correlated features (keep one from each pair)
        corr_matrix = df[high_variance_features].corr().abs()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        corr_threshold = 0.95
        to_drop = [
            column
            for column in upper_triangle.columns
            if any(upper_triangle[column] > corr_threshold)
        ]

        selected_features = [f for f in high_variance_features if f not in to_drop]
        logger.info(f"✓ Removed {len(to_drop)} highly correlated features")

        # 3. Select top features by correlation with target (if provided)
        if target_col and target_col in df.columns:
            correlations = df[selected_features + [target_col]].corr()[target_col].abs()
            correlations = correlations.drop(target_col).sort_values(ascending=False)

            if max_features and len(correlations) > max_features:
                selected_features = correlations.head(max_features).index.tolist()
                logger.info(
                    f"✓ Selected top {max_features} features by correlation with target"
                )

        logger.info(f"✓ Final feature count: {len(selected_features)}")
        return selected_features

    def execute(self, demo_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Execute the complete feature engineering pipeline.

        Args:
            demo_data: Optional demo DataFrame (if None, creates synthetic data)

        Returns:
            dict: Execution results and metrics
        """
        if not self.setup_complete:
            raise RuntimeError("Setup must be completed before execution")

        logger.info("=" * 70)
        logger.info("EXECUTING: Advanced Feature Engineering Pipeline (rec_11)")
        logger.info("=" * 70)
        start_time = datetime.now()

        try:
            # Step 1: Create or load demo data
            logger.info("\nStep 1: Loading demo data...")
            if demo_data is None:
                demo_data = self._create_demo_data()

            logger.info(f"Initial data shape: {demo_data.shape}")
            logger.info(f"Initial features: {len(demo_data.columns)}")

            # Step 2: Create panel structure (using rec_22)
            logger.info("\nStep 2: Creating panel structure...")
            panel_df = self.panel_data_system.create_panel_index(demo_data)

            # Step 3: Generate temporal features
            if self.config["include_temporal"]:
                panel_df = self.generate_temporal_features(panel_df)

            # Step 4: Generate cumulative features
            if self.config["include_cumulative"]:
                panel_df = self.generate_cumulative_features(panel_df)

            # Step 5: Generate interaction features
            if self.config["include_interaction"]:
                panel_df = self.generate_interaction_features(panel_df)

            # Step 6: Generate contextual features
            if self.config["include_contextual"]:
                panel_df = self.generate_contextual_features(panel_df)

            # Step 7: Generate derived features
            if self.config["include_derived"]:
                panel_df = self.generate_derived_features(panel_df)

            # Step 8: Generate engineered features
            panel_df = self.generate_engineered_features(panel_df)

            # Step 9: Feature selection
            logger.info("\nStep 9: Performing feature selection...")
            selected_features = self.select_features(panel_df, max_features=100)

            # Calculate total features
            total_features = len(panel_df.columns)
            original_features = len(demo_data.columns)
            new_features = total_features - original_features

            # Summary
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info("\n" + "=" * 70)
            logger.info("ADVANCED FEATURE ENGINEERING - EXECUTION COMPLETE")
            logger.info("=" * 70)
            logger.info(f"✓ Original features: {original_features}")
            logger.info(f"✓ Total features generated: {total_features}")
            logger.info(f"✓ New features added: {new_features}")
            logger.info(
                f"✓ Selected features (after filtering): {len(selected_features)}"
            )
            logger.info(f"✓ Feature categories: {len(self.feature_catalog)}")

            for category, count in self.feature_catalog:
                logger.info(f"  - {category}: {count} features")

            logger.info(f"✓ Execution time: {execution_time:.2f}s")
            logger.info("=" * 70)

            results = {
                "success": True,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "original_features": original_features,
                "total_features": total_features,
                "new_features": new_features,
                "selected_features": len(selected_features),
                "feature_catalog": self.feature_catalog,
                "panel_shape": panel_df.shape,
                "selected_feature_names": selected_features,
            }

            return results

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    def _create_demo_data(self) -> pd.DataFrame:
        """Create synthetic NBA game data for demonstration."""
        np.random.seed(42)

        num_players = 3
        games_per_player = 30
        total_rows = num_players * games_per_player

        data = {
            "player_id": np.repeat(range(1, num_players + 1), games_per_player),
            "game_id": np.tile(range(1, games_per_player + 1), num_players),
            "game_date": pd.date_range("2023-01-01", periods=games_per_player).tolist()
            * num_players,
            # Basic stats
            "points": np.random.poisson(20, total_rows),
            "rebounds": np.random.poisson(7, total_rows),
            "assists": np.random.poisson(5, total_rows),
            "minutes": np.random.normal(32, 5, total_rows).clip(20, 40),
            # Shooting stats
            "fga": np.random.poisson(15, total_rows),
            "fgm": np.random.poisson(8, total_rows),
            "three_pa": np.random.poisson(6, total_rows),
            "three_pm": np.random.poisson(2, total_rows),
            "fta": np.random.poisson(4, total_rows),
            "ftm": np.random.poisson(3, total_rows),
            # Other stats
            "steals": np.random.poisson(1, total_rows),
            "blocks": np.random.poisson(1, total_rows),
            "turnovers": np.random.poisson(2, total_rows),
            # Contextual
            "is_home": np.random.choice([0, 1], total_rows),
            "days_rest": np.random.choice(
                [0, 1, 2, 3], total_rows, p=[0.3, 0.4, 0.2, 0.1]
            ),
            "opponent_win_pct": np.random.uniform(0.3, 0.7, total_rows),
            # Team stats (for advanced metrics)
            "team_minutes": [240] * total_rows,
            "team_fga": np.random.poisson(85, total_rows),
            "team_fta": np.random.poisson(25, total_rows),
            "team_turnovers": np.random.poisson(14, total_rows),
            "team_rebounds": np.random.poisson(45, total_rows),
            "team_pace": np.random.normal(100, 5, total_rows),
        }

        df = pd.DataFrame(data)

        # Calculate shooting percentages
        df["fg_pct"] = df["fgm"] / df["fga"].replace(0, 1)
        df["three_pct"] = df["three_pm"] / df["three_pa"].replace(0, 1)
        df["ft_pct"] = df["ftm"] / df["fta"].replace(0, 1)

        # Add game number
        df["game_number"] = df.groupby("player_id").cumcount() + 1

        logger.info(
            f"Created demo data: {len(df)} observations, {len(df['player_id'].unique())} players"
        )

        return df

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        self.panel_data_system = None
        self.feature_catalog = []


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Starting: Advanced Feature Engineering Pipeline")
    logger.info("=" * 80)

    # Initialize and execute
    implementation = AdvancedFeatureEngineeringPipeline()

    # Validate prerequisites
    if not implementation.validate_prerequisites():
        logger.error("Prerequisites not met. Exiting.")
        sys.exit(1)

    # Setup
    if not implementation.setup():
        logger.error("Setup failed. Exiting.")
        sys.exit(1)

    # Execute
    results = implementation.execute()

    # Cleanup
    implementation.cleanup()

    # Report results
    logger.info("\n" + "=" * 80)
    logger.info("Results:")
    logger.info(
        json.dumps(
            {k: v for k, v in results.items() if k != "selected_feature_names"},
            indent=2,
        )
    )
    logger.info("=" * 80)

    if results.get("success"):
        logger.info("✅ Implementation completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Implementation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
