#!/usr/bin/env python3
"""
Data Validation & Quality Checks - Schema Validators and Quality Assurance

Provides comprehensive data validation for NBA data scrapers with:
- ESPN schema validators for JSON data
- Basketball Reference validators for HTML/table data
- Data completeness checkers
- Cross-source validation
- Quality reports and metrics
- Auto-retry on validation failure

Based on Crawl4AI MCP server validation patterns.

Usage:
    from data_validators import ESPNSchemaValidator, BasketballReferenceValidator, DataCompletenessChecker

    # ESPN validation
    espn_validator = ESPNSchemaValidator()
    result = await espn_validator.validate_game_data(data)

    # Basketball Reference validation
    bref_validator = BasketballReferenceValidator()
    result = await bref_validator.validate_player_stats(data)

    # Completeness checking
    checker = DataCompletenessChecker()
    result = await checker.check_completeness(data, "player_stats")

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Set
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import jsonschema
    from jsonschema import validate, ValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

try:
    from bs4 import BeautifulSoup

    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False


@dataclass
class ValidationResult:
    """Result of data validation"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    validation_method: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add validation warning"""
        self.warnings.append(warning)

    def calculate_quality_score(self) -> None:
        """Calculate quality score based on errors and warnings"""
        if not self.errors and not self.warnings:
            self.quality_score = 1.0
        elif not self.errors:
            self.quality_score = 0.8 - (len(self.warnings) * 0.1)
        else:
            self.quality_score = max(
                0.0, 0.5 - (len(self.errors) * 0.1) - (len(self.warnings) * 0.05)
            )


class BaseValidator(ABC):
    """Base class for data validators"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"validator.{name}")
        self.schemas: Dict[str, Dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load validation schemas"""
        pass

    @abstractmethod
    async def validate(self, data: Any, data_type: str = "unknown") -> ValidationResult:
        """Validate data and return result"""
        pass

    def validate_schema(self, data: Dict[str, Any], schema_name: str) -> List[str]:
        """Validate data against JSON schema"""
        if not HAS_JSONSCHEMA:
            return ["jsonschema not available"]

        if schema_name not in self.schemas:
            return [f"Schema '{schema_name}' not found"]

        try:
            validate(data, self.schemas[schema_name])
            return []
        except ValidationError as e:
            return [f"Schema validation error: {e.message}"]
        except Exception as e:
            return [f"Schema validation failed: {e}"]


