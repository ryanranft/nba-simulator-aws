#!/usr/bin/env python3
"""
Identify Specific hoopR Data Gaps

Creates a detailed report of missing data that can be used to:
1. Generate backfill tasks
2. Prioritize data collection
3. Track collection progress

Usage:
    python scripts/validation/identify_hoopr_gaps.py
    python scripts/validation/identify_hoopr_gaps.py --output gaps_report.json
    python scripts/validation/identify_hoopr_gaps.py --start-date 2025-03-01 --end-date 2025-10-31
"""

import argparse
import json
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
    sys.exit(1)


def get_db_connection():
    """Get database connection."""
    import os

    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'nba_simulator'),
        'user': os.getenv('POSTGRES_USER', 'ryanranft'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'port': int(os.getenv('POSTGRES_PORT', 5432))
    }

    try:
        return psycopg2.connect(**db_config)
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)


def identify_date_gaps(conn, start_date=None, end_date=None):
    """Identify specific date ranges with missing data."""
    print("\n🔍 Identifying Date Gaps...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get all game dates
        where_clause = ""
        if start_date:
            where_clause += f" WHERE game_date >= '{start_date}'"
        if end_date:
            if where_clause:
                where_clause += f" AND game_date <= '{end_date}'"
            else:
                where_clause += f" WHERE game_date <= '{end_date}'"

        cur.execute(f"""
            SELECT DISTINCT game_date::date as date
            FROM hoopr_schedule
            {where_clause}
            ORDER BY date
        """)

        game_dates = [row['date'] for row in cur.fetchall()]

        if not game_dates:
            print("❌ No data found in specified date range")
            return []

        # Find gaps
        gaps = []
        for i in range(len(game_dates) - 1):
            current = game_dates[i]
            next_date = game_dates[i + 1]
            gap_days = (next_date - current).days

            # Consider gap if > 1 day (NBA games happen almost daily during season)
            if gap_days > 1:
                gaps.append({
                    'start_date': str(current),
                    'end_date': str(next_date),
                    'gap_days': gap_days,
                    'is_offseason': current.month >= 7 and next_date.month >= 9
                })

        return gaps


def categorize_gaps(gaps):
    """Categorize gaps by type and priority."""
    print("\n📊 Categorizing Gaps...")

    categories = {
        'critical': [],      # Large gaps during season (>7 days, not offseason)
        'important': [],     # Medium gaps (3-7 days, not offseason)
        'minor': [],         # Small gaps (1-3 days)
        'offseason': []      # Expected offseason gaps
    }

    for gap in gaps:
        if gap['is_offseason']:
            categories['offseason'].append(gap)
        elif gap['gap_days'] > 7:
            categories['critical'].append(gap)
        elif gap['gap_days'] >= 3:
            categories['important'].append(gap)
        else:
            categories['minor'].append(gap)

    return categories


def generate_gap_report(categories, output_file=None):
    """Generate detailed gap report."""
    print("\n" + "="*80)
    print("GAP ANALYSIS REPORT")
    print("="*80)

    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'critical_gaps': len(categories['critical']),
            'important_gaps': len(categories['important']),
            'minor_gaps': len(categories['minor']),
            'offseason_gaps': len(categories['offseason']),
            'total_gaps': sum(len(v) for v in categories.values())
        },
        'gaps': categories
    }

    print(f"\n📈 Summary:")
    print(f"   Critical Gaps (>7 days):     {report['summary']['critical_gaps']}")
    print(f"   Important Gaps (3-7 days):   {report['summary']['important_gaps']}")
    print(f"   Minor Gaps (1-3 days):       {report['summary']['minor_gaps']}")
    print(f"   Offseason Gaps (expected):   {report['summary']['offseason_gaps']}")
    print(f"   Total Gaps:                  {report['summary']['total_gaps']}")

    # Show critical gaps
    if categories['critical']:
        print(f"\n❌ CRITICAL GAPS ({len(categories['critical'])}):")
        for gap in categories['critical'][:10]:
            print(f"   {gap['start_date']} to {gap['end_date']} ({gap['gap_days']} days)")
        if len(categories['critical']) > 10:
            print(f"   ... and {len(categories['critical']) - 10} more")

    # Show important gaps
    if categories['important']:
        print(f"\n⚠️  IMPORTANT GAPS ({len(categories['important'])}):")
        for gap in categories['important'][:10]:
            print(f"   {gap['start_date']} to {gap['end_date']} ({gap['gap_days']} days)")
        if len(categories['important']) > 10:
            print(f"   ... and {len(categories['important']) - 10} more")

    # Save to file if requested
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Full report saved to: {output_path}")

    return report


def generate_backfill_script(categories):
    """Generate R script to backfill missing data."""
    critical_gaps = categories['critical']
    important_gaps = categories['important']

    if not critical_gaps and not important_gaps:
        print("\n✅ No gaps to backfill!")
        return None

    print("\n" + "="*80)
    print("BACKFILL SCRIPT")
    print("="*80)

    script_lines = [
        "#!/usr/bin/env Rscript",
        "# Auto-generated backfill script for hoopR data gaps",
        f"# Generated: {datetime.now().isoformat()}",
        "",
        "library(hoopR)",
        "",
        "# Backfill critical gaps (>7 days)",
    ]

    for i, gap in enumerate(critical_gaps, 1):
        start = datetime.strptime(gap['start_date'], '%Y-%m-%d')
        end = datetime.strptime(gap['end_date'], '%Y-%m-%d')

        # Determine season
        season = start.year if start.month >= 10 else start.year - 1

        script_lines.append(f"# Gap {i}: {gap['start_date']} to {gap['end_date']}")
        script_lines.append(f"# Season: {season}-{season+1}")
        script_lines.append("")

    script_lines.extend([
        "",
        "# Run comprehensive scraper for affected seasons",
        "# Uncomment and modify as needed:",
        "# source('scripts/etl/scrape_hoopr_all_152_endpoints.R')",
        ""
    ])

    # Identify unique seasons that need backfill
    seasons_to_backfill = set()
    for gap in critical_gaps + important_gaps:
        start = datetime.strptime(gap['start_date'], '%Y-%m-%d')
        season = start.year if start.month >= 10 else start.year - 1
        seasons_to_backfill.add(season)

    script_lines.append("# Seasons to backfill:")
    for season in sorted(seasons_to_backfill):
        script_lines.append(f"# - {season}-{season+1}")

    script_content = "\n".join(script_lines)

    # Save script
    script_path = project_root / "scripts" / "backfill_hoopr_gaps.R"
    with open(script_path, 'w') as f:
        f.write(script_content)

    print(f"\n📝 Backfill script created: {script_path}")
    print(f"\n   Seasons needing backfill: {', '.join(f'{s}-{s+1}' for s in sorted(seasons_to_backfill))}")

    return script_path


def main():
    parser = argparse.ArgumentParser(description='Identify hoopR data gaps')
    parser.add_argument('--output', '-o',
                       help='Output file for JSON report')
    parser.add_argument('--start-date',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--generate-backfill', action='store_true',
                       help='Generate backfill R script')

    args = parser.parse_args()

    print("\n🔍 hoopR Gap Identification Tool")
    print(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    conn = get_db_connection()

    try:
        # Identify gaps
        gaps = identify_date_gaps(conn, args.start_date, args.end_date)

        if not gaps:
            print("\n✅ No gaps found in date range!")
            sys.exit(0)

        # Categorize gaps
        categories = categorize_gaps(gaps)

        # Generate report
        report = generate_gap_report(categories, args.output)

        # Generate backfill script if requested
        if args.generate_backfill:
            generate_backfill_script(categories)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
