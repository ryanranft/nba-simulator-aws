#!/usr/bin/env python3
"""
Populate Test Snapshot Data

Creates minimal test data in game_state_snapshots and player_snapshot_stats
for testing the plus/minus system without running full Phase 9 processors.

Created: October 19, 2025
Purpose: Enable plus/minus system testing with synthetic snapshot data
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load RDS credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'nba_simulator'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', 5432))
}

def create_test_game_data(conn, game_id, num_events=200):
    """
    Create test game with realistic snapshot progression.

    Args:
        conn: Database connection
        game_id: Game identifier
        num_events: Number of events to simulate

    Returns:
        Number of snapshots created
    """
    cursor = conn.cursor()

    print(f"  Creating test game: {game_id}")
    print(f"    Events: {num_events}")

    # Sample roster for each team (5 starters + 2 bench)
    home_players = [
        ('tatumja01', 'Jayson Tatum'),
        ('brownja02', 'Jaylen Brown'),
        ('smartma01', 'Marcus Smart'),
        ('horfoal01', 'Al Horford'),
        ('williro01', 'Robert Williams'),
        ('whitede01', 'Derrick White'),
        ('pritcpa01', 'Payton Pritchard')
    ]

    away_players = [
        ('jamesle01', 'LeBron James'),
        ('davisan02', 'Anthony Davis'),
        ('westbru01', 'Russell Westbrook'),
        ('reaveau01', 'Austin Reaves'),
        ('walkelo01', 'Lonnie Walker'),
        ('schrodn01', 'Dennis Schroder'),
        ('beaslma01', 'Malik Beasley')
    ]

    # Track cumulative stats
    home_score = 0
    away_score = 0

    player_stats = {}
    for player_id, player_name in home_players + away_players:
        player_stats[player_id] = {
            'name': player_name,
            'team': 'BOS' if player_id in [p[0] for p in home_players] else 'LAL',
            'points': 0,
            'fgm': 0,
            'fga': 0,
            'fg3m': 0,
            'fg3a': 0,
            'ftm': 0,
            'fta': 0,
            'reb': 0,
            'ast': 0,
            'stl': 0,
            'blk': 0,
            'tov': 0,
            'pf': 0,
            'minutes': 0.0,
            'on_court': False
        }

    # Set starters on court
    for player_id, _ in home_players[:5] + away_players[:5]:
        player_stats[player_id]['on_court'] = True

    snapshot_count = 0

    # Create events with realistic progression
    for event_num in range(num_events):
        quarter = (event_num // 50) + 1  # 50 events per quarter
        event_in_quarter = event_num % 50
        game_clock_seconds = event_num * 15  # ~15 seconds per event avg

        # Randomly update score (simplified)
        if event_num % 5 == 0:  # Score every ~5 events
            scoring_team = 'home' if event_num % 10 < 5 else 'away'
            points = 2 if event_num % 7 != 0 else 3  # Mostly 2s, some 3s

            if scoring_team == 'home':
                home_score += points
                # Award points to random on-court home player
                scorers = [p for p in home_players[:5] if player_stats[p[0]]['on_court']]
                if scorers:
                    scorer = scorers[event_num % len(scorers)]
                    player_stats[scorer[0]]['points'] += points
                    player_stats[scorer[0]]['fgm'] += 1
                    player_stats[scorer[0]]['fga'] += 1
                    if points == 3:
                        player_stats[scorer[0]]['fg3m'] += 1
                        player_stats[scorer[0]]['fg3a'] += 1
            else:
                away_score += points
                scorers = [p for p in away_players[:5] if player_stats[p[0]]['on_court']]
                if scorers:
                    scorer = scorers[event_num % len(scorers)]
                    player_stats[scorer[0]]['points'] += points
                    player_stats[scorer[0]]['fgm'] += 1
                    player_stats[scorer[0]]['fga'] += 1
                    if points == 3:
                        player_stats[scorer[0]]['fg3m'] += 1
                        player_stats[scorer[0]]['fg3a'] += 1

        # Randomly accumulate other stats
        if event_num % 8 == 0:  # Rebound
            all_oncourt = [(p[0], p[1]) for p in home_players + away_players
                          if player_stats[p[0]]['on_court']]
            if all_oncourt:
                rebounder = all_oncourt[event_num % len(all_oncourt)]
                player_stats[rebounder[0]]['reb'] += 1

        if event_num % 12 == 0:  # Assist
            all_oncourt = [(p[0], p[1]) for p in home_players + away_players
                          if player_stats[p[0]]['on_court']]
            if all_oncourt:
                assister = all_oncourt[event_num % len(all_oncourt)]
                player_stats[assister[0]]['ast'] += 1

        # Update minutes for on-court players
        for player_id in player_stats:
            if player_stats[player_id]['on_court']:
                player_stats[player_id]['minutes'] += 0.25  # ~15 sec = 0.25 min

        # Create game state snapshot
        cursor.execute("""
            INSERT INTO game_state_snapshots
            (game_id, event_num, quarter, game_clock_seconds,
             home_score, away_score, data_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING snapshot_id
        """, (game_id, event_num, quarter, game_clock_seconds,
              home_score, away_score, 'test_data'))

        snapshot_id = cursor.fetchone()[0]
        snapshot_count += 1

        # Create player snapshot stats for all players who have played
        for player_id, stats in player_stats.items():
            if stats['minutes'] > 0 or stats['on_court']:
                plus_minus = (home_score - away_score) if stats['team'] == 'BOS' else (away_score - home_score)

                cursor.execute("""
                    INSERT INTO player_snapshot_stats
                    (snapshot_id, player_id, player_name, team_id,
                     points, fgm, fga, fg3m, fg3a, ftm, fta,
                     reb, ast, stl, blk, tov, pf,
                     plus_minus, minutes, on_court)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (snapshot_id, player_id, stats['name'], stats['team'],
                      stats['points'], stats['fgm'], stats['fga'],
                      stats['fg3m'], stats['fg3a'], stats['ftm'], stats['fta'],
                      stats['reb'], stats['ast'], stats['stl'], stats['blk'],
                      stats['tov'], stats['pf'], plus_minus, stats['minutes'],
                      stats['on_court']))

        # Occasional substitution (every ~40 events)
        if event_num > 0 and event_num % 40 == 0:
            # Sub out a home player
            on_court_home = [p for p in home_players if player_stats[p[0]]['on_court']]
            off_court_home = [p for p in home_players if not player_stats[p[0]]['on_court']]

            if on_court_home and off_court_home:
                out_player = on_court_home[-1]  # Last in list
                in_player = off_court_home[0]   # First bench player

                player_stats[out_player[0]]['on_court'] = False
                player_stats[in_player[0]]['on_court'] = True

    conn.commit()
    print(f"    ✅ Created {snapshot_count} snapshots")

    return snapshot_count

