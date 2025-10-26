#!/usr/bin/env python3
"""
Test Suite: Phase 0.0015 - Increase Information Availability (rec_180)

Comprehensive tests for:
- SearchResult and RetrievalContext data structures
- ExternalResourceConnector (database connectivity and JSONB queries)
- SemanticSearchEngine (pgvector similarity search)
- InformationRetriever (context formatting and token management)
- LLMQueryHandler (query processing and follow-up generation)
- IncreaseInformationAvailability (main orchestration class)
- Integration with Phases 0.10/0.11/0.12

Created: October 25, 2025
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from unittest.mock import Mock, MagicMock, patch, call

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import implementation
impl_path = (
    project_root / "docs" / "phases" / "phase_0" / "0.15_information_availability"
)
sys.path.insert(0, str(impl_path))

from implement_rec_180 import (
    IncreaseInformationAvailability,
    ExternalResourceConnector,
    SemanticSearchEngine,
    InformationRetriever,
    LLMQueryHandler,
    SearchResult,
    RetrievalContext,
)


# =============================================================================
# Data Structure Tests
# =============================================================================


class TestSearchResult(unittest.TestCase):
    """Test suite for SearchResult dataclass"""

    def test_search_result_creation(self):
        """Test creating SearchResult with all fields"""
        result = SearchResult(
            source="player",
            entity_id="jamesle01",
            content="LeBron James statistics",
            metadata={"team": "LAL"},
            similarity_score=0.95,
        )

        self.assertEqual(result.source, "player")
        self.assertEqual(result.entity_id, "jamesle01")
        self.assertEqual(result.content, "LeBron James statistics")
        self.assertEqual(result.metadata, {"team": "LAL"})
        self.assertEqual(result.similarity_score, 0.95)
        self.assertIsInstance(result.timestamp, datetime)

    def test_search_result_to_dict(self):
        """Test SearchResult serialization to dictionary"""
        result = SearchResult(
            source="game",
            entity_id="401234567",
            content="Lakers vs Celtics",
            metadata={"score": "108-102"},
            similarity_score=0.88,
        )

        result_dict = result.to_dict()

        self.assertIn("source", result_dict)
        self.assertIn("entity_id", result_dict)
        self.assertIn("content", result_dict)
        self.assertIn("metadata", result_dict)
        self.assertIn("similarity_score", result_dict)
        self.assertIn("timestamp", result_dict)
        self.assertEqual(result_dict["source"], "game")
        self.assertEqual(result_dict["entity_id"], "401234567")

    def test_search_result_timestamp_auto_generated(self):
        """Test that timestamp is automatically generated"""
        result1 = SearchResult(
            source="player",
            entity_id="test1",
            content="test",
            metadata={},
            similarity_score=0.5,
        )

        result2 = SearchResult(
            source="player",
            entity_id="test2",
            content="test",
            metadata={},
            similarity_score=0.5,
        )

        # Timestamps should be close but not identical
        self.assertIsInstance(result1.timestamp, datetime)
        self.assertIsInstance(result2.timestamp, datetime)


class TestRetrievalContext(unittest.TestCase):
    """Test suite for RetrievalContext dataclass"""

    def test_retrieval_context_creation(self):
        """Test creating RetrievalContext"""
        results = [
            SearchResult("player", "jamesle01", "LeBron", {}, 0.9),
            SearchResult("game", "401234567", "Lakers win", {}, 0.85),
        ]

        context = RetrievalContext(
            query="Who is LeBron?",
            results=results,
            formatted_context="Formatted text",
            token_count=150,
            retrieval_time=0.235,
        )

        self.assertEqual(context.query, "Who is LeBron?")
        self.assertEqual(len(context.results), 2)
        self.assertEqual(context.formatted_context, "Formatted text")
        self.assertEqual(context.token_count, 150)
        self.assertAlmostEqual(context.retrieval_time, 0.235, places=3)

    def test_retrieval_context_to_dict(self):
        """Test RetrievalContext serialization"""
        results = [SearchResult("player", "test", "content", {}, 0.8)]

        context = RetrievalContext(
            query="test query",
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        context_dict = context.to_dict()

        self.assertIn("query", context_dict)
        self.assertIn("results", context_dict)
        self.assertIn("formatted_context", context_dict)
        self.assertIn("token_count", context_dict)
        self.assertIn("retrieval_time", context_dict)
        self.assertIsInstance(context_dict["results"], list)
        self.assertEqual(len(context_dict["results"]), 1)


# =============================================================================
# ExternalResourceConnector Tests
# =============================================================================


class TestExternalResourceConnector(unittest.TestCase):
    """Test suite for ExternalResourceConnector"""

    def setUp(self):
        """Set up test fixtures"""
        self.connection_params = {
            "host": "test-host",
            "database": "test-db",
            "user": "test-user",
            "password": "test-pass",
            "port": "5432",
        }

    def test_initialization(self):
        """Test ExternalResourceConnector initialization"""
        connector = ExternalResourceConnector(self.connection_params)

        self.assertIsNotNone(connector)
        self.assertEqual(connector.connection_params["host"], "test-host")
        self.assertEqual(connector.connection_params["database"], "test-db")
        self.assertIsNone(connector.conn)

    def test_initialization_with_defaults(self):
        """Test initialization with environment variable defaults"""
        with patch.dict(
            "os.environ",
            {
                "RDS_HOST": "env-host",
                "RDS_DATABASE": "env-db",
                "RDS_USER": "env-user",
                "RDS_PASSWORD": "env-pass",
            },
        ):
            connector = ExternalResourceConnector()

            self.assertEqual(connector.connection_params["host"], "env-host")
            self.assertEqual(connector.connection_params["database"], "env-db")

    @patch("implement_rec_180.psycopg2.connect")
    @patch("implement_rec_180.register_vector")
    def test_connect_success(self, mock_register_vector, mock_connect):
        """Test successful database connection"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        connector = ExternalResourceConnector(self.connection_params)
        connector.connect()

        self.assertEqual(connector.conn, mock_conn)
        mock_connect.assert_called_once_with(**self.connection_params)
        mock_register_vector.assert_called_once_with(mock_conn)

    @patch("implement_rec_180.psycopg2.connect")
    def test_connect_failure(self, mock_connect):
        """Test connection failure handling"""
        mock_connect.side_effect = Exception("Connection failed")

        connector = ExternalResourceConnector(self.connection_params)

        with self.assertRaises(Exception) as context:
            connector.connect()

        self.assertIn("Connection failed", str(context.exception))

    def test_query_jsonb_without_connection(self):
        """Test that querying without connection raises error"""
        connector = ExternalResourceConnector(self.connection_params)

        with self.assertRaises(RuntimeError) as context:
            connector.query_jsonb_data("player")

        self.assertIn("Must call connect()", str(context.exception))

    @patch("implement_rec_180.psycopg2.connect")
    @patch("implement_rec_180.register_vector")
    def test_query_jsonb_player_data(self, mock_register_vector, mock_connect):
        """Test querying player JSONB data"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("jamesle01", {"name": "LeBron James"}),
            ("curryst01", {"name": "Stephen Curry"}),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = ExternalResourceConnector(self.connection_params)
        connector.connect()
        results = connector.query_jsonb_data("player")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "jamesle01")
        self.assertEqual(results[0]["data"], {"name": "LeBron James"})

    @patch("implement_rec_180.psycopg2.connect")
    @patch("implement_rec_180.register_vector")
    def test_query_jsonb_with_filters(self, mock_register_vector, mock_connect):
        """Test querying with filters"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = ExternalResourceConnector(self.connection_params)
        connector.connect()
        connector.query_jsonb_data("player", filters={"team": "LAL"})

        # Verify cursor.execute was called (filter logic applied)
        mock_cursor.execute.assert_called_once()

    def test_query_jsonb_invalid_entity_type(self):
        """Test querying with invalid entity type"""
        connector = ExternalResourceConnector(self.connection_params)
        connector.conn = Mock()  # Mock connection

        with self.assertRaises(ValueError) as context:
            connector.query_jsonb_data("invalid_type")

        self.assertIn("Unknown entity type", str(context.exception))

    @patch("implement_rec_180.psycopg2.connect")
    @patch("implement_rec_180.register_vector")
    def test_disconnect(self, mock_register_vector, mock_connect):
        """Test disconnection"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        connector = ExternalResourceConnector(self.connection_params)
        connector.connect()
        connector.disconnect()

        mock_conn.close.assert_called_once()


# =============================================================================
# SemanticSearchEngine Tests
# =============================================================================


class TestSemanticSearchEngine(unittest.TestCase):
    """Test suite for SemanticSearchEngine"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_conn = Mock()

    def test_initialization(self):
        """Test SemanticSearchEngine initialization"""
        engine = SemanticSearchEngine(self.mock_conn)

        self.assertIsNotNone(engine)
        self.assertEqual(engine.conn, self.mock_conn)

    def test_generate_embedding_mock(self):
        """Test embedding generation (mock)"""
        engine = SemanticSearchEngine(self.mock_conn)
        embedding = engine.generate_embedding("LeBron James stats")

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 1536)  # OpenAI ada-002 dimension

    def test_search_no_connection(self):
        """Test search without connection raises error"""
        engine = SemanticSearchEngine(None)

        with self.assertRaises(RuntimeError) as context:
            engine.search("test query")

        self.assertIn("Connection not established", str(context.exception))

    def test_search_basic(self):
        """Test basic semantic search"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("player", "jamesle01", "LeBron James", {"team": "LAL"}, 0.95),
            ("player", "curryst01", "Stephen Curry", {"team": "GSW"}, 0.88),
        ]
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.search("best players")

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results[0].entity_id, "jamesle01")
        self.assertAlmostEqual(results[0].similarity_score, 0.95, places=2)

    def test_search_with_entity_type_filter(self):
        """Test search with entity type filtering"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("player", "jamesle01", "LeBron", {}, 0.9)]
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.search("test", entity_types=["player"])

        self.assertEqual(len(results), 1)
        mock_cursor.execute.assert_called_once()

    def test_search_with_top_k(self):
        """Test search with custom top_k"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.search("test", top_k=10)

        # Verify top_k was passed to query
        call_args = mock_cursor.execute.call_args
        self.assertIn(10, call_args[0][1])  # Check parameters

    def test_search_empty_results(self):
        """Test search with no results"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.search("nonexistent query")

        self.assertEqual(len(results), 0)

    def test_search_error_handling(self):
        """Test search error handling"""
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.search("test")

        # Should return empty list on error
        self.assertEqual(len(results), 0)

    def test_multi_source_search(self):
        """Test multi-source search"""
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            [("player", "p1", "Player 1", {}, 0.95)],
            [("game", "g1", "Game 1", {}, 0.90)],
        ]
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.multi_source_search(
            "test", top_k_per_source={"player": 3, "game": 2}
        )

        self.assertEqual(len(results), 2)
        # Results should be sorted by similarity
        self.assertGreaterEqual(
            results[0].similarity_score, results[1].similarity_score
        )

    def test_multi_source_search_sorting(self):
        """Test that multi-source results are properly sorted"""
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            [("player", "p1", "P1", {}, 0.80)],  # Lower score
            [("game", "g1", "G1", {}, 0.95)],  # Higher score
        ]
        self.mock_conn.cursor.return_value = mock_cursor

        engine = SemanticSearchEngine(self.mock_conn)
        results = engine.multi_source_search(
            "test", top_k_per_source={"player": 1, "game": 1}
        )

        # First result should be the one with higher score
        self.assertEqual(results[0].source, "game")
        self.assertEqual(results[0].similarity_score, 0.95)


