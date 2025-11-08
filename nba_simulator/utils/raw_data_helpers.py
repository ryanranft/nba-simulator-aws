"""
JSONB Helper Utilities for raw_data Schema

Utilities for extracting and navigating JSONB structures in the raw_data schema.
Provides type-safe accessor functions for common field patterns.

Schema Structure:
    raw_data.nba_games:
        - game_id (text, primary key)
        - source (text)
        - season (int)
        - game_date (date)
        - collected_at (timestamp)
        - updated_at (timestamp)
        - data (jsonb) - Game information, teams, scores, play summaries
        - metadata (jsonb) - Collection, migration, validation info

    raw_data.nba_misc:
        - id (serial, primary key)
        - source (text)
        - entity_type (text)
        - collected_at (timestamp)
        - data (jsonb) - Entity-specific data
        - metadata (jsonb) - Collection and migration info

Usage:
    from nba_simulator.utils.raw_data_helpers import get_game_score, get_team_info

    # Extract scores from game row
    scores = get_game_score(game_row)
    print(f"Home: {scores['home']}, Away: {scores['away']}")

    # Extract team info
    teams = get_team_info(game_row)
    print(f"{teams['home']['name']} vs {teams['away']['name']}")
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date


# ============================================================================
# Game Data Extraction (raw_data.nba_games)
# ============================================================================


def get_game_score(game_row: Dict[str, Any]) -> Dict[str, Optional[int]]:
    """
    Extract home/away scores from game JSONB.

    Args:
        game_row: Row from raw_data.nba_games (dict with 'data' key)

    Returns:
        Dict with 'home' and 'away' scores (None if missing)

    Example:
        >>> scores = get_game_score(game_row)
        >>> print(f"Home: {scores['home']}, Away: {scores['away']}")
        Home: 105, Away: 98
    """
    data = game_row.get("data", {})
    teams = data.get("teams", {})

    return {
        "home": teams.get("home", {}).get("score"),
        "away": teams.get("away", {}).get("score"),
    }


def get_team_info(game_row: Dict[str, Any]) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Extract team names and abbreviations from game JSONB.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with 'home' and 'away' team info (name, abbreviation)

    Example:
        >>> teams = get_team_info(game_row)
        >>> print(f"{teams['home']['name']} ({teams['home']['abbreviation']})")
        Los Angeles Lakers (LAL)
    """
    data = game_row.get("data", {})
    teams = data.get("teams", {})

    return {
        "home": {
            "name": teams.get("home", {}).get("name"),
            "abbreviation": teams.get("home", {}).get("abbreviation"),
        },
        "away": {
            "name": teams.get("away", {}).get("name"),
            "abbreviation": teams.get("away", {}).get("abbreviation"),
        },
    }


def get_game_info(game_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract game metadata (game_id, date, season).

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with game_id, game_date, season, season_year

    Example:
        >>> info = get_game_info(game_row)
        >>> print(f"Game {info['game_id']} on {info['game_date']}")
        Game 401468003 on 2023-11-05
    """
    data = game_row.get("data", {})
    game_info = data.get("game_info", {})

    return {
        "game_id": game_info.get("game_id") or game_row.get("game_id"),
        "game_date": game_info.get("game_date"),
        "season": game_info.get("season"),
        "season_year": game_info.get("season_year"),
    }


def get_play_summary(game_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract play-by-play summary from game JSONB.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with total_plays, periods, event_types (None if no PBP)

    Example:
        >>> pbp = get_play_summary(game_row)
        >>> print(f"Total plays: {pbp['total_plays']}, Periods: {pbp['periods']}")
        Total plays: 452, Periods: 4
    """
    data = game_row.get("data", {})
    pbp = data.get("play_by_play", {})
    summary = pbp.get("summary", {})

    return {
        "total_plays": pbp.get("total_plays", 0),
        "periods": summary.get("periods"),
        "event_types": summary.get("event_types", {}),
    }


def get_source_data(game_row: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract source information from game JSONB.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with original_game_id, source

    Example:
        >>> source = get_source_data(game_row)
        >>> print(f"Source: {source['source']}, ID: {source['original_game_id']}")
        Source: ESPN, ID: 401468003
    """
    data = game_row.get("data", {})
    source_data = data.get("source_data", {})

    return {
        "original_game_id": source_data.get("original_game_id"),
        "source": source_data.get("source") or game_row.get("source"),
    }


# ============================================================================
# Metadata Extraction (raw_data.nba_games.metadata)
# ============================================================================


def get_collection_info(game_row: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract collection timestamps and source system from metadata.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with collected_at, updated_at, source_system

    Example:
        >>> collection = get_collection_info(game_row)
        >>> print(f"Collected: {collection['collected_at']}")
        Collected: 2025-11-05T12:34:56
    """
    metadata = game_row.get("metadata", {})
    collection = metadata.get("collection", {})

    return {
        "collected_at": collection.get("collected_at"),
        "updated_at": collection.get("updated_at"),
        "source_system": collection.get("source_system"),
    }


def get_validation_status(game_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract validation status from metadata.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with has_play_by_play, play_count, validated_at

    Example:
        >>> validation = get_validation_status(game_row)
        >>> if validation['has_play_by_play']:
        ...     print(f"Has {validation['play_count']} plays")
        Has 452 plays
    """
    metadata = game_row.get("metadata", {})
    validation = metadata.get("validation", {})

    return {
        "has_play_by_play": validation.get("has_play_by_play", False),
        "play_count": validation.get("play_count", 0),
        "validated_at": validation.get("validated_at"),
    }


def get_migration_info(game_row: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract migration metadata.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with migrated_at, migrated_from, migration_version

    Example:
        >>> migration = get_migration_info(game_row)
        >>> print(f"Migrated from {migration['migrated_from']}")
        Migrated from master.nba_games
    """
    metadata = game_row.get("metadata", {})
    migration = metadata.get("migration", {})

    return {
        "migrated_at": migration.get("migrated_at"),
        "migrated_from": migration.get("migrated_from"),
        "migration_version": migration.get("migration_version"),
    }


# ============================================================================
# File Validation Extraction (raw_data.nba_misc where entity_type='file_validation')
# ============================================================================


def get_file_validation_info(misc_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract file validation information from nba_misc row.

    Args:
        misc_row: Row from raw_data.nba_misc (entity_type='file_validation')

    Returns:
        Dict with file_name, file_size_bytes, validation results

    Example:
        >>> file_val = get_file_validation_info(misc_row)
        >>> print(f"{file_val['file_name']}: {file_val['file_size_bytes']} bytes")
        401468003.json: 245678 bytes
    """
    data = misc_row.get("data", {})
    file_info = data.get("file_info", {})
    validation = data.get("validation", {})

    return {
        "file_name": file_info.get("file_name"),
        "file_size_bytes": file_info.get("file_size_bytes"),
        "validation_timestamp": file_info.get("validation_timestamp"),
        "has_pbp_data": validation.get("has_pbp_data", False),
        "has_game_info": validation.get("has_game_info", False),
        "has_team_data": validation.get("has_team_data", False),
        "play_count": validation.get("play_count", 0),
        "error_message": validation.get("error_message"),
    }


def get_game_reference(misc_row: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract game reference from nba_misc row.

    Args:
        misc_row: Row from raw_data.nba_misc

    Returns:
        Dict with game_id, season, league, game_date, teams

    Example:
        >>> ref = get_game_reference(misc_row)
        >>> print(f"Game {ref['game_id']}: {ref['home_team']} vs {ref['away_team']}")
        Game 401468003: Lakers vs Celtics
    """
    data = misc_row.get("data", {})
    game_ref = data.get("game_reference", {})

    return {
        "game_id": game_ref.get("game_id"),
        "season": game_ref.get("season"),
        "league": game_ref.get("league"),
        "game_date": game_ref.get("game_date"),
        "home_team": game_ref.get("home_team"),
        "away_team": game_ref.get("away_team"),
    }


# ============================================================================
# Composite Functions (Multi-field extraction)
# ============================================================================


def get_complete_game_data(game_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all commonly-used game data in one call.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with all game data (info, teams, scores, play_summary, source, validation)

    Example:
        >>> game = get_complete_game_data(game_row)
        >>> print(f"{game['teams']['home']['name']} {game['scores']['home']} - "
        ...       f"{game['teams']['away']['name']} {game['scores']['away']}")
        Lakers 105 - Celtics 98
    """
    return {
        "info": get_game_info(game_row),
        "teams": get_team_info(game_row),
        "scores": get_game_score(game_row),
        "play_summary": get_play_summary(game_row),
        "source": get_source_data(game_row),
        "validation": get_validation_status(game_row),
        "collection": get_collection_info(game_row),
    }


def get_game_summary_string(game_row: Dict[str, Any]) -> str:
    """
    Generate human-readable game summary string.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Formatted string with game summary

    Example:
        >>> print(get_game_summary_string(game_row))
        2023-11-05: Los Angeles Lakers 105 - Boston Celtics 98 (452 plays)
    """
    info = get_game_info(game_row)
    teams = get_team_info(game_row)
    scores = get_game_score(game_row)
    pbp = get_play_summary(game_row)

    return (
        f"{info['game_date']}: "
        f"{teams['home']['name']} {scores['home']} - "
        f"{teams['away']['name']} {scores['away']} "
        f"({pbp['total_plays']} plays)"
    )


# ============================================================================
# JSONB Path Navigation (for advanced queries)
# ============================================================================


def navigate_jsonb_path(row: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Navigate nested JSONB structure using dot notation.

    Args:
        row: Database row with JSONB columns
        path: Dot-separated path (e.g., "data.teams.home.name")
        default: Default value if path not found

    Returns:
        Value at path, or default if not found

    Example:
        >>> home_score = navigate_jsonb_path(game_row, "data.teams.home.score")
        >>> print(home_score)
        105

        >>> missing = navigate_jsonb_path(game_row, "data.missing.path", default=0)
        >>> print(missing)
        0
    """
    parts = path.split(".")
    current = row

    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return default
        else:
            return default

    return current


def check_jsonb_path_exists(row: Dict[str, Any], path: str) -> bool:
    """
    Check if a JSONB path exists in the row.

    Args:
        row: Database row with JSONB columns
        path: Dot-separated path to check

    Returns:
        True if path exists, False otherwise

    Example:
        >>> if check_jsonb_path_exists(game_row, "data.play_by_play"):
        ...     print("Game has play-by-play data")
        Game has play-by-play data
    """
    parts = path.split(".")
    current = row

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False

    return True


def extract_all_jsonb_keys(row: Dict[str, Any], column: str = "data") -> List[str]:
    """
    Extract all top-level keys from a JSONB column.

    Args:
        row: Database row with JSONB columns
        column: Name of JSONB column ('data' or 'metadata')

    Returns:
        List of top-level keys

    Example:
        >>> keys = extract_all_jsonb_keys(game_row, 'data')
        >>> print(keys)
        ['game_info', 'teams', 'source_data', 'play_by_play']
    """
    jsonb_col = row.get(column, {})
    if isinstance(jsonb_col, dict):
        return list(jsonb_col.keys())
    return []


# ============================================================================
# Data Quality Helpers
# ============================================================================


def validate_required_fields(game_row: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required JSONB fields are present in game row.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Tuple of (is_valid, list_of_missing_fields)

    Example:
        >>> is_valid, missing = validate_required_fields(game_row)
        >>> if not is_valid:
        ...     print(f"Missing fields: {', '.join(missing)}")
        Missing fields: data.teams.home.score
    """
    required_paths = [
        "data.game_info.game_id",
        "data.game_info.game_date",
        "data.teams.home.name",
        "data.teams.away.name",
        "data.teams.home.score",
        "data.teams.away.score",
        "metadata.collection.source_system",
    ]

    missing = []
    for path in required_paths:
        if not check_jsonb_path_exists(game_row, path):
            missing.append(path)

    return (len(missing) == 0, missing)


def check_data_completeness(game_row: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check completeness of various data sections.

    Args:
        game_row: Row from raw_data.nba_games

    Returns:
        Dict with boolean flags for each data section

    Example:
        >>> completeness = check_data_completeness(game_row)
        >>> print(f"Has PBP: {completeness['has_play_by_play']}")
        >>> print(f"Has metadata: {completeness['has_metadata']}")
        Has PBP: True
        Has metadata: True
    """
    return {
        "has_game_info": check_jsonb_path_exists(game_row, "data.game_info"),
        "has_teams": check_jsonb_path_exists(game_row, "data.teams"),
        "has_scores": (
            check_jsonb_path_exists(game_row, "data.teams.home.score")
            and check_jsonb_path_exists(game_row, "data.teams.away.score")
        ),
        "has_play_by_play": check_jsonb_path_exists(game_row, "data.play_by_play"),
        "has_source_data": check_jsonb_path_exists(game_row, "data.source_data"),
        "has_metadata": check_jsonb_path_exists(game_row, "metadata"),
        "has_collection_info": check_jsonb_path_exists(game_row, "metadata.collection"),
        "has_validation": check_jsonb_path_exists(game_row, "metadata.validation"),
    }


# ============================================================================
# ESPN Enriched Data Extraction (espn_features from enrichment pipeline)
# ============================================================================


def get_espn_game_info(game_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ESPN game info from enriched data.

    Returns enriched ESPN features including season, attendance, broadcast,
    overtime status, and margin of victory.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features

    Returns:
        Dict with ESPN game info fields (9 fields):
            - game_id: ESPN game ID
            - game_date: ISO timestamp
            - season: Season string (e.g., "2023-24")
            - season_year: Season year (int)
            - season_type: Season type code
            - attendance: Game attendance
            - broadcast: Broadcast info
            - overtime: Boolean overtime flag
            - margin_of_victory: Point differential

    Example:
        >>> game_info = get_espn_game_info(game_row)
        >>> print(f"Season: {game_info['season']}, Attendance: {game_info['attendance']}")
    """
    data = game_row.get("data", {})
    espn_features = data.get("espn_features", {})
    return espn_features.get("game_info", {})


def get_espn_box_score(
    game_row: Dict[str, Any], team: str = "home"
) -> List[Dict[str, Any]]:
    """
    Extract ESPN box score for a specific team.

    Returns list of player stat dictionaries with all traditional box score stats
    including shooting percentages, rebounds, assists, etc.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features
        team: 'home' or 'away'

    Returns:
        List of player dicts, each containing:
            - player_id: ESPN player ID
            - name: Player display name
            - position: Position abbreviation
            - jersey: Jersey number
            - starter: Boolean starter flag
            - stats: Dict with 25 stat fields:
                * minutes, field_goals_made, field_goals_attempted
                * three_pointers_made, three_pointers_attempted
                * free_throws_made, free_throws_attempted
                * offensive_rebounds, defensive_rebounds, rebounds
                * assists, steals, blocks, turnovers, personal_fouls
                * points, plus_minus
                * field_goal_pct, three_point_pct, free_throw_pct (derived)
                * double_double, triple_double (derived)

    Example:
        >>> home_players = get_espn_box_score(game_row, 'home')
        >>> for player in home_players:
        ...     print(f"{player['name']}: {player['stats']['points']} pts")
    """
    data = game_row.get("data", {})
    espn_features = data.get("espn_features", {})
    box_score = espn_features.get("box_score", {})
    return box_score.get(team, {}).get("players", [])


def get_quarter_scores(game_row: Dict[str, Any], team: str = "home") -> List[int]:
    """
    Extract quarter-by-quarter scores for a team.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features
        team: 'home' or 'away'

    Returns:
        List of quarter scores (typically 4 items, more if overtime)

    Example:
        >>> quarters = get_quarter_scores(game_row, 'home')
        >>> print(f"Q1: {quarters[0]}, Q2: {quarters[1]}, Total: {sum(quarters)}")
    """
    data = game_row.get("data", {})
    espn_features = data.get("espn_features", {})
    scoring = espn_features.get("scoring", {})
    return scoring.get(team, {}).get("quarters", [])


def get_espn_venue(game_row: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Extract ESPN venue information.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features

    Returns:
        Dict with venue fields:
            - name: Full venue name
            - city: City
            - state: State code

    Example:
        >>> venue = get_espn_venue(game_row)
        >>> print(f"Venue: {venue['name']} ({venue['city']}, {venue['state']})")
    """
    data = game_row.get("data", {})
    espn_features = data.get("espn_features", {})
    return espn_features.get("venue", {})


def get_espn_officials(game_row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract ESPN officials list.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features

    Returns:
        List of official dicts, each containing:
            - name: Official's full name
            - number: Official's number (may be None)

    Example:
        >>> officials = get_espn_officials(game_row)
        >>> print(f"Referees: {', '.join(o['name'] for o in officials)}")
    """
    data = game_row.get("data", {})
    espn_features = data.get("espn_features", {})
    return espn_features.get("officials", [])


def get_player_stats(
    game_row: Dict[str, Any], team: str, player_name: str
) -> Optional[Dict[str, Any]]:
    """
    Get stats for a specific player by name.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features
        team: 'home' or 'away'
        player_name: Player's display name (case-sensitive)

    Returns:
        Dict with player stats, or None if player not found

    Example:
        >>> stats = get_player_stats(game_row, 'home', 'LeBron James')
        >>> if stats:
        ...     print(f"Points: {stats['points']}, Rebounds: {stats['rebounds']}")
    """
    players = get_espn_box_score(game_row, team)
    for player in players:
        if player.get("name") == player_name:
            return player.get("stats", {})
    return None


def get_top_scorer(game_row: Dict[str, Any], team: str) -> Optional[Dict[str, Any]]:
    """
    Get top scorer for a team.

    Args:
        game_row: Row from raw_data.nba_games with enriched espn_features
        team: 'home' or 'away'

    Returns:
        Player dict (with name and stats), or None if no players found

    Example:
        >>> top_scorer = get_top_scorer(game_row, 'home')
        >>> if top_scorer:
        ...     print(f"{top_scorer['name']}: {top_scorer['stats']['points']} pts")
    """
    players = get_espn_box_score(game_row, team)
    if not players:
        return None
    return max(players, key=lambda p: p.get("stats", {}).get("points") or 0)


# ============================================================================
# Export all functions
# ============================================================================

__all__ = [
    # Game data extraction
    "get_game_score",
    "get_team_info",
    "get_game_info",
    "get_play_summary",
    "get_source_data",
    # Metadata extraction
    "get_collection_info",
    "get_validation_status",
    "get_migration_info",
    # File validation extraction
    "get_file_validation_info",
    "get_game_reference",
    # Composite functions
    "get_complete_game_data",
    "get_game_summary_string",
    # ESPN enriched data extraction
    "get_espn_game_info",
    "get_espn_box_score",
    "get_quarter_scores",
    "get_espn_venue",
    "get_espn_officials",
    "get_player_stats",
    "get_top_scorer",
    # JSONB path navigation
    "navigate_jsonb_path",
    "check_jsonb_path_exists",
    "extract_all_jsonb_keys",
    # Data quality helpers
    "validate_required_fields",
    "check_data_completeness",
]
