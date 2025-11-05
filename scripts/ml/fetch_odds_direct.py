#!/usr/bin/env python3
"""
Direct fetch script for betting odds from The Odds API.

Fetches odds directly from The Odds API and stores them using synchronous psycopg2.
This is a fallback when the async odds-api scraper isn't working.

Usage:
    python scripts/ml/fetch_odds_direct.py
    python scripts/ml/fetch_odds_direct.py --date 2025-11-03
"""

import argparse
import os
import sys
import requests
import psycopg2
from datetime import datetime, date
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

# The Odds API configuration
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"
REGIONS = "us"
MARKETS = "h2h,spreads,totals"
MARKETS_WITH_PROPS = "h2h,spreads,totals,player_points,player_assists,player_rebounds,player_threes,player_points_rebounds,player_points_assists,player_points_rebounds_assists,player_steals,player_blocks,player_double_double,player_triple_double"
ODDS_FORMAT = "american"


def get_odds_api_key() -> Optional[str]:
    """Get The Odds API key from environment or centralized secrets."""
    # Try multiple possible env var names
    api_key = (
        os.getenv("ODDS_API_KEY")
        or os.getenv("ODDS_API_KEY_ODDS_API_WORKFLOW")
        or os.getenv("THE_ODDS_API_KEY")
    )

    # If not found, try to load from centralized secrets manager
    if not api_key:
        try:
            # Try to load from the centralized secrets path used by odds-api
            secrets_path = "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/odds-api/.env.odds_api.production/ODDS_API_KEY_ODDS_API_WORKFLOW.env"
            if os.path.exists(secrets_path):
                with open(secrets_path, "r") as f:
                    api_key = f.read().strip()
                    if api_key:
                        os.environ["ODDS_API_KEY"] = api_key
        except Exception as e:
            pass  # Silently fail and return None

    return api_key


def fetch_odds_from_api(
    api_key: str, include_player_props: bool = False
) -> Optional[List[Dict]]:
    """Fetch current NBA odds from The Odds API."""
    url = f"{ODDS_API_BASE}/sports/{SPORT}/odds"
    markets_to_use = MARKETS_WITH_PROPS if include_player_props else MARKETS
    params = {
        "apiKey": api_key,
        "regions": REGIONS,
        "markets": markets_to_use,
        "oddsFormat": ODDS_FORMAT,
    }

    print(f"Fetching odds from The Odds API...")
    print(f"URL: {url}")

    try:
        response = requests.get(url, params=params, timeout=30)

        # Check rate limits
        remaining = response.headers.get("x-requests-remaining", "unknown")
        used = response.headers.get("x-requests-used", "unknown")

        print(f"\n📊 API Usage:")
        print(f"  Requests used: {used}")
        print(f"  Requests remaining: {remaining}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success: {len(data)} games with odds")
            return data
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return None


def get_or_create_bookmaker(
    conn, cursor, bookmaker_key: str, bookmaker_title: str
) -> int:
    """Get or create bookmaker and return bookmaker_id."""
    cursor.execute(
        """
        SELECT bookmaker_id FROM odds.bookmakers
        WHERE bookmaker_key = %s
        """,
        (bookmaker_key,),
    )
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        cursor.execute(
            """
            INSERT INTO odds.bookmakers (bookmaker_key, bookmaker_title)
            VALUES (%s, %s)
            RETURNING bookmaker_id
            """,
            (bookmaker_key, bookmaker_title),
        )
        return cursor.fetchone()[0]


def get_or_create_market_type(conn, cursor, market_key: str, market_name: str) -> int:
    """Get or create market type and return market_type_id."""
    cursor.execute(
        """
        SELECT market_type_id FROM odds.market_types
        WHERE market_key = %s
        """,
        (market_key,),
    )
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        cursor.execute(
            """
            INSERT INTO odds.market_types (market_key, market_name)
            VALUES (%s, %s)
            RETURNING market_type_id
            """,
            (market_key, market_name),
        )
        return cursor.fetchone()[0]


