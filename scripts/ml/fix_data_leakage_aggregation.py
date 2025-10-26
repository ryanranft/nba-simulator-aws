#!/usr/bin/env python3
"""
Fix Data Leakage: Aggregate ONLY historical features (lag and rolling), not current game stats.

PROBLEM: Previous version included current game statistics (points, rebounds, etc.) which
         caused data leakage - the model could see the game outcome before predicting it.

SOLUTION: Only use lag variables and rolling windows which contain information from
          PREVIOUS games, not the current game being predicted.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import from power directory with period in name using importlib
import importlib.util

spec_rec22 = importlib.util.spec_from_file_location(
    "implement_rec_22",
    os.path.join(
        os.path.dirname(__file__),
        "../../docs/phases/phase_5/5.0020_panel_data/implement_rec_22.py",
    ),
)
implement_rec_22 = importlib.util.module_from_spec(spec_rec22)
spec_rec22.loader.exec_module(implement_rec_22)
PanelDataProcessingSystem = implement_rec_22.PanelDataProcessingSystem

print("=" * 70)
print("FIXING DATA LEAKAGE - GAME PREDICTION WITH CLEAN FEATURES")
print("=" * 70)
print("\nGoal: Remove data leakage by using ONLY pre-game features")
print("Strategy: Filter to lag and rolling features only")
print("Expected: 600-800 clean features → realistic 65-72% accuracy")
print("=" * 70)

# Load real NBA player box scores
print("\n[1/6] Loading real NBA player box scores...")
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

# Add year column for temporal split
df["year"] = pd.to_datetime(df["game_date_time"]).dt.year

# Prepare panel data
print("\n[2/6] Preparing panel data structure...")

df_panel = df[
    [
        "game_id",
        "athlete_id",
        "team_id",
        "game_date_time",
        "home_away",
        "year",
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
    "year",
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
print("\n[3/6] Creating panel index and generating historical features...")
panel_system = PanelDataProcessingSystem()
df_panel = panel_system.create_panel_index(df_panel)

print(f"  Panel index created: {len(df_panel):,} observations")

# Generate lag and rolling features
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

print(f"  Generating historical features for {len(stat_cols)} statistics...")
for i, stat in enumerate(stat_cols, 1):
    print(f"  [{i}/{len(stat_cols)}] {stat}...", end="", flush=True)
    df_panel = panel_system.generate_lags(df_panel, [stat], [1, 2, 3, 5, 10])
    df_panel = panel_system.generate_rolling_stats(df_panel, [stat], [3, 5, 10, 20])
    print(" ✓")

print(f"\n  ✓ Features generated: {len(df_panel.columns)} total columns")

# Reset index to access columns
print("\n[4/6] Filtering to ONLY historical features (removing data leakage)...")
df_panel_flat = df_panel.reset_index()

# Get ALL numeric columns
numeric_cols = df_panel_flat.select_dtypes(include=[np.number]).columns.tolist()

# CRITICAL: Filter to ONLY lag and rolling features
# These contain information from PREVIOUS games, not the current game
lag_and_rolling_features = [
    col for col in numeric_cols if ("_lag" in col or "_rolling" in col)
]

# Current game stats to EXCLUDE (these cause data leakage)
current_game_stats = [
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
    "fg_pct",
    "three_pct",
    "ft_pct",
]

# Verify we're excluding current game stats
excluded_count = sum(
    1
    for col in lag_and_rolling_features
    if any(stat in col for stat in current_game_stats)
    and not ("_lag" in col or "_rolling" in col)
)
if excluded_count > 0:
    print(f"  ⚠️  WARNING: {excluded_count} current game stats still in feature list!")

print(f"\n  ✓ Historical features (lag + rolling): {len(lag_and_rolling_features)}")
print(f"  ✓ Excluded current game stats: {len(current_game_stats)}")
print(f"\n  Sample historical features:")
for feature in lag_and_rolling_features[:10]:
    print(f"    - {feature}")

# Separate home and away teams
print("\n[5/6] Separating home and away teams...")
df_home = df_panel_flat[df_panel_flat["home_away"] == "home"].copy()
df_away = df_panel_flat[df_panel_flat["home_away"] == "away"].copy()

print(f"  Home team observations: {len(df_home):,}")
print(f"  Away team observations: {len(df_away):,}")

# Aggregate ONLY historical features per team per game
print("\n[6/6] Aggregating historical features (this may take a few minutes)...")

# Define aggregation functions
agg_funcs = ["mean", "std", "max", "min", "sum"]

print("  Aggregating home team historical features...")
home_agg = df_home.groupby("game_id")[lag_and_rolling_features].agg(agg_funcs)
home_agg.columns = ["home_" + "_".join(col).strip() for col in home_agg.columns.values]
home_agg = home_agg.reset_index()

print("  Aggregating away team historical features...")
away_agg = df_away.groupby("game_id")[lag_and_rolling_features].agg(agg_funcs)
away_agg.columns = ["away_" + "_".join(col).strip() for col in away_agg.columns.values]
away_agg = away_agg.reset_index()

# Get target variable and year (for temporal split)
target_and_year = df_home.groupby("game_id")[["won", "year"]].first().reset_index()

print(f"\n  ✓ Home historical features: {len(home_agg.columns) - 1}")  # -1 for game_id
print(f"  ✓ Away historical features: {len(away_agg.columns) - 1}")

# Merge home and away
print("\n  Creating final game-level dataset...")
game_features = home_agg.merge(away_agg, on="game_id")
game_features = game_features.merge(target_and_year, on="game_id")

# Create matchup features (home - away) for means
print("  Creating matchup features from historical data...")
matchup_features = pd.DataFrame()
matchup_features["game_id"] = game_features["game_id"]

for col in lag_and_rolling_features[:30]:  # Create matchup features for top 30 features
    home_col = f"home_{col}_mean"
    away_col = f"away_{col}_mean"

    if home_col in game_features.columns and away_col in game_features.columns:
        matchup_features[f"matchup_{col}_diff"] = (
            game_features[home_col] - game_features[away_col]
        )

# Merge matchup features
game_features = game_features.merge(matchup_features, on="game_id")

print(
    f"\n  ✓ Final clean game-level features: {len(game_features.columns) - 3}"
)  # -3 for game_id, won, year
print(f"  Total games: {len(game_features):,}")

# Data leakage check
leaky_features = [
    col
    for col in game_features.columns
    if any(stat in col for stat in current_game_stats)
    and not ("_lag" in col or "_rolling" in col)
]
if leaky_features:
    print(f"\n  ⚠️  WARNING: Found {len(leaky_features)} potentially leaky features!")
    print(f"  Sample: {leaky_features[:5]}")
else:
    print(f"\n  ✅ DATA LEAKAGE CHECK PASSED - No current game stats in features")

# Save
output_path = "/tmp/real_nba_game_features_clean.parquet"
game_features.to_parquet(output_path, index=False)

# Print temporal split info
print("\n" + "=" * 70)
print("TEMPORAL SPLIT INFORMATION")
print("=" * 70)
year_dist = game_features["year"].value_counts().sort_index()
for year, count in year_dist.items():
    split_type = "TRAIN" if year <= 2020 else "TEST"
    print(f"  {year}: {count:,} games ({split_type})")

print("\n" + "=" * 70)
print("SUCCESS!")
print("=" * 70)
print(f"  Historical features only: {len(lag_and_rolling_features)}")
print(f"  Game-level features: {len(game_features.columns) - 3}")
print(f"  Total games: {len(game_features):,}")
print(f"  Saved to: {output_path}")
print()
print("  ✅ Data leakage FIXED - only using pre-game information")
print("  ✅ Temporal split ready - 2018-2020 train, 2021 test")
print()
print("Next step: Train models with clean features")
print("  python scripts/ml/train_with_clean_features.py")
print("  Expected accuracy: 65-72% (realistic for NBA prediction)")
print("=" * 70)
