"""
Unit Tests for hoopR Scraper

Tests all hoopR scraper functionality including:
- R package integration (via rpy2)
- Subprocess fallback method
- Play-by-play data scraping
- Team schedule scraping
- Player box scores
- R dependency checking
- Error handling (R not installed, rpy2 unavailable)
- Data validation
- ESPN data integration
"""

import pytest
import asyncio
import subprocess
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, AsyncMock, patch, call
from typing import Dict, List
import tempfile
import json

# Import scraper components
from nba_simulator.etl.extractors.hoopr import HoopRScraper
from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    ErrorCategory
)
from nba_simulator.etl.validation import ValidationReport, DataSource


class TestHoopRScraperInitialization:
    """Test hoopR scraper initialization"""

    def test_scraper_initialization(self, hoopr_config):
        """Test that scraper initializes correctly"""
        scraper = HoopRScraper(hoopr_config)
        
        assert scraper.config == hoopr_config
        assert scraper.data_source == DataSource.HOOPR
        assert hasattr(scraper, 'use_rpy2')
    
    def test_scraper_inheritance(self, hoopr_config):
        """Test that scraper inherits from AsyncBaseScraper"""
        scraper = HoopRScraper(hoopr_config)
        
        assert isinstance(scraper, AsyncBaseScraper)
        assert hasattr(scraper, 'scrape')
        assert hasattr(scraper, 'save_to_s3')
    
    def test_rpy2_integration_mode(self, hoopr_config):
        """Test initialization with rpy2 integration"""
        scraper = HoopRScraper(hoopr_config, use_rpy2=True)
        
        # If rpy2 available, should use it
        assert hasattr(scraper, 'use_rpy2')
    
    def test_subprocess_mode(self, hoopr_config):
        """Test initialization with subprocess mode"""
        scraper = HoopRScraper(hoopr_config, use_rpy2=False)
        
        # Should not use rpy2
        assert scraper.use_rpy2 is False
    
    def test_r_dependency_checking(self, hoopr_config):
        """Test that R dependency is checked"""
        scraper = HoopRScraper(hoopr_config)
        
        # Should have method to check R installation
        assert hasattr(scraper, '_check_r_installed') or \
               hasattr(scraper, 'check_dependencies')


