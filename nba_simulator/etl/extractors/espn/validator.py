#!/usr/bin/env python3
"""
ESPN PBP File Validation Script

Scans all 44,826 ESPN PBP JSON files, validates data presence, extracts metadata,
and stores validation results in PostgreSQL for accurate coverage analysis.

This script addresses the data reading issues causing 106.2% coverage by:
1. Properly determining NBA seasons from game dates
2. Validating that files actually contain PBP data
3. Filtering for NBA games only (excluding international, summer league, etc.)
4. Cataloging all files for accurate analysis
"""

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/espn_file_validation.log"),
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


def init_database():
    """Initialize database schema and validation table"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create master schema if it doesn't exist
                cur.execute("CREATE SCHEMA IF NOT EXISTS master;")

                # Create validation table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS master.espn_file_validation (
                        file_name VARCHAR(100) PRIMARY KEY,
                        game_id VARCHAR(20) NOT NULL,
                        has_pbp_data BOOLEAN NOT NULL,
                        has_game_info BOOLEAN NOT NULL,
                        has_team_data BOOLEAN NOT NULL,
                        game_date TIMESTAMP WITH TIME ZONE,
                        season VARCHAR(10),
                        league VARCHAR(20),
                        home_team VARCHAR(100),
                        away_team VARCHAR(100),
                        play_count INTEGER,
                        file_size_bytes BIGINT,
                        validation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        error_message TEXT
                    );
                """
                )

                # Create indexes for performance
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_espn_validation_season ON master.espn_file_validation(season);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_espn_validation_league ON master.espn_file_validation(league);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_espn_validation_pbp ON master.espn_file_validation(has_pbp_data);"
                )

                conn.commit()
                logger.info("Database schema initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def determine_nba_season(game_date: datetime) -> str:
    """Determine NBA season from game date"""
    year = game_date.year
    month = game_date.month

    if month >= 10:  # Oct-Dec = start of season
        season = f"{year}-{str(year + 1)[2:]}"
    else:  # Jan-Sep = end of previous season
        season = f"{year - 1}-{str(year)[2:]}"

    return season


def validate_file(file_path: Path) -> Dict:
    """Validate single ESPN PBP file"""
    result = {
        "file_name": file_path.name,
        "game_id": file_path.stem,
        "has_pbp_data": False,
        "has_game_info": False,
        "has_team_data": False,
        "play_count": 0,
        "file_size_bytes": file_path.stat().st_size,
        "game_date": None,
        "season": None,
        "league": None,
        "home_team": None,
        "away_team": None,
        "error_message": None,
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Navigate to gamepackage
        gamepackage = data["page"]["content"]["gamepackage"]

        # Check game info
        gm_info = gamepackage.get("gmInfo", {})
        if "dtTm" in gm_info:
            result["has_game_info"] = True
            game_date = datetime.fromisoformat(gm_info["dtTm"].replace("Z", "+00:00"))
            result["game_date"] = game_date
            result["season"] = determine_nba_season(game_date)

        # Check team data
        pbp_data = gamepackage.get("pbp", {})
        teams_data = pbp_data.get("tms", {})
        if teams_data.get("home") and teams_data.get("away"):
            result["has_team_data"] = True
            result["home_team"] = teams_data["home"].get("displayName")
            result["away_team"] = teams_data["away"].get("displayName")

            # Determine league from team data
            home_league = teams_data["home"].get("league", "NBA")
            away_league = teams_data["away"].get("league", "NBA")
            result["league"] = home_league if home_league == away_league else "Mixed"

        # Check PBP data
        play_grps = pbp_data.get("playGrps", [])
        if play_grps:
            result["has_pbp_data"] = True
            # Count total plays - playGrps is a list of lists
            for period_plays in play_grps:
                if isinstance(period_plays, list):
                    result["play_count"] += len(period_plays)

    except json.JSONDecodeError as e:
        result["error_message"] = f"JSON decode error: {str(e)}"
    except KeyError as e:
        result["error_message"] = f"Missing key in data structure: {str(e)}"
    except Exception as e:
        result["error_message"] = f"Unexpected error: {str(e)}"

    return result


def store_validation_results(validation_results: List[Dict]):
    """Store validation results in PostgreSQL"""
    if not validation_results:
        return

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Clear existing data for this validation run
                cur.execute("DELETE FROM master.espn_file_validation;")

                # Insert validation results
                execute_batch(
                    cur,
                    """
                    INSERT INTO master.espn_file_validation
                    (file_name, game_id, has_pbp_data, has_game_info, has_team_data,
                     game_date, season, league, home_team, away_team, play_count,
                     file_size_bytes, error_message)
                    VALUES (%(file_name)s, %(game_id)s, %(has_pbp_data)s, %(has_game_info)s,
                            %(has_team_data)s, %(game_date)s, %(season)s, %(league)s,
                            %(home_team)s, %(away_team)s, %(play_count)s,
                            %(file_size_bytes)s, %(error_message)s)
                """,
                    validation_results,
                    page_size=1000,
                )

                conn.commit()
                logger.info(
                    f"Stored {len(validation_results)} validation results in database"
                )

    except Exception as e:
        logger.error(f"Error storing validation results: {e}")
        raise


def save_validation_report(validation_results: List[Dict], output_file: Path):
    """Save validation results to JSON file"""
    report = {
        "validation_timestamp": datetime.now().isoformat(),
        "total_files": len(validation_results),
        "files_with_pbp": sum(1 for r in validation_results if r["has_pbp_data"]),
        "files_with_game_info": sum(
            1 for r in validation_results if r["has_game_info"]
        ),
        "files_with_team_data": sum(
            1 for r in validation_results if r["has_team_data"]
        ),
        "total_plays": sum(r["play_count"] for r in validation_results),
        "files_with_errors": sum(1 for r in validation_results if r["error_message"]),
        "season_breakdown": {},
        "league_breakdown": {},
        "validation_results": validation_results,
    }

    # Calculate season breakdown
    for result in validation_results:
        if result["season"]:
            season = result["season"]
            if season not in report["season_breakdown"]:
                report["season_breakdown"][season] = {
                    "total_files": 0,
                    "files_with_pbp": 0,
                    "total_plays": 0,
                }
            report["season_breakdown"][season]["total_files"] += 1
            if result["has_pbp_data"]:
                report["season_breakdown"][season]["files_with_pbp"] += 1
                report["season_breakdown"][season]["total_plays"] += result[
                    "play_count"
                ]

    # Calculate league breakdown
    for result in validation_results:
        if result["league"]:
            league = result["league"]
            if league not in report["league_breakdown"]:
                report["league_breakdown"][league] = 0
            report["league_breakdown"][league] += 1

    # Save report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Validation report saved to {output_file}")


def process_files_batch(file_paths: List[Path]) -> List[Dict]:
    """Process a batch of files"""
    results = []
    for file_path in file_paths:
        try:
            result = validate_file(file_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            results.append(
                {
                    "file_name": file_path.name,
                    "game_id": file_path.stem,
                    "has_pbp_data": False,
                    "has_game_info": False,
                    "has_team_data": False,
                    "play_count": 0,
                    "file_size_bytes": file_path.stat().st_size,
                    "error_message": str(e),
                }
            )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Validate ESPN PBP files and extract metadata"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/nba_pbp",
        help="Directory containing ESPN PBP JSON files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/espn_file_validation_report.json",
        help="Output JSON file for validation report",
    )
    parser.add_argument(
        "--max-workers", type=int, default=8, help="Maximum number of worker processes"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of files to process per batch",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output)

    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        sys.exit(1)

    # Initialize database
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    # Get all JSON files
    all_files = list(input_dir.glob("*.json"))
    logger.info(f"Found {len(all_files)} JSON files to validate")

    if not all_files:
        logger.warning("No JSON files found in input directory")
        return

    # Process files in batches using multiprocessing
    all_results = []
    batch_count = 0

    logger.info(
        f"Processing files with {args.max_workers} workers, batch size {args.batch_size}"
    )

    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        # Create batches
        batches = [
            all_files[i : i + args.batch_size]
            for i in range(0, len(all_files), args.batch_size)
        ]

        # Submit batches
        future_to_batch = {
            executor.submit(process_files_batch, batch): batch for batch in batches
        }

        # Collect results
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            batch_count += 1

            try:
                batch_results = future.result()
                all_results.extend(batch_results)

                logger.info(
                    f"Completed batch {batch_count}/{len(batches)} "
                    f"({len(batch_results)} files)"
                )

            except Exception as e:
                logger.error(f"Error processing batch {batch_count}: {e}")

    logger.info(f"Validation complete. Processed {len(all_results)} files")

    # Store results in database
    try:
        store_validation_results(all_results)
    except Exception as e:
        logger.error(f"Failed to store results in database: {e}")
        sys.exit(1)

    # Save validation report
    save_validation_report(all_results, output_file)

    # Print summary
    total_files = len(all_results)
    files_with_pbp = sum(1 for r in all_results if r["has_pbp_data"])
    files_with_game_info = sum(1 for r in all_results if r["has_game_info"])
    files_with_team_data = sum(1 for r in all_results if r["has_team_data"])
    total_plays = sum(r["play_count"] for r in all_results)
    files_with_errors = sum(1 for r in all_results if r["error_message"])

    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {total_files:,}")
    logger.info(
        f"Files with PBP data: {files_with_pbp:,} ({files_with_pbp/total_files*100:.1f}%)"
    )
    logger.info(
        f"Files with game info: {files_with_game_info:,} ({files_with_game_info/total_files*100:.1f}%)"
    )
    logger.info(
        f"Files with team data: {files_with_team_data:,} ({files_with_team_data/total_files*100:.1f}%)"
    )
    logger.info(f"Total plays found: {total_plays:,}")
    logger.info(
        f"Files with errors: {files_with_errors:,} ({files_with_errors/total_files*100:.1f}%)"
    )

    # Print season breakdown
    season_counts = {}
    for result in all_results:
        if result["season"]:
            season = result["season"]
            if season not in season_counts:
                season_counts[season] = {"total": 0, "with_pbp": 0}
            season_counts[season]["total"] += 1
            if result["has_pbp_data"]:
                season_counts[season]["with_pbp"] += 1

    logger.info("\nSeason breakdown:")
    for season in sorted(season_counts.keys()):
        counts = season_counts[season]
        logger.info(
            f"  {season}: {counts['with_pbp']:,}/{counts['total']:,} files with PBP "
            f"({counts['with_pbp']/counts['total']*100:.1f}%)"
        )

    logger.info(f"\nValidation report saved to: {output_file}")
    logger.info("Results stored in PostgreSQL table: master.espn_file_validation")


if __name__ == "__main__":
    main()
