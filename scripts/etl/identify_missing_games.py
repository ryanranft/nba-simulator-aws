#!/usr/bin/env python3
"""
Missing Games Identifier

Identifies specific games that are missing from our ESPN PBP data
by comparing against expected NBA schedule data.

Usage:
    python scripts/etl/identify_missing_games.py --season 2024-25
    python scripts/etl/identify_missing_games.py --all-seasons 2022-2025

Version: 1.0
Created: October 13, 2025
"""

import json
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import requests
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/missing_games_analysis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MissingGamesIdentifier:
    """Identifies missing games by comparing against NBA schedule"""

    def __init__(self, pbp_dir: str):
        self.pbp_dir = Path(pbp_dir)
        self.missing_games = defaultdict(list)
        self.season_stats = defaultdict(
            lambda: {
                "total_games": 0,
                "found_games": 0,
                "missing_games": 0,
                "missing_game_ids": [],
            }
        )

        logger.info(f"Initialized Missing Games Identifier")
        logger.info(f"PBP directory: {self.pbp_dir}")

    def get_nba_schedule(self, season: str) -> List[Dict]:
        """Get NBA schedule for a season from ESPN API"""
        logger.info(f"Fetching NBA schedule for {season}")

        # Convert season format (e.g., "2024-25" -> "2024")
        year = season.split("-")[0]

        try:
            # ESPN API endpoint for NBA schedule
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

            # Get regular season games (typically Oct-Apr)
            games = []

            # Try different months to get full season
            for month in range(10, 13):  # Oct-Dec
                date_str = f"{year}-{month:02d}-01"
                params = {"dates": date_str}

                try:
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    if "events" in data:
                        for event in data["events"]:
                            if event.get("season", {}).get("year") == int(year):
                                games.append(
                                    {
                                        "id": event["id"],
                                        "date": event["date"],
                                        "home_team": event["competitions"][0][
                                            "competitors"
                                        ][0]["team"]["abbreviation"],
                                        "away_team": event["competitions"][0][
                                            "competitors"
                                        ][1]["team"]["abbreviation"],
                                        "season": season,
                                    }
                                )

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    logger.warning(f"Error fetching {date_str}: {e}")
                    continue

            # Get games from next year (Jan-Apr)
            next_year = str(int(year) + 1)
            for month in range(1, 5):  # Jan-Apr
                date_str = f"{next_year}-{month:02d}-01"
                params = {"dates": date_str}

                try:
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    if "events" in data:
                        for event in data["events"]:
                            if event.get("season", {}).get("year") == int(year):
                                games.append(
                                    {
                                        "id": event["id"],
                                        "date": event["date"],
                                        "home_team": event["competitions"][0][
                                            "competitors"
                                        ][0]["team"]["abbreviation"],
                                        "away_team": event["competitions"][0][
                                            "competitors"
                                        ][1]["team"]["abbreviation"],
                                        "season": season,
                                    }
                                )

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    logger.warning(f"Error fetching {date_str}: {e}")
                    continue

            logger.info(f"Found {len(games)} games for {season}")
            return games

        except Exception as e:
            logger.error(f"Error fetching NBA schedule for {season}: {e}")
            return []

    def get_existing_games(self, season: str) -> Set[str]:
        """Get list of existing game IDs from PBP files"""
        logger.info(f"Scanning existing games for {season}")

        existing_games = set()
        files_processed = 0

        for file_path in self.pbp_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Get game date
                gamepackage = data["page"]["content"]["gamepackage"]
                gm_info = gamepackage.get("gmInfo", {})
                game_date_str = gm_info.get("dtTm", "")

                if not game_date_str:
                    continue

                # Parse date and check season
                try:
                    game_date = datetime.fromisoformat(
                        game_date_str.replace("Z", "+00:00")
                    )
                    file_season = f"{game_date.year}-{str(game_date.year + 1)[2:]}"

                    if file_season == season:
                        game_id = file_path.stem
                        existing_games.add(game_id)
                        files_processed += 1

                        if files_processed % 1000 == 0:
                            logger.info(
                                f"Processed {files_processed} files for {season}"
                            )

                except Exception as e:
                    continue

            except Exception as e:
                continue

        logger.info(f"Found {len(existing_games)} existing games for {season}")
        return existing_games

    def identify_missing_games(self, season: str) -> Dict:
        """Identify missing games for a specific season"""
        logger.info(f"Identifying missing games for {season}")

        # Get expected games from NBA schedule
        expected_games = self.get_nba_schedule(season)
        if not expected_games:
            logger.error(f"Could not get NBA schedule for {season}")
            return {}

        # Get existing games from PBP files
        existing_games = self.get_existing_games(season)

        # Find missing games
        expected_game_ids = {str(game["id"]) for game in expected_games}
        missing_game_ids = expected_game_ids - existing_games

        # Get details of missing games
        missing_games_details = []
        for game in expected_games:
            if str(game["id"]) in missing_game_ids:
                missing_games_details.append(
                    {
                        "game_id": str(game["id"]),
                        "date": game["date"],
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "season": season,
                    }
                )

        # Update statistics
        stats = self.season_stats[season]
        stats["total_games"] = len(expected_games)
        stats["found_games"] = len(existing_games)
        stats["missing_games"] = len(missing_game_ids)
        stats["missing_game_ids"] = missing_games_details

        logger.info(
            f"Season {season}: {len(missing_game_ids)}/{len(expected_games)} games missing"
        )

        return {
            "season": season,
            "total_games": len(expected_games),
            "found_games": len(existing_games),
            "missing_games": len(missing_game_ids),
            "missing_game_details": missing_games_details,
        }

    def analyze_all_seasons(self, start_year: int, end_year: int) -> Dict:
        """Analyze missing games for multiple seasons"""
        logger.info(f"Analyzing missing games for seasons {start_year}-{end_year}")

        results = {}

        for year in range(start_year, end_year + 1):
            season = f"{year}-{str(year + 1)[2:]}"
            logger.info(f"Analyzing season {season}")

            try:
                season_result = self.identify_missing_games(season)
                if season_result:
                    results[season] = season_result

                # Rate limiting between seasons
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error analyzing season {season}: {e}")
                continue

        return results

    def save_missing_games_report(self, results: Dict, output_file: str):
        """Save missing games report to file"""
        logger.info(f"Saving missing games report to {output_file}")

        report = {
            "analysis_date": datetime.now().isoformat(),
            "total_seasons": len(results),
            "total_missing_games": sum(r["missing_games"] for r in results.values()),
            "seasons": results,
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {output_file}")

    def print_summary(self, results: Dict):
        """Print summary of missing games analysis"""
        print("\n" + "=" * 60)
        print("MISSING GAMES ANALYSIS SUMMARY")
        print("=" * 60)

        total_missing = 0
        total_expected = 0

        for season, data in results.items():
            missing = data["missing_games"]
            total = data["total_games"]
            found = data["found_games"]
            coverage = (found / total * 100) if total > 0 else 0

            print(f"\n{season}:")
            print(f"  Expected games: {total:,}")
            print(f"  Found games: {found:,}")
            print(f"  Missing games: {missing:,}")
            print(f"  Coverage: {coverage:.1f}%")

            if missing > 0:
                print(f"  Missing game IDs: {missing} games")
                # Show first few missing games as examples
                if data["missing_game_details"]:
                    print(f"  Examples:")
                    for game in data["missing_game_details"][:3]:
                        print(
                            f"    {game['game_id']}: {game['away_team']} @ {game['home_team']} ({game['date']})"
                        )

            total_missing += missing
            total_expected += total

        print(f"\n" + "=" * 60)
        print(f"TOTAL SUMMARY:")
        print(f"  Expected games: {total_expected:,}")
        print(f"  Missing games: {total_missing:,}")
        print(
            f"  Overall coverage: {(total_expected - total_missing) / total_expected * 100:.1f}%"
        )
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Identify missing NBA games from PBP data"
    )
    parser.add_argument(
        "--pbp-dir", default="data/nba_pbp", help="Directory with ESPN PBP JSON files"
    )
    parser.add_argument("--season", help="Specific season to analyze (e.g., 2024-25)")
    parser.add_argument(
        "--all-seasons",
        nargs=2,
        metavar=("START", "END"),
        help="Analyze all seasons from START to END year",
    )
    parser.add_argument(
        "--output",
        default="data/missing_games_report.json",
        help="Output file for missing games report",
    )

    args = parser.parse_args()

    # Create identifier
    identifier = MissingGamesIdentifier(args.pbp_dir)

    if args.season:
        # Analyze single season
        results = identifier.identify_missing_games(args.season)
        if results:
            identifier.save_missing_games_report({args.season: results}, args.output)
            identifier.print_summary({args.season: results})

    elif args.all_seasons:
        # Analyze multiple seasons
        start_year = int(args.all_seasons[0])
        end_year = int(args.all_seasons[1])
        results = identifier.analyze_all_seasons(start_year, end_year)

        if results:
            identifier.save_missing_games_report(results, args.output)
            identifier.print_summary(results)

    else:
        logger.error("Must specify either --season or --all-seasons")
        return


if __name__ == "__main__":
    main()





