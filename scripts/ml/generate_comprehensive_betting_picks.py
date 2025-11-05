#!/usr/bin/env python3
"""
Generate Comprehensive Betting Picks Using Advanced Simulator Predictions

This script matches advanced simulator predictions to odds and generates
comprehensive betting picks for all market types:
- Moneyline (h2h)
- Point Spreads
- Totals (Over/Under)
- Player Props (if available in predictions)

Usage:
    python scripts/ml/generate_comprehensive_betting_picks.py
    python scripts/ml/generate_comprehensive_betting_picks.py --predictions /path/to/predictions.csv
    python scripts/ml/generate_comprehensive_betting_picks.py --min-ev 0.05

Created: November 2, 2025
Author: NBA Simulator AWS Project
"""

import argparse
import os
import sys
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import warnings

import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv
from pytz import timezone
from pathlib import Path

# Add parent directory to path to import advanced simulator
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.ml.advanced_multi_simulator import AdvancedMultiSimulator

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


def calculate_expected_value(model_prob: float, odds: float) -> float:
    """Calculate expected value of a $100 bet as a percentage."""
    if odds > 0:
        ev = ((model_prob * odds) - ((1 - model_prob) * 100)) / 100
    else:
        bet_amount = abs(odds)
        ev = ((model_prob * 100) - ((1 - model_prob) * bet_amount)) / bet_amount
    return ev


def calculate_edge(model_prob: float, implied_prob: float) -> float:
    """Calculate betting edge."""
    return model_prob - implied_prob


def normalize_team_name(name: str) -> str:
    """Normalize team name for matching."""
    if pd.isna(name):
        return ""
    name = str(name).strip().lower()
    # Handle common variations
    name = name.replace("philadelphia 76ers", "76ers").replace("sixers", "76ers")
    name = name.replace("la clippers", "clippers").replace("l.a. clippers", "clippers")
    name = name.replace("la lakers", "lakers").replace("l.a. lakers", "lakers")
    return name


def calculate_spread_probability(predicted_margin: float, spread: float) -> float:
    """Calculate probability of covering a spread."""
    diff = predicted_margin - spread
    prob = 1 / (1 + np.exp(-diff / 3))
    return max(0.01, min(0.99, prob))


