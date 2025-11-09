#!/usr/bin/env python3
"""
hoopR Parquet Loader
Load hoopR parquet files into PostgreSQL databases (nba_simulator and nba_mcp_synthesis)

Usage:
    # Load all parquet files from backup directory
    python scripts/etl/load_hoopr_parquet.py

    # Load specific season
    python scripts/etl/load_hoopr_parquet.py --season 2025

    # Load to specific database
    python scripts/etl/load_hoopr_parquet.py --database nba_simulator
    python scripts/etl/load_hoopr_parquet.py --database nba_mcp_synthesis
    python scripts/etl/load_hoopr_parquet.py --database both  # Default

    # Dry run (no actual loading)
    python scripts/etl/load_hoopr_parquet.py --dry-run

Created: November 9, 2025
Purpose: Load hoopR data from parquet files into both local PostgreSQL databases
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HooprParquetLoader:
    """Load hoopR parquet files into PostgreSQL databases"""

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
        'nba_simulator': {
            'pbp': 'play_by_play_hoopr_nba',
            'player_box': 'player_box_hoopr_nba',
            'team_box': 'team_box_hoopr_nba',
            'schedule': 'schedule_hoopr_nba'
        },
        'nba_mcp_synthesis': {
            'pbp': 'play_by_play_hoopr_nba',
            'player_box': 'player_box_hoopr_nba',
            'team_box': 'team_box_hoopr_nba',
            'schedule': 'schedule_hoopr_nba'
        }
    }

    # Column mappings (DataFrame column -> PostgreSQL column)
    COLUMN_MAPPINGS = {
        'pbp': {
            'id': 'event_id',
            'type_text': 'type_text',
            'text': 'description',
            'athlete_id_1': 'athlete_id_1',
            'athlete_id_2': 'athlete_id_2',
            'athlete_id_3': 'athlete_id_3',
            'away_score': 'away_score',
            'home_score': 'home_score'
        },
        'player_box': {
            'athlete_id': 'athlete_id',
            'athlete_display_name': 'athlete_name',
            'athlete_position_abbreviation': 'athlete_position',
            'athlete_jersey': 'athlete_jersey',
            'team_abbreviation': 'team_abbrev',
            'field_goals_made': 'fgm',
            'field_goals_attempted': 'fga',
            'three_point_field_goals_made': 'fg3m',
            'three_point_field_goals_attempted': 'fg3a',
            'free_throws_made': 'ftm',
            'free_throws_attempted': 'fta',
            'offensive_rebounds': 'oreb',
            'defensive_rebounds': 'dreb',
            'turnovers': 'tov',
            'opponent_team_abbreviation': 'opponent_team_abbrev'
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
            'turnovers': 'tov',
            'opponent_team_abbreviation': 'opponent_team_abbrev'
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
            'play_by_play_available': 'pbp_available'
        }
    }

    def __init__(self, parquet_dir: Optional[Path] = None, dry_run: bool = False):
        """
        Initialize loader

        Args:
            parquet_dir: Directory containing parquet files (default: ~/Desktop/sports_data_backup/hoopR/nba)
            dry_run: If True, don't actually insert data
        """
        self.parquet_dir = parquet_dir or self.DEFAULT_PARQUET_DIR
        self.dry_run = dry_run

        # Stats
        self.stats = {
            'nba_simulator': {'pbp': 0, 'player_box': 0, 'team_box': 0, 'schedule': 0},
            'nba_mcp_synthesis': {'pbp': 0, 'player_box': 0, 'team_box': 0, 'schedule': 0},
            'errors': []
        }

        logger.info(f"Initialized HooprParquetLoader (dry_run={dry_run})")
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

    def find_parquet_files(self, season: Optional[int] = None, data_type: Optional[str] = None) -> Dict[str, List[Path]]:
        """
        Find parquet files in backup directory

        Args:
            season: Optional season filter (e.g., 2025)
            data_type: Optional data type filter ('pbp', 'player_box', 'team_box', 'schedule')

        Returns:
            Dict mapping data types to lists of parquet files
        """
        files = {
            'pbp': [],
            'player_box': [],
            'team_box': [],
            'schedule': []
        }

        # Map directory names to data types
        dir_mapping = {
            'pbp': 'pbp',
            'player_box': 'player_box',
            'team_box': 'team_box',
            'schedule': 'schedule'
        }

        for dir_name, dtype in dir_mapping.items():
            if data_type and dtype != data_type:
                continue

            parquet_dir = self.parquet_dir / dir_name / "parquet"
            if not parquet_dir.exists():
                logger.warning(f"Directory not found: {parquet_dir}")
                continue

            # Find all parquet files
            pattern = f"nba_data_{season}.parquet" if season else "nba_data_*.parquet"
            found_files = list(parquet_dir.glob(pattern))

            if found_files:
                files[dtype].extend(found_files)
                logger.info(f"Found {len(found_files)} {dtype} files in {parquet_dir}")

        return files

    def prepare_df_for_insert(self, df: pd.DataFrame, data_type: str, db_name: str) -> pd.DataFrame:
        """
        Prepare DataFrame for database insertion

        Args:
            df: Source DataFrame from parquet
            data_type: Type of data ('pbp', 'player_box', etc.)
            db_name: Target database name

        Returns:
            Prepared DataFrame with mapped columns
        """
        # Make a copy
        df = df.copy()

        # Rename columns based on mapping
        if data_type in self.COLUMN_MAPPINGS:
            df = df.rename(columns=self.COLUMN_MAPPINGS[data_type])

        # Add raw_data JSONB column (store original data)
        df['raw_data'] = df.apply(lambda row: json.dumps(row.to_dict(), default=str), axis=1)

        # Handle datetime columns
        datetime_cols = ['game_date', 'game_datetime', 'game_date_time']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Handle boolean columns
        bool_cols = ['scoring_play', 'shooting_play', 'starter', 'did_not_play', 'ejected',
                     'team_winner', 'home_winner', 'away_winner', 'game_completed',
                     'neutral_site', 'pbp_available', 'team_box_available', 'player_box_available']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        # Replace NaN with None for PostgreSQL NULL
        df = df.where(pd.notna(df), None)

        return df

    def insert_batch(self, conn, schema: str, table: str, df: pd.DataFrame, batch_size: int = 1000):
        """
        Insert DataFrame into database using batch inserts with UPSERT

        Args:
            conn: Database connection
            schema: Schema name
            table: Table name
            df: DataFrame to insert
            batch_size: Number of rows per batch
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {schema}.{table}")
            return 0

        # Get column names
        columns = df.columns.tolist()
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join([f'"{col}"' for col in columns])

        # Determine conflict column based on table
        if 'event_id' in columns:
            conflict_col = 'event_id'
        elif 'game_id' in columns and 'athlete_id' in columns:
            conflict_col = '(game_id, athlete_id)'
        elif 'game_id' in columns and 'team_id' in columns:
            conflict_col = '(game_id, team_id)'
        else:
            conflict_col = 'game_id'

        # Build UPSERT query (INSERT ... ON CONFLICT DO UPDATE)
        update_set = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in columns if col not in ['created_at']])

        query = f"""
            INSERT INTO {schema}.{table} ({column_names})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_col}) DO UPDATE SET
                {update_set},
                updated_at = CURRENT_TIMESTAMP
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
                    logger.info(f"Inserted {inserted}/{len(data)} rows into {schema}.{table}")

            conn.commit()
            logger.info(f"✅ Inserted {inserted} rows into {schema}.{table}")
            return inserted

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting into {schema}.{table}: {e}")
            self.stats['errors'].append(f"{schema}.{table}: {str(e)}")
            return 0
        finally:
            cursor.close()

    def load_parquet_file(self, file_path: Path, data_type: str, db_name: str) -> int:
        """
        Load a single parquet file into database

        Args:
            file_path: Path to parquet file
            data_type: Type of data
            db_name: Database name

        Returns:
            Number of rows inserted
        """
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

            # Prepare DataFrame
            df = self.prepare_df_for_insert(df, data_type, db_name)

            if self.dry_run:
                logger.info(f"DRY RUN: Would insert {len(df)} rows")
                logger.info(f"Sample columns: {df.columns.tolist()[:10]}")
                return len(df)

            # Get database connection
            conn = self.get_db_connection(db_name)

            try:
                # Insert data
                schema = self.DB_CONFIGS[db_name]['schema']
                table = self.TABLE_NAMES[db_name][data_type]
                inserted = self.insert_batch(conn, schema, table, df)

                return inserted

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
            self.stats['errors'].append(f"{file_path.name}: {str(e)}")
            return 0

    def load_all(self, season: Optional[int] = None, databases: List[str] = None):
        """
        Load all parquet files into databases

        Args:
            season: Optional season filter
            databases: List of databases to load into (default: both)
        """
        if databases is None:
            databases = ['nba_simulator', 'nba_mcp_synthesis']

        logger.info(f"\n{'='*80}")
        logger.info(f"HOOPR PARQUET LOADER")
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
    parser = argparse.ArgumentParser(description='Load hoopR parquet files into PostgreSQL')
    parser.add_argument('--season', type=int, help='Load specific season only')
    parser.add_argument('--database', choices=['nba_simulator', 'nba_mcp_synthesis', 'both'],
                       default='both', help='Target database (default: both)')
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
    loader = HooprParquetLoader(
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