class TestHoopRPlayByPlayScraping:
    """Test hoopR play-by-play scraping"""

    @pytest.mark.asyncio
    async def test_scrape_play_by_play_rpy2(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test play-by-play scraping with rpy2"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                plays = await hoopr_scraper_rpy2.scrape_play_by_play(game_id)
            
            assert isinstance(plays, list)
            assert len(plays) > 0
            assert all('game_id' in play for play in plays)
    
    @pytest.mark.asyncio
    async def test_scrape_play_by_play_subprocess(
        self, hoopr_scraper_subprocess, mock_hoopr_pbp_json
    ):
        """Test play-by-play scraping with subprocess"""
        game_id = "401468224"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = mock_hoopr_pbp_json
            mock_run.return_value.returncode = 0
            
            async with hoopr_scraper_subprocess:
                plays = await hoopr_scraper_subprocess.scrape_play_by_play(game_id)
            
            assert isinstance(plays, list)
            assert len(plays) > 0
    
    @pytest.mark.asyncio
    async def test_scrape_play_by_play_all_quarters(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test play-by-play includes all quarters"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                plays = await hoopr_scraper_rpy2.scrape_play_by_play(game_id)
            
            # Should have plays from multiple quarters
            quarters = set(play.get('qtr', 0) for play in plays)
            assert len(quarters) >= 4
    
    @pytest.mark.asyncio
    async def test_scrape_play_by_play_with_validation(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test play-by-play with data validation"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                plays = await hoopr_scraper_rpy2.scrape_play_by_play(
                    game_id,
                    validate=True
                )
            
            # Validated plays should have validation metadata
            assert all(isinstance(play, dict) for play in plays)


class TestHoopRScheduleScraping:
    """Test hoopR schedule scraping"""

    @pytest.mark.asyncio
    async def test_scrape_team_schedule_rpy2(
        self, hoopr_scraper_rpy2, mock_hoopr_schedule_data
    ):
        """Test team schedule scraping with rpy2"""
        team = "LAL"
        season = 2024
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_schedule_data
            
            async with hoopr_scraper_rpy2:
                games = await hoopr_scraper_rpy2.scrape_team_schedule(
                    team=team,
                    season=season
                )
            
            assert isinstance(games, list)
            assert len(games) > 0
            assert all('game_id' in game for game in games)
    
    @pytest.mark.asyncio
    async def test_scrape_team_schedule_subprocess(
        self, hoopr_scraper_subprocess, mock_hoopr_schedule_json
    ):
        """Test team schedule scraping with subprocess"""
        team = "LAL"
        season = 2024
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = mock_hoopr_schedule_json
            mock_run.return_value.returncode = 0
            
            async with hoopr_scraper_subprocess:
                games = await hoopr_scraper_subprocess.scrape_team_schedule(
                    team=team,
                    season=season
                )
            
            assert isinstance(games, list)
    
    @pytest.mark.asyncio
    async def test_scrape_full_season_schedule(
        self, hoopr_scraper_rpy2, mock_hoopr_schedule_data
    ):
        """Test scraping full season schedule"""
        season = 2024
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_schedule_data
            
            async with hoopr_scraper_rpy2:
                games = await hoopr_scraper_rpy2.scrape_season_schedule(
                    season=season
                )
            
            assert isinstance(games, list)
            # Full season should have many games
            assert len(games) > 50


class TestHoopRRosterScraping:
    """Test hoopR roster scraping"""

    @pytest.mark.asyncio
    async def test_scrape_team_roster(
        self, hoopr_scraper_rpy2, mock_hoopr_roster_data
    ):
        """Test team roster scraping"""
        team = "LAL"
        season = 2024
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_roster_data
            
            async with hoopr_scraper_rpy2:
                roster = await hoopr_scraper_rpy2.scrape_team_roster(
                    team=team,
                    season=season
                )
            
            assert isinstance(roster, list)
            assert len(roster) > 0
            assert all('player_id' in player for player in roster)
            assert all('name' in player for player in roster)


class TestHoopRBoxScoreScraping:
    """Test hoopR box score scraping"""

    @pytest.mark.asyncio
    async def test_scrape_box_score(
        self, hoopr_scraper_rpy2, mock_hoopr_boxscore_data
    ):
        """Test box score scraping"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_boxscore_data
            
            async with hoopr_scraper_rpy2:
                box_score = await hoopr_scraper_rpy2.scrape_box_score(game_id)
            
            assert isinstance(box_score, dict)
            assert 'game_id' in box_score
            assert 'teams' in box_score
    
    @pytest.mark.asyncio
    async def test_scrape_box_score_player_stats(
        self, hoopr_scraper_rpy2, mock_hoopr_boxscore_data
    ):
        """Test box score includes player statistics"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_boxscore_data
            
            async with hoopr_scraper_rpy2:
                box_score = await hoopr_scraper_rpy2.scrape_box_score(game_id)
            
            # Should have player stats
            for team in box_score['teams']:
                assert 'players' in team
                assert len(team['players']) > 0


class TestHoopRRIntegration:
    """Test R integration methods"""

    def test_rpy2_available_detection(self, hoopr_config):
        """Test detection of rpy2 availability"""
        scraper = HoopRScraper(hoopr_config)
        
        # Should detect if rpy2 is available
        # (This is environment-dependent)
        assert isinstance(scraper.use_rpy2, bool)
    
    @pytest.mark.asyncio
    async def test_rpy2_r_call(self, hoopr_scraper_rpy2):
        """Test direct R call via rpy2"""
        r_code = 'library(hoopR)'
        
        with patch('rpy2.robjects.r') as mock_r:
            result = hoopr_scraper_rpy2._call_r_function(r_code)
            mock_r.assert_called()
    
    @pytest.mark.asyncio
    async def test_subprocess_r_call(self, hoopr_scraper_subprocess):
        """Test R call via subprocess"""
        r_script = 'library(hoopR); print("test")'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"result": "test"}'
            
            result = await hoopr_scraper_subprocess._call_r_subprocess(r_script)
            
            mock_run.assert_called_once()
            # Should call R script
            call_args = mock_run.call_args[0][0]
            assert 'Rscript' in call_args or 'R' in call_args
    
    def test_r_script_generation(self, hoopr_scraper_subprocess):
        """Test R script generation for subprocess"""
        game_id = "401468224"
        
        script = hoopr_scraper_subprocess._generate_r_script(
            function="nba_pbp",
            game_id=game_id
        )
        
        assert 'library(hoopR)' in script
        assert game_id in script


class TestHoopRDependencyChecking:
    """Test R dependency checking"""

    def test_check_r_installed(self, hoopr_config):
        """Test checking if R is installed"""
        scraper = HoopRScraper(hoopr_config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            is_installed = scraper._check_r_installed()
            
            # Should try to run R --version or similar
            mock_run.assert_called()
    
    def test_check_hoopr_package_installed(self, hoopr_config):
        """Test checking if hoopR package is installed"""
        scraper = HoopRScraper(hoopr_config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'hoopR'
            
            is_installed = scraper._check_hoopr_installed()
            
            assert is_installed is True
    
    def test_fallback_to_espn_if_r_unavailable(self, hoopr_config):
        """Test fallback to direct ESPN API if R unavailable"""
        scraper = HoopRScraper(hoopr_config)
        
        with patch.object(scraper, '_check_r_installed', return_value=False):
            # Should have fallback mechanism
            assert hasattr(scraper, 'fallback_to_espn') or \
                   hasattr(scraper, '_use_espn_fallback')


class TestHoopRErrorHandling:
    """Test hoopR error handling"""

    @pytest.mark.asyncio
    async def test_r_not_installed_error(self, hoopr_scraper_subprocess):
        """Test error when R is not installed"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("R not found")
            
            async with hoopr_scraper_subprocess:
                with pytest.raises(RuntimeError):
                    await hoopr_scraper_subprocess.scrape_play_by_play("401468224")
    
    @pytest.mark.asyncio
    async def test_hoopr_package_not_installed(self, hoopr_scraper_rpy2):
        """Test error when hoopR package not installed"""
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.side_effect = Exception("package 'hoopR' not found")
            
            async with hoopr_scraper_rpy2:
                with pytest.raises(ImportError):
                    await hoopr_scraper_rpy2.scrape_play_by_play("401468224")
    
    @pytest.mark.asyncio
    async def test_r_script_error(self, hoopr_scraper_subprocess):
        """Test handling of R script errors"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Error in R script"
            
            async with hoopr_scraper_subprocess:
                with pytest.raises(RuntimeError):
                    await hoopr_scraper_subprocess.scrape_play_by_play("401468224")
    
    @pytest.mark.asyncio
    async def test_invalid_game_id(self, hoopr_scraper_rpy2):
        """Test handling of invalid game ID"""
        invalid_game_id = "invalid"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.side_effect = Exception("Invalid game ID")
            
            async with hoopr_scraper_rpy2:
                with pytest.raises(ValueError):
                    await hoopr_scraper_rpy2.scrape_play_by_play(invalid_game_id)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, hoopr_scraper_subprocess):
        """Test handling of R script timeout"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("Rscript", 30)
            
            async with hoopr_scraper_subprocess:
                with pytest.raises(TimeoutError):
                    await hoopr_scraper_subprocess.scrape_play_by_play("401468224")


class TestHoopRDataValidation:
    """Test hoopR data validation"""

    @pytest.mark.asyncio
    async def test_validate_play_by_play_data(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test validation of play-by-play data"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                plays = await hoopr_scraper_rpy2.scrape_play_by_play(
                    game_id,
                    validate=True
                )
            
            # All plays should be validated
            assert all(isinstance(play, dict) for play in plays)
    
    @pytest.mark.asyncio
    async def test_data_quality_checks(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test data quality validation"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                plays = await hoopr_scraper_rpy2.scrape_play_by_play(game_id)
            
            # Quality checks
            for play in plays:
                # Should have required fields
                assert 'game_id' in play
                # Times should be valid
                if 'time' in play:
                    assert isinstance(play['time'], (str, int, float))


class TestHoopRESPNCompatibility:
    """Test hoopR compatibility with ESPN data"""

    @pytest.mark.asyncio
    async def test_espn_data_format(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test that hoopR returns ESPN-compatible data format"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                plays = await hoopr_scraper_rpy2.scrape_play_by_play(game_id)
            
            # Should be compatible with ESPN data structure
            assert isinstance(plays, list)
    
    @pytest.mark.asyncio
    async def test_cross_validation_with_espn(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test cross-validation with ESPN data"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            async with hoopr_scraper_rpy2:
                hoopr_plays = await hoopr_scraper_rpy2.scrape_play_by_play(game_id)
            
            # hoopR uses ESPN data, so should be similar structure
            assert len(hoopr_plays) > 0


class TestHoopRS3Integration:
    """Test hoopR S3 integration"""

    @pytest.mark.asyncio
    async def test_save_to_s3(
        self, hoopr_scraper_rpy2, mock_hoopr_pbp_data
    ):
        """Test saving hoopR data to S3"""
        game_id = "401468224"
        
        with patch('rpy2.robjects.r') as mock_r:
            mock_r.return_value = mock_hoopr_pbp_data
            
            with patch.object(hoopr_scraper_rpy2, 'save_to_s3') as mock_save:
                async with hoopr_scraper_rpy2:
                    await hoopr_scraper_rpy2.scrape_play_by_play(
                        game_id,
                        save_s3=True
                    )
                
                mock_save.assert_called()
    
    @pytest.mark.asyncio
    async def test_s3_key_generation(self, hoopr_scraper_rpy2):
        """Test S3 key generation for hoopR data"""
        game_id = "401468224"
        
        expected_key = f"hoopr/play_by_play/{game_id}.json"
        
        actual_key = hoopr_scraper_rpy2._generate_s3_key(
            data_type="play_by_play",
            game_id=game_id
        )
        
        assert "hoopr" in actual_key
        assert game_id in actual_key


class TestHoopRPerformance:
    """Test hoopR performance and optimization"""

    @pytest.mark.asyncio
    async def test_async_execution(self, hoopr_scraper_subprocess):
        """Test that R calls are executed asynchronously"""
        game_id = "401468224"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '[]'
            mock_run.return_value.returncode = 0
            
            async with hoopr_scraper_subprocess:
                # Should be async
                result = await hoopr_scraper_subprocess.scrape_play_by_play(game_id)
                assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, hoopr_scraper_subprocess):
        """Test handling of concurrent R calls"""
        game_ids = ["401468224", "401468225"]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = '[]'
            mock_run.return_value.returncode = 0
            
            async with hoopr_scraper_subprocess:
                # Should handle multiple concurrent calls
                tasks = [
                    hoopr_scraper_subprocess.scrape_play_by_play(gid)
                    for gid in game_ids
                ]
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 2


# Fixtures
@pytest.fixture
def hoopr_config():
    """Provide hoopR scraper configuration"""
    return ScraperConfig(
        base_url="",  # Not used for hoopR
        rate_limit=1.0,
        s3_bucket="test-nba-bucket",
        max_retries=3,
        timeout=60  # R scripts may take longer
    )


@pytest.fixture
def hoopr_scraper_rpy2(hoopr_config):
    """Provide hoopR scraper instance with rpy2 mode"""
    return HoopRScraper(hoopr_config, use_rpy2=True)


@pytest.fixture
def hoopr_scraper_subprocess(hoopr_config):
    """Provide hoopR scraper instance with subprocess mode"""
    return HoopRScraper(hoopr_config, use_rpy2=False)


@pytest.fixture
def mock_hoopr_pbp_data():
    """Provide mock hoopR play-by-play data"""
    return [
        {
            'game_id': '401468224',
            'qtr': 1,
            'time': '12:00',
            'description': 'Jump ball won by LAL',
            'home_score': 0,
            'away_score': 0
        },
        {
            'game_id': '401468224',
            'qtr': 1,
            'time': '11:45',
            'description': 'LeBron James makes 2-pt shot',
            'home_score': 2,
            'away_score': 0
        }
    ]


@pytest.fixture
def mock_hoopr_pbp_json():
    """Provide mock hoopR play-by-play JSON"""
    return json.dumps([
        {'game_id': '401468224', 'qtr': 1, 'time': '12:00'},
        {'game_id': '401468224', 'qtr': 1, 'time': '11:45'}
    ])


@pytest.fixture
def mock_hoopr_schedule_data():
    """Provide mock hoopR schedule data"""
    return [
        {
            'game_id': '401468224',
            'date': '2024-11-01',
            'home_team': 'LAL',
            'away_team': 'BOS'
        },
        {
            'game_id': '401468225',
            'date': '2024-11-03',
            'home_team': 'LAL',
            'away_team': 'DEN'
        }
    ]


@pytest.fixture
def mock_hoopr_schedule_json():
    """Provide mock hoopR schedule JSON"""
    return json.dumps([
        {'game_id': '401468224', 'date': '2024-11-01'},
        {'game_id': '401468225', 'date': '2024-11-03'}
    ])


@pytest.fixture
def mock_hoopr_roster_data():
    """Provide mock hoopR roster data"""
    return [
        {
            'player_id': '2544',
            'name': 'LeBron James',
            'position': 'F',
            'number': '23'
        },
        {
            'player_id': '203076',
            'name': 'Anthony Davis',
            'position': 'F-C',
            'number': '3'
        }
    ]


@pytest.fixture
def mock_hoopr_boxscore_data():
    """Provide mock hoopR box score data"""
    return {
        'game_id': '401468224',
        'teams': [
            {
                'team': 'LAL',
                'players': [
                    {
                        'player_id': '2544',
                        'name': 'LeBron James',
                        'min': 35,
                        'pts': 28,
                        'reb': 8,
                        'ast': 11
                    }
                ]
            },
            {
                'team': 'BOS',
                'players': [
                    {
                        'player_id': '1628369',
                        'name': 'Jayson Tatum',
                        'min': 38,
                        'pts': 31,
                        'reb': 10,
                        'ast': 5
                    }
                ]
            }
        ]
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
