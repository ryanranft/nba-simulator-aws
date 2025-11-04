"""
Unit Tests for NBA API Scraper

Tests all NBA API scraper functionality including:
- Player statistics scraping (traditional, advanced, tracking)
- Team statistics scraping
- Game details and summaries
- Lineup data
- Shot chart data
- Hustle statistics
- Official NBA.com header handling
- Rate limiting
- Error handling
"""

import pytest
import aiohttp
import asyncio
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, List

# Import scraper components
from nba_simulator.etl.extractors.nba_api import NBAAPIScraper
from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    ErrorCategory
)
from nba_simulator.etl.validation import ValidationReport, DataSource


class TestNBAAPIScraperInitialization:
    """Test NBA API scraper initialization"""

    def test_scraper_initialization(self, nba_api_config):
        """Test that scraper initializes correctly"""
        scraper = NBAAPIScraper(nba_api_config)
        
        assert scraper.config == nba_api_config
        assert scraper.data_source == DataSource.NBA_API
        assert hasattr(scraper, 'PLAYER_STATS')
        assert hasattr(scraper, 'TEAM_STATS')
        assert hasattr(scraper, 'BOX_SCORE_TRADITIONAL')
    
    def test_scraper_inheritance(self, nba_api_config):
        """Test that scraper inherits from AsyncBaseScraper"""
        scraper = NBAAPIScraper(nba_api_config)
        
        assert isinstance(scraper, AsyncBaseScraper)
        assert hasattr(scraper, 'scrape')
        assert hasattr(scraper, 'save_to_s3')
    
    def test_endpoint_configuration(self, nba_api_config):
        """Test that all NBA API endpoints are configured"""
        scraper = NBAAPIScraper(nba_api_config)
        
        expected_endpoints = [
            'SCOREBOARD',
            'PLAYER_STATS',
            'TEAM_STATS',
            'BOX_SCORE_TRADITIONAL',
            'BOX_SCORE_ADVANCED',
            'PLAYER_GAME_LOG',
            'TEAM_GAME_LOG',
            'SHOT_CHART',
            'PLAYER_TRACKING',
            'HUSTLE_STATS'
        ]
        
        for endpoint in expected_endpoints:
            assert hasattr(scraper, endpoint)
            assert isinstance(getattr(scraper, endpoint), str)
    
    def test_season_type_constants(self, nba_api_config):
        """Test that season type constants are defined"""
        scraper = NBAAPIScraper(nba_api_config)
        
        assert hasattr(scraper, 'SEASON_TYPE_REGULAR')
        assert hasattr(scraper, 'SEASON_TYPE_PLAYOFFS')
        assert hasattr(scraper, 'SEASON_TYPE_PRESEASON')
    
    def test_nba_headers_configured(self, nba_api_config):
        """Test that NBA.com required headers are configured"""
        scraper = NBAAPIScraper(nba_api_config)
        
        # NBA API requires specific headers to avoid being blocked
        assert hasattr(scraper, '_get_nba_headers')
        headers = scraper._get_nba_headers()
        
        assert 'User-Agent' in headers
        assert 'Referer' in headers or 'Origin' in headers


