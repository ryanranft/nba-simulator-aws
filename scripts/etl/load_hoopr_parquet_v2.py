#!/usr/bin/env python3
"""
hoopR Parquet Loader v2 - Schema-Aware Version
Load hoopR parquet files into PostgreSQL with automatic column detection

This version automatically detects which columns exist in target tables
and only inserts matching columns, making it compatible with different
schema versions.

Usage:
    # Load all parquet files from backup directory
    python scripts/etl/load_hoopr_parquet_v2.py

    # Load specific season
    python scripts/etl/load_hoopr_parquet_v2.py --season 2025

    # Load to specific database
    python scripts/etl/load_hoopr_parquet_v2.py --database nba_simulator
    python scripts/etl/load_hoopr_parquet_v2.py --database nba_mcp_synthesis
    python scripts/etl/load_hoopr_parquet_v2.py --database both  # Default

    # Dry run (no actual loading)
    python scripts/etl/load_hoopr_parquet_v2.py --dry-run

Created: November 9, 2025 (v2)
Purpose: Schema-aware hoopR data loading with automatic column detection
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HooprParquetLoaderV2:
    """Load hoopR parquet files into PostgreSQL with automatic schema detection"""

    # Default parquet backup location
    DEFAULT_PARQUET_DIR = Path.home() / "Desktop/sports_data_backup/hoopR/nba"

    # Database configurations
    DB_CONFIGS = {
        'nba_simulator': {
            'host': 'localhost',
            'port': 5432,
            'database': 'nba_simulator',
            'user': 'ryanranft',
            'schema': 'hoopr'
        },
        'nba_mcp_synthesis': {
            'host': 'localhost',
            'port': 5432,
            'database': 'nba_mcp_synthesis',
            'user': 'ryanranft',
            'schema': 'hoopr_raw'
        }
    }

    # Table name mapping (parquet type -> table name)
    TABLE_NAMES = {
        'pbp': 'play_by_play_hoopr_nba',
        'player_box': 'player_box_hoopr_nba',
        'team_box': 'team_box_hoopr_nba',
        'schedule': 'schedule_hoopr_nba'
    }

    # Column mappings (DataFrame column -> PostgreSQL column)
    # These are applied first, then we filter to only existing columns
    COLUMN_MAPPINGS = {
        'pbp': {
            'id': 'event_id',
            'text': 'description',
            'game_date_time': 'game_datetime',
        },
        'player_box': {
            'athlete_id': 'athlete_id',
            'athlete_display_name': 'athlete_name',
            'athlete_position_abbreviation': 'athlete_position',
            'team_abbreviation': 'team_abbrev',
            'field_goals_made': 'fgm',
            'field_goals_attempted': 'fga',
            'three_point_field_goals_made': 'fg3m',
            'three_point_field_goals_attempted': 'fg3a',
            'free_throws_made': 'ftm',
            'free_throws_attempted': 'fta',
            'offensive_rebounds': 'oreb',
            'defensive_rebounds': 'dreb',
            'opponent_team_abbreviation': 'opponent_team_abbrev',
            'game_date_time': 'game_datetime',
        },
        'team_box': {
            'team_abbreviation': 'team_abbrev',
            'team_home_away': 'home_away',
            'field_goals_made': 'fgm',
            'field_goals_attempted': 'fga',
            'field_goal_pct': 'fg_pct',
            'three_point_field_goals_made': 'fg3m',
            'three_point_field_goals_attempted': 'fg3a',
            'three_point_field_goal_pct': 'fg3_pct',
            'free_throws_made': 'ftm',
            'free_throws_attempted': 'fta',
            'free_throw_pct': 'ft_pct',
            'offensive_rebounds': 'oreb',
            'defensive_rebounds': 'dreb',
            'total_rebounds': 'reb',
            'opponent_team_abbreviation': 'opponent_team_abbrev',
            'game_date_time': 'game_datetime',
        },
        'schedule': {
            'id': 'game_id',
            'home_id': 'home_team_id',
            'away_id': 'away_team_id',
            'home_abbreviation': 'home_team_abbrev',
            'away_abbreviation': 'away_team_abbrev',
            'status_type_completed': 'game_completed',
            'status_type_name': 'status_type',
            'status_type_detail': 'status_detail',
            'venue_full_name': 'venue_name',
            'venue_address_city': 'venue_city',
            'venue_address_state': 'venue_state',
            'play_by_play_available': 'pbp_available',
            'game_date_time': 'game_datetime',
        }
    }

    # Primary key columns for conflict detection
    PK_COLUMNS = {
        'pbp': 'event_id',
        'player_box': ['game_id', 'athlete_id'],
        'team_box': ['game_id', 'team_id'],
        'schedule': 'game_id'
    }

    def __init__(self, parquet_dir: Optional[Path] = None, dry_run: bool = False):
        """
        Initialize loader

        Args:
            parquet_dir: Directory containing parquet files
            dry_run: If True, don't actually insert data
        """
        self.parquet_dir = parquet_dir or self.DEFAULT_PARQUET_DIR
        self.dry_run = dry_run

        # Cache for table columns
        self._table_columns_cache = {}

        # Stats
        self.stats = {
            'nba_simulator': {'pbp': 0, 'player_box': 0, 'team_box': 0, 'schedule': 0},
            'nba_mcp_synthesis': {'pbp': 0, 'player_box': 0, 'team_box': 0, 'schedule': 0},
            'errors': []
        }

        logger.info(f"Initialized HooprParquetLoaderV2 (dry_run={dry_run})")
        logger.info(f"Parquet directory: {self.parquet_dir}")

    def get_db_connection(self, db_name: str):
        """Get database connection"""
        config = self.DB_CONFIGS[db_name]
        return psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user']
        )

    def get_table_columns(self, conn, schema: str, table: str) -> Set[str]:
        """
        Get list of columns that exist in target table

        Args:
            conn: Database connection
            schema: Schema name
            table: Table name

        Returns:
            Set of column names
        """
        cache_key = f"{schema}.{table}"
        if cache_key in self._table_columns_cache:
            return self._table_columns_cache[cache_key]

        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            AND column_name NOT IN ('created_at', 'updated_at', 'id')
        """

        cursor = conn.cursor()
        try:
            cursor.execute(query, (schema, table))
            columns = {row[0] for row in cursor.fetchall()}
            self._table_columns_cache[cache_key] = columns
            logger.debug(f"Table {schema}.{table} has {len(columns)} columns")
            return columns
        finally:
            cursor.close()

    def find_parquet_files(self, season: Optional[int] = None) -> Dict[str, List[Path]]:
        """Find parquet files in backup directory"""
        files = {
            'pbp': [],
            'player_box': [],
            'team_box': [],
            'schedule': []
        }

        for data_type in files.keys():
            parquet_dir = self.parquet_dir / data_type / "parquet"
            if not parquet_dir.exists():
                continue

            pattern = f"nba_data_{season}.parquet" if season else "nba_data_*.parquet"
            found_files = list(parquet_dir.glob(pattern))

            if found_files:
                files[data_type].extend(found_files)
                logger.info(f"Found {len(found_files)} {data_type} files")

        return files

    def prepare_df_for_insert(
        self,
        df: pd.DataFrame,
        data_type: str,
        existing_columns: Set[str]
    ) -> pd.DataFrame:
        """
        Prepare DataFrame for database insertion

        Args:
            df: Source DataFrame from parquet
            data_type: Type of data
            existing_columns: Columns that exist in target table

        Returns:
            Prepared DataFrame with only matching columns
        """
        # Make a copy
        df = df.copy()

        # Apply column mappings
        if data_type in self.COLUMN_MAPPINGS:
            df = df.rename(columns=self.COLUMN_MAPPINGS[data_type])

        # Handle datetime columns
        datetime_cols = [col for col in ['game_date', 'game_datetime'] if col in df.columns]
        for col in datetime_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # Handle boolean columns
        bool_cols = [col for col in ['scoring_play', 'shooting_play', 'starter',
                                       'did_not_play', 'ejected', 'team_winner',
                                       'game_completed', 'pbp_available']
                     if col in df.columns]
        for col in bool_cols:
            df[col] = df[col].fillna(False).astype(bool)

        # Filter to only columns that exist in target table
        available_cols = [col for col in df.columns if col in existing_columns]
        missing_cols = existing_columns - set(df.columns)

        if available_cols:
            df = df[available_cols]
            logger.debug(f"Keeping {len(available_cols)} columns, skipping {len(missing_cols)} missing columns")
        else:
            logger.warning(f"No matching columns found for {data_type}!")
            return pd.DataFrame()

        # Replace NaN with None for PostgreSQL NULL
        df = df.where(pd.notna(df), None)

        return df

    def insert_batch(
        self,
        conn,
        schema: str,
        table: str,
        df: pd.DataFrame,
        data_type: str,
        batch_size: int = 1000
    ):
        """
        Insert DataFrame into database using batch inserts with UPSERT

        Args:
            conn: Database connection
            schema: Schema name
            table: Table name
            df: DataFrame to insert
            data_type: Type of data (for conflict detection)
            batch_size: Number of rows per batch
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {schema}.{table}")
            return 0

        # Get column names
        columns = df.columns.tolist()
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join([f'"{col}"' for col in columns])

        # Determine conflict column
        pk = self.PK_COLUMNS.get(data_type, 'game_id')
        if isinstance(pk, list):
            conflict_col = '(' + ', '.join(pk) + ')'
        else:
            conflict_col = pk

        # Build UPSERT query
        update_set = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in columns])

        query = f"""
            INSERT INTO {schema}.{table} ({column_names})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_col}) DO UPDATE SET
                {update_set}
        """

        # Convert DataFrame to list of tuples
        data = [tuple(row) for row in df.values]

        # Execute in batches
        cursor = conn.cursor()
        inserted = 0

        try:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                execute_batch(cursor, query, batch)
                inserted += len(batch)
                if i % (batch_size * 10) == 0 and i > 0:
                    logger.info(f"  Inserted {inserted}/{len(data)} rows")

            conn.commit()
            logger.info(f"✅ Inserted {inserted} rows into {schema}.{table}")
            return inserted

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error inserting into {schema}.{table}: {e}")
            self.stats['errors'].append(f"{schema}.{table}: {str(e)}")
            return 0
        finally:
            cursor.close()

    def load_parquet_file(
        self,
        file_path: Path,
        data_type: str,
        db_name: str
    ) -> int:
        """Load a single parquet file into database"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Loading: {file_path.name}")
        logger.info(f"Target: {db_name}.{self.DB_CONFIGS[db_name]['schema']}")
        logger.info(f"{'='*60}")

        try:
            # Read parquet file
            df = pd.read_parquet(file_path)
            logger.info(f"Read {len(df)} rows from {file_path.name}")

            if df.empty:
                logger.warning(f"Empty file: {file_path.name}")
                return 0

            if self.dry_run:
                logger.info(f"DRY RUN: Would insert {len(df)} rows")
                logger.info(f"Sample columns: {df.columns.tolist()[:10]}")
                return len(df)

            # Get database connection
            conn = self.get_db_connection(db_name)

            try:
                schema = self.DB_CONFIGS[db_name]['schema']
                table = self.TABLE_NAMES[data_type]

                # Get existing table columns
                existing_columns = self.get_table_columns(conn, schema, table)
                logger.info(f"Target table has {len(existing_columns)} columns")

                # Prepare DataFrame
                df = self.prepare_df_for_insert(df, data_type, existing_columns)

                if df.empty:
                    logger.warning(f"No matching columns, skipping {file_path.name}")
                    return 0

                # Insert data
                inserted = self.insert_batch(conn, schema, table, df, data_type)
                return inserted

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
            self.stats['errors'].append(f"{file_path.name}: {str(e)}")
            return 0

    def load_all(self, season: Optional[int] = None, databases: List[str] = None):
        """Load all parquet files into databases"""
        if databases is None:
            databases = ['nba_simulator', 'nba_mcp_synthesis']

        logger.info(f"\n{'='*80}")
        logger.info(f"HOOPR PARQUET LOADER V2 (Schema-Aware)")
        logger.info(f"{'='*80}")
        logger.info(f"Target databases: {', '.join(databases)}")
        logger.info(f"Season filter: {season or 'ALL'}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"{'='*80}\n")

        # Find parquet files
        files = self.find_parquet_files(season=season)

        # Load each file type
        for data_type, file_list in files.items():
            if not file_list:
                logger.warning(f"No {data_type} files found")
                continue

            logger.info(f"\n📊 Loading {data_type} data ({len(file_list)} files)")

            for file_path in sorted(file_list):
                for db_name in databases:
                    inserted = self.load_parquet_file(file_path, data_type, db_name)
                    self.stats[db_name][data_type] += inserted

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print loading summary"""
        logger.info(f"\n{'='*80}")
        logger.info("LOADING SUMMARY")
        logger.info(f"{'='*80}")

        for db_name in ['nba_simulator', 'nba_mcp_synthesis']:
            logger.info(f"\n{db_name}:")
            for data_type, count in self.stats[db_name].items():
                logger.info(f"  {data_type:15s}: {count:,} rows")

        if self.stats['errors']:
            logger.error(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                logger.error(f"  - {error}")
        else:
            logger.info("\n✅ No errors!")

        logger.info(f"{'='*80}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Load hoopR parquet files into PostgreSQL (Schema-Aware v2)'
    )
    parser.add_argument('--season', type=int, help='Load specific season only')
    parser.add_argument(
        '--database',
        choices=['nba_simulator', 'nba_mcp_synthesis', 'both'],
        default='both',
        help='Target database (default: both)'
    )
    parser.add_argument('--parquet-dir', type=Path, help='Parquet files directory')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual loading)')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine databases to load
    if args.database == 'both':
        databases = ['nba_simulator', 'nba_mcp_synthesis']
    else:
        databases = [args.database]

    # Create loader
    loader = HooprParquetLoaderV2(
        parquet_dir=args.parquet_dir,
        dry_run=args.dry_run
    )

    # Load data
    loader.load_all(season=args.season, databases=databases)

    # Exit with error code if there were errors
    if loader.stats['errors']:
        sys.exit(1)


if __name__ == '__main__':
    main()
