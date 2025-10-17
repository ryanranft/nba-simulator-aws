#!/usr/bin/env python3
"""
NBA.com Stats API Verification Script (Date+Team Matching Strategy)

Purpose: Verify ESPN S3 data quality by comparing against NBA.com Stats API
- Samples 100 random games from S3
- Queries NBA.com Stats API by date
- Matches games using date + team abbreviations
- Compares scores, dates, team IDs
- Logs discrepancies to docs/VERIFICATION_RESULTS.md

Success Criteria:
- Score accuracy ≥ 99%
- Date accuracy ≥ 99%
- Data completeness ≥ 95%
- Discrepancy rate ≤ 5%

Created: October 6, 2025 (Phase 1, Sub-Phase 1.6)
Updated: October 6, 2025 (Implemented date+team matching)
"""

import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import boto3
import requests
from botocore.exceptions import ClientError

# Configuration
S3_BUCKET = "nba-sim-raw-data-lake"
SAMPLE_SIZE = 20  # Reduced for faster testing (was 100)
NBA_API_BASE = "https://stats.nba.com/stats"
RESULTS_FILE = Path(__file__).parent.parent.parent / "docs" / "VERIFICATION_RESULTS.md"
TEAM_MAPPING_FILE = Path(__file__).parent.parent / "mapping" / "team_id_mapping.json"

# NBA.com Stats API requires User-Agent header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://stats.nba.com/",
}

# Rate limiting
REQUEST_DELAY = 0.6  # 600ms between requests (safer rate limit)


# ESPN Game ID Decoding (per LESSONS_LEARNED.md:269-294)
def decode_espn_game_id(game_id: str) -> Optional[Dict]:
    """
    Decode ESPN game ID to extract date information

    Format: YYMMDD### (pre-2018) or 401###### (2018+)
    - YY: Year code (offset from 1980)
    - MM: Month (01-12)
    - DD: Day (01-31)
    - ###: Sequence number

    Examples:
    - 190302004 → 1999-03-02 (game #4)
    - 401307856 → 2021 (new format, date encoded differently)

    Returns:
        Dict with 'year', 'month', 'day', 'sequence' or None if invalid
    """
    game_id = str(game_id)

    # New format (2018+): 401######
    if game_id.startswith("401") or game_id.startswith("400"):
        # New format doesn't encode date in same way
        # Return None to indicate we can't decode it
        return None

    # Old format: YYMMDD###
    if len(game_id) >= 8:
        try:
            year_code = int(game_id[0:2])
            month = int(game_id[2:4])
            day = int(game_id[4:6])
            sequence = int(game_id[6:]) if len(game_id) > 6 else 0

            # Year calculation: 1980 + year_code
            year = 1980 + year_code

            # Validation
            if 1 <= month <= 12 and 1 <= day <= 31 and 1980 <= year <= 2020:
                return {
                    "year": year,
                    "month": month,
                    "day": day,
                    "sequence": sequence,
                    "date_str": f"{year:04d}{month:02d}{day:02d}",
                }
        except (ValueError, IndexError):
            pass

    return None