# =============================================================================
# InformationRetriever Tests
# =============================================================================


class TestInformationRetriever(unittest.TestCase):
    """Test suite for InformationRetriever"""

    def test_initialization(self):
        """Test InformationRetriever initialization"""
        retriever = InformationRetriever(max_context_tokens=2000)

        self.assertEqual(retriever.max_context_tokens, 2000)

    def test_initialization_default(self):
        """Test initialization with default token limit"""
        retriever = InformationRetriever()

        self.assertEqual(retriever.max_context_tokens, 3000)

    def test_estimate_tokens(self):
        """Test token estimation"""
        retriever = InformationRetriever()

        text = "This is a test" * 100  # 400 chars
        estimated = retriever.estimate_tokens(text)

        self.assertEqual(estimated, 350)  # 1400 / 4

    def test_format_for_llm_empty_results(self):
        """Test formatting with no results"""
        retriever = InformationRetriever()
        formatted = retriever.format_for_llm([])

        self.assertEqual(formatted, "No relevant information found.")

    def test_format_for_llm_single_result(self):
        """Test formatting single result"""
        retriever = InformationRetriever()
        results = [
            SearchResult(
                "player", "jamesle01", "LeBron James stats", {"team": "LAL"}, 0.95
            )
        ]

        formatted = retriever.format_for_llm(results)

        self.assertIn("PLAYER #1", formatted)
        self.assertIn("jamesle01", formatted)
        self.assertIn("LeBron James stats", formatted)
        self.assertIn("similarity: 0.950", formatted)

    def test_format_for_llm_multiple_results(self):
        """Test formatting multiple results"""
        retriever = InformationRetriever()
        results = [
            SearchResult("player", "p1", "Player 1", {}, 0.9),
            SearchResult("game", "g1", "Game 1", {}, 0.85),
            SearchResult("player", "p2", "Player 2", {}, 0.8),
        ]

        formatted = retriever.format_for_llm(results)

        self.assertIn("PLAYER #1", formatted)
        self.assertIn("GAME #2", formatted)
        self.assertIn("PLAYER #3", formatted)

    def test_format_for_llm_respects_token_limit(self):
        """Test that formatting respects token limit"""
        retriever = InformationRetriever(max_context_tokens=50)  # Very small limit

        # Create results that would exceed limit
        large_content = "x" * 1000
        results = [
            SearchResult("player", f"p{i}", large_content, {}, 0.9) for i in range(10)
        ]

        formatted = retriever.format_for_llm(results)
        token_count = retriever.estimate_tokens(formatted)

        # Should not exceed limit
        self.assertLessEqual(token_count, 50)

    def test_retrieve_context(self):
        """Test full context retrieval"""
        retriever = InformationRetriever()
        results = [SearchResult("player", "jamesle01", "LeBron", {}, 0.95)]

        context = retriever.retrieve_context("Who is LeBron?", results)

        self.assertIsInstance(context, RetrievalContext)
        self.assertEqual(context.query, "Who is LeBron?")
        self.assertEqual(len(context.results), 1)
        self.assertGreater(context.token_count, 0)
        self.assertGreater(context.retrieval_time, 0)

    def test_retrieve_context_timing(self):
        """Test that retrieval timing is recorded"""
        retriever = InformationRetriever()
        results = [SearchResult("player", "test", "content", {}, 0.8)]

        context = retriever.retrieve_context("test", results)

        # Should have positive retrieval time
        self.assertIsInstance(context.retrieval_time, float)
        self.assertGreaterEqual(context.retrieval_time, 0)


