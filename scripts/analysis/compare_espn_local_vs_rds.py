"""
Compare ESPN Local SQLite Database vs RDS PostgreSQL

Compares the local ESPN SQLite database with the RDS PostgreSQL database
to identify gaps, discrepancies, and data quality issues.

Usage:
    python scripts/analysis/compare_espn_local_vs_rds.py
    python scripts/analysis/compare_espn_local_vs_rds.py --output reports/espn_comparison.md

Requires:
    - Local SQLite database at /tmp/espn_local.db
    - RDS credentials in ~/nba-sim-credentials.env
    - psycopg2 package for PostgreSQL connection

Duration: 1-2 hours
"""

import sqlite3
import psycopg2
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

# Database configurations
SQLITE_DB = Path("/tmp/espn_local.db")

RDS_CONFIG = {
    'host': os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'nba_simulator'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', 5432),
    'sslmode': 'require'
}


def connect_local():
    """Connect to local SQLite database"""
    if not SQLITE_DB.exists():
        raise FileNotFoundError(f"Local database not found: {SQLITE_DB}")
    return sqlite3.connect(str(SQLITE_DB))


def connect_rds():
    """Connect to RDS PostgreSQL database"""
    return psycopg2.connect(**RDS_CONFIG)


def get_local_summary(conn_local):
    """Get summary statistics from local SQLite database"""
    cursor = conn_local.cursor()

    summary = {}

    # Total games
    cursor.execute("SELECT COUNT(*) FROM games")
    summary['total_games'] = cursor.fetchone()[0]

    # Games with PBP
    cursor.execute("SELECT COUNT(*) FROM games WHERE has_pbp = 1")
    summary['games_with_pbp'] = cursor.fetchone()[0]

    # Total events
    cursor.execute("SELECT COUNT(*) FROM pbp_events")
    summary['total_events'] = cursor.fetchone()[0]

    # Date range
    cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games WHERE game_date IS NOT NULL")
    summary['date_range'] = cursor.fetchone()

    # Games by year
    cursor.execute("""
        SELECT season, COUNT(*) as games, SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) as with_pbp
        FROM games
        WHERE season IS NOT NULL
        GROUP BY season
        ORDER BY season
    """)
    summary['games_by_year'] = cursor.fetchall()

    return summary


def get_rds_summary(conn_rds):
    """Get summary statistics from RDS PostgreSQL database"""
    cursor = conn_rds.cursor()

    summary = {}

    # Check if tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('games', 'temporal_events')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    summary['tables_exist'] = tables

    if 'games' in tables:
        # Total games
        cursor.execute("SELECT COUNT(*) FROM games")
        summary['total_games'] = cursor.fetchone()[0]

        # Date range
        cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games WHERE game_date IS NOT NULL")
        summary['date_range'] = cursor.fetchone()

        # Games by season (handling different column types)
        cursor.execute("""
            SELECT
                EXTRACT(YEAR FROM game_date::date) as year,
                COUNT(*) as games
            FROM games
            WHERE game_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM game_date::date)
            ORDER BY year
        """)
        summary['games_by_year'] = cursor.fetchall()
    else:
        summary['total_games'] = 0
        summary['date_range'] = (None, None)
        summary['games_by_year'] = []

    if 'temporal_events' in tables:
        # Check for ESPN events
        cursor.execute("SELECT COUNT(*) FROM temporal_events WHERE data_source = 'espn'")
        summary['espn_events'] = cursor.fetchone()[0]

        # Total events
        cursor.execute("SELECT COUNT(*) FROM temporal_events")
        summary['total_events'] = cursor.fetchone()[0]
    else:
        summary['espn_events'] = 0
        summary['total_events'] = 0

    return summary