def main():
    """Create test data for plus/minus system testing"""
    print("=" * 70)
    print("POPULATING TEST SNAPSHOT DATA")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}\n")

    try:
        # Connect to RDS
        print("Connecting to RDS...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected\n")

        # Create 3 test games
        print("Creating test games:")
        print("-" * 70)

        game_ids = [
            ('0021500001', 200),  # 200 events (realistic)
            ('0021500002', 180),  # Shorter game
            ('0021500003', 220)   # Longer game
        ]

        total_snapshots = 0
        for game_id, num_events in game_ids:
            snapshots = create_test_game_data(conn, game_id, num_events)
            total_snapshots += snapshots

        print()
        print("=" * 70)
        print("✅ TEST DATA POPULATED SUCCESSFULLY")
        print("=" * 70)
        print(f"  Games created: {len(game_ids)}")
        print(f"  Total snapshots: {total_snapshots:,}")
        print()

        # Verify data
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM game_state_snapshots;")
        snapshot_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_snapshot_stats;")
        player_stat_count = cursor.fetchone()[0]

        print("Data Verification:")
        print("-" * 70)
        print(f"  game_state_snapshots: {snapshot_count:,} rows")
        print(f"  player_snapshot_stats: {player_stat_count:,} rows")
        print()
        print("Ready for plus/minus system testing!")
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
