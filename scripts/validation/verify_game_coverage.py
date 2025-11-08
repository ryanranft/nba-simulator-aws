#!/usr/bin/env python3
"""
ESPN Schedule vs Database Coverage Verification

This script cross-references ESPN schedule data with the local PostgreSQL database
to identify which completed games are missing from our dataset.

Usage:
    python scripts/validation/verify_game_coverage.py --seasons 2011,2012,2019
    python scripts/validation/verify_game_coverage.py --all
    python scripts/validation/verify_game_coverage.py --season 2011 --detailed
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GameCoverageVerifier:
    """Verify game coverage by cross-referencing ESPN schedules with database."""

    # Season bounds for proper regular season filtering
    SEASON_BOUNDS = {
        2011: ("2011-12-25", "2012-04-26"),  # Lockout season
        2012: ("2012-10-30", "2013-04-17"),
        2013: ("2013-10-29", "2014-04-16"),
        2014: ("2014-10-28", "2015-04-15"),
        2015: ("2015-10-27", "2016-04-13"),
        2016: ("2016-10-25", "2017-04-12"),
        2017: ("2017-10-17", "2018-04-11"),
        2018: ("2018-10-16", "2019-04-10"),
        2019: ("2019-10-22", "2020-03-11"),  # COVID suspension (bubble separate)
        2020: ("2020-12-22", "2021-05-16"),  # COVID shortened
        2021: ("2021-10-19", "2022-04-10"),
        2022: ("2022-10-18", "2023-04-09"),
        2023: ("2023-10-24", "2024-04-14"),
    }

    # Expected regular season game counts
    EXPECTED_GAMES = {
        2011: 990,  # Lockout: 66 games × 30 teams / 2
        2019: 971,  # COVID interrupted (pre-shutdown)
        2020: 1080,  # COVID shortened: 72 games × 30 teams / 2
    }

    # NBA teams (30 teams)
    NBA_TEAMS = {
        "ATL",
        "BOS",
        "BKN",
        "CHA",
        "CHI",
        "CLE",
        "DAL",
        "DEN",
        "DET",
        "GS",
        "HOU",
        "IND",
        "LAC",
        "LAL",
        "MEM",
        "MIA",
        "MIL",
        "MIN",
        "NO",
        "NY",
        "OKC",
        "ORL",
        "PHI",
        "PHX",
        "POR",
        "SA",
        "SAC",
        "TOR",
        "UTAH",
        "WSH",
        "NJ",  # Old New Jersey Nets (pre-Brooklyn move)
    }

    def __init__(self, db_config: Dict[str, str] = None):
        """Initialize verifier with database and S3 connections."""
        self.db_config = db_config or self._load_db_config()
        self.s3_client = boto3.client("s3")
        self.s3_bucket = "nba-sim-raw-data-lake"

    def _load_db_config(self) -> Dict[str, str]:
        """Load database configuration from environment."""
        return {
            "dbname": os.getenv("POSTGRES_DB", "nba_simulator"),
            "user": os.getenv("POSTGRES_USER", "ryanranft"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    def get_db_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)

    def get_schedule_dates_for_season(self, season: int) -> List[str]:
        """Get all dates to check for a season (Oct 1 - Jun 30)."""
        if season not in self.SEASON_BOUNDS:
            # Default bounds
            start_date = datetime(season, 10, 1)
            end_date = datetime(season + 1, 6, 30)
        else:
            start_str, end_str = self.SEASON_BOUNDS[season]
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        return dates

    def load_schedule_from_s3(self, date_str: str) -> Dict:
        """Load schedule file from S3 for a given date."""
        key = f"espn_schedules/{date_str}.json"

        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except self.s3_client.exceptions.NoSuchKey:
            logger.debug(f"Schedule file not found: {key}")
            return None
        except Exception as e:
            logger.warning(f"Error loading {key}: {e}")
            return None

    def extract_completed_games(self, schedule_data: Dict, date_str: str) -> List[Dict]:
        """Extract completed games from schedule data."""
        if not schedule_data:
            return []

        completed_games = []

        try:
            events = (
                schedule_data.get("page", {})
                .get("content", {})
                .get("events", {})
                .get(date_str, [])
            )

            for event in events:
                # Check if game was completed
                completed = event.get("completed", False)
                status = event.get("status", {})
                state = status.get("state", "")
                detail = status.get("detail", "")

                # Game is completed if marked completed and status is post
                if completed and state == "post":
                    game_id = event.get("id")
                    competitors = event.get("competitors", [])

                    # Extract team info
                    home_team = None
                    away_team = None
                    for comp in competitors:
                        if comp.get("isHome"):
                            home_team = comp.get("abbrev")
                        else:
                            away_team = comp.get("abbrev")

                    completed_games.append(
                        {
                            "game_id": game_id,
                            "date": event.get("date"),
                            "status_detail": detail,
                            "home_team": home_team,
                            "away_team": away_team,
                            "completed": True,
                        }
                    )
        except Exception as e:
            logger.warning(f"Error parsing schedule for {date_str}: {e}")

        return completed_games

    def get_schedule_games_for_season(self, season: int) -> Dict[str, Dict]:
        """Get all completed games from schedules for a season."""
        logger.info(f"Loading schedule data for {season} season...")

        dates = self.get_schedule_dates_for_season(season)
        all_games = {}

        for i, date_str in enumerate(dates):
            if i % 30 == 0:
                logger.info(f"  Processing schedules: {i}/{len(dates)} dates...")

            schedule_data = self.load_schedule_from_s3(date_str)
            completed_games = self.extract_completed_games(schedule_data, date_str)

            for game in completed_games:
                game_id = game["game_id"]
                if game_id:
                    all_games[game_id] = game

        logger.info(f"  Found {len(all_games)} completed games in schedules")
        return all_games

    def get_database_games_for_season(self, season: int) -> Dict[str, Dict]:
        """Get all games from database for a season."""
        logger.info(f"Loading database games for {season} season...")

        query = """
        SELECT
            game_id,
            game_date,
            data->'teams'->'home'->>'abbreviation' as home_team,
            data->'teams'->'away'->>'abbreviation' as away_team,
            source
        FROM raw_data.nba_games
        WHERE season = %s
        ORDER BY game_date
        """

        games = {}
        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (season,))
                rows = cur.fetchall()

                for row in rows:
                    game_id = row["game_id"]
                    games[game_id] = {
                        "game_id": game_id,
                        "date": (
                            row["game_date"].isoformat() if row["game_date"] else None
                        ),
                        "home_team": row["home_team"],
                        "away_team": row["away_team"],
                        "source": row["source"],
                    }

        logger.info(f"  Found {len(games)} games in database")
        return games

    def filter_regular_season_games(
        self, games: Dict[str, Dict], season: int
    ) -> Dict[str, Dict]:
        """Filter games to only regular season (exclude preseason/playoffs)."""
        if season not in self.SEASON_BOUNDS:
            return games

        start_str, end_str = self.SEASON_BOUNDS[season]
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

        filtered = {}
        for game_id, game in games.items():
            # Parse game date
            if game.get("date"):
                try:
                    if isinstance(game["date"], str):
                        # Try ISO format first
                        if "T" in game["date"]:
                            game_date = datetime.fromisoformat(
                                game["date"].replace("Z", "+00:00")
                            ).date()
                        else:
                            game_date = datetime.strptime(
                                game["date"][:10], "%Y-%m-%d"
                            ).date()
                    else:
                        game_date = game["date"]

                    # Check if within regular season bounds
                    if start_date <= game_date <= end_date:
                        # Also filter for NBA teams only
                        home = game.get("home_team")
                        away = game.get("away_team")
                        if home in self.NBA_TEAMS and away in self.NBA_TEAMS:
                            filtered[game_id] = game
                except Exception as e:
                    logger.debug(f"Error parsing date for {game_id}: {e}")

        return filtered

    def analyze_season(self, season: int, detailed: bool = False) -> Dict:
        """Analyze game coverage for a single season."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing Season {season}")
        logger.info(f"{'='*60}")

        # Get schedule games
        schedule_games_all = self.get_schedule_games_for_season(season)
        schedule_games = self.filter_regular_season_games(schedule_games_all, season)

        # Get database games
        db_games_all = self.get_database_games_for_season(season)
        db_games = self.filter_regular_season_games(db_games_all, season)

        # Convert to sets for comparison
        schedule_ids = set(schedule_games.keys())
        db_ids = set(db_games.keys())

        # Find differences
        missing_ids = schedule_ids - db_ids  # In schedule but not in DB
        extra_ids = db_ids - schedule_ids  # In DB but not in schedule

        # Expected games
        expected = self.EXPECTED_GAMES.get(season, 1230)

        # Build result
        result = {
            "season": season,
            "season_label": f"{season}-{str(season+1)[-2:]}",
            "expected_games": expected,
            "schedule_games": len(schedule_games),
            "database_games": len(db_games),
            "missing_count": len(missing_ids),
            "extra_count": len(extra_ids),
            "missing_games": [],
            "extra_games": [],
            "team_summary": {},
        }

        # Add missing game details
        for game_id in sorted(missing_ids):
            game = schedule_games[game_id]
            result["missing_games"].append(
                {
                    "game_id": game_id,
                    "date": game.get("date"),
                    "home_team": game.get("home_team"),
                    "away_team": game.get("away_team"),
                    "status": game.get("status_detail"),
                }
            )

        # Add extra game details (likely playoffs/preseason)
        if detailed:
            for game_id in sorted(extra_ids):
                game = db_games[game_id]
                result["extra_games"].append(
                    {
                        "game_id": game_id,
                        "date": game.get("date"),
                        "home_team": game.get("home_team"),
                        "away_team": game.get("away_team"),
                        "source": game.get("source"),
                    }
                )

        # Team-level summary for missing games
        team_missing = defaultdict(list)
        for game_id in missing_ids:
            game = schedule_games[game_id]
            home = game.get("home_team")
            away = game.get("away_team")
            if home:
                team_missing[home].append(game_id)
            if away:
                team_missing[away].append(game_id)

        result["team_summary"] = {
            team: len(games) for team, games in sorted(team_missing.items())
        }

        # Print summary
        logger.info(f"\nResults:")
        logger.info(f"  Expected regular season games: {expected}")
        logger.info(f"  Schedule shows completed:      {len(schedule_games)}")
        logger.info(f"  Database has:                  {len(db_games)}")
        logger.info(f"  Missing from DB:               {len(missing_ids)} games")
        logger.info(f"  Extra in DB:                   {len(extra_ids)} games")

        if team_missing:
            logger.info(f"\nTeams affected by missing games:")
            for team in sorted(
                team_missing.keys(), key=lambda t: len(team_missing[t]), reverse=True
            )[:10]:
                count = len(team_missing[team])
                logger.info(f"    {team}: {count} games missing")

        return result

    def verify_seasons(self, seasons: List[int], detailed: bool = False) -> Dict:
        """Verify coverage for multiple seasons."""
        results = {}

        for season in seasons:
            try:
                results[season] = self.analyze_season(season, detailed=detailed)
            except Exception as e:
                logger.error(f"Error analyzing season {season}: {e}", exc_info=True)
                results[season] = {"error": str(e)}

        return results

    def generate_report(self, results: Dict, output_file: str = None):
        """Generate comprehensive coverage report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not output_file:
            output_file = f"game_coverage_report_{timestamp}.json"

        # Add metadata
        report = {
            "generated_at": timestamp,
            "total_seasons_analyzed": len(results),
            "seasons": results,
            "summary": {
                "total_missing_games": sum(
                    r.get("missing_count", 0)
                    for r in results.values()
                    if "error" not in r
                ),
                "seasons_with_gaps": [
                    season
                    for season, r in results.items()
                    if "error" not in r and r.get("missing_count", 0) > 0
                ],
            },
        }

        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"\nReport saved to: {output_path}")

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"Total seasons analyzed: {len(results)}")
        logger.info(f"Total missing games: {report['summary']['total_missing_games']}")
        logger.info(
            f"Seasons with gaps: {', '.join(map(str, report['summary']['seasons_with_gaps']))}"
        )

        return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify game coverage using ESPN schedules"
    )
    parser.add_argument(
        "--seasons",
        type=str,
        help="Comma-separated list of seasons (e.g., 2011,2012,2019)",
    )
    parser.add_argument(
        "--all", action="store_true", help="Verify all seasons with known gaps"
    )
    parser.add_argument("--season", type=int, help="Verify single season")
    parser.add_argument(
        "--detailed", action="store_true", help="Include detailed extra games info"
    )
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    # Determine which seasons to verify
    if args.all:
        seasons = [2011, 2012, 2015, 2017, 2018, 2019]
    elif args.season:
        seasons = [args.season]
    elif args.seasons:
        seasons = [int(s.strip()) for s in args.seasons.split(",")]
    else:
        # Default: seasons with known gaps
        seasons = [2011, 2019]

    logger.info(f"Verifying seasons: {seasons}")

    # Run verification
    verifier = GameCoverageVerifier()
    results = verifier.verify_seasons(seasons, detailed=args.detailed)

    # Generate report
    output_file = (
        args.output
        or f'game_coverage_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )
    report_path = verifier.generate_report(results, output_file)

    logger.info(f"\nVerification complete! Report: {report_path}")


if __name__ == "__main__":
    main()