class ESPNSchemaValidator(BaseValidator):
    """ESPN-specific data validator"""

    def __init__(self):
        super().__init__("espn")
        self._load_espn_schemas()

    def _load_espn_schemas(self) -> None:
        """Load ESPN-specific schemas"""
        self.schemas = {
            "game_summary": {
                "type": "object",
                "required": ["id", "date", "competitions"],
                "properties": {
                    "id": {"type": "string"},
                    "date": {"type": "string"},
                    "competitions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["competitors"],
                            "properties": {
                                "competitors": {
                                    "type": "array",
                                    "minItems": 2,
                                    "maxItems": 2,
                                    "items": {
                                        "type": "object",
                                        "required": ["team", "score"],
                                        "properties": {
                                            "team": {
                                                "type": "object",
                                                "required": ["displayName"],
                                                "properties": {
                                                    "displayName": {"type": "string"},
                                                    "id": {"type": "string"},
                                                },
                                            },
                                            "score": {"type": ["string", "number"]},
                                        },
                                    },
                                }
                            },
                        },
                    },
                    "status": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "object",
                                "properties": {"name": {"type": "string"}},
                            }
                        },
                    },
                },
            },
            "player_stats": {
                "type": "object",
                "required": ["athlete", "statistics"],
                "properties": {
                    "athlete": {
                        "type": "object",
                        "required": ["id", "displayName"],
                        "properties": {
                            "id": {"type": "string"},
                            "displayName": {"type": "string"},
                            "position": {
                                "type": "object",
                                "properties": {"displayName": {"type": "string"}},
                            },
                        },
                    },
                    "statistics": {"type": "array", "items": {"type": "number"}},
                },
            },
            "play_by_play": {
                "type": "object",
                "required": ["plays"],
                "properties": {
                    "plays": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "period", "clock"],
                            "properties": {
                                "id": {"type": "string"},
                                "period": {
                                    "type": "object",
                                    "properties": {"number": {"type": "integer"}},
                                },
                                "clock": {
                                    "type": "object",
                                    "properties": {"displayValue": {"type": "string"}},
                                },
                                "type": {
                                    "type": "object",
                                    "properties": {"text": {"type": "string"}},
                                },
                                "text": {"type": "string"},
                            },
                        },
                    }
                },
            },
        }

    async def validate(self, data: Any, data_type: str = "unknown") -> ValidationResult:
        """Validate ESPN data"""
        result = ValidationResult(is_valid=True, validation_method=f"espn_{data_type}")

        try:
            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                result.add_error("Data must be a dictionary")
                return result

            # Determine schema based on data structure
            schema_name = self._determine_schema(data)
            if not schema_name:
                result.add_error("Unable to determine data schema")
                return result

            # Validate against schema
            schema_errors = self.validate_schema(data, schema_name)
            result.errors.extend(schema_errors)

            # Additional ESPN-specific validations
            additional_errors = await self._validate_espn_specific(data, data_type)
            result.errors.extend(additional_errors)

            # Calculate quality score
            result.calculate_quality_score()

            return result

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")
            return result
        except Exception as e:
            result.add_error(f"Validation error: {e}")
            return result

    def _determine_schema(self, data: Dict[str, Any]) -> Optional[str]:
        """Determine which schema to use based on data structure"""
        if "competitions" in data:
            return "game_summary"
        elif "athlete" in data and "statistics" in data:
            return "player_stats"
        elif "plays" in data:
            return "play_by_play"
        else:
            return None

    async def _validate_espn_specific(
        self, data: Dict[str, Any], data_type: str
    ) -> List[str]:
        """ESPN-specific validation rules"""
        errors = []

        # Validate game data
        if "competitions" in data:
            competitions = data.get("competitions", [])
            if len(competitions) != 1:
                errors.append("Game should have exactly one competition")

            if competitions:
                competitors = competitions[0].get("competitors", [])
                if len(competitors) != 2:
                    errors.append("Game should have exactly two competitors")

                # Check team names are not empty
                for i, competitor in enumerate(competitors):
                    team_name = competitor.get("team", {}).get("displayName", "")
                    if not team_name.strip():
                        errors.append(f"Competitor {i+1} has empty team name")

        # Validate player stats
        elif "athlete" in data:
            athlete = data.get("athlete", {})
            if not athlete.get("displayName", "").strip():
                errors.append("Player name is empty")

            stats = data.get("statistics", [])
            if not stats:
                errors.append("Player has no statistics")

        # Validate play-by-play
        elif "plays" in data:
            plays = data.get("plays", [])
            if not plays:
                errors.append("No plays found in play-by-play data")

            # Check for required play fields
            for i, play in enumerate(plays[:10]):  # Check first 10 plays
                if not play.get("text", "").strip():
                    errors.append(f"Play {i+1} has empty text")

        return errors

    async def validate_game_data(self, data: Any) -> ValidationResult:
        """Validate ESPN game data specifically"""
        return await self.validate(data, "game_data")

    async def validate_player_stats(self, data: Any) -> ValidationResult:
        """Validate ESPN player stats specifically"""
        return await self.validate(data, "player_stats")

    async def validate_play_by_play(self, data: Any) -> ValidationResult:
        """Validate ESPN play-by-play data specifically"""
        return await self.validate(data, "play_by_play")