class TestNBAAPIPlayerStatsScraping:
    """Test NBA API player statistics scraping"""

    @pytest.mark.asyncio
    async def test_scrape_player_stats_success(
        self, nba_api_scraper, mock_nba_player_stats_response
    ):
        """Test successful player stats scraping"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_player_stats(season="2024-25")
            
            assert isinstance(stats, list)
            assert len(stats) > 0
            assert all('PLAYER_ID' in player for player in stats)
            assert all('PLAYER_NAME' in player for player in stats)
    
    @pytest.mark.asyncio
    async def test_scrape_player_stats_traditional(
        self, nba_api_scraper, mock_nba_player_stats_response
    ):
        """Test scraping traditional player statistics"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_player_stats(
                    season="2024-25",
                    stat_type="traditional"
                )
            
            # Traditional stats should include PTS, REB, AST
            for player in stats:
                assert 'PTS' in player or 'points' in str(player).lower()
    
    @pytest.mark.asyncio
    async def test_scrape_player_stats_advanced(
        self, nba_api_scraper, mock_nba_player_advanced_stats_response
    ):
        """Test scraping advanced player statistics"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_advanced_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_player_stats(
                    season="2024-25",
                    stat_type="advanced"
                )
            
            # Advanced stats should include efficiency metrics
            for player in stats:
                assert 'PIE' in player or 'OFFRTG' in player or \
                       'advanced' in str(player).lower()
    
    @pytest.mark.asyncio
    async def test_scrape_player_game_log(
        self, nba_api_scraper, mock_nba_player_gamelog_response
    ):
        """Test scraping player game log"""
        player_id = "2544"  # LeBron James
        season = "2024-25"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_gamelog_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                games = await nba_api_scraper.scrape_player_game_log(
                    player_id=player_id,
                    season=season
                )
            
            assert isinstance(games, list)
            assert len(games) > 0
            assert all('GAME_ID' in game for game in games)
            assert all('GAME_DATE' in game for game in games)
    
    @pytest.mark.asyncio
    async def test_scrape_player_tracking_data(
        self, nba_api_scraper, mock_nba_player_tracking_response
    ):
        """Test scraping player tracking data"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_tracking_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                tracking = await nba_api_scraper.scrape_player_tracking(
                    season="2024-25"
                )
            
            assert isinstance(tracking, list)
            # Tracking data includes distance, speed, touches, etc.


class TestNBAAPITeamStatsScraping:
    """Test NBA API team statistics scraping"""

    @pytest.mark.asyncio
    async def test_scrape_team_stats_success(
        self, nba_api_scraper, mock_nba_team_stats_response
    ):
        """Test successful team stats scraping"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_team_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_team_stats(season="2024-25")
            
            assert isinstance(stats, list)
            assert len(stats) > 0
            assert all('TEAM_ID' in team for team in stats)
            assert all('TEAM_NAME' in team for team in stats)
    
    @pytest.mark.asyncio
    async def test_scrape_team_stats_traditional(
        self, nba_api_scraper, mock_nba_team_stats_response
    ):
        """Test scraping traditional team statistics"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_team_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_team_stats(
                    season="2024-25",
                    stat_type="traditional"
                )
            
            # Traditional stats
            for team in stats:
                assert 'W' in team or 'L' in team  # Wins/Losses
    
    @pytest.mark.asyncio
    async def test_scrape_team_game_log(
        self, nba_api_scraper, mock_nba_team_gamelog_response
    ):
        """Test scraping team game log"""
        team_id = "1610612747"  # Lakers
        season = "2024-25"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_team_gamelog_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                games = await nba_api_scraper.scrape_team_game_log(
                    team_id=team_id,
                    season=season
                )
            
            assert isinstance(games, list)
            assert len(games) > 0


class TestNBAAPIBoxScoreScraping:
    """Test NBA API box score scraping"""

    @pytest.mark.asyncio
    async def test_scrape_box_score_traditional(
        self, nba_api_scraper, mock_nba_boxscore_traditional_response
    ):
        """Test scraping traditional box score"""
        game_id = "0022400123"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_boxscore_traditional_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                box_score = await nba_api_scraper.scrape_box_score_traditional(
                    game_id
                )
            
            assert isinstance(box_score, dict)
            assert 'PlayerStats' in box_score or 'resultSets' in box_score
    
    @pytest.mark.asyncio
    async def test_scrape_box_score_advanced(
        self, nba_api_scraper, mock_nba_boxscore_advanced_response
    ):
        """Test scraping advanced box score"""
        game_id = "0022400123"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_boxscore_advanced_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                box_score = await nba_api_scraper.scrape_box_score_advanced(
                    game_id
                )
            
            assert isinstance(box_score, dict)
            # Advanced box score includes efficiency metrics
    
    @pytest.mark.asyncio
    async def test_scrape_hustle_stats(
        self, nba_api_scraper, mock_nba_hustle_stats_response
    ):
        """Test scraping hustle statistics"""
        game_id = "0022400123"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_hustle_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                hustle = await nba_api_scraper.scrape_hustle_stats(game_id)
            
            assert isinstance(hustle, dict)
            # Hustle stats include deflections, charges drawn, etc.


