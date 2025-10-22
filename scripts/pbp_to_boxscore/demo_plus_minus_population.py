#!/usr/bin/env python3
"""
Plus/Minus Population Demo & Test Script

Demonstrates populating plus/minus tables and validates performance improvements.

Created: October 19, 2025
"""

import sqlite3
import time
from populate_plus_minus_tables import PlusMinusPopulator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_plus_minus_tables(db_path: str):
    """Create plus/minus tables in SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("Creating plus/minus tables...")

    # Read and execute SQL files
    sql_files = [
        '../../../sql/plus_minus/01_create_lineup_snapshots.sql',
        '../../../sql/plus_minus/02_create_player_plus_minus_snapshots.sql',
        '../../../sql/plus_minus/03_create_possession_metadata.sql',
        '../../../sql/plus_minus/vw_lineup_plus_minus.sql',
        '../../../sql/plus_minus/vw_on_off_analysis.sql'
    ]

    for sql_file in sql_files:
        try:
            with open(sql_file, 'r') as f:
                sql = f.read()
                # Split by statement and execute
                for statement in sql.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        # Remove comments
                        lines = [line for line in statement.split('\n')
                                if not line.strip().startswith('--')]
                        clean_statement = '\n'.join(lines)
                        if clean_statement.strip():
                            try:
                                cursor.execute(clean_statement)
                            except sqlite3.Error as e:
                                # Ignore "table already exists" errors
                                if 'already exists' not in str(e):
                                    logger.warning(f"SQL error: {e}")
            logger.info(f"  Loaded {sql_file}")
        except FileNotFoundError:
            logger.warning(f"  File not found: {sql_file}")
        except Exception as e:
            logger.error(f"  Error loading {sql_file}: {e}")

    conn.commit()
    conn.close()
    logger.info("✅ Plus/minus tables created")


def get_sample_games(db_path: str, limit: int = 3) -> list:
    """Get sample game IDs that have snapshot data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT g.game_id, COUNT(*) as snapshot_count
        FROM game_state_snapshots g
        JOIN player_snapshot_stats p ON g.snapshot_id = p.snapshot_id
        GROUP BY g.game_id
        HAVING snapshot_count > 100
        ORDER BY snapshot_count DESC
        LIMIT ?
    """

    cursor.execute(query, (limit,))
    games = [row[0] for row in cursor.fetchall()]

    conn.close()
    return games


def test_view_performance(db_path: str, game_id: str):
    """Test optimized view performance"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("\n" + "="*60)
    logger.info("TESTING VIEW PERFORMANCE")
    logger.info("="*60)

    # Test 1: vw_lineup_plus_minus
    logger.info("\n1. Testing vw_lineup_plus_minus...")
    start = time.time()
    cursor.execute("""
        SELECT
            lineup_display,
            possessions_played,
            net_rating,
            offensive_rating,
            defensive_rating
        FROM vw_lineup_plus_minus
        WHERE possessions_played >= 5
        ORDER BY net_rating DESC
        LIMIT 10
    """)
    results = cursor.fetchall()
    elapsed = time.time() - start

    logger.info(f"   Query time: {elapsed:.3f} seconds")
    logger.info(f"   Top lineups found: {len(results)}")
    if results:
        logger.info(f"   Best net rating: {results[0][2]}")

    # Test 2: vw_on_off_analysis
    logger.info("\n2. Testing vw_on_off_analysis...")
    start = time.time()
    cursor.execute("""
        SELECT
            player_name,
            net_rating_diff,
            possessions_on_court,
            possessions_off_court,
            confidence_level
        FROM vw_on_off_analysis
        WHERE confidence_level IN ('MEDIUM', 'HIGH')
        ORDER BY net_rating_diff DESC
        LIMIT 10
    """)
    results = cursor.fetchall()
    elapsed = time.time() - start

    logger.info(f"   Query time: {elapsed:.3f} seconds")
    logger.info(f"   Players with on/off data: {len(results)}")
    if results:
        logger.info(f"   Best on/off differential: {results[0][1]}")

    conn.close()