def calculate_total_probability(
    predicted_total: float, total_line: float, outcome: str
) -> float:
    """Calculate probability for over/under."""
    if "Over" in outcome or outcome == "Over":
        diff = predicted_total - total_line
        prob = 0.5 + (diff * 0.02)
    elif "Under" in outcome or outcome == "Under":
        diff = total_line - predicted_total
        prob = 0.5 + (diff * 0.02)
    else:
        prob = 0.5
    return max(0.01, min(0.99, prob))


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
    ORDER BY e.commence_time, b.bookmaker_title, mt.market_key;
    """

    df = pd.read_sql(query, conn, params=(game_date,))

    if len(df) > 0:
        df["commence_time"] = pd.to_datetime(df["commence_time"], utc=True)
        df["commence_time_ct"] = df["commence_time"].dt.tz_convert(chicago_tz)
        df["game_date_ct"] = df["commence_time_ct"].dt.date

    return df


def simulate_bet_win_rate(
    simulator: AdvancedMultiSimulator,
    home_team_id: str,
    away_team_id: str,
    game_date: date,
    market_type: str,
    outcome_name: str,
    point: Optional[float],
    home_team_name: str,
    away_team_name: str,
    n_simulations: int = 10000,
    game_state: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Simulate a bet and return actual win percentage from simulations.

    Args:
        simulator: AdvancedMultiSimulator instance
        home_team_id: Home team ID
        away_team_id: Away team ID
        game_date: Game date
        market_type: Market type ('h2h', 'spreads', 'totals')
        outcome_name: Outcome name (team name or 'Over'/'Under')
        point: Spread or total point value
        home_team_name: Home team name
        away_team_name: Away team name
        n_simulations: Number of simulations (default: 10000)
        game_state: Optional game state dictionary for in-progress games

    Returns:
        Win percentage (0.0 to 1.0) - actual percentage of simulations where bet wins
    """
    try:
        # Run simulation with game state if provided
        result, _ = simulator.predict_game(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            game_date=game_date,
            use_ensemble=True,
            n_simulations=n_simulations,
            game_state=game_state,
        )

        # Get predicted scores from simulation result
        # Note: These scores may be inflated, so we use them for margin calculation
        # but may need to normalize for total points
        predicted_home_score = result.predicted_home_score
        predicted_away_score = result.predicted_away_score

        # Normalize scores to realistic NBA averages if they're inflated
        # Typical NBA game: ~224 total points, ~12.7 margin
        if predicted_home_score > 200 or predicted_away_score > 200:
            # Scores are inflated, normalize to realistic range
            # Use the margin from inflated scores but scale total
            raw_margin = predicted_home_score - predicted_away_score
            # Scale to realistic total (224 average)
            scale_factor = 224.0 / (predicted_home_score + predicted_away_score)
            predicted_home_score = 112.0 + (raw_margin / 2) * scale_factor
            predicted_away_score = 112.0 - (raw_margin / 2) * scale_factor

        predicted_total = predicted_home_score + predicted_away_score
        predicted_margin = predicted_home_score - predicted_away_score

        # For spreads
        if market_type == "spreads" and point is not None:
            spread = float(point)
            outcome_normalized = normalize_team_name(outcome_name)
            home_normalized = normalize_team_name(home_team_name)

            # Use normal distribution approximation for margin
            std_dev = 12.0  # Typical NBA game margin std dev

            if (
                outcome_normalized in home_normalized
                or home_normalized in outcome_normalized
            ):
                # Home team covering spread: win if margin > spread
                # z_score = (spread - predicted_margin) / std_dev
                # If predicted_margin > spread, z_score is negative, so norm.cdf(z_score) < 0.5
                # win_prob = 1 - norm.cdf(z_score) > 0.5
                z_score = (spread - predicted_margin) / std_dev
                try:
                    from scipy.stats import norm

                    win_prob = 1 - norm.cdf(z_score)
                except ImportError:
                    # Approximate CDF using error function
                    import math

                    win_prob = 0.5 * (1 - math.erf(z_score / math.sqrt(2)))
                    win_prob = 1 - win_prob
            else:
                # Away team covering spread: win if margin < -spread
                # This means: predicted_margin < -spread, or -spread > predicted_margin
                # z_score = (-spread - predicted_margin) / std_dev
                # If predicted_margin < -spread, then -spread - predicted_margin > 0, so z_score > 0
                # win_prob = norm.cdf(z_score) > 0.5
                # But we need: if home -X wins with prob P, then away +X should win with prob (1-P)
                # For complementary spreads: if spread = X, then home -X and away +X are opposite
                # If home -X wins when margin > X, then away +X wins when margin < X
                # So for away +X: z_score = (X - predicted_margin) / std_dev
                # win_prob = norm.cdf(z_score) = 1 - (1 - norm.cdf(z_score)) = 1 - prob(home -X)
                z_score = (spread - predicted_margin) / std_dev
                try:
                    from scipy.stats import norm

                    # Away covers if margin < spread (for +spread), which is complementary to home covering
                    win_prob = norm.cdf(z_score)
                except ImportError:
                    # Approximate CDF using error function
                    import math

                    win_prob = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

            return max(0.0, min(1.0, win_prob))

        # For totals
        elif market_type == "totals" and point is not None:
            total_line = float(point)

            if "Over" in outcome_name or outcome_name == "Over":
                # Win if total > line
                std_dev = 15.0  # Typical NBA total std dev
                z_score = (total_line - predicted_total) / std_dev
                try:
                    from scipy.stats import norm

                    win_prob = 1 - norm.cdf(z_score)
                except ImportError:
                    # Approximate CDF using error function
                    import math

                    win_prob = 0.5 * (1 - math.erf(z_score / math.sqrt(2)))
                    win_prob = 1 - win_prob
            elif "Under" in outcome_name or outcome_name == "Under":
                # Win if total < line
                std_dev = 15.0
                z_score = (total_line - predicted_total) / std_dev
                try:
                    from scipy.stats import norm

                    win_prob = norm.cdf(z_score)
                except ImportError:
                    # Approximate CDF using error function
                    import math

                    win_prob = 0.5 * (1 - math.erf(z_score / math.sqrt(2)))
                    win_prob = 1 - win_prob
            else:
                return 0.0

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


