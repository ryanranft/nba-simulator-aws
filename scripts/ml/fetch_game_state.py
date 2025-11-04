#!/usr/bin/env python3
"""
Fetch Current Game State from game_states Table

This module provides functionality to query the game_states table
to get the current state of in-progress games, including:
- Current scores (home and away)
- Current quarter
- Time remaining in quarter
- Game status (in_progress, halftime, etc.)

Usage:
    from scripts.ml.fetch_game_state import get_game_state

    game_state = get_game_state(game_id="401234567", db_conn=conn)
    if game_state:
        print(f"Current score: {game_state['current_score_home']} - {game_state['current_score_away']}")
        print(f"Quarter: {game_state['quarter']}")
        print(f"Time remaining: {game_state['game_clock_seconds']} seconds")

Created: November 3, 2025
Author: NBA Simulator AWS Project
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from datetime import datetime, date
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
env_paths = [
    "/Users/ryanranft/nba-sim-credentials.env",
    "/Users/ryanranft/nba-simulator-aws/.env",
    os.path.expanduser("~/.env")
]

for path in env_paths:
    if os.path.exists(path):
        load_dotenv(path)
        break


def get_game_state(
    game_id: str,
    db_conn: Optional[psycopg2.extensions.connection] = None,
    game_date: Optional[date] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent game state for a given game_id.

    Queries the game_states table for the most recent state before/at current time.
    Returns None if no game state is found or if game is not in progress.

    Args:
        game_id: Game identifier (e.g., "401234567")
        db_conn: PostgreSQL connection object. If None, creates a new connection.
        game_date: Optional game date for validation (not currently used but available for future use)

    Returns:
        Dictionary with game state information:
        {
            'current_score_home': int,
            'current_score_away': int,
            'quarter': int,
            'game_clock_seconds': int (or None),
            'game_status': str ('in_progress', 'halftime', 'final', 'scheduled'),
            'score_differential': int,
            'state_time': datetime
        }
        Or None if no game state found or game is not in progress.
    """
    # Create connection if not provided
    conn = db_conn
    close_conn = False

    if conn is None:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432)
            )
            close_conn = True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None

    try:
        query = """
        SELECT
            current_score_home,
            current_score_away,
            quarter,
            game_clock_seconds,
            game_status,
            score_differential,
            state_time
        FROM game_states
        WHERE game_id = %s
          AND state_time <= NOW()
          AND game_status IN ('in_progress', 'halftime')
        ORDER BY state_time DESC
        LIMIT 1
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (game_id,))
            result = cursor.fetchone()

            if result is None:
                logger.debug(f"No in-progress game state found for game_id: {game_id}")
                return None

            # Convert to dictionary
            game_state = {
                'current_score_home': int(result['current_score_home']) if result['current_score_home'] is not None else 0,
                'current_score_away': int(result['current_score_away']) if result['current_score_away'] is not None else 0,
                'quarter': int(result['quarter']) if result['quarter'] is not None else 1,
                'game_clock_seconds': int(result['game_clock_seconds']) if result['game_clock_seconds'] is not None else None,
                'game_status': str(result['game_status']) if result['game_status'] else 'unknown',
                'score_differential': int(result['score_differential']) if result['score_differential'] is not None else 0,
                'state_time': result['state_time']
            }

            logger.info(
                f"Found game state for {game_id}: "
                f"Q{game_state['quarter']} "
                f"{game_state['current_score_home']}-{game_state['current_score_away']} "
                f"({game_state['game_status']})"
            )

            return game_state

    except Exception as e:
        logger.error(f"Error querying game state for game_id {game_id}: {e}")
        return None

    finally:
        if close_conn and conn:
            conn.close()


def get_game_state_by_team_names(
    home_team_name: str,
    away_team_name: str,
    game_date: date,
    db_conn: Optional[psycopg2.extensions.connection] = None
) -> Optional[Dict[str, Any]]:
    """
    Get game state by team names and game date.

    First finds the game_id by matching team names and date,
    then calls get_game_state().

    Args:
        home_team_name: Home team name
        away_team_name: Away team name
        game_date: Game date
        db_conn: PostgreSQL connection object. If None, creates a new connection.

    Returns:
        Dictionary with game state information (same format as get_game_state)
        Or None if game not found or not in progress.
    """
    # Create connection if not provided
    conn = db_conn
    close_conn = False

    if conn is None:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432)
            )
            close_conn = True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None

    try:
        # First, find the game_id by team names and date
        query = """
        SELECT g.game_id
        FROM games g
        JOIN teams th ON g.home_team_id = th.team_id
        JOIN teams ta ON g.away_team_id = ta.team_id
        WHERE g.game_date = %s
          AND (
            (LOWER(th.team_name) LIKE LOWER(%s) OR LOWER(th.team_name) LIKE LOWER(%s))
            AND (LOWER(ta.team_name) LIKE LOWER(%s) OR LOWER(ta.team_name) LIKE LOWER(%s))
          )
        ORDER BY g.game_date DESC
        LIMIT 1
        """

        # Normalize team names for matching
        home_lower = home_team_name.lower()
        away_lower = away_team_name.lower()

        with conn.cursor() as cursor:
            cursor.execute(query, (
                game_date,
                f'%{home_lower}%',
                f'%{home_team_name.replace(" ", "%")}%',
                f'%{away_lower}%',
                f'%{away_team_name.replace(" ", "%")}%'
            ))
            result = cursor.fetchone()

            if result is None:
                logger.debug(f"No game found for {away_team_name} @ {home_team_name} on {game_date}")
                return None

            game_id = result[0]

            # Now get the game state
            return get_game_state(game_id, db_conn=conn, game_date=game_date)

    except Exception as e:
        logger.error(f"Error finding game state for {away_team_name} @ {home_team_name} on {game_date}: {e}")
        return None

    finally:
        if close_conn and conn:
            conn.close()


def calculate_remaining_time(game_state: Dict[str, Any]) -> float:
    """
    Calculate remaining time in the game (in minutes).

    Args:
        game_state: Dictionary with game state information

    Returns:
        Remaining time in minutes (float)
    """
    quarter = game_state.get('quarter', 1)
    game_clock_seconds = game_state.get('game_clock_seconds', 0) or 0

    # Calculate quarters remaining
    if quarter <= 4:
        quarters_remaining = 4 - quarter
    else:
        # Overtime
        quarters_remaining = 0

    # Calculate total remaining time
    # Each quarter is 12 minutes = 720 seconds
    remaining_quarters_minutes = quarters_remaining * 12.0
    current_quarter_minutes = game_clock_seconds / 60.0

    total_remaining = remaining_quarters_minutes + current_quarter_minutes

    return total_remaining


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Fetch game state for a game")
    parser.add_argument("--game-id", type=str, help="Game ID")
    parser.add_argument("--home-team", type=str, help="Home team name")
    parser.add_argument("--away-team", type=str, help="Away team name")
    parser.add_argument("--game-date", type=str, help="Game date (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.game_id:
        game_state = get_game_state(args.game_id)
    elif args.home_team and args.away_team and args.game_date:
        from datetime import datetime
        game_date = datetime.strptime(args.game_date, "%Y-%m-%d").date()
        game_state = get_game_state_by_team_names(
            args.home_team, args.away_team, game_date
        )
    else:
        print("Please provide either --game-id or --home-team --away-team --game-date")
        sys.exit(1)

    if game_state:
        print(f"\nGame State:")
        print(f"  Score: {game_state['current_score_home']} - {game_state['current_score_away']}")
        print(f"  Quarter: {game_state['quarter']}")
        print(f"  Time remaining: {game_state['game_clock_seconds']} seconds")
        print(f"  Status: {game_state['game_status']}")
        print(f"  Score differential: {game_state['score_differential']:+d}")

        remaining = calculate_remaining_time(game_state)
        print(f"  Remaining time: {remaining:.1f} minutes")
    else:
        print("No game state found (game may not be in progress)")

