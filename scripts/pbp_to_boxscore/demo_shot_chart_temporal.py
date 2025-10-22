#!/usr/bin/env python3
"""
Demo: Shot Chart Temporal Integration

Creates sample shot data and demonstrates spatial + temporal basketball analytics.

This shows how linking shot charts to temporal snapshots enables queries like:
- "Show LeBron's shot chart in Q4 clutch moments"
- "Where did Curry shoot from when trailing by 5+?"
- "How did Kobe's shot selection change by quarter?"

Created: October 18, 2025
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_shot_data(conn):
    """Create sample shot events with coordinates"""
    cursor = conn.cursor()

    game_id = "202406060BOS"

    # Sample shots with realistic coordinates
    # Court: 50 feet wide (0-50), 47 feet long (0-47)
    # Basket at (25, 5.25)
    sample_shots = [
        # Q1 - Tatum hot start
        (game_id, 2, '11:45', 'Jayson Tatum', 'BOS', 1, '2PT', True, 23, 25, 20, 0, 3),
        (game_id, 5, '11:00', 'Jayson Tatum', 'BOS', 1, '2PT', True, 8, 28, 10, 2, 5),
        (game_id, 8, '10:15', 'Jayson Tatum', 'BOS', 1, '3PT', False, 26, 25, 28, 4, 5),

        # Q1 - Butler response
        (game_id, 3, '11:30', 'Jimmy Butler', 'MIA', 1, '2PT', True, 4, 25, 7, 0, 0),
        (game_id, 10, '9:45', 'Jimmy Butler', 'MIA', 1, '3PT', True, 24, 25, 25, 2, 2),

        # Q2 - Brown gets going
        (game_id, 14, '11:45', 'Jaylen Brown', 'BOS', 2, '3PT', True, 25, 7, 23, 25, 28),
        (game_id, 16, '11:30', 'Jaylen Brown', 'BOS', 2, '2PT', True, 6, 22, 9, 25, 31),

        # Q3 - Mid-range battle
        (game_id, 25, '6:00', 'Jayson Tatum', 'BOS', 3, '2PT', True, 15, 30, 18, 70, 80),
        (game_id, 26, '5:45', 'Bam Adebayo', 'MIA', 3, '2PT', False, 12, 25, 15, 70, 80),

        # Q4 - Clutch time
        (game_id, 35, '4:30', 'Jayson Tatum', 'BOS', 4, '2PT', True, 10, 25, 12, 95, 98),
        (game_id, 37, '4:00', 'Jimmy Butler', 'MIA', 4, '3PT', True, 25, 7, 22, 95, 100),
        (game_id, 40, '3:30', 'Jaylen Brown', 'BOS', 4, 'FT', True, 0, 25, 15, 98, 100),
        (game_id, 41, '3:29', 'Jaylen Brown', 'BOS', 4, 'FT', True, 0, 25, 15, 98, 100),
        (game_id, 44, '1:00', 'Jayson Tatum', 'BOS', 4, '2PT', True, 8, 27, 10, 98, 102),
        (game_id, 47, '0:30', 'Jimmy Butler', 'MIA', 4, '2PT', True, 5, 25, 8, 98, 104),
        (game_id, 49, '0:10', 'Jaylen Brown', 'BOS', 4, 'FT', True, 0, 25, 15, 100, 104),
        (game_id, 50, '0:09', 'Jaylen Brown', 'BOS', 4, 'FT', True, 0, 25, 15, 100, 104),
    ]

    # First, ensure the games table has this game
    cursor.execute("""
        INSERT OR IGNORE INTO games (game_id, game_date, season, home_team, away_team, home_score, away_score)
        VALUES (?, '2024-06-06', 2024, 'BOS', 'MIA', 106, 100)
    """, (game_id,))

    # Insert shots into game_play_by_play
    for shot in sample_shots:
        (gid, event_num, time_rem, player, team, quarter, shot_type, made,
         distance, shot_x, shot_y, away_score, home_score) = shot

        # Determine offensive/defensive teams
        offensive_team = team
        defensive_team = 'MIA' if team == 'BOS' else 'BOS'

        cursor.execute("""
            INSERT OR REPLACE INTO game_play_by_play (
                game_id, event_number, quarter, time_remaining,
                event_type, description, primary_player,
                offensive_team, defensive_team,
                home_score, away_score,
                shot_made, shot_type, shot_distance, shot_x, shot_y
            ) VALUES (?, ?, ?, ?, 'shot', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gid, event_num, quarter, time_rem,
            f"{player} {'makes' if made else 'misses'} {shot_type}",
            player, offensive_team, defensive_team,
            home_score, away_score,
            made, shot_type, distance, shot_x, shot_y
        ))

    conn.commit()
    logger.info(f"✓ Created {len(sample_shots)} sample shot events")
    logger.info(f"  Game: {game_id}")
    logger.info(f"  Shot types: 2PT, 3PT, FT")
    logger.info(f"  Includes coordinates for shot charts")


