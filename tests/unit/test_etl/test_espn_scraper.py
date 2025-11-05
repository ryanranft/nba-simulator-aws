"""
Unit Tests for ESPN Scraper

Tests all ESPN scraper functionality including:
- Schedule scraping
- Play-by-play data collection
- Box score extraction
- Data validation
- Error handling
- Rate limiting
- S3 integration
"""

import pytest
import aiohttp
import asyncio
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, List

# Import scraper components
from nba_simulator.etl.extractors.espn import ESPNScraper
from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    ErrorCategory,
)
from nba_simulator.etl.validation import ValidationReport, DataSource


class TestESPNScraperInitialization:
    """Test ESPN scraper initialization"""

    def test_scraper_initialization(self, espn_config):
        """Test that scraper initializes correctly"""
        scraper = ESPNScraper(espn_config)

        assert scraper.config == espn_config
        assert scraper.data_source == DataSource.ESPN
        assert hasattr(scraper, "SCOREBOARD_ENDPOINT")
        assert hasattr(scraper, "PLAYBYPLAY_ENDPOINT")

    def test_scraper_inheritance(self, espn_config):
        """Test that scraper inherits from AsyncBaseScraper"""
        scraper = ESPNScraper(espn_config)

        assert isinstance(scraper, AsyncBaseScraper)
        assert hasattr(scraper, "scrape")
        assert hasattr(scraper, "save_to_s3")

    def test_endpoint_configuration(self, espn_config):
        """Test that all ESPN endpoints are configured"""
        scraper = ESPNScraper(espn_config)

        expected_endpoints = [
            "SCOREBOARD_ENDPOINT",
            "SUMMARY_ENDPOINT",
            "PLAYBYPLAY_ENDPOINT",
            "BOXSCORE_ENDPOINT",
            "TEAMS_ENDPOINT",
        ]

        for endpoint in expected_endpoints:
            assert hasattr(scraper, endpoint)
            assert isinstance(getattr(scraper, endpoint), str)

    def test_custom_config_override(self):
        """Test that custom configuration overrides defaults"""
        custom_config = ScraperConfig(
            base_url="https://custom.espn.com",
            rate_limit=0.25,
            s3_bucket="custom-bucket",
        )

        scraper = ESPNScraper(custom_config)

        assert scraper.config.base_url == "https://custom.espn.com"
        assert scraper.config.rate_limit == 0.25
        assert scraper.config.s3_bucket == "custom-bucket"


class TestESPNScheduleScraping:
    """Test ESPN schedule scraping functionality"""

    @pytest.mark.asyncio
    async def test_scrape_schedule_success(
        self, espn_scraper, mock_espn_schedule_response
    ):
        """Test successful schedule scraping"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_schedule_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                games = await espn_scraper.scrape_schedule(season=2024)

            assert isinstance(games, list)
            assert len(games) > 0
            assert all("game_id" in game for game in games)

    @pytest.mark.asyncio
    async def test_scrape_schedule_empty_response(self, espn_scraper):
        """Test schedule scraping with empty response"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"events": []}
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                games = await espn_scraper.scrape_schedule(season=2024)

            assert games == []

    @pytest.mark.asyncio
    async def test_scrape_schedule_specific_date(
        self, espn_scraper, mock_espn_schedule_response
    ):
        """Test schedule scraping for specific date"""
        test_date = date(2024, 11, 1)

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_schedule_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                games = await espn_scraper.scrape_schedule(
                    season=2024, start_date=test_date, end_date=test_date
                )

            assert isinstance(games, list)

    @pytest.mark.asyncio
    async def test_scrape_schedule_rate_limiting(self, espn_scraper):
        """Test that rate limiting is applied"""
        import time

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"events": []}
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                start = time.time()

                # Make multiple requests
                for _ in range(3):
                    await espn_scraper.scrape_schedule(season=2024)

                elapsed = time.time() - start

                # Should take at least rate_limit * (requests - 1)
                expected_min = espn_scraper.config.rate_limit * 2
                assert elapsed >= expected_min


