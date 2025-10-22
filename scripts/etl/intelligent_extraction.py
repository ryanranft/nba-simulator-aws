#!/usr/bin/env python3
"""
Intelligent Content Extraction Strategies

Provides intelligent content extraction for NBA data scrapers with:
- ESPN-specific extraction strategies
- Basketball Reference extraction strategies
- LLM-based extraction using Google Gemini
- Content validation and parsing improvements
- Schema validation and data quality checks

Based on Crawl4AI MCP server intelligent extraction patterns.

Usage:
    from intelligent_extraction import ESPNExtractionStrategy, BasketballReferenceExtractionStrategy

    # ESPN extraction
    espn_strategy = ESPNExtractionStrategy()
    data = await espn_strategy.extract_game_data(response_text)

    # Basketball Reference extraction
    bref_strategy = BasketballReferenceExtractionStrategy()
    data = await bref_strategy.extract_player_stats(response_text)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

try:
    from bs4 import BeautifulSoup

    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

try:
    import google.generativeai as genai

    HAS_GOOGLE_AI = True
except ImportError:
    HAS_GOOGLE_AI = False


@dataclass
class ExtractionResult:
    """Result of content extraction"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    extraction_method: str = ""
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class BaseExtractionStrategy(ABC):
    """Base class for content extraction strategies"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"extraction.{name}")
        self.schemas: Dict[str, Dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load JSON schemas for validation"""
        # This would load schemas from files or define them inline
        # For now, we'll define basic schemas
        pass

    @abstractmethod
    async def extract(
        self, content: str, content_type: str = "html"
    ) -> ExtractionResult:
        """Extract structured data from content"""
        pass

    def validate_data(self, data: Dict[str, Any], schema_name: str) -> List[str]:
        """Validate extracted data against schema"""
        if not HAS_JSONSCHEMA:
            self.logger.warning("jsonschema not available, skipping validation")
            return []

        if schema_name not in self.schemas:
            self.logger.warning(f"Schema '{schema_name}' not found")
            return []

        try:
            jsonschema.validate(data, self.schemas[schema_name])
            return []
        except jsonschema.ValidationError as e:
            return [f"Validation error: {e.message}"]
        except Exception as e:
            return [f"Schema validation failed: {e}"]


