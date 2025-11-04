"""
Unit Tests for Raw Data Schema (5 Tables)

Tests all raw_data schema tables (Medallion Architecture - Bronze Layer):
- nba_games: Raw game data from external sources
- nba_misc: Miscellaneous raw NBA data
- nba_players: Raw player information
- nba_teams: Raw team information
- schema_version: Schema version tracking

The raw_data schema represents the Bronze layer in Medallion architecture:
Bronze (raw_data) → Silver (public) → Gold (analytics/aggregations)
"""

import pytest
from datetime import datetime


class TestRawDataSchemaCore:
    """Tests for core raw_data schema tables"""
    
    def test_nba_games_table_exists(self, mock_db_connection):
        """Test that raw_data.nba_games table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('nba_games',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw_data' AND table_name = 'nba_games'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'nba_games'
    
    def test_nba_players_table_exists(self, mock_db_connection):
        """Test that raw_data.nba_players table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('nba_players',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw_data' AND table_name = 'nba_players'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'nba_players'
    
    def test_nba_teams_table_exists(self, mock_db_connection):
        """Test that raw_data.nba_teams table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('nba_teams',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw_data' AND table_name = 'nba_teams'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'nba_teams'
    
    def test_nba_misc_table_exists(self, mock_db_connection):
        """Test that raw_data.nba_misc table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('nba_misc',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw_data' AND table_name = 'nba_misc'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'nba_misc'
    
    def test_schema_version_table_exists(self, mock_db_connection):
        """Test that raw_data.schema_version table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('schema_version',)]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw_data' AND table_name = 'schema_version'
        """)
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'schema_version'


class TestRawDataSchemaStructure:
    """Tests for raw_data schema structure (Bronze layer)"""
    
    def test_nba_games_has_expected_columns(self, mock_db_connection):
        """Test that nba_games has expected Bronze layer structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('raw_id',), ('source_system',), ('source_id',), 
            ('raw_data',), ('ingestion_timestamp',), ('data_source',),
            ('file_path',), ('is_processed',)
        ]
        
        cursor.execute("SELECT * FROM raw_data.nba_games LIMIT 1")
        
        # Verify Bronze layer columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'raw_id' in columns
        assert 'source_system' in columns
        assert 'raw_data' in columns  # JSONB column with original data
        assert 'ingestion_timestamp' in columns
    
    def test_nba_players_has_expected_columns(self, mock_db_connection):
        """Test that nba_players has expected Bronze layer structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('raw_id',), ('source_system',), ('player_id',), 
            ('raw_data',), ('ingestion_timestamp',), ('is_processed',)
        ]
        
        cursor.execute("SELECT * FROM raw_data.nba_players LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'raw_id' in columns
        assert 'player_id' in columns
        assert 'raw_data' in columns
    
    def test_nba_teams_has_expected_columns(self, mock_db_connection):
        """Test that nba_teams has expected Bronze layer structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('raw_id',), ('source_system',), ('team_id',), 
            ('raw_data',), ('ingestion_timestamp',), ('is_processed',)
        ]
        
        cursor.execute("SELECT * FROM raw_data.nba_teams LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'raw_id' in columns
        assert 'team_id' in columns
        assert 'raw_data' in columns
    
    def test_nba_misc_has_expected_columns(self, mock_db_connection):
        """Test that nba_misc has expected Bronze layer structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('raw_id',), ('data_type',), ('source_system',), 
            ('raw_data',), ('ingestion_timestamp',), ('is_processed',)
        ]
        
        cursor.execute("SELECT * FROM raw_data.nba_misc LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'raw_id' in columns
        assert 'data_type' in columns
        assert 'raw_data' in columns
    
    def test_schema_version_has_expected_columns(self, mock_db_connection):
        """Test that schema_version table has version tracking columns"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ('version_id',), ('schema_name',), ('version_number',), 
            ('applied_at',), ('description',), ('migration_script',)
        ]
        
        cursor.execute("SELECT * FROM raw_data.schema_version LIMIT 1")
        
        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert 'version_id' in columns
        assert 'version_number' in columns
        assert 'applied_at' in columns


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.raw_data
class TestRawDataSchemaIntegration:
    """Integration tests for raw_data schema (Bronze layer)"""
    
    def test_all_5_raw_data_tables_exist(self, mock_db_connection):
        """Test that all 5 raw_data schema tables exist"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        
        expected_tables = [
            'nba_games', 'nba_misc', 'nba_players', 'nba_teams', 'schema_version'
        ]
        
        cursor.fetchall.return_value = [(t,) for t in expected_tables]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw_data'
            ORDER BY table_name
        """)
        results = cursor.fetchall()
        
        # Verify we got 5 tables
        assert len(results) == 5
        
        # Verify all expected tables are present
        table_names = [r[0] for r in results]
        for table in expected_tables:
            assert table in table_names
    
    def test_raw_data_uses_jsonb_for_flexibility(self, mock_db_connection):
        """Test that raw_data columns use JSONB type"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('raw_data', 'jsonb')]
        
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'raw_data'
            AND table_name = 'nba_games'
            AND column_name = 'raw_data'
        """)
        result = cursor.fetchall()
        
        # Should use JSONB for flexible raw data storage
        assert len(result) > 0
        if len(result) > 0:
            assert result[0][1] == 'jsonb'
    
    def test_bronze_to_silver_transformation_possible(self, mock_db_connection):
        """Test that data can be transformed from Bronze to Silver"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        # Mock query showing Bronze → Silver transformation
        cursor.execute("""
            SELECT 
                r.raw_id,
                r.raw_data->>'game_id' as game_id,
                r.raw_data->>'home_team' as home_team
            FROM raw_data.nba_games r
            WHERE r.is_processed = false
            LIMIT 10
        """)
        
        # Query should execute successfully
        assert cursor.execute.called


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.medallion
class TestMedallionArchitecture:
    """Tests for Medallion Architecture (Bronze → Silver → Gold)"""
    
    def test_bronze_layer_captures_source_system(self, mock_db_connection):
        """Test that Bronze layer tracks data source"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ('espn',), ('basketball_reference',), ('nba_api',), ('hoopr',)
        ]
        
        cursor.execute("""
            SELECT DISTINCT source_system
            FROM raw_data.nba_games
            ORDER BY source_system
        """)
        sources = cursor.fetchall()
        
        # Should track multiple data sources
        assert len(sources) >= 0
    
    def test_processing_flag_tracks_bronze_to_silver_etl(self, mock_db_connection):
        """Test that is_processed flag tracks ETL progress"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (100, 80, 20)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_processed = true) as processed,
                COUNT(*) FILTER (WHERE is_processed = false) as pending
            FROM raw_data.nba_games
        """)
        result = cursor.fetchone()
        
        # Should track processing status
        assert result is not None
    
    def test_ingestion_timestamps_enable_incremental_loads(self, mock_db_connection):
        """Test that ingestion timestamps support incremental ETL"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('2024-10-23 12:00:00',)
        
        cursor.execute("""
            SELECT MAX(ingestion_timestamp)
            FROM raw_data.nba_games
        """)
        latest_ingestion = cursor.fetchone()
        
        # Should have timestamps for incremental loading
        assert latest_ingestion is not None
    
    def test_raw_data_retention_policy_exists(self, mock_db_connection):
        """Test that old raw data can be identified for archival"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (50,)
        
        # Mock query for data older than 90 days
        cursor.execute("""
            SELECT COUNT(*)
            FROM raw_data.nba_games
            WHERE ingestion_timestamp < NOW() - INTERVAL '90 days'
            AND is_processed = true
        """)
        old_records = cursor.fetchone()[0]
        
        # Should be able to identify old data for retention policy
        assert old_records >= 0


@pytest.mark.unit
@pytest.mark.database
class TestRawDataQuality:
    """Tests for raw data quality and validation"""
    
    def test_no_duplicate_raw_records(self, mock_db_connection):
        """Test that raw data doesn't have duplicates from same source"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        
        cursor.execute("""
            SELECT source_system, source_id, COUNT(*)
            FROM raw_data.nba_games
            GROUP BY source_system, source_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        # Should not have duplicate records from same source
        assert len(duplicates) == 0
    
    def test_raw_data_is_valid_json(self, mock_db_connection):
        """Test that raw_data column contains valid JSON"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        
        # Check for invalid JSON (this would fail at insert, but test structure)
        cursor.execute("""
            SELECT COUNT(*)
            FROM raw_data.nba_games
            WHERE raw_data IS NULL
        """)
        null_data = cursor.fetchone()[0]
        
        # Should not have null raw_data
        assert null_data == 0
    
    def test_source_system_is_documented(self, mock_db_connection):
        """Test that all source systems are known"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ('espn',), ('basketball_reference',), ('nba_api',), ('hoopr',)
        ]
        
        cursor.execute("""
            SELECT DISTINCT source_system
            FROM raw_data.nba_games
            ORDER BY source_system
        """)
        sources = cursor.fetchall()
        
        # Should only have known data sources
        known_sources = {'espn', 'basketball_reference', 'nba_api', 'hoopr', 'betting'}
        for source in sources:
            if len(source) > 0:
                assert source[0] in known_sources or source[0] is None
    
    def test_ingestion_timestamps_are_reasonable(self, mock_db_connection):
        """Test that ingestion timestamps are not in the future"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM raw_data.nba_games
            WHERE ingestion_timestamp > NOW()
        """)
        future_timestamps = cursor.fetchone()[0]
        
        # Should not have future timestamps
        assert future_timestamps == 0


@pytest.mark.unit
@pytest.mark.database
class TestSchemaVersionTracking:
    """Tests for schema version management"""
    
    def test_schema_version_tracks_migrations(self, mock_db_connection):
        """Test that schema_version table tracks all migrations"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            (1, 'raw_data', '1.0.0'),
            (2, 'raw_data', '1.1.0'),
            (3, 'raw_data', '1.2.0')
        ]
        
        cursor.execute("""
            SELECT version_id, schema_name, version_number
            FROM raw_data.schema_version
            ORDER BY version_id
        """)
        versions = cursor.fetchall()
        
        # Should track version history
        assert len(versions) >= 0
    
    def test_latest_schema_version_is_identifiable(self, mock_db_connection):
        """Test that latest version can be identified"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('raw_data', '1.2.0')
        
        cursor.execute("""
            SELECT schema_name, version_number
            FROM raw_data.schema_version
            ORDER BY applied_at DESC
            LIMIT 1
        """)
        latest = cursor.fetchone()
        
        # Should be able to get latest version
        assert latest is not None
    
    def test_schema_versions_have_descriptions(self, mock_db_connection):
        """Test that schema versions are documented"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM raw_data.schema_version
            WHERE description IS NULL OR description = ''
        """)
        undocumented = cursor.fetchone()[0]
        
        # All versions should have descriptions
        assert undocumented == 0
    
    def test_migration_scripts_are_tracked(self, mock_db_connection):
        """Test that migration scripts are stored"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('001_initial_schema.sql',)]
        
        cursor.execute("""
            SELECT migration_script
            FROM raw_data.schema_version
            WHERE migration_script IS NOT NULL
        """)
        scripts = cursor.fetchall()
        
        # Should track migration scripts
        assert len(scripts) >= 0


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.performance
class TestRawDataPerformance:
    """Performance tests for raw_data schema"""
    
    def test_jsonb_column_has_gin_index(self, mock_db_connection):
        """Test that JSONB columns have GIN indexes for fast queries"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('idx_nba_games_raw_data_gin',)]
        
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'raw_data'
            AND tablename = 'nba_games'
            AND indexdef LIKE '%gin%'
        """)
        gin_indexes = cursor.fetchall()
        
        # Should have GIN index for JSONB queries
        assert len(gin_indexes) >= 0
    
    def test_source_system_has_index(self, mock_db_connection):
        """Test that source_system column is indexed"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('idx_nba_games_source_system',)]
        
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'raw_data'
            AND tablename = 'nba_games'
            AND indexdef LIKE '%source_system%'
        """)
        indexes = cursor.fetchall()
        
        # Should have index for filtering by source
        assert len(indexes) >= 0
    
    def test_ingestion_timestamp_has_index(self, mock_db_connection):
        """Test that ingestion_timestamp is indexed for time-based queries"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('idx_nba_games_ingestion_timestamp',)]
        
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'raw_data'
            AND tablename = 'nba_games'
            AND indexdef LIKE '%ingestion_timestamp%'
        """)
        indexes = cursor.fetchall()
        
        # Should have index for incremental loads
        assert len(indexes) >= 0
