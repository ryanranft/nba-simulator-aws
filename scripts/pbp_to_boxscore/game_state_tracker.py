#!/usr/bin/env python3
"""
Game State Tracker - Maintains Cumulative Game State

Purpose: Track cumulative player stats, lineups, and game state throughout NBA games
Database: RDS PostgreSQL (nba_simulator)
Created: October 19, 2025

=== OVERVIEW ===

This module maintains the complete state of an NBA game as play-by-play events
are processed. It tracks:

1. Cumulative player stats (points, rebounds, assists, etc.)
2. On-court lineups (5 players per team)
3. Substitutions
4. Plus/minus calculations
5. Quarter boundaries
6. Score progression

=== STATE MACHINE ===

The GameStateTracker is a state machine that:
- Initializes with starting lineups
- Processes each play event sequentially
- Updates cumulative stats
- Creates immutable snapshots after each event
- Validates state consistency

=== USAGE ===

```python
tracker = GameStateTracker(game_id="400827936", home_team_id="BOS", away_team_id="LAL")

# Set starting lineups
tracker.set_starting_lineup("BOS", ["Ray Allen", "Kevin Garnett", ...])
tracker.set_starting_lineup("LAL", ["Kobe Bryant", "Pau Gasol", ...])

# Process events
for event in play_by_play_events:
    parsed_play = parser.parse(event.play_text)
    snapshot = tracker.process_event(event, parsed_play)
```
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib
import copy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Cumulative state for a single player."""

    player_id: str
    player_name: str
    team_id: str

    # Box score stats (cumulative)
    points: int = 0
    fgm: int = 0
    fga: int = 0
    fg3m: int = 0
    fg3a: int = 0
    ftm: int = 0
    fta: int = 0
    oreb: int = 0
    dreb: int = 0
    reb: int = 0
    ast: int = 0
    stl: int = 0
    blk: int = 0
    tov: int = 0
    pf: int = 0

    # Plus/minus
    plus_minus: int = 0

    # On-court status
    on_court: bool = False
    minutes_played: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class GameState:
    """Complete game state at a specific moment in time."""

    game_id: str
    event_num: int
    period: int
    clock_display: str
    home_score: int
    away_score: int

    # Player states
    players: Dict[str, PlayerState] = field(default_factory=dict)

    # Lineups (on-court players)
    home_lineup: Set[str] = field(default_factory=set)
    away_lineup: Set[str] = field(default_factory=set)

    # Lineup hash (for plus/minus tracking)
    home_lineup_hash: Optional[str] = None
    away_lineup_hash: Optional[str] = None

    # Metadata
    last_event_text: str = ""
    timestamp: Optional[datetime] = None

    def get_lineup_hash(self, player_names: Set[str]) -> str:
        """Calculate MD5 hash for a lineup (exactly 5 players)."""
        if len(player_names) != 5:
            logger.warning(
                f"Lineup has {len(player_names)} players (expected 5): {player_names}"
            )

        # Sort names for consistent hashing
        sorted_names = sorted(player_names)
        lineup_str = "|".join(sorted_names)
        return hashlib.md5(lineup_str.encode(), usedforsecurity=False).hexdigest()

    def update_lineup_hashes(self):
        """Update lineup hashes based on current lineups."""
        if self.home_lineup:
            self.home_lineup_hash = self.get_lineup_hash(self.home_lineup)
        if self.away_lineup:
            self.away_lineup_hash = self.get_lineup_hash(self.away_lineup)


