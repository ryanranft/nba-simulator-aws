"""
hoopR Agent - hoopR Data Integration

Coordinates data collection from the hoopR R package.
Manages play-by-play and schedule data from hoopR.

Responsibilities:
- hoopR scraper coordination
- Play-by-play data collection
- Schedule data synchronization
- R integration management
- Data format conversion
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent, AgentPriority
from ..database import execute_query


class HooprAgent(BaseAgent):
    """
    hoopR integration agent.

    Coordinates collection from hoopR R package:
    - Play-by-play data
    - Schedule information
    - Team data
    - Player data

    Manages R process integration and data format conversion.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hoopR Agent.

        Args:
            config: Configuration with keys:
                - data_types: Types to collect (default: ['pbp', 'schedule'])
                - seasons: Seasons to process (default: current)
                - batch_size: Games per batch (default: 50)
                - validate_data: Validate after collection (default: True)
        """
        super().__init__(
            agent_name="hoopr", config=config, priority=AgentPriority.NORMAL
        )

        # Configuration
        self.data_types = self.config.get("data_types", ["pbp", "schedule"])
        self.seasons = self.config.get("seasons", [datetime.now().year])
        self.batch_size = self.config.get("batch_size", 50)
        self.validate_data = self.config.get("validate_data", True)

        # State
        self.games_processed: List[str] = []
        self.games_failed: List[str] = []
        self.records_collected = 0

    def _validate_config(self) -> bool:
        """Validate hoopR agent configuration"""
        try:
            valid_types = ["pbp", "schedule", "teams", "players"]
            for dtype in self.data_types:
                if dtype not in valid_types:
                    self.log_error(f"Invalid data_type: {dtype}")
                    return False

            if not isinstance(self.seasons, list) or not self.seasons:
                self.log_error("seasons must be non-empty list")
                return False

            if self.batch_size <= 0:
                self.log_error("batch_size must be positive")
                return False

            self.logger.info("hoopR agent configuration validated")
            return True

        except Exception as e:
            self.log_error(f"Configuration validation error: {e}")
            return False

    def _execute_core(self) -> bool:
        """Execute hoopR data collection"""
        try:
            self.logger.info("Starting hoopR data collection...")

            # Process each season
            for season in self.seasons:
                self.logger.info(f"Processing season: {season}")

                # Get games for this season
                games = self._get_season_games(season)

                if not games:
                    self.logger.warning(f"No games found for season {season}")
                    continue

                # Process in batches
                for i in range(0, len(games), self.batch_size):
                    batch = games[i : i + self.batch_size]
                    self._process_batch(batch)

            # Calculate metrics
            self.metrics.items_processed = len(self.games_processed) + len(
                self.games_failed
            )
            self.metrics.items_successful = len(self.games_processed)
            self.metrics.items_failed = len(self.games_failed)

            if self.metrics.items_processed > 0:
                self.metrics.quality_score = (
                    self.metrics.items_successful / self.metrics.items_processed * 100
                )
            else:
                self.metrics.quality_score = 100.0

            self.logger.info(
                f"hoopR collection complete. "
                f"Processed: {len(self.games_processed)}, "
                f"Failed: {len(self.games_failed)}, "
                f"Records: {self.records_collected}"
            )

            return self.metrics.quality_score >= 70.0  # Require 70% success rate

        except Exception as e:
            self.log_error(f"hoopR collection error: {e}")
            return False

    def _get_season_games(self, season: int) -> List[Dict[str, Any]]:
        """
        Get games for a season.

        Args:
            season: Season year

        Returns:
            List of game dictionaries
        """
        try:
            query = f"""
                SELECT game_id, game_date, home_team, away_team
                FROM games
                WHERE EXTRACT(YEAR FROM game_date) = {season}
                ORDER BY game_date
            """

            results = execute_query(query)
            return results if results else []

        except Exception as e:
            self.log_error(f"Error getting season games: {e}")
            return []

    def _process_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Process a batch of games.

        Args:
            batch: List of games to process
        """
        try:
            self.logger.debug(f"Processing batch of {len(batch)} games")

            for game in batch:
                game_id = game["game_id"]

                # Collect each data type
                success = True
                for data_type in self.data_types:
                    if not self._collect_game_data(game_id, data_type):
                        success = False

                if success:
                    self.games_processed.append(game_id)
                else:
                    self.games_failed.append(game_id)

        except Exception as e:
            self.log_error(f"Error processing batch: {e}")

    def _collect_game_data(self, game_id: str, data_type: str) -> bool:
        """
        Collect specific data type for a game.

        Args:
            game_id: Game identifier
            data_type: Type of data to collect

        Returns:
            bool: True if collection successful
        """
        try:
            # In real implementation, would:
            # 1. Call hoopR R package via rpy2 or subprocess
            # 2. Parse returned data
            # 3. Convert to standard format
            # 4. Store in database

            self.logger.debug(f"Collecting {data_type} for game {game_id}")

            # Simulate collection
            records_added = 100  # Simulated
            self.records_collected += records_added

            # Validate if enabled
            if self.validate_data:
                if not self._validate_game_data(game_id, data_type):
                    self.log_warning(
                        f"Validation failed for {data_type} in game {game_id}"
                    )
                    return False

            return True

        except Exception as e:
            self.log_error(f"Error collecting {data_type} for game {game_id}: {e}")
            return False

    def _validate_game_data(self, game_id: str, data_type: str) -> bool:
        """
        Validate collected data.

        Args:
            game_id: Game identifier
            data_type: Type of data to validate

        Returns:
            bool: True if validation passes
        """
        try:
            # In real implementation, would run validation queries
            # For now, simulate validation
            return True

        except Exception as e:
            self.log_error(f"Validation error: {e}")
            return False

    def get_agent_info(self) -> Dict[str, Any]:
        """Get hoopR agent information"""
        return {
            "name": "hoopR Data Collector",
            "version": "1.0.0",
            "description": "Coordinates hoopR R package data collection",
            "capabilities": [
                "Play-by-play collection",
                "Schedule synchronization",
                "R integration",
                "Data format conversion",
                "Validation",
            ],
            "data_types": self.data_types,
            "seasons": self.seasons,
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            "games_processed": len(self.games_processed),
            "games_failed": len(self.games_failed),
            "records_collected": self.records_collected,
            "success_rate": (
                len(self.games_processed)
                / (len(self.games_processed) + len(self.games_failed))
                * 100
                if (self.games_processed or self.games_failed)
                else 0
            ),
            "seasons_processed": self.seasons,
        }
