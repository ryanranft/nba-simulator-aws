#!/usr/bin/env python3
"""
0.0011: Vector Search Queries

Purpose: Semantic search over NBA embeddings
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    from scripts.0_0011.vector_search import VectorSearch

    search = VectorSearch()
    results = search.similarity_search("best power forwards in Lakers history")
    search.print_results(results)
"""

import os
import sys
from typing import List, Dict, Optional, Tuple
import psycopg2
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.0_0011.openai_embedder import OpenAIEmbedder


class VectorSearch:
    """
    Perform vector similarity search over NBA embeddings
    """

    def __init__(self, embedder: Optional[OpenAIEmbedder] = None):
        """
        Initialize vector search

        Args:
            embedder: Optional OpenAIEmbedder instance (creates new one if not provided)
        """
        self.embedder = embedder or OpenAIEmbedder()
        self.conn = self._create_db_connection()
        self.cursor = self.conn.cursor()

    def _create_db_connection(self):
        """Create PostgreSQL database connection"""
        config = {
            'host': os.getenv('RDS_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
            'port': int(os.getenv('RDS_PORT', os.getenv('POSTGRES_PORT', '5432'))),
            'database': os.getenv('RDS_DATABASE', os.getenv('POSTGRES_DB', 'nba_data')),
            'user': os.getenv('RDS_USER', os.getenv('POSTGRES_USER', 'postgres')),
            'password': os.getenv('RDS_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
        }
        return psycopg2.connect(**config)

    def similarity_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Perform similarity search using query text

        Args:
            query: Search query text
            entity_type: Filter by entity type ('player', 'game', etc.)
            limit: Maximum number of results
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of result dictionaries
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        if not query_embedding:
            print("❌ Failed to generate query embedding")
            return []

        return self.similarity_search_by_vector(
            query_embedding,
            entity_type=entity_type,
            limit=limit,
            min_similarity=min_similarity
        )

    def similarity_search_by_vector(
        self,
        query_embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Perform similarity search using embedding vector

        Args:
            query_embedding: Query embedding vector
            entity_type: Filter by entity type
            limit: Maximum number of results
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of result dictionaries
        """
        # Build query
        query_sql = """
            SELECT
                entity_id,
                entity_type,
                text_content,
                1 - (embedding <=> %s::vector) as similarity,
                metadata
            FROM rag.nba_embeddings
            WHERE 1=1
        """

        params = [query_embedding]

        if entity_type:
            query_sql += " AND entity_type = %s"
            params.append(entity_type)

        if min_similarity > 0:
            query_sql += " AND (1 - (embedding <=> %s::vector)) >= %s"
            params.extend([query_embedding, min_similarity])

        query_sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, limit])

        # Execute query
        self.cursor.execute(query_sql, params)
        rows = self.cursor.fetchall()

        # Format results
        results = []
        for row in rows:
            results.append({
                'entity_id': row[0],
                'entity_type': row[1],
                'text_content': row[2],
                'similarity': float(row[3]),
                'metadata': row[4] or {}
            })

        return results

    def hybrid_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Perform hybrid search (keyword + semantic)

        Args:
            query: Search query text
            entity_type: Filter by entity type
            limit: Maximum number of results

        Returns:
            List of result dictionaries with combined scores
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        if not query_embedding:
            print("❌ Failed to generate query embedding")
            return []

        # Execute hybrid search using database function
        self.cursor.execute("""
            SELECT * FROM rag.hybrid_search(%s, %s::vector, %s, %s);
        """, (query, query_embedding, entity_type, limit))

        rows = self.cursor.fetchall()

        # Format results
        results = []
        for row in rows:
            results.append({
                'entity_id': row[0],
                'entity_type': row[1],
                'text_content': row[2],
                'vector_similarity': float(row[3]),
                'text_rank': float(row[4]),
                'combined_score': float(row[5]),
                'metadata': row[6] or {}
            })

        return results

    def find_similar_entities(
        self,
        entity_id: str,
        entity_type: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find entities similar to a given entity

        Args:
            entity_id: ID of reference entity
            entity_type: Type of reference entity
            limit: Maximum number of results

        Returns:
            List of similar entities
        """
        # Get embedding of reference entity
        self.cursor.execute("""
            SELECT embedding
            FROM rag.nba_embeddings
            WHERE entity_type = %s AND entity_id = %s;
        """, (entity_type, entity_id))

        row = self.cursor.fetchone()
        if not row:
            print(f"❌ Entity not found: {entity_type}/{entity_id}")
            return []

        reference_embedding = row[0]

        # Find similar entities (excluding the reference entity)
        return self.similarity_search_by_vector(
            reference_embedding,
            entity_type=entity_type,
            limit=limit + 1  # +1 because we'll filter out the reference
        )[1:]  # Skip first result (the reference entity itself)

    def print_results(self, results: List[Dict], show_metadata: bool = False):
        """
        Print search results in formatted output

        Args:
            results: List of result dictionaries
            show_metadata: Whether to show metadata
        """
        if not results:
            print("\n📭 No results found\n")
            return

        print(f"\n{'='*80}")
        print(f"Search Results ({len(results)} found)")
        print(f"{'='*80}\n")

        for i, result in enumerate(results, 1):
            entity_type = result['entity_type']
            entity_id = result['entity_id']
            text = result['text_content']

            # Get similarity score
            if 'combined_score' in result:
                score = result['combined_score']
                score_type = "Combined"
            else:
                score = result['similarity']
                score_type = "Similarity"

            print(f"{i}. [{entity_type.upper()}] {entity_id}")
            print(f"   {score_type}: {score:.4f}")
            print(f"   {text}")

            if show_metadata and result.get('metadata'):
                print(f"   Metadata: {result['metadata']}")

            print()

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Search NBA embeddings')
    parser.add_argument('query', nargs='+', help='Search query')
    parser.add_argument('--type', choices=['player', 'game'], help='Filter by entity type')
    parser.add_argument('--limit', type=int, default=10, help='Number of results')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid search')
    parser.add_argument('--metadata', action='store_true', help='Show metadata')

    args = parser.parse_args()

    query = ' '.join(args.query)

    print(f"\nSearching for: '{query}'")
    if args.type:
        print(f"Filtering by: {args.type}")
    print()

    with VectorSearch() as search:
        if args.hybrid:
            results = search.hybrid_search(query, entity_type=args.type, limit=args.limit)
        else:
            results = search.similarity_search(query, entity_type=args.type, limit=args.limit)

        search.print_results(results, show_metadata=args.metadata)