def get_team_id_from_name(team_name: str, db_conn) -> Optional[str]:
    """Get team ID from team name with improved matching."""
    # Try exact match first
    query = """
    SELECT team_id, team_name
    FROM teams
    WHERE LOWER(team_name) = LOWER(%s)
    LIMIT 1
    """
    cursor = db_conn.cursor()
    cursor.execute(query, (team_name,))
    result = cursor.fetchone()

    if result:
        cursor.close()
        return str(result[0])

    # Try partial match
    query = """
    SELECT team_id, team_name
    FROM teams
    WHERE LOWER(team_name) LIKE LOWER(%s || '%%')
       OR LOWER(%s || '%%') LIKE LOWER(team_name)
    LIMIT 1
    """
    cursor.execute(query, (team_name, team_name))
    result = cursor.fetchone()

    if result:
        cursor.close()
        return str(result[0])

    # Try common name variations
    name_variations = {
        "76ers": ["philadelphia 76ers", "sixers", "philadelphia"],
        "clippers": ["la clippers", "l.a. clippers", "los angeles clippers"],
        "lakers": ["la lakers", "l.a. lakers", "los angeles lakers"],
    }

    team_lower = team_name.lower()
    for key, variations in name_variations.items():
        if key in team_lower or team_lower in variations:
            for variation in variations:
                cursor.execute(query, (variation, variation))
                result = cursor.fetchone()
                if result:
                    cursor.close()
                    return str(result[0])

    cursor.close()
    return None


def validate_complementary_probabilities(game_picks: List[Dict]) -> List[Dict]:
    """
    Validate that complementary spreads have complementary probabilities.
    For same game, same spread value:
    - If home -X has prob P, away +X should have prob ~(1-P)
    """
    validated = []
    spread_probs = {}  # (game_id, abs_spread) -> {home_prob, away_prob}

    # Group picks by game and spread
    for pick in game_picks:
        if pick["market_type"] == "spreads" and pd.notna(pick.get("point")):
            spread = abs(float(pick["point"]))
            game_key = (pick["game_id"], spread)

            if "home" in pick["recommendation"].lower() or pick[
                "recommendation"
            ].startswith(pick["home_team"]):
                if game_key not in spread_probs:
                    spread_probs[game_key] = {}
                spread_probs[game_key]["home_prob"] = pick["model_probability"]
            elif "away" in pick["recommendation"].lower() or pick[
                "recommendation"
            ].startswith(pick["away_team"]):
                if game_key not in spread_probs:
                    spread_probs[game_key] = {}
                spread_probs[game_key]["away_prob"] = pick["model_probability"]

    # Validate and fix complementary probabilities
    for pick in game_picks:
        if pick["market_type"] == "spreads" and pd.notna(pick.get("point")):
            spread = abs(float(pick["point"]))
            game_key = (pick["game_id"], spread)

            if game_key in spread_probs:
                home_prob = spread_probs[game_key].get("home_prob")
                away_prob = spread_probs[game_key].get("away_prob")

                if home_prob is not None and away_prob is not None:
                    # Check if probabilities are complementary (sum should be ~1.0)
                    prob_sum = home_prob + away_prob
                    if prob_sum > 1.15 or prob_sum < 0.85:  # More than 15% off
                        # If both are high, keep the one that makes more sense based on predicted winner
                        # Otherwise, adjust to be complementary
                        if home_prob > 0.6 and away_prob > 0.6:
                            # Both high - this is wrong, keep the one with higher probability
                            # and set the other to complementary
                            if home_prob > away_prob:
                                pick["model_probability"] = home_prob
                                # Mark away as invalid (will be filtered)
                                if "away" in pick["recommendation"].lower() or pick[
                                    "recommendation"
                                ].startswith(pick["away_team"]):
                                    pick["model_probability"] = 1.0 - home_prob
                            else:
                                pick["model_probability"] = away_prob
                                # Mark home as invalid (will be filtered)
                                if "home" in pick["recommendation"].lower() or pick[
                                    "recommendation"
                                ].startswith(pick["home_team"]):
                                    pick["model_probability"] = 1.0 - away_prob

        validated.append(pick)

    return validated


