#!/usr/bin/env python3
"""
Auto-Update Utility for DATA_CATALOG.md

This script automatically updates the DATA_CATALOG.md file with current statistics
from various data sources (ESPN local DB, S3, RDS, etc.).

Usage:
    # Update ESPN statistics
    python scripts/utils/update_data_catalog.py --source espn --action update

    # Verify catalog consistency
    python scripts/utils/update_data_catalog.py --verify

    # Force full refresh of all sources
    python scripts/utils/update_data_catalog.py --refresh-all

    # Dry run (show changes without applying)
    python scripts/utils/update_data_catalog.py --source espn --dry-run

Integration:
    - Called automatically at end of scraper runs
    - Called after RDS load operations
    - Called during session startup for freshness checks
    - Can be run manually for verification

Version: 1.0
Last Updated: October 9, 2025
"""

import argparse
import sqlite3
import re
import os
import subprocess
from datetime import datetime
from typing import Dict, Tuple, Optional
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configuration
PROJECT_ROOT = "/Users/ryanranft/nba-simulator-aws"
DATA_CATALOG_PATH = os.path.join(PROJECT_ROOT, "docs", "DATA_CATALOG.md")
ESPN_LOCAL_DB = "/tmp/espn_local.db"
S3_BUCKET = "s3://nba-sim-raw-data-lake"


