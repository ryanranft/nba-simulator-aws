#!/usr/bin/env python3
"""
Test Phase 2 Fixes - Possession Detection Improvements

Tests the bug fixes for:
- Fix #6a: Foul handling (offensive fouls, charges)
- Fix #6b: Violation handling
- Fix #6c: Out-of-bounds handling
- Fix #6d: Improved NULL team_id rebound handling
- Fix #7: Team ID normalization (float handling)

Expected: 195-205 possessions/game (95%+ detection)
"""

import psycopg2
import os
import statistics
from dataclasses import dataclass
from typing import List, Dict
from nba_simulator.etl.extractors.possession.detector import PossessionDetector


# Minimal config classes
@dataclass
class MinimalPossessionDetectionConfig:
    min_duration: float = 0.0
    max_duration: float = 120.0
    start_events: List[str] = None
    end_events: List[str] = None
    continuation_events: List[str] = None
    edge_cases: Dict = None
    merge_offensive_rebounds: bool = True

    def __post_init__(self):
        if self.start_events is None:
            self.start_events = [
                "jump_ball",
                "made_shot",
                "defensive_rebound",
                "turnover",
                "steal",
            ]
        if self.end_events is None:
            self.end_events = ["made_shot", "missed_shot", "turnover", "period_end"]
        if self.continuation_events is None:
            self.continuation_events = ["free_throw", "offensive_rebound"]
        if self.edge_cases is None:
            self.edge_cases = {}


@dataclass
class MinimalValidationConfig:
    enable_oliver_validation: bool = False
    oliver_tolerance_pct: float = 10.0
    oliver_formula_coefficients: Dict = None
    check_duration_bounds: bool = True
    warn_if_duration_outlier: bool = True
    outlier_threshold_seconds: float = 60.0
    verify_possession_chains: bool = False
    check_orphaned_events: bool = False
    max_orphaned_events_pct: float = 5.0
    verify_score_progression: bool = False
    check_impossible_scores: bool = False

    def __post_init__(self):
        if self.oliver_formula_coefficients is None:
            self.oliver_formula_coefficients = {"fta_coefficient": 0.44}


@dataclass
class MinimalContextDetectionConfig:
    clutch_time: Dict = None
    garbage_time: Dict = None
    fastbreak: Dict = None
    timeout_detection: Dict = None

    def __post_init__(self):
        if self.clutch_time is None:
            self.clutch_time = {
                "enabled": False,
                "time_remaining_seconds": 300.0,
                "score_margin": 5,
            }
        if self.garbage_time is None:
            self.garbage_time = {"enabled": False}
        if self.fastbreak is None:
            self.fastbreak = {"enabled": False, "max_duration_seconds": 8.0}
        if self.timeout_detection is None:
            self.timeout_detection = {"enabled": False}

    @property
    def fastbreak_max_duration(self) -> float:
        return self.fastbreak.get("max_duration_seconds", 8.0)

    @property
    def clutch_time_threshold(self) -> float:
        return self.clutch_time.get("time_remaining_seconds", 300.0)

    @property
    def clutch_score_margin(self) -> int:
        return self.clutch_time.get("score_margin", 5)

    @property
    def clutch_enabled(self) -> bool:
        return self.clutch_time.get("enabled", False)

    @property
    def fastbreak_enabled(self) -> bool:
        return self.fastbreak.get("enabled", False)


@dataclass
class MinimalConfig:
    possession_detection: MinimalPossessionDetectionConfig = None
    validation: MinimalValidationConfig = None
    context_detection: MinimalContextDetectionConfig = None

    def __post_init__(self):
        if self.possession_detection is None:
            self.possession_detection = MinimalPossessionDetectionConfig()
        if self.validation is None:
            self.validation = MinimalValidationConfig()
        if self.context_detection is None:
            self.context_detection = MinimalContextDetectionConfig()


# Database config
db_config = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "database": os.environ.get("POSTGRES_DB", "nba_simulator"),
    "user": os.environ.get("POSTGRES_USER", "ryanranft"),
    "password": os.environ.get("POSTGRES_PASSWORD", ""),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}


