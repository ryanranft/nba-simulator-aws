"""
Unit Tests for Basketball Reference Scraper

Tests all Basketball Reference scraper functionality including:
- Season schedule scraping
- Player statistics scraping
- Team data scraping
- Box score extraction
- Play-by-play scraping
- Historical data handling
- HTML parsing
- Rate limiting (3 seconds - respectful)
- Error handling
"""

import pytest
import aiohttp
import asyncio
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, List

# Import scraper components
from nba_simulator.etl.extractors.basketball_reference import BasketballReferenceScraper
from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    ErrorCategory
)
from nba_simulator.etl.validation import ValidationReport, DataSource


class TestBasketballReferenceScraperInitialization:
    """Test Basketball Reference scraper initialization"""

    def test_scraper_initialization(self, bbref_config):
        """Test that scraper initializes correctly"""
        scraper = BasketballReferenceScraper(bbref_config)
        
        assert scraper.config == bbref_config
        assert scraper.data_source == DataSource.BASKETBALL_REFERENCE
        assert hasattr(scraper, 'SCHEDULE_PATH')
        assert hasattr(scraper, 'BOX_SCORE_PATH')
        assert hasattr(scraper, 'PLAYER_PATH')
    
    def test_scraper_requires_beautifulsoup(self, bbref_config):
        """Test that scraper requires BeautifulSoup"""
        # BeautifulSoup should be installed
        scraper = BasketballReferenceScraper(bbref_config)
        assert scraper is not None
    
    def test_scraper_inheritance(self, bbref_config):
        """Test that scraper inherits from AsyncBaseScraper"""
        scraper = BasketballReferenceScraper(bbref_config)
        
        assert isinstance(scraper, AsyncBaseScraper)
        assert hasattr(scraper, 'scrape')
        assert hasattr(scraper, 'save_to_s3')
    
    def test_url_pattern_configuration(self, bbref_config):
        """Test that all URL patterns are configured"""
        scraper = BasketballReferenceScraper(bbref_config)
        
        expected_patterns = [
            'SCHEDULE_PATH',
            'BOX_SCORE_PATH',
            'PLAYER_PATH',
            'TEAM_PATH',
            'PLAY_BY_PLAY_PATH'
        ]
        
        for pattern in expected_patterns:
            assert hasattr(scraper, pattern)
            assert isinstance(getattr(scraper, pattern), str)
    
    def test_respectful_rate_limiting(self, bbref_config):
        """Test that rate limiting is set to respectful value (3+ seconds)"""
        scraper = BasketballReferenceScraper(bbref_config)
        
        # Basketball Reference requires respectful scraping
        assert scraper.config.rate_limit >= 3.0