class BasketballReferenceValidator(BaseValidator):
    """Basketball Reference-specific data validator"""

    def __init__(self):
        super().__init__("basketball_reference")
        self._load_bref_schemas()

    def _load_bref_schemas(self) -> None:
        """Load Basketball Reference-specific schemas"""
        self.schemas = {
            "player_stats": {
                "type": "object",
                "required": ["players"],
                "properties": {
                    "players": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["player", "stats"],
                            "properties": {
                                "player": {"type": "string"},
                                "season": {"type": "string"},
                                "stats": {
                                    "type": "object",
                                    "required": [
                                        "games",
                                        "points",
                                        "rebounds",
                                        "assists",
                                    ],
                                    "properties": {
                                        "games": {"type": "number", "minimum": 0},
                                        "minutes_per_game": {
                                            "type": "number",
                                            "minimum": 0,
                                        },
                                        "field_goals": {"type": "number", "minimum": 0},
                                        "field_goal_attempts": {
                                            "type": "number",
                                            "minimum": 0,
                                        },
                                        "field_goal_percentage": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "three_pointers": {
                                            "type": "number",
                                            "minimum": 0,
                                        },
                                        "three_point_attempts": {
                                            "type": "number",
                                            "minimum": 0,
                                        },
                                        "three_point_percentage": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "free_throws": {"type": "number", "minimum": 0},
                                        "free_throw_attempts": {
                                            "type": "number",
                                            "minimum": 0,
                                        },
                                        "free_throw_percentage": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "rebounds": {"type": "number", "minimum": 0},
                                        "assists": {"type": "number", "minimum": 0},
                                        "steals": {"type": "number", "minimum": 0},
                                        "blocks": {"type": "number", "minimum": 0},
                                        "turnovers": {"type": "number", "minimum": 0},
                                        "points": {"type": "number", "minimum": 0},
                                    },
                                },
                            },
                        },
                    }
                },
            },
            "team_stats": {
                "type": "object",
                "required": ["teams"],
                "properties": {
                    "teams": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["team", "stats"],
                            "properties": {
                                "team": {"type": "string"},
                                "season": {"type": "string"},
                                "stats": {
                                    "type": "object",
                                    "required": ["games", "points"],
                                    "properties": {
                                        "games": {"type": "number", "minimum": 0},
                                        "points": {"type": "number", "minimum": 0},
                                        "field_goal_percentage": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "three_point_percentage": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "free_throw_percentage": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                        },
                                        "rebounds": {"type": "number", "minimum": 0},
                                        "assists": {"type": "number", "minimum": 0},
                                        "steals": {"type": "number", "minimum": 0},
                                        "blocks": {"type": "number", "minimum": 0},
                                        "turnovers": {"type": "number", "minimum": 0},
                                    },
                                },
                            },
                        },
                    }
                },
            },
            "schedule": {
                "type": "object",
                "required": ["games"],
                "properties": {
                    "games": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["date", "visitor", "home"],
                            "properties": {
                                "date": {"type": "string"},
                                "time": {"type": "string"},
                                "visitor": {"type": "string"},
                                "visitor_score": {"type": ["number", "null"]},
                                "home": {"type": "string"},
                                "home_score": {"type": ["number", "null"]},
                                "box_score": {"type": ["string", "null"]},
                                "attendance": {"type": ["number", "null"]},
                            },
                        },
                    }
                },
            },
        }

    async def validate(self, data: Any, data_type: str = "unknown") -> ValidationResult:
        """Validate Basketball Reference data"""
        result = ValidationResult(
            is_valid=True, validation_method=f"basketball_reference_{data_type}"
        )

        try:
            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                result.add_error("Data must be a dictionary")
                return result

            # Determine schema based on data structure
            schema_name = self._determine_schema(data)
            if not schema_name:
                result.add_error("Unable to determine data schema")
                return result

            # Validate against schema
            schema_errors = self.validate_schema(data, schema_name)
            result.errors.extend(schema_errors)

            # Additional Basketball Reference-specific validations
            additional_errors = await self._validate_bref_specific(data, data_type)
            result.errors.extend(additional_errors)

            # Calculate quality score
            result.calculate_quality_score()

            return result

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")
            return result
        except Exception as e:
            result.add_error(f"Validation error: {e}")
            return result

    def _determine_schema(self, data: Dict[str, Any]) -> Optional[str]:
        """Determine which schema to use based on data structure"""
        if "players" in data:
            return "player_stats"
        elif "teams" in data:
            return "team_stats"
        elif "games" in data:
            return "schedule"
        else:
            return None

    async def _validate_bref_specific(
        self, data: Dict[str, Any], data_type: str
    ) -> List[str]:
        """Basketball Reference-specific validation rules"""
        errors = []

        # Validate player stats
        if "players" in data:
            players = data.get("players", [])
            if not players:
                errors.append("No players found in player stats data")

            for i, player in enumerate(players):
                player_name = player.get("player", "")
                if not player_name.strip():
                    errors.append(f"Player {i+1} has empty name")

                stats = player.get("stats", {})
                if not stats:
                    errors.append(f"Player {i+1} has no statistics")
                    continue

                # Check for impossible stats
                if stats.get("field_goals", 0) > stats.get("field_goal_attempts", 0):
                    errors.append(f"Player {i+1}: field goals > field goal attempts")

                if stats.get("three_pointers", 0) > stats.get(
                    "three_point_attempts", 0
                ):
                    errors.append(f"Player {i+1}: 3-pointers > 3-point attempts")

                if stats.get("free_throws", 0) > stats.get("free_throw_attempts", 0):
                    errors.append(f"Player {i+1}: free throws > free throw attempts")

                # Check percentage ranges
                fg_pct = stats.get("field_goal_percentage", 0)
                if fg_pct > 1.0:
                    errors.append(f"Player {i+1}: field goal percentage > 100%")

                three_pct = stats.get("three_point_percentage", 0)
                if three_pct > 1.0:
                    errors.append(f"Player {i+1}: 3-point percentage > 100%")

                ft_pct = stats.get("free_throw_percentage", 0)
                if ft_pct > 1.0:
                    errors.append(f"Player {i+1}: free throw percentage > 100%")

        # Validate team stats
        elif "teams" in data:
            teams = data.get("teams", [])
            if not teams:
                errors.append("No teams found in team stats data")

            for i, team in enumerate(teams):
                team_name = team.get("team", "")
                if not team_name.strip():
                    errors.append(f"Team {i+1} has empty name")

        # Validate schedule
        elif "games" in data:
            games = data.get("games", [])
            if not games:
                errors.append("No games found in schedule data")

            for i, game in enumerate(games):
                visitor = game.get("visitor", "")
                home = game.get("home", "")
                if not visitor.strip():
                    errors.append(f"Game {i+1}: visitor team name is empty")
                if not home.strip():
                    errors.append(f"Game {i+1}: home team name is empty")

                # Check scores are reasonable
                visitor_score = game.get("visitor_score")
                home_score = game.get("home_score")
                if visitor_score is not None and visitor_score < 0:
                    errors.append(f"Game {i+1}: visitor score is negative")
                if home_score is not None and home_score < 0:
                    errors.append(f"Game {i+1}: home score is negative")

        return errors

    async def validate_player_stats(self, data: Any) -> ValidationResult:
        """Validate Basketball Reference player stats specifically"""
        return await self.validate(data, "player_stats")

    async def validate_team_stats(self, data: Any) -> ValidationResult:
        """Validate Basketball Reference team stats specifically"""
        return await self.validate(data, "team_stats")

    async def validate_schedule(self, data: Any) -> ValidationResult:
        """Validate Basketball Reference schedule specifically"""
        return await self.validate(data, "schedule")


