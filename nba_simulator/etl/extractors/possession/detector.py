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

    # Identification (required fields)
    possession_number: int
    game_id: str
    season: int
    game_date: datetime

    # Event boundaries (required)
    start_event_id: int
    end_event_id: int

    # Temporal boundaries (required)
    period: int
    start_clock_minutes: int
    start_clock_seconds: float
    end_clock_minutes: int
    end_clock_seconds: float

    # Team attribution (required)
    offensive_team_id: int
    defensive_team_id: int
    home_team_id: int
    away_team_id: int

    # Optional fields with defaults
    event_count: int = 0
    duration_seconds: float = 0.0

    # Score context (optional)
    score_differential_start: int = 0
    home_score_start: int = 0
    away_score_start: int = 0
    home_score_end: int = 0
    away_score_end: int = 0

    # Possession outcome (optional)
    points_scored: int = 0
    possession_result: str = (
        ""  # 'made_shot', 'missed_shot', 'turnover', 'foul', 'end_period'
    )

    # Shot statistics (optional)
    field_goals_attempted: int = 0
    field_goals_made: int = 0
    three_pointers_attempted: int = 0
    three_pointers_made: int = 0
    free_throws_attempted: int = 0
    free_throws_made: int = 0

    # Context flags (optional)
    is_clutch_time: bool = False
    is_garbage_time: bool = False
    is_fastbreak: bool = False
    has_timeout: bool = False

    # Validation (optional)
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

        REWRITTEN (Nov 5, 2025) to fix critical flaw: Only detected ~46 possessions/game
        instead of ~200 because it only looked for jump balls.

        New algorithm properly tracks possession changes:
        - Made shots → opponent gets ball (inbound) [~90-110 per game]
        - Defensive rebounds → rebounding team gets ball [~40-50 per game]
        - Turnovers → opponent gets ball [~25-30 per game]
        - Steals → stealing team gets ball [~10-20 per game]
        - Offensive rebounds → same team keeps ball (NO possession change)

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
        current_offensive_team_id = None

        def get_opponent_team(team_id):
            """
            Get opponent team ID.

            Returns the opponent's team ID given a team ID.
            If unknown team_id provided, defaults to home team as opponent.
            """
            if team_id == home_team_id:
                return away_team_id
            elif team_id == away_team_id:
                return home_team_id
            else:
                # CRITICAL FIX: Unknown team - log error and default to home team
                logger.error(
                    f"Unknown team_id {team_id} (not {home_team_id} or {away_team_id}), "
                    f"defaulting to home team {home_team_id}"
                )
                return home_team_id

        def get_event_description(event):
            """
            Get event description from event_data JSONB field.

            FIX #6: Correctly parse home_description/visitor_description from event_data
            instead of looking for non-existent 'description' field.

            Args:
                event: Event dictionary with event_data JSONB field

            Returns:
                str: Combined description text (lowercase) or empty string
            """
            event_data = event.get("event_data", {})
            if not event_data:
                return ""

            home_desc = (event_data.get("home_description") or "").lower()
            visitor_desc = (event_data.get("visitor_description") or "").lower()
            neutral_desc = (event_data.get("neutral_description") or "").lower()

            # Combine all descriptions
            combined = " ".join([home_desc, visitor_desc, neutral_desc]).strip()
            return combined

        def infer_team_from_event_data(event):
            """
            Infer team_id from event_data when team_id is NULL.

            For rebounds without team_id, parse home_description or visitor_description
            to determine which team got the rebound.

            FIX #4: Now case-insensitive and checks for multiple keywords.

            Args:
                event: Event dictionary with event_data JSONB field

            Returns:
                int: team_id (home_team_id or away_team_id) or None if cannot infer
            """
            event_data = event.get("event_data", {})
            if not event_data:
                return None

            # FIX #4: Use .lower() for case-insensitive matching
            home_desc = (event_data.get("home_description") or "").lower()
            visitor_desc = (event_data.get("visitor_description") or "").lower()

            # Keywords that indicate team action (not just "Rebound")
            team_keywords = ["rebound", "reb", "defensive rebound", "offensive rebound"]

            # Check if home team made the play
            if home_desc and any(keyword in home_desc for keyword in team_keywords):
                logger.debug(f"Inferred home team from: {home_desc}")
                return home_team_id

            # Check if visitor/away team made the play
            if visitor_desc and any(
                keyword in visitor_desc for keyword in team_keywords
            ):
                logger.debug(f"Inferred away team from: {visitor_desc}")
                return away_team_id

            # Could not infer team
            logger.debug(
                f"Cannot infer team from event_data: home='{home_desc}', visitor='{visitor_desc}'"
            )
            return None

        def close_possession(events_list, poss_num, team_id, reason=""):
            """
            Close current possession and add to list.

            CRITICAL FIX (Bug #1): Now requires team_id parameter to pass to _build_possession.
            This prevents context loss when event lists are empty or minimal.

            Args:
                events_list: List of events in the possession
                poss_num: Current possession number
                team_id: Offensive team ID for this possession
                reason: Reason for closing (for logging)

            Returns:
                Updated possession number
            """
            nonlocal consecutive_empty_possessions

            if not events_list:
                consecutive_empty_possessions += 1
                if consecutive_empty_possessions > 5:
                    logger.warning(
                        f"Too many consecutive empty possessions ({consecutive_empty_possessions}) - may indicate logic error"
                    )
                return poss_num

            consecutive_empty_possessions = 0  # Reset counter
            possession = self._build_possession(
                events_list, poss_num, metadata, team_id
            )
            if possession:
                possessions.append(possession)
                logger.debug(
                    f"Closed possession #{poss_num}: {len(events_list)} events, team={possession.offensive_team_id}, reason={reason}"
                )
                return poss_num + 1
            return poss_num

        def start_possession(team_id, start_event, reason=""):
            """Start new possession for given team."""
            logger.debug(
                f"Started possession for team {team_id} at event {start_event.get('event_id')}, reason={reason}"
            )
            return [start_event]

        # FIX #3: Add validation logging to track possession changes
        possession_change_counter = {
            "made_shot": 0,
            "defensive_rebound": 0,
            "turnover": 0,
            "offensive_foul": 0,
            "violation": 0,
            "jump_ball": 0,
            "period_end": 0,
            "team_correction": 0,
        }

        # Phase 5: Safeguards - track empty possessions
        consecutive_empty_possessions = 0

        # 4. Iterate through events with state machine logic
        for i, event in enumerate(events):
            event_type = event.get("event_type", "").lower()

            # CRITICAL FIX: Use normalize_team_id() to ensure consistent type conversion
            event_team_id = normalize_team_id(event.get("team_id"))

            # For rebounds with NULL team_id, try to infer from event_data
            if event_team_id is None and event_type == "rebound":
                event_team_id = infer_team_from_event_data(event)
                if event_team_id:
                    logger.debug(f"Inferred team_id {event_team_id} for rebound event")

            # Initialize first possession if not started yet
            if current_offensive_team_id is None and event_team_id:
                # Start first possession with first event
                current_possession_events = start_possession(
                    event_team_id, event, "first_event"
                )
                current_offensive_team_id = event_team_id
                continue  # Skip to next event

            # FIX #4: Guard against empty possession state (sync error recovery)
            if current_offensive_team_id and not current_possession_events:
                # We closed previous possession but haven't started new one yet
                # This indicates state machine may be out of sync
                if event_team_id and event_team_id != current_offensive_team_id:
                    # Event is by different team - switch possession
                    logger.debug(
                        f"Empty possession state - switching from {current_offensive_team_id} to {event_team_id} "
                        f"(event_type={event_type}, event_id={event.get('event_id')})"
                    )
                    current_offensive_team_id = event_team_id

                # Start new possession with this event
                current_possession_events = start_possession(
                    current_offensive_team_id or event_team_id,
                    event,
                    "empty_state_recovery",
                )
                if not current_offensive_team_id:
                    current_offensive_team_id = event_team_id
                continue

            # POSSESSION CHANGE EVENT #1: Made Shot → Opponent Inbounds
            if event_type == "made_shot":
                # SMARTER LOGIC: Trust the made_shot event type over team_id matching
                # The team that made the shot is the shooter (use event's team_id)
                shooter_team = (
                    event_team_id if event_team_id else current_offensive_team_id
                )

                if not shooter_team:
                    # Can't determine shooter - skip this event
                    logger.warning(f"Made shot with no team info - skipping")
                    continue

                # Log if team mismatch (data quality indicator, not error)
                if (
                    current_offensive_team_id
                    and event_team_id
                    and event_team_id != current_offensive_team_id
                ):
                    logger.debug(
                        f"Team mismatch on made_shot: expected {current_offensive_team_id}, "
                        f"got {event_team_id} - using event's team"
                    )

                # Add event and close possession (use shooter's team for possession)
                current_possession_events.append(event)
                possession_number = close_possession(
                    current_possession_events,
                    possession_number,
                    shooter_team,  # Use actual shooter's team
                    "made_shot",
                )
                possession_change_counter["made_shot"] += 1

                # Opponent gets ball (use shooter's team for opponent lookup)
                opponent_team = get_opponent_team(shooter_team)
                current_possession_events = []
                current_offensive_team_id = opponent_team

                logger.debug(
                    f"Team {opponent_team} gets ball after made shot by {shooter_team}"
                )

            # POSSESSION CHANGE EVENT #2: Defensive Rebound
            elif event_type == "rebound":
                # FIX #6d: Improved handling for rebounds with NULL team_id
                if event_team_id is None:
                    # Try to infer from event_data first (most reliable)
                    inferred_team = infer_team_from_event_data(event)

                    if inferred_team:
                        event_team_id = inferred_team
                        logger.debug(
                            f"Inferred team {event_team_id} from event_data for rebound "
                            f"(event_id={event.get('event_id')})"
                        )
                    elif current_offensive_team_id and i > 0:
                        # Check previous event to determine rebound type
                        prev_event = events[i - 1]
                        prev_type = prev_event.get("event_type", "").lower()

                        if "missed" in prev_type:
                            # Previous event was missed shot - likely defensive rebound
                            event_team_id = get_opponent_team(current_offensive_team_id)
                            logger.debug(
                                f"NULL rebound after missed shot - assuming defensive by team {event_team_id} "
                                f"(event_id={event.get('event_id')})"
                            )
                        else:
                            # No missed shot before this - could be offensive rebound or ambiguous
                            # Skip rather than guess wrong
                            logger.warning(
                                f"Skipping rebound with NULL team_id - cannot determine type, no previous missed shot "
                                f"(event_id={event.get('event_id')}, prev_type={prev_type})"
                            )
                            continue
                    else:
                        # No active possession yet or first event - skip this rebound
                        logger.warning(
                            f"Skipping rebound event - NULL team_id and no context available "
                            f"(event_id={event.get('event_id')})"
                        )
                        continue

                if current_offensive_team_id is None:
                    # First possession of game - rebound starts it
                    current_possession_events = start_possession(
                        event_team_id, event, "first_rebound"
                    )
                    current_offensive_team_id = event_team_id
                elif event_team_id != current_offensive_team_id:
                    # Defensive rebound - possession changes
                    current_possession_events.append(event)
                    possession_number = close_possession(
                        current_possession_events,
                        possession_number,
                        current_offensive_team_id,
                        "defensive_rebound",
                    )
                    # Track possession change
                    possession_change_counter["defensive_rebound"] += 1
                    # Rebounding team gets ball
                    current_possession_events = []
                    current_offensive_team_id = event_team_id
                    # Don't add rebound event to next possession
                    logger.debug(
                        f"Team {event_team_id} gets ball after defensive rebound"
                    )
                else:
                    # Offensive rebound - possession continues
                    current_possession_events.append(event)
                    logger.debug(f"Offensive rebound - possession continues")

                # Phase 3: Recovery logic - if we have a rebound but no active possession, start one
                if not current_possession_events and event_team_id:
                    logger.debug(
                        f"Rebound with no active possession - starting new possession for {event_team_id}"
                    )
                    current_possession_events = start_possession(
                        event_team_id, event, "rebound_recovery"
                    )
                    current_offensive_team_id = event_team_id

            # POSSESSION CHANGE EVENT #3: Turnover
            elif event_type == "turnover":
                # SMARTER LOGIC: Trust the turnover event type
                # The team that turned it over loses possession
                turnover_team = (
                    event_team_id if event_team_id else current_offensive_team_id
                )

                if not turnover_team:
                    # Can't determine who turned it over - add to current possession
                    logger.warning(
                        f"Turnover with no team info - adding to current possession"
                    )
                    if current_possession_events:
                        current_possession_events.append(event)
                    continue

                # Log if team mismatch (data quality indicator)
                if (
                    current_offensive_team_id
                    and event_team_id
                    and event_team_id != current_offensive_team_id
                ):
                    logger.debug(
                        f"Team mismatch on turnover: expected {current_offensive_team_id}, "
                        f"got {event_team_id} - using event's team"
                    )

                # Add event and close possession
                current_possession_events.append(event)
                possession_number = close_possession(
                    current_possession_events,
                    possession_number,
                    turnover_team,  # Use actual turnover team
                    "turnover",
                )
                possession_change_counter["turnover"] += 1

                # Opponent gets ball
                opponent_team = get_opponent_team(turnover_team)
                current_possession_events = []
                current_offensive_team_id = opponent_team

                logger.debug(
                    f"Team {opponent_team} gets ball after turnover by {turnover_team}"
                )

            # NOTE: "steal" event type removed (Bug #3 fix) - doesn't exist in database
            # Steals are already captured as turnover events above

            # POSSESSION START EVENT #4: Jump Ball
            elif event_type == "jump_ball":
                # Close previous possession if any
                if current_possession_events:
                    possession_number = close_possession(
                        current_possession_events,
                        possession_number,
                        current_offensive_team_id,
                        "jump_ball",
                    )
                    # Track possession change
                    possession_change_counter["jump_ball"] += 1
                # Start new possession (jump ball winner gets ball)
                current_possession_events = start_possession(
                    event_team_id, event, "jump_ball"
                )
                current_offensive_team_id = event_team_id

            # POSSESSION END EVENT: Missed Shot (only ends if followed by defensive rebound)
            elif event_type == "missed_shot":
                # SMARTER LOGIC: Trust the missed shot event
                # If team doesn't match, it means we lost track - switch to shooter's team
                if current_offensive_team_id != event_team_id and event_team_id:
                    logger.debug(
                        f"Team mismatch on missed_shot: expected {current_offensive_team_id}, "
                        f"got {event_team_id} - switching to event's team"
                    )

                    # Close current (wrong) possession if it has events
                    if current_possession_events:
                        possession_number = close_possession(
                            current_possession_events,
                            possession_number,
                            current_offensive_team_id,
                            "team_correction",
                        )
                        possession_change_counter["team_correction"] += 1

                    # Start new possession for actual shooter
                    current_possession_events = []
                    current_offensive_team_id = event_team_id

                # Add missed shot to current possession (don't close yet - wait for rebound)
                current_possession_events.append(event)

            # CONTINUATION EVENT: Free Throws
            elif event_type == "free_throw":
                # Free throws continue possession (or end it if made on final attempt)
                if current_offensive_team_id == event_team_id:
                    current_possession_events.append(event)
                else:
                    current_possession_events.append(event)

            # SPECIAL EVENT: Period End
            elif event_type == "period_end":
                # Close possession at end of period
                if current_possession_events:
                    current_possession_events.append(event)
                    possession_number = close_possession(
                        current_possession_events,
                        possession_number,
                        current_offensive_team_id,
                        "period_end",
                    )
                    # Track possession change
                    possession_change_counter["period_end"] += 1
                    current_possession_events = []
                    current_offensive_team_id = None

            # FIX #6a: POSSESSION CHANGE EVENT - Offensive Fouls
            elif event_type == "foul":
                # Parse event description to determine foul type
                description = get_event_description(event)

                # FIX: Be more specific with offensive foul detection to avoid false positives
                # Only match explicit offensive foul language
                is_offensive_foul = (
                    "offensive foul" in description
                    or "charging foul" in description
                    or " charge "
                    in description  # Space-bounded to avoid "discharge", "charged"
                    or description.startswith("charge ")
                    or description.endswith(" charge")
                    or "clear path" in description
                    or "clearpath" in description
                )

                if is_offensive_foul and current_offensive_team_id == event_team_id:
                    # Offensive foul by offensive team - possession changes
                    current_possession_events.append(event)
                    possession_number = close_possession(
                        current_possession_events,
                        possession_number,
                        current_offensive_team_id,
                        "offensive_foul",
                    )
                    # Track possession change
                    possession_change_counter["offensive_foul"] += 1
                    # Opponent gets ball
                    opponent_team = get_opponent_team(event_team_id)
                    current_possession_events = []
                    current_offensive_team_id = opponent_team
                    logger.debug(
                        f"Team {opponent_team} gets ball after offensive foul by {event_team_id}: '{description[:50]}'"
                    )
                else:
                    # Regular defensive foul - possession continues
                    if current_offensive_team_id:
                        current_possession_events.append(event)

            # FIX #6b: POSSESSION CHANGE EVENT - Violations
            elif event_type == "other":
                # Parse description to check if it's a violation
                description = get_event_description(event)

                is_violation = "violation" in description

                if is_violation and event_team_id:
                    # Violation - possession changes to opponent
                    if (
                        current_possession_events
                        and current_offensive_team_id == event_team_id
                    ):
                        current_possession_events.append(event)
                        possession_number = close_possession(
                            current_possession_events,
                            possession_number,
                            current_offensive_team_id,
                            "violation",
                        )
                        # Track possession change
                        possession_change_counter["violation"] += 1
                        # Opponent gets ball
                        opponent_team = get_opponent_team(event_team_id)
                        current_possession_events = []
                        current_offensive_team_id = opponent_team
                        logger.debug(
                            f"Team {opponent_team} gets ball after violation by {event_team_id}"
                        )
                    else:
                        # Edge case: violation before possession established or by wrong team
                        if current_offensive_team_id:
                            current_possession_events.append(event)
                else:
                    # Non-violation "other" event
                    if current_offensive_team_id:
                        current_possession_events.append(event)

            # ALL OTHER EVENTS: Add to current possession
            else:
                if current_offensive_team_id:
                    current_possession_events.append(event)
                elif event_type not in ["", "unknown"]:
                    # Event before first possession starts
                    logger.debug(f"Event {event_type} before first possession")

        # 5. Handle any unclosed possession at end of game
        if current_possession_events:
            possession_number = close_possession(
                current_possession_events,
                possession_number,
                current_offensive_team_id,
                "end_of_game",
            )

        # Log possession change statistics
        total_changes = sum(possession_change_counter.values())
        logger.info(
            f"Detected {len(possessions)} possessions from {len(events)} events "
            f"in game {game_id}"
        )
        logger.info(
            f"Possession changes by type (total={total_changes}): "
            f"made_shot={possession_change_counter['made_shot']}, "
            f"def_reb={possession_change_counter['defensive_rebound']}, "
            f"turnover={possession_change_counter['turnover']}, "
            f"off_foul={possession_change_counter['offensive_foul']}, "
            f"violation={possession_change_counter['violation']}, "
            f"jump_ball={possession_change_counter['jump_ball']}, "
            f"period_end={possession_change_counter['period_end']}"
        )

        return possessions

    def _build_possession(
        self,
        events: List[Dict],
        possession_number: int,
        metadata: Dict,
        offensive_team_id: int,
    ) -> Optional[PossessionBoundary]:
        """
        Build a PossessionBoundary object from a list of events.

        CRITICAL FIX (Bug #1): Now accepts offensive_team_id as parameter instead of
        inferring from events. This prevents context loss when possessions have
        empty or minimal event lists.

        Args:
            events: List of events in the possession
            possession_number: Sequential number for this possession
            metadata: Game metadata dict
            offensive_team_id: Team ID that has offensive possession (must be provided)

        Returns:
            PossessionBoundary object or None if invalid
        """
        if not events:
            return None

        start_event = events[0]
        end_event = events[-1]

        # Extract basic info
        try:
            # CRITICAL FIX: Use provided offensive_team_id instead of inferring
            # offensive_team_id = self.determine_offensive_team(events)  # OLD WAY
            defensive_team_id = (
                metadata["away_team_id"]
                if offensive_team_id == metadata["home_team_id"]
                else metadata["home_team_id"]
            )

            # Calculate duration
            duration = self.calculate_duration(start_event, end_event)

            # Extract scores (handle None values)
            home_score_start = start_event.get("home_score") or 0
            away_score_start = start_event.get("away_score") or 0
            home_score_end = end_event.get("home_score") or 0
            away_score_end = end_event.get("away_score") or 0

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

    def is_start_event(
        self, event: Dict, current_offensive_team_id: Optional[int] = None
    ) -> bool:
        """
        Check if event starts a new possession.

        Start events include:
        - Defensive rebound (team gets ball after opponent miss)
        - Jump ball
        - Turnover by opponent

        Args:
            event: Event dictionary with 'event_type' key
            current_offensive_team_id: Team currently on offense (None if no active possession)

        Returns:
            True if event starts a possession, False otherwise
        """
        event_type = event.get("event_type", "").lower()
        event_team_id = event.get("team_id")

        # Special handling for rebounds - defensive rebound starts new possession
        if event_type == "rebound":
            if current_offensive_team_id is None:
                # First possession - any rebound could start it
                return True
            else:
                # Defensive rebound: rebounding team != offensive team
                return event_team_id != current_offensive_team_id

        # O(1) lookup in cached set for other events
        return event_type in self._start_event_types

    def is_end_event(
        self, event: Dict, current_offensive_team_id: Optional[int] = None
    ) -> bool:
        """
        Check if event ends current possession.

        End events include:
        - Shot made
        - Shot missed (but only if followed by defensive rebound)
        - Turnover by offensive team
        - End of period
        - Foul that gives possession to defense

        Args:
            event: Event dictionary with 'event_type' key
            current_offensive_team_id: Team currently on offense (None if no active possession)

        Returns:
            True if event ends a possession, False otherwise
        """
        event_type = event.get("event_type", "").lower()
        event_team_id = event.get("team_id")

        # Special handling for rebounds - defensive rebound ends possession
        if event_type == "rebound":
            if current_offensive_team_id is not None:
                # Defensive rebound ends possession (different team gets ball)
                return event_team_id != current_offensive_team_id
            return False  # Can't end possession if none is active

        # O(1) lookup in cached set (includes turnover, made_shot, missed_shot, period_end)
        if event_type in self._end_event_types:
            return True

        # Special case: fouls that change possession
        if "foul" in event_type:
            # Check if foul description indicates possession change
            description = (event.get("description") or "").lower()
            if any(
                keyword in description
                for keyword in ["offensive foul", "charge", "clear path"]
            ):
                return True

        return False

    def is_continuation_event(
        self, event: Dict, current_offensive_team_id: Optional[int] = None
    ) -> bool:
        """
        Check if event continues current possession.

        Continuation events include:
        - Offensive rebound (same team keeps possession)
        - Free throws (possession typically continues)
        - Some offensive fouls (possession retained)

        Args:
            event: Event dictionary with 'event_type' key
            current_offensive_team_id: Team currently on offense (None if no active possession)

        Returns:
            True if event continues possession, False otherwise
        """
        event_type = event.get("event_type", "").lower()
        event_team_id = event.get("team_id")

        # Special handling for rebounds - offensive rebound continues possession
        if event_type == "rebound":
            if current_offensive_team_id is not None:
                # Offensive rebound: same team keeps ball
                return event_team_id == current_offensive_team_id
            return False  # Can't continue if no possession active

        # O(1) lookup in cached set for other events (like free throws)
        return event_type in self._continuation_event_types

    def calculate_duration(self, start_event: Dict, end_event: Dict) -> float:
        """
        Calculate possession duration in seconds.

        Handles game clock logic (counts down from 12:00 to 0:00 each period).

        FIX #5: Now properly handles period boundaries to avoid negative durations
        and 700s+ outliers.

        Args:
            start_event: Event dictionary with clock_minutes, clock_seconds, period
            end_event: Event dictionary with clock_minutes, clock_seconds, period

        Returns:
            Duration in seconds (positive float)
        """
        # Extract clock times, handling None values
        start_mins = start_event.get("clock_minutes") or 0
        start_secs = start_event.get("clock_seconds") or 0.0
        end_mins = end_event.get("clock_minutes") or 0
        end_secs = end_event.get("clock_seconds") or 0.0

        # FIX #5: Extract period information
        start_period = start_event.get("period", 1)
        end_period = end_event.get("period", 1)

        # Convert to float if needed
        try:
            start_mins = float(start_mins)
            start_secs = float(start_secs)
            end_mins = float(end_mins)
            end_secs = float(end_secs)
        except (TypeError, ValueError):
            logger.warning(
                f"Invalid clock values: start=({start_mins}, {start_secs}), end=({end_mins}, {end_secs})"
            )
            return 0.0

        # Convert to total seconds (game clock counts down)
        start_total = start_mins * 60 + start_secs
        end_total = end_mins * 60 + end_secs

        # FIX #5: Check for period boundary
        if start_period != end_period:
            # Possession spans multiple periods - use only time in start period
            # The possession ended at period boundary, so duration is from start to 0:00
            logger.debug(
                f"Possession spans periods {start_period} → {end_period}, "
                f"using start period time only: {start_total}s"
            )
            duration = start_total  # Time from possession start to period end
        else:
            # Normal case: same period
            duration = start_total - end_total

        # Validate duration is positive and within bounds
        min_duration = self.possession_detection.min_duration
        max_duration = self.possession_detection.max_duration

        if duration < 0:
            # FIX #5: This should rarely happen now, but handle gracefully
            logger.error(
                f"Negative duration: {duration}s (periods: {start_period} → {end_period}), "
                f"returning 0"
            )
            return 0.0

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

        # Helper to convert team_id to integer
        def to_int_team_id(team_id):
            if team_id:
                try:
                    return int(float(team_id))
                except (ValueError, TypeError):
                    return 0
            return 0

        # For rebounds and steals, the team that got the ball is offense
        if "rebound" in event_type or "steal" in event_type:
            return to_int_team_id(first_event.get("team_id"))

        # For inbounds, the inbounding team is offense
        if "inbound" in event_type:
            return to_int_team_id(first_event.get("team_id"))

        # Look at subsequent events for shooting team
        for event in events:
            event_type = event.get("event_type", "").lower()
            if "shot" in event_type or "field goal" in event_type:
                return to_int_team_id(event.get("team_id"))

        # Fallback: return team_id from first event
        logger.warning(f"Could not determine offensive team, using first event team_id")
        team_id = first_event.get("team_id")
        # Convert to integer if it's a string
        if team_id:
            try:
                return int(float(team_id))
            except (ValueError, TypeError):
                logger.warning(f"Could not convert team_id {team_id} to integer")
                return 0
        return 0

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
        # Handle None values
        home_score = home_score or 0
        away_score = away_score or 0

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


