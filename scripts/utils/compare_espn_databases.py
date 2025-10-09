#!/usr/bin/env python3
"""
Compare ESPN Local Database vs RDS

This script compares the ESPN local SQLite database (/tmp/espn_local.db)
with the RDS PostgreSQL database to identify:
- Data completeness differences
- Missing games in each source
- Event count discrepancies
- Data quality issues

Usage:
    python scripts/utils/compare_espn_databases.py
    python scripts/utils/compare_espn_databases.py --detailed
    python scripts/utils/compare_espn_databases.py --export-missing

Output:
    - Summary report showing differences
    - Optional: Detailed game-by-game comparison
    - Optional: CSV export of missing games

Version: 1.0
Last Updated: October 9, 2025
"""

import argparse
import sqlite3
import psycopg2
import os
import sys
from datetime import datetime
from typing import Dict, Set, Tuple
from dotenv import load_dotenv

# Load environment variables from credentials file
load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

# Configuration
ESPN_LOCAL_DB = "/tmp/espn_local.db"
PROJECT_ROOT = "/Users/ryanranft/nba-simulator-aws"


class DatabaseComparator:
    """Compare ESPN local SQLite database with RDS PostgreSQL database."""

    def __init__(self):
        self.local_conn = None
        self.rds_conn = None

    def connect_local(self):
        """Connect to ESPN local SQLite database."""
        if not os.path.exists(ESPN_LOCAL_DB):
            raise FileNotFoundError(f"ESPN local database not found at {ESPN_LOCAL_DB}")

        self.local_conn = sqlite3.connect(ESPN_LOCAL_DB)
        print(f"✅ Connected to local database: {ESPN_LOCAL_DB}")

    def connect_rds(self):
        """Connect to RDS PostgreSQL database."""
        try:
            self.rds_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
                database=os.getenv('DB_NAME', 'nba_simulator'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432),
                sslmode='require'
            )
            print(f"✅ Connected to RDS database: {os.getenv('DB_HOST')}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to RDS: {e}")

    def get_local_statistics(self) -> Dict:
        """Get statistics from local database."""
        cursor = self.local_conn.cursor()

        # Total games
        cursor.execute("SELECT COUNT(*) FROM games")
        total_games = cursor.fetchone()[0]

        # Games with PBP
        cursor.execute("SELECT COUNT(*) FROM games WHERE has_pbp = 1")
        games_with_pbp = cursor.fetchone()[0]

        # Total events
        cursor.execute("SELECT COUNT(*) FROM pbp_events")
        total_events = cursor.fetchone()[0]

        # Get all game IDs with PBP
        cursor.execute("SELECT game_id FROM games WHERE has_pbp = 1")
        game_ids = set(row[0] for row in cursor.fetchall())

        # Date range
        cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games")
        min_date, max_date = cursor.fetchone()

        cursor.close()

        return {
            'total_games': total_games,
            'games_with_pbp': games_with_pbp,
            'total_events': total_events,
            'game_ids': game_ids,
            'date_range': (min_date, max_date)
        }

    def get_rds_statistics(self, fetch_all_ids: bool = True) -> Dict:
        """Get statistics from RDS database."""
        cursor = self.rds_conn.cursor()

        # Total events
        cursor.execute("SELECT COUNT(*) FROM temporal_events")
        total_events = cursor.fetchone()[0]

        # Unique games
        cursor.execute("SELECT COUNT(DISTINCT game_id) FROM temporal_events")
        unique_games = cursor.fetchone()[0]

        # Get game IDs (optionally limit for performance)
        if fetch_all_ids:
            print("   Fetching all game IDs from RDS (this may take a minute)...")
            cursor.execute("SELECT DISTINCT game_id FROM temporal_events")
            game_ids = set(row[0] for row in cursor.fetchall())
        else:
            # Just get a sample for quick comparison
            cursor.execute("SELECT DISTINCT game_id FROM temporal_events LIMIT 1000")
            game_ids = set(row[0] for row in cursor.fetchall())

        # Date range
        cursor.execute("""
            SELECT
                MIN(wall_clock_utc::date),
                MAX(wall_clock_utc::date)
            FROM temporal_events
        """)
        min_date, max_date = cursor.fetchone()

        cursor.close()

        return {
            'total_events': total_events,
            'unique_games': unique_games,
            'game_ids': game_ids,
            'date_range': (str(min_date), str(max_date))
        }

    def compare_databases_summary(self) -> Dict:
        """Compare databases using aggregate statistics only (fast)."""
        print("\n" + "="*70)
        print("ESPN DATABASE COMPARISON: Local SQLite vs RDS PostgreSQL")
        print("="*70)

        # Connect to both databases
        self.connect_local()
        self.connect_rds()

        # Get statistics (without fetching all game IDs)
        print("\n📊 Fetching statistics...")

        # Local stats
        local_cursor = self.local_conn.cursor()
        local_cursor.execute("SELECT COUNT(*) FROM games")
        local_total_games = local_cursor.fetchone()[0]

        local_cursor.execute("SELECT COUNT(*) FROM games WHERE has_pbp = 1")
        local_games_with_pbp = local_cursor.fetchone()[0]

        local_cursor.execute("SELECT COUNT(*) FROM pbp_events")
        local_total_events = local_cursor.fetchone()[0]

        local_cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games")
        local_date_range = local_cursor.fetchone()

        # RDS stats (optimized - no game ID fetching)
        rds_cursor = self.rds_conn.cursor()
        rds_cursor.execute("SELECT COUNT(*) FROM temporal_events")
        rds_total_events = rds_cursor.fetchone()[0]

        rds_cursor.execute("SELECT COUNT(DISTINCT game_id) FROM temporal_events")
        rds_unique_games = rds_cursor.fetchone()[0]

        rds_cursor.execute("""
            SELECT MIN(wall_clock_utc::date), MAX(wall_clock_utc::date)
            FROM temporal_events
        """)
        rds_date_range = rds_cursor.fetchone()

        # Print summary
        print("\n" + "-"*70)
        print("SUMMARY STATISTICS")
        print("-"*70)

        print("\nLocal SQLite Database:")
        print(f"  Total games: {local_total_games:,}")
        print(f"  Games with PBP: {local_games_with_pbp:,}")
        print(f"  Total PBP events: {local_total_events:,}")
        print(f"  Date range: {local_date_range[0]} to {local_date_range[1]}")

        print("\nRDS PostgreSQL Database (temporal_events):")
        print(f"  Unique games: {rds_unique_games:,}")
        print(f"  Total events: {rds_total_events:,}")
        print(f"  Date range: {rds_date_range[0]} to {rds_date_range[1]}")

        # Event count comparison
        print("\n" + "-"*70)
        print("EVENT COUNT COMPARISON")
        print("-"*70)

        if local_total_events == rds_total_events:
            print(f"\n✅ Event counts MATCH: {local_total_events:,} events")
        else:
            diff = rds_total_events - local_total_events
            pct_diff = (diff / local_total_events) * 100 if local_total_events > 0 else 0
            print(f"\n⚠️  Event count MISMATCH:")
            print(f"   Local: {local_total_events:,} events")
            print(f"   RDS:   {rds_total_events:,} events")
            print(f"   Difference: {diff:+,} events ({pct_diff:+.2f}%)")

        # Game count comparison
        print("\n" + "-"*70)
        print("GAME COUNT COMPARISON")
        print("-"*70)

        if local_games_with_pbp == rds_unique_games:
            print(f"\n✅ Game counts MATCH: {local_games_with_pbp:,} games")
        else:
            diff = rds_unique_games - local_games_with_pbp
            pct_diff = (diff / local_games_with_pbp) * 100 if local_games_with_pbp > 0 else 0
            print(f"\n⚠️  Game count MISMATCH:")
            print(f"   Local: {local_games_with_pbp:,} games with PBP")
            print(f"   RDS:   {rds_unique_games:,} unique games")
            print(f"   Difference: {diff:+,} games ({pct_diff:+.2f}%)")

        # Overall assessment
        print("\n" + "-"*70)
        print("ASSESSMENT")
        print("-"*70)

        issues = []
        if local_total_events != rds_total_events:
            issues.append("Event count mismatch")
        if local_games_with_pbp != rds_unique_games:
            issues.append("Game count mismatch")

        if not issues:
            print("\n✅ Databases are SYNCHRONIZED")
            print("   - Event counts match")
            print("   - Game counts match")
            print("   - Ready for production use")
        else:
            print("\n⚠️  Databases have DIFFERENCES:")
            for issue in issues:
                print(f"   • {issue}")
            print("\nNote: Run with --detailed flag for game-by-game comparison")

        print("\n" + "="*70)

        local_cursor.close()
        rds_cursor.close()

        return {
            'local_total_games': local_total_games,
            'local_games_with_pbp': local_games_with_pbp,
            'local_total_events': local_total_events,
            'rds_unique_games': rds_unique_games,
            'rds_total_events': rds_total_events,
            'issues': issues
        }

    def compare_databases(self) -> Dict:
        """Full comparison including game-by-game (slow, for detailed analysis)."""
        print("\n" + "="*70)
        print("ESPN DATABASE COMPARISON: Local SQLite vs RDS PostgreSQL")
        print("="*70)

        # Connect to both databases
        self.connect_local()
        self.connect_rds()

        # Get statistics
        print("\n📊 Fetching statistics...")
        local_stats = self.get_local_statistics()
        rds_stats = self.get_rds_statistics()

        # Print summary
        print("\n" + "-"*70)
        print("SUMMARY STATISTICS")
        print("-"*70)

        print("\nLocal SQLite Database:")
        print(f"  Total games: {local_stats['total_games']:,}")
        print(f"  Games with PBP: {local_stats['games_with_pbp']:,}")
        print(f"  Total PBP events: {local_stats['total_events']:,}")
        print(f"  Date range: {local_stats['date_range'][0]} to {local_stats['date_range'][1]}")

        print("\nRDS PostgreSQL Database (temporal_events):")
        print(f"  Unique games: {rds_stats['unique_games']:,}")
        print(f"  Total events: {rds_stats['total_events']:,}")
        print(f"  Date range: {rds_stats['date_range'][0]} to {rds_stats['date_range'][1]}")

        # Compare game IDs
        print("\n" + "-"*70)
        print("GAME ID COMPARISON")
        print("-"*70)

        local_ids = local_stats['game_ids']
        rds_ids = rds_stats['game_ids']

        # Find differences
        only_in_local = local_ids - rds_ids
        only_in_rds = rds_ids - local_ids
        in_both = local_ids & rds_ids

        print(f"\nGames in both databases: {len(in_both):,}")
        print(f"Games only in local DB: {len(only_in_local):,}")
        print(f"Games only in RDS: {len(only_in_rds):,}")

        if only_in_local:
            print(f"\n⚠️  {len(only_in_local):,} games in local DB but NOT in RDS")
            print(f"   Sample game IDs: {list(only_in_local)[:5]}")

        if only_in_rds:
            print(f"\n⚠️  {len(only_in_rds):,} games in RDS but NOT in local DB")
            print(f"   Sample game IDs: {list(only_in_rds)[:5]}")

        # Event count comparison
        print("\n" + "-"*70)
        print("EVENT COUNT COMPARISON")
        print("-"*70)

        if local_stats['total_events'] == rds_stats['total_events']:
            print(f"\n✅ Event counts MATCH: {local_stats['total_events']:,} events")
        else:
            diff = rds_stats['total_events'] - local_stats['total_events']
            pct_diff = (diff / local_stats['total_events']) * 100 if local_stats['total_events'] > 0 else 0
            print(f"\n⚠️  Event count MISMATCH:")
            print(f"   Local: {local_stats['total_events']:,} events")
            print(f"   RDS:   {rds_stats['total_events']:,} events")
            print(f"   Difference: {diff:+,} events ({pct_diff:+.2f}%)")

        # Overall assessment
        print("\n" + "-"*70)
        print("ASSESSMENT")
        print("-"*70)

        issues = []
        if only_in_local:
            issues.append(f"{len(only_in_local):,} games missing from RDS")
        if only_in_rds:
            issues.append(f"{len(only_in_rds):,} games missing from local DB")
        if local_stats['total_events'] != rds_stats['total_events']:
            issues.append("Event count mismatch")

        if not issues:
            print("\n✅ Databases are SYNCHRONIZED")
            print("   - All games present in both databases")
            print("   - Event counts match")
        else:
            print("\n⚠️  Databases have DIFFERENCES:")
            for issue in issues:
                print(f"   • {issue}")

        print("\n" + "="*70)

        return {
            'local_stats': local_stats,
            'rds_stats': rds_stats,
            'only_in_local': only_in_local,
            'only_in_rds': only_in_rds,
            'in_both': in_both,
            'issues': issues
        }

    def detailed_comparison(self):
        """Perform detailed game-by-game comparison."""
        print("\n📋 Performing detailed game-by-game comparison...")

        # Get game IDs from both sources
        local_cursor = self.local_conn.cursor()
        local_cursor.execute("""
            SELECT game_id, game_date, pbp_event_count
            FROM games
            WHERE has_pbp = 1
            ORDER BY game_date
        """)
        local_games = {row[0]: (row[1], row[2]) for row in local_cursor.fetchall()}

        rds_cursor = self.rds_conn.cursor()
        rds_cursor.execute("""
            SELECT game_id, COUNT(*) as event_count
            FROM temporal_events
            GROUP BY game_id
            ORDER BY game_id
        """)
        rds_games = {row[0]: row[1] for row in rds_cursor.fetchall()}

        # Compare event counts for matching games
        mismatches = []
        for game_id in local_games:
            if game_id in rds_games:
                local_count = local_games[game_id][1]
                rds_count = rds_games[game_id]
                if local_count != rds_count:
                    diff = rds_count - local_count
                    mismatches.append((game_id, local_games[game_id][0], local_count, rds_count, diff))

        if mismatches:
            print(f"\n⚠️  Found {len(mismatches):,} games with event count mismatches:")
            print(f"\nSample (first 10):")
            print(f"{'Game ID':<12} {'Date':<12} {'Local':<8} {'RDS':<8} {'Diff':<8}")
            print("-" * 60)
            for game_id, date, local_cnt, rds_cnt, diff in mismatches[:10]:
                print(f"{game_id:<12} {date:<12} {local_cnt:<8} {rds_cnt:<8} {diff:+8}")
        else:
            print(f"\n✅ All matching games have identical event counts")

        local_cursor.close()
        rds_cursor.close()

    def export_missing_games(self, output_path: str = None):
        """Export missing games to CSV file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/espn_missing_games_{timestamp}.csv"

        print(f"\n📤 Exporting missing games to: {output_path}")

        # Get missing game lists
        local_stats = self.get_local_statistics()
        rds_stats = self.get_rds_statistics()

        only_in_local = local_stats['game_ids'] - rds_stats['game_ids']
        only_in_rds = rds_stats['game_ids'] - local_stats['game_ids']

        # Get details for games only in local
        cursor = self.local_conn.cursor()
        with open(output_path, 'w') as f:
            f.write("source,game_id,game_date,event_count\n")

            # Games only in local DB
            for game_id in sorted(only_in_local):
                cursor.execute("""
                    SELECT game_date, pbp_event_count
                    FROM games
                    WHERE game_id = ?
                """, (game_id,))
                row = cursor.fetchone()
                if row:
                    f.write(f"local_only,{game_id},{row[0]},{row[1]}\n")

            # Games only in RDS
            for game_id in sorted(only_in_rds):
                f.write(f"rds_only,{game_id},unknown,unknown\n")

        cursor.close()
        print(f"✅ Exported {len(only_in_local) + len(only_in_rds):,} missing games")

    def close_connections(self):
        """Close database connections."""
        if self.local_conn:
            self.local_conn.close()
        if self.rds_conn:
            self.rds_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Compare ESPN local SQLite database with RDS PostgreSQL database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Perform detailed game-by-game comparison'
    )

    parser.add_argument(
        '--export-missing',
        action='store_true',
        help='Export missing games to CSV file'
    )

    args = parser.parse_args()

    try:
        comparator = DatabaseComparator()

        # Choose comparison mode
        if args.detailed or args.export_missing:
            # Full comparison (slower, fetches all game IDs)
            results = comparator.compare_databases()

            # Detailed game-by-game if requested
            if args.detailed:
                comparator.detailed_comparison()

            # Export if requested
            if args.export_missing:
                comparator.export_missing_games()
        else:
            # Fast summary comparison (default)
            results = comparator.compare_databases_summary()

        comparator.close_connections()

        # Exit code based on whether issues were found
        sys.exit(0 if not results['issues'] else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()