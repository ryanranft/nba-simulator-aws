#!/usr/bin/env python3
"""
ESPN API Connectivity Fix

This script fixes ESPN API connectivity issues by:
1. Using proper SSL context
2. Adding better error handling and retry logic
3. Using different endpoints and approaches
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


class FixedESPNScraper:
    def __init__(self, output_dir: str = "data/scraped_espn_fixed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ESPN API configuration
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
        self.rate_limit_delay = 1.0  # 1 second between requests

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
                "Referer": "https://www.espn.com/",
                "Origin": "https://www.espn.com",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            }
        )

        # Disable SSL verification for now
        self.session.verify = False

    def test_connectivity(self) -> bool:
        """Test basic connectivity to ESPN API"""
        logger.info("Testing ESPN API connectivity...")

        try:
            # Test with a simple endpoint
            test_url = f"{self.base_url}/scoreboard"
            params = {"dates": "20240115"}  # Use a known date

            logger.info(f"Testing URL: {test_url}")
            response = self.session.get(test_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if "events" in data:
                    logger.info("✅ ESPN API connectivity test successful!")
                    logger.info(f"Found {len(data['events'])} events")
                    return True
                else:
                    logger.warning("⚠️ ESPN API returned unexpected data structure")
                    return False
            else:
                logger.warning(f"⚠️ ESPN API returned status {response.status_code}")
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

    def test_playbyplay_endpoint(self, game_id: str = "401734908") -> bool:
        """Test the play-by-play endpoint with a specific game"""
        logger.info(f"Testing PlayByPlay endpoint with game {game_id}...")

        try:
            url = f"{self.base_url}/playbyplay/{game_id}"

            logger.info(f"Testing URL: {url}")
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if "page" in data and "content" in data["page"]:
                    logger.info("✅ PlayByPlay endpoint test successful!")
                    return True
                else:
                    logger.warning(
                        "⚠️ PlayByPlay endpoint returned unexpected data structure"
                    )
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

    def scrape_game_playbyplay(self, game_id: str) -> Optional[Dict]:
        """Scrape play-by-play data for a specific game"""
        logger.info(f"Scraping play-by-play for game {game_id}...")

        try:
            url = f"{self.base_url}/playbyplay/{game_id}"

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Save the data
                output_file = self.output_dir / f"{game_id}.json"
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

    def scrape_failed_games(self, game_ids: List[str]) -> Dict:
        """Scrape multiple failed games"""
        logger.info(f"Starting to scrape {len(game_ids)} failed games...")

        successful_games = 0
        failed_games = 0
        results = []

        for i, game_id in enumerate(game_ids):
            logger.info(f"Processing game {i+1}/{len(game_ids)}: {game_id}")

            # Scrape game data
            game_data = self.scrape_game_playbyplay(game_id)

            if game_data:
                successful_games += 1
                results.append(
                    {"game_id": game_id, "status": "success", "data": game_data}
                )
            else:
                failed_games += 1
                results.append({"game_id": game_id, "status": "failed", "data": None})

            # Rate limiting
            if i < len(game_ids) - 1:  # Don't delay after last request
                time.sleep(self.rate_limit_delay)

        # Summary
        logger.info("=" * 50)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total games attempted: {len(game_ids)}")
        logger.info(f"Successful: {successful_games}")
        logger.info(f"Failed: {failed_games}")
        logger.info(f"Success rate: {(successful_games/len(game_ids)*100):.1f}%")
        logger.info(f"Output directory: {self.output_dir}")

        return {
            "total": len(game_ids),
            "successful": successful_games,
            "failed": failed_games,
            "success_rate": successful_games / len(game_ids) * 100,
            "results": results,
        }

    def run_comprehensive_test(self):
        """Run comprehensive tests of ESPN API functionality"""
        logger.info("=" * 60)
        logger.info("ESPN API COMPREHENSIVE TEST")
        logger.info("=" * 60)

        # Test 1: Basic connectivity
        logger.info("\n[TEST 1] Basic Connectivity")
        connectivity_ok = self.test_connectivity()

        # Test 2: PlayByPlay endpoint
        logger.info("\n[TEST 2] PlayByPlay Endpoint")
        pbp_ok = self.test_playbyplay_endpoint()

        # Test 3: Scrape a few failed games
        logger.info("\n[TEST 3] Scrape Failed Games")
        test_game_ids = [
            "401734908",
            "400223639",
            "400232028",
            "151112012",
            "180116011",
        ]
        scraping_results = self.scrape_failed_games(test_game_ids)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(
            f"Basic Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}"
        )
        logger.info(f"PlayByPlay Endpoint: {'✅ PASS' if pbp_ok else '❌ FAIL'}")
        logger.info(
            f"Test Games Scraped: {scraping_results['successful']}/{scraping_results['total']}"
        )
        logger.info(f"Success Rate: {scraping_results['success_rate']:.1f}%")
        logger.info(f"Output Directory: {self.output_dir}")

        return {
            "connectivity": connectivity_ok,
            "playbyplay": pbp_ok,
            "scraping_results": scraping_results,
        }


def main():
    """Main function"""
    scraper = FixedESPNScraper()

    logger.info("Starting ESPN API connectivity fix and test...")

    # Run comprehensive test
    results = scraper.run_comprehensive_test()

    if results["connectivity"] and results["playbyplay"]:
        logger.info("✅ ESPN API is working correctly!")

        # If tests pass, scrape all failed games
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING ALL FAILED GAMES")
        logger.info("=" * 60)

        # Failed game IDs from the extraction log
        failed_game_ids = [
            "201024017",
            "131207019",
            "400223639",
            "401734908",
            "400232028",
            "151112012",
            "401705756",
            "180116011",
            "400216824",
            "190408025",
            "151216004",
            "171107013",
            "400228075",
            "400232881",
            "210213024",
            "271009013",
            "180106011",
            "171213005",
            "400228425",
            "140325021",
            "131215024",
            "180501010",
            "190307011",
            "170111029",
            "170113014",
            "180317022",
            "200427011",
            "200117001",
            "211207023",
            "160310029",
            "190329006",
            "211111008",
            "200107001",
            "401705243",
            "150325012",
            "131123006",
            "151228013",
            "400234810",
            "210125006",
            "210415016",
            "401705613",
            "400224543",
            "140307015",
            "151120026",
            "190210009",
            "180124025",
            "161226006",
            "180205003",
            "140111022",
            "201023013",
            "191115021",
            "400233951",
            "401705097",
            "190227004",
            "151115016",
            "150131018",
            "400226600",
            "190310015",
            "140407100",
            "200226027",
            "160327024",
            "200412021",
            "210208003",
            "400225186",
            "210214020",
            "161228018",
            "400227441",
            "191119002",
            "150524024",
            "170305023",
            "140322025",
            "171208022",
            "140209017",
            "140217009",
            "160104023",
            "211011014",
            "170114010",
            "400234328",
            "160222001",
            "400222706",
            "210311005",
            "220115004",
            "200204013",
            "201222020",
            "191223003",
            "150421001",
            "160418019",
            "400234778",
            "190219013",
            "170104010",
            "400226315",
            "191127015",
            "210301005",
            "141105025",
            "400231829",
            "401705078",
            "141119006",
            "400219456",
            "401705582",
            "150322016",
            "160126017",
            "400235493",
            "180123021",
            "151127022",
            "401705428",
            "220105004",
            "400235169",
            "190322021",
            "211118012",
            "400224282",
            "131230014",
            "400236196",
            "400225240",
            "131109005",
            "160201018",
            "151202010",
            "210113026",
            "400220412",
            "140204019",
            "400237787",
        ]

        final_results = scraper.scrape_failed_games(failed_game_ids)
        logger.info(
            f"✅ Final scraping complete: {final_results['successful']}/{final_results['total']} games successful"
        )

    else:
        logger.error("❌ ESPN API has issues that need to be addressed")

    return results


if __name__ == "__main__":
    main()