# =============================================================================
# LLMQueryHandler Tests
# =============================================================================


class TestLLMQueryHandler(unittest.TestCase):
    """Test suite for LLMQueryHandler"""

    def test_initialization(self):
        """Test LLMQueryHandler initialization"""
        handler = LLMQueryHandler()

        self.assertIsNotNone(handler)

    def test_process_query(self):
        """Test basic query processing"""
        handler = LLMQueryHandler()
        results = [SearchResult("player", "jamesle01", "LeBron", {}, 0.9)]
        context = RetrievalContext(
            query="test",
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        response = handler.process_query("Who is LeBron?", context)

        self.assertIsInstance(response, str)
        self.assertIn("Query:", response)
        self.assertIn("Who is LeBron?", response)

    def test_should_ask_followup_no_results(self):
        """Test follow-up detection with no results"""
        handler = LLMQueryHandler()
        context = RetrievalContext(
            query="test",
            results=[],  # No results
            formatted_context="",
            token_count=0,
            retrieval_time=0.1,
        )

        should_followup = handler.should_ask_followup("test", context)

        self.assertTrue(should_followup)

    def test_should_ask_followup_low_similarity(self):
        """Test follow-up detection with low similarity scores"""
        handler = LLMQueryHandler()
        results = [
            SearchResult("player", "p1", "content", {}, 0.5),  # Low score
            SearchResult("player", "p2", "content", {}, 0.6),  # Low score
        ]
        context = RetrievalContext(
            query="test",
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        should_followup = handler.should_ask_followup("test", context)

        self.assertTrue(should_followup)

    def test_should_ask_followup_short_query(self):
        """Test follow-up detection for short queries"""
        handler = LLMQueryHandler()
        results = [SearchResult("player", "p1", "content", {}, 0.9)]
        context = RetrievalContext(
            query="LeBron",  # Very short query
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        should_followup = handler.should_ask_followup("LeBron", context)

        self.assertTrue(should_followup)

    def test_should_ask_followup_good_results(self):
        """Test that follow-up not needed with good results"""
        handler = LLMQueryHandler()
        results = [
            SearchResult("player", "p1", "content", {}, 0.95),
            SearchResult("player", "p2", "content", {}, 0.90),
        ]
        context = RetrievalContext(
            query="Who are the best players in history?",  # Sufficient length
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        should_followup = handler.should_ask_followup(
            "Who are the best players in history?", context
        )

        self.assertFalse(should_followup)

    def test_generate_followup_questions_no_results(self):
        """Test follow-up generation with no results"""
        handler = LLMQueryHandler()
        context = RetrievalContext(
            query="test",
            results=[],
            formatted_context="",
            token_count=0,
            retrieval_time=0.1,
        )

        followups = handler.generate_followup_questions("test", context)

        self.assertIsInstance(followups, list)
        self.assertGreater(len(followups), 0)
        self.assertLessEqual(len(followups), 3)
        self.assertIn("rephrase", followups[0].lower())

    def test_generate_followup_questions_with_player_results(self):
        """Test follow-up generation with player results"""
        handler = LLMQueryHandler()
        results = [SearchResult("player", "p1", "content", {}, 0.8)]
        context = RetrievalContext(
            query="test",
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        followups = handler.generate_followup_questions("test", context)

        self.assertGreater(len(followups), 0)
        # Should suggest player-specific followups
        has_player_followup = any("player" in q.lower() for q in followups)
        self.assertTrue(has_player_followup)

    def test_generate_followup_questions_with_game_results(self):
        """Test follow-up generation with game results"""
        handler = LLMQueryHandler()
        results = [SearchResult("game", "g1", "content", {}, 0.8)]
        context = RetrievalContext(
            query="test",
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        followups = handler.generate_followup_questions("test", context)

        # Should suggest game-specific followups
        has_game_followup = any("game" in q.lower() for q in followups)
        self.assertTrue(has_game_followup)

    def test_generate_followup_questions_limit(self):
        """Test that follow-up questions are limited to 3"""
        handler = LLMQueryHandler()
        results = [
            SearchResult("player", "p1", "content", {}, 0.8),
            SearchResult("game", "g1", "content", {}, 0.8),
        ]
        context = RetrievalContext(
            query="test",
            results=results,
            formatted_context="formatted",
            token_count=100,
            retrieval_time=0.1,
        )

        followups = handler.generate_followup_questions("test", context)

        self.assertLessEqual(len(followups), 3)


# =============================================================================
# Main IncreaseInformationAvailability Tests
# =============================================================================


class TestIncreaseInformationAvailability(unittest.TestCase):
    """Test suite for main IncreaseInformationAvailability class"""

    def test_initialization(self):
        """Test initialization"""
        impl = IncreaseInformationAvailability()

        self.assertIsNotNone(impl)
        self.assertFalse(impl.initialized)
        self.assertIsNone(impl.resource_connector)
        self.assertIsNone(impl.search_engine)
        self.assertIsNone(impl.retriever)
        self.assertIsNone(impl.query_handler)

    def test_initialization_with_config(self):
        """Test initialization with configuration"""
        config = {"max_context_tokens": 2000, "default_top_k": 10}
        impl = IncreaseInformationAvailability(config=config)

        self.assertEqual(impl.config["max_context_tokens"], 2000)
        self.assertEqual(impl.config["default_top_k"], 10)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_setup_success(self, mock_connector_class):
        """Test successful setup"""
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        result = impl.setup()

        self.assertTrue(result["success"])
        self.assertTrue(impl.initialized)
        self.assertIsNotNone(impl.resource_connector)
        self.assertIsNotNone(impl.search_engine)
        self.assertIsNotNone(impl.retriever)
        self.assertIsNotNone(impl.query_handler)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_setup_failure(self, mock_connector_class):
        """Test setup failure handling"""
        mock_connector = Mock()
        mock_connector.connect.side_effect = Exception("Connection failed")
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        result = impl.setup()

        self.assertFalse(result["success"])
        self.assertIn("Connection failed", result["message"])
        self.assertFalse(impl.initialized)

    def test_execute_without_setup(self):
        """Test that execute fails without setup"""
        impl = IncreaseInformationAvailability()

        with self.assertRaises(RuntimeError) as context:
            impl.execute("test query")

        self.assertIn("Must call setup()", str(context.exception))

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_execute_success(self, mock_connector_class):
        """Test successful execution"""
        # Mock connector
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        # Create and setup
        impl = IncreaseInformationAvailability()
        impl.setup()

        # Mock search results
        impl.search_engine.search = Mock(
            return_value=[SearchResult("player", "jamesle01", "LeBron", {}, 0.95)]
        )

        # Execute
        result = impl.execute("Who is LeBron?")

        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "Who is LeBron?")
        self.assertIn("response", result)
        self.assertIn("context", result)
        self.assertIn("metadata", result)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_execute_with_options(self, mock_connector_class):
        """Test execution with custom options"""
        # Setup mocks
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        impl.setup()

        impl.search_engine.search = Mock(return_value=[])

        # Execute with options
        options = {"top_k": 10, "entity_types": ["player"], "include_followups": False}
        result = impl.execute("test query", options=options)

        # Verify search was called with correct params
        impl.search_engine.search.assert_called_with(
            query="test query", top_k=10, entity_types=["player"]
        )

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_execute_followup_generation(self, mock_connector_class):
        """Test that follow-ups are generated when appropriate"""
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        impl.setup()

        # Mock empty search results (should trigger follow-ups)
        impl.search_engine.search = Mock(return_value=[])

        result = impl.execute("test")

        self.assertTrue(result["success"])
        self.assertIn("followup_questions", result)
        self.assertGreater(len(result["followup_questions"]), 0)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_execute_error_handling(self, mock_connector_class):
        """Test execution error handling"""
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        impl.setup()

        # Force an error
        impl.search_engine.search = Mock(side_effect=Exception("Search failed"))

        result = impl.execute("test")

        self.assertFalse(result["success"])
        self.assertIn("message", result)

    def test_validate_not_initialized(self):
        """Test validation fails when not initialized"""
        impl = IncreaseInformationAvailability()

        is_valid = impl.validate()

        self.assertFalse(is_valid)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_validate_success(self, mock_connector_class):
        """Test successful validation"""
        mock_connector = Mock()
        mock_connector.conn = Mock()  # Valid connection
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        impl.setup()

        is_valid = impl.validate()

        self.assertTrue(is_valid)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_validate_no_connection(self, mock_connector_class):
        """Test validation fails without database connection"""
        mock_connector = Mock()
        mock_connector.conn = None  # No connection
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        # Manually set initialized to bypass setup
        impl.initialized = True
        impl.resource_connector = mock_connector
        impl.search_engine = Mock()
        impl.retriever = Mock()
        impl.query_handler = Mock()

        is_valid = impl.validate()

        self.assertFalse(is_valid)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_cleanup(self, mock_connector_class):
        """Test cleanup"""
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        impl = IncreaseInformationAvailability()
        impl.setup()
        impl.cleanup()

        mock_connector.disconnect.assert_called_once()
        self.assertFalse(impl.initialized)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_end_to_end_workflow(self, mock_connector_class):
        """Test complete end-to-end workflow"""
        # Setup mocks
        mock_connector = Mock()
        mock_conn = Mock()
        mock_connector.conn = mock_conn
        mock_connector_class.return_value = mock_connector

        # Initialize system
        config = {"max_context_tokens": 3000, "default_top_k": 5}
        system = IncreaseInformationAvailability(config=config)

        # Setup
        setup_result = system.setup()
        self.assertTrue(setup_result["success"])

        # Mock search to return results
        mock_results = [
            SearchResult("player", "jamesle01", "LeBron James", {"team": "LAL"}, 0.95),
            SearchResult("player", "curryst01", "Stephen Curry", {"team": "GSW"}, 0.90),
        ]
        system.search_engine.search = Mock(return_value=mock_results)

        # Execute query
        result = system.execute("Who are the best NBA players?")

        # Verify complete workflow
        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "Who are the best NBA players?")
        self.assertIn("response", result)
        self.assertIn("context", result)
        self.assertEqual(result["metadata"]["results_count"], 2)

        # Validate
        is_valid = system.validate()
        self.assertTrue(is_valid)

        # Cleanup
        system.cleanup()
        self.assertFalse(system.initialized)

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_multiple_queries_same_session(self, mock_connector_class):
        """Test handling multiple queries in same session"""
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        system = IncreaseInformationAvailability()
        system.setup()

        # Mock search
        system.search_engine.search = Mock(
            return_value=[SearchResult("player", "p1", "content", {}, 0.9)]
        )

        # Execute multiple queries
        result1 = system.execute("Query 1")
        result2 = system.execute("Query 2")
        result3 = system.execute("Query 3")

        self.assertTrue(result1["success"])
        self.assertTrue(result2["success"])
        self.assertTrue(result3["success"])

        # System should still be valid
        self.assertTrue(system.validate())

        system.cleanup()

    @patch("implement_rec_180.ExternalResourceConnector")
    def test_config_propagation(self, mock_connector_class):
        """Test that configuration propagates to all components"""
        mock_connector = Mock()
        mock_connector.conn = Mock()
        mock_connector_class.return_value = mock_connector

        config = {"max_context_tokens": 1500, "default_top_k": 8}
        system = IncreaseInformationAvailability(config=config)
        system.setup()

        # Check retriever received config
        self.assertEqual(system.retriever.max_context_tokens, 1500)

        system.cleanup()


# =============================================================================
# Test Runner
# =============================================================================


def run_tests():
    """Run all test suites with detailed output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestSearchResult,
        TestRetrievalContext,
        TestExternalResourceConnector,
        TestSemanticSearchEngine,
        TestInformationRetriever,
        TestLLMQueryHandler,
        TestIncreaseInformationAvailability,
        TestIntegration,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
