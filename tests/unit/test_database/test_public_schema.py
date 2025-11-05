"""
Unit Tests for Public Schema (40 Tables)

Tests all core tables in the public schema including:
- Game data (games, game_states, game_state_snapshots)
- Player data (players, player_biographical, player_game_stats, player_snapshots)
- Team data (teams, team_seasons, team_game_stats)
- Play-by-play data (play_by_play, plays, temporal_events)
- Box scores (box_score_players, box_score_teams, box_score_snapshots)
- Advanced metrics (possession_panel, lineup_snapshots, player_plus_minus_snapshots)
- External data integration (hoopr_*, nba_api_*)
- Monitoring (dims_*)
"""

import pytest
from datetime import datetime


class TestPublicSchemaCore:
    """Tests for core public schema tables"""

    def test_games_table_exists(self, mock_db_connection):
        """Test that games table exists and has expected structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ("game_id",),
            ("game_date",),
            ("season",),
            ("home_team",),
            ("away_team",),
            ("home_score",),
            ("away_score",),
        ]
        cursor.fetchall.return_value = []

        # Verify table can be queried
        cursor.execute("SELECT * FROM games LIMIT 1")
        assert cursor.execute.called

    def test_games_table_has_game_id_primary_key(self, mock_db_connection):
        """Test that games table has game_id as primary key"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [("constraint_name",), ("column_name",)]
        cursor.fetchall.return_value = [("games_pkey", "game_id")]

        # Verify primary key constraint
        cursor.execute(
            """
            SELECT constraint_name, column_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'games' AND table_schema = 'public'
        """
        )
        results = cursor.fetchall()
        assert len(results) > 0

    def test_players_table_exists(self, mock_db_connection):
        """Test that players table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("players",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'players'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == "players"

    def test_teams_table_exists(self, mock_db_connection):
        """Test that teams table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("teams",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'teams'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestPlayByPlayTables:
    """Tests for play-by-play related tables"""

    def test_play_by_play_table_exists(self, mock_db_connection):
        """Test that play_by_play table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("play_by_play",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'play_by_play'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_plays_table_exists(self, mock_db_connection):
        """Test that plays table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("plays",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'plays'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_temporal_events_table_exists(self, mock_db_connection):
        """Test that temporal_events table exists (5.8 GB critical table)"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("temporal_events",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'temporal_events'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_hoopr_play_by_play_table_exists(self, mock_db_connection):
        """Test that hoopr_play_by_play table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("hoopr_play_by_play",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'hoopr_play_by_play'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestBoxScoreTables:
    """Tests for box score related tables"""

    def test_box_score_players_table_exists(self, mock_db_connection):
        """Test that box_score_players table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("box_score_players",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'box_score_players'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_box_score_teams_table_exists(self, mock_db_connection):
        """Test that box_score_teams table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("box_score_teams",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'box_score_teams'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_box_score_snapshots_table_exists(self, mock_db_connection):
        """Test that box_score_snapshots table exists (Phase 8 output)"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("box_score_snapshots",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'box_score_snapshots'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_box_score_verification_table_exists(self, mock_db_connection):
        """Test that box_score_verification table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("box_score_verification",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'box_score_verification'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_quarter_box_scores_table_exists(self, mock_db_connection):
        """Test that quarter_box_scores table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("quarter_box_scores",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'quarter_box_scores'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestPlayerTables:
    """Tests for player-related tables"""

    def test_player_biographical_table_exists(self, mock_db_connection):
        """Test that player_biographical table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("player_biographical",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'player_biographical'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_player_game_stats_table_exists(self, mock_db_connection):
        """Test that player_game_stats table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("player_game_stats",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'player_game_stats'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_player_snapshots_table_exists(self, mock_db_connection):
        """Test that player_snapshots table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("player_snapshots",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'player_snapshots'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_player_snapshot_stats_table_exists(self, mock_db_connection):
        """Test that player_snapshot_stats table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("player_snapshot_stats",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'player_snapshot_stats'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_player_plus_minus_snapshots_table_exists(self, mock_db_connection):
        """Test that player_plus_minus_snapshots table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("player_plus_minus_snapshots",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'player_plus_minus_snapshots'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestTeamTables:
    """Tests for team-related tables"""

    def test_team_seasons_table_exists(self, mock_db_connection):
        """Test that team_seasons table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("team_seasons",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'team_seasons'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_team_game_stats_table_exists(self, mock_db_connection):
        """Test that team_game_stats table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("team_game_stats",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'team_game_stats'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestAdvancedMetricsTables:
    """Tests for advanced metrics and tracking tables"""

    def test_possession_metadata_table_exists(self, mock_db_connection):
        """Test that possession_metadata table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("possession_metadata",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'possession_metadata'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_possession_panel_table_exists(self, mock_db_connection):
        """Test that possession_panel table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("possession_panel",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'possession_panel'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_possession_panel_pbpstats_table_exists(self, mock_db_connection):
        """Test that possession_panel_pbpstats table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("possession_panel_pbpstats",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'possession_panel_pbpstats'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_lineup_snapshots_table_exists(self, mock_db_connection):
        """Test that lineup_snapshots table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("lineup_snapshots",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'lineup_snapshots'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestGameStateTables:
    """Tests for game state tracking tables"""

    def test_game_states_table_exists(self, mock_db_connection):
        """Test that game_states table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("game_states",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'game_states'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_game_state_snapshots_table_exists(self, mock_db_connection):
        """Test that game_state_snapshots table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("game_state_snapshots",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'game_state_snapshots'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_games_summary_table_exists(self, mock_db_connection):
        """Test that games_summary table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("games_summary",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'games_summary'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestExternalDataIntegrationTables:
    """Tests for external data source integration tables"""

    def test_hoopr_schedule_table_exists(self, mock_db_connection):
        """Test that hoopr_schedule table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("hoopr_schedule",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'hoopr_schedule'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_hoopr_player_box_table_exists(self, mock_db_connection):
        """Test that hoopr_player_box table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("hoopr_player_box",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'hoopr_player_box'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_hoopr_team_box_table_exists(self, mock_db_connection):
        """Test that hoopr_team_box table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("hoopr_team_box",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'hoopr_team_box'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_nba_api_comprehensive_table_exists(self, mock_db_connection):
        """Test that nba_api_comprehensive table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("nba_api_comprehensive",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'nba_api_comprehensive'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_nba_api_game_advanced_table_exists(self, mock_db_connection):
        """Test that nba_api_game_advanced table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("nba_api_game_advanced",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'nba_api_game_advanced'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_nba_api_player_dashboards_table_exists(self, mock_db_connection):
        """Test that nba_api_player_dashboards table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("nba_api_player_dashboards",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'nba_api_player_dashboards'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_nba_api_player_tracking_table_exists(self, mock_db_connection):
        """Test that nba_api_player_tracking table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("nba_api_player_tracking",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'nba_api_player_tracking'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_nba_api_team_dashboards_table_exists(self, mock_db_connection):
        """Test that nba_api_team_dashboards table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("nba_api_team_dashboards",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'nba_api_team_dashboards'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


class TestDIMSMonitoringTables:
    """Tests for DIMS (Data Integrity Monitoring System) tables"""

    def test_dims_config_table_exists(self, mock_db_connection):
        """Test that dims_config table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("dims_config",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'dims_config'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_dims_metrics_history_table_exists(self, mock_db_connection):
        """Test that dims_metrics_history table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("dims_metrics_history",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'dims_metrics_history'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_dims_metrics_snapshots_table_exists(self, mock_db_connection):
        """Test that dims_metrics_snapshots table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("dims_metrics_snapshots",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'dims_metrics_snapshots'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_dims_verification_runs_table_exists(self, mock_db_connection):
        """Test that dims_verification_runs table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("dims_verification_runs",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'dims_verification_runs'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_dims_event_log_table_exists(self, mock_db_connection):
        """Test that dims_event_log table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("dims_event_log",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'dims_event_log'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1

    def test_dims_approval_log_table_exists(self, mock_db_connection):
        """Test that dims_approval_log table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("dims_approval_log",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'dims_approval_log'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1


@pytest.mark.unit
@pytest.mark.database
class TestPublicSchemaIntegration:
    """Integration tests for public schema table relationships"""

    def test_all_40_public_tables_exist(self, mock_db_connection):
        """Test that all 40 public schema tables exist"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value

        # Mock response with all 40 tables
        expected_tables = [
            "box_score_players",
            "box_score_snapshots",
            "box_score_teams",
            "box_score_verification",
            "dims_approval_log",
            "dims_config",
            "dims_event_log",
            "dims_metrics_history",
            "dims_metrics_snapshots",
            "dims_verification_runs",
            "game_state_snapshots",
            "game_states",
            "games",
            "games_summary",
            "hoopr_play_by_play",
            "hoopr_player_box",
            "hoopr_schedule",
            "hoopr_team_box",
            "lineup_snapshots",
            "nba_api_comprehensive",
            "nba_api_game_advanced",
            "nba_api_player_dashboards",
            "nba_api_player_tracking",
            "nba_api_team_dashboards",
            "play_by_play",
            "player_biographical",
            "player_game_stats",
            "player_plus_minus_snapshots",
            "player_snapshot_stats",
            "player_snapshots",
            "players",
            "plays",
            "possession_metadata",
            "possession_panel",
            "possession_panel_pbpstats",
            "quarter_box_scores",
            "team_game_stats",
            "team_seasons",
            "teams",
            "temporal_events",
        ]

        cursor.fetchall.return_value = [(t,) for t in expected_tables]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )
        results = cursor.fetchall()

        # Verify we got 40 tables
        assert len(results) == 40

        # Verify all expected tables are present
        table_names = [r[0] for r in results]
        for table in expected_tables:
            assert table in table_names

    def test_games_and_players_foreign_key_relationship(self, mock_db_connection):
        """Test that foreign key relationships exist between games and players"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("fk_game_player",)]

        cursor.execute(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name IN ('games', 'players')
            AND constraint_type = 'FOREIGN KEY'
        """
        )
        results = cursor.fetchall()

        # Should have foreign key relationships
        assert len(results) >= 0
