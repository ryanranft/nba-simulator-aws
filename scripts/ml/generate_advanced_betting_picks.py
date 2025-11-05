#!/usr/bin/env python3
"""
Generate Comprehensive Betting Picks Using Advanced Simulator Predictions

Purpose:
- Load advanced simulator predictions for today's games
- Fetch all odds types (moneyline, spreads, totals, player props) from database
- Match predictions to odds and calculate edges
- Generate comprehensive picks CSV with value bets

Usage:
    python scripts/ml/generate_advanced_betting_picks.py
    python scripts/ml/generate_advanced_betting_picks.py --predictions /path/to/predictions.csv
    python scripts/ml/generate_advanced_betting_picks.py --min-edge 0.05

Created: November 2, 2025
Author: NBA Simulator AWS Project
"""

import argparse
import os
import sys
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import warnings

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from pytz import timezone

warnings.filterwarnings("ignore")

# Load database credentials
env_path = "/Users/ryanranft/nba-sim-credentials.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


def american_odds_to_probability(odds: float) -> float:
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def calculate_expected_value(model_prob: float, odds: float) -> float:
    """
    Calculate expected value of a $100 bet.

    Returns EV as a percentage (e.g., 0.14 = 14% EV).
    """
    if odds > 0:
        ev = ((model_prob * odds) - ((1 - model_prob) * 100)) / 100
    else:
        bet_amount = abs(odds)
        ev = ((model_prob * 100) - ((1 - model_prob) * bet_amount)) / bet_amount

    return ev


def calculate_edge(model_prob: float, implied_prob: float) -> float:
    """Calculate betting edge (model_prob - implied_prob)."""
    return model_prob - implied_prob


def normalize_team_name(name: str) -> str:
    """Normalize team name for matching."""
    if pd.isna(name):
        return ""
    return str(name).strip().lower()


