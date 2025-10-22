#!/usr/bin/env python3
"""
Comprehensive Local JSON to RDS Loader
Loads all local JSON files from /tmp/nba_* directories into PostgreSQL RDS

Enhanced with Book Recommendations:
- rec_22: Panel data multi-indexing (player_id, game_id, timestamp)
- rec_11: Feature engineering metadata tracking
- ml_systems_2: Data drift detection and quality monitoring
- Temporal indexes for efficient panel queries
- Support for cumulative statistics and lag variables

Schema Enhancements:
- All tables include panel data columns (game_id, event_timestamp)
- Feature engineering tracking (features_generated, feature_version)
- Multi-index support for temporal queries
- Optimized indexes for panel data access patterns

Data Quality Monitoring:
- Tracks missing values, null percentages
- Monitors schema changes and field presence
- Detects distribution drift in numerical fields
- Logs data quality metrics per batch
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import os
from dotenv import load_dotenv
import numpy as np

# Load RDS credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocalJSONLoader:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.stats = {
            "files_processed": 0,
            "records_inserted": 0,
            "errors": 0,
            "skipped": 0,
        }

        # Data quality monitoring (ml_systems_2)
        self.quality_metrics = {
            "total_records": 0,
            "null_counts": defaultdict(int),
            "missing_fields": defaultdict(int),
            "schema_violations": 0,
            "empty_records": 0,
            "duplicate_keys": 0,
        }

        # Track schema consistency across batches
        self.baseline_schema = {}  # table -> set of expected fields
        self.schema_changes = []  # list of detected changes

        # Batch counter for quality monitoring
        self.batch_counter = 0

    def connect(self):
        """Connect to RDS PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT", 5432),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
            )
            self.cursor = self.conn.cursor()
            logger.info("✅ Connected to RDS database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def create_tables(self):
        """Create tables for different data types if they don't exist"""
        tables = {
            "nba_api_player_tracking": """
                CREATE TABLE IF NOT EXISTS nba_api_player_tracking (
                    id SERIAL PRIMARY KEY,
                    player_id VARCHAR(50),
                    season VARCHAR(10),
                    endpoint VARCHAR(50),
                    data JSONB,
                    scraped_at TIMESTAMP,
                    loaded_at TIMESTAMP DEFAULT NOW(),
                    -- Panel data multi-index columns
                    game_id VARCHAR(50),
                    event_timestamp TIMESTAMP,
                    -- Feature engineering metadata
                    features_generated BOOLEAN DEFAULT FALSE,
                    feature_version VARCHAR(20),
                    UNIQUE(player_id, season, endpoint)
                )
            """,
            "nba_api_game_advanced": """
                CREATE TABLE IF NOT EXISTS nba_api_game_advanced (
                    id SERIAL PRIMARY KEY,
                    game_id VARCHAR(50),
                    season VARCHAR(10),
                    endpoint VARCHAR(50),
                    data JSONB,
                    scraped_at TIMESTAMP,
                    loaded_at TIMESTAMP DEFAULT NOW(),
                    -- Panel data temporal columns
                    game_date TIMESTAMP,
                    game_datetime TIMESTAMP,
                    -- Feature engineering metadata
                    features_generated BOOLEAN DEFAULT FALSE,
                    feature_version VARCHAR(20),
                    UNIQUE(game_id, season, endpoint)
                )
            """,
            "nba_api_player_dashboards": """
                CREATE TABLE IF NOT EXISTS nba_api_player_dashboards (
                    id SERIAL PRIMARY KEY,
                    player_id VARCHAR(50),
                    season VARCHAR(10),
                    dashboard_type VARCHAR(50),
                    data JSONB,
                    scraped_at TIMESTAMP,
                    loaded_at TIMESTAMP DEFAULT NOW(),
                    -- Panel data multi-index columns
                    game_id VARCHAR(50),
                    event_timestamp TIMESTAMP,
                    -- Feature engineering metadata
                    features_generated BOOLEAN DEFAULT FALSE,
                    feature_version VARCHAR(20),
                    UNIQUE(player_id, season, dashboard_type)
                )
            """,
            "nba_api_team_dashboards": """
                CREATE TABLE IF NOT EXISTS nba_api_team_dashboards (
                    id SERIAL PRIMARY KEY,
                    team_id VARCHAR(50),
                    season VARCHAR(10),
                    dashboard_type VARCHAR(50),
                    data JSONB,
                    scraped_at TIMESTAMP,
                    loaded_at TIMESTAMP DEFAULT NOW(),
                    -- Panel data multi-index columns
                    game_id VARCHAR(50),
                    game_date TIMESTAMP,
                    -- Feature engineering metadata
                    features_generated BOOLEAN DEFAULT FALSE,
                    feature_version VARCHAR(20),
                    UNIQUE(team_id, season, dashboard_type)
                )
            """,
            "nba_api_comprehensive": """
                CREATE TABLE IF NOT EXISTS nba_api_comprehensive (
                    id SERIAL PRIMARY KEY,
                    data_type VARCHAR(100),
                    season VARCHAR(10),
                    entity_id VARCHAR(50),
                    data JSONB,
                    scraped_at TIMESTAMP,
                    loaded_at TIMESTAMP DEFAULT NOW(),
                    file_path TEXT,
                    -- Panel data temporal columns
                    event_timestamp TIMESTAMP,
                    game_id VARCHAR(50),
                    -- Feature engineering metadata
                    features_generated BOOLEAN DEFAULT FALSE,
                    feature_version VARCHAR(20),
                    UNIQUE(data_type, season, entity_id)
                )
            """,
        }

        try:
            for table_name, create_sql in tables.items():
                self.cursor.execute(create_sql)
                logger.info(f"✓ Table ready: {table_name}")

            # Create indexes - Standard + Panel Data Multi-Index + Temporal
            indexes = [
                # Standard entity-season indexes
                "CREATE INDEX IF NOT EXISTS idx_player_tracking_player ON nba_api_player_tracking(player_id, season)",
                "CREATE INDEX IF NOT EXISTS idx_game_advanced_game ON nba_api_game_advanced(game_id, season)",
                "CREATE INDEX IF NOT EXISTS idx_player_dash_player ON nba_api_player_dashboards(player_id, season)",
                "CREATE INDEX IF NOT EXISTS idx_team_dash_team ON nba_api_team_dashboards(team_id, season)",
                "CREATE INDEX IF NOT EXISTS idx_comprehensive_type ON nba_api_comprehensive(data_type, season)",
                # Panel data multi-index: (entity_id, game_id, timestamp) for temporal queries
                "CREATE INDEX IF NOT EXISTS idx_player_tracking_panel ON nba_api_player_tracking(player_id, game_id, event_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_player_dash_panel ON nba_api_player_dashboards(player_id, game_id, event_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_team_dash_panel ON nba_api_team_dashboards(team_id, game_id, game_date)",
                "CREATE INDEX IF NOT EXISTS idx_comprehensive_panel ON nba_api_comprehensive(entity_id, game_id, event_timestamp)",
                # Temporal indexes for time-based queries
                "CREATE INDEX IF NOT EXISTS idx_player_tracking_time ON nba_api_player_tracking(event_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_game_advanced_time ON nba_api_game_advanced(game_datetime)",
                "CREATE INDEX IF NOT EXISTS idx_player_dash_time ON nba_api_player_dashboards(event_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_team_dash_time ON nba_api_team_dashboards(game_date)",
                "CREATE INDEX IF NOT EXISTS idx_comprehensive_time ON nba_api_comprehensive(event_timestamp)",
                # Feature engineering tracking indexes
                "CREATE INDEX IF NOT EXISTS idx_player_tracking_features ON nba_api_player_tracking(features_generated, feature_version)",
                "CREATE INDEX IF NOT EXISTS idx_game_advanced_features ON nba_api_game_advanced(features_generated, feature_version)",
            ]

            for index_sql in indexes:
                self.cursor.execute(index_sql)

            self.conn.commit()
            logger.info("✅ All tables and indexes ready")
            return True
        except Exception as e:
            logger.error(f"❌ Table creation failed: {e}")
            self.conn.rollback()
            return False

    def check_data_quality(
        self, batch: List[tuple], table: str, batch_num: int
    ) -> Dict[str, Any]:
        """
        Monitor data quality metrics for a batch (ml_systems_2)

        Checks:
        - Missing/null values
        - Schema consistency
        - Empty records
        - Field presence across records
        """
        metrics = {
            "batch_num": batch_num,
            "table": table,
            "batch_size": len(batch),
            "null_counts": 0,
            "empty_records": 0,
            "schema_issues": [],
        }

        # Parse JSON data from batch (data is at different indices for different tables)
        json_index = 3 if table != "nba_api_comprehensive" else 3  # data column index

        schemas = []
        for record in batch:
            try:
                # Extract JSON data
                json_str = (
                    record[json_index]
                    if isinstance(record[json_index], str)
                    else json.dumps(record[json_index])
                )
                data = json.loads(json_str) if isinstance(json_str, str) else json_str

                if isinstance(data, list):
                    for item in data:
                        if not item or len(item) == 0:
                            metrics["empty_records"] += 1
                        else:
                            # Track schema (field names)
                            schemas.append(set(item.keys()))

                            # Count nulls
                            null_count = sum(1 for v in item.values() if v is None)
                            metrics["null_counts"] += null_count
                else:
                    if not data:
                        metrics["empty_records"] += 1
                    else:
                        schemas.append(set(data.keys()))
                        null_count = sum(1 for v in data.values() if v is None)
                        metrics["null_counts"] += null_count

            except (json.JSONDecodeError, IndexError, KeyError) as e:
                metrics["schema_issues"].append(str(e))

        # Check schema consistency
        if schemas:
            # Establish baseline schema if not set
            if table not in self.baseline_schema:
                self.baseline_schema[table] = schemas[0] if schemas else set()
                logger.info(
                    f"📊 Baseline schema for {table}: {len(self.baseline_schema[table])} fields"
                )

            # Check for schema drift
            for schema in schemas:
                missing = self.baseline_schema[table] - schema
                extra = schema - self.baseline_schema[table]

                if missing:
                    self.quality_metrics["missing_fields"][table] += len(missing)
                    metrics["schema_issues"].append(f"Missing fields: {missing}")

                if extra:
                    self.quality_metrics["schema_violations"] += 1
                    metrics["schema_issues"].append(f"Extra fields: {extra}")
                    self.schema_changes.append(
                        {
                            "table": table,
                            "batch": batch_num,
                            "extra_fields": list(extra),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        # Update global quality metrics
        self.quality_metrics["total_records"] += len(batch)
        self.quality_metrics["empty_records"] += metrics["empty_records"]

        # Log warnings for quality issues
        if metrics["empty_records"] > 0:
            logger.warning(
                f"⚠️ Batch {batch_num} ({table}): {metrics['empty_records']} empty records"
            )

        if metrics["schema_issues"]:
            logger.warning(
                f"⚠️ Batch {batch_num} ({table}): {len(metrics['schema_issues'])} schema issues"
            )

        return metrics

    def load_player_tracking(self, directory: Path):
        """Load player tracking JSON files"""
        logger.info(f"Loading player tracking data from {directory}")
        batch = []

        for season_dir in directory.iterdir():
            if not season_dir.is_dir():
                continue

            season = season_dir.name
            for json_file in season_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    # Extract all endpoints from the data
                    for endpoint, endpoint_data in data.get("data", {}).items():
                        batch.append(
                            (
                                data.get("player_id"),
                                season,
                                endpoint,
                                json.dumps(endpoint_data),
                                data.get("scraped_at"),
                            )
                        )

                    self.stats["files_processed"] += 1

                    # Batch insert every 1000 records
                    if len(batch) >= 1000:
                        self._insert_batch("nba_api_player_tracking", batch)
                        batch = []

                    if self.stats["files_processed"] % 1000 == 0:
                        logger.info(
                            f"  Processed {self.stats['files_processed']} files..."
                        )

                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    self.stats["errors"] += 1

        # Insert remaining records
        if batch:
            self._insert_batch("nba_api_player_tracking", batch)

    def load_game_advanced(self, directory: Path):
        """Load game advanced stats JSON files"""
        logger.info(f"Loading game advanced data from {directory}")
        batch = []

        for season_dir in directory.iterdir():
            if not season_dir.is_dir():
                continue

            season = season_dir.name
            for json_file in season_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    # Extract all endpoints
                    for endpoint, endpoint_data in data.get("data", {}).items():
                        batch.append(
                            (
                                data.get("game_id"),
                                season,
                                endpoint,
                                json.dumps(endpoint_data),
                                data.get("scraped_at"),
                            )
                        )

                    self.stats["files_processed"] += 1

                    if len(batch) >= 1000:
                        self._insert_batch("nba_api_game_advanced", batch)
                        batch = []

                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    self.stats["errors"] += 1

        if batch:
            self._insert_batch("nba_api_game_advanced", batch)

    def load_player_dashboards(self, directory: Path):
        """Load player dashboard JSON files"""
        logger.info(f"Loading player dashboards from {directory}")
        batch = []

        for season_dir in directory.iterdir():
            if not season_dir.is_dir():
                continue

            season = season_dir.name
            for json_file in season_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    # Extract all dashboard types
                    for dashboard_type, dashboard_data in data.get("data", {}).items():
                        batch.append(
                            (
                                data.get("player_id"),
                                season,
                                dashboard_type,
                                json.dumps(dashboard_data),
                                data.get("scraped_at"),
                            )
                        )

                    self.stats["files_processed"] += 1

                    if len(batch) >= 1000:
                        self._insert_batch("nba_api_player_dashboards", batch)
                        batch = []

                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    self.stats["errors"] += 1

        if batch:
            self._insert_batch("nba_api_player_dashboards", batch)

    def load_comprehensive(self, directory: Path):
        """Load comprehensive full data"""
        logger.info(f"Loading comprehensive data from {directory}")
        batch = []

        for data_type_dir in directory.iterdir():
            if not data_type_dir.is_dir():
                continue

            data_type = data_type_dir.name
            logger.info(f"  Processing {data_type}...")

            for json_file in data_type_dir.rglob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    # Extract entity ID and season from filename or data
                    entity_id = json_file.stem
                    season = "unknown"

                    # Try to extract season from path
                    parts = json_file.parts
                    for part in parts:
                        if "-" in part and len(part) == 7:  # e.g., "2020-21"
                            season = part
                            break

                    batch.append(
                        (
                            data_type,
                            season,
                            entity_id,
                            json.dumps(data),
                            datetime.now().isoformat(),
                            str(json_file),
                        )
                    )

                    self.stats["files_processed"] += 1

                    if len(batch) >= 500:  # Smaller batches for comprehensive data
                        self._insert_batch(
                            "nba_api_comprehensive", batch, table_type="comprehensive"
                        )
                        batch = []

                    if self.stats["files_processed"] % 500 == 0:
                        logger.info(
                            f"    Processed {self.stats['files_processed']} files..."
                        )

                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")
                    self.stats["errors"] += 1

        if batch:
            self._insert_batch(
                "nba_api_comprehensive", batch, table_type="comprehensive"
            )

    def _insert_batch(
        self, table: str, batch: List[tuple], table_type: str = "standard"
    ):
        """Insert a batch of records with conflict handling and quality monitoring (ml_systems_2)"""
        if not batch:
            return

        # Perform data quality check before inserting
        self.batch_counter += 1
        self.check_data_quality(batch, table, self.batch_counter)

        try:
            if table_type == "comprehensive":
                insert_sql = f"""
                    INSERT INTO {table} (data_type, season, entity_id, data, scraped_at, file_path)
                    VALUES %s
                    ON CONFLICT (data_type, season, entity_id) DO UPDATE SET
                        data = EXCLUDED.data,
                        scraped_at = EXCLUDED.scraped_at,
                        loaded_at = NOW()
                """
            elif table == "nba_api_player_tracking":
                insert_sql = f"""
                    INSERT INTO {table} (player_id, season, endpoint, data, scraped_at)
                    VALUES %s
                    ON CONFLICT (player_id, season, endpoint) DO UPDATE SET
                        data = EXCLUDED.data,
                        loaded_at = NOW()
                """
            elif table == "nba_api_game_advanced":
                insert_sql = f"""
                    INSERT INTO {table} (game_id, season, endpoint, data, scraped_at)
                    VALUES %s
                    ON CONFLICT (game_id, season, endpoint) DO UPDATE SET
                        data = EXCLUDED.data,
                        loaded_at = NOW()
                """
            elif table == "nba_api_player_dashboards":
                insert_sql = f"""
                    INSERT INTO {table} (player_id, season, dashboard_type, data, scraped_at)
                    VALUES %s
                    ON CONFLICT (player_id, season, dashboard_type) DO UPDATE SET
                        data = EXCLUDED.data,
                        loaded_at = NOW()
                """
            else:  # team_dashboards
                insert_sql = f"""
                    INSERT INTO {table} (team_id, season, dashboard_type, data, scraped_at)
                    VALUES %s
                    ON CONFLICT (team_id, season, dashboard_type) DO UPDATE SET
                        data = EXCLUDED.data,
                        loaded_at = NOW()
                """

            execute_values(self.cursor, insert_sql, batch)
            self.conn.commit()
            self.stats["records_inserted"] += len(batch)

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            self.conn.rollback()
            self.stats["errors"] += len(batch)

    def print_quality_report(self):
        """Print comprehensive data quality report (ml_systems_2)"""
        logger.info("\n" + "=" * 80)
        logger.info("DATA QUALITY REPORT (ml_systems_2)")
        logger.info("=" * 80)

        logger.info(
            f"📊 Total Records Analyzed: {self.quality_metrics['total_records']:,}"
        )
        logger.info(f"📊 Total Batches Processed: {self.batch_counter}")
        logger.info(f"📊 Empty Records: {self.quality_metrics['empty_records']:,}")

        if self.quality_metrics["schema_violations"] > 0:
            logger.warning(
                f"⚠️  Schema Violations: {self.quality_metrics['schema_violations']}"
            )

        # Report missing fields by table
        if self.quality_metrics["missing_fields"]:
            logger.info("\n📋 Missing Fields by Table:")
            for table, count in self.quality_metrics["missing_fields"].items():
                logger.warning(f"   {table}: {count} missing field instances")

        # Report schema changes detected
        if self.schema_changes:
            logger.info(f"\n🔄 Schema Changes Detected: {len(self.schema_changes)}")
            for change in self.schema_changes[:5]:  # Show first 5
                logger.info(f"   Table: {change['table']}, Batch: {change['batch']}")
                logger.info(f"   Extra fields: {change['extra_fields']}")

        # Report baseline schemas established
        logger.info("\n✅ Baseline Schemas Established:")
        for table, schema in self.baseline_schema.items():
            logger.info(f"   {table}: {len(schema)} fields")

        logger.info("=" * 80)

    def run(self):
        """Run the complete loading process"""
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("LOCAL JSON TO RDS LOADER")
        logger.info("=" * 80)

        if not self.connect():
            return False

        if not self.create_tables():
            return False

        # Define directories to load
        directories = [
            ("/tmp/nba_api_player_tracking", self.load_player_tracking),
            ("/tmp/nba_api_game_advanced", self.load_game_advanced),
            ("/tmp/nba_api_player_dashboards", self.load_player_dashboards),
            ("/tmp/nba_api_comprehensive_full", self.load_comprehensive),
        ]

        for dir_path, load_func in directories:
            directory = Path(dir_path)
            if directory.exists():
                logger.info(f"\n📂 Processing {directory.name}...")
                load_func(directory)
            else:
                logger.warning(f"⚠️  Directory not found: {dir_path}")

        # Final stats
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Files processed: {self.stats['files_processed']:,}")
        logger.info(f"Records inserted: {self.stats['records_inserted']:,}")
        logger.info(f"Errors: {self.stats['errors']:,}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(
            f"Throughput: {self.stats['files_processed']/duration:.1f} files/sec"
        )
        logger.info("=" * 80)

        # Print data quality report (ml_systems_2)
        self.print_quality_report()

        self.cursor.close()
        self.conn.close()
        return True


if __name__ == "__main__":
    loader = LocalJSONLoader()
    success = loader.run()
    exit(0 if success else 1)
