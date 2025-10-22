#!/usr/bin/env python3
"""
Demo: Temporal Box Score Snapshots

Creates sample play-by-play data and processes it into temporal snapshots
to demonstrate the system without needing actual Basketball Reference data.

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


def create_sample_pbp_data(conn):
    """Create sample play-by-play data for testing"""
    cursor = conn.cursor()

    # Sample game: 2024 Finals Game 1 - BOS vs MIA
    game_id = "202406060BOS"

    sample_events = [
        # Q1 events
        (game_id, 1, "12:00", "Jump ball: Bam Adebayo vs. Al Horford", 0, 0),
        (game_id, 1, "11:45", "Jayson Tatum makes 3-pt jump shot", 0, 3),
        (game_id, 1, "11:30", "Jimmy Butler makes 2-pt layup", 2, 3),
        (game_id, 1, "11:15", "Jaylen Brown defensive rebound", 2, 3),
        (game_id, 1, "11:00", "Jaylen Brown makes 2-pt jump shot (Jayson Tatum assists)", 2, 5),
        (game_id, 1, "10:45", "Bam Adebayo offensive rebound", 2, 5),
        (game_id, 1, "10:30", "Bam Adebayo makes 2-pt putback", 4, 5),
        (game_id, 1, "10:15", "Jayson Tatum misses 3-pt jump shot", 4, 5),
        (game_id, 1, "10:00", "Jimmy Butler defensive rebound", 4, 5),
        (game_id, 1, "9:45", "Jimmy Butler makes 3-pt jump shot", 7, 5),
        (game_id, 1, "9:30", "Jaylen Brown makes free throw", 7, 6),
        (game_id, 1, "9:29", "Jaylen Brown makes free throw", 7, 7),
        (game_id, 1, "9:15", "Tyler Herro misses 2-pt jump shot", 7, 7),
        (game_id, 1, "9:00", "Al Horford defensive rebound", 7, 7),
        (game_id, 1, "8:45", "Jayson Tatum makes 2-pt jump shot", 7, 9),

        # Q2 events (simulated halftime)
        (game_id, 2, "12:00", "Start of 2nd quarter", 25, 28),
        (game_id, 2, "11:45", "Jayson Tatum makes 3-pt jump shot", 25, 31),
        (game_id, 2, "11:30", "Jimmy Butler makes 2-pt layup", 27, 31),
        (game_id, 2, "6:00", "Halftime approaching", 48, 52),
        (game_id, 2, "0:00", "End of 2nd quarter", 52, 58),

        # Q3 events
        (game_id, 3, "12:00", "Start of 3rd quarter", 52, 58),
        (game_id, 3, "6:00", "Jayson Tatum makes 3-pt jump shot", 70, 80),
        (game_id, 3, "0:00", "End of 3rd quarter", 78, 86),

        # Q4 events (clutch time)
        (game_id, 4, "12:00", "Start of 4th quarter", 78, 86),
        (game_id, 4, "5:00", "Clutch time begins", 95, 98),
        (game_id, 4, "4:30", "Jayson Tatum makes 2-pt jump shot", 95, 100),
        (game_id, 4, "4:00", "Jimmy Butler makes 3-pt jump shot", 98, 100),
        (game_id, 4, "3:30", "Jaylen Brown makes free throw", 98, 101),
        (game_id, 4, "3:29", "Jaylen Brown makes free throw", 98, 102),
        (game_id, 4, "2:00", "Jimmy Butler misses 3-pt jump shot", 98, 102),
        (game_id, 4, "1:30", "Al Horford defensive rebound", 98, 102),
        (game_id, 4, "1:00", "Jayson Tatum makes 2-pt jump shot", 98, 104),
        (game_id, 4, "0:30", "Jimmy Butler makes 2-pt layup", 100, 104),
        (game_id, 4, "0:10", "Jaylen Brown makes free throw", 100, 105),
        (game_id, 4, "0:09", "Jaylen Brown makes free throw", 100, 106),
        (game_id, 4, "0:00", "Game ends", 100, 106),
    ]

    # Insert sample events
    for event in sample_events:
        cursor.execute("""
            INSERT INTO game_play_by_play
            (game_id, quarter, time_remaining, description, away_score, home_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, event)

    conn.commit()
    logger.info(f"✓ Created {len(sample_events)} sample PBP events")
    logger.info(f"  Game: {game_id}")
    logger.info(f"  Final Score: MIA 100 - BOS 106")


