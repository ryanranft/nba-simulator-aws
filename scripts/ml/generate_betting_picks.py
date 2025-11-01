#!/usr/bin/env python3
"""
Generate Betting Picks Using Predictions + Odds API

Purpose:
- Load ML predictions for today's games
- Filter for predictions with >70% win probability
- Query today's betting odds from PostgreSQL odds schema
- Match predictions to odds and calculate edges
- Generate picks CSV with value bets

Usage:
    python scripts/ml/generate_betting_picks.py
    python scripts/ml/generate_betting_picks.py --predictions /path/to/predictions.csv
    python scripts/ml/generate_betting_picks.py --min-confidence 0.75

Author: NBA Simulator AWS Project
Created: October 30, 2025
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

warnings.filterwarnings("ignore")

# Load database credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")


def american_odds_to_probability(odds: float) -> float:
    """
    Convert American odds to implied probability.

    Args:
        odds: American odds (e.g., -110, +150)

    Returns:
        Implied probability (0.0 to 1.0)
    """
    if odds > 0:
        # Positive odds: +150 -> 100/(150+100) = 0.40
        return 100 / (odds + 100)
    else:
        # Negative odds: -110 -> 110/(110+100) = 0.524
        return abs(odds) / (abs(odds) + 100)


def calculate_edge(model_prob: float, implied_prob: float) -> float:
    """
    Calculate betting edge: difference between model probability and market implied probability.

    Args:
        model_prob: Model's predicted probability (0.0 to 1.0)
        implied_prob: Market implied probability from odds (0.0 to 1.0)

    Returns:
        Edge as percentage (positive = value bet)
    """
    return model_prob - implied_prob


def calculate_expected_value(model_prob: float, odds: float) -> float:
    """
    Calculate expected value of a bet.

    Args:
        model_prob: Model's predicted probability
        odds: American odds

    Returns:
        Expected value (positive = profitable bet)
    """
    if odds > 0:
        # Positive odds: +150 -> win $150 on $100 bet
        payout_ratio = odds / 100
    else:
        # Negative odds: -110 -> win $100 on $110 bet
        payout_ratio = 100 / abs(odds)

    ev = (model_prob * payout_ratio) - 1
    return ev


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name for matching between predictions and odds.

    Args:
        team_name: Team name from predictions or odds

    Returns:
        Normalized team name
    """
    # Remove common suffixes and normalize
    team_name = team_name.strip()

    # Common variations
    name_mapping = {
        "LA Clippers": "Los Angeles Clippers",
        "LA Lakers": "Los Angeles Lakers",
        "L.A. Clippers": "Los Angeles Clippers",
        "L.A. Lakers": "Los Angeles Lakers",
    }

    return name_mapping.get(team_name, team_name)


def query_todays_odds(conn) -> pd.DataFrame:
    """
    Query today's latest betting odds from PostgreSQL.

    Args:
        conn: PostgreSQL connection

    Returns:
        DataFrame with odds data
    """
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
    WHERE DATE(e.commence_time) >= CURRENT_DATE
      AND DATE(e.commence_time) <= CURRENT_DATE + INTERVAL '1 day'
      AND os.is_latest = true
      AND mt.market_key = 'h2h'
    ORDER BY e.commence_time, b.bookmaker_title, os.fetched_at DESC;
    """

    df = pd.read_sql(query, conn)
    return df


def match_predictions_to_odds(
    predictions_df: pd.DataFrame, odds_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Match predictions to odds by team names and date.

    Args:
        predictions_df: DataFrame with predictions
        odds_df: DataFrame with odds

    Returns:
        DataFrame with matched predictions and odds
    """
    matched = []

    for _, pred_row in predictions_df.iterrows():
        pred_home = normalize_team_name(pred_row["home_team"])
        pred_away = normalize_team_name(pred_row["away_team"])
        pred_date = pd.to_datetime(pred_row["game_date"]).date()

        # Find matching odds
        for _, odds_row in odds_df.iterrows():
            odds_home = normalize_team_name(odds_row["home_team"])
            odds_away = normalize_team_name(odds_row["away_team"])
            odds_date = pd.to_datetime(odds_row["commence_time"]).date()

            # Check if teams match (either direction)
            home_match = pred_home == odds_home or pred_home == odds_away
            away_match = pred_away == odds_away or pred_away == odds_home
            date_match = pred_date == odds_date

            if home_match and away_match and date_match:
                # Determine if odds are for home or away team
                if normalize_team_name(odds_row["outcome_name"]) == pred_home:
                    # Odds for home team
                    model_prob = pred_row["home_win_probability"]
                    team_bet = pred_row["home_team"]
                elif normalize_team_name(odds_row["outcome_name"]) == pred_away:
                    # Odds for away team
                    model_prob = pred_row["away_win_probability"]
                    team_bet = pred_row["away_team"]
                else:
                    continue

                # Only include if this is the predicted winner
                if team_bet != pred_row["predicted_winner"]:
                    continue

                # Calculate metrics
                implied_prob = american_odds_to_probability(odds_row["odds"])
                edge = calculate_edge(model_prob, implied_prob)
                ev = calculate_expected_value(model_prob, odds_row["odds"])

                matched.append(
                    {
                        "game_id": pred_row["game_id"],
                        "game_date": pred_row["game_date"],
                        "home_team": pred_row["home_team"],
                        "away_team": pred_row["away_team"],
                        "predicted_winner": pred_row["predicted_winner"],
                        "model_probability": model_prob,
                        "confidence": pred_row["confidence"],
                        "prediction_strength": pred_row["prediction_strength"],
                        "bookmaker": odds_row["bookmaker_title"],
                        "bookmaker_key": odds_row["bookmaker_key"],
                        "recommendation": f"{team_bet} ML",
                        "odds": odds_row["odds"],
                        "market_probability": implied_prob,
                        "edge": edge,
                        "expected_value": ev,
                        "event_id": odds_row["event_id"],
                    }
                )

    if not matched:
        return pd.DataFrame()

    return pd.DataFrame(matched)