class ESPNExtractionStrategy(BaseExtractionStrategy):
    """ESPN-specific content extraction strategy"""

    def __init__(self):
        super().__init__("espn")
        self._load_espn_schemas()

    def _load_espn_schemas(self) -> None:
        """Load ESPN-specific schemas"""
        self.schemas = {
            "game_summary": {
                "type": "object",
                "required": ["gameId", "date", "homeTeam", "awayTeam"],
                "properties": {
                    "gameId": {"type": "string"},
                    "date": {"type": "string"},
                    "homeTeam": {"type": "object"},
                    "awayTeam": {"type": "object"},
                    "score": {"type": "object"},
                    "status": {"type": "string"},
                },
            },
            "player_stats": {
                "type": "object",
                "required": ["playerId", "name", "stats"],
                "properties": {
                    "playerId": {"type": "string"},
                    "name": {"type": "string"},
                    "stats": {"type": "object"},
                    "team": {"type": "string"},
                },
            },
            "play_by_play": {
                "type": "object",
                "required": ["gameId", "plays"],
                "properties": {
                    "gameId": {"type": "string"},
                    "plays": {"type": "array", "items": {"type": "object"}},
                },
            },
        }

    async def extract(
        self, content: str, content_type: str = "json"
    ) -> ExtractionResult:
        """Extract data from ESPN content"""
        try:
            if content_type == "json":
                return await self._extract_from_json(content)
            elif content_type == "html":
                return await self._extract_from_html(content)
            else:
                return ExtractionResult(
                    success=False, errors=[f"Unsupported content type: {content_type}"]
                )
        except Exception as e:
            self.logger.error(f"ESPN extraction failed: {e}")
            return ExtractionResult(success=False, errors=[f"Extraction error: {e}"])

    async def _extract_from_json(self, content: str) -> ExtractionResult:
        """Extract data from ESPN JSON response"""
        try:
            data = json.loads(content)

            # Determine data type and extract accordingly
            if "events" in data:
                return await self._extract_schedule_data(data)
            elif "boxscore" in data:
                return await self._extract_box_score_data(data)
            elif "plays" in data:
                return await self._extract_play_by_play_data(data)
            else:
                return ExtractionResult(
                    success=False, errors=["Unknown ESPN data format"]
                )
        except json.JSONDecodeError as e:
            return ExtractionResult(success=False, errors=[f"Invalid JSON: {e}"])

    async def _extract_schedule_data(self, data: Dict[str, Any]) -> ExtractionResult:
        """Extract schedule data from ESPN response"""
        try:
            events = data.get("events", [])
            extracted_games = []

            for event in events:
                game_data = {
                    "gameId": event.get("id"),
                    "date": event.get("date"),
                    "homeTeam": {
                        "id": event.get("competitions", [{}])[0]
                        .get("competitors", [{}])[0]
                        .get("id"),
                        "name": event.get("competitions", [{}])[0]
                        .get("competitors", [{}])[0]
                        .get("team", {})
                        .get("displayName"),
                        "score": event.get("competitions", [{}])[0]
                        .get("competitors", [{}])[0]
                        .get("score"),
                    },
                    "awayTeam": {
                        "id": event.get("competitions", [{}])[0]
                        .get("competitors", [{}])[1]
                        .get("id"),
                        "name": event.get("competitions", [{}])[0]
                        .get("competitors", [{}])[1]
                        .get("team", {})
                        .get("displayName"),
                        "score": event.get("competitions", [{}])[0]
                        .get("competitors", [{}])[1]
                        .get("score"),
                    },
                    "status": event.get("status", {}).get("type", {}).get("name"),
                    "venue": event.get("competitions", [{}])[0]
                    .get("venue", {})
                    .get("fullName"),
                }
                extracted_games.append(game_data)

            # Validate extracted data
            validation_errors = []
            for game in extracted_games:
                errors = self.validate_data(game, "game_summary")
                validation_errors.extend(errors)

            return ExtractionResult(
                success=len(validation_errors) == 0,
                data={"games": extracted_games},
                confidence=0.9 if len(validation_errors) == 0 else 0.6,
                extraction_method="espn_schedule_parser",
                errors=validation_errors,
                metadata={"total_games": len(extracted_games)},
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"Schedule extraction error: {e}"]
            )

    async def _extract_box_score_data(self, data: Dict[str, Any]) -> ExtractionResult:
        """Extract box score data from ESPN response"""
        try:
            boxscore = data.get("boxscore", {})
            players = boxscore.get("players", [])

            extracted_stats = []
            for player_group in players:
                for player in player_group.get("statistics", []):
                    player_data = {
                        "playerId": player.get("athlete", {}).get("id"),
                        "name": player.get("athlete", {}).get("displayName"),
                        "team": player_group.get("team", {}).get("displayName"),
                        "stats": player.get("stats", []),
                        "position": player.get("athlete", {})
                        .get("position", {})
                        .get("displayName"),
                    }
                    extracted_stats.append(player_data)

            return ExtractionResult(
                success=True,
                data={"players": extracted_stats},
                confidence=0.85,
                extraction_method="espn_boxscore_parser",
                metadata={"total_players": len(extracted_stats)},
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"Box score extraction error: {e}"]
            )

    async def _extract_play_by_play_data(
        self, data: Dict[str, Any]
    ) -> ExtractionResult:
        """Extract play-by-play data from ESPN response"""
        try:
            plays = data.get("plays", [])
            extracted_plays = []

            for play in plays:
                play_data = {
                    "playId": play.get("id"),
                    "period": play.get("period", {}).get("number"),
                    "clock": play.get("clock", {}).get("displayValue"),
                    "type": play.get("type", {}).get("text"),
                    "text": play.get("text"),
                    "score": play.get("scoreValue"),
                    "team": play.get("team", {}).get("displayName"),
                }
                extracted_plays.append(play_data)

            return ExtractionResult(
                success=True,
                data={"plays": extracted_plays},
                confidence=0.9,
                extraction_method="espn_pbp_parser",
                metadata={"total_plays": len(extracted_plays)},
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"Play-by-play extraction error: {e}"]
            )

    async def _extract_from_html(self, content: str) -> ExtractionResult:
        """Extract data from ESPN HTML content"""
        if not HAS_BEAUTIFULSOUP:
            return ExtractionResult(
                success=False, errors=["BeautifulSoup not available for HTML parsing"]
            )

        try:
            soup = BeautifulSoup(content, "html.parser")

            # Look for JSON data in script tags
            script_tags = soup.find_all("script", type="application/json")
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    return await self._extract_from_json(json.dumps(json_data))
                except:
                    continue

            return ExtractionResult(
                success=False, errors=["No JSON data found in HTML"]
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"HTML extraction error: {e}"]
            )


class BasketballReferenceExtractionStrategy(BaseExtractionStrategy):
    """Basketball Reference-specific content extraction strategy"""

    def __init__(self):
        super().__init__("basketball_reference")
        self._load_bref_schemas()

    def _load_bref_schemas(self) -> None:
        """Load Basketball Reference-specific schemas"""
        self.schemas = {
            "player_stats": {
                "type": "object",
                "required": ["player", "season", "stats"],
                "properties": {
                    "player": {"type": "string"},
                    "season": {"type": "string"},
                    "stats": {"type": "object"},
                },
            },
            "team_stats": {
                "type": "object",
                "required": ["team", "season", "stats"],
                "properties": {
                    "team": {"type": "string"},
                    "season": {"type": "string"},
                    "stats": {"type": "object"},
                },
            },
            "schedule": {
                "type": "object",
                "required": ["games"],
                "properties": {"games": {"type": "array", "items": {"type": "object"}}},
            },
        }

    async def extract(
        self, content: str, content_type: str = "html"
    ) -> ExtractionResult:
        """Extract data from Basketball Reference content"""
        try:
            if content_type == "html":
                return await self._extract_from_html(content)
            else:
                return ExtractionResult(
                    success=False, errors=[f"Unsupported content type: {content_type}"]
                )
        except Exception as e:
            self.logger.error(f"Basketball Reference extraction failed: {e}")
            return ExtractionResult(success=False, errors=[f"Extraction error: {e}"])

    async def _extract_from_html(self, content: str) -> ExtractionResult:
        """Extract data from Basketball Reference HTML"""
        if not HAS_BEAUTIFULSOUP:
            return ExtractionResult(
                success=False, errors=["BeautifulSoup not available for HTML parsing"]
            )

        try:
            soup = BeautifulSoup(content, "html.parser")

            # Determine page type and extract accordingly
            if "per_game" in soup.find("title", {}).get("text", "").lower():
                return await self._extract_player_stats(soup)
            elif "team" in soup.find("title", {}).get("text", "").lower():
                return await self._extract_team_stats(soup)
            elif "schedule" in soup.find("title", {}).get("text", "").lower():
                return await self._extract_schedule(soup)
            else:
                return ExtractionResult(
                    success=False, errors=["Unknown Basketball Reference page type"]
                )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"HTML extraction error: {e}"]
            )

    async def _extract_player_stats(self, soup: BeautifulSoup) -> ExtractionResult:
        """Extract player statistics from Basketball Reference page"""
        try:
            # Find the stats table
            stats_table = soup.find("table", {"id": "per_game"})
            if not stats_table:
                return ExtractionResult(
                    success=False, errors=["Player stats table not found"]
                )

            players = []
            rows = stats_table.find("tbody").find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 10:  # Skip header rows
                    continue

                player_data = {
                    "player": cells[0].get_text(strip=True),
                    "season": "2024-25",  # Extract from URL or page
                    "stats": {
                        "games": self._parse_number(cells[1].get_text()),
                        "minutes_per_game": self._parse_number(cells[2].get_text()),
                        "field_goals": self._parse_number(cells[3].get_text()),
                        "field_goal_attempts": self._parse_number(cells[4].get_text()),
                        "field_goal_percentage": self._parse_number(
                            cells[5].get_text()
                        ),
                        "three_pointers": self._parse_number(cells[6].get_text()),
                        "three_point_attempts": self._parse_number(cells[7].get_text()),
                        "three_point_percentage": self._parse_number(
                            cells[8].get_text()
                        ),
                        "free_throws": self._parse_number(cells[9].get_text()),
                        "free_throw_attempts": self._parse_number(cells[10].get_text()),
                        "free_throw_percentage": self._parse_number(
                            cells[11].get_text()
                        ),
                        "rebounds": self._parse_number(cells[12].get_text()),
                        "assists": self._parse_number(cells[13].get_text()),
                        "steals": self._parse_number(cells[14].get_text()),
                        "blocks": self._parse_number(cells[15].get_text()),
                        "turnovers": self._parse_number(cells[16].get_text()),
                        "points": self._parse_number(cells[17].get_text()),
                    },
                }
                players.append(player_data)

            return ExtractionResult(
                success=True,
                data={"players": players},
                confidence=0.85,
                extraction_method="bref_player_stats_parser",
                metadata={"total_players": len(players)},
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"Player stats extraction error: {e}"]
            )

    async def _extract_team_stats(self, soup: BeautifulSoup) -> ExtractionResult:
        """Extract team statistics from Basketball Reference page"""
        try:
            # Find the team stats table
            stats_table = soup.find("table", {"id": "team_stats"})
            if not stats_table:
                return ExtractionResult(
                    success=False, errors=["Team stats table not found"]
                )

            teams = []
            rows = stats_table.find("tbody").find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 10:
                    continue

                team_data = {
                    "team": cells[0].get_text(strip=True),
                    "season": "2024-25",
                    "stats": {
                        "games": self._parse_number(cells[1].get_text()),
                        "minutes": self._parse_number(cells[2].get_text()),
                        "field_goals": self._parse_number(cells[3].get_text()),
                        "field_goal_attempts": self._parse_number(cells[4].get_text()),
                        "field_goal_percentage": self._parse_number(
                            cells[5].get_text()
                        ),
                        "three_pointers": self._parse_number(cells[6].get_text()),
                        "three_point_attempts": self._parse_number(cells[7].get_text()),
                        "three_point_percentage": self._parse_number(
                            cells[8].get_text()
                        ),
                        "free_throws": self._parse_number(cells[9].get_text()),
                        "free_throw_attempts": self._parse_number(cells[10].get_text()),
                        "free_throw_percentage": self._parse_number(
                            cells[11].get_text()
                        ),
                        "rebounds": self._parse_number(cells[12].get_text()),
                        "assists": self._parse_number(cells[13].get_text()),
                        "steals": self._parse_number(cells[14].get_text()),
                        "blocks": self._parse_number(cells[15].get_text()),
                        "turnovers": self._parse_number(cells[16].get_text()),
                        "points": self._parse_number(cells[17].get_text()),
                    },
                }
                teams.append(team_data)

            return ExtractionResult(
                success=True,
                data={"teams": teams},
                confidence=0.85,
                extraction_method="bref_team_stats_parser",
                metadata={"total_teams": len(teams)},
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"Team stats extraction error: {e}"]
            )

    async def _extract_schedule(self, soup: BeautifulSoup) -> ExtractionResult:
        """Extract schedule data from Basketball Reference page"""
        try:
            # Find the schedule table
            schedule_table = soup.find("table", {"id": "schedule"})
            if not schedule_table:
                return ExtractionResult(
                    success=False, errors=["Schedule table not found"]
                )

            games = []
            rows = schedule_table.find("tbody").find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 8:
                    continue

                game_data = {
                    "date": cells[0].get_text(strip=True),
                    "time": cells[1].get_text(strip=True),
                    "visitor": cells[2].get_text(strip=True),
                    "visitor_score": self._parse_number(cells[3].get_text()),
                    "home": cells[4].get_text(strip=True),
                    "home_score": self._parse_number(cells[5].get_text()),
                    "box_score": (
                        cells[6].find("a")["href"] if cells[6].find("a") else None
                    ),
                    "attendance": (
                        self._parse_number(cells[7].get_text())
                        if len(cells) > 7
                        else None
                    ),
                }
                games.append(game_data)

            return ExtractionResult(
                success=True,
                data={"games": games},
                confidence=0.9,
                extraction_method="bref_schedule_parser",
                metadata={"total_games": len(games)},
            )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"Schedule extraction error: {e}"]
            )

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text, handling Basketball Reference formatting"""
        if not text or text == "":
            return None

        # Remove common Basketball Reference formatting
        text = text.replace(",", "").replace("%", "").strip()

        try:
            return float(text)
        except ValueError:
            return None


class LLMExtractionStrategy(BaseExtractionStrategy):
    """LLM-based extraction strategy using Google Gemini"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("llm")
        self.api_key = api_key
        self.model = None

        if HAS_GOOGLE_AI and api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")

    async def extract(
        self,
        content: str,
        content_type: str = "html",
        instruction: str = "Extract structured NBA data",
    ) -> ExtractionResult:
        """Extract data using LLM"""
        if not self.model:
            return ExtractionResult(
                success=False, errors=["Google AI model not configured"]
            )

        try:
            # Prepare prompt for LLM
            prompt = f"""
            {instruction}

            Content to extract from:
            {content[:4000]}  # Limit content size

            Please extract structured data in JSON format with the following structure:
            {{
                "data": {{
                    // Extracted structured data here
                }},
                "confidence": 0.0-1.0,
                "extraction_method": "llm_gemini"
            }}
            """

            # Call LLM
            response = await asyncio.to_thread(self.model.generate_content, prompt)

            # Parse LLM response
            response_text = response.text

            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group())

                return ExtractionResult(
                    success=True,
                    data=extracted_data.get("data"),
                    confidence=extracted_data.get("confidence", 0.7),
                    extraction_method="llm_gemini",
                    metadata={"llm_response": response_text[:500]},
                )
            else:
                return ExtractionResult(
                    success=False, errors=["No JSON found in LLM response"]
                )

        except Exception as e:
            return ExtractionResult(
                success=False, errors=[f"LLM extraction error: {e}"]
            )


