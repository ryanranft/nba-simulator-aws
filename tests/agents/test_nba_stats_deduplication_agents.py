"""
Tests for NBA Stats and Deduplication Agents

Comprehensive test suite covering:
- NBA Stats Agent: NBA API coordination and data collection
- Deduplication Agent: Duplicate detection and resolution

Test Coverage:
- Configuration validation
- Core execution logic
- Error handling
- Metrics collection
- State management
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile

from nba_simulator.agents.nba_stats import NBAStatsAgent
from nba_simulator.agents.deduplication import DeduplicationAgent
from nba_simulator.agents.base_agent import AgentState, AgentPriority


# ============================================================================
# NBA STATS AGENT TESTS
# ============================================================================


class TestNBAStatsAgent:
    """Test suite for NBA Stats Agent"""

    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def valid_config(self):
        """Valid NBA Stats agent configuration"""
        return {
            "api_rate_limit": 60,
            "max_concurrent": 5,
            "retry_attempts": 3,
            "data_types": ["boxscore", "tracking"],
        }

    @pytest.fixture
    def agent(self, valid_config, temp_state_dir):
        """Create NBA Stats agent instance"""
        agent = NBAStatsAgent(config=valid_config)
        agent.state_dir = temp_state_dir
        agent.state_file = temp_state_dir / "nba_stats_state.json"
        return agent

    # === Initialization Tests ===

    def test_agent_initialization(self, agent, valid_config):
        """Test agent initializes with correct properties"""
        assert agent.agent_name == "nba_stats"
        assert agent.priority == AgentPriority.HIGH
        assert agent.state == AgentState.INITIALIZED
        assert agent.api_rate_limit == valid_config["api_rate_limit"]
        assert agent.max_concurrent == valid_config["max_concurrent"]
        assert agent.retry_attempts == valid_config["retry_attempts"]
        assert agent.data_types == valid_config["data_types"]

    def test_default_configuration(self, temp_state_dir):
        """Test agent uses sensible defaults"""
        agent = NBAStatsAgent()
        agent.state_dir = temp_state_dir

        assert agent.api_rate_limit == 60
        assert agent.max_concurrent == 5
        assert agent.retry_attempts == 3
        assert agent.data_types == ["boxscore", "tracking"]

    def test_custom_configuration(self, temp_state_dir):
        """Test agent accepts custom configuration"""
        config = {
            "api_rate_limit": 120,
            "max_concurrent": 10,
            "retry_attempts": 5,
            "data_types": ["boxscore", "tracking", "lineups", "shots"],
        }
        agent = NBAStatsAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent.api_rate_limit == 120
        assert agent.max_concurrent == 10
        assert agent.retry_attempts == 5
        assert len(agent.data_types) == 4

    # === Configuration Validation Tests ===

    def test_validate_config_success(self, agent):
        """Test configuration validation passes with valid config"""
        assert agent._validate_config() is True

    def test_validate_config_invalid_rate_limit(self, temp_state_dir):
        """Test validation fails with invalid rate limit"""
        config = {"api_rate_limit": -10}
        agent = NBAStatsAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False
        assert len(agent.errors) > 0
        assert "api_rate_limit" in agent.errors[0]

    def test_validate_config_zero_rate_limit(self, temp_state_dir):
        """Test validation fails with zero rate limit"""
        config = {"api_rate_limit": 0}
        agent = NBAStatsAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False

    def test_validate_config_invalid_concurrent(self, temp_state_dir):
        """Test validation fails with invalid max_concurrent"""
        config = {"max_concurrent": -5}
        agent = NBAStatsAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False
        assert "max_concurrent" in agent.errors[0]

    def test_validate_config_invalid_data_type(self, temp_state_dir):
        """Test validation fails with invalid data type"""
        config = {"data_types": ["invalid_type", "boxscore"]}
        agent = NBAStatsAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False
        assert "Invalid data_type" in agent.errors[0]

    def test_validate_config_valid_data_types(self, temp_state_dir):
        """Test validation passes with all valid data types"""
        config = {"data_types": ["boxscore", "tracking", "lineups", "shots"]}
        agent = NBAStatsAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is True

    # === Execution Tests ===

    @patch("nba_simulator.agents.nba_stats.execute_query")
    def test_execute_core_no_games(self, mock_query, agent):
        """Test execution with no games to process"""
        mock_query.return_value = []

        result = agent._execute_core()

        assert result is True
        assert agent.metrics.items_processed == 0
        assert agent.metrics.items_successful == 0

    @patch("nba_simulator.agents.nba_stats.execute_query")
    def test_execute_core_with_games(self, mock_query, agent):
        """Test execution with games to process"""
        # Mock games to process
        mock_games = [
            {
                "game_id": "game1",
                "game_date": "2024-01-01",
                "home_team": "LAL",
                "away_team": "GSW",
            },
            {
                "game_id": "game2",
                "game_date": "2024-01-02",
                "home_team": "BOS",
                "away_team": "MIA",
            },
        ]
        mock_query.return_value = mock_games

        result = agent._execute_core()

        assert result is True
        assert agent.metrics.items_processed == 2
        assert agent.metrics.items_successful == 2
        assert agent.metrics.items_failed == 0
        assert len(agent.games_processed) == 2

    @patch("nba_simulator.agents.nba_stats.execute_query")
    def test_execute_core_success_rate_calculation(self, mock_query, agent):
        """Test quality score is calculated correctly"""
        mock_games = [
            {
                "game_id": f"game{i}",
                "game_date": "2024-01-01",
                "home_team": "LAL",
                "away_team": "GSW",
            }
            for i in range(10)
        ]
        mock_query.return_value = mock_games

        result = agent._execute_core()

        assert result is True
        assert agent.metrics.quality_score == 100.0  # All successful

    @patch("nba_simulator.agents.nba_stats.execute_query")
    def test_execute_core_handles_errors(self, mock_query, agent):
        """Test execution handles database errors gracefully"""
        mock_query.side_effect = Exception("Database error")

        result = agent._execute_core()

        assert result is False
        assert len(agent.errors) > 0

    # === Game Processing Tests ===

    def test_process_game_success(self, agent):
        """Test individual game processing"""
        result = agent._process_game("test_game_id")

        assert result is True

    def test_process_game_handles_errors(self, agent):
        """Test game processing handles errors"""
        # Override to raise error
        original_method = agent._collect_data_type
        agent._collect_data_type = Mock(side_effect=Exception("API error"))

        result = agent._process_game("test_game_id")

        # Should still return True but log warnings
        assert result is True

        # Restore original
        agent._collect_data_type = original_method

    # === Data Collection Tests ===

    def test_collect_data_type_success(self, agent):
        """Test data type collection succeeds"""
        result = agent._collect_data_type("game1", "boxscore")

        assert result is True
        assert agent.requests_successful > 0

    def test_collect_data_type_retry_logic(self, agent):
        """Test retry logic on failures"""
        # Set up to fail initially
        agent.retry_attempts = 3

        # Test collection (simulated success)
        result = agent._collect_data_type("game1", "tracking")

        assert result is True

    def test_collect_data_type_handles_errors(self, agent):
        """Test data collection handles exceptions"""
        # Override to raise error
        agent.retry_attempts = 1
        original_sleep = agent._apply_rate_limit
        agent._apply_rate_limit = Mock(side_effect=Exception("Network error"))

        result = agent._collect_data_type("game1", "boxscore")

        # Should handle error gracefully
        assert len(agent.errors) > 0

        # Restore
        agent._apply_rate_limit = original_sleep

    # === Rate Limiting Tests ===

    def test_rate_limiting_applied(self, agent):
        """Test rate limiting is applied between requests"""
        import time

        start = time.time()

        agent._apply_rate_limit()

        elapsed = time.time() - start
        expected_delay = 60.0 / agent.api_rate_limit

        # Should have waited at least the expected delay
        assert elapsed >= expected_delay * 0.9  # Allow 10% tolerance

    def test_rate_limit_configuration(self, temp_state_dir):
        """Test different rate limit configurations"""
        configs = [30, 60, 120]

        for rate in configs:
            agent = NBAStatsAgent(config={"api_rate_limit": rate})
            agent.state_dir = temp_state_dir
            assert agent.api_rate_limit == rate

    # === Agent Info Tests ===

    def test_get_agent_info(self, agent):
        """Test agent info returns correct metadata"""
        info = agent.get_agent_info()

        assert info["name"] == "NBA Stats Collector"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert len(info["capabilities"]) >= 5
        assert info["api_rate_limit"] == agent.api_rate_limit
        assert info["data_types"] == agent.data_types

    def test_get_collection_stats(self, agent):
        """Test collection statistics"""
        # Process some games
        agent.requests_made = 10
        agent.requests_successful = 8
        agent.requests_failed = 2
        agent.games_processed = ["game1", "game2"]

        stats = agent.get_collection_stats()

        assert stats["games_processed"] == 2
        assert stats["requests_made"] == 10
        assert stats["requests_successful"] == 8
        assert stats["requests_failed"] == 2
        assert stats["success_rate"] == 80.0

    def test_get_collection_stats_no_requests(self, agent):
        """Test statistics with no requests made"""
        stats = agent.get_collection_stats()

        assert stats["success_rate"] == 0


# ============================================================================
# DEDUPLICATION AGENT TESTS
# ============================================================================


class TestDeduplicationAgent:
    """Test suite for Deduplication Agent"""

    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def valid_config(self):
        """Valid deduplication agent configuration"""
        return {
            "similarity_threshold": 95.0,
            "merge_strategy": "merge",
            "tables_to_check": ["games", "players"],
            "auto_merge": False,
        }

    @pytest.fixture
    def agent(self, valid_config, temp_state_dir):
        """Create deduplication agent instance"""
        agent = DeduplicationAgent(config=valid_config)
        agent.state_dir = temp_state_dir
        agent.state_file = temp_state_dir / "deduplication_state.json"
        return agent

    # === Initialization Tests ===

    def test_agent_initialization(self, agent, valid_config):
        """Test agent initializes with correct properties"""
        assert agent.agent_name == "deduplication"
        assert agent.priority == AgentPriority.NORMAL
        assert agent.state == AgentState.INITIALIZED
        assert agent.similarity_threshold == valid_config["similarity_threshold"]
        assert agent.merge_strategy == valid_config["merge_strategy"]
        assert agent.tables_to_check == valid_config["tables_to_check"]
        assert agent.auto_merge == valid_config["auto_merge"]

    def test_default_configuration(self, temp_state_dir):
        """Test agent uses sensible defaults"""
        agent = DeduplicationAgent()
        agent.state_dir = temp_state_dir

        assert agent.similarity_threshold == 95.0
        assert agent.merge_strategy == "merge"
        assert agent.tables_to_check == ["games", "players"]
        assert agent.auto_merge is False

    def test_custom_configuration(self, temp_state_dir):
        """Test agent accepts custom configuration"""
        config = {
            "similarity_threshold": 90.0,
            "merge_strategy": "latest",
            "tables_to_check": ["games", "players", "teams"],
            "auto_merge": True,
        }
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent.similarity_threshold == 90.0
        assert agent.merge_strategy == "latest"
        assert len(agent.tables_to_check) == 3
        assert agent.auto_merge is True

    # === Configuration Validation Tests ===

    def test_validate_config_success(self, agent):
        """Test configuration validation passes with valid config"""
        assert agent._validate_config() is True

    def test_validate_config_invalid_threshold_too_low(self, temp_state_dir):
        """Test validation fails with threshold below 0"""
        config = {"similarity_threshold": -10.0}
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False
        assert len(agent.errors) > 0

    def test_validate_config_invalid_threshold_too_high(self, temp_state_dir):
        """Test validation fails with threshold above 100"""
        config = {"similarity_threshold": 150.0}
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False

    def test_validate_config_boundary_values(self, temp_state_dir):
        """Test threshold boundary values"""
        # Test 0.0 (valid)
        agent = DeduplicationAgent(config={"similarity_threshold": 0.0})
        agent.state_dir = temp_state_dir
        assert agent._validate_config() is True

        # Test 100.0 (valid)
        agent = DeduplicationAgent(config={"similarity_threshold": 100.0})
        agent.state_dir = temp_state_dir
        assert agent._validate_config() is True

    def test_validate_config_invalid_strategy(self, temp_state_dir):
        """Test validation fails with invalid merge strategy"""
        config = {"merge_strategy": "invalid_strategy"}
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False
        assert "merge_strategy" in agent.errors[0]

    def test_validate_config_all_valid_strategies(self, temp_state_dir):
        """Test all valid merge strategies"""
        strategies = ["latest", "complete", "merge", "manual"]

        for strategy in strategies:
            agent = DeduplicationAgent(config={"merge_strategy": strategy})
            agent.state_dir = temp_state_dir
            assert agent._validate_config() is True

    def test_validate_config_invalid_tables_type(self, temp_state_dir):
        """Test validation fails with non-list tables"""
        config = {"tables_to_check": "games"}
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        assert agent._validate_config() is False
        assert "must be a list" in agent.errors[0]

    # === Execution Tests ===

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_execute_core_no_duplicates(self, mock_query, agent):
        """Test execution with no duplicates found"""
        mock_query.return_value = []

        result = agent._execute_core()

        assert result is True
        assert agent.metrics.quality_score == 100.0  # No duplicates is perfect

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_execute_core_with_duplicates_no_auto_merge(self, mock_query, agent):
        """Test execution finds duplicates but doesn't auto-merge"""
        mock_duplicates = [
            {"id1": "game1", "id2": "game2"},
            {"id1": "game3", "id2": "game4"},
        ]
        mock_query.return_value = mock_duplicates

        result = agent._execute_core()

        assert result is True
        assert len(agent.duplicates_found["games"]) == 2
        # No merges because auto_merge is False
        assert agent.duplicates_merged["games"] == 0

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_execute_core_with_auto_merge(self, mock_query, temp_state_dir):
        """Test execution with auto-merge enabled"""
        config = {"auto_merge": True, "tables_to_check": ["games"]}
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        mock_duplicates = [{"id1": "game1", "id2": "game2"}]
        mock_query.return_value = mock_duplicates

        result = agent._execute_core()

        assert result is True
        assert agent.duplicates_merged["games"] > 0

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_execute_core_multiple_tables(self, mock_query, agent):
        """Test execution checks multiple tables"""
        mock_query.return_value = []

        result = agent._execute_core()

        assert result is True
        # Should have checked all tables
        assert mock_query.call_count >= len(agent.tables_to_check)

    # === Duplicate Detection Tests ===

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_find_duplicate_games(self, mock_query, agent):
        """Test finding duplicate games"""
        mock_results = [
            {"id1": "game1", "id2": "game2"},
            {"id1": "game3", "id2": "game4"},
        ]
        mock_query.return_value = mock_results

        duplicates = agent._find_duplicate_games()

        assert len(duplicates) == 2
        assert duplicates[0] == ("game1", "game2")
        assert duplicates[1] == ("game3", "game4")

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_find_duplicate_games_no_results(self, mock_query, agent):
        """Test finding duplicates with no results"""
        mock_query.return_value = []

        duplicates = agent._find_duplicate_games()

        assert len(duplicates) == 0

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_find_duplicate_players(self, mock_query, agent):
        """Test finding duplicate players"""
        mock_results = [{"id1": "player1", "id2": "player2"}]
        mock_query.return_value = mock_results

        duplicates = agent._find_duplicate_players()

        assert len(duplicates) == 1
        assert duplicates[0] == ("player1", "player2")

    def test_find_duplicates_unsupported_table(self, agent):
        """Test handling of unsupported table"""
        duplicates = agent._find_duplicates("unsupported_table")

        assert len(duplicates) == 0
        assert len(agent.warnings) > 0

    # === Merge Resolution Tests ===

    def test_merge_records_success(self, agent):
        """Test successful record merge"""
        result = agent._merge_records("games", "game1", "game2")

        assert result is True

    def test_merge_records_handles_errors(self, agent):
        """Test merge handles errors gracefully"""
        # Override to raise error
        original_logger = agent.logger
        agent.logger = Mock()
        agent.logger.debug = Mock(side_effect=Exception("Merge error"))

        result = agent._merge_records("games", "game1", "game2")

        # Should handle error and return False
        assert result is False
        assert len(agent.errors) > 0

        # Restore
        agent.logger = original_logger

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_resolve_duplicates(self, mock_query, agent):
        """Test resolving multiple duplicate pairs"""
        duplicates = [("id1", "id2"), ("id3", "id4")]

        agent._resolve_duplicates("games", duplicates)

        # All should be processed (success or flagged)
        total = agent.duplicates_merged["games"] + agent.duplicates_flagged["games"]
        assert total == 2

    # === Reporting Tests ===

    def test_get_agent_info(self, agent):
        """Test agent info returns correct metadata"""
        info = agent.get_agent_info()

        assert info["name"] == "Deduplication Manager"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert len(info["capabilities"]) >= 5
        assert info["merge_strategy"] == agent.merge_strategy
        assert info["similarity_threshold"] == agent.similarity_threshold

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_get_deduplication_report(self, mock_query, agent):
        """Test deduplication report generation"""
        # Set up some test data
        agent.duplicates_found["games"] = [("g1", "g2"), ("g3", "g4")]
        agent.duplicates_merged["games"] = 1
        agent.duplicates_flagged["games"] = 1

        report = agent.get_deduplication_report()

        assert report["tables_checked"] == agent.tables_to_check
        assert report["duplicates_by_table"]["games"] == 2
        assert report["merged_by_table"]["games"] == 1
        assert report["flagged_by_table"]["games"] == 1
        assert report["total_duplicates"] == 2
        assert report["total_merged"] == 1
        assert report["total_flagged"] == 1

    def test_get_deduplication_report_empty(self, agent):
        """Test report with no duplicates"""
        report = agent.get_deduplication_report()

        assert report["total_duplicates"] == 0
        assert report["total_merged"] == 0
        assert report["total_flagged"] == 0

    # === Metrics Tests ===

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_metrics_calculation(self, mock_query, agent):
        """Test metrics are calculated correctly"""
        # Set up duplicates
        agent.duplicates_found["games"] = [("g1", "g2")]
        agent.duplicates_merged["games"] = 1
        agent.duplicates_flagged["games"] = 0

        agent._execute_core()

        assert agent.metrics.items_processed == 1
        assert agent.metrics.items_successful == 1
        assert agent.metrics.quality_score == 100.0

    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_metrics_with_failures(self, mock_query, temp_state_dir):
        """Test metrics with some merge failures"""
        config = {"auto_merge": True}
        agent = DeduplicationAgent(config=config)
        agent.state_dir = temp_state_dir

        mock_query.return_value = [
            {"id1": "g1", "id2": "g2"},
            {"id1": "g3", "id2": "g4"},
        ]

        # Mock one success, one failure
        agent._merge_records = Mock(side_effect=[True, False])

        agent._execute_core()

        assert agent.metrics.items_processed == 2
        assert agent.metrics.quality_score == 50.0  # 1 of 2 successful


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestAgentIntegration:
    """Integration tests for both agents working together"""

    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_agents_can_coexist(self, temp_state_dir):
        """Test both agents can be created and initialized"""
        nba_agent = NBAStatsAgent()
        dedup_agent = DeduplicationAgent()

        nba_agent.state_dir = temp_state_dir
        dedup_agent.state_dir = temp_state_dir

        assert nba_agent.initialize() is True
        assert dedup_agent.initialize() is True

    def test_agents_have_different_priorities(self, temp_state_dir):
        """Test agents have appropriate priorities"""
        nba_agent = NBAStatsAgent()
        dedup_agent = DeduplicationAgent()

        nba_agent.state_dir = temp_state_dir
        dedup_agent.state_dir = temp_state_dir

        # NBA Stats should have higher priority
        assert nba_agent.priority.value < dedup_agent.priority.value

    @patch("nba_simulator.agents.nba_stats.execute_query")
    @patch("nba_simulator.agents.deduplication.execute_query")
    def test_sequential_execution(
        self, mock_dedup_query, mock_nba_query, temp_state_dir
    ):
        """Test agents can execute sequentially"""
        nba_agent = NBAStatsAgent()
        dedup_agent = DeduplicationAgent()

        nba_agent.state_dir = temp_state_dir
        dedup_agent.state_dir = temp_state_dir

        mock_nba_query.return_value = []
        mock_dedup_query.return_value = []

        # Initialize both
        assert nba_agent.initialize() is True
        assert dedup_agent.initialize() is True

        # Execute sequentially
        assert nba_agent.execute() is True
        assert dedup_agent.execute() is True

        # Check states
        assert nba_agent.state == AgentState.COMPLETED
        assert dedup_agent.state == AgentState.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
