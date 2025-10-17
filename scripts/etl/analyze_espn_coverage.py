#!/usr/bin/env python3
"""
ESPN Coverage Analysis Script

Analyzes the loaded ESPN PBP data to generate accurate coverage reports.
Queries PostgreSQL to determine actual vs expected games per season.

This script addresses the 106.2% coverage issue by:
1. Using correct NBA season logic
2. Only counting NBA games (30 teams)
3. Calculating accurate coverage percentages
4. Identifying missing games for targeted scraping
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/espn_coverage_analysis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        dbname=os.getenv("RDS_DB_NAME", "nba_simulator"),
        user=os.getenv("RDS_USERNAME", "ryanranft"),
        password=os.getenv("RDS_PASSWORD"),
        host=os.getenv("RDS_HOSTNAME", "localhost"),
        port=os.getenv("RDS_PORT", "5432"),
    )


def get_season_statistics() -> List[Dict]:
    """Get games by season from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT season,
                           COUNT(*) as game_count,
                           COUNT(DISTINCT home_team) as unique_home_teams,
                           COUNT(DISTINCT away_team) as unique_away_teams,
                           MIN(game_date) as season_start,
                           MAX(game_date) as season_end,
                           AVG(final_score_home) as avg_home_score,
                           AVG(final_score_away) as avg_away_score
                    FROM master.nba_games
                    GROUP BY season
                    ORDER BY season
                """
                )

                return [dict(row) for row in cur.fetchall()]

    except Exception as e:
        logger.error(f"Error getting season statistics: {e}")
        raise


def get_team_statistics() -> List[Dict]:
    """Get games by team from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    WITH team_games AS (
                        SELECT season, home_team as team, COUNT(*) as home_games
                        FROM master.nba_games
                        GROUP BY season, home_team
                        UNION ALL
                        SELECT season, away_team as team, COUNT(*) as away_games
                        FROM master.nba_games
                        GROUP BY season, away_team
                    )
                    SELECT season, team, SUM(home_games) as total_games
                    FROM team_games
                    GROUP BY season, team
                    ORDER BY season, team
                """
                )

                return [dict(row) for row in cur.fetchall()]

    except Exception as e:
        logger.error(f"Error getting team statistics: {e}")
        raise


def get_play_statistics() -> List[Dict]:
    """Get play statistics by season"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT g.season,
                           COUNT(DISTINCT g.game_id) as games_with_plays,
                           COUNT(p.id) as total_plays,
                           AVG(play_counts.plays_per_game) as avg_plays_per_game
                    FROM master.nba_games g
                    LEFT JOIN master.nba_plays p ON g.game_id = p.game_id
                    LEFT JOIN (
                        SELECT game_id, COUNT(*) as plays_per_game
                        FROM master.nba_plays
                        GROUP BY game_id
                    ) play_counts ON g.game_id = play_counts.game_id
                    GROUP BY g.season
                    ORDER BY g.season
                """
                )

                return [dict(row) for row in cur.fetchall()]

    except Exception as e:
        logger.error(f"Error getting play statistics: {e}")
        raise


def calculate_expected_games(season: str) -> int:
    """Calculate expected number of games for a season"""
    # NBA regular season: 82 games × 30 teams / 2 = 1,230 games
    # Playoffs: ~80-90 games (varies by year)
    # Total per season: ~1,310-1,320 games

    if season == "2020-21":
        # COVID shortened season
        return 1080
    elif season == "2011-12":
        # Lockout shortened season
        return 990
    elif season < "2020-21":
        # Normal seasons before COVID
        return 1320
    else:
        # Normal seasons
        return 1320


def analyze_coverage() -> Dict:
    """Analyze coverage and generate report"""
    logger.info("Analyzing ESPN PBP data coverage...")

    # Get statistics
    season_stats = get_season_statistics()
    team_stats = get_team_statistics()
    play_stats = get_play_statistics()

    # Create coverage report
    report = {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_seasons": len(season_stats),
        "season_analysis": {},
        "overall_statistics": {
            "total_games": sum(s["game_count"] for s in season_stats),
            "total_plays": sum(p["total_plays"] for p in play_stats),
            "avg_plays_per_game": 0,
        },
        "coverage_summary": {
            "seasons_with_complete_data": 0,
            "seasons_with_partial_data": 0,
            "seasons_with_no_data": 0,
        },
    }

    # Analyze each season
    total_games = 0
    total_plays = 0

    for season_stat in season_stats:
        season = season_stat["season"]
        actual_games = season_stat["game_count"]
        expected_games = calculate_expected_games(season)
        coverage_pct = (
            (actual_games / expected_games * 100) if expected_games > 0 else 0
        )

        # Get play stats for this season
        play_stat = next((p for p in play_stats if p["season"] == season), {})

        season_analysis = {
            "actual_games": actual_games,
            "expected_games": expected_games,
            "coverage_percentage": round(coverage_pct, 1),
            "games_missing": max(0, expected_games - actual_games),
            "unique_teams": max(
                season_stat["unique_home_teams"], season_stat["unique_away_teams"]
            ),
            "season_start": (
                season_stat["season_start"].isoformat()
                if season_stat["season_start"]
                else None
            ),
            "season_end": (
                season_stat["season_end"].isoformat()
                if season_stat["season_end"]
                else None
            ),
            "total_plays": play_stat.get("total_plays", 0),
            "avg_plays_per_game": round(play_stat.get("avg_plays_per_game", 0), 1),
            "avg_home_score": round(season_stat["avg_home_score"], 1),
            "avg_away_score": round(season_stat["avg_away_score"], 1),
        }

        report["season_analysis"][season] = season_analysis

        total_games += actual_games
        total_plays += play_stat.get("total_plays", 0)

        # Categorize coverage
        if coverage_pct >= 95:
            report["coverage_summary"]["seasons_with_complete_data"] += 1
        elif coverage_pct >= 50:
            report["coverage_summary"]["seasons_with_partial_data"] += 1
        else:
            report["coverage_summary"]["seasons_with_no_data"] += 1

    # Calculate overall statistics
    report["overall_statistics"]["total_games"] = total_games
    report["overall_statistics"]["total_plays"] = total_plays
    if total_games > 0:
        report["overall_statistics"]["avg_plays_per_game"] = round(
            total_plays / total_games, 1
        )

    # Analyze team coverage
    team_coverage = {}
    for team_stat in team_stats:
        season = team_stat["season"]
        team = team_stat["team"]
        games = team_stat["total_games"]

        if season not in team_coverage:
            team_coverage[season] = {}

        team_coverage[season][team] = games

    report["team_coverage"] = team_coverage

    # Identify missing games
    missing_games = {}
    for season, analysis in report["season_analysis"].items():
        if analysis["games_missing"] > 0:
            missing_games[season] = {
                "games_missing": analysis["games_missing"],
                "coverage_percentage": analysis["coverage_percentage"],
            }

    report["missing_games"] = missing_games

    return report


def save_coverage_report(report: Dict, output_file: Path):
    """Save coverage report to JSON file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Coverage report saved to {output_file}")


