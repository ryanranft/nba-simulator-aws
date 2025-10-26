#!/usr/bin/env python3
"""
Initialize odds schema in RDS PostgreSQL.

Creates the odds schema and core tables needed for betting odds data.
Uses synchronous psycopg2 to match nba-simulator-aws patterns.

Usage:
    python scripts/db/init_odds_schema.py
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from external credentials file
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"),
    "database": os.getenv("DB_NAME", "nba_simulator"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432),
    "sslmode": "require",
}


def create_odds_schema(conn):
    """Create odds schema and core tables."""
    cursor = conn.cursor()

    print("=" * 70)
    print("CREATING ODDS SCHEMA AND TABLES")
    print("=" * 70)
    print()

    # Create schema
    print("1. Creating odds schema...")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS odds")
    print("   ✓ Schema created")
    print()

    # Create events table
    print("2. Creating odds.events table...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS odds.events (
            event_id VARCHAR(100) PRIMARY KEY,
            sport_key VARCHAR(50) NOT NULL,
            sport_title VARCHAR(100),
            commence_time TIMESTAMP NOT NULL,
            home_team VARCHAR(100) NOT NULL,
            away_team VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    print("   ✓ Table created")
    print()

    # Create bookmakers table
    print("3. Creating odds.bookmakers table...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS odds.bookmakers (
            bookmaker_id SERIAL PRIMARY KEY,
            bookmaker_key VARCHAR(50) UNIQUE NOT NULL,
            bookmaker_title VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    print("   ✓ Table created")
    print()

    # Create market_types table
    print("4. Creating odds.market_types table...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS odds.market_types (
            market_type_id SERIAL PRIMARY KEY,
            market_key VARCHAR(50) UNIQUE NOT NULL,
            market_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    print("   ✓ Table created")
    print()

    # Create odds_snapshots table
    print("5. Creating odds.odds_snapshots table...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS odds.odds_snapshots (
            snapshot_id BIGSERIAL PRIMARY KEY,
            event_id VARCHAR(100) NOT NULL REFERENCES odds.events(event_id) ON DELETE CASCADE,
            bookmaker_id INTEGER NOT NULL REFERENCES odds.bookmakers(bookmaker_id),
            market_type_id INTEGER NOT NULL REFERENCES odds.market_types(market_type_id),
            outcome_name VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2),
            point DECIMAL(10, 2),
            last_update TIMESTAMP NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_latest BOOLEAN DEFAULT TRUE
        )
    """
    )
    print("   ✓ Table created")
    print()

    # Create scores table
    print("6. Creating odds.scores table...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS odds.scores (
            score_id SERIAL PRIMARY KEY,
            event_id VARCHAR(100) NOT NULL REFERENCES odds.events(event_id) ON DELETE CASCADE,
            home_score INTEGER,
            away_score INTEGER,
            is_final BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    print("   ✓ Table created")
    print()

    # Create indexes
    print("7. Creating indexes...")
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_commence_time
        ON odds.events(commence_time)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_home_team
        ON odds.events(home_team)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_away_team
        ON odds.events(away_team)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_odds_snapshots_event
        ON odds.odds_snapshots(event_id)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_odds_snapshots_is_latest
        ON odds.odds_snapshots(is_latest) WHERE is_latest = TRUE
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scores_event
        ON odds.scores(event_id)
    """
    )
    print("   ✓ Indexes created")
    print()

    # Insert common bookmakers
    print("8. Inserting common bookmakers...")
    bookmakers = [
        ("draftkings", "DraftKings"),
        ("fanduel", "FanDuel"),
        ("betmgm", "BetMGM"),
        ("pointsbet", "PointsBet"),
        ("williamhill_us", "William Hill (US)"),
        ("barstool", "Barstool Sportsbook"),
        ("betonlineag", "BetOnline.ag"),
        ("bovada", "Bovada"),
        ("mybookieag", "MyBookie.ag"),
        ("wynnbet", "WynnBET"),
    ]

    for key, title in bookmakers:
        cursor.execute(
            """
            INSERT INTO odds.bookmakers (bookmaker_key, bookmaker_title)
            VALUES (%s, %s)
            ON CONFLICT (bookmaker_key) DO NOTHING
        """,
            (key, title),
        )
    print(f"   ✓ Inserted {len(bookmakers)} bookmakers")
    print()

    # Insert common market types
    print("9. Inserting common market types...")
    markets = [
        ("h2h", "Head to Head (Moneyline)"),
        ("spreads", "Spreads"),
        ("totals", "Totals (Over/Under)"),
        ("h2h_q1", "Q1 Moneyline"),
        ("h2h_q2", "Q2 Moneyline"),
        ("h2h_q3", "Q3 Moneyline"),
        ("h2h_q4", "Q4 Moneyline"),
        ("h2h_h1", "First Half Moneyline"),
        ("h2h_h2", "Second Half Moneyline"),
    ]

    for key, name in markets:
        cursor.execute(
            """
            INSERT INTO odds.market_types (market_key, market_name)
            VALUES (%s, %s)
            ON CONFLICT (market_key) DO NOTHING
        """,
            (key, name),
        )
    print(f"   ✓ Inserted {len(markets)} market types")
    print()

    conn.commit()
    print("=" * 70)
    print("✅ ODDS SCHEMA INITIALIZATION COMPLETE")
    print("=" * 70)
    print()


def verify_schema(conn):
    """Verify schema was created successfully."""
    cursor = conn.cursor()

    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print()

    # Check schema exists
    cursor.execute(
        """
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = 'odds'
    """
    )
    if cursor.fetchone():
        print("✓ odds schema exists")
    else:
        print("✗ odds schema NOT found")
        return False

    # Check tables
    cursor.execute(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'odds'
        ORDER BY table_name
    """
    )
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        "events",
        "bookmakers",
        "market_types",
        "odds_snapshots",
        "scores",
    ]

    print(f"\nTables found ({len(tables)}):")
    for table in tables:
        if table in expected_tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ? {table} (unexpected)")

    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"\n✗ Missing tables: {', '.join(missing)}")
        return False

    # Check row counts
    print("\nRow counts:")
    for table in tables:
        # Table names come from information_schema, not user input - safe
        cursor.execute(f"SELECT COUNT(*) FROM odds.{table}")  # nosec B608
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count:,} rows")

    print()
    print("=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)
    print()

    return True


def main():
    """Main execution."""
    print()
    print("=" * 70)
    print("ODDS SCHEMA INITIALIZATION")
    print("Database:", DB_CONFIG["host"], "/", DB_CONFIG["database"])
    print("=" * 70)
    print()

    try:
        # Connect to database
        print("Connecting to RDS PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected successfully")
        print()

        # Create schema and tables
        create_odds_schema(conn)

        # Verify
        if verify_schema(conn):
            print("🎉 Database initialization successful!")
            print()
            print("Next steps:")
            print("  1. Run odds-api scraper: python scripts/run_scraper.py")
            print("  2. Verify data collection")
            print("  3. Create Phase 0.0007 validator")
            return 0
        else:
            print("⚠️  Verification failed - check output above")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
