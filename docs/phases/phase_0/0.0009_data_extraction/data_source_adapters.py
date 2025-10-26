#!/usr/bin/env python3
"""
Data Source Adapters for NBA Data Extraction

Provides adapter classes that parse complex real NBA data files from various sources
and transform them into standardized schema formats.

Adapters:
- ESPNAdapter: Complex nested JSON from ESPN box scores
- NBAAPIAdapter: NBA API team stats and play-by-play data
- BasketballReferenceAdapter: Basketball Reference statistics
- OddsAPIAdapter: Betting odds from Odds API

Generated: 2025-10-23
Purpose: Deep JSON parsing for real data validation
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataSourceAdapter(ABC):
    """
    Abstract base class for data source adapters.

    Each adapter knows how to:
    1. Navigate source-specific JSON structures
    2. Extract data fields
    3. Transform to standardized schemas
    4. Handle missing/malformed data
    """

    @abstractmethod
    def parse_game(self, raw_data: Dict) -> Optional[Dict]:
        """
        Parse game data from source format.

        Args:
            raw_data: Raw data from source

        Returns:
            dict: Game data in standardized format, or None if parsing fails
        """
        pass

    @abstractmethod
    def parse_player_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Parse player stats from source format.

        Args:
            raw_data: Raw data from source

        Returns:
            list: Player stats in standardized format
        """
        pass

    @abstractmethod
    def parse_team_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Parse team stats from source format.

        Args:
            raw_data: Raw data from source

        Returns:
            list: Team stats in standardized format
        """
        pass

    def _safe_get(self, data: Dict, *keys, default=None):
        """
        Safely navigate nested dictionaries.

        Example:
            _safe_get(data, 'page', 'content', 'game', default={})
        """
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current if current is not None else default


class ESPNAdapter(DataSourceAdapter):
    """
    Adapter for ESPN JSON format.

    Handles TWO ESPN formats:
    1. Website Scrape Format (page.content.gamepackage) - 44,830+ files
    2. API Format (boxscore, header, players) - Newer format

    Website Format Structure:
        raw_data['page']['content']['gamepackage']
        ├── gmStrp              # Game strip (basic info)
        ├── bxscr              # Box score (player stats)
        └── gmInfo             # Game info (attendance, venue)

    API Format Structure:
        raw_data
        ├── header              # Game info
        ├── boxscore            # Teams and players
        │   ├── teams[]        # Team stats
        │   └── players[]      # Player stats
        └── gameInfo           # Additional game details
    """

    def _detect_format(self, raw_data: Dict) -> str:
        """Detect which ESPN format this file uses."""
        if "page" in raw_data:
            return "website"
        elif "boxscore" in raw_data and "header" in raw_data:
            return "api"
        else:
            return "unknown"

    def parse_game(self, raw_data: Dict) -> Optional[Dict]:
        """
        Extract game data from ESPN JSON.
        Handles both website scrape and API formats.

        Returns:
            dict: {game_id, date, home_team, away_team, home_score, away_score,
                   attendance, venue, overtime}
        """
        try:
            fmt = self._detect_format(raw_data)

            if fmt == "api":
                return self._parse_game_api_format(raw_data)
            elif fmt == "website":
                return self._parse_game_website_format(raw_data)
            else:
                logger.warning(f"Unknown ESPN format for game parsing")
                return None

        except Exception as e:
            logger.error(f"ESPN game parsing failed: {e}", exc_info=True)
            return None

    def _parse_game_website_format(self, raw_data: Dict) -> Optional[Dict]:
        """Parse game from website scrape format."""
        gamepackage = self._safe_get(
            raw_data, "page", "content", "gamepackage", default={}
        )
        gm_strip = self._safe_get(gamepackage, "gmStrp", default={})
        gm_info = self._safe_get(gamepackage, "gmInfo", default={})

        teams = self._safe_get(gm_strip, "tms", default=[])
        if len(teams) < 2:
            logger.warning("ESPN game missing teams data")
            return None

        home_team = teams[0]
        away_team = teams[1]

        game_data = {
            "game_id": self._safe_get(gm_strip, "gid", default="unknown"),
            "date": self._safe_get(gm_strip, "dt", default=""),
            "home_team": self._safe_get(home_team, "displayName", default="Unknown"),
            "away_team": self._safe_get(away_team, "displayName", default="Unknown"),
            "home_score": self._safe_int_from_str(home_team.get("score", "0")),
            "away_score": self._safe_int_from_str(away_team.get("score", "0")),
        }

        # Optional fields
        if "attendance" in gm_info:
            game_data["attendance"] = self._safe_int(gm_info, "attendance")

        venue = self._safe_get(gm_info, "venue", default={})
        if "fullName" in venue:
            game_data["venue"] = venue["fullName"]

        # Check for overtime
        periods = self._safe_get(gm_strip, "periods", default=[])
        game_data["overtime"] = len(periods) > 4

        return game_data

    def _parse_game_api_format(self, raw_data: Dict) -> Optional[Dict]:
        """Parse game from ESPN API format."""
        header = self._safe_get(raw_data, "header", default={})
        competitions = self._safe_get(header, "competitions", default=[])

        if not competitions:
            logger.warning("ESPN API format missing competitions")
            return None

        competition = competitions[0]
        competitors = self._safe_get(competition, "competitors", default=[])

        if len(competitors) < 2:
            logger.warning("ESPN API format missing competitors")
            return None

        # Find home and away teams
        home_team = None
        away_team = None
        for comp in competitors:
            if comp.get("homeAway") == "home":
                home_team = comp
            elif comp.get("homeAway") == "away":
                away_team = comp

        if not home_team or not away_team:
            # Fallback to first two
            home_team = competitors[0] if len(competitors) > 0 else {}
            away_team = competitors[1] if len(competitors) > 1 else {}

        game_data = {
            "game_id": str(self._safe_get(header, "id", default="unknown")),
            "date": self._safe_get(competition, "date", default=""),
            "home_team": self._safe_get(
                home_team, "team", "displayName", default="Unknown"
            ),
            "away_team": self._safe_get(
                away_team, "team", "displayName", default="Unknown"
            ),
            "home_score": self._safe_int_from_str(home_team.get("score", "0")),
            "away_score": self._safe_int_from_str(away_team.get("score", "0")),
        }

        return game_data

    def parse_player_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Extract player stats from ESPN box score.

        ESPN Structure:
            page.content.gamepackage.bxscr[] (array of 2 teams)
              → stats[] (array of stat groups: starters, bench)
                → athlts[] (array of athletes)
                  → athlt (player info)
                  → stats[] (player stat values)
                → keys[] (column headers)

        Returns:
            list: [{player_id, name, team, points, rebounds, assists, minutes, position}]
        """
        players = []

        try:
            gamepackage = self._safe_get(
                raw_data, "page", "content", "gamepackage", default={}
            )
            bxscr = self._safe_get(gamepackage, "bxscr", default=[])

            # bxscr is a LIST of 2 teams, not a dict
            if not isinstance(bxscr, list):
                logger.warning("ESPN bxscr is not a list")
                return []

            for team_data in bxscr:
                # Get team info
                team_info = self._safe_get(team_data, "tm", default={})
                team_name = self._safe_get(team_info, "dspNm", default="Unknown")

                # Get stat groups (starters, bench, etc.)
                stat_groups = self._safe_get(team_data, "stats", default=[])

                for group in stat_groups:
                    # Get athletes and stat keys for this group
                    athletes = self._safe_get(group, "athlts", default=[])
                    keys = self._safe_get(group, "keys", default=[])

                    # Build key index for easier lookup
                    key_indices = {key: idx for idx, key in enumerate(keys)}

                    for athlete_data in athletes:
                        # Player info is in 'athlt', not 'athlete'
                        player_info = self._safe_get(athlete_data, "athlt", default={})
                        stats = self._safe_get(athlete_data, "stats", default=[])

                        if not player_info or not stats:
                            continue

                        # Extract stats using key indices
                        player = {
                            "player_id": str(
                                self._safe_get(player_info, "id", default="unknown")
                            ),
                            "name": self._safe_get(
                                player_info, "dspNm", default="Unknown"
                            ),
                            "team": team_name,
                        }

                        # Extract specific stats by key name
                        if "PTS" in key_indices and len(stats) > key_indices["PTS"]:
                            player["points"] = self._safe_int_from_str(
                                stats[key_indices["PTS"]]
                            )

                        if "REB" in key_indices and len(stats) > key_indices["REB"]:
                            player["rebounds"] = self._safe_int_from_str(
                                stats[key_indices["REB"]]
                            )

                        if "AST" in key_indices and len(stats) > key_indices["AST"]:
                            player["assists"] = self._safe_int_from_str(
                                stats[key_indices["AST"]]
                            )

                        if "MIN" in key_indices and len(stats) > key_indices["MIN"]:
                            player["minutes"] = self._safe_int_from_str(
                                stats[key_indices["MIN"]]
                            )

                        players.append(player)

            logger.debug(f"ESPN player stats: extracted {len(players)} players")
            return players

        except Exception as e:
            logger.error(f"ESPN player stats parsing failed: {e}", exc_info=True)
            return []

    def parse_team_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Extract team stats from ESPN JSON.
        Handles both website scrape and API formats.

        Returns:
            list: [{team_id, team_name, game_id, points, field_goals_made, ...}]
        """
        try:
            fmt = self._detect_format(raw_data)

            if fmt == "api":
                return self._parse_team_stats_api_format(raw_data)
            elif fmt == "website":
                return self._parse_team_stats_website_format(raw_data)
            else:
                logger.warning(f"Unknown ESPN format for team stats parsing")
                return []

        except Exception as e:
            logger.error(f"ESPN team stats parsing failed: {e}", exc_info=True)
            return []

    def _parse_team_stats_website_format(self, raw_data: Dict) -> List[Dict]:
        """Parse team stats from website scrape format (limited data)."""
        teams = []
        gamepackage = self._safe_get(
            raw_data, "page", "content", "gamepackage", default={}
        )
        gm_strip = self._safe_get(gamepackage, "gmStrp", default={})
        game_id = self._safe_get(gm_strip, "gid", default="unknown")

        teams_data = self._safe_get(gm_strip, "tms", default=[])

        for team_data in teams_data:
            team = {
                "team_id": str(self._safe_get(team_data, "id", default="unknown")),
                "team_name": self._safe_get(
                    team_data, "displayName", default="Unknown"
                ),
                "game_id": game_id,
                "points": self._safe_int_from_str(team_data.get("score", "0")),
                "field_goals_made": 0,
                "field_goals_attempted": 0,
            }
            teams.append(team)

        logger.debug(f"ESPN team stats (website): extracted {len(teams)} teams")
        return teams

    def _parse_team_stats_api_format(self, raw_data: Dict) -> List[Dict]:
        """Parse team stats from ESPN API format (full statistics available)."""
        teams = []

        header = self._safe_get(raw_data, "header", default={})
        game_id = str(self._safe_get(header, "id", default="unknown"))

        boxscore = self._safe_get(raw_data, "boxscore", default={})
        teams_data = self._safe_get(boxscore, "teams", default=[])

        for team_data in teams_data:
            team_info = self._safe_get(team_data, "team", default={})
            statistics = self._safe_get(team_data, "statistics", default=[])

            # Build stats dict from statistics array
            stats_dict = {}
            for stat in statistics:
                name = stat.get("name", "")
                value = stat.get("displayValue", "")
                stats_dict[name] = value

            team = {
                "team_id": str(self._safe_get(team_info, "id", default="unknown")),
                "team_name": self._safe_get(
                    team_info, "displayName", default="Unknown"
                ),
                "game_id": game_id,
                "points": self._parse_stat_value(stats_dict.get("points", "0")),
            }

            # Extract shooting stats (format: "45-90")
            if "fieldGoalsMade-fieldGoalsAttempted" in stats_dict:
                fg = stats_dict["fieldGoalsMade-fieldGoalsAttempted"]
                parts = fg.split("-")
                if len(parts) == 2:
                    team["field_goals_made"] = self._safe_int_from_str(parts[0])
                    team["field_goals_attempted"] = self._safe_int_from_str(parts[1])

            teams.append(team)

        logger.debug(f"ESPN team stats (API): extracted {len(teams)} teams")
        return teams

    def _parse_stat_value(self, value: str) -> int:
        """Parse stat value that might be in various formats."""
        if "-" in str(value):
            # Format like "45-90", take first number
            return self._safe_int_from_str(value.split("-")[0])
        return self._safe_int_from_str(value)

    def _safe_int(self, data: Dict, key: str, default: int = 0) -> int:
        """Safely extract integer from dict."""
        try:
            value = data.get(key, default)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _safe_int_from_str(self, value: Any, default: int = 0) -> int:
        """Safely convert string to int."""
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                # Handle formats like "10-15" (take first number)
                if "-" in value:
                    value = value.split("-")[0]
                return int(value)
            return default
        except (ValueError, TypeError):
            return default

    def _parse_shooting_stat(self, stat_str: str, index: int) -> int:
        """
        Parse shooting stats from format "made-attempted".

        Args:
            stat_str: String like "10-15"
            index: 0 for made, 1 for attempted
        """
        try:
            parts = stat_str.split("-")
            if len(parts) > index:
                return int(parts[index])
            return 0
        except (ValueError, AttributeError):
            return 0


class NBAAPIAdapter(DataSourceAdapter):
    """
    Adapter for NBA API format.

    Handles:
    - nba_team_stats files (44,831 files)
    - nba_pbp files (44,828 files)
    - Simpler structure than ESPN
    """

    def parse_game(self, raw_data: Dict) -> Optional[Dict]:
        """Extract game data from NBA API format."""
        try:
            # NBA API structure is simpler
            header = self._safe_get(raw_data, "header", default={})

            return {
                "game_id": str(self._safe_get(header, "id", default="unknown")),
                "date": self._safe_get(header, "gameDate", default=""),
                "home_team": self._safe_get(
                    header, "homeTeam", "name", default="Unknown"
                ),
                "away_team": self._safe_get(
                    header, "awayTeam", "name", default="Unknown"
                ),
                "home_score": self._safe_int(header.get("homeTeam", {}), "score"),
                "away_score": self._safe_int(header.get("awayTeam", {}), "score"),
            }
        except Exception as e:
            logger.error(f"NBA API game parsing failed: {e}")
            return None

    def parse_player_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Extract player stats from NBA API format.

        NBA API Structure:
            resultSets[] (array of result sets)
              → name: "PlayerStats"
              → headers: ["GAME_ID", "PLAYER_ID", "PLAYER_NAME", ...]
              → rowSet: [row arrays matching headers]
        """
        players = []

        try:
            result_sets = self._safe_get(raw_data, "resultSets", default=[])

            for result_set in result_sets:
                if result_set.get("name") == "PlayerStats":
                    headers = result_set.get("headers", [])
                    row_set = result_set.get("rowSet", [])

                    # Build header index
                    header_idx = {header: idx for idx, header in enumerate(headers)}

                    for row in row_set:
                        if not isinstance(row, list) or len(row) != len(headers):
                            continue

                        player = {
                            "player_id": str(
                                row[header_idx.get("PLAYER_ID", 0)]
                                if "PLAYER_ID" in header_idx
                                else "unknown"
                            ),
                            "name": (
                                row[header_idx.get("PLAYER_NAME", 0)]
                                if "PLAYER_NAME" in header_idx
                                else "Unknown"
                            ),
                            "team": (
                                row[header_idx.get("TEAM_ABBREVIATION", 0)]
                                if "TEAM_ABBREVIATION" in header_idx
                                else "Unknown"
                            ),
                        }

                        # Extract common stats if available
                        if "PTS" in header_idx:
                            player["points"] = self._safe_int_value(
                                row[header_idx["PTS"]]
                            )
                        if "REB" in header_idx:
                            player["rebounds"] = self._safe_int_value(
                                row[header_idx["REB"]]
                            )
                        if "AST" in header_idx:
                            player["assists"] = self._safe_int_value(
                                row[header_idx["AST"]]
                            )
                        if "MIN" in header_idx:
                            # MIN might be in "MM:SS" format, just store as string or convert
                            player["minutes"] = row[header_idx["MIN"]]

                        players.append(player)

            logger.debug(f"NBA API player stats: extracted {len(players)} players")
            return players

        except Exception as e:
            logger.error(f"NBA API player stats parsing failed: {e}", exc_info=True)
            return []

    def _safe_int_value(self, value, default: int = 0) -> int:
        """Safely convert a value to int."""
        try:
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            return default

    def parse_team_stats(self, raw_data: Dict) -> List[Dict]:
        """Extract team stats from NBA API format."""
        try:
            teams = []
            teams_data = self._safe_get(raw_data, "teams", default=[])

            for team_data in teams_data:
                team = {
                    "team_id": str(
                        self._safe_get(team_data, "teamId", default="unknown")
                    ),
                    "team_name": self._safe_get(
                        team_data, "teamName", default="Unknown"
                    ),
                    "game_id": str(
                        self._safe_get(raw_data, "gameId", default="unknown")
                    ),
                    "points": self._safe_int(team_data, "points"),
                    "field_goals_made": self._safe_int(team_data, "fieldGoalsMade"),
                    "field_goals_attempted": self._safe_int(
                        team_data, "fieldGoalsAttempted"
                    ),
                    "rebounds": self._safe_int(team_data, "rebounds"),
                    "assists": self._safe_int(team_data, "assists"),
                }
                teams.append(team)

            return teams
        except Exception as e:
            logger.error(f"NBA API team stats parsing failed: {e}")
            return []

    def _safe_int(self, data: Dict, key: str, default: int = 0) -> int:
        """Safely extract integer from dict."""
        try:
            value = data.get(key, default)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default