def get_events_for_game(conn, game_id):
    """Fetch events for a game, ordered by temporal sequence."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            event_id, game_id, team_id, quarter as period,
            game_clock_seconds, event_data, event_type,
            player_id, wall_clock_utc
        FROM temporal_events
        WHERE game_id = %s
        ORDER BY quarter, game_clock_seconds DESC, event_id
    """,
        (game_id,),
    )

    columns = [
        "event_id",
        "game_id",
        "team_id",
        "period",
        "game_clock_seconds",
        "event_data",
        "event_type",
        "player_id",
        "wall_clock_utc",
    ]

    events = []
    for row in cur.fetchall():
        event = dict(zip(columns, row))

        # Convert game_clock_seconds to clock_minutes and clock_seconds
        total_seconds = event["game_clock_seconds"] or 0
        event["clock_minutes"] = total_seconds // 60
        event["clock_seconds"] = total_seconds % 60
        event["game_date"] = event.get("wall_clock_utc")
        # Add dummy season (not critical for possession detection)
        event["season"] = "1999-00"  # dummy value

        events.append(event)

    cur.close()
    return events


def test_games(game_ids):
    """Test possession detection on multiple games."""
    conn = psycopg2.connect(**db_config)
    config = MinimalConfig()
    detector = PossessionDetector(config)

    results = []

    print("=" * 80)
    print("PHASE 2 FIX VALIDATION - Testing on 10 Games")
    print("=" * 80)
    print()

    for i, game_id in enumerate(game_ids, 1):
        events = get_events_for_game(conn, game_id)

        if not events:
            print(f"❌ Game {game_id}: No events found")
            continue

        possessions = detector.detect_possessions(events)

        # Count possessions by team
        team_counts = {}
        total_duration = 0

        for poss in possessions:
            team = poss.offensive_team_id
            team_counts[team] = team_counts.get(team, 0) + 1
            total_duration += poss.duration_seconds

        total_poss = len(possessions)
        avg_duration = total_duration / total_poss if total_poss > 0 else 0

        # Calculate team balance (should be <2.0)
        if len(team_counts) == 2:
            counts = list(team_counts.values())
            imbalance = abs(counts[0] - counts[1])
        else:
            imbalance = 999  # Error case

        # Determine status
        poss_ok = 195 <= total_poss <= 205
        balance_ok = imbalance <= 2.0
        duration_ok = 8.0 <= avg_duration <= 14.0

        status = "✅ PASS" if (poss_ok and balance_ok) else "⚠️  REVIEW"

        results.append(
            {
                "game_id": game_id,
                "possessions": total_poss,
                "imbalance": imbalance,
                "avg_duration": avg_duration,
                "pass": poss_ok and balance_ok,
            }
        )

        print(f"{status} Game {i}: {game_id}")
        print(
            f"  Possessions: {total_poss:3d} {'✅' if poss_ok else '❌'} (target: 195-205)"
        )
        print(
            f"  Team Balance: {imbalance:3d} {'✅' if balance_ok else '❌'} (target: ≤2)"
        )
        print(
            f"  Avg Duration: {avg_duration:5.1f}s {'✅' if duration_ok else '⚠️'} (target: 8-14s)"
        )
        print(f"  Team Counts: {team_counts}")
        print()

    conn.close()

    # Summary statistics
    if results:
        avg_poss = statistics.mean(r["possessions"] for r in results)
        avg_imbalance = statistics.mean(r["imbalance"] for r in results)
        avg_dur = statistics.mean(r["avg_duration"] for r in results)
        pass_rate = sum(1 for r in results if r["pass"]) / len(results) * 100

        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Average Possessions: {avg_poss:.1f} (target: 200)")
        print(f"Average Team Imbalance: {avg_imbalance:.1f} (target: <2.0)")
        print(f"Average Duration: {avg_dur:.1f}s (target: 8-14s)")
        print(
            f"Pass Rate: {pass_rate:.0f}% ({sum(1 for r in results if r['pass'])}/{len(results)})"
        )
        print()

        # Detection rate
        detection_rate = (avg_poss / 200) * 100
        print(f"Detection Rate: {detection_rate:.1f}% (was 85%, target 95%+)")

        if detection_rate >= 95:
            print()
            print("🎉 SUCCESS! Detection rate meets or exceeds 95% target!")
        elif detection_rate >= 90:
            print()
            print("🟡 CLOSE! Detection rate is 90%+, close to 95% target")
        else:
            print()
            print("⚠️  NEEDS WORK: Detection rate still below 90%")

        print("=" * 80)


if __name__ == "__main__":
    # Get 10 most recent games from database
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT game_id
        FROM temporal_events
        ORDER BY game_id DESC
        LIMIT 10
    """
    )
    game_ids = [gid for (gid,) in cur.fetchall()]
    cur.close()
    conn.close()

    print(f"Testing on games: {game_ids[:3]}... (10 total)")
    print()

    test_games(game_ids)
