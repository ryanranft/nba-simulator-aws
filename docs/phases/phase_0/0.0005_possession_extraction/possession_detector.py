"""
Phase 0.0005: Possession Extraction - Possession Detector

This module detects possession boundaries from the event stream in temporal_events.
Identifies when possessions start and end, building chains of events into possessions.

Methodology: Dean Oliver's "Basketball on Paper" possession definitions
- Possession starts: defensive rebound, steal, inbound, jump ball
- Possession ends: shot (made/missed), turnover, end of period, defensive foul
- Special cases: offensive rebounds continue possession

Author: NBA Simulator AWS Team
Created: November 5, 2025
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PossessionBoundary:
    """
    Represents a single possession with start/end boundaries.

    A possession is the period when one team has offensive control of the ball,
    ending when they score, turn it over, or commit a foul that gives possession
    to the other team.
    """

    # Identification
    possession_number: int
    game_id: str
    season: int
    game_date: datetime

    # Event boundaries
    start_event_id: int
    end_event_id: int
    event_count: int = 0

    # Temporal boundaries
    period: int
    start_clock_minutes: int
    start_clock_seconds: float
    end_clock_minutes: int
    end_clock_seconds: float
    duration_seconds: float = 0.0

    # Team attribution
    offensive_team_id: int
    defensive_team_id: int
    home_team_id: int
    away_team_id: int

    # Score context
    score_differential_start: int = 0
    home_score_start: int = 0
    away_score_start: int = 0
    home_score_end: int = 0
    away_score_end: int = 0

    # Possession outcome
    points_scored: int = 0
    possession_result: str = (
        ""  # 'made_shot', 'missed_shot', 'turnover', 'foul', 'end_period'
    )

    # Shot statistics
    field_goals_attempted: int = 0
    field_goals_made: int = 0
    three_pointers_attempted: int = 0
    three_pointers_made: int = 0
    free_throws_attempted: int = 0
    free_throws_made: int = 0

    # Context flags
    is_clutch_time: bool = False
    is_garbage_time: bool = False
    is_fastbreak: bool = False
    has_timeout: bool = False

    # Validation
    validation_status: str = "valid"
    validation_notes: str = ""

    def calculate_efficiency(self) -> float:
        """
        Calculate points per possession (PPP).

        Returns:
            Points per possession, or 0.0 if invalid
        """
        # PPP is simply points scored in the possession
        # (since this is already per-possession basis)
        return float(self.points_scored)

    def calculate_efg_percentage(self) -> float:
        """
        Calculate effective field goal percentage.

        eFG% = (FGM + 0.5 * 3PM) / FGA

        Returns:
            Effective FG percentage, or 0.0 if no attempts
        """
        if self.field_goals_attempted == 0:
            return 0.0

        efg = (
            self.field_goals_made + 0.5 * self.three_pointers_made
        ) / self.field_goals_attempted
        return round(efg, 3)

    def to_dict(self) -> Dict:
        """Convert possession boundary to dictionary for database insertion."""
        return {
            "possession_number": self.possession_number,
            "game_id": self.game_id,
            "season": self.season,
            "game_date": self.game_date,
            "period": self.period,
            "offensive_team_id": self.offensive_team_id,
            "defensive_team_id": self.defensive_team_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "start_clock_minutes": self.start_clock_minutes,
            "start_clock_seconds": self.start_clock_seconds,
            "end_clock_minutes": self.end_clock_minutes,
            "end_clock_seconds": self.end_clock_seconds,
            "duration_seconds": self.duration_seconds,
            "score_differential_start": self.score_differential_start,
            "home_score_start": self.home_score_start,
            "away_score_start": self.away_score_start,
            "home_score_end": self.home_score_end,
            "away_score_end": self.away_score_end,
            "points_scored": self.points_scored,
            "possession_result": self.possession_result,
            "field_goals_attempted": self.field_goals_attempted,
            "field_goals_made": self.field_goals_made,
            "three_pointers_attempted": self.three_pointers_attempted,
            "three_pointers_made": self.three_pointers_made,
            "free_throws_attempted": self.free_throws_attempted,
            "free_throws_made": self.free_throws_made,
            "points_per_possession": self.calculate_efficiency(),
            "effective_field_goal_pct": self.calculate_efg_percentage(),
            "start_event_id": self.start_event_id,
            "end_event_id": self.end_event_id,
            "event_count": self.event_count,
            "is_clutch_time": self.is_clutch_time,
            "is_garbage_time": self.is_garbage_time,
            "is_fastbreak": self.is_fastbreak,
            "has_timeout": self.has_timeout,
            "validation_status": self.validation_status,
            "validation_notes": self.validation_notes,
        }


class PossessionDetector:
    """
    Detects possession boundaries from temporal event stream.

    This class analyzes play-by-play events and identifies when possessions
    start and end, creating PossessionBoundary objects that represent each
    offensive possession.

    Algorithm:
    1. Load events for a game sorted by (period, clock)
    2. Iterate through events looking for start events
    3. When start event found, begin tracking possession
    4. Continue until end event found
    5. Create PossessionBoundary with all events in between
    6. Handle edge cases (offensive rebounds, technical fouls, etc.)
    """

    def __init__(self, config):
        """
        Initialize possession detector with configuration.

        Args:
            config: PossessionConfig instance with detection rules
        """
        self.config = config
        self.possession_detection = config.possession_detection
        self.validation = config.validation
        self.context_detection = config.context_detection

        # Cache for performance
        self._start_event_types = set(self.possession_detection.start_events)
        self._end_event_types = set(self.possession_detection.end_events)
        self._continuation_event_types = set(
            self.possession_detection.continuation_events
        )

        logger.info(
            f"PossessionDetector initialized: "
            f"{len(self._start_event_types)} start events, "
            f"{len(self._end_event_types)} end events"
        )

    def detect_possessions(self, events: List[Dict]) -> List[PossessionBoundary]:
        """
        Detect possession boundaries from event stream.

        This is the main entry point for possession detection. Takes a sorted
        list of events and returns a list of detected possessions.

        Args:
            events: List of event dictionaries sorted by (period, clock)
                   Expected keys: event_id, event_type, period, clock_minutes,
                                 clock_seconds, team_id, player_id, score, etc.

        Returns:
            List of PossessionBoundary objects

        Raises:
            ValueError: If events are not properly sorted or missing required fields
        """
        # 1. Validate events list
        if not validate_event_list(events):
            raise ValueError("Event list validation failed - check logs for details")

        logger.info(f"Processing {len(events)} events for possession detection")

        # 2. Extract game metadata
        metadata = extract_game_metadata(events)
        game_id = metadata["game_id"]
        season = metadata["season"]
        game_date = metadata["game_date"]
        home_team_id = metadata["home_team_id"]
        away_team_id = metadata["away_team_id"]

        # 3. Initialize tracking variables
        possessions = []
        current_possession_events = []
        possession_number = 0
        in_possession = False

        # 4. Iterate through events
        for i, event in enumerate(events):
            event_type = event.get("event_type", "").lower()

            # Check if this starts a new possession
            if self.is_start_event(event):
                # If we were tracking a possession, close it first
                if in_possession and current_possession_events:
                    possession = self._build_possession(
                        current_possession_events, possession_number, metadata
                    )
                    if possession:
                        possessions.append(possession)
                        possession_number += 1

                # Start new possession
                current_possession_events = [event]
                in_possession = True
                logger.debug(
                    f"Started possession #{possession_number} at event {i}: {event_type}"
                )

            # Check if this ends the current possession
            elif self.is_end_event(event):
                if in_possession:
                    # Add this final event to possession
                    current_possession_events.append(event)

                    # Build and save possession
                    possession = self._build_possession(
                        current_possession_events, possession_number, metadata
                    )
                    if possession:
                        possessions.append(possession)
                        possession_number += 1

                    # Reset for next possession
                    current_possession_events = []
                    in_possession = False
                    logger.debug(
                        f"Ended possession #{possession_number-1} at event {i}: {event_type}"
                    )
                else:
                    # End event without start - might be beginning of game
                    logger.warning(
                        f"End event without possession start at {i}: {event_type}"
                    )

            # Check if this continues the current possession
            elif self.is_continuation_event(event):
                if in_possession:
                    current_possession_events.append(event)
                    logger.debug(
                        f"Continuation event in possession at {i}: {event_type}"
                    )
                else:
                    logger.warning(
                        f"Continuation event without possession at {i}: {event_type}"
                    )

            # Regular event during possession
            elif in_possession:
                current_possession_events.append(event)

        # 5. Handle any unclosed possession at end of game
        if in_possession and current_possession_events:
            # Force close the possession
            possession = self._build_possession(
                current_possession_events, possession_number, metadata
            )
            if possession:
                possessions.append(possession)
                logger.info(f"Closed final possession at end of game")

        # 6. Validate and merge possessions if needed
        if self.validation.verify_possession_chains:
            logger.info("Validating possession chains...")
            validated_possessions = []
            for poss in possessions:
                # For now, we'll accept all possessions
                # Full validation would check the event list in each possession
                validated_possessions.append(poss)
            possessions = validated_possessions

        # 7. Merge possessions if configured
        if self.possession_detection.merge_offensive_rebounds:
            logger.info("Merging possessions with offensive rebounds...")
            possessions = self.merge_possessions_if_needed(possessions)

        logger.info(
            f"Detected {len(possessions)} possessions from {len(events)} events "
            f"in game {game_id}"
        )

        return possessions

    def _build_possession(
        self, events: List[Dict], possession_number: int, metadata: Dict
    ) -> Optional[PossessionBoundary]:
        """
        Build a PossessionBoundary object from a list of events.

        Args:
            events: List of events in the possession
            possession_number: Sequential number for this possession
            metadata: Game metadata dict

        Returns:
            PossessionBoundary object or None if invalid
        """
        if not events:
            return None

        start_event = events[0]
        end_event = events[-1]

        # Extract basic info
        try:
            offensive_team_id = self.determine_offensive_team(events)
            defensive_team_id = (
                metadata["away_team_id"]
                if offensive_team_id == metadata["home_team_id"]
                else metadata["home_team_id"]
            )

            # Calculate duration
            duration = self.calculate_duration(start_event, end_event)

            # Extract scores
            home_score_start = start_event.get("home_score", 0)
            away_score_start = start_event.get("away_score", 0)
            home_score_end = end_event.get("home_score", 0)
            away_score_end = end_event.get("away_score", 0)

            # Calculate score differential
            score_diff = self.calculate_score_differential(
                offensive_team_id,
                metadata["home_team_id"],
                home_score_start,
                away_score_start,
            )

            # Calculate points scored in possession
            if offensive_team_id == metadata["home_team_id"]:
                points_scored = home_score_end - home_score_start
            else:
                points_scored = away_score_end - away_score_start

            # Determine possession result
            end_event_type = end_event.get("event_type", "").lower()
            if "made" in end_event_type:
                possession_result = "made_shot"
            elif "missed" in end_event_type or "miss" in end_event_type:
                possession_result = "missed_shot"
            elif "turnover" in end_event_type:
                possession_result = "turnover"
            elif "foul" in end_event_type:
                possession_result = "foul"
            elif "period" in end_event_type:
                possession_result = "end_period"
            else:
                possession_result = "other"

            # Count shot attempts
            fga = sum(
                1
                for e in events
                if "shot" in e.get("event_type", "").lower()
                or "field goal" in e.get("event_type", "").lower()
            )
            fgm = sum(
                1
                for e in events
                if "made" in e.get("event_type", "").lower()
                and "shot" in e.get("event_type", "").lower()
            )
            threes_att = sum(
                1
                for e in events
                if "3" in e.get("event_type", "")
                or "three" in e.get("event_type", "").lower()
            )
            threes_made = sum(
                1
                for e in events
                if "made" in e.get("event_type", "").lower()
                and (
                    "3" in e.get("event_type", "")
                    or "three" in e.get("event_type", "").lower()
                )
            )

            # Context flags
            is_clutch = self.detect_clutch_time(start_event)
            is_fastbreak = self.detect_fastbreak(duration)
            is_garbage = False  # TODO: Implement garbage time detection
            has_timeout = any(
                "timeout" in e.get("event_type", "").lower() for e in events
            )

            # Create PossessionBoundary
            possession = PossessionBoundary(
                possession_number=possession_number,
                game_id=metadata["game_id"],
                season=metadata["season"],
                game_date=metadata["game_date"],
                start_event_id=start_event.get("event_id"),
                end_event_id=end_event.get("event_id"),
                event_count=len(events),
                period=start_event.get("period"),
                start_clock_minutes=start_event.get("clock_minutes"),
                start_clock_seconds=start_event.get("clock_seconds"),
                end_clock_minutes=end_event.get("clock_minutes"),
                end_clock_seconds=end_event.get("clock_seconds"),
                duration_seconds=duration,
                offensive_team_id=offensive_team_id,
                defensive_team_id=defensive_team_id,
                home_team_id=metadata["home_team_id"],
                away_team_id=metadata["away_team_id"],
                score_differential_start=score_diff,
                home_score_start=home_score_start,
                away_score_start=away_score_start,
                home_score_end=home_score_end,
                away_score_end=away_score_end,
                points_scored=points_scored,
                possession_result=possession_result,
                field_goals_attempted=fga,
                field_goals_made=fgm,
                three_pointers_attempted=threes_att,
                three_pointers_made=threes_made,
                is_clutch_time=is_clutch,
                is_fastbreak=is_fastbreak,
                is_garbage_time=is_garbage,
                has_timeout=has_timeout,
                validation_status="valid",
            )

            return possession

        except Exception as e:
            logger.error(f"Error building possession: {e}")
            return None

    def is_start_event(self, event: Dict) -> bool:
        """
        Check if event starts a new possession.

        Start events include:
        - Defensive rebound
        - Steal
        - Inbound pass (after opponent scores)
        - Jump ball won
        - Technical foul shot made (offense retains)

        Args:
            event: Event dictionary with 'event_type' key

        Returns:
            True if event starts a possession, False otherwise
        """
        event_type = event.get("event_type", "").lower()

        # O(1) lookup in cached set
        return event_type in self._start_event_types

    def is_end_event(self, event: Dict) -> bool:
        """
        Check if event ends current possession.

        End events include:
        - Shot made
        - Shot missed (and defensive rebound)
        - Turnover
        - End of period
        - Foul that gives possession to defense

        Args:
            event: Event dictionary with 'event_type' key

        Returns:
            True if event ends a possession, False otherwise
        """
        event_type = event.get("event_type", "").lower()

        # O(1) lookup in cached set
        if event_type in self._end_event_types:
            return True

        # Special case: fouls that change possession
        if "foul" in event_type:
            # Check if foul description indicates possession change
            description = event.get("description", "").lower()
            if any(
                keyword in description
                for keyword in ["offensive foul", "charge", "clear path"]
            ):
                return True

        return False

    def is_continuation_event(self, event: Dict) -> bool:
        """
        Check if event continues current possession.

        Continuation events include:
        - Offensive rebound (possession continues)
        - Some offensive fouls (possession retained)

        Args:
            event: Event dictionary with 'event_type' key

        Returns:
            True if event continues possession, False otherwise
        """
        event_type = event.get("event_type", "").lower()

        # O(1) lookup in cached set
        return event_type in self._continuation_event_types

    def calculate_duration(self, start_event: Dict, end_event: Dict) -> float:
        """
        Calculate possession duration in seconds.

        Handles game clock logic (counts down from 12:00 to 0:00 each period).

        Args:
            start_event: Event dictionary with clock_minutes, clock_seconds
            end_event: Event dictionary with clock_minutes, clock_seconds

        Returns:
            Duration in seconds (positive float)
        """
        # Extract clock times
        start_mins = start_event.get("clock_minutes", 0)
        start_secs = start_event.get("clock_seconds", 0.0)
        end_mins = end_event.get("clock_minutes", 0)
        end_secs = end_event.get("clock_seconds", 0.0)

        # Convert to total seconds (game clock counts down)
        start_total = start_mins * 60 + start_secs
        end_total = end_mins * 60 + end_secs

        # Duration is the difference (start is higher than end in game clock)
        duration = start_total - end_total

        # Validate duration is positive and within bounds
        min_duration = self.possession_detection.min_duration
        max_duration = self.possession_detection.max_duration

        if duration < 0:
            logger.warning(
                f"Negative duration calculated: {duration}s - possibly period boundary"
            )
            duration = abs(duration)

        if duration < min_duration or duration > max_duration:
            logger.warning(
                f"Duration {duration}s outside normal bounds "
                f"[{min_duration}, {max_duration}]"
            )

        return round(duration, 2)

    def determine_offensive_team(self, events: List[Dict]) -> int:
        """
        Determine which team has offensive possession.

        Looks at event types and team_id to determine offensive team.

        Args:
            events: List of events in the possession

        Returns:
            Team ID of offensive team
        """
        if not events:
            raise ValueError("Cannot determine offensive team from empty event list")

        # First event typically indicates offensive team
        first_event = events[0]
        event_type = first_event.get("event_type", "").lower()

        # For rebounds and steals, the team that got the ball is offense
        if "rebound" in event_type or "steal" in event_type:
            return first_event.get("team_id")

        # For inbounds, the inbounding team is offense
        if "inbound" in event_type:
            return first_event.get("team_id")

        # Look at subsequent events for shooting team
        for event in events:
            event_type = event.get("event_type", "").lower()
            if "shot" in event_type or "field goal" in event_type:
                return event.get("team_id")

        # Fallback: return team_id from first event
        logger.warning(f"Could not determine offensive team, using first event team_id")
        return first_event.get("team_id")

    def calculate_score_differential(
        self,
        offensive_team_id: int,
        home_team_id: int,
        home_score: int,
        away_score: int,
    ) -> int:
        """
        Calculate score differential from offensive team perspective.

        Args:
            offensive_team_id: Team ID of offensive team
            home_team_id: Team ID of home team
            home_score: Home team score
            away_score: Away team score

        Returns:
            Score differential (+/- from offensive team perspective)
        """
        if offensive_team_id == home_team_id:
            # Offensive team is home
            return home_score - away_score
        else:
            # Offensive team is away
            return away_score - home_score

    def detect_clutch_time(self, event: Dict) -> bool:
        """
        Detect if possession occurs during clutch time.

        Clutch time: Last 5 minutes of 4th quarter or OT, score within 5 points.

        Args:
            event: Event dictionary with period, clock, score info

        Returns:
            True if clutch time, False otherwise
        """
        period = event.get("period", 1)
        clock_minutes = event.get("clock_minutes", 12)
        clock_seconds = event.get("clock_seconds", 0.0)

        # Must be in 4th quarter or overtime
        if period < 4:
            return False

        # Calculate time remaining in period
        time_remaining = clock_minutes * 60 + clock_seconds

        # Must be last 5 minutes (300 seconds)
        clutch_time_threshold = self.context_detection.clutch_time_threshold
        if time_remaining > clutch_time_threshold:
            return False

        # Check score differential if available
        home_score = event.get("home_score", 0)
        away_score = event.get("away_score", 0)
        score_diff = abs(home_score - away_score)

        # Must be within 5 points
        clutch_score_margin = self.context_detection.clutch_score_margin
        return score_diff <= clutch_score_margin

    def detect_fastbreak(self, duration: float) -> bool:
        """
        Detect if possession is a fastbreak.

        Fastbreak: Possession duration < 8 seconds.

        Args:
            duration: Possession duration in seconds

        Returns:
            True if fastbreak, False otherwise
        """
        fastbreak_threshold = self.context_detection.fastbreak_max_duration
        return duration < fastbreak_threshold

    def validate_possession_chain(self, events: List[Dict]) -> Tuple[bool, str]:
        """
        Validate that events in possession form a logical chain.

        Checks:
        - Events are in chronological order
        - No impossible event sequences
        - Team consistency maintained

        Args:
            events: List of events in the possession

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not events:
            return (False, "Empty event list")

        # Check events are in chronological order (clock counts down)
        for i in range(len(events) - 1):
            curr = events[i]
            next_event = events[i + 1]

            curr_period = curr.get("period", 0)
            next_period = next_event.get("period", 0)

            # Same period: clock should decrease
            if curr_period == next_period:
                curr_time = curr.get("clock_minutes", 0) * 60 + curr.get(
                    "clock_seconds", 0
                )
                next_time = next_event.get("clock_minutes", 0) * 60 + next_event.get(
                    "clock_seconds", 0
                )

                if next_time > curr_time:
                    return (False, f"Events not in chronological order at index {i}")

        # Check for impossible sequences
        for i in range(len(events) - 1):
            curr_type = events[i].get("event_type", "").lower()
            next_type = events[i + 1].get("event_type", "").lower()

            # Made shot cannot be followed by offensive rebound
            if "made" in curr_type and "offensive rebound" in next_type:
                return (
                    False,
                    "Impossible sequence: made shot followed by offensive rebound",
                )

        return (True, "")

    def find_orphaned_events(
        self, all_events: List[Dict], possessions: List[PossessionBoundary]
    ) -> List[Dict]:
        """
        Find events that weren't assigned to any possession.

        Args:
            all_events: Complete list of events for game
            possessions: List of detected possessions

        Returns:
            List of orphaned events
        """
        # Create set of all event IDs assigned to possessions
        assigned_event_ids = set()
        for poss in possessions:
            # We need to track event IDs between start and end
            # For now, just track start and end event IDs
            assigned_event_ids.add(poss.start_event_id)
            assigned_event_ids.add(poss.end_event_id)

        # Find events not in assigned set
        orphaned = []
        for event in all_events:
            event_id = event.get("event_id")
            if event_id and event_id not in assigned_event_ids:
                orphaned.append(event)

        return orphaned

    def merge_possessions_if_needed(
        self, possessions: List[PossessionBoundary]
    ) -> List[PossessionBoundary]:
        """
        Merge possessions that should be combined (e.g., offensive rebound cases).

        Args:
            possessions: Initial list of possessions

        Returns:
            Merged list of possessions
        """
        if len(possessions) < 2:
            return possessions

        merged = []
        i = 0

        while i < len(possessions):
            current = possessions[i]

            # Check if next possession should be merged
            if i + 1 < len(possessions):
                next_poss = possessions[i + 1]

                # Merge if same offensive team (indicates offensive rebound continuation)
                if current.offensive_team_id == next_poss.offensive_team_id:
                    # Merge: extend current possession to include next
                    current.end_event_id = next_poss.end_event_id
                    current.end_clock_minutes = next_poss.end_clock_minutes
                    current.end_clock_seconds = next_poss.end_clock_seconds
                    current.event_count += next_poss.event_count
                    current.points_scored += next_poss.points_scored
                    current.field_goals_attempted += next_poss.field_goals_attempted
                    current.field_goals_made += next_poss.field_goals_made
                    # Recalculate duration
                    current.duration_seconds = (
                        current.start_clock_minutes * 60 + current.start_clock_seconds
                    ) - (current.end_clock_minutes * 60 + current.end_clock_seconds)
                    # Skip next possession since we merged it
                    i += 2
                else:
                    # Different teams, don't merge
                    merged.append(current)
                    i += 1
            else:
                # Last possession, just add it
                merged.append(current)
                i += 1

        return merged

    def __repr__(self) -> str:
        """String representation of detector."""
        return (
            f"PossessionDetector("
            f"start_events={len(self._start_event_types)}, "
            f"end_events={len(self._end_event_types)})"
        )