class TestNBAAPIShotChartScraping:
    """Test NBA API shot chart scraping"""

    @pytest.mark.asyncio
    async def test_scrape_shot_chart(
        self, nba_api_scraper, mock_nba_shot_chart_response
    ):
        """Test scraping shot chart data"""
        player_id = "2544"
        season = "2024-25"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_shot_chart_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                shots = await nba_api_scraper.scrape_shot_chart(
                    player_id=player_id,
                    season=season
                )
            
            assert isinstance(shots, list)
            assert len(shots) > 0
            # Shot chart includes x, y coordinates and make/miss
            assert all('LOC_X' in shot or 'x' in str(shot).lower() 
                      for shot in shots)
    
    @pytest.mark.asyncio
    async def test_scrape_shot_chart_team(
        self, nba_api_scraper, mock_nba_shot_chart_response
    ):
        """Test scraping team shot chart"""
        team_id = "1610612747"
        season = "2024-25"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_shot_chart_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                shots = await nba_api_scraper.scrape_shot_chart(
                    team_id=team_id,
                    season=season
                )
            
            assert isinstance(shots, list)


class TestNBAAPILineupData:
    """Test NBA API lineup data scraping"""

    @pytest.mark.asyncio
    async def test_scrape_lineup_stats(
        self, nba_api_scraper, mock_nba_lineup_response
    ):
        """Test scraping lineup statistics"""
        season = "2024-25"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_lineup_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                lineups = await nba_api_scraper.scrape_lineup_stats(
                    season=season
                )
            
            assert isinstance(lineups, list)
            # Lineup data includes 5-player combinations
    
    @pytest.mark.asyncio
    async def test_scrape_team_lineups(
        self, nba_api_scraper, mock_nba_lineup_response
    ):
        """Test scraping specific team lineups"""
        team_id = "1610612747"
        season = "2024-25"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_lineup_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                lineups = await nba_api_scraper.scrape_lineup_stats(
                    season=season,
                    team_id=team_id
                )
            
            assert isinstance(lineups, list)


