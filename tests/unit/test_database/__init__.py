"""
Database Unit Tests
Tests for all 54 database tables across 4 schemas

Schemas:
- public: 40 tables (games, players, teams, play_by_play, etc.)
- odds: 5 tables (bookmakers, events, market_types, odds_snapshots, scores)
- rag: 4 tables (embeddings for vector search)
- raw_data: 5 tables (staging for Medallion architecture)
"""

__all__ = [
    "test_public_schema",
    "test_odds_schema",
    "test_rag_schema",
    "test_raw_data_schema",
    "test_connection",
    "test_queries",
]
