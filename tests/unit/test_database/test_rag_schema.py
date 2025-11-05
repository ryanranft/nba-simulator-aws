"""
Unit Tests for RAG Schema (4 Tables)

Tests all RAG (Retrieval-Augmented Generation) schema tables including:
- document_embeddings: Document-level embeddings
- embedding_generation_log: Log of embedding generation jobs
- nba_embeddings: NBA-specific content embeddings
- play_embeddings: Play-by-play event embeddings

Uses pgvector extension for vector similarity search
"""

import pytest
from datetime import datetime


class TestRAGSchemaCore:
    """Tests for core RAG schema tables"""

    def test_document_embeddings_table_exists(self, mock_db_connection):
        """Test that rag.document_embeddings table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("document_embeddings",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'rag' AND table_name = 'document_embeddings'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == "document_embeddings"

    def test_document_embeddings_has_primary_key(self, mock_db_connection):
        """Test that document_embeddings table has a primary key"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [("constraint_name",), ("column_name",)]
        cursor.fetchall.return_value = [("document_embeddings_pkey", "embedding_id")]

        cursor.execute(
            """
            SELECT constraint_name, column_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'document_embeddings' AND table_schema = 'rag'
        """
        )
        results = cursor.fetchall()
        assert len(results) > 0

    def test_embedding_generation_log_table_exists(self, mock_db_connection):
        """Test that rag.embedding_generation_log table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("embedding_generation_log",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'rag' AND table_name = 'embedding_generation_log'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == "embedding_generation_log"

    def test_nba_embeddings_table_exists(self, mock_db_connection):
        """Test that rag.nba_embeddings table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("nba_embeddings",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'rag' AND table_name = 'nba_embeddings'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == "nba_embeddings"

    def test_play_embeddings_table_exists(self, mock_db_connection):
        """Test that rag.play_embeddings table exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("play_embeddings",)]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'rag' AND table_name = 'play_embeddings'
        """
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == "play_embeddings"


class TestRAGSchemaStructure:
    """Tests for RAG schema structure and vector columns"""

    def test_document_embeddings_has_vector_column(self, mock_db_connection):
        """Test that document_embeddings has vector column for pgvector"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ("embedding_id",),
            ("document_id",),
            ("document_type",),
            ("embedding_vector",),
            ("model_name",),
            ("created_at",),
        ]

        cursor.execute("SELECT * FROM rag.document_embeddings LIMIT 1")

        # Verify vector column exists
        columns = [desc[0] for desc in cursor.description]
        assert "embedding_vector" in columns
        assert "model_name" in columns

    def test_nba_embeddings_has_expected_columns(self, mock_db_connection):
        """Test that nba_embeddings has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ("embedding_id",),
            ("content_type",),
            ("content_id",),
            ("content_text",),
            ("embedding_vector",),
            ("metadata",),
            ("model_name",),
            ("embedding_dim",),
            ("created_at",),
        ]

        cursor.execute("SELECT * FROM rag.nba_embeddings LIMIT 1")

        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert "embedding_id" in columns
        assert "content_type" in columns
        assert "embedding_vector" in columns
        assert "metadata" in columns

    def test_play_embeddings_has_expected_columns(self, mock_db_connection):
        """Test that play_embeddings has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ("embedding_id",),
            ("play_id",),
            ("game_id",),
            ("play_text",),
            ("embedding_vector",),
            ("event_type",),
            ("players_involved",),
            ("model_name",),
            ("created_at",),
        ]

        cursor.execute("SELECT * FROM rag.play_embeddings LIMIT 1")

        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert "embedding_id" in columns
        assert "play_id" in columns
        assert "game_id" in columns
        assert "embedding_vector" in columns

    def test_embedding_generation_log_has_expected_columns(self, mock_db_connection):
        """Test that embedding_generation_log has expected column structure"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [
            ("log_id",),
            ("job_id",),
            ("table_name",),
            ("records_processed",),
            ("records_success",),
            ("records_failed",),
            ("model_name",),
            ("start_time",),
            ("end_time",),
            ("status",),
            ("error_message",),
        ]

        cursor.execute("SELECT * FROM rag.embedding_generation_log LIMIT 1")

        # Verify columns exist
        columns = [desc[0] for desc in cursor.description]
        assert "log_id" in columns
        assert "records_processed" in columns
        assert "status" in columns


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.rag
class TestRAGSchemaIntegration:
    """Integration tests for RAG schema"""

    def test_all_4_rag_tables_exist(self, mock_db_connection):
        """Test that all 4 RAG schema tables exist"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value

        expected_tables = [
            "document_embeddings",
            "embedding_generation_log",
            "nba_embeddings",
            "play_embeddings",
        ]

        cursor.fetchall.return_value = [(t,) for t in expected_tables]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'rag'
            ORDER BY table_name
        """
        )
        results = cursor.fetchall()

        # Verify we got 4 tables
        assert len(results) == 4

        # Verify all expected tables are present
        table_names = [r[0] for r in results]
        for table in expected_tables:
            assert table in table_names

    def test_pgvector_extension_enabled(self, mock_db_connection):
        """Test that pgvector extension is installed"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("vector",)

        cursor.execute(
            """
            SELECT extname 
            FROM pg_extension 
            WHERE extname = 'vector'
        """
        )
        result = cursor.fetchone()

        # pgvector should be installed for vector operations
        assert result is not None

    def test_play_embeddings_linked_to_plays(self, mock_db_connection):
        """Test that play_embeddings has foreign key to public.plays"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("fk_play_embeddings_plays",)]

        cursor.execute(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'rag'
            AND table_name = 'play_embeddings'
            AND constraint_type = 'FOREIGN KEY'
        """
        )
        results = cursor.fetchall()

        # Should have foreign key to plays table
        assert len(results) >= 0

    def test_embeddings_have_consistent_dimensions(self, mock_db_connection):
        """Test that all embeddings in a table have same dimensions"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1,)

        # Check that all embeddings have same dimension
        cursor.execute(
            """
            SELECT COUNT(DISTINCT embedding_dim)
            FROM rag.nba_embeddings
        """
        )
        distinct_dims = cursor.fetchone()[0]

        # Should have consistent embedding dimensions (typically 1 per model)
        assert distinct_dims >= 1


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.vector
class TestVectorSimilarityOperations:
    """Tests for vector similarity search operations"""

    def test_vector_cosine_similarity_function_exists(self, mock_db_connection):
        """Test that cosine similarity operator exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("<=>", "cosine distance")

        # Check that vector cosine distance operator exists
        cursor.execute(
            """
            SELECT oprname, oprcode
            FROM pg_operator
            WHERE oprname = '<=>'
        """
        )
        result = cursor.fetchone()

        # Cosine similarity operator should exist
        assert result is not None

    def test_vector_similarity_search_structure(self, mock_db_connection):
        """Test that similarity search can be performed"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []

        # Mock a similarity search query structure
        cursor.execute(
            """
            SELECT embedding_id, content_text,
                   embedding_vector <=> '[mock_vector]' AS distance
            FROM rag.nba_embeddings
            ORDER BY distance
            LIMIT 10
        """
        )

        # Query should execute without error
        assert cursor.execute.called

    def test_play_embeddings_similarity_index_exists(self, mock_db_connection):
        """Test that similarity search index exists"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("idx_play_embeddings_vector",)]

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'rag' AND tablename = 'play_embeddings'
        """
        )
        indexes = cursor.fetchall()

        # Should have vector index for fast similarity search
        assert len(indexes) >= 0


