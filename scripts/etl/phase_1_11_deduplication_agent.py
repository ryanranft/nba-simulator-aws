#!/usr/bin/env python3
"""
Phase 1.11 Multi-Source Deduplication Agent
Cross-validates and deduplicates data from ESPN, hoopR, NBA API, Basketball Reference
Runs as background agent for comprehensive data deduplication and conflict resolution
"""

import asyncio
import logging
import json
import time
import pandas as pd
import psycopg2
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
import sys
import os
from collections import defaultdict
import hashlib

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/phase_1_11_deduplication_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Phase1DeduplicationAgent:
    def __init__(
        self,
        output_dir="/tmp/phase_1_11_deduplication",
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

        # Data source configurations
        self.data_sources = {
            "espn": {
                "priority": 1,
                "description": "Primary source - ESPN API",
                "confidence_weight": 0.9,
            },
            "hoopr": {
                "priority": 2,
                "description": "Secondary source - hoopR package",
                "confidence_weight": 0.8,
            },
            "nba_api": {
                "priority": 3,
                "description": "Official source - NBA Stats API",
                "confidence_weight": 0.95,
            },
            "basketball_reference": {
                "priority": 4,
                "description": "Historical source - Basketball Reference",
                "confidence_weight": 0.85,
            },
        }

        # Statistics
        self.stats = {
            "total_records_processed": 0,
            "duplicates_found": 0,
            "conflicts_resolved": 0,
            "records_deduplicated": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        # Deduplication metrics
        self.deduplication_metrics = {
            "duplicates_by_source": defaultdict(int),
            "conflicts_by_field": defaultdict(int),
            "resolution_methods": defaultdict(int),
            "processing_times": defaultdict(float),
            "error_patterns": defaultdict(int),
        }

        logger.info("Phase 1.11 Multi-Source Deduplication Agent initialized")
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

    def load_data_from_sources(self) -> Dict[str, List[Dict]]:
        """Load data from all available sources"""
        logger.info("Loading data from all sources...")

        all_data = {}

        try:
            # Load ESPN data
            espn_data = self._load_espn_data()
            if espn_data:
                all_data["espn"] = espn_data
                logger.info(f"Loaded {len(espn_data)} ESPN records")

            # Load hoopR data
            hoopr_data = self._load_hoopr_data()
            if hoopr_data:
                all_data["hoopr"] = hoopr_data
                logger.info(f"Loaded {len(hoopr_data)} hoopR records")

            # Load NBA API data
            nba_api_data = self._load_nba_api_data()
            if nba_api_data:
                all_data["nba_api"] = nba_api_data
                logger.info(f"Loaded {len(nba_api_data)} NBA API records")

            # Load Basketball Reference data
            bbref_data = self._load_basketball_reference_data()
            if bbref_data:
                all_data["basketball_reference"] = bbref_data
                logger.info(f"Loaded {len(bbref_data)} Basketball Reference records")

            total_records = sum(len(records) for records in all_data.values())
            self.stats["total_records_processed"] = total_records

            logger.info(f"Total records loaded: {total_records}")
            return all_data

        except Exception as e:
            logger.error(f"Error loading data from sources: {e}")
            self.stats["errors"] += 1
            return {}

    def _load_espn_data(self) -> List[Dict]:
        """Load ESPN data from database or files"""
        try:
            conn = self.connect_to_database()
            if not conn:
                return []

            # Query ESPN data
            espn_query = """
            SELECT
                game_id, player_id, team_id, season, game_date,
                pts, reb, ast, stl, blk, tov, pf, fgm, fga, fg_pct,
                fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
                plus_minus, minutes_played
            FROM nba_plays
            WHERE season >= 2020
            ORDER BY game_date DESC
            LIMIT 1000
            """

            df = pd.read_sql_query(espn_query, conn)
            conn.close()

            if not df.empty:
                return df.to_dict("records")
            else:
                logger.warning("No ESPN data found")
                return []

        except Exception as e:
            logger.error(f"Error loading ESPN data: {e}")
            return []

    def _load_hoopr_data(self) -> List[Dict]:
        """Load hoopR data from files"""
        try:
            hoopr_data = []

            # Look for hoopR data files
            hoopr_dir = Path("/tmp/hoopr_phase1")
            if hoopr_dir.exists():
                for file_path in hoopr_dir.rglob("*.csv"):
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            # Add source identifier
                            df["source"] = "hoopr"
                            df["file_path"] = str(file_path)
                            hoopr_data.extend(df.to_dict("records"))
                    except Exception as e:
                        logger.warning(f"Error reading hoopR file {file_path}: {e}")

            return hoopr_data

        except Exception as e:
            logger.error(f"Error loading hoopR data: {e}")
            return []

    def _load_nba_api_data(self) -> List[Dict]:
        """Load NBA API data from files"""
        try:
            nba_api_data = []

            # Look for NBA API data files
            nba_api_dir = Path("/tmp/phase_1_7_nba_stats")
            if nba_api_dir.exists():
                for file_path in nba_api_dir.rglob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for record in data:
                                    record["source"] = "nba_api"
                                    record["file_path"] = str(file_path)
                                    nba_api_data.append(record)
                            elif isinstance(data, dict):
                                data["source"] = "nba_api"
                                data["file_path"] = str(file_path)
                                nba_api_data.append(data)
                    except Exception as e:
                        logger.warning(f"Error reading NBA API file {file_path}: {e}")

            return nba_api_data

        except Exception as e:
            logger.error(f"Error loading NBA API data: {e}")
            return []

    def _load_basketball_reference_data(self) -> List[Dict]:
        """Load Basketball Reference data from files"""
        try:
            bbref_data = []

            # Look for Basketball Reference data files
            bbref_dir = Path("/tmp/bbref_tier_1")
            if bbref_dir.exists():
                for file_path in bbref_dir.rglob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for record in data:
                                    record["source"] = "basketball_reference"
                                    record["file_path"] = str(file_path)
                                    bbref_data.append(record)
                            elif isinstance(data, dict):
                                data["source"] = "basketball_reference"
                                data["file_path"] = str(file_path)
                                bbref_data.append(data)
                    except Exception as e:
                        logger.warning(
                            f"Error reading Basketball Reference file {file_path}: {e}"
                        )

            return bbref_data

        except Exception as e:
            logger.error(f"Error loading Basketball Reference data: {e}")
            return []

    def identify_duplicates(
        self, all_data: Dict[str, List[Dict]]
    ) -> Dict[str, List[Dict]]:
        """Identify duplicate records across sources"""
        logger.info("Identifying duplicate records...")

        duplicates = defaultdict(list)

        try:
            # Create a mapping of game identifiers to records
            game_records = defaultdict(list)

            for source, records in all_data.items():
                for record in records:
                    # Create a unique game identifier
                    game_id = self._create_game_identifier(record)
                    if game_id:
                        game_records[game_id].append(
                            {
                                "source": source,
                                "record": record,
                                "confidence": self.data_sources[source][
                                    "confidence_weight"
                                ],
                            }
                        )

            # Find duplicates (games with multiple sources)
            for game_id, records in game_records.items():
                if len(records) > 1:
                    duplicates[game_id] = records
                    self.stats["duplicates_found"] += len(records)
                    self.deduplication_metrics["duplicates_by_source"][game_id] = len(
                        records
                    )

            logger.info(f"Found {len(duplicates)} games with duplicate records")
            return dict(duplicates)

        except Exception as e:
            logger.error(f"Error identifying duplicates: {e}")
            self.stats["errors"] += 1
            return {}

    def _create_game_identifier(self, record: Dict) -> Optional[str]:
        """Create a unique game identifier from record data"""
        try:
            # Try different identifier combinations
            identifiers = []

            if "game_id" in record and record["game_id"]:
                identifiers.append(f"game_id:{record['game_id']}")

            if "game_date" in record and record["game_date"]:
                identifiers.append(f"date:{record['game_date']}")

            if "home_team_id" in record and "away_team_id" in record:
                if record["home_team_id"] and record["away_team_id"]:
                    identifiers.append(
                        f"teams:{record['home_team_id']}-{record['away_team_id']}"
                    )

            if "season" in record and record["season"]:
                identifiers.append(f"season:{record['season']}")

            if identifiers:
                return "|".join(sorted(identifiers))
            else:
                return None

        except Exception as e:
            logger.error(f"Error creating game identifier: {e}")
            return None

    def resolve_conflicts(self, duplicates: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Resolve conflicts between duplicate records"""
        logger.info("Resolving conflicts between duplicate records...")

        resolved_records = {}

        try:
            for game_id, records in duplicates.items():
                # Sort records by confidence (highest first)
                sorted_records = sorted(
                    records, key=lambda x: x["confidence"], reverse=True
                )

                # Use the highest confidence record as the base
                base_record = sorted_records[0]["record"].copy()
                base_source = sorted_records[0]["source"]

                # Merge data from other sources where base record is missing
                merged_record = self._merge_records(sorted_records)

                # Track resolution method
                resolution_method = f"highest_confidence_{base_source}"
                self.deduplication_metrics["resolution_methods"][resolution_method] += 1

                resolved_records[game_id] = {
                    "final_record": merged_record,
                    "resolution_method": resolution_method,
                    "sources_used": [r["source"] for r in sorted_records],
                    "confidence_score": max(r["confidence"] for r in sorted_records),
                }

                self.stats["conflicts_resolved"] += 1

            logger.info(f"Resolved {len(resolved_records)} conflicts")
            return resolved_records

        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
            self.stats["errors"] += 1
            return {}

    def _merge_records(self, records: List[Dict]) -> Dict:
        """Merge multiple records into a single record"""
        try:
            # Start with the highest confidence record
            merged = records[0]["record"].copy()

            # Add fields from other records where merged record is missing or empty
            for record_info in records[1:]:
                record = record_info["record"]
                for key, value in record.items():
                    if key not in merged or not merged[key] or merged[key] == "":
                        if value and value != "":
                            merged[key] = value

            # Add metadata
            merged["deduplication_timestamp"] = datetime.now().isoformat()
            merged["sources_merged"] = [r["source"] for r in records]

            return merged

        except Exception as e:
            logger.error(f"Error merging records: {e}")
            return records[0]["record"]

    def generate_deduplication_report(
        self, duplicates: Dict, resolved_records: Dict
    ) -> Dict:
        """Generate comprehensive deduplication report"""
        logger.info("Generating deduplication report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_records_processed": self.stats["total_records_processed"],
                "duplicates_found": self.stats["duplicates_found"],
                "conflicts_resolved": self.stats["conflicts_resolved"],
                "records_deduplicated": len(resolved_records),
                "total_errors": self.stats["errors"],
                "deduplication_duration": str(
                    datetime.now() - self.stats["start_time"]
                ),
            },
            "deduplication_metrics": dict(self.deduplication_metrics),
            "duplicate_summary": {
                "games_with_duplicates": len(duplicates),
                "total_duplicate_records": sum(
                    len(records) for records in duplicates.values()
                ),
                "average_duplicates_per_game": (
                    sum(len(records) for records in duplicates.values())
                    / len(duplicates)
                    if duplicates
                    else 0
                ),
            },
            "resolution_summary": {
                "conflicts_resolved": len(resolved_records),
                "resolution_methods_used": dict(
                    self.deduplication_metrics["resolution_methods"]
                ),
                "sources_involved": list(
                    set(
                        source
                        for game_records in duplicates.values()
                        for record_info in game_records
                        for source in [record_info["source"]]
                    )
                ),
            },
            "recommendations": self._generate_recommendations(),
        }

        # Save report
        report_file = self.output_dir / "deduplication_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Deduplication report saved to {report_file}")
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on deduplication results"""
        recommendations = []

        if self.stats["errors"] > 0:
            recommendations.append(
                f"Address {self.stats['errors']} deduplication errors"
            )

        if self.stats["duplicates_found"] == 0:
            recommendations.append(
                "No duplicates found - verify data sources are properly loaded"
            )

        if self.stats["conflicts_resolved"] > 0:
            recommendations.append(
                f"Review {self.stats['conflicts_resolved']} resolved conflicts for accuracy"
            )

        recommendations.append("Implement automated deduplication pipeline")
        recommendations.append("Set up data quality monitoring for new data")
        recommendations.append("Create data source priority hierarchy")

        return recommendations

    def log_progress(self):
        """Log current progress"""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("PHASE 1.11 MULTI-SOURCE DEDUPLICATION AGENT PROGRESS")
        logger.info("=" * 60)
        logger.info(f"Total records processed: {self.stats['total_records_processed']}")
        logger.info(f"Duplicates found: {self.stats['duplicates_found']}")
        logger.info(f"Conflicts resolved: {self.stats['conflicts_resolved']}")
        logger.info(f"Records deduplicated: {self.stats['records_deduplicated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Elapsed time: {elapsed}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    async def run(self):
        """Main execution method"""
        logger.info("Starting Phase 1.11 Multi-Source Deduplication Agent")

        try:
            # Load data from all sources
            all_data = self.load_data_from_sources()

            if not all_data:
                logger.error("No data loaded from any source")
                return

            # Identify duplicates
            duplicates = self.identify_duplicates(all_data)

            # Resolve conflicts
            resolved_records = self.resolve_conflicts(duplicates)

            # Log progress
            self.log_progress()

            # Generate final report
            report = self.generate_deduplication_report(duplicates, resolved_records)

            logger.info(
                "Phase 1.11 Multi-Source Deduplication Agent completed successfully"
            )
            logger.info(f"Report saved to: {self.output_dir}/deduplication_report.json")

        except Exception as e:
            logger.error(f"Phase 1.11 Multi-Source Deduplication Agent failed: {e}")


def main():
    """Main entry point"""
    agent = Phase1DeduplicationAgent()

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Phase 1.11 Multi-Source Deduplication Agent interrupted by user")
    except Exception as e:
        logger.error(f"Phase 1.11 Multi-Source Deduplication Agent failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