def create_temporal_tables(conn):
    """Create temporal snapshot tables"""
    logger.info("Creating temporal snapshot tables...")

    with open('sql/temporal_box_score_snapshots.sql', 'r') as f:
        schema = f.read()
        conn.executescript(schema)

    logger.info("✓ Tables created")


def process_to_snapshots(conn):
    """Process PBP into temporal snapshots"""
    from sqlite_pbp_processor import SQLitePBPProcessor

    processor = SQLitePBPProcessor(db_path="/tmp/basketball_reference_boxscores.db")

    games = processor.get_available_games()
    logger.info(f"Found {len(games)} games to process")

    for game_id in games:
        player_snapshots, team_snapshots = processor.process_game(game_id)
        processor.save_snapshots(player_snapshots, team_snapshots)

    processor.close()


def run_demo_queries(conn):
    """Run demo queries to show temporal capabilities"""
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("DEMO QUERY 1: Quarter-by-Quarter Team Scoring")
    print("="*70)

    cursor.execute("""
        SELECT
            period as quarter,
            MAX(points) as final_points,
            team_id,
            is_home
        FROM team_box_score_snapshots
        WHERE game_id = '202406060BOS'
        GROUP BY period, team_id
        ORDER BY team_id, period
    """)

    print("\nQuarter | Team | Home? | Points")
    print("-" * 40)
    for row in cursor.fetchall():
        quarter, points, team, is_home = row
        home_str = "Home" if is_home else "Away"
        print(f"Q{quarter:<6} | {team:<4} | {home_str:<5} | {points}")

    print("\n" + "="*70)
    print("DEMO QUERY 2: Halftime Snapshot")
    print("="*70)

    cursor.execute("""
        SELECT
            team_id,
            points as halftime_points,
            fgm,
            fga,
            ROUND(fg_pct, 1) as fg_pct,
            score_diff
        FROM team_box_score_snapshots
        WHERE game_id = '202406060BOS'
        AND period = 2
        AND event_number = (
            SELECT MAX(event_number)
            FROM team_box_score_snapshots
            WHERE game_id = '202406060BOS' AND period = 2
        )
    """)

    print("\nHalftime Box Score:")
    print("Team | Points | FGM-FGA | FG% | Diff")
    print("-" * 45)
    for row in cursor.fetchall():
        team, pts, fgm, fga, fg_pct, diff = row
        print(f"{team:<4} | {pts:>6} | {fgm}-{fga:<3} | {fg_pct}% | {diff:+}")

    print("\n" + "="*70)
    print("DEMO QUERY 3: Clutch Moments (Q4, Last 5 min, Close Game)")
    print("="*70)

    cursor.execute("""
        SELECT
            game_clock,
            score_diff,
            points as home_score,
            (SELECT points FROM team_box_score_snapshots t2
             WHERE t2.game_id = t.game_id
             AND t2.event_number = t.event_number
             AND t2.is_home = 0) as away_score
        FROM team_box_score_snapshots t
        WHERE game_id = '202406060BOS'
        AND period = 4
        AND time_elapsed_seconds >= (48 * 60 - 5 * 60)
        AND is_home = 1
        ORDER BY event_number
    """)

    print("\nTime  | Home | Away | Diff")
    print("-" * 35)
    rows = cursor.fetchall()
    for row in rows[:10]:  # Show first 10
        time, diff, home, away = row
        print(f"{time:<5} | {home:>4} | {away:>4} | {diff:+}")

    if len(rows) > 10:
        print(f"... ({len(rows) - 10} more clutch moments)")

    print("\n" + "="*70)
    print("DEMO QUERY 4: Player Performance Timeline")
    print("="*70)

    cursor.execute("""
        SELECT
            player_name,
            period,
            MAX(points) as points,
            MAX(fgm) as fgm,
            MAX(fga) as fga,
            ROUND(MAX(fg_pct), 1) as fg_pct
        FROM player_box_score_snapshots
        WHERE game_id = '202406060BOS'
        AND player_name LIKE '%Tatum%'
        GROUP BY player_name, period
        ORDER BY period
    """)

    print("\nJayson Tatum - Quarter by Quarter:")
    print("Quarter | Points | FG | FG%")
    print("-" * 35)
    for row in cursor.fetchall():
        player, quarter, pts, fgm, fga, fg_pct = row
        print(f"Q{quarter:<6} | {pts:>6} | {fgm}-{fga} | {fg_pct}%")

    print("\n" + "="*70)
    print("DEMO QUERY 5: When Did Team Take The Lead?")
    print("="*70)

    cursor.execute("""
        SELECT
            period,
            game_clock,
            points as home_pts,
            score_diff,
            event_number
        FROM team_box_score_snapshots
        WHERE game_id = '202406060BOS'
        AND is_home = 1
        AND is_leading = 1
        ORDER BY event_number
        LIMIT 5
    """)

    print("\nFirst 5 moments Boston took the lead:")
    print("Quarter | Time  | Score | Diff | Event#")
    print("-" * 45)
    for row in cursor.fetchall():
        quarter, time, pts, diff, event = row
        print(f"Q{quarter:<6} | {time:<5} | {pts:>5} | +{diff}  | #{event}")

    print("\n" + "="*70)
    print("DEMO QUERY 6: Score Progression Over Time")
    print("="*70)

    cursor.execute("""
        SELECT
            event_number,
            period,
            game_clock,
            points as home_score,
            score_diff
        FROM team_box_score_snapshots
        WHERE game_id = '202406060BOS'
        AND is_home = 1
        AND event_number % 5 = 0  -- Every 5th event
        ORDER BY event_number
        LIMIT 15
    """)

    print("\nScore progression (sampled every 5 events):")
    print("Event# | Q | Time  | Home | Diff")
    print("-" * 40)
    for row in cursor.fetchall():
        event, quarter, time, home, diff = row
        print(f"#{event:<5} | {quarter} | {time:<5} | {home:>4} | {diff:+}")


