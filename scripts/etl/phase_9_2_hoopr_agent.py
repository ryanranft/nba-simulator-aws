#!/usr/bin/env python3
"""
9.0002 hoopR Processor Agent
Cross-validation with ESPN data, process hoopR play-by-play
Runs as background agent for comprehensive hoopR data processing
"""

import asyncio
import logging
import json
import time
import pandas as pd
import psycopg2
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
import os
import subprocess
from collections import defaultdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/phase_9_2_hoopr_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Phase9HoopRProcessorAgent:
    def __init__(
        self,
        output_dir="/tmp/phase_9_2_hoopr",
        config_file="config/scraper_config.yaml",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Database configuration
        self.db_config = {
            "host": "localhost",
            "database": "nba_simulator",
            "user": "postgres",
            "password": "password",
        }

        # Statistics
        self.stats = {
            "games_processed": 0,
            "plays_processed": 0,
            "cross_validations": 0,
            "discrepancies_found": 0,
            "start_time": datetime.now(),
        }

        # Processing metrics
        self.processing_metrics = {
            "games_by_season": defaultdict(int),
            "plays_by_game": defaultdict(int),
            "validation_results": defaultdict(int),
            "processing_times": defaultdict(float),
            "error_patterns": defaultdict(int),
        }

        logger.info("9.0002 hoopR Processor Agent initialized")
        logger.info(f"Output directory: {self.output_dir}")

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info("Connected to PostgreSQL database")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None

    async def load_hoopr_data(self, season: int) -> Optional[pd.DataFrame]:
        """Load hoopR play-by-play data for a specific season"""
        logger.info(f"Loading hoopR data for season {season}")

        try:
            # Use R script to load hoopR data
            r_script = f"""
            library(hoopR)
            library(dplyr)

            # Load play-by-play data for season
            pbp_data <- load_nba_pbp(season = {season})

            if (!is.null(pbp_data) && nrow(pbp_data) > 0) {{
                # Save to CSV for Python processing
                write.csv(pbp_data, "/tmp/hoopr_pbp_{season}.csv", row.names = FALSE)
                cat("SUCCESS: Loaded", nrow(pbp_data), "plays for season", {season})
            }} else {{
                cat("ERROR: No data found for season", {season})
            }}
            """

            # Write R script to temporary file
            r_script_file = f"/tmp/load_hoopr_{season}.R"
            with open(r_script_file, "w") as f:
                f.write(r_script)

            # Execute R script
            result = subprocess.run(
                ["Rscript", r_script_file], capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0 and "SUCCESS" in result.stdout:
                # Load the CSV file
                csv_file = f"/tmp/hoopr_pbp_{season}.csv"
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    logger.info(f"Loaded {len(df)} hoopR plays for season {season}")

                    # Clean up temporary files
                    os.remove(r_script_file)
                    os.remove(csv_file)

                    return df
                else:
                    logger.error(f"CSV file not created for season {season}")
                    return None
            else:
                logger.error(f"R script failed for season {season}: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Error loading hoopR data for season {season}: {e}")
            return None

    async def load_espn_data(self, season: int) -> Optional[pd.DataFrame]:
        """Load ESPN play-by-play data for comparison"""
        logger.info(f"Loading ESPN data for season {season}")

        try:
            conn = self.connect_to_database()
            if not conn:
                return None

            # Query ESPN data from database
            query = """
            SELECT game_id, play_id, period, clock, description,
                   team_id, player_id, score_home, score_away,
                   play_type, shot_type, shot_distance, shot_made
            FROM nba_plays
            WHERE season = %s
            ORDER BY game_id, play_id
            """

            df = pd.read_sql_query(query, conn, params=[season])
            conn.close()

            logger.info(f"Loaded {len(df)} ESPN plays for season {season}")
            return df

        except Exception as e:
            logger.error(f"Error loading ESPN data for season {season}: {e}")
            return None

    async def cross_validate_data(
        self, hoopr_df: pd.DataFrame, espn_df: pd.DataFrame, season: int
    ) -> Dict:
        """Cross-validate hoopR and ESPN data"""
        logger.info(f"Cross-validating data for season {season}")

        validation_results = {
            "season": season,
            "hoopr_games": 0,
            "espn_games": 0,
            "common_games": 0,
            "hoopr_plays": 0,
            "espn_plays": 0,
            "discrepancies": [],
            "validation_score": 0.0,
        }

        try:
            if hoopr_df is None or espn_df is None:
                logger.warning(
                    f"Incomplete data for season {season} - skipping validation"
                )
                return validation_results

            # Count games and plays
            hoopr_games = (
                hoopr_df["game_id"].nunique() if "game_id" in hoopr_df.columns else 0
            )
            espn_games = (
                espn_df["game_id"].nunique() if "game_id" in espn_df.columns else 0
            )

            validation_results["hoopr_games"] = hoopr_games
            validation_results["espn_games"] = espn_games
            validation_results["hoopr_plays"] = len(hoopr_df)
            validation_results["espn_plays"] = len(espn_df)

            # Find common games
            if "game_id" in hoopr_df.columns and "game_id" in espn_df.columns:
                hoopr_game_ids = set(hoopr_df["game_id"].unique())
                espn_game_ids = set(espn_df["game_id"].unique())
                common_games = hoopr_game_ids.intersection(espn_game_ids)

                validation_results["common_games"] = len(common_games)

                # Sample validation for common games
                if common_games:
                    sample_game = list(common_games)[0]

                    hoopr_sample = hoopr_df[hoopr_df["game_id"] == sample_game]
                    espn_sample = espn_df[espn_df["game_id"] == sample_game]

                    # Compare play counts
                    hoopr_plays = len(hoopr_sample)
                    espn_plays = len(espn_sample)

                    if abs(hoopr_plays - espn_plays) > 5:  # Allow some variance
                        discrepancy = {
                            "game_id": sample_game,
                            "hoopr_plays": hoopr_plays,
                            "espn_plays": espn_plays,
                            "difference": abs(hoopr_plays - espn_plays),
                        }
                        validation_results["discrepancies"].append(discrepancy)
                        self.stats["discrepancies_found"] += 1

            # Calculate validation score
            if hoopr_games > 0 and espn_games > 0:
                validation_results["validation_score"] = validation_results[
                    "common_games"
                ] / max(hoopr_games, espn_games)

            self.stats["cross_validations"] += 1
            logger.info(
                f"Cross-validation complete for season {season}: {validation_results['validation_score']:.2%} match"
            )

            return validation_results

        except Exception as e:
            logger.error(f"Error cross-validating season {season}: {e}")
            return validation_results

    async def process_season(self, season: int):
        """Process a complete season"""
        logger.info(f"Processing season {season}")

        start_time = time.time()

        try:
            # Load hoopR data
            hoopr_df = await self.load_hoopr_data(season)

            # Load ESPN data
            espn_df = await self.load_espn_data(season)

            # Cross-validate
            validation_results = await self.cross_validate_data(
                hoopr_df, espn_df, season
            )

            # Save results
            season_dir = self.output_dir / f"season_{season}"
            season_dir.mkdir(exist_ok=True)

            # Save hoopR data
            if hoopr_df is not None:
                hoopr_file = season_dir / f"hoopr_pbp_{season}.csv"
                hoopr_df.to_csv(hoopr_file, index=False)
                logger.info(f"Saved hoopR data to {hoopr_file}")

            # Save validation results
            validation_file = season_dir / f"validation_{season}.json"
            with open(validation_file, "w") as f:
                json.dump(validation_results, f, indent=2, default=str)

            # Update statistics
            processing_time = time.time() - start_time
            self.processing_metrics["games_by_season"][season] = validation_results[
                "hoopr_games"
            ]
            self.processing_metrics["plays_by_game"][season] = validation_results[
                "hoopr_plays"
            ]
            self.processing_metrics["processing_times"][season] = processing_time
            self.processing_metrics["validation_results"][season] = validation_results[
                "validation_score"
            ]

            self.stats["games_processed"] += validation_results["hoopr_games"]
            self.stats["plays_processed"] += validation_results["hoopr_plays"]

            logger.info(f"Season {season} processing complete: {processing_time:.2f}s")

        except Exception as e:
            logger.error(f"Error processing season {season}: {e}")
            self.processing_metrics["error_patterns"][str(e)] += 1

    def generate_processing_report(self) -> Dict:
        """Generate comprehensive processing report"""
        logger.info("Generating processing report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "games_processed": self.stats["games_processed"],
                "plays_processed": self.stats["plays_processed"],
                "cross_validations": self.stats["cross_validations"],
                "discrepancies_found": self.stats["discrepancies_found"],
                "processing_duration": str(datetime.now() - self.stats["start_time"]),
            },
            "processing_metrics": dict(self.processing_metrics),
            "recommendations": self._generate_recommendations(),
        }

        # Save report
        report_file = self.output_dir / "hoopr_processing_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Processing report saved to {report_file}")
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on processing results"""
        recommendations = []

        if self.stats["discrepancies_found"] > 0:
            recommendations.append(
                f"Investigate {self.stats['discrepancies_found']} data discrepancies"
            )

        if self.processing_metrics["error_patterns"]:
            recommendations.append(
                f"Address {len(self.processing_metrics['error_patterns'])} error patterns"
            )

        avg_validation_score = (
            sum(self.processing_metrics["validation_results"].values())
            / len(self.processing_metrics["validation_results"])
            if self.processing_metrics["validation_results"]
            else 0
        )
        if avg_validation_score < 0.8:
            recommendations.append("Improve data quality - validation score below 80%")

        return recommendations

    def log_progress(self):
        """Log current progress"""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("PHASE 9.2 HOOPR PROCESSOR AGENT PROGRESS")
        logger.info("=" * 60)
        logger.info(f"Games processed: {self.stats['games_processed']}")
        logger.info(f"Plays processed: {self.stats['plays_processed']}")
        logger.info(f"Cross-validations: {self.stats['cross_validations']}")
        logger.info(f"Discrepancies found: {self.stats['discrepancies_found']}")
        logger.info(f"Elapsed time: {elapsed}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution method"""
        logger.info("Starting 9.0002 hoopR Processor Agent")

        # Target seasons (recent seasons where hoopR data is most reliable)
        target_seasons = [2020, 2021, 2022, 2023, 2024, 2025]

        try:
            for season in target_seasons:
                await self.process_season(season)

                # Log progress after each season
                self.log_progress()

            # Generate final report
            report = self.generate_processing_report()

            logger.info("9.0002 hoopR Processor Agent completed successfully")
            logger.info(
                f"Report saved to: {self.output_dir}/hoopr_processing_report.json"
            )

        except Exception as e:
            logger.error(f"9.0002 hoopR Processor Agent failed: {e}")


def main():
    """Main entry point"""
    agent = Phase9HoopRProcessorAgent()

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("9.0002 hoopR Processor Agent interrupted by user")
    except Exception as e:
        logger.error(f"9.0002 hoopR Processor Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
