"""
Database Module

Provides database connection pooling and query execution using existing
PostgreSQL infrastructure.
"""

from nba_simulator.database.connection import DatabaseConnection, get_connection
from nba_simulator.database.queries import execute_query, execute_many

__all__ = [
    "DatabaseConnection",
    "get_connection",
    "execute_query",
    "execute_many",
]
