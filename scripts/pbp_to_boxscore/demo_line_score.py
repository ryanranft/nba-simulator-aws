#!/usr/bin/env python3
"""
Line Score Demo

Demonstrates the quarter-by-quarter scoring display
that updates at each play-by-play event, including unlimited overtime periods.

Created: October 18, 2025
"""

import sqlite3
import json
from pathlib import Path

def create_demo_data():
    """Create demo PBP data with scoring events across quarters"""
    db_path = "/tmp/line_score_demo.db"

    # Remove existing demo database
    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    print("Creating tables...")
    with open('sql/temporal_box_score_snapshots.sql', 'r') as f:
        schema = f.read()
        conn.executescript(schema)

    # Create game_play_by_play table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_play_by_play (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            quarter INTEGER NOT NULL,
            time_remaining TEXT,
            description TEXT,
            home_score INTEGER DEFAULT 0,
            away_score INTEGER DEFAULT 0
        )
    """)

    # Insert demo PBP events with realistic scoring progression
    game_id = "202406060BOS"

    events = [
        # Q1 - BOS leads 43-24
        (1, "11:30", "Jayson Tatum makes 3-pt jump shot", 3, 0),
        (1, "10:45", "NYK player makes 2-pt shot", 3, 2),
        (1, "9:20", "Derrick White makes 2-pt shot", 5, 2),
        (1, "8:15", "NYK player makes 3-pt shot", 5, 5),
        (1, "6:30", "Jaylen Brown makes 2-pt shot", 7, 5),
        (1, "5:00", "NYK player makes 2-pt shot", 7, 7),
        (1, "3:45", "Jayson Tatum makes 3-pt jump shot", 10, 7),
        (1, "2:20", "NYK player makes free throw", 10, 8),
        (1, "1:15", "Kristaps Porzingis makes 2-pt shot", 12, 8),
        (1, "0:30", "NYK player makes 3-pt shot", 12, 11),
        (1, "0:05", "Jaylen Brown makes layup", 14, 11),
        # End Q1: BOS 43, NYK 24 (using realistic final scores)
        (1, "0:00", "End of Q1", 43, 24),

        # Q2 - BOS adds 31, NYK adds 31 (tied quarter)
        (2, "11:45", "Payton Pritchard makes 3-pt shot", 46, 24),
        (2, "10:30", "NYK player makes 2-pt shot", 46, 26),
        (2, "8:50", "Sam Hauser makes 3-pt shot", 49, 26),
        (2, "7:15", "NYK player makes 3-pt shot", 49, 29),
        (2, "5:30", "Jayson Tatum makes 2-pt shot", 51, 29),
        (2, "4:00", "NYK player makes 2-pt shot", 51, 31),
        (2, "2:45", "Derrick White makes 3-pt shot", 54, 31),
        (2, "1:20", "NYK player makes 3-pt shot", 54, 34),
        (2, "0:35", "Jaylen Brown makes 2-pt shot", 56, 34),
        (2, "0:08", "NYK player makes free throw", 56, 35),
        # End Q2: BOS 74, NYK 55
        (2, "0:00", "End of Q2", 74, 55),

        # Q3 - BOS adds 39, NYK adds 31
        (3, "11:20", "Jayson Tatum makes 3-pt shot", 77, 55),
        (3, "9:45", "NYK player makes 2-pt shot", 77, 57),
        (3, "8:10", "Jaylen Brown makes layup", 79, 57),
        (3, "6:30", "NYK player makes 3-pt shot", 79, 60),
        (3, "4:55", "Kristaps Porzingis makes 3-pt shot", 82, 60),
        (3, "3:20", "NYK player makes 2-pt shot", 82, 62),
        (3, "1:40", "Derrick White makes 3-pt shot", 85, 62),
        (3, "0:25", "NYK player makes 2-pt shot", 85, 64),
        # End Q3: BOS 113, NYK 86
        (3, "0:00", "End of Q3", 113, 86),

        # Q4 - BOS adds 19, NYK adds 22 (NYK wins quarter, tied at end of regulation!)
        (4, "10:50", "NYK player makes 3-pt shot", 113, 89),
        (4, "9:15", "Jayson Tatum makes 2-pt shot", 115, 89),
        (4, "7:30", "NYK player makes 2-pt shot", 115, 91),
        (4, "5:45", "Payton Pritchard makes 3-pt shot", 118, 91),
        (4, "3:50", "NYK player makes 3-pt shot", 118, 94),
        (4, "2:10", "Jaylen Brown makes free throw", 119, 94),
        (4, "0:55", "NYK player makes 2-pt shot", 119, 96),
        (4, "0:15", "NYK player makes free throw", 119, 97),
        (4, "0:03", "BOS makes shot", 121, 97),
        (4, "0:01", "NYK makes shot", 121, 99),
        # End of regulation tied 121-121!
        (4, "0:00", "End of Q4 - Overtime!", 121, 121),

        # OT1 - BOS adds 5, NYK adds 3
        (5, "4:30", "Jayson Tatum makes 2-pt shot", 123, 121),
        (5, "3:15", "NYK player makes free throw", 123, 122),
        (5, "2:00", "Derrick White makes 3-pt shot", 126, 122),
        (5, "0:45", "NYK player makes 2-pt shot", 126, 124),
        # End OT1 tied 126-126!
        (5, "0:00", "End of OT1 - Double OT!", 126, 126),

        # OT2 - BOS adds 4, NYK adds 2
        (6, "3:20", "Jaylen Brown makes 2-pt shot", 128, 126),
        (6, "1:45", "NYK player makes 2-pt shot", 128, 128),
        (6, "0:30", "Jayson Tatum makes 2-pt shot", 130, 128),
        # End OT2 tied 130-130!
        (6, "0:00", "End of OT2 - Triple OT!", 130, 130),

        # OT3 - BOS adds 7, NYK adds 3 (BOS finally wins!)
        (7, "3:00", "Payton Pritchard makes 3-pt shot", 133, 130),
        (7, "2:10", "NYK player makes free throw", 133, 131),
        (7, "1:25", "Jayson Tatum makes 2-pt shot", 135, 131),
        (7, "0:40", "NYK player makes 2-pt shot", 135, 133),
        (7, "0:10", "Derrick White makes 2-pt shot", 137, 133),
        # Final after 3 OT: BOS 137, NYK 133
        (7, "0:00", "Final - Triple OT!", 137, 133),
    ]

    for quarter, time_rem, desc, home, away in events:
        cursor.execute("""
            INSERT INTO game_play_by_play (game_id, quarter, time_remaining, description, home_score, away_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (game_id, quarter, time_rem, desc, home, away))

    conn.commit()

    print(f"✓ Created {len(events)} demo PBP events")
    print(f"  Database: {db_path}\n")

    return db_path


