#!/usr/bin/env python3
"""
Phase 0.0010: Temporal Integration for JSONB Storage

Purpose: Enable temporal queries that join JSONB raw data with temporal snapshots
Created: October 25, 2025
Implementation ID: rec_033_postgresql_temporal

Key Capabilities:
- Query player stats at exact timestamps
- Reconstruct game states at specific moments
- Join JSONB data with temporal tables
- Support millisecond-precision historical queries

Usage:
    from scripts.0_0010.temporal_queries import TemporalJSONBQueries

    queries = TemporalJSONBQueries()
    stats = queries.get_player_stats_at_timestamp(
        player_name="LeBron James",
        timestamp="2016-06-19 19:02:34.56-05:00"
    )
"""

import os
import psycopg2
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json


class TemporalJSONBQueries:
    """
    Query helper for temporal integration with JSONB storage

    Enables millisecond-precision historical queries by joining:
    - raw_data.nba_games (JSONB raw data)
    - raw_data.nba_players (JSONB player data)
    - player_snapshots (temporal cumulative stats)
    - game_states (temporal game situations)
    - temporal_events (play-by-play with timestamps)
    """

    def __init__(self, conn=None):
        """
        Initialize temporal query helper

        Args:
            conn: Optional existing psycopg2 connection
        """
        if conn:
            self.conn = conn
            self.own_connection = False
        else:
            self.conn = self._create_connection()
            self.own_connection = True

        self.cursor = self.conn.cursor()

    def _create_connection(self):
        """Create database connection from environment variables"""
        config = {
            "host": os.getenv("RDS_HOST", os.getenv("POSTGRES_HOST", "localhost")),
            "port": int(os.getenv("RDS_PORT", os.getenv("POSTGRES_PORT", "5432"))),
            "database": os.getenv("RDS_DATABASE", os.getenv("POSTGRES_DB", "nba_data")),
            "user": os.getenv("RDS_USER", os.getenv("POSTGRES_USER", "postgres")),
            "password": os.getenv("RDS_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
        }

        return psycopg2.connect(**config)

    def close(self):
        """Close database connection if we own it"""
        if self.own_connection and self.conn:
            self.cursor.close()
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    # ========================================================================
    # Core Temporal Queries
    # ========================================================================

    def get_player_stats_at_timestamp(
        self, player_name: str = None, player_id: str = None, timestamp: str = None
    ) -> Optional[Dict]:
        """
        Get player's cumulative career statistics at exact timestamp

        This is THE core query that powers the project vision:
        "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT
        on June 19, 2016?"

        Args:
            player_name: Player's full name (e.g., "LeBron James")
            player_id: Player's ID (alternative to name)
            timestamp: ISO 8601 timestamp with timezone
                      (e.g., "2016-06-19 19:02:34.56-05:00")

        Returns:
            Dictionary with:
            - player_info: Name, ID, birth date
            - timestamp: Query timestamp
            - age_at_timestamp: Exact age in years (to millisecond)
            - career_stats: Cumulative points, assists, rebounds, etc.
            - recent_performance: Last 10 games before timestamp
            - raw_data_sources: Which JSONB sources have data for this player
        """
        if not (player_name or player_id):
            raise ValueError("Must provide either player_name or player_id")

        if not timestamp:
            raise ValueError("Must provide timestamp")

        # Query joins JSONB player data + temporal snapshots + biographical
        query = """
            WITH player_info AS (
                -- Get player biographical info (birth date for age calculation)
                SELECT DISTINCT
                    pb.player_id,
                    pb.player_name,
                    pb.birth_date
                FROM player_biographical pb
                WHERE 1=1
                    {player_filter}
                LIMIT 1
            ),
            temporal_snapshot AS (
                -- Get most recent snapshot before/at timestamp
                SELECT
                    ps.player_id,
                    ps.snapshot_timestamp,
                    ps.cumulative_points,
                    ps.cumulative_assists,
                    ps.cumulative_rebounds,
                    ps.cumulative_steals,
                    ps.cumulative_blocks,
                    ps.cumulative_turnovers,
                    ps.cumulative_field_goals_made,
                    ps.cumulative_field_goals_attempted,
                    ps.cumulative_three_point_made,
                    ps.cumulative_three_point_attempted,
                    ps.cumulative_free_throws_made,
                    ps.cumulative_free_throws_attempted,
                    ps.career_games_played,
                    ps.career_minutes_played
                FROM player_snapshots ps
                WHERE ps.player_id = (SELECT player_id FROM player_info)
                  AND ps.snapshot_timestamp <= %s::timestamptz
                ORDER BY ps.snapshot_timestamp DESC
                LIMIT 1
            ),
            jsonb_sources AS (
                -- Get list of JSONB sources with data for this player
                SELECT
                    source,
                    COUNT(*) as records_count,
                    MIN(season) as first_season,
                    MAX(season) as last_season
                FROM raw_data.nba_players
                WHERE player_id = (SELECT player_id FROM player_info)
                GROUP BY source
            ),
            recent_games AS (
                -- Get last 10 games before timestamp for recent performance
                SELECT
                    te.event_timestamp,
                    te.game_id,
                    te.event_type,
                    te.points_scored,
                    te.event_details
                FROM temporal_events te
                WHERE te.player_id = (SELECT player_id FROM player_info)
                  AND te.event_timestamp <= %s::timestamptz
                ORDER BY te.event_timestamp DESC
                LIMIT 100  -- ~10 games worth of events
            )
            SELECT
                -- Player info
                pi.player_id,
                pi.player_name,
                pi.birth_date,

                -- Age calculation (to millisecond precision)
                EXTRACT(EPOCH FROM (%s::timestamptz - pi.birth_date)) / 31557600.0 AS age_years,

                -- Temporal snapshot data
                ts.snapshot_timestamp,
                ts.cumulative_points,
                ts.cumulative_assists,
                ts.cumulative_rebounds,
                ts.cumulative_steals,
                ts.cumulative_blocks,
                ts.cumulative_turnovers,
                ts.cumulative_field_goals_made,
                ts.cumulative_field_goals_attempted,
                ts.cumulative_three_point_made,
                ts.cumulative_three_point_attempted,
                ts.cumulative_free_throws_made,
                ts.cumulative_free_throws_attempted,
                ts.career_games_played,
                ts.career_minutes_played,

                -- Shooting percentages (calculated)
                CASE
                    WHEN ts.cumulative_field_goals_attempted > 0
                    THEN ts.cumulative_field_goals_made::float / ts.cumulative_field_goals_attempted
                    ELSE 0
                END as fg_percentage,

                CASE
                    WHEN ts.cumulative_three_point_attempted > 0
                    THEN ts.cumulative_three_point_made::float / ts.cumulative_three_point_attempted
                    ELSE 0
                END as three_point_percentage,

                CASE
                    WHEN ts.cumulative_free_throws_attempted > 0
                    THEN ts.cumulative_free_throws_made::float / ts.cumulative_free_throws_attempted
                    ELSE 0
                END as ft_percentage,

                -- JSONB source availability
                (SELECT json_agg(row_to_json(js.*)) FROM jsonb_sources js) as jsonb_sources,

                -- Recent performance
                (SELECT json_agg(row_to_json(rg.*)) FROM recent_games rg) as recent_events

            FROM player_info pi
            LEFT JOIN temporal_snapshot ts ON pi.player_id = ts.player_id;
        """

        # Build player filter clause
        if player_name:
            player_filter = f"AND pb.player_name ILIKE '%{player_name}%'"
        else:
            player_filter = f"AND pb.player_id = '{player_id}'"

        query = query.format(player_filter=player_filter)

        # Execute with timestamp parameter (used 3 times in query)
        self.cursor.execute(query, (timestamp, timestamp, timestamp))

        result = self.cursor.fetchone()

        if not result:
            return None

        # Parse result into structured dictionary
        columns = [desc[0] for desc in self.cursor.description]
        result_dict = dict(zip(columns, result))

        return {
            "player_info": {
                "player_id": result_dict["player_id"],
                "player_name": result_dict["player_name"],
                "birth_date": (
                    result_dict["birth_date"].isoformat()
                    if result_dict["birth_date"]
                    else None
                ),
            },
            "query_timestamp": timestamp,
            "age_at_timestamp": (
                round(result_dict["age_years"], 6) if result_dict["age_years"] else None
            ),
            "snapshot_timestamp": (
                result_dict["snapshot_timestamp"].isoformat()
                if result_dict["snapshot_timestamp"]
                else None
            ),
            "career_stats": {
                "games_played": result_dict["career_games_played"],
                "minutes_played": result_dict["career_minutes_played"],
                "points": result_dict["cumulative_points"],
                "assists": result_dict["cumulative_assists"],
                "rebounds": result_dict["cumulative_rebounds"],
                "steals": result_dict["cumulative_steals"],
                "blocks": result_dict["cumulative_blocks"],
                "turnovers": result_dict["cumulative_turnovers"],
                "field_goals_made": result_dict["cumulative_field_goals_made"],
                "field_goals_attempted": result_dict[
                    "cumulative_field_goals_attempted"
                ],
                "three_point_made": result_dict["cumulative_three_point_made"],
                "three_point_attempted": result_dict[
                    "cumulative_three_point_attempted"
                ],
                "free_throws_made": result_dict["cumulative_free_throws_made"],
                "free_throws_attempted": result_dict[
                    "cumulative_free_throws_attempted"
                ],
                "fg_percentage": (
                    round(result_dict["fg_percentage"], 4)
                    if result_dict["fg_percentage"]
                    else 0.0
                ),
                "three_point_percentage": (
                    round(result_dict["three_point_percentage"], 4)
                    if result_dict["three_point_percentage"]
                    else 0.0
                ),
                "ft_percentage": (
                    round(result_dict["ft_percentage"], 4)
                    if result_dict["ft_percentage"]
                    else 0.0
                ),
            },
            "jsonb_sources": result_dict["jsonb_sources"] or [],
            "recent_events": result_dict["recent_events"] or [],
        }

    def get_game_state_at_timestamp(
        self, game_id: str, timestamp: str
    ) -> Optional[Dict]:
        """
        Reconstruct complete game state at exact moment in time

        Enables context-adaptive simulations by providing:
        - Current score
        - Possession
        - Active lineups (both teams)
        - Quarter/time remaining
        - Timeout situation
        - Player fatigue levels

        Args:
            game_id: Game identifier
            timestamp: ISO 8601 timestamp with timezone

        Returns:
            Dictionary with complete game state
        """
        query = """
            WITH game_state AS (
                -- Get most recent game state before/at timestamp
                SELECT
                    gs.game_id,
                    gs.state_timestamp,
                    gs.quarter,
                    gs.time_remaining_seconds,
                    gs.home_score,
                    gs.away_score,
                    gs.possession_team_id,
                    gs.home_timeouts_remaining,
                    gs.away_timeouts_remaining,
                    gs.home_lineup,
                    gs.away_lineup,
                    gs.state_details
                FROM game_states gs
                WHERE gs.game_id = %s
                  AND gs.state_timestamp <= %s::timestamptz
                ORDER BY gs.state_timestamp DESC
                LIMIT 1
            ),
            game_jsonb AS (
                -- Get JSONB raw data for this game
                SELECT
                    game_id,
                    source,
                    game_date,
                    data
                FROM raw_data.nba_games
                WHERE game_id = %s
                LIMIT 1
            )
            SELECT
                gs.*,
                gj.source,
                gj.game_date as jsonb_game_date,
                gj.data->>'home_team' as home_team,
                gj.data->>'away_team' as away_team,
                gj.data
            FROM game_state gs
            LEFT JOIN game_jsonb gj ON gs.game_id = gj.game_id;
        """

        self.cursor.execute(query, (game_id, timestamp, game_id))
        result = self.cursor.fetchone()

        if not result:
            return None

        columns = [desc[0] for desc in self.cursor.description]
        result_dict = dict(zip(columns, result))

        return {
            "game_id": result_dict["game_id"],
            "game_date": result_dict.get(
                "jsonb_game_date", result_dict.get("game_date", None)
            ),
            "home_team": result_dict.get("home_team"),
            "away_team": result_dict.get("away_team"),
            "query_timestamp": timestamp,
            "state_timestamp": (
                result_dict["state_timestamp"].isoformat()
                if result_dict.get("state_timestamp")
                else None
            ),
            "score": {
                "home": result_dict.get("home_score"),
                "away": result_dict.get("away_score"),
                "differential": (
                    (
                        result_dict.get("home_score", 0)
                        - result_dict.get("away_score", 0)
                    )
                    if result_dict.get("home_score") and result_dict.get("away_score")
                    else None
                ),
            },
            "game_situation": {
                "quarter": result_dict.get("quarter"),
                "time_remaining_seconds": result_dict.get("time_remaining_seconds"),
                "possession_team_id": result_dict.get("possession_team_id"),
            },
            "timeouts": {
                "home_remaining": result_dict.get("home_timeouts_remaining"),
                "away_remaining": result_dict.get("away_timeouts_remaining"),
            },
            "lineups": {
                "home": result_dict.get("home_lineup"),
                "away": result_dict.get("away_lineup"),
            },
            "state_details": result_dict.get("state_details"),
            "raw_data_source": result_dict.get("source"),
            "raw_data": result_dict.get("data"),
        }

    def query_historical_context(
        self, player_id: str, timestamp: str, lookback_days: int = 7
    ) -> Dict:
        """
        Get historical context for simulation at specific timestamp

        Provides all context needed for adaptive simulation:
        - Recent performance (last N games)
        - Fatigue accumulation
        - Matchup history
        - Shooting trends

        Args:
            player_id: Player identifier
            timestamp: Target timestamp
            lookback_days: How many days back to analyze

        Returns:
            Dictionary with historical context
        """
        lookback_timestamp = f"(%s::timestamptz - INTERVAL '{lookback_days} days')"

        query = f"""
            WITH recent_games AS (
                -- Get all games in lookback period
                SELECT DISTINCT
                    te.game_id,
                    MIN(te.event_timestamp) as game_start,
                    MAX(te.event_timestamp) as game_end
                FROM temporal_events te
                WHERE te.player_id = %s
                  AND te.event_timestamp BETWEEN {lookback_timestamp} AND %s::timestamptz
                GROUP BY te.game_id
                ORDER BY game_start DESC
            ),
            performance_stats AS (
                -- Aggregate performance in lookback period
                SELECT
                    COUNT(DISTINCT rg.game_id) as games_played,
                    SUM(CASE WHEN te.event_type = 'shot' AND te.points_scored > 0 THEN 1 ELSE 0 END) as shots_made,
                    SUM(CASE WHEN te.event_type = 'shot' THEN 1 ELSE 0 END) as shots_attempted,
                    SUM(te.points_scored) as total_points,
                    AVG(te.points_scored) as avg_points_per_event
                FROM temporal_events te
                INNER JOIN recent_games rg ON te.game_id = rg.game_id
                WHERE te.player_id = %s
            ),
            fatigue_calc AS (
                -- Calculate fatigue based on minutes played
                SELECT
                    SUM(
                        EXTRACT(EPOCH FROM (rg.game_end - rg.game_start)) / 3600.0
                    ) as total_hours_played,
                    COUNT(*) as games_in_period
                FROM recent_games rg
            )
            SELECT
                ps.*,
                fc.total_hours_played,
                fc.games_in_period,
                (
                    SELECT json_agg(
                        json_build_object(
                            'game_id', game_id,
                            'game_start', game_start,
                            'game_end', game_end
                        )
                    )
                    FROM recent_games
                ) as game_list
            FROM performance_stats ps
            CROSS JOIN fatigue_calc fc;
        """

        self.cursor.execute(query, (player_id, timestamp, timestamp, player_id))
        result = self.cursor.fetchone()

        if not result:
            return {
                "player_id": player_id,
                "timestamp": timestamp,
                "lookback_days": lookback_days,
                "games_played": 0,
                "performance": {},
                "fatigue": {},
                "games": [],
            }

        columns = [desc[0] for desc in self.cursor.description]
        result_dict = dict(zip(columns, result))

        return {
            "player_id": player_id,
            "timestamp": timestamp,
            "lookback_days": lookback_days,
            "games_played": result_dict["games_played"] or 0,
            "performance": {
                "total_points": result_dict["total_points"] or 0,
                "shots_made": result_dict["shots_made"] or 0,
                "shots_attempted": result_dict["shots_attempted"] or 0,
                "shooting_percentage": (
                    round(result_dict["shots_made"] / result_dict["shots_attempted"], 4)
                    if result_dict["shots_attempted"]
                    and result_dict["shots_attempted"] > 0
                    else 0.0
                ),
                "avg_points_per_event": (
                    round(result_dict["avg_points_per_event"], 4)
                    if result_dict["avg_points_per_event"]
                    else 0.0
                ),
            },
            "fatigue": {
                "total_hours_played": (
                    round(result_dict["total_hours_played"], 2)
                    if result_dict["total_hours_played"]
                    else 0.0
                ),
                "games_in_period": result_dict["games_in_period"] or 0,
                "avg_hours_per_game": (
                    round(
                        result_dict["total_hours_played"]
                        / result_dict["games_in_period"],
                        2,
                    )
                    if result_dict["games_in_period"]
                    and result_dict["games_in_period"] > 0
                    else 0.0
                ),
            },
            "games": result_dict["game_list"] or [],
        }

    # ========================================================================
    # Advanced Temporal Queries
    # ========================================================================

    def get_career_trajectory(
        self,
        player_id: str,
        start_timestamp: str,
        end_timestamp: str,
        interval_days: int = 30,
    ) -> List[Dict]:
        """
        Get player's career trajectory between two timestamps

        Returns snapshots at regular intervals to show career progression.
        Useful for visualizing career arcs and aging effects.

        Args:
            player_id: Player identifier
            start_timestamp: Start of period
            end_timestamp: End of period
            interval_days: Days between snapshots

        Returns:
            List of snapshots showing career progression
        """
        query = """
            SELECT
                snapshot_timestamp,
                cumulative_points,
                cumulative_assists,
                cumulative_rebounds,
                career_games_played,
                cumulative_field_goals_made::float / NULLIF(cumulative_field_goals_attempted, 0) as fg_pct
            FROM player_snapshots
            WHERE player_id = %s
              AND snapshot_timestamp BETWEEN %s::timestamptz AND %s::timestamptz
            ORDER BY snapshot_timestamp;
        """

        self.cursor.execute(query, (player_id, start_timestamp, end_timestamp))

        results = []
        for row in self.cursor.fetchall():
            results.append(
                {
                    "timestamp": row[0].isoformat(),
                    "cumulative_points": row[1],
                    "cumulative_assists": row[2],
                    "cumulative_rebounds": row[3],
                    "games_played": row[4],
                    "fg_percentage": round(row[5], 4) if row[5] else 0.0,
                }
            )

        return results


def main():
    """Example usage demonstrating temporal integration"""
    print("Phase 0.0010: Temporal Integration - Example Usage\n")
    print("=" * 70)

    with TemporalJSONBQueries() as queries:
        # Example 1: Player stats at exact timestamp
        print("\n1. Get Player Stats at Exact Timestamp")
        print("-" * 70)

        # This demonstrates the CORE VISION of the project
        stats = queries.get_player_stats_at_timestamp(
            player_name="LeBron James",
            timestamp="2020-10-11 21:00:00-05:00",  # 2020 Finals end
        )

        if stats:
            print(f"Player: {stats['player_info']['player_name']}")
            print(f"Age at timestamp: {stats['age_at_timestamp']:.2f} years")
            print(f"Career points: {stats['career_stats']['points']:,}")
            print(f"Career games: {stats['career_stats']['games_played']:,}")
            print(f"FG%: {stats['career_stats']['fg_percentage']:.1%}")
        else:
            print(
                "  (No data available for example - requires populated temporal tables)"
            )

        # Example 2: Game state reconstruction
        print("\n2. Reconstruct Game State at Timestamp")
        print("-" * 70)

        state = queries.get_game_state_at_timestamp(
            game_id="401359859", timestamp="2022-01-15 20:45:00-06:00"
        )

        if state:
            print(f"Game: {state['home_team']} vs {state['away_team']}")
            print(f"Score: {state['score']['home']} - {state['score']['away']}")
            print(f"Quarter: {state['game_situation']['quarter']}")
        else:
            print(
                "  (No data available for example - requires populated temporal tables)"
            )

        # Example 3: Historical context
        print("\n3. Query Historical Context (Last 7 Days)")
        print("-" * 70)

        context = queries.query_historical_context(
            player_id="2544",  # LeBron
            timestamp="2020-10-11 21:00:00-05:00",
            lookback_days=7,
        )

        print(f"Games played (last 7 days): {context['games_played']}")
        print(f"Total points: {context['performance']['total_points']}")
        print(f"Shooting %: {context['performance']['shooting_percentage']:.1%}")
        print(f"Total hours played: {context['fatigue']['total_hours_played']:.1f}h")

    print("\n" + "=" * 70)
    print("Temporal integration examples complete!")
    print("\nThese queries enable the core project vision:")
    print(
        '  "What were Kobe Bryant\'s stats at exactly 7:02:34.56 PM on June 19, 2016?"'
    )


if __name__ == "__main__":
    main()