def save_missing_games_report(report: Dict, output_file: Path):
    """Save missing games report to JSON file"""
    missing_games = report.get("missing_games", {})

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(missing_games, f, indent=2, default=str)

    logger.info(f"Missing games report saved to {output_file}")


def print_summary(report: Dict):
    """Print coverage summary to console"""
    logger.info("=" * 80)
    logger.info("ESPN PBP DATA COVERAGE ANALYSIS")
    logger.info("=" * 80)

    # Overall statistics
    overall = report["overall_statistics"]
    logger.info(f"Total games: {overall['total_games']:,}")
    logger.info(f"Total plays: {overall['total_plays']:,}")
    logger.info(f"Average plays per game: {overall['avg_plays_per_game']}")

    # Coverage summary
    coverage = report["coverage_summary"]
    logger.info(f"\nCoverage Summary:")
    logger.info(
        f"  Complete data (≥95%): {coverage['seasons_with_complete_data']} seasons"
    )
    logger.info(
        f"  Partial data (50-94%): {coverage['seasons_with_partial_data']} seasons"
    )
    logger.info(f"  No data (<50%): {coverage['seasons_with_no_data']} seasons")

    # Season breakdown
    logger.info(f"\nSeason Breakdown:")
    logger.info(
        f"{'Season':<10} {'Games':<8} {'Expected':<10} {'Coverage':<10} {'Missing':<8} {'Plays':<8} {'Avg/Game':<8}"
    )
    logger.info("-" * 80)

    for season in sorted(report["season_analysis"].keys()):
        analysis = report["season_analysis"][season]
        logger.info(
            f"{season:<10} {analysis['actual_games']:<8} {analysis['expected_games']:<10} "
            f"{analysis['coverage_percentage']:<9}% {analysis['games_missing']:<8} "
            f"{analysis['total_plays']:<8} {analysis['avg_plays_per_game']:<8}"
        )

    # Missing games
    missing_games = report.get("missing_games", {})
    if missing_games:
        logger.info(f"\nMissing Games by Season:")
        for season, missing in missing_games.items():
            logger.info(
                f"  {season}: {missing['games_missing']} games missing "
                f"({missing['coverage_percentage']}% coverage)"
            )
    else:
        logger.info(f"\nNo missing games identified - all seasons have complete data!")

    # Team analysis
    logger.info(f"\nTeam Coverage Analysis:")
    for season in sorted(report["team_coverage"].keys()):
        team_games = report["team_coverage"][season]
        teams_with_82_games = sum(1 for games in team_games.values() if games >= 82)
        total_teams = len(team_games)

        logger.info(
            f"  {season}: {teams_with_82_games}/{total_teams} teams with ≥82 games"
        )


def main():
    parser = argparse.ArgumentParser(description="Analyze ESPN PBP data coverage")
    parser.add_argument(
        "--output",
        type=str,
        default="data/espn_coverage_report.json",
        help="Output JSON file for coverage report",
    )
    parser.add_argument(
        "--missing-output",
        type=str,
        default="data/espn_missing_games.json",
        help="Output JSON file for missing games report",
    )

    args = parser.parse_args()

    output_file = Path(args.output)
    missing_output_file = Path(args.missing_output)

    # Check database connection
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM master.nba_games")
                game_count = cur.fetchone()[0]
                logger.info(f"Found {game_count:,} games in database")

                if game_count == 0:
                    logger.error(
                        "No games found in database. Run load_validated_espn_pbp.py first."
                    )
                    sys.exit(1)

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

    # Analyze coverage
    try:
        report = analyze_coverage()
    except Exception as e:
        logger.error(f"Error analyzing coverage: {e}")
        sys.exit(1)

    # Save reports
    save_coverage_report(report, output_file)
    save_missing_games_report(report, missing_output_file)

    # Print summary
    print_summary(report)

    logger.info(f"\nAnalysis complete!")
    logger.info(f"Coverage report: {output_file}")
    logger.info(f"Missing games report: {missing_output_file}")


if __name__ == "__main__":
    main()
