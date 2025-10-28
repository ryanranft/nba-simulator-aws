#!/usr/bin/env python3
"""
Fetch all betting odds for October 28, 2025 from RDS PostgreSQL odds schema.

This script queries the odds database to retrieve:
- All games scheduled for October 28, 2025
- All betting markets (moneylines, spreads, totals, props)
- Odds from all available bookmakers
- Latest odds snapshots

Usage:
    python scripts/betting/fetch_todays_odds.py --date 2025-10-28
    python scripts/betting/fetch_todays_odds.py --date 2025-10-28 --output data/betting/odds_2025-10-28.json
"""

import os
import sys
import json
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load credentials
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


def fetch_games_for_date(conn, target_date: date) -> List[Dict[str, Any]]:
    """Fetch all games scheduled for the target date."""
    query = """
        SELECT
            event_id,
            sport_key,
            sport_title,
            commence_time,
            home_team,
            away_team,
            created_at,
            updated_at
        FROM odds.events
        WHERE commence_time::date = %s
        ORDER BY commence_time
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (target_date,))
        games = cursor.fetchall()
        return [dict(game) for game in games]


def fetch_odds_for_game(conn, event_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch all odds for a specific game, organized by market type."""
    query = """
        SELECT
            os.snapshot_id,
            os.event_id,
            b.bookmaker_key,
            b.bookmaker_title,
            mt.market_key,
            mt.market_name,
            os.outcome_name,
            os.price,
            os.point,
            os.last_update,
            os.fetched_at,
            os.is_latest
        FROM odds.odds_snapshots os
        JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
        JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
        WHERE os.event_id = %s
          AND os.is_latest = TRUE
        ORDER BY mt.market_key, b.bookmaker_key, os.outcome_name
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (event_id,))
        odds_data = cursor.fetchall()
        
        # Organize by market type
        markets = {}
        for row in odds_data:
            row_dict = dict(row)
            market_key = row_dict['market_key']
            
            if market_key not in markets:
                markets[market_key] = {
                    'market_name': row_dict['market_name'],
                    'bookmakers': {}
                }
            
            bookmaker = row_dict['bookmaker_key']
            if bookmaker not in markets[market_key]['bookmakers']:
                markets[market_key]['bookmakers'][bookmaker] = {
                    'bookmaker_title': row_dict['bookmaker_title'],
                    'outcomes': []
                }
            
            markets[market_key]['bookmakers'][bookmaker]['outcomes'].append({
                'outcome_name': row_dict['outcome_name'],
                'price': float(row_dict['price']) if row_dict['price'] else None,
                'point': float(row_dict['point']) if row_dict['point'] else None,
                'last_update': row_dict['last_update'].isoformat() if row_dict['last_update'] else None,
            })
        
        return markets


def calculate_market_consensus(markets: Dict) -> Dict[str, Any]:
    """Calculate consensus odds across all bookmakers."""
    consensus = {}
    
    for market_key, market_data in markets.items():
        if market_key not in ['h2h', 'spreads', 'totals']:
            continue
            
        # Aggregate across bookmakers
        outcomes = {}
        for bookmaker, bookie_data in market_data['bookmakers'].items():
            for outcome in bookie_data['outcomes']:
                outcome_name = outcome['outcome_name']
                if outcome_name not in outcomes:
                    outcomes[outcome_name] = {
                        'prices': [],
                        'points': []
                    }
                if outcome['price'] is not None:
                    outcomes[outcome_name]['prices'].append(outcome['price'])
                if outcome['point'] is not None:
                    outcomes[outcome_name]['points'].append(outcome['point'])
        
        # Calculate averages
        consensus[market_key] = {}
        for outcome_name, data in outcomes.items():
            consensus[market_key][outcome_name] = {
                'avg_price': sum(data['prices']) / len(data['prices']) if data['prices'] else None,
                'avg_point': sum(data['points']) / len(data['points']) if data['points'] else None,
                'num_bookmakers': len(data['prices']),
            }
    
    return consensus


def fetch_all_odds_for_date(target_date: date) -> Dict[str, Any]:
    """Fetch all games and odds for the target date."""
    print(f"\n{'='*70}")
    print(f"FETCHING ODDS FOR {target_date}")
    print(f"{'='*70}\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # Fetch games
        print("1. Fetching games from database...")
        games = fetch_games_for_date(conn, target_date)
        print(f"   ✓ Found {len(games)} games\n")
        
        if not games:
            print(f"⚠️  No games found for {target_date}")
            print("   This could mean:")
            print("   - No games scheduled for this date")
            print("   - odds-api scraper hasn't run yet")
            print("   - Database connection issue\n")
            return {"date": str(target_date), "games": [], "total_games": 0}
        
        # Fetch odds for each game
        print("2. Fetching odds for each game...")
        games_with_odds = []
        
        for i, game in enumerate(games, 1):
            print(f"   [{i}/{len(games)}] {game['away_team']} @ {game['home_team']}")
            
            markets = fetch_odds_for_game(conn, game['event_id'])
            consensus = calculate_market_consensus(markets)
            
            games_with_odds.append({
                'event_id': game['event_id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'commence_time': game['commence_time'].isoformat(),
                'markets': markets,
                'consensus': consensus,
            })
            
            # Print market summary
            print(f"       Markets: {', '.join(markets.keys())}")
            print(f"       Bookmakers: {len(set(b for m in markets.values() for b in m['bookmakers'].keys()))}")
        
        print(f"\n   ✓ Fetched odds for all {len(games)} games\n")
        
        # Summary statistics
        total_markets = sum(len(g['markets']) for g in games_with_odds)
        unique_bookmakers = set()
        for game in games_with_odds:
            for market in game['markets'].values():
                unique_bookmakers.update(market['bookmakers'].keys())
        
        result = {
            'date': str(target_date),
            'fetched_at': datetime.now().isoformat(),
            'total_games': len(games_with_odds),
            'total_markets': total_markets,
            'unique_bookmakers': sorted(list(unique_bookmakers)),
            'games': games_with_odds,
        }
        
        print(f"{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Date: {target_date}")
        print(f"Games: {result['total_games']}")
        print(f"Markets: {result['total_markets']}")
        print(f"Bookmakers: {len(result['unique_bookmakers'])}")
        print(f"{'='*70}\n")
        
        return result
        
    finally:
        conn.close()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Fetch betting odds for NBA games"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2025-10-28",
        help="Date to fetch odds for (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ Invalid date format: {args.date}")
        print("   Use YYYY-MM-DD format (e.g., 2025-10-28)")
        return 1
    
    # Fetch odds
    try:
        result = fetch_all_odds_for_date(target_date)
        
        # Save to file
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(f"data/betting/odds_{args.date}.json")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"✅ Odds data saved to: {output_path}\n")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

