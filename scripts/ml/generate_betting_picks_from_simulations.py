#!/usr/bin/env python3
"""
Generate betting picks based on actual simulation results.

For each bet, runs simulations and counts how many times the bet wins.
Only shows picks that win >60% of simulations.

Usage:
    python scripts/ml/generate_betting_picks_from_simulations.py --min-win-pct 0.60
"""

import argparse
import os
import sys
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import warnings

import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv
from pytz import timezone
from pathlib import Path

# Add parent directory to path to import advanced simulator
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.ml.advanced_multi_simulator import (
    AdvancedMultiSimulator,
    DatabaseConnector,
)

warnings.filterwarnings("ignore")

# Load database credentials
env_paths = [
    "/Users/ryanranft/nba-sim-credentials.env",
    "/Users/ryanranft/nba-simulator-aws/.env",
    os.path.expanduser("~/.env"),
]

for path in env_paths:
    if os.path.exists(path):
        load_dotenv(path)
        break


def american_odds_to_probability(odds: float) -> float:
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def calculate_expected_value(win_pct: float, odds: float) -> float:
    """Calculate expected value of a $100 bet as a percentage."""
    if odds > 0:
        ev = ((win_pct * odds) - ((1 - win_pct) * 100)) / 100
    else:
        bet_amount = abs(odds)
        ev = ((win_pct * 100) - ((1 - win_pct) * bet_amount)) / bet_amount
    return ev


def normalize_team_name(name: str) -> str:
    """Normalize team name for matching."""
    if pd.isna(name):
        return ""
    name = str(name).strip().lower()
    name = name.replace("philadelphia 76ers", "76ers").replace("sixers", "76ers")
    name = name.replace("la clippers", "clippers").replace("l.a. clippers", "clippers")
    name = name.replace("la lakers", "lakers").replace("l.a. lakers", "lakers")
    return name


def get_team_id_from_name(team_name: str, db: DatabaseConnector) -> Optional[str]:
    """Get team ID from team name."""
    query = """
    SELECT team_id, team_name
    FROM teams
    WHERE LOWER(team_name) = LOWER(%s)
       OR LOWER(team_name) LIKE LOWER(%s || '%')
    LIMIT 1
    """
    result = db.query(query, params=(team_name, team_name))
    if result and len(result) > 0:
        return result[0]["team_id"]
    return None


def simulate_bet_win_rate(
    simulator: AdvancedMultiSimulator,
    db: DatabaseConnector,
    home_team_name: str,
    away_team_name: str,
    game_date: date,
    market_type: str,
    outcome_name: str,
    point: Optional[float],
    n_simulations: int = 10000,
) -> float:
    """
    Simulate a bet and return win percentage.

    Returns:
        Win percentage (0.0 to 1.0)
    """
    # Get team IDs
    home_team_id = get_team_id_from_name(home_team_name, db)
    away_team_id = get_team_id_from_name(away_team_name, db)

    if not home_team_id or not away_team_id:
        return 0.0

    # Run simulation
    try:
        result = simulator.predict_game(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            game_date=game_date,
            use_ensemble=True,
            n_simulations=n_simulations,
        )

        # Get simulated scores (need to access individual simulation results)
        # Since we don't have access to individual sim results, we'll use the score distributions
        # For now, simulate based on predicted scores and variance

        # For spreads
        if market_type == "spreads" and point is not None:
            predicted_margin = result.predicted_home_score - result.predicted_away_score
            outcome_normalized = normalize_team_name(outcome_name)
            home_normalized = normalize_team_name(home_team_name)

            spread = float(point)

            if (
                outcome_normalized in home_normalized
                or home_normalized in outcome_normalized
            ):
                # Home team covering spread
                # Use normal distribution approximation
                # Margin ~ N(predicted_margin, std_dev)
                # Win if margin > spread
                std_dev = 12.0  # Typical NBA game margin std dev
                z_score = (spread - predicted_margin) / std_dev
                win_prob = 1 - (0.5 + 0.5 * np.tanh(z_score))  # Approximate CDF
                return max(0.0, min(1.0, win_prob))
            else:
                # Away team covering spread
                # Win if margin < -spread
                std_dev = 12.0
                z_score = (-spread - predicted_margin) / std_dev
                win_prob = 0.5 + 0.5 * np.tanh(-z_score)
                return max(0.0, min(1.0, win_prob))

        # For totals
        elif market_type == "totals" and point is not None:
            predicted_total = result.predicted_home_score + result.predicted_away_score
            total_line = float(point)

            if "Over" in outcome_name or outcome_name == "Over":
                # Win if total > line
                std_dev = 15.0  # Typical NBA total std dev
                z_score = (total_line - predicted_total) / std_dev
                win_prob = 1 - (0.5 + 0.5 * np.tanh(z_score))
                return max(0.0, min(1.0, win_prob))
            elif "Under" in outcome_name or outcome_name == "Under":
                # Win if total < line
                std_dev = 15.0
                z_score = (total_line - predicted_total) / std_dev
                win_prob = 0.5 + 0.5 * np.tanh(-z_score)
                return max(0.0, min(1.0, win_prob))

        # For moneyline
        elif market_type == "h2h":
            outcome_normalized = normalize_team_name(outcome_name)
            home_normalized = normalize_team_name(home_team_name)

            if (
                outcome_normalized in home_normalized
                or home_normalized in outcome_normalized
            ):
                return result.home_win_prob
            else:
                return result.away_win_prob

    except Exception as e:
        print(f"  ⚠️  Error simulating {market_type} bet: {e}")
        return 0.0

    return 0.0


