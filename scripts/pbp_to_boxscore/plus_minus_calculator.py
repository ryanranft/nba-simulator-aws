#!/usr/bin/env python3
"""
Plus/Minus Calculator

Calculates plus/minus metrics at various granularities:
- Lineup-based (5-player combinations)
- Individual player (on/off court)
- Possession-based intervals
- Stint-based analysis

Created: October 19, 2025
"""

import hashlib
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PossessionInterval:
    """Represents a possession-based interval"""
    start_possession: int
    end_possession: int
    interval_number: int
    interval_size: int  # Number of possessions per interval (e.g., 10, 25, 50)


class PlusMinusCalculator:
    """
    Calculator for plus/minus metrics including lineup analysis,
    on/off differentials, and possession-based intervals.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize calculator with database connection.

        Args:
            conn: SQLite database connection with required tables:
                  - lineup_snapshots
                  - player_plus_minus_snapshots
                  - possession_metadata
        """
        self.conn = conn
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

    # ========================================================================
    # Lineup Methods
    # ========================================================================

    def calculate_lineup_hash(self, player_ids: List[str]) -> str:
        """
        Calculate MD5 hash for a lineup (must be exactly 5 players).

        Players are automatically sorted alphabetically to ensure consistent
        hashing regardless of input order.

        Args:
            player_ids: List of 5 player IDs

        Returns:
            MD5 hash string

        Raises:
            ValueError: If not exactly 5 players provided
        """
        if len(player_ids) != 5:
            raise ValueError(f"Lineup must have exactly 5 players, got {len(player_ids)}")

        # Sort alphabetically to ensure consistent hash
        sorted_players = sorted(player_ids)

        # Create hash string
        lineup_string = '|'.join(sorted_players)

        # Calculate MD5
        return hashlib.md5(lineup_string.encode()).hexdigest()

    def get_active_lineup(self, game_id: str, event_number: int,
                          team_id: str) -> Optional[List[str]]:
        """
        Get the 5 players on court for a team at a specific event.

        Args:
            game_id: Game identifier
            event_number: Event number in game
            team_id: Team identifier

        Returns:
            List of 5 player IDs (alphabetically sorted), or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT player1_id, player2_id, player3_id, player4_id, player5_id
            FROM lineup_snapshots
            WHERE game_id = ? AND event_number = ? AND team_id = ?
        """, (game_id, event_number, team_id))

        result = cursor.fetchone()
        if result:
            return [result[0], result[1], result[2], result[3], result[4]]
        return None

    def get_lineup_stats(self, game_id: str, lineup_hash: str) -> Optional[Dict]:
        """
        Get aggregate stats for a specific lineup in a game.

        Args:
            game_id: Game identifier
            lineup_hash: MD5 hash of lineup

        Returns:
            Dictionary with lineup stats, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM vw_lineup_plus_minus
            WHERE lineup_hash = ?
              AND (first_game <= ? AND last_game >= ?)
        """, (lineup_hash, game_id, game_id))

        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def get_top_lineups(self, game_id: str, team_id: str,
                        min_possessions: int = 10,
                        order_by: str = 'net_rating',
                        limit: int = 5) -> List[Dict]:
        """
        Get best-performing lineups for a team in a game.

        Args:
            game_id: Game identifier
            team_id: Team identifier
            min_possessions: Minimum possessions for inclusion
            order_by: Metric to sort by ('net_rating', 'offensive_rating',
                     'defensive_rating', 'plus_minus_per_possession')
            limit: Maximum number of lineups to return

        Returns:
            List of lineup dictionaries ordered by specified metric
        """
        cursor = self.conn.cursor()

        # Validate order_by to prevent SQL injection
        valid_metrics = ['net_rating', 'offensive_rating', 'defensive_rating',
                        'plus_minus_per_possession', 'total_plus_minus']
        if order_by not in valid_metrics:
            raise ValueError(f"Invalid order_by metric: {order_by}")

        query = f"""
            SELECT *
            FROM vw_lineup_plus_minus
            WHERE team_id = ?
              AND (first_game <= ? AND last_game >= ?)
              AND possessions_played >= ?
            ORDER BY {order_by} DESC
            LIMIT ?
        """

        cursor.execute(query, (team_id, game_id, game_id, min_possessions, limit))
        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # Individual Player Plus/Minus Methods
    # ========================================================================

    def calculate_player_plus_minus(self, game_id: str, player_id: str,
                                     possession_range: Optional[Tuple[int, int]] = None
                                     ) -> Dict:
        """
        Calculate player's plus/minus for a game or possession range.

        Args:
            game_id: Game identifier
            player_id: Player identifier
            possession_range: Optional (start_poss, end_poss) tuple

        Returns:
            Dictionary with on-court plus/minus, possessions, etc.
        """
        cursor = self.conn.cursor()

        where_clause = "WHERE game_id = ? AND player_id = ? AND on_court = 1"
        params = [game_id, player_id]

        if possession_range:
            where_clause += " AND possession_number BETWEEN ? AND ?"
            params.extend(possession_range)

        query = f"""
            SELECT
                COUNT(DISTINCT possession_number) as possessions,
                MAX(plus_minus) - MIN(plus_minus) as plus_minus,
                SUM(1) / 60.0 as minutes_played
            FROM player_plus_minus_snapshots
            {where_clause}
        """

        cursor.execute(query, params)
        result = cursor.fetchone()

        if result and result['possessions'] > 0:
            return {
                'possessions': result['possessions'],
                'plus_minus': result['plus_minus'],
                'minutes_played': round(result['minutes_played'], 2),
                'plus_minus_per_possession': round(
                    result['plus_minus'] / result['possessions'], 3
                ),
                'plus_minus_per_minute': round(
                    result['plus_minus'] / result['minutes_played'], 2
                ) if result['minutes_played'] > 0 else 0
            }

        return {
            'possessions': 0,
            'plus_minus': 0,
            'minutes_played': 0,
            'plus_minus_per_possession': 0,
            'plus_minus_per_minute': 0
        }

    def calculate_on_off_differential(self, game_id: str,
                                       player_id: str) -> Dict:
        """
        Calculate on-court vs off-court differential for a player.

        Args:
            game_id: Game identifier
            player_id: Player identifier

        Returns:
            Dictionary with on-court, off-court, and differential metrics
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM vw_on_off_analysis
            WHERE game_id = ? AND player_id = ?
        """, (game_id, player_id))

        result = cursor.fetchone()
        if result:
            return dict(result)

        return {
            'plus_minus_on_court': 0,
            'plus_minus_off_court': 0,
            'plus_minus_differential': 0,
            'net_rating_diff': 0,
            'replacement_value_48min': 0,
            'confidence_level': 'NONE'
        }

    def get_player_stints(self, game_id: str, player_id: str) -> List[Dict]:
        """
        Get all playing stints for a player in a game.

        Args:
            game_id: Game identifier
            player_id: Player identifier

        Returns:
            List of stint dictionaries with start/end events, duration, +/-
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                stint_id,
                stint_number,
                stint_start_event,
                MIN(time_elapsed_seconds) as start_seconds,
                MAX(time_elapsed_seconds) as end_seconds,
                MAX(time_elapsed_seconds) - MIN(time_elapsed_seconds) as duration_seconds,
                COUNT(DISTINCT possession_number) as possessions,
                MAX(plus_minus) - MIN(plus_minus) as stint_plus_minus
            FROM player_plus_minus_snapshots
            WHERE game_id = ? AND player_id = ? AND stint_id IS NOT NULL
            GROUP BY stint_id
            ORDER BY stint_number
        """, (game_id, player_id))

        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # Possession-Based Interval Methods
    # ========================================================================

    def get_possession_intervals(self, game_id: str,
                                  interval_size: int = 10) -> List[PossessionInterval]:
        """
        Generate possession-based intervals for a game.

        Args:
            game_id: Game identifier
            interval_size: Number of possessions per interval (10, 25, 50, 100)

        Returns:
            List of PossessionInterval objects
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MIN(possession_number) as min_poss,
                   MAX(possession_number) as max_poss
            FROM possession_metadata
            WHERE game_id = ?
        """, (game_id,))

        result = cursor.fetchone()
        if not result or result['min_poss'] is None:
            return []

        min_poss = result['min_poss']
        max_poss = result['max_poss']

        intervals = []
        interval_num = 1
        start_poss = min_poss

        while start_poss <= max_poss:
            end_poss = min(start_poss + interval_size - 1, max_poss)
            intervals.append(PossessionInterval(
                start_possession=start_poss,
                end_possession=end_poss,
                interval_number=interval_num,
                interval_size=interval_size
            ))
            start_poss = end_poss + 1
            interval_num += 1

        return intervals

    def calculate_possession_interval_stats(self, game_id: str, team_id: str,
                                            interval: PossessionInterval) -> Dict:
        """
        Calculate team stats for a possession-based interval.

        Args:
            game_id: Game identifier
            team_id: Team identifier
            interval: PossessionInterval object

        Returns:
            Dictionary with offensive/defensive ratings, pace, etc.
        """
        cursor = self.conn.cursor()

        # Offensive stats (team has the ball)
        cursor.execute("""
            SELECT
                COUNT(*) as possessions,
                SUM(points_scored) as points,
                SUM(CASE WHEN possession_result = 'made_shot' THEN 1 ELSE 0 END) as made_shots,
                SUM(CASE WHEN possession_result = 'turnover' THEN 1 ELSE 0 END) as turnovers
            FROM possession_metadata
            WHERE game_id = ?
              AND offensive_team_id = ?
              AND possession_number BETWEEN ? AND ?
        """, (game_id, team_id, interval.start_possession, interval.end_possession))

        off_result = cursor.fetchone()

        # Defensive stats (opponent has the ball)
        cursor.execute("""
            SELECT
                COUNT(*) as possessions,
                SUM(points_scored) as points_allowed
            FROM possession_metadata
            WHERE game_id = ?
              AND defensive_team_id = ?
              AND possession_number BETWEEN ? AND ?
        """, (game_id, team_id, interval.start_possession, interval.end_possession))

        def_result = cursor.fetchone()

        offensive_rating = (off_result['points'] * 100.0 / off_result['possessions']
                           if off_result['possessions'] > 0 else 0)
        defensive_rating = (def_result['points_allowed'] * 100.0 / def_result['possessions']
                           if def_result['possessions'] > 0 else 0)

        return {
            'interval_number': interval.interval_number,
            'start_possession': interval.start_possession,
            'end_possession': interval.end_possession,
            'interval_size': interval.interval_size,

            # Offensive
            'offensive_possessions': off_result['possessions'],
            'points_scored': off_result['points'],
            'offensive_rating': round(offensive_rating, 1),
            'made_shots': off_result['made_shots'],
            'turnovers': off_result['turnovers'],

            # Defensive
            'defensive_possessions': def_result['possessions'],
            'points_allowed': def_result['points_allowed'],
            'defensive_rating': round(defensive_rating, 1),

            # Net
            'net_rating': round(offensive_rating - defensive_rating, 1),
            'point_differential': off_result['points'] - def_result['points_allowed']
        }

    # ========================================================================
    # Integration Methods
    # ========================================================================

    def add_plus_minus_to_interval(self, interval_stats: Dict, game_id: str,
                                   player_id: str,
                                   possession_range: Optional[Tuple[int, int]] = None
                                   ) -> Dict:
        """
        Enrich interval box score stats with plus/minus data.

        Args:
            interval_stats: Dictionary from interval_box_score_calculator
            game_id: Game identifier
            player_id: Player identifier
            possession_range: Optional (start_poss, end_poss) for possession-based

        Returns:
            interval_stats enriched with plus/minus metrics
        """
        # Add individual plus/minus
        pm_stats = self.calculate_player_plus_minus(game_id, player_id, possession_range)
        interval_stats.update({
            'player_plus_minus': pm_stats['plus_minus'],
            'player_pm_per_poss': pm_stats['plus_minus_per_possession'],
            'player_pm_per_minute': pm_stats['plus_minus_per_minute']
        })

        # Add on/off differential
        on_off = self.calculate_on_off_differential(game_id, player_id)
        interval_stats.update({
            'on_off_differential': on_off.get('plus_minus_differential', 0),
            'net_rating_diff': on_off.get('net_rating_diff', 0),
            'replacement_value': on_off.get('replacement_value_48min', 0)
        })

        return interval_stats


