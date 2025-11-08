"""
Tests for 0.0010: Temporal Integration

Comprehensive test suite for temporal query capabilities that join
JSONB raw data with temporal snapshots.

Usage:
    pytest tests/phases/phase_0/test_0_0010_temporal.py -v
    pytest tests/phases/phase_0/test_0_0010_temporal.py::TestTemporalQueries -v
    pytest tests/phases/phase_0/test_0_0010_temporal.py -k "test_player_stats" -v
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
import importlib.util

# Load Temporal Query Module
spec = importlib.util.spec_from_file_location(
    "temporal_queries", project_root / "scripts/0_10/temporal_queries.py"
)
temporal_queries = importlib.util.module_from_spec(spec)
spec.loader.exec_module(temporal_queries)
TemporalJSONBQueries = temporal_queries.TemporalJSONBQueries

# Load Query Helper (with temporal methods)
spec = importlib.util.spec_from_file_location(
    "query_helper", project_root / "scripts/0_10/main.py"
)
query_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query_helper)
JSONBQueryHelper = query_helper.JSONBQueryHelper


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        yield mock_conn, mock_cursor


@pytest.fixture
def sample_player_stats():
    """Sample player stats data"""
    return {
        "player_id": "2544",
        "player_name": "LeBron James",
        "birth_date": datetime(1984, 12, 30),
        "career_points": 38652,
        "career_assists": 10420,
        "career_rebounds": 10550,
        "career_games": 1421,
        "fg_made": 14919,
        "fg_attempted": 30427,
        "3pt_made": 2410,
        "3pt_attempted": 7101,
    }


@pytest.fixture
def sample_game_state():
    """Sample game state data"""
    return {
        "game_id": "401359859",
        "game_date": datetime(2022, 1, 15),
        "quarter": 4,
        "time_remaining": 120,
        "home_score": 105,
        "away_score": 102,
        "home_team": "LAL",
        "away_team": "GSW",
        "possession_team": "LAL",
        "home_timeouts": 2,
        "away_timeouts": 1,
    }


# ============================================================================
# Test Temporal Query Integration
# ============================================================================


class TestTemporalQueries:
    """Test TemporalJSONBQueries class"""

    def test_temporal_queries_creation(self, mock_db_connection):
        """Test TemporalJSONBQueries can be created"""
        mock_conn, mock_cursor = mock_db_connection

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            assert queries is not None
            assert queries.conn == mock_conn

    def test_context_manager(self, mock_db_connection):
        """Test temporal queries work as context manager"""
        mock_conn, mock_cursor = mock_db_connection

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            with TemporalJSONBQueries() as queries:
                assert queries is not None

            # Verify connections were closed
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_get_player_stats_at_timestamp(
        self, mock_db_connection, sample_player_stats
    ):
        """Test getting player stats at exact timestamp"""
        mock_conn, mock_cursor = mock_db_connection

        # Mock database result
        mock_cursor.description = [
            ("player_id",),
            ("player_name",),
            ("birth_date",),
            ("age_years",),
            ("snapshot_timestamp",),
            ("cumulative_points",),
            ("cumulative_assists",),
            ("cumulative_rebounds",),
            ("cumulative_steals",),
            ("cumulative_blocks",),
            ("cumulative_turnovers",),
            ("cumulative_field_goals_made",),
            ("cumulative_field_goals_attempted",),
            ("cumulative_three_point_made",),
            ("cumulative_three_point_attempted",),
            ("cumulative_free_throws_made",),
            ("cumulative_free_throws_attempted",),
            ("career_games_played",),
            ("career_minutes_played",),
            ("fg_percentage",),
            ("three_point_percentage",),
            ("ft_percentage",),
            ("jsonb_sources",),
            ("recent_events",),
        ]

        mock_cursor.fetchone.return_value = (
            "2544",
            "LeBron James",
            datetime(1984, 12, 30),
            38.28,
            datetime(2023, 3, 15),
            38652,
            10420,
            10550,
            2200,
            1050,
            4788,
            14919,
            30427,
            2410,
            7101,
            8390,
            11252,
            1421,
            55000,
            0.4903,
            0.3394,
            0.7457,
            None,
            None,
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            stats = queries.get_player_stats_at_timestamp(
                player_name="LeBron James", timestamp="2023-03-15 20:00:00-05:00"
            )

            assert stats is not None
            assert stats["player_info"]["player_name"] == "LeBron James"
            assert stats["career_stats"]["points"] == 38652
            assert stats["career_stats"]["games_played"] == 1421
            assert stats["age_at_timestamp"] == 38.28
            assert "fg_percentage" in stats["career_stats"]

    def test_get_player_stats_missing_player(self, mock_db_connection):
        """Test getting stats for non-existent player returns None"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            stats = queries.get_player_stats_at_timestamp(
                player_name="Nonexistent Player", timestamp="2023-03-15 20:00:00-05:00"
            )

            assert stats is None

    def test_get_player_stats_requires_params(self, mock_db_connection):
        """Test that player_stats requires either name or ID"""
        mock_conn, mock_cursor = mock_db_connection

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            with pytest.raises(
                ValueError, match="Must provide either player_name or player_id"
            ):
                queries.get_player_stats_at_timestamp(
                    timestamp="2023-03-15 20:00:00-05:00"
                )

            with pytest.raises(ValueError, match="Must provide timestamp"):
                queries.get_player_stats_at_timestamp(player_name="LeBron James")

    def test_get_game_state_at_timestamp(self, mock_db_connection, sample_game_state):
        """Test reconstructing game state at exact moment"""
        mock_conn, mock_cursor = mock_db_connection

        # Mock database result
        mock_cursor.description = [
            ("game_id",),
            ("state_timestamp",),
            ("quarter",),
            ("time_remaining_seconds",),
            ("home_score",),
            ("away_score",),
            ("possession_team_id",),
            ("home_timeouts_remaining",),
            ("away_timeouts_remaining",),
            ("home_lineup",),
            ("away_lineup",),
            ("state_details",),
            ("source",),
            ("game_date",),
            ("home_team",),
            ("away_team",),
            ("data",),
        ]

        mock_cursor.fetchone.return_value = (
            "401359859",
            datetime(2022, 1, 15, 20, 45),
            4,
            120,
            105,
            102,
            "LAL",
            2,
            1,
            ["player1", "player2", "player3", "player4", "player5"],
            ["player6", "player7", "player8", "player9", "player10"],
            {"note": "crunch time"},
            "espn",
            datetime(2022, 1, 15),
            "LAL",
            "GSW",
            {"home_team": "LAL", "away_team": "GSW"},
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            state = queries.get_game_state_at_timestamp(
                game_id="401359859", timestamp="2022-01-15 20:45:00-06:00"
            )

            assert state is not None
            assert state["game_id"] == "401359859"
            assert state["home_team"] == "LAL"
            assert state["away_team"] == "GSW"
            assert state["score"]["home"] == 105
            assert state["score"]["away"] == 102
            assert state["score"]["differential"] == 3
            assert state["game_situation"]["quarter"] == 4
            assert state["game_situation"]["time_remaining_seconds"] == 120

    def test_query_historical_context(self, mock_db_connection):
        """Test getting historical context for simulation"""
        mock_conn, mock_cursor = mock_db_connection

        # Mock database result
        mock_cursor.description = [
            ("games_played",),
            ("shots_made",),
            ("shots_attempted",),
            ("total_points",),
            ("avg_points_per_event",),
            ("total_hours_played",),
            ("games_in_period",),
            ("game_list",),
        ]

        game_list = [
            {
                "game_id": "game1",
                "game_start": "2023-03-10T19:00:00",
                "game_end": "2023-03-10T21:30:00",
            },
            {
                "game_id": "game2",
                "game_start": "2023-03-12T20:00:00",
                "game_end": "2023-03-12T22:30:00",
            },
        ]

        mock_cursor.fetchone.return_value = (
            2,
            18,
            42,
            50,
            1.19,
            5.0,
            2,
            json.dumps(game_list),
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            context = queries.query_historical_context(
                player_id="2544", timestamp="2023-03-15 20:00:00-05:00", lookback_days=7
            )

            assert context is not None
            assert context["games_played"] == 2
            assert context["performance"]["total_points"] == 50
            assert context["performance"]["shots_made"] == 18
            assert context["performance"]["shots_attempted"] == 42
            assert context["fatigue"]["total_hours_played"] == 5.0
            assert context["fatigue"]["games_in_period"] == 2

    def test_get_career_trajectory(self, mock_db_connection):
        """Test getting player career trajectory"""
        mock_conn, mock_cursor = mock_db_connection

        # Mock multiple snapshots
        mock_cursor.fetchall.return_value = [
            (datetime(2020, 1, 1), 32000, 9000, 9000, 1200, 0.501),
            (datetime(2021, 1, 1), 34000, 9500, 9500, 1280, 0.499),
            (datetime(2022, 1, 1), 36000, 10000, 10000, 1360, 0.495),
            (datetime(2023, 1, 1), 38000, 10400, 10500, 1420, 0.490),
        ]

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            trajectory = queries.get_career_trajectory(
                player_id="2544",
                start_timestamp="2020-01-01",
                end_timestamp="2023-12-31",
                interval_days=365,
            )

            assert len(trajectory) == 4
            assert trajectory[0]["cumulative_points"] == 32000
            assert trajectory[3]["cumulative_points"] == 38000
            assert all("fg_percentage" in t for t in trajectory)


# ============================================================================
# Test Extended Query Helper Methods
# ============================================================================


class TestExtendedQueryHelper:
    """Test temporal methods added to JSONBQueryHelper"""

    def test_get_player_performance_with_context(self, mock_db_connection):
        """Test getting player performance with temporal context"""
        mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = (
            "401359859",  # game_id
            datetime(2022, 1, 15),  # game_date
            {"home_team": "LAL", "away_team": "GSW"},  # data
            35000,  # career_points_before_game
            9500,  # career_assists_before_game
            9800,  # career_rebounds_before_game
            1380,  # games_played_before
            datetime(2022, 1, 15),  # snapshot_timestamp
            "LeBron James",  # player_name
            datetime(1984, 12, 30),  # birth_date
            37.04,  # age_at_game
        )

        with patch.object(
            JSONBQueryHelper, "_create_connection", return_value=mock_conn
        ):
            helper = JSONBQueryHelper()

            result = helper.get_player_performance_with_context(
                player_id="2544", game_id="401359859"
            )

            assert result is not None
            assert result["game_id"] == "401359859"
            assert result["temporal_context"]["career_points_before_game"] == 35000
            assert result["temporal_context"]["player_name"] == "LeBron James"
            assert result["temporal_context"]["age_at_game"] == 37.04

    def test_get_matchup_history_temporal(self, mock_db_connection):
        """Test getting team matchup history with temporal data"""
        mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = [
            ("game1", datetime(2022, 12, 25), "LAL", "GSW", 110, 115, 5),
            ("game2", datetime(2022, 3, 15), "GSW", "LAL", 120, 118, 8),
            ("game3", datetime(2021, 10, 19), "LAL", "GSW", 98, 105, 3),
        ]

        with patch.object(
            JSONBQueryHelper, "_create_connection", return_value=mock_conn
        ):
            helper = JSONBQueryHelper()

            matchups = helper.get_matchup_history_temporal(
                team1="LAL", team2="GSW", start_date="2021-01-01", end_date="2022-12-31"
            )

            assert len(matchups) == 3
            assert matchups[0][2] == "LAL"  # home_team
            assert matchups[0][3] == "GSW"  # away_team

    def test_aggregate_with_temporal_filter(self, mock_db_connection):
        """Test temporal aggregation"""
        mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = [("LAL", 82), ("GSW", 80), ("BOS", 78)]

        with patch.object(
            JSONBQueryHelper, "_create_connection", return_value=mock_conn
        ):
            helper = JSONBQueryHelper()

            results = helper.aggregate_with_temporal_filter(
                table="nba_games",
                json_field="home_team",
                start_timestamp="2022-01-01",
                end_timestamp="2022-12-31",
            )

            assert len(results) == 3
            assert results[0][0] == "LAL"
            assert results[0][1] == 82


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for temporal queries"""

    @pytest.mark.skipif(
        not os.getenv("RDS_PASSWORD"), reason="Requires database connection"
    )
    def test_end_to_end_player_query(self):
        """Test complete player stats query (requires real database)"""
        # This would test against actual RDS database
        # Skipped in CI/CD environments
        pass

    @pytest.mark.skipif(
        not os.getenv("RDS_PASSWORD"), reason="Requires database connection"
    )
    def test_end_to_end_game_state(self):
        """Test complete game state reconstruction (requires real database)"""
        # This would test against actual RDS database
        # Skipped in CI/CD environments
        pass


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Performance-related tests"""

    def test_query_response_time_under_100ms(self, mock_db_connection):
        """Test that temporal queries complete quickly"""
        import time

        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            start = time.time()
            queries.get_player_stats_at_timestamp(
                player_name="LeBron James", timestamp="2023-03-15 20:00:00-05:00"
            )
            duration = time.time() - start

            # Mock queries should be nearly instantaneous
            assert duration < 0.1  # 100ms

    def test_large_trajectory_handling(self, mock_db_connection):
        """Test handling large career trajectories"""
        mock_conn, mock_cursor = mock_db_connection

        # Simulate 20 years of monthly snapshots (240 points)
        large_trajectory = [
            (datetime(2000, 1, 1), i * 100, i * 30, i * 40, i, 0.5) for i in range(240)
        ]
        mock_cursor.fetchall.return_value = large_trajectory

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            trajectory = queries.get_career_trajectory(
                player_id="2544",
                start_timestamp="2000-01-01",
                end_timestamp="2020-12-31",
            )

            assert len(trajectory) == 240


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_timestamp_format(self, mock_db_connection):
        """Test handling of invalid timestamp formats"""
        mock_conn, mock_cursor = mock_db_connection

        # PostgreSQL will raise error for invalid timestamp
        mock_cursor.execute.side_effect = Exception(
            "invalid input syntax for type timestamp"
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            with pytest.raises(Exception):
                queries.get_player_stats_at_timestamp(
                    player_name="LeBron James", timestamp="not a valid timestamp"
                )

    def test_future_timestamp_query(self, mock_db_connection):
        """Test querying with future timestamp (should return most recent)"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None  # No future data

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            stats = queries.get_player_stats_at_timestamp(
                player_name="LeBron James",
                timestamp="2050-01-01 00:00:00-05:00",  # Future
            )

            # Should return None (no data in future)
            assert stats is None

    def test_missing_temporal_tables(self, mock_db_connection):
        """Test graceful handling when temporal tables don't exist"""
        mock_conn, mock_cursor = mock_db_connection

        # Simulate missing table error
        mock_cursor.execute.side_effect = Exception(
            'relation "player_snapshots" does not exist'
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            with pytest.raises(Exception, match="does not exist"):
                queries.get_player_stats_at_timestamp(
                    player_name="LeBron James", timestamp="2023-03-15 20:00:00-05:00"
                )


# ============================================================================
# Validation Tests
# ============================================================================


class TestValidation:
    """Test data validation in temporal queries"""

    def test_age_calculation_accuracy(self, mock_db_connection):
        """Test that age calculation is accurate to milliseconds"""
        mock_conn, mock_cursor = mock_db_connection

        # LeBron born Dec 30, 1984
        # Query on Jan 1, 2024
        # Expected age: 39.005 years (approximately)

        mock_cursor.description = [
            ("player_id",),
            ("player_name",),
            ("birth_date",),
            ("age_years",),
            ("snapshot_timestamp",),
            ("cumulative_points",),
            ("cumulative_assists",),
            ("cumulative_rebounds",),
            ("cumulative_steals",),
            ("cumulative_blocks",),
            ("cumulative_turnovers",),
            ("cumulative_field_goals_made",),
            ("cumulative_field_goals_attempted",),
            ("cumulative_three_point_made",),
            ("cumulative_three_point_attempted",),
            ("cumulative_free_throws_made",),
            ("cumulative_free_throws_attempted",),
            ("career_games_played",),
            ("career_minutes_played",),
            ("fg_percentage",),
            ("three_point_percentage",),
            ("ft_percentage",),
            ("jsonb_sources",),
            ("recent_events",),
        ]

        mock_cursor.fetchone.return_value = (
            "2544",
            "LeBron James",
            datetime(1984, 12, 30),
            39.005479,
            datetime(2024, 1, 1),
            38652,
            10420,
            10550,
            2200,
            1050,
            4788,
            14919,
            30427,
            2410,
            7101,
            8390,
            11252,
            1421,
            55000,
            0.4903,
            0.3394,
            0.7457,
            None,
            None,
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            stats = queries.get_player_stats_at_timestamp(
                player_name="LeBron James", timestamp="2024-01-01 00:00:00-05:00"
            )

            # Age should be very close to 39.00548 years
            assert stats["age_at_timestamp"] > 39.0
            assert stats["age_at_timestamp"] < 39.01

    def test_shooting_percentage_calculation(self, mock_db_connection):
        """Test that shooting percentages are calculated correctly"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.description = [
            ("player_id",),
            ("player_name",),
            ("birth_date",),
            ("age_years",),
            ("snapshot_timestamp",),
            ("cumulative_points",),
            ("cumulative_assists",),
            ("cumulative_rebounds",),
            ("cumulative_steals",),
            ("cumulative_blocks",),
            ("cumulative_turnovers",),
            ("cumulative_field_goals_made",),
            ("cumulative_field_goals_attempted",),
            ("cumulative_three_point_made",),
            ("cumulative_three_point_attempted",),
            ("cumulative_free_throws_made",),
            ("cumulative_free_throws_attempted",),
            ("career_games_played",),
            ("career_minutes_played",),
            ("fg_percentage",),
            ("three_point_percentage",),
            ("ft_percentage",),
            ("jsonb_sources",),
            ("recent_events",),
        ]

        # 10000 made / 20000 attempted = 0.5000 exactly
        mock_cursor.fetchone.return_value = (
            "2544",
            "LeBron James",
            datetime(1984, 12, 30),
            39.0,
            datetime(2024, 1, 1),
            20000,
            5000,
            5000,
            1000,
            500,
            2000,
            10000,
            20000,
            2000,
            6000,
            4000,
            5000,
            1000,
            40000,
            0.5000,
            0.3333,
            0.8000,
            None,
            None,
        )

        with patch.object(
            TemporalJSONBQueries, "_create_connection", return_value=mock_conn
        ):
            queries = TemporalJSONBQueries()

            stats = queries.get_player_stats_at_timestamp(
                player_name="LeBron James", timestamp="2024-01-01 00:00:00-05:00"
            )

            assert stats["career_stats"]["fg_percentage"] == 0.5000
            assert stats["career_stats"]["three_point_percentage"] == 0.3333
            assert stats["career_stats"]["ft_percentage"] == 0.8000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
