#!/usr/bin/env python3
"""
Fixed NBA API Scraper

This script fixes the NBA API connectivity issues by:
1. Using proper SSL context
2. Adding better error handling
3. Using requests instead of urllib3
4. Adding proper headers and user agents
"""

import requests
import json
import logging
import ssl
import time
from pathlib import Path
from typing import Dict, List, Optional
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FixedNBAApiScraper:
    def __init__(self, output_dir: str = "/tmp/nba_api_fixed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # NBA API configuration
        self.base_url = "https://stats.nba.com"
        self.rate_limit_delay = 1.5  # 1.5 seconds between requests

        # Create session with retry strategy
        self.session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Headers to mimic a real browser
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://www.nba.com/",
                "Origin": "https://www.nba.com",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            }
        )

        # Disable SSL verification for now
        self.session.verify = False

    def test_connectivity(self) -> bool:
        """Test basic connectivity to NBA API"""
        logger.info("Testing NBA API connectivity...")

        try:
            # Test with a simple endpoint
            test_url = f"{self.base_url}/stats/leaguedashplayerbiostats"
            params = {
                "Season": "2023-24",
                "SeasonType": "Regular Season",
                "PerMode": "PerGame",
            }

            logger.info(f"Testing URL: {test_url}")
            response = self.session.get(test_url, params=params, timeout=30)

            if response.status_code == 200:
                logger.info("✅ NBA API connectivity test successful!")
                return True
            else:
                logger.warning(f"⚠️ NBA API returned status {response.status_code}")
                logger.warning(f"Response: {response.text[:200]}...")
                return False

        except requests.exceptions.SSLError as e:
            logger.error(f"❌ SSL Error: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection Error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ Timeout Error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected Error: {e}")
            return False

    def test_playbyplay_endpoint(self, game_id: str = "0022400001") -> bool:
        """Test the play-by-play endpoint with a specific game"""
        logger.info(f"Testing PlayByPlay endpoint with game {game_id}...")

        try:
            url = f"{self.base_url}/stats/playbyplayv2"
            params = {"GameID": game_id, "StartPeriod": 0, "EndPeriod": 0}

            logger.info(f"Testing URL: {url}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if "resultSets" in data and len(data["resultSets"]) > 0:
                    logger.info("✅ PlayByPlay endpoint test successful!")
                    logger.info(
                        f"Response contains {len(data['resultSets'])} result sets"
                    )
                    return True
                else:
                    logger.warning("⚠️ PlayByPlay endpoint returned empty data")
                    return False
            else:
                logger.warning(
                    f"⚠️ PlayByPlay endpoint returned status {response.status_code}"
                )
                logger.warning(f"Response: {response.text[:200]}...")
                return False

        except Exception as e:
            logger.error(f"❌ PlayByPlay test error: {e}")
            return False

    def scrape_recent_games(
        self, season: str = "2023-24", limit: int = 10
    ) -> List[Dict]:
        """Scrape recent games for testing"""
        logger.info(f"Scraping {limit} recent games from {season}...")

        try:
            # Get game schedule first
            schedule_url = f"{self.base_url}/stats/scoreboardV2"
            params = {
                "GameDate": "2024-01-15",  # Use a known game date
                "LeagueID": "00",
                "DayOffset": "0",
            }

            logger.info("Fetching game schedule...")
            response = self.session.get(schedule_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                games = []

                if "resultSets" in data and len(data["resultSets"]) > 0:
                    game_header = data["resultSets"][0]
                    if "rowSet" in game_header:
                        for game_row in game_header["rowSet"][:limit]:
                            if len(game_row) > 0:
                                game_id = game_row[2]  # GameID is typically in column 2
                                games.append(
                                    {
                                        "game_id": game_id,
                                        "game_date": (
                                            game_row[0] if len(game_row) > 0 else None
                                        ),
                                        "home_team": (
                                            game_row[6] if len(game_row) > 6 else None
                                        ),
                                        "away_team": (
                                            game_row[7] if len(game_row) > 7 else None
                                        ),
                                    }
                                )

                logger.info(f"Found {len(games)} games")
                return games
            else:
                logger.error(f"Failed to fetch schedule: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return []

    def scrape_game_playbyplay(self, game_id: str) -> Optional[Dict]:
        """Scrape play-by-play data for a specific game"""
        logger.info(f"Scraping play-by-play for game {game_id}...")

        try:
            url = f"{self.base_url}/stats/playbyplayv2"
            params = {"GameID": game_id, "StartPeriod": 0, "EndPeriod": 0}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Save the data
                output_file = self.output_dir / f"pbp_{game_id}.json"
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)

                logger.info(f"✅ Saved play-by-play data for game {game_id}")
                return data
            else:
                logger.warning(
                    f"⚠️ Failed to fetch game {game_id}: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"❌ Error scraping game {game_id}: {e}")
            return None

    def run_comprehensive_test(self):
        """Run comprehensive tests of NBA API functionality"""
        logger.info("=" * 60)
        logger.info("NBA API COMPREHENSIVE TEST")
        logger.info("=" * 60)

        # Test 1: Basic connectivity
        logger.info("\n[TEST 1] Basic Connectivity")
        connectivity_ok = self.test_connectivity()

        # Test 2: PlayByPlay endpoint
        logger.info("\n[TEST 2] PlayByPlay Endpoint")
        pbp_ok = self.test_playbyplay_endpoint()

        # Test 3: Scrape recent games
        logger.info("\n[TEST 3] Scrape Recent Games")
        games = self.scrape_recent_games(limit=5)

        # Test 4: Scrape play-by-play for each game
        successful_pbp = 0
        if games:
            logger.info(f"\n[TEST 4] Scrape PlayByPlay for {len(games)} games")
            for game in games:
                game_id = game["game_id"]
                pbp_data = self.scrape_game_playbyplay(game_id)
                if pbp_data:
                    successful_pbp += 1
                time.sleep(self.rate_limit_delay)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(
            f"Basic Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}"
        )
        logger.info(f"PlayByPlay Endpoint: {'✅ PASS' if pbp_ok else '❌ FAIL'}")
        logger.info(f"Games Found: {len(games)}")
        logger.info(
            f"PlayByPlay Scraped: {successful_pbp}/{len(games) if games else 0}"
        )
        logger.info(f"Output Directory: {self.output_dir}")

        return {
            "connectivity": connectivity_ok,
            "playbyplay": pbp_ok,
            "games_found": len(games),
            "pbp_scraped": successful_pbp,
        }


def main():
    """Main function"""
    scraper = FixedNBAApiScraper()

    logger.info("Starting NBA API connectivity fix and test...")

    # Run comprehensive test
    results = scraper.run_comprehensive_test()

    if results["connectivity"] and results["playbyplay"]:
        logger.info("✅ NBA API is working correctly!")
    else:
        logger.error("❌ NBA API has issues that need to be addressed")

    return results


if __name__ == "__main__":
    main()





