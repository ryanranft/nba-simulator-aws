"""
NBA API Scraper - Official NBA Statistics

Comprehensive scraper for NBA.com's official statistics API including:
- Player statistics (traditional, advanced, tracking)
- Team statistics (traditional, advanced, tracking)
- Game statistics and summaries
- Lineup data
- Shot chart data
- Player tracking data
- Hustle statistics

Features:
- Async HTTP requests with rate limiting
- Official NBA.com headers for compatibility
- Automatic error handling with retry
- Data validation before storage
- Structured JSON responses
- Multi-season support

Usage:
    config = ScraperConfig(
        base_url="https://stats.nba.com/stats",
        rate_limit=0.6,  # ~100 requests per minute is safe
        s3_bucket="nba-sim-raw-data-lake"
    )

    async with NBAAPIScraper(config) as scraper:
        # Scrape player stats
        stats = await scraper.scrape_player_stats(season="2024-25")

        # Scrape team stats
        stats = await scraper.scrape_team_stats(season="2024-25")

        # Scrape game details
        details = await scraper.scrape_game_details(game_id="0022400123")

Version: 2.0 (Refactored)
Created: November 2, 2025
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pathlib import Path

from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    safe_execute,
)
from nba_simulator.etl.validation import (
    validate_box_score,
    DataSource,
    ValidationReport,
)
from nba_simulator.utils import logger


class NBAAPIScraper(AsyncBaseScraper):
    """
    Async scraper for NBA.com official statistics API.

    The NBA API requires specific headers to avoid being blocked.
    This scraper handles all the nuances of the official API.
    """

    # NBA API endpoints
    SCOREBOARD = "scoreboardV2"
    PLAYER_STATS = "leaguedashplayerstats"
    TEAM_STATS = "leaguedashteamstats"
    BOX_SCORE_TRADITIONAL = "boxscoretraditionalv2"
    BOX_SCORE_ADVANCED = "boxscoreadvancedv2"
    PLAYER_GAME_LOG = "playergamelog"
    TEAM_GAME_LOG = "teamgamelog"
    SHOT_CHART = "shotchartdetail"
    PLAYER_TRACKING = "playerdashptshotlog"
    HUSTLE_STATS = "hustlestatsboxscore"

    # Season type codes
    SEASON_TYPE_REGULAR = "Regular Season"
    SEASON_TYPE_PLAYOFFS = "Playoffs"
    SEASON_TYPE_PRESEASON = "Pre Season"

    def __init__(self, config: ScraperConfig, **kwargs):
        """
        Initialize NBA API scraper.

        Args:
            config: Scraper configuration
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(config, **kwargs)

        # Initialize error handler
        self.error_handler = ScraperErrorHandler(max_retries=config.retry_attempts)

        # NBA API specific settings
        self.data_source = DataSource.NBA_API

        # Critical: NBA API requires specific headers or it blocks requests
        self.headers = {
            **self.headers,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "stats.nba.com",
            "Origin": "https://www.nba.com",
            "Referer": "https://www.nba.com/",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true",
            "Connection": "keep-alive",
        }

        self.logger.info(
            f"Initialized NBA API scraper (rate_limit={config.rate_limit}s)"
        )

    async def scrape(self) -> None:
        """
        Main scraping entry point.

        Override to implement complete scraping workflow.
        """
        self.logger.info("Starting NBA API scrape...")

        # Scrape current season player stats
        season = "2024-25"
        player_stats = await self.scrape_player_stats(season=season)
        self.logger.info(f"Scraped {len(player_stats)} player records")

    async def scrape_player_stats(
        self,
        season: str = "2024-25",
        season_type: str = SEASON_TYPE_REGULAR,
        per_mode: str = "PerGame",
        measure_type: str = "Base",
    ) -> List[Dict[str, Any]]:
        """
        Scrape league-wide player statistics.

        Args:
            season: Season in format "2024-25"
            season_type: "Regular Season", "Playoffs", or "Pre Season"
            per_mode: "Totals", "PerGame", "Per36", "Per100Possessions"
            measure_type: "Base", "Advanced", "Misc", "Scoring", etc.

        Returns:
            List of player stat dictionaries
        """
        self.logger.info(f"Scraping player stats: {season} ({season_type})")

        # Build parameters
        params = {
            "Season": season,
            "SeasonType": season_type,
            "PerMode": per_mode,
            "MeasureType": measure_type,
            "LeagueID": "00",  # NBA
        }

        # Fetch data
        url = f"{self.config.base_url}/{self.PLAYER_STATS}"

        async def fetch_stats():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await self.error_handler.retry_with_backoff(
            fetch_stats, metadata={"endpoint": "player_stats", "season": season}
        )

        if not data:
            self.logger.warning("No player stats retrieved")
            return []

        # Extract player stats from NBA API response format
        player_stats = self._extract_stats_from_response(data)

        # Store data
        if player_stats:
            filename = (
                f"player_stats_{season.replace('-', '_')}_{measure_type.lower()}.json"
            )
            await self.store_data(
                player_stats,
                filename,
                subdir=f"nba_api/player_stats/{season.split('-')[0]}",
            )

        self.logger.info(f"Scraped {len(player_stats)} player stat records")
        return player_stats

    async def scrape_team_stats(
        self,
        season: str = "2024-25",
        season_type: str = SEASON_TYPE_REGULAR,
        per_mode: str = "PerGame",
        measure_type: str = "Base",
    ) -> List[Dict[str, Any]]:
        """
        Scrape league-wide team statistics.

        Args:
            season: Season in format "2024-25"
            season_type: "Regular Season", "Playoffs", or "Pre Season"
            per_mode: "Totals", "PerGame", "Per36", "Per100Possessions"
            measure_type: "Base", "Advanced", "Misc", "Scoring", etc.

        Returns:
            List of team stat dictionaries
        """
        self.logger.info(f"Scraping team stats: {season} ({season_type})")

        # Build parameters
        params = {
            "Season": season,
            "SeasonType": season_type,
            "PerMode": per_mode,
            "MeasureType": measure_type,
            "LeagueID": "00",
        }

        # Fetch data
        url = f"{self.config.base_url}/{self.TEAM_STATS}"

        async def fetch_stats():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await safe_execute(
            fetch_stats,
            max_retries=self.config.retry_attempts,
            metadata={"endpoint": "team_stats", "season": season},
        )

        if not data:
            return []

        # Extract team stats
        team_stats = self._extract_stats_from_response(data)

        # Store data
        if team_stats:
            filename = (
                f"team_stats_{season.replace('-', '_')}_{measure_type.lower()}.json"
            )
            await self.store_data(
                team_stats,
                filename,
                subdir=f"nba_api/team_stats/{season.split('-')[0]}",
            )

        self.logger.info(f"Scraped {len(team_stats)} team stat records")
        return team_stats

    async def scrape_box_score(
        self, game_id: str, advanced: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape box score for a specific game.

        Args:
            game_id: NBA game ID (e.g., "0022400123")
            advanced: If True, get advanced stats instead of traditional

        Returns:
            Box score dictionary or None on error
        """
        self.logger.info(f"Scraping box score: {game_id} (advanced={advanced})")

        # Choose endpoint
        endpoint = self.BOX_SCORE_ADVANCED if advanced else self.BOX_SCORE_TRADITIONAL

        # Build parameters
        params = {
            "GameID": game_id,
            "StartPeriod": "0",
            "EndPeriod": "10",
            "StartRange": "0",
            "EndRange": "28800",
            "RangeType": "0",
        }

        # Fetch data
        url = f"{self.config.base_url}/{endpoint}"

        async def fetch_box_score():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await safe_execute(
            fetch_box_score,
            max_retries=self.config.retry_attempts,
            metadata={"game_id": game_id, "advanced": advanced},
        )

        if not data:
            return None

        # Extract box score
        box_score = self._extract_box_score_from_response(data, game_id)

        # Validate player stats
        if box_score and "players" in box_score:
            valid_players = []
            for player in box_score["players"]:
                report = validate_box_score(player, source=self.data_source)
                if report.is_valid or report.has_warnings:
                    valid_players.append(player)
            box_score["players"] = valid_players

        # Store box score
        if box_score:
            box_type = "advanced" if advanced else "traditional"
            filename = f"boxscore_{game_id}_{box_type}.json"
            await self.store_data(
                box_score, filename, subdir=f"nba_api/box_scores/{game_id[:4]}"
            )

        return box_score

    async def scrape_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape complete game details including both traditional and advanced stats.

        Args:
            game_id: NBA game ID

        Returns:
            Dictionary with all game data or None on error
        """
        self.logger.info(f"Scraping complete game details: {game_id}")

        game_data = {
            "game_id": game_id,
            "traditional_box_score": None,
            "advanced_box_score": None,
        }

        # Scrape traditional box score
        traditional = await self.scrape_box_score(game_id, advanced=False)
        if traditional:
            game_data["traditional_box_score"] = traditional

        # Scrape advanced box score
        advanced = await self.scrape_box_score(game_id, advanced=True)
        if advanced:
            game_data["advanced_box_score"] = advanced

        # Store complete game data
        if any(game_data.values()):
            filename = f"game_details_{game_id}.json"
            await self.store_data(
                game_data, filename, subdir=f"nba_api/games/{game_id[:4]}"
            )

        return game_data

    async def scrape_player_game_log(
        self,
        player_id: str,
        season: str = "2024-25",
        season_type: str = SEASON_TYPE_REGULAR,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape game log for a specific player.

        Args:
            player_id: NBA player ID (e.g., "2544" for LeBron James)
            season: Season in format "2024-25"
            season_type: "Regular Season", "Playoffs", or "Pre Season"

        Returns:
            List of game log entries or None on error
        """
        self.logger.info(f"Scraping player game log: {player_id} ({season})")

        # Build parameters
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
        }

        # Fetch data
        url = f"{self.config.base_url}/{self.PLAYER_GAME_LOG}"

        async def fetch_log():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await safe_execute(
            fetch_log,
            max_retries=self.config.retry_attempts,
            metadata={"player_id": player_id, "season": season},
        )

        if not data:
            return None

        # Extract game log
        game_log = self._extract_stats_from_response(data)

        # Store data
        if game_log:
            filename = f"player_{player_id}_log_{season.replace('-', '_')}.json"
            await self.store_data(
                game_log, filename, subdir=f"nba_api/player_logs/{season.split('-')[0]}"
            )

        return game_log

    async def scrape_shot_chart(
        self,
        player_id: str,
        season: str = "2024-25",
        season_type: str = SEASON_TYPE_REGULAR,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape shot chart data for a player.

        Args:
            player_id: NBA player ID
            season: Season in format "2024-25"
            season_type: "Regular Season", "Playoffs", or "Pre Season"

        Returns:
            List of shot attempts with locations or None on error
        """
        self.logger.info(f"Scraping shot chart: {player_id} ({season})")

        # Build parameters
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "TeamID": "0",
            "GameID": "",
            "Outcome": "",
            "Location": "",
            "Month": "0",
            "SeasonSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "OpponentTeamID": "0",
            "VsConference": "",
            "VsDivision": "",
            "Position": "",
            "RookieYear": "",
            "GameSegment": "",
            "Period": "0",
            "LastNGames": "0",
            "ContextMeasure": "FGA",
        }

        # Fetch data
        url = f"{self.config.base_url}/{self.SHOT_CHART}"

        data = await safe_execute(
            self._fetch_url_json,
            url,
            params,
            max_retries=self.config.retry_attempts,
            metadata={"player_id": player_id, "season": season},
        )

        if not data:
            return None

        # Extract shot chart data
        shots = self._extract_stats_from_response(data)

        # Store data
        if shots:
            filename = f"shot_chart_{player_id}_{season.replace('-', '_')}.json"
            await self.store_data(
                shots, filename, subdir=f"nba_api/shot_charts/{season.split('-')[0]}"
            )

        return shots

    async def _fetch_url_json(self, url: str, params: Dict) -> Optional[Dict]:
        """Helper to fetch URL and parse JSON"""
        async with self.get_session() as session:
            response = await self.fetch_url(url, params=params, session=session)
            if response:
                return await self.parse_json_response(response)
            return None

    def _extract_stats_from_response(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Extract statistics from NBA API response format.

        NBA API returns data in a specific format:
        {
            "resultSets": [{
                "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS", ...],
                "rowSet": [[2544, "LeBron James", 25.5, ...], ...]
            }]
        }

        Args:
            data: NBA API response

        Returns:
            List of stat dictionaries
        """
        stats = []

        try:
            result_sets = data.get("resultSets", [])
            if not result_sets:
                return stats

            # Usually first result set contains the main data
            result_set = result_sets[0]
            headers = result_set.get("headers", [])
            rows = result_set.get("rowSet", [])

            # Convert to list of dictionaries
            for row in rows:
                stat_dict = dict(zip(headers, row))
                stats.append(stat_dict)

        except Exception as e:
            self.logger.error(f"Error extracting stats from response: {e}")

        return stats

    def _extract_box_score_from_response(
        self, data: Dict, game_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract box score from NBA API response.

        Args:
            data: NBA API box score response
            game_id: Game ID

        Returns:
            Box score dictionary
        """
        try:
            box_score = {"game_id": game_id, "players": []}

            # NBA API box score has multiple result sets
            result_sets = data.get("resultSets", [])

            # PlayerStats is usually in one of the result sets
            for result_set in result_sets:
                name = result_set.get("name", "")
                if "PlayerStats" in name:
                    headers = result_set.get("headers", [])
                    rows = result_set.get("rowSet", [])

                    for row in rows:
                        player_dict = dict(zip(headers, row))
                        box_score["players"].append(player_dict)

            return box_score

        except Exception as e:
            self.logger.error(f"Error extracting box score: {e}")
            return None

    async def get_error_summary(self) -> Dict[str, Any]:
        """Get error handling summary"""
        return self.error_handler.get_error_summary()


# Convenience function
async def scrape_nba_api_season(
    season: str = "2024-25",
    output_dir: str = "/tmp/nba_api_scraper",
    s3_bucket: Optional[str] = None,
    include_advanced: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to scrape NBA API season data.

    Args:
        season: Season in format "2024-25"
        output_dir: Output directory
        s3_bucket: Optional S3 bucket
        include_advanced: Include advanced stats

    Returns:
        Dictionary with scraping results
    """
    config = ScraperConfig(
        base_url="https://stats.nba.com/stats",
        rate_limit=0.6,  # ~100 requests per minute
        timeout=30,
        retry_attempts=3,
        max_concurrent=3,
        s3_bucket=s3_bucket,
        output_dir=output_dir,
    )

    results = {"players_scraped": 0, "teams_scraped": 0, "errors": 0}

    async with NBAAPIScraper(config) as scraper:
        # Scrape player stats
        players = await scraper.scrape_player_stats(season=season)
        results["players_scraped"] = len(players)

        # Scrape team stats
        teams = await scraper.scrape_team_stats(season=season)
        results["teams_scraped"] = len(teams)

        # Scrape advanced stats if requested
        if include_advanced:
            await scraper.scrape_player_stats(season=season, measure_type="Advanced")
            await scraper.scrape_team_stats(season=season, measure_type="Advanced")

        # Get error summary
        error_summary = await scraper.get_error_summary()
        results["errors"] = error_summary.get("total_errors", 0)

    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        config = ScraperConfig(
            base_url="https://stats.nba.com/stats",
            rate_limit=0.6,
            output_dir="/tmp/nba_api_test",
        )

        async with NBAAPIScraper(config) as scraper:
            # Scrape current season player stats
            players = await scraper.scrape_player_stats(season="2024-25")
            print(f"Scraped {len(players)} players")

    asyncio.run(main())