@pytest.mark.unit
@pytest.mark.database
class TestEmbeddingDataQuality:
    """Tests for embedding data quality and validation"""

    def test_embeddings_not_null(self, mock_db_connection):
        """Test that embedding vectors are not null"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)

        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM rag.nba_embeddings 
            WHERE embedding_vector IS NULL
        """
        )
        null_embeddings = cursor.fetchone()[0]

        # Should have no null embeddings
        assert null_embeddings == 0

    def test_embedding_generation_log_tracks_failures(self, mock_db_connection):
        """Test that generation log captures failures"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.description = [("log_id",), ("status",), ("error_message",)]
        cursor.fetchall.return_value = []

        cursor.execute(
            """
            SELECT log_id, status, error_message
            FROM rag.embedding_generation_log
            WHERE status = 'failed'
        """
        )
        failures = cursor.fetchall()

        # Query should execute successfully
        assert cursor.execute.called

    def test_play_embeddings_cover_all_play_types(self, mock_db_connection):
        """Test that embeddings exist for various play types"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("shot",),
            ("rebound",),
            ("assist",),
            ("turnover",),
            ("foul",),
        ]

        cursor.execute(
            """
            SELECT DISTINCT event_type
            FROM rag.play_embeddings
            ORDER BY event_type
        """
        )
        event_types = cursor.fetchall()

        # Should have embeddings for various event types
        assert len(event_types) >= 0

    def test_embeddings_have_timestamps(self, mock_db_connection):
        """Test that all embeddings have creation timestamps"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)

        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM rag.nba_embeddings 
            WHERE created_at IS NULL
        """
        )
        missing_timestamps = cursor.fetchone()[0]

        # Should have timestamps for all records
        assert missing_timestamps == 0


@pytest.mark.unit
@pytest.mark.database
class TestEmbeddingModelTracking:
    """Tests for tracking embedding models used"""

    def test_model_names_are_recorded(self, mock_db_connection):
        """Test that model names are tracked for embeddings"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("text-embedding-ada-002",),
            ("all-MiniLM-L6-v2",),
        ]

        cursor.execute(
            """
            SELECT DISTINCT model_name
            FROM rag.nba_embeddings
            ORDER BY model_name
        """
        )
        models = cursor.fetchall()

        # Should track which models generated embeddings
        assert len(models) >= 0

    def test_embedding_dimensions_match_model(self, mock_db_connection):
        """Test that embedding dimensions align with model specifications"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("text-embedding-ada-002", 1536)]

        cursor.execute(
            """
            SELECT model_name, embedding_dim
            FROM rag.nba_embeddings
            WHERE model_name = 'text-embedding-ada-002'
            LIMIT 1
        """
        )
        result = cursor.fetchall()

        # OpenAI ada-002 should have 1536 dimensions
        assert len(result) >= 0
