#!/usr/bin/env python3
"""
Phase 0.10: PostgreSQL JSONB Query Helpers

Purpose: Helper classes and functions for querying JSONB data
Created: October 25, 2025
Implementation ID: rec_033_postgresql

Usage:
    from scripts.0_10.main import JSONBQueryHelper

    helper = JSONBQueryHelper()
    game = helper.get_game_data('401359859')
    players = helper.search_players('LeBron')
"""

import os
import psycopg2
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class JSONBQueryHelper:
    """Helper class for querying JSONB data in PostgreSQL"""

    def __init__(self, conn=None):
        """
        Initialize query helper

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
    # Game Queries
    # ========================================================================

    def get_game_data(
        self, game_id: str, fields: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Retrieve specific fields from game data

        Args:
            game_id: Game ID to retrieve
            fields: Optional list of JSON fields to extract

        Returns:
            Dictionary with game data, or None if not found
        """
        if fields:
            field_selects = [f"data->'{f}' as {f}" for f in fields]
            select_clause = ", ".join(field_selects)
        else:
            select_clause = "data"

        self.cursor.execute(
            f"""
            SELECT {select_clause}
            FROM raw_data.nba_games
            WHERE game_id = %s;
        """,
            (game_id,),
        )

        result = self.cursor.fetchone()
        if not result:
            return None

        if fields:
            return dict(zip(fields, result))
        else:
            return result[0]

    def get_games_by_date(
        self, start_date: str, end_date: Optional[str] = None
    ) -> List[Tuple]:
        """
        Get games within date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: Optional end date (defaults to start_date)

        Returns:
            List of (game_id, game_date, data) tuples
        """
        if not end_date:
            end_date = start_date

        self.cursor.execute(
            """
            SELECT game_id, game_date, data
            FROM raw_data.nba_games
            WHERE game_date BETWEEN %s AND %s
            ORDER BY game_date, game_id;
        """,
            (start_date, end_date),
        )

        return self.cursor.fetchall()

    def get_games_by_season(self, season: int) -> List[Tuple]:
        """Get all games for a season"""
        self.cursor.execute(
            """
            SELECT game_id, game_date, data
            FROM raw_data.nba_games
            WHERE season = %s
            ORDER BY game_date;
        """,
            (season,),
        )

        return self.cursor.fetchall()

    def get_games_by_teams(
        self, team1: str, team2: Optional[str] = None
    ) -> List[Tuple]:
        """
        Get games involving specific team(s)

        Args:
            team1: First team abbreviation
            team2: Optional second team (for head-to-head)
        """
        if team2:
            self.cursor.execute(
                """
                SELECT game_id, game_date, data
                FROM raw_data.nba_games
                WHERE (data->>'home_team' = %s AND data->>'away_team' = %s)
                   OR (data->>'home_team' = %s AND data->>'away_team' = %s)
                ORDER BY game_date DESC;
            """,
                (team1, team2, team2, team1),
            )
        else:
            self.cursor.execute(
                """
                SELECT game_id, game_date, data
                FROM raw_data.nba_games
                WHERE data->>'home_team' = %s
                   OR data->>'away_team' = %s
                ORDER BY game_date DESC;
            """,
                (team1, team1),
            )

        return self.cursor.fetchall()

    # ========================================================================
    # Player Queries
    # ========================================================================

    def search_players(self, name_pattern: str, limit: int = 100) -> List[Tuple]:
        """
        Search players by name pattern

        Args:
            name_pattern: Name or partial name to search
            limit: Maximum results to return

        Returns:
            List of (player_id, name, team, season) tuples
        """
        self.cursor.execute(
            """
            SELECT
                player_id,
                data->>'player_name' as name,
                data->>'team' as team,
                season
            FROM raw_data.nba_players
            WHERE data->>'player_name' ILIKE %s
            ORDER BY season DESC, player_name
            LIMIT %s;
        """,
            (f"%{name_pattern}%", limit),
        )

        return self.cursor.fetchall()

    def get_player_data(
        self, player_id: str, season: Optional[int] = None
    ) -> Optional[Dict]:
        """Get player data for specific player and season"""
        if season:
            self.cursor.execute(
                """
                SELECT data
                FROM raw_data.nba_players
                WHERE player_id = %s AND season = %s;
            """,
                (player_id, season),
            )
        else:
            self.cursor.execute(
                """
                SELECT data
                FROM raw_data.nba_players
                WHERE player_id = %s
                ORDER BY season DESC
                LIMIT 1;
            """,
                (player_id,),
            )

        result = self.cursor.fetchone()
        return result[0] if result else None

    # ========================================================================
    # Team Queries
    # ========================================================================

    def get_team_data(
        self, team_id: str, season: Optional[int] = None
    ) -> Optional[Dict]:
        """Get team data for specific team and season"""
        if season:
            self.cursor.execute(
                """
                SELECT data
                FROM raw_data.nba_teams
                WHERE team_id = %s AND season = %s;
            """,
                (team_id, season),
            )
        else:
            self.cursor.execute(
                """
                SELECT data
                FROM raw_data.nba_teams
                WHERE team_id = %s
                ORDER BY season DESC
                LIMIT 1;
            """,
                (team_id,),
            )

        result = self.cursor.fetchone()
        return result[0] if result else None

    # ========================================================================
    # Aggregation Queries
    # ========================================================================

    def aggregate_by_field(
        self, table: str, json_field: str, limit: int = 50
    ) -> List[Tuple]:
        """
        Aggregate counts by a JSON field

        Args:
            table: Table name ('nba_games', 'nba_players', 'nba_teams')
            json_field: JSON field to aggregate on
            limit: Maximum results

        Returns:
            List of (field_value, count) tuples
        """
        self.cursor.execute(
            f"""
            SELECT
                data->>%s as field_value,
                COUNT(*) as count
            FROM raw_data.{table}
            WHERE data->>%s IS NOT NULL
            GROUP BY data->>%s
            ORDER BY count DESC
            LIMIT %s;
        """,
            (json_field, json_field, json_field, limit),
        )

        return self.cursor.fetchall()

    def get_source_stats(self) -> List[Tuple]:
        """Get statistics by data source"""
        self.cursor.execute(
            """
            SELECT * FROM raw_data.data_source_stats
            ORDER BY table_name, source;
        """
        )

        return self.cursor.fetchall()

    def get_season_coverage(self) -> List[Tuple]:
        """Get season coverage statistics"""
        self.cursor.execute(
            """
            SELECT * FROM raw_data.season_coverage
            ORDER BY table_name, season DESC;
        """
        )

        return self.cursor.fetchall()

    # ========================================================================
    # Advanced JSONB Queries
    # ========================================================================

    def query_json_path(
        self,
        table: str,
        json_path: str,
        value: Any,
        operator: str = "=",
        limit: int = 100,
    ) -> List[Dict]:
        """
        Query JSONB data using JSON path

        Args:
            table: Table name
            json_path: JSON path (e.g., 'team->abbreviation')
            value: Value to match
            operator: SQL operator (=, !=, >, <, etc.)
            limit: Maximum results

        Returns:
            List of matching JSONB records
        """
        query = f"""
            SELECT data
            FROM raw_data.{table}
            WHERE data->>%s {operator} %s
            LIMIT %s;
        """
        self.cursor.execute(query, (json_path, value, limit))

        return [row[0] for row in self.cursor.fetchall()]

    def jsonb_contains(
        self, table: str, json_subset: Dict, limit: int = 100
    ) -> List[Dict]:
        """
        Find records where JSONB contains subset

        Args:
            table: Table name
            json_subset: JSON subset to match
            limit: Maximum results

        Returns:
            List of matching JSONB records
        """
        self.cursor.execute(
            f"""
            SELECT data
            FROM raw_data.{table}
            WHERE data @> %s::jsonb
            LIMIT %s;
        """,
            (psycopg2.extras.Json(json_subset), limit),
        )

        return [row[0] for row in self.cursor.fetchall()]

    # ========================================================================
    # Temporal Integration Methods
    # ========================================================================

    def get_player_performance_with_context(
        self, player_id: str, game_id: str, timestamp: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get player's game performance with temporal career context

        Joins JSONB raw game data with temporal snapshots to provide:
        - Game stats from JSONB
        - Career cumulative stats at game time
        - Age at game time
        - Recent performance trends

        Args:
            player_id: Player identifier
            game_id: Game identifier
            timestamp: Optional specific timestamp (defaults to game end)

        Returns:
            Dictionary with game stats + temporal context
        """
        query = """
            WITH game_data AS (
                -- Get JSONB game data
                SELECT
                    game_id,
                    game_date,
                    data
                FROM raw_data.nba_games
                WHERE game_id = %s
            ),
            player_snapshot AS (
                -- Get player snapshot at/before game time
                SELECT
                    ps.cumulative_points,
                    ps.cumulative_assists,
                    ps.cumulative_rebounds,
                    ps.career_games_played,
                    ps.snapshot_timestamp
                FROM player_snapshots ps
                WHERE ps.player_id = %s
                  AND ps.snapshot_timestamp <= COALESCE(%s::timestamptz, (SELECT game_date FROM game_data))
                ORDER BY ps.snapshot_timestamp DESC
                LIMIT 1
            ),
            player_bio AS (
                -- Get biographical info for age calculation
                SELECT
                    player_name,
                    birth_date
                FROM player_biographical
                WHERE player_id = %s
            )
            SELECT
                gd.game_id,
                gd.game_date,
                gd.data,
                ps.cumulative_points as career_points_before_game,
                ps.cumulative_assists as career_assists_before_game,
                ps.cumulative_rebounds as career_rebounds_before_game,
                ps.career_games_played as games_played_before,
                ps.snapshot_timestamp,
                pb.player_name,
                pb.birth_date,
                EXTRACT(EPOCH FROM (gd.game_date - pb.birth_date)) / 31557600.0 as age_at_game
            FROM game_data gd
            CROSS JOIN player_snapshot ps
            CROSS JOIN player_bio pb;
        """

        self.cursor.execute(query, (game_id, player_id, timestamp, player_id))
        result = self.cursor.fetchone()

        if not result:
            return None

        return {
            "game_id": result[0],
            "game_date": result[1].isoformat() if result[1] else None,
            "raw_game_data": result[2],
            "temporal_context": {
                "career_points_before_game": result[3],
                "career_assists_before_game": result[4],
                "career_rebounds_before_game": result[5],
                "games_played_before": result[6],
                "snapshot_timestamp": result[7].isoformat() if result[7] else None,
                "player_name": result[8],
                "birth_date": result[9].isoformat() if result[9] else None,
                "age_at_game": round(result[10], 4) if result[10] else None,
            },
        }

    def get_matchup_history_temporal(
        self, team1: str, team2: str, start_date: str, end_date: str
    ) -> List[Tuple]:
        """
        Get head-to-head matchup history with temporal precision

        Args:
            team1: First team abbreviation
            team2: Second team abbreviation
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of games with temporal context
        """
        self.cursor.execute(
            """
            SELECT
                g.game_id,
                g.game_date,
                g.data->>'home_team' as home_team,
                g.data->>'away_team' as away_team,
                g.data->'home_score' as home_score,
                g.data->'away_score' as away_score,
                COUNT(DISTINCT gs.id) as state_snapshots_available
            FROM raw_data.nba_games g
            LEFT JOIN game_states gs ON g.game_id = gs.game_id
            WHERE g.game_date BETWEEN %s AND %s
              AND (
                  (g.data->>'home_team' = %s AND g.data->>'away_team' = %s)
                  OR (g.data->>'home_team' = %s AND g.data->>'away_team' = %s)
              )
            GROUP BY g.game_id, g.game_date, g.data
            ORDER BY g.game_date DESC;
        """,
            (start_date, end_date, team1, team2, team2, team1),
        )

        return self.cursor.fetchall()

    def aggregate_with_temporal_filter(
        self,
        table: str,
        json_field: str,
        start_timestamp: str,
        end_timestamp: str,
        groupby_field: Optional[str] = None,
    ) -> List[Tuple]:
        """
        Aggregate JSONB data within temporal bounds

        Args:
            table: Table name ('nba_games', 'nba_players', 'nba_teams')
            json_field: JSON field to aggregate
            start_timestamp: Start timestamp
            end_timestamp: End timestamp
            groupby_field: Optional field to group by

        Returns:
            Aggregated results with counts
        """
        if table == "nba_games":
            time_column = "game_date"
        else:
            time_column = "collected_at"

        if groupby_field:
            self.cursor.execute(
                f"""
                SELECT
                    data->>%s as group_value,
                    COUNT(*) as count,
                    MIN({time_column}) as first_occurrence,
                    MAX({time_column}) as last_occurrence
                FROM raw_data.{table}
                WHERE {time_column} BETWEEN %s::timestamptz AND %s::timestamptz
                  AND data->>%s IS NOT NULL
                GROUP BY data->>%s
                ORDER BY count DESC;
            """,
                (
                    groupby_field,
                    start_timestamp,
                    end_timestamp,
                    json_field,
                    groupby_field,
                ),
            )
        else:
            self.cursor.execute(
                f"""
                SELECT
                    data->>%s as field_value,
                    COUNT(*) as count
                FROM raw_data.{table}
                WHERE {time_column} BETWEEN %s::timestamptz AND %s::timestamptz
                  AND data->>%s IS NOT NULL
                GROUP BY data->>%s
                ORDER BY count DESC;
            """,
                (json_field, start_timestamp, end_timestamp, json_field, json_field),
            )

        return self.cursor.fetchall()


def main():
    """Example usage"""
    print("Phase 0.10: JSONB Query Helpers - Example Usage\n")
    print("=" * 70)

    with JSONBQueryHelper() as helper:
        # Example 1: Get source statistics
        print("\n1. Data Source Statistics:")
        print("-" * 70)
        stats = helper.get_source_stats()
        for stat in stats:
            print(f"  {stat}")

        # Example 2: Get season coverage
        print("\n2. Season Coverage:")
        print("-" * 70)
        coverage = helper.get_season_coverage()
        for cov in coverage[:10]:  # First 10
            print(f"  {cov}")

        # Example 3: Search players
        print("\n3. Search for 'James' players:")
        print("-" * 70)
        players = helper.search_players("James", limit=5)
        for player in players:
            print(f"  {player}")

    print("\n" + "=" * 70)
    print("Query helper examples complete!")


if __name__ == "__main__":
    main()