class ExtractionManager:
    """Manages multiple extraction strategies"""

    def __init__(self):
        self.strategies: Dict[str, BaseExtractionStrategy] = {}
        self.logger = logging.getLogger("extraction_manager")

    def add_strategy(self, name: str, strategy: BaseExtractionStrategy) -> None:
        """Add an extraction strategy"""
        self.strategies[name] = strategy
        self.logger.info(f"Added extraction strategy: {name}")

    async def extract_with_fallback(
        self, content: str, content_type: str = "html", preferred_strategy: str = None
    ) -> ExtractionResult:
        """Extract data with fallback strategies"""
        strategies_to_try = []

        if preferred_strategy and preferred_strategy in self.strategies:
            strategies_to_try.append(preferred_strategy)

        # Add other strategies as fallbacks
        for name in self.strategies:
            if name != preferred_strategy:
                strategies_to_try.append(name)

        last_error = None

        for strategy_name in strategies_to_try:
            try:
                strategy = self.strategies[strategy_name]
                result = await strategy.extract(content, content_type)

                if result.success:
                    self.logger.info(f"Extraction successful with {strategy_name}")
                    return result
                else:
                    last_error = result.errors
                    self.logger.warning(
                        f"Extraction failed with {strategy_name}: {result.errors}"
                    )

            except Exception as e:
                last_error = [str(e)]
                self.logger.error(f"Strategy {strategy_name} failed: {e}")

        return ExtractionResult(
            success=False, errors=last_error or ["All extraction strategies failed"]
        )


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create extraction manager
        manager = ExtractionManager()

        # Add strategies
        manager.add_strategy("espn", ESPNExtractionStrategy())
        manager.add_strategy(
            "basketball_reference", BasketballReferenceExtractionStrategy()
        )

        # Example ESPN JSON content
        espn_content = """
        {
            "events": [
                {
                    "id": "12345",
                    "date": "2024-10-13",
                    "competitions": [{
                        "competitors": [
                            {
                                "id": "1",
                                "team": {"displayName": "Lakers"},
                                "score": "110"
                            },
                            {
                                "id": "2",
                                "team": {"displayName": "Warriors"},
                                "score": "108"
                            }
                        ]
                    }]
                }
            ]
        }
        """

        # Extract with ESPN strategy
        result = await manager.extract_with_fallback(
            espn_content, content_type="json", preferred_strategy="espn"
        )

        print(f"Extraction success: {result.success}")
        print(f"Confidence: {result.confidence}")
        print(f"Method: {result.extraction_method}")
        if result.data:
            print(f"Games found: {len(result.data.get('games', []))}")

    asyncio.run(example_usage())





