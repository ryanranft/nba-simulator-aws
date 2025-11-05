"""
ESPN Scraper - Async NBA Data Collection from ESPN

Comprehensive scraper for ESPN's NBA data including:
- Game schedules
- Play-by-play data
- Box scores
- Team information
- Player statistics

Features:
- Async HTTP requests with rate limiting
- Automatic error handling with retry
- Data validation before storage
- Multi-format support (JSON, HTML)
- S3 integration for data lake storage

Usage:
    config = ScraperConfig(
        base_url="https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        rate_limit=0.5,  # 2 requests per second
        s3_bucket="nba-sim-raw-data-lake"
    )

    async with ESPNScraper(config) as scraper:
        # Scrape schedule
        games = await scraper.scrape_schedule(season=2024)

        # Scrape play-by-play
        await scraper.scrape_play_by_play(game_id="401234567")

        # Scrape box score
        await scraper.scrape_box_score(game_id="401234567")

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
    ErrorCategory,
    safe_execute,
)
from nba_simulator.etl.validation import (
    validate_game,
    validate_play_by_play,
    validate_box_score,
    DataSource,
    ValidationReport,
)
from nba_simulator.utils import logger


class ESPNScraper(AsyncBaseScraper):
    """
    Async scraper for ESPN NBA data.

    Provides comprehensive data collection from ESPN's APIs with
    built-in error handling, validation, and storage capabilities.
    """

    # ESPN API endpoints
    SCOREBOARD_ENDPOINT = "/scoreboard"
    SUMMARY_ENDPOINT = "/summary"
    PLAYBYPLAY_ENDPOINT = "/playbyplay"
    BOXSCORE_ENDPOINT = "/boxscore"
    TEAMS_ENDPOINT = "/teams"

    def __init__(self, config: ScraperConfig, **kwargs):
        """
        Initialize ESPN scraper.

        Args:
            config: Scraper configuration
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(config, **kwargs)

        # Initialize error handler
        self.error_handler = ScraperErrorHandler(max_retries=config.retry_attempts)

        # ESPN-specific settings
        self.data_source = DataSource.ESPN
        self.headers = {**self.headers, "Accept": "application/json"}

        self.logger.info(f"Initialized ESPN scraper (rate_limit={config.rate_limit}s)")

    async def scrape(self) -> None:
        """
        Main scraping entry point.

        Override to implement complete scraping workflow.
        Example: scrape all games for current season.
        """
        self.logger.info("Starting ESPN scrape...")

        # Get current season
        current_year = datetime.now().year
        season = current_year if datetime.now().month >= 10 else current_year - 1

        # Scrape schedule
        games = await self.scrape_schedule(season=season)
        self.logger.info(f"Found {len(games)} games for season {season}")

        # Scrape detailed data for recent games
        for game in games[:10]:  # Limit to 10 most recent for demo
            game_id = game.get("id")
            if game_id:
                await self.scrape_game_details(game_id)

    async def scrape_schedule(
        self, season: Optional[int] = None, date_filter: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape game schedule from ESPN.

        Args:
            season: Season year (e.g., 2024 for 2024-25 season)
            date_filter: Optional date to filter games

        Returns:
            List of game dictionaries
        """
        self.logger.info(f"Scraping schedule (season={season}, date={date_filter})")

        # Build URL
        url = f"{self.config.base_url}{self.SCOREBOARD_ENDPOINT}"
        params = {}

        if date_filter:
            params["dates"] = date_filter.strftime("%Y%m%d")

        # Fetch schedule with error handling
        async def fetch_schedule():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await self.error_handler.retry_with_backoff(
            fetch_schedule, metadata={"url": url, "season": season}
        )

        if not data:
            self.logger.warning("No schedule data retrieved")
            return []

        # Extract games
        games = self._extract_games_from_scoreboard(data)

        # Validate games
        valid_games = []
        for game in games:
            report = validate_game(game, source=self.data_source)
            if report.is_valid:
                valid_games.append(game)
            else:
                self.logger.warning(f"Invalid game data: {game.get('id')}")
                report.log_results()

        # Store to S3/local
        if valid_games:
            season_str = str(season) if season else datetime.now().year
            filename = f"schedule_{season_str}_{datetime.now().strftime('%Y%m%d')}.json"
            await self.store_data(
                valid_games, filename, subdir=f"espn/schedules/{season_str}"
            )

        self.logger.info(f"Scraped {len(valid_games)}/{len(games)} valid games")
        return valid_games

    async def scrape_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape complete game details (summary, play-by-play, box score).

        Args:
            game_id: ESPN game ID

        Returns:
            Dictionary with all game data or None on error
        """
        self.logger.info(f"Scraping game details: {game_id}")

        game_data = {
            "game_id": game_id,
            "summary": None,
            "play_by_play": None,
            "box_score": None,
        }

        # Scrape summary
        summary = await self.scrape_game_summary(game_id)
        if summary:
            game_data["summary"] = summary

        # Scrape play-by-play
        pbp = await self.scrape_play_by_play(game_id)
        if pbp:
            game_data["play_by_play"] = pbp

        # Scrape box score
        box_score = await self.scrape_box_score(game_id)
        if box_score:
            game_data["box_score"] = box_score

        # Store complete game data
        if any(game_data.values()):
            filename = f"game_{game_id}_{datetime.now().strftime('%Y%m%d')}.json"
            await self.store_data(
                game_data, filename, subdir=f"espn/games/{game_id[:4]}"  # Group by year
            )

        return game_data

    async def scrape_game_summary(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape game summary data.

        Args:
            game_id: ESPN game ID

        Returns:
            Game summary dictionary or None on error
        """
        url = f"{self.config.base_url}{self.SUMMARY_ENDPOINT}"
        params = {"event": game_id}

        async def fetch_summary():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await safe_execute(
            fetch_summary,
            max_retries=self.config.retry_attempts,
            metadata={"game_id": game_id, "endpoint": "summary"},
        )

        if data:
            self.logger.debug(f"Retrieved summary for game {game_id}")

        return data

    async def scrape_play_by_play(self, game_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape play-by-play data for a game.

        Args:
            game_id: ESPN game ID

        Returns:
            List of play dictionaries or None on error
        """
        self.logger.info(f"Scraping play-by-play: {game_id}")

        url = f"{self.config.base_url}{self.PLAYBYPLAY_ENDPOINT}"
        params = {"event": game_id}

        async def fetch_pbp():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await self.error_handler.retry_with_backoff(
            fetch_pbp, metadata={"game_id": game_id, "endpoint": "playbyplay"}
        )

        if not data:
            return None

        # Extract plays
        plays = self._extract_plays_from_pbp(data, game_id)

        # Validate plays
        valid_plays = []
        for play in plays:
            report = validate_play_by_play(play, source=self.data_source)
            if report.is_valid:
                valid_plays.append(play)
            elif report.has_warnings:
                # Include plays with only warnings
                valid_plays.append(play)

        # Store play-by-play data
        if valid_plays:
            filename = f"pbp_{game_id}.json"
            await self.store_data(
                valid_plays, filename, subdir=f"espn/play_by_play/{game_id[:4]}"
            )

        self.logger.info(f"Scraped {len(valid_plays)} plays for game {game_id}")
        return valid_plays

    async def scrape_box_score(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape box score data for a game.

        Args:
            game_id: ESPN game ID

        Returns:
            Box score dictionary or None on error
        """
        self.logger.info(f"Scraping box score: {game_id}")

        url = f"{self.config.base_url}{self.BOXSCORE_ENDPOINT}"
        params = {"event": game_id}

        async def fetch_box_score():
            async with self.get_session() as session:
                response = await self.fetch_url(url, params=params, session=session)
                if response:
                    return await self.parse_json_response(response)
                return None

        data = await safe_execute(
            fetch_box_score,
            max_retries=self.config.retry_attempts,
            metadata={"game_id": game_id, "endpoint": "boxscore"},
        )

        if not data:
            return None

        # Extract player stats
        player_stats = self._extract_player_stats(data, game_id)

        # Validate box scores
        valid_stats = []
        for stat in player_stats:
            report = validate_box_score(stat, source=self.data_source)
            if report.is_valid or report.has_warnings:
                valid_stats.append(stat)

        # Store box score data
        if valid_stats:
            filename = f"boxscore_{game_id}.json"
            await self.store_data(
                {"players": valid_stats},
                filename,
                subdir=f"espn/box_scores/{game_id[:4]}",
            )

        self.logger.info(f"Scraped box scores for {len(valid_stats)} players")
        return {"players": valid_stats}

    def _extract_games_from_scoreboard(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Extract game information from scoreboard response.

        Args:
            data: ESPN scoreboard API response

        Returns:
            List of game dictionaries
        """
        games = []

        try:
            events = data.get("events", [])

            for event in events:
                competitions = event.get("competitions", [])
                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get("competitors", [])

                if len(competitors) != 2:
                    continue

                # Extract team info
                home_team = next(
                    (c for c in competitors if c.get("homeAway") == "home"), None
                )
                away_team = next(
                    (c for c in competitors if c.get("homeAway") == "away"), None
                )

                if not home_team or not away_team:
                    continue

                game = {
                    "game_id": event.get("id"),
                    "game_date": event.get("date"),
                    "season": event.get("season", {}).get("year"),
                    "home_team": home_team.get("team", {}).get("abbreviation"),
                    "away_team": away_team.get("team", {}).get("abbreviation"),
                    "home_score": int(home_team.get("score", 0)),
                    "away_score": int(away_team.get("score", 0)),
                    "status": competition.get("status", {}).get("type", {}).get("name"),
                    "venue": competition.get("venue", {}).get("fullName"),
                }

                games.append(game)

        except Exception as e:
            self.logger.error(f"Error extracting games from scoreboard: {e}")

        return games

    def _extract_plays_from_pbp(self, data: Dict, game_id: str) -> List[Dict[str, Any]]:
        """
        Extract individual plays from play-by-play response.

        Args:
            data: ESPN play-by-play API response
            game_id: Game ID

        Returns:
            List of play dictionaries
        """
        plays = []

        try:
            # ESPN PBP structure varies, this is a simplified extraction
            plays_data = data.get("plays", [])

            for play_data in plays_data:
                play = {
                    "game_id": game_id,
                    "play_id": play_data.get("id"),
                    "period": play_data.get("period", {}).get("number"),
                    "time_remaining": play_data.get("clock", {}).get("displayValue"),
                    "description": play_data.get("text", ""),
                    "score_home": play_data.get("homeScore"),
                    "score_away": play_data.get("awayScore"),
                    "play_type": play_data.get("type", {}).get("text"),
                }
                plays.append(play)

        except Exception as e:
            self.logger.error(f"Error extracting plays: {e}")

        return plays

    def _extract_player_stats(self, data: Dict, game_id: str) -> List[Dict[str, Any]]:
        """
        Extract player statistics from box score response.

        Args:
            data: ESPN box score API response
            game_id: Game ID

        Returns:
            List of player stat dictionaries
        """
        player_stats = []

        try:
            teams = data.get("teams", [])

            for team in teams:
                team_abbr = team.get("team", {}).get("abbreviation")
                players = team.get("statistics", [{}])[0].get("athletes", [])

                for player in players:
                    athlete = player.get("athlete", {})
                    stats = player.get("stats", [])

                    # ESPN returns stats as a list of strings
                    # Format varies, this is simplified
                    stat_dict = {
                        "game_id": game_id,
                        "player_id": athlete.get("id"),
                        "player_name": athlete.get("displayName"),
                        "team": team_abbr,
                        "stats": stats,  # Raw stats array
                    }

                    player_stats.append(stat_dict)

        except Exception as e:
            self.logger.error(f"Error extracting player stats: {e}")

        return player_stats

    async def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error handling summary.

        Returns:
            Dictionary with error statistics
        """
        return self.error_handler.get_error_summary()


# Convenience function for quick ESPN scraping
async def scrape_espn_games(
    season: int,
    game_ids: Optional[List[str]] = None,
    output_dir: str = "/tmp/espn_scraper",
    s3_bucket: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to scrape ESPN data.

    Args:
        season: Season year (e.g., 2024)
        game_ids: Optional list of specific game IDs to scrape
        output_dir: Output directory for data
        s3_bucket: Optional S3 bucket for storage

    Returns:
        Dictionary with scraping results
    """
    config = ScraperConfig(
        base_url="https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        rate_limit=0.5,  # 2 req/sec
        timeout=30,
        retry_attempts=3,
        max_concurrent=5,
        s3_bucket=s3_bucket,
        output_dir=output_dir,
    )

    results = {"games_scraped": 0, "plays_scraped": 0, "errors": 0}

    async with ESPNScraper(config) as scraper:
        if game_ids:
            # Scrape specific games
            for game_id in game_ids:
                game_data = await scraper.scrape_game_details(game_id)
                if game_data:
                    results["games_scraped"] += 1
                    if game_data.get("play_by_play"):
                        results["plays_scraped"] += len(game_data["play_by_play"])
        else:
            # Scrape full schedule
            games = await scraper.scrape_schedule(season=season)
            results["games_scraped"] = len(games)

        # Get error summary
        error_summary = await scraper.get_error_summary()
        results["errors"] = error_summary.get("total_errors", 0)

    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        config = ScraperConfig(
            base_url="https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
            rate_limit=0.5,
            output_dir="/tmp/espn_test",
        )

        async with ESPNScraper(config) as scraper:
            # Scrape today's games
            games = await scraper.scrape_schedule()
            print(f"Found {len(games)} games")

            # Scrape first game details
            if games:
                game_id = games[0]["game_id"]
                await scraper.scrape_game_details(game_id)

    asyncio.run(main())