class TestNBAAPIScoreboard:
    """Test NBA API scoreboard scraping"""

    @pytest.mark.asyncio
    async def test_scrape_scoreboard(
        self, nba_api_scraper, mock_nba_scoreboard_response
    ):
        """Test scraping daily scoreboard"""
        game_date = date(2024, 11, 1)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_scoreboard_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                games = await nba_api_scraper.scrape_scoreboard(game_date)
            
            assert isinstance(games, list)
            assert len(games) > 0
            assert all('gameId' in game or 'GAME_ID' in game for game in games)
    
    @pytest.mark.asyncio
    async def test_scrape_scoreboard_today(self, nba_api_scraper, mock_nba_scoreboard_response):
        """Test scraping today's scoreboard"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_scoreboard_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                games = await nba_api_scraper.scrape_scoreboard()
            
            assert isinstance(games, list)


class TestNBAAPISeasonTypes:
    """Test NBA API season type handling"""

    @pytest.mark.asyncio
    async def test_scrape_regular_season_stats(
        self, nba_api_scraper, mock_nba_player_stats_response
    ):
        """Test scraping regular season statistics"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_player_stats(
                    season="2024-25",
                    season_type="Regular Season"
                )
            
            assert isinstance(stats, list)
    
    @pytest.mark.asyncio
    async def test_scrape_playoff_stats(
        self, nba_api_scraper, mock_nba_player_stats_response
    ):
        """Test scraping playoff statistics"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_player_stats(
                    season="2023-24",
                    season_type="Playoffs"
                )
            
            assert isinstance(stats, list)


class TestNBAAPIHeaderHandling:
    """Test NBA API header handling"""

    def test_get_nba_headers(self, nba_api_scraper):
        """Test NBA.com required headers"""
        headers = nba_api_scraper._get_nba_headers()
        
        # NBA API requires specific headers
        assert 'User-Agent' in headers
        assert 'Referer' in headers or 'Origin' in headers
        assert 'Accept' in headers
    
    def test_headers_prevent_blocking(self, nba_api_scraper):
        """Test that headers prevent API blocking"""
        headers = nba_api_scraper._get_nba_headers()
        
        # Should look like a browser request
        user_agent = headers.get('User-Agent', '')
        assert 'Mozilla' in user_agent or 'Chrome' in user_agent


class TestNBAAPIErrorHandling:
    """Test NBA API error handling"""

    @pytest.mark.asyncio
    async def test_http_403_handling(self, nba_api_scraper):
        """Test handling of 403 Forbidden (missing headers)"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 403
            
            async with nba_api_scraper:
                with pytest.raises(aiohttp.ClientError):
                    await nba_api_scraper.scrape_player_stats(season="2024-25")
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, nba_api_scraper):
        """Test handling of rate limit errors"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 429
            
            async with nba_api_scraper:
                # Should retry with backoff
                with pytest.raises(aiohttp.ClientError):
                    await nba_api_scraper.scrape_player_stats(season="2024-25")
    
    @pytest.mark.asyncio
    async def test_invalid_season_format(self, nba_api_scraper):
        """Test handling of invalid season format"""
        invalid_season = "2024"  # Should be "2024-25"
        
        with pytest.raises(ValueError):
            async with nba_api_scraper:
                await nba_api_scraper.scrape_player_stats(season=invalid_season)


class TestNBAAPIDataValidation:
    """Test NBA API data validation"""

    @pytest.mark.asyncio
    async def test_validate_scraped_data(
        self, nba_api_scraper, mock_nba_player_stats_response
    ):
        """Test validation of scraped data"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with nba_api_scraper:
                stats = await nba_api_scraper.scrape_player_stats(
                    season="2024-25",
                    validate=True
                )
            
            # All data should pass validation
            assert all(isinstance(player, dict) for player in stats)


