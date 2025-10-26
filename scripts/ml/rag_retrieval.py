"""
RAG Retrieval Module with Temporal Awareness

Retrieves relevant context from PostgreSQL using pgvector semantic search.
Integrates JSONB data, vector embeddings, and temporal snapshots.

Part of Phase 0.0012: RAG + LLM Integration (rec_188)
"""

import os
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
import openai


class TemporalRAGRetrieval:
    """Context retrieval with temporal awareness for NBA data"""

    def __init__(self, db_connection: psycopg2.extensions.connection):
        """
        Initialize RAG retrieval module.

        Args:
            db_connection: PostgreSQL connection with pgvector
        """
        self.conn = db_connection
        register_vector(self.conn)

        # Initialize OpenAI for embeddings
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("Warning: OPENAI_API_KEY not set. Embedding generation will fail.")

    def retrieve_context(
        self, query: str, query_analysis: Dict, top_k: int = 10
    ) -> List[Dict]:
        """
        Retrieve relevant context based on query analysis.

        Args:
            query: Original user query
            query_analysis: Parsed query information from QueryUnderstanding
            top_k: Number of results to retrieve

        Returns:
            List of context dictionaries with content and metadata
        """
        intent = query_analysis["intent"]
        entities = query_analysis["entities"]
        temporal = query_analysis["temporal"]

        # Route to appropriate retrieval strategy
        if intent == "comparison" and len(entities["players"]) >= 2:
            return self._retrieve_comparison_context(entities, temporal, top_k)

        elif intent == "narrative":
            return self._retrieve_narrative_context(query, temporal, top_k)

        elif intent == "statistics":
            return self._retrieve_statistical_context(entities, temporal, top_k)

        elif intent == "ranking":
            return self._retrieve_ranking_context(query, temporal, top_k)

        else:
            return self._retrieve_general_context(query, top_k)

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002", input=text
            )
            return response["data"][0]["embedding"]

        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

    def _retrieve_comparison_context(
        self, entities: Dict, temporal: Dict, top_k: int
    ) -> List[Dict]:
        """
        Retrieve context for player/team comparisons.

        Args:
            entities: Extracted entities (players, teams)
            temporal: Temporal information (season, date)
            top_k: Number of results

        Returns:
            List of player comparison contexts
        """
        players = entities.get("players", [])
        season = temporal.get("season")

        if not players:
            return []

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Get comprehensive player data for comparison
        cur.execute(
            """
            WITH player_embeddings AS (
                SELECT
                    e.entity_id as player_id,
                    e.text_content,
                    e.metadata,
                    e.embedding
                FROM nba_embeddings e
                WHERE e.entity_type = 'player'
                  AND e.metadata->>'name' = ANY(%s)
            ),
            player_data AS (
                SELECT
                    pe.player_id,
                    pe.text_content,
                    pe.metadata,
                    r.data->'career_stats' as career_stats,
                    r.data->'season_stats' as season_stats,
                    r.data->'biographical' as bio
                FROM player_embeddings pe
                LEFT JOIN raw_data.nba_players r ON pe.player_id = r.player_id
            )
            SELECT * FROM player_data;
        """,
            (players,),
        )

        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "source": "player",
                    "player_id": row["player_id"],
                    "content": row["text_content"],
                    "metadata": row["metadata"],
                    "career_stats": row["career_stats"],
                    "season_stats": row["season_stats"],
                    "biographical": row["bio"],
                }
            )

        cur.close()
        return results

    def _retrieve_narrative_context(
        self, query: str, temporal: Dict, top_k: int
    ) -> List[Dict]:
        """
        Retrieve play-by-play narrative context.

        Args:
            query: User query
            temporal: Temporal information
            top_k: Number of results

        Returns:
            List of play-by-play contexts
        """
        query_embedding = self._get_embedding(query)
        game_date = temporal.get("date")
        season = temporal.get("season")

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Search play embeddings with temporal filtering
        cur.execute(
            """
            SELECT
                entity_id as play_id,
                text_content as description,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM nba_embeddings
            WHERE entity_type = 'play'
              AND (%s IS NULL OR (metadata->>'game_date')::date = %s)
              AND (%s IS NULL OR (metadata->>'season')::int = %s)
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """,
            (
                query_embedding,
                game_date,
                game_date,
                season,
                season,
                query_embedding,
                top_k,
            ),
        )

        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "source": "play",
                    "play_id": row["play_id"],
                    "content": row["description"],
                    "metadata": row["metadata"],
                    "similarity": float(row["similarity"]),
                }
            )

        cur.close()
        return results

    def _retrieve_statistical_context(
        self, entities: Dict, temporal: Dict, top_k: int
    ) -> List[Dict]:
        """
        Retrieve statistical context for entities.

        Args:
            entities: Extracted entities
            temporal: Temporal information
            top_k: Number of results

        Returns:
            List of statistical contexts
        """
        players = entities.get("players", [])
        teams = entities.get("teams", [])
        season = temporal.get("season")

        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        results = []

        # Retrieve player statistics
        if players:
            cur.execute(
                """
                SELECT
                    e.entity_id as player_id,
                    e.metadata->>'name' as player_name,
                    r.data->'career_stats' as career_stats,
                    r.data->'season_stats' as season_stats,
                    r.data->'advanced_stats' as advanced_stats
                FROM nba_embeddings e
                LEFT JOIN raw_data.nba_players r ON e.entity_id = r.player_id
                WHERE e.entity_type = 'player'
                  AND e.metadata->>'name' = ANY(%s)
                  AND (%s IS NULL OR r.season = %s)
                LIMIT %s;
            """,
                (players, season, season, top_k),
            )

            for row in cur.fetchall():
                results.append(
                    {
                        "source": "player_stats",
                        "player_id": row["player_id"],
                        "player_name": row["player_name"],
                        "career_stats": row["career_stats"],
                        "season_stats": row["season_stats"],
                        "advanced_stats": row["advanced_stats"],
                    }
                )

        # Retrieve team statistics
        if teams:
            cur.execute(
                """
                SELECT
                    e.entity_id as team_id,
                    e.metadata->>'name' as team_name,
                    r.data->'team_stats' as team_stats,
                    r.data->'season_record' as record
                FROM nba_embeddings e
                LEFT JOIN raw_data.nba_teams r ON e.entity_id = r.team_id
                WHERE e.entity_type = 'team'
                  AND e.metadata->>'abbreviation' = ANY(%s)
                  AND (%s IS NULL OR r.season = %s)
                LIMIT %s;
            """,
                (teams, season, season, top_k),
            )

            for row in cur.fetchall():
                results.append(
                    {
                        "source": "team_stats",
                        "team_id": row["team_id"],
                        "team_name": row["team_name"],
                        "team_stats": row["team_stats"],
                        "record": row["record"],
                    }
                )

        cur.close()
        return results

    def _retrieve_ranking_context(
        self, query: str, temporal: Dict, top_k: int
    ) -> List[Dict]:
        """
        Retrieve context for ranking queries.

        Args:
            query: User query
            temporal: Temporal information
            top_k: Number of results

        Returns:
            List of ranked entities
        """
        query_embedding = self._get_embedding(query)
        season = temporal.get("season")

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Semantic search across players
        cur.execute(
            """
            SELECT
                e.entity_id as player_id,
                e.text_content as description,
                e.metadata,
                r.data->'career_stats' as stats,
                1 - (e.embedding <=> %s::vector) as similarity
            FROM nba_embeddings e
            LEFT JOIN raw_data.nba_players r ON e.entity_id = r.player_id
            WHERE e.entity_type = 'player'
              AND (%s IS NULL OR r.season = %s)
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s;
        """,
            (query_embedding, season, season, query_embedding, top_k),
        )

        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "source": "player",
                    "player_id": row["player_id"],
                    "content": row["description"],
                    "metadata": row["metadata"],
                    "stats": row["stats"],
                    "similarity": float(row["similarity"]),
                }
            )

        cur.close()
        return results

    def _retrieve_general_context(self, query: str, top_k: int) -> List[Dict]:
        """
        General context retrieval using hybrid search.

        Args:
            query: User query
            top_k: Number of results

        Returns:
            List of mixed-source contexts
        """
        query_embedding = self._get_embedding(query)

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Hybrid search across all entity types
        cur.execute(
            """
            WITH ranked_results AS (
                -- Search players (top 40%)
                (
                    SELECT
                        'player' as source,
                        entity_id,
                        text_content as content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM nba_embeddings
                    WHERE entity_type = 'player'
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                )
                UNION ALL
                -- Search games (top 30%)
                (
                    SELECT
                        'game' as source,
                        entity_id,
                        text_content as content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM nba_embeddings
                    WHERE entity_type = 'game'
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                )
                UNION ALL
                -- Search plays (top 30%)
                (
                    SELECT
                        'play' as source,
                        entity_id,
                        text_content as content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM nba_embeddings
                    WHERE entity_type = 'play'
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                )
            )
            SELECT * FROM ranked_results
            ORDER BY similarity DESC
            LIMIT %s;
        """,
            (
                query_embedding,
                query_embedding,
                int(top_k * 0.4),
                query_embedding,
                query_embedding,
                int(top_k * 0.3),
                query_embedding,
                query_embedding,
                int(top_k * 0.3),
                top_k,
            ),
        )

        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "source": row["source"],
                    "entity_id": row["entity_id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "similarity": float(row["similarity"]),
                }
            )

        cur.close()
        return results

    def enrich_with_jsonb(self, contexts: List[Dict]) -> List[Dict]:
        """
        Enrich retrieved contexts with JSONB raw data.

        Args:
            contexts: Retrieved contexts from vector search

        Returns:
            Enriched contexts with additional JSONB data
        """
        if not contexts:
            return contexts

        cur = self.conn.cursor(cursor_factory=RealDictCursor)

        for ctx in contexts:
            entity_type = ctx.get("source", "")
            entity_id = (
                ctx.get("entity_id") or ctx.get("player_id") or ctx.get("team_id")
            )

            if not entity_id:
                continue

            # Enrich based on entity type
            if entity_type == "player":
                cur.execute(
                    """
                    SELECT data
                    FROM raw_data.nba_players
                    WHERE player_id = %s
                    LIMIT 1;
                """,
                    (entity_id,),
                )

                row = cur.fetchone()
                if row:
                    ctx["raw_data"] = row["data"]

            elif entity_type == "game":
                cur.execute(
                    """
                    SELECT data
                    FROM raw_data.nba_games
                    WHERE game_id = %s
                    LIMIT 1;
                """,
                    (entity_id,),
                )

                row = cur.fetchone()
                if row:
                    ctx["raw_data"] = row["data"]

        cur.close()
        return contexts


# Standalone testing
if __name__ == "__main__":
    import sys

    # Test connection
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "nba_data"),
            user=os.getenv("POSTGRES_USER", "nba_admin"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )

        retrieval = TemporalRAGRetrieval(conn)

        # Test query
        from query_understanding import QueryUnderstanding

        qp = QueryUnderstanding(conn)
        test_query = "Who were the best three-point shooters in 2022?"

        print(f"Testing RAG Retrieval for: {test_query}")
        print("=" * 80)

        # Analyze query
        analysis = qp.analyze_query(test_query)
        print(f"\nQuery Analysis:")
        print(f"  Intent: {analysis['intent']}")
        print(f"  Type: {analysis['query_type']}")

        # Retrieve context
        contexts = retrieval.retrieve_context(test_query, analysis, top_k=5)
        print(f"\nRetrieved {len(contexts)} contexts:")

        for i, ctx in enumerate(contexts, 1):
            print(f"\n{i}. Source: {ctx['source']}")
            print(f"   Content: {ctx.get('content', 'N/A')[:100]}...")
            print(f"   Similarity: {ctx.get('similarity', 'N/A')}")

        conn.close()

    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