class TestESPNPlayByPlayScraping:
    """Test ESPN play-by-play scraping"""

    @pytest.mark.asyncio
    async def test_scrape_play_by_play_success(
        self, espn_scraper, mock_espn_pbp_response
    ):
        """Test successful play-by-play scraping"""
        game_id = "401234567"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_pbp_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                plays = await espn_scraper.scrape_play_by_play(game_id)

            assert isinstance(plays, list)
            assert len(plays) > 0
            assert all("play_id" in play for play in plays)
            assert all("game_id" in play for play in plays)

    @pytest.mark.asyncio
    async def test_scrape_play_by_play_with_validation(
        self, espn_scraper, mock_espn_pbp_response
    ):
        """Test play-by-play scraping with data validation"""
        game_id = "401234567"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_pbp_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                plays = await espn_scraper.scrape_play_by_play(game_id, validate=True)

            # All plays should pass validation
            assert all(play.get("validated", True) for play in plays)

    @pytest.mark.asyncio
    async def test_scrape_play_by_play_invalid_game_id(self, espn_scraper):
        """Test play-by-play scraping with invalid game ID"""
        invalid_game_id = "invalid_id"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404

            async with espn_scraper:
                with pytest.raises(ValueError):
                    await espn_scraper.scrape_play_by_play(invalid_game_id)

    @pytest.mark.asyncio
    async def test_scrape_play_by_play_save_to_s3(
        self, espn_scraper, mock_espn_pbp_response
    ):
        """Test play-by-play data saved to S3"""
        game_id = "401234567"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_pbp_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            with patch.object(espn_scraper, "save_to_s3") as mock_save:
                async with espn_scraper:
                    await espn_scraper.scrape_play_by_play(game_id, save_s3=True)

                # Verify S3 save was called
                mock_save.assert_called_once()
                call_args = mock_save.call_args
                assert game_id in str(call_args)


class TestESPNBoxScoreScraping:
    """Test ESPN box score scraping"""

    @pytest.mark.asyncio
    async def test_scrape_box_score_success(
        self, espn_scraper, mock_espn_boxscore_response
    ):
        """Test successful box score scraping"""
        game_id = "401234567"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_boxscore_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                box_score = await espn_scraper.scrape_box_score(game_id)

            assert isinstance(box_score, dict)
            assert "game_id" in box_score
            assert "teams" in box_score
            assert len(box_score["teams"]) == 2

    @pytest.mark.asyncio
    async def test_scrape_box_score_player_stats(
        self, espn_scraper, mock_espn_boxscore_response
    ):
        """Test box score includes player statistics"""
        game_id = "401234567"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_boxscore_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                box_score = await espn_scraper.scrape_box_score(game_id)

            # Each team should have players
            for team in box_score["teams"]:
                assert "players" in team
                assert len(team["players"]) > 0

                # Each player should have stats
                for player in team["players"]:
                    assert "player_id" in player
                    assert "stats" in player

    @pytest.mark.asyncio
    async def test_scrape_box_score_team_totals(
        self, espn_scraper, mock_espn_boxscore_response
    ):
        """Test box score includes team totals"""
        game_id = "401234567"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_boxscore_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                box_score = await espn_scraper.scrape_box_score(game_id)

            for team in box_score["teams"]:
                assert "totals" in team
                totals = team["totals"]
                assert "points" in totals
                assert "rebounds" in totals
                assert "assists" in totals


class TestESPNErrorHandling:
    """Test ESPN scraper error handling"""

    @pytest.mark.asyncio
    async def test_http_error_handling(self, espn_scraper):
        """Test handling of HTTP errors"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 500

            async with espn_scraper:
                with pytest.raises(aiohttp.ClientError):
                    await espn_scraper.scrape_schedule(season=2024)

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, espn_scraper):
        """Test handling of network timeouts"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()

            async with espn_scraper:
                with pytest.raises(asyncio.TimeoutError):
                    await espn_scraper.scrape_schedule(season=2024)

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, espn_scraper):
        """Test handling of rate limit errors (429)"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 429

            async with espn_scraper:
                # Should retry with backoff
                with pytest.raises(aiohttp.ClientError):
                    await espn_scraper.scrape_schedule(season=2024)

    @pytest.mark.asyncio
    async def test_malformed_json_handling(self, espn_scraper):
        """Test handling of malformed JSON responses"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                side_effect=ValueError("Invalid JSON")
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                with pytest.raises(ValueError):
                    await espn_scraper.scrape_schedule(season=2024)


