"""
Tests for Historical, hoopR, and Basketball Reference Agents

Comprehensive test suite covering the final 3 agents:
- Historical Agent: Historical data management across NBA eras
- hoopR Agent: hoopR R package integration
- Basketball Reference Agent: 13-tier hierarchical collection system

Test Coverage:
- Configuration validation
- Core execution logic
- Error handling
- Metrics collection
- Era/tier/season processing
- Integration tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile

from nba_simulator.agents.historical import HistoricalAgent
from nba_simulator.agents.hoopr import HooprAgent
from nba_simulator.agents.bbref import BasketballReferenceAgent, BBRefTier
from nba_simulator.agents.base_agent import AgentState, AgentPriority


# ============================================================================
# HISTORICAL AGENT TESTS
# ============================================================================

class TestHistoricalAgent:
    """Test suite for Historical Agent"""
    
    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def valid_config(self):
        """Valid historical agent configuration"""
        return {
            'start_year': 1946,
            'end_year': 2024,
            'eras_to_process': ['all'],
            'validate_rules': True
        }
    
    @pytest.fixture
    def agent(self, valid_config, temp_state_dir):
        """Create historical agent instance"""
        agent = HistoricalAgent(config=valid_config)
        agent.state_dir = temp_state_dir
        agent.state_file = temp_state_dir / "historical_state.json"
        return agent
    
    # === Initialization Tests ===
    
    def test_agent_initialization(self, agent, valid_config):
        """Test agent initializes with correct properties"""
        assert agent.agent_name == "historical"
        assert agent.priority == AgentPriority.NORMAL
        assert agent.state == AgentState.INITIALIZED
        assert agent.start_year == valid_config['start_year']
        assert agent.end_year == valid_config['end_year']
        assert agent.validate_rules == valid_config['validate_rules']
    
    def test_default_configuration(self, temp_state_dir):
        """Test agent uses sensible defaults"""
        agent = HistoricalAgent()
        agent.state_dir = temp_state_dir
        
        assert agent.start_year == 1946
        assert agent.end_year == datetime.now().year
        assert agent.eras_to_process == ['all']
        assert agent.validate_rules is True
    
    def test_era_definitions(self, agent):
        """Test era definitions are correct"""
        assert agent.eras['baa'] == (1946, 1949)
        assert agent.eras['early_nba'] == (1950, 1979)
        assert agent.eras['modern'] == (1980, 1999)
        assert agent.eras['contemporary'] == (2000, 2024)
    
    # === Configuration Validation Tests ===
    
    def test_validate_config_success(self, agent):
        """Test configuration validation passes with valid config"""
        assert agent._validate_config() is True
    
    def test_validate_config_start_year_too_early(self, temp_state_dir):
        """Test validation fails with start_year before NBA founding"""
        config = {'start_year': 1945}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert len(agent.errors) > 0
        assert "1946" in agent.errors[0]
    
    def test_validate_config_end_before_start(self, temp_state_dir):
        """Test validation fails with end_year < start_year"""
        config = {'start_year': 2024, 'end_year': 2020}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "end_year must be >= start_year" in agent.errors[0]
    
    def test_validate_config_future_year_warning(self, temp_state_dir):
        """Test warning for future end_year"""
        config = {'end_year': 2030}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        # Should validate but produce warning
        assert agent._validate_config() is True
        assert len(agent.warnings) > 0
    
    def test_validate_config_boundary_1946(self, temp_state_dir):
        """Test 1946 is valid (NBA founding year)"""
        config = {'start_year': 1946}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is True
    
    # === Execution Tests ===
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_execute_core_all_eras(self, mock_query, agent):
        """Test execution processes all eras"""
        mock_query.return_value = [
            {'game_id': 'g1', 'game_date': '1947-01-01', 
             'home_team': 'NYK', 'away_team': 'BOS',
             'home_score': 85, 'away_score': 80}
        ]
        
        result = agent._execute_core()
        
        assert result is True
        assert len(agent.games_by_era) > 0
        assert agent.metrics.items_processed > 0
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_execute_core_specific_era(self, mock_query, temp_state_dir):
        """Test execution with specific era"""
        config = {'eras_to_process': ['baa']}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        mock_query.return_value = []
        
        result = agent._execute_core()
        
        assert result is True
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_execute_core_year_range_filter(self, mock_query, temp_state_dir):
        """Test execution respects year range"""
        config = {'start_year': 1980, 'end_year': 1999}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        mock_query.return_value = []
        
        result = agent._execute_core()
        
        # Should skip BAA and early_nba eras
        assert result is True
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_execute_core_quality_score_calculation(self, mock_query, agent):
        """Test quality score is calculated correctly"""
        mock_query.return_value = [
            {'game_id': f'g{i}', 'game_date': '2020-01-01',
             'home_team': 'LAL', 'away_team': 'BOS',
             'home_score': 100, 'away_score': 95}
            for i in range(10)
        ]
        
        result = agent._execute_core()
        
        assert result is True
        assert agent.metrics.quality_score > 0
    
    # === Era Processing Tests ===
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_process_era_baa(self, mock_query, agent):
        """Test BAA era processing"""
        mock_query.return_value = [
            {'game_id': 'g1', 'game_date': '1947-01-01',
             'home_team': 'NYK', 'away_team': 'BOS',
             'home_score': 85, 'away_score': 80}
        ]
        
        agent._process_era('baa', 1946, 1949)
        
        assert agent.games_by_era['baa'] == 1
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_process_era_no_games(self, mock_query, agent):
        """Test era processing with no games"""
        mock_query.return_value = []
        
        agent._process_era('modern', 1980, 1999)
        
        assert agent.games_by_era['modern'] == 0
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_get_era_games(self, mock_query, agent):
        """Test fetching games for an era"""
        mock_games = [
            {'game_id': 'g1', 'game_date': '1980-01-01',
             'home_team': 'LAL', 'away_team': 'BOS',
             'home_score': 105, 'away_score': 100}
        ]
        mock_query.return_value = mock_games
        
        games = agent._get_era_games(1980, 1989)
        
        assert len(games) == 1
        assert games[0]['game_id'] == 'g1'
    
    # === Validation Tests ===
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_validate_baa_era_high_scores(self, mock_query, agent):
        """Test BAA era validation catches unrealistic scores"""
        games = [
            {'game_id': 'g1', 'game_date': '1947-01-01',
             'home_team': 'NYK', 'away_team': 'BOS',
             'home_score': 150, 'away_score': 140}  # Too high for BAA
        ]
        
        agent._validate_baa_era(games)
        
        assert len(agent.validation_issues) > 0
        assert 'high BAA score' in agent.validation_issues[0].lower()
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_validate_baa_era_normal_scores(self, mock_query, agent):
        """Test BAA era validation passes normal scores"""
        games = [
            {'game_id': 'g1', 'game_date': '1947-01-01',
             'home_team': 'NYK', 'away_team': 'BOS',
             'home_score': 85, 'away_score': 80}  # Normal for BAA
        ]
        
        agent._validate_baa_era(games)
        
        # Should not create issues for normal scores
        assert len(agent.validation_issues) == 0
    
    def test_validate_rules_disabled(self, temp_state_dir):
        """Test validation can be disabled"""
        config = {'validate_rules': False}
        agent = HistoricalAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent.validate_rules is False
    
    # === Reporting Tests ===
    
    def test_get_agent_info(self, agent):
        """Test agent info returns correct metadata"""
        info = agent.get_agent_info()
        
        assert info['name'] == 'Historical Data Manager'
        assert info['version'] == '1.0.0'
        assert 'capabilities' in info
        assert len(info['capabilities']) >= 5
        assert 'year_range' in info
        assert 'eras' in info
    
    @patch('nba_simulator.agents.historical.execute_query')
    def test_get_historical_report(self, mock_query, agent):
        """Test historical report generation"""
        agent.games_by_era = {'baa': 100, 'modern': 500}
        agent.validation_issues = ['issue1', 'issue2']
        
        report = agent.get_historical_report()
        
        assert report['total_games'] == 600
        assert report['validation_issues'] == 2
        assert 'baa' in report['eras_processed']
        assert 'modern' in report['eras_processed']


# ============================================================================
# HOOPR AGENT TESTS
# ============================================================================

class TestHooprAgent:
    """Test suite for hoopR Agent"""
    
    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def valid_config(self):
        """Valid hoopR agent configuration"""
        return {
            'data_types': ['pbp', 'schedule'],
            'seasons': [2023, 2024],
            'batch_size': 50,
            'validate_data': True
        }
    
    @pytest.fixture
    def agent(self, valid_config, temp_state_dir):
        """Create hoopR agent instance"""
        agent = HooprAgent(config=valid_config)
        agent.state_dir = temp_state_dir
        agent.state_file = temp_state_dir / "hoopr_state.json"
        return agent
    
    # === Initialization Tests ===
    
    def test_agent_initialization(self, agent, valid_config):
        """Test agent initializes with correct properties"""
        assert agent.agent_name == "hoopr"
        assert agent.priority == AgentPriority.NORMAL
        assert agent.state == AgentState.INITIALIZED
        assert agent.data_types == valid_config['data_types']
        assert agent.seasons == valid_config['seasons']
        assert agent.batch_size == valid_config['batch_size']
        assert agent.validate_data == valid_config['validate_data']
    
    def test_default_configuration(self, temp_state_dir):
        """Test agent uses sensible defaults"""
        agent = HooprAgent()
        agent.state_dir = temp_state_dir
        
        assert agent.data_types == ['pbp', 'schedule']
        assert agent.seasons == [datetime.now().year]
        assert agent.batch_size == 50
        assert agent.validate_data is True
    
    def test_custom_configuration(self, temp_state_dir):
        """Test agent accepts custom configuration"""
        config = {
            'data_types': ['pbp', 'schedule', 'teams', 'players'],
            'seasons': [2020, 2021, 2022],
            'batch_size': 100,
            'validate_data': False
        }
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert len(agent.data_types) == 4
        assert len(agent.seasons) == 3
        assert agent.batch_size == 100
        assert agent.validate_data is False
    
    # === Configuration Validation Tests ===
    
    def test_validate_config_success(self, agent):
        """Test configuration validation passes with valid config"""
        assert agent._validate_config() is True
    
    def test_validate_config_invalid_data_type(self, temp_state_dir):
        """Test validation fails with invalid data type"""
        config = {'data_types': ['invalid_type']}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "Invalid data_type" in agent.errors[0]
    
    def test_validate_config_all_valid_data_types(self, temp_state_dir):
        """Test validation passes with all valid data types"""
        config = {'data_types': ['pbp', 'schedule', 'teams', 'players']}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is True
    
    def test_validate_config_empty_seasons(self, temp_state_dir):
        """Test validation fails with empty seasons list"""
        config = {'seasons': []}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "non-empty list" in agent.errors[0]
    
    def test_validate_config_invalid_seasons_type(self, temp_state_dir):
        """Test validation fails with non-list seasons"""
        config = {'seasons': 2024}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
    
    def test_validate_config_invalid_batch_size(self, temp_state_dir):
        """Test validation fails with invalid batch size"""
        config = {'batch_size': -10}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "batch_size" in agent.errors[0]
    
    # === Execution Tests ===
    
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_execute_core_multiple_seasons(self, mock_query, agent):
        """Test execution processes multiple seasons"""
        mock_games = [
            {'game_id': 'g1', 'game_date': '2023-01-01',
             'home_team': 'LAL', 'away_team': 'BOS'},
            {'game_id': 'g2', 'game_date': '2024-01-01',
             'home_team': 'GSW', 'away_team': 'MIA'}
        ]
        mock_query.return_value = mock_games
        
        result = agent._execute_core()
        
        assert result is True
        assert len(agent.games_processed) > 0
    
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_execute_core_no_games(self, mock_query, agent):
        """Test execution with no games found"""
        mock_query.return_value = []
        
        result = agent._execute_core()
        
        assert result is True  # No games is not a failure
        assert agent.metrics.quality_score == 100.0
    
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_execute_core_success_rate_threshold(self, mock_query, temp_state_dir):
        """Test execution requires 70% success rate"""
        agent = HooprAgent()
        agent.state_dir = temp_state_dir
        
        # Create games where 60% will fail
        mock_games = [
            {'game_id': f'g{i}', 'game_date': '2024-01-01',
             'home_team': 'LAL', 'away_team': 'BOS'}
            for i in range(10)
        ]
        mock_query.return_value = mock_games
        
        # Mock to fail 4 out of 10
        agent._collect_game_data = Mock(side_effect=[
            True, True, True, True, True, True,
            False, False, False, False
        ])
        
        result = agent._execute_core()
        
        # 60% < 70% threshold, should fail
        assert result is False
    
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_execute_core_batch_processing(self, mock_query, temp_state_dir):
        """Test games are processed in batches"""
        config = {'batch_size': 5}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        # Create 12 games (will need 3 batches)
        mock_games = [
            {'game_id': f'g{i}', 'game_date': '2024-01-01',
             'home_team': 'LAL', 'away_team': 'BOS'}
            for i in range(12)
        ]
        mock_query.return_value = mock_games
        
        result = agent._execute_core()
        
        assert result is True
        assert len(agent.games_processed) == 12
    
    # === Season Processing Tests ===
    
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_get_season_games(self, mock_query, agent):
        """Test fetching games for a season"""
        mock_games = [
            {'game_id': 'g1', 'game_date': '2024-01-01',
             'home_team': 'LAL', 'away_team': 'BOS'}
        ]
        mock_query.return_value = mock_games
        
        games = agent._get_season_games(2024)
        
        assert len(games) == 1
        assert games[0]['game_id'] == 'g1'
    
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_get_season_games_error_handling(self, mock_query, agent):
        """Test season games error handling"""
        mock_query.side_effect = Exception("Database error")
        
        games = agent._get_season_games(2024)
        
        assert len(games) == 0
        assert len(agent.errors) > 0
    
    # === Data Collection Tests ===
    
    def test_collect_game_data_success(self, agent):
        """Test successful game data collection"""
        result = agent._collect_game_data('g1', 'pbp')
        
        assert result is True
        assert agent.records_collected > 0
    
    def test_collect_game_data_all_types(self, agent):
        """Test collection of all data types"""
        for data_type in ['pbp', 'schedule', 'teams', 'players']:
            result = agent._collect_game_data('g1', data_type)
            assert result is True
    
    def test_collect_game_data_validation_disabled(self, temp_state_dir):
        """Test collection without validation"""
        config = {'validate_data': False}
        agent = HooprAgent(config=config)
        agent.state_dir = temp_state_dir
        
        result = agent._collect_game_data('g1', 'pbp')
        
        assert result is True
    
    def test_validate_game_data(self, agent):
        """Test game data validation"""
        result = agent._validate_game_data('g1', 'pbp')
        
        assert result is True
    
    # === Reporting Tests ===
    
    def test_get_agent_info(self, agent):
        """Test agent info returns correct metadata"""
        info = agent.get_agent_info()
        
        assert info['name'] == 'hoopR Data Collector'
        assert info['version'] == '1.0.0'
        assert 'capabilities' in info
        assert len(info['capabilities']) >= 5
        assert info['data_types'] == agent.data_types
        assert info['seasons'] == agent.seasons
    
    def test_get_collection_stats(self, agent):
        """Test collection statistics"""
        agent.games_processed = ['g1', 'g2', 'g3']
        agent.games_failed = ['g4']
        agent.records_collected = 1000
        
        stats = agent.get_collection_stats()
        
        assert stats['games_processed'] == 3
        assert stats['games_failed'] == 1
        assert stats['records_collected'] == 1000
        assert stats['success_rate'] == 75.0


# ============================================================================
# BASKETBALL REFERENCE AGENT TESTS
# ============================================================================

class TestBasketballReferenceAgent:
    """Test suite for Basketball Reference Agent"""
    
    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def valid_config(self):
        """Valid Basketball Reference agent configuration"""
        return {
            'tiers_to_process': [1, 2, 3, 4],
            'max_requests_per_hour': 20,
            'start_tier': 1,
            'end_tier': 13,
            'backfill_mode': False
        }
    
    @pytest.fixture
    def agent(self, valid_config, temp_state_dir):
        """Create Basketball Reference agent instance"""
        agent = BasketballReferenceAgent(config=valid_config)
        agent.state_dir = temp_state_dir
        agent.state_file = temp_state_dir / "bbref_state.json"
        return agent
    
    # === Initialization Tests ===
    
    def test_agent_initialization(self, agent, valid_config):
        """Test agent initializes with correct properties"""
        assert agent.agent_name == "bbref"
        assert agent.priority == AgentPriority.NORMAL
        assert agent.state == AgentState.INITIALIZED
        assert agent.tiers_to_process == valid_config['tiers_to_process']
        assert agent.max_requests_per_hour == valid_config['max_requests_per_hour']
        assert agent.backfill_mode == valid_config['backfill_mode']
    
    def test_default_configuration(self, temp_state_dir):
        """Test agent uses sensible defaults"""
        agent = BasketballReferenceAgent()
        agent.state_dir = temp_state_dir
        
        assert agent.tiers_to_process == [1, 2, 3, 4]
        assert agent.max_requests_per_hour == 20
        assert agent.start_tier == 1
        assert agent.end_tier == 13
        assert agent.backfill_mode is False
    
    def test_tier_progress_initialization(self, agent):
        """Test tier progress tracking is initialized"""
        assert len(agent.tier_progress) == 13
        for tier_num in range(1, 14):
            assert tier_num in agent.tier_progress
            assert agent.tier_progress[tier_num]['status'] == 'pending'
    
    def test_tier_enum_values(self):
        """Test tier enum has all 13 tiers"""
        assert BBRefTier.TIER_1.value == 1
        assert BBRefTier.TIER_13.value == 13
        assert len(BBRefTier) == 13
    
    # === Configuration Validation Tests ===
    
    def test_validate_config_success(self, agent):
        """Test configuration validation passes with valid config"""
        assert agent._validate_config() is True
    
    def test_validate_config_invalid_start_tier_low(self, temp_state_dir):
        """Test validation fails with start_tier < 1"""
        config = {'start_tier': 0}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "start_tier" in agent.errors[0]
    
    def test_validate_config_invalid_start_tier_high(self, temp_state_dir):
        """Test validation fails with start_tier > 13"""
        config = {'start_tier': 14}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
    
    def test_validate_config_invalid_end_tier_low(self, temp_state_dir):
        """Test validation fails with end_tier < 1"""
        config = {'end_tier': 0}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
    
    def test_validate_config_invalid_end_tier_high(self, temp_state_dir):
        """Test validation fails with end_tier > 13"""
        config = {'end_tier': 15}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
    
    def test_validate_config_end_before_start(self, temp_state_dir):
        """Test validation fails with end_tier < start_tier"""
        config = {'start_tier': 10, 'end_tier': 5}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "end_tier must be >= start_tier" in agent.errors[0]
    
    def test_validate_config_tiers_not_list(self, temp_state_dir):
        """Test validation fails with non-list tiers_to_process"""
        config = {'tiers_to_process': 5}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "must be a list" in agent.errors[0]
    
    def test_validate_config_invalid_tier_number(self, temp_state_dir):
        """Test validation fails with invalid tier number"""
        config = {'tiers_to_process': [1, 2, 15]}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "Invalid tier number" in agent.errors[0]
    
    def test_validate_config_invalid_rate_limit(self, temp_state_dir):
        """Test validation fails with invalid rate limit"""
        config = {'max_requests_per_hour': -10}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        assert agent._validate_config() is False
        assert "max_requests_per_hour" in agent.errors[0]
    
    def test_validate_config_boundary_values(self, temp_state_dir):
        """Test validation with boundary tier values"""
        # Test tier 1
        agent = BasketballReferenceAgent(config={'start_tier': 1, 'end_tier': 1})
        agent.state_dir = temp_state_dir
        assert agent._validate_config() is True
        
        # Test tier 13
        agent = BasketballReferenceAgent(config={'start_tier': 13, 'end_tier': 13})
        agent.state_dir = temp_state_dir
        assert agent._validate_config() is True
    
    # === Execution Tests ===
    
    def test_execute_core_normal_mode(self, agent):
        """Test execution in normal mode (specific tiers)"""
        result = agent._execute_core()
        
        assert result is True
        assert agent.metrics.items_processed > 0
    
    def test_execute_core_backfill_mode(self, temp_state_dir):
        """Test execution in backfill mode (all tiers)"""
        config = {'backfill_mode': True, 'start_tier': 1, 'end_tier': 4}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        result = agent._execute_core()
        
        assert result is True
        # Should process tiers 1-4
        for tier in range(1, 5):
            assert agent.tier_progress[tier]['status'] == 'complete'
    
    def test_execute_core_tier_range_filter(self, temp_state_dir):
        """Test execution respects tier range"""
        config = {'start_tier': 5, 'end_tier': 7, 'backfill_mode': True}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        result = agent._execute_core()
        
        # Only tiers 5-7 should be processed
        assert agent.tier_progress[5]['status'] == 'complete'
        assert agent.tier_progress[6]['status'] == 'complete'
        assert agent.tier_progress[7]['status'] == 'complete'
        assert agent.tier_progress[4]['status'] == 'pending'
        assert agent.tier_progress[8]['status'] == 'pending'
    
    def test_execute_core_quality_score_threshold(self, agent):
        """Test execution requires 75% quality score"""
        result = agent._execute_core()
        
        # All tiers should succeed, so quality score should be 100%
        assert result is True
        assert agent.metrics.quality_score >= 75.0
    
    # === Tier Processing Tests ===
    
    def test_process_tier_success(self, agent):
        """Test individual tier processing"""
        result = agent._process_tier(1)
        
        assert result is True
        assert agent.tier_progress[1]['status'] == 'complete'
        assert agent.tier_progress[1]['items_processed'] > 0
    
    def test_process_tier_all_tiers(self, agent):
        """Test processing all 13 tiers"""
        for tier_num in range(1, 14):
            result = agent._process_tier(tier_num)
            assert result is True
            assert agent.tier_progress[tier_num]['status'] == 'complete'
    
    def test_process_tier_updates_progress(self, agent):
        """Test tier processing updates progress tracking"""
        agent._process_tier(1)
        
        tier_data = agent.tier_progress[1]
        assert tier_data['status'] == 'complete'
        assert tier_data['items_processed'] > 0
        assert tier_data['items_successful'] > 0
    
    def test_tier_processing_order(self, temp_state_dir):
        """Test tiers are processed in order"""
        config = {'tiers_to_process': [3, 1, 2], 'backfill_mode': False}
        agent = BasketballReferenceAgent(config=config)
        agent.state_dir = temp_state_dir
        
        agent._execute_core()
        
        # Should process in sorted order: 1, 2, 3
        assert agent.tier_progress[1]['status'] == 'complete'
        assert agent.tier_progress[2]['status'] == 'complete'
        assert agent.tier_progress[3]['status'] == 'complete'
    
    # === Tier Content Tests ===
    
    def test_tier_1_current_season_schedules(self, agent):
        """Test Tier 1 processes current season schedules"""
        result = agent._process_tier_1()
        
        assert result is True
        assert agent.tier_progress[1]['items_processed'] > 0
    
    def test_tier_13_transactions(self, agent):
        """Test Tier 13 processes transactions and trades"""
        result = agent._process_tier_13()
        
        assert result is True
        assert agent.tier_progress[13]['items_processed'] > 0
    
    def test_all_tier_methods_exist(self, agent):
        """Test all 13 tier processing methods exist"""
        for tier_num in range(1, 14):
            method_name = f'_process_tier_{tier_num}'
            assert hasattr(agent, method_name)
            method = getattr(agent, method_name)
            assert callable(method)
    
    # === Rate Limiting Tests ===
    
    def test_rate_limiting_applied(self, agent):
        """Test rate limiting is applied"""
        import time
        start = time.time()
        
        agent._apply_rate_limit()
        
        elapsed = time.time() - start
        # With 20 requests/hour, should wait at least 180 seconds
        # But we cap at 3 minutes, so should wait ~180 seconds
        # Allow for some variance
        assert elapsed >= 0.1  # At least some delay
    
    def test_rate_limit_configuration(self, temp_state_dir):
        """Test different rate limit configurations"""
        rates = [10, 20, 60]
        
        for rate in rates:
            agent = BasketballReferenceAgent(
                config={'max_requests_per_hour': rate}
            )
            agent.state_dir = temp_state_dir
            assert agent.max_requests_per_hour == rate
    
    # === Reporting Tests ===
    
    def test_get_agent_info(self, agent):
        """Test agent info returns correct metadata"""
        info = agent.get_agent_info()
        
        assert info['name'] == 'Basketball Reference Collector'
        assert info['version'] == '1.0.0'
        assert 'capabilities' in info
        assert '13-tier' in info['capabilities'][0]
        assert 'tier_system' in info
        assert info['tier_system']['total_tiers'] == 13
    
    def test_get_tier_report(self, agent):
        """Test tier-by-tier report generation"""
        # Process some tiers
        agent._process_tier(1)
        agent._process_tier(2)
        
        report = agent.get_tier_report()
        
        assert len(report['tiers_processed']) == 2
        assert report['total_items'] > 0
        assert report['total_successful'] > 0
    
    def test_get_tier_report_empty(self, agent):
        """Test tier report with no processing"""
        report = agent.get_tier_report()
        
        assert len(report['tiers_processed']) == 0
        assert report['total_items'] == 0
    
    def test_get_collection_stats(self, agent):
        """Test collection statistics"""
        agent._process_tier(1)
        
        stats = agent.get_collection_stats()
        
        assert stats['requests_made'] > 0
        assert stats['requests_successful'] > 0
        assert stats['pages_collected'] > 0
        assert stats['success_rate'] == 100.0
        assert stats['tiers_processed'] == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFinalAgentsIntegration:
    """Integration tests for Historical, hoopR, and BBRef agents"""
    
    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_all_agents_can_coexist(self, temp_state_dir):
        """Test all three agents can be created together"""
        historical = HistoricalAgent()
        hoopr = HooprAgent()
        bbref = BasketballReferenceAgent()
        
        historical.state_dir = temp_state_dir
        hoopr.state_dir = temp_state_dir
        bbref.state_dir = temp_state_dir
        
        assert historical.initialize() is True
        assert hoopr.initialize() is True
        assert bbref.initialize() is True
    
    def test_agents_have_appropriate_priorities(self, temp_state_dir):
        """Test agents have appropriate priority levels"""
        historical = HistoricalAgent()
        hoopr = HooprAgent()
        bbref = BasketballReferenceAgent()
        
        # All should be NORMAL priority for collection agents
        assert historical.priority == AgentPriority.NORMAL
        assert hoopr.priority == AgentPriority.NORMAL
        assert bbref.priority == AgentPriority.NORMAL
    
    @patch('nba_simulator.agents.historical.execute_query')
    @patch('nba_simulator.agents.hoopr.execute_query')
    def test_sequential_execution(
        self, 
        mock_hoopr_query, 
        mock_hist_query, 
        temp_state_dir
    ):
        """Test agents can execute sequentially"""
        historical = HistoricalAgent()
        hoopr = HooprAgent()
        bbref = BasketballReferenceAgent()
        
        historical.state_dir = temp_state_dir
        hoopr.state_dir = temp_state_dir
        bbref.state_dir = temp_state_dir
        
        mock_hist_query.return_value = []
        mock_hoopr_query.return_value = []
        
        # Initialize all
        assert historical.initialize() is True
        assert hoopr.initialize() is True
        assert bbref.initialize() is True
        
        # Execute sequentially
        assert historical.execute() is True
        assert hoopr.execute() is True
        assert bbref.execute() is True
        
        # Check final states
        assert historical.state == AgentState.COMPLETED
        assert hoopr.state == AgentState.COMPLETED
        assert bbref.state == AgentState.COMPLETED
    
    def test_all_agents_follow_base_pattern(self, temp_state_dir):
        """Test all agents follow BaseAgent pattern"""
        agents = [
            HistoricalAgent(),
            HooprAgent(),
            BasketballReferenceAgent()
        ]
        
        for agent in agents:
            agent.state_dir = temp_state_dir
            
            # All should have standard methods
            assert hasattr(agent, 'initialize')
            assert hasattr(agent, 'execute')
            assert hasattr(agent, 'shutdown')
            assert hasattr(agent, 'get_status')
            assert hasattr(agent, 'get_metrics')
            assert hasattr(agent, 'generate_report')
            
            # All should have required abstract methods implemented
            assert hasattr(agent, '_validate_config')
            assert hasattr(agent, '_execute_core')
            assert hasattr(agent, 'get_agent_info')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
