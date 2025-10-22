#!/usr/bin/env python3
"""
Second-by-Second and Decisecond Interval Demo

Demonstrates maximum time granularity for temporal box scores:
- Second-by-second intervals (2,880 per regulation, 300 per OT)
- Decisecond (0.1s) intervals for final minute
- Buzzer beater analysis
- ML-ready high-frequency time-series data

Created: October 19, 2025
"""

import sqlite3
import sys
from pathlib import Path

# Add the pbp_to_boxscore directory to path
sys.path.insert(0, str(Path(__file__).parent))

from interval_box_score_calculator import IntervalBoxScoreCalculator, TimeInterval


def create_sample_data_with_second_precision():
    """Create sample temporal box score data with second-level snapshots"""
    db_path = "/tmp/second_demo.db"

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
            timestamp TEXT,

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
            minutes REAL DEFAULT 0.0,

            UNIQUE(game_id, event_number, player_id)
        )
    """)

    # Create player biographical table
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

    # Insert Jayson Tatum biographical data
    tatum_bio = (
        "tatumja01",                            # player_id
        "1998-03-03",                           # birth_date (March 3, 1998)
        "day",                                  # birth_date_precision
        "St. Louis",                            # birth_city
        "Missouri",                             # birth_state
        "USA",                                  # birth_country
        80,                                     # height_inches (6'8")
        210,                                    # weight_pounds
        85,                                     # wingspan_inches (7'1")
        "2017-10-17",                           # nba_debut_date
        None,                                   # nba_retirement_date (active)
        2017,                                   # draft_year
        1,                                      # draft_round
        3,                                      # draft_pick
        "BOS",                                  # draft_team_id
        "Duke",                                 # college
        "Chaminade College Preparatory School", # high_school
        "USA",                                  # nationality
        "SF",                                   # position
        0,                                      # jersey_number
        "nba_api"                               # data_source
    )
    cursor.execute("""
        INSERT INTO player_biographical
        (player_id, birth_date, birth_date_precision, birth_city, birth_state, birth_country,
         height_inches, weight_pounds, wingspan_inches,
         nba_debut_date, nba_retirement_date,
         draft_year, draft_round, draft_pick, draft_team_id,
         college, high_school,
         nationality, position, jersey_number, data_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tatum_bio)

    # Insert Tatum snapshots for final 15 seconds of regulation
    # Simulating a buzzer beater scenario
    # Starting at 2865 seconds (47:45 remaining) through 2880 (end)
    # Game on October 22, 2024 at 7:30 PM ET (final 15 seconds at ~8:18 PM)

    game_id = "BUZZER_GAME"
    player_id = "tatumja01"
    player_name = "Jayson Tatum"

    # Game tied at 110-110 going into final 15 seconds
    # Tatum has 32 points on 12-24 FG
    # Tatum's age at this moment: 26.6412 years (born March 3, 1998)

    snapshots = [
        # 15 seconds left (47:45) - Inbound
        (game_id, 2850, player_id, player_name, "BOS", 4, 2865, "2024-10-22 20:17:45", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.75),

        # 14 seconds - Dribbling
        (game_id, 2851, player_id, player_name, "BOS", 4, 2866, "2024-10-22 20:17:46", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.77),

        # 13 seconds - Dribbling
        (game_id, 2852, player_id, player_name, "BOS", 4, 2867, "2024-10-22 20:17:47", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.78),

        # 12 seconds - Call play
        (game_id, 2853, player_id, player_name, "BOS", 4, 2868, "2024-10-22 20:17:48", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.80),

        # 11 seconds - Drive starts
        (game_id, 2854, player_id, player_name, "BOS", 4, 2869, "2024-10-22 20:17:49", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.82),

        # 10 seconds - Driving
        (game_id, 2855, player_id, player_name, "BOS", 4, 2870, "2024-10-22 20:17:50", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.83),

        # 9 seconds - Crossover
        (game_id, 2856, player_id, player_name, "BOS", 4, 2871, "2024-10-22 20:17:51", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.85),

        # 8 seconds - Step back
        (game_id, 2857, player_id, player_name, "BOS", 4, 2872, "2024-10-22 20:17:52", 32, 12, 24, 5, 13, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.87),

        # 7 seconds - SHOT ATTEMPT
        (game_id, 2858, player_id, player_name, "BOS", 4, 2873, "2024-10-22 20:17:53", 32, 12, 25, 5, 14, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.88),

        # 6 seconds - SHOT MADE! 3-pointer! 113-110 Celtics lead!
        (game_id, 2859, player_id, player_name, "BOS", 4, 2874, "2024-10-22 20:17:54", 35, 13, 25, 6, 14, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.90),

        # 5 seconds - Opponent timeout
        (game_id, 2860, player_id, player_name, "BOS", 4, 2875, "2024-10-22 20:17:55", 35, 13, 25, 6, 14, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.92),

        # 4 seconds - Defending
        (game_id, 2861, player_id, player_name, "BOS", 4, 2876, "2024-10-22 20:17:56", 35, 13, 25, 6, 14, 2, 2, 0, 5, 5, 2, 1, 1, 3, 2, 47.93),

        # 3 seconds - Steal!
        (game_id, 2862, player_id, player_name, "BOS", 4, 2877, "2024-10-22 20:17:57", 35, 13, 25, 6, 14, 2, 2, 0, 5, 5, 2, 2, 1, 3, 2, 47.95),

        # 2 seconds - Fouled!
        (game_id, 2863, player_id, player_name, "BOS", 4, 2878, "2024-10-22 20:17:58", 35, 13, 25, 6, 14, 2, 3, 0, 5, 5, 2, 2, 1, 3, 3, 47.97),

        # 1 second - FT made
        (game_id, 2864, player_id, player_name, "BOS", 4, 2879, "2024-10-22 20:17:59", 36, 13, 25, 6, 14, 3, 3, 0, 5, 5, 2, 2, 1, 3, 3, 47.98),

        # 0 seconds - FINAL
        (game_id, 2865, player_id, player_name, "BOS", 4, 2880, "2024-10-22 20:18:00", 36, 13, 25, 6, 14, 3, 3, 0, 5, 5, 2, 2, 1, 3, 3, 48.00),
    ]

    for row in snapshots:
        cursor.execute("""
            INSERT INTO player_box_score_snapshots
            (game_id, event_number, player_id, player_name, team_id, period, time_elapsed_seconds, timestamp,
             points, fgm, fga, fg3m, fg3a, ftm, fta,
             oreb, dreb, reb, ast, stl, blk, tov, pf, minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # Insert BOS team snapshots for final 15 seconds (simplified - just enough for demo)
    team_snapshots = [
        # Basic team stats - starting tied 110-110, ending 114-110
        (game_id, 2850, "BOS", 4, 2865, 110, 42, 88, 15, 38, 11, 14, 8, 28, 36, 25, 5, 3, 10, 15),
        (game_id, 2859, "BOS", 4, 2874, 113, 43, 89, 16, 39, 11, 14, 8, 28, 36, 25, 5, 3, 10, 15),  # After Tatum 3PT
        (game_id, 2864, "BOS", 4, 2879, 114, 43, 89, 16, 39, 12, 15, 8, 28, 36, 25, 6, 3, 10, 16),  # After FT
        (game_id, 2865, "BOS", 4, 2880, 114, 43, 89, 16, 39, 12, 15, 8, 28, 36, 25, 6, 3, 10, 16),  # Final
    ]

    for row in team_snapshots:
        cursor.execute("""
            INSERT INTO team_box_score_snapshots
            (game_id, event_number, team_id, period, time_elapsed_seconds,
             points, fgm, fga, fg3m, fg3a, ftm, fta,
             oreb, dreb, reb, ast, stl, blk, tov, pf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    conn.commit()
    print(f"✓ Created second-level temporal database: {db_path}\n")
    return db_path, conn


def display_player_biographical(calc: IntervalBoxScoreCalculator, game_id: str,
                                player_id: str, player_name: str):
    """Display player biographical data and age calculations"""

    print("=" * 120)
    print(f"PLAYER BIOGRAPHICAL DATA - {player_name}")
    print("=" * 120)
    print()

    # Get biographical data
    bio_data = calc.get_player_biographical(player_id)

    if not bio_data:
        print(f"⚠️  No biographical data found for {player_name}")
        return

    print("PLAYER INFORMATION:")
    print("-" * 60)
    print(f"  Name: {player_name}")
    print(f"  Player ID: {player_id}")
    print(f"  Position: {bio_data['position']}")
    print(f"  Jersey Number: #{bio_data['jersey_number']}")
    print()

    print("PHYSICAL ATTRIBUTES:")
    print("-" * 60)
    print(f"  Height: {bio_data['height_inches']} inches (6'8\")")
    print(f"  Weight: {bio_data['weight_pounds']} lbs")
    print(f"  Wingspan: {bio_data['wingspan_inches']} inches (7'1\")")

    # Calculate BMI
    height_m = bio_data['height_inches'] * 0.0254
    weight_kg = bio_data['weight_pounds'] * 0.453592
    bmi = weight_kg / (height_m ** 2)
    print(f"  BMI: {bmi:.2f}")

    # Wingspan ratio
    wingspan_ratio = bio_data['wingspan_inches'] / bio_data['height_inches']
    print(f"  Wingspan/Height Ratio: {wingspan_ratio:.3f}")
    print()

    print("CAREER TIMELINE:")
    print("-" * 60)
    print(f"  Birth Date: {bio_data['birth_date']} (St. Louis, MO)")
    print(f"  Birth Precision: ±{24} hours (time unknown, assumed midnight UTC)")
    print(f"  NBA Debut: {bio_data['nba_debut_date']}")
    print(f"  Draft: {bio_data['draft_year']} - Round {bio_data['draft_round']}, Pick {bio_data['draft_pick']}")
    print(f"  Draft Team: {bio_data['draft_team_id']}")
    print(f"  College: {bio_data['college']}")
    print()

    # Get first snapshot to calculate age
    cursor = calc.conn.cursor()
    cursor.execute("""
        SELECT timestamp FROM player_box_score_snapshots
        WHERE game_id = ? AND player_id = ?
        ORDER BY time_elapsed_seconds
        LIMIT 1
    """, (game_id, player_id))
    result = cursor.fetchone()

    if result:
        timestamp = result[0]
        age_data = calc.calculate_age_at_timestamp(bio_data['birth_date'], timestamp)

        print("AGE AT GAME TIME (7 ML-OPTIMIZED FORMATS):")
        print("-" * 60)
        print(f"1. Decimal Years: {age_data['age_years_decimal']:.4f} years")
        print(f"   → Best for: Regression models, age-performance curves, neural networks")
        print()
        print(f"2. Days Since Birth: {age_data['age_days']:,} days")
        print(f"   → Best for: Tree-based models (RF, XGBoost), discrete binning")
        print()
        print(f"3. Total Seconds: {age_data['age_seconds']:,} seconds")
        print(f"   → Best for: LSTM/RNN time-series models, exact temporal precision")
        print()
        print(f"4. Age Uncertainty: ±{age_data['age_uncertainty_hours']} hours")
        print(f"   → Best for: Model confidence scoring, uncertainty-aware predictions")
        print()
        print(f"5. Minimum Age: {age_data['age_min_decimal']:.4f} years (born at 23:59:59)")
        print(f"   → Best for: Conservative estimates, lower bound calculations")
        print()
        print(f"6. Maximum Age: {age_data['age_max_decimal']:.4f} years (born at 00:00:00)")
        print(f"   → Best for: Liberal estimates, upper bound calculations")
        print()
        print(f"7. Human Readable: {age_data['age_string']}")
        print(f"   → Best for: Display, documentation, user-facing applications")
        print()

        # NBA experience
        exp_data = calc.calculate_nba_experience(bio_data['nba_debut_date'], timestamp)
        print("NBA EXPERIENCE:")
        print("-" * 60)
        print(f"  Years in NBA: {exp_data['nba_experience_years']:.4f} years")
        print(f"  Days Since Debut: {exp_data['nba_experience_days']:,} days")
        print(f"  Rookie Status: {'Yes' if exp_data['is_rookie'] else 'No'}")
        print()


def display_age_evolution(calc: IntervalBoxScoreCalculator, game_id: str,
                          player_id: str, player_name: str):
    """Display age evolution over final 15 seconds - demonstrates time-varying ML feature"""

    print("=" * 120)
    print(f"AGE EVOLUTION ANALYSIS - FINAL 15 SECONDS - {player_name}")
    print("=" * 120)
    print()
    print("Demonstrates age as a TIME-VARYING FEATURE for ML models")
    print("Age precision: DECIMAL(10,4) = 4 decimal places")
    print()

    # Get biographical data
    bio_data = calc.get_player_biographical(player_id)
    birth_date = bio_data['birth_date']

    # Get snapshots for final 15 seconds
    cursor = calc.conn.cursor()
    cursor.execute("""
        SELECT time_elapsed_seconds, timestamp, points, fgm, fga, stl
        FROM player_box_score_snapshots
        WHERE game_id = ? AND player_id = ? AND period = 4
        AND time_elapsed_seconds >= 2865 AND time_elapsed_seconds <= 2880
        ORDER BY time_elapsed_seconds
    """, (game_id, player_id))

    snapshots = cursor.fetchall()

    print(f"{'Second':<12} {'Timestamp':<20} {'Age (Seconds)':<18} {'Age (Years)':<15} {'Event':<30}")
    print("-" * 120)

    # Event descriptions
    events = {
        2865: "Inbound - 15s left",
        2866: "Dribbling",
        2867: "Dribbling",
        2868: "Call play",
        2869: "Drive starts",
        2870: "Driving",
        2871: "Crossover",
        2872: "Step back",
        2873: "SHOT ATTEMPT!",
        2874: "3-PT MADE! 113-110",
        2875: "Opponent timeout",
        2876: "Defense",
        2877: "STEAL!",
        2878: "Fouled",
        2879: "FT MADE - 114-110",
        2880: "FINAL BUZZER",
    }

    ages_seconds = []
    ages_years = []

    for snapshot in snapshots:
        time_sec, timestamp, points, fgm, fga, stl = snapshot

        # Calculate age at this exact second
        age_data = calc.calculate_age_at_timestamp(birth_date, timestamp)
        ages_seconds.append(age_data['age_seconds'])
        ages_years.append(age_data['age_years_decimal'])

        event = events.get(time_sec, "")

        print(f"{time_sec}s       "
              f"{timestamp:<20} "
              f"{age_data['age_seconds']:>15,}  "
              f"{age_data['age_years_decimal']:>13.4f}  "
              f"{event:<30}")

    print()
    print("AGE DELTA ANALYSIS (Age change over 15 seconds):")
    print("-" * 60)
    age_delta_seconds = ages_seconds[-1] - ages_seconds[0]
    age_delta_years = ages_years[-1] - ages_years[0]
    print(f"  Seconds elapsed: 15")
    print(f"  Age change (seconds): {age_delta_seconds:,} seconds")
    print(f"  Age change (years): {age_delta_years:.10f} years")
    print(f"  Age change (days): {age_delta_years * 365.25:.10f} days")
    print()
    print("ML TIME-SERIES IMPLICATIONS:")
    print("-" * 60)
    print("  • LSTM Models: Age_seconds provides monotonically increasing feature")
    print("  • Transformer Models: Age as positional encoding + time-varying context")
    print("  • RNN Models: Captures aging effect across 2,880 timesteps per game")
    print("  • Fatigue Modeling: Age × Time_elapsed interaction for energy depletion")
    print("  • Career Arc: Age trajectory combined with performance metrics")
    print()


def display_final_seconds(calc: IntervalBoxScoreCalculator, game_id: str,
                          player_id: str, player_name: str):
    """Display second-by-second breakdown of final 15 seconds"""

    print("=" * 120)
    print(f"SECOND-BY-SECOND ANALYSIS - FINAL 15 SECONDS - {player_name}")
    print("=" * 120)
    print()
    print(f"{'Second':<12} {'Event':<30} {'PTS':>4} {'FGM-FGA':>8} {'FG%':>6} {'TS%':>6} {'STL':>4} {'Game Situation':<25}")
    print("-" * 120)

    # Get final 15 seconds (2865-2880)
    final_15 = calc.calculate_seconds_range(game_id, player_id, 2865, 2880, period=4)

    # Event descriptions for each second
    events = {
        2865: ("Inbound", "Tied 110-110, 15 sec left"),
        2866: ("Dribbling", "Advancing ball"),
        2867: ("Dribbling", "Crossing halfcourt"),
        2868: ("Call play", "Setting up offense"),
        2869: ("Drive starts", "Attacking basket"),
        2870: ("Driving", "Into the paint"),
        2871: ("Crossover", "Creating space"),
        2872: ("Step back", "Shot preparation"),
        2873: ("SHOT!", "3-PT ATTEMPT!"),
        2874: ("BUCKET!", "3-PT MADE! 113-110 BOS"),
        2875: ("Timeout", "Opponent calls timeout"),
        2876: ("Defense", "Defending inbound"),
        2877: ("STEAL!", "Turnover forced!"),
        2878: ("Fouled", "Intentional foul"),
        2879: ("FT MADE", "114-110 BOS, 1 sec left"),
    }

    for stats in final_15:
        second = stats['start_seconds']
        event_desc, situation = events.get(second, ("", ""))

        if stats['points'] > 0 or stats['fga'] > 0 or stats['stl'] > 0:
            fg_str = f"{stats['fgm']}-{stats['fga']}"
            print(f"{second}s-{second+1}s  "
                  f"{event_desc:<30} "
                  f"{stats['points']:>4} "
                  f"{fg_str:>8} "
                  f"{stats['fg_pct']:>6.1f} "
                  f"{stats['ts_pct']:>6.1f} "
                  f"{stats['stl']:>4} "
                  f"{situation:<25}")

    print()


def display_decisecond_breakdown(calc: IntervalBoxScoreCalculator, game_id: str,
                                 player_id: str, player_name: str):
    """Display 0.1-second breakdown of final 5 seconds"""

    print("=" * 100)
    print(f"DECISECOND (0.1s) ANALYSIS - FINAL 5 SECONDS - {player_name}")
    print("=" * 100)
    print()
    print("Note: This demonstrates 0.1s precision. Real play-by-play data may only have second-level precision.")
    print()
    print(f"{'Time':<12} {'Event':<40} {'PTS':>4} {'FGM':>4} {'FGA':>4}")
    print("-" * 100)

    # Get final 5 seconds with decisecond precision (2875-2880)
    final_5_decisec = calc.calculate_deciseconds_range(game_id, player_id, 2875.0, 2880.0, period=4)

    # Show only seconds with activity (since we have second-level data)
    active_seconds = []
    for i, stats in enumerate(final_5_decisec):
        # Group by second
        second = int(stats['start_seconds'])
        if second not in active_seconds:
            active_seconds.append(second)

            events_by_second = {
                2875: "Opponent timeout - defending lead",
                2876: "Defending inbound pass",
                2877: "STEAL! Turnover forced!",
                2878: "Fouled - going to line",
                2879: "FREE THROW MADE - 114-110"
            }

            event = events_by_second.get(second, "")

            if stats['points'] > 0 or stats['stl'] > 0:
                time_label = f"{second}s-{second+1}s"
                print(f"{time_label:<12} {event:<40} {stats['points']:>4} {stats['fgm']:>4} {stats['fga']:>4}")

    print()
    print("ℹ️  With actual sub-second data, would show:")
    print("   4.9s-5.0s: Timeout ends")
    print("   4.1s-4.2s: Inbound pass")
    print("   3.2s-3.3s: Steal occurs")
    print("   2.8s-2.9s: Foul called")
    print("   1.5s-1.6s: Free throw released")
    print("   1.4s-1.5s: Free throw made!")
    print()


def display_ml_applications(calc: IntervalBoxScoreCalculator, game_id: str,
                           player_id: str):
    """Demonstrate ML feature extraction from second-level data"""

    print("=" * 100)
    print("MACHINE LEARNING APPLICATIONS - HIGH-FREQUENCY TIME-SERIES DATA")
    print("=" * 100)
    print()

    # Extract second-level features
    print("1. TIME-SERIES FEATURE EXTRACTION")
    print("-" * 60)

    # Get a sample range (final minute)
    final_minute = calc.calculate_seconds_range(game_id, player_id, 2820, 2880, period=4)

    print(f"   Sample size: {len(final_minute)} one-second intervals")
    print(f"   Time range: Final 60 seconds of regulation")
    print()

    # Calculate features
    scoring_events = [s['points'] for s in final_minute if s['points'] > 0]
    shot_attempts = [s['fga'] for s in final_minute if s['fga'] > 0]

    print(f"   Scoring events: {len(scoring_events)}")
    print(f"   Shot attempts: {len(shot_attempts)}")
    print()

    print("2. POTENTIAL ML FEATURES FROM SECOND-LEVEL DATA")
    print("-" * 60)
    features = [
        "• Scoring rate (points per second)",
        "• Shot frequency (attempts per second)",
        "• Time since last event",
        "• Scoring momentum (rolling average)",
        "• Clutch timing (seconds < 10 with close score)",
        "• Event density (events per second)",
        "• Performance under pressure (stats when seconds < 30)",
        "• Buzzer beater probability (distance from basket × time remaining)"
    ]

    for feature in features:
        print(f"   {feature}")

    print()

    print("3. TIME-SERIES MODELS ENABLED")
    print("-" * 60)
    models = [
        "• LSTM (Long Short-Term Memory) - 2,880 timesteps per game",
        "• Transformer - Attention over second-level events",
        "• CNN - Conv1D over temporal patterns",
        "• RNN - Recurrent patterns in scoring",
        "• Prophet - Time-series forecasting",
        "• ARIMA - Autoregressive scoring models"
    ]

    for model in models:
        print(f"   {model}")

    print()


def display_summary():
    """Display summary and benefits"""
    print("=" * 100)
    print("SUMMARY - SECOND AND DECISECOND INTERVALS")
    print("=" * 100)
    print()

    print("GRANULARITY ACHIEVED:")
    print("-" * 60)
    print("  • Second-by-Second: 2,880 intervals per regulation game")
    print("  • Second-by-Second OT: 300 intervals per overtime period")
    print("  • Decisecond (0.1s): 600 intervals for final minute")
    print("  • Decisecond Range: Any time range with 0.1s precision")
    print()

    print("KEY CAPABILITIES:")
    print("-" * 60)
    print("  ✅ Buzzer beater analysis - exact timing of game-winning shots")
    print("  ✅ Clutch performance - second-by-second pressure situations")
    print("  ✅ ML time-series - 2,880+ data points per game")
    print("  ✅ Shot clock correlation - performance by second on clock")
    print("  ✅ Momentum tracking - scoring runs at finest granularity")
    print("  ✅ Event timing - precise temporal patterns")
    print()

    print("USE CASES:")
    print("-" * 60)
    print("  1. Buzzer Beaters: Identify exact second of game-winning plays")
    print("  2. Clutch Analysis: Performance in final 10 seconds")
    print("  3. ML Models: LSTM/Transformer on second-level sequences")
    print("  4. Shot Clock: Correlation between time and efficiency")
    print("  5. Momentum: Detect 5-second scoring bursts")
    print("  6. Pressure: Stats when time < 10s and game close")
    print()

    print("COMPLETE TEMPORAL HIERARCHY:")
    print("-" * 60)
    print("  1. Full Game (48 minutes)")
    print("  2. Halves (2: H1, H2)")
    print("  3. Quarters (4: Q1-Q4)")
    print("  4. 6-Minute Intervals (8)")
    print("  5. 3-Minute Intervals (16)")
    print("  6. 1:30 Intervals (32)")
    print("  7. 1-Minute Intervals (48)")
    print("  8. 1-Second Intervals (2,880)")
    print("  9. 0.1-Second Intervals (600 for final minute)")
    print(" 10. Any Exact Moment (temporal snapshots)")
    print()

    print("✨ This is the most comprehensive temporal box score system with")
    print("   granularity from full game down to deciseconds!")
    print()


def main():
    """Run second and decisecond interval demo"""
    print()
    db_path, conn = create_sample_data_with_second_precision()

    # Create calculator
    calc = IntervalBoxScoreCalculator(conn)

    # Demo data
    game_id = "BUZZER_GAME"
    player_id = "tatumja01"
    player_name = "Jayson Tatum"

    # Display biographical data and age evolution FIRST
    display_player_biographical(calc, game_id, player_id, player_name)
    display_age_evolution(calc, game_id, player_id, player_name)

    # Display interval demonstrations
    display_final_seconds(calc, game_id, player_id, player_name)
    display_decisecond_breakdown(calc, game_id, player_id, player_name)
    display_ml_applications(calc, game_id, player_id)
    display_summary()

    conn.close()


if __name__ == "__main__":
    main()