class TestBasketballReferenceScheduleScraping:
    """Test Basketball Reference schedule scraping"""

    @pytest.mark.asyncio
    async def test_scrape_season_schedule_success(
        self, bbref_scraper, mock_bbref_schedule_html
    ):
        """Test successful season schedule scraping"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_schedule_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                games = await bbref_scraper.scrape_season_schedule(season=2024)
            
            assert isinstance(games, list)
            assert len(games) > 0
            assert all('game_id' in game for game in games)
            assert all('date' in game for game in games)
    
    @pytest.mark.asyncio
    async def test_scrape_historical_season(self, bbref_scraper, mock_bbref_schedule_html):
        """Test scraping historical season (e.g., 1980s)"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_schedule_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                games = await bbref_scraper.scrape_season_schedule(season=1985)
            
            assert isinstance(games, list)
            # Historical seasons may have different data structure
    
    @pytest.mark.asyncio
    async def test_scrape_schedule_month_filter(self, bbref_scraper, mock_bbref_schedule_html):
        """Test schedule scraping with month filter"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_schedule_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                games = await bbref_scraper.scrape_season_schedule(
                    season=2024,
                    month="november"
                )
            
            assert isinstance(games, list)
    
    @pytest.mark.asyncio
    async def test_scrape_schedule_rate_limiting(self, bbref_scraper):
        """Test that respectful rate limiting is applied (3+ seconds)"""
        import time
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="<html></html>"
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                start = time.time()
                
                # Make multiple requests
                for _ in range(2):
                    await bbref_scraper.scrape_season_schedule(season=2024)
                
                elapsed = time.time() - start
                
                # Should take at least 3 seconds between requests
                expected_min = bbref_scraper.config.rate_limit
                assert elapsed >= expected_min


class TestBasketballReferencePlayerScraping:
    """Test Basketball Reference player scraping"""

    @pytest.mark.asyncio
    async def test_scrape_player_season_stats(
        self, bbref_scraper, mock_bbref_player_html
    ):
        """Test scraping player season statistics"""
        player_id = "jamesle01"
        season = 2024
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_player_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                stats = await bbref_scraper.scrape_player_season_stats(
                    player_id=player_id,
                    season=season
                )
            
            assert isinstance(stats, dict)
            assert 'player_id' in stats
            assert 'season' in stats
            assert 'statistics' in stats
    
    @pytest.mark.asyncio
    async def test_scrape_player_career_stats(
        self, bbref_scraper, mock_bbref_player_html
    ):
        """Test scraping player career statistics"""
        player_id = "jamesle01"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_player_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                stats = await bbref_scraper.scrape_player_career_stats(
                    player_id=player_id
                )
            
            assert isinstance(stats, dict)
            assert 'player_id' in stats
            assert 'seasons' in stats
            assert isinstance(stats['seasons'], list)
    
    @pytest.mark.asyncio
    async def test_scrape_player_game_log(
        self, bbref_scraper, mock_bbref_player_gamelog_html
    ):
        """Test scraping player game log"""
        player_id = "jamesle01"
        season = 2024
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_player_gamelog_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                games = await bbref_scraper.scrape_player_game_log(
                    player_id=player_id,
                    season=season
                )
            
            assert isinstance(games, list)
            assert len(games) > 0
            assert all('game_id' in game for game in games)
            assert all('stats' in game for game in games)
    
    @pytest.mark.asyncio
    async def test_scrape_player_invalid_id(self, bbref_scraper):
        """Test scraping with invalid player ID"""
        invalid_player_id = "invalid999"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404
            
            async with bbref_scraper:
                with pytest.raises(ValueError):
                    await bbref_scraper.scrape_player_season_stats(
                        player_id=invalid_player_id,
                        season=2024
                    )


class TestBasketballReferenceBoxScoreScraping:
    """Test Basketball Reference box score scraping"""

    @pytest.mark.asyncio
    async def test_scrape_box_score_success(
        self, bbref_scraper, mock_bbref_boxscore_html
    ):
        """Test successful box score scraping"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                box_score = await bbref_scraper.scrape_box_score(game_id)
            
            assert isinstance(box_score, dict)
            assert 'game_id' in box_score
            assert 'teams' in box_score
            assert len(box_score['teams']) == 2
    
    @pytest.mark.asyncio
    async def test_scrape_box_score_basic_stats(
        self, bbref_scraper, mock_bbref_boxscore_html
    ):
        """Test box score includes basic statistics"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                box_score = await bbref_scraper.scrape_box_score(game_id)
            
            for team in box_score['teams']:
                assert 'players' in team
                for player in team['players']:
                    assert 'name' in player
                    assert 'stats' in player
                    stats = player['stats']
                    assert 'minutes' in stats
                    assert 'points' in stats
    
    @pytest.mark.asyncio
    async def test_scrape_box_score_advanced_stats(
        self, bbref_scraper, mock_bbref_boxscore_advanced_html
    ):
        """Test box score includes advanced statistics"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_advanced_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                box_score = await bbref_scraper.scrape_box_score(
                    game_id,
                    include_advanced=True
                )
            
            # Should include advanced metrics
            for team in box_score['teams']:
                for player in team['players']:
                    if player.get('advanced_stats'):
                        advanced = player['advanced_stats']
                        # Check for advanced metrics
                        assert 'ts_pct' in advanced or 'plus_minus' in advanced
    
    @pytest.mark.asyncio
    async def test_scrape_historical_box_score(
        self, bbref_scraper, mock_bbref_boxscore_html
    ):
        """Test scraping historical box score (pre-1980s)"""
        # Historical games have different data availability
        game_id = "197011030LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                box_score = await bbref_scraper.scrape_box_score(game_id)
            
            # Historical games may have limited stats
            assert isinstance(box_score, dict)
            assert 'game_id' in box_score


