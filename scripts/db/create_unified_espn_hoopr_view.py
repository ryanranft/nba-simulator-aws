#!/usr/bin/env python3
"""
Create Unified ESPN + hoopR View

Creates a unified view combining the best of both data sources:
- ESPN: Historical data (1993-2001) - 11,210 games
- hoopR: Modern data (2002-2025) - 30,758 games with 100% coverage

Strategy:
1. Use ESPN for pre-2002 historical data (exclusive coverage)
2. Use hoopR for 2002+ (better coverage, richer schema)
3. Map common columns for seamless querying

Total unified coverage: 1993-2025 (33 years)

Usage:
    python scripts/db/create_unified_espn_hoopr_view.py
    python scripts/db/create_unified_espn_hoopr_view.py --drop-existing

Version: 1.0
Created: October 9, 2025
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import argparse

# Load environment variables
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}


def create_unified_play_by_play_view(cursor, drop_existing=False):
    """Create unified play-by-play view combining ESPN + hoopR."""
    print("=" * 70)
    print("CREATING UNIFIED PLAY-BY-PLAY VIEW")
    print("=" * 70)
    print()

    view_name = "unified_play_by_play"

    # Check if view exists
    cursor.execute(
        f"""
        SELECT EXISTS (
            SELECT FROM information_schema.views
            WHERE table_name = '{view_name}'
        );
    """
    )
    exists = cursor.fetchone()[0]

    if exists:
        if drop_existing:
            print(f"Dropping existing view: {view_name}...")
            cursor.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE;")
            print("  ✓ View dropped")
        else:
            print(
                f"⚠️  View {view_name} already exists. Use --drop-existing to recreate."
            )
            return

    print(f"Creating view: {view_name}...")

    # Define common columns between ESPN and hoopR
    # ESPN columns: game_id, period_number, clock_display_value, scoring_play, etc.
    # hoopR columns: game_id, period_number, clock_display_value, scoring_play, etc.

    cursor.execute(
        f"""
        CREATE VIEW {view_name} AS

        -- ESPN data: Pre-2002 historical coverage (1993-2001)
        SELECT
            pbp.game_id,
            pbp.period_number,
            pbp.clock_display as clock_display_value,
            pbp.home_score,
            pbp.away_score,
            NULL::TEXT as type_text,  -- ESPN doesn't have type_text
            pbp.play_text as description,
            pbp.scoring_play,
            'ESPN' as data_source,
            g.game_date
        FROM play_by_play pbp
        JOIN games g ON pbp.game_id = g.game_id
        WHERE g.game_date < '2002-01-01'

        UNION ALL

        -- hoopR data: 2002-2025 modern coverage (better completeness)
        SELECT
            game_id::TEXT,  -- Cast to TEXT to match ESPN VARCHAR
            period_number,
            clock_display_value,
            home_score,
            away_score,
            type_text,
            text as description,
            CASE WHEN scoring_play = 1 THEN true ELSE false END as scoring_play,
            'hoopR' as data_source,
            game_date::DATE
        FROM hoopr_play_by_play
        WHERE game_date >= '2002-01-01'

        ORDER BY game_date, game_id, period_number DESC, clock_display_value DESC;
    """
    )

    print(f"  ✓ Created view: {view_name}")
    print()

    # Print statistics
    cursor.execute(f"SELECT COUNT(*) FROM {view_name};")
    total = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {view_name} WHERE data_source = 'ESPN';")
    espn_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {view_name} WHERE data_source = 'hoopR';")
    hoopr_count = cursor.fetchone()[0]

    print(f"View Statistics:")
    print(f"  Total events:    {total:,}")
    print(f"  ESPN (pre-2002): {espn_count:,} ({espn_count/total*100:.1f}%)")
    print(f"  hoopR (2002+):   {hoopr_count:,} ({hoopr_count/total*100:.1f}%)")
    print()


def create_unified_schedule_view(cursor, drop_existing=False):
    """Create unified schedule view combining ESPN + hoopR."""
    print("=" * 70)
    print("CREATING UNIFIED SCHEDULE VIEW")
    print("=" * 70)
    print()

    view_name = "unified_schedule"

    # Check if view exists
    cursor.execute(
        f"""
        SELECT EXISTS (
            SELECT FROM information_schema.views
            WHERE table_name = '{view_name}'
        );
    """
    )
    exists = cursor.fetchone()[0]

    if exists:
        if drop_existing:
            print(f"Dropping existing view: {view_name}...")
            cursor.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE;")
            print("  ✓ View dropped")
        else:
            print(
                f"⚠️  View {view_name} already exists. Use --drop-existing to recreate."
            )
            return

    print(f"Creating view: {view_name}...")

    cursor.execute(
        f"""
        CREATE VIEW {view_name} AS

        -- ESPN schedule: Pre-2002 games
        SELECT
            game_id,
            game_date,
            CAST(home_team_id AS INTEGER) as home_team_id,
            home_team_name,
            CAST(away_team_id AS INTEGER) as away_team_id,
            away_team_name,
            home_team_score,
            away_team_score,
            'ESPN' as data_source
        FROM games
        WHERE game_date < '2002-01-01'

        UNION ALL

        -- hoopR schedule: 2002+ games (more complete)
        SELECT
            game_id::TEXT,  -- Cast to TEXT to match ESPN VARCHAR
            game_date,
            home_team_id,
            home_team_name,
            away_team_id,
            away_team_name,
            home_team_score,
            away_team_score,
            'hoopR' as data_source
        FROM hoopr_schedule
        WHERE game_date >= '2002-01-01'

        ORDER BY game_date, game_id;
    """
    )

    print(f"  ✓ Created view: {view_name}")
    print()

    # Print statistics
    cursor.execute(f"SELECT COUNT(*) FROM {view_name};")
    total = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {view_name} WHERE data_source = 'ESPN';")
    espn_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {view_name} WHERE data_source = 'hoopR';")
    hoopr_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT MIN(game_date), MAX(game_date) FROM {view_name};")
    min_date, max_date = cursor.fetchone()

    print(f"View Statistics:")
    print(f"  Total games:     {total:,}")
    print(f"  ESPN (pre-2002): {espn_count:,} ({espn_count/total*100:.1f}%)")
    print(f"  hoopR (2002+):   {hoopr_count:,} ({hoopr_count/total*100:.1f}%)")
    print(f"  Date range:      {min_date} to {max_date}")
    print(
        f"  Coverage:        {(max_date.year - min_date.year) if min_date and max_date else 0} years"
    )
    print()


def create_documentation_view(cursor):
    """Create a view documenting the unified data strategy."""
    print("=" * 70)
    print("CREATING DATA SOURCE DOCUMENTATION VIEW")
    print("=" * 70)
    print()

    view_name = "data_source_coverage"

    cursor.execute(
        f"""
        CREATE OR REPLACE VIEW {view_name} AS
        SELECT
            EXTRACT(YEAR FROM game_date) as season_year,
            data_source,
            COUNT(*) as game_count,
            COUNT(DISTINCT game_id) as unique_games
        FROM unified_schedule
        WHERE game_date IS NOT NULL
        GROUP BY season_year, data_source
        ORDER BY season_year, data_source;
    """
    )

    print(f"  ✓ Created view: {view_name}")
    print()

    # Show sample
    print("Coverage by Year and Source:")
    cursor.execute(
        f"""
        SELECT season_year, data_source, game_count
        FROM {view_name}
        ORDER BY season_year
        LIMIT 10;
    """
    )

    print(f"  {'Year':<8} {'Source':<10} {'Games':<10}")
    print("  " + "-" * 30)
    for row in cursor.fetchall():
        print(f"  {int(row[0]):<8} {row[1]:<10} {row[2]:<10,}")
    print(f"  ... (showing first 10 years)")
    print()


def print_summary(cursor):
    """Print summary of unified views."""
    print("=" * 70)
    print("UNIFIED VIEW SUMMARY")
    print("=" * 70)
    print()

    # List all unified views
    cursor.execute(
        """
        SELECT table_name, view_definition
        FROM information_schema.views
        WHERE table_name LIKE 'unified_%' OR table_name LIKE 'data_source_%'
        ORDER BY table_name;
    """
    )

    views = cursor.fetchall()
    print(f"Created {len(views)} unified views:")
    for view_name, _ in views:
        print(f"  ✓ {view_name}")

    print()
    print("=" * 70)
    print("USAGE EXAMPLES")
    print("=" * 70)
    print(
        """
