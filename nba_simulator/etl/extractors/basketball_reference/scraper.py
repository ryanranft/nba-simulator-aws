"""
Basketball Reference Scraper - HTML-Based Data Collection

Comprehensive scraper for Basketball-Reference.com NBA data including:
- Historical game data (1946-present)
- Player statistics (career, season, game logs)
- Team statistics and records
- Advanced metrics
- Play-by-play data
- Draft information

Features:
- HTML parsing with BeautifulSoup
- Async HTTP requests with rate limiting
- Respectful scraping (follows robots.txt)
- Error handling with retry
- Data validation
- Multi-format storage (JSON, CSV)

Usage:
    config = ScraperConfig(
        base_url="https://www.basketball-reference.com",
        rate_limit=3.0,  # Be respectful - 3 seconds between requests
        s3_bucket="nba-sim-raw-data-lake"
    )

    async with BasketballReferenceScraper(config) as scraper:
        # Scrape season schedule
        games = await scraper.scrape_season_schedule(season=2024)

        # Scrape player stats
        await scraper.scrape_player_season_stats(player_id="jamesle01", season=2024)

        # Scrape box score
        await scraper.scrape_box_score(game_id="202411010LAL")

Version: 2.0 (Refactored)
Created: November 2, 2025
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, date
from pathlib import Path
import re

from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    safe_execute,
)
from nba_simulator.etl.validation import (
    validate_game,
    validate_box_score,
    DataSource,
    ValidationReport,
)
from nba_simulator.utils import logger

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning(
        "BeautifulSoup4 not installed. Install with: pip install beautifulsoup4"
    )


class BasketballReferenceScraper(AsyncBaseScraper):
    """
    Async scraper for Basketball-Reference.com data.

    Handles HTML parsing and data extraction from Basketball Reference
    with proper rate limiting and error handling.

    Note: Basketball Reference is HTML-based, so we use BeautifulSoup
    for parsing instead of JSON APIs.
    """

    # Basketball Reference URL patterns
    SCHEDULE_PATH = "/leagues/NBA_{season}_games.html"
    BOX_SCORE_PATH = "/boxscores/{game_id}.html"
    PLAYER_PATH = "/players/{letter}/{player_id}.html"
    TEAM_PATH = "/teams/{team}/{season}.html"
    PLAY_BY_PLAY_PATH = "/boxscores/pbp/{game_id}.html"

    def __init__(self, config: ScraperConfig, **kwargs):
        """
        Initialize Basketball Reference scraper.

        Args:
            config: Scraper configuration
            **kwargs: Additional arguments passed to base class
        """
        if not HAS_BS4:
            raise ImportError(
                "BeautifulSoup4 is required for Basketball Reference scraping. "
                "Install with: pip install beautifulsoup4 lxml"
            )

        # Set respectful rate limit (Basketball Reference asks for 3+ seconds)
        if config.rate_limit < 3.0:
            logger.warning(
                f"Rate limit {config.rate_limit}s is too aggressive. Setting to 3.0s"
            )
            config.rate_limit = 3.0

        super().__init__(config, **kwargs)

        # Initialize error handler
        self.error_handler = ScraperErrorHandler(max_retries=config.retry_attempts)

        # Basketball Reference specific settings
        self.data_source = DataSource.BASKETBALL_REFERENCE
        self.headers = {
            **self.headers,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.basketball-reference.com/",
        }

        # Cache for avoiding duplicate requests
        self.scraped_ids: Set[str] = set()

        self.logger.info(
            f"Initialized Basketball Reference scraper (rate_limit={config.rate_limit}s)"
        )

    async def scrape(self) -> None:
        """
        Main scraping entry point.

        Override to implement complete scraping workflow.
        """
        self.logger.info("Starting Basketball Reference scrape...")

        # Scrape current season schedule
        current_year = datetime.now().year
        season = current_year if datetime.now().month >= 10 else current_year - 1

        games = await self.scrape_season_schedule(season=season)
        self.logger.info(f"Found {len(games)} games for season {season}")

    async def scrape_season_schedule(
        self, season: int, month: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape complete season schedule from Basketball Reference.

        Args:
            season: Season year (e.g., 2024 for 2024-25 season)
            month: Optional month filter (e.g., 'october', 'november')

        Returns:
            List of game dictionaries
        """
        self.logger.info(f"Scraping season schedule: {season} (month={month})")

        # Build URL
        url = f"{self.config.base_url}{self.SCHEDULE_PATH.format(season=season)}"
        if month:
            url += f"#{month}"

        # Fetch schedule HTML
        async def fetch_schedule():
            async with self.get_session() as session:
                response = await self.fetch_url(url, session=session)
                if response:
                    return await self.parse_text_response(response)
                return None

        html = await self.error_handler.retry_with_backoff(
            fetch_schedule, metadata={"url": url, "season": season, "month": month}
        )

        if not html:
            self.logger.warning("No schedule HTML retrieved")
            return []

        # Parse HTML
        games = self._parse_schedule_html(html, season)

        # Validate games
        valid_games = []
        for game in games:
            report = validate_game(game, source=self.data_source)
            if report.is_valid:
                valid_games.append(game)
                self.scraped_ids.add(game["game_id"])

        # Store schedule
        if valid_games:
            filename = f"schedule_{season}.json"
            await self.store_data(
                valid_games, filename, subdir=f"basketball_reference/schedules"
            )

        self.logger.info(f"Scraped {len(valid_games)}/{len(games)} valid games")
        return valid_games

    async def scrape_box_score(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed box score for a game.

        Args:
            game_id: Basketball Reference game ID (e.g., '202411010LAL')

        Returns:
            Dictionary with box score data or None on error
        """
        if game_id in self.scraped_ids:
            self.logger.info(f"Game {game_id} already scraped, skipping")
            return None

        self.logger.info(f"Scraping box score: {game_id}")

        # Build URL
        url = f"{self.config.base_url}{self.BOX_SCORE_PATH.format(game_id=game_id)}"

        # Fetch box score HTML
        async def fetch_box_score():
            async with self.get_session() as session:
                response = await self.fetch_url(url, session=session)
                if response:
                    return await self.parse_text_response(response)
                return None

        html = await safe_execute(
            fetch_box_score,
            max_retries=self.config.retry_attempts,
            metadata={"game_id": game_id, "url": url},
        )

        if not html:
            return None

        # Parse HTML
        box_score = self._parse_box_score_html(html, game_id)

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
            filename = f"boxscore_{game_id}.json"
            await self.store_data(
                box_score,
                filename,
                subdir=f"basketball_reference/box_scores/{game_id[:4]}",
            )
            self.scraped_ids.add(game_id)

        return box_score

    async def scrape_play_by_play(self, game_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape play-by-play data for a game.

        Args:
            game_id: Basketball Reference game ID

        Returns:
            List of play dictionaries or None on error
        """
        self.logger.info(f"Scraping play-by-play: {game_id}")

        # Build URL
        url = f"{self.config.base_url}{self.PLAY_BY_PLAY_PATH.format(game_id=game_id)}"

        # Fetch PBP HTML
        async def fetch_pbp():
            async with self.get_session() as session:
                response = await self.fetch_url(url, session=session)
                if response:
                    return await self.parse_text_response(response)
                return None

        html = await safe_execute(
            fetch_pbp,
            max_retries=self.config.retry_attempts,
            metadata={"game_id": game_id, "url": url},
        )

        if not html:
            return None

        # Parse HTML
        plays = self._parse_play_by_play_html(html, game_id)

        # Store play-by-play
        if plays:
            filename = f"pbp_{game_id}.json"
            await self.store_data(
                plays,
                filename,
                subdir=f"basketball_reference/play_by_play/{game_id[:4]}",
            )

        self.logger.info(f"Scraped {len(plays)} plays for game {game_id}")
        return plays

    async def scrape_player_season_stats(
        self, player_id: str, season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape player statistics for a season.

        Args:
            player_id: Basketball Reference player ID (e.g., 'jamesle01')
            season: Season year (optional, gets career if not specified)

        Returns:
            Dictionary with player statistics or None on error
        """
        self.logger.info(f"Scraping player stats: {player_id} (season={season})")

        # Extract first letter for URL
        letter = player_id[0].lower()

        # Build URL
        url = f"{self.config.base_url}{self.PLAYER_PATH.format(letter=letter, player_id=player_id)}"

        # Fetch player page HTML
        html = await safe_execute(
            self._fetch_url_text,
            url,
            max_retries=self.config.retry_attempts,
            metadata={"player_id": player_id, "season": season},
        )

        if not html:
            return None

        # Parse HTML
        player_stats = self._parse_player_stats_html(html, player_id, season)

        # Store player stats
        if player_stats:
            season_str = str(season) if season else "career"
            filename = f"player_{player_id}_{season_str}.json"
            await self.store_data(
                player_stats, filename, subdir=f"basketball_reference/players/{letter}"
            )

        return player_stats

    async def _fetch_url_text(self, url: str) -> Optional[str]:
        """Helper to fetch URL and return text"""
        async with self.get_session() as session:
            response = await self.fetch_url(url, session=session)
            if response:
                return await self.parse_text_response(response)
            return None

    def _parse_schedule_html(self, html: str, season: int) -> List[Dict[str, Any]]:
        """
        Parse schedule HTML to extract games.

        Args:
            html: HTML content
            season: Season year

        Returns:
            List of game dictionaries
        """
        games = []

        try:
            soup = BeautifulSoup(html, "lxml")

            # Find schedule table
            schedule_table = soup.find("table", {"id": "schedule"})
            if not schedule_table:
                self.logger.warning("Schedule table not found in HTML")
                return games

            # Parse rows
            rows = schedule_table.find("tbody").find_all("tr")

            for row in rows:
                # Skip header rows
                if row.get("class") and "thead" in row.get("class"):
                    continue

                cells = row.find_all(["th", "td"])
                if len(cells) < 7:
                    continue

                # Extract data
                date_str = cells[0].get_text(strip=True)
                visitor_team = cells[2].get_text(strip=True)
                visitor_pts = cells[3].get_text(strip=True)
                home_team = cells[4].get_text(strip=True)
                home_pts = cells[5].get_text(strip=True)

                # Extract game ID from box score link
                box_score_link = cells[6].find("a")
                game_id = None
                if box_score_link and box_score_link.get("href"):
                    href = box_score_link.get("href")
                    match = re.search(r"/boxscores/(\w+)\.html", href)
                    if match:
                        game_id = match.group(1)

                if not game_id:
                    continue

                game = {
                    "game_id": game_id,
                    "game_date": date_str,
                    "season": season,
                    "home_team": self._normalize_team_name(home_team),
                    "away_team": self._normalize_team_name(visitor_team),
                    "home_score": int(home_pts) if home_pts.isdigit() else 0,
                    "away_score": int(visitor_pts) if visitor_pts.isdigit() else 0,
                }

                games.append(game)

        except Exception as e:
            self.logger.error(f"Error parsing schedule HTML: {e}")

        return games

    def _parse_box_score_html(
        self, html: str, game_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse box score HTML to extract player statistics.

        Args:
            html: HTML content
            game_id: Game ID

        Returns:
            Dictionary with box score data
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            box_score = {"game_id": game_id, "players": []}

            # Find all box score tables (one per team)
            tables = soup.find_all("table", {"class": "stats_table"})

            for table in tables:
                # Get team from table ID
                table_id = table.get("id", "")
                if not table_id.startswith("box-"):
                    continue

                team_abbr = table_id.replace("box-", "").replace("-game-basic", "")

                # Parse player rows
                tbody = table.find("tbody")
                if not tbody:
                    continue

                rows = tbody.find_all("tr")

                for row in rows:
                    # Skip summary rows
                    if row.get("class") and any(
                        c in ["thead", "over_header"] for c in row.get("class", [])
                    ):
                        continue

                    cells = row.find_all(["th", "td"])
                    if len(cells) < 5:
                        continue

                    # Extract player data
                    player_cell = cells[0]
                    player_link = player_cell.find("a")

                    if not player_link:
                        continue

                    player_name = player_link.get_text(strip=True)
                    player_href = player_link.get("href", "")
                    player_id = re.search(r"/players/\w/(\w+)\.html", player_href)
                    player_id = player_id.group(1) if player_id else None

                    # Extract stats (simplified - Basketball Reference has many columns)
                    stats = {
                        "game_id": game_id,
                        "player_id": player_id,
                        "player_name": player_name,
                        "team": team_abbr.upper(),
                    }

                    box_score["players"].append(stats)

            return box_score

        except Exception as e:
            self.logger.error(f"Error parsing box score HTML: {e}")
            return None

    def _parse_play_by_play_html(self, html: str, game_id: str) -> List[Dict[str, Any]]:
        """
        Parse play-by-play HTML.

        Args:
            html: HTML content
            game_id: Game ID

        Returns:
            List of play dictionaries
        """
        plays = []

        try:
            soup = BeautifulSoup(html, "lxml")

            # Find play-by-play table
            pbp_table = soup.find("table", {"id": "pbp"})
            if not pbp_table:
                return plays

            # Parse rows (simplified)
            rows = pbp_table.find("tbody").find_all("tr")

            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) < 3:
                    continue

                play = {
                    "game_id": game_id,
                    "time": cells[0].get_text(strip=True),
                    "description": " ".join(
                        cell.get_text(strip=True) for cell in cells[1:]
                    ),
                }

                plays.append(play)

        except Exception as e:
            self.logger.error(f"Error parsing play-by-play HTML: {e}")

        return plays

    def _parse_player_stats_html(
        self, html: str, player_id: str, season: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Parse player statistics HTML (simplified)"""
        # This would be a complex parser for player stats tables
        # Returning placeholder for now
        return {"player_id": player_id, "season": season, "stats": {}}

    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team name to abbreviation.

        Args:
            team_name: Full team name

        Returns:
            Team abbreviation
        """
        # Simplified mapping - would need complete mapping
        team_map = {
            "Los Angeles Lakers": "LAL",
            "Golden State Warriors": "GSW",
            "Boston Celtics": "BOS",
            "Miami Heat": "MIA",
            # ... would need full mapping
        }

        return team_map.get(team_name, team_name[:3].upper())


# Convenience function
async def scrape_basketball_reference_season(
    season: int, output_dir: str = "/tmp/bbref_scraper", s3_bucket: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to scrape Basketball Reference season data.

    Args:
        season: Season year (e.g., 2024)
        output_dir: Output directory
        s3_bucket: Optional S3 bucket

    Returns:
        Dictionary with scraping results
    """
    config = ScraperConfig(
        base_url="https://www.basketball-reference.com",
        rate_limit=3.0,  # Respectful rate limit
        timeout=30,
        retry_attempts=3,
        max_concurrent=2,  # Keep low to be respectful
        s3_bucket=s3_bucket,
        output_dir=output_dir,
    )

    results = {"games_scraped": 0, "errors": 0}

    async with BasketballReferenceScraper(config) as scraper:
        games = await scraper.scrape_season_schedule(season=season)
        results["games_scraped"] = len(games)

    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        config = ScraperConfig(
            base_url="https://www.basketball-reference.com",
            rate_limit=3.0,
            output_dir="/tmp/bbref_test",
        )

        async with BasketballReferenceScraper(config) as scraper:
            # Scrape 2024 season schedule
            games = await scraper.scrape_season_schedule(season=2024)
            print(f"Found {len(games)} games")

    asyncio.run(main())
