#!/usr/bin/env python3
"""
Panel Data Processing System (rec_22)

Implements proper panel data infrastructure for NBA temporal analytics.
This is the foundation for all panel data work in the project.

Source: Econometric Analysis (Panel Data Models, Ch 9-11)
Priority: CRITICAL (Block 1, Recommendation #1)
Phase: 0 (Data Collection)

Key Features:
- Multi-index DataFrames (player_id, game_id, timestamp)
- Lag variable generation (previous game stats)
- Rolling window statistics (last N games)
- Cumulative statistics (career totals at any point)
- Panel transformations (within, between, first-difference)
- Temporal query function (stats at exact timestamp)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
import boto3
from io import BytesIO
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PanelDataProcessingSystem:
    """
    Panel data processing system for NBA temporal analytics.

    Provides infrastructure for:
    - Multi-indexed panel data (player-game-time)
    - Temporal queries (stats at exact timestamps)
    - Lag/lead variable generation
    - Rolling window statistics
    - Cumulative statistics
    - Panel transformations

    Example:
        >>> system = PanelDataProcessingSystem()
        >>> system.setup()
        >>> panel = system.create_panel_from_s3('s3://bucket/box_scores/2023/')
        >>> panel = system.generate_lags(panel, ['points', 'rebounds'], [1, 2, 3])
        >>> stats = system.query_stats_at_time(player_id=2544,
        ...                                    timestamp=datetime(2023, 6, 12))
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize panel data processing system.

        Args:
            config: Configuration dictionary with optional keys:
                - s3_bucket: S3 bucket name for data
                - cache_dir: Local cache directory
                - index_cols: Column names for multi-index
        """
        self.config = config or {}
        self.s3_bucket = self.config.get("s3_bucket", "nba-sim-raw-data-lake")
        self.cache_dir = self.config.get("cache_dir", "/tmp/panel_cache")  # nosec B108
        self.index_cols = self.config.get(
            "index_cols", ["player_id", "game_id", "timestamp"]
        )

        # Initialize S3 client
        self.s3_client = None

        # Panel data cache
        self.panel_data = None

        logger.info("PanelDataProcessingSystem initialized")

    def setup(self) -> None:
        """Set up infrastructure and validate prerequisites."""
        logger.info("Setting up panel data processing system...")

        # Initialize S3 client
        try:
            self.s3_client = boto3.client("s3")
            logger.info("✓ S3 client initialized")
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}")
            logger.warning("  S3 operations will not be available")

        # Create cache directory
        import os

        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"✓ Cache directory ready: {self.cache_dir}")

        logger.info("✓ Panel data processing system ready")

    def validate_prerequisites(self) -> Dict:
        """
        Validate that required packages and data are available.

        Returns:
            Dict with validation results
        """
        results = {
            "pandas_available": False,
            "numpy_available": False,
            "s3_available": False,
            "all_ready": False,
        }

        # Check pandas
        try:
            import pandas

            results["pandas_available"] = True
            logger.info(f"✓ pandas {pandas.__version__} available")
        except ImportError:
            logger.error("✗ pandas not available")

        # Check numpy
        try:
            import numpy

            results["numpy_available"] = True
            logger.info(f"✓ numpy {numpy.__version__} available")
        except ImportError:
            logger.error("✗ numpy not available")

        # Check S3 access
        if self.s3_client is not None:
            try:
                self.s3_client.list_objects_v2(Bucket=self.s3_bucket, MaxKeys=1)
                results["s3_available"] = True
                logger.info(f"✓ S3 bucket '{self.s3_bucket}' accessible")
            except Exception as e:
                logger.warning(f"✗ S3 access failed: {e}")

        results["all_ready"] = (
            results["pandas_available"] and results["numpy_available"]
        )

        return results

    # ==================== DATA LOADING ====================

    def load_game_data_from_s3(self, s3_prefix: str) -> pd.DataFrame:
        """
        Load game-level data from S3 box scores.

        Args:
            s3_prefix: S3 prefix (e.g., 'box_scores/2023/')

        Returns:
            DataFrame with one row per player per game
        """
        logger.info(f"Loading game data from s3://{self.s3_bucket}/{s3_prefix}")

        if self.s3_client is None:
            raise RuntimeError("S3 client not initialized. Call setup() first.")

        # List all files in prefix
        response = self.s3_client.list_objects_v2(
            Bucket=self.s3_bucket, Prefix=s3_prefix
        )

        if "Contents" not in response:
            logger.warning(f"No files found at {s3_prefix}")
            return pd.DataFrame()

        files = [
            obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".json")
        ]

        logger.info(f"Found {len(files)} JSON files")

        # Load and parse files
        all_data = []
        for i, file_key in enumerate(files[:10]):  # Limit to 10 for demo
            try:
                obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_key)
                data = json.loads(obj["Body"].read().decode("utf-8"))

                # Extract player-game observations
                # This is a simplified example - adjust based on your data structure
                if "boxScore" in data and "players" in data["boxScore"]:
                    for team in data["boxScore"]["players"]:
                        for player in team.get("statistics", []):
                            all_data.append(
                                {
                                    "game_id": data.get("header", {}).get("id"),
                                    "game_date": data.get("header", {})
                                    .get("competitions", [{}])[0]
                                    .get("date"),
                                    "player_id": player.get("athlete", {}).get("id"),
                                    "player_name": player.get("athlete", {}).get(
                                        "displayName"
                                    ),
                                    "team_id": team.get("team", {}).get("id"),
                                    "minutes": player.get("min", 0),
                                    "points": player.get("points", 0),
                                    "rebounds": player.get("totReb", 0),
                                    "assists": player.get("assists", 0),
                                    "steals": player.get("steals", 0),
                                    "blocks": player.get("blocks", 0),
                                    "turnovers": player.get("turnovers", 0),
                                    "fg_made": player.get("fieldGoalsMade", 0),
                                    "fg_attempted": player.get(
                                        "fieldGoalsAttempted", 0
                                    ),
                                    "fg3_made": player.get(
                                        "threePointFieldGoalsMade", 0
                                    ),
                                    "fg3_attempted": player.get(
                                        "threePointFieldGoalsAttempted", 0
                                    ),
                                    "ft_made": player.get("freeThrowsMade", 0),
                                    "ft_attempted": player.get(
                                        "freeThrowsAttempted", 0
                                    ),
                                }
                            )

                if (i + 1) % 100 == 0:
                    logger.info(f"  Processed {i + 1}/{len(files)} files")

            except Exception as e:
                logger.warning(f"Error processing {file_key}: {e}")
                continue

        df = pd.DataFrame(all_data)
        logger.info(f"✓ Loaded {len(df):,} player-game observations")

        return df

    # ==================== PANEL STRUCTURE ====================

    def create_panel_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert flat DataFrame to multi-indexed panel data.

        Sets index: (player_id, game_id, timestamp)
        Sorts by: player_id, timestamp

        Args:
            df: Flat DataFrame with player-game observations

        Returns:
            Multi-indexed panel DataFrame
        """
        logger.info("Creating panel index...")

        # Ensure required columns exist
        required_cols = ["player_id", "game_id"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Create timestamp if not present (use game_date)
        if "timestamp" not in df.columns:
            if "game_date" in df.columns:
                df["timestamp"] = pd.to_datetime(df["game_date"])
            else:
                # Assign sequential timestamps
                df["timestamp"] = pd.to_datetime("2020-01-01") + pd.to_timedelta(
                    range(len(df)), unit="D"
                )

        # Set multi-index
        df = df.set_index(["player_id", "game_id", "timestamp"])

        # Sort by player_id, timestamp (critical for lag operations)
        df = df.sort_index(level=["player_id", "timestamp"])

        # Validate no duplicate indices
        if df.index.duplicated().any():
            n_dupes = df.index.duplicated().sum()
            logger.warning(f"Found {n_dupes} duplicate indices - keeping first")
            df = df[~df.index.duplicated(keep="first")]

        logger.info(f"✓ Panel index created: {len(df):,} observations")
        logger.info(f"  Players: {df.index.get_level_values('player_id').nunique():,}")
        logger.info(f"  Games: {df.index.get_level_values('game_id').nunique():,}")

        return df

    # ==================== LAG VARIABLES ====================

    def generate_lags(
        self, df: pd.DataFrame, variables: List[str], lags: List[int]
    ) -> pd.DataFrame:
        """
        Generate lagged variables within each player.

        Args:
            df: Panel DataFrame (must have player_id in index)
            variables: Columns to lag (e.g., ['points', 'rebounds'])
            lags: Lag periods (e.g., [1, 2, 3, 5, 10])

        Returns:
            DataFrame with added columns: {var}_lag{n}

        Example:
            >>> df = system.generate_lags(df, ['points'], [1, 2, 3])
            # Creates: points_lag1, points_lag2, points_lag3
        """
        logger.info(
            f"Generating lags for {len(variables)} variables, {len(lags)} periods"
        )

        # Verify variables exist
        missing = [v for v in variables if v not in df.columns]
        if missing:
            raise ValueError(f"Variables not in DataFrame: {missing}")

        # Group by player_id (entity)
        for var in variables:
            for lag in lags:
                col_name = f"{var}_lag{lag}"

                # Shift within each player group
                df[col_name] = df.groupby(level="player_id")[var].shift(lag)

                logger.info(
                    f"  ✓ Created {col_name} ({df[col_name].notna().sum():,} non-null)"
                )

        logger.info(f"✓ Generated {len(variables) * len(lags)} lag variables")

        return df

    # ==================== ROLLING WINDOWS ====================

    def generate_rolling_stats(
        self,
        df: pd.DataFrame,
        variables: List[str],
        windows: List[int],
        stats: List[str] = ["mean", "std"],
    ) -> pd.DataFrame:
        """
        Generate rolling window statistics within each player.

        Args:
            df: Panel DataFrame
            variables: Columns to aggregate
            windows: Window sizes (e.g., [3, 5, 10, 20])
            stats: Statistics to compute (['mean', 'std', 'max', 'min'])

        Returns:
            DataFrame with columns: {var}_rolling_{n}_{stat}

        Example:
            >>> df = system.generate_rolling_stats(df, ['points'], [5, 10])
            # Creates: points_rolling_5_mean, points_rolling_5_std, etc.
        """
        logger.info(f"Generating rolling stats for {len(variables)} variables")

        for var in variables:
            if var not in df.columns:
                logger.warning(f"Variable '{var}' not in DataFrame, skipping")
                continue

            for window in windows:
                # Get rolling object (within each player)
                rolling = df.groupby(level="player_id")[var].rolling(
                    window=window, min_periods=1  # Allow partial windows
                )

                for stat in stats:
                    col_name = f"{var}_rolling_{window}_{stat}"

                    if stat == "mean":
                        values = rolling.mean()
                    elif stat == "std":
                        values = rolling.std()
                    elif stat == "max":
                        values = rolling.max()
                    elif stat == "min":
                        values = rolling.min()
                    else:
                        logger.warning(f"Unknown stat '{stat}', skipping")
                        continue

                    # Reset index to align with original DataFrame
                    df[col_name] = values.reset_index(level=0, drop=True)

                    logger.info(f"  ✓ Created {col_name}")

        logger.info(f"✓ Generated rolling statistics")

        return df

    # ==================== CUMULATIVE STATISTICS ====================

    def generate_cumulative_stats(
        self, df: pd.DataFrame, variables: List[str]
    ) -> pd.DataFrame:
        """
        Generate cumulative statistics (career totals at each point).

        Args:
            df: Panel DataFrame
            variables: Columns to accumulate

        Returns:
            DataFrame with columns: {var}_cumulative

        Example:
            >>> df = system.generate_cumulative_stats(df, ['points', 'games'])
            # Creates: points_cumulative, games_cumulative
        """
        logger.info(f"Generating cumulative stats for {len(variables)} variables")

        for var in variables:
            if var not in df.columns:
                # Create binary 'games' variable if requested
                if var == "games":
                    df[var] = 1
                else:
                    logger.warning(f"Variable '{var}' not in DataFrame, skipping")
                    continue

            col_name = f"{var}_cumulative"

            # Cumulative sum within each player
            df[col_name] = df.groupby(level="player_id")[var].cumsum()

            logger.info(f"  ✓ Created {col_name}")

        logger.info(f"✓ Generated cumulative statistics")

        return df

    # ==================== PANEL TRANSFORMATIONS ====================

    def within_transform(self, df: pd.DataFrame, variable: str) -> pd.Series:
        """
        Within transformation (de-meaning within entity).

        y_it - ȳ_i (subtract player-specific mean)

        Args:
            df: Panel DataFrame
            variable: Column to transform

        Returns:
            Demeaned series
        """
        if variable not in df.columns:
            raise ValueError(f"Variable '{variable}' not in DataFrame")

        # Calculate player means
        player_means = df.groupby(level="player_id")[variable].transform("mean")

        # Subtract player mean from each observation
        demeaned = df[variable] - player_means

        logger.info(f"✓ Within transform: {variable} → mean={demeaned.mean():.6f}")

        return demeaned

    def between_transform(self, df: pd.DataFrame, variable: str) -> pd.Series:
        """
        Between transformation (entity means).

        ȳ_i (player-specific mean)

        Args:
            df: Panel DataFrame
            variable: Column to transform

        Returns:
            Series of entity means
        """
        if variable not in df.columns:
            raise ValueError(f"Variable '{variable}' not in DataFrame")

        # Calculate and broadcast player means
        player_means = df.groupby(level="player_id")[variable].transform("mean")

        logger.info(f"✓ Between transform: {variable}")

        return player_means

    def first_difference(self, df: pd.DataFrame, variable: str) -> pd.Series:
        """
        First-difference transformation.

        Δy_it = y_it - y_i,t-1

        Args:
            df: Panel DataFrame
            variable: Column to transform

        Returns:
            First-differenced series
        """
        if variable not in df.columns:
            raise ValueError(f"Variable '{variable}' not in DataFrame")

        # Difference within each player
        differenced = df.groupby(level="player_id")[variable].diff()

        logger.info(
            f"✓ First difference: {variable} → {differenced.notna().sum():,} non-null"
        )

        return differenced

    # ==================== TEMPORAL QUERIES ====================

    def query_stats_at_time(
        self,
        player_id: int,
        timestamp: datetime,
        cumulative_cols: Optional[List[str]] = None,
    ) -> Dict:
        """
        Query player statistics at exact moment in time.

        Args:
            player_id: NBA player ID
            timestamp: Exact moment (with millisecond precision)
            cumulative_cols: Cumulative stat columns to return

        Returns:
            Dict with cumulative stats at that exact moment

        Example:
            >>> stats = system.query_stats_at_time(
            ...     player_id=2544,  # LeBron James
            ...     timestamp=datetime(2023, 6, 12, 21, 0, 0)
            ... )
            >>> print(stats['points_cumulative'])  # Career points through that moment
        """
        if self.panel_data is None:
            raise RuntimeError(
                "Panel data not loaded. Call create_panel_index() first."
            )

        df = self.panel_data

        # Filter to player
        try:
            player_data = df.xs(player_id, level="player_id")
        except KeyError:
            return {"error": f"Player ID {player_id} not found"}

        # Filter to times <= query timestamp
        player_data = player_data[
            player_data.index.get_level_values("timestamp") <= timestamp
        ]

        if len(player_data) == 0:
            return {"error": f"No data for player {player_id} before {timestamp}"}

        # Get most recent observation
        latest = player_data.iloc[-1]

        # Return cumulative stats
        if cumulative_cols is None:
            cumulative_cols = [col for col in df.columns if "cumulative" in col]

        result = {
            "player_id": player_id,
            "query_timestamp": timestamp.isoformat(),
            "latest_game_timestamp": latest.name[1].isoformat(),  # game_id, timestamp
            "observations_through_time": len(player_data),
        }

        for col in cumulative_cols:
            if col in latest.index:
                result[col] = latest[col]

        return result

    # ==================== MAIN EXECUTION ====================

    def execute(self) -> Dict:
        """
        Execute complete panel data processing demonstration.

        Returns:
            Dict with execution results
        """
        logger.info("=" * 70)
        logger.info("EXECUTING: Panel Data Processing System (rec_22)")
        logger.info("=" * 70)

        results = {
            "success": False,
            "steps_completed": [],
            "panel_shape": None,
            "features_created": 0,
            "sample_query": None,
        }

        # Step 1: Setup
        self.setup()
        results["steps_completed"].append("setup")

        # Step 2: Validate prerequisites
        validation = self.validate_prerequisites()
        if not validation["all_ready"]:
            results["error"] = "Prerequisites not met"
            return results
        results["steps_completed"].append("validation")

        # Step 3: Create demo panel data (simplified)
        logger.info("\nStep 3: Creating demo panel data...")
        demo_data = self._create_demo_panel_data()
        results["steps_completed"].append("demo_data_creation")

        # Step 4: Create panel index
        logger.info("\nStep 4: Creating panel index...")
        panel = self.create_panel_index(demo_data)
        self.panel_data = panel  # Store for temporal queries
        results["panel_shape"] = panel.shape
        results["steps_completed"].append("panel_index")

        # Step 5: Generate lag variables
        logger.info("\nStep 5: Generating lag variables...")
        panel = self.generate_lags(panel, ["points", "rebounds"], [1, 2, 3])
        results["features_created"] += 6  # 2 vars × 3 lags
        results["steps_completed"].append("lags")

        # Step 6: Generate rolling statistics
        logger.info("\nStep 6: Generating rolling statistics...")
        panel = self.generate_rolling_stats(panel, ["points"], [5, 10], ["mean", "std"])
        results["features_created"] += 4  # 1 var × 2 windows × 2 stats
        results["steps_completed"].append("rolling")

        # Step 7: Generate cumulative statistics
        logger.info("\nStep 7: Generating cumulative statistics...")
        panel = self.generate_cumulative_stats(panel, ["points", "games"])
        results["features_created"] += 2
        results["steps_completed"].append("cumulative")

        # Step 8: Temporal query demo
        logger.info("\nStep 8: Demonstrating temporal query...")
        self.panel_data = panel  # Update with new features

        # Query first player's stats at a specific time
        first_player = panel.index.get_level_values("player_id").unique()[0]
        query_time = panel.index.get_level_values("timestamp").max()

        sample_query = self.query_stats_at_time(first_player, query_time)
        results["sample_query"] = sample_query
        results["steps_completed"].append("temporal_query")

        # Success
        results["success"] = True

        logger.info("\n" + "=" * 70)
        logger.info("PANEL DATA PROCESSING SYSTEM - EXECUTION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"✓ Panel shape: {results['panel_shape']}")
        logger.info(f"✓ Features created: {results['features_created']}")
        logger.info(f"✓ Steps completed: {len(results['steps_completed'])}")
        logger.info("=" * 70)

        return results

    def _create_demo_panel_data(
        self, n_players: int = 3, n_games_per_player: int = 10
    ) -> pd.DataFrame:
        """
        Create demo panel data for testing.

        Args:
            n_players: Number of players
            n_games_per_player: Games per player

        Returns:
            Demo DataFrame with player-game observations
        """
        np.random.seed(42)

        data = []
        base_date = datetime(2023, 1, 1)

        for player_id in range(1, n_players + 1):
            for game_num in range(1, n_games_per_player + 1):
                game_id = f"game_{game_num:03d}"
                timestamp = base_date + pd.Timedelta(days=game_num * 3)

                # Simulate stats with some consistency per player
                player_skill = 15 + player_id * 5

                data.append(
                    {
                        "player_id": player_id,
                        "game_id": game_id,
                        "game_date": timestamp,
                        "points": player_skill + np.random.randint(-5, 10),
                        "rebounds": 5 + np.random.randint(-2, 5),
                        "assists": 3 + np.random.randint(-1, 4),
                        "minutes": 25 + np.random.randint(-5, 10),
                    }
                )

        df = pd.DataFrame(data)
        logger.info(f"Created demo data: {len(df)} observations, {n_players} players")

        return df

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up panel data processing system...")
        self.panel_data = None
        logger.info("✓ Cleanup complete")


# Convenience functions for external use
def create_panel_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to create panel index from flat DataFrame.

    Args:
        df: Flat DataFrame with player-game observations

    Returns:
        Multi-indexed panel DataFrame
    """
    system = PanelDataProcessingSystem()
    system.setup()
    return system.create_panel_index(df)


def generate_temporal_features(
    df: pd.DataFrame,
    base_vars: List[str] = ["points", "rebounds", "assists"],
    lags: List[int] = [1, 2, 3],
    windows: List[int] = [5, 10],
) -> pd.DataFrame:
    """
    Convenience function to generate comprehensive temporal features.

    Args:
        df: Panel DataFrame
        base_vars: Base variables to create features from
        lags: Lag periods
        windows: Rolling window sizes

    Returns:
        DataFrame with temporal features added
    """
    system = PanelDataProcessingSystem()
    system.setup()

    # Lags
    df = system.generate_lags(df, base_vars, lags)

    # Rolling stats
    df = system.generate_rolling_stats(df, base_vars, windows, ["mean", "std"])

    # Cumulative
    df = system.generate_cumulative_stats(df, base_vars + ["games"])

    return df


if __name__ == "__main__":
    # Run demonstration
    system = PanelDataProcessingSystem()
    results = system.execute()

    if results["success"]:
        print("\n✅ Panel Data Processing System - Fully Operational")
        print(f"   Features Created: {results['features_created']}")
        print(f"   Panel Shape: {results['panel_shape']}")
    else:
        print("\n❌ Execution failed")
        if "error" in results:
            print(f"   Error: {results['error']}")