def process_and_display_line_scores(db_path):
    """Process PBP and display line scores at key moments"""
    from sqlite_pbp_processor import SQLitePBPProcessor

    print("Processing PBP into temporal snapshots...\n")
    processor = SQLitePBPProcessor(db_path=db_path)

    try:
        # Process the demo game
        game_id = "202406060BOS"
        player_snapshots, team_snapshots = processor.process_game(game_id)

        if team_snapshots:
            processor.save_snapshots(player_snapshots, team_snapshots)
            print()

        # Query line scores at different moments
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("="*70)
        print("LINE SCORE DISPLAY AT KEY MOMENTS")
        print("="*70)
        print()

        # Find quarter-end event numbers
        cursor.execute("""
            SELECT period, MAX(event_number) as last_event
            FROM team_box_score_snapshots
            WHERE game_id = ?
            GROUP BY period
            ORDER BY period
        """, (game_id,))

        quarter_ends = {row['period']: row['last_event'] for row in cursor.fetchall()}

        for quarter, event_num in sorted(quarter_ends.items()):
            print(f"End of Q{quarter} (Event #{event_num}):")
            print("-" * 70)

            cursor.execute("""
                SELECT
                    team_id,
                    is_home,
                    q1_points,
                    q2_points,
                    q3_points,
                    q4_points,
                    overtime_line_score,
                    points as total
                FROM team_box_score_snapshots
                WHERE game_id = ? AND event_number = ?
                ORDER BY is_home DESC
            """, (game_id, event_num))

            # Determine if there's overtime
            rows = cursor.fetchall()
            has_ot = any(row['overtime_line_score'] and row['overtime_line_score'] != '[]' for row in rows)

            # Build header
            header = "Line Score Scoring  1   2   3   4"
            if has_ot:
                # Parse OT periods from first row
                ot_scores = json.loads(rows[0]['overtime_line_score']) if rows else []
                for i in range(1, len(ot_scores) + 1):
                    header += f" OT{i}" if i > 1 else " OT"
            header += "   T"
            print(header)

            for row in rows:
                team = "BOS" if row['is_home'] else "NYK"
                line = f"{team:3} {row['q1_points']:3} {row['q2_points']:3} {row['q3_points']:3} {row['q4_points']:3}"

                # Add OT periods
                if row['overtime_line_score'] and row['overtime_line_score'] != '[]':
                    ot_scores = json.loads(row['overtime_line_score'])
                    for ot_pts in ot_scores:
                        line += f"  {ot_pts:2}"

                line += f" {row['total']:4}"
                print(line)

            print()

        # Show the view output
        print("="*70)
        print("USING vw_line_score VIEW")
        print("="*70)
        print()

        cursor.execute("""
            SELECT
                team_id,
                is_home,
                q1_points,
                q2_points,
                q3_points,
                q4_points,
                overtime_line_score,
                total_points,
                event_number
            FROM vw_line_score
            WHERE game_id = ?
            ORDER BY event_number DESC, is_home DESC
            LIMIT 2
        """, (game_id,))

        rows = cursor.fetchall()

        print("Final Score:")
        print("-" * 70)

        # Build header with OT periods
        has_ot = any(row['overtime_line_score'] and row['overtime_line_score'] != '[]' for row in rows)
        header = "Team  1   2   3   4"
        if has_ot:
            ot_scores = json.loads(rows[0]['overtime_line_score']) if rows else []
            for i in range(1, len(ot_scores) + 1):
                header += f" OT{i}" if i > 1 else " OT"
        header += "   T"
        print(header)

        for row in rows:
            team = "BOS" if row['is_home'] else "NYK"
            line = f"{team:3} {row['q1_points']:3} {row['q2_points']:3} {row['q3_points']:3} {row['q4_points']:3}"

            # Add OT periods
            if row['overtime_line_score'] and row['overtime_line_score'] != '[]':
                ot_scores = json.loads(row['overtime_line_score'])
                for ot_pts in ot_scores:
                    line += f"  {ot_pts:2}"

            line += f" {row['total_points']:4}"
            print(line)

        print()
        print("="*70)
        print("✓ LINE SCORE DEMO COMPLETE")
        print("="*70)
        print()
        print("The line score shows quarter-by-quarter scoring:")
        print("  - Q1: Points scored IN quarter 1 only")
        print("  - Q2: Points scored IN quarter 2 only (not cumulative)")
        print("  - Q3: Points scored IN quarter 3 only")
        print("  - Q4: Points scored IN quarter 4 only")
        print("  - T:  Total points (sum of all quarters)")
        print()
        print("This matches the format requested:")
        print("  Line Score Scoring  1   2   3   4    T")
        print("  NYK                24  31  32  22  109")
        print("  BOS                43  31  39  19  132")

        conn.close()

    finally:
        processor.close()


def main():
    """Run line score demo"""
    print("\n" + "="*70)
    print("LINE SCORE TEMPORAL INTEGRATION DEMO")
    print("="*70)
    print()
    print("This demo shows quarter-by-quarter scoring that updates at each")
    print("play-by-play event, matching the format:")
    print()
    print("  Line Score Scoring  1   2   3   4    T")
    print("  NYK                24  31  32  22  109")
    print("  BOS                43  31  39  19  132")
    print()
    print("="*70)
    print()

    # Create demo data
    db_path = create_demo_data()

    # Process and display
    process_and_display_line_scores(db_path)


if __name__ == "__main__":
    main()
