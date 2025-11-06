#!/usr/bin/env python3
"""
Basketball Reference Play-by-Play Discovery Script

Migrated to AsyncBaseScraper framework

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

Features:
- AsyncBaseScraper framework for standardized infrastructure
- Automatic rate limiting and retry logic
- Async HTTP requests with asyncio.to_thread()
- BeautifulSoup parsing wrapped in async
- Configuration-driven behavior
- Telemetry and monitoring

Usage:
    python scripts/etl/basketball_reference_pbp_discovery.py
    python scripts/etl/basketball_reference_pbp_discovery.py --start-year 2024 --end-year 1990
    python scripts/etl/basketball_reference_pbp_discovery.py --games-per-year 5
    python scripts/etl/basketball_reference_pbp_discovery.py --verbose

Version: 2.0 (Migrated to AsyncBaseScraper)
Created: October 18, 2025
Migrated: October 22, 2025 (Session 5)
"""

import asyncio
import argparse
import requests
from bs4 import BeautifulSoup
import random
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from nba_simulator.etl.config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PBPDiscovery(AsyncBaseScraper):
    """
    Discover Basketball Reference play-by-play data coverage

    Migrated to AsyncBaseScraper framework for:
    - Automatic rate limiting and retry logic
    - Telemetry and monitoring
    - Configuration-driven behavior

    Note: Research tool - no database or S3 operations
    """

    def __init__(self, config, games_per_year=10, verbose=False):
        super().__init__(config)

        self.games_per_year = games_per_year
        self.verbose = verbose

        # Results
        self.results = {}
        self.earliest_pbp_year = None
        self.total_games_tested = 0
        self.total_pbp_found = 0

    async def scrape(self) -> None:
        """Main scraping method (required by AsyncBaseScraper)"""
        # Business logic is in run() method called from main()
        pass

    def get_sample_games_for_season(self, season: int, count: int = 10) -> List[str]:
        """Get sample game IDs for a season"""
        # This is a simplified approach - we'll generate sample game IDs
        # based on typical season dates and team codes

        # Common NBA team codes (mix of current and historical)
        teams = [
            "BOS",
            "LAL",
            "NYK",
            "CHI",
            "MIA",
            "GSW",
            "SAS",
            "DEN",
            "PHI",
            "DAL",
            "MIL",
            "ATL",
            "TOR",
            "UTA",
            "PHO",
            "CLE",
        ]

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
                home_team = random.choice(
                    teams
                )  # nosec B311 - random.choice() used for sampling game IDs, not cryptographic purposes

                # Build game ID: YYYYMMDD0{HOME_TEAM}
                date_code = f"{year}{month:02d}{day:02d}"
                game_id = f"{date_code}0{home_team}"

                sample_games.append(game_id)

                if len(sample_games) >= count:
                    return sample_games[:count]

        return sample_games[:count]

    async def check_pbp_for_game(self, game_id: str) -> Tuple[bool, int]:
        """
        Check if a game has play-by-play data (async)

        Returns:
            (has_pbp, event_count) - True if PBP table exists, count of events
        """
        url = f"{self.config.base_url}/boxscores/{game_id}.html"

        try:
            # Use rate limiter from base class
            await self.rate_limiter.acquire()

            # Wrap synchronous requests.get in asyncio.to_thread
            response = await asyncio.to_thread(
                requests.get,
                url,
                headers={"User-Agent": self.config.user_agent},
                timeout=self.config.timeout,
            )

            # Game doesn't exist
            if response.status_code == 404:
                self.logger.debug(f"Game {game_id} not found (404)")
                return (False, 0)

            # Rate limited
            if response.status_code == 429:
                self.logger.warning(f"Rate limited on {game_id}")
                return (False, 0)

            response.raise_for_status()

            # Parse HTML (wrapped in async)
            has_pbp, event_count = await self._parse_pbp_check(response.text, game_id)
            return (has_pbp, event_count)

        except Exception as e:
            self.logger.error(f"Error checking {game_id}: {e}")
            return (False, 0)

    async def _parse_pbp_check(self, html: str, game_id: str) -> Tuple[bool, int]:
        """Parse HTML to check for PBP data (async wrapper)"""
        # Wrap synchronous BeautifulSoup parsing in asyncio.to_thread
        return await asyncio.to_thread(self._parse_pbp_check_sync, html, game_id)

    def _parse_pbp_check_sync(self, html: str, game_id: str) -> Tuple[bool, int]:
        """Synchronous version of PBP check parsing"""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Look for PBP table
            pbp_table = soup.find("table", {"id": "pbp"})

            if not pbp_table:
                self.logger.debug(f"Game {game_id}: No PBP table found")
                return (False, 0)

            # Count PBP events
            tbody = pbp_table.find("tbody")
            if not tbody:
                return (True, 0)  # Table exists but no events

            rows = tbody.find_all("tr")

            # Filter out header rows
            event_rows = [
                r for r in rows if not (r.get("class") and "thead" in r.get("class"))
            ]

            event_count = len(event_rows)

            self.logger.debug(f"Game {game_id}: Found {event_count} PBP events")
            return (True, event_count)

        except Exception as e:
            self.logger.error(f"Error parsing {game_id}: {e}")
            return (False, 0)

    async def test_season(self, season: int) -> Dict:
        """Test a season for PBP availability (async)"""
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"Testing {season-1}-{str(season)[-2:]} season...")
        self.logger.info(f"{'='*70}")

        # Get sample games
        sample_games = self.get_sample_games_for_season(season, self.games_per_year)

        self.logger.info(f"Testing {len(sample_games)} sample games...")

        results = {
            "season": season,
            "games_tested": 0,
            "games_with_pbp": 0,
            "total_pbp_events": 0,
            "sample_game_ids": [],
            "pbp_game_ids": [],
        }

        for game_id in sample_games:
            self.total_games_tested += 1
            results["games_tested"] += 1

            # Async call
            has_pbp, event_count = await self.check_pbp_for_game(game_id)

            results["sample_game_ids"].append(game_id)

            if has_pbp:
                results["games_with_pbp"] += 1
                results["total_pbp_events"] += event_count
                results["pbp_game_ids"].append(game_id)
                self.total_pbp_found += 1

                if self.verbose:
                    self.logger.info(f"  ✓ {game_id}: {event_count} PBP events")
            else:
                if self.verbose:
                    self.logger.debug(f"  ✗ {game_id}: No PBP")

        # Summary
        pbp_pct = (
            (results["games_with_pbp"] / results["games_tested"] * 100)
            if results["games_tested"] > 0
            else 0
        )

        self.logger.info(f"\nResults:")
        self.logger.info(f"  Games tested:     {results['games_tested']}")
        self.logger.info(
            f"  Games with PBP:   {results['games_with_pbp']} ({pbp_pct:.1f}%)"
        )
        self.logger.info(
            f"  Avg events/game:  {results['total_pbp_events'] / max(results['games_with_pbp'], 1):.0f}"
        )

        if results["games_with_pbp"] > 0:
            self.logger.info(f"  ✅ PBP DATA FOUND for {season}")
            if not self.earliest_pbp_year or season < self.earliest_pbp_year:
                self.earliest_pbp_year = season
        else:
            self.logger.info(f"  ❌ NO PBP DATA for {season}")

        return results

    async def run(self, start_year: int = 2024, end_year: int = 1990):
        """Run discovery across year range (async)"""
        print("\n" + "=" * 70)
        print("BASKETBALL REFERENCE PLAY-BY-PLAY DISCOVERY (AsyncBaseScraper)")
        print("=" * 70)
        print(f"\nYears to test: {start_year} down to {end_year}")
        print(f"Games per year: {self.games_per_year}")
        print(f"Total tests: ~{(start_year - end_year + 1) * self.games_per_year}")
        print(
            f"Estimated time: ~{(start_year - end_year + 1) * self.games_per_year * 12.0 / 60:.1f} minutes"
        )
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Test each season
        for season in range(start_year, end_year - 1, -1):
            season_results = await self.test_season(season)
            self.results[season] = season_results

            # Early termination if we find 3 consecutive years with no PBP
            if len(self.results) >= 3:
                last_3_seasons = sorted(self.results.keys(), reverse=True)[:3]
                last_3_had_pbp = [
                    self.results[s]["games_with_pbp"] > 0 for s in last_3_seasons
                ]

                if not any(last_3_had_pbp):
                    self.logger.info(
                        f"\n⚠️  Found 3 consecutive years with no PBP. Stopping early."
                    )
                    break

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate final discovery report"""
        print("\n" + "=" * 70)
        print("DISCOVERY REPORT")
        print("=" * 70)

        print(f"\nTesting Summary:")
        print(f"  Total games tested:  {self.total_games_tested}")
        print(f"  Games with PBP:      {self.total_pbp_found}")
        print(
            f"  Earliest PBP year:   {self.earliest_pbp_year if self.earliest_pbp_year else 'None found'}"
        )

        print(f"\nYear-by-Year Results:")
        print(
            f"{'Year':<8} {'Tested':<10} {'With PBP':<12} {'% Coverage':<12} {'Status':<10}"
        )
        print("-" * 70)

        for season in sorted(self.results.keys(), reverse=True):
            r = self.results[season]
            pct = (
                (r["games_with_pbp"] / r["games_tested"] * 100)
                if r["games_tested"] > 0
                else 0
            )
            status = "✅ HAS PBP" if r["games_with_pbp"] > 0 else "❌ NO PBP"

            print(
                f"{season:<8} {r['games_tested']:<10} {r['games_with_pbp']:<12} {pct:>6.1f}%     {status:<10}"
            )

        # Comparison with other sources
        print(f"\nComparison with Other Sources:")
        print(f"  ESPN API:          1993-2025")
        print(f"  NBA API:           1996-2025")
        print(f"  hoopR:             2002-2025")
        print(
            f"  Basketball Ref:    {self.earliest_pbp_year if self.earliest_pbp_year else 'Unknown'}-2025"
        )

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
                print(
                    f"\n⚠️  Basketball Reference PBP starts around same time as other sources"
                )
                print(f"   Useful for cross-validation but no new historical data")

        # Recommendations
        print(f"\nRecommendations:")
        if self.earliest_pbp_year:
            estimated_seasons = 2025 - self.earliest_pbp_year
            estimated_games = estimated_seasons * 1250  # Rough estimate
            estimated_days = (estimated_games * RATE_LIMIT) / 86400

            print(
                f"  1. Run historical PBP backfill starting from {self.earliest_pbp_year}"
            )
            print(
                f"  2. Estimated backfill: ~{estimated_games:,} games over ~{estimated_days:.1f} days"
            )
            print(f"  3. Use separate storage path: s3://.../basketball_reference/pbp/")
            print(f"  4. Cross-validate overlapping years with ESPN/NBA API")
        else:
            print(f"  ⚠️  No PBP data found in tested years")
            print(f"  Consider testing more recent years or different game samples")

        # Save detailed results
        report_file = f"basketball_reference_pbp_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"reports/{report_file}", "w") as f:
            json.dump(
                {
                    "discovery_date": datetime.now().isoformat(),
                    "earliest_pbp_year": self.earliest_pbp_year,
                    "total_games_tested": self.total_games_tested,
                    "total_pbp_found": self.total_pbp_found,
                    "results_by_year": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n✓ Detailed report saved to: reports/{report_file}")
        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference PBP discovery scraper (AsyncBaseScraper)"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        help="Year to start discovery (defaults to config value: 2024)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        help="Year to end discovery (defaults to config value: 1990)",
    )
    parser.add_argument(
        "--games-per-year",
        type=int,
        help="Number of games to test per year (defaults to config value: 10)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output for each game"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default="config/scraper_config.yaml",
        help="Configuration file path",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config("basketball_reference_pbp_discovery")
        if not config:
            print("❌ Basketball Reference PBP discovery configuration not found")
            return 1

        print(f"✅ Loaded Basketball Reference PBP discovery configuration")
        print(f"   Base URL: {config.base_url}")
        print(
            f"   Rate limit: {config.rate_limit.requests_per_second} req/s (12s between requests)"
        )
        print(f"   Max concurrent: {config.max_concurrent}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    # Get configuration defaults
    start_year = args.start_year or config.custom_settings.get(
        "default_start_year", 2024
    )
    end_year = args.end_year or config.custom_settings.get("default_end_year", 1990)
    games_per_year = args.games_per_year or config.custom_settings.get(
        "default_games_per_year", 10
    )

    # Create reports directory if it doesn't exist
    import os

    os.makedirs("reports", exist_ok=True)

    discovery = PBPDiscovery(
        config=config, games_per_year=games_per_year, verbose=args.verbose
    )

    try:
        # Run discovery using async context manager
        async with discovery:
            await discovery.run(start_year=start_year, end_year=end_year)

        # Print final statistics from base class
        print("\n📊 Base Statistics:")
        print(f"   Requests: {discovery.stats.requests_made}")
        print(f"   Success rate: {discovery.stats.success_rate:.2%}")
        print(f"   Errors: {discovery.stats.errors}")
        print(f"   Elapsed time: {discovery.stats.elapsed_time:.2f}s")

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Discovery interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