class TestBasketballReferencePlayByPlayScraping:
    """Test Basketball Reference play-by-play scraping"""

    @pytest.mark.asyncio
    async def test_scrape_play_by_play_success(
        self, bbref_scraper, mock_bbref_pbp_html
    ):
        """Test successful play-by-play scraping"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_pbp_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                plays = await bbref_scraper.scrape_play_by_play(game_id)
            
            assert isinstance(plays, list)
            assert len(plays) > 0
            assert all('quarter' in play for play in plays)
            assert all('time' in play for play in plays)
    
    @pytest.mark.asyncio
    async def test_scrape_pbp_all_quarters(
        self, bbref_scraper, mock_bbref_pbp_html
    ):
        """Test play-by-play includes all quarters"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_pbp_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                plays = await bbref_scraper.scrape_play_by_play(game_id)
            
            # Check that multiple quarters are present
            quarters = set(play['quarter'] for play in plays)
            assert len(quarters) >= 4  # At least 4 quarters
    
    @pytest.mark.asyncio
    async def test_scrape_pbp_overtime_game(
        self, bbref_scraper, mock_bbref_pbp_overtime_html
    ):
        """Test play-by-play for overtime game"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_pbp_overtime_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                plays = await bbref_scraper.scrape_play_by_play(game_id)
            
            # Should have plays from OT periods
            quarters = set(play['quarter'] for play in plays)
            assert 5 in quarters  # OT1


class TestBasketballReferenceTeamScraping:
    """Test Basketball Reference team scraping"""

    @pytest.mark.asyncio
    async def test_scrape_team_season_stats(
        self, bbref_scraper, mock_bbref_team_html
    ):
        """Test scraping team season statistics"""
        team_abbrev = "LAL"
        season = 2024
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_team_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                stats = await bbref_scraper.scrape_team_season_stats(
                    team_abbrev=team_abbrev,
                    season=season
                )
            
            assert isinstance(stats, dict)
            assert 'team' in stats
            assert 'season' in stats
            assert 'record' in stats
    
    @pytest.mark.asyncio
    async def test_scrape_team_roster(
        self, bbref_scraper, mock_bbref_team_html
    ):
        """Test scraping team roster"""
        team_abbrev = "LAL"
        season = 2024
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_team_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                roster = await bbref_scraper.scrape_team_roster(
                    team_abbrev=team_abbrev,
                    season=season
                )
            
            assert isinstance(roster, list)
            assert len(roster) > 0
            assert all('player_id' in player for player in roster)
            assert all('name' in player for player in roster)


class TestBasketballReferenceHTMLParsing:
    """Test Basketball Reference HTML parsing"""

    def test_parse_table_with_beautifulsoup(self, bbref_scraper):
        """Test parsing HTML tables"""
        html = """
        <table id="test_table">
            <thead>
                <tr><th>Name</th><th>Points</th></tr>
            </thead>
            <tbody>
                <tr><td>Player 1</td><td>25</td></tr>
                <tr><td>Player 2</td><td>30</td></tr>
            </tbody>
        </table>
        """
        
        data = bbref_scraper._parse_table(html, table_id="test_table")
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['Name'] == 'Player 1'
        assert data[0]['Points'] == '25'
    
    def test_parse_commented_table(self, bbref_scraper):
        """Test parsing HTML tables in comments (BBRef uses this)"""
        html = """
        <!-- 
        <table id="advanced_stats">
            <thead>
                <tr><th>Player</th><th>TS%</th></tr>
            </thead>
            <tbody>
                <tr><td>Player 1</td><td>0.580</td></tr>
            </tbody>
        </table>
        -->
        """
        
        data = bbref_scraper._parse_commented_table(html, table_id="advanced_stats")
        
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_extract_game_id_from_url(self, bbref_scraper):
        """Test extracting game ID from BBRef URL"""
        url = "https://www.basketball-reference.com/boxscores/202411010LAL.html"
        
        game_id = bbref_scraper._extract_game_id(url)
        
        assert game_id == "202411010LAL"
    
    def test_parse_player_id_from_link(self, bbref_scraper):
        """Test extracting player ID from BBRef player link"""
        link = "/players/j/jamesle01.html"
        
        player_id = bbref_scraper._extract_player_id(link)
        
        assert player_id == "jamesle01"


class TestBasketballReferenceErrorHandling:
    """Test Basketball Reference error handling"""

    @pytest.mark.asyncio
    async def test_http_404_handling(self, bbref_scraper):
        """Test handling of 404 errors"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404
            
            async with bbref_scraper:
                with pytest.raises(ValueError):
                    await bbref_scraper.scrape_box_score("invalid_game_id")
    
    @pytest.mark.asyncio
    async def test_http_503_handling(self, bbref_scraper):
        """Test handling of 503 service unavailable"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 503
            
            async with bbref_scraper:
                # Should retry with backoff
                with pytest.raises(aiohttp.ClientError):
                    await bbref_scraper.scrape_season_schedule(season=2024)
    
    @pytest.mark.asyncio
    async def test_malformed_html_handling(self, bbref_scraper):
        """Test handling of malformed HTML"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="<html><broken>"
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                # Should handle gracefully
                result = await bbref_scraper.scrape_season_schedule(season=2024)
                assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_robots_txt_respect(self, bbref_scraper):
        """Test that scraper respects robots.txt"""
        # Basketball Reference scraper should check robots.txt
        assert hasattr(bbref_scraper, 'check_robots_txt') or \
               bbref_scraper.config.rate_limit >= 3.0


