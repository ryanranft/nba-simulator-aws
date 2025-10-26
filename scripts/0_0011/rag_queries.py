#!/usr/bin/env python3
"""
Phase 0.0011: RAG Query Interface

Purpose: Retrieval-Augmented Generation queries for NBA data
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    from scripts.0_0011.rag_queries import RAGQueries

    rag = RAGQueries()
    context = rag.retrieve_context("Who are the best Lakers players?")
    answer = rag.generate_answer("Who are the best Lakers players?", context)
"""

import os
import sys
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.0_0011.vector_search import VectorSearch
from scripts.0_0011.openai_embedder import OpenAIEmbedder


class RAGQueries:
    """
    Retrieval-Augmented Generation system for NBA data

    Combines vector search with JSONB data to provide context-rich answers
    """

    def __init__(self):
        """Initialize RAG system"""
        self.vector_search = VectorSearch()
        self.embedder = self.vector_search.embedder
        self.conn = self.vector_search.conn
        self.cursor = self.vector_search.cursor

    def retrieve_context(
        self,
        query: str,
        entity_type: Optional[str] = None,
        k: int = 5,
        include_jsonb: bool = True
    ) -> List[Dict]:
        """
        Retrieve relevant context for a query

        Args:
            query: User query
            entity_type: Filter by entity type
            k: Number of results to retrieve
            include_jsonb: Whether to include full JSONB data

        Returns:
            List of context dictionaries
        """
        # Perform vector search
        results = self.vector_search.similarity_search(
            query,
            entity_type=entity_type,
            limit=k
        )

        if not include_jsonb:
            return results

        # Enrich with JSONB data
        enriched_results = []

        for result in results:
            entity_id = result['entity_id']
            entity_type = result['entity_type']

            # Get full JSONB data
            if entity_type == 'player':
                self.cursor.execute("""
                    SELECT data
                    FROM raw_data.nba_players
                    WHERE player_id = %s
                    LIMIT 1;
                """, (entity_id,))
            elif entity_type == 'game':
                self.cursor.execute("""
                    SELECT data
                    FROM raw_data.nba_games
                    WHERE game_id = %s
                    LIMIT 1;
                """, (entity_id,))
            else:
                enriched_results.append(result)
                continue

            row = self.cursor.fetchone()
            if row:
                result['jsonb_data'] = row[0]

            enriched_results.append(result)

        return enriched_results

    def format_context_for_llm(self, context: List[Dict]) -> str:
        """
        Format retrieved context for LLM consumption

        Args:
            context: List of context dictionaries

        Returns:
            Formatted context string
        """
        if not context:
            return "No relevant context found."

        formatted_parts = []

        for i, item in enumerate(context, 1):
            formatted_parts.append(f"[{i}] {item['text_content']}")

            # Add additional data if available
            if 'jsonb_data' in item:
                jsonb = item['jsonb_data']

                # Add selected fields based on entity type
                if item['entity_type'] == 'player':
                    if 'career_stats' in jsonb:
                        stats = jsonb['career_stats']
                        formatted_parts.append(f"    Career Stats: {json.dumps(stats)}")

                elif item['entity_type'] == 'game':
                    if 'box_score' in jsonb:
                        formatted_parts.append(f"    Box Score Available: Yes")

        return "\n".join(formatted_parts)

    def search_with_temporal_context(
        self,
        query: str,
        timestamp: Optional[str] = None,
        k: int = 5
    ) -> List[Dict]:
        """
        Search with temporal context integration

        Args:
            query: User query
            timestamp: ISO timestamp for temporal filtering
            k: Number of results

        Returns:
            List of results with temporal context
        """
        # Standard vector search
        results = self.retrieve_context(query, k=k, include_jsonb=True)

        if not timestamp:
            return results

        # Enrich with temporal data if available
        for result in results:
            entity_id = result['entity_id']
            entity_type = result['entity_type']

            if entity_type == 'player':
                # Get player stats at specific timestamp
                self.cursor.execute("""
                    SELECT
                        cumulative_points,
                        cumulative_assists,
                        cumulative_rebounds,
                        games_played
                    FROM player_snapshots
                    WHERE player_id = %s
                      AND snapshot_timestamp <= %s
                    ORDER BY snapshot_timestamp DESC
                    LIMIT 1;
                """, (entity_id, timestamp))

                row = self.cursor.fetchone()
                if row:
                    result['temporal_stats'] = {
                        'points': row[0],
                        'assists': row[1],
                        'rebounds': row[2],
                        'games_played': row[3]
                    }

        return results

    def player_comparison(
        self,
        player1_query: str,
        player2_query: str
    ) -> Dict:
        """
        Compare two players using embeddings and data

        Args:
            player1_query: Query for first player
            player2_query: Query for second player

        Returns:
            Comparison dictionary
        """
        # Find both players
        player1_results = self.retrieve_context(player1_query, entity_type='player', k=1, include_jsonb=True)
        player2_results = self.retrieve_context(player2_query, entity_type='player', k=1, include_jsonb=True)

        if not player1_results or not player2_results:
            return {
                'error': 'Could not find one or both players'
            }

        player1 = player1_results[0]
        player2 = player2_results[0]

        comparison = {
            'player1': {
                'id': player1['entity_id'],
                'name': player1.get('metadata', {}).get('player_name', player1['entity_id']),
                'description': player1['text_content'],
                'data': player1.get('jsonb_data', {})
            },
            'player2': {
                'id': player2['entity_id'],
                'name': player2.get('metadata', {}).get('player_name', player2['entity_id']),
                'description': player2['text_content'],
                'data': player2.get('jsonb_data', {})
            },
            'similarity': None
        }

        # Calculate similarity between players
        try:
            self.cursor.execute("""
                SELECT
                    1 - (e1.embedding <=> e2.embedding) as similarity
                FROM rag.nba_embeddings e1
                CROSS JOIN rag.nba_embeddings e2
                WHERE e1.entity_type = 'player' AND e1.entity_id = %s
                  AND e2.entity_type = 'player' AND e2.entity_id = %s;
            """, (player1['entity_id'], player2['entity_id']))

            row = self.cursor.fetchone()
            if row:
                comparison['similarity'] = float(row[0])

        except Exception as e:
            print(f"⚠️  Could not calculate similarity: {e}")

        return comparison

    def find_similar_games(
        self,
        game_description: str,
        k: int = 10
    ) -> List[Dict]:
        """
        Find games similar to a description

        Example: "close playoff games with game-winning shots"

        Args:
            game_description: Description of desired game characteristics
            k: Number of results

        Returns:
            List of similar games
        """
        return self.retrieve_context(
            game_description,
            entity_type='game',
            k=k,
            include_jsonb=True
        )

    def semantic_player_search(
        self,
        characteristics: str,
        k: int = 10
    ) -> List[Dict]:
        """
        Find players by characteristics

        Example: "tall point guards with good three-point shooting"

        Args:
            characteristics: Player characteristics description
            k: Number of results

        Returns:
            List of matching players
        """
        return self.retrieve_context(
            characteristics,
            entity_type='player',
            k=k,
            include_jsonb=True
        )

    def get_stats(self) -> Dict:
        """
        Get RAG system statistics

        Returns:
            Dictionary with statistics
        """
        # Get embedding statistics
        self.cursor.execute("SELECT * FROM rag.get_embedding_stats();")
        stats_rows = self.cursor.fetchall()

        stats = {
            'embeddings_by_type': {},
            'total_embeddings': 0
        }

        for row in stats_rows:
            entity_type = row[0]
            count = row[1]
            stats['embeddings_by_type'][entity_type] = {
                'count': count,
                'avg_text_length': float(row[2]) if row[2] else 0,
                'earliest_created': row[3],
                'latest_created': row[4]
            }
            stats['total_embeddings'] += count

        return stats

    def close(self):
        """Close connections"""
        self.vector_search.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='RAG queries for NBA data')
    parser.add_argument('query', nargs='+', help='Query text')
    parser.add_argument('--type', choices=['player', 'game'], help='Entity type')
    parser.add_argument('--k', type=int, default=5, help='Number of results')
    parser.add_argument('--compare', action='store_true', help='Compare two players')
    parser.add_argument('--stats', action='store_true', help='Show RAG stats')

    args = parser.parse_args()

    with RAGQueries() as rag:
        if args.stats:
            stats = rag.get_stats()
            print(f"\n{'='*60}")
            print("RAG System Statistics")
            print(f"{'='*60}\n")
            print(f"Total Embeddings: {stats['total_embeddings']:,}\n")

            for entity_type, data in stats['embeddings_by_type'].items():
                print(f"{entity_type.upper()}:")
                print(f"  Count: {data['count']:,}")
                print(f"  Avg Text Length: {data['avg_text_length']:.1f}")
                print()

        elif args.compare:
            # Expecting two player names
            query_parts = ' '.join(args.query).split(' vs ')
            if len(query_parts) != 2:
                print("❌ For comparison, use: player1 vs player2")
                sys.exit(1)

            comparison = rag.player_comparison(query_parts[0].strip(), query_parts[1].strip())

            if 'error' in comparison:
                print(f"❌ {comparison['error']}")
            else:
                print(f"\n{'='*60}")
                print("Player Comparison")
                print(f"{'='*60}\n")

                print(f"Player 1: {comparison['player1']['name']}")
                print(f"{comparison['player1']['description']}\n")

                print(f"Player 2: {comparison['player2']['name']}")
                print(f"{comparison['player2']['description']}\n")

                if comparison['similarity'] is not None:
                    print(f"Similarity Score: {comparison['similarity']:.4f}")
                print()

        else:
            query = ' '.join(args.query)
            context = rag.retrieve_context(query, entity_type=args.type, k=args.k)

            print(f"\nQuery: '{query}'")
            print(f"Found {len(context)} results\n")

            formatted_context = rag.format_context_for_llm(context)
            print(formatted_context)
            print()