class GameStateTracker:
    """
    Tracks the complete state of an NBA game as events are processed.

    Maintains cumulative stats, lineups, and plus/minus calculations.
    Creates immutable snapshots after each event.
    """

    def __init__(self, game_id: str, home_team_id: str, away_team_id: str):
        """
        Initialize GameStateTracker.

        Args:
            game_id: Unique game identifier
            home_team_id: Home team ID
            away_team_id: Away team ID
        """
        self.game_id = game_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id

        # Current state
        self.current_state = GameState(
            game_id=game_id,
            event_num=0,
            period=1,
            clock_display="12:00",
            home_score=0,
            away_score=0,
        )

        # Track all snapshots
        self.snapshots: List[GameState] = []

        # Event counter
        self.events_processed = 0

        logger.info(f"GameStateTracker initialized for game {game_id}")
        logger.info(f"  Home: {home_team_id}")
        logger.info(f"  Away: {away_team_id}")

    def set_starting_lineup(self, team_id: str, player_names: List[str]):
        """
        Set the starting lineup for a team.

        Args:
            team_id: Team identifier
            player_names: List of 5 player names
        """
        if len(player_names) != 5:
            logger.warning(
                f"Starting lineup for {team_id} has {len(player_names)} players (expected 5)"
            )

        # Add players to state if not already present
        for player_name in player_names:
            player_id = self._generate_player_id(player_name, team_id)

            if player_id not in self.current_state.players:
                self.current_state.players[player_id] = PlayerState(
                    player_id=player_id,
                    player_name=player_name,
                    team_id=team_id,
                    on_court=True,
                )
            else:
                self.current_state.players[player_id].on_court = True

        # Set lineup
        if team_id == self.home_team_id:
            self.current_state.home_lineup = set(player_names)
        else:
            self.current_state.away_lineup = set(player_names)

        # Update lineup hashes
        self.current_state.update_lineup_hashes()

        logger.info(f"Starting lineup set for {team_id}: {player_names}")

    def process_event(
        self,
        event_num: int,
        period: int,
        clock_display: str,
        play_text: str,
        parsed_play,
        home_score: int = 0,
        away_score: int = 0,
    ) -> GameState:
        """
        Process a single play-by-play event and update game state.

        Args:
            event_num: Event number (sequence)
            period: Period/quarter number
            clock_display: Game clock (e.g., "7:42")
            play_text: Original play text
            parsed_play: ParsedPlay object from PlayTextParser
            home_score: Current home team score
            away_score: Current away team score

        Returns:
            Immutable snapshot of game state after this event
        """
        # Update plus/minus BEFORE updating scores (uses previous scores)
        self._update_plus_minus(home_score, away_score)

        # Update event metadata
        self.current_state.event_num = event_num
        self.current_state.period = period
        self.current_state.clock_display = clock_display
        self.current_state.last_event_text = play_text
        self.current_state.home_score = home_score
        self.current_state.away_score = away_score
        self.current_state.timestamp = datetime.now()

        # Process substitutions first
        if parsed_play.action_type.value in ["substitution_in"]:
            self._process_substitution(parsed_play)

        # Apply stat updates
        if parsed_play.stat_updates:
            self._apply_stat_updates(parsed_play.stat_updates, parsed_play.team_id)

        # Create immutable snapshot
        snapshot = self._create_snapshot()

        self.snapshots.append(snapshot)
        self.events_processed += 1

        return snapshot

    def _process_substitution(self, parsed_play):
        """Process a substitution event."""
        player_in_name = parsed_play.primary_player
        player_out_name = parsed_play.secondary_player
        team_id = parsed_play.team_id or self._infer_team_id(
            player_in_name, player_out_name
        )

        if not team_id:
            logger.warning(
                f"Could not determine team for substitution: {player_in_name} for {player_out_name}"
            )
            return

        # Get or create player states
        player_in_id = self._generate_player_id(player_in_name, team_id)
        player_out_id = self._generate_player_id(player_out_name, team_id)

        if player_in_id not in self.current_state.players:
            self.current_state.players[player_in_id] = PlayerState(
                player_id=player_in_id,
                player_name=player_in_name,
                team_id=team_id,
                on_court=False,
            )

        if player_out_id not in self.current_state.players:
            self.current_state.players[player_out_id] = PlayerState(
                player_id=player_out_id,
                player_name=player_out_name,
                team_id=team_id,
                on_court=True,
            )

        # Update on-court status
        self.current_state.players[player_in_id].on_court = True
        self.current_state.players[player_out_id].on_court = False

        # Update lineup
        if team_id == self.home_team_id:
            self.current_state.home_lineup.discard(player_out_name)
            self.current_state.home_lineup.add(player_in_name)
        else:
            self.current_state.away_lineup.discard(player_out_name)
            self.current_state.away_lineup.add(player_in_name)

        # Update lineup hashes
        self.current_state.update_lineup_hashes()

        logger.debug(
            f"Substitution: {player_in_name} in for {player_out_name} ({team_id})"
        )

    def _apply_stat_updates(
        self, stat_updates: Dict[str, Dict[str, int]], team_id: Optional[str]
    ):
        """Apply stat updates to player states."""
        for player_name, stats in stat_updates.items():
            # Infer team if not provided
            if not team_id:
                team_id = self._infer_team_id_from_player(player_name)

            player_id = self._generate_player_id(player_name, team_id)

            # Get or create player state
            if player_id not in self.current_state.players:
                self.current_state.players[player_id] = PlayerState(
                    player_id=player_id,
                    player_name=player_name,
                    team_id=team_id,
                    on_court=False,  # Will be updated by lineup tracking
                )

            player_state = self.current_state.players[player_id]

            # Apply each stat update
            for stat_name, value in stats.items():
                stat_attr = stat_name.lower()

                if stat_attr == "pts":
                    player_state.points += value
                elif stat_attr == "fgm":
                    player_state.fgm += value
                elif stat_attr == "fga":
                    player_state.fga += value
                elif stat_attr == "fg3m":
                    player_state.fg3m += value
                elif stat_attr == "fg3a":
                    player_state.fg3a += value
                elif stat_attr == "ftm":
                    player_state.ftm += value
                elif stat_attr == "fta":
                    player_state.fta += value
                elif stat_attr == "oreb":
                    player_state.oreb += value
                elif stat_attr == "dreb":
                    player_state.dreb += value
                elif stat_attr == "reb":
                    player_state.reb += value
                elif stat_attr == "ast":
                    player_state.ast += value
                elif stat_attr == "stl":
                    player_state.stl += value
                elif stat_attr == "blk":
                    player_state.blk += value
                elif stat_attr == "tov":
                    player_state.tov += value
                elif stat_attr == "pf":
                    player_state.pf += value

    def _update_plus_minus(self, new_home_score: int, new_away_score: int):
        """Update plus/minus for all on-court players."""
        # Calculate score changes (use previous scores stored in current_state)
        home_score_change = new_home_score - self.current_state.home_score
        away_score_change = new_away_score - self.current_state.away_score

        if home_score_change == 0 and away_score_change == 0:
            return  # No score change

        # Update plus/minus for home team players
        for player_name in self.current_state.home_lineup:
            player_id = self._generate_player_id(player_name, self.home_team_id)
            if player_id in self.current_state.players:
                player = self.current_state.players[player_id]
                if player.on_court:
                    player.plus_minus += home_score_change - away_score_change

        # Update plus/minus for away team players
        for player_name in self.current_state.away_lineup:
            player_id = self._generate_player_id(player_name, self.away_team_id)
            if player_id in self.current_state.players:
                player = self.current_state.players[player_id]
                if player.on_court:
                    player.plus_minus += away_score_change - home_score_change

    def _create_snapshot(self) -> GameState:
        """Create an immutable snapshot of current game state."""
        # Deep copy to make snapshot immutable
        return copy.deepcopy(self.current_state)

    def _generate_player_id(self, player_name: str, team_id: str) -> str:
        """Generate a unique player ID from name and team."""
        # Simple ID: team_firstname_lastname
        # In production, would map to actual player IDs from database
        normalized_name = player_name.replace("'", "").replace(".", "")
        return f"{team_id}_{normalized_name.replace(' ', '_')}"

    def _infer_team_id(
        self, player_in_name: str, player_out_name: str
    ) -> Optional[str]:
        """Infer team ID from substitution players."""
        # Check which lineup contains the outgoing player
        if player_out_name in self.current_state.home_lineup:
            return self.home_team_id
        elif player_out_name in self.current_state.away_lineup:
            return self.away_team_id

        # Check existing player states
        for player_id, player_state in self.current_state.players.items():
            if player_state.player_name == player_out_name:
                return player_state.team_id

        return None

    def _infer_team_id_from_player(self, player_name: str) -> Optional[str]:
        """Infer team ID from a single player name."""
        # Check lineups
        if player_name in self.current_state.home_lineup:
            return self.home_team_id
        elif player_name in self.current_state.away_lineup:
            return self.away_team_id

        # Check existing player states
        for player_id, player_state in self.current_state.players.items():
            if player_state.player_name == player_name:
                return player_state.team_id

        # Default: assume home team (will be corrected by lineup tracking)
        return self.home_team_id

    def get_current_state(self) -> GameState:
        """Get current game state (mutable)."""
        return self.current_state

    def get_snapshot(self, event_num: int) -> Optional[GameState]:
        """Get a specific snapshot by event number."""
        for snapshot in self.snapshots:
            if snapshot.event_num == event_num:
                return snapshot
        return None

    def get_all_snapshots(self) -> List[GameState]:
        """Get all snapshots."""
        return self.snapshots

    def get_player_stats(self, player_name: str) -> Optional[PlayerState]:
        """Get current stats for a specific player."""
        for player_id, player_state in self.current_state.players.items():
            if player_state.player_name == player_name:
                return player_state
        return None

    def get_stats_summary(self) -> Dict:
        """Get summary of game state tracking."""
        return {
            "game_id": self.game_id,
            "events_processed": self.events_processed,
            "snapshots_created": len(self.snapshots),
            "total_players": len(self.current_state.players),
            "home_lineup_size": len(self.current_state.home_lineup),
            "away_lineup_size": len(self.current_state.away_lineup),
            "current_period": self.current_state.period,
            "current_score": f"{self.current_state.away_score}-{self.current_state.home_score}",
        }