def store_odds_data(
    conn,
    odds_data: List[Dict],
    target_date: Optional[date] = None,
    include_player_props: bool = False,
):
    """Store odds data in database."""
    cursor = conn.cursor()

    events_stored = 0
    odds_stored = 0

    print(f"\nStoring odds data...")

    for event in odds_data:
        event_id = event.get("id")
        commence_time = datetime.fromisoformat(
            event["commence_time"].replace("Z", "+00:00")
        )

        # Filter by date if specified (check both UTC date and CT date)
        if target_date:
            commence_date_utc = commence_time.date()
            # Convert to Chicago timezone for date comparison
            from pytz import timezone

            chicago_tz = timezone("America/Chicago")
            commence_time_ct = commence_time.astimezone(chicago_tz)
            commence_date_ct = commence_time_ct.date()

            if commence_date_utc != target_date and commence_date_ct != target_date:
                continue

        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")

        # Store or update event
        cursor.execute(
            """
            INSERT INTO odds.events (event_id, sport_key, sport_title, commence_time, home_team, away_team)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE
            SET updated_at = CURRENT_TIMESTAMP
            """,
            (event_id, SPORT, "NBA", commence_time, home_team, away_team),
        )

        events_stored += 1

        # Mark old snapshots as not latest
        cursor.execute(
            """
            UPDATE odds.odds_snapshots
            SET is_latest = FALSE
            WHERE event_id = %s
            """,
            (event_id,),
        )

        # Store odds for each bookmaker
        for bookmaker in event.get("bookmakers", []):
            bookmaker_key = bookmaker.get("key", "")
            bookmaker_title = bookmaker.get("title", bookmaker_key)

            bookmaker_id = get_or_create_bookmaker(
                conn, cursor, bookmaker_key, bookmaker_title
            )

            # Store odds for each market
            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")
                market_name = market.get("last_update", "")

                # Skip markets we don't want (only if not including player props)
                if not include_player_props and market_key not in [
                    "h2h",
                    "spreads",
                    "totals",
                ]:
                    continue

                market_type_id = get_or_create_market_type(
                    conn, cursor, market_key, market_name or market_key
                )

                # Store outcomes
                for outcome in market.get("outcomes", []):
                    outcome_name = outcome.get("name", "")
                    price = outcome.get("price")
                    point = outcome.get("point")

                    if price is None:
                        continue

                    last_update = market.get("last_update")
                    if last_update:
                        last_update_dt = datetime.fromisoformat(
                            last_update.replace("Z", "+00:00")
                        )
                    else:
                        last_update_dt = datetime.now()

                    # Insert odds snapshot
                    cursor.execute(
                        """
                        INSERT INTO odds.odds_snapshots
                        (event_id, bookmaker_id, market_type_id, outcome_name, price, point, last_update, is_latest)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                        """,
                        (
                            event_id,
                            bookmaker_id,
                            market_type_id,
                            outcome_name,
                            price,
                            point,
                            last_update_dt,
                        ),
                    )

                    odds_stored += 1

    conn.commit()

    print(f"  ✓ Stored {events_stored} events")
    print(f"  ✓ Stored {odds_stored} odds snapshots")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch odds directly from The Odds API"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date (YYYY-MM-DD). If not specified, fetches all upcoming games.",
    )
    parser.add_argument(
        "--include-player-props",
        action="store_true",
        default=False,
        help="Include player props in fetch (default: False)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("DIRECT ODDS FETCH - THE ODDS API")
    print("=" * 80)
    print()

    # Get API key
    api_key = get_odds_api_key()
    if not api_key:
        print("❌ ODDS_API_KEY not found in environment variables")
        print("   Set ODDS_API_KEY in /Users/ryanranft/nba-sim-credentials.env")
        sys.exit(1)

    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            print(f"Target date: {target_date}")
        except ValueError:
            print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        print("Fetching all upcoming games...")

    # Fetch odds
    odds_data = fetch_odds_from_api(
        api_key, include_player_props=args.include_player_props
    )
    if not odds_data:
        print("❌ Failed to fetch odds")
        sys.exit(1)

    # Connect to database
    print("\nConnecting to database...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432),
            sslmode="require",
        )
        print("✓ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    try:
        # Store odds
        store_odds_data(
            conn, odds_data, target_date, include_player_props=args.include_player_props
        )

        print("\n" + "=" * 80)
        print("✅ ODDS FETCH COMPLETE")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