class DataCatalogUpdater:
    """Updates DATA_CATALOG.md with current statistics from data sources."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.catalog_content = None
        self.changes_made = []

    def load_catalog(self) -> str:
        """Load the current DATA_CATALOG.md content."""
        if not os.path.exists(DATA_CATALOG_PATH):
            raise FileNotFoundError(f"DATA_CATALOG.md not found at {DATA_CATALOG_PATH}")

        with open(DATA_CATALOG_PATH, "r") as f:
            self.catalog_content = f.read()

        return self.catalog_content

    def save_catalog(self) -> None:
        """Save the updated catalog content."""
        if self.dry_run:
            print("\n🔍 DRY RUN - Changes that would be made:")
            for change in self.changes_made:
                print(f"  • {change}")
            print("\nNot writing to file (dry run mode)")
            return

        with open(DATA_CATALOG_PATH, "w") as f:
            f.write(self.catalog_content)

        print(f"\n✅ Updated {DATA_CATALOG_PATH}")
        print(f"📝 Changes made: {len(self.changes_made)}")
        for change in self.changes_made:
            print(f"  • {change}")

    def update_field(self, pattern: str, replacement: str, description: str) -> bool:
        """Update a single field using regex pattern matching."""
        new_content = re.sub(pattern, replacement, self.catalog_content)

        if new_content != self.catalog_content:
            self.catalog_content = new_content
            self.changes_made.append(description)
            return True
        return False

    def update_last_updated(self) -> None:
        """Update the 'Last Updated' timestamp in the Quick Reference section."""
        now = datetime.now().strftime("%B %d, %Y %I:%M %p CT")
        pattern = r"(\*\*Last Full Update:\*\*\s+)[^|\n]+"
        replacement = f"\\1{now}"
        self.update_field(pattern, replacement, f"Last Full Update → {now}")

    def get_espn_statistics(self) -> Dict[str, any]:
        """Query ESPN local database for current statistics."""
        if not os.path.exists(ESPN_LOCAL_DB):
            raise FileNotFoundError(f"ESPN local database not found at {ESPN_LOCAL_DB}")

        conn = sqlite3.connect(ESPN_LOCAL_DB)
        cursor = conn.cursor()

        # Get total games
        cursor.execute("SELECT COUNT(*) FROM games")
        total_games = cursor.fetchone()[0]

        # Get games with PBP
        cursor.execute("SELECT COUNT(*) FROM games WHERE has_pbp = 1")
        games_with_pbp = cursor.fetchone()[0]

        # Get total PBP events
        cursor.execute("SELECT COUNT(*) FROM pbp_events")
        total_events = cursor.fetchone()[0]

        # Get date range
        cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games")
        min_date, max_date = cursor.fetchone()

        # Get coverage by era
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN season < 2002 THEN 'Early Digital'
                    WHEN season BETWEEN 2002 AND 2010 THEN 'Transition'
                    ELSE 'Modern'
                END as era,
                COUNT(*) as total_games,
                SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) as pbp_games,
                ROUND(100.0 * SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct,
                ROUND(AVG(CASE WHEN has_pbp = 1 THEN pbp_event_count ELSE 0 END), 0) as avg_events
            FROM games
            WHERE season IS NOT NULL
            GROUP BY era
            ORDER BY MIN(season)
        """
        )
        era_stats = cursor.fetchall()

        conn.close()

        return {
            "total_games": total_games,
            "games_with_pbp": games_with_pbp,
            "total_events": total_events,
            "min_date": min_date,
            "max_date": max_date,
            "pbp_coverage_pct": (
                round(100.0 * games_with_pbp / total_games, 1) if total_games > 0 else 0
            ),
            "era_stats": era_stats,
        }

    def update_espn_statistics(self) -> None:
        """Update ESPN section with latest statistics from local database."""
        print("\n📊 Fetching ESPN statistics from local database...")

        try:
            stats = self.get_espn_statistics()

            # Update Quick Reference table - ESPN row
            pattern = (
                r"(\| ESPN API \|[^\|]+\|[^\|]+\| )(\d+|[\d,]+)( \| )([\d,]+)( \|)"
            )
            replacement = (
                f'\\g<1>{stats["total_games"]:,}\\g<3>{stats["total_events"]:,}\\g<5>'
            )
            self.update_field(
                pattern,
                replacement,
                f"ESPN Quick Reference: {stats['total_games']:,} games, {stats['total_events']:,} events",
            )

            # Update Source 1 statistics table - Total Games
            pattern = r"(\| \*\*Total Games\*\* \| )([\d,]+)( \|)"
            replacement = f'\\g<1>{stats["total_games"]:,}\\g<3>'
            self.update_field(
                pattern, replacement, f"ESPN Total Games → {stats['total_games']:,}"
            )

            # Update Source 1 statistics table - Games with PBP
            pattern = (
                r"(\| \*\*Games with PBP\*\* \| )([\d,]+)( \| [\d.]+% coverage \|)"
            )
            replacement = f'\\g<1>{stats["games_with_pbp"]:,}\\g<3>'
            self.update_field(
                pattern,
                replacement,
                f"ESPN Games with PBP → {stats['games_with_pbp']:,} ({stats['pbp_coverage_pct']}%)",
            )

            # Update Source 1 statistics table - Total PBP Events
            pattern = r"(\| \*\*Total PBP Events\*\* \| )([\d,]+)( \|)"
            replacement = f'\\g<1>{stats["total_events"]:,}\\g<3>'
            self.update_field(
                pattern,
                replacement,
                f"ESPN Total PBP Events → {stats['total_events']:,}",
            )

            # Update coverage by era table
            for era_name, total_games, pbp_games, pct, avg_events in stats["era_stats"]:
                # Update era row in coverage table
                pattern = rf"(\| \*\*{era_name}\*\* \|[^\|]+\| )([\d,]+)( \| [\d.]+% \([\d,]+ games\) \| ~)([\d,]+)( events \|)"
                replacement = f"\\g<1>{total_games:,}\\g<3>{int(avg_events)}\\g<5>"
                self.update_field(
                    pattern,
                    replacement,
                    f"ESPN {era_name} era → {total_games:,} games, {pct}% PBP, ~{int(avg_events)} events/game",
                )

            # Update Last Updated timestamp
            self.update_last_updated()

            print(f"✅ ESPN statistics updated successfully")
            print(f"   Games: {stats['total_games']:,}")
            print(
                f"   Games with PBP: {stats['games_with_pbp']:,} ({stats['pbp_coverage_pct']}%)"
            )
            print(f"   Total Events: {stats['total_events']:,}")
            print(f"   Date Range: {stats['min_date']} to {stats['max_date']}")

        except Exception as e:
            print(f"❌ Error updating ESPN statistics: {e}")
            raise

    def get_s3_statistics(self, prefix: str) -> Tuple[int, str]:
        """Get file count and size from S3 bucket prefix."""
        try:
            result = subprocess.run(
                [
                    "aws",
                    "s3",
                    "ls",
                    f"{S3_BUCKET}/{prefix}/",
                    "--recursive",
                    "--summarize",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                print(f"⚠️  Warning: Could not access S3 bucket {prefix}")
                return None, None

            # Parse output for file count and size
            file_count = None
            total_size = None

            for line in result.stdout.split("\n"):
                if "Total Objects:" in line:
                    file_count = int(line.split(":")[1].strip())
                elif "Total Size:" in line:
                    size_str = line.split(":")[1].strip()
                    total_size = self._parse_size(size_str)

            return file_count, total_size

        except Exception as e:
            print(f"⚠️  Warning: Error accessing S3: {e}")
            return None, None

    def _parse_size(self, size_str: str) -> str:
        """Parse S3 size output to human-readable format."""
        size_bytes = int(size_str)

        # Convert to GB
        size_gb = size_bytes / (1024**3)

        if size_gb >= 1:
            return f"{size_gb:.1f} GB"
        else:
            size_mb = size_bytes / (1024**2)
            return f"{size_mb:.1f} MB"

    def verify_catalog_consistency(self) -> bool:
        """Verify that catalog statistics are consistent across sections."""
        print("\n🔍 Verifying catalog consistency...")

        issues = []

        # Load catalog content
        self.load_catalog()

        # Extract ESPN statistics from different sections
        quick_ref_games = self._extract_value(
            r"\| ESPN API \|[^\|]+\|[^\|]+\| (\d+|[\d,]+) \|"
        )
        quick_ref_events = self._extract_value(
            r"\| ESPN API \|[^\|]+\|[^\|]+\| [\d,]+ \| ([\d,]+) \|"
        )

        source1_games = self._extract_value(r"\| \*\*Total Games\*\* \| ([\d,]+) \|")
        source1_pbp_games = self._extract_value(
            r"\| \*\*Games with PBP\*\* \| ([\d,]+) \|"
        )
        source1_events = self._extract_value(
            r"\| \*\*Total PBP Events\*\* \| ([\d,]+) \|"
        )

        # Compare values
        if quick_ref_games != source1_games:
            issues.append(
                f"Total games mismatch: Quick Ref ({quick_ref_games}) vs Source 1 ({source1_games})"
            )

        if quick_ref_events != source1_events:
            issues.append(
                f"Total events mismatch: Quick Ref ({quick_ref_events}) vs Source 1 ({source1_events})"
            )

        # Check if actual database matches catalog
        try:
            db_stats = self.get_espn_statistics()
            db_games_str = f"{db_stats['total_games']:,}"
            db_events_str = f"{db_stats['total_events']:,}"

            if source1_games != db_games_str:
                issues.append(
                    f"Database mismatch: Catalog shows {source1_games} games, DB has {db_games_str}"
                )

            if source1_events != db_events_str:
                issues.append(
                    f"Database mismatch: Catalog shows {source1_events} events, DB has {db_events_str}"
                )

        except Exception as e:
            issues.append(f"Could not verify against database: {e}")

        # Report results
        if issues:
            print("❌ Consistency issues found:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        else:
            print("✅ Catalog is consistent across all sections")
            return True

    def _extract_value(self, pattern: str) -> Optional[str]:
        """Extract a value from catalog using regex pattern."""
        match = re.search(pattern, self.catalog_content)
        if match:
            return match.group(1).replace(",", "")
        return None

    def update_hoopr_progress(
        self, seasons_complete: int, total_seasons: int = 24
    ) -> None:
        """Update hoopR progress statistics."""
        print(
            f"\n📊 Updating hoopR progress: {seasons_complete}/{total_seasons} seasons complete..."
        )

        try:
            self.load_catalog()

            pct_complete = round(100.0 * seasons_complete / total_seasons)

            # Update Quick Reference table - hoopR row
            pattern = r"(\| hoopR \|[^\|]+\| 🔄 )\d+%( COMPLETE \|)"
            replacement = f"\\g<1>{pct_complete}%\\2"
            self.update_field(
                pattern, replacement, f"hoopR Progress → {pct_complete}% complete"
            )

            # Update Source 2 statistics table
            pattern = (
                r"(\| \*\*Seasons Complete\*\* \| )\d+( seasons \| )\d+%( complete \|)"
            )
            replacement = f"\\g<1>{seasons_complete}\\2{pct_complete}%\\3"
            self.update_field(
                pattern,
                replacement,
                f"hoopR Seasons Complete → {seasons_complete} ({pct_complete}%)",
            )

            # Update Last Updated timestamp
            self.update_last_updated()

            self.save_catalog()

            print(f"✅ hoopR progress updated: {pct_complete}% complete")

        except Exception as e:
            print(f"❌ Error updating hoopR progress: {e}")
            raise

    def refresh_all_sources(self) -> None:
        """Refresh statistics for all data sources."""
        print("\n🔄 Refreshing all data sources...")

        self.load_catalog()

        # Update ESPN
        self.update_espn_statistics()

        # Update S3 file counts (if available)
        print("\n📦 Checking S3 statistics...")
        espn_files, espn_size = self.get_s3_statistics("espn")
        if espn_files:
            print(f"   ESPN: {espn_files:,} files, {espn_size}")

        hoopr_files, hoopr_size = self.get_s3_statistics("hoopr_phase1")
        if hoopr_files:
            print(f"   hoopR: {hoopr_files:,} files, {hoopr_size}")

        # Save all changes
        self.save_catalog()


def main():
    parser = argparse.ArgumentParser(
        description="Update DATA_CATALOG.md with current statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update ESPN statistics from local database
  %(prog)s --source espn --action update

  # Update hoopR progress
  %(prog)s --source hoopr --seasons-complete 7

  # Verify catalog consistency
  %(prog)s --verify

  # Refresh all sources
  %(prog)s --refresh-all

  # Dry run (show changes without applying)
  %(prog)s --source espn --dry-run
        """,
    )

    parser.add_argument(
        "--source",
        choices=["espn", "hoopr", "nba_api", "basketball_ref"],
        help="Data source to update",
    )

    parser.add_argument(
        "--action",
        choices=["update", "verify"],
        default="update",
        help="Action to perform (default: update)",
    )

    parser.add_argument(
        "--seasons-complete",
        type=int,
        help="Number of hoopR seasons complete (for hoopR updates)",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify catalog consistency across sections",
    )

    parser.add_argument(
        "--refresh-all", action="store_true", help="Refresh all data sources"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying them"
    )

    args = parser.parse_args()

    # Create updater instance
    updater = DataCatalogUpdater(dry_run=args.dry_run)

    try:
        # Handle verification
        if args.verify:
            success = updater.verify_catalog_consistency()
            sys.exit(0 if success else 1)

        # Handle refresh all
        if args.refresh_all:
            updater.refresh_all_sources()
            return

        # Handle source-specific updates
        if args.source == "espn":
            updater.load_catalog()
            updater.update_espn_statistics()
            updater.save_catalog()

        elif args.source == "hoopr":
            if not args.seasons_complete:
                print("❌ Error: --seasons-complete required for hoopR updates")
                sys.exit(1)
            updater.update_hoopr_progress(args.seasons_complete)

        else:
            print(f"❌ Source '{args.source}' not yet implemented")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
