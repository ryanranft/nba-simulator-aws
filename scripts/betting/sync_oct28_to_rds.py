#!/usr/bin/env python3
"""
Quick sync of October 28, 2025 odds data from local to RDS.

Usage:
    python scripts/betting/sync_oct28_to_rds.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load RDS credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

# Local PostgreSQL
LOCAL_CONFIG = {"host": "localhost", "port": 5432, "database": "nba_unified"}

# RDS PostgreSQL
RDS_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}

print("=" * 70)
print("SYNCING OCTOBER 28, 2025 ODDS DATA TO RDS")
print("=" * 70)

# Connect to both databases
print("\nConnecting to databases...")
local_conn = psycopg2.connect(**LOCAL_CONFIG)
rds_conn = psycopg2.connect(**RDS_CONFIG)
print("  ✓ Connected")

# Sync bookmakers
print("\n1. Syncing bookmakers...")
local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
local_cur.execute("SELECT bookmaker_key, title FROM odds.bookmakers")
bookmakers = local_cur.fetchall()

rds_cur = rds_conn.cursor()
for row in bookmakers:
    rds_cur.execute(
        """
        INSERT INTO odds.bookmakers (bookmaker_key, bookmaker_title)
        VALUES (%s, %s)
        ON CONFLICT (bookmaker_key) DO UPDATE 
        SET bookmaker_title = EXCLUDED.bookmaker_title
        """,
        (row["bookmaker_key"], row["title"]),
    )
rds_conn.commit()
print(f"  ✓ Synced {len(bookmakers)} bookmakers")

# Sync market types
print("2. Syncing market types...")
local_cur.execute("SELECT market_key, market_name FROM odds.market_types")
markets = local_cur.fetchall()

for row in markets:
    rds_cur.execute(
        """
        INSERT INTO odds.market_types (market_key, market_name)
        VALUES (%s, %s)
        ON CONFLICT (market_key) DO UPDATE 
        SET market_name = EXCLUDED.market_name
        """,
        (row["market_key"], row["market_name"]),
    )
rds_conn.commit()
print(f"  ✓ Synced {len(markets)} market types")

# Get bookmaker/market mappings from RDS
rds_cur.execute("SELECT bookmaker_id, bookmaker_key FROM odds.bookmakers")
bookmaker_map = {row[1]: row[0] for row in rds_cur.fetchall()}

rds_cur.execute("SELECT market_type_id, market_key FROM odds.market_types")
market_map = {row[1]: row[0] for row in rds_cur.fetchall()}

# Sync October 28 events
print("3. Syncing October 28 events...")
local_cur.execute(
    """
    SELECT event_id, sport_key, sport_title, commence_time, home_team, away_team, created_at, updated_at
    FROM odds.events
    WHERE commence_time::date = '2025-10-28'
    """
)
events = local_cur.fetchall()

for row in events:
    rds_cur.execute(
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
rds_conn.commit()
print(f"  ✓ Synced {len(events)} events")

# Show game details
print("\n  October 28 Games:")
for evt in events:
    print(f"    • {evt['away_team']} @ {evt['home_team']}")

# Get event IDs for October 28
event_ids = [evt["event_id"] for evt in events]

# Sync October 28 odds snapshots
print("\n4. Syncing October 28 odds snapshots...")
local_cur.execute(
    """
    SELECT 
        event_id, bookmaker_key, market_key, outcome_name, price, point, last_update
    FROM odds.odds_snapshots
    WHERE event_id = ANY(%s)
    """,
    (event_ids,),
)
snapshots = local_cur.fetchall()

synced = 0
skipped = 0

for row in snapshots:
    bookmaker_id = bookmaker_map.get(row["bookmaker_key"])
    market_type_id = market_map.get(row["market_key"])

    if not bookmaker_id or not market_type_id:
        skipped += 1
        continue

    last_update = row["last_update"] if row["last_update"] else datetime.now()

    rds_cur.execute(
        """
        INSERT INTO odds.odds_snapshots (
            event_id, bookmaker_id, market_type_id, outcome_name, price, point, last_update, fetched_at, is_latest
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, TRUE)
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
        ),
    )
    synced += 1

rds_conn.commit()
print(f"  ✓ Synced {synced:,} odds snapshots")
if skipped > 0:
    print(f"  ⚠️  Skipped {skipped:,} snapshots")

# Verify
print("\n5. Verifying RDS data...")
rds_cur.execute(
    "SELECT COUNT(*) FROM odds.events WHERE commence_time::date = '2025-10-28'"
)
rds_events = rds_cur.fetchone()[0]

rds_cur.execute(
    """
    SELECT COUNT(*) FROM odds.odds_snapshots 
    WHERE event_id = ANY(%s)
    """,
    (event_ids,),
)
rds_snapshots = rds_cur.fetchone()[0]

print(f"  October 28 Events in RDS: {rds_events}")
print(f"  October 28 Odds in RDS: {rds_snapshots:,}")

# Close connections
local_conn.close()
rds_conn.close()

print("\n" + "=" * 70)
print("✅ SYNC COMPLETE")
print("=" * 70)
print("\nYou can now run betting analysis:")
print("  python3 scripts/betting/run_full_betting_analysis.py --date 2025-10-28")