def create_sample_temporal_data(conn):
    """Create minimal temporal snapshot data for shot linking"""
    cursor = conn.cursor()

    game_id = "202406060BOS"

    # Create player snapshots (simplified for demo)
    # Use full name as player_id to match what's in game_play_by_play
    players = [
        ('Jayson Tatum', 'BOS'),
        ('Jaylen Brown', 'BOS'),
        ('Jimmy Butler', 'MIA'),
        ('Bam Adebayo', 'MIA'),
    ]

    event_numbers = [2, 3, 5, 8, 10, 14, 16, 25, 26, 35, 37, 40, 41, 44, 47, 49, 50]

    for event_num in event_numbers:
        for player_name, team in players:
            # Simplified player stats (normally from SQLitePBPProcessor)
            cursor.execute("""
                INSERT OR IGNORE INTO player_box_score_snapshots (
                    game_id, event_number, player_id, player_name, team_id,
                    period, points, fgm, fga, fg_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id, event_num, player_name,  # Use full name as ID
                player_name, team,
                (event_num // 15) + 1,  # Rough quarter approximation
                event_num * 2, event_num, event_num * 2, 50.0
            ))

        # Team snapshots
        for team, is_home in [('BOS', True), ('MIA', False)]:
            cursor.execute("""
                INSERT OR IGNORE INTO team_box_score_snapshots (
                    game_id, event_number, team_id, is_home,
                    period, points, fgm, fga, score_diff, is_leading
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id, event_num, team, is_home,
                (event_num // 15) + 1,
                event_num * 3, event_num * 2, event_num * 4,
                -2 if team == 'MIA' else 2,  # BOS leading by 2
                team == 'BOS'
            ))

    conn.commit()
    logger.info(f"✓ Created temporal snapshots for {len(event_numbers)} events")


def run_demo_queries(conn):
    """Run demo queries showing shot chart + temporal integration"""
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("DEMO QUERY 1: Player Shot Chart by Quarter")
    print("="*70)

    cursor.execute("""
        SELECT
            player_name,
            period as quarter,
            shot_zone,
            COUNT(*) as shots,
            SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes,
            ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
        FROM shot_event_snapshots
        WHERE game_id = '202406060BOS'
        AND player_name = 'Jayson Tatum'
        GROUP BY player_name, period, shot_zone
        ORDER BY period, shot_zone
    """)

    print("\nJayson Tatum's Shot Chart by Quarter:")
    print("Quarter | Zone          | Shots | Makes | FG%")
    print("-" * 55)
    for row in cursor.fetchall():
        player, quarter, zone, shots, makes, fg_pct = row
        print(f"Q{quarter:<6} | {zone:<13} | {shots:>5} | {makes:>5} | {fg_pct}%")

    print("\n" + "="*70)
    print("DEMO QUERY 2: Clutch Shot Chart (Q4, <5 min, Close Game)")
    print("="*70)

    cursor.execute("""
        SELECT
            player_name,
            shot_zone,
            shot_type,
            shot_x,
            shot_y,
            shot_made,
            score_diff
        FROM shot_event_snapshots
        WHERE game_id = '202406060BOS'
        AND is_clutch = 1
        ORDER BY event_number
    """)

    print("\nClutch Shots:")
    print("Player         | Zone       | Type | Location  | Made | Diff")
    print("-" * 65)
    for row in cursor.fetchall():
        player, zone, shot_type, x, y, made, diff = row
        made_str = "✓" if made else "✗"
        print(f"{player:<14} | {zone:<10} | {shot_type:<4} | ({x:>2},{y:>2})   | {made_str:>4} | {diff:+}")

    print("\n" + "="*70)
    print("DEMO QUERY 3: Shot Selection by Game State (Leading vs Trailing)")
    print("="*70)

    cursor.execute("""
        SELECT
            is_leading,
            shot_zone,
            COUNT(*) as shots,
            ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
        FROM shot_event_snapshots
        WHERE game_id = '202406060BOS'
        GROUP BY is_leading, shot_zone
        ORDER BY is_leading DESC, shots DESC
    """)

    print("\nShot Selection:")
    print("State    | Zone          | Shots | FG%")
    print("-" * 45)
    for row in cursor.fetchall():
        is_leading, zone, shots, fg_pct = row
        state = "Leading" if is_leading else "Trailing"
        print(f"{state:<8} | {zone:<13} | {shots:>5} | {fg_pct}%")

    print("\n" + "="*70)
    print("DEMO QUERY 4: Assisted vs Unassisted Efficiency")
    print("="*70)

    cursor.execute("""
        SELECT
            player_name,
            is_assisted,
            COUNT(*) as shots,
            SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes,
            ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
        FROM shot_event_snapshots
        WHERE game_id = '202406060BOS'
        AND shot_type != 'FT'
        GROUP BY player_name, is_assisted
        ORDER BY player_name, is_assisted DESC
    """)

    print("\nAssisted vs Unassisted:")
    print("Player         | Assisted? | Shots | Makes | FG%")
    print("-" * 55)
    for row in cursor.fetchall():
        player, assisted, shots, makes, fg_pct = row
        assisted_str = "Yes" if assisted else "No"
        print(f"{player:<14} | {assisted_str:<9} | {shots:>5} | {makes:>5} | {fg_pct}%")

    print("\n" + "="*70)
    print("DEMO QUERY 5: Shot Coordinates (for Visualization)")
    print("="*70)

    cursor.execute("""
        SELECT
            player_name,
            period,
            shot_x,
            shot_y,
            shot_distance,
            shot_made,
            shot_type
        FROM shot_event_snapshots
        WHERE game_id = '202406060BOS'
        ORDER BY period, event_number
        LIMIT 10
    """)

    print("\nShot Coordinates (first 10):")
    print("Player         | Q | X  | Y  | Dist | Made | Type")
    print("-" * 60)
    for row in cursor.fetchall():
        player, quarter, x, y, dist, made, shot_type = row
        made_str = "✓" if made else "✗"
        print(f"{player:<14} | {quarter} | {x:>2} | {y:>2} | {dist:>4} | {made_str:>4} | {shot_type}")

    print("\n" + "="*70)
    print("DEMO QUERY 6: Zone-Based Efficiency Summary")
    print("="*70)

    cursor.execute("""
        SELECT
            shot_zone,
            COUNT(*) as total_shots,
            SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes,
            ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct,
            AVG(shot_distance) as avg_distance
        FROM shot_event_snapshots
        WHERE game_id = '202406060BOS'
        AND shot_type != 'FT'
        GROUP BY shot_zone
        ORDER BY total_shots DESC
    """)

    print("\nZone Efficiency:")
    print("Zone          | Shots | Makes | FG%  | Avg Dist")
    print("-" * 55)
    for row in cursor.fetchall():
        zone, shots, makes, fg_pct, avg_dist = row
        print(f"{zone:<13} | {shots:>5} | {makes:>5} | {fg_pct:>4}% | {avg_dist:.1f} ft")


def main():
    """Run complete shot chart + temporal demo"""
    print("\n" + "="*70)
    print("SHOT CHART TEMPORAL INTEGRATION - DEMO")
    print("="*70)
    print("\nThis demo shows spatial + temporal basketball analytics:")
    print("  • Shot charts linked to game moments")
    print("  • Shot selection by game state (leading/trailing)")
    print("  • Clutch shooting analysis")
    print("  • Zone-based efficiency\n")

    # Connect to database
    conn = sqlite3.connect('/tmp/basketball_reference_boxscores.db')
    conn.row_factory = sqlite3.Row

    try:
        # Step 0: Create tables
        print("\n" + "="*70)
        print("STEP 0: Creating Shot Chart Tables")
        print("="*70 + "\n")

        with open('sql/shot_chart_temporal_integration.sql', 'r') as f:
            schema = f.read()
            conn.executescript(schema)
        logger.info("✓ Tables created")

        # Step 1: Create shot data
        print("\n" + "="*70)
        print("STEP 1: Creating Sample Shot Data")
        print("="*70 + "\n")
        create_sample_shot_data(conn)

        # Step 2: Create temporal data
        print("\n" + "="*70)
        print("STEP 2: Creating Temporal Snapshot Data")
        print("="*70 + "\n")
        create_sample_temporal_data(conn)

        # Step 3: Process shots
        print("\n" + "="*70)
        print("STEP 3: Linking Shots to Temporal Snapshots")
        print("="*70 + "\n")

        from shot_chart_temporal_processor import ShotChartTemporalProcessor

        processor = ShotChartTemporalProcessor()
        shots_processed = processor.process_game('202406060BOS')
        processor.close()

        logger.info(f"✓ Processed {shots_processed} shots")

        # Step 4: Run demo queries
        print("\n" + "="*70)
        print("STEP 4: Demo Spatial + Temporal Queries")
        print("="*70 + "\n")
        run_demo_queries(conn)

        # Summary
        print("\n" + "="*70)
        print("✓ DEMO COMPLETE")
        print("="*70)
        print("\nThe shot chart temporal system enables:")
        print("  ✓ Shot charts at any game moment (halftime, clutch, etc.)")
        print("  ✓ Shot selection by game state (leading/trailing)")
        print("  ✓ Zone-based efficiency analysis")
        print("  ✓ Assisted vs unassisted breakdowns")
        print("  ✓ Clutch shooting identification")
        print("  ✓ Spatial + temporal ML features")
        print("\nThis data is ready for ML training!")
        print("\nDatabase: /tmp/basketball_reference_boxscores.db")
        print("Tables: shot_event_snapshots, player_shooting_zones")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