def find_missing_games(conn_local, conn_rds):
    """Find games in local database but not in RDS"""
    cursor_local = conn_local.cursor()
    cursor_rds = conn_rds.cursor()

    # Get all game IDs from local
    cursor_local.execute("SELECT game_id FROM games")
    local_game_ids = set(row[0] for row in cursor_local.fetchall())

    # Get all game IDs from RDS (if table exists)
    cursor_rds.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'games'
    """)

    if cursor_rds.fetchone():
        cursor_rds.execute("SELECT game_id FROM games")
        rds_game_ids = set(str(row[0]) for row in cursor_rds.fetchall())
    else:
        rds_game_ids = set()

    # Find missing games
    missing_in_rds = local_game_ids - rds_game_ids
    extra_in_rds = rds_game_ids - local_game_ids

    return {
        'missing_in_rds': sorted(missing_in_rds),
        'extra_in_rds': sorted(extra_in_rds),
        'total_local': len(local_game_ids),
        'total_rds': len(rds_game_ids)
    }


def analyze_data_quality(conn_local):
    """Analyze data quality in local database"""
    cursor = conn_local.cursor()

    quality = {}

    # Games with missing fields
    cursor.execute("""
        SELECT
            SUM(CASE WHEN game_date IS NULL THEN 1 ELSE 0 END) as missing_date,
            SUM(CASE WHEN home_team IS NULL THEN 1 ELSE 0 END) as missing_home,
            SUM(CASE WHEN away_team IS NULL THEN 1 ELSE 0 END) as missing_away,
            SUM(CASE WHEN home_score = 0 AND away_score = 0 THEN 1 ELSE 0 END) as zero_scores
        FROM games
    """)
    row = cursor.fetchone()
    quality['missing_fields'] = {
        'missing_date': row[0],
        'missing_home_team': row[1],
        'missing_away_team': row[2],
        'zero_scores': row[3]
    }

    # PBP coverage by year
    cursor.execute("""
        SELECT
            season,
            COUNT(*) as total_games,
            SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) as with_pbp,
            ROUND(100.0 * SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as coverage_pct,
            ROUND(AVG(pbp_event_count), 0) as avg_events
        FROM games
        WHERE season IS NOT NULL
        GROUP BY season
        ORDER BY season
    """)
    quality['pbp_coverage'] = cursor.fetchall()

    return quality


def generate_report(local_summary, rds_summary, missing_games, quality, output_path):
    """Generate comparison report in Markdown format"""
    lines = []

    lines.append("# ESPN Local Database vs RDS Comparison Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Local Database:** {local_summary['total_games']:,} games, {local_summary['total_events']:,} events")
    lines.append(f"- **RDS Database:** {rds_summary['total_games']:,} games, {rds_summary.get('espn_events', 0):,} ESPN events")
    lines.append(f"- **Missing in RDS:** {len(missing_games['missing_in_rds']):,} games")
    lines.append(f"- **Extra in RDS:** {len(missing_games['extra_in_rds']):,} games")
    lines.append("")

    # Local Database Summary
    lines.append("## Local SQLite Database Summary")
    lines.append("")
    lines.append(f"**Total Games:** {local_summary['total_games']:,}")
    lines.append(f"**Games with Play-by-Play:** {local_summary['games_with_pbp']:,} ({local_summary['games_with_pbp']/local_summary['total_games']*100:.1f}%)")
    lines.append(f"**Total Play-by-Play Events:** {local_summary['total_events']:,}")
    lines.append(f"**Date Range:** {local_summary['date_range'][0]} to {local_summary['date_range'][1]}")
    lines.append("")

    # RDS Database Summary
    lines.append("## RDS PostgreSQL Database Summary")
    lines.append("")
    lines.append(f"**Tables Present:** {', '.join(rds_summary['tables_exist']) if rds_summary['tables_exist'] else 'None'}")
    lines.append(f"**Total Games:** {rds_summary['total_games']:,}")
    lines.append(f"**ESPN Events:** {rds_summary.get('espn_events', 0):,}")
    lines.append(f"**Total Events (All Sources):** {rds_summary.get('total_events', 0):,}")

    if rds_summary['date_range'][0]:
        lines.append(f"**Date Range:** {rds_summary['date_range'][0]} to {rds_summary['date_range'][1]}")
    lines.append("")

    # Missing Games Analysis
    lines.append("## Missing Games Analysis")
    lines.append("")
    lines.append(f"**Games in Local but NOT in RDS:** {len(missing_games['missing_in_rds']):,}")
    lines.append(f"**Games in RDS but NOT in Local:** {len(missing_games['extra_in_rds']):,}")
    lines.append("")

    if missing_games['missing_in_rds']:
        lines.append("### Sample Missing Games (first 20):")
        lines.append("```")
        for game_id in missing_games['missing_in_rds'][:20]:
            lines.append(game_id)
        lines.append("```")
        lines.append("")

    # Data Quality Analysis
    lines.append("## Data Quality Analysis")
    lines.append("")
    lines.append("### Missing Fields")
    lines.append("")
    lines.append(f"- Missing game dates: {quality['missing_fields']['missing_date']:,}")
    lines.append(f"- Missing home team: {quality['missing_fields']['missing_home_team']:,}")
    lines.append(f"- Missing away team: {quality['missing_fields']['missing_away_team']:,}")
    lines.append(f"- Zero scores: {quality['missing_fields']['zero_scores']:,}")
    lines.append("")

    # Play-by-Play Coverage by Year
    lines.append("### Play-by-Play Coverage by Year")
    lines.append("")
    lines.append("| Year | Total Games | Games with PBP | Coverage % | Avg Events/Game |")
    lines.append("|------|-------------|----------------|------------|-----------------|")

    for season, total, with_pbp, coverage, avg_events in quality['pbp_coverage']:
        lines.append(f"| {season} | {total:,} | {with_pbp:,} | {coverage:.1f}% | {avg_events:.0f} |")

    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")

    if len(missing_games['missing_in_rds']) > 0:
        lines.append(f"1. **Load missing games to RDS:** {len(missing_games['missing_in_rds']):,} games need to be loaded")
        lines.append(f"   - Use: `python scripts/db/load_espn_events.py`")
        lines.append("")

    if rds_summary['total_games'] == 0:
        lines.append("2. **RDS database is empty:** Need to perform initial data load")
        lines.append(f"   - Extract schedule: `python scripts/etl/extract_schedule_local.py`")
        lines.append(f"   - Load events: `python scripts/db/load_espn_events.py`")
        lines.append("")

    if quality['missing_fields']['zero_scores'] > 100:
        lines.append("3. **Many games with zero scores:** Likely future or cancelled games")
        lines.append(f"   - {quality['missing_fields']['zero_scores']:,} games affected")
        lines.append(f"   - Consider filtering or marking as incomplete")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by: `scripts/analysis/compare_espn_local_vs_rds.py`*")

    # Write report
    report_text = "\n".join(lines)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text)
        print(f"\n✓ Report saved to: {output_path}")
    else:
        print(report_text)

    return report_text


def main():
    parser = argparse.ArgumentParser(description="Compare ESPN local database with RDS")
    parser.add_argument('--output', help='Output report path (default: print to stdout)')
    parser.add_argument('--no-rds', action='store_true', help='Skip RDS comparison (local analysis only)')

    args = parser.parse_args()

    print("="*80)
    print("ESPN LOCAL vs RDS COMPARISON")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Connect to local database
    print("Connecting to local SQLite database...")
    try:
        conn_local = connect_local()
        print("✓ Connected to local database")
    except Exception as e:
        print(f"ERROR: Failed to connect to local database: {e}")
        return

    # Get local summary
    print("\nAnalyzing local database...")
    local_summary = get_local_summary(conn_local)
    print(f"✓ Found {local_summary['total_games']:,} games in local database")

    # Connect to RDS (if not skipped)
    if not args.no_rds:
        print("\nConnecting to RDS PostgreSQL database...")
        try:
            conn_rds = connect_rds()
            print("✓ Connected to RDS")

            print("\nAnalyzing RDS database...")
            rds_summary = get_rds_summary(conn_rds)
            print(f"✓ Found {rds_summary['total_games']:,} games in RDS")

            print("\nFinding missing games...")
            missing_games = find_missing_games(conn_local, conn_rds)
            print(f"✓ Found {len(missing_games['missing_in_rds']):,} games missing in RDS")

        except Exception as e:
            print(f"⚠ WARNING: Failed to connect to RDS: {e}")
            print("Continuing with local-only analysis...")
            args.no_rds = True

    # If RDS skipped, create empty summaries
    if args.no_rds:
        rds_summary = {
            'tables_exist': [],
            'total_games': 0,
            'espn_events': 0,
            'total_events': 0,
            'date_range': (None, None),
            'games_by_year': []
        }
        missing_games = {
            'missing_in_rds': [],
            'extra_in_rds': [],
            'total_local': local_summary['total_games'],
            'total_rds': 0
        }

    # Analyze data quality
    print("\nAnalyzing data quality...")
    quality = analyze_data_quality(conn_local)
    print("✓ Quality analysis complete")

    # Generate report
    print("\nGenerating comparison report...")
    generate_report(local_summary, rds_summary, missing_games, quality, args.output)

    # Close connections
    conn_local.close()
    if not args.no_rds:
        conn_rds.close()

    print()
    print("="*80)
    print("COMPARISON COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