class TestNBAAPIS3Integration:
    """Test NBA API S3 integration"""

    @pytest.mark.asyncio
    async def test_save_to_s3(
        self, nba_api_scraper, mock_nba_player_stats_response
    ):
        """Test saving scraped data to S3"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_nba_player_stats_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            with patch.object(nba_api_scraper, 'save_to_s3') as mock_save:
                async with nba_api_scraper:
                    await nba_api_scraper.scrape_player_stats(
                        season="2024-25",
                        save_s3=True
                    )
                
                mock_save.assert_called()


# Fixtures
@pytest.fixture
def nba_api_config():
    """Provide NBA API scraper configuration"""
    return ScraperConfig(
        base_url="https://stats.nba.com/stats",
        rate_limit=0.6,  # ~100 requests per minute
        s3_bucket="test-nba-bucket",
        max_retries=3,
        timeout=30
    )


@pytest.fixture
def nba_api_scraper(nba_api_config):
    """Provide NBA API scraper instance"""
    return NBAAPIScraper(nba_api_config)


@pytest.fixture
def mock_nba_player_stats_response():
    """Provide mock NBA API player stats response"""
    return {
        "resultSets": [
            {
                "name": "LeagueDashPlayerStats",
                "headers": ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "GP", "PTS", "REB", "AST"],
                "rowSet": [
                    ["2544", "LeBron James", "1610612747", 60, 25.7, 7.3, 7.3],
                    ["1628369", "Jayson Tatum", "1610612738", 65, 26.9, 8.1, 4.9]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_player_advanced_stats_response():
    """Provide mock NBA API advanced player stats response"""
    return {
        "resultSets": [
            {
                "name": "LeagueDashPlayerStats",
                "headers": ["PLAYER_ID", "PLAYER_NAME", "PIE", "OFFRTG", "DEFRTG"],
                "rowSet": [
                    ["2544", "LeBron James", 0.158, 117.2, 110.3]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_player_gamelog_response():
    """Provide mock NBA API player game log response"""
    return {
        "resultSets": [
            {
                "name": "PlayerGameLog",
                "headers": ["GAME_ID", "GAME_DATE", "MATCHUP", "PTS"],
                "rowSet": [
                    ["0022400123", "2024-11-01", "LAL vs. BOS", 28],
                    ["0022400124", "2024-11-03", "LAL @ DEN", 30]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_player_tracking_response():
    """Provide mock NBA API player tracking response"""
    return {
        "resultSets": [
            {
                "name": "PlayerTrackingData",
                "headers": ["PLAYER_ID", "DIST_FEET", "AVG_SPEED"],
                "rowSet": [
                    ["2544", 12500.5, 4.2]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_team_stats_response():
    """Provide mock NBA API team stats response"""
    return {
        "resultSets": [
            {
                "name": "LeagueDashTeamStats",
                "headers": ["TEAM_ID", "TEAM_NAME", "W", "L", "PTS"],
                "rowSet": [
                    ["1610612747", "Los Angeles Lakers", 47, 35, 115.2],
                    ["1610612738", "Boston Celtics", 64, 18, 120.6]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_team_gamelog_response():
    """Provide mock NBA API team game log response"""
    return {
        "resultSets": [
            {
                "name": "TeamGameLog",
                "headers": ["GAME_ID", "GAME_DATE", "MATCHUP", "WL"],
                "rowSet": [
                    ["0022400123", "2024-11-01", "LAL vs. BOS", "L"]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_boxscore_traditional_response():
    """Provide mock NBA API traditional box score response"""
    return {
        "resultSets": [
            {
                "name": "PlayerStats",
                "headers": ["PLAYER_ID", "PLAYER_NAME", "MIN", "PTS"],
                "rowSet": [
                    ["2544", "LeBron James", "35:00", 28]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_boxscore_advanced_response():
    """Provide mock NBA API advanced box score response"""
    return {
        "resultSets": [
            {
                "name": "PlayerStats",
                "headers": ["PLAYER_ID", "PLAYER_NAME", "OFFRTG", "DEFRTG"],
                "rowSet": [
                    ["2544", "LeBron James", 118.5, 108.2]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_hustle_stats_response():
    """Provide mock NBA API hustle stats response"""
    return {
        "resultSets": [
            {
                "name": "HustleStats",
                "headers": ["PLAYER_ID", "DEFLECTIONS", "CHARGES_DRAWN"],
                "rowSet": [
                    ["2544", 3, 1]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_shot_chart_response():
    """Provide mock NBA API shot chart response"""
    return {
        "resultSets": [
            {
                "name": "Shot_Chart_Detail",
                "headers": ["GAME_ID", "PLAYER_ID", "LOC_X", "LOC_Y", "SHOT_MADE_FLAG"],
                "rowSet": [
                    ["0022400123", "2544", 45, 120, 1],
                    ["0022400123", "2544", -30, 180, 0]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_lineup_response():
    """Provide mock NBA API lineup response"""
    return {
        "resultSets": [
            {
                "name": "Lineups",
                "headers": ["GROUP_ID", "GROUP_NAME", "MIN", "PLUS_MINUS"],
                "rowSet": [
                    ["123-456-789-012-345", "James-Davis-Reaves-Russell-Hachimura", 125.5, 8.2]
                ]
            }
        ]
    }


@pytest.fixture
def mock_nba_scoreboard_response():
    """Provide mock NBA API scoreboard response"""
    return {
        "resultSets": [
            {
                "name": "GameHeader",
                "headers": ["GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"],
                "rowSet": [
                    ["0022400123", "1610612747", "1610612738"]
                ]
            }
        ]
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