def load_advanced_predictions(predictions_path: str) -> pd.DataFrame:
    """Load advanced simulator predictions."""
    df = pd.read_csv(predictions_path)

    # Ensure we have required columns
    required_cols = [
        "game_id",
        "home_team",
        "away_team",
        "predicted_winner",
        "home_win_probability",
        "away_win_probability",
        "predicted_home_score",
        "predicted_away_score",
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    return df


def query_all_odds(conn, game_date: date) -> pd.DataFrame:
    """Query all odds types for a given date from database."""
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
    ORDER BY e.commence_time, b.bookmaker_title, mt.market_key, os.fetched_at DESC;
    """

    df = pd.read_sql(query, conn, params=(game_date,))

    if len(df) > 0:
        # Convert to Chicago timezone
        df["commence_time"] = pd.to_datetime(df["commence_time"], utc=True)
        df["commence_time_ct"] = df["commence_time"].dt.tz_convert(chicago_tz)
        df["game_date_ct"] = df["commence_time_ct"].dt.date

    return df


def calculate_spread_probability(predicted_margin: float, spread: float) -> float:
    """Calculate probability of covering a spread."""
    # Use logistic function centered at the spread
    # If predicted_margin > spread, higher probability of covering
    diff = predicted_margin - spread
    prob = 1 / (1 + np.exp(-diff / 3))  # 3-point spread sensitivity
    return max(0.01, min(0.99, prob))


def calculate_total_probability(
    predicted_total: float, total_line: float, outcome: str
) -> float:
    """Calculate probability for over/under."""
    if "Over" in outcome or outcome == "Over":
        # Higher probability when predicted_total > total_line
        diff = predicted_total - total_line
        prob = 0.5 + (diff * 0.02)  # 2% per point
    elif "Under" in outcome or outcome == "Under":
        # Higher probability when total_line > predicted_total
        diff = total_line - predicted_total
        prob = 0.5 + (diff * 0.02)  # 2% per point
    else:
        prob = 0.5

    return max(0.01, min(0.99, prob))


def match_predictions_to_odds(
    predictions_df: pd.DataFrame, odds_df: pd.DataFrame
) -> pd.DataFrame:
    """Match predictions to odds and calculate edges for all market types."""
    import numpy as np

    matched = []
    today = date.today()

    for _, pred_row in predictions_df.iterrows():
        pred_home = normalize_team_name(pred_row["home_team"])
        pred_away = normalize_team_name(pred_row["away_team"])
        pred_date = pd.to_datetime(pred_row["game_date"]).date()
        predicted_winner = pred_row["predicted_winner"]
        predicted_home_score = pred_row["predicted_home_score"]
        predicted_away_score = pred_row["predicted_away_score"]
        predicted_total = predicted_home_score + predicted_away_score
        predicted_margin = predicted_home_score - predicted_away_score

        # Match odds
        for _, odds_row in odds_df.iterrows():
            odds_home = normalize_team_name(odds_row["home_team"])
            odds_away = normalize_team_name(odds_row["away_team"])

            # Use Chicago time date for matching
            odds_date = odds_row.get("game_date_ct", odds_row["commence_time"].date())

            # Match teams and date
            home_match = (
                pred_home == odds_home
                or pred_home in odds_home
                or odds_home in pred_home
            )
            away_match = (
                pred_away == odds_away
                or pred_away in odds_away
                or odds_away in pred_away
            )
            date_match = pred_date == today and odds_date == today

            if not (home_match and away_match and date_match):
                continue

            market_key = odds_row["market_key"]
            outcome_name = str(odds_row["outcome_name"])
            odds_value = float(odds_row["odds"])
            point = odds_row.get("spread_or_total")

            model_prob = None
            recommendation = None

            # Calculate model probability based on market type
            if market_key == "h2h":
                # Moneyline
                if normalize_team_name(outcome_name) == normalize_team_name(
                    predicted_winner
                ):
                    model_prob = (
                        pred_row["home_win_probability"]
                        if predicted_winner == pred_row["home_team"]
                        else pred_row["away_win_probability"]
                    )
                    recommendation = f"{predicted_winner} ML"
                else:
                    continue

            elif market_key == "spreads":
                # Point spread
                if point is None:
                    continue

                spread = float(point)

                # Determine if betting home or away spread
                if (
                    pred_home in normalize_team_name(outcome_name)
                    or normalize_team_name(outcome_name) in pred_home
                ):
                    # Home team spread
                    model_prob = calculate_spread_probability(predicted_margin, spread)
                    recommendation = f"{pred_row['home_team']} {spread:+.1f}"
                elif (
                    pred_away in normalize_team_name(outcome_name)
                    or normalize_team_name(outcome_name) in pred_away
                ):
                    # Away team spread
                    model_prob = calculate_spread_probability(
                        -predicted_margin, -spread
                    )
                    recommendation = f"{pred_row['away_team']} {spread:+.1f}"
                else:
                    continue

            elif market_key == "totals":
                # Over/Under
                if point is None:
                    continue

                total_line = float(point)

                if "Over" in outcome_name or outcome_name == "Over":
                    model_prob = calculate_total_probability(
                        predicted_total, total_line, "Over"
                    )
                    recommendation = f"Over {total_line:.1f}"
                elif "Under" in outcome_name or outcome_name == "Under":
                    model_prob = calculate_total_probability(
                        predicted_total, total_line, "Under"
                    )
                    recommendation = f"Under {total_line:.1f}"
                else:
                    continue

            else:
                # Player props and other markets - skip for now
                continue

            if model_prob is None:
                continue

            # Calculate metrics
            implied_prob = american_odds_to_probability(odds_value)
            edge = calculate_edge(model_prob, implied_prob)
            ev = calculate_expected_value(model_prob, odds_value)

            matched.append(
                {
                    "game_id": pred_row["game_id"],
                    "game_date": pred_date,
                    "home_team": pred_row["home_team"],
                    "away_team": pred_row["away_team"],
                    "predicted_winner": predicted_winner,
                    "model_probability": model_prob,
                    "confidence": pred_row.get("confidence", 0),
                    "prediction_strength": pred_row.get("prediction_strength", "N/A"),
                    "market_type": market_key,
                    "recommendation": recommendation,
                    "bookmaker": odds_row["bookmaker_title"],
                    "bookmaker_key": odds_row["bookmaker_key"],
                    "odds": odds_value,
                    "point": point,
                    "market_probability": implied_prob,
                    "edge": edge,
                    "expected_value": ev,
                    "event_id": odds_row["event_id"],
                }
            )

    if len(matched) == 0:
        return pd.DataFrame()

    return pd.DataFrame(matched)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive betting picks using advanced simulator predictions"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="/tmp/nba_predictions/predictions_latest.csv",
        help="Path to advanced simulator predictions CSV",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.0,
        help="Minimum edge threshold (default: 0.0 = show all)",
    )
    parser.add_argument(
        "--min-ev",
        type=float,
        default=0.0,
        help="Minimum expected value threshold (default: 0.0 = show all)",
    )

    args = parser.parse_args()

    print(f"\n{'='*100}")
    print("GENERATING COMPREHENSIVE BETTING PICKS - ADVANCED SIMULATOR")
    print(f"{'='*100}\n")

    # Load predictions
    print(f"Loading predictions from: {args.predictions}")
    try:
        df_predictions = load_advanced_predictions(args.predictions)
        print(f"✓ Loaded {len(df_predictions)} predictions")
    except Exception as e:
        print(f"⚠️  Error loading predictions: {e}")
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
        df_odds = query_all_odds(conn, today)
        print(f"✓ Loaded {len(df_odds)} odds records")
        if len(df_odds) > 0:
            print(f"  Market types: {df_odds['market_key'].unique().tolist()}")
            print(f"  Bookmakers: {df_odds['bookmaker_key'].unique().tolist()}")
    except Exception as e:
        print(f"⚠️  Error querying odds: {e}")
        conn.close()
        sys.exit(1)

    if len(df_odds) == 0:
        print("⚠️  No odds found for today. Make sure odds scraper is running.")
        conn.close()
        sys.exit(0)

    # Match predictions to odds
    print("\nMatching predictions to odds...")
    import numpy as np

    df_matched = match_predictions_to_odds(df_predictions, df_odds)

    if len(df_matched) == 0:
        print("⚠️  No matches found between predictions and odds.")
        print("   Check that team names match and games are for today.")
        conn.close()
        sys.exit(0)

    print(f"✓ Matched {len(df_matched)} bets")

    # Filter by edge and EV
    print(
        f"\nFiltering bets (min edge: {args.min_edge:.1%}, min EV: {args.min_ev:.1%})..."
    )
    df_filtered = df_matched[
        (df_matched["edge"] >= args.min_edge)
        & (df_matched["expected_value"] >= args.min_ev)
    ].copy()
    print(f"✓ {len(df_filtered)} bets meet thresholds")

    # Sort by expected value
    df_sorted = df_filtered.sort_values("expected_value", ascending=False)

    # Save output
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.dirname(args.predictions)
        output_path = os.path.join(
            output_dir, f"advanced_betting_picks_{timestamp}.csv"
        )

    df_sorted.to_csv(output_path, index=False)

    # Create symlink
    latest_path = os.path.join(
        os.path.dirname(output_path), "advanced_betting_picks_latest.csv"
    )
    if os.path.exists(latest_path) or os.path.islink(latest_path):
        os.remove(latest_path)
    os.symlink(os.path.basename(output_path), latest_path)

    # Display summary
    print(f"\n{'='*100}")
    print("BETTING PICKS SUMMARY")
    print(f"{'='*100}\n")

    # Group by market type
    for market_type in df_sorted["market_type"].unique():
        df_market = df_sorted[df_sorted["market_type"] == market_type].head(10)

        print(
            f"{market_type.upper()} ({len(df_sorted[df_sorted['market_type'] == market_type])} bets):"
        )
        print("-" * 100)

        for _, row in df_market.iterrows():
            print(f"  {row['away_team']} @ {row['home_team']}")
            print(f"    Pick: {row['recommendation']}")
            print(
                f"    Odds: {row['odds']:+d} | Model Prob: {row['model_probability']:.1%} | Market Prob: {row['market_probability']:.1%}"
            )
            print(
                f"    Edge: {row['edge']:+.1%} | EV: {row['expected_value']:+.1%} | Book: {row['bookmaker']}"
            )
            print()

    print(f"{'='*100}")
    print(f"✓ Saved to: {output_path}")
    print(f"✓ Symlink: {latest_path}")
    print(f"{'='*100}\n")

    conn.close()


if __name__ == "__main__":
    main()
