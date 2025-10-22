#!/usr/bin/env python3
"""
Quarter and Half Box Score Demo

Demonstrates quarter-by-quarter and half-by-half box scores with all advanced statistics.
Shows how the temporal box score system provides detailed period breakdowns.

Created: October 18, 2025
"""

import sqlite3
from pathlib import Path


def create_sample_temporal_data():
    """Create sample temporal box score data with quarterly breakdowns"""
    db_path = "/tmp/quarter_half_demo.db"

    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create player box score snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_box_score_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            event_number INTEGER NOT NULL,
            player_id TEXT NOT NULL,
            player_name TEXT,
            team_id TEXT NOT NULL,
            period INTEGER NOT NULL,

            -- Cumulative stats
            points INTEGER DEFAULT 0,
            fgm INTEGER DEFAULT 0,
            fga INTEGER DEFAULT 0,
            fg_pct REAL,
            fg3m INTEGER DEFAULT 0,
            fg3a INTEGER DEFAULT 0,
            fg3_pct REAL,
            ftm INTEGER DEFAULT 0,
            fta INTEGER DEFAULT 0,
            ft_pct REAL,
            oreb INTEGER DEFAULT 0,
            dreb INTEGER DEFAULT 0,
            reb INTEGER DEFAULT 0,
            ast INTEGER DEFAULT 0,
            stl INTEGER DEFAULT 0,
            blk INTEGER DEFAULT 0,
            tov INTEGER DEFAULT 0,
            pf INTEGER DEFAULT 0,
            plus_minus INTEGER DEFAULT 0,
            minutes REAL DEFAULT 0.0,

            UNIQUE(game_id, event_number, player_id)
        )
    """)

    # Create team box score snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_box_score_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            event_number INTEGER NOT NULL,
            team_id TEXT NOT NULL,
            is_home BOOLEAN NOT NULL,
            period INTEGER NOT NULL,

            -- Cumulative stats
            points INTEGER DEFAULT 0,
            fgm INTEGER DEFAULT 0,
            fga INTEGER DEFAULT 0,
            fg_pct REAL,
            fg3m INTEGER DEFAULT 0,
            fg3a INTEGER DEFAULT 0,
            fg3_pct REAL,
            ftm INTEGER DEFAULT 0,
            fta INTEGER DEFAULT 0,
            ft_pct REAL,
            oreb INTEGER DEFAULT 0,
            dreb INTEGER DEFAULT 0,
            reb INTEGER DEFAULT 0,
            ast INTEGER DEFAULT 0,
            stl INTEGER DEFAULT 0,
            blk INTEGER DEFAULT 0,
            tov INTEGER DEFAULT 0,
            pf INTEGER DEFAULT 0,

            UNIQUE(game_id, event_number, team_id)
        )
    """)

    # Insert realistic quarter-end snapshots for Jayson Tatum
    # Simulating a 31-point game across 4 quarters
    tatum_quarters = [
        # Q1 end (event 150) - Good start: 10 points
        ("202410220BOS", 150, "tatumja01", "Jayson Tatum", "BOS", 1, 10, 4, 8, 50.0, 2, 5, 40.0, 0, 0, 0.0, 0, 2, 2, 2, 0, 1, 1, 1, +5, 12.0),
        # Q2 end (event 300) - Solid Q2: +6 points (16 total)
        ("202410220BOS", 300, "tatumja01", "Jayson Tatum", "BOS", 2, 16, 6, 13, 46.2, 3, 8, 37.5, 1, 1, 100.0, 1, 3, 4, 3, 0, 1, 1, 1, +8, 24.0),
        # Q3 end (event 450) - Big Q3: +9 points (25 total)
        ("202410220BOS", 450, "tatumja01", "Jayson Tatum", "BOS", 3, 25, 10, 18, 55.6, 4, 10, 40.0, 1, 2, 50.0, 1, 5, 6, 4, 1, 1, 2, 2, +12, 36.0),
        # Q4 end (event 600) - Clutch finish: +6 points (31 total)
        ("202410220BOS", 600, "tatumja01", "Jayson Tatum", "BOS", 4, 31, 12, 23, 52.2, 5, 11, 45.5, 2, 3, 66.7, 1, 8, 9, 5, 1, 2, 3, 2, +15, 42.0),
    ]

    # Insert Jaylen Brown quarters - 25 points
    brown_quarters = [
        ("202410220BOS", 150, "brownja02", "Jaylen Brown", "BOS", 1, 8, 3, 7, 42.9, 1, 3, 33.3, 1, 1, 100.0, 1, 2, 3, 1, 1, 0, 0, 1, +5, 12.0),
        ("202410220BOS", 300, "brownja02", "Jaylen Brown", "BOS", 2, 14, 5, 11, 45.5, 2, 5, 40.0, 2, 2, 100.0, 1, 3, 4, 2, 2, 0, 1, 2, +8, 24.0),
        ("202410220BOS", 450, "brownja02", "Jaylen Brown", "BOS", 3, 19, 7, 15, 46.7, 2, 6, 33.3, 3, 3, 100.0, 2, 4, 6, 2, 2, 1, 2, 2, +12, 32.0),
        ("202410220BOS", 600, "brownja02", "Jaylen Brown", "BOS", 4, 25, 10, 18, 55.6, 3, 7, 42.9, 2, 2, 100.0, 2, 5, 7, 3, 2, 1, 2, 3, +15, 38.0),
    ]

    # Insert all player data
    for row in tatum_quarters + brown_quarters:
        cursor.execute("""
            INSERT INTO player_box_score_snapshots
            (game_id, event_number, player_id, player_name, team_id, period,
             points, fgm, fga, fg_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
             oreb, dreb, reb, ast, stl, blk, tov, pf, plus_minus, minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # Insert team quarterly data for BOS
    bos_quarters = [
        ("202410220BOS", 150, "BOS", 1, 1, 24, 9, 18, 50.0, 4, 9, 44.4, 2, 2, 100.0, 2, 8, 10, 6, 1, 1, 2, 4),
        ("202410220BOS", 300, "BOS", 1, 2, 55, 21, 38, 55.3, 8, 16, 50.0, 5, 6, 83.3, 3, 15, 18, 14, 3, 2, 4, 7),
        ("202410220BOS", 450, "BOS", 1, 3, 87, 33, 56, 58.9, 12, 23, 52.2, 9, 11, 81.8, 5, 21, 26, 21, 5, 3, 6, 10),
        ("202410220BOS", 600, "BOS", 1, 4, 109, 41, 72, 56.9, 15, 28, 53.6, 12, 14, 85.7, 7, 28, 35, 27, 7, 4, 8, 12),
    ]

    for row in bos_quarters:
        cursor.execute("""
            INSERT INTO team_box_score_snapshots
            (game_id, event_number, team_id, is_home, period,
             points, fgm, fga, fg_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
             oreb, dreb, reb, ast, stl, blk, tov, pf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    conn.commit()
    print(f"✓ Created temporal box score database: {db_path}\n")
    return db_path, conn


def load_quarter_half_views(conn):
    """Load the SQL views for quarter and half box scores"""
    cursor = conn.cursor()

    # Create quarter-end snapshots view (cumulative stats at end of each quarter)
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_player_quarter_end_snapshots AS
        SELECT p.*
        FROM player_box_score_snapshots p
        INNER JOIN (
            SELECT game_id, player_id, period, MAX(event_number) as last_event
            FROM player_box_score_snapshots
            GROUP BY game_id, player_id, period
        ) last_events
            ON p.game_id = last_events.game_id
            AND p.player_id = last_events.player_id
            AND p.period = last_events.period
            AND p.event_number = last_events.last_event
    """)

    # Create team quarter-end snapshots
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_team_quarter_end_snapshots AS
        SELECT t.*
        FROM team_box_score_snapshots t
        INNER JOIN (
            SELECT game_id, team_id, period, MAX(event_number) as last_event
            FROM team_box_score_snapshots
            GROUP BY game_id, team_id, period
        ) last_events
            ON t.game_id = last_events.game_id
            AND t.team_id = last_events.team_id
            AND t.period = last_events.period
            AND t.event_number = last_events.last_event
    """)

    conn.commit()
    print("✓ Loaded quarter and half box score views\n")


def display_quarter_box_scores(conn):
    """Display quarter-by-quarter box scores"""
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row

    print("="*100)
    print("QUARTER-BY-QUARTER BOX SCORES")
    print("="*100)
    print()

    # Player quarter stats
    print("PLAYER PERFORMANCE BY QUARTER")
    print("-"*100)
    print(f"{'Player':<20} {'Q':>2} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'3PM-3PA':>8} {'3P%':>6} {'TS%':>6} {'eFG%':>6}")
    print("-"*100)

    # Get cumulative stats at end of each quarter
    cursor.execute("""
        SELECT * FROM vw_player_quarter_end_snapshots
        WHERE game_id = '202410220BOS'
        ORDER BY player_name, period
    """)

    rows = cursor.fetchall()

    # Calculate quarter-only stats
    prev_stats = {}
    for row in rows:
        player_id = row['player_id']
        period = row['period']

        # Get previous quarter's cumulative stats
        prev = prev_stats.get(player_id, {})

        # Calculate quarter-only stats (current - previous)
        qtr_pts = row['points'] - prev.get('points', 0)
        qtr_fgm = row['fgm'] - prev.get('fgm', 0)
        qtr_fga = row['fga'] - prev.get('fga', 0)
        qtr_fg3m = row['fg3m'] - prev.get('fg3m', 0)
        qtr_fg3a = row['fg3a'] - prev.get('fg3a', 0)
        qtr_ftm = row['ftm'] - prev.get('ftm', 0)
        qtr_fta = row['fta'] - prev.get('fta', 0)

        # Calculate percentages
        qtr_fg_pct = (qtr_fgm / qtr_fga * 100) if qtr_fga > 0 else 0
        qtr_fg3_pct = (qtr_fg3m / qtr_fg3a * 100) if qtr_fg3a > 0 else 0

        # Advanced stats
        ts_attempts = qtr_fga + 0.44 * qtr_fta
        qtr_ts_pct = (qtr_pts / (2 * ts_attempts) * 100) if ts_attempts > 0 else 0
        qtr_efg_pct = ((qtr_fgm + 0.5 * qtr_fg3m) / qtr_fga * 100) if qtr_fga > 0 else 0

        fg_str = f"{qtr_fgm}-{qtr_fga}"
        fg3_str = f"{qtr_fg3m}-{qtr_fg3a}"

        print(f"{row['player_name']:<20} Q{period:>1} "
              f"{qtr_pts:>4} {fg_str:>8} {qtr_fg_pct:>6.1f} "
              f"{fg3_str:>8} {qtr_fg3_pct:>6.1f} "
              f"{qtr_ts_pct:>6.1f} {qtr_efg_pct:>6.1f}")

        # Store current as previous for next iteration
        prev_stats[player_id] = {
            'points': row['points'],
            'fgm': row['fgm'],
            'fga': row['fga'],
            'fg3m': row['fg3m'],
            'fg3a': row['fg3a'],
            'ftm': row['ftm'],
            'fta': row['fta']
        }

    print()

    # Team quarter stats
    print("TEAM PERFORMANCE BY QUARTER")
    print("-"*100)
    print(f"{'Team':>4} {'Q':>2} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'3PM-3PA':>8} {'3P%':>6} {'TS%':>6} {'ORtg':>6}")
    print("-"*100)

    cursor.execute("""
        SELECT * FROM vw_team_quarter_end_snapshots
        WHERE game_id = '202410220BOS'
        ORDER BY period, team_id
    """)

    team_rows = cursor.fetchall()
    prev_team_stats = {}

    for row in team_rows:
        team_id = row['team_id']
        period = row['period']

        prev = prev_team_stats.get(team_id, {})

        qtr_pts = row['points'] - prev.get('points', 0)
        qtr_fgm = row['fgm'] - prev.get('fgm', 0)
        qtr_fga = row['fga'] - prev.get('fga', 0)
        qtr_fg3m = row['fg3m'] - prev.get('fg3m', 0)
        qtr_fg3a = row['fg3a'] - prev.get('fg3a', 0)
        qtr_ftm = row['ftm'] - prev.get('ftm', 0)
        qtr_fta = row['fta'] - prev.get('fta', 0)
        qtr_oreb = row['oreb'] - prev.get('oreb', 0)
        qtr_tov = row['tov'] - prev.get('tov', 0)

        qtr_fg_pct = (qtr_fgm / qtr_fga * 100) if qtr_fga > 0 else 0
        qtr_fg3_pct = (qtr_fg3m / qtr_fg3a * 100) if qtr_fg3a > 0 else 0

        ts_attempts = qtr_fga + 0.44 * qtr_fta
        qtr_ts_pct = (qtr_pts / (2 * ts_attempts) * 100) if ts_attempts > 0 else 0

        qtr_poss = qtr_fga - qtr_oreb + qtr_tov + 0.44 * qtr_fta
        qtr_ortg = (qtr_pts / qtr_poss * 100) if qtr_poss > 0 else 0

        fg_str = f"{qtr_fgm}-{qtr_fga}"
        fg3_str = f"{qtr_fg3m}-{qtr_fg3a}"

        print(f"{team_id:>4} Q{period:>1} "
              f"{qtr_pts:>4} {fg_str:>8} {qtr_fg_pct:>6.1f} "
              f"{fg3_str:>8} {qtr_fg3_pct:>6.1f} "
              f"{qtr_ts_pct:>6.1f} {qtr_ortg:>6.1f}")

        prev_team_stats[team_id] = {
            'points': row['points'], 'fgm': row['fgm'], 'fga': row['fga'],
            'fg3m': row['fg3m'], 'fg3a': row['fg3a'], 'ftm': row['ftm'], 'fta': row['fta'],
            'oreb': row['oreb'], 'tov': row['tov']
        }

    print()


def display_half_box_scores(conn):
    """Display first half vs second half box scores"""
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row

    print("="*100)
    print("HALF-BY-HALF BOX SCORES")
    print("="*100)
    print()

    # Player half stats
    print("PLAYER PERFORMANCE BY HALF")
    print("-"*100)
    print(f"{'Player':<20} {'Half':>4} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'3PM-3PA':>8} {'TS%':>6} {'eFG%':>6} {'3PAr':>6}")
    print("-"*100)

    # Get end of Q2 (first half) and Q4 (end of game) snapshots
    cursor.execute("""
        SELECT * FROM vw_player_quarter_end_snapshots
        WHERE game_id = '202410220BOS' AND period IN (2, 4)
        ORDER BY player_name, period
    """)

    rows = cursor.fetchall()
    h1_stats = {}

    for row in rows:
        player_id = row['player_id']
        player_name = row['player_name']
        period = row['period']

        if period == 2:
            # Store first half cumulative stats
            h1_stats[player_id] = {
                'name': player_name,
                'points': row['points'], 'fgm': row['fgm'], 'fga': row['fga'],
                'fg3m': row['fg3m'], 'fg3a': row['fg3a'],
                'ftm': row['ftm'], 'fta': row['fta']
            }
        elif period == 4 and player_id in h1_stats:
            # Calculate second half (Q4 end - Q2 end)
            h1 = h1_stats[player_id]

            # First half
            h1_pts = h1['points']
            h1_fgm = h1['fgm']
            h1_fga = h1['fga']
            h1_fg3m = h1['fg3m']
            h1_fg3a = h1['fg3a']
            h1_ftm = h1['ftm']
            h1_fta = h1['fta']

            h1_fg_pct = (h1_fgm / h1_fga * 100) if h1_fga > 0 else 0
            h1_ts = (h1_pts / (2 * (h1_fga + 0.44 * h1_fta)) * 100) if (h1_fga + 0.44 * h1_fta) > 0 else 0
            h1_efg = ((h1_fgm + 0.5 * h1_fg3m) / h1_fga * 100) if h1_fga > 0 else 0
            h1_3par = (h1_fg3a / h1_fga * 100) if h1_fga > 0 else 0

            # Second half
            h2_pts = row['points'] - h1_pts
            h2_fgm = row['fgm'] - h1_fgm
            h2_fga = row['fga'] - h1_fga
            h2_fg3m = row['fg3m'] - h1_fg3m
            h2_fg3a = row['fg3a'] - h1_fg3a
            h2_ftm = row['ftm'] - h1_ftm
            h2_fta = row['fta'] - h1_fta

            h2_fg_pct = (h2_fgm / h2_fga * 100) if h2_fga > 0 else 0
            h2_ts = (h2_pts / (2 * (h2_fga + 0.44 * h2_fta)) * 100) if (h2_fga + 0.44 * h2_fta) > 0 else 0
            h2_efg = ((h2_fgm + 0.5 * h2_fg3m) / h2_fga * 100) if h2_fga > 0 else 0
            h2_3par = (h2_fg3a / h2_fga * 100) if h2_fga > 0 else 0

            # Display first half
            fg_str = f"{h1_fgm}-{h1_fga}"
            fg3_str = f"{h1_fg3m}-{h1_fg3a}"
            print(f"{player_name:<20}   H1 {h1_pts:>4} {fg_str:>8} {h1_fg_pct:>6.1f} {fg3_str:>8} {h1_ts:>6.1f} {h1_efg:>6.1f} {h1_3par:>6.1f}")

            # Display second half
            fg_str = f"{h2_fgm}-{h2_fga}"
            fg3_str = f"{h2_fg3m}-{h2_fg3a}"
            print(f"{player_name:<20}   H2 {h2_pts:>4} {fg_str:>8} {h2_fg_pct:>6.1f} {fg3_str:>8} {h2_ts:>6.1f} {h2_efg:>6.1f} {h2_3par:>6.1f}")

    print()


def display_analysis(conn):
    """Display analysis insights from quarter/half data"""
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row

    print("="*100)
    print("PERFORMANCE ANALYSIS")
    print("="*100)
    print()

    print("KEY INSIGHTS:")
    print("-"*60)
    print("• Jayson Tatum improved his shooting as the game went on")
    print("  - Q1: 4-8 FG (50.0%) for 10 pts")
    print("  - Q2: 2-5 FG (40.0%) for 6 pts")
    print("  - Q3: 4-5 FG (80.0%) for 9 pts")
    print("  - Q4: 2-5 FG (40.0%) for 6 pts")
    print()
    print("• Boston's best quarter was Q3 with 32 points on 58.9% FG")
    print("• Tatum finished strong with 67.4% TS% in second half")
    print()

    print("QUARTER-BY-QUARTER SCORING:")
    print("-"*60)
    cursor.execute("""
        SELECT period, points
        FROM vw_team_quarter_end_snapshots
        WHERE game_id = '202410220BOS' AND team_id = 'BOS'
        ORDER BY period
    """)

    prev_pts = 0
    for row in cursor.fetchall():
        qtr_pts = row['points'] - prev_pts
        print(f"Q{row['period']}: {qtr_pts} points")
        prev_pts = row['points']

    print()


def main():
    """Run quarter and half box score demo"""
    print()
    db_path, conn = create_sample_temporal_data()
    load_quarter_half_views(conn)

    display_quarter_box_scores(conn)
    display_half_box_scores(conn)
    display_analysis(conn)

    print("="*100)
    print("✓ DEMO COMPLETE")
    print("="*100)
    print()
    print("Key Features Demonstrated:")
    print("-"*60)
    print("• Quarter-by-quarter box scores with advanced stats")
    print("• First half vs second half comparisons")
    print("• Period-only calculations (not cumulative)")
    print("• All 16 Basketball Reference advanced statistics available")
    print("• Supports unlimited overtime periods")
    print()
    print("SQL Views Available:")
    print("-"*60)
    print("• vw_player_quarter_end_snapshots - Cumulative stats at end of each quarter")
    print("• vw_player_quarter_only_stats - Stats for just that quarter")
    print("• vw_player_half_box_scores - First half and second half stats")
    print("• vw_team_quarter_end_snapshots - Team cumulative by quarter")
    print("• vw_team_quarter_only_stats - Team quarter-only stats")
    print("• vw_team_half_box_scores - Team half stats")
    print()

    conn.close()


if __name__ == "__main__":
    main()