class BasketballReferenceAdapter(DataSourceAdapter):
    """
    Adapter for Basketball Reference data.

    Handles:
    - Basketball Reference statistics (444 files)
    - HTML/table-based data converted to JSON
    - TWO STRUCTURES:
      1. Dict format: Game box scores with game_id, date, teams
      2. List format: Player season totals (array of player dicts)
    """

    def parse_game(self, raw_data: Dict) -> Optional[Dict]:
        """
        Extract game data from Basketball Reference format.

        Note: Many BBRef files are player season totals (List format),
        not game box scores. Returns None for non-game files.
        """
        try:
            # Check if this is a list (player totals) vs dict (game data)
            if isinstance(raw_data, list):
                logger.debug(
                    "BBRef file is player season totals array, skipping GAME schema"
                )
                return None

            # Only process if it's a game dict
            if isinstance(raw_data, dict) and "game_id" in raw_data:
                return {
                    "game_id": str(
                        self._safe_get(raw_data, "game_id", default="unknown")
                    ),
                    "date": self._safe_get(raw_data, "date", default=""),
                    "home_team": self._safe_get(
                        raw_data, "home_team", default="Unknown"
                    ),
                    "away_team": self._safe_get(
                        raw_data, "visitor_team", default="Unknown"
                    ),
                    "home_score": self._safe_int(raw_data, "home_score"),
                    "away_score": self._safe_int(raw_data, "visitor_score"),
                }

            logger.debug("BBRef file missing game_id field, not a game box score")
            return None

        except Exception as e:
            logger.error(
                f"Basketball Reference game parsing failed: {e}", exc_info=True
            )
            return None

    def parse_player_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Extract player stats from Basketball Reference format.

        Handles both:
        - List format: Player season totals (most common in our dataset)
        - Dict format: Game box scores
        """
        players = []

        try:
            if isinstance(raw_data, list):
                # Player season totals format
                for player_data in raw_data:
                    if not isinstance(player_data, dict):
                        continue

                    player = {
                        "player_id": player_data.get("slug", "unknown"),
                        "name": player_data.get("name", "Unknown"),
                        "team": (
                            str(player_data.get("team", "Unknown"))
                            if player_data.get("team")
                            else "Unknown"
                        ),
                    }

                    # Extract common stats if available
                    if "points" in player_data:
                        player["points"] = self._safe_int_value(
                            player_data.get("points")
                        )
                    if "total_rebounds" in player_data:
                        player["rebounds"] = self._safe_int_value(
                            player_data.get("total_rebounds")
                        )
                    if "assists" in player_data:
                        player["assists"] = self._safe_int_value(
                            player_data.get("assists")
                        )
                    if "minutes_played" in player_data:
                        player["minutes"] = self._safe_int_value(
                            player_data.get("minutes_played")
                        )

                    players.append(player)

            elif isinstance(raw_data, dict):
                # Game box score format (if it exists)
                # Would need specific structure documentation to implement
                logger.debug("BBRef dict format for player stats not yet implemented")
                pass

            logger.debug(f"BBRef player stats: extracted {len(players)} players")
            return players

        except Exception as e:
            logger.error(
                f"Basketball Reference player stats parsing failed: {e}", exc_info=True
            )
            return []

    def parse_team_stats(self, raw_data: Dict) -> List[Dict]:
        """
        Extract team stats from Basketball Reference format.

        Note: Player season totals files (List format) don't contain team stats.
        Only game box scores (Dict format) would have team stats.
        """
        try:
            # Player totals files don't have team stats
            if isinstance(raw_data, list):
                logger.debug("BBRef player totals file has no team stats")
                return []

            # Game box score format would go here
            if isinstance(raw_data, dict) and "teams" in raw_data:
                # Would need specific structure documentation
                logger.debug("BBRef dict format for team stats not yet implemented")
                return []

            return []

        except Exception as e:
            logger.error(
                f"Basketball Reference team stats parsing failed: {e}", exc_info=True
            )
            return []

    def _safe_int(self, data: Dict, key: str, default: int = 0) -> int:
        """Safely extract integer from dict."""
        try:
            value = data.get(key, default)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _safe_int_value(self, value, default: int = 0) -> int:
        """Safely convert a value to int."""
        try:
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            return default


class OddsAPIAdapter:
    """
    Adapter for Odds API betting data.

    Handles:
    - Betting odds from Odds API
    - Spread, moneyline, over/under data
    """

    def parse_betting_odds(self, raw_data: Dict) -> Optional[Dict]:
        """
        Extract betting odds from Odds API format.

        Returns:
            dict: {game_id, bookmaker, spread, moneyline, over_under}
        """
        try:
            return {
                "game_id": str(self._safe_get(raw_data, "game_id", default="unknown")),
                "bookmaker": self._safe_get(raw_data, "bookmaker", default="Unknown"),
                "spread": float(self._safe_get(raw_data, "spread", default=0.0)),
                "moneyline": self._safe_get(raw_data, "moneyline", default={}),
                "over_under": float(self._safe_get(raw_data, "total", default=0.0)),
            }
        except Exception as e:
            logger.error(f"Odds API parsing failed: {e}")
            return None

    def _safe_get(self, data: Dict, *keys, default=None):
        """Safely navigate nested dictionaries."""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current if current is not None else default
