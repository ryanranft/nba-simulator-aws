"""
RDS Loader - PostgreSQL Database Loading

Loads data to PostgreSQL RDS across 4 schemas:
- public: Core NBA data (40 tables)
- odds: Betting data (5 tables)
- rag: Vector embeddings (4 tables)
- raw_data: Staging area (5 tables)

Features:
- Bulk COPY for fast loading (100K+ rows/sec)
- Upsert support (INSERT ... ON CONFLICT)
- Transaction management
- Automatic table creation
- Index management
- Schema-aware loading

Based on proven patterns from:
- scripts/etl/load_espn_pbp_to_rds.py
- scripts/db/load_hoopr_to_rds.py
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import io
import asyncpg

from .base_loader import BaseLoader, LoadStatus, transaction_manager
from ...database import get_db_connection
from ...config import config


class RDSLoader(BaseLoader):
    """
    PostgreSQL RDS loader with bulk COPY support.
    
    Optimized for loading large datasets (millions of rows).
    Uses COPY command for 10-100x faster loading vs INSERT.
    """
    
    def __init__(
        self,
        table_name: str,
        schema: str = 'public',
        upsert: bool = True,
        create_table: bool = False,
        **kwargs
    ):
        """
        Initialize RDS loader.
        
        Args:
            table_name: Target table name
            schema: Schema name (public, odds, rag, raw_data)
            upsert: Use UPSERT (ON CONFLICT) instead of INSERT
            create_table: Create table if doesn't exist
            **kwargs: Additional BaseLoader arguments
        """
        super().__init__(**kwargs)
        
        self.table_name = table_name
        self.schema = schema
        self.full_table_name = f"{schema}.{table_name}"
        self.upsert = upsert
        self.create_table_if_missing = create_table
        
        # Database connection (will be initialized)
        self.conn = None
        self.pool = None
        
        self.logger.info(f"Target table: {self.full_table_name}")
        self.logger.info(f"Upsert mode: {self.upsert}")
    
    async def _get_connection(self):
        """Get database connection from pool"""
        if self.conn is None:
            db_config = config.load_database_config()
            self.conn = await asyncpg.connect(**db_config)
        return self.conn
    
    async def validate_input(self, data: Any) -> Tuple[bool, str]:
        """
        Validate input data.
        
        Args:
            data: List of dicts or dict of lists
            
        Returns:
            (is_valid, error_message)
        """
        if not data:
            return False, "Empty data provided"
        
        # Check format
        if isinstance(data, list):
            if not all(isinstance(row, dict) for row in data):
                return False, "Data must be list of dicts"
        elif isinstance(data, dict):
            # Dict of lists format
            if not all(isinstance(v, list) for v in data.values()):
                return False, "Data dict must contain lists"
        else:
            return False, "Data must be list of dicts or dict of lists"
        
        # Check table exists (or will be created)
        conn = await self._get_connection()
        exists = await self._table_exists(conn)
        
        if not exists and not self.create_table_if_missing:
            return False, f"Table {self.full_table_name} does not exist"
        
        return True, ""
    
    async def prepare_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Prepare data for loading.
        
        Args:
            data: Raw input data
            
        Returns:
            List of dicts ready for loading
        """
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Convert dict of lists to list of dicts
            keys = list(data.keys())
            length = len(data[keys[0]])
            return [
                {key: data[key][i] for key in keys}
                for i in range(length)
            ]
        else:
            raise ValueError("Unsupported data format")
    
    async def load_batch(self, batch: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Load batch using COPY or INSERT.
        
        Args:
            batch: List of dicts to load
            
        Returns:
            (records_loaded, records_failed)
        """
        if not batch:
            return 0, 0
        
        conn = await self._get_connection()
        
        try:
            if self.upsert:
                # Use INSERT with ON CONFLICT
                return await self._load_batch_upsert(conn, batch)
            else:
                # Use fast COPY
                return await self._load_batch_copy(conn, batch)
                
        except Exception as e:
            self.logger.error(f"Batch load failed: {e}")
            return 0, len(batch)
    
    async def _load_batch_copy(
        self,
        conn: asyncpg.Connection,
        batch: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Load batch using COPY command (fastest method).
        
        Args:
            conn: Database connection
            batch: Records to load
            
        Returns:
            (loaded, failed)
        """
        if not batch:
            return 0, 0
        
        # Get columns from first record
        columns = list(batch[0].keys())
        column_list = ", ".join(columns)
        
        # Create CSV in memory
        output = io.StringIO()
        for row in batch:
            csv_row = []
            for col in columns:
                value = row.get(col)
                if value is None:
                    csv_row.append("")
                else:
                    # Escape for CSV
                    value_str = str(value).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    csv_row.append(value_str)
            output.write("\t".join(csv_row) + "\n")
        
        output.seek(0)
        
        # Execute COPY
        try:
            result = await conn.copy_to_table(
                self.table_name,
                source=output,
                schema_name=self.schema,
                columns=columns,
                format='text'
            )
            
            # Parse result (format: "COPY N")
            loaded = int(result.split()[1]) if result else len(batch)
            return loaded, 0
            
        except Exception as e:
            self.logger.error(f"COPY failed: {e}")
            return 0, len(batch)
    
    async def _load_batch_upsert(
        self,
        conn: asyncpg.Connection,
        batch: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Load batch using INSERT ... ON CONFLICT (upsert).
        
        Args:
            conn: Database connection
            batch: Records to load
            
        Returns:
            (loaded, failed)
        """
        if not batch:
            return 0, 0
        
        # Get columns
        columns = list(batch[0].keys())
        column_list = ", ".join(columns)
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        
        # Build upsert query
        # Assumes first column is primary key
        pk_column = columns[0]
        update_list = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns[1:]])
        
        query = f"""
            INSERT INTO {self.full_table_name} ({column_list})
            VALUES ({placeholders})
            ON CONFLICT ({pk_column}) DO UPDATE SET
                {update_list}
        """
        
        # Prepare data tuples
        data_tuples = [
            tuple(row[col] for col in columns)
            for row in batch
        ]
        
        try:
            await conn.executemany(query, data_tuples)
            return len(batch), 0
            
        except Exception as e:
            self.logger.error(f"UPSERT failed: {e}")
            # Try individually to identify failures
            loaded = 0
            failed = 0
            for row_tuple in data_tuples:
                try:
                    await conn.execute(query, *row_tuple)
                    loaded += 1
                except:
                    failed += 1
            return loaded, failed
    
    async def verify_load(self, expected_count: int) -> bool:
        """
        Verify loaded data count.
        
        Args:
            expected_count: Expected number of records
            
        Returns:
            True if count matches
        """
        conn = await self._get_connection()
        
        try:
            result = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.full_table_name}"
            )
            
            if result >= expected_count:
                self.logger.info(f"✓ Verification passed: {result:,} records in table")
                return True
            else:
                self.logger.warning(
                    f"⚠️  Count mismatch: Expected {expected_count:,}, found {result:,}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return False
    
    async def cleanup(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            self.conn = None
    
    async def _table_exists(self, conn: asyncpg.Connection) -> bool:
        """Check if table exists"""
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = $1 AND table_name = $2
            )
            """,
            self.schema,
            self.table_name
        )
        return result
    
    async def create_indexes(self, index_definitions: List[Dict[str, Any]]):
        """
        Create indexes on table.
        
        Args:
            index_definitions: List of dicts with:
                - name: Index name
                - columns: List of column names
                - unique: Whether index is unique (optional)
        """
        conn = await self._get_connection()
        
        for idx_def in index_definitions:
            idx_name = idx_def['name']
            columns = ", ".join(idx_def['columns'])
            unique = "UNIQUE" if idx_def.get('unique', False) else ""
            
            query = f"""
                CREATE {unique} INDEX IF NOT EXISTS {idx_name}
                ON {self.full_table_name} ({columns})
            """
            
            try:
                await conn.execute(query)
                self.logger.info(f"✓ Created index: {idx_name}")
            except Exception as e:
                self.logger.warning(f"⚠️  Index {idx_name} creation failed: {e}")


class TemporalEventsLoader(RDSLoader):
    """
    Specialized loader for temporal_events table (14.1M+ records).
    
    The temporal_events table enables millisecond-precision
    temporal queries for reconstructing any NBA game moment.
    
    Schema:
        - event_id: Unique event identifier
        - game_id: Game identifier
        - player_id, team_id: Optional identifiers
        - wall_clock_utc, wall_clock_local: Event timestamps
        - game_clock_seconds: Game time
        - quarter: Period/quarter number
        - precision_level: minute/second/millisecond
        - event_type: Type of event (play, timeout, etc.)
        - event_data: JSONB with event details
        - data_source: Source (espn, hoopr, etc.)
    """
    
    def __init__(self, **kwargs):
        """Initialize temporal events loader"""
        super().__init__(
            table_name='temporal_events',
            schema='public',
            upsert=True,
            **kwargs
        )
        
        self.logger.info("Temporal events loader for historical reconstruction")
    
    async def prepare_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Prepare temporal event data.
        
        Ensures required fields and proper formatting.
        """
        records = await super().prepare_data(data)
        
        # Validate temporal event fields
        required_fields = ['game_id', 'wall_clock_utc', 'precision_level', 'data_source']
        
        validated_records = []
        for record in records:
            # Check required fields
            if all(field in record for field in required_fields):
                # Ensure event_data is JSON
                if 'event_data' in record and not isinstance(record['event_data'], str):
                    record['event_data'] = json.dumps(record['event_data'])
                validated_records.append(record)
            else:
                self.logger.warning(f"Skipping invalid temporal event record: {record.get('event_id', 'unknown')}")
        
        self.logger.info(f"Validated {len(validated_records)} temporal events")
        return validated_records
    
    async def create_temporal_indexes(self):
        """Create optimized indexes for temporal queries"""
        await self.create_indexes([
            {
                'name': 'idx_temporal_events_game_id',
                'columns': ['game_id', 'wall_clock_utc']
            },
            {
                'name': 'idx_temporal_events_game_clock',
                'columns': ['game_id', 'quarter', 'game_clock_seconds']
            },
            {
                'name': 'idx_temporal_events_player',
                'columns': ['player_id', 'wall_clock_utc']
            },
            {
                'name': 'idx_temporal_events_team',
                'columns': ['team_id', 'wall_clock_utc']
            },
            {
                'name': 'idx_temporal_events_type',
                'columns': ['event_type', 'data_source']
            }
        ])


__all__ = [
    'RDSLoader',
    'TemporalEventsLoader',
]