# Utility functions for possession detection


def validate_event_list(events: List[Dict]) -> bool:
    """
    Validate that event list has required fields and is properly sorted.

    Args:
        events: List of event dictionaries

    Returns:
        True if valid, False otherwise
    """
    if not events:
        return False

    required_fields = [
        "event_id",
        "event_type",
        "period",
        "clock_minutes",
        "clock_seconds",
        "team_id",
    ]

    # Check all events have required fields
    for event in events:
        for field in required_fields:
            if field not in event:
                logger.error(f"Event missing required field: {field}")
                return False

    # Check events are sorted by (period, clock) - clock counts down
    for i in range(len(events) - 1):
        curr = events[i]
        next_event = events[i + 1]

        curr_period = curr["period"]
        next_period = next_event["period"]
        curr_time = curr["clock_minutes"] * 60 + curr["clock_seconds"]
        next_time = next_event["clock_minutes"] * 60 + next_event["clock_seconds"]

        # Period should increase or stay same
        if next_period < curr_period:
            logger.error("Events not sorted: period decreased")
            return False

        # Within same period, time should decrease (clock counts down)
        if curr_period == next_period and next_time > curr_time:
            logger.error("Events not sorted: clock time increased within period")
            return False

    return True


def extract_game_metadata(events: List[Dict]) -> Dict:
    """
    Extract game-level metadata from event list.

    Args:
        events: List of event dictionaries

    Returns:
        Dictionary with game_id, season, game_date, home_team_id, away_team_id
    """
    if not events:
        raise ValueError("Cannot extract metadata from empty event list")

    first_event = events[0]

    # Extract basic metadata from first event
    metadata = {
        "game_id": first_event.get("game_id"),
        "season": first_event.get("season"),
        "game_date": first_event.get("game_date"),
    }

    # Determine home/away teams by looking at all events
    # Home team typically has 'home' in team description or is listed first
    teams_seen = set()
    for event in events:
        team_id = event.get("team_id")
        if team_id:
            teams_seen.add(team_id)

    # Assume first two unique team IDs are home and away
    teams_list = sorted(list(teams_seen))  # Sort for consistency
    if len(teams_list) >= 2:
        metadata["home_team_id"] = teams_list[0]
        metadata["away_team_id"] = teams_list[1]
    else:
        metadata["home_team_id"] = None
        metadata["away_team_id"] = None

    return metadata
