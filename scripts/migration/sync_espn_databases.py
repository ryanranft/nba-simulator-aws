#!/usr/bin/env python3
"""
Sync ESPN Data Between nba_simulator and nba_mcp_synthesis Databases

This script ensures both databases have identical ESPN data by:
1. Comparing row counts and identifying discrepancies
2. Determining source of truth (nba_simulator is primary)
3. Syncing missing/extra data to nba_mcp_synthesis

Source Database (Primary):
- Database: nba_simulator
- Schema: espn
- Tables: espn_games (box_score_nba_espn), espn_team_stats (team_stats_nba_espn),
          espn_plays (pbp_nba_espn), espn_schedules (schedule_nba_espn)

Target Database (Secondary):
- Database: nba_mcp_synthesis
- Schema: espn_raw
- Tables: box_score_nba_espn, team_stats_nba_espn, pbp_nba_espn, schedule_nba_espn

Current Discrepancies:
- PBP: nba_simulator (14,180,218) vs nba_mcp_synthesis (14,180,696) - 478 extra
- Team Stats: nba_simulator (86,470) vs nba_mcp_synthesis (258) - 86,212 missing
- Box Scores: Both (45,129) - IDENTICAL
- Schedules: nba_simulator (6,917) vs nba_mcp_synthesis (0) - 6,917 missing

Usage:
    # Dry run (show what would be synced)
    python scripts/migration/sync_espn_databases.py --dry-run

    # Full sync (nba_simulator → nba_mcp_synthesis)
    python scripts/migration/sync_espn_databases.py

    # Sync specific tables
    python scripts/migration/sync_espn_databases.py --tables team_stats,schedules

    # Reverse sync (nba_mcp_synthesis → nba_simulator) - USE WITH CAUTION
    python scripts/migration/sync_espn_databases.py --reverse --dry-run
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_batch, Json, RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ESPNDatabaseSyncer:
    """Sync ESPN data between nba_simulator and nba_mcp_synthesis databases."""

    # Table mappings: source_table → target_table
    TABLE_MAPPINGS = {
        "espn.espn_games": "espn_raw.box_score_nba_espn",
        "espn.espn_team_stats": "espn_raw.team_stats_nba_espn",
        "espn.espn_plays": "espn_raw.pbp_nba_espn",
        "espn.espn_schedules": "espn_raw.schedule_nba_espn",
    }

    def __init__(
        self,
        source_db: str = "nba_simulator",
        target_db: str = "nba_mcp_synthesis",
        dry_run: bool = False,
        reverse: bool = False,
    ):
        """
        Initialize syncer.

        Args:
            source_db: Source database name (default: nba_simulator)
            target_db: Target database name (default: nba_mcp_synthesis)
            dry_run: If True, show what would be synced without making changes
            reverse: If True, sync from target to source (CAUTION!)
        """
        self.source_db = source_db
        self.target_db = target_db
        self.dry_run = dry_run
        self.reverse = reverse

        if reverse:
            logger.warning("⚠️  REVERSE MODE: Will sync from nba_mcp_synthesis → nba_simulator")
            logger.warning("⚠️  This may overwrite data in nba_simulator!")

        # Swap source/target if reverse mode
        if reverse:
            self.source_db, self.target_db = self.target_db, self.source_db
            # Reverse table mappings
            self.TABLE_MAPPINGS = {v: k for k, v in self.TABLE_MAPPINGS.items()}

        # Database configs
        self.source_config = self._get_db_config(self.source_db)
        self.target_config = self._get_db_config(self.target_db)

        # Statistics
        self.stats = {
            "games_synced": 0,
            "team_stats_synced": 0,
            "plays_synced": 0,
            "schedules_synced": 0,
            "games_deleted": 0,
            "team_stats_deleted": 0,
            "plays_deleted": 0,
        }

        # Connections
        self.source_conn = None
        self.target_conn = None

        logger.info(f"Initialized ESPNDatabaseSyncer")
        logger.info(f"  Source: {self.source_db}")
        logger.info(f"  Target: {self.target_db}")
        logger.info(f"  Dry run: {dry_run}")
        logger.info(f"  Reverse mode: {reverse}")

    def _get_db_config(self, db_name: str) -> Dict[str, str]:
        """Get database configuration."""
        return {
            "dbname": db_name,
            "user": os.getenv("POSTGRES_USER", "ryanranft"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    def connect(self):
        """Establish database connections."""
        try:
            self.source_conn = psycopg2.connect(**self.source_config)
            logger.info(f"✓ Connected to source: {self.source_db}")
        except Exception as e:
            logger.error(f"Failed to connect to source database {self.source_db}: {e}")
            raise

        try:
            self.target_conn = psycopg2.connect(**self.target_config)
            logger.info(f"✓ Connected to target: {self.target_db}")
        except Exception as e:
            logger.error(f"Failed to connect to target database {self.target_db}: {e}")
            raise

    def close(self):
        """Close database connections."""
        if self.source_conn:
            self.source_conn.close()
            logger.info(f"Closed source connection ({self.source_db})")

        if self.target_conn:
            self.target_conn.close()
            logger.info(f"Closed target connection ({self.target_db})")

    def compare_counts(self) -> Dict[str, Tuple[int, int]]:
        """
        Compare row counts between source and target.

        Returns:
            Dict mapping table name to (source_count, target_count)
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("COMPARING ROW COUNTS")
        logger.info("=" * 70)

        counts = {}

        for source_table, target_table in self.TABLE_MAPPINGS.items():
            # Count source
            with self.source_conn.cursor() as cur:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {source_table}")
                    source_count = cur.fetchone()[0]
                except Exception as e:
                    logger.warning(f"Could not count {source_table}: {e}")
                    source_count = 0

            # Count target
            with self.target_conn.cursor() as cur:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {target_table}")
                    target_count = cur.fetchone()[0]
                except Exception as e:
                    logger.warning(f"Could not count {target_table}: {e}")
                    target_count = 0

            counts[source_table] = (source_count, target_count)

            # Calculate difference
            diff = source_count - target_count
            status = "✓" if diff == 0 else "⚠️"

            logger.info(f"{status} {source_table}")
            logger.info(f"   Source: {source_count:,}")
            logger.info(f"   Target: {target_count:,}")
            logger.info(f"   Diff:   {diff:+,}")
            logger.info("")

        logger.info("=" * 70)
        return counts

    def check_schemas(self):
        """Check if target schemas and tables exist, create if needed."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("CHECKING TARGET SCHEMAS AND TABLES")
        logger.info("=" * 70)

        # Check if espn_raw schema exists
        with self.target_conn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'espn_raw'"
            )
            schema_exists = cur.fetchone() is not None

            if not schema_exists:
                logger.info("Creating espn_raw schema in target database...")
                if not self.dry_run:
                    cur.execute("CREATE SCHEMA espn_raw")
                    self.target_conn.commit()
                    logger.info("✓ Created espn_raw schema")
                else:
                    logger.info("[DRY RUN] Would create espn_raw schema")

        # Check each target table
        for source_table, target_table in self.TABLE_MAPPINGS.items():
            schema, table = target_table.split(".")

            with self.target_conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}' AND table_name = '{table}'
                    """
                )
                table_exists = cur.fetchone() is not None

                if not table_exists:
                    logger.warning(f"⚠️  Table {target_table} does not exist!")
                    logger.info(f"   Will need to create based on {source_table} schema")
                else:
                    logger.info(f"✓ Table {target_table} exists")

        logger.info("=" * 70)

    def sync_table(
        self,
        source_table: str,
        target_table: str,
        batch_size: int = 1000,
    ):
        """
        Sync data from source table to target table.

        Args:
            source_table: Fully qualified source table (e.g., 'espn.espn_games')
            target_table: Fully qualified target table (e.g., 'espn_raw.box_score_nba_espn')
            batch_size: Number of records to process per batch
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"SYNCING: {source_table} → {target_table}")
        logger.info("=" * 70)

        # For now, implement full table copy
        # TODO: Implement differential sync (only missing records)

        logger.info("Sync strategy: FULL TABLE COPY")
        logger.info("⚠️  This will DELETE all data in target and copy from source")

        if self.dry_run:
            logger.info("[DRY RUN] Would sync data")
            return

        # Count source
        with self.source_conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {source_table}")
            total = cur.fetchone()[0]

        logger.info(f"Total records to sync: {total:,}")

        # For now, log that this is a placeholder
        logger.warning("⚠️  Full sync not yet implemented")
        logger.warning("⚠️  This requires table schema mapping first")
        logger.info("=" * 70)

    def sync_all(self, tables: Optional[List[str]] = None):
        """
        Sync all tables or specified tables.

        Args:
            tables: List of table names to sync (e.g., ['games', 'team_stats'])
                   If None, syncs all tables
        """
        self.connect()

        try:
            # Compare counts
            counts = self.compare_counts()

            # Check schemas
            self.check_schemas()

            # Sync each table
            for source_table, target_table in self.TABLE_MAPPINGS.items():
                # Check if we should sync this table
                table_name = source_table.split(".")[-1].replace("espn_", "")
                if tables and table_name not in tables:
                    logger.info(f"Skipping {source_table} (not in requested tables)")
                    continue

                source_count, target_count = counts[source_table]

                if source_count == target_count:
                    logger.info(f"✓ {source_table} already in sync ({source_count:,} records)")
                    continue

                self.sync_table(source_table, target_table)

            # Print summary
            self.print_summary()

        finally:
            self.close()

    def print_summary(self):
        """Print sync summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("SYNC SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Games synced:       {self.stats['games_synced']:,}")
        logger.info(f"Team stats synced:  {self.stats['team_stats_synced']:,}")
        logger.info(f"Plays synced:       {self.stats['plays_synced']:,}")
        logger.info(f"Schedules synced:   {self.stats['schedules_synced']:,}")
        logger.info("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync ESPN data between nba_simulator and nba_mcp_synthesis"
    )
    parser.add_argument(
        "--source-db",
        default="nba_simulator",
        help="Source database (default: nba_simulator)",
    )
    parser.add_argument(
        "--target-db",
        default="nba_mcp_synthesis",
        help="Target database (default: nba_mcp_synthesis)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Sync from nba_mcp_synthesis to nba_simulator (CAUTION!)",
    )
    parser.add_argument(
        "--tables",
        help="Comma-separated list of tables to sync (e.g., 'games,team_stats')",
    )

    args = parser.parse_args()

    # Parse tables
    tables = None
    if args.tables:
        tables = [t.strip() for t in args.tables.split(",")]

    # Create syncer
    syncer = ESPNDatabaseSyncer(
        source_db=args.source_db,
        target_db=args.target_db,
        dry_run=args.dry_run,
        reverse=args.reverse,
    )

    # Run sync
    syncer.sync_all(tables=tables)


if __name__ == "__main__":
    main()
