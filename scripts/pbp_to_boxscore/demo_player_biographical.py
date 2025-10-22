#!/usr/bin/env python3
"""
Player Biographical Data Integration Demo

Demonstrates biographical data features for machine learning:
- Age calculations (7 formats) at any timestamp
- Physical attributes (height, weight, wingspan, BMI)
- NBA experience tracking
- Career timeline analysis
- Multi-player comparisons
- Age-performance correlation features

Created: October 19, 2025
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List

# Add the pbp_to_boxscore directory to path
sys.path.insert(0, str(Path(__file__).parent))

from interval_box_score_calculator import IntervalBoxScoreCalculator


def create_sample_biographical_data():
    """Create sample database with multiple players' biographical data"""
    db_path = "/tmp/biographical_demo.db"

    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    # Insert multiple players for comparison
    players = [
        # Jayson Tatum (SF, 6'8", young star)
        ("tatumja01", "1998-03-03", "day", "St. Louis", "Missouri", "USA",
         80, 210, 85, "2017-10-17", None, 2017, 1, 3, "BOS", "Duke",
         "Chaminade College Preparatory School", "USA", "SF", 0, "nba_api"),

        # LeBron James (SF, 6'9", veteran superstar)
        ("jamesle01", "1984-12-30", "day", "Akron", "Ohio", "USA",
         81, 250, 84, "2003-10-29", None, 2003, 1, 1, "CLE",
         "None (HS to NBA)", "St. Vincent-St. Mary High School", "USA", "SF", 23, "nba_api"),

        # Stephen Curry (PG, 6'2", sharpshooter)
        ("curryst01", "1988-03-14", "day", "Akron", "Ohio", "USA",
         74, 185, 76, "2009-10-28", None, 2009, 1, 7, "GSW", "Davidson",
         "Charlotte Christian School", "USA", "PG", 30, "nba_api"),

        # Giannis Antetokounmpo (PF, 6'11", physical specimen)
        ("antetgi01", "1994-12-06", "day", "Athens", None, "Greece",
         83, 242, 91, "2013-10-30", None, 2013, 1, 15, "MIL", None,
         "Filathlitikos", "Greece", "PF", 34, "nba_api"),

        # Victor Wembanyama (C, 7'4", next generation)
        ("wembavi01", "2004-01-04", "day", "Le Chesnay", None, "France",
         88, 209, 96, "2023-10-25", None, 2023, 1, 1, "SAS", None,
         "Nanterre 92", "France", "C", 1, "nba_api"),
    ]

    for player in players:
        cursor.execute("""
            INSERT INTO player_biographical
            (player_id, birth_date, birth_date_precision, birth_city, birth_state, birth_country,
             height_inches, weight_pounds, wingspan_inches,
             nba_debut_date, nba_retirement_date,
             draft_year, draft_round, draft_pick, draft_team_id,
             college, high_school,
             nationality, position, jersey_number, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, player)

    conn.commit()
    print(f"✓ Created biographical database with {len(players)} players: {db_path}\n")
    return db_path, conn


def display_player_comparison(calc: IntervalBoxScoreCalculator, timestamp: str):
    """Compare biographical data across multiple players"""

    print("=" * 120)
    print(f"PLAYER BIOGRAPHICAL COMPARISON - Timestamp: {timestamp}")
    print("=" * 120)
    print()

    players = [
        ("tatumja01", "Jayson Tatum"),
        ("jamesle01", "LeBron James"),
        ("curryst01", "Stephen Curry"),
        ("antetgi01", "Giannis Antetokounmpo"),
        ("wembavi01", "Victor Wembanyama"),
    ]

    # Physical attributes comparison
    print("PHYSICAL ATTRIBUTES COMPARISON:")
    print("-" * 120)
    print(f"{'Player':<25} {'Pos':<5} {'Height':<10} {'Weight':<10} {'Wingspan':<10} {'BMI':<8} {'Wing/Height':<12}")
    print("-" * 120)

    for player_id, player_name in players:
        bio = calc.get_player_biographical(player_id)
        if bio:
            height_m = bio['height_inches'] * 0.0254
            weight_kg = bio['weight_pounds'] * 0.453592
            bmi = weight_kg / (height_m ** 2)
            wingspan_ratio = bio['wingspan_inches'] / bio['height_inches']

            height_ft = f"{bio['height_inches'] // 12}'{bio['height_inches'] % 12}\""
            wingspan_ft = f"{bio['wingspan_inches'] // 12}'{bio['wingspan_inches'] % 12}\""

            print(f"{player_name:<25} {bio['position']:<5} {height_ft:<10} {bio['weight_pounds']} lbs    "
                  f"{wingspan_ft:<10} {bmi:>6.2f}  {wingspan_ratio:>10.3f}")

    print()

    # Age comparison at timestamp
    print(f"AGE ANALYSIS AT {timestamp}:")
    print("-" * 120)
    print(f"{'Player':<25} {'Birth Date':<15} {'Age (Years)':<15} {'Age (Days)':<12} {'Experience':<12} {'Rookie?':<10}")
    print("-" * 120)

    for player_id, player_name in players:
        bio = calc.get_player_biographical(player_id)
        if bio:
            age_data = calc.calculate_age_at_timestamp(bio['birth_date'], timestamp)
            exp_data = calc.calculate_nba_experience(bio['nba_debut_date'], timestamp)

            print(f"{player_name:<25} {bio['birth_date']:<15} {age_data['age_years_decimal']:>13.4f}  "
                  f"{age_data['age_days']:>10,}  {exp_data['nba_experience_years']:>10.2f}  "
                  f"{'Yes' if exp_data['is_rookie'] else 'No':<10}")

    print()

    # Draft analysis
    print("DRAFT PEDIGREE:")
    print("-" * 120)
    print(f"{'Player':<25} {'Draft Year':<12} {'Round':<8} {'Pick':<8} {'Team':<8} {'College':<30}")
    print("-" * 120)

    for player_id, player_name in players:
        bio = calc.get_player_biographical(player_id)
        if bio:
            college = bio['college'] if bio['college'] else "N/A"
            print(f"{player_name:<25} {bio['draft_year']:<12} {bio['draft_round']:<8} "
                  f"{bio['draft_pick']:<8} {bio['draft_team_id']:<8} {college:<30}")

    print()


def display_age_formats_detail(calc: IntervalBoxScoreCalculator, player_id: str,
                                player_name: str, timestamp: str):
    """Show all 7 age formats for a single player at specific timestamp"""

    print("=" * 120)
    print(f"AGE CALCULATION FORMATS - {player_name} at {timestamp}")
    print("=" * 120)
    print()

    bio = calc.get_player_biographical(player_id)
    age_data = calc.calculate_age_at_timestamp(bio['birth_date'], timestamp)

    print("7 ML-OPTIMIZED AGE FORMATS:")
    print("-" * 120)
    print()

    formats = [
        ("1. Decimal Years (DECIMAL(10,4))", age_data['age_years_decimal'],
         "Regression models, age-performance curves, neural networks",
         "Linear/polynomial regression, continuous gradient optimization"),

        ("2. Integer Days", age_data['age_days'],
         "Tree-based models (RF, XGBoost), discrete age binning",
         "Decision trees, random forests, categorical features"),

        ("3. Total Seconds (BIGINT)", age_data['age_seconds'],
         "LSTM/RNN time-series models, exact temporal precision",
         "Sequential models, high-frequency timesteps, fatigue analysis"),

        ("4. Age Uncertainty Hours", age_data['age_uncertainty_hours'],
         "Model confidence scoring, uncertainty-aware predictions",
         "Bayesian models, ensemble weighting, confidence intervals"),

        ("5. Minimum Age (Lower Bound)", age_data['age_min_decimal'],
         "Conservative estimates, lower bound calculations",
         "Pessimistic scenarios, risk-averse predictions"),

        ("6. Maximum Age (Upper Bound)", age_data['age_max_decimal'],
         "Liberal estimates, upper bound calculations",
         "Optimistic scenarios, aggressive predictions"),

        ("7. Human Readable String", age_data['age_string'],
         "Display, documentation, user-facing applications",
         "Reports, dashboards, explanations"),
    ]

    for label, value, primary_use, examples in formats:
        print(f"{label}")
        print(f"  Value: {value}")
        print(f"  Primary Use: {primary_use}")
        print(f"  Examples: {examples}")
        print()

    print("UNCERTAINTY ANALYSIS:")
    print("-" * 120)
    print(f"  Birth Date Precision: ±{age_data['age_uncertainty_hours']} hours (birth time unknown)")
    print(f"  Assumption: Born at midnight UTC (00:00:00)")
    print(f"  Age Range: {age_data['age_min_decimal']:.4f} - {age_data['age_max_decimal']:.4f} years")
    age_uncertainty_years = age_data['age_max_decimal'] - age_data['age_min_decimal']
    print(f"  Total Uncertainty: ±{age_uncertainty_years:.4f} years (±{age_uncertainty_years * 365.25:.4f} days)")
    print()


def display_career_arc_analysis(calc: IntervalBoxScoreCalculator, player_id: str,
                                 player_name: str):
    """Show career timeline across multiple timestamps"""

    print("=" * 120)
    print(f"CAREER ARC ANALYSIS - {player_name}")
    print("=" * 120)
    print()

    bio = calc.get_player_biographical(player_id)

    # Key career timestamps
    timestamps = [
        ("2017-10-17 20:00:00", "NBA Debut Night"),
        ("2018-06-10 21:00:00", "End of Rookie Season"),
        ("2020-09-27 20:00:00", "Eastern Conference Finals Game 7"),
        ("2022-06-16 21:00:00", "First NBA Finals"),
        ("2024-10-22 20:18:00", "Current Season (Sample Game)"),
    ]

    print(f"{'Date':<20} {'Event':<35} {'Age':<15} {'Experience':<15} {'Rookie?':<10}")
    print("-" * 120)

    for timestamp, event in timestamps:
        age_data = calc.calculate_age_at_timestamp(bio['birth_date'], timestamp)
        exp_data = calc.calculate_nba_experience(bio['nba_debut_date'], timestamp)

        print(f"{timestamp:<20} {event:<35} {age_data['age_years_decimal']:>13.4f}  "
              f"{exp_data['nba_experience_years']:>13.2f}  {'Yes' if exp_data['is_rookie'] else 'No':<10}")

    print()

    print("CAREER MILESTONES:")
    print("-" * 60)
    print(f"  Birth Date: {bio['birth_date']}")
    print(f"  NBA Debut: {bio['nba_debut_date']}")
    print(f"  Draft: {bio['draft_year']} - Round {bio['draft_round']}, Pick {bio['draft_pick']}")

    # Age at debut
    debut_age = calc.calculate_age_at_timestamp(bio['birth_date'], bio['nba_debut_date'])
    print(f"  Age at Debut: {debut_age['age_years_decimal']:.4f} years ({debut_age['age_string']})")

    # Current age
    current_timestamp = "2024-10-22 20:18:00"
    current_age = calc.calculate_age_at_timestamp(bio['birth_date'], current_timestamp)
    current_exp = calc.calculate_nba_experience(bio['nba_debut_date'], current_timestamp)
    print(f"  Current Age: {current_age['age_years_decimal']:.4f} years")
    print(f"  Current Experience: {current_exp['nba_experience_years']:.2f} years ({current_exp['nba_experience_days']:,} days)")

    print()


def display_ml_feature_engineering(calc: IntervalBoxScoreCalculator):
    """Demonstrate ML feature engineering with biographical data"""

    print("=" * 120)
    print("MACHINE LEARNING FEATURE ENGINEERING WITH BIOGRAPHICAL DATA")
    print("=" * 120)
    print()

    print("1. AGE-BASED FEATURES")
    print("-" * 60)
    print("  • age_years_decimal: Continuous age for regression")
    print("  • age_days: Discrete age for tree-based models")
    print("  • age_seconds: High-frequency time-series (LSTM input)")
    print("  • age_squared: Quadratic aging effects (performance curve)")
    print("  • age_cubed: Cubic aging effects (career arc)")
    print("  • is_prime_age: Boolean (27-31 years for NBA)")
    print("  • years_to_peak: Distance from peak age (28)")
    print("  • years_from_peak: Distance from peak age (absolute)")
    print()

    print("2. PHYSICAL ATTRIBUTE FEATURES")
    print("-" * 60)
    print("  • height_inches: Raw height")
    print("  • weight_pounds: Raw weight")
    print("  • bmi: Body Mass Index (weight/height²)")
    print("  • wingspan_inches: Defensive reach")
    print("  • wingspan_height_ratio: Defensive advantage indicator")
    print("  • height_weight_interaction: Size + strength composite")
    print("  • position_specific_height: Height deviation from position average")
    print()

    print("3. EXPERIENCE-BASED FEATURES")
    print("-" * 60)
    print("  • nba_experience_years: Years in league")
    print("  • nba_experience_days: Days in league (discrete)")
    print("  • is_rookie: Boolean (< 1 year)")
    print("  • is_veteran: Boolean (> 5 years)")
    print("  • experience_squared: Learning curve (quadratic)")
    print("  • age_experience_ratio: Draft age proxy")
    print("  • seasons_played: Count of seasons (discrete)")
    print()

    print("4. DRAFT PEDIGREE FEATURES")
    print("-" * 60)
    print("  • draft_pick: Overall pick number (1-60)")
    print("  • draft_round: Round 1 vs Round 2")
    print("  • is_lottery_pick: Boolean (picks 1-14)")
    print("  • is_top_pick: Boolean (picks 1-3)")
    print("  • is_first_overall: Boolean (pick 1)")
    print("  • draft_year: Year drafted (cohort effects)")
    print("  • years_since_draft: Career progression")
    print()

    print("5. COMBINED INTERACTION FEATURES")
    print("-" * 60)
    print("  • age × height: Size-aging interaction")
    print("  • age × weight: Weight management over time")
    print("  • age × experience: Disentangle age from learning")
    print("  • age × draft_pick: High pick expectations vs aging")
    print("  • height × wingspan_ratio: True defensive size")
    print("  • bmi × age: Body composition aging")
    print("  • experience × draft_year: Cohort × learning effects")
    print()

    print("6. TIME-VARYING FEATURES (LSTM/RNN)")
    print("-" * 60)
    print("  • age_seconds[t]: Monotonically increasing over game")
    print("  • fatigue_index[t]: age × time_elapsed_seconds")
    print("  • energy_remaining[t]: (max_age - age_seconds[t])")
    print("  • aging_velocity[t]: Δage between timesteps")
    print("  • career_phase[t]: Rookie/Prime/Veteran/Decline (categorical)")
    print()

    print("7. EXAMPLE: FEATURE VECTOR FOR ML MODEL")
    print("-" * 60)

    # Example: Jayson Tatum at game time
    player_id = "tatumja01"
    timestamp = "2024-10-22 20:18:00"
    bio = calc.get_player_biographical(player_id)
    age_data = calc.calculate_age_at_timestamp(bio['birth_date'], timestamp)
    exp_data = calc.calculate_nba_experience(bio['nba_debut_date'], timestamp)

    # Calculate features
    height_m = bio['height_inches'] * 0.0254
    weight_kg = bio['weight_pounds'] * 0.453592
    bmi = weight_kg / (height_m ** 2)
    wingspan_ratio = bio['wingspan_inches'] / bio['height_inches']
    age_squared = age_data['age_years_decimal'] ** 2
    is_prime_age = 27 <= age_data['age_years_decimal'] <= 31

    print(f"  Player: Jayson Tatum")
    print(f"  Timestamp: {timestamp}")
    print()
    print(f"  Feature Vector:")
    print(f"    age_years_decimal: {age_data['age_years_decimal']:.4f}")
    print(f"    age_days: {age_data['age_days']:,}")
    print(f"    age_seconds: {age_data['age_seconds']:,}")
    print(f"    age_squared: {age_squared:.4f}")
    print(f"    height_inches: {bio['height_inches']}")
    print(f"    weight_pounds: {bio['weight_pounds']}")
    print(f"    bmi: {bmi:.2f}")
    print(f"    wingspan_inches: {bio['wingspan_inches']}")
    print(f"    wingspan_height_ratio: {wingspan_ratio:.3f}")
    print(f"    nba_experience_years: {exp_data['nba_experience_years']:.2f}")
    print(f"    nba_experience_days: {exp_data['nba_experience_days']:,}")
    print(f"    is_rookie: {exp_data['is_rookie']}")
    print(f"    draft_pick: {bio['draft_pick']}")
    print(f"    is_lottery_pick: {bio['draft_pick'] <= 14}")
    print(f"    is_prime_age: {is_prime_age}")
    print()

    print("8. INTEGRATION WITH INTERVAL BOX SCORES")
    print("-" * 60)
    print("  Use calc.add_biographical_to_interval() to enrich interval stats:")
    print()
    print("  Example:")
    print("  ```python")
    print("  # Calculate interval stats")
    print("  interval_stats = calc.calculate_interval_stats(game_id, player_id, interval)")
    print()
    print("  # Add biographical features")
    print("  interval_stats = calc.add_biographical_to_interval(")
    print("      interval_stats, player_id, timestamp")
    print("  )")
    print()
    print("  # Now interval_stats contains:")
    print("  # - All box score metrics (points, rebounds, assists, etc.)")
    print("  # - All advanced metrics (TS%, usage rate, etc.)")
    print("  # - All 7 age formats")
    print("  # - Physical attributes (height, weight, wingspan, BMI)")
    print("  # - NBA experience metrics")
    print("  # - Draft information")
    print("  ```")
    print()


def main():
    """Run player biographical data demo"""
    print()
    db_path, conn = create_sample_biographical_data()

    # Create calculator
    calc = IntervalBoxScoreCalculator(conn)

    # Sample timestamp for analysis
    timestamp = "2024-10-22 20:18:00"

    # Display demonstrations
    display_player_comparison(calc, timestamp)
    display_age_formats_detail(calc, "tatumja01", "Jayson Tatum", timestamp)
    display_career_arc_analysis(calc, "tatumja01", "Jayson Tatum")
    display_ml_feature_engineering(calc)

    conn.close()


if __name__ == "__main__":
    main()
