#!/usr/bin/env python3
"""
Basketball Reference Play-by-Play Discovery Script

Discovers the earliest season with play-by-play data on Basketball Reference
by testing sample games across different years.

Purpose:
- Find when Basketball Reference PBP data begins
- Determine if they have PBP earlier than ESPN (1993) or NBA API (1996)
- Estimate total games with PBP for backfill planning

Method:
1. Start from 2024 (known to have PBP)
2. Work backwards year by year
3. Test 10 random games per season
4. Check if PBP table exists
5. Count PBP events if found
6. Record first season with NO PBP in any tested games

Output:
- Year-by-year PBP availability report
- Earliest year with PBP
- Estimated PBP coverage
- Recommendations for backfill scraper

Runtime: ~30 minutes (testing ~300 games across 30 years @ 12s/game)

Usage:
    python scripts/etl/basketball_reference_pbp_discovery.py
    python scripts/etl/basketball_reference_pbp_discovery.py --start-year 2024 --end-year 1990
    python scripts/etl/basketball_reference_pbp_discovery.py --games-per-year 5
    python scripts/etl/basketball_reference_pbp_discovery.py --verbose

Version: 1.0
Created: October 18, 2025
"""

import argparse
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "https://www.basketball-reference.com"
RATE_LIMIT = 12.0  # 12 seconds between requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PBPDiscovery:
    """Discover Basketball Reference play-by-play data coverage"""

    def __init__(self, games_per_year=10, verbose=False):
        self.games_per_year = games_per_year
        self.verbose = verbose
        self.last_request_time = 0

        # Results
        self.results = {}
        self.earliest_pbp_year = None
        self.total_games_tested = 0
        self.total_pbp_found = 0

    def rate_limit_wait(self):
        """Enforce 12-second rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT:
            sleep_time = RATE_LIMIT - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_sample_games_for_season(self, season: int, count: int = 10) -> List[str]:
        """Get sample game IDs for a season"""
        # This is a simplified approach - we'll generate sample game IDs
        # based on typical season dates and team codes

        # Common NBA team codes (mix of current and historical)
        teams = ['BOS', 'LAL', 'NYK', 'CHI', 'MIA', 'GSW', 'SAS', 'DEN',
                 'PHI', 'DAL', 'MIL', 'ATL', 'TOR', 'UTA', 'PHO', 'CLE']

        # NBA season typically runs October-April
        # Generate dates across the season
        sample_games = []

        # Try different months
        months = [10, 11, 12, 1, 2, 3, 4]  # Oct-April
        for month in months:
            if month >= 10:  # Oct, Nov, Dec (first half of season)
                year = season - 1
            else:  # Jan-Apr (second half)
                year = season

            # Try a few days in each month
            days = [5, 15, 25] if month != 4 else [5, 10, 15]  # Fewer games in April

            for day in days:
                # Pick random home team
                home_team = random.choice(teams)

                # Build game ID: YYYYMMDD0{HOME_TEAM}
                date_code = f"{year}{month:02d}{day:02d}"
                game_id = f"{date_code}0{home_team}"

                sample_games.append(game_id)

                if len(sample_games) >= count:
                    return sample_games[:count]

        return sample_games[:count]

    def check_pbp_for_game(self, game_id: str) -> Tuple[bool, int]:
        """
        Check if a game has play-by-play data

        Returns:
            (has_pbp, event_count) - True if PBP table exists, count of events
        """
        url = f"{BASE_URL}/boxscores/{game_id}.html"

        try:
            self.rate_limit_wait()

            response = requests.get(url, headers=HEADERS, timeout=30)

            # Game doesn't exist
            if response.status_code == 404:
                logger.debug(f"Game {game_id} not found (404)")
                return (False, 0)

            # Rate limited
            if response.status_code == 429:
                logger.warning(f"Rate limited on {game_id}")
                return (False, 0)

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for PBP table
            pbp_table = soup.find('table', {'id': 'pbp'})

            if not pbp_table:
                logger.debug(f"Game {game_id}: No PBP table found")
                return (False, 0)

            # Count PBP events
            tbody = pbp_table.find('tbody')
            if not tbody:
                return (True, 0)  # Table exists but no events

            rows = tbody.find_all('tr')

            # Filter out header rows
            event_rows = [r for r in rows if not (r.get('class') and 'thead' in r.get('class'))]

            event_count = len(event_rows)

            logger.debug(f"Game {game_id}: Found {event_count} PBP events")
            return (True, event_count)

        except Exception as e:
            logger.error(f"Error checking {game_id}: {e}")
            return (False, 0)

    def test_season(self, season: int) -> Dict:
        """Test a season for PBP availability"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing {season-1}-{str(season)[-2:]} season...")
        logger.info(f"{'='*70}")

        # Get sample games
        sample_games = self.get_sample_games_for_season(season, self.games_per_year)

        logger.info(f"Testing {len(sample_games)} sample games...")

        results = {
            'season': season,
            'games_tested': 0,
            'games_with_pbp': 0,
            'total_pbp_events': 0,
            'sample_game_ids': [],
            'pbp_game_ids': []
        }

        for game_id in sample_games:
            self.total_games_tested += 1
            results['games_tested'] += 1

            has_pbp, event_count = self.check_pbp_for_game(game_id)

            results['sample_game_ids'].append(game_id)

            if has_pbp:
                results['games_with_pbp'] += 1
                results['total_pbp_events'] += event_count
                results['pbp_game_ids'].append(game_id)
                self.total_pbp_found += 1

                if self.verbose:
                    logger.info(f"  ✓ {game_id}: {event_count} PBP events")
            else:
                if self.verbose:
                    logger.debug(f"  ✗ {game_id}: No PBP")

        # Summary
        pbp_pct = (results['games_with_pbp'] / results['games_tested'] * 100) if results['games_tested'] > 0 else 0

        logger.info(f"\nResults:")
        logger.info(f"  Games tested:     {results['games_tested']}")
        logger.info(f"  Games with PBP:   {results['games_with_pbp']} ({pbp_pct:.1f}%)")
        logger.info(f"  Avg events/game:  {results['total_pbp_events'] / max(results['games_with_pbp'], 1):.0f}")

        if results['games_with_pbp'] > 0:
            logger.info(f"  ✅ PBP DATA FOUND for {season}")
            if not self.earliest_pbp_year or season < self.earliest_pbp_year:
                self.earliest_pbp_year = season
        else:
            logger.info(f"  ❌ NO PBP DATA for {season}")

        return results

    def run(self, start_year: int = 2024, end_year: int = 1990):
        """Run discovery across year range"""
        print("\n" + "="*70)
        print("BASKETBALL REFERENCE PLAY-BY-PLAY DISCOVERY")
        print("="*70)
        print(f"\nYears to test: {start_year} down to {end_year}")
        print(f"Games per year: {self.games_per_year}")
        print(f"Total tests: ~{(start_year - end_year + 1) * self.games_per_year}")
        print(f"Estimated time: ~{(start_year - end_year + 1) * self.games_per_year * RATE_LIMIT / 60:.1f} minutes")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Test each season
        for season in range(start_year, end_year - 1, -1):
            season_results = self.test_season(season)
            self.results[season] = season_results

            # Early termination if we find 3 consecutive years with no PBP
            if len(self.results) >= 3:
                last_3_seasons = sorted(self.results.keys(), reverse=True)[:3]
                last_3_had_pbp = [self.results[s]['games_with_pbp'] > 0 for s in last_3_seasons]

                if not any(last_3_had_pbp):
                    logger.info(f"\n⚠️  Found 3 consecutive years with no PBP. Stopping early.")
                    break

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate final discovery report"""
        print("\n" + "="*70)
        print("DISCOVERY REPORT")
        print("="*70)

        print(f"\nTesting Summary:")
        print(f"  Total games tested:  {self.total_games_tested}")
        print(f"  Games with PBP:      {self.total_pbp_found}")
        print(f"  Earliest PBP year:   {self.earliest_pbp_year if self.earliest_pbp_year else 'None found'}")

        print(f"\nYear-by-Year Results:")
        print(f"{'Year':<8} {'Tested':<10} {'With PBP':<12} {'% Coverage':<12} {'Status':<10}")
        print("-" * 70)

        for season in sorted(self.results.keys(), reverse=True):
            r = self.results[season]
            pct = (r['games_with_pbp'] / r['games_tested'] * 100) if r['games_tested'] > 0 else 0
            status = "✅ HAS PBP" if r['games_with_pbp'] > 0 else "❌ NO PBP"

            print(f"{season:<8} {r['games_tested']:<10} {r['games_with_pbp']:<12} {pct:>6.1f}%     {status:<10}")

        # Comparison with other sources
        print(f"\nComparison with Other Sources:")
        print(f"  ESPN API:          1993-2025")
        print(f"  NBA API:           1996-2025")
        print(f"  hoopR:             2002-2025")
        print(f"  Basketball Ref:    {self.earliest_pbp_year if self.earliest_pbp_year else 'Unknown'}-2025")

        if self.earliest_pbp_year:
            if self.earliest_pbp_year < 1993:
                print(f"\n🎉 Basketball Reference has PBP EARLIER than ESPN (1993)!")
                print(f"   This fills a {1993 - self.earliest_pbp_year}-year gap!")
            elif self.earliest_pbp_year < 1996:
                print(f"\n✅ Basketball Reference has PBP earlier than NBA API (1996)")
                print(f"   This fills a {1996 - self.earliest_pbp_year}-year gap!")
            elif self.earliest_pbp_year < 2002:
                print(f"\n✅ Basketball Reference has PBP earlier than hoopR (2002)")
                print(f"   This fills a {2002 - self.earliest_pbp_year}-year gap!")
            else:
                print(f"\n⚠️  Basketball Reference PBP starts around same time as other sources")
                print(f"   Useful for cross-validation but no new historical data")

        # Recommendations
        print(f"\nRecommendations:")
        if self.earliest_pbp_year:
            estimated_seasons = 2025 - self.earliest_pbp_year
            estimated_games = estimated_seasons * 1250  # Rough estimate
            estimated_days = (estimated_games * RATE_LIMIT) / 86400

            print(f"  1. Run historical PBP backfill starting from {self.earliest_pbp_year}")
            print(f"  2. Estimated backfill: ~{estimated_games:,} games over ~{estimated_days:.1f} days")
            print(f"  3. Use separate storage path: s3://.../basketball_reference/pbp/")
            print(f"  4. Cross-validate overlapping years with ESPN/NBA API")
        else:
            print(f"  ⚠️  No PBP data found in tested years")
            print(f"  Consider testing more recent years or different game samples")

        # Save detailed results
        report_file = f"basketball_reference_pbp_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"reports/{report_file}", 'w') as f:
            json.dump({
                'discovery_date': datetime.now().isoformat(),
                'earliest_pbp_year': self.earliest_pbp_year,
                'total_games_tested': self.total_games_tested,
                'total_pbp_found': self.total_pbp_found,
                'results_by_year': self.results
            }, f, indent=2)

        print(f"\n✓ Detailed report saved to: reports/{report_file}")
        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description="Discover Basketball Reference play-by-play data coverage"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2024,
        help="Year to start discovery (default: 2024)"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=1990,
        help="Year to end discovery (default: 1990)"
    )
    parser.add_argument(
        "--games-per-year",
        type=int,
        default=10,
        help="Number of games to test per year (default: 10)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output for each game"
    )

    args = parser.parse_args()

    # Create reports directory if it doesn't exist
    import os
    os.makedirs("reports", exist_ok=True)

    discovery = PBPDiscovery(
        games_per_year=args.games_per_year,
        verbose=args.verbose
    )

    discovery.run(
        start_year=args.start_year,
        end_year=args.end_year
    )


if __name__ == "__main__":
    main()