class DataCompletenessChecker:
    """Checks data completeness and consistency"""

    def __init__(self):
        self.logger = logging.getLogger("completeness_checker")
        self.required_fields = {
            "player_stats": ["player", "games", "points", "rebounds", "assists"],
            "team_stats": ["team", "games", "points"],
            "game_summary": ["id", "date", "competitions"],
            "play_by_play": ["plays"],
            "schedule": ["games"],
        }

    async def check_completeness(self, data: Any, data_type: str) -> ValidationResult:
        """Check data completeness"""
        result = ValidationResult(
            is_valid=True, validation_method=f"completeness_{data_type}"
        )

        try:
            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                result.add_error("Data must be a dictionary")
                return result

            # Check required fields
            required = self.required_fields.get(data_type, [])
            missing_fields = []

            for field in required:
                if field not in data:
                    missing_fields.append(field)

            if missing_fields:
                result.add_error(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            # Check data is not empty
            if not data:
                result.add_error("Data is completely empty")

            # Type-specific completeness checks
            if data_type == "player_stats":
                await self._check_player_stats_completeness(data, result)
            elif data_type == "team_stats":
                await self._check_team_stats_completeness(data, result)
            elif data_type == "game_summary":
                await self._check_game_summary_completeness(data, result)
            elif data_type == "play_by_play":
                await self._check_play_by_play_completeness(data, result)
            elif data_type == "schedule":
                await self._check_schedule_completeness(data, result)

            # Calculate quality score
            result.calculate_quality_score()

            return result

        except Exception as e:
            result.add_error(f"Completeness check error: {e}")
            return result

    async def _check_player_stats_completeness(
        self, data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check player stats completeness"""
        players = data.get("players", [])
        if not players:
            result.add_error("No players found")
            return

        for i, player in enumerate(players):
            stats = player.get("stats", {})
            if not stats:
                result.add_error(f"Player {i+1} has no statistics")
                continue

            # Check for zero or missing key stats
            key_stats = ["games", "points", "rebounds", "assists"]
            for stat in key_stats:
                value = stats.get(stat)
                if value is None:
                    result.add_warning(f"Player {i+1}: {stat} is missing")
                elif value == 0 and stat == "games":
                    result.add_warning(f"Player {i+1}: games played is 0")

    async def _check_team_stats_completeness(
        self, data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check team stats completeness"""
        teams = data.get("teams", [])
        if not teams:
            result.add_error("No teams found")
            return

        for i, team in enumerate(teams):
            stats = team.get("stats", {})
            if not stats:
                result.add_error(f"Team {i+1} has no statistics")
                continue

            # Check for missing key stats
            key_stats = ["games", "points"]
            for stat in key_stats:
                if stat not in stats:
                    result.add_warning(f"Team {i+1}: {stat} is missing")

    async def _check_game_summary_completeness(
        self, data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check game summary completeness"""
        competitions = data.get("competitions", [])
        if not competitions:
            result.add_error("No competitions found")
            return

        competition = competitions[0]
        competitors = competition.get("competitors", [])
        if len(competitors) != 2:
            result.add_error(f"Expected 2 competitors, found {len(competitors)}")

        for i, competitor in enumerate(competitors):
            team = competitor.get("team", {})
            if not team.get("displayName"):
                result.add_error(f"Competitor {i+1} has no team name")

    async def _check_play_by_play_completeness(
        self, data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check play-by-play completeness"""
        plays = data.get("plays", [])
        if not plays:
            result.add_error("No plays found")
            return

        # Check first few plays have required fields
        for i, play in enumerate(plays[:5]):
            if not play.get("text"):
                result.add_warning(f"Play {i+1} has no text description")

    async def _check_schedule_completeness(
        self, data: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check schedule completeness"""
        games = data.get("games", [])
        if not games:
            result.add_error("No games found")
            return

        for i, game in enumerate(games):
            if not game.get("visitor"):
                result.add_warning(f"Game {i+1}: visitor team missing")
            if not game.get("home"):
                result.add_warning(f"Game {i+1}: home team missing")


class CrossSourceValidator:
    """Validates data consistency across different sources"""

    def __init__(self):
        self.logger = logging.getLogger("cross_source_validator")

    async def validate_cross_source(
        self, espn_data: Any, bref_data: Any, data_type: str = "player_stats"
    ) -> ValidationResult:
        """Validate data consistency between ESPN and Basketball Reference"""
        result = ValidationResult(validation_method=f"cross_source_{data_type}")

        try:
            if isinstance(espn_data, str):
                espn_data = json.loads(espn_data)
            if isinstance(bref_data, str):
                bref_data = json.loads(bref_data)

            if data_type == "player_stats":
                await self._validate_player_stats_cross_source(
                    espn_data, bref_data, result
                )
            elif data_type == "team_stats":
                await self._validate_team_stats_cross_source(
                    espn_data, bref_data, result
                )
            elif data_type == "schedule":
                await self._validate_schedule_cross_source(espn_data, bref_data, result)

            # Calculate quality score
            result.calculate_quality_score()

            return result

        except Exception as e:
            result.add_error(f"Cross-source validation error: {e}")
            return result

    async def _validate_player_stats_cross_source(
        self,
        espn_data: Dict[str, Any],
        bref_data: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate player stats consistency between sources"""
        # This would implement cross-source validation logic
        # For now, we'll add a placeholder
        result.add_warning("Cross-source player stats validation not yet implemented")

    async def _validate_team_stats_cross_source(
        self,
        espn_data: Dict[str, Any],
        bref_data: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate team stats consistency between sources"""
        result.add_warning("Cross-source team stats validation not yet implemented")

    async def _validate_schedule_cross_source(
        self,
        espn_data: Dict[str, Any],
        bref_data: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate schedule consistency between sources"""
        result.add_warning("Cross-source schedule validation not yet implemented")


class ValidationManager:
    """Manages multiple validators"""

    def __init__(self):
        self.validators = {
            "espn": ESPNSchemaValidator(),
            "basketball_reference": BasketballReferenceValidator(),
            "completeness": DataCompletenessChecker(),
            "cross_source": CrossSourceValidator(),
        }
        self.logger = logging.getLogger("validation_manager")

    async def validate_data(
        self, data: Any, source: str, data_type: str
    ) -> ValidationResult:
        """Validate data using appropriate validator"""
        if source not in self.validators:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown source: {source}"],
                validation_method="unknown",
            )

        validator = self.validators[source]
        return await validator.validate(data, data_type)

    async def validate_with_retry(
        self, data: Any, source: str, data_type: str, max_retries: int = 3
    ) -> ValidationResult:
        """Validate data with retry on failure"""
        for attempt in range(max_retries):
            result = await self.validate_data(data, source, data_type)

            if result.is_valid:
                return result

            if attempt < max_retries - 1:
                self.logger.warning(
                    f"Validation attempt {attempt + 1} failed, retrying..."
                )
                await asyncio.sleep(1)  # Brief delay before retry

        return result

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validators"""
        return {
            "available_validators": list(self.validators.keys()),
            "total_validators": len(self.validators),
        }


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create validation manager
        manager = ValidationManager()

        # Example ESPN data
        espn_data = {
            "id": "12345",
            "date": "2024-10-13",
            "competitions": [
                {
                    "competitors": [
                        {"team": {"displayName": "Lakers"}, "score": "110"},
                        {"team": {"displayName": "Warriors"}, "score": "108"},
                    ]
                }
            ],
        }

        # Validate ESPN data
        result = await manager.validate_data(espn_data, "espn", "game_summary")

        print(f"ESPN validation success: {result.is_valid}")
        print(f"Quality score: {result.quality_score}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")

        # Example Basketball Reference data
        bref_data = {
            "players": [
                {
                    "player": "LeBron James",
                    "season": "2024-25",
                    "stats": {
                        "games": 10,
                        "points": 250,
                        "rebounds": 80,
                        "assists": 60,
                    },
                }
            ]
        }

        # Validate Basketball Reference data
        result = await manager.validate_data(
            bref_data, "basketball_reference", "player_stats"
        )

        print(f"\nBasketball Reference validation success: {result.is_valid}")
        print(f"Quality score: {result.quality_score}")
        if result.errors:
            print(f"Errors: {result.errors}")

    asyncio.run(example_usage())
