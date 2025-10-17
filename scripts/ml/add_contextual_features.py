#!/usr/bin/env python3
"""
Add Contextual Features: Team records, win streaks, days of rest, back-to-back games.

These features provide additional context beyond player statistics:
- Team win/loss records up to game date
- Current win/loss streaks
- Days since last game (rest)
- Back-to-back games indicator
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 70)
print("ADD CONTEXTUAL FEATURES")
print("=" * 70)
print("\nGoal: Add team-level context features beyond player statistics")
print("Features: Win records, streaks, rest days, back-to-back games")
print("=" * 70)

# Load original data with timestamps
print("\n[1/6] Loading original game data...")
years = ["2018", "2019", "2020", "2021"]
dfs = []

for year in years:
    df = pd.read_parquet(
        f"s3://nba-sim-raw-data-lake/hoopr_parquet/player_box/nba_data_{year}.parquet"
    )
    dfs.append(df)

df_raw = pd.concat(dfs, ignore_index=True)
print(f"  Loaded: {len(df_raw):,} player-game observations")

# Get unique games with timestamps
print("\n[2/6] Extracting game-level information...")
game_info = df_raw[
    ["game_id", "game_date_time", "team_id", "home_away", "team_winner"]
].drop_duplicates(subset=["game_id", "team_id"])

game_info["timestamp"] = pd.to_datetime(game_info["game_date_time"])
game_info["year"] = game_info["timestamp"].dt.year
game_info["won"] = game_info["team_winner"].astype(int)

print(f"  Unique games: {game_info['game_id'].nunique():,}")
print(f"  Teams: {game_info['team_id'].nunique()}")

# Sort by timestamp for sequential processing
game_info = game_info.sort_values(["team_id", "timestamp"]).reset_index(drop=True)

print("\n[3/6] Computing team records and streaks...")

# Initialize contextual features
game_info["team_wins_prior"] = 0
game_info["team_losses_prior"] = 0
game_info["team_games_prior"] = 0
game_info["team_win_pct_prior"] = 0.0
game_info["team_current_streak"] = 0  # Positive = win streak, negative = loss streak
game_info["days_since_last_game"] = 0.0

# Compute features for each team
teams = game_info["team_id"].unique()
print(f"  Processing {len(teams)} teams...")

for i, team in enumerate(teams, 1):
    if i % 5 == 0:
        print(f"    Progress: {i}/{len(teams)} teams processed...")

    team_games = game_info[game_info["team_id"] == team].copy()

    wins_prior = 0
    losses_prior = 0
    current_streak = 0
    last_game_date = None

    for idx in team_games.index:
        game_date = game_info.loc[idx, "timestamp"]
        won = game_info.loc[idx, "won"]

        # Set prior record (before this game)
        game_info.loc[idx, "team_wins_prior"] = wins_prior
        game_info.loc[idx, "team_losses_prior"] = losses_prior
        game_info.loc[idx, "team_games_prior"] = wins_prior + losses_prior

        if wins_prior + losses_prior > 0:
            game_info.loc[idx, "team_win_pct_prior"] = wins_prior / (
                wins_prior + losses_prior
            )

        # Set current streak (before this game)
        game_info.loc[idx, "team_current_streak"] = current_streak

        # Days since last game
        if last_game_date is not None:
            days_rest = (game_date - last_game_date).total_seconds() / 86400
            game_info.loc[idx, "days_since_last_game"] = days_rest

        # Update for next iteration
        if won == 1:
            wins_prior += 1
            current_streak = current_streak + 1 if current_streak >= 0 else 1
        else:
            losses_prior += 1
            current_streak = current_streak - 1 if current_streak <= 0 else -1

        last_game_date = game_date

print(f"  ✓ Computed team records and streaks")

# Add back-to-back indicator
print("\n[4/6] Adding back-to-back game indicators...")
game_info["is_back_to_back"] = (game_info["days_since_last_game"] <= 1.5).astype(int)
print(
    f"  Back-to-back games: {game_info['is_back_to_back'].sum():,} ({game_info['is_back_to_back'].mean():.1%})"
)

# Pivot to game level (home vs away)
print("\n[5/6] Pivoting to game-level features...")

home_features = game_info[game_info["home_away"] == "home"][
    [
        "game_id",
        "team_wins_prior",
        "team_losses_prior",
        "team_games_prior",
        "team_win_pct_prior",
        "team_current_streak",
        "days_since_last_game",
        "is_back_to_back",
    ]
].copy()

home_features.columns = [
    "game_id",
    "home_wins_prior",
    "home_losses_prior",
    "home_games_prior",
    "home_win_pct_prior",
    "home_current_streak",
    "home_days_rest",
    "home_back_to_back",
]

away_features = game_info[game_info["home_away"] == "away"][
    [
        "game_id",
        "team_wins_prior",
        "team_losses_prior",
        "team_games_prior",
        "team_win_pct_prior",
        "team_current_streak",
        "days_since_last_game",
        "is_back_to_back",
    ]
].copy()

away_features.columns = [
    "game_id",
    "away_wins_prior",
    "away_losses_prior",
    "away_games_prior",
    "away_win_pct_prior",
    "away_current_streak",
    "away_days_rest",
    "away_back_to_back",
]

# Merge home and away
contextual_features = home_features.merge(away_features, on="game_id", how="inner")

# Add matchup features
contextual_features["matchup_win_pct_diff"] = (
    contextual_features["home_win_pct_prior"]
    - contextual_features["away_win_pct_prior"]
)
contextual_features["matchup_wins_diff"] = (
    contextual_features["home_wins_prior"] - contextual_features["away_wins_prior"]
)
contextual_features["matchup_streak_diff"] = (
    contextual_features["home_current_streak"]
    - contextual_features["away_current_streak"]
)
contextual_features["matchup_rest_diff"] = (
    contextual_features["home_days_rest"] - contextual_features["away_days_rest"]
)

print(
    f"  Game-level contextual features: {len(contextual_features.columns) - 1}"
)  # -1 for game_id
print(f"  Games with features: {len(contextual_features):,}")

# Add year for joining
year_mapping = game_info[["game_id", "year"]].drop_duplicates()
contextual_features = contextual_features.merge(year_mapping, on="game_id", how="left")

# Load selected features and merge
print("\n[6/6] Merging with selected features...")
df_selected = pd.read_parquet("/tmp/real_nba_game_features_selected.parquet")

print(f"  Before merge: {len(df_selected.columns)} columns")

# Merge
df_enhanced = df_selected.merge(contextual_features, on=["game_id", "year"], how="left")

# Fill any NaN values (early season games with no prior record)
contextual_cols = [col for col in df_enhanced.columns if col not in df_selected.columns]
for col in contextual_cols:
    if df_enhanced[col].isna().any():
        if "pct" in col:
            df_enhanced[col] = df_enhanced[col].fillna(0.5)  # 50% win rate
        else:
            df_enhanced[col] = df_enhanced[col].fillna(0)

print(f"  After merge: {len(df_enhanced.columns)} columns")
print(f"  New contextual features: {len(contextual_cols)}")
print(f"\n  Contextual features added:")
for col in sorted(contextual_cols):
    print(f"    - {col}")

# Save enhanced dataset
output_path = "/tmp/real_nba_game_features_enhanced.parquet"
df_enhanced.to_parquet(output_path, index=False)

print(f"\n  ✓ Saved to: {output_path}")

# Summary statistics
print("\n" + "=" * 70)
print("CONTEXTUAL FEATURES SUMMARY")
print("=" * 70)

print(f"\nDataset:")
print(f"  Total games: {len(df_enhanced):,}")
print(f"  Total features: {len(df_enhanced.columns) - 3}")  # -3 for game_id, won, year
print(f"  - Player panel features: 300")
print(f"  - Contextual features: {len(contextual_cols)}")

print(f"\nSample contextual feature statistics:")
print(
    f"  Home win %: {df_enhanced['home_win_pct_prior'].mean():.1%} ± {df_enhanced['home_win_pct_prior'].std():.1%}"
)
print(
    f"  Away win %: {df_enhanced['away_win_pct_prior'].mean():.1%} ± {df_enhanced['away_win_pct_prior'].std():.1%}"
)
print(
    f"  Win % diff (home - away): {df_enhanced['matchup_win_pct_diff'].mean():.1%} ± {df_enhanced['matchup_win_pct_diff'].std():.1%}"
)
print(
    f"  Days rest (home): {df_enhanced['home_days_rest'].mean():.1f} ± {df_enhanced['home_days_rest'].std():.1f}"
)
print(
    f"  Back-to-back games: {df_enhanced['home_back_to_back'].mean():.1%} home, {df_enhanced['away_back_to_back'].mean():.1%} away"
)

print("\n" + "=" * 70)
print("✓ Contextual features added successfully!")
print("\nNext Steps:")
print("  1. Re-train model with enhanced features")
print("  2. Validate final performance")
print("  3. Update documentation")
print("=" * 70)
