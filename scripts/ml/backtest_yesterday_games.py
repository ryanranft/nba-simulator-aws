#!/usr/bin/env python3
"""
Backtest Yesterday's Games Using Improved Simulator

This script:
1. Fetches actual game results from ESPN API for a specific date
2. Generates predictions using the improved simulator (trained on data before that date)
3. Compares predictions vs actual results
4. Calculates comprehensive accuracy metrics

Usage:
    python scripts/ml/backtest_yesterday_games.py --date 2025-11-02
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
from pytz import timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advanced_multi_simulator import AdvancedMultiSimulator
import requests
import logging
import psycopg2
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_actual_results_from_espn(game_date: date) -> pd.DataFrame:
    """Fetch actual game results from ESPN API"""
    logger.info(f"Fetching actual results from ESPN API for {game_date}...")

    date_str = game_date.strftime("%Y%m%d")
    espn_api = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

    try:
        response = requests.get(espn_api, params={"dates": date_str}, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        if "events" in data:
            for event in data["events"]:
                status = event.get("status", {}).get("type", {}).get("name", "")

                # Only include completed games
                if status != "STATUS_FINAL":
                    continue

                game_id = event.get("id")
                competitions = event.get("competitions", [])

                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get("competitors", [])

                if len(competitors) != 2:
                    continue

                # Get teams and scores
                home_team = None
                away_team = None

                for competitor in competitors:
                    team_info = competitor.get("team", {})
                    home_away = competitor.get("homeAway", "")
                    score = int(competitor.get("score", 0))
                    winner = competitor.get("winner", False)

                    team_data = {
                        "name": team_info.get("displayName", ""),
                        "abbreviation": team_info.get("abbreviation", ""),
                        "score": score,
                        "winner": winner,
                    }

                    if home_away == "home":
                        home_team = team_data
                    else:
                        away_team = team_data

                if not home_team or not away_team:
                    continue

                results.append({
                    "game_id": game_id,
                    "game_date": game_date.strftime("%Y-%m-%d"),
                    "home_team_name": home_team["name"],
                    "away_team_name": away_team["name"],
                    "home_team_abbr": home_team["abbreviation"],
                    "away_team_abbr": away_team["abbreviation"],
                    "home_score": home_team["score"],
                    "away_score": away_team["score"],
                    "home_win": 1 if home_team["winner"] else 0,
                    "actual_winner": home_team["name"] if home_team["winner"] else away_team["name"],
                })

        df = pd.DataFrame(results)
        logger.info(f"  ✓ Found {len(df)} completed games")
        return df

    except Exception as e:
        logger.error(f"  ⚠️  Error fetching results: {e}")
        return pd.DataFrame()


def get_team_ids_from_names(home_name: str, away_name: str) -> tuple:
    """Get team IDs from team names"""
    load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )

    # Try to match team names (fuzzy matching)
    query = """
    SELECT team_id, team_name, team_abbreviation
    FROM teams
    WHERE team_name ILIKE %s OR team_name ILIKE %s
       OR team_abbreviation ILIKE %s OR team_abbreviation ILIKE %s
    """

    home_id = None
    away_id = None

    # Try home team
    home_df = pd.read_sql(query, conn, params=(f"%{home_name}%", f"%{home_name}%", f"%{home_name}%", f"%{home_name}%"))
    if len(home_df) > 0:
        home_id = home_df.iloc[0]['team_id']

    # Try away team
    away_df = pd.read_sql(query, conn, params=(f"%{away_name}%", f"%{away_name}%", f"%{away_name}%", f"%{away_name}%"))
    if len(away_df) > 0:
        away_id = away_df.iloc[0]['team_id']

    conn.close()

    return home_id, away_id


def generate_predictions_for_games(
    games_df: pd.DataFrame,
    simulator: AdvancedMultiSimulator
) -> pd.DataFrame:
    """Generate predictions for all games"""
    predictions = []

    for _, game in games_df.iterrows():
        home_name = game['home_team_name']
        away_name = game['away_team_name']
        game_date_obj = datetime.strptime(game['game_date'], '%Y-%m-%d').date()

        logger.info(f"Predicting: {away_name} @ {home_name}")

        # Get team IDs
        home_id, away_id = get_team_ids_from_names(home_name, away_name)

        if not home_id or not away_id:
            logger.warning(f"  ⚠️  Could not find team IDs for {away_name} @ {home_name}")
            continue

        try:
            # Get ensemble prediction
            ensemble_result, individual_results = simulator.predict_game(
                home_team_id=home_id,
                away_team_id=away_id,
                game_date=game_date_obj,
                use_ensemble=True,
                n_simulations=10000
            )

            # Calculate prediction strength
            confidence = ensemble_result.confidence
            if confidence >= 0.75:
                prediction_strength = "Very Strong"
            elif confidence >= 0.65:
                prediction_strength = "Strong"
            elif confidence >= 0.55:
                prediction_strength = "Moderate"
            elif confidence >= 0.45:
                prediction_strength = "Weak"
            else:
                prediction_strength = "Very Weak"

            predicted_winner = home_name if ensemble_result.home_win_prob > 0.5 else away_name

            predictions.append({
                'game_id': game['game_id'],
                'game_date': game['game_date'],
                'home_team_name': home_name,
                'away_team_name': away_name,
                'home_team_id': home_id,
                'away_team_id': away_id,
                'predicted_winner': predicted_winner,
                'actual_winner': game['actual_winner'],
                'predicted_home_score': ensemble_result.predicted_home_score,
                'predicted_away_score': ensemble_result.predicted_away_score,
                'actual_home_score': game['home_score'],
                'actual_away_score': game['away_score'],
                'home_win_probability': ensemble_result.home_win_prob,
                'away_win_probability': ensemble_result.away_win_prob,
                'confidence': confidence,
                'prediction_strength': prediction_strength,
                'correct': predicted_winner == game['actual_winner'],
            })

            logger.info(f"  ✓ Predicted: {predicted_winner} ({ensemble_result.home_win_prob:.1%})")

        except Exception as e:
            logger.error(f"  ✗ Error predicting {away_name} @ {home_name}: {e}")
            continue

    return pd.DataFrame(predictions)


def query_odds_from_db(conn, game_date: date) -> pd.DataFrame:
    """Query betting odds from database for a specific date"""
    logger.info(f"Querying betting odds from database for {game_date}...")

    chicago_tz = timezone('America/Chicago')

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

    try:
        df = pd.read_sql(query, conn, params=(game_date,))

        if len(df) > 0:
            df['commence_time'] = pd.to_datetime(df['commence_time'], utc=True)
            df['commence_time_ct'] = df['commence_time'].dt.tz_convert(chicago_tz)
            df['game_date_ct'] = df['commence_time_ct'].dt.date

        logger.info(f"  ✓ Found {len(df)} odds records")
        return df
    except Exception as e:
        logger.warning(f"  ⚠️  Error querying odds: {e}")
        return pd.DataFrame()


def normalize_team_name(name: str) -> str:
    """Normalize team name for matching"""
    if pd.isna(name):
        return ""
    name = str(name).strip().lower()
    name = name.replace("philadelphia 76ers", "76ers").replace("sixers", "76ers")
    name = name.replace("la clippers", "clippers").replace("l.a. clippers", "clippers")
    name = name.replace("la lakers", "lakers").replace("l.a. lakers", "lakers")
    return name


def determine_bet_outcome(
    market_key: str,
    outcome_name: str,
    point: float,
    actual_home_score: int,
    actual_away_score: int,
    home_team_name: str,
    away_team_name: str
) -> bool:
    """Determine if a bet won based on actual game results"""
    if market_key == 'h2h':
        # Moneyline - check if predicted team won
        outcome_normalized = normalize_team_name(outcome_name)
        home_normalized = normalize_team_name(home_team_name)
        away_normalized = normalize_team_name(away_team_name)

        if outcome_normalized in home_normalized or home_normalized in outcome_normalized:
            return actual_home_score > actual_away_score
        elif outcome_normalized in away_normalized or away_normalized in outcome_normalized:
            return actual_away_score > actual_home_score
        return False

    elif market_key == 'spreads':
        # Point spread
        if pd.isna(point):
            return False

        spread = float(point)
        outcome_normalized = normalize_team_name(outcome_name)
        home_normalized = normalize_team_name(home_team_name)
        away_normalized = normalize_team_name(away_team_name)

        actual_margin = actual_home_score - actual_away_score

        if outcome_normalized in home_normalized or home_normalized in outcome_normalized:
            # Home team covering spread
            return actual_margin > spread
        elif outcome_normalized in away_normalized or away_normalized in outcome_normalized:
            # Away team covering spread
            return actual_margin < -spread
        return False

    elif market_key == 'totals':
        # Over/Under
        if pd.isna(point):
            return False

        total_line = float(point)
        actual_total = actual_home_score + actual_away_score

        if 'Over' in outcome_name or outcome_name == 'Over':
            return actual_total > total_line
        elif 'Under' in outcome_name or outcome_name == 'Under':
            return actual_total < total_line
        return False

    return False


def match_predictions_to_odds_and_calculate_outcomes(
    predictions_df: pd.DataFrame,
    odds_df: pd.DataFrame
) -> pd.DataFrame:
    """Match predictions to odds and determine bet outcomes"""
    matched_bets = []

    for _, pred_row in predictions_df.iterrows():
        pred_home = normalize_team_name(pred_row['home_team_name'])
        pred_away = normalize_team_name(pred_row['away_team_name'])
        actual_home_score = pred_row['actual_home_score']
        actual_away_score = pred_row['actual_away_score']
        actual_margin = actual_home_score - actual_away_score
        actual_total = actual_home_score + actual_away_score

        # Get predicted values (use actual scores if predicted scores are inflated)
        predicted_home_score = pred_row['predicted_home_score']
        predicted_away_score = pred_row['predicted_away_score']

        # If predicted scores are unrealistic (too high), use win probability to estimate
        if predicted_home_score > 200 or predicted_away_score > 200:
            # Use win probability to estimate realistic scores
            home_win_prob = pred_row['home_win_probability']
            avg_total = 225.0  # NBA average
            predicted_margin = (home_win_prob - 0.5) * 14  # Convert to spread
            predicted_home_score = (avg_total + predicted_margin) / 2
            predicted_away_score = (avg_total - predicted_margin) / 2

        predicted_margin = predicted_home_score - predicted_away_score
        predicted_total = predicted_home_score + predicted_away_score

        for _, odds_row in odds_df.iterrows():
            odds_home = normalize_team_name(odds_row['home_team'])
            odds_away = normalize_team_name(odds_row['away_team'])

            # Match teams
            home_match = (pred_home == odds_home or pred_home in odds_home or odds_home in pred_home)
            away_match = (pred_away == odds_away or pred_away in odds_away or odds_away in pred_away)

            if not (home_match and away_match):
                continue

            market_key = str(odds_row['market_key'])
            outcome_name = str(odds_row['outcome_name'])
            odds_value = float(odds_row['odds']) if pd.notna(odds_row['odds']) else None
            point = odds_row.get('spread_or_total')

            # Determine if this bet won
            bet_won = determine_bet_outcome(
                market_key,
                outcome_name,
                point,
                actual_home_score,
                actual_away_score,
                pred_row['home_team_name'],
                pred_row['away_team_name']
            )

            # Calculate payout if bet won
            payout = 0.0
            if bet_won and odds_value is not None:
                if odds_value > 0:
                    payout = odds_value
                else:
                    payout = 100 * (100 / abs(odds_value))

            matched_bets.append({
                'game_id': pred_row['game_id'],
                'home_team': pred_row['home_team_name'],
                'away_team': pred_row['away_team_name'],
                'predicted_winner': pred_row['predicted_winner'],
                'actual_winner': pred_row['actual_winner'],
                'market_type': market_key,
                'outcome_name': outcome_name,
                'bookmaker': odds_row.get('bookmaker_title', 'Unknown'),
                'odds': odds_value,
                'point': point,
                'bet_won': bet_won,
                'payout': payout,
                'actual_home_score': actual_home_score,
                'actual_away_score': actual_away_score,
                'actual_margin': actual_margin,
                'actual_total': actual_total,
                'predicted_margin': predicted_margin,
                'predicted_total': predicted_total,
            })

    return pd.DataFrame(matched_bets)


def calculate_betting_metrics(df_bets: pd.DataFrame) -> Dict:
    """Calculate betting accuracy metrics"""
    if len(df_bets) == 0:
        return {}

    total_bets = len(df_bets)
    winning_bets = df_bets['bet_won'].sum()
    win_rate = winning_bets / total_bets if total_bets > 0 else 0.0

    # Calculate ROI (assuming $100 bets)
    total_wagered = total_bets * 100
    total_winnings = df_bets[df_bets['bet_won']]['payout'].sum()
    roi = ((total_winnings - total_wagered) / total_wagered) * 100 if total_wagered > 0 else 0.0

    # By market type
    by_market = {}
    for market in df_bets['market_type'].unique():
        market_bets = df_bets[df_bets['market_type'] == market]
        market_wins = market_bets['bet_won'].sum()
        market_total = len(market_bets)
        by_market[market] = {
            'total': market_total,
            'wins': market_wins,
            'win_rate': market_wins / market_total if market_total > 0 else 0.0
        }

    return {
        'total_bets': total_bets,
        'winning_bets': winning_bets,
        'win_rate': win_rate,
        'total_wagered': total_wagered,
        'total_winnings': total_winnings,
        'roi': roi,
        'by_market': by_market,
    }


def calculate_accuracy_metrics(df_predictions: pd.DataFrame) -> Dict:
    """Calculate comprehensive accuracy metrics"""
    if len(df_predictions) == 0:
        return {}

    # Win probability accuracy
    win_accuracy = df_predictions['correct'].mean()

    # Score accuracy
    df_predictions['home_score_error'] = df_predictions['predicted_home_score'] - df_predictions['actual_home_score']
    df_predictions['away_score_error'] = df_predictions['predicted_away_score'] - df_predictions['actual_away_score']
    df_predictions['predicted_total'] = df_predictions['predicted_home_score'] + df_predictions['predicted_away_score']
    df_predictions['actual_total'] = df_predictions['actual_home_score'] + df_predictions['actual_away_score']
    df_predictions['total_error'] = df_predictions['predicted_total'] - df_predictions['actual_total']
    df_predictions['predicted_margin'] = df_predictions['predicted_home_score'] - df_predictions['predicted_away_score']
    df_predictions['actual_margin'] = df_predictions['actual_home_score'] - df_predictions['actual_away_score']
    df_predictions['margin_error'] = df_predictions['predicted_margin'] - df_predictions['actual_margin']

    # Score MAE
    home_score_mae = df_predictions['home_score_error'].abs().mean()
    away_score_mae = df_predictions['away_score_error'].abs().mean()
    score_mae = (home_score_mae + away_score_mae) / 2

    # Score RMSE
    home_score_rmse = np.sqrt((df_predictions['home_score_error'] ** 2).mean())
    away_score_rmse = np.sqrt((df_predictions['away_score_error'] ** 2).mean())
    score_rmse = np.sqrt((home_score_rmse ** 2 + away_score_rmse ** 2) / 2)

    # Total Points MAE
    total_points_mae = df_predictions['total_error'].abs().mean()

    # Margin MAE
    margin_mae = df_predictions['margin_error'].abs().mean()

    # Brier Score
    actual_home_win = (df_predictions['actual_winner'] == df_predictions['home_team_name']).astype(int)
    pred_home_win_prob = df_predictions['home_win_probability'].values
    brier_score = np.mean((pred_home_win_prob - actual_home_win) ** 2)

    return {
        'total_games': len(df_predictions),
        'correct': df_predictions['correct'].sum(),
        'incorrect': (~df_predictions['correct']).sum(),
        'win_accuracy': win_accuracy,
        'home_score_mae': home_score_mae,
        'away_score_mae': away_score_mae,
        'score_mae': score_mae,
        'home_score_rmse': home_score_rmse,
        'away_score_rmse': away_score_rmse,
        'score_rmse': score_rmse,
        'total_points_mae': total_points_mae,
        'margin_mae': margin_mae,
        'brier_score': brier_score,
    }


def generate_report(df_predictions: pd.DataFrame, metrics: Dict, output_path: Path):
    """Generate comprehensive report"""
    print("\n" + "="*80)
    print("YESTERDAY'S GAMES BACKTEST REPORT")
    print("="*80)

    print(f"\nOverall Performance:")
    print(f"  Total Games: {metrics['total_games']}")
    print(f"  Correct Predictions: {metrics['correct']}")
    print(f"  Incorrect Predictions: {metrics['incorrect']}")
    print(f"  Win Accuracy: {metrics['win_accuracy']:.1%}")

    print(f"\nScore Accuracy Metrics:")
    print(f"  Home Score MAE: {metrics['home_score_mae']:.2f} points")
    print(f"  Away Score MAE: {metrics['away_score_mae']:.2f} points")
    print(f"  Average Score MAE: {metrics['score_mae']:.2f} points")
    print(f"  Average Score RMSE: {metrics['score_rmse']:.2f} points")
    print(f"  Total Points MAE: {metrics['total_points_mae']:.2f} points")
    print(f"  Margin MAE: {metrics['margin_mae']:.2f} points")
    print(f"  Brier Score: {metrics['brier_score']:.4f} (lower is better)")

    print(f"\nGame-by-Game Results:")
    print("="*80)
    for _, game in df_predictions.iterrows():
        status = "✓" if game['correct'] else "✗"
        print(f"\n{status} {game['away_team_name']} @ {game['home_team_name']}")
        print(f"  Winner: Predicted {game['predicted_winner']}, Actual {game['actual_winner']}")
        print(f"  Score: Predicted {game['home_team_name']} {game['predicted_home_score']:.1f} - {game['away_team_name']} {game['predicted_away_score']:.1f}")
        print(f"         Actual    {game['home_team_name']} {game['actual_home_score']} - {game['away_team_name']} {game['actual_away_score']}")
        print(f"  Errors: Home {game['home_score_error']:+.1f}, Away {game['away_score_error']:+.1f}, Total {game['total_error']:+.1f}")
        print(f"  Strength: {game['prediction_strength']}, Confidence: {game['confidence']:.1%}")

    # Betting results
    if metrics.get('betting') and metrics['betting'] is not None:
        betting = metrics['betting']
        bets_df = metrics.get('bets_df', pd.DataFrame())

        print(f"\n\nBetting Results:")
        print("="*80)
        print(f"Total Bets: {betting['total_bets']}")
        print(f"Winning Bets: {betting['winning_bets']}")
        print(f"Win Rate: {betting['win_rate']:.1%}")
        print(f"Total Wagered: ${betting['total_wagered']:,.0f} (assuming $100 per bet)")
        print(f"Total Winnings: ${betting['total_winnings']:,.0f}")
        print(f"ROI: {betting['roi']:.1f}%")

        print(f"\nBy Market Type:")
        for market, stats in betting['by_market'].items():
            market_name = {'h2h': 'Moneyline', 'spreads': 'Spreads', 'totals': 'Totals'}.get(market, market)
            print(f"  {market_name}: {stats['wins']}/{stats['total']} ({stats['win_rate']:.1%})")

        if len(bets_df) > 0:
            print(f"\nBet-by-Bet Results:")
            print("-"*80)
            for _, bet in bets_df.iterrows():
                status = "✓" if bet['bet_won'] else "✗"
                market_name = {'h2h': 'ML', 'spreads': 'Spread', 'totals': 'Total'}.get(bet['market_type'], bet['market_type'])
                print(f"{status} {bet['away_team']} @ {bet['home_team']} - {market_name}: {bet['outcome_name']} {bet.get('point', '')}")
                print(f"    Odds: {bet['odds']}, Payout: ${bet['payout']:.0f} if won")

            # Save bets to CSV
            bets_output_path = output_path.parent / f"{output_path.stem}_bets.csv"
            bets_df.to_csv(bets_output_path, index=False)
            print(f"\n✓ Betting results saved to: {bets_output_path}")

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_predictions.to_csv(output_path, index=False)
    print(f"\n✓ Detailed report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Backtest yesterday's games using improved simulator"
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date to backtest (YYYY-MM-DD). Default: yesterday'
    )
    parser.add_argument(
        '--train-seasons',
        type=str,
        default='2020-2024',
        help='Training seasons (e.g., 2020-2024)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='/tmp/yesterday_backtest_predictions.csv',
        help='Output CSV file path'
    )

    args = parser.parse_args()

    # Parse date
    if args.date:
        game_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        game_date = date.today() - timedelta(days=1)

    # Parse training seasons
    if '-' in args.train_seasons:
        start_season, end_season = map(int, args.train_seasons.split('-'))
    else:
        start_season = end_season = int(args.train_seasons)

    logger.info("="*80)
    logger.info("YESTERDAY'S GAMES BACKTEST")
    logger.info("="*80)
    logger.info(f"Game Date: {game_date}")
    logger.info(f"Training Seasons: {start_season}-{end_season}")
    logger.info("")

    # Fetch actual results
    logger.info("[1/3] Fetching actual game results...")
    actual_games = fetch_actual_results_from_espn(game_date)

    if len(actual_games) == 0:
        logger.error("No completed games found for this date")
        return

    # Initialize simulator
    logger.info("\n[2/3] Training improved simulator...")
    simulator = AdvancedMultiSimulator()

    try:
        # Train simulators (using data before game_date)
        simulator.train_all(start_season=start_season, end_season=end_season)

        # Generate predictions
        logger.info("\n[3/3] Generating predictions...")
        predictions_df = generate_predictions_for_games(actual_games, simulator)

        if len(predictions_df) == 0:
            logger.error("No predictions generated")
            return

        # Calculate metrics
        metrics = calculate_accuracy_metrics(predictions_df)

        # Fetch and match betting odds
        logger.info("\n[4/4] Fetching betting odds and calculating bet outcomes...")
        load_dotenv("/Users/ryanranft/nba-sim-credentials.env")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            sslmode='require'
        )

        try:
            odds_df = query_odds_from_db(conn, game_date)

            if len(odds_df) > 0:
                bets_df = match_predictions_to_odds_and_calculate_outcomes(predictions_df, odds_df)
                betting_metrics = calculate_betting_metrics(bets_df)

                # Add betting metrics to report
                metrics['betting'] = betting_metrics
                metrics['bets_df'] = bets_df
            else:
                logger.warning("  ⚠️  No odds found in database for this date")
                metrics['betting'] = None
                metrics['bets_df'] = pd.DataFrame()
        except Exception as e:
            logger.warning(f"  ⚠️  Error fetching odds: {e}")
            metrics['betting'] = None
            metrics['bets_df'] = pd.DataFrame()
        finally:
            conn.close()

        # Generate report
        output_path = Path(args.output)
        generate_report(predictions_df, metrics, output_path)

        print("\n" + "="*80)
        print("BACKTEST COMPLETE")
        print("="*80)

    finally:
        simulator.close()


if __name__ == "__main__":
    main()

