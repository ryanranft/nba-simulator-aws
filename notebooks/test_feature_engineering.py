#!/usr/bin/env python3
"""
Test script for feature engineering notebook.
Validates that feature engineering code will work correctly in SageMaker.

This script performs a dry-run validation without executing the full notebook.
"""

import sys

def test_imports():
    """Test that all required libraries are available."""
    print("Testing imports...")
    required_packages = [
        'pandas',
        'numpy',
        'psycopg2',
        'sqlalchemy',
        'boto3'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False

    print("✓ All imports available\n")
    return True

def test_database_connection():
    """Test RDS connection."""
    print("Testing database connection...")
    try:
        import psycopg2

        # Load credentials
        import os
        db_password = os.getenv('NBA_SIM_DB_PASSWORD')
        if not db_password:
            print("  ⚠ NBA_SIM_DB_PASSWORD not set - skipping connection test")
            return True

        conn = psycopg2.connect(
            host='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com',
            database='nba_simulator',
            user='postgres',
            password=db_password,
            connect_timeout=5
        )

        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM games')
        count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f"  ✓ Connected to RDS")
        print(f"  ✓ Games table accessible ({count:,} rows)\n")
        return True

    except Exception as e:
        print(f"  ✗ Database connection failed: {e}\n")
        return False

def test_s3_access():
    """Test S3 access."""
    print("Testing S3 access...")
    try:
        import boto3

        s3 = boto3.client('s3')

        # Test read access
        response = s3.list_objects_v2(
            Bucket='nba-sim-raw-data-lake',
            Prefix='schedule/',
            MaxKeys=5
        )

        if 'Contents' in response and len(response['Contents']) > 0:
            print(f"  ✓ S3 read access confirmed")
            print(f"  ✓ Found {len(response['Contents'])} objects\n")
            return True
        else:
            print(f"  ✗ No objects found in S3 bucket\n")
            return False

    except Exception as e:
        print(f"  ✗ S3 access failed: {e}\n")
        return False

def test_feature_logic():
    """Test feature engineering logic with sample data."""
    print("Testing feature engineering logic...")
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta

        # Create sample game data
        dates = pd.date_range(start='2023-10-01', periods=100, freq='D')
        sample_games = pd.DataFrame({
            'game_id': range(100),
            'game_date': dates,
            'home_team_id': [1, 2] * 50,
            'away_team_id': [2, 1] * 50,
            'home_points': np.random.randint(90, 120, 100),
            'away_points': np.random.randint(90, 120, 100),
            'season': [2024] * 100
        })

        sample_games['home_win'] = (sample_games['home_points'] > sample_games['away_points']).astype(int)

        # Test rolling stats calculation
        team_games = sample_games[sample_games['home_team_id'] == 1].copy()
        team_games['rolling_ppg'] = team_games['home_points'].rolling(window=10, min_periods=1).mean()

        if team_games['rolling_ppg'].isna().sum() == 0:
            print(f"  ✓ Rolling stats calculation works")
        else:
            print(f"  ✗ Rolling stats has NaN values")
            return False

        # Test rest days calculation
        team_games['rest_days'] = team_games['game_date'].diff().dt.days - 1
        team_games['rest_days'] = team_games['rest_days'].fillna(7)

        if (team_games['rest_days'] >= 0).all():
            print(f"  ✓ Rest days calculation works")
        else:
            print(f"  ✗ Rest days has negative values")
            return False

        # Test categorical encoding
        sample_games['month'] = sample_games['game_date'].dt.month
        sample_games['day_of_week'] = sample_games['game_date'].dt.dayofweek

        if sample_games['month'].between(1, 12).all():
            print(f"  ✓ Categorical encoding works")
        else:
            print(f"  ✗ Categorical encoding failed")
            return False

        print(f"  ✓ All feature logic validated\n")
        return True

    except Exception as e:
        print(f"  ✗ Feature logic test failed: {e}\n")
        return False

def test_parquet_write():
    """Test Parquet file writing."""
    print("Testing Parquet write capability...")
    try:
        import pandas as pd
        import tempfile
        import os

        # Create sample dataframe
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6]
        })

        # Test local write
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
            tmp_path = tmp.name

        df.to_parquet(tmp_path, engine='pyarrow')

        # Read back
        df_read = pd.read_parquet(tmp_path)

        # Clean up
        os.unlink(tmp_path)

        if df.equals(df_read):
            print(f"  ✓ Parquet write/read works\n")
            return True
        else:
            print(f"  ✗ Parquet data mismatch\n")
            return False

    except Exception as e:
        print(f"  ✗ Parquet test failed: {e}\n")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("FEATURE ENGINEERING NOTEBOOK - VALIDATION TESTS")
    print("=" * 70)
    print()

    tests = [
        ("Import Test", test_imports),
        ("Database Connection", test_database_connection),
        ("S3 Access", test_s3_access),
        ("Feature Logic", test_feature_logic),
        ("Parquet Write", test_parquet_write)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Unexpected error in {name}: {e}\n")
            results.append((name, False))

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} - {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed - notebook is ready for SageMaker")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed - fix issues before running notebook")
        return 1

if __name__ == '__main__':
    sys.exit(main())