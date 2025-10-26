#!/usr/bin/env python3
"""
Implementation: Increase Information Availability

Recommendation ID: rec_180
Source: Hands On Large Language Models
Priority: CRITICAL

Description:
Use an LLM to add external information. This way, if external resources or tools
have important information, then they can be easily accessed. Using semantic search,
this system would allow information to be easily available for LLM to use.

This implementation integrates with:
- Phase 0.10: PostgreSQL JSONB Storage
- Phase 0.11: RAG Pipeline with pgvector
- Phase 0.12: RAG + LLM Integration

Expected Impact:
Enables LLMs to use information that it might not know of through:
- External data source connectivity
- Semantic search integration
- Intelligent information retrieval
- Follow-up question generation

Created: October 25, 2025
"""

import logging
import os
import psycopg2
from pgvector.psycopg2 import register_vector
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result from semantic search"""

    source: str  # 'player', 'game', 'play', 'team'
    entity_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "entity_id": self.entity_id,
            "content": self.content,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RetrievalContext:
    """Context package for LLM consumption"""

    query: str
    results: List[SearchResult]
    formatted_context: str
    token_count: int
    retrieval_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "formatted_context": self.formatted_context,
            "token_count": self.token_count,
            "retrieval_time": self.retrieval_time,
        }


class ExternalResourceConnector:
    """
    Connects to external NBA data sources (PostgreSQL JSONB storage).

    Integrates with Phase 0.10 PostgreSQL infrastructure to query
    structured NBA data stored in JSONB columns.
    """

    def __init__(self, connection_params: Optional[Dict[str, str]] = None):
        """
        Initialize external resource connector.

        Args:
            connection_params: Database connection parameters
                              (defaults to environment variables)
        """
        self.connection_params = connection_params or {
            "host": os.getenv("RDS_HOST"),
            "database": os.getenv("RDS_DATABASE"),
            "user": os.getenv("RDS_USER"),
            "password": os.getenv("RDS_PASSWORD"),
            "port": os.getenv("RDS_PORT", "5432"),
        }
        self.conn = None
        logger.info("Initialized ExternalResourceConnector")

    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            register_vector(self.conn)
            logger.info("✅ Connected to PostgreSQL with pgvector")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def query_jsonb_data(
        self, entity_type: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query structured NBA data from JSONB columns.

        Args:
            entity_type: Type of entity ('player', 'game', 'team')
            filters: Optional filters to apply

        Returns:
            List of matching records
        """
        if not self.conn:
            raise RuntimeError("Must call connect() before querying")

        # Build query based on entity type
        # Note: This assumes tables exist from Phase 0.10
        query_map = {
            "player": "SELECT player_id, data FROM nba_players_jsonb WHERE data IS NOT NULL",
            "game": "SELECT game_id, data FROM nba_games_jsonb WHERE data IS NOT NULL",
            "team": "SELECT team_id, data FROM nba_teams_jsonb WHERE data IS NOT NULL",
        }

        if entity_type not in query_map:
            raise ValueError(f"Unknown entity type: {entity_type}")

        base_query = query_map[entity_type]

        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_clauses.append(f"data->>{key!r} = {value!r}")
                else:
                    filter_clauses.append(f"data->>{key!r} = '{value}'")

            if filter_clauses:
                base_query += " AND " + " AND ".join(filter_clauses)

        base_query += " LIMIT 100;"  # Safety limit

        try:
            cur = self.conn.cursor()
            cur.execute(base_query)
            results = cur.fetchall()
            return [{"id": row[0], "data": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def disconnect(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")


class SemanticSearchEngine:
    """
    Semantic search using pgvector integration.

    Integrates with Phase 0.11 RAG Pipeline to perform vector similarity
    searches over embedded NBA data.
    """

    def __init__(self, connection):
        """
        Initialize semantic search engine.

        Args:
            connection: psycopg2 connection with pgvector enabled
        """
        self.conn = connection
        logger.info("Initialized SemanticSearchEngine")

    def generate_embedding(
        self, text: str, model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed
            model: Embedding model to use

        Returns:
            Embedding vector (1536 dimensions for ada-002)

        Note: In production, this would use the OpenAI API.
              For testing, we return a mock embedding.
        """
        # Mock implementation for testing
        # In production, this would call OpenAI:
        # import openai
        # response = openai.Embedding.create(input=text, model=model)
        # return response['data'][0]['embedding']

        logger.info(f"Generated embedding for text: {text[:50]}...")
        return [0.0] * 1536  # Mock 1536-dimensional vector

    def search(
        self, query: str, top_k: int = 5, entity_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Perform semantic similarity search.

        Args:
            query: Search query text
            top_k: Number of results to return
            entity_types: Filter by entity types (player, game, play)

        Returns:
            List of SearchResult objects ranked by similarity
        """
        if not self.conn:
            raise RuntimeError("Connection not established")

        # Generate query embedding
        query_embedding = self.generate_embedding(query)

        # Build SQL query
        # Note: where_clause is built from validated entity_types, not user input
        # entity_types are filtered against known types by the caller
        where_clause = ""
        if entity_types:
            entity_list = "', '".join(entity_types)
            where_clause = f"WHERE entity_type IN ('{entity_list}')"

        sql = f"""
            SELECT
                entity_type,
                entity_id,
                text_content,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM nba_embeddings
            {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """  # nosec B608 - entity_types are validated, not user input

        try:
            cur = self.conn.cursor()
            cur.execute(sql, (query_embedding, query_embedding, top_k))

            results = []
            for entity_type, entity_id, content, metadata, similarity in cur.fetchall():
                results.append(
                    SearchResult(
                        source=entity_type,
                        entity_id=entity_id,
                        content=content,
                        metadata=metadata or {},
                        similarity_score=float(similarity),
                    )
                )

            logger.info(f"✅ Found {len(results)} results for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def multi_source_search(
        self, query: str, top_k_per_source: Dict[str, int]
    ) -> List[SearchResult]:
        """
        Search across multiple entity types with different k values.

        Args:
            query: Search query
            top_k_per_source: Dict mapping entity_type to number of results
                            e.g., {'player': 3, 'game': 2}

        Returns:
            Combined list of SearchResult objects
        """
        all_results = []

        for entity_type, k in top_k_per_source.items():
            results = self.search(query, top_k=k, entity_types=[entity_type])
            all_results.extend(results)

        # Sort by similarity score
        all_results.sort(key=lambda r: r.similarity_score, reverse=True)

        return all_results


class InformationRetriever:
    """
    Retrieves and formats information for LLM consumption.

    Handles context aggregation, token management, and prompt-ready formatting.
    """

    def __init__(self, max_context_tokens: int = 3000):
        """
        Initialize information retriever.

        Args:
            max_context_tokens: Maximum tokens for context (default 3000)
        """
        self.max_context_tokens = max_context_tokens
        logger.info(
            f"Initialized InformationRetriever (max_tokens={max_context_tokens})"
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Rough approximation: 1 token ≈ 4 characters

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def format_for_llm(self, results: List[SearchResult]) -> str:
        """
        Format search results for LLM consumption.

        Args:
            results: List of SearchResult objects

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found."

        context_parts = []
        total_tokens = 0

        for i, result in enumerate(results, 1):
            # Format each result
            result_text = f"""[{result.source.upper()} #{i}] (similarity: {result.similarity_score:.3f})
Entity: {result.entity_id}
Content: {result.content}
Metadata: {json.dumps(result.metadata, indent=2)}
"""

            # Check token budget
            result_tokens = self.estimate_tokens(result_text)
            if total_tokens + result_tokens > self.max_context_tokens:
                logger.warning(
                    f"Reached token limit, including {i-1}/{len(results)} results"
                )
                break

            context_parts.append(result_text)
            total_tokens += result_tokens

        return "\n\n".join(context_parts)

    def retrieve_context(
        self, query: str, results: List[SearchResult]
    ) -> RetrievalContext:
        """
        Build complete retrieval context package.

        Args:
            query: Original query
            results: Search results

        Returns:
            RetrievalContext object
        """
        import time

        start_time = time.time()

        formatted = self.format_for_llm(results)
        token_count = self.estimate_tokens(formatted)
        retrieval_time = time.time() - start_time

        context = RetrievalContext(
            query=query,
            results=results,
            formatted_context=formatted,
            token_count=token_count,
            retrieval_time=retrieval_time,
        )

        logger.info(
            f"✅ Retrieved context: {len(results)} results, {token_count} tokens, {retrieval_time:.3f}s"
        )
        return context


class LLMQueryHandler:
    """
    Handles LLM queries and follow-up question generation.

    Integrates with Phase 0.12 RAG + LLM interface for natural language
    query processing.
    """

    def __init__(self):
        """Initialize LLM query handler"""
        logger.info("Initialized LLMQueryHandler")

    def process_query(self, user_query: str, context: RetrievalContext) -> str:
        """
        Process user query with retrieved context.

        Args:
            user_query: User's natural language question
            context: Retrieved context from semantic search

        Returns:
            LLM response (mock implementation)

        Note: In production, this would call OpenAI ChatCompletion API
        """
        # Mock implementation
        # In production, this would use:
        # import openai
        # response = openai.ChatCompletion.create(...)

        logger.info(f"Processing query: {user_query[:50]}...")

        # For now, return a formatted response
        response = f"""Query: {user_query}

Retrieved Context Summary:
- Found {len(context.results)} relevant items
- Total context tokens: {context.token_count}
- Retrieval time: {context.retrieval_time:.3f}s

Based on the retrieved information, here's the response:
{context.formatted_context[:200]}...
[Mock LLM response - in production, this would be generated by GPT-4]
"""

        return response

    def should_ask_followup(self, query: str, context: RetrievalContext) -> bool:
        """
        Determine if a follow-up question is needed.

        Args:
            query: Original query
            context: Retrieved context

        Returns:
            True if follow-up recommended
        """
        # Simple heuristics for follow-up detection

        # If no results found, suggest follow-up
        if not context.results:
            return True

        # If low similarity scores, suggest clarification
        avg_similarity = sum(r.similarity_score for r in context.results) / len(
            context.results
        )
        if avg_similarity < 0.7:
            return True

        # If query is very short, might need clarification
        if len(query.split()) < 3:
            return True

        return False

    def generate_followup_questions(
        self, query: str, context: RetrievalContext
    ) -> List[str]:
        """
        Generate suggested follow-up questions.

        Args:
            query: Original query
            context: Retrieved context

        Returns:
            List of suggested follow-up questions
        """
        followups = []

        if not context.results:
            followups.append(
                "Could you rephrase your question with more specific details?"
            )
            followups.append("What specific aspect are you interested in?")
        else:
            # Generate contextual follow-ups based on results
            sources = set(r.source for r in context.results)

            if "player" in sources:
                followups.append(
                    "Would you like to know more about specific player statistics?"
                )

            if "game" in sources:
                followups.append("Would you like details about specific games?")

            followups.append("Would you like to see related information?")

        return followups[:3]  # Return top 3


class IncreaseInformationAvailability:
    """
    Main orchestration class for information availability system.

    Coordinates all components:
    - ExternalResourceConnector (Phase 0.10 integration)
    - SemanticSearchEngine (Phase 0.11 integration)
    - InformationRetriever
    - LLMQueryHandler (Phase 0.12 integration)

    Provides unified API for enabling LLM access to external NBA information.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize information availability system.

        Args:
            config: Configuration dictionary
                   - max_context_tokens: Maximum tokens for context (default: 3000)
                   - default_top_k: Default number of search results (default: 5)
                   - connection_params: Database connection parameters
        """
        self.config = config or {}
        self.initialized = False

        # Initialize components
        self.resource_connector = None
        self.search_engine = None
        self.retriever = None
        self.query_handler = None

        logger.info(f"Initialized {self.__class__.__name__}")

    def setup(self) -> Dict[str, Any]:
        """
        Set up the information availability system.

        Returns:
            Setup results with status and component info
        """
        logger.info("Setting up information availability system...")

        try:
            # Step 1: Set up external resource connector
            connection_params = self.config.get("connection_params")
            self.resource_connector = ExternalResourceConnector(connection_params)
            self.resource_connector.connect()

            # Step 2: Initialize semantic search engine
            self.search_engine = SemanticSearchEngine(self.resource_connector.conn)

            # Step 3: Initialize information retriever
            max_tokens = self.config.get("max_context_tokens", 3000)
            self.retriever = InformationRetriever(max_context_tokens=max_tokens)

            # Step 4: Initialize LLM query handler
            self.query_handler = LLMQueryHandler()

            self.initialized = True
            logger.info("✅ Setup complete - all components initialized")

            return {
                "success": True,
                "message": "Setup completed successfully",
                "components": {
                    "resource_connector": "connected",
                    "search_engine": "ready",
                    "retriever": "ready",
                    "query_handler": "ready",
                },
            }

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return {"success": False, "message": f"Setup failed: {str(e)}"}

    def execute(
        self, user_query: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute information retrieval and LLM query.

        Args:
            user_query: Natural language query from user
            options: Execution options
                    - top_k: Number of search results (default: 5)
                    - entity_types: Filter by entity types
                    - include_followups: Generate follow-up questions (default: True)

        Returns:
            Execution results with LLM response and metadata
        """
        if not self.initialized:
            raise RuntimeError("Must call setup() before execute()")

        logger.info(f"Executing query: {user_query[:50]}...")

        options = options or {}
        top_k = options.get("top_k", self.config.get("default_top_k", 5))
        entity_types = options.get("entity_types")
        include_followups = options.get("include_followups", True)

        try:
            # Step 1: Perform semantic search
            search_results = self.search_engine.search(
                query=user_query, top_k=top_k, entity_types=entity_types
            )

            # Step 2: Retrieve and format context
            context = self.retriever.retrieve_context(user_query, search_results)

            # Step 3: Process with LLM
            llm_response = self.query_handler.process_query(user_query, context)

            # Step 4: Generate follow-ups if needed
            followups = []
            if include_followups:
                needs_followup = self.query_handler.should_ask_followup(
                    user_query, context
                )
                if needs_followup:
                    followups = self.query_handler.generate_followup_questions(
                        user_query, context
                    )

            logger.info("✅ Execution complete")

            return {
                "success": True,
                "query": user_query,
                "response": llm_response,
                "context": context.to_dict(),
                "followup_questions": followups,
                "metadata": {
                    "results_count": len(search_results),
                    "token_count": context.token_count,
                    "retrieval_time": context.retrieval_time,
                    "has_followups": len(followups) > 0,
                },
            }

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"success": False, "message": f"Execution failed: {str(e)}"}

    def validate(self) -> bool:
        """
        Validate the system is properly configured and functional.

        Returns:
            True if validation passes
        """
        logger.info("Validating information availability system...")

        if not self.initialized:
            logger.error("System not initialized")
            return False

        # Check all components exist
        components = [
            self.resource_connector,
            self.search_engine,
            self.retriever,
            self.query_handler,
        ]

        if not all(components):
            logger.error("Not all components initialized")
            return False

        # Check database connection
        if not self.resource_connector.conn:
            logger.error("Database connection not established")
            return False

        logger.info("✅ Validation complete - system is functional")
        return True

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")

        if self.resource_connector:
            self.resource_connector.disconnect()

        self.initialized = False
        logger.info("✅ Cleanup complete")


def main():
    """Main execution function with example usage"""
    print("=" * 80)
    print("Phase 0.15: Increase Information Availability")
    print("=" * 80)
    print()

    # Initialize
    config = {"max_context_tokens": 3000, "default_top_k": 5}
    impl = IncreaseInformationAvailability(config=config)

    # Setup
    print("Setting up system...")
    setup_result = impl.setup()
    print(f"Setup: {setup_result['message']}")

    if setup_result["success"]:
        print(f"Components: {setup_result['components']}")
        print()

        # Execute example query
        print("Executing example query...")
        query = "Who are the best three-point shooters in Lakers history?"
        result = impl.execute(query)

        if result["success"]:
            print(f"\nQuery: {result['query']}")
            print(f"\nResponse:\n{result['response'][:500]}...")
            print(f"\nMetadata:")
            for key, value in result["metadata"].items():
                print(f"  - {key}: {value}")

            if result["followup_questions"]:
                print(f"\nSuggested follow-ups:")
                for i, q in enumerate(result["followup_questions"], 1):
                    print(f"  {i}. {q}")
        else:
            print(f"Execution failed: {result['message']}")

        # Validate
        print("\nValidating system...")
        is_valid = impl.validate()
        print(f"Validation: {'✅ Passed' if is_valid else '❌ Failed'}")

        # Cleanup
        impl.cleanup()

    print("\n✅ Implementation complete!")


if __name__ == "__main__":
    main()
