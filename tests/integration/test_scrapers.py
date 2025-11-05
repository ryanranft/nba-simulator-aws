"""
Integration Tests for ETL Scrapers

Tests complete workflow of all scrapers including error handling and validation.
Updated Day 3: Added NBA API and hoopR scraper tests
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from nba_simulator.etl.base import ScraperConfig
from nba_simulator.etl.extractors.espn import ESPNScraper
from nba_simulator.etl.extractors.basketball_reference import BasketballReferenceScraper
from nba_simulator.etl.extractors.nba_api import NBAAPIScraper
from nba_simulator.etl.extractors.hoopr import HoopRScraper
from nba_simulator.etl.validation import DataSource


@pytest.fixture
def espn_config():
    """ESPN scraper configuration for testing"""
    return ScraperConfig(
        base_url="https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        rate_limit=0.1,
        timeout=5,
        retry_attempts=2,
        max_concurrent=2,
        output_dir="/tmp/test_espn",
        dry_run=True,
    )


@pytest.fixture
def bbref_config():
    """Basketball Reference scraper configuration for testing"""
    return ScraperConfig(
        base_url="https://www.basketball-reference.com",
        rate_limit=0.1,
        timeout=5,
        retry_attempts=2,
        max_concurrent=1,
        output_dir="/tmp/test_bbref",
        dry_run=True,
    )


@pytest.fixture
def nba_api_config():
    """NBA API scraper configuration for testing"""
    return ScraperConfig(
        base_url="https://stats.nba.com/stats",
        rate_limit=0.1,
        timeout=5,
        retry_attempts=2,
        max_concurrent=2,
        output_dir="/tmp/test_nba_api",
        dry_run=True,
    )


@pytest.fixture
def hoopr_config():
    """hoopR scraper configuration for testing"""
    return ScraperConfig(
        base_url="",
        rate_limit=0.1,
        timeout=5,
        retry_attempts=2,
        max_concurrent=1,
        output_dir="/tmp/test_hoopr",
        dry_run=True,
    )


class TestESPNScraper:
    """Test ESPN scraper functionality"""

    @pytest.mark.asyncio
    async def test_scraper_initialization(self, espn_config):
        """Test ESPN scraper initializes correctly"""
        async with ESPNScraper(espn_config) as scraper:
            assert scraper.data_source == DataSource.ESPN
            assert scraper.error_handler is not None
            assert scraper.config.rate_limit == 0.1

    @pytest.mark.asyncio
    async def test_scrape_schedule_with_mock_data(self, espn_config):
        """Test schedule scraping with mocked API response"""
        mock_response_data = {
            "events": [
                {
                    "id": "401234567",
                    "date": "2024-11-01T00:00Z",
                    "season": {"year": 2024},
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {"abbreviation": "LAL"},
                                    "score": "110",
                                },
                                {
                                    "homeAway": "away",
                                    "team": {"abbreviation": "GSW"},
                                    "score": "105",
                                },
                            ],
                            "status": {"type": {"name": "STATUS_FINAL"}},
                            "venue": {"fullName": "Crypto.com Arena"},
                        }
                    ],
                }
            ]
        }

        async with ESPNScraper(espn_config) as scraper:
            with patch.object(
                scraper, "fetch_url", new_callable=AsyncMock
            ) as mock_fetch:
                with patch.object(
                    scraper, "parse_json_response", new_callable=AsyncMock
                ) as mock_parse:
                    mock_parse.return_value = mock_response_data

                    games = await scraper.scrape_schedule(season=2024)

                    assert len(games) > 0
                    assert games[0]["game_id"] == "401234567"
                    assert games[0]["home_team"] == "LAL"
                    assert games[0]["away_team"] == "GSW"


class TestBasketballReferenceScraper:
    """Test Basketball Reference scraper functionality"""

    @pytest.mark.asyncio
    async def test_scraper_initialization(self, bbref_config):
        """Test Basketball Reference scraper initializes correctly"""
        async with BasketballReferenceScraper(bbref_config) as scraper:
            assert scraper.data_source == DataSource.BASKETBALL_REFERENCE
            assert scraper.error_handler is not None
            assert scraper.config.rate_limit >= 3.0

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self):
        """Test that Basketball Reference enforces respectful rate limits"""
        config = ScraperConfig(
            base_url="https://www.basketball-reference.com",
            rate_limit=0.5,
            output_dir="/tmp/test_bbref",
            dry_run=True,
        )

        async with BasketballReferenceScraper(config) as scraper:
            assert scraper.config.rate_limit >= 3.0


class TestNBAAPIScraper:
    """Test NBA API scraper functionality"""

    @pytest.mark.asyncio
    async def test_scraper_initialization(self, nba_api_config):
        """Test NBA API scraper initializes correctly"""
        async with NBAAPIScraper(nba_api_config) as scraper:
            assert scraper.data_source == DataSource.NBA_API
            assert scraper.error_handler is not None
            assert "x-nba-stats-token" in scraper.headers
            assert "x-nba-stats-origin" in scraper.headers

    @pytest.mark.asyncio
    async def test_headers_include_nba_requirements(self, nba_api_config):
        """Test that NBA API headers include required fields"""
        async with NBAAPIScraper(nba_api_config) as scraper:
            # NBA API requires specific headers
            assert scraper.headers["Host"] == "stats.nba.com"
            assert scraper.headers["Referer"] == "https://www.nba.com/"
            assert scraper.headers["x-nba-stats-token"] == "true"

    @pytest.mark.asyncio
    async def test_player_stats_with_mock_data(self, nba_api_config):
        """Test player stats scraping with mocked API response"""
        mock_response = {
            "resultSets": [
                {
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS", "REB", "AST"],
                    "rowSet": [
                        [2544, "LeBron James", 25.5, 7.2, 8.1],
                        [201939, "Stephen Curry", 27.3, 4.5, 6.2],
                    ],
                }
            ]
        }

        async with NBAAPIScraper(nba_api_config) as scraper:
            with patch.object(scraper, "fetch_url", new_callable=AsyncMock):
                with patch.object(
                    scraper, "parse_json_response", new_callable=AsyncMock
                ) as mock_parse:
                    mock_parse.return_value = mock_response

                    players = await scraper.scrape_player_stats(season="2024-25")

                    assert len(players) == 2
                    assert players[0]["PLAYER_NAME"] == "LeBron James"
                    assert players[1]["PLAYER_NAME"] == "Stephen Curry"

    @pytest.mark.asyncio
    async def test_extract_stats_from_response(self, nba_api_config):
        """Test NBA API response extraction"""
        mock_data = {
            "resultSets": [
                {
                    "headers": ["ID", "NAME", "VALUE"],
                    "rowSet": [[1, "Test", 100], [2, "Example", 200]],
                }
            ]
        }

        async with NBAAPIScraper(nba_api_config) as scraper:
            stats = scraper._extract_stats_from_response(mock_data)

            assert len(stats) == 2
            assert stats[0]["ID"] == 1
            assert stats[0]["NAME"] == "Test"
            assert stats[0]["VALUE"] == 100


class TestHoopRScraper:
    """Test hoopR scraper functionality"""

    @pytest.mark.asyncio
    async def test_scraper_initialization(self, hoopr_config):
        """Test hoopR scraper initializes correctly"""
        async with HoopRScraper(hoopr_config) as scraper:
            assert scraper.data_source == DataSource.HOOPR
            assert scraper.error_handler is not None
            # R availability depends on system
            assert isinstance(scraper.r_available, bool)

    @pytest.mark.asyncio
    async def test_r_installation_check(self, hoopr_config):
        """Test R installation detection"""
        async with HoopRScraper(hoopr_config) as scraper:
            # Should not raise error even if R not installed
            assert hasattr(scraper, "r_available")

            if scraper.r_available:
                # If R is available, should have integration method
                assert hasattr(scraper, "use_rpy2")

    @pytest.mark.asyncio
    async def test_graceful_handling_without_r(self, hoopr_config):
        """Test graceful handling when R not available"""
        async with HoopRScraper(hoopr_config) as scraper:
            if not scraper.r_available:
                # Should still initialize without error
                result = await scraper.scrape_play_by_play("test_id")
                assert result is None  # Should return None gracefully


class TestScraperIntegration:
    """Integration tests for complete scraping workflows"""

    @pytest.mark.asyncio
    async def test_all_scrapers_extend_base(self):
        """Test that all scrapers properly extend AsyncBaseScraper"""
        from nba_simulator.etl.base import AsyncBaseScraper

        assert issubclass(ESPNScraper, AsyncBaseScraper)
        assert issubclass(BasketballReferenceScraper, AsyncBaseScraper)
        assert issubclass(NBAAPIScraper, AsyncBaseScraper)
        assert issubclass(HoopRScraper, AsyncBaseScraper)

    @pytest.mark.asyncio
    async def test_all_scrapers_have_error_handler(self):
        """Test that all scrapers have error handler integration"""
        configs = [
            ScraperConfig(base_url="https://test.com", output_dir="/tmp", dry_run=True),
            ScraperConfig(base_url="https://test.com", output_dir="/tmp", dry_run=True),
            ScraperConfig(base_url="https://test.com", output_dir="/tmp", dry_run=True),
            ScraperConfig(base_url="", output_dir="/tmp", dry_run=True),
        ]

        scrapers = [
            ESPNScraper(configs[0]),
            BasketballReferenceScraper(configs[1]),
            NBAAPIScraper(configs[2]),
            HoopRScraper(configs[3]),
        ]

        for scraper in scrapers:
            async with scraper:
                assert hasattr(scraper, "error_handler")
                assert scraper.error_handler is not None

    @pytest.mark.asyncio
    async def test_all_scrapers_have_data_source(self):
        """Test that all scrapers have data source set"""
        espn_config = ScraperConfig(
            base_url="https://test.com", output_dir="/tmp", dry_run=True
        )

        async with ESPNScraper(espn_config) as espn:
            assert espn.data_source == DataSource.ESPN

        async with BasketballReferenceScraper(espn_config) as bbref:
            assert bbref.data_source == DataSource.BASKETBALL_REFERENCE

        async with NBAAPIScraper(espn_config) as nba_api:
            assert nba_api.data_source == DataSource.NBA_API

        hoopr_config = ScraperConfig(base_url="", output_dir="/tmp", dry_run=True)
        async with HoopRScraper(hoopr_config) as hoopr:
            assert hoopr.data_source == DataSource.HOOPR


class TestConvenienceFunctions:
    """Test convenience functions for quick scraping"""

    @pytest.mark.asyncio
    async def test_scrape_nba_api_season_function(self):
        """Test scrape_nba_api_season convenience function"""
        from nba_simulator.etl.extractors.nba_api import scrape_nba_api_season

        with patch(
            "nba_simulator.etl.extractors.nba_api.scraper.NBAAPIScraper"
        ) as MockScraper:
            mock_instance = Mock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.scrape_player_stats = AsyncMock(return_value=[{"id": 1}])
            mock_instance.scrape_team_stats = AsyncMock(return_value=[{"id": 1}])
            mock_instance.get_error_summary = AsyncMock(
                return_value={"total_errors": 0}
            )

            MockScraper.return_value = mock_instance

            results = await scrape_nba_api_season(
                season="2024-25", output_dir="/tmp/test"
            )

            assert "players_scraped" in results
            assert "teams_scraped" in results

    @pytest.mark.asyncio
    async def test_scrape_hoopr_season_function(self):
        """Test scrape_hoopr_season convenience function"""
        from nba_simulator.etl.extractors.hoopr import scrape_hoopr_season

        with patch(
            "nba_simulator.etl.extractors.hoopr.scraper.HoopRScraper"
        ) as MockScraper:
            mock_instance = Mock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.r_available = True
            mock_instance.scrape_team_schedule = AsyncMock(return_value=[{"id": 1}])
            mock_instance.get_error_summary = AsyncMock(
                return_value={"total_errors": 0}
            )

            MockScraper.return_value = mock_instance

            results = await scrape_hoopr_season(
                season=2024, teams=["LAL"], output_dir="/tmp/test"
            )

            assert "teams_scraped" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