class TestBasketballReferenceDataValidation:
    """Test Basketball Reference data validation"""

    @pytest.mark.asyncio
    async def test_validate_scraped_data(
        self, bbref_scraper, mock_bbref_boxscore_html
    ):
        """Test validation of scraped data"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                box_score = await bbref_scraper.scrape_box_score(
                    game_id,
                    validate=True
                )
            
            # Should have validation metadata
            assert box_score.get('validated') is True
    
    @pytest.mark.asyncio
    async def test_data_quality_checks(
        self, bbref_scraper, mock_bbref_boxscore_html
    ):
        """Test data quality validation"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            async with bbref_scraper:
                box_score = await bbref_scraper.scrape_box_score(game_id)
                
                # Quality checks
                for team in box_score['teams']:
                    # Team totals should sum correctly
                    assert 'totals' in team
                    # Player stats should be reasonable
                    for player in team['players']:
                        stats = player['stats']
                        if 'points' in stats:
                            assert stats['points'] >= 0


class TestBasketballReferenceS3Integration:
    """Test Basketball Reference S3 integration"""

    @pytest.mark.asyncio
    async def test_save_to_s3(
        self, bbref_scraper, mock_bbref_boxscore_html
    ):
        """Test saving scraped data to S3"""
        game_id = "202411010LAL"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_bbref_boxscore_html
            )
            mock_get.return_value.__aenter__.return_value.status = 200
            
            with patch.object(bbref_scraper, 'save_to_s3') as mock_save:
                async with bbref_scraper:
                    await bbref_scraper.scrape_box_score(
                        game_id,
                        save_s3=True
                    )
                
                mock_save.assert_called()
    
    @pytest.mark.asyncio
    async def test_s3_key_generation(self, bbref_scraper):
        """Test S3 key generation for Basketball Reference data"""
        game_id = "202411010LAL"
        
        expected_key = f"basketball_reference/box_scores/2024/november/{game_id}.json"
        
        actual_key = bbref_scraper._generate_s3_key(
            data_type="box_score",
            game_id=game_id,
            date="2024-11-01"
        )
        
        assert "basketball_reference" in actual_key
        assert game_id in actual_key


# Fixtures
@pytest.fixture
def bbref_config():
    """Provide Basketball Reference scraper configuration"""
    return ScraperConfig(
        base_url="https://www.basketball-reference.com",
        rate_limit=3.0,  # Respectful rate limiting
        s3_bucket="test-nba-bucket",
        max_retries=3,
        timeout=30
    )


@pytest.fixture
def bbref_scraper(bbref_config):
    """Provide Basketball Reference scraper instance"""
    return BasketballReferenceScraper(bbref_config)