def validate_data_quality(db_path: str, game_id: str):
    """Run data quality checks"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("\n" + "="*60)
    logger.info("DATA QUALITY VALIDATION")
    logger.info("="*60)

    # Check 1: Lineup hash uniqueness
    logger.info("\n1. Checking lineup hash consistency...")
    cursor.execute("""
        SELECT COUNT(DISTINCT lineup_hash) as unique_lineups,
               COUNT(*) as total_snapshots
        FROM lineup_snapshots
        WHERE game_id = ?
    """, (game_id,))
    result = cursor.fetchone()
    logger.info(f"   Unique lineups: {result[0]}")
    logger.info(f"   Total snapshots: {result[1]}")

    # Check 2: Player count per event
    logger.info("\n2. Checking player counts per event...")
    cursor.execute("""
        SELECT event_number, COUNT(*) as player_count
        FROM player_plus_minus_snapshots
        WHERE game_id = ? AND on_court = 1
        GROUP BY event_number
        HAVING player_count != 10
        LIMIT 5
    """, (game_id,))
    invalid_events = cursor.fetchall()
    if invalid_events:
        logger.warning(f"   Found {len(invalid_events)} events with != 10 on-court players")
    else:
        logger.info("   ✅ All events have exactly 10 on-court players")

    # Check 3: Plus/minus consistency
    logger.info("\n3. Checking plus/minus calculations...")
    cursor.execute("""
        SELECT COUNT(*) as violations
        FROM player_plus_minus_snapshots
        WHERE plus_minus != (team_score - opponent_score)
        AND game_id = ?
    """, (game_id,))
    violations = cursor.fetchone()[0]
    if violations > 0:
        logger.warning(f"   Found {violations} plus/minus calculation errors")
    else:
        logger.info("   ✅ All plus/minus calculations correct")

    # Check 4: Possession count
    logger.info("\n4. Checking possession metadata...")
    cursor.execute("""
        SELECT COUNT(*) as possession_count,
               MIN(possession_number) as min_poss,
               MAX(possession_number) as max_poss
        FROM possession_metadata
        WHERE game_id = ?
    """, (game_id,))
    result = cursor.fetchone()
    logger.info(f"   Total possessions: {result[0]}")
    logger.info(f"   Range: {result[1]} - {result[2]}")

    conn.close()


def show_sample_queries(db_path: str, game_id: str):
    """Demonstrate sample plus/minus queries"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("\n" + "="*60)
    logger.info("SAMPLE PLUS/MINUS QUERIES")
    logger.info("="*60)

    # Query 1: Best lineups
    logger.info("\n1. Best Lineups by Net Rating:")
    cursor.execute("""
        SELECT
            lineup_display,
            possessions_played,
            net_rating,
            offensive_rating,
            defensive_rating
        FROM vw_lineup_plus_minus
        WHERE possessions_played >= 5
        ORDER BY net_rating DESC
        LIMIT 5
    """)
    results = cursor.fetchall()
    for i, row in enumerate(results, 1):
        logger.info(f"   {i}. {row[0][:50]}...")
        logger.info(f"      Possessions: {row[1]}, Net: {row[2]}, Off: {row[3]}, Def: {row[4]}")

    # Query 2: Top player impact
    logger.info("\n2. Highest Impact Players (On/Off Differential):")
    cursor.execute("""
        SELECT
            player_name,
            net_rating_diff,
            replacement_value_48min,
            possessions_on_court,
            confidence_level
        FROM vw_on_off_analysis
        WHERE confidence_level IN ('MEDIUM', 'HIGH')
        ORDER BY net_rating_diff DESC
        LIMIT 5
    """)
    results = cursor.fetchall()
    for i, row in enumerate(results, 1):
        logger.info(f"   {i}. {row[0]}")
        logger.info(f"      Net Rating Diff: {row[1]}, Replacement Value: {row[2]}")
        logger.info(f"      Possessions: {row[3]}, Confidence: {row[4]}")

    # Query 3: Possession intervals
    logger.info("\n3. 25-Possession Interval Performance:")
    cursor.execute("""
        SELECT
            ((possession_number - 1) / 25) + 1 as interval,
            offensive_team_id,
            COUNT(*) as possessions,
            SUM(points_scored) as points,
            ROUND(SUM(points_scored) * 100.0 / COUNT(*), 1) as offensive_rating
        FROM possession_metadata
        WHERE game_id = ?
        GROUP BY interval, offensive_team_id
        ORDER BY interval, offensive_team_id
        LIMIT 10
    """, (game_id,))
    results = cursor.fetchall()
    for row in results:
        logger.info(f"   Interval {row[0]} - {row[1]}: {row[2]} poss, {row[3]} pts, {row[4]} ORtg")

    conn.close()


def main():
    """Main demo execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Plus/Minus Population Demo")
    parser.add_argument('--database', default='nba.db', help='SQLite database path')
    parser.add_argument('--create-tables', action='store_true', help='Create plus/minus tables')
    parser.add_argument('--populate', action='store_true', help='Populate tables with data')
    parser.add_argument('--test', action='store_true', help='Test views and performance')
    parser.add_argument('--game-id', help='Specific game ID to process')
    parser.add_argument('--num-games', type=int, default=3, help='Number of games to process')

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("PLUS/MINUS SYSTEM POPULATION DEMO")
    logger.info("="*60)

    # Create tables if requested
    if args.create_tables:
        create_plus_minus_tables(args.database)

    # Get sample games
    if args.game_id:
        game_ids = [args.game_id]
    else:
        logger.info(f"\nFinding {args.num_games} sample games with snapshot data...")
        game_ids = get_sample_games(args.database, args.num_games)
        if not game_ids:
            logger.error("No games found with snapshot data!")
            return
        logger.info(f"Found games: {', '.join(game_ids)}")

    # Populate tables if requested
    if args.populate:
        logger.info("\n" + "="*60)
        logger.info("POPULATING PLUS/MINUS TABLES")
        logger.info("="*60)

        populator = PlusMinusPopulator({'database': args.database}, use_postgres=False)
        try:
            results = populator.populate_multiple_games(game_ids)

            logger.info("\n📊 Population Summary:")
            total_lineups = sum(r.get('lineups', 0) for r in results.values() if 'error' not in r)
            total_player = sum(r.get('player_pm', 0) for r in results.values() if 'error' not in r)
            total_poss = sum(r.get('possessions', 0) for r in results.values() if 'error' not in r)

            logger.info(f"   Games processed: {len(game_ids)}")
            logger.info(f"   Lineup snapshots: {total_lineups}")
            logger.info(f"   Player +/- records: {total_player}")
            logger.info(f"   Possessions tracked: {total_poss}")
        finally:
            populator.close()

    # Test performance if requested
    if args.test and game_ids:
        test_view_performance(args.database, game_ids[0])
        validate_data_quality(args.database, game_ids[0])
        show_sample_queries(args.database, game_ids[0])

    logger.info("\n" + "="*60)
    logger.info("✅ DEMO COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()