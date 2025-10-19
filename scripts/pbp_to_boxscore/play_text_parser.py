#!/usr/bin/env python3
"""
Play Text Parser - Natural Language Processing for NBA Play-by-Play Text

Purpose: Parse natural language play descriptions into structured stat updates
Database: RDS PostgreSQL (nba_simulator)
Created: October 19, 2025

=== OVERVIEW ===

This module parses play_by_play.play_text natural language into structured events.

Examples:
- "LeBron James makes 25 ft three point jumper (Dwyane Wade assists)."
  → Player: LeBron James, Action: FG3M, Assisted By: Dwyane Wade

- "Kevin Garnett missed 11 ft jumper."
  → Player: Kevin Garnett, Action: FGA (miss), Distance: 11 ft

- "Ervin Johnson defensive rebound."
  → Player: Ervin Johnson, Action: DREB

=== SUPPORTED PLAY TYPES ===

1. Field Goals (made/missed)
2. Three Pointers (made/missed)
3. Free Throws (made/missed)
4. Rebounds (offensive/defensive)
5. Assists
6. Steals
7. Blocks
8. Turnovers
9. Fouls (personal, shooting, technical)
10. Substitutions (enters/exits)

=== STAT UPDATES ===

Each parsed play returns a dictionary with:
- action_type: String (e.g., "FGM", "FGA", "FG3M", "REB", "AST")
- players: List of player names involved
- stats: Dict of stat updates per player
- details: Additional context (shot distance, foul type, etc.)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Enumeration of all supported play action types."""

    # Field Goals
    FGM = "field_goal_made"
    FGA = "field_goal_attempted"
    FG3M = "three_point_made"
    FG3A = "three_point_attempted"

    # Free Throws
    FTM = "free_throw_made"
    FTA = "free_throw_attempted"

    # Rebounds
    DREB = "defensive_rebound"
    OREB = "offensive_rebound"

    # Playmaking
    AST = "assist"

    # Defense
    STL = "steal"
    BLK = "block"

    # Turnovers
    TOV = "turnover"

    # Fouls
    PF = "personal_foul"
    TF = "technical_foul"
    FF = "flagrant_foul"

    # Substitutions
    SUB_IN = "substitution_in"
    SUB_OUT = "substitution_out"

    # Other
    TIMEOUT = "timeout"
    JUMPBALL = "jump_ball"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


@dataclass
class ParsedPlay:
    """Structured representation of a parsed play."""

    action_type: ActionType
    primary_player: Optional[str] = None
    secondary_player: Optional[str] = None  # Assisting player, fouled player, etc.
    team_id: Optional[str] = None

    # Shot details
    is_three_pointer: bool = False
    shot_made: bool = False
    shot_distance: Optional[int] = None  # In feet
    shot_type: Optional[str] = None  # "jumper", "layup", "dunk", etc.

    # Free throw details
    free_throw_num: Optional[int] = None
    free_throw_total: Optional[int] = None

    # Foul details
    foul_type: Optional[str] = None
    drawn_by: Optional[str] = None

    # Turnover details
    turnover_type: Optional[str] = None
    stolen_by: Optional[str] = None

    # Rebound details
    is_offensive: bool = False
    is_defensive: bool = False

    # Additional context
    assisted: bool = False
    blocked_by: Optional[str] = None

    # Stat updates to apply
    stat_updates: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Original text
    original_text: str = ""


class PlayTextParser:
    """
    Parses natural language NBA play-by-play text into structured events.

    Uses regex patterns to identify play types and extract player names,
    actions, and stat updates.
    """

    def __init__(self):
        """Initialize the parser with regex patterns."""
        self.patterns = self._compile_patterns()
        self.stats_parsed = 0
        self.stats_failed = 0

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """
        Compile regex patterns for all play types.

        Returns:
            Dictionary mapping pattern names to compiled regex objects
        """
        patterns = {}

        # Field Goal Made (2-pointer)
        patterns["fg_made_2pt"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+makes?\s+(?:(\d+)\s+ft\s+)?(.+?)(?:\s+\((.+?)\s+assists?\))?\.?$",
            re.IGNORECASE,
        )

        # Three Point Made
        patterns["fg_made_3pt"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+makes?\s+(?:(\d+)\s+ft\s+)?three\s+point\s+(.+?)(?:\s+\((.+?)\s+assists?\))?\.?$",
            re.IGNORECASE,
        )

        # Field Goal Missed (2-pointer)
        patterns["fg_missed_2pt"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+miss(?:ed|es)?\s+(?:(\d+)\s+ft\s+)?(.+?)(?:\s+block(?:ed)?\s+by\s+(.+?))?\.?$",
            re.IGNORECASE,
        )

        # Three Point Missed
        patterns["fg_missed_3pt"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+miss(?:ed|es)?\s+(?:(\d+)\s+ft\s+)?three\s+point\s+(.+?)(?:\s+block(?:ed)?\s+by\s+(.+?))?\.?$",
            re.IGNORECASE,
        )

        # Free Throw Made
        patterns["ft_made"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+makes?\s+free\s+throw\s+(\d+)\s+of\s+(\d+)\.?$",
            re.IGNORECASE,
        )

        # Free Throw Missed
        patterns["ft_missed"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+miss(?:ed|es)?\s+free\s+throw\s+(\d+)\s+of\s+(\d+)\.?$",
            re.IGNORECASE,
        )

        # Defensive Rebound
        patterns["rebound_def"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+defensive\s+rebound\.?$",
            re.IGNORECASE,
        )

        # Offensive Rebound
        patterns["rebound_off"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+offensive\s+rebound\.?$",
            re.IGNORECASE,
        )

        # Steal
        patterns["steal"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+steal(?:s)?(?:\s+from\s+(.+?))?\.?$",
            re.IGNORECASE,
        )

        # Block (standalone)
        patterns["block"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+blocks?\s+(.+?)(?:'s)?\s+(.+?)\.?$",
            re.IGNORECASE,
        )

        # Turnover (improved to not capture turnover type as part of name)
        # Use negative lookahead to stop before turnover keywords
        # Capture steal by specifically, or other context
        patterns["turnover"] = re.compile(
            r"^([A-Z][a-z]+(?:\s+(?!bad|lost|traveling|offensive|turnover)[A-Z][a-z'\.]+)*)\s+(bad\s+pass|lost\s+ball|traveling|offensive\s+foul)(?:\s+turnover)?(?:\s+\(steal\s+by\s+(.+?)\))?(?:\s+\((?!steal\s+by)(.+?)\))?\.?$",
            re.IGNORECASE,
        )

        # Personal Foul
        patterns["foul_personal"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+(?:personal|shooting)\s+foul(?:\s+\(drawn\s+by\s+(.+?)\))?\.?$",
            re.IGNORECASE,
        )

        # Block (standalone shot block)
        patterns["block_standalone"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+blocks?\s+([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)'?s?\s+(.+?)\.?$",
            re.IGNORECASE,
        )

        # Technical Foul
        patterns["foul_technical"] = re.compile(
            r"^(?:([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+)?technical\s+foul\.?$",
            re.IGNORECASE,
        )

        # Substitution
        patterns["substitution"] = re.compile(
            r"^([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+enters?\s+(?:the\s+)?game\s+for\s+([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\.?$",
            re.IGNORECASE,
        )

        # Timeout
        patterns["timeout"] = re.compile(
            r"^(?:([A-Z][a-z]+(?:\s[A-Z][a-z'\.]+)*)\s+)?(?:official\s+)?timeout\.?$",
            re.IGNORECASE,
        )

        # Jump Ball
        patterns["jumpball"] = re.compile(
            r"^jump\s+ball:?\s+(.+?)\s+vs\.?\s+(.+?)(?:\s+\((.+?)\s+gains\s+possession\))?\.?$",
            re.IGNORECASE,
        )

        return patterns

    def parse(self, play_text: str, team_id: Optional[str] = None) -> ParsedPlay:
        """
        Parse a single play text into structured format.

        Args:
            play_text: Natural language play description
            team_id: Team identifier (if known)

        Returns:
            ParsedPlay object with extracted information
        """
        play_text = play_text.strip()

        # Try each pattern in order of specificity
        # (More specific patterns first to avoid false matches)

        # Free throws (must check FIRST before regular FG patterns)
        match = self.patterns["ft_made"].match(play_text)
        if match:
            return self._parse_free_throw_made(match, play_text, team_id)

        match = self.patterns["ft_missed"].match(play_text)
        if match:
            return self._parse_free_throw_missed(match, play_text, team_id)

        # Three pointers (must check before regular FG)
        match = self.patterns["fg_made_3pt"].match(play_text)
        if match:
            return self._parse_three_point_made(match, play_text, team_id)

        match = self.patterns["fg_missed_3pt"].match(play_text)
        if match:
            return self._parse_three_point_missed(match, play_text, team_id)

        # Regular field goals
        match = self.patterns["fg_made_2pt"].match(play_text)
        if match:
            return self._parse_field_goal_made(match, play_text, team_id)

        match = self.patterns["fg_missed_2pt"].match(play_text)
        if match:
            return self._parse_field_goal_missed(match, play_text, team_id)

        # Rebounds
        match = self.patterns["rebound_def"].match(play_text)
        if match:
            return self._parse_defensive_rebound(match, play_text, team_id)

        match = self.patterns["rebound_off"].match(play_text)
        if match:
            return self._parse_offensive_rebound(match, play_text, team_id)

        # Steals
        match = self.patterns["steal"].match(play_text)
        if match:
            return self._parse_steal(match, play_text, team_id)

        # Blocks (standalone - not part of shot attempt)
        if "block_standalone" in self.patterns:
            match = self.patterns["block_standalone"].match(play_text)
            if match:
                return self._parse_block_standalone(match, play_text, team_id)

        # Turnovers
        match = self.patterns["turnover"].match(play_text)
        if match:
            return self._parse_turnover(match, play_text, team_id)

        # Fouls
        match = self.patterns["foul_personal"].match(play_text)
        if match:
            return self._parse_personal_foul(match, play_text, team_id)

        match = self.patterns["foul_technical"].match(play_text)
        if match:
            return self._parse_technical_foul(match, play_text, team_id)

        # Substitutions
        match = self.patterns["substitution"].match(play_text)
        if match:
            return self._parse_substitution(match, play_text, team_id)

        # Timeout
        match = self.patterns["timeout"].match(play_text)
        if match:
            return self._parse_timeout(match, play_text, team_id)

        # Jump Ball
        match = self.patterns["jumpball"].match(play_text)
        if match:
            return self._parse_jumpball(match, play_text, team_id)

        # No match found
        self.stats_failed += 1
        logger.debug(f"Failed to parse: {play_text}")
        return ParsedPlay(
            action_type=ActionType.UNKNOWN, original_text=play_text, team_id=team_id
        )

    # ========================================================================
    # PARSING METHODS FOR EACH PLAY TYPE
    # ========================================================================

    def _parse_three_point_made(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse three point field goal made."""
        player = match.group(1).strip()
        distance = int(match.group(2)) if match.group(2) else None
        shot_type = match.group(3).strip() if match.group(3) else None
        assister = match.group(4).strip() if match.group(4) else None

        stat_updates = {player: {"FG3M": 1, "FG3A": 1, "FGM": 1, "FGA": 1, "PTS": 3}}

        if assister:
            stat_updates[assister] = {"AST": 1}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.FG3M,
            primary_player=player,
            secondary_player=assister,
            team_id=team_id,
            is_three_pointer=True,
            shot_made=True,
            shot_distance=distance,
            shot_type=shot_type,
            assisted=(assister is not None),
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_three_point_missed(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse three point field goal missed."""
        player = match.group(1).strip()
        distance = int(match.group(2)) if match.group(2) else None
        shot_type = match.group(3).strip() if match.group(3) else None
        blocker = match.group(4).strip() if match.group(4) else None

        stat_updates = {player: {"FG3A": 1, "FGA": 1}}

        if blocker:
            stat_updates[blocker] = {"BLK": 1}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.FG3A,
            primary_player=player,
            team_id=team_id,
            is_three_pointer=True,
            shot_made=False,
            shot_distance=distance,
            shot_type=shot_type,
            blocked_by=blocker,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_field_goal_made(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse regular field goal made (2-pointer)."""
        player = match.group(1).strip()
        distance = int(match.group(2)) if match.group(2) else None
        shot_type = match.group(3).strip() if match.group(3) else None
        assister = match.group(4).strip() if match.group(4) else None

        stat_updates = {player: {"FGM": 1, "FGA": 1, "PTS": 2}}

        if assister:
            stat_updates[assister] = {"AST": 1}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.FGM,
            primary_player=player,
            secondary_player=assister,
            team_id=team_id,
            is_three_pointer=False,
            shot_made=True,
            shot_distance=distance,
            shot_type=shot_type,
            assisted=(assister is not None),
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_field_goal_missed(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse regular field goal missed (2-pointer)."""
        player = match.group(1).strip()
        distance = int(match.group(2)) if match.group(2) else None
        shot_type = match.group(3).strip() if match.group(3) else None
        blocker = match.group(4).strip() if match.group(4) else None

        stat_updates = {player: {"FGA": 1}}

        if blocker:
            stat_updates[blocker] = {"BLK": 1}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.FGA,
            primary_player=player,
            team_id=team_id,
            is_three_pointer=False,
            shot_made=False,
            shot_distance=distance,
            shot_type=shot_type,
            blocked_by=blocker,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_free_throw_made(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse free throw made."""
        player = match.group(1).strip()
        ft_num = int(match.group(2))
        ft_total = int(match.group(3))

        stat_updates = {player: {"FTM": 1, "FTA": 1, "PTS": 1}}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.FTM,
            primary_player=player,
            team_id=team_id,
            free_throw_num=ft_num,
            free_throw_total=ft_total,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_free_throw_missed(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse free throw missed."""
        player = match.group(1).strip()
        ft_num = int(match.group(2))
        ft_total = int(match.group(3))

        stat_updates = {player: {"FTA": 1}}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.FTA,
            primary_player=player,
            team_id=team_id,
            free_throw_num=ft_num,
            free_throw_total=ft_total,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_defensive_rebound(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse defensive rebound."""
        player = match.group(1).strip()

        stat_updates = {player: {"DREB": 1, "REB": 1}}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.DREB,
            primary_player=player,
            team_id=team_id,
            is_defensive=True,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_offensive_rebound(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse offensive rebound."""
        player = match.group(1).strip()

        stat_updates = {player: {"OREB": 1, "REB": 1}}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.OREB,
            primary_player=player,
            team_id=team_id,
            is_offensive=True,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_steal(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse steal."""
        player = match.group(1).strip()
        from_player = match.group(2).strip() if match.group(2) else None

        stat_updates = {player: {"STL": 1}}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.STL,
            primary_player=player,
            secondary_player=from_player,
            team_id=team_id,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_block_standalone(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse standalone block (not part of shot attempt)."""
        blocker = match.group(1).strip()
        shot_player = match.group(2).strip().rstrip("'s")  # Remove possessive
        shot_type = match.group(3).strip() if match.group(3) else None

        stat_updates = {blocker: {"BLK": 1}, shot_player: {"FGA": 1}}  # Missed shot

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.BLK,
            primary_player=blocker,
            secondary_player=shot_player,
            team_id=team_id,
            shot_type=shot_type,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_turnover(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse turnover."""
        player = match.group(1).strip()
        turnover_type = match.group(2).strip() if match.group(2) else "turnover"
        # Group 3 is steal by (if present)
        stolen_by = match.group(3).strip() if match.group(3) else None

        stat_updates = {player: {"TOV": 1}}

        if stolen_by:
            stat_updates[stolen_by] = {"STL": 1}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.TOV,
            primary_player=player,
            team_id=team_id,
            turnover_type=turnover_type,
            stolen_by=stolen_by,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_personal_foul(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse personal foul."""
        player = match.group(1).strip()
        drawn_by = match.group(2).strip() if match.group(2) else None

        stat_updates = {player: {"PF": 1}}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.PF,
            primary_player=player,
            secondary_player=drawn_by,
            team_id=team_id,
            foul_type="personal",
            drawn_by=drawn_by,
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_technical_foul(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse technical foul."""
        player = match.group(1).strip() if match.group(1) else None

        stat_updates = {}
        if player:
            stat_updates[player] = {"PF": 1}

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.TF,
            primary_player=player,
            team_id=team_id,
            foul_type="technical",
            stat_updates=stat_updates,
            original_text=play_text,
        )

    def _parse_substitution(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse substitution."""
        player_in = match.group(1).strip()
        player_out = match.group(2).strip()

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.SUB_IN,
            primary_player=player_in,
            secondary_player=player_out,
            team_id=team_id,
            stat_updates={},  # No stat changes for substitutions
            original_text=play_text,
        )

    def _parse_timeout(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse timeout."""
        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.TIMEOUT,
            team_id=team_id,
            stat_updates={},
            original_text=play_text,
        )

    def _parse_jumpball(
        self, match: re.Match, play_text: str, team_id: Optional[str]
    ) -> ParsedPlay:
        """Parse jump ball."""
        player1 = match.group(1).strip()
        player2 = match.group(2).strip()
        possession_winner = match.group(3).strip() if match.group(3) else None

        self.stats_parsed += 1

        return ParsedPlay(
            action_type=ActionType.JUMPBALL,
            primary_player=player1,
            secondary_player=player2,
            team_id=team_id,
            stat_updates={},
            original_text=play_text,
        )

    def get_stats(self) -> Dict[str, int]:
        """Get parser statistics."""
        return {
            "parsed": self.stats_parsed,
            "failed": self.stats_failed,
            "total": self.stats_parsed + self.stats_failed,
            "success_rate": (
                self.stats_parsed / (self.stats_parsed + self.stats_failed)
                if (self.stats_parsed + self.stats_failed) > 0
                else 0.0
            ),
        }


# =============================================================================
# TESTING AND VALIDATION
# =============================================================================


def test_parser():
    """Test the parser with common play examples."""
    parser = PlayTextParser()

    test_plays = [
        "LeBron James makes 25 ft three point jumper (Dwyane Wade assists).",
        "Kevin Garnett missed 11 ft jumper.",
        "Ervin Johnson defensive rebound.",
        "Kobe Bryant makes free throw 1 of 2.",
        "Tim Duncan missed free throw 2 of 2.",
        "Steve Nash offensive rebound.",
        "Chris Paul steal from Jason Kidd.",
        "Dwight Howard blocks Pau Gasol's layup.",
        "Carmelo Anthony bad pass turnover (steal by Rajon Rondo).",
        "Dirk Nowitzki personal foul (drawn by Kevin Durant).",
        "Derek Fisher enters game for Kobe Bryant.",
        "Official timeout.",
        "Jump ball: Shaquille O'Neal vs. Tim Duncan (Kevin Garnett gains possession).",
    ]

    logger.info("=== Testing Play Text Parser ===\n")

    for play_text in test_plays:
        parsed = parser.parse(play_text)
        logger.info(f"Input:  {play_text}")
        logger.info(f"Action: {parsed.action_type.value}")
        logger.info(f"Player: {parsed.primary_player}")
        if parsed.stat_updates:
            logger.info(f"Stats:  {parsed.stat_updates}")
        logger.info("")

    stats = parser.get_stats()
    logger.info(f"Parser Statistics:")
    logger.info(f"  Parsed: {stats['parsed']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Success Rate: {stats['success_rate']:.1%}")


if __name__ == "__main__":
    test_parser()