def main():
    """Run complete demo"""
    print("\n" + "="*70)
    print("TEMPORAL BOX SCORE SNAPSHOTS - DEMO")
    print("="*70)
    print("\nThis demo shows how temporal snapshots enable ML queries")
    print("at any moment in game time.\n")

    # Connect to database
    conn = sqlite3.connect('/tmp/basketball_reference_boxscores.db')

    try:
        # Step 1: Create sample PBP data
        print("\n" + "="*70)
        print("STEP 1: Creating Sample Play-by-Play Data")
        print("="*70 + "\n")
        create_sample_pbp_data(conn)

        # Step 2: Create temporal tables
        print("\n" + "="*70)
        print("STEP 2: Creating Temporal Snapshot Tables")
        print("="*70 + "\n")
        create_temporal_tables(conn)

        # Step 3: Process into snapshots
        print("\n" + "="*70)
        print("STEP 3: Processing PBP into Temporal Snapshots")
        print("="*70 + "\n")
        process_to_snapshots(conn)

        # Step 4: Run demo queries
        print("\n" + "="*70)
        print("STEP 4: Demo ML Queries")
        print("="*70 + "\n")
        run_demo_queries(conn)

        # Summary
        print("\n" + "="*70)
        print("✓ DEMO COMPLETE")
        print("="*70)
        print("\nThe temporal snapshot system enables:")
        print("  ✓ Query stats at any moment (halftime, Q3 start, etc.)")
        print("  ✓ Track score progression over time")
        print("  ✓ Find clutch moments automatically")
        print("  ✓ Extract player performance dynamics")
        print("  ✓ Generate ML features (momentum, fatigue, etc.)")
        print("\nThis data is now ready for ML training!")
        print("\nDatabase: /tmp/basketball_reference_boxscores.db")
        print("Tables: player_box_score_snapshots, team_box_score_snapshots")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
