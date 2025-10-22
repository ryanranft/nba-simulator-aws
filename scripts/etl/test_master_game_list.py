#!/usr/bin/env python3
"""
Test Master Game List Builder

Tests the robust scraper across different eras to validate it finds
the correct number of games. Run this overnight when rate limits reset.

Usage:
    python scripts/etl/test_master_game_list.py
    python scripts/etl/test_master_game_list.py --verbose

Expected Results:
    1947 (BAA first season):  ~60 games (short season)
    1955 (Pre-shot-clock):    ~108 games (8 teams × 72 games / 2)
    1990 (Pre-expansion):     ~1,179 games
    2000 (Modern 30 teams):   ~1,264 games
    2010 (Modern full):       ~1,312 games
    2023 (Most recent):       ~1,320 games
"""

import sys
import time
from build_master_game_list_robust import MasterGameListBuilder

# Expected game counts (approximate, varies by lockouts/strikes)
EXPECTED_COUNTS = {
    1947: (60, 70),      # BAA first season: 60-70 games
    1955: (100, 120),    # Pre-shot-clock: 100-120 games
    1990: (1170, 1190),  # 27 teams: ~1,179 games
    2000: (1250, 1280),  # 29 teams: ~1,264 games
    2010: (1300, 1330),  # 30 teams: ~1,312 games
    2023: (1310, 1330),  # 30 teams + playoffs: ~1,320 games
}

def test_season(season, verbose=False):
    """Test scraping a single season"""
    print(f"\n{'='*70}")
    print(f"Testing {season} season...")
    print(f"{'='*70}")

    builder = MasterGameListBuilder(
        start_season=season,
        end_season=season,
        dry_run=True
    )

    try:
        # Scrape season
        games = builder.scrape_season_schedule(season)

        # Check count
        min_expected, max_expected = EXPECTED_COUNTS.get(season, (0, 999999))

        print(f"\nResults:")
        print(f"  Games found: {len(games)}")
        print(f"  Expected:    {min_expected}-{max_expected}")

        if min_expected <= len(games) <= max_expected:
            print(f"  ✅ PASS")
            result = "PASS"
        else:
            print(f"  ❌ FAIL (outside expected range)")
            result = "FAIL"

        if verbose and len(games) > 0:
            print(f"\nSample games:")
            for i, game in enumerate(games[:5]):
                print(f"  {i+1}. {game['game_date']} - {game['away_team']} @ {game['home_team']} ({game['game_id']})")

        return result, len(games)

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return "ERROR", 0

def main():
    verbose = "--verbose" in sys.argv

    print("\n" + "="*70)
    print("MASTER GAME LIST BUILDER - VALIDATION TEST")
    print("="*70)
    print("\nThis script tests the scraper across different eras.")
    print("Due to Basketball Reference rate limiting (12s/request),")
    print("this test will take ~2 minutes.")
    print("\nPress Ctrl+C to cancel within 5 seconds...")

    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        return

    results = {}

    # Test each season
    for season in sorted(EXPECTED_COUNTS.keys()):
        result, count = test_season(season, verbose=verbose)
        results[season] = (result, count)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for r, _ in results.values() if r == "PASS")
    failed = sum(1 for r, _ in results.values() if r == "FAIL")
    errors = sum(1 for r, _ in results.values() if r == "ERROR")

    for season in sorted(results.keys()):
        result, count = results[season]
        min_exp, max_exp = EXPECTED_COUNTS[season]
        status_icon = "✅" if result == "PASS" else "❌"
        print(f"{status_icon} {season}: {count:4d} games (expected {min_exp}-{max_exp})")

    print(f"\nResults: {passed} passed, {failed} failed, {errors} errors")

    if failed == 0 and errors == 0:
        print("\n🎉 All tests passed! Ready to run full scraper.")
    else:
        print("\n⚠️  Some tests failed. Review results above.")

if __name__ == "__main__":
    main()
