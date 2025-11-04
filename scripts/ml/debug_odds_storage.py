#!/usr/bin/env python3
"""
Debug script to check odds storage in database.

Checks if events and odds exist but aren't being found due to date/timezone filters.
"""

import psycopg2
import os
from datetime import date, datetime
from dotenv import load_dotenv
from pytz import timezone

load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=os.getenv('DB_PORT', 5432),
    sslmode='require'
)

cur = conn.cursor()

print("=" * 80)
print("ODDS STORAGE DEBUG")
print("=" * 80)
print()

# Check total counts
cur.execute("SELECT COUNT(*) FROM odds.events")
total_events = cur.fetchone()[0]
print(f"Total events in odds.events: {total_events}")

cur.execute("SELECT COUNT(*) FROM odds.odds_snapshots WHERE is_latest = true")
total_latest_odds = cur.fetchone()[0]
print(f"Total latest odds snapshots: {total_latest_odds}")
print()

# Check events by date (no timezone conversion)
cur.execute("""
SELECT 
    DATE(commence_time) as game_date_utc,
    COUNT(*) as num_events
FROM odds.events
WHERE commence_time >= NOW() - INTERVAL '7 days'
  AND commence_time <= NOW() + INTERVAL '7 days'
GROUP BY DATE(commence_time)
ORDER BY game_date_utc DESC
""")

print("Events by UTC date (last 7 days + next 7 days):")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} events")
print()

# Check events with Chicago timezone conversion
today = date.today()
cur.execute("""
SELECT 
    DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago') as game_date_ct,
    COUNT(*) as num_events,
    COUNT(os.snapshot_id) as num_odds
FROM odds.events e
LEFT JOIN odds.odds_snapshots os ON e.event_id = os.event_id AND os.is_latest = true
WHERE e.commence_time >= NOW() - INTERVAL '7 days'
  AND e.commence_time <= NOW() + INTERVAL '7 days'
GROUP BY DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago')
ORDER BY game_date_ct DESC
""")

print(f"Events by Chicago date (today is {today}):")
results = cur.fetchall()
for row in results:
    is_today = row[0] == today
    marker = " ← TODAY" if is_today else ""
    print(f"  {row[0]}: {row[1]} events, {row[2]} odds{marker}")
print()

# Get most recent events regardless of date
cur.execute("""
SELECT 
    e.event_id,
    e.home_team,
    e.away_team,
    e.commence_time,
    e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago' as commence_time_ct,
    DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago') as game_date_ct,
    e.created_at,
    COUNT(os.snapshot_id) as num_odds
FROM odds.events e
LEFT JOIN odds.odds_snapshots os ON e.event_id = os.event_id AND os.is_latest = true
WHERE e.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY e.event_id, e.home_team, e.away_team, e.commence_time, e.created_at
ORDER BY e.created_at DESC
LIMIT 20
""")

print("Most recent events (last 24 hours):")
results = cur.fetchall()
if len(results) > 0:
    for row in results:
        print(f"  {row[2]} @ {row[1]}")
        print(f"    Event ID: {row[0]}")
        print(f"    Commence (UTC): {row[3]}")
        print(f"    Commence (CT): {row[4]}")
        print(f"    Game Date (CT): {row[5]}")
        print(f"    Created: {row[6]}")
        print(f"    Odds: {row[7]} records")
        print()
else:
    print("  No events found in last 24 hours")
    print()

# Check if there are any odds snapshots without events
cur.execute("""
SELECT 
    COUNT(*) as num_orphaned_odds
FROM odds.odds_snapshots os
WHERE NOT EXISTS (
    SELECT 1 FROM odds.events e WHERE e.event_id = os.event_id
)
""")
orphaned = cur.fetchone()[0]
print(f"Orphaned odds snapshots (no event): {orphaned}")
print()

# Check odds snapshots created recently
cur.execute("""
SELECT 
    COUNT(*) as num_snapshots,
    MIN(fetched_at) as earliest,
    MAX(fetched_at) as latest
FROM odds.odds_snapshots
WHERE fetched_at >= NOW() - INTERVAL '24 hours'
  AND is_latest = true
""")
result = cur.fetchone()
print(f"Odds snapshots created in last 24 hours: {result[0]}")
if result[0] > 0:
    print(f"  Earliest: {result[1]}")
    print(f"  Latest: {result[2]}")
print()

conn.close()

print("=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)

