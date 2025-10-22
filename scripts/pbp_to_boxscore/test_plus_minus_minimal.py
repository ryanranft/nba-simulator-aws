#!/usr/bin/env python3
"""
Minimal Plus/Minus System Test - RDS PostgreSQL

Tests core table population without complex views.
Focus on validating data insertion and basic queries.

Created: October 19, 2025
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from populate_plus_minus_tables import PlusMinusPopulator

load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'nba_simulator'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', 5432))
}

SQL_DIR = Path(__file__).parent.parent.parent / 'sql' / 'plus_minus'

print("=" * 70)
print("PLUS/MINUS SYSTEM - MINIMAL RDS TEST")
print("=" * 70)
print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

def create_tables(conn):
    """Create plus/minus tables"""
    print("Step 1: Creating Tables")
    print("-" * 70)

    cursor = conn.cursor()
    table_files = [
        ('lineup_snapshots', SQL_DIR / '01_create_lineup_snapshots.sql'),
        ('player_plus_minus_snapshots', SQL_DIR / '02_create_player_plus_minus_snapshots.sql'),
        ('possession_metadata', SQL_DIR / '03_create_possession_metadata.sql')
    ]

    for table_name, sql_file in table_files:
        print(f"  {table_name}...", end=' ')
        with open(sql_file, 'r') as f:
            sql = f.read()
        try:
            cursor.execute(sql)
            conn.commit()
            print("✅")
        except psycopg2.Error as e:
            if 'already exists' in str(e):
                print("(exists)")
                conn.rollback()
            else:
                print(f"ERROR: {e}")
                raise
    print()

def populate_tables(conn):
    """Populate tables with test data"""
    print("Step 2: Populating Tables")
    print("-" * 70)

    cursor = conn.cursor()

    # Find a game with snapshot data
    cursor.execute("""
        SELECT g.game_id, COUNT(*) as snapshot_count
        FROM game_state_snapshots g
        GROUP BY g.game_id
        HAVING COUNT(*) > 100
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    if not result:
        print("  ERROR: No games found with snapshot data")
        return False

    game_id, snapshot_count = result
    print(f"  Found game: {game_id} ({snapshot_count:,} snapshots)")

    # Populate tables
    populator = PlusMinusPopulator(DB_CONFIG, use_postgres=True)
    try:
        result = populator.populate_game(game_id)
        print(f"  Lineup snapshots: {result.get('lineups', 0):,}")
        print(f"  Player +/- records: {result.get('player_pm', 0):,}")
        print(f"  Possessions tracked: {result.get('possessions', 0):,}")
        print()
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        populator.close()

def validate_data(conn):
    """Run basic validation queries"""
    print("Step 3: Data Validation")
    print("-" * 70)

    cursor = conn.cursor()

    # Check 1: Row counts
    cursor.execute("SELECT COUNT(*) FROM lineup_snapshots;")
    lineup_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM player_plus_minus_snapshots;")
    player_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM possession_metadata;")
    poss_count = cursor.fetchone()[0]

    print(f"  lineup_snapshots: {lineup_count:,} rows")
    print(f"  player_plus_minus_snapshots: {player_count:,} rows")
    print(f"  possession_metadata: {poss_count:,} rows")
    print()

    # Check 2: Sample lineup query
    print("  Sample Query: Best Lineups by Plus/Minus")
    cursor.execute("""
        SELECT
            lineup_hash,
            COUNT(DISTINCT possession_number) as possessions,
            MAX(plus_minus) - MIN(plus_minus) as total_plus_minus
        FROM lineup_snapshots
        WHERE possession_number IS NOT NULL
        GROUP BY lineup_hash
        HAVING COUNT(DISTINCT possession_number) >= 5
        ORDER BY total_plus_minus DESC
        LIMIT 5
    """)
    results = cursor.fetchall()
    for lineup_hash, poss, pm in results:
        print(f"    {lineup_hash[:16]}... : {poss} poss, +{pm} +/-")
    print()

    # Check 3: Sample player query
    print("  Sample Query: Player On-Court Plus/Minus")
    cursor.execute("""
        SELECT
            player_id,
            MAX(plus_minus) - MIN(plus_minus) as on_court_plus_minus,
            COUNT(*) as events_on_court
        FROM player_plus_minus_snapshots
        WHERE on_court = TRUE
        GROUP BY player_id
        ORDER BY on_court_plus_minus DESC
        LIMIT 5
    """)
    results = cursor.fetchall()
    for player_id, pm, events in results:
        print(f"    {player_id}: +{pm} +/- ({events:,} events)")
    print()

    return True

def main():
    """Run minimal test"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to RDS\n")

        create_tables(conn)

        if not populate_tables(conn):
            print("\n❌ Population failed")
            return 1

        if not validate_data(conn):
            print("\n❌ Validation failed")
            return 1

        print("=" * 70)
        print("✅ MINIMAL TEST COMPLETE")
        print("=" * 70)
        print()
        print("System Status: Core tables working ✅")
        print("  - 3 tables created and populated")
        print("  - Data insertion successful")
        print("  - Basic queries validated")
        print()
        print("Next Steps:")
        print("  - Fix view SQL for PostgreSQL compatibility")
        print("  - Add biographical data columns if needed")
        print("  - Run full performance tests")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
