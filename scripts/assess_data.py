#!/usr/bin/env python3
"""
NBA Database Data Assessment Script
Checks data completeness, quality, and availability across all eras (1946-2025)
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBADataAssessor:
    """Comprehensive data assessment for NBA database"""

    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.results = {
            "assessment_date": datetime.now().isoformat(),
            "database_info": {},
            "tables": {},
            "seasons": {},
            "eras": {},
            "summary": {},
            "issues": [],
        }

    def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("RDS_HOST"),
                port=os.getenv("RDS_PORT", 5432),
                database=os.getenv("RDS_DATABASE"),
                user=os.getenv("RDS_USERNAME"),
                password=os.getenv("RDS_PASSWORD"),
            )
            logger.info("Connected to database successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.results["issues"].append(f"Database connection failed: {e}")
            return False

    def assess_database_info(self):
        """Get basic database information"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get database size
                cur.execute(
                    """
                    SELECT pg_database.datname as database_name,
                           pg_size_pretty(pg_database_size(pg_database.datname)) as size
                    FROM pg_database
                    WHERE datname = %s
                """,
                    (os.getenv("RDS_DATABASE"),),
                )
                db_info = cur.fetchone()

                self.results["database_info"] = {
                    "name": db_info["database_name"],
                    "size": db_info["size"],
                }

                logger.info(f"Database: {db_info['database_name']} ({db_info['size']})")

        except Exception as e:
            logger.error(f"Failed to assess database info: {e}")
            self.results["issues"].append(f"Database info assessment failed: {e}")

    def get_all_tables(self) -> List[str]:
        """Get list of all tables in database"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """
                )
                tables = [row[0] for row in cur.fetchall()]
                logger.info(f"Found {len(tables)} tables")
                return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    def assess_table(self, table_name: str) -> Dict[str, Any]:
        """Assess a single table"""
        assessment = {
            "name": table_name,
            "exists": True,
            "row_count": 0,
            "size": None,
            "columns": [],
            "has_season_column": False,
            "season_coverage": {},
            "issues": [],
        }

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get row count
                cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                assessment["row_count"] = cur.fetchone()["count"]

                # Get table size
                cur.execute(
                    """
                    SELECT pg_size_pretty(pg_total_relation_size(%s)) as size
                """,
                    (table_name,),
                )
                assessment["size"] = cur.fetchone()["size"]

                # Get columns
                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """,
                    (table_name,),
                )
                columns = cur.fetchall()
                assessment["columns"] = [
                    {"name": col["column_name"], "type": col["data_type"]}
                    for col in columns
                ]

                # Check for season column
                column_names = [col["column_name"] for col in columns]
                assessment["has_season_column"] = "season" in column_names

                # If has season, analyze coverage
                if assessment["has_season_column"]:
                    cur.execute(
                        f"""
                        SELECT season, COUNT(*) as count
                        FROM {table_name}
                        GROUP BY season
                        ORDER BY season
                    """
                    )
                    seasons = cur.fetchall()
                    assessment["season_coverage"] = {
                        row["season"]: row["count"] for row in seasons
                    }
                    assessment["season_range"] = {
                        "min": (
                            min(seasons, key=lambda x: x["season"])["season"]
                            if seasons
                            else None
                        ),
                        "max": (
                            max(seasons, key=lambda x: x["season"])["season"]
                            if seasons
                            else None
                        ),
                        "total_seasons": len(seasons),
                    }

                logger.info(
                    f"✓ {table_name}: {assessment['row_count']:,} rows ({assessment['size']})"
                )

        except Exception as e:
            logger.error(f"Failed to assess table {table_name}: {e}")
            assessment["issues"].append(str(e))

        return assessment

    def analyze_season_completeness(self):
        """Analyze data completeness by season across all tables"""
        season_data = defaultdict(
            lambda: {
                "games": 0,
                "players": 0,
                "box_scores": 0,
                "play_by_play": 0,
                "advanced_stats": 0,
            }
        )

        try:
            # Games by season
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT season, COUNT(*) as count
                    FROM games
                    GROUP BY season
                    ORDER BY season
                """
                )
                for row in cur.fetchall():
                    season_data[row["season"]]["games"] = row["count"]

                # Box score players by season
                cur.execute(
                    """
                    SELECT season, COUNT(*) as count
                    FROM box_score_players
                    GROUP BY season
                    ORDER BY season
                """
                )
                for row in cur.fetchall():
                    season_data[row["season"]]["box_scores"] = row["count"]

                # Check for play_by_play table
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'play_by_play'
                    )
                """
                )
                has_pbp = cur.fetchone()[0]

                if has_pbp:
                    cur.execute(
                        """
                        SELECT season, COUNT(*) as count
                        FROM play_by_play
                        GROUP BY season
                        ORDER BY season
                    """
                    )
                    for row in cur.fetchall():
                        season_data[row["season"]]["play_by_play"] = row["count"]

            self.results["seasons"] = dict(season_data)
            logger.info(f"Analyzed {len(season_data)} seasons")

        except Exception as e:
            logger.error(f"Failed to analyze season completeness: {e}")
            self.results["issues"].append(f"Season analysis failed: {e}")

    def analyze_eras(self):
        """Analyze data availability by era"""
        eras = {
            "early_era": {"years": "1946-1960", "seasons": [], "quality": "minimal"},
            "box_score_era": {
                "years": "1960-1990",
                "seasons": [],
                "quality": "enhanced",
            },
            "pbp_era": {"years": "1990-2025", "seasons": [], "quality": "detailed"},
        }

        for season, data in self.results.get("seasons", {}).items():
            # Parse season (e.g., "2023-24" -> 2023)
            try:
                year = int(season.split("-")[0])

                if 1946 <= year < 1960:
                    eras["early_era"]["seasons"].append(season)
                elif 1960 <= year < 1990:
                    eras["box_score_era"]["seasons"].append(season)
                elif 1990 <= year <= 2025:
                    eras["pbp_era"]["seasons"].append(season)

            except (ValueError, IndexError):
                continue

        # Calculate era statistics
        for era_name, era_data in eras.items():
            era_data["season_count"] = len(era_data["seasons"])

            # Check data availability
            if era_data["seasons"]:
                total_games = sum(
                    self.results["seasons"].get(s, {}).get("games", 0)
                    for s in era_data["seasons"]
                )
                total_pbp = sum(
                    self.results["seasons"].get(s, {}).get("play_by_play", 0)
                    for s in era_data["seasons"]
                )

                era_data["total_games"] = total_games
                era_data["total_pbp_events"] = total_pbp
                era_data["pbp_coverage"] = (
                    (total_pbp / total_games) if total_games > 0 else 0
                )

        self.results["eras"] = eras

        for era_name, era_data in eras.items():
            logger.info(
                f"{era_name}: {era_data['season_count']} seasons, "
                f"{era_data.get('total_games', 0):,} games"
            )

    def generate_summary(self):
        """Generate overall summary statistics"""
        summary = {
            "total_tables": len(self.results["tables"]),
            "total_rows": sum(
                t.get("row_count", 0) for t in self.results["tables"].values()
            ),
            "total_seasons": len(self.results.get("seasons", {})),
            "season_range": {},
            "data_quality": {},
        }

        # Season range
        if self.results.get("seasons"):
            seasons = list(self.results["seasons"].keys())
            summary["season_range"] = {
                "earliest": min(seasons),
                "latest": max(seasons),
                "total": len(seasons),
            }

        # Data quality metrics
        total_games = sum(s.get("games", 0) for s in self.results["seasons"].values())
        total_box_scores = sum(
            s.get("box_scores", 0) for s in self.results["seasons"].values()
        )
        total_pbp = sum(
            s.get("play_by_play", 0) for s in self.results["seasons"].values()
        )

        summary["data_quality"] = {
            "total_games": total_games,
            "total_box_scores": total_box_scores,
            "total_pbp_events": total_pbp,
            "box_score_coverage": (
                (total_box_scores / total_games) if total_games > 0 else 0
            ),
            "pbp_coverage": (total_pbp / total_games) if total_games > 0 else 0,
        }

        # Identify missing data
        expected_tables = [
            "games",
            "players",
            "teams",
            "box_score_players",
            "box_score_teams",
            "play_by_play",
            "player_game_stats",
            "team_game_stats",
        ]

        missing_tables = [t for t in expected_tables if t not in self.results["tables"]]
        if missing_tables:
            summary["missing_tables"] = missing_tables
            self.results["issues"].append(
                f"Missing tables: {', '.join(missing_tables)}"
            )

        self.results["summary"] = summary

        logger.info(f"\nSummary:")
        logger.info(f"  Total Tables: {summary['total_tables']}")
        logger.info(f"  Total Rows: {summary['total_rows']:,}")
        logger.info(f"  Total Seasons: {summary['total_seasons']}")
        logger.info(f"  Total Games: {summary['data_quality']['total_games']:,}")
        logger.info(
            f"  Box Score Coverage: {summary['data_quality']['box_score_coverage']:.1%}"
        )
        logger.info(f"  PBP Coverage: {summary['data_quality']['pbp_coverage']:.1%}")

    def run_assessment(self) -> Dict[str, Any]:
        """Run complete data assessment"""
        logger.info("Starting NBA Database Assessment...")
        logger.info("=" * 80)

        if not self.connect():
            return self.results

        try:
            # 1. Database info
            logger.info("\n1. Assessing database info...")
            self.assess_database_info()

            # 2. Get all tables
            logger.info("\n2. Discovering tables...")
            tables = self.get_all_tables()

            # 3. Assess each table
            logger.info("\n3. Assessing tables...")
            for table in tables:
                assessment = self.assess_table(table)
                self.results["tables"][table] = assessment

            # 4. Analyze season completeness
            logger.info("\n4. Analyzing season completeness...")
            self.analyze_season_completeness()

            # 5. Analyze eras
            logger.info("\n5. Analyzing eras...")
            self.analyze_eras()

            # 6. Generate summary
            logger.info("\n6. Generating summary...")
            self.generate_summary()

            logger.info("\n" + "=" * 80)
            logger.info("Assessment complete!")

            if self.results["issues"]:
                logger.warning(f"\nFound {len(self.results['issues'])} issues:")
                for issue in self.results["issues"]:
                    logger.warning(f"  - {issue}")

        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            self.results["issues"].append(f"Assessment failed: {e}")

        finally:
            if self.conn:
                self.conn.close()
                logger.info("Database connection closed")

        return self.results

    def save_results(self, output_file: str):
        """Save assessment results to JSON file"""
        try:
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"\nResults saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="NBA Database Data Assessment")
    parser.add_argument(
        "--output",
        default="data_assessment.json",
        help="Output file for assessment results (default: data_assessment.json)",
    )

    args = parser.parse_args()

    # Run assessment
    assessor = NBADataAssessor()
    results = assessor.run_assessment()

    # Save results
    assessor.save_results(args.output)

    # Print summary
    print("\n" + "=" * 80)
    print("ASSESSMENT SUMMARY")
    print("=" * 80)

    summary = results.get("summary", {})
    print(f"\nDatabase: {results.get('database_info', {}).get('name', 'Unknown')}")
    print(f"Size: {results.get('database_info', {}).get('size', 'Unknown')}")
    print(f"\nTables: {summary.get('total_tables', 0)}")
    print(f"Total Rows: {summary.get('total_rows', 0):,}")
    print(f"Total Seasons: {summary.get('total_seasons', 0)}")

    if summary.get("season_range"):
        print(
            f"Season Range: {summary['season_range'].get('earliest')} to {summary['season_range'].get('latest')}"
        )

    if summary.get("data_quality"):
        dq = summary["data_quality"]
        print(f"\nData Quality:")
        print(f"  Games: {dq.get('total_games', 0):,}")
        print(f"  Box Scores: {dq.get('total_box_scores', 0):,}")
        print(f"  PBP Events: {dq.get('total_pbp_events', 0):,}")
        print(f"  Box Score Coverage: {dq.get('box_score_coverage', 0):.1%}")
        print(f"  PBP Coverage: {dq.get('pbp_coverage', 0):.1%}")

    if results.get("issues"):
        print(f"\n⚠️  Issues Found: {len(results['issues'])}")
        for issue in results["issues"][:5]:  # Show first 5
            print(f"  - {issue}")
        if len(results["issues"]) > 5:
            print(f"  ... and {len(results['issues']) - 5} more")
    else:
        print("\n✅ No issues found")

    print("\n" + "=" * 80)
    print(f"Full results saved to: {args.output}")
    print("=" * 80)


if __name__ == "__main__":
    main()
