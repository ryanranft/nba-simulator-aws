#!/usr/bin/env python3
"""
Verify hoopR Data Coverage

Checks for gaps in hoopR data collection and reports:
1. Overall coverage (earliest to latest game)
2. Games by season
3. Potential gaps in coverage
4. Comparison with expected NBA schedule

Usage:
    python scripts/validation/verify_hoopr_coverage.py
    python scripts/validation/verify_hoopr_coverage.py --detailed
    python scripts/validation/verify_hoopr_coverage.py --season 2025
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ Error: psycopg2 not installed")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Get database connection with proper credentials."""
    import os

    # Try environment variables first
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'nba_simulator'),
        'user': os.getenv('POSTGRES_USER', 'ryanranft'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'port': int(os.getenv('POSTGRES_PORT', 5432))
    }

    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTry setting environment variables:")
        print("  export POSTGRES_HOST=localhost")
        print("  export POSTGRES_DB=nba_simulator")
        print("  export POSTGRES_USER=ryanranft")
        sys.exit(1)


def check_overall_coverage(conn):
    """Check overall hoopR data coverage."""
    print("\n" + "="*80)
    print("HOOPR DATA COVERAGE OVERVIEW")
    print("="*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Overall stats
        cur.execute("""
            SELECT
                MIN(game_date) as earliest_game,
                MAX(game_date) as latest_game,
                COUNT(*) as total_games,
                COUNT(DISTINCT EXTRACT(YEAR FROM game_date)) as seasons_covered
            FROM hoopr_schedule
        """)
        overall = cur.fetchone()

        if overall['total_games'] == 0:
            print("❌ No data found in hoopr_schedule table!")
            return None

        print(f"\n📊 Overall Coverage:")
        print(f"   Earliest Game: {overall['earliest_game']}")
        print(f"   Latest Game:   {overall['latest_game']}")
        print(f"   Total Games:   {overall['total_games']:,}")
        print(f"   Seasons:       {overall['seasons_covered']}")

        # Calculate coverage span
        earliest = overall['earliest_game']
        latest = overall['latest_game']
        days_span = (latest - earliest).days
        years_span = days_span / 365.25

        print(f"   Time Span:     {days_span:,} days ({years_span:.1f} years)")

        return overall


def check_season_coverage(conn, specific_season=None):
    """Check coverage by NBA season."""
    print("\n" + "="*80)
    print("COVERAGE BY NBA SEASON")
    print("="*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # NBA seasons run Oct-June, so season year is the year the season starts
        query = """
            WITH season_games AS (
                SELECT
                    CASE
                        WHEN EXTRACT(MONTH FROM game_date) >= 10
                        THEN EXTRACT(YEAR FROM game_date)
                        ELSE EXTRACT(YEAR FROM game_date) - 1
                    END as season_year,
                    game_date
                FROM hoopr_schedule
            )
            SELECT
                season_year,
                COUNT(*) as game_count,
                MIN(game_date) as first_game,
                MAX(game_date) as last_game,
                MAX(game_date) - MIN(game_date) as season_span
            FROM season_games
            {where_clause}
            GROUP BY season_year
            ORDER BY season_year DESC
        """

        where_clause = f"WHERE season_year = {specific_season}" if specific_season else ""
        cur.execute(query.format(where_clause=where_clause))
        seasons = cur.fetchall()

        print(f"\n{'Season':<10} {'Games':<10} {'First Game':<15} {'Last Game':<15} {'Span (days)':<12} {'Status'}")
        print("-" * 85)

        for season in seasons:
            season_str = f"{int(season['season_year'])}-{int(season['season_year'])+1}"

            # Determine status based on game count and recency
            if season['game_count'] >= 1200:
                status = "✅ Complete"
            elif season['season_year'] >= 2025:
                status = "🔄 Current"
            elif season['game_count'] >= 900:
                status = "⚠️  Partial"
            else:
                status = "❌ Incomplete"

            print(f"{season_str:<10} {season['game_count']:<10,} "
                  f"{season['first_game']!s:<15} {season['last_game']!s:<15} "
                  f"{season['season_span'].days:<12} {status}")

        return seasons


def find_gaps(conn, min_gap_days=7):
    """Find gaps in data collection (periods with no games)."""
    print("\n" + "="*80)
    print(f"POTENTIAL DATA GAPS (>{min_gap_days} days with no games)")
    print("="*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find gaps between consecutive games
        cur.execute("""
            WITH ordered_games AS (
                SELECT
                    game_date,
                    LAG(game_date) OVER (ORDER BY game_date) as prev_game_date
                FROM hoopr_schedule
            ),
            gaps AS (
                SELECT
                    prev_game_date as gap_start,
                    game_date as gap_end,
                    game_date - prev_game_date as gap_days
                FROM ordered_games
                WHERE prev_game_date IS NOT NULL
                  AND game_date - prev_game_date > %s
            )
            SELECT * FROM gaps
            ORDER BY gap_days DESC
            LIMIT 20
        """, (timedelta(days=min_gap_days),))

        gaps = cur.fetchall()

        if not gaps:
            print(f"\n✅ No significant gaps found (all gaps < {min_gap_days} days)")
            return []

        print(f"\n{'Gap Start':<15} {'Gap End':<15} {'Days':<10} {'Likely Reason'}")
        print("-" * 65)

        for gap in gaps:
            days = gap['gap_days'].days

            # Determine likely reason for gap
            month_start = gap['gap_start'].month
            month_end = gap['gap_end'].month

            if month_start >= 7 and month_end >= 9:
                reason = "Offseason (expected)"
            elif days > 180:
                reason = "⚠️  DATA MISSING"
            elif 30 < days <= 60:
                reason = "All-Star Break (expected)"
            elif days > 60:
                reason = "⚠️  CHECK DATA"
            else:
                reason = "Possible data gap"

            print(f"{gap['gap_start']!s:<15} {gap['gap_end']!s:<15} "
                  f"{days:<10} {reason}")

        return gaps


def check_current_season(conn):
    """Check if we have current season (2025-26) data."""
    print("\n" + "="*80)
    print("CURRENT SEASON (2025-26) STATUS")
    print("="*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check for games since Oct 1, 2025 (start of 2025-26 season)
        cur.execute("""
            SELECT
                COUNT(*) as game_count,
                MIN(game_date) as first_game,
                MAX(game_date) as last_game
            FROM hoopr_schedule
            WHERE game_date >= '2025-10-01'
        """)

        current = cur.fetchone()

        if current['game_count'] == 0:
            print("\n❌ NO DATA for 2025-26 season (started ~Oct 22, 2025)")
            print("\n   Action needed:")
            print("   1. Start autonomous collection system")
            print("   2. Or run: Rscript scripts/etl/scrape_hoopr_all_152_endpoints.R --season 2025")
            return False
        else:
            print(f"\n✅ Current Season Data Found:")
            print(f"   Games:      {current['game_count']}")
            print(f"   First Game: {current['first_game']}")
            print(f"   Last Game:  {current['last_game']}")

            # Check how current the data is
            days_old = (datetime.now().date() - current['last_game']).days

            if days_old == 0:
                print(f"   Status:     ✅ Up to date (today)")
            elif days_old <= 1:
                print(f"   Status:     ✅ Current (yesterday)")
            elif days_old <= 3:
                print(f"   Status:     ⚠️  {days_old} days old")
            else:
                print(f"   Status:     ❌ {days_old} days old - needs update")

            return True


def check_recent_collection(conn):
    """Check if data collection is happening regularly."""
    print("\n" + "="*80)
    print("RECENT COLLECTION ACTIVITY")
    print("="*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check last 30 days of data
        cur.execute("""
            SELECT
                game_date::date as date,
                COUNT(*) as games
            FROM hoopr_schedule
            WHERE game_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY game_date::date
            ORDER BY game_date DESC
            LIMIT 15
        """)

        recent = cur.fetchall()

        if not recent:
            print("\n❌ No games in last 30 days")
            return False

        print(f"\n📅 Last 15 Days:")
        print(f"{'Date':<15} {'Games':<10}")
        print("-" * 25)

        for row in recent:
            print(f"{row['date']!s:<15} {row['games']:<10}")

        return True


def generate_recommendations(overall, seasons, gaps):
    """Generate recommendations based on findings."""
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    recommendations = []

    # Check for large gaps
    large_gaps = [g for g in gaps if g['gap_days'].days > 60 and
                  not (g['gap_start'].month >= 7 and g['gap_end'].month >= 9)]

    if large_gaps:
        print("\n⚠️  LARGE DATA GAPS DETECTED:")
        for gap in large_gaps[:3]:
            print(f"   {gap['gap_start']} to {gap['gap_end']} ({gap['gap_days'].days} days)")
        recommendations.append("Run backfill script for missing periods")

    # Check if latest data is old
    if overall:
        days_since_latest = (datetime.now().date() - overall['latest_game']).days
        if days_since_latest > 3:
            print(f"\n⚠️  STALE DATA: Latest game is {days_since_latest} days old")
            recommendations.append("Start autonomous collection system")
            recommendations.append("Or run manual collection for recent games")

    # Check for incomplete recent seasons
    recent_incomplete = [s for s in seasons
                        if s['season_year'] >= 2023 and s['game_count'] < 900]
    if recent_incomplete:
        print(f"\n⚠️  INCOMPLETE RECENT SEASONS:")
        for season in recent_incomplete:
            print(f"   {season['season_year']}-{season['season_year']+1}: "
                  f"{season['game_count']} games (expected ~1230)")
        recommendations.append("Backfill recent incomplete seasons")

    if recommendations:
        print("\n📋 Actions to Take:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n✅ Data coverage looks good! No major issues detected.")

    return recommendations


def main():
    parser = argparse.ArgumentParser(description='Verify hoopR data coverage')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed gap analysis')
    parser.add_argument('--season', type=int,
                       help='Check specific season (e.g., 2025 for 2025-26)')
    parser.add_argument('--min-gap-days', type=int, default=7,
                       help='Minimum gap size to report (default: 7 days)')

    args = parser.parse_args()

    print("\n🏀 hoopR Data Coverage Verification")
    print(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    conn = get_db_connection()

    try:
        # Run checks
        overall = check_overall_coverage(conn)
        if not overall:
            sys.exit(1)

        seasons = check_season_coverage(conn, args.season)

        if args.detailed:
            gaps = find_gaps(conn, args.min_gap_days)
        else:
            gaps = find_gaps(conn, 60)  # Only show major gaps by default

        check_current_season(conn)
        check_recent_collection(conn)

        # Generate recommendations
        recommendations = generate_recommendations(overall, seasons, gaps)

        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