def format_picks_table(df_picks: pd.DataFrame) -> str:
    """Format picks as a readable table."""
    if len(df_picks) == 0:
        return "No picks found matching criteria."

    lines = []
    lines.append("=" * 120)
    lines.append("BETTING PICKS - TODAY'S GAMES (>70% Win Probability)")
    lines.append("=" * 120)
    lines.append("")

    # Sort by expected value (descending)
    df_sorted = df_picks.sort_values("expected_value", ascending=False)

    for _, pick in df_sorted.iterrows():
        game = f"{pick['away_team']} @ {pick['home_team']}"
        recommendation = pick["recommendation"]
        bookmaker = pick["bookmaker"]
        odds = pick["odds"]
        model_prob = pick["model_probability"]
        market_prob = pick["market_probability"]
        edge = pick["edge"]
        ev = pick["expected_value"]
        confidence = pick["prediction_strength"]

        odds_str = f"+{odds}" if odds > 0 else str(odds)

        lines.append(
            f"{game:50} | "
            f"{recommendation:25} | "
            f"{bookmaker:15} | "
            f"{odds_str:8} | "
            f"Model: {model_prob:.1%} | "
            f"Market: {market_prob:.1%} | "
            f"Edge: {edge:+.1%} | "
            f"EV: {ev:+.2%} | "
            f"{confidence}"
        )

    lines.append("")
    lines.append("=" * 120)

    return "\n".join(lines)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Generate betting picks using predictions and odds API"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="/Users/ryanranft/nba-simulator-aws/tmp/predictions/predictions_latest.csv",
        help="Path to predictions CSV file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: auto-generated in same directory as predictions)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.70,
        help="Minimum confidence threshold (default: 0.70 = 70%%)",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.0,
        help="Minimum edge threshold (default: 0.0 = show all)",
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("GENERATING BETTING PICKS FROM PREDICTIONS + ODDS")
    print(f"{'='*80}\n")

    # Load predictions
    print(f"Loading predictions from: {args.predictions}")
    try:
        df_predictions = pd.read_csv(args.predictions)
        print(f"✓ Loaded {len(df_predictions)} predictions")
    except Exception as e:
        print(f"⚠️  Error loading predictions: {e}")
        sys.exit(1)

    # Filter for high-confidence predictions
    print(
        f"\nFiltering for predictions with confidence >= {args.min_confidence:.1%}..."
    )
    df_filtered = df_predictions[
        df_predictions["confidence"] >= args.min_confidence
    ].copy()
    print(f"✓ {len(df_filtered)} predictions meet confidence threshold")

    if len(df_filtered) == 0:
        print(
            "⚠️  No predictions meet the confidence threshold. Try lowering --min-confidence."
        )
        sys.exit(0)

    # Connect to database
    print("\nConnecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME", "nba_simulator"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432),
            sslmode="require",
        )
        print("✓ Database connection established")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print(
            "   Make sure credentials are in /Users/ryanranft/nba-sim-credentials.env"
        )
        sys.exit(1)

    # Query today's odds
    print("\nQuerying today's betting odds...")
    try:
        df_odds = query_todays_odds(conn)
        print(f"✓ Found {len(df_odds)} odds records for today")

        if len(df_odds) == 0:
            print("⚠️  No odds found for today's games.")
            print(
                "   Make sure the odds-api scraper has run and collected today's data."
            )
            conn.close()
            sys.exit(0)
    except Exception as e:
        print(f"⚠️  Error querying odds: {e}")
        conn.close()
        sys.exit(1)

    # Match predictions to odds
    print("\nMatching predictions to odds...")
    df_picks = match_predictions_to_odds(df_filtered, df_odds)
    print(f"✓ Matched {len(df_picks)} predictions to odds")

    if len(df_picks) == 0:
        print("⚠️  No matches found between predictions and odds.")
        print(
            "   Check team name variations or verify odds data exists for today's games."
        )
        conn.close()
        sys.exit(0)

    # Filter by minimum edge if specified
    if args.min_edge > 0:
        before_count = len(df_picks)
        df_picks = df_picks[df_picks["edge"] >= args.min_edge].copy()
        after_count = len(df_picks)
        print(
            f"\nFiltered to {after_count} picks with edge >= {args.min_edge:.1%} "
            f"({before_count - after_count} removed)"
        )

    # Close database connection
    conn.close()

    # Save picks CSV
    if args.output:
        output_path = args.output
    else:
        # Auto-generate output path
        pred_dir = os.path.dirname(args.predictions)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(pred_dir, f"betting_picks_{timestamp}.csv")

    df_picks.to_csv(output_path, index=False)
    print(f"\n✓ Saved picks to: {output_path}")

    # Display picks
    print("\n" + format_picks_table(df_picks))

    # Summary statistics
    print("\nPICKS SUMMARY")
    print("=" * 80)
    print(f"Total picks: {len(df_picks)}")
    if len(df_picks) > 0:
        print(f"Avg edge: {df_picks['edge'].mean():.2%}")
        print(f"Avg expected value: {df_picks['expected_value'].mean():.2%}")
        print(f"Picks with positive EV: {(df_picks['expected_value'] > 0).sum()}")
        print(f"Unique games: {df_picks['game_id'].nunique()}")
        print(f"Unique bookmakers: {df_picks['bookmaker'].nunique()}")
    print()

    print("✓ Picks generation complete!")


if __name__ == "__main__":
    main()