def normalize_team_id(team_id) -> Optional[int]:
    """
    Convert team_id to integer, handling various input types.

    Handles string, float, int, and scientific notation formats.
    Returns None for invalid or None inputs.

    Args:
        team_id: Team ID in any format (int, str, float, or None)

    Returns:
        Integer team ID, or None if invalid

    Examples:
        normalize_team_id(1610612747) -> 1610612747
        normalize_team_id("1610612747") -> 1610612747
        normalize_team_id(1.610612747e9) -> 1610612747
        normalize_team_id("invalid") -> None
        normalize_team_id(None) -> None
    """
    if team_id is None:
        return None

    try:
        # Convert to float first (handles scientific notation), then to int
        return int(float(team_id))
    except (ValueError, TypeError, OverflowError):
        logger.warning(f"Invalid team_id: {team_id} (type: {type(team_id).__name__})")
        return None


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
    # CRITICAL FIX: Normalize team_id BEFORE adding to set to avoid spurious IDs
    teams_seen = set()
    for event in events:
        team_id = normalize_team_id(event.get("team_id"))
        if team_id:
            teams_seen.add(team_id)  # Now all integers

    # Assume first two unique team IDs are home and away (already integers)
    teams_list = sorted(list(teams_seen))  # Sort for consistency

    if len(teams_list) >= 2:
        metadata["home_team_id"] = teams_list[0]  # Already int
        metadata["away_team_id"] = teams_list[1]  # Already int
    elif len(teams_list) == 1:
        # Only one team found - use it for both (edge case)
        logger.warning(f"Only one team found in events: {teams_list[0]}")
        metadata["home_team_id"] = teams_list[0]
        metadata["away_team_id"] = teams_list[0]
    else:
        # No valid teams found
        logger.error("No valid team IDs found in events")
        metadata["home_team_id"] = 0
        metadata["away_team_id"] = 0

    return metadata
