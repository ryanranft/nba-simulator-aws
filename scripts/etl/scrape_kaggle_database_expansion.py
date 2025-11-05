#!/usr/bin/env python3
"""
Kaggle Database Expansion Scraper
Extracts and processes the 12 missing tables from the Kaggle NBA database.

Currently using only 5/17 tables (29%). This scraper extracts the remaining 12 tables
to add 25-35 additional features to our dataset.

Missing Tables to Extract:
- draft_combine_stats - Physical measurements, athleticism tests
- draft_history - Complete draft history 1947-present
- officials - Referee assignments per game
- line_score - Quarter-by-quarter scoring
- game_info - Game metadata (attendance, duration)
- other_stats - Paint points, fast break, 2nd chance
- team_history - Franchise history
- team_details - Team details/metadata
- inactive_players - Historical inactive list
- player_attributes - Player physical attributes
- team_attributes - Team attributes
- game_attributes - Game-specific attributes

Coverage: 1947-present (varies by table)
Output: JSON files for each table with normalized schema
"""

import argparse
import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os


class KaggleDatabaseExpander:
    """
    Kaggle Database Expansion scraper

    Extracts missing tables from Kaggle NBA database
    """

    def __init__(self, db_path: str, output_dir: str = "/tmp/kaggle_expanded"):
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each table type
        self.table_categories = {
            "draft": ["draft_combine_stats", "draft_history"],
            "game_details": ["officials", "line_score", "game_info", "other_stats"],
            "team_data": ["team_history", "team_details", "team_attributes"],
            "player_data": ["inactive_players", "player_attributes"],
            "game_data": ["game_attributes"],
        }

        for category in self.table_categories.keys():
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)

        self.stats = {
            "start_time": datetime.now(),
            "tables_processed": 0,
            "records_extracted": 0,
            "files_created": 0,
            "errors": 0,
        }

        print(f"Kaggle Database Expander initialized")
        print(f"Database: {self.db_path}")
        print(f"Output directory: {self.output_dir}")

    def get_table_info(self, table_name: str) -> Dict:
        """Get information about a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get table schema
            cursor.execute(
                f"PRAGMA table_info({table_name})"
            )  # nosec B608 - table_name from DB schema, not user input
            columns = cursor.fetchall()

            # Get row count
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            )  # nosec B608 - table_name from DB schema, not user input
            row_count = cursor.fetchone()[0]

            # Get sample data
            cursor.execute(
                f"SELECT * FROM {table_name} LIMIT 5"
            )  # nosec B608 - table_name from DB schema, not user input
            sample_data = cursor.fetchall()

            conn.close()

            return {
                "table_name": table_name,
                "columns": [col[1] for col in columns],
                "row_count": row_count,
                "sample_data": sample_data,
                "exists": True,
            }

        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return {"table_name": table_name, "exists": False, "error": str(e)}
            else:
                raise e

    def extract_table(self, table_name: str) -> bool:
        """Extract a single table from the database"""
        print(f"Extracting table: {table_name}")

        try:
            # Check if table exists
            table_info = self.get_table_info(table_name)
            if not table_info["exists"]:
                print(f"  ⚠️ Table {table_name} does not exist")
                return False

            print(f"  → Found {table_info['row_count']} records")
            print(f"  → Columns: {', '.join(table_info['columns'])}")

            # Extract all data
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                f"SELECT * FROM {table_name}", conn
            )  # nosec B608 - table_name from DB schema, not user input
            conn.close()

            if df.empty:
                print(f"  ⚠️ Table {table_name} is empty")
                return False

            # Determine output category
            category = None
            for cat, tables in self.table_categories.items():
                if table_name in tables:
                    category = cat
                    break

            if not category:
                category = "other"
                (self.output_dir / category).mkdir(parents=True, exist_ok=True)

            # Save as JSON
            output_file = self.output_dir / category / f"{table_name}.json"
            df.to_json(output_file, orient="records", indent=2)

            # Add metadata
            metadata = {
                "table_name": table_name,
                "extraction_date": datetime.now().isoformat(),
                "row_count": len(df),
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict(),
                "sample_records": df.head(3).to_dict("records"),
            }

            metadata_file = self.output_dir / category / f"{table_name}_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

            print(f"  ✅ Extracted {len(df)} records to {output_file}")
            self.stats["tables_processed"] += 1
            self.stats["records_extracted"] += len(df)
            self.stats["files_created"] += 2  # Data + metadata files

            return True

        except Exception as e:
            print(f"  ❌ Error extracting table {table_name}: {e}")
            self.stats["errors"] += 1
            return False

    def extract_all_missing_tables(self) -> Dict:
        """Extract all missing tables from the database"""
        print("Starting Kaggle database expansion")

        # Define all tables to extract
        tables_to_extract = [
            "draft_combine_stats",
            "draft_history",
            "officials",
            "line_score",
            "game_info",
            "other_stats",
            "team_history",
            "team_details",
            "inactive_players",
            "player_attributes",
            "team_attributes",
            "game_attributes",
        ]

        successful_tables = []
        failed_tables = []

        for table_name in tables_to_extract:
            print(f"\nProcessing table: {table_name}")

            if self.extract_table(table_name):
                successful_tables.append(table_name)
                print(f"✅ Successfully extracted {table_name}")
            else:
                failed_tables.append(table_name)
                print(f"❌ Failed to extract {table_name}")

        # Generate summary report
        end_time = datetime.now()
        duration = (end_time - self.stats["start_time"]).total_seconds()

        summary = {
            "extraction_summary": {
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "total_tables": len(tables_to_extract),
                "successful_tables": len(successful_tables),
                "failed_tables": len(failed_tables),
                "success_rate": (
                    len(successful_tables) / len(tables_to_extract)
                    if tables_to_extract
                    else 0
                ),
                "records_extracted": self.stats["records_extracted"],
                "files_created": self.stats["files_created"],
                "errors": self.stats["errors"],
            },
            "successful_tables": successful_tables,
            "failed_tables": failed_tables,
            "table_categories": self.table_categories,
            "features_added": [
                "Draft combine statistics (physical measurements, athleticism)",
                "Complete draft history (1947-present)",
                "Game officials and referee assignments",
                "Quarter-by-quarter scoring breakdown",
                "Game metadata (attendance, duration, venue)",
                "Advanced game statistics (paint points, fast break, 2nd chance)",
                "Team franchise history and details",
                "Player inactive lists and attributes",
                "Team and game attributes",
            ],
            "output_directory": str(self.output_dir),
        }

        # Save summary report
        summary_file = self.output_dir / "extraction_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 60)
        print("KAGGLE DATABASE EXPANSION COMPLETE")
        print("=" * 60)
        print(f"Total tables: {len(tables_to_extract)}")
        print(f"Successful: {len(successful_tables)}")
        print(f"Failed: {len(failed_tables)}")
        print(f"Success rate: {len(successful_tables)/len(tables_to_extract)*100:.1f}%")
        print(f"Records extracted: {self.stats['records_extracted']}")
        print(f"Files created: {self.stats['files_created']}")
        print(f"Duration: {duration/60:.1f} minutes")
        print(f"Output directory: {self.output_dir}")
        print(f"Summary report: {summary_file}")

        return summary


def main():
    parser = argparse.ArgumentParser(description="Kaggle Database Expansion Scraper")
    parser.add_argument(
        "--db-path", type=str, required=True, help="Path to Kaggle SQLite database"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/kaggle_expanded",
        help="Output directory (default: /tmp/kaggle_expanded)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Test mode: only extract first 3 tables",
    )

    args = parser.parse_args()

    if not Path(args.db_path).exists():
        print(f"❌ Database file not found: {args.db_path}")
        return 1

    expander = KaggleDatabaseExpander(db_path=args.db_path, output_dir=args.output_dir)

    if args.test_mode:
        print("🧪 TEST MODE: Only extracting first 3 tables")
        # Override the extract_all_missing_tables method for test mode
        tables_to_extract = ["draft_combine_stats", "draft_history", "officials"]
        successful_tables = []
        for table_name in tables_to_extract:
            if expander.extract_table(table_name):
                successful_tables.append(table_name)
        print(
            f"Test mode completed: {len(successful_tables)}/{len(tables_to_extract)} tables extracted"
        )
        return 0

    summary = expander.extract_all_missing_tables()

    if summary["extraction_summary"]["success_rate"] > 0.5:
        print("✅ Kaggle database expansion completed successfully!")
        return 0
    else:
        print("❌ Kaggle database expansion had significant failures")
        return 1


if __name__ == "__main__":
    exit(main())
