#!/usr/bin/env python3
"""
Improved Feature Aggregation: Convert 149 player-level panel features to game-level features.

Key improvements:
1. Aggregate ALL 149 features (not just 14)
2. Separate home/away teams
3. Create team-level aggregations (mean, std, max, min, sum)
4. Create matchup features (home - away)
5. Expected result: ~750 game-level features
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import from power directories with periods in names using importlib
import importlib.util
spec_rec22 = importlib.util.spec_from_file_location(
    "implement_rec_22",
    os.path.join(os.path.dirname(__file__), "../../docs/phases/phase_5/5.20_panel_data/implement_rec_22.py")
)
implement_rec_22 = importlib.util.module_from_spec(spec_rec22)
spec_rec22.loader.exec_module(implement_rec_22)
PanelDataProcessingSystem = implement_rec_22.PanelDataProcessingSystem

spec_rec11 = importlib.util.spec_from_file_location(
    "implement_rec_11",
    os.path.join(os.path.dirname(__file__), "../../docs/phases/phase_5/5.1_feature_engineering/implement_rec_11.py")
)
implement_rec_11 = importlib.util.module_from_spec(spec_rec11)
spec_rec11.loader.exec_module(implement_rec_11)
AdvancedFeatureEngineeringPipeline = implement_rec_11.AdvancedFeatureEngineeringPipeline

print("=" * 70)
print("IMPROVED FEATURE AGGREGATION FOR NBA GAME PREDICTION")
print("=" * 70)
print("\nGoal: Convert 149 player-level features → game-level features")
print("Strategy: Home/away team aggregations + matchup features")
print("Expected: ~750 game-level features → 68-71% accuracy")
print("=" * 70)

# Load real NBA player box scores (reusing previous work)
print("\n[1/7] Loading real NBA player box scores...")
years = ["2018", "2019", "2020", "2021"]
dfs = []

for year in years:
    df = pd.read_parquet(
        f"s3://nba-sim-raw-data-lake/hoopr_parquet/player_box/nba_data_{year}.parquet"
    )
    dfs.append(df)
    print(f"  ✓ Loaded {year}: {len(df):,} player-game observations")

df = pd.concat(dfs, ignore_index=True)
print(f"\n  Total observations: {len(df):,}")

# Prepare panel data
print("\n[2/7] Preparing panel data structure...")

# Need home_away flag for team separation
df_panel = df[
    [
        "game_id",
        "athlete_id",
        "team_id",
        "game_date_time",
        "home_away",
        "minutes",
        "points",
        "rebounds",
        "assists",
        "field_goals_made",
        "field_goals_attempted",
        "three_point_field_goals_made",
        "three_point_field_goals_attempted",
        "free_throws_made",
        "free_throws_attempted",
        "steals",
        "blocks",
        "turnovers",
        "fouls",
        "team_winner",
    ]
].copy()

df_panel.columns = [
    "game_id",
    "player_id",
    "team_id",
    "timestamp",
    "home_away",
    "minutes",
    "points",
    "rebounds",
    "assists",
    "fgm",
    "fga",
    "three_pm",
    "three_pa",
    "ftm",
    "fta",
    "steals",
    "blocks",
    "turnovers",
    "fouls",
    "won",
]

# Calculate percentages
df_panel["fg_pct"] = df_panel["fgm"] / df_panel["fga"].replace(0, np.nan)
df_panel["three_pct"] = df_panel["three_pm"] / df_panel["three_pa"].replace(0, np.nan)
df_panel["ft_pct"] = df_panel["ftm"] / df_panel["fta"].replace(0, np.nan)
df_panel[["fg_pct", "three_pct", "ft_pct"]] = df_panel[
    ["fg_pct", "three_pct", "ft_pct"]
].fillna(0)

df_panel["won"] = df_panel["won"].astype(int)
df_panel = df_panel.sort_values(["player_id", "timestamp"]).reset_index(drop=True)

print(f"  ✓ Panel data prepared: {df_panel.shape}")

# Create panel index and generate features
print("\n[3/7] Creating panel index and generating features...")
panel_system = PanelDataProcessingSystem()
df_panel = panel_system.create_panel_index(df_panel)

print(f"  Panel index created: {len(df_panel):,} observations")

# Generate features
stat_cols = [
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
]

print(f"  Generating features for {len(stat_cols)} statistics...")
for i, stat in enumerate(stat_cols, 1):
    print(f"  [{i}/{len(stat_cols)}] {stat}...", end="", flush=True)
    df_panel = panel_system.generate_lags(df_panel, [stat], [1, 2, 3, 5, 10])
    df_panel = panel_system.generate_rolling_stats(df_panel, [stat], [3, 5, 10, 20])
    print(" ✓")

print(f"\n  ✓ Features generated: {len(df_panel.columns)} player-level features")

# Reset index to access columns
print("\n[4/7] Preparing for improved aggregation...")
df_panel_flat = df_panel.reset_index()

# Get numeric columns (features to aggregate)
numeric_cols = df_panel_flat.select_dtypes(include=[np.number]).columns.tolist()

# Exclude ID columns and target
exclude_cols = ["player_id", "team_id", "won", "game_id"]
feature_cols = [col for col in numeric_cols if col not in exclude_cols]

print(f"  ✓ Features to aggregate: {len(feature_cols)}")
print(f"  Sample features: {feature_cols[:10]}...")

# Separate home and away teams
print("\n[5/7] Separating home and away teams...")
df_home = df_panel_flat[df_panel_flat["home_away"] == "home"].copy()
df_away = df_panel_flat[df_panel_flat["home_away"] == "away"].copy()

print(f"  Home team observations: {len(df_home):,}")
print(f"  Away team observations: {len(df_away):,}")

# Aggregate features per team per game
print("\n[6/7] Aggregating features (this may take a few minutes)...")

# Define aggregation functions
agg_funcs = ["mean", "std", "max", "min", "sum"]

print("  Aggregating home team features...")
home_agg = df_home.groupby("game_id")[feature_cols].agg(agg_funcs)
home_agg.columns = ["home_" + "_".join(col).strip() for col in home_agg.columns.values]
home_agg = home_agg.reset_index()

print("  Aggregating away team features...")
away_agg = df_away.groupby("game_id")[feature_cols].agg(agg_funcs)
away_agg.columns = ["away_" + "_".join(col).strip() for col in away_agg.columns.values]
away_agg = away_agg.reset_index()

# Get target variable (same for all players in a game)
target = df_home.groupby("game_id")["won"].first().reset_index()

print(f"\n  ✓ Home features: {len(home_agg.columns) - 1}")  # -1 for game_id
print(f"  ✓ Away features: {len(away_agg.columns) - 1}")

# Merge home and away
print("\n[7/7] Creating final game-level dataset...")
game_features = home_agg.merge(away_agg, on="game_id")
game_features = game_features.merge(target, on="game_id")

# Create matchup features (home - away) for means
print("  Creating matchup features...")
matchup_features = pd.DataFrame()
matchup_features["game_id"] = game_features["game_id"]

for col in feature_cols[:20]:  # Create matchup features for top 20 features
    home_col = f"home_{col}_mean"
    away_col = f"away_{col}_mean"

    if home_col in game_features.columns and away_col in game_features.columns:
        matchup_features[f"matchup_{col}_diff"] = (
            game_features[home_col] - game_features[away_col]
        )

# Merge matchup features
game_features = game_features.merge(matchup_features, on="game_id")

print(
    f"\n  ✓ Final game-level features: {len(game_features.columns) - 2}"
)  # -2 for game_id and won
print(f"  Total games: {len(game_features):,}")

# Save
output_path = "/tmp/real_nba_game_features_improved.parquet"
game_features.to_parquet(output_path, index=False)

print("\n" + "=" * 70)
print("SUCCESS!")
print("=" * 70)
print(f"  Player-level features: 149")
print(f"  Game-level features: {len(game_features.columns) - 2}")
print(f"  Improvement: {len(game_features.columns) - 2} vs 14 (previous)")
print(f"  Saved to: {output_path}")
print()
print("Next step: Train models with improved features")
print("  python scripts/ml/train_with_improved_features.py")
print("  Expected accuracy: 68-71% (vs 54.4% previous)")
print("=" * 70)
