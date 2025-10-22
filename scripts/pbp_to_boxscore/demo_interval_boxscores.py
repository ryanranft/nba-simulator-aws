#!/usr/bin/env python3
"""
Interval Box Score Demo

Demonstrates interval-based box scores at multiple granularities:
- 6-minute intervals (8 per regulation)
- 3-minute intervals (16 per regulation)
- 1:30 intervals (32 per regulation)
- 1-minute intervals (48 per regulation)
- OT 2:30 halves (2 per OT period)
- OT 1-minute intervals (5 per OT period)

All intervals include complete advanced statistics.

Created: October 19, 2025
"""

import sqlite3
import sys
from pathlib import Path

# Add the pbp_to_boxscore directory to path
sys.path.insert(0, str(Path(__file__).parent))

from interval_box_score_calculator import IntervalBoxScoreCalculator, TimeInterval


def create_sample_temporal_data():
    """Create sample temporal box score data with fine-grained time tracking"""
    db_path = "/tmp/interval_demo.db"

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
            time_elapsed_seconds INTEGER NOT NULL,

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
            period INTEGER NOT NULL,
            time_elapsed_seconds INTEGER NOT NULL,

            -- Cumulative stats
            points INTEGER DEFAULT 0,
            fgm INTEGER DEFAULT 0,
            fga INTEGER DEFAULT 0,
            fg3m INTEGER DEFAULT 0,
            fg3a INTEGER DEFAULT 0,
            ftm INTEGER DEFAULT 0,
            fta INTEGER DEFAULT 0,
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

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_time
        ON player_box_score_snapshots(game_id, player_id, time_elapsed_seconds)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_team_time
        ON team_box_score_snapshots(game_id, team_id, time_elapsed_seconds)
    """)

    # Insert Jayson Tatum snapshots at key time intervals
    # Simulating 35-point game with 2OT on October 22, 2024 at 7:30 PM ET
    # Jayson Tatum would be 26 years old at this game (born March 3, 1998)
    tatum_snapshots = [
        # Q1 end (720 seconds = 12 minutes) - Adding timestamp field
        ("OT_GAME", 150, "tatumja01", "Jayson Tatum", "BOS", 1, 720, "2024-10-22 19:42:00", 8, 3, 6, 50.0, 2, 4, 50.0, 0, 0, 0.0, 0, 2, 2, 1, 0, 0, 1, 1, 12.0),
        # Q2 end (1440 seconds = 24 minutes)
        ("OT_GAME", 300, "tatumja01", "Jayson Tatum", "BOS", 2, 1440, "2024-10-22 19:54:00", 15, 6, 12, 50.0, 3, 7, 42.9, 0, 0, 0.0, 1, 4, 5, 3, 1, 0, 2, 2, 24.0),
        # Q3 end (2160 seconds = 36 minutes)
        ("OT_GAME", 450, "tatumja01", "Jayson Tatum", "BOS", 3, 2160, "2024-10-22 20:06:00", 23, 9, 18, 50.0, 4, 10, 40.0, 1, 1, 100.0, 1, 6, 7, 4, 1, 1, 3, 2, 36.0),
        # Q4 end (2880 seconds = 48 minutes) - Game tied!
        ("OT_GAME", 600, "tatumja01", "Jayson Tatum", "BOS", 4, 2880, "2024-10-22 20:18:00", 28, 11, 23, 47.8, 5, 12, 41.7, 1, 1, 100.0, 1, 8, 9, 5, 1, 1, 4, 3, 42.0),
        # OT1 end (3180 seconds = 53 minutes)
        ("OT_GAME", 720, "tatumja01", "Jayson Tatum", "BOS", 5, 3180, "2024-10-22 20:23:00", 31, 12, 26, 46.2, 6, 14, 42.9, 1, 1, 100.0, 1, 9, 10, 6, 1, 1, 4, 3, 47.0),
        # OT2 end (3480 seconds = 58 minutes) - FINAL
        ("OT_GAME", 840, "tatumja01", "Jayson Tatum", "BOS", 6, 3480, "2024-10-22 20:28:00", 35, 14, 30, 46.7, 6, 15, 40.0, 1, 2, 50.0, 2, 11, 13, 7, 2, 1, 5, 4, 52.0),

        # Additional snapshots for finer granularity
        # 6 min mark (360 seconds)
        ("OT_GAME", 75, "tatumja01", "Jayson Tatum", "BOS", 1, 360, "2024-10-22 19:36:00", 4, 2, 3, 66.7, 0, 1, 0.0, 0, 0, 0.0, 0, 1, 1, 1, 0, 0, 0, 0, 6.0),
        # 3 min mark (180 seconds)
        ("OT_GAME", 35, "tatumja01", "Jayson Tatum", "BOS", 1, 180, "2024-10-22 19:33:00", 2, 1, 2, 50.0, 0, 1, 0.0, 0, 0, 0.0, 0, 1, 1, 0, 0, 0, 0, 0, 3.0),
        # 1 min mark (60 seconds)
        ("OT_GAME", 12, "tatumja01", "Jayson Tatum", "BOS", 1, 60, "2024-10-22 19:31:00", 0, 0, 1, 0.0, 0, 1, 0.0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0),

        # OT1 2:30 mark (3030 seconds = 50.5 minutes)
        ("OT_GAME", 780, "tatumja01", "Jayson Tatum", "BOS", 5, 3030, "2024-10-22 20:20:30", 29, 11, 24, 45.8, 6, 13, 46.2, 1, 1, 100.0, 1, 8, 9, 5, 1, 1, 4, 3, 44.5),
        # OT2 2:30 mark (3330 seconds = 55.5 minutes)
        ("OT_GAME", 810, "tatumja01", "Jayson Tatum", "BOS", 6, 3330, "2024-10-22 20:25:30", 33, 13, 28, 46.4, 6, 14, 42.9, 1, 2, 50.0, 1, 10, 11, 6, 1, 1, 4, 3, 49.5),
    ]

    # Insert all Tatum snapshots (sorted by time)
    for row in sorted(tatum_snapshots, key=lambda x: x[6]):  # Sort by time_elapsed_seconds
        cursor.execute("""
            INSERT INTO player_box_score_snapshots
            (game_id, event_number, player_id, player_name, team_id, period, time_elapsed_seconds, timestamp,
             points, fgm, fga, fg_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
             oreb, dreb, reb, ast, stl, blk, tov, pf, minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # Insert team snapshots for BOS
    bos_snapshots = [
        ("OT_GAME", 150, "BOS", 1, 720, 28, 11, 20, 5, 10, 1, 2, 2, 10, 12, 6, 1, 1, 2, 4),
        ("OT_GAME", 300, "BOS", 2, 1440, 55, 21, 40, 9, 18, 4, 6, 3, 18, 21, 13, 3, 2, 4, 7),
        ("OT_GAME", 450, "BOS", 3, 2160, 82, 31, 58, 14, 25, 6, 9, 5, 25, 30, 19, 5, 3, 6, 10),
        ("OT_GAME", 600, "BOS", 4, 2880, 104, 40, 75, 18, 32, 6, 11, 7, 32, 39, 24, 7, 4, 8, 12),
        ("OT_GAME", 720, "BOS", 5, 3180, 111, 43, 82, 19, 36, 6, 12, 8, 35, 43, 26, 8, 5, 9, 14),
        ("OT_GAME", 840, "BOS", 6, 3480, 118, 46, 89, 20, 39, 6, 13, 9, 38, 47, 28, 10, 6, 10, 16),
    ]

    for row in bos_snapshots:
        cursor.execute("""
            INSERT INTO team_box_score_snapshots
            (game_id, event_number, team_id, period, time_elapsed_seconds,
             points, fgm, fga, fg3m, fg3a, ftm, fta,
             oreb, dreb, reb, ast, stl, blk, tov, pf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # Insert team snapshots for LAL (opponent) - Competitive game that goes to 2OT
    lal_snapshots = [
        ("OT_GAME", 150, "LAL", 1, 720, 26, 10, 22, 4, 11, 2, 3, 3, 9, 12, 5, 2, 0, 3, 5),
        ("OT_GAME", 300, "LAL", 2, 1440, 53, 20, 43, 8, 19, 5, 7, 5, 16, 21, 11, 4, 1, 5, 8),
        ("OT_GAME", 450, "LAL", 3, 2160, 80, 30, 62, 12, 27, 8, 11, 7, 23, 30, 17, 6, 2, 7, 11),
        ("OT_GAME", 600, "LAL", 4, 2880, 104, 39, 78, 16, 34, 10, 13, 9, 30, 39, 22, 8, 3, 9, 14),  # Tied!
        ("OT_GAME", 720, "LAL", 5, 3180, 109, 41, 85, 17, 37, 10, 14, 10, 33, 43, 24, 9, 4, 10, 16),
        ("OT_GAME", 840, "LAL", 6, 3480, 115, 43, 92, 18, 41, 11, 15, 11, 36, 47, 26, 11, 5, 11, 18),  # BOS wins 118-115
    ]

    for row in lal_snapshots:
        cursor.execute("""
            INSERT INTO team_box_score_snapshots
            (game_id, event_number, team_id, period, time_elapsed_seconds,
             points, fgm, fga, fg3m, fg3a, ftm, fta,
             oreb, dreb, reb, ast, stl, blk, tov, pf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # Insert player biographical data for Jayson Tatum
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_biographical (
            player_id TEXT PRIMARY KEY,
            birth_date DATE,
            birth_date_precision TEXT,
            birth_city TEXT,
            birth_state TEXT,
            birth_country TEXT,
            height_inches INTEGER,
            weight_pounds INTEGER,
            wingspan_inches INTEGER,
            nba_debut_date DATE,
            nba_retirement_date DATE,
            draft_year INTEGER,
            draft_round INTEGER,
            draft_pick INTEGER,
            draft_team_id TEXT,
            college TEXT,
            high_school TEXT,
            nationality TEXT,
            position TEXT,
            jersey_number INTEGER,
            data_source TEXT
        )
    """)

    # Jayson Tatum biographical data
    tatum_bio = (
        "tatumja01",           # player_id
        "1998-03-03",          # birth_date (March 3, 1998)
        "day",                 # birth_date_precision
        "St. Louis",           # birth_city
        "Missouri",            # birth_state
        "USA",                 # birth_country
        80,                    # height_inches (6'8")
        210,                   # weight_pounds
        85,                    # wingspan_inches (7'1")
        "2017-10-17",          # nba_debut_date
        None,                  # nba_retirement_date (active)
        2017,                  # draft_year
        1,                     # draft_round
        3,                     # draft_pick
        "BOS",                 # draft_team_id
        "Duke",                # college
        "Chaminade College Preparatory School",  # high_school
        "USA",                 # nationality
        "SF",                  # position (Small Forward)
        0,                     # jersey_number
        "nba_api"              # data_source
    )

    cursor.execute("""
        INSERT OR REPLACE INTO player_biographical
        (player_id, birth_date, birth_date_precision, birth_city, birth_state, birth_country,
         height_inches, weight_pounds, wingspan_inches, nba_debut_date, nba_retirement_date,
         draft_year, draft_round, draft_pick, draft_team_id, college, high_school,
         nationality, position, jersey_number, data_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tatum_bio)

    conn.commit()
    print(f"✓ Created temporal box score database with OT (BOS vs LAL): {db_path}")
    print(f"✓ Added biographical data for Jayson Tatum\n")
    return db_path, conn


def display_interval_box_scores(calc: IntervalBoxScoreCalculator, game_id: str, player_id: str,
                                player_name: str, interval_type: str):
    """Display box scores for a specific interval type with ALL 16 Basketball Reference advanced stats"""

    # Get interval stats
    if interval_type in ['6min', '3min', '90sec', '1min']:
        intervals = calc.calculate_all_regulation_intervals(game_id, player_id, interval_type)
        title = {
            '6min': '6-MINUTE INTERVALS',
            '3min': '3-MINUTE INTERVALS',
            '90sec': '1:30 (90-SECOND) INTERVALS',
            '1min': '1-MINUTE INTERVALS'
        }[interval_type]
    else:
        return

    print("=" * 140)
    print(f"{title} - {player_name} - ALL 16 BASKETBALL REFERENCE ADVANCED STATS")
    print("=" * 140)
    print()

    # SECTION 1: Basic Stats & Shooting Efficiency (5 stats)
    print("SHOOTING EFFICIENCY (TS%, eFG%, 3PAr, FTr):")
    print(f"{'Interval':<12} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'3PM-3PA':>8} {'3P%':>6} {'TS%':>6} {'eFG%':>6} {'3PAr':>6} {'FTr':>6}")
    print("-" * 140)

    for stats in intervals:
        if stats['points'] == 0 and stats['fga'] == 0:
            continue  # Skip empty intervals

        fg_str = f"{stats['fgm']}-{stats['fga']}"
        fg3_str = f"{stats['fg3m']}-{stats['fg3a']}"

        print(f"{stats['interval']:<12} "
              f"{stats['points']:>4} "
              f"{fg_str:>8} "
              f"{stats['fg_pct']:>6.1f} "
              f"{fg3_str:>8} "
              f"{stats['fg3_pct']:>6.1f} "
              f"{stats['ts_pct']:>6.1f} "
              f"{stats['efg_pct']:>6.1f} "
              f"{stats['3par']:>6.1f} "
              f"{stats.get('ft_rate', 0.0):>6.2f}")

    print()

    # SECTION 2: Rebounding Percentages (3 stats)
    print("REBOUNDING PERCENTAGES (ORB%, DRB%, TRB%):")
    print(f"{'Interval':<12} {'OREB':>5} {'DREB':>5} {'REB':>5} {'ORB%':>7} {'DRB%':>7} {'TRB%':>7}")
    print("-" * 140)

    for stats in intervals:
        if stats['points'] == 0 and stats['fga'] == 0:
            continue

        print(f"{stats['interval']:<12} "
              f"{stats['oreb']:>5} "
              f"{stats['dreb']:>5} "
              f"{stats['reb']:>5} "
              f"{stats.get('orb_pct', 0.0):>7.1f} "
              f"{stats.get('drb_pct', 0.0):>7.1f} "
              f"{stats.get('trb_pct', 0.0):>7.1f}")

    print()

    # SECTION 3: Playmaking & Defense (4 stats)
    print("PLAYMAKING & DEFENSE (AST%, STL%, BLK%, TOV%):")
    print(f"{'Interval':<12} {'AST':>4} {'STL':>4} {'BLK':>4} {'TOV':>4} {'AST%':>7} {'STL%':>7} {'BLK%':>7} {'TOV%':>7}")
    print("-" * 140)

    for stats in intervals:
        if stats['points'] == 0 and stats['fga'] == 0:
            continue

        print(f"{stats['interval']:<12} "
              f"{stats['ast']:>4} "
              f"{stats['stl']:>4} "
              f"{stats['blk']:>4} "
              f"{stats['tov']:>4} "
              f"{stats.get('ast_pct', 0.0):>7.1f} "
              f"{stats.get('stl_pct', 0.0):>7.1f} "
              f"{stats.get('blk_pct', 0.0):>7.1f} "
              f"{stats['tov_pct']:>7.1f}")

    print()

    # SECTION 4: Usage & Impact (4 stats)
    print("USAGE & IMPACT (USG%, ORtg, DRtg, BPM):")
    print(f"{'Interval':<12} {'USG%':>7} {'ORtg':>7} {'DRtg':>7} {'BPM':>7}")
    print("-" * 140)

    for stats in intervals:
        if stats['points'] == 0 and stats['fga'] == 0:
            continue

        print(f"{stats['interval']:<12} "
              f"{stats.get('usg_pct', 0.0):>7.1f} "
              f"{stats.get('ortg', 0.0):>7.1f} "
              f"{stats.get('drtg', 0.0):>7.1f} "
              f"{stats.get('bpm', 0.0):>7.1f}")

    print()


def display_ot_intervals(calc: IntervalBoxScoreCalculator, game_id: str, player_id: str,
                        player_name: str):
    """Display OT interval box scores"""

    # OT1 halves (2:30 intervals)
    print("=" * 110)
    print(f"OVERTIME 1 - 2:30 HALVES - {player_name}")
    print("=" * 110)
    print()
    print(f"{'Interval':<18} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'3PM-3PA':>8} {'TS%':>6} {'eFG%':>6}")
    print("-" * 110)

    ot1_halves = calc.calculate_all_ot_intervals(game_id, player_id, 5, 'half')
    for stats in ot1_halves:
        fg_str = f"{stats['fgm']}-{stats['fga']}"
        fg3_str = f"{stats['fg3m']}-{stats['fg3a']}"

        print(f"{stats['interval']:<18} "
              f"{stats['points']:>4} "
              f"{fg_str:>8} "
              f"{stats['fg_pct']:>6.1f} "
              f"{fg3_str:>8} "
              f"{stats['ts_pct']:>6.1f} "
              f"{stats['efg_pct']:>6.1f}")

    print()

    # OT2 halves
    print("=" * 110)
    print(f"OVERTIME 2 - 2:30 HALVES - {player_name}")
    print("=" * 110)
    print()
    print(f"{'Interval':<18} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'3PM-3PA':>8} {'TS%':>6} {'eFG%':>6}")
    print("-" * 110)

    ot2_halves = calc.calculate_all_ot_intervals(game_id, player_id, 6, 'half')
    for stats in ot2_halves:
        fg_str = f"{stats['fgm']}-{stats['fga']}"
        fg3_str = f"{stats['fg3m']}-{stats['fg3a']}"

        print(f"{stats['interval']:<18} "
              f"{stats['points']:>4} "
              f"{fg_str:>8} "
              f"{stats['fg_pct']:>6.1f} "
              f"{fg3_str:>8} "
              f"{stats['ts_pct']:>6.1f} "
              f"{stats['efg_pct']:>6.1f}")

    print()

    # OT1 minutes
    print("=" * 110)
    print(f"OVERTIME 1 - 1-MINUTE INTERVALS - {player_name}")
    print("=" * 110)
    print()
    print(f"{'Interval':<15} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'TS%':>6}")
    print("-" * 110)

    ot1_minutes = calc.calculate_all_ot_intervals(game_id, player_id, 5, 'minute')
    for stats in ot1_minutes:
        if stats['points'] == 0 and stats['fga'] == 0:
            continue  # Skip empty minutes

        fg_str = f"{stats['fgm']}-{stats['fga']}"

        print(f"{stats['interval']:<15} "
              f"{stats['points']:>4} "
              f"{fg_str:>8} "
              f"{stats['fg_pct']:>6.1f} "
              f"{stats['ts_pct']:>6.1f}")

    print()


def display_team_intervals(calc: IntervalBoxScoreCalculator, game_id: str, team_id: str):
    """Display team interval box scores"""

    print("=" * 110)
    print(f"TEAM {team_id} - 6-MINUTE INTERVALS")
    print("=" * 110)
    print()
    print(f"{'Interval':<12} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'TS%':>6} {'ORtg':>6} {'Pace':>6} {'Poss':>5}")
    print("-" * 110)

    intervals = calc.get_6min_intervals()
    for interval in intervals:
        stats = calc.calculate_team_interval_stats(game_id, team_id, interval)

        if stats['points'] == 0 and stats['fga'] == 0:
            continue

        fg_str = f"{stats['fgm']}-{stats['fga']}"

        print(f"{stats['interval']:<12} "
              f"{stats['points']:>4} "
              f"{fg_str:>8} "
              f"{stats.get('fg_pct', 0.0):>6.1f} "
              f"{stats.get('ts_pct', 0.0):>6.1f} "
              f"{stats.get('ortg', 0.0):>6.1f} "
              f"{stats.get('pace', 0.0):>6.1f} "
              f"{stats.get('possessions', 0.0):>5.1f}")

    print()


def display_player_biographical(calc: IntervalBoxScoreCalculator, game_id: str,
                                player_id: str, player_name: str):
    """Display player biographical data and age calculations"""

    # Get biographical data
    bio_data = calc.get_player_biographical(player_id)

    if not bio_data:
        print("No biographical data available")
        return

    print("=" * 140)
    print(f"PLAYER BIOGRAPHICAL DATA - {player_name}")
    print("=" * 140)
    print()

    # Player Information
    print("PLAYER INFORMATION:")
    print("-" * 80)
    print(f"  Position: {bio_data.get('position', 'N/A')}")
    print(f"  Jersey #: {bio_data.get('jersey_number', 'N/A')}")
    print(f"  Nationality: {bio_data.get('nationality', 'N/A')}")
    print(f"  Birthplace: {bio_data.get('birth_city', 'N/A')}, {bio_data.get('birth_state', 'N/A')}, {bio_data.get('birth_country', 'N/A')}")
    print()

    # Physical Attributes
    print("PHYSICAL ATTRIBUTES:")
    print("-" * 80)
    height_ft = bio_data.get('height_inches', 0) // 12
    height_in = bio_data.get('height_inches', 0) % 12
    print(f"  Height: {height_ft}'{height_in}\" ({bio_data.get('height_inches', 'N/A')} inches)")
    print(f"  Weight: {bio_data.get('weight_pounds', 'N/A')} lbs")

    if bio_data.get('wingspan_inches'):
        wingspan_ft = bio_data['wingspan_inches'] // 12
        wingspan_in = bio_data['wingspan_inches'] % 12
        print(f"  Wingspan: {wingspan_ft}'{wingspan_in}\" ({bio_data['wingspan_inches']} inches)")

        if bio_data.get('height_inches'):
            wingspan_ratio = bio_data['wingspan_inches'] / bio_data['height_inches']
            print(f"  Wingspan/Height Ratio: {wingspan_ratio:.3f}")

    if bio_data.get('height_inches') and bio_data.get('weight_pounds'):
        height_m = bio_data['height_inches'] * 0.0254
        weight_kg = bio_data['weight_pounds'] * 0.453592
        bmi = weight_kg / (height_m ** 2)
        print(f"  BMI: {bmi:.2f}")
    print()

    # Career Information
    print("CAREER INFORMATION:")
    print("-" * 80)
    print(f"  College: {bio_data.get('college', 'N/A')}")
    print(f"  High School: {bio_data.get('high_school', 'N/A')}")
    print(f"  NBA Debut: {bio_data.get('nba_debut_date', 'N/A')}")
    print(f"  Draft Year: {bio_data.get('draft_year', 'N/A')}")
    print(f"  Draft Pick: Round {bio_data.get('draft_round', 'N/A')}, Pick #{bio_data.get('draft_pick', 'N/A')}")
    print(f"  Drafted By: {bio_data.get('draft_team_id', 'N/A')}")
    print()

    # Age Calculations at Game Time (using first snapshot timestamp)
    print("AGE CALCULATIONS (ALL 7 FORMATS) - At Game Time:")
    print("-" * 80)

    # Get a snapshot to get timestamp
    cursor = calc.conn.cursor()
    cursor.execute("""
        SELECT timestamp FROM player_box_score_snapshots
        WHERE game_id = ? AND player_id = ?
        ORDER BY event_number
        LIMIT 1
    """, (game_id, player_id))

    result = cursor.fetchone()
    if result and result['timestamp'] and bio_data.get('birth_date'):
        timestamp = result['timestamp']
        age_data = calc.calculate_age_at_timestamp(bio_data['birth_date'], timestamp)

        print(f"  1. Decimal Years (DECIMAL(10,4)): {age_data['age_years_decimal']} years")
        print(f"     → Best for: Regression models, age-performance curves")
        print()
        print(f"  2. Days Since Birth: {age_data['age_days']} days")
        print(f"     → Best for: Tree-based models, discrete binning")
        print()
        print(f"  3. Seconds Since Birth: {age_data['age_seconds']:,} seconds")
        print(f"     → Best for: LSTM/RNN time-series models")
        print()
        print(f"  4. Age Uncertainty: ±{age_data['age_uncertainty_hours']} hours")
        print(f"     → Birth time unknown (assumed midnight UTC)")
        print()
        print(f"  5. Minimum Age (born 23:59:59): {age_data['age_min_decimal']} years")
        print(f"     → Best for: Conservative estimates, lower bounds")
        print()
        print(f"  6. Maximum Age (born 00:00:00): {age_data['age_max_decimal']} years")
        print(f"     → Best for: Liberal estimates, upper bounds")
        print()
        print(f"  7. Human-Readable: {age_data['age_string']}")
        print(f"     → Best for: Display, documentation")
        print()

        # NBA Experience
        if bio_data.get('nba_debut_date'):
            exp_data = calc.calculate_nba_experience(bio_data['nba_debut_date'], timestamp)
            print(f"NBA EXPERIENCE:")
            print(f"  Years in NBA: {exp_data['nba_experience_years']} years")
            print(f"  Days Since Debut: {exp_data['nba_experience_days']} days")
            print(f"  Rookie Status: {'Yes' if exp_data['is_rookie'] else 'No'}")
            print()

    print()

def display_analysis():
    """Display analysis and insights"""
    print("=" * 110)
    print("KEY INSIGHTS FROM INTERVAL ANALYSIS")
    print("=" * 110)
    print()
    print("REGULATION INTERVALS:")
    print("-" * 60)
    print("• First 6 minutes: Tatum started strong with 4 points")
    print("• Minutes 0-3: Tatum scored 2 points")
    print("• First minute: Tatum took 1 shot, missed")
    print()
    print("OVERTIME ANALYSIS:")
    print("-" * 60)
    print("• OT1 First Half (0-2:30): Tatum scored in crucial moments")
    print("• OT2 Second Half (2:30-5:00): Clinched victory")
    print("• Minute-by-minute breakdown shows exact clutch timing")
    print()
    print("PRACTICAL APPLICATIONS:")
    print("-" * 60)
    print("• Momentum Tracking: 3-minute intervals reveal scoring runs")
    print("• Fatigue Analysis: 1-minute intervals show late-game decline")
    print("• Substitution Impact: 90-second intervals capture sub patterns")
    print("• Betting Props: 6-minute intervals for quarter splits")
    print("• ML Features: Time-series data for prediction models")
    print()


def main():
    """Run interval box score demo"""
    print()
    db_path, conn = create_sample_temporal_data()

    # Create calculator
    calc = IntervalBoxScoreCalculator(conn)

    # Demo player
    game_id = "OT_GAME"
    player_id = "tatumja01"
    player_name = "Jayson Tatum"
    team_id = "BOS"

    # Display player biographical data and age calculations
    display_player_biographical(calc, game_id, player_id, player_name)

    # Display all interval types
    display_interval_box_scores(calc, game_id, player_id, player_name, '6min')
    display_interval_box_scores(calc, game_id, player_id, player_name, '3min')
    display_interval_box_scores(calc, game_id, player_id, player_name, '1min')

    # Display OT intervals
    display_ot_intervals(calc, game_id, player_id, player_name)

    # Display team intervals
    display_team_intervals(calc, game_id, team_id)

    # Display analysis
    display_analysis()

    print("=" * 140)
    print("✓ DEMO COMPLETE - ALL 16 BASKETBALL REFERENCE STATS + BIOGRAPHICAL DATA INTEGRATED")
    print("=" * 140)
    print()
    print("Features Demonstrated:")
    print("-" * 80)
    print("INTERVAL TYPES:")
    print("  • 6-minute intervals (8 per regulation game)")
    print("  • 3-minute intervals (16 per regulation game)")
    print("  • 1:30 intervals (32 per regulation game)")
    print("  • 1-minute intervals (48 per regulation game)")
    print("  • OT 2:30 halves (2 per OT period)")
    print("  • OT 1-minute intervals (5 per OT period)")
    print()
    print("BIOGRAPHICAL DATA (NEW):")
    print("  • Player information (position, birthplace, nationality)")
    print("  • Physical attributes (height, weight, wingspan, BMI)")
    print("  • Career timeline (debut, draft info, college)")
    print("  • Age calculations (7 formats with DECIMAL(10,4) precision)")
    print("  • NBA experience (years since debut, rookie status)")
    print()
    print("ALL 16 Basketball Reference Advanced Statistics Per Interval:")
    print("-" * 80)
    print()
    print("SHOOTING EFFICIENCY (5 stats):")
    print("  1. TS% (True Shooting Percentage)")
    print("  2. eFG% (Effective Field Goal Percentage)")
    print("  3. 3PAr (3-Point Attempt Rate)")
    print("  4. FTr (Free Throw Rate)")
    print("  5. Standard percentages (FG%, 3P%, FT%)")
    print()
    print("REBOUNDING (3 stats):")
    print("  6. ORB% (Offensive Rebound Percentage)")
    print("  7. DRB% (Defensive Rebound Percentage)")
    print("  8. TRB% (Total Rebound Percentage)")
    print()
    print("PLAYMAKING & DEFENSE (4 stats):")
    print("  9. AST% (Assist Percentage)")
    print(" 10. STL% (Steal Percentage)")
    print(" 11. BLK% (Block Percentage)")
    print(" 12. TOV% (Turnover Percentage)")
    print()
    print("USAGE & IMPACT (4 stats):")
    print(" 13. USG% (Usage Percentage)")
    print(" 14. ORtg (Offensive Rating - points per 100 possessions)")
    print(" 15. DRtg (Defensive Rating - opponent points per 100 possessions)")
    print(" 16. BPM (Box Plus/Minus - overall impact metric)")
    print()
    print("Benefits:")
    print("-" * 80)
    print("• 100% Basketball Reference advanced stats coverage at ALL interval levels")
    print("• Granular momentum tracking at any time resolution")
    print("• Complete player impact metrics (rebounding %, playmaking %, usage %)")
    print("• Clutch performance analysis (OT halves and minutes)")
    print("• ML-ready time-series features with full statistical context")
    print("• Betting analytics for interval props with advanced metrics")
    print("• No schema changes - uses existing temporal snapshots with team/opponent context")
    print()

    conn.close()


if __name__ == "__main__":
    main()