class TestESPNDataValidation:
    """Test ESPN data validation"""

    @pytest.mark.asyncio
    async def test_validate_schedule_data(
        self, espn_scraper, mock_espn_schedule_response
    ):
        """Test validation of schedule data"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_schedule_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                games = await espn_scraper.scrape_schedule(season=2024, validate=True)

            # All games should pass validation
            assert all(game.get("validated", True) for game in games)

    @pytest.mark.asyncio
    async def test_validation_report_generation(
        self, espn_scraper, mock_espn_schedule_response
    ):
        """Test that validation reports are generated"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_schedule_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                games = await espn_scraper.scrape_schedule(season=2024, validate=True)
                report = espn_scraper.get_validation_report()

            assert isinstance(report, ValidationReport)
            assert report.total_records > 0

    @pytest.mark.asyncio
    async def test_invalid_data_rejection(self, espn_scraper):
        """Test that invalid data is rejected"""
        invalid_response = {"events": [{"invalid": "data"}]}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=invalid_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            async with espn_scraper:
                games = await espn_scraper.scrape_schedule(season=2024, validate=True)

                # Invalid games should be filtered out
                assert len(games) == 0


class TestESPNS3Integration:
    """Test ESPN scraper S3 integration"""

    @pytest.mark.asyncio
    async def test_save_to_s3(self, espn_scraper, mock_espn_schedule_response):
        """Test saving data to S3"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_schedule_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            with patch.object(espn_scraper, "save_to_s3") as mock_save:
                async with espn_scraper:
                    await espn_scraper.scrape_schedule(season=2024, save_s3=True)

                mock_save.assert_called()

    @pytest.mark.asyncio
    async def test_s3_key_generation(self, espn_scraper):
        """Test S3 key generation for saved data"""
        game_id = "401234567"
        date_str = "20241101"

        expected_key = f"espn/play_by_play/{date_str}/{game_id}.json"

        actual_key = espn_scraper._generate_s3_key(
            data_type="play_by_play", game_id=game_id, date=date_str
        )

        assert actual_key == expected_key

    @pytest.mark.asyncio
    async def test_s3_upload_error_handling(
        self, espn_scraper, mock_espn_schedule_response
    ):
        """Test handling of S3 upload errors"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_espn_schedule_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            with patch.object(espn_scraper, "save_to_s3") as mock_save:
                mock_save.side_effect = Exception("S3 upload failed")

                async with espn_scraper:
                    # Should handle S3 error gracefully
                    games = await espn_scraper.scrape_schedule(
                        season=2024, save_s3=True
                    )

                    # Data should still be returned even if S3 fails
                    assert len(games) > 0


# Fixtures
@pytest.fixture
def espn_config():
    """Provide ESPN scraper configuration"""
    return ScraperConfig(
        base_url="https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        rate_limit=0.5,
        s3_bucket="test-nba-bucket",
        max_retries=3,
        timeout=30,
    )


@pytest.fixture
def espn_scraper(espn_config):
    """Provide ESPN scraper instance"""
    return ESPNScraper(espn_config)


@pytest.fixture
def mock_espn_schedule_response():
    """Provide mock ESPN schedule API response"""
    return {
        "events": [
            {
                "id": "401234567",
                "date": "2024-11-01T00:00:00Z",
                "name": "Los Angeles Lakers vs Boston Celtics",
                "competitions": [
                    {
                        "competitors": [
                            {"team": {"id": "13", "name": "Lakers"}},
                            {"team": {"id": "2", "name": "Celtics"}},
                        ]
                    }
                ],
            }
        ]
    }


@pytest.fixture
def mock_espn_pbp_response():
    """Provide mock ESPN play-by-play API response"""
    return {
        "plays": [
            {
                "id": "play_001",
                "game_id": "401234567",
                "type": "shot",
                "description": "LeBron James makes 2-pt layup",
                "period": 1,
                "time": "11:30",
            },
            {
                "id": "play_002",
                "game_id": "401234567",
                "type": "shot",
                "description": "Jayson Tatum makes 3-pt jumper",
                "period": 1,
                "time": "11:15",
            },
        ]
    }


@pytest.fixture
def mock_espn_boxscore_response():
    """Provide mock ESPN box score API response"""
    return {
        "game_id": "401234567",
        "teams": [
            {
                "team_id": "13",
                "name": "Lakers",
                "totals": {"points": 110, "rebounds": 45, "assists": 28},
                "players": [
                    {
                        "player_id": "1966",
                        "name": "LeBron James",
                        "stats": {"points": 28, "rebounds": 8, "assists": 11},
                    }
                ],
            },
            {
                "team_id": "2",
                "name": "Celtics",
                "totals": {"points": 105, "rebounds": 42, "assists": 25},
                "players": [
                    {
                        "player_id": "4433134",
                        "name": "Jayson Tatum",
                        "stats": {"points": 31, "rebounds": 10, "assists": 5},
                    }
                ],
            },
        ],
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
