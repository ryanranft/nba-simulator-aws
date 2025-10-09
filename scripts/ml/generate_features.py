#!/usr/bin/env python3
"""
Feature Engineering Script for NBA Game Prediction
Converted from 02_feature_engineering.ipynb for command-line execution
"""

import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
import boto3
from datetime import datetime
import os
import sys

# Database configuration
DB_HOST = 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'
DB_NAME = 'nba_simulator'
DB_USER = 'postgres'
DB_PORT = 5432

# Load password from credentials file or environment
DB_PASSWORD = os.getenv('DB_PASSWORD') or os.getenv('NBA_SIM_DB_PASSWORD')
if not DB_PASSWORD:
    # Try to load from credentials file
    cred_file = os.path.expanduser('~/nba-sim-credentials.env')
    if os.path.exists(cred_file):
        with open(cred_file) as f:
            for line in f:
                line = line.strip()
                if ('DB_PASSWORD' in line or 'NBA_SIM_DB_PASSWORD' in line) and '=' in line:
                    # Handle both 'export VAR=value' and 'VAR=value' formats
                    if line.startswith('export '):
                        line = line[7:]  # Remove 'export '
                    if 'DB_PASSWORD=' in line:
                        DB_PASSWORD = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break

# S3 configuration
S3_BUCKET = 'nba-sim-raw-data-lake'
S3_PREFIX = 'ml-features'

