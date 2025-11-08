"""
ESPN Feature Extractor - Complete 58-Feature Extraction from S3

Extracts all 58 ESPN features from JSON files stored in S3:
- 20 game-level features (season_type, venue, attendance, officials, etc.)
- 25 player box score features (all traditional stats)
- 13 play-by-play features (coordinates, event types, etc.)

Includes both direct extraction (48 features) and derived calculation (9 features).

Usage:
    from nba_simulator.etl.extractors.espn import ESPNFeatureExtractor

    extractor = ESPNFeatureExtractor()
    features = extractor.extract_game_features(game_id="401468003")

    # Or batch extraction
    features_batch = extractor.batch_extract_games(game_ids=["401468003", "401468004"])
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import logging
import boto3
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

# Relative imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from nba_simulator.config import config


class ESPNJSONReader:
    """
    Reads ESPN JSON files from S3 with caching and parallel loading support.
    """

    def __init__(self, bucket: str = None, cache_dir: str = None):
        """
        Initialize ESPN JSON reader.

        Args:
            bucket: S3 bucket name (defaults to config)
            cache_dir: Local cache directory (optional)
        """
        s3_config = config.load_s3_config()
        self.bucket = bucket or s3_config["bucket"]
        self.cache_dir = Path(cache_dir) if cache_dir else None

        # Initialize S3 client
        aws_config = config.load_aws_config()
        self.s3_client = boto3.client(
            "s3",
            region_name=s3_config["region"],
            aws_access_key_id=aws_config.get("access_key_id"),
            aws_secret_access_key=aws_config.get("secret_access_key"),
        )

        self.logger = logging.getLogger(__name__)

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Cache enabled at {self.cache_dir}")

    def read_game(self, game_id: str, s3_prefix: str = "box_scores") -> Optional[Dict]:
        """
        Read ESPN JSON for a single game from S3.

        Args:
            game_id: ESPN game ID
            s3_prefix: S3 key prefix (default: "box_scores")

        Returns:
            Parsed JSON dict, or None if not found
        """
        # Check cache first
        if self.cache_dir:
            cache_file = self.cache_dir / f"{game_id}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, "r") as f:
                        return json.load(f)
                except Exception as e:
                    self.logger.warning(f"Cache read failed for {game_id}: {e}")

        # Read from S3
        s3_key = f"{s3_prefix}/{game_id}.json"

        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            game_data = json.loads(response["Body"].read().decode("utf-8"))

            # Cache for next time
            if self.cache_dir:
                cache_file = self.cache_dir / f"{game_id}.json"
                with open(cache_file, "w") as f:
                    json.dump(game_data, f)

            return game_data

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                self.logger.warning(f"Game {game_id} not found in S3")
            else:
                self.logger.error(f"S3 error reading {game_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading {game_id}: {e}")
            return None

    def batch_read_games(
        self, game_ids: List[str], max_workers: int = 10
    ) -> Dict[str, Optional[Dict]]:
        """
        Read multiple games in parallel.

        Args:
            game_ids: List of ESPN game IDs
            max_workers: Number of parallel threads

        Returns:
            Dict mapping game_id → parsed JSON (or None if failed)
        """
        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_game_id = {
                executor.submit(self.read_game, game_id): game_id
                for game_id in game_ids
            }

            for future in as_completed(future_to_game_id):
                game_id = future_to_game_id[future]
                try:
                    results[game_id] = future.result()
                except Exception as e:
                    self.logger.error(f"Error loading {game_id}: {e}")
                    results[game_id] = None

        return results


class ESPNFeatureExtractor:
    """
    Extracts all 58 ESPN features from JSON files.

    Handles 3 feature categories:
    - Direct extraction (48 features from JSON)
    - Derived calculation (9 features computed from extracted data)
    - Missing data handling (graceful NULL insertion)
    """

    def __init__(self, reader: ESPNJSONReader = None):
        """
        Initialize feature extractor.

        Args:
            reader: ESPNJSONReader instance (creates new if None)
        """
        self.reader = reader or ESPNJSONReader()
        self.logger = logging.getLogger(__name__)

    def _detect_format(self, raw_json: Dict) -> int:
        """
        Detect ESPN JSON format.

        Returns:
            1: Format 1 (page.content.gamepackage) - older games ~1993-2019
            2: Format 2 (boxscore top-level) - newer games ~2020+
            0: Unknown format
        """
        if "page" in raw_json and isinstance(raw_json.get("page"), dict):
            content = raw_json["page"].get("content", {})
            if "gamepackage" in content:
                return 1

        if "boxscore" in raw_json and "header" in raw_json:
            return 2

        return 0

    def extract_game_features(
        self, game_id: str = None, raw_json: Dict = None
    ) -> Dict[str, Any]:
        """
        Extract all 58 features for a game (supports both Format 1 and Format 2).

        Args:
            game_id: ESPN game ID (if reading from S3)
            raw_json: Pre-loaded JSON (if already in memory)

        Returns:
            Dict with complete JSONB structure for raw_data.nba_games
        """
        # Load JSON if needed
        if raw_json is None:
            if game_id is None:
                raise ValueError("Must provide either game_id or raw_json")
            raw_json = self.reader.read_game(game_id)
            if raw_json is None:
                return None

        # Detect format
        format_version = self._detect_format(raw_json)

        if format_version == 1:
            return self._extract_features_format1(raw_json, game_id)
        elif format_version == 2:
            return self._extract_features_format2(raw_json, game_id)
        else:
            self.logger.error(f"Unknown JSON format for game {game_id}")
            return None

    def _extract_features_format1(
        self, raw_json: Dict, game_id: str = None
    ) -> Dict[str, Any]:
        """Extract features from Format 1 (page.content.gamepackage)"""
        try:
            gp = raw_json["page"]["content"]["gamepackage"]
        except KeyError:
            self.logger.error(f"Invalid Format 1 structure for game {game_id}")
            return None

        # Extract all feature categories
        features = {
            "game_info": self._extract_game_info(gp),
            "scoring": self._extract_linescores(gp),
            "venue": self._extract_venue(gp),
            "officials": self._extract_officials(gp),
            "box_score": self._extract_box_score(gp),
            "plays_summary": self._extract_plays_summary(gp),
            "source_data": {
                "source": "ESPN",
                "format": 1,
                "original_game_id": game_id or self._safe_get(gp, ["gmStrp", "gid"]),
                "s3_key": f"box_scores/{game_id}.json" if game_id else None,
            },
        }

        return features

    def _extract_features_format2(
        self, raw_json: Dict, game_id: str = None
    ) -> Dict[str, Any]:
        """Extract features from Format 2 (boxscore top-level)"""
        # Extract all feature categories
        features = {
            "game_info": self._extract_game_info_format2(raw_json),
            "scoring": self._extract_linescores_format2(raw_json),
            "venue": self._extract_venue_format2(raw_json),
            "officials": self._extract_officials_format2(raw_json),
            "box_score": self._extract_box_score_format2(raw_json),
            "plays_summary": self._extract_plays_summary_format2(raw_json),
            "source_data": {
                "source": "ESPN",
                "format": 2,
                "original_game_id": game_id
                or self._safe_get(raw_json, ["header", "id"]),
                "s3_key": f"box_scores/{game_id}.json" if game_id else None,
            },
        }

        return features

    # ========================================================================
    # Game-Level Features (20 total)
    # ========================================================================

    def _extract_game_info(self, gp: Dict) -> Dict[str, Any]:
        """Extract game info features (7 features + 2 derived)"""
        gm_strip = gp.get("gmStrp", {})
        gm_info = gp.get("gmInfo", {})

        # Extract linescores to determine overtime
        home_linescores = self._safe_get(gm_strip, ["tms", 0, "linescores"], [])
        away_linescores = self._safe_get(gm_strip, ["tms", 1, "linescores"], [])

        # Get scores for margin calculation (convert to int)
        home_score = self._safe_get_int(gm_strip, ["tms", 0, "score"])
        away_score = self._safe_get_int(gm_strip, ["tms", 1, "score"])

        return {
            "game_id": self._safe_get(gm_strip, ["gid"]),
            "game_date": self._safe_get(gm_strip, ["dt"]),
            "season": self._extract_season(self._safe_get(gm_strip, ["dt"])),
            "season_year": self._extract_season_year(self._safe_get(gm_strip, ["dt"])),
            "season_type": self._safe_get(gm_strip, ["seasonType"]),
            "attendance": self._safe_get_int(gm_info, ["attnd"]),
            "broadcast": self._extract_broadcast(gm_info),
            # Derived features
            "overtime": len(home_linescores) > 4 or len(away_linescores) > 4,
            "margin_of_victory": (
                abs(home_score - away_score)
                if (home_score is not None and away_score is not None)
                else None
            ),
        }

    def _extract_linescores(self, gp: Dict) -> Dict[str, Dict]:
        """Extract quarter-by-quarter scores (8 features)"""
        gm_strip = gp.get("gmStrp", {})

        home_linescores = self._safe_get(gm_strip, ["tms", 0, "linescores"], [])
        away_linescores = self._safe_get(gm_strip, ["tms", 1, "linescores"], [])

        def extract_quarters(linescores: List[Dict]) -> List[int]:
            """Extract quarter scores from linescores array"""
            quarters = []
            for ls in linescores:
                value = ls.get("displayValue")
                if value and value.isdigit():
                    quarters.append(int(value))
            return quarters

        home_quarters = extract_quarters(home_linescores)
        away_quarters = extract_quarters(away_linescores)

        return {
            "home": {
                "quarters": home_quarters,
                "total": self._safe_get_int(gm_strip, ["tms", 0, "score"]),
            },
            "away": {
                "quarters": away_quarters,
                "total": self._safe_get_int(gm_strip, ["tms", 1, "score"]),
            },
        }

    def _extract_venue(self, gp: Dict) -> Dict[str, str]:
        """Extract venue information (2 features)"""
        gm_info = gp.get("gmInfo", {})
        venue = gm_info.get("venue", {})

        return {
            "name": venue.get("fullName"),
            "city": venue.get("address", {}).get("city"),
            "state": venue.get("address", {}).get("state"),
        }

    def _extract_officials(self, gp: Dict) -> List[Dict[str, str]]:
        """Extract officials/referees (1+ features)"""
        gm_info = gp.get("gmInfo", {})
        refs = gm_info.get("refs", [])

        officials = []
        for ref in refs:
            if isinstance(ref, dict):
                officials.append(
                    {
                        "name": ref.get("dspNm") or ref.get("name"),
                        "number": ref.get("number"),
                    }
                )
            elif isinstance(ref, str):
                officials.append({"name": ref, "number": None})

        return officials

    def _extract_broadcast(self, gm_info: Dict) -> List[str]:
        """Extract broadcast networks (1 feature)"""
        coverage = gm_info.get("cvrg", [])

        if isinstance(coverage, list):
            return [
                c.get("name") for c in coverage if isinstance(c, dict) and c.get("name")
            ]
        elif isinstance(coverage, str):
            return [coverage]
        return []

    # ========================================================================
    # Player Box Score Features (25 total)
    # ========================================================================

    def _extract_box_score(self, gp: Dict) -> Dict[str, Dict]:
        """Extract complete box score for both teams (25 features per player)"""
        bxscr = gp.get("bxscr", [])

        if len(bxscr) < 2:
            return {"home": {"players": []}, "away": {"players": []}}

        result = {
            "home": self._extract_team_box_score(bxscr[0]),
            "away": self._extract_team_box_score(bxscr[1]),
        }

        return result

    def _extract_team_box_score(self, team_bxscr: Dict) -> Dict:
        """Extract box score for one team"""
        stats_groups = team_bxscr.get("stats", [])
        team_info = team_bxscr.get("tm", {})

        players = []

        for group in stats_groups:
            is_starter = group.get("type") == "starters"
            keys = group.get("keys", [])
            labels = group.get("lbls", [])
            athletes = group.get("athlts", [])

            for athlete_data in athletes:
                player = self._parse_player(athlete_data, keys, is_starter)
                if player:
                    players.append(player)

        return {
            "team_id": str(team_info.get("id")),
            "team_name": team_info.get("displayName") or team_info.get("name"),
            "team_abbreviation": team_info.get("abbrev"),
            "players": players,
        }

    def _parse_player(
        self, athlete_data: Dict, keys: List[str], is_starter: bool
    ) -> Optional[Dict]:
        """Parse individual player stats (25 features)"""
        athlt = athlete_data.get("athlt", {})
        stats = athlete_data.get("stats", [])

        if not athlt or not stats:
            return None

        player = {
            "player_id": str(athlt.get("id")),
            "name": athlt.get("dspNm") or athlt.get("name"),
            "jersey": athlt.get("jersey"),
            "position": athlt.get("pos"),
            "starter": is_starter,
            "stats": {},
        }

        # Parse stats using key index
        stat_map = {
            "minutes": "minutes",
            "fieldGoalsMade-fieldGoalsAttempted": "field_goals",
            "threePointFieldGoalsMade-threePointFieldGoalsAttempted": "three_pointers",
            "freeThrowsMade-freeThrowsAttempted": "free_throws",
            "offensiveRebounds": "offensive_rebounds",
            "defensiveRebounds": "defensive_rebounds",
            "rebounds": "rebounds",
            "assists": "assists",
            "steals": "steals",
            "blocks": "blocks",
            "turnovers": "turnovers",
            "fouls": "fouls",
            "plusMinus": "plus_minus",
            "points": "points",
        }

        for key, stat_name in stat_map.items():
            try:
                idx = keys.index(key)
                value = stats[idx]

                if "-" in str(value):
                    # Parse "made-attempted" format
                    made, attempted = value.split("-")
                    if stat_name == "field_goals":
                        player["stats"]["field_goals_made"] = int(made)
                        player["stats"]["field_goals_attempted"] = int(attempted)
                    elif stat_name == "three_pointers":
                        player["stats"]["three_pointers_made"] = int(made)
                        player["stats"]["three_pointers_attempted"] = int(attempted)
                    elif stat_name == "free_throws":
                        player["stats"]["free_throws_made"] = int(made)
                        player["stats"]["free_throws_attempted"] = int(attempted)
                elif value and str(value).strip() not in ["", "--", "DNP"]:
                    # Direct integer value
                    player["stats"][stat_name] = int(value) if value != "--" else 0

            except (ValueError, IndexError, KeyError):
                continue

        # Calculate derived stats (5 features: FG%, 3P%, FT%, double-double, triple-double)
        player["stats"].update(self._calculate_player_derived_stats(player["stats"]))

        return player

    # ========================================================================
    # Play-by-Play Features (13 total)
    # ========================================================================

    def _extract_plays_summary(self, gp: Dict) -> Dict[str, Any]:
        """Extract play-by-play summary (13 features - detailed extraction)"""
        pbp = gp.get("pbp", {})

        if not pbp:
            return {"total_plays": 0, "periods": 0, "event_types": {}, "plays": []}

        # Get play groups (nested by period)
        play_groups = pbp.get("playGrps", [])

        all_plays = []
        event_type_counts = {}

        for period_idx, period_plays in enumerate(play_groups):
            if isinstance(period_plays, list):
                for play in period_plays:
                    play_data = self._parse_play(play, period_idx + 1)
                    if play_data:
                        all_plays.append(play_data)

                        # Count event types
                        event_type = play_data.get("event_type")
                        if event_type:
                            event_type_counts[event_type] = (
                                event_type_counts.get(event_type, 0) + 1
                            )

        return {
            "total_plays": len(all_plays),
            "periods": len(play_groups),
            "event_types": event_type_counts,
            "plays": all_plays[:100],  # Store first 100 plays (summary)
        }

    def _parse_play(self, play: Dict, period: int) -> Optional[Dict]:
        """Parse individual play data"""
        if not isinstance(play, dict):
            return None

        play_data = {
            "period": period,
            "clock": self._safe_get(play, ["clock", "displayValue"]),
            "team": self._safe_get(play, ["team", "abbreviation"]),
            "event_type": self._safe_get(play, ["type", "text"]),
            "description": play.get("text"),
            "scoring_play": play.get("scoringPlay", False),
            "shot_value": self._extract_shot_value(play),
            "coordinates": self._extract_coordinates(play),
            "participants": self._extract_participants(play),
        }

        return play_data

    def _extract_shot_value(self, play: Dict) -> Optional[int]:
        """Extract shot value (2 or 3 points)"""
        text = play.get("text", "")
        if "3-pt" in text or "three point" in text.lower():
            return 3
        elif "made" in text.lower() or "missed" in text.lower():
            return 2
        return None

    def _extract_coordinates(self, play: Dict) -> Optional[Dict[str, float]]:
        """Extract shot coordinates"""
        coords = play.get("coordinate", {}) or play.get("coordinates", {})
        if coords and "x" in coords and "y" in coords:
            return {"x": float(coords["x"]), "y": float(coords["y"])}
        return None

    def _extract_participants(self, play: Dict) -> List[Dict]:
        """Extract play participants (assists, etc.)"""
        participants = play.get("participants", [])
        result = []

        for p in participants:
            if isinstance(p, dict):
                result.append(
                    {
                        "athlete_id": str(p.get("athlete", {}).get("id")),
                        "type": p.get("type"),
                    }
                )

        return result

    # ========================================================================
    # Derived Features (9 total)
    # ========================================================================

    def _calculate_player_derived_stats(self, stats: Dict) -> Dict[str, Any]:
        """Calculate derived player stats (5 features)"""
        derived = {}

        # Shooting percentages (3 features) - handle None values
        fg_made = stats.get("field_goals_made") or 0
        fg_attempted = stats.get("field_goals_attempted") or 0
        if fg_attempted > 0:
            derived["field_goal_pct"] = round(fg_made / fg_attempted, 3)

        three_made = stats.get("three_pointers_made") or 0
        three_attempted = stats.get("three_pointers_attempted") or 0
        if three_attempted > 0:
            derived["three_point_pct"] = round(three_made / three_attempted, 3)

        ft_made = stats.get("free_throws_made") or 0
        ft_attempted = stats.get("free_throws_attempted") or 0
        if ft_attempted > 0:
            derived["free_throw_pct"] = round(ft_made / ft_attempted, 3)

        # Double-double / triple-double (2 features) - handle None values
        points = stats.get("points") or 0
        rebounds = stats.get("rebounds") or 0
        assists = stats.get("assists") or 0
        steals = stats.get("steals") or 0
        blocks = stats.get("blocks") or 0

        double_digit_stats = sum(
            [points >= 10, rebounds >= 10, assists >= 10, steals >= 10, blocks >= 10]
        )

        derived["double_double"] = double_digit_stats >= 2
        derived["triple_double"] = double_digit_stats >= 3

        return derived

    def calculate_shot_distance(
        self, x: float, y: float, hoop_x: float = 25, hoop_y: float = 5.25
    ) -> float:
        """
        Calculate shot distance from coordinates.

        Args:
            x: Shot x coordinate
            y: Shot y coordinate
            hoop_x: Hoop x coordinate (default: 25 ft)
            hoop_y: Hoop y coordinate (default: 5.25 ft from baseline)

        Returns:
            Distance in feet
        """
        return math.sqrt((x - hoop_x) ** 2 + (y - hoop_y) ** 2)

    # ========================================================================
    # Format 2 Extraction Methods (boxscore top-level)
    # ========================================================================

    def _extract_game_info_format2(self, raw_json: Dict) -> Dict[str, Any]:
        """Extract game info features from Format 2 (7 features + 2 derived)"""
        header = raw_json.get("header", {})
        competition = self._safe_get(header, ["competitions", 0], {})
        competitors = competition.get("competitors", [])

        # Get home/away scores for margin calculation
        home_score = None
        away_score = None
        home_linescores = []
        away_linescores = []

        for comp in competitors:
            if comp.get("homeAway") == "home":
                home_score = self._safe_get_int(comp, ["score"])
                home_linescores = comp.get("linescores", [])
            elif comp.get("homeAway") == "away":
                away_score = self._safe_get_int(comp, ["score"])
                away_linescores = comp.get("linescores", [])

        game_date = competition.get("date")

        # Extract attendance and broadcast from gameInfo
        game_info_section = raw_json.get("gameInfo", {})

        return {
            "game_id": header.get("id"),
            "game_date": game_date,
            "season": self._extract_season(game_date),
            "season_year": self._extract_season_year(game_date),
            "season_type": self._safe_get(header, ["season", "type"]),
            "attendance": game_info_section.get("attendance"),
            "broadcast": self._extract_broadcast_format2(raw_json),
            # Derived features
            "overtime": len(home_linescores) > 4 or len(away_linescores) > 4,
            "margin_of_victory": (
                abs(home_score - away_score)
                if (home_score is not None and away_score is not None)
                else None
            ),
        }

    def _extract_linescores_format2(self, raw_json: Dict) -> Dict[str, Dict]:
        """Extract quarter-by-quarter scores from Format 2 (8 features)"""
        header = raw_json.get("header", {})
        competition = self._safe_get(header, ["competitions", 0], {})
        competitors = competition.get("competitors", [])

        home_quarters = []
        away_quarters = []
        home_total = None
        away_total = None

        for comp in competitors:
            linescores = comp.get("linescores", [])
            quarters = [
                self._safe_get_int({"score": ls.get("displayValue")}, ["score"])
                for ls in linescores
            ]

            if comp.get("homeAway") == "home":
                home_quarters = quarters
                home_total = self._safe_get_int(comp, ["score"])
            elif comp.get("homeAway") == "away":
                away_quarters = quarters
                away_total = self._safe_get_int(comp, ["score"])

        return {
            "home": {"quarters": home_quarters, "total": home_total},
            "away": {"quarters": away_quarters, "total": away_total},
        }

    def _extract_venue_format2(self, raw_json: Dict) -> Dict[str, Any]:
        """Extract venue information from Format 2 (3 features)"""
        game_info = raw_json.get("gameInfo", {})
        venue = game_info.get("venue", {})
        address = venue.get("address", {})

        return {
            "name": venue.get("fullName"),
            "city": address.get("city"),
            "state": address.get("state"),
        }

    def _extract_officials_format2(self, raw_json: Dict) -> List[Dict]:
        """Extract officials from Format 2 (1 feature)"""
        game_info = raw_json.get("gameInfo", {})
        officials_raw = game_info.get("officials", [])

        return [
            {"name": official.get("fullName"), "number": official.get("number")}
            for official in officials_raw
        ]

    def _extract_box_score_format2(self, raw_json: Dict) -> Dict[str, Dict]:
        """Extract player box score stats from Format 2 (25 features)"""
        boxscore = raw_json.get("boxscore", {})
        players_data = boxscore.get("players", [])

        result = {"home": {"players": []}, "away": {"players": []}}

        for team_group in players_data:
            team = team_group.get("team", {})
            home_away = team_group.get("displayOrder")  # 1 = home, 2 = away

            # Get stat definitions
            statistics = team_group.get("statistics", [])
            if not statistics:
                continue

            stat_group = statistics[0]  # Usually only one stat group
            stat_labels = stat_group.get("labels", [])
            stat_keys = stat_group.get("keys", [])

            # Process each athlete
            athletes = stat_group.get("athletes", [])
            for athlete_data in athletes:
                player = self._parse_player_format2(
                    athlete_data, stat_keys, stat_labels
                )

                # Add to home or away
                if home_away == 1:
                    result["home"]["players"].append(player)
                elif home_away == 2:
                    result["away"]["players"].append(player)

        return result

    def _parse_player_format2(
        self, athlete_data: Dict, stat_keys: List[str], stat_labels: List[str]
    ) -> Dict:
        """Parse individual player from Format 2"""
        athlete = athlete_data.get("athlete", {})
        stats_raw = athlete_data.get("stats", [])

        # Build stat dict from keys and values
        stats_dict = {}
        for i, key in enumerate(stat_keys):
            if i < len(stats_raw):
                stats_dict[key] = stats_raw[i]

        # Helper to parse "X-Y" format strings
        def parse_made_attempted(value_str):
            """Parse '2-4' into (2, 4)"""
            if not value_str or "-" not in value_str:
                return None, None
            try:
                parts = value_str.split("-")
                return int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                return None, None

        # Parse field goals
        fg_made, fg_attempted = parse_made_attempted(
            stats_dict.get("fieldGoalsMade-fieldGoalsAttempted")
        )

        # Parse three pointers
        three_made, three_attempted = parse_made_attempted(
            stats_dict.get("threePointFieldGoalsMade-threePointFieldGoalsAttempted")
        )

        # Parse free throws
        ft_made, ft_attempted = parse_made_attempted(
            stats_dict.get("freeThrowsMade-freeThrowsAttempted")
        )

        # Extract standard stats
        stats = {
            "minutes": stats_dict.get("minutes"),
            "field_goals_made": fg_made,
            "field_goals_attempted": fg_attempted,
            "three_pointers_made": three_made,
            "three_pointers_attempted": three_attempted,
            "free_throws_made": ft_made,
            "free_throws_attempted": ft_attempted,
            "offensive_rebounds": self._safe_get_int(
                {"val": stats_dict.get("offensiveRebounds")}, ["val"]
            ),
            "defensive_rebounds": self._safe_get_int(
                {"val": stats_dict.get("defensiveRebounds")}, ["val"]
            ),
            "rebounds": self._safe_get_int(
                {"val": stats_dict.get("rebounds")}, ["val"]
            ),
            "assists": self._safe_get_int({"val": stats_dict.get("assists")}, ["val"]),
            "steals": self._safe_get_int({"val": stats_dict.get("steals")}, ["val"]),
            "blocks": self._safe_get_int({"val": stats_dict.get("blocks")}, ["val"]),
            "turnovers": self._safe_get_int(
                {"val": stats_dict.get("turnovers")}, ["val"]
            ),
            "personal_fouls": self._safe_get_int(
                {"val": stats_dict.get("fouls")}, ["val"]
            ),
            "points": self._safe_get_int({"val": stats_dict.get("points")}, ["val"]),
            "plus_minus": self._safe_get_int(
                {"val": stats_dict.get("plusMinus")}, ["val"]
            ),
        }

        # Calculate derived stats
        derived = self._calculate_player_derived_stats(stats)
        stats.update(derived)

        return {
            "player_id": athlete.get("id"),
            "name": athlete.get("displayName"),
            "position": athlete.get("position", {}).get("abbreviation"),
            "jersey": athlete.get("jersey"),
            "starter": athlete_data.get("starter", False),
            "stats": stats,
        }

    def _extract_plays_summary_format2(self, raw_json: Dict) -> Dict[str, Any]:
        """Extract play-by-play summary from Format 2 (13 features)"""
        plays = raw_json.get("plays", [])

        if not plays:
            return {"total_plays": 0, "periods": 0, "event_types": {}}

        # Count event types
        event_types = {}
        for play in plays:
            event_type = play.get("type", {}).get("text", "Unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Get max period
        max_period = max(
            [play.get("period", {}).get("number", 0) for play in plays], default=0
        )

        return {
            "total_plays": len(plays),
            "periods": max_period,
            "event_types": event_types,
        }

    def _extract_broadcast_format2(self, raw_json: Dict) -> Optional[str]:
        """Extract broadcast info from Format 2"""
        broadcasts = raw_json.get("broadcasts", [])
        if broadcasts and len(broadcasts) > 0:
            return broadcasts[0].get("name")
        return None

    # ========================================================================
    # Helper Functions
    # ========================================================================

    def _safe_get(self, data: Dict, keys: List[str], default: Any = None) -> Any:
        """Safely navigate nested dict"""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            elif isinstance(current, list) and isinstance(key, int):
                try:
                    current = current[key]
                except IndexError:
                    return default
            else:
                return default
        return current

    def _safe_get_int(
        self, data: Dict, keys: List[str], default: int = None
    ) -> Optional[int]:
        """Safely get integer value"""
        value = self._safe_get(data, keys, default)
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _extract_season(self, game_date: str) -> Optional[str]:
        """Extract season string from game date (e.g., '2023-24')"""
        if not game_date:
            return None
        try:
            dt = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
            year = dt.year
            # NBA season spans October-June, so games after July = next season
            if dt.month >= 10:
                return f"{year}-{str(year + 1)[2:]}"
            else:
                return f"{year - 1}-{str(year)[2:]}"
        except Exception:
            return None

    def _extract_season_year(self, game_date: str) -> Optional[int]:
        """Extract season year from game date"""
        if not game_date:
            return None
        try:
            dt = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
            year = dt.year
            if dt.month >= 10:
                return year
            else:
                return year - 1
        except Exception:
            return None

    def batch_extract_games(self, game_ids: List[str]) -> Dict[str, Dict]:
        """
        Extract features for multiple games in parallel.

        Args:
            game_ids: List of ESPN game IDs

        Returns:
            Dict mapping game_id → features
        """
        # Read all games in parallel
        raw_jsons = self.reader.batch_read_games(game_ids)

        # Extract features for each
        results = {}
        for game_id, raw_json in raw_jsons.items():
            if raw_json:
                features = self.extract_game_features(
                    game_id=game_id, raw_json=raw_json
                )
                results[game_id] = features
            else:
                results[game_id] = None

        return results


# Convenience function
def extract_espn_features(game_id: str) -> Optional[Dict]:
    """
    Convenience function to extract features for a single game.

    Args:
        game_id: ESPN game ID

    Returns:
        Feature dict or None
    """
    extractor = ESPNFeatureExtractor()
    return extractor.extract_game_features(game_id=game_id)