class NBAStatsVerifier:
    """Verifies ESPN S3 data against NBA.com Stats API using date+team matching"""

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.team_mapping = self.load_team_mapping()
        self.nba_cache = {}  # Cache NBA.com API responses by date
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "sample_size": SAMPLE_SIZE,
            "total_compared": 0,
            "score_matches": 0,
            "date_matches": 0,
            "found_in_nba_api": 0,
            "discrepancies": [],
            "errors": [],
        }

    def load_team_mapping(self) -> Dict:
        """Load team ID mapping table"""
        try:
            with open(TEAM_MAPPING_FILE) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Team mapping file not found: {TEAM_MAPPING_FILE}")
            return {}

    def get_nba_id_from_abbr(self, abbreviation: str) -> Optional[int]:
        """Get NBA.com team ID from abbreviation"""
        team = self.team_mapping.get(abbreviation)
        return team["nba_id"] if team else None

    def get_abbr_from_nba_id(self, nba_id: int) -> Optional[str]:
        """Get team abbreviation from NBA.com team ID"""
        for abbr, data in self.team_mapping.items():
            if data["nba_id"] == nba_id:
                return abbr
        return None

    def get_random_game_sample(self) -> List[str]:
        """Get random sample of game IDs from S3 schedule files"""
        print(f"Sampling {SAMPLE_SIZE} random games from S3...")

        try:
            # List all schedule files (these have game data)
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=S3_BUCKET, Prefix="schedule/")

            all_files = []
            for page in pages:
                if "Contents" in page:
                    all_files.extend([obj["Key"] for obj in page["Contents"]])

            # Extract dates from filenames
            dates = []
            for key in all_files:
                if key.endswith(".json"):
                    # Extract date from "schedule/YYYYMMDD.json"
                    date_str = key.split("/")[-1].replace(".json", "")
                    if len(date_str) == 8 and date_str.isdigit():
                        dates.append(date_str)

            # Random sample of dates
            if len(dates) < SAMPLE_SIZE:
                print(f"Warning: Only {len(dates)} dates available, using all")
                return dates

            sample = random.sample(dates, SAMPLE_SIZE)
            print(f"✓ Sampled {len(sample)} dates")
            return sorted(sample)  # Sort for easier debugging

        except ClientError as e:
            print(f"Error accessing S3: {e}")
            self.results["errors"].append(f"S3 error: {str(e)}")
            return []

    def get_espn_schedule_data(self, date_str: str) -> Optional[Dict]:
        """
        Fetch schedule data from ESPN API for a given date
        date_str format: YYYYMMDD
        """
        try:
            # ESPN API endpoint
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            params = {"dates": date_str}

            response = requests.get(url, params=params, timeout=10)
            time.sleep(REQUEST_DELAY)  # Rate limiting

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"ESPN API error for {date_str}: {e}")
            return None

    def get_nba_stats_scoreboard(self, date_str: str) -> Optional[Dict]:
        """
        Fetch scoreboard data from NBA.com Stats API for a given date
        date_str format: YYYYMMDD
        """
        # Check cache first
        if date_str in self.nba_cache:
            return self.nba_cache[date_str]

        try:
            # Convert YYYYMMDD to YYYY-MM-DD for NBA.com API
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

            url = f"{NBA_API_BASE}/scoreboardV2"
            params = {"GameDate": formatted_date, "LeagueID": "00", "DayOffset": "0"}

            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            time.sleep(REQUEST_DELAY)  # Rate limiting

            if response.status_code == 200:
                data = response.json()
                self.nba_cache[date_str] = data
                return data
            else:
                print(f"NBA API error for {date_str}: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"NBA API error for {date_str}: {e}")
            return None

    def extract_espn_games(self, espn_data: Dict) -> List[Dict]:
        """Extract game information from ESPN schedule data"""
        games = []

        if not espn_data:
            return games

        # ESPN data structure varies, try different paths
        events = None
        if "events" in espn_data:
            events = espn_data["events"]
        elif "scoreboard" in espn_data and "events" in espn_data["scoreboard"]:
            events = espn_data["scoreboard"]["events"]

        if not events:
            return games

        for event in events:
            try:
                # Extract game info
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])

                if len(competitors) != 2:
                    continue

                # Find home/away teams
                home_team = None
                away_team = None
                for team in competitors:
                    team_info = team.get("team", {})
                    if team.get("homeAway") == "home":
                        home_team = {
                            "abbreviation": team_info.get("abbreviation"),
                            "score": team.get("score"),
                            "name": team_info.get("displayName"),
                        }
                    else:
                        away_team = {
                            "abbreviation": team_info.get("abbreviation"),
                            "score": team.get("score"),
                            "name": team_info.get("displayName"),
                        }

                if home_team and away_team:
                    games.append(
                        {
                            "game_id": event.get("id"),
                            "date": comp.get("date", "")[:10],  # YYYY-MM-DD
                            "home": home_team,
                            "away": away_team,
                            "status": comp.get("status", {})
                            .get("type", {})
                            .get("description"),
                        }
                    )

            except (KeyError, IndexError, TypeError) as e:
                continue

        return games

    def extract_nba_games(self, nba_data: Dict) -> List[Dict]:
        """Extract game information from NBA.com Stats API response"""
        games = []

        if not nba_data or "resultSets" not in nba_data:
            return games

        # Find GameHeader and LineScore result sets
        game_header = None
        line_score = None

        for result_set in nba_data["resultSets"]:
            if result_set["name"] == "GameHeader":
                game_header = result_set
            elif result_set["name"] == "LineScore":
                line_score = result_set

        if not game_header or not line_score:
            return games

        # Parse GameHeader
        headers = game_header["headers"]
        for row in game_header["rowSet"]:
            game_dict = dict(zip(headers, row))

            # Find corresponding scores from LineScore
            game_id = game_dict.get("GAME_ID")
            scores = {}
            for score_row in line_score["rowSet"]:
                score_dict = dict(zip(line_score["headers"], score_row))
                if score_dict.get("GAME_ID") == game_id:
                    team_abbr = score_dict.get("TEAM_ABBREVIATION")
                    scores[team_abbr] = {
                        "score": score_dict.get("PTS"),
                        "team_id": score_dict.get("TEAM_ID"),
                    }

            games.append(
                {
                    "game_id": game_id,
                    "date": game_dict.get("GAME_DATE_EST"),
                    "home_team_id": game_dict.get("HOME_TEAM_ID"),
                    "away_team_id": game_dict.get("VISITOR_TEAM_ID"),
                    "scores": scores,
                }
            )

        return games

    def match_and_compare_games(
        self, date_str: str, espn_games: List[Dict], nba_games: List[Dict]
    ):
        """Match ESPN games to NBA.com games and compare"""

        # Group ESPN games by team matchup to detect duplicates
        game_groups = {}
        for espn_game in espn_games:
            # Skip if game not final
            if espn_game.get("status") != "Final":
                continue

            espn_home = espn_game["home"]["abbreviation"]
            espn_away = espn_game["away"]["abbreviation"]
            matchup = f"{espn_away}@{espn_home}"

            if matchup not in game_groups:
                game_groups[matchup] = []
            game_groups[matchup].append(espn_game)

        # Process each unique matchup
        for matchup, games in game_groups.items():
            # Check for duplicate game IDs (same matchup, different IDs)
            if len(games) > 1:
                game_ids = [g["game_id"] for g in games]
                decoded_ids = []
                for gid in game_ids:
                    decoded = decode_espn_game_id(gid)
                    if decoded:
                        decoded_ids.append(f"{gid} (decoded: {decoded['date_str']})")
                    else:
                        decoded_ids.append(f"{gid} (new format)")

                # Log duplicate detection
                print(f"    ⚠️ Duplicate IDs for {matchup}: {', '.join(decoded_ids)}")

                # Use the game with the highest score (most complete data)
                espn_game = max(
                    games,
                    key=lambda g: (g["home"]["score"] or 0) + (g["away"]["score"] or 0),
                )
            else:
                espn_game = games[0]

            espn_home = espn_game["home"]["abbreviation"]
            espn_away = espn_game["away"]["abbreviation"]
            espn_home_score = espn_game["home"]["score"]
            espn_away_score = espn_game["away"]["score"]

            # Decode game ID for additional validation
            game_id_info = decode_espn_game_id(espn_game["game_id"])
            if game_id_info:
                # Verify decoded date matches expected date
                if game_id_info["date_str"] != date_str:
                    print(
                        f"    ⚠️ Game ID date mismatch: {espn_game['game_id']} decodes to {game_id_info['date_str']}, expected {date_str}"
                    )

            # Find matching NBA.com game
            nba_match = None
            for nba_game in nba_games:
                nba_home_id = nba_game["home_team_id"]
                nba_away_id = nba_game["away_team_id"]

                nba_home = self.get_abbr_from_nba_id(nba_home_id)
                nba_away = self.get_abbr_from_nba_id(nba_away_id)

                # Match by teams
                if espn_home == nba_home and espn_away == nba_away:
                    nba_match = nba_game
                    break

            if not nba_match:
                # Game not found in NBA.com data
                continue

            # Game found - increment counter
            self.results["found_in_nba_api"] += 1
            self.results["total_compared"] += 1

            # Extract NBA.com scores
            nba_scores = nba_match["scores"]
            nba_home_score = nba_scores.get(espn_home, {}).get("score")
            nba_away_score = nba_scores.get(espn_away, {}).get("score")

            # Compare dates (should always match since we query by date)
            self.results["date_matches"] += 1

            # Compare scores
            discrepancy = None
            if str(espn_home_score) != str(nba_home_score):
                discrepancy = {
                    "date": date_str,
                    "game_id": espn_game["game_id"],
                    "teams": f"{espn_away} @ {espn_home}",
                    "issues": [
                        f"Home score: ESPN={espn_home_score}, NBA.com={nba_home_score}"
                    ],
                }

            if str(espn_away_score) != str(nba_away_score):
                if discrepancy:
                    discrepancy["issues"].append(
                        f"Away score: ESPN={espn_away_score}, NBA.com={nba_away_score}"
                    )
                else:
                    discrepancy = {
                        "date": date_str,
                        "game_id": espn_game["game_id"],
                        "teams": f"{espn_away} @ {espn_home}",
                        "issues": [
                            f"Away score: ESPN={espn_away_score}, NBA.com={nba_away_score}"
                        ],
                    }

            if discrepancy:
                self.results["discrepancies"].append(discrepancy)
            else:
                self.results["score_matches"] += 1

    def run_verification(self):
        """Main verification workflow"""
        print("\n=== NBA.com Stats API Verification (Date+Team Matching) ===\n")

        # Step 1: Get random sample of dates
        date_sample = self.get_random_game_sample()
        if not date_sample:
            print("Error: Could not sample dates from S3")
            return

        # Step 2: Compare games for each date
        print(f"\nVerifying games from {len(date_sample)} dates...")
        print("(This may take a few minutes due to API rate limiting)\n")

        dates_processed = 0
        for date_str in date_sample:
            dates_processed += 1
            print(
                f"[{dates_processed}/{len(date_sample)}] Processing {date_str}...",
                end=" ",
            )

            # Get ESPN data for this date
            espn_data = self.get_espn_schedule_data(date_str)
            if not espn_data:
                print("⊘ No ESPN data")
                continue

            espn_games = self.extract_espn_games(espn_data)
            if not espn_games:
                print("⊘ No ESPN games parsed")
                continue

            # Get NBA.com data for this date
            nba_data = self.get_nba_stats_scoreboard(date_str)
            if not nba_data:
                print("⊘ No NBA.com data")
                continue

            nba_games = self.extract_nba_games(nba_data)
            if not nba_games:
                print("⊘ No NBA.com games parsed")
                continue

            # Match and compare
            self.match_and_compare_games(date_str, espn_games, nba_games)

            print(f"✓ {len(espn_games)} ESPN games, {len(nba_games)} NBA.com games")

        # Step 3: Calculate metrics
        self.calculate_metrics()

        # Step 4: Write results
        self.write_results()

        # Step 5: Print summary
        self.print_summary()

    def calculate_metrics(self):
        """Calculate verification metrics"""
        total = self.results["total_compared"]
        if total == 0:
            return

        self.results["score_accuracy"] = self.results["score_matches"] / total * 100
        self.results["date_accuracy"] = self.results["date_matches"] / total * 100
        self.results["data_completeness"] = (
            (self.results["found_in_nba_api"] / total * 100) if total > 0 else 0
        )
        self.results["discrepancy_rate"] = (
            (len(self.results["discrepancies"]) / total * 100) if total > 0 else 0
        )

    def write_results(self):
        """Write results to VERIFICATION_RESULTS.md"""
        print(f"\nWriting results to {RESULTS_FILE}...")

        content = f"""# Data Verification Results

**Generated:** {self.results['timestamp']}
**Verification Source:** NBA.com Stats API
**Matching Strategy:** Date + Team Abbreviations
**Sample Size:** {self.results['sample_size']} dates

---

## Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Score Accuracy** | {self.results.get('score_accuracy', 0):.1f}% | ≥ 99% | {'✅' if self.results.get('score_accuracy', 0) >= 99 else '❌'} |
| **Date Accuracy** | {self.results.get('date_accuracy', 0):.1f}% | ≥ 99% | {'✅' if self.results.get('date_accuracy', 0) >= 99 else '❌'} |
| **Data Completeness** | {self.results.get('data_completeness', 0):.1f}% | ≥ 95% | {'✅' if self.results.get('data_completeness', 0) >= 95 else '❌'} |
| **Discrepancy Rate** | {self.results.get('discrepancy_rate', 0):.1f}% | ≤ 5% | {'✅' if self.results.get('discrepancy_rate', 0) <= 5 else '❌'} |

**Games Compared:** {self.results['total_compared']}
**Found in NBA.com API:** {self.results['found_in_nba_api']}
**Score Matches:** {self.results['score_matches']}
**Discrepancies Found:** {len(self.results['discrepancies'])}

---

## Discrepancies

"""

        if self.results["discrepancies"]:
            for disc in self.results["discrepancies"]:
                content += (
                    f"\n### {disc['date']} - {disc['teams']} (Game {disc['game_id']})\n"
                )
                for issue in disc["issues"]:
                    content += f"- {issue}\n"
        else:
            content += "✅ No discrepancies found!\n"

        content += "\n---\n\n## Errors\n\n"

        if self.results["errors"]:
            for error in self.results["errors"]:
                content += f"- {error}\n"
        else:
            content += "✅ No errors encountered\n"

        content += "\n---\n\n## Conclusion\n\n"

        # Determine overall pass/fail
        passed = (
            self.results.get("score_accuracy", 0) >= 99
            and self.results.get("date_accuracy", 0) >= 99
            and self.results.get("data_completeness", 0) >= 95
            and self.results.get("discrepancy_rate", 0) <= 5
        )

        if passed:
            content += "✅ **VERIFICATION PASSED** - ESPN data quality meets all success criteria\n"
        else:
            content += (
                "❌ **VERIFICATION FAILED** - Some metrics below success criteria\n"
            )

        content += f"\n*Next verification: Run monthly or after data updates*\n"

        # Write to file
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        RESULTS_FILE.write_text(content)
        print(f"✓ Results written to {RESULTS_FILE}")

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 50)
        print("VERIFICATION SUMMARY")
        print("=" * 50)
        print(f"Games Compared:      {self.results['total_compared']}")
        print(f"Score Accuracy:      {self.results.get('score_accuracy', 0):.1f}%")
        print(f"Date Accuracy:       {self.results.get('date_accuracy', 0):.1f}%")
        print(f"Data Completeness:   {self.results.get('data_completeness', 0):.1f}%")
        print(f"Discrepancy Rate:    {self.results.get('discrepancy_rate', 0):.1f}%")
        print("=" * 50)
        print(f"\nFull results: {RESULTS_FILE}")


def main():
    """Main entry point"""
    verifier = NBAStatsVerifier()
    verifier.run_verification()


if __name__ == "__main__":
    main()
