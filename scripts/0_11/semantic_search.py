#!/usr/bin/env python3
"""
Phase 0.11: Semantic Search Interface

Purpose: High-level semantic search interface for NBA data
Created: October 25, 2025
Implementation ID: rec_034_pgvector

This module provides a simplified interface for common semantic search tasks
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.0_11.rag_queries import RAGQueries


class SemanticSearch:
    """
    High-level interface for semantic search over NBA data

    Simplifies common search patterns
    """

    def __init__(self):
        """Initialize semantic search"""
        self.rag = RAGQueries()

    def search_players(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for players semantically

        Args:
            query: Natural language query
            limit: Number of results

        Returns:
            List of player results
        """
        return self.rag.semantic_player_search(query, k=limit)

    def search_games(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for games semantically

        Args:
            query: Natural language query
            limit: Number of results

        Returns:
            List of game results
        """
        return self.rag.find_similar_games(query, k=limit)

    def compare_players(self, player1: str, player2: str) -> Dict:
        """
        Compare two players

        Args:
            player1: First player name or description
            player2: Second player name or description

        Returns:
            Comparison dictionary
        """
        return self.rag.player_comparison(player1, player2)

    def close(self):
        """Close connections"""
        self.rag.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions for quick searches
def search_players(query: str, limit: int = 10) -> List[Dict]:
    """Quick player search"""
    with SemanticSearch() as search:
        return search.search_players(query, limit)


def search_games(query: str, limit: int = 10) -> List[Dict]:
    """Quick game search"""
    with SemanticSearch() as search:
        return search.search_games(query, limit)


def compare_players(player1: str, player2: str) -> Dict:
    """Quick player comparison"""
    with SemanticSearch() as search:
        return search.compare_players(player1, player2)


if __name__ == '__main__':
    # Example usage
    print("Semantic Search Examples")
    print("=" * 60)
    print()

    print("Example 1: Search for players")
    print("  search_players('tall point guards with good shooting')")
    print()

    print("Example 2: Search for games")
    print("  search_games('close playoff games with buzzer beaters')")
    print()

    print("Example 3: Compare players")
    print("  compare_players('LeBron James', 'Michael Jordan')")
    print()