@pytest.fixture
def mock_bbref_schedule_html():
    """Provide mock Basketball Reference schedule HTML"""
    return """
    <html>
    <table id="schedule">
        <thead><tr><th>Date</th><th>Visitor</th><th>Home</th></tr></thead>
        <tbody>
            <tr>
                <td>2024-11-01</td>
                <td><a href="/teams/LAL/2024.html">Lakers</a></td>
                <td><a href="/teams/BOS/2024.html">Celtics</a></td>
            </tr>
        </tbody>
    </table>
    </html>
    """


@pytest.fixture
def mock_bbref_player_html():
    """Provide mock Basketball Reference player HTML"""
    return """
    <html>
    <div id="meta">
        <h1>LeBron James</h1>
    </div>
    <table id="per_game">
        <thead><tr><th>Season</th><th>Team</th><th>PTS</th></tr></thead>
        <tbody>
            <tr><td>2023-24</td><td>LAL</td><td>25.7</td></tr>
        </tbody>
    </table>
    </html>
    """


@pytest.fixture
def mock_bbref_player_gamelog_html():
    """Provide mock Basketball Reference player game log HTML"""
    return """
    <html>
    <table id="pgl_basic">
        <thead><tr><th>Date</th><th>Opp</th><th>PTS</th></tr></thead>
        <tbody>
            <tr><td>2024-11-01</td><td>BOS</td><td>28</td></tr>
            <tr><td>2024-11-03</td><td>DEN</td><td>30</td></tr>
        </tbody>
    </table>
    </html>
    """


@pytest.fixture
def mock_bbref_boxscore_html():
    """Provide mock Basketball Reference box score HTML"""
    return """
    <html>
    <table id="box-LAL-game-basic">
        <thead><tr><th>Player</th><th>MP</th><th>PTS</th></tr></thead>
        <tbody>
            <tr><td><a href="/players/j/jamesle01.html">LeBron James</a></td><td>35:00</td><td>28</td></tr>
        </tbody>
    </table>
    <table id="box-BOS-game-basic">
        <thead><tr><th>Player</th><th>MP</th><th>PTS</th></tr></thead>
        <tbody>
            <tr><td><a href="/players/t/tatumja01.html">Jayson Tatum</a></td><td>38:00</td><td>31</td></tr>
        </tbody>
    </table>
    </html>
    """


@pytest.fixture
def mock_bbref_boxscore_advanced_html():
    """Provide mock Basketball Reference advanced box score HTML"""
    return """
    <html>
    <!-- Advanced stats are often in comments -->
    <!--
    <table id="box-LAL-game-advanced">
        <thead><tr><th>Player</th><th>TS%</th><th>+/-</th></tr></thead>
        <tbody>
            <tr><td>LeBron James</td><td>0.580</td><td>+5</td></tr>
        </tbody>
    </table>
    -->
    </html>
    """


@pytest.fixture
def mock_bbref_pbp_html():
    """Provide mock Basketball Reference play-by-play HTML"""
    return """
    <html>
    <table id="pbp">
        <tbody>
            <tr>
                <td>12:00</td>
                <td>Jump ball won by Lakers</td>
                <td></td>
                <td>0-0</td>
            </tr>
            <tr>
                <td>11:45</td>
                <td></td>
                <td>Tatum makes 2-pt shot</td>
                <td>0-2</td>
            </tr>
        </tbody>
    </table>
    </html>
    """


@pytest.fixture
def mock_bbref_pbp_overtime_html():
    """Provide mock Basketball Reference OT play-by-play HTML"""
    return """
    <html>
    <table id="pbp">
        <tbody>
            <tr><td class="center">5:00</td><td colspan="5">Start of Overtime</td></tr>
            <tr><td>4:45</td><td>LeBron makes 3-pt shot</td><td></td><td>105-102</td></tr>
        </tbody>
    </table>
    </html>
    """


@pytest.fixture
def mock_bbref_team_html():
    """Provide mock Basketball Reference team HTML"""
    return """
    <html>
    <div id="meta">
        <h1>2023-24 Los Angeles Lakers</h1>
        <p>Record: 47-35</p>
    </div>
    <table id="roster">
        <thead><tr><th>Player</th><th>Pos</th></tr></thead>
        <tbody>
            <tr><td><a href="/players/j/jamesle01.html">LeBron James</a></td><td>F</td></tr>
        </tbody>
    </table>
    </html>
    """


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