def main():
    print("=" * 70)
    print("NBA GAME PREDICTION - FEATURE ENGINEERING")
    print("=" * 70)
    print()

    # Check password
    if not DB_PASSWORD:
        print("❌ Error: NBA_SIM_DB_PASSWORD environment variable not set")
        print("Load credentials with: source ~/nba-sim-credentials.env")
        sys.exit(1)

    # 1. Connect to database
    print("[1/7] Connecting to RDS database...")
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require')

    # Validate connection
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text('SELECT COUNT(*) FROM games'))
            count = result.fetchone()[0]
            print(f"✓ Connected to RDS ({count:,} games in database)")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # 2. Load game data
    print("\n[2/7] Loading game data...")
    games_query = """
        SELECT
            game_id, game_date, season,
            home_team_id, away_team_id,
            home_score, away_score,
            CASE WHEN home_score > away_score THEN 1 ELSE 0 END as home_win
        FROM games
        WHERE home_score IS NOT NULL
        AND away_score IS NOT NULL
        AND completed = true
        ORDER BY game_date
    """

    games = pd.read_sql(games_query, engine)
    games['game_date'] = pd.to_datetime(games['game_date'])

    # Rename to match expected column names in rest of script
    games = games.rename(columns={
        'home_score': 'home_points',
        'away_score': 'away_points'
    })

    print(f"✓ Loaded {len(games):,} games")
    print(f"  Date range: {games['game_date'].min()} to {games['game_date'].max()}")
    print(f"  Home win rate: {games['home_win'].mean():.3f}")

    # 3. Calculate rolling statistics
    print("\n[3/7] Calculating team rolling statistics...")
    print("  This may take 5-10 minutes...")

    all_teams = pd.concat([games['home_team_id'], games['away_team_id']]).unique()
    print(f"  Processing {len(all_teams)} teams...")

    def calculate_rolling_stats(games_df, team_id, is_home=True, window=10):
        """Calculate rolling statistics for a team"""
        if is_home:
            team_games = games_df[games_df['home_team_id'] == team_id].copy()
            team_games['points_for'] = team_games['home_points']
            team_games['points_against'] = team_games['away_points']
            team_games['won'] = team_games['home_win']
        else:
            team_games = games_df[games_df['away_team_id'] == team_id].copy()
            team_games['points_for'] = team_games['away_points']
            team_games['points_against'] = team_games['home_points']
            team_games['won'] = 1 - team_games['home_win']

        team_games = team_games.sort_values('game_date')

        # Calculate rolling statistics (using past games only)
        team_games['rolling_win_pct'] = team_games['won'].rolling(window=window, min_periods=1).mean().shift(1)
        team_games['rolling_ppg'] = team_games['points_for'].rolling(window=window, min_periods=1).mean().shift(1)
        team_games['rolling_papg'] = team_games['points_against'].rolling(window=window, min_periods=1).mean().shift(1)
        team_games['rolling_margin'] = team_games['rolling_ppg'] - team_games['rolling_papg']

        return team_games[['game_id', 'rolling_win_pct', 'rolling_ppg', 'rolling_papg', 'rolling_margin']]

    home_stats_list = []
    away_stats_list = []

    for i, team_id in enumerate(all_teams, 1):
        if i % 10 == 0:
            print(f"    Progress: {i}/{len(all_teams)} teams...")

        home_stats = calculate_rolling_stats(games, team_id, is_home=True)
        home_stats = home_stats.rename(columns={
            'rolling_win_pct': 'home_rolling_win_pct',
            'rolling_ppg': 'home_rolling_ppg',
            'rolling_papg': 'home_rolling_papg',
            'rolling_margin': 'home_rolling_margin'
        })
        home_stats_list.append(home_stats)

        away_stats = calculate_rolling_stats(games, team_id, is_home=False)
        away_stats = away_stats.rename(columns={
            'rolling_win_pct': 'away_rolling_win_pct',
            'rolling_ppg': 'away_rolling_ppg',
            'rolling_papg': 'away_rolling_papg',
            'rolling_margin': 'away_rolling_margin'
        })
        away_stats_list.append(away_stats)

    home_stats_df = pd.concat(home_stats_list, ignore_index=True)
    away_stats_df = pd.concat(away_stats_list, ignore_index=True)

    games_with_stats = games.merge(home_stats_df, on='game_id', how='left')
    games_with_stats = games_with_stats.merge(away_stats_df, on='game_id', how='left')

    print(f"✓ Rolling statistics calculated for {len(all_teams)} teams")

    # 4. Calculate rest days
    print("\n[4/7] Calculating rest days and back-to-backs...")

    def calculate_rest_days(games_df, team_id, is_home=True):
        """Calculate rest days since last game"""
        if is_home:
            team_games = games_df[games_df['home_team_id'] == team_id].copy()
        else:
            team_games = games_df[games_df['away_team_id'] == team_id].copy()

        team_games = team_games.sort_values('game_date')
        team_games['rest_days'] = team_games['game_date'].diff().dt.days - 1
        team_games['rest_days'] = team_games['rest_days'].fillna(7)
        team_games['back_to_back'] = (team_games['rest_days'] == 0).astype(int)

        return team_games[['game_id', 'rest_days', 'back_to_back']]

    home_rest_list = []
    away_rest_list = []

    for team_id in all_teams:
        home_rest = calculate_rest_days(games, team_id, is_home=True)
        home_rest = home_rest.rename(columns={
            'rest_days': 'home_rest_days',
            'back_to_back': 'home_back_to_back'
        })
        home_rest_list.append(home_rest)

        away_rest = calculate_rest_days(games, team_id, is_home=False)
        away_rest = away_rest.rename(columns={
            'rest_days': 'away_rest_days',
            'back_to_back': 'away_back_to_back'
        })
        away_rest_list.append(away_rest)

    home_rest_df = pd.concat(home_rest_list, ignore_index=True)
    away_rest_df = pd.concat(away_rest_list, ignore_index=True)

    games_with_stats = games_with_stats.merge(home_rest_df, on='game_id', how='left')
    games_with_stats = games_with_stats.merge(away_rest_df, on='game_id', how='left')

    print("✓ Rest days calculated")

    # 5. Add temporal features
    print("\n[5/7] Adding temporal features...")

    games_with_stats['month'] = games_with_stats['game_date'].dt.month
    games_with_stats['day_of_week'] = games_with_stats['game_date'].dt.dayofweek
    games_with_stats['is_weekend'] = (games_with_stats['day_of_week'] >= 5).astype(int)

    # Season phase (early/mid/late) - NBA season spans Oct-Apr
    # Early: Oct-Dec (10, 11, 12), Mid: Jan-Feb (1, 2), Late: Mar-Apr (3, 4)
    games_with_stats['season_phase'] = games_with_stats['month'].map({
        10: 0, 11: 0, 12: 0,  # Early season
        1: 1, 2: 1,           # Mid season
        3: 2, 4: 2, 5: 2, 6: 2  # Late season (includes playoffs)
    }).fillna(0).astype(int)

    print("✓ Temporal features added")

    # 6. Select features and clean
    print("\n[6/7] Preparing final feature set...")

    feature_columns = [
        'game_id', 'game_date', 'season',
        'home_team_id', 'away_team_id',
        'home_win',
        'home_rolling_win_pct', 'home_rolling_ppg', 'home_rolling_papg', 'home_rolling_margin',
        'home_rest_days', 'home_back_to_back',
        'away_rolling_win_pct', 'away_rolling_ppg', 'away_rolling_papg', 'away_rolling_margin',
        'away_rest_days', 'away_back_to_back',
        'month', 'day_of_week', 'is_weekend', 'season_phase'
    ]

    features_df = games_with_stats[feature_columns].copy()
    features_df_clean = features_df.dropna()

    print(f"✓ Feature set prepared")
    print(f"  Total features: {len(feature_columns) - 5} (excluding IDs)")
    print(f"  Before cleaning: {len(features_df):,} rows")
    print(f"  After cleaning:  {len(features_df_clean):,} rows")
    print(f"  Dropped: {len(features_df) - len(features_df_clean):,} rows with missing values")

    # Create train/test split (80/20 chronological)
    features_df_clean = features_df_clean.sort_values('game_date')
    split_idx = int(len(features_df_clean) * 0.8)

    train_df = features_df_clean.iloc[:split_idx]
    test_df = features_df_clean.iloc[split_idx:]

    print(f"\nTrain/Test Split:")
    print(f"  Train: {len(train_df):,} rows ({train_df['game_date'].min()} to {train_df['game_date'].max()})")
    print(f"  Test:  {len(test_df):,} rows ({test_df['game_date'].min()} to {test_df['game_date'].max()})")

    # 7. Save to S3
    print(f"\n[7/7] Saving features to S3...")

    # Save locally first, then upload to S3
    import tempfile

    s3 = boto3.client('s3')

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save full dataset
        full_local = f'{tmpdir}/game_features.parquet'
        train_local = f'{tmpdir}/train.parquet'
        test_local = f'{tmpdir}/test.parquet'

        print(f"  Saving full dataset locally...")
        features_df_clean.to_parquet(full_local, engine='pyarrow', index=False)

        print(f"  Saving train set locally...")
        train_df.to_parquet(train_local, engine='pyarrow', index=False)

        print(f"  Saving test set locally...")
        test_df.to_parquet(test_local, engine='pyarrow', index=False)

        # Upload to S3
        print(f"  Uploading to S3...")
        s3.upload_file(full_local, S3_BUCKET, f'{S3_PREFIX}/game_features.parquet')
        print(f"    ✓ Uploaded game_features.parquet")

        s3.upload_file(train_local, S3_BUCKET, f'{S3_PREFIX}/train.parquet')
        print(f"    ✓ Uploaded train.parquet")

        s3.upload_file(test_local, S3_BUCKET, f'{S3_PREFIX}/test.parquet')
        print(f"    ✓ Uploaded test.parquet")

    # Verify upload
    try:
        response = s3.head_object(Bucket=S3_BUCKET, Key=f'{S3_PREFIX}/game_features.parquet')
        file_size_mb = response['ContentLength'] / (1024 * 1024)
        print(f"\n✓ Upload verified: {file_size_mb:.2f} MB")
    except Exception as e:
        print(f"⚠️  Could not verify upload: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("FEATURE ENGINEERING COMPLETE")
    print("=" * 70)
    print(f"\n📊 Features Generated:")
    print(f"  Total games: {len(features_df_clean):,}")
    print(f"  Features: {len(feature_columns) - 5}")
    print(f"  Train set: {len(train_df):,} games")
    print(f"  Test set: {len(test_df):,} games")
    print(f"\n💾 S3 Outputs:")
    print(f"  Full: s3://{S3_BUCKET}/{S3_PREFIX}/game_features.parquet")
    print(f"  Train: s3://{S3_BUCKET}/{S3_PREFIX}/train.parquet")
    print(f"  Test: s3://{S3_BUCKET}/{S3_PREFIX}/test.parquet")
    print(f"\n🎯 Next Steps:")
    print(f"  1. Train baseline models (Logistic Regression, Random Forest)")
    print(f"  2. Train advanced models (XGBoost, LightGBM)")
    print(f"  3. Evaluate and select best model")
    print("=" * 70)

if __name__ == '__main__':
    main()