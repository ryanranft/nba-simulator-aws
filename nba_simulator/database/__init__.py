"""
Database Module

Provides connection pooling and query management for PostgreSQL.
"""

from .connection import (
    DatabaseConnection,
    get_db_connection,
    execute_query
)

__all__ = [
    'DatabaseConnection',
    'get_db_connection', 
    'execute_query'
]
