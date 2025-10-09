#!/usr/bin/env python3
"""
Create Unified Multi-Source NBA Database

Creates a comprehensive database combining ESPN, hoopR, NBA API, Basketball Reference,
and Kaggle data sources with discrepancy tracking for ML data quality.

CRITICAL: This unified database is SEPARATE from source databases.
Source databases remain pure - no cross-contamination.

Database Structure:
1. unified_play_by_play - All PBP events from all sources
2. unified_schedule - All games from all sources
3. source_coverage - Which sources have each game
4. data_quality_discrepancies - Where sources disagree
5. quality_scores - ML-ready quality assessment per game

Usage:
    python scripts/db/create_unified_database.py --create-local
    python scripts/db/create_unified_database.py --create-rds
    python scripts/db/create_unified_database.py --create-both

Version: 1.0
Created: October 9, 2025
"""

import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import argparse
from pathlib import Path

# Load credentials
load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

# Database paths
UNIFIED_LOCAL_DB = "/tmp/unified_nba.db"

# RDS configuration
RDS_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', 5432),
    'sslmode': 'require'
}


def create_local_unified_database():
    """Create local SQLite unified database."""

    print("=" * 70)
    print("CREATE LOCAL UNIFIED DATABASE")
    print("=" * 70)
    print()

    print(f"Database path: {UNIFIED_LOCAL_DB}")
    print()

    # Remove existing if present
    if Path(UNIFIED_LOCAL_DB).exists():
        response = input("Database exists. Overwrite? (yes/no): ").strip().lower()
        if response == 'yes':
            Path(UNIFIED_LOCAL_DB).unlink()
            print("✓ Removed existing database")
        else:
            print("Cancelled")
            return

    # Create database
    conn = sqlite3.connect(UNIFIED_LOCAL_DB)
    cursor = conn.cursor()
    print("✓ Created new database")
    print()

    # Create tables
    print("Creating tables...")
    print()

    # 1. Unified play-by-play
    print("  Creating: unified_play_by_play")
    cursor.execute("""
        CREATE TABLE unified_play_by_play (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            source TEXT NOT NULL CHECK (source IN ('ESPN', 'hoopR', 'NBA_API', 'BBRef', 'Kaggle')),

            -- Common fields (mapped from all sources)
            game_date DATE NOT NULL,
            period_number INTEGER,
            clock_display TEXT,
            clock_seconds REAL,
            event_description TEXT,
            home_score INTEGER,
            away_score INTEGER,
            scoring_play BOOLEAN,
            score_value INTEGER,

            -- Team/Player
            team_id TEXT,
            player_id TEXT,

            -- Coordinates
            coordinate_x REAL,
            coordinate_y REAL,

            -- Type
            event_type TEXT,

            -- Source-specific fields preserved
            raw_json TEXT,

            -- Metadata
            quality_score NUMERIC,  -- 0-100
            is_primary BOOLEAN DEFAULT FALSE,  -- TRUE if recommended source
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("CREATE INDEX idx_unified_pbp_game_id ON unified_play_by_play(game_id);")
    cursor.execute("CREATE INDEX idx_unified_pbp_source ON unified_play_by_play(source);")
    cursor.execute("CREATE INDEX idx_unified_pbp_date ON unified_play_by_play(game_date);")
    cursor.execute("CREATE INDEX idx_unified_pbp_primary ON unified_play_by_play(is_primary);")

    # 2. Unified schedule
    print("  Creating: unified_schedule")
    cursor.execute("""
        CREATE TABLE unified_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            source TEXT NOT NULL CHECK (source IN ('ESPN', 'hoopR', 'NBA_API', 'BBRef', 'Kaggle')),

            -- Game info
            game_date DATE NOT NULL,
            season INTEGER,
            game_type TEXT,  -- Regular, Playoff, etc.

            -- Teams
            home_team_id TEXT,
            home_team_name TEXT,
            away_team_id TEXT,
            away_team_name TEXT,

            -- Score
            home_score INTEGER,
            away_score INTEGER,

            -- Metadata
            has_pbp BOOLEAN DEFAULT FALSE,
            pbp_event_count INTEGER,
            quality_score NUMERIC,
            is_primary BOOLEAN DEFAULT FALSE,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("CREATE INDEX idx_unified_schedule_game_id ON unified_schedule(game_id);")
    cursor.execute("CREATE INDEX idx_unified_schedule_source ON unified_schedule(source);")
    cursor.execute("CREATE INDEX idx_unified_schedule_date ON unified_schedule(game_date);")

    # 3. Source coverage tracking
    print("  Creating: source_coverage")
    cursor.execute("""
        CREATE TABLE source_coverage (
            game_id TEXT PRIMARY KEY,
            game_date DATE NOT NULL,

            -- Which sources have this game?
            has_espn BOOLEAN DEFAULT FALSE,
            has_hoopr BOOLEAN DEFAULT FALSE,
            has_nba_api BOOLEAN DEFAULT FALSE,
            has_bbref BOOLEAN DEFAULT FALSE,
            has_kaggle BOOLEAN DEFAULT FALSE,

            -- Event counts per source
            espn_event_count INTEGER,
            hoopr_event_count INTEGER,
            nba_api_event_count INTEGER,
            bbref_event_count INTEGER,
            kaggle_event_count INTEGER,

            -- Recommended source
            primary_source TEXT,
            backup_sources TEXT,  -- Comma-separated

            -- Quality
            total_sources INTEGER,
            has_discrepancies BOOLEAN DEFAULT FALSE,
            overall_quality_score NUMERIC,

            -- Metadata
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("CREATE INDEX idx_coverage_date ON source_coverage(game_date);")
    cursor.execute("CREATE INDEX idx_coverage_primary_source ON source_coverage(primary_source);")
    cursor.execute("CREATE INDEX idx_coverage_discrepancies ON source_coverage(has_discrepancies);")

    # 4. Data quality discrepancies
    print("  Creating: data_quality_discrepancies")
    cursor.execute("""
        CREATE TABLE data_quality_discrepancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            field_name TEXT NOT NULL,  -- event_count, home_score, coordinate_x, etc.

            -- Values from each source (NULL if source doesn't have game)
            espn_value TEXT,
            hoopr_value TEXT,
            nba_api_value TEXT,
            bbref_value TEXT,
            kaggle_value TEXT,

            -- Analysis
            difference NUMERIC,
            pct_difference NUMERIC,
            severity TEXT CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),

            -- Resolution
            recommended_source TEXT,
            recommended_value TEXT,
            ml_impact_notes TEXT,

            -- Metadata
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolution_status TEXT DEFAULT 'UNRESOLVED'
        );
    """)

    cursor.execute("CREATE INDEX idx_discrepancy_game_id ON data_quality_discrepancies(game_id);")
    cursor.execute("CREATE INDEX idx_discrepancy_severity ON data_quality_discrepancies(severity);")
    cursor.execute("CREATE INDEX idx_discrepancy_status ON data_quality_discrepancies(resolution_status);")

    # 5. Quality scores (ML-ready)
    print("  Creating: quality_scores")
    cursor.execute("""
        CREATE TABLE quality_scores (
            game_id TEXT PRIMARY KEY,
            game_date DATE NOT NULL,

            -- Recommended source for ML
            recommended_source TEXT,
            quality_score NUMERIC,  -- 0-100
            uncertainty TEXT CHECK (uncertainty IN ('LOW', 'MEDIUM', 'HIGH')),

            -- Discrepancy summary
            has_event_count_issue BOOLEAN DEFAULT FALSE,
            has_coordinate_issue BOOLEAN DEFAULT FALSE,
            has_score_issue BOOLEAN DEFAULT FALSE,
            has_timing_issue BOOLEAN DEFAULT FALSE,

            -- ML guidance
            use_for_training BOOLEAN DEFAULT TRUE,
            ml_notes TEXT,

            -- Metadata
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("CREATE INDEX idx_quality_scores_date ON quality_scores(game_date);")
    cursor.execute("CREATE INDEX idx_quality_scores_source ON quality_scores(recommended_source);")
    cursor.execute("CREATE INDEX idx_quality_scores_training ON quality_scores(use_for_training);")

    print()
    print("✓ All tables created successfully")
    print()

    # Print summary
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()

    print(f"Created {len(tables)} tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM pragma_table_info('{table[0]}');")
        col_count = cursor.fetchone()[0]
        print(f"  ✓ {table[0]} ({col_count} columns)")

    print()
    conn.commit()
    cursor.close()
    conn.close()

    print("=" * 70)
    print(f"✓ Local unified database created: {UNIFIED_LOCAL_DB}")
    print("=" * 70)


def create_rds_unified_database():
    """Create RDS PostgreSQL unified database."""

    print("=" * 70)
    print("CREATE RDS UNIFIED DATABASE")
    print("=" * 70)
    print()

    # Validate credentials
    if not RDS_CONFIG['user'] or not RDS_CONFIG['password']:
        print("ERROR: RDS credentials not found")
        sys.exit(1)

    # Connect to RDS
    print(f"Connecting to: {RDS_CONFIG['database']} at {RDS_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**RDS_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        sys.exit(1)

    # Create tables
    print("Creating tables...")
    print()

    # 1. Unified play-by-play
    print("  Creating: unified_play_by_play")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unified_play_by_play (
            id SERIAL PRIMARY KEY,
            game_id TEXT NOT NULL,
            source TEXT NOT NULL CHECK (source IN ('ESPN', 'hoopR', 'NBA_API', 'BBRef', 'Kaggle')),

            -- Common fields
            game_date DATE NOT NULL,
            period_number INTEGER,
            clock_display TEXT,
            clock_seconds DOUBLE PRECISION,
            event_description TEXT,
            home_score INTEGER,
            away_score INTEGER,
            scoring_play BOOLEAN,
            score_value INTEGER,

            -- Team/Player
            team_id TEXT,
            player_id TEXT,

            -- Coordinates
            coordinate_x DOUBLE PRECISION,
            coordinate_y DOUBLE PRECISION,

            -- Type
            event_type TEXT,

            -- Source-specific fields
            raw_json JSONB,

            -- Metadata
            quality_score NUMERIC,
            is_primary BOOLEAN DEFAULT FALSE,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_unified_pbp_game_id ON unified_play_by_play(game_id);
        CREATE INDEX IF NOT EXISTS idx_unified_pbp_source ON unified_play_by_play(source);
        CREATE INDEX IF NOT EXISTS idx_unified_pbp_date ON unified_play_by_play(game_date);
        CREATE INDEX IF NOT EXISTS idx_unified_pbp_primary ON unified_play_by_play(is_primary);
    """)

    # 2. Unified schedule
    print("  Creating: unified_schedule_v2")  # v2 to avoid conflict with views
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unified_schedule_v2 (
            id SERIAL PRIMARY KEY,
            game_id TEXT NOT NULL,
            source TEXT NOT NULL CHECK (source IN ('ESPN', 'hoopR', 'NBA_API', 'BBRef', 'Kaggle')),

            -- Game info
            game_date DATE NOT NULL,
            season INTEGER,
            game_type TEXT,

            -- Teams
            home_team_id TEXT,
            home_team_name TEXT,
            away_team_id TEXT,
            away_team_name TEXT,

            -- Score
            home_score INTEGER,
            away_score INTEGER,

            -- Metadata
            has_pbp BOOLEAN DEFAULT FALSE,
            pbp_event_count INTEGER,
            quality_score NUMERIC,
            is_primary BOOLEAN DEFAULT FALSE,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_unified_schedule_v2_game_id ON unified_schedule_v2(game_id);
        CREATE INDEX IF NOT EXISTS idx_unified_schedule_v2_source ON unified_schedule_v2(source);
        CREATE INDEX IF NOT EXISTS idx_unified_schedule_v2_date ON unified_schedule_v2(game_date);
    """)

    # 3. Source coverage
    print("  Creating: source_coverage")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_coverage (
            game_id TEXT PRIMARY KEY,
            game_date DATE NOT NULL,

            -- Which sources have this game?
            has_espn BOOLEAN DEFAULT FALSE,
            has_hoopr BOOLEAN DEFAULT FALSE,
            has_nba_api BOOLEAN DEFAULT FALSE,
            has_bbref BOOLEAN DEFAULT FALSE,
            has_kaggle BOOLEAN DEFAULT FALSE,

            -- Event counts
            espn_event_count INTEGER,
            hoopr_event_count INTEGER,
            nba_api_event_count INTEGER,
            bbref_event_count INTEGER,
            kaggle_event_count INTEGER,

            -- Recommended
            primary_source TEXT,
            backup_sources TEXT,

            -- Quality
            total_sources INTEGER,
            has_discrepancies BOOLEAN DEFAULT FALSE,
            overall_quality_score NUMERIC,

            -- Metadata
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_coverage_date ON source_coverage(game_date);
        CREATE INDEX IF NOT EXISTS idx_coverage_primary_source ON source_coverage(primary_source);
        CREATE INDEX IF NOT EXISTS idx_coverage_discrepancies ON source_coverage(has_discrepancies);
    """)

    # 4. Discrepancies
    print("  Creating: data_quality_discrepancies")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_discrepancies (
            id SERIAL PRIMARY KEY,
            game_id TEXT NOT NULL,
            field_name TEXT NOT NULL,

            -- Values from each source
            espn_value TEXT,
            hoopr_value TEXT,
            nba_api_value TEXT,
            bbref_value TEXT,
            kaggle_value TEXT,

            -- Analysis
            difference NUMERIC,
            pct_difference NUMERIC,
            severity TEXT CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),

            -- Resolution
            recommended_source TEXT,
            recommended_value TEXT,
            ml_impact_notes TEXT,

            -- Metadata
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolution_status TEXT DEFAULT 'UNRESOLVED'
        );

        CREATE INDEX IF NOT EXISTS idx_discrepancy_game_id ON data_quality_discrepancies(game_id);
        CREATE INDEX IF NOT EXISTS idx_discrepancy_severity ON data_quality_discrepancies(severity);
        CREATE INDEX IF NOT EXISTS idx_discrepancy_status ON data_quality_discrepancies(resolution_status);
    """)

    # 5. Quality scores
    print("  Creating: quality_scores")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_scores (
            game_id TEXT PRIMARY KEY,
            game_date DATE NOT NULL,

            -- Recommended
            recommended_source TEXT,
            quality_score NUMERIC,
            uncertainty TEXT CHECK (uncertainty IN ('LOW', 'MEDIUM', 'HIGH')),

            -- Discrepancy flags
            has_event_count_issue BOOLEAN DEFAULT FALSE,
            has_coordinate_issue BOOLEAN DEFAULT FALSE,
            has_score_issue BOOLEAN DEFAULT FALSE,
            has_timing_issue BOOLEAN DEFAULT FALSE,

            -- ML guidance
            use_for_training BOOLEAN DEFAULT TRUE,
            ml_notes TEXT,

            -- Metadata
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_quality_scores_date ON quality_scores(game_date);
        CREATE INDEX IF NOT EXISTS idx_quality_scores_source ON quality_scores(recommended_source);
        CREATE INDEX IF NOT EXISTS idx_quality_scores_training ON quality_scores(use_for_training);
    """)

    print()
    conn.commit()
    print("✓ All tables created successfully")
    print()

    # Print summary
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN ('unified_play_by_play', 'unified_schedule_v2', 'source_coverage',
                             'data_quality_discrepancies', 'quality_scores')
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()

    print(f"Created {len(tables)} unified tables in RDS:")
    for table in tables:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = '{table[0]}';
        """)
        col_count = cursor.fetchone()[0]
        print(f"  ✓ {table[0]} ({col_count} columns)")

    print()
    cursor.close()
    conn.close()

    print("=" * 70)
    print(f"✓ RDS unified database tables created")
    print("=" * 70)


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Create unified multi-source NBA database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create local SQLite database
  python scripts/db/create_unified_database.py --create-local

  # Create RDS PostgreSQL database
  python scripts/db/create_unified_database.py --create-rds

  # Create both
  python scripts/db/create_unified_database.py --create-both

Purpose:
  Creates comprehensive database combining ESPN, hoopR, NBA API, Basketball Ref,
  and Kaggle data with discrepancy tracking for ML data quality.

  CRITICAL: Source databases remain pure (no cross-contamination).
  This unified database is SEPARATE and combines all sources.
        """
    )

    parser.add_argument(
        '--create-local',
        action='store_true',
        help='Create local SQLite unified database'
    )

    parser.add_argument(
        '--create-rds',
        action='store_true',
        help='Create RDS PostgreSQL unified database'
    )

    parser.add_argument(
        '--create-both',
        action='store_true',
        help='Create both local and RDS databases'
    )

    args = parser.parse_args()

    # Default to local if no args
    if not args.create_local and not args.create_rds and not args.create_both:
        args.create_local = True

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if args.create_local or args.create_both:
        create_local_unified_database()
        print()

    if args.create_rds or args.create_both:
        create_rds_unified_database()
        print()

    print(f"✓ Database creation complete!")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