-- Query all play-by-play events (1993-2025)
SELECT * FROM unified_play_by_play
WHERE game_date >= '2010-01-01'
LIMIT 100;

-- Query all games (1993-2025)
SELECT * FROM unified_schedule
WHERE game_date BETWEEN '2020-01-01' AND '2020-12-31';

-- Check coverage by year
SELECT * FROM data_source_coverage
ORDER BY season_year DESC;

-- Compare ESPN vs hoopR for specific year
SELECT
    season_year,
    SUM(CASE WHEN data_source = 'ESPN' THEN game_count ELSE 0 END) as espn_games,
    SUM(CASE WHEN data_source = 'hoopR' THEN game_count ELSE 0 END) as hoopr_games
FROM data_source_coverage
GROUP BY season_year
ORDER BY season_year;
    """
    )
    print("=" * 70)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Create unified ESPN + hoopR views in RDS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create views
  python scripts/db/create_unified_espn_hoopr_view.py

  # Recreate existing views
  python scripts/db/create_unified_espn_hoopr_view.py --drop-existing

Strategy:
  ESPN:  1993-2001 historical data (exclusive coverage)
  hoopR: 2002-2025 modern data (better coverage, richer schema)

  Result: Seamless 33-year dataset (1993-2025)
        """,
    )

    parser.add_argument(
        "--drop-existing", action="store_true", help="Drop and recreate existing views"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("CREATE UNIFIED ESPN + HOOPR VIEWS")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Validate credentials
    if not DB_CONFIG["user"] or not DB_CONFIG["password"]:
        print("ERROR: Database credentials not found")
        sys.exit(1)

    # Connect to database
    print(f"Connecting to: {DB_CONFIG['database']} at {DB_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        sys.exit(1)

    try:
        # Create unified views
        create_unified_play_by_play_view(cursor, args.drop_existing)
        create_unified_schedule_view(cursor, args.drop_existing)
        create_documentation_view(cursor)

        # Commit
        conn.commit()
        print("✓ All views committed to database")
        print()

        # Print summary
        print_summary(cursor)

        print(f"\n✓ Unified views created successfully!")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        print("Transaction rolled back")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")


if __name__ == "__main__":
    main()