# =============================================================================
# TESTING
# =============================================================================


def test_game_state_tracker():
    """Test the game state tracker with sample events."""
    logger.info("=== Testing Game State Tracker ===\n")

    # Initialize tracker
    tracker = GameStateTracker(
        game_id="TEST_GAME_001", home_team_id="BOS", away_team_id="LAL"
    )

    # Set starting lineups
    home_lineup = [
        "Ray Allen",
        "Kevin Garnett",
        "Paul Pierce",
        "Rajon Rondo",
        "Kendrick Perkins",
    ]
    away_lineup = [
        "Kobe Bryant",
        "Pau Gasol",
        "Derek Fisher",
        "Lamar Odom",
        "Andrew Bynum",
    ]

    tracker.set_starting_lineup("BOS", home_lineup)
    tracker.set_starting_lineup("LAL", away_lineup)

    # Simulate some events (would normally come from parser)
    from play_text_parser import PlayTextParser, ParsedPlay, ActionType

    parser = PlayTextParser()

    # Event 1: Kobe scores
    play1 = parser.parse("Kobe Bryant makes 15 ft jumper.")
    snapshot1 = tracker.process_event(
        event_num=1,
        period=1,
        clock_display="11:47",
        play_text="Kobe Bryant makes 15 ft jumper.",
        parsed_play=play1,
        home_score=0,
        away_score=2,
    )

    logger.info(f"After Event 1:")
    kobe_stats = tracker.get_player_stats("Kobe Bryant")
    logger.info(
        f"  Kobe Bryant: {kobe_stats.points} PTS, {kobe_stats.fgm}/{kobe_stats.fga} FG, +/- {kobe_stats.plus_minus}"
    )

    # Event 2: Ray Allen scores 3
    play2 = parser.parse(
        "Ray Allen makes 25 ft three point jumper (Rajon Rondo assists)."
    )
    snapshot2 = tracker.process_event(
        event_num=2,
        period=1,
        clock_display="11:15",
        play_text="Ray Allen makes 25 ft three point jumper (Rajon Rondo assists).",
        parsed_play=play2,
        home_score=3,
        away_score=2,
    )

    logger.info(f"\nAfter Event 2:")
    ray_stats = tracker.get_player_stats("Ray Allen")
    rondo_stats = tracker.get_player_stats("Rajon Rondo")
    logger.info(
        f"  Ray Allen: {ray_stats.points} PTS, {ray_stats.fg3m}/{ray_stats.fg3a} 3P, +/- {ray_stats.plus_minus}"
    )
    logger.info(f"  Rajon Rondo: {rondo_stats.ast} AST, +/- {rondo_stats.plus_minus}")

    # Event 3: Substitution
    play3 = parser.parse("Glen Davis enters game for Kendrick Perkins.")
    snapshot3 = tracker.process_event(
        event_num=3,
        period=1,
        clock_display="10:30",
        play_text="Glen Davis enters game for Kendrick Perkins.",
        parsed_play=play3,
        home_score=3,
        away_score=2,
    )

    logger.info(f"\nAfter Event 3 (Substitution):")
    logger.info(f"  Home lineup: {tracker.current_state.home_lineup}")

    # Summary
    summary = tracker.get_stats_summary()
    logger.info(f"\n=== Summary ===")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    test_game_state_tracker()