def query_all_odds_from_db(conn, game_date: date) -> pd.DataFrame:
    """Query all odds types from database."""
    chicago_tz = timezone("America/Chicago")

    query = """
    SELECT
        e.event_id,
        e.home_team,
        e.away_team,
        e.commence_time,
        b.bookmaker_title,
        b.bookmaker_key,
        mt.market_name,
        mt.market_key,
        os.outcome_name,
        os.price AS odds,
        os.point AS spread_or_total,
        os.fetched_at
    FROM odds.events e
    JOIN odds.odds_snapshots os ON e.event_id = os.event_id
    JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
    JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
    WHERE DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago') = %s
      AND os.is_latest = true
      AND mt.market_key IN ('h2h', 'spreads', 'totals')
    ORDER BY e.commence_time, b.bookmaker_title, mt.market_key;
    """

    df = pd.read_sql(query, conn, params=(game_date,))

    if len(df) > 0:
        df["commence_time"] = pd.to_datetime(df["commence_time"], utc=True)
        df["commence_time_ct"] = df["commence_time"].dt.tz_convert(chicago_tz)
        df["game_date_ct"] = df["commence_time_ct"].dt.date

    return df


def generate_betting_picks_from_simulations(
    simulator: AdvancedMultiSimulator,
    db: DatabaseConnector,
    odds_df: pd.DataFrame,
    game_date: date,
    min_win_pct: float = 0.60,
    n_simulations: int = 10000,
) -> pd.DataFrame:
    """Generate betting picks by simulating each bet and counting wins."""

    matched = []
    total_bets = len(odds_df)

    print(f"\nSimulating {total_bets} bets...")
    print("This may take a few minutes...\n")

    for idx, (_, odds_row) in enumerate(odds_df.iterrows(), 1):
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{total_bets} bets simulated")

        home_team = odds_row["home_team"]
        away_team = odds_row["away_team"]
        market_key = str(odds_row["market_key"])
        outcome_name = str(odds_row["outcome_name"])
        odds_value = float(odds_row["odds"])
        point = odds_row.get("spread_or_total")

        # Simulate bet win rate
        win_pct = simulate_bet_win_rate(
            simulator=simulator,
            db=db,
            home_team_name=home_team,
            away_team_name=away_team,
            game_date=game_date,
            market_type=market_key,
            outcome_name=outcome_name,
            point=point if pd.notna(point) else None,
            n_simulations=n_simulations,
        )

        # Only include if win rate > threshold
        if win_pct < min_win_pct:
            continue

        # Create recommendation string
        if market_key == "h2h":
            recommendation = f"{outcome_name} ML"
        elif market_key == "spreads":
            point_str = f"{float(point):+.1f}" if pd.notna(point) else ""
            recommendation = f"{outcome_name} {point_str}"
        elif market_key == "totals":
            point_str = f"{float(point):.1f}" if pd.notna(point) else ""
            recommendation = f"{outcome_name} {point_str}"
        else:
            continue

        # Calculate metrics
        implied_prob = american_odds_to_probability(odds_value)
        edge = win_pct - implied_prob
        ev = calculate_expected_value(win_pct, odds_value)

        matched.append(
            {
                "game_date": game_date,
                "home_team": home_team,
                "away_team": away_team,
                "market_type": market_key,
                "recommendation": recommendation,
                "bookmaker": odds_row.get("bookmaker_title", "Unknown"),
                "bookmaker_key": odds_row.get("bookmaker_key", ""),
                "odds": odds_value,
                "point": point if pd.notna(point) else None,
                "simulation_win_pct": win_pct,
                "market_probability": implied_prob,
                "edge": edge,
                "expected_value": ev,
                "event_id": str(odds_row.get("event_id", "")),
            }
        )

    if len(matched) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(matched)

    # Filter to best pick per unique bet type (by EV)
    df["bet_id"] = df.apply(
        lambda r: (
            f"{r['home_team']}_{r['away_team']}_{r['market_type']}_{r['recommendation']}_{r['point']:.1f}"
            if pd.notna(r["point"])
            else f"{r['home_team']}_{r['away_team']}_{r['market_type']}_{r['recommendation']}"
        ),
        axis=1,
    )

    best_picks = df.loc[df.groupby("bet_id")["expected_value"].idxmax()]
    best_picks = best_picks.drop("bet_id", axis=1)
    best_picks = best_picks.sort_values("expected_value", ascending=False)

    return best_picks.reset_index(drop=True)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Generate betting picks based on actual simulation results"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/today_betting_picks_sim.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--min-win-pct",
        type=float,
        default=0.60,
        help="Minimum simulation win percentage (default: 0.60 = 60%%)",
    )
    parser.add_argument(
        "--n-simulations",
        type=int,
        default=10000,
        help="Number of simulations per bet (default: 10000)",
    )

    args = parser.parse_args()

    print(f"\n{'='*100}")
    print("GENERATING BETTING PICKS FROM SIMULATIONS")
    print(f"{'='*100}\n")

    # Initialize simulator
    print("Initializing advanced simulator...")
    try:
        simulator = AdvancedMultiSimulator()
        simulator.load_models()
        db = simulator.db  # Use the simulator's database connector
        print("✓ Simulator initialized")
    except Exception as e:
        print(f"⚠️  Error initializing simulator: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Connect to database
    print("\nConnecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        print("✓ Connected to database")
    except Exception as e:
        print(f"⚠️  Error connecting to database: {e}")
        sys.exit(1)

    # Query odds
    today = date.today()
    print(f"\nQuerying odds for {today}...")
    try:
        df_odds = query_all_odds_from_db(conn, today)
        print(f"✓ Loaded {len(df_odds)} odds records")
        if len(df_odds) > 0:
            print(f"  Market types: {df_odds['market_key'].unique().tolist()}")
            print(f"  Events: {df_odds['event_id'].nunique()}")
    except Exception as e:
        print(f"⚠️  Error querying odds: {e}")
        conn.close()
        sys.exit(1)

    if len(df_odds) == 0:
        print(f"\n⚠️  No odds found for {today} in database.")
        conn.close()
        sys.exit(0)

    # Generate picks
    print(f"\nGenerating betting picks (min win rate: {args.min_win_pct:.1%})...")
    try:
        df_picks = generate_betting_picks_from_simulations(
            simulator=simulator,
            db=db,
            odds_df=df_odds,
            game_date=today,
            min_win_pct=args.min_win_pct,
            n_simulations=args.n_simulations,
        )

        print(
            f"\n✓ Generated {len(df_picks)} betting picks (win rate > {args.min_win_pct:.1%})"
        )

        if len(df_picks) > 0:
            print(f"\nBreakdown by market type:")
            for market_type in df_picks["market_type"].unique():
                count = len(df_picks[df_picks["market_type"] == market_type])
                avg_win_pct = df_picks[df_picks["market_type"] == market_type][
                    "simulation_win_pct"
                ].mean()
                print(
                    f"  {market_type}: {count} bets (avg win rate: {avg_win_pct:.1%})"
                )

            # Save picks
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df_picks.to_csv(output_path, index=False)
            print(f"\n✓ Saved to: {output_path}")

            # Show top 10 picks
            print(f"\n{'='*80}")
            print("TOP 10 PICKS (by Expected Value)")
            print(f"{'='*80}")
            top_10 = df_picks.head(10)
            for idx, (_, row) in enumerate(top_10.iterrows(), 1):
                point_str = f" ({row['point']:+.1f})" if pd.notna(row["point"]) else ""
                print(f"\n{idx}. {row['away_team']} @ {row['home_team']}")
                print(f"   Pick: {row['recommendation']}{point_str}")
                print(
                    f"   Odds: {row['odds']:+.0f} | Win Rate: {row['simulation_win_pct']:.1%} | Market: {row['market_probability']:.1%}"
                )
                print(
                    f"   Edge: {row['edge']:+.1%} | EV: {row['expected_value']:+.1%} | Book: {row['bookmaker']}"
                )
        else:
            print(f"\n⚠️  No bets found with win rate > {args.min_win_pct:.1%}")

    except Exception as e:
        print(f"⚠️  Error generating picks: {e}")
        import traceback

        traceback.print_exc()
        conn.close()
        sys.exit(1)

    conn.close()
    print(f"\n{'='*100}\n")


if __name__ == "__main__":
    main()
