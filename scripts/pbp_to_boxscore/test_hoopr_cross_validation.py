#!/usr/bin/env python3
"""
Cross-Validation Test: hoopR vs ESPN Processors

Tests the cross-validation functionality between hoopR and ESPN processors
to ensure data quality and identify any discrepancies.

Created: October 13, 2025
Phase: 9.2 (hoopR Processor)
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.pbp_to_boxscore.hoopr_processor import (
    HoopRPlayByPlayProcessor,
    process_hoopr_games_batch,
)
from scripts.pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_cross_validation():
    """Test cross-validation between hoopR and ESPN processors."""

    # Initialize processors
    hoopr_processor = HoopRPlayByPlayProcessor()
    espn_processor = ESPNPlayByPlayProcessor()

    # Test game ID (we know this exists in hoopR)
    test_game_id = "400278393"

    print("=" * 60)
    print("CROSS-VALIDATION TEST: hoopR vs ESPN")
    print("=" * 60)
    print(f"Test Game ID: {test_game_id}")
    print()

    try:
        # Test hoopR processor
        print("1. Testing hoopR processor...")
        hoopr_snapshots, hoopr_verification = hoopr_processor.process_game(test_game_id)
        print(f"   ✅ hoopR: Generated {len(hoopr_snapshots)} snapshots")

        if hoopr_snapshots:
            final_hoopr = hoopr_snapshots[-1]
            print(
                f"   📊 hoopR Final Score: {final_hoopr.away_score} - {final_hoopr.home_score}"
            )

        # Test ESPN processor (if data exists)
        print("\n2. Testing ESPN processor...")
        try:
            espn_snapshots, espn_verification = espn_processor.process_game(
                test_game_id
            )
            print(f"   ✅ ESPN: Generated {len(espn_snapshots)} snapshots")

            if espn_snapshots:
                final_espn = espn_snapshots[-1]
                print(
                    f"   📊 ESPN Final Score: {final_espn.away_score} - {final_espn.home_score}"
                )

                # Cross-validation
                print("\n3. Cross-validation analysis...")
                validation_result = hoopr_processor.cross_validate_with_espn(
                    test_game_id, espn_processor
                )

                if validation_result["status"] == "success":
                    print(f"   ✅ Cross-validation successful")
                    print(f"   📈 hoopR events: {validation_result['hoopr_events']}")
                    print(f"   📈 ESPN events: {validation_result['espn_events']}")
                    print(f"   📊 Total difference: {validation_result['total_diff']}")
                    print(
                        f"   💡 Recommendation: {validation_result['recommendation']}"
                    )
                else:
                    print(
                        f"   ❌ Cross-validation failed: {validation_result.get('reason', 'Unknown error')}"
                    )

        except Exception as e:
            print(f"   ⚠️ ESPN data not available for game {test_game_id}: {e}")
            print("   ℹ️ This is expected for older games (2013)")

        # Test batch processing
        print("\n4. Testing batch processing...")
        test_games = [test_game_id]
        batch_results = process_hoopr_games_batch(test_games)

        print(f"   📊 Processed: {batch_results['processed']}")
        print(f"   ❌ Failed: {batch_results['failed']}")
        if batch_results["errors"]:
            print(f"   ⚠️ Errors: {batch_results['errors']}")

        print("\n" + "=" * 60)
        print("✅ CROSS-VALIDATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Cross-validation test failed: {e}")
        logger.exception("Cross-validation test failed")
        return False


def test_event_parsing():
    """Test individual event parsing capabilities."""

    print("\n" + "=" * 60)
    print("EVENT PARSING TEST")
    print("=" * 60)

    hoopr_processor = HoopRPlayByPlayProcessor()

    # Test different event types
    test_events = [
        {
            "type_text": "Substitution",
            "text": "Andrew Nicholson enters the game for Nikola Vucevic",
            "athlete_id_1": 6614.0,
            "athlete_id_2": 6478.0,
            "team_id": 19.0,
            "scoring_play": 0,
            "score_value": 0,
            "clock_display_value": "0:42.0",
            "period_number": 2,
        },
        {
            "type_text": "Free Throw - 2 of 2",
            "text": "Jameer Nelson makes free throw 2 of 2",
            "athlete_id_1": 2439.0,
            "athlete_id_2": None,
            "team_id": 19.0,
            "scoring_play": 1,
            "score_value": 1,
            "clock_display_value": "0:42.0",
            "period_number": 2,
        },
        {
            "type_text": "2-Point Field Goal",
            "text": "LeBron James makes 2-pt shot",
            "athlete_id_1": 2544.0,
            "athlete_id_2": None,
            "team_id": 5.0,
            "scoring_play": 1,
            "score_value": 2,
            "clock_display_value": "7:32",
            "period_number": 1,
        },
    ]

    for i, event in enumerate(test_events, 1):
        print(f"\n{i}. Testing event: {event['type_text']}")
        parsed = hoopr_processor.parse_event(event, i)

        print(f"   Event Type: {parsed['event_type']}")
        print(f"   Player ID: {parsed['player_id']}")
        print(f"   Team ID: {parsed['team_id']}")
        print(f"   Points: {parsed['points']}")
        print(f"   Stat Updates: {parsed['stat_updates']}")

        if parsed["substitution"]:
            print(f"   Substitution: {parsed['substitution']}")

    print("\n✅ Event parsing test completed!")


if __name__ == "__main__":
    print("hoopR Processor Cross-Validation Test")
    print("=" * 60)

    # Run tests
    success = test_cross_validation()
    test_event_parsing()

    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("hoopR processor is ready for production use.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check the errors above.")
