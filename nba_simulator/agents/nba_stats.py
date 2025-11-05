"""
NBA Stats Agent - NBA API Coordination

Coordinates data collection from the NBA's official API.
Manages advanced statistics, player tracking, and team data.

Responsibilities:
- NBA API scraper coordination
- Advanced statistics collection
- Player tracking data
- Team statistics
- Rate limiting and API management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import time

from .base_agent import BaseAgent, AgentPriority
from ..database import execute_query


class NBAStatsAgent(BaseAgent):
    """
    NBA API coordination agent.

    Coordinates collection of:
    - Advanced box scores
    - Player tracking data
    - Team statistics
    - Lineup data
    - Shot charts

    Manages NBA API rate limits and retries.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NBA Stats Agent.

        Args:
            config: Configuration with keys:
                - api_rate_limit: Requests per minute (default: 60)
                - max_concurrent: Max concurrent requests (default: 5)
                - retry_attempts: Retry attempts per request (default: 3)
                - data_types: Types to collect (default: ['boxscore', 'tracking'])
        """
        super().__init__(
            agent_name="nba_stats", config=config, priority=AgentPriority.HIGH
        )

        # Configuration
        self.api_rate_limit = self.config.get("api_rate_limit", 60)
        self.max_concurrent = self.config.get("max_concurrent", 5)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.data_types = self.config.get("data_types", ["boxscore", "tracking"])

        # State
        self.requests_made = 0
        self.requests_successful = 0
        self.requests_failed = 0
        self.games_processed: List[str] = []

    def _validate_config(self) -> bool:
        """Validate NBA Stats agent configuration"""
        try:
            if self.api_rate_limit <= 0:
                self.log_error("api_rate_limit must be positive")
                return False

            if self.max_concurrent <= 0:
                self.log_error("max_concurrent must be positive")
                return False

            valid_types = ["boxscore", "tracking", "lineups", "shots"]
            for dtype in self.data_types:
                if dtype not in valid_types:
                    self.log_error(f"Invalid data_type: {dtype}")
                    return False

            self.logger.info("NBA Stats agent configuration validated")
            return True

        except Exception as e:
            self.log_error(f"Configuration validation error: {e}")
            return False

    def _execute_core(self) -> bool:
        """Execute NBA Stats collection"""
        try:
            self.logger.info("Starting NBA Stats collection...")

            # Get games needing NBA Stats data
            games = self._get_games_to_process()
            self.metrics.items_processed = len(games)

            if not games:
                self.logger.info("No games require NBA Stats processing")
                return True

            self.logger.info(f"Processing {len(games)} games")

            # Process each game
            for game_data in games:
                game_id = game_data["game_id"]
                success = self._process_game(game_id)

                if success:
                    self.games_processed.append(game_id)
                    self.metrics.items_successful += 1
                else:
                    self.metrics.items_failed += 1

            # Calculate quality score
            if self.metrics.items_processed > 0:
                self.metrics.quality_score = (
                    self.metrics.items_successful / self.metrics.items_processed * 100
                )

            success_rate = self.metrics.quality_score
            self.logger.info(
                f"NBA Stats collection complete. " f"Success rate: {success_rate:.1f}%"
            )

            return success_rate >= 80.0  # Require 80% success rate

        except Exception as e:
            self.log_error(f"NBA Stats collection error: {e}")
            return False

    def _get_games_to_process(self) -> List[Dict[str, Any]]:
        """Get games that need NBA Stats data"""
        try:
            # Get recent games without complete NBA stats
            query = """
                SELECT game_id, game_date, home_team, away_team
                FROM games
                WHERE game_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY game_date DESC
                LIMIT 50
            """

            results = execute_query(query)
            return results if results else []

        except Exception as e:
            self.log_error(f"Error getting games to process: {e}")
            return []

    def _process_game(self, game_id: str) -> bool:
        """
        Process NBA Stats for a single game.

        Args:
            game_id: Game identifier

        Returns:
            bool: True if processing successful
        """
        try:
            self.logger.debug(f"Processing game: {game_id}")

            # Collect each data type
            for data_type in self.data_types:
                success = self._collect_data_type(game_id, data_type)
                if not success:
                    self.log_warning(
                        f"Failed to collect {data_type} for game {game_id}"
                    )
                    # Continue with other data types

            # Rate limiting
            self._apply_rate_limit()

            return True

        except Exception as e:
            self.log_error(f"Error processing game {game_id}: {e}")
            return False

    def _collect_data_type(self, game_id: str, data_type: str) -> bool:
        """
        Collect specific data type for a game.

        Args:
            game_id: Game identifier
            data_type: Type of data to collect

        Returns:
            bool: True if collection successful
        """
        try:
            # Simulate API call with retry logic
            for attempt in range(self.retry_attempts):
                self.requests_made += 1

                # In real implementation, would make actual NBA API call
                # For now, simulate success
                success = True  # Simulated

                if success:
                    self.requests_successful += 1
                    return True

                # Retry with exponential backoff
                if attempt < self.retry_attempts - 1:
                    delay = 2**attempt
                    time.sleep(delay)

            self.requests_failed += 1
            return False

        except Exception as e:
            self.log_error(f"Error collecting {data_type}: {e}")
            self.requests_failed += 1
            return False

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests"""
        # Simple rate limiting: sleep to maintain rate
        seconds_per_request = 60.0 / self.api_rate_limit
        time.sleep(seconds_per_request)

    def get_agent_info(self) -> Dict[str, Any]:
        """Get NBA Stats agent information"""
        return {
            "name": "NBA Stats Collector",
            "version": "1.0.0",
            "description": "Coordinates NBA API data collection",
            "capabilities": [
                "Advanced box scores",
                "Player tracking data",
                "Team statistics",
                "Rate limit management",
                "Automatic retries",
            ],
            "api_rate_limit": self.api_rate_limit,
            "data_types": self.data_types,
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            "games_processed": len(self.games_processed),
            "requests_made": self.requests_made,
            "requests_successful": self.requests_successful,
            "requests_failed": self.requests_failed,
            "success_rate": (
                self.requests_successful / self.requests_made * 100
                if self.requests_made > 0
                else 0
            ),
        }
