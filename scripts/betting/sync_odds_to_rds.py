#!/usr/bin/env python3
"""
Sync odds data from local PostgreSQL to RDS.

Keeps both databases in sync:
- Local: localhost:5432/nba_unified (fast, scraper writes here)
- RDS: nba-sim-db.../nba_simulator (production, betting scripts read here)

Usage:
    python scripts/betting/sync_odds_to_rds.py --full-sync        # One-time full sync
    python scripts/betting/sync_odds_to_rds.py --continuous       # Continuous sync every 60s
    python scripts/betting/sync_odds_to_rds.py --check-only       # Just check status
"""

import os
import sys
import time
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load RDS credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

# Local PostgreSQL configuration
LOCAL_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "nba_unified",
}

# RDS PostgreSQL configuration
RDS_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}


class OddsSyncManager:
    """Manages synchronization between local and RDS databases."""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.local_conn = None
        self.rds_conn = None

    def connect_local(self):
        """Connect to local PostgreSQL."""
        if self.verbose:
            print("Connecting to local PostgreSQL...")
        try:
            self.local_conn = psycopg2.connect(**LOCAL_CONFIG)
            if self.verbose:
                print("  ✓ Local connection established")
        except Exception as e:
            print(f"  ✗ Local connection failed: {e}")
            sys.exit(1)

    def connect_rds(self):
        """Connect to RDS PostgreSQL."""
        if self.verbose:
            print("Connecting to RDS PostgreSQL...")
        try:
            self.rds_conn = psycopg2.connect(**RDS_CONFIG)
            if self.verbose:
                print("  ✓ RDS connection established")
        except Exception as e:
            print(f"  ✗ RDS connection failed: {e}")
            sys.exit(1)

    def check_status(self):
        """Check current status of both databases."""
        print("\n" + "=" * 70)
        print("DATABASE STATUS CHECK")
        print("=" * 70)

        # Local database
        local_cursor = self.local_conn.cursor(cursor_factory=RealDictCursor)
        local_cursor.execute("SELECT COUNT(*) as count FROM odds.events")
        local_events = local_cursor.fetchone()["count"]
        local_cursor.execute("SELECT COUNT(*) as count FROM odds.odds_snapshots")
        local_snapshots = local_cursor.fetchone()["count"]
        local_cursor.execute(
            "SELECT COUNT(*) as count FROM odds.events WHERE commence_time::date = '2025-10-28'"
        )
        local_oct28 = local_cursor.fetchone()["count"]

        print(f"\nLocal Database (localhost:5432/nba_unified):")
        print(f"  Events: {local_events:,}")
        print(f"  Odds Snapshots: {local_snapshots:,}")
        print(f"  October 28 Games: {local_oct28}")

        # RDS database
        rds_cursor = self.rds_conn.cursor(cursor_factory=RealDictCursor)
        rds_cursor.execute("SELECT COUNT(*) as count FROM odds.events")
        rds_events = rds_cursor.fetchone()["count"]
        rds_cursor.execute("SELECT COUNT(*) as count FROM odds.odds_snapshots")
        rds_snapshots = rds_cursor.fetchone()["count"]
        rds_cursor.execute(
            "SELECT COUNT(*) as count FROM odds.events WHERE commence_time::date = '2025-10-28'"
        )
        rds_oct28 = rds_cursor.fetchone()["count"]

        print(f"\nRDS Database (nba-sim-db...amazonaws.com/nba_simulator):")
        print(f"  Events: {rds_events:,}")
        print(f"  Odds Snapshots: {rds_snapshots:,}")
        print(f"  October 28 Games: {rds_oct28}")

        print(f"\nSync Status:")
        events_diff = local_events - rds_events
        snapshots_diff = local_snapshots - rds_snapshots
        print(f"  Events to sync: {events_diff:,}")
        print(f"  Snapshots to sync: {snapshots_diff:,}")

        if events_diff == 0 and snapshots_diff == 0:
            print("  ✅ Databases are in sync!")
        else:
            print("  ⚠️  Databases need synchronization")

        print("=" * 70)

        return {
            "local_events": local_events,
            "rds_events": rds_events,
            "local_snapshots": local_snapshots,
            "rds_snapshots": rds_snapshots,
            "needs_sync": events_diff > 0 or snapshots_diff > 0,
        }

    def sync_bookmakers(self):
        """Sync bookmakers reference table."""
        if self.verbose:
            print("\nSyncing bookmakers...")

        local_cursor = self.local_conn.cursor(cursor_factory=RealDictCursor)
        local_cursor.execute("SELECT bookmaker_key, title FROM odds.bookmakers")
        bookmakers = local_cursor.fetchall()

        rds_cursor = self.rds_conn.cursor()
        synced = 0

        for row in bookmakers:
            rds_cursor.execute(
                """
                INSERT INTO odds.bookmakers (bookmaker_key, bookmaker_title)
                VALUES (%s, %s)
                ON CONFLICT (bookmaker_key) DO UPDATE
                SET bookmaker_title = EXCLUDED.bookmaker_title
                """,
                (row["bookmaker_key"], row["title"]),
            )
            synced += 1

        self.rds_conn.commit()
        if self.verbose:
            print(f"  ✓ Synced {synced} bookmakers")

    def sync_market_types(self):
        """Sync market_types reference table."""
        if self.verbose:
            print("Syncing market types...")

        local_cursor = self.local_conn.cursor(cursor_factory=RealDictCursor)
        local_cursor.execute("SELECT market_key, market_name FROM odds.market_types")
        market_types = local_cursor.fetchall()

        rds_cursor = self.rds_conn.cursor()
        synced = 0

        for row in market_types:
            rds_cursor.execute(
                """
                INSERT INTO odds.market_types (market_key, market_name)
                VALUES (%s, %s)
                ON CONFLICT (market_key) DO UPDATE
                SET market_name = EXCLUDED.market_name
                """,
                (row["market_key"], row["market_name"]),
            )
            synced += 1

        self.rds_conn.commit()
        if self.verbose:
            print(f"  ✓ Synced {synced} market types")

    def sync_events(self):
        """Sync events table."""
        if self.verbose:
            print("Syncing events...")

        local_cursor = self.local_conn.cursor(cursor_factory=RealDictCursor)
        local_cursor.execute(
            """
            SELECT
                event_id, sport_key, sport_title, commence_time,
                home_team, away_team, created_at, updated_at
            FROM odds.events
            """
        )
        events = local_cursor.fetchall()

        rds_cursor = self.rds_conn.cursor()
        synced = 0

        for row in events:
            rds_cursor.execute(
                """
                INSERT INTO odds.events (
                    event_id, sport_key, sport_title, commence_time,
                    home_team, away_team, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO UPDATE SET
                    sport_key = EXCLUDED.sport_key,
                    sport_title = EXCLUDED.sport_title,
                    commence_time = EXCLUDED.commence_time,
                    home_team = EXCLUDED.home_team,
                    away_team = EXCLUDED.away_team,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    row["event_id"],
                    row["sport_key"],
                    row["sport_title"],
                    row["commence_time"],
                    row["home_team"],
                    row["away_team"],
                    row["created_at"],
                    row["updated_at"],
                ),
            )
            synced += 1

        self.rds_conn.commit()
        if self.verbose:
            print(f"  ✓ Synced {synced:,} events")

    def sync_odds_snapshots(self, batch_size=1000):
        """Sync odds_snapshots table in batches."""
        if self.verbose:
            print("Syncing odds snapshots...")

        # Get bookmaker and market_type mappings from RDS
        rds_cursor = self.rds_conn.cursor(cursor_factory=RealDictCursor)

        # Bookmaker mapping
        rds_cursor.execute("SELECT bookmaker_id, bookmaker_key FROM odds.bookmakers")
        bookmaker_map = {
            row["bookmaker_key"]: row["bookmaker_id"] for row in rds_cursor.fetchall()
        }

        # Market type mapping
        rds_cursor.execute("SELECT market_type_id, market_key FROM odds.market_types")
        market_map = {
            row["market_key"]: row["market_type_id"] for row in rds_cursor.fetchall()
        }

        # Get total count
        local_cursor = self.local_conn.cursor(cursor_factory=RealDictCursor)
        local_cursor.execute("SELECT COUNT(*) as count FROM odds.odds_snapshots")
        total = local_cursor.fetchone()["count"]

        # Fetch in batches
        offset = 0
        synced = 0
        skipped = 0

        while offset < total:
            local_cursor.execute(
                """
                SELECT
                    event_id,
                    bookmaker_key,
                    market_key,
                    outcome_name,
                    price,
                    point,
                    last_update
                FROM odds.odds_snapshots
                LIMIT %s OFFSET %s
                """,
                (batch_size, offset),
            )
            batch = local_cursor.fetchall()

            if not batch:
                break

            # Insert batch
            for row in batch:
                bookmaker_id = bookmaker_map.get(row["bookmaker_key"])
                market_type_id = market_map.get(row["market_key"])

                if not bookmaker_id or not market_type_id:
                    skipped += 1
                    continue

                # Determine if it's latest (for simplicity, mark all as latest)
                is_latest = True

                # Use last_update if available, otherwise use current timestamp
                last_update = row["last_update"] if row["last_update"] else datetime.now()

                rds_cursor.execute(
                    """
                    INSERT INTO odds.odds_snapshots (
                        event_id, bookmaker_id, market_type_id,
                        outcome_name, price, point, last_update, fetched_at, is_latest
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        row["event_id"],
                        bookmaker_id,
                        market_type_id,
                        row["outcome_name"],
                        row["price"],
                        row["point"],
                        last_update,
                        is_latest,
                    ),
                )
                synced += 1

            self.rds_conn.commit()
            offset += batch_size

            if self.verbose:
                pct = (offset / total) * 100
                print(f"  Progress: {synced:,} / {total:,} ({pct:.1f}%)")

        if self.verbose:
            print(f"  ✓ Synced {synced:,} odds snapshots")
            if skipped > 0:
                print(f"  ⚠️  Skipped {skipped:,} snapshots (missing bookmaker/market mapping)")

    def full_sync(self):
        """Perform full synchronization."""
        print("\n" + "=" * 70)
        print("STARTING FULL SYNC")
        print("=" * 70)

        start_time = time.time()

        # Sync reference tables first
        self.sync_bookmakers()
        self.sync_market_types()

        # Sync main tables
        self.sync_events()
        self.sync_odds_snapshots()

        elapsed = time.time() - start_time

        print("\n" + "=" * 70)
        print("SYNC COMPLETE")
        print("=" * 70)
        print(f"Duration: {elapsed:.1f} seconds")

        # Check final status
        self.check_status()

    def continuous_sync(self, interval=60):
        """Run continuous sync at specified interval."""
        print("\n" + "=" * 70)
        print("STARTING CONTINUOUS SYNC")
        print(f"Interval: {interval} seconds")
        print("Press Ctrl+C to stop")
        print("=" * 70)

        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Syncing...")

                # Quick incremental sync
                self.sync_bookmakers()
                self.sync_market_types()
                self.sync_events()
                self.sync_odds_snapshots(batch_size=500)

                print(f"  ✓ Sync completed. Next sync in {interval}s...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nContinuous sync stopped by user.")

    def close(self):
        """Close database connections."""
        if self.local_conn:
            self.local_conn.close()
        if self.rds_conn:
            self.rds_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Sync odds data between local PostgreSQL and RDS"
    )
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Perform one-time full sync of all data",
    )
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuous sync in background"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds for continuous sync (default: 60)",
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check status, don't sync"
    )
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Create sync manager
    sync_manager = OddsSyncManager(verbose=not args.quiet)

    try:
        # Connect to databases
        sync_manager.connect_local()
        sync_manager.connect_rds()

        if args.check_only:
            # Just check status
            sync_manager.check_status()

        elif args.full_sync:
            # Full sync
            sync_manager.full_sync()

        elif args.continuous:
            # Continuous sync
            sync_manager.continuous_sync(interval=args.interval)

        else:
            # Default: check status and ask
            status = sync_manager.check_status()
            if status["needs_sync"]:
                print("\nRun with --full-sync to synchronize databases.")
            print("\nOptions:")
            print("  --full-sync      One-time full synchronization")
            print("  --continuous     Continuous sync every 60 seconds")
            print("  --check-only     Only check status")

    finally:
        sync_manager.close()


if __name__ == "__main__":
    main()

