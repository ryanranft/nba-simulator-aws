#!/usr/bin/env python3
"""
Test script for Phase 2 possession detection fixes on 10 games.

Tests both Phase 1 and Phase 2 fixes together:
- Phase 1: Team balance (target: ≤2 diff)
- Phase 2: Detection rate (target: 195-205 poss/game = 95%+)
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
            game_clock_seconds % 60 as clock_seconds,
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
        return {
            "total": 0,
            "teams": {},
            "balance": 0,
            "avg_duration": 0.0,
            "duration_outliers": 0,
        }

    # Count by team
    team_counts = {}
    total_duration = 0.0
    outliers = 0

    for poss in possessions:
        team_id = poss.offensive_team_id
        team_counts[team_id] = team_counts.get(team_id, 0) + 1
        total_duration += poss.duration_seconds

        # Count outliers (<1s or >35s)
        if poss.duration_seconds < 1.0 or poss.duration_seconds > 35.0:
            outliers += 1

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
        "duration_outliers": outliers,
    }


def test_game(detector: PossessionDetector, game_id: str) -> Dict:
    """Test possession detection on a single game."""
    print(f"\nGame {game_id}:", end=" ")

    # Load events
    events = load_game_events(game_id)

    # Detect possessions
    possessions = detector.detect_possessions(events)

    # Analyze
    stats = analyze_possessions(possessions)

    # Print concise results
    teams = list(stats["teams"].items())
    if len(teams) >= 2:
        team1, count1 = teams[0]
        team2, count2 = teams[1]
        balance_emoji = (
            "✅" if stats["balance"] <= 2 else ("⚠️" if stats["balance"] <= 5 else "❌")
        )
        detection_emoji = (
            "✅"
            if 190 <= stats["total"] <= 210
            else ("⚠️" if 180 <= stats["total"] <= 220 else "❌")
        )

        print(
            f"{stats['total']} poss {detection_emoji}, balance={stats['balance']} {balance_emoji}, "
            f"dur={stats['avg_duration']:.1f}s, outliers={stats['duration_outliers']}"
        )

    return stats


def main():
    """Run tests on 10 sample games."""
    print("=" * 70)
    print("PHASE 2 TEST: 10 Games")
    print("=" * 70)
    print("\nPhase 1 fixes: Team balance (target: ≤2 diff)")
    print("Phase 2 fixes: Detection rate (target: 195-205 poss/game)")
    print("              Duration quality (target: <5% outliers)")

    # Initialize detector
    cfg = PossessionConfig.from_yaml("config/possession_extraction_local.yaml")
    detector = PossessionDetector(cfg)

    # Test 10 diverse games from different parts of the season
    test_games = [
        "11300002",  # Early season
        "11300004",
        "11300005",
        "11300006",
        "11300007",
        "11300010",  # Mid season
        "11300020",
        "11300030",
        "11300040",
        "11300050",  # Later season
    ]

    results = []
    for game_id in test_games:
        try:
            stats = test_game(detector, game_id)
            results.append((game_id, stats))
        except Exception as e:
            print(f"❌ ERROR: {e}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    if not results:
        print("❌ No successful tests")
        return

    total_poss = sum(r[1]["total"] for r in results)
    avg_poss = total_poss / len(results)
    avg_balance = sum(r[1]["balance"] for r in results) / len(results)
    avg_duration = sum(r[1]["avg_duration"] for r in results) / len(results)
    total_outliers = sum(r[1]["duration_outliers"] for r in results)
    outlier_pct = (total_outliers / total_poss * 100) if total_poss > 0 else 0

    print(f"\nAverage across {len(results)} games:")
    print(f"  Possessions/game: {avg_poss:.1f}")
    print(f"  Detection rate: {avg_poss/200*100:.1f}% (target: 95%+)")
    print(f"  Team balance avg: {avg_balance:.1f} (target: ≤2)")
    print(f"  Avg duration: {avg_duration:.1f}s (target: 10-12s)")
    print(f"  Duration outliers: {outlier_pct:.1f}% (target: <5%)")

    # Check pass/fail
    balance_pass = sum(1 for _, s in results if s["balance"] <= 2)
    balance_warn = sum(1 for _, s in results if 2 < s["balance"] <= 5)
    balance_fail = sum(1 for _, s in results if s["balance"] > 5)

    detection_excellent = sum(1 for _, s in results if 190 <= s["total"] <= 210)
    detection_good = sum(1 for _, s in results if 180 <= s["total"] <= 220)
    detection_poor = len(results) - detection_good

    print(f"\nTeam balance results:")
    print(f"  ✅ ≤2 diff: {balance_pass}/{len(results)} games")
    print(f"  ⚠️  3-5 diff: {balance_warn}/{len(results)} games")
    print(f"  ❌ >5 diff: {balance_fail}/{len(results)} games")

    print(f"\nDetection rate results:")
    print(f"  ✅ 190-210 poss: {detection_excellent}/{len(results)} games")
    print(f"  ⚠️  180-220 poss: {detection_good}/{len(results)} games")
    print(f"  ❌ Outside range: {detection_poor}/{len(results)} games")

    # Overall verdict
    print(f"\n{'='*70}")
    if avg_balance <= 2 and avg_poss >= 190 and outlier_pct < 5:
        print("✅ PHASE 2 COMPLETE: All targets met!")
        print("   Ready for Phase 3 (comprehensive testing)")
    elif avg_balance <= 3 and avg_poss >= 180 and outlier_pct < 10:
        print("⚠️  PHASE 2: Partial success - close to targets")
        print("   May proceed or continue debugging")
    else:
        print("❌ PHASE 2: Need more work")
        print("   Additional debugging required")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