# ============================================================================
# Utility Functions
# ============================================================================

def create_sample_plus_minus_data(conn: sqlite3.Connection):
    """
    Create sample plus/minus tables for demo/testing.

    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()

    # Read and execute table creation SQL
    import os
    sql_dir = os.path.join(os.path.dirname(__file__), '../../sql/plus_minus')

    for sql_file in ['01_create_lineup_snapshots.sql',
                     '02_create_player_plus_minus_snapshots.sql',
                     '03_create_possession_metadata.sql']:
        file_path = os.path.join(sql_dir, sql_file)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                sql = f.read()
                # Execute each statement separately
                for statement in sql.split(';'):
                    if statement.strip() and not statement.strip().startswith('--'):
                        cursor.execute(statement)

    conn.commit()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Calculate lineup hash
    calc = PlusMinusCalculator(sqlite3.connect(':memory:'))

    players = ['tatumja01', 'brownja02', 'whitede01', 'horfoal01', 'holidjr01']
    lineup_hash = calc.calculate_lineup_hash(players)
    print(f"Lineup hash: {lineup_hash}")

    # Example: Get possession intervals
    intervals_10 = calc.get_possession_intervals('0021500001', interval_size=10)
    print(f"10-possession intervals: {len(intervals_10)}")

    intervals_25 = calc.get_possession_intervals('0021500001', interval_size=25)
    print(f"25-possession intervals: {len(intervals_25)}")
