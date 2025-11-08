#!/usr/bin/env python3
"""
Simple test script for Phase 1 possession detection bug fixes.
Uses direct psycopg2 connection to avoid config issues.
"""

import sys
import os
import psycopg2
from typing import Dict, List

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nba_simulator.etl.extractors.possession.detector import PossessionDetector
from nba_simulator.etl.extractors.possession.config import PossessionConfig


def load_game_events(game_id: str) -> List[Dict]:
    """Load events for a game from temporal_events table."""
    # Connect directly to local PostgreSQL
    conn = psycopg2.connect(
        host="localhost", port=5432, database="nba_simulator", user="ryanranft"
    )

    query = """
        SELECT
            event_id,
            game_id,
            team_id,
            player_id,
            quarter as period,
            FLOOR(game_clock_seconds / 60) as clock_minutes,
            game_clock_seconds %% 60 as clock_seconds,
            event_type,
            event_data,
            wall_clock_utc,
            data_source,
            precision_level
        FROM temporal_events
        WHERE game_id = %s
        ORDER BY quarter, game_clock_seconds DESC
    """

    cursor = conn.cursor()
    cursor.execute(query, (game_id,))
    results = cursor.fetchall()

    events = []
    for row in results:
        event = {
            "event_id": row[0],
            "game_id": row[1],
            "team_id": row[2],
            "player_id": row[3],
            "period": row[4],
            "clock_minutes": row[5],
            "clock_seconds": row[6],
            "event_type": row[7],
            "event_data": row[8] or {},
            "wall_clock_utc": row[9],
            "data_source": row[10],
            "precision_level": row[11],
        }
        events.append(event)

    cursor.close()
    conn.close()

    return events


def analyze_possessions(possessions: List) -> Dict:
    """Analyze possession statistics."""
    if not possessions:
        return {"total": 0, "teams": {}, "balance": 0, "avg_duration": 0.0}

    # Count by team
    team_counts = {}
    total_duration = 0.0

    for poss in possessions:
        team_id = poss.offensive_team_id
        team_counts[team_id] = team_counts.get(team_id, 0) + 1
        total_duration += poss.duration_seconds

    # Calculate balance
    counts = list(team_counts.values())
    balance = max(counts) - min(counts) if len(counts) >= 2 else 0

    # Average duration
    avg_duration = total_duration / len(possessions) if possessions else 0.0

    return {
        "total": len(possessions),
        "teams": team_counts,
        "balance": balance,
        "avg_duration": avg_duration,
    }


def test_game(detector: PossessionDetector, game_id: str) -> Dict:
    """Test possession detection on a single game."""
    print(f"\n{'='*60}")
    print(f"Testing game: {game_id}")
    print(f"{'='*60}")

    # Load events
    events = load_game_events(game_id)
    print(f"Loaded {len(events)} events")

    # Count rebounds with NULL team_id before
    null_rebounds = sum(
        1 for e in events if e["event_type"] == "rebound" and e["team_id"] is None
    )
    print(f"Rebounds with NULL team_id: {null_rebounds}")

    # Detect possessions
    possessions = detector.detect_possessions(events)

    # Analyze
    stats = analyze_possessions(possessions)

    print(f"\nResults:")
    print(f"  Total possessions: {stats['total']}")
    print(f"  Detection rate: {stats['total']/200*100:.1f}% (expected ~200)")

    teams = list(stats["teams"].items())
    if len(teams) >= 2:
        team1, count1 = teams[0]
        team2, count2 = teams[1]
        print(f"  Team {team1}: {count1} possessions")
        print(f"  Team {team2}: {count2} possessions")
        print(f"  Balance difference: {stats['balance']} (target: ≤2)")

        if stats["balance"] <= 2:
            print(f"  ✅ PASS: Balance ≤2")
        elif stats["balance"] <= 5:
            print(f"  ⚠️  WARN: Balance {stats['balance']} (acceptable but not ideal)")
        else:
            print(f"  ❌ FAIL: Balance {stats['balance']} > 5")

    print(f"  Average duration: {stats['avg_duration']:.1f}s (target: 10-12s)")

    return stats


def main():
    """Run tests on 5 sample games."""
    print("=" * 60)
    print("PHASE 1 BUG FIXES TEST (Simple)")
    print("=" * 60)
    print("\nBugs fixed:")
    print("  1. NULL team_id rebounds handling")
    print("  2. Made shot duplicate event removal")
    print("  3. Non-existent 'steal' event handling removal")
    print("\nExpected improvements:")
    print("  - Team balance: 3-12 → ≤2 possession difference")
    print("  - Detection rate: 90% → 95%+")
    print("  - NULL rebounds: Handled gracefully")

    # Initialize detector
    cfg = PossessionConfig.from_yaml("config/possession_extraction_local.yaml")
    detector = PossessionDetector(cfg)

    # Test games (same as previous session)
    test_games = [
        "11300002",  # Game 1: CHI @ IND
        "11300004",  # Game 2
        "11300005",  # Game 3
        "11300006",  # Game 4
        "11300007",  # Game 5
    ]

    results = []
    for game_id in test_games:
        try:
            stats = test_game(detector, game_id)
            results.append((game_id, stats))
        except Exception as e:
            print(f"❌ ERROR testing {game_id}: {e}")
            import traceback

            traceback.print_exc()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if not results:
        print("❌ No successful tests")
        return

    total_poss = sum(r[1]["total"] for r in results)
    avg_poss = total_poss / len(results)
    avg_balance = sum(r[1]["balance"] for r in results) / len(results)
    avg_duration = sum(r[1]["avg_duration"] for r in results) / len(results)

    print(f"\nAverage across {len(results)} games:")
    print(f"  Possessions/game: {avg_poss:.1f}")
    print(f"  Detection rate: {avg_poss/200*100:.1f}% (target: 95%+)")
    print(f"  Team balance avg: {avg_balance:.1f} (target: ≤2)")
    print(f"  Avg duration: {avg_duration:.1f}s (target: 10-12s)")

    # Check pass/fail
    balance_pass = sum(1 for _, s in results if s["balance"] <= 2)
    balance_warn = sum(1 for _, s in results if 2 < s["balance"] <= 5)
    balance_fail = sum(1 for _, s in results if s["balance"] > 5)

    print(f"\nTeam balance results:")
    print(f"  ✅ ≤2 diff: {balance_pass}/{len(results)} games")
    print(f"  ⚠️  3-5 diff: {balance_warn}/{len(results)} games")
    print(f"  ❌ >5 diff: {balance_fail}/{len(results)} games")

    # Overall verdict
    print(f"\n{'='*60}")
    if avg_balance <= 2 and avg_poss >= 190:
        print("✅ PHASE 1 FIXES: SUCCESS")
        print("   Ready to proceed to Phase 2")
    elif avg_balance <= 5 and avg_poss >= 180:
        print("⚠️  PHASE 1 FIXES: PARTIAL SUCCESS")
        print("   Some improvement but not at target yet")
    else:
        print("❌ PHASE 1 FIXES: NEED MORE WORK")
        print("   Team balance or detection rate still below target")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