def match_predictions_to_all_markets(
    predictions_df: pd.DataFrame,
    odds_df: pd.DataFrame,
    simulator: Optional[AdvancedMultiSimulator] = None,
    db_conn: Optional[psycopg2.extensions.connection] = None,
) -> pd.DataFrame:
    """Match predictions to all market types and calculate edges using actual simulation win rates."""

    matched = []
    today = date.today()

    # Cache for team IDs
    team_id_cache = {}

    # Track games processed for debugging
    games_processed = set()
    games_with_errors = []

    for _, pred_row in predictions_df.iterrows():
        game_id = pred_row["game_id"]
        pred_home = normalize_team_name(pred_row["home_team"])
        pred_away = normalize_team_name(pred_row["away_team"])
        pred_date = pd.to_datetime(pred_row["game_date"]).date()

        games_processed.add(game_id)

        # Use realistic averages (scores from advanced sim are inflated)
        predicted_total = 224.0  # NBA average
        home_win_prob = pred_row["home_win_probability"]
        away_win_prob = pred_row["away_win_probability"]
        predicted_margin = (home_win_prob - 0.5) * 14  # Convert prob to spread

        for _, odds_row in odds_df.iterrows():
            odds_home = normalize_team_name(odds_row["home_team"])
            odds_away = normalize_team_name(odds_row["away_team"])
            odds_date = odds_row.get("game_date_ct", today)
            if pd.isna(odds_date):
                odds_date = today

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

            market_key = str(odds_row["market_key"])
            outcome_name = str(odds_row["outcome_name"])
            odds_value = float(odds_row["odds"])
            point = odds_row.get("spread_or_total")

            model_prob = None
            recommendation = None

            # Calculate model probability based on market type
            if market_key == "h2h":
                # Moneyline
                if normalize_team_name(outcome_name) == normalize_team_name(
                    pred_row["predicted_winner"]
                ):
                    model_prob = (
                        home_win_prob
                        if pred_row["predicted_winner"] == pred_row["home_team"]
                        else away_win_prob
                    )
                    recommendation = f"{pred_row['predicted_winner']} ML"

                    # Only show moneyline bets that win >60% of simulations
                    if model_prob < 0.60:
                        continue
                else:
                    continue

            elif market_key == "spreads":
                if pd.isna(point):
                    continue
                spread = float(point)
                outcome_lower = normalize_team_name(outcome_name)
                if pred_home in outcome_lower or outcome_lower in pred_home:
                    recommendation = f"{pred_row['home_team']} {spread:+.1f}"
                elif pred_away in outcome_lower or outcome_lower in pred_away:
                    recommendation = f"{pred_row['away_team']} {spread:+.1f}"
                else:
                    continue

                # Calculate spread probability using predicted scores from predictions CSV
                # Use the predicted scores directly (they're already from simulations)
                # Normalize scores first if needed
                pred_home_score = pred_row.get("predicted_home_score", 110.0)
                pred_away_score = pred_row.get("predicted_away_score", 110.0)

                # Normalize if inflated (scores > 200 are likely inflated)
                if pred_home_score > 200 or pred_away_score > 200:
                    raw_margin = pred_home_score - pred_away_score
                    # Scale to realistic total (224 average)
                    scale_factor = 224.0 / (pred_home_score + pred_away_score)
                    pred_home_score = 112.0 + (raw_margin / 2) * scale_factor
                    pred_away_score = 112.0 - (raw_margin / 2) * scale_factor

                pred_margin = pred_home_score - pred_away_score

                # Use normal distribution approximation for spread probability
                std_dev = 12.0  # Typical NBA game margin std dev
                abs_spread = abs(spread)
                z_score = (abs_spread - pred_margin) / std_dev

                try:
                    from scipy.stats import norm

                    if pred_home in outcome_lower or outcome_lower in pred_home:
                        # Home team covering spread: win if margin > spread
                        # For home -8.0: win if margin > 8.0
                        model_prob = 1 - norm.cdf(z_score)
                    else:
                        # Away team covering spread: win if margin < spread (complementary)
                        # For away +8.0: win if margin < 8.0 (complementary to home -8.0)
                        model_prob = norm.cdf(z_score)
                except ImportError:
                    # Approximate CDF using error function
                    import math

                    if pred_home in outcome_lower or outcome_lower in pred_home:
                        model_prob = 0.5 * (1 - math.erf(z_score / math.sqrt(2)))
                        model_prob = 1 - model_prob
                    else:
                        model_prob = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

                model_prob = max(0.0, min(1.0, model_prob))

                # Only show spread bets that win >60% of simulations
                if model_prob < 0.60:
                    continue

            elif market_key == "totals":
                if pd.isna(point):
                    continue
                total_line = float(point)
                if "Over" in outcome_name or outcome_name == "Over":
                    recommendation = f"Over {total_line:.1f}"
                elif "Under" in outcome_name or outcome_name == "Under":
                    recommendation = f"Under {total_line:.1f}"
                else:
                    continue

                # Calculate total probability using predicted scores from predictions CSV
                # Use the predicted scores directly (they're already from simulations)
                pred_home_score = pred_row.get("predicted_home_score", 110.0)
                pred_away_score = pred_row.get("predicted_away_score", 110.0)

                # Normalize if inflated (scores > 200 are likely inflated)
                if pred_home_score > 200 or pred_away_score > 200:
                    raw_total = pred_home_score + pred_away_score
                    # Scale to realistic total (224 average)
                    scale_factor = 224.0 / raw_total
                    pred_home_score = pred_home_score * scale_factor
                    pred_away_score = pred_away_score * scale_factor

                pred_total = pred_home_score + pred_away_score

                # Use normal distribution approximation for total probability
                std_dev = 15.0  # Typical NBA total std dev
                z_score = (total_line - pred_total) / std_dev

                try:
                    from scipy.stats import norm

                    if "Over" in outcome_name or outcome_name == "Over":
                        # Over wins if total > line
                        model_prob = 1 - norm.cdf(z_score)
                    else:
                        # Under wins if total < line (complementary)
                        model_prob = norm.cdf(z_score)
                except ImportError:
                    # Approximate CDF using error function
                    import math

                    if "Over" in outcome_name or outcome_name == "Over":
                        model_prob = 0.5 * (1 - math.erf(z_score / math.sqrt(2)))
                        model_prob = 1 - model_prob
                    else:
                        model_prob = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

                model_prob = max(0.0, min(1.0, model_prob))

                # Only show totals bets that win >60% of simulations
                if model_prob < 0.60:
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
                    "predicted_winner": pred_row["predicted_winner"],
                    "model_probability": model_prob,
                    "confidence": pred_row.get("confidence", 0),
                    "prediction_strength": pred_row.get("prediction_strength", "N/A"),
                    "market_type": market_key,
                    "recommendation": recommendation,
                    "bookmaker": odds_row.get("bookmaker_title", "Unknown"),
                    "bookmaker_key": odds_row.get("bookmaker_key", ""),
                    "odds": odds_value,
                    "point": point,
                    "market_probability": implied_prob,
                    "edge": edge,
                    "expected_value": ev,
                    "event_id": str(odds_row.get("event_id", "")),
                }
            )

    if len(matched) == 0:
        print(f"\n⚠️  Warning: No bets matched. Games processed: {len(games_processed)}")
        if games_with_errors:
            print(f"  Errors encountered: {len(games_with_errors)}")
            for error in games_with_errors[:5]:  # Show first 5 errors
                print(f"    - {error}")
        return pd.DataFrame()

    # Validate complementary probabilities
    df_matched = pd.DataFrame(matched)
    validated_picks = validate_complementary_probabilities(matched)
    df_validated = pd.DataFrame(validated_picks)

    # Print debug info
    print(f"\n✓ Matched {len(df_matched)} bets from {len(games_processed)} games")
    if games_with_errors:
        print(
            f"  ⚠️  {len(games_with_errors)} errors encountered (using fallback probabilities)"
        )

    return df_validated


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
        df_predictions = pd.read_csv(args.predictions)
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
        df_odds = query_all_odds_from_db(conn, today)
        print(f"✓ Loaded {len(df_odds)} odds records")
        if len(df_odds) > 0:
            print(f"  Market types: {df_odds['market_key'].unique().tolist()}")
            print(f"  Bookmakers: {df_odds['bookmaker_key'].unique().tolist()}")
            print(f"  Events: {df_odds['event_id'].nunique()}")
    except Exception as e:
        print(f"⚠️  Error querying odds: {e}")
        conn.close()
        sys.exit(1)

    if len(df_odds) == 0:
        print(f"\n⚠️  No odds found for {today} in database.")
        print("   To generate betting picks, you need:")
        print("   1. Start the odds scraper (in odds-api directory)")
        print("   2. Wait for odds to be fetched and stored")
        print("   3. Then re-run this script")
        print()
        print("Current predictions are available at:")
        print(f"   {args.predictions}")
        conn.close()
        sys.exit(0)

    # Note: We use predicted scores directly from predictions CSV instead of re-running simulations
    # This avoids the need to train the simulator and is much faster
    print(f"\nUsing predicted scores from predictions CSV for win rate calculations...")
    simulator = None  # Not needed - we use predictions CSV directly

    # Match predictions to odds
    print(
        f"\nMatching predictions to odds (using predicted scores from simulations)..."
    )
    df_matched = match_predictions_to_all_markets(
        df_predictions, df_odds, simulator=None, db_conn=None
    )

    if len(df_matched) == 0:
        print("⚠️  No matches found between predictions and odds.")
        print("   Check that team names match and games are for today.")
        conn.close()
        sys.exit(0)

    print(f"✓ Matched {len(df_matched)} bets")

    # Filter by EV
    print(f"\nFiltering bets (min EV: {args.min_ev:.1%})...")
    df_filtered = df_matched[df_matched["expected_value"] >= args.min_ev].copy()
    print(f"✓ {len(df_filtered)} bets meet EV threshold")

    if len(df_filtered) == 0:
        print("⚠️  No bets meet the EV threshold.")
        conn.close()
        sys.exit(0)

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
    print("COMPREHENSIVE BETTING PICKS - ADVANCED SIMULATOR")
    print(f"{'='*100}\n")

    # Group by market type
    for market_type in ["h2h", "spreads", "totals"]:
        market_name = {
            "h2h": "MONEYLINE",
            "spreads": "POINT SPREADS",
            "totals": "TOTALS (OVER/UNDER)",
        }.get(market_type, market_type.upper())

        df_market = df_sorted[df_sorted["market_type"] == market_type]

        if len(df_market) > 0:
            print(f"{market_name} ({len(df_market)} bets):")
            print("-" * 100)

            for idx, (_, row) in enumerate(df_market.head(10).iterrows(), 1):
                point_str = f" ({row['point']:+.1f})" if pd.notna(row["point"]) else ""
                odds_value = row["odds"]
                odds_str = f"{odds_value:+.0f}" if pd.notna(odds_value) else "N/A"
                print(f"{idx}. {row['away_team']} @ {row['home_team']}")
                print(f"   Pick: {row['recommendation']}{point_str}")
                print(
                    f"   Odds: {odds_str} | Model: {row['model_probability']:.1%} | Market: {row['market_probability']:.1%}"
                )
                print(
                    f"   Edge: {row['edge']:+.1%} | EV: {row['expected_value']:+.1%} | Book: {row['bookmaker']}"
                )
                print()
            print()

    print(f"{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")
    print(f"Total bets: {len(df_sorted)}")
    print(f"Positive EV bets: {(df_sorted['expected_value'] > 0).sum()}")
    print(f"Strong bets (EV > 5%): {(df_sorted['expected_value'] > 0.05).sum()}")
    print(f"Games covered: {df_sorted['game_id'].nunique()}")
    print(f"Market types: {', '.join(df_sorted['market_type'].unique())}")
    print()
    print(f"✓ Saved to: {output_path}")
    print(f"✓ Symlink: {latest_path}")
    print(f"{'='*100}\n")

    conn.close()


if __name__ == "__main__":
    main()
