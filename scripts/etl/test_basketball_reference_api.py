#!/usr/bin/env python3
"""
Basketball Reference API Diagnostic Tool
Tests endpoints to identify specific failure reasons
"""

import time
import logging
import sys
from datetime import datetime

try:
    from basketball_reference_web_scraper import client
    from basketball_reference_web_scraper.data import OutputType

    HAS_BBREF = True
except ImportError:
    HAS_BBREF = False
    print("❌ basketball_reference_web_scraper not installed")
    print("Install with: pip install basketball_reference_web_scraper")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_basic_connectivity():
    """Test if API is accessible at all"""
    print("Testing basic connectivity...")
    try:
        # Try simplest request - current season schedule
        result = client.season_schedule(season_end_year=2024)
        print(f"✅ Basic connectivity works! Got {len(result)} games")
        return True
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        print(f"Error type: {type(e).__name__}")
        logger.error(f"Basic connectivity error: {e}", exc_info=True)
        return False


def test_historical_season(year):
    """Test if historical seasons work"""
    print(f"Testing season {year}...")
    try:
        result = client.season_schedule(season_end_year=year)
        print(f"✅ Season {year} works! Got {len(result)} games")
        return True
    except Exception as e:
        print(f"❌ Season {year} failed: {e}")
        print(f"Error type: {type(e).__name__}")
        logger.error(f"Season {year} error: {e}", exc_info=True)
        return False


def test_rate_limits():
    """Test if rate limiting is the issue"""
    print("\nTesting rate limits...")
    rate_limits = [1.0, 3.0, 5.0, 10.0, 15.0, 20.0]

    for rate_limit in rate_limits:
        print(f"Testing with {rate_limit}s delay...")
        try:
            time.sleep(rate_limit)
            result = client.season_schedule(season_end_year=2024)
            print(f"✅ Success with {rate_limit}s delay!")
            return rate_limit
        except Exception as e:
            print(f"❌ Failed even with {rate_limit}s delay: {e}")
            logger.error(f"Rate limit {rate_limit}s error: {e}")

    return None


def test_different_endpoints():
    """Test different Basketball Reference endpoints"""
    print("\nTesting different endpoints...")

    endpoints_to_test = [
        ("season_schedule", lambda: client.season_schedule(season_end_year=2024)),
        (
            "player_box_scores",
            lambda: client.player_box_scores(day=1, month=1, year=2024),
        ),
        ("team_box_scores", lambda: client.team_box_scores(day=1, month=1, year=2024)),
        ("season_totals", lambda: client.season_totals(season_end_year=2024)),
        ("standings", lambda: client.standings(season_end_year=2024)),
    ]

    working_endpoints = []
    failed_endpoints = []

    for endpoint_name, endpoint_func in endpoints_to_test:
        try:
            print(f"  Testing {endpoint_name}...")
            time.sleep(5)  # Be nice to API
            result = endpoint_func()
            if result:
                print(f"    ✅ {endpoint_name} works!")
                working_endpoints.append(endpoint_name)
            else:
                print(f"    ⚠️ {endpoint_name} returned empty result")
                failed_endpoints.append(endpoint_name)
        except Exception as e:
            print(f"    ❌ {endpoint_name} failed: {e}")
            failed_endpoints.append(endpoint_name)
            logger.error(f"{endpoint_name} error: {e}")

    return working_endpoints, failed_endpoints


def test_user_agent():
    """Test with different user agents"""
    print("\nTesting different user agents...")

    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Python-urllib/3.9",
    ]

    for ua in user_agents:
        try:
            print(f"  Testing with user agent: {ua[:50]}...")

            # Try to set user agent (this might not work with all versions)
            if hasattr(client, "http_client"):
                client.http_client.headers.update({"User-Agent": ua})

            time.sleep(3)
            result = client.season_schedule(season_end_year=2024)
            if result:
                print(f"    ✅ Success with user agent!")
                return ua
            else:
                print(f"    ⚠️ Empty result with user agent")
        except Exception as e:
            print(f"    ❌ Failed with user agent: {e}")
            logger.error(f"User agent {ua} error: {e}")

    return None


def test_package_version():
    """Check package version and compatibility"""
    print("\nChecking package version...")

    try:
        import basketball_reference_web_scraper

        version = getattr(basketball_reference_web_scraper, "__version__", "Unknown")
        print(f"Package version: {version}")

        # Check if it's a recent version
        if version != "Unknown":
            print(f"✅ Package version detected: {version}")
        else:
            print("⚠️ Could not detect package version")

    except Exception as e:
        print(f"❌ Error checking package version: {e}")


def main():
    print("Basketball Reference API Diagnostic")
    print("=" * 60)
    print(f"Start time: {datetime.now()}")
    print()

    # Test 1: Basic connectivity
    print("[1] Testing basic connectivity...")
    if not test_basic_connectivity():
        print("\n⚠️ API appears to be down or blocked")
        print("Possible causes:")
        print("  - IP rate limited/banned")
        print("  - API endpoint changed")
        print("  - Network connectivity issue")
        print("  - Package version incompatible")

        # Still continue with other tests
        print("\nContinuing with additional diagnostics...")
    else:
        print("\n✅ Basic connectivity confirmed!")

    # Test 2: Historical seasons
    print("\n[2] Testing historical seasons...")
    test_years = [2024, 2020, 2010, 2000, 1993]
    working_years = []

    for year in test_years:
        if test_historical_season(year):
            working_years.append(year)
        time.sleep(5)  # Be nice to API

    if working_years:
        print(f"\n✅ Working years: {working_years}")
    else:
        print("\n❌ No historical years working")

    # Test 3: Rate limiting
    print("\n[3] Testing rate limits...")
    optimal_delay = test_rate_limits()
    if optimal_delay:
        print(f"\n✅ Optimal delay: {optimal_delay}s")
    else:
        print("\n❌ Rate limiting not solving the issue")

    # Test 4: Different endpoints
    print("\n[4] Testing different endpoints...")
    working_endpoints, failed_endpoints = test_different_endpoints()

    if working_endpoints:
        print(f"\n✅ Working endpoints: {working_endpoints}")
    if failed_endpoints:
        print(f"\n❌ Failed endpoints: {failed_endpoints}")

    # Test 5: User agent
    print("\n[5] Testing user agents...")
    working_ua = test_user_agent()
    if working_ua:
        print(f"\n✅ Working user agent: {working_ua}")
    else:
        print("\n❌ No user agent fixes the issue")

    # Test 6: Package version
    print("\n[6] Checking package version...")
    test_package_version()

    # Summary
    print(f"\n{'='*60}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")

    if working_years:
        print(f"✅ Working seasons: {working_years}")
    else:
        print("❌ No seasons working")

    if working_endpoints:
        print(f"✅ Working endpoints: {working_endpoints}")
    else:
        print("❌ No endpoints working")

    if optimal_delay:
        print(f"✅ Recommended delay: {optimal_delay}s")
    else:
        print("❌ Rate limiting not the issue")

    if working_ua:
        print(f"✅ Recommended user agent: {working_ua}")
    else:
        print("❌ User agent not the issue")

    print(f"\nEnd time: {datetime.now()}")

    # Return appropriate exit code
    if working_years and working_endpoints:
        print("\n✅ Basketball Reference API is working!")
        return 0
    else:
        print("\n❌ Basketball Reference API has issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
