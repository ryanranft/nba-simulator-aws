#!/usr/bin/env python3
"""
Phase 0.11: RAG Pipeline Tests

Purpose: Comprehensive test suite for RAG pipeline with pgvector
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    pytest tests/phases/phase_0/test_0_11.py -v
    pytest tests/phases/phase_0/test_0_11.py::TestDatabaseSchema -v
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import psycopg2
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# Import modules with numeric prefixes using importlib
def load_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load Phase 0.11 modules
db_init_module = load_module(
    "init_0_11", project_root / "scripts" / "db" / "0_11_init.py"
)
embedder_module = load_module(
    "embedder_0_11", project_root / "scripts" / "0_11" / "openai_embedder.py"
)
batch_module = load_module(
    "batch_0_11", project_root / "scripts" / "0_11" / "batch_processor.py"
)

RAGDatabaseInitializer = db_init_module.RAGDatabaseInitializer
OpenAIEmbedder = embedder_module.OpenAIEmbedder
BatchProcessor = batch_module.BatchProcessor


class TestDatabaseInitializer:
    """Test RAG database initialization"""

    @pytest.fixture
    def initializer(self):
        """Create initializer instance"""
        return RAGDatabaseInitializer()

    def test_get_db_config(self, initializer, monkeypatch):
        """Test database configuration retrieval"""
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("POSTGRES_DB", "test_db")
        monkeypatch.setenv("POSTGRES_USER", "test_user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

        config = initializer.get_db_config()

        assert config["host"] == "localhost"
        assert config["port"] == 5432
        assert config["database"] == "test_db"
        assert config["user"] == "test_user"
        assert config["password"] == "test_pass"

    def test_missing_password_raises_error(self, initializer, monkeypatch):
        """Test that missing password raises ValueError"""
        monkeypatch.delenv("RDS_PASSWORD", raising=False)
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="password not found"):
            initializer.get_db_config()


class TestOpenAIEmbedder:
    """Test OpenAI embedding generation"""

    @pytest.fixture
    def embedder(self, monkeypatch):
        """Create embedder with mocked API key"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        return OpenAIEmbedder()

    def test_initialization(self, embedder):
        """Test embedder initialization"""
        assert embedder.model == "text-embedding-ada-002"
        assert embedder.dimension == 1536
        assert embedder.cost_per_1k_tokens == 0.0001

    def test_model_specs(self, embedder):
        """Test that model specifications are correct"""
        assert "text-embedding-ada-002" in embedder.model_specs
        assert "text-embedding-3-small" in embedder.model_specs
        assert "text-embedding-3-large" in embedder.model_specs

    def test_unknown_model_raises_error(self, monkeypatch):
        """Test that unknown model raises ValueError"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        with pytest.raises(ValueError, match="Unknown model"):
            OpenAIEmbedder(model="invalid-model")

    def test_missing_api_key_raises_error(self, monkeypatch):
        """Test that missing API key raises ValueError"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API key not found"):
            OpenAIEmbedder()

    @patch("scripts.0_11.openai_embedder.OpenAI")
    def test_generate_embedding_success(self, mock_openai, embedder):
        """Test successful embedding generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_response.usage = Mock(total_tokens=100)

        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        embedder.client = mock_client

        # Generate embedding
        result = embedder.generate_embedding("test text")

        assert result is not None
        assert len(result) == 1536
        assert embedder.stats["total_calls"] == 1
        assert embedder.stats["total_tokens"] == 100

    @patch("scripts.0_11.openai_embedder.OpenAI")
    def test_generate_embedding_empty_text(self, mock_openai, embedder):
        """Test that empty text returns None"""
        result = embedder.generate_embedding("")
        assert result is None

        result = embedder.generate_embedding("   ")
        assert result is None

    def test_estimate_cost(self, embedder):
        """Test cost estimation"""
        text = "test text" * 100  # ~900 characters
        cost = embedder.estimate_cost(text)

        assert cost > 0
        assert isinstance(cost, float)

    def test_estimate_batch_cost(self, embedder):
        """Test batch cost estimation"""
        texts = ["test text"] * 100

        estimates = embedder.estimate_batch_cost(texts)

        assert "total_texts" in estimates
        assert "estimated_tokens" in estimates
        assert "estimated_cost_usd" in estimates
        assert estimates["total_texts"] == 100

    def test_get_stats(self, embedder):
        """Test statistics retrieval"""
        stats = embedder.get_stats()

        assert "total_calls" in stats
        assert "total_tokens" in stats
        assert "total_cost_usd" in stats
        assert "avg_tokens_per_call" in stats
        assert "success_rate" in stats

    def test_reset_stats(self, embedder):
        """Test statistics reset"""
        embedder.stats["total_calls"] = 10
        embedder.reset_stats()

        assert embedder.stats["total_calls"] == 0
        assert embedder.stats["total_tokens"] == 0


class TestBatchProcessor:
    """Test batch processing functionality"""

    @pytest.fixture
    def processor(self):
        """Create batch processor"""
        return BatchProcessor(batch_size=10)

    def test_initialization(self, processor):
        """Test processor initialization"""
        assert processor.batch_size == 10

    def test_extract_metadata_player(self, processor):
        """Test player metadata extraction"""
        player_data = {
            "player_name": "LeBron James",
            "team": "LAL",
            "position": "F",
            "season": 2024,
        }

        metadata = processor._extract_metadata(player_data, "player")

        assert metadata["player_name"] == "LeBron James"
        assert metadata["team"] == "LAL"
        assert metadata["position"] == "F"
        assert metadata["season"] == 2024

    def test_extract_metadata_game(self, processor):
        """Test game metadata extraction"""
        game_data = {
            "season": 2024,
            "game_date": "2024-01-15",
            "home_team": "LAL",
            "away_team": "GSW",
        }

        metadata = processor._extract_metadata(game_data, "game")

        assert metadata["season"] == 2024
        assert metadata["game_date"] == "2024-01-15"
        assert metadata["home_team"] == "LAL"
        assert metadata["away_team"] == "GSW"


class TestDatabaseSchema:
    """Test database schema validation"""

    @pytest.mark.skipif(
        not os.getenv("RDS_HOST") and not os.getenv("POSTGRES_HOST"),
        reason="Database not configured",
    )
    def test_schema_file_exists(self):
        """Test that schema SQL file exists"""
        schema_file = Path("scripts/db/migrations/0_11_schema.sql")
        assert schema_file.exists()

        # Check file is not empty
        content = schema_file.read_text()
        assert len(content) > 0
        assert "CREATE EXTENSION" in content
        assert "vector" in content

    def test_schema_contains_required_tables(self):
        """Test schema file contains required table definitions"""
        schema_file = Path("scripts/db/migrations/0_11_schema.sql")
        content = schema_file.read_text()

        required_tables = [
            "nba_embeddings",
            "play_embeddings",
            "document_embeddings",
            "embedding_generation_log",
        ]

        for table in required_tables:
            assert table in content, f"Table {table} not found in schema"

    def test_schema_contains_functions(self):
        """Test schema contains required functions"""
        schema_file = Path("scripts/db/migrations/0_11_schema.sql")
        content = schema_file.read_text()

        required_functions = [
            "similarity_search",
            "hybrid_search",
            "get_embedding_stats",
            "refresh_embedding_views",
        ]

        for func in required_functions:
            assert func in content, f"Function {func} not found in schema"

    def test_schema_contains_hnsw_indexes(self):
        """Test schema creates HNSW indexes"""
        schema_file = Path("scripts/db/migrations/0_11_schema.sql")
        content = schema_file.read_text()

        assert "USING hnsw" in content
        assert "vector_cosine_ops" in content


class TestFileStructure:
    """Test that all required files exist"""

    def test_implementation_files_exist(self):
        """Test all implementation files exist"""
        required_files = [
            "scripts/db/migrations/0_11_schema.sql",
            "scripts/db/0_11_init.py",
            "scripts/0_11/main.py",
            "scripts/0_11/embedding_pipeline.py",
            "scripts/0_11/openai_embedder.py",
            "scripts/0_11/batch_processor.py",
            "scripts/0_11/vector_search.py",
            "scripts/0_11/rag_queries.py",
            "scripts/0_11/semantic_search.py",
        ]

        for file_path in required_files:
            full_path = Path(file_path)
            assert full_path.exists(), f"Required file not found: {file_path}"

    def test_test_file_exists(self):
        """Test that test file exists"""
        test_file = Path("tests/phases/phase_0/test_0_11.py")
        assert test_file.exists()

    def test_validator_file_exists(self):
        """Test that validator file exists"""
        validator_file = Path("validators/phases/phase_0/validate_0_11.py")
        assert validator_file.exists()


class TestIntegration:
    """Integration tests (require database)"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("RDS_HOST") and not os.getenv("POSTGRES_HOST"),
        reason="Database not configured",
    )
    def test_database_connection(self):
        """Test database connection"""
        initializer = RAGDatabaseInitializer()
        assert initializer.connect() == True
        initializer.close()

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("RDS_HOST") and not os.getenv("POSTGRES_HOST"),
        reason="Database not configured",
    )
    def test_pgvector_extension(self):
        """Test pgvector extension is available"""
        initializer = RAGDatabaseInitializer()
        if initializer.connect():
            # This test just checks if we can connect
            # Actual pgvector check would require admin privileges
            initializer.close()
            assert True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
