"""
Database Connection Management

Provides connection pooling and management for PostgreSQL database using
existing credentials and infrastructure.
"""

import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
from typing import Optional, Any, List, Dict
from contextlib import contextmanager
from dotenv import load_dotenv


# Load credentials from existing location
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")


class DatabaseConnection:
    """
    Database connection manager with connection pooling.

    Wraps existing psycopg2 functionality without breaking current scripts.
    """

    def __init__(self, database_url: Optional[str] = None, pool_size: int = 5):
        """
        Initialize database connection manager.

        Args:
            database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
            pool_size: Maximum number of connections in pool
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")

        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment")

        self.pool_size = pool_size
        self._pool: Optional[psycopg2.pool.SimpleConnectionPool] = None

    def _get_pool(self) -> psycopg2.pool.SimpleConnectionPool:
        """
        Get or create connection pool.

        Returns:
            Connection pool
        """
        if self._pool is None:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min connections
                self.pool_size,  # max connections
                self.database_url,
            )

        return self._pool

    @contextmanager
    def get_connection(self):
        """
        Get database connection from pool (context manager).

        Yields:
            psycopg2 connection

        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM games LIMIT 10")
        """
        pool = self._get_pool()
        conn = pool.getconn()

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)

    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Get database cursor (context manager).

        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)

        Yields:
            psycopg2 cursor

        Example:
            with db.get_cursor(psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM games LIMIT 10")
                results = cursor.fetchall()
        """
        with self.get_connection() as conn:
            if cursor_factory:
                cursor = conn.cursor(cursor_factory=cursor_factory)
            else:
                cursor = conn.cursor()

            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(
        self, sql: str, params: Optional[tuple] = None, fetch_one: bool = False
    ) -> Any:
        """
        Execute SQL query and return results.

        Args:
            sql: SQL query
            params: Query parameters (for parameterized queries)
            fetch_one: If True, return single row; if False, return all rows

        Returns:
            Query results (list of tuples or single tuple)
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)

            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()

    def execute_query_dict(
        self, sql: str, params: Optional[tuple] = None, fetch_one: bool = False
    ) -> Any:
        """
        Execute SQL query and return results as dictionaries.

        Args:
            sql: SQL query
            params: Query parameters
            fetch_one: If True, return single dict; if False, return list of dicts

        Returns:
            Query results as dictionaries
        """
        with self.get_cursor(psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql, params)

            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()

    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        Execute SQL query multiple times with different parameters.

        Args:
            sql: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_cursor() as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount

    def close(self):
        """Close all connections in pool"""
        if self._pool:
            self._pool.closeall()
            self._pool = None


# Global connection instance
_global_connection: Optional[DatabaseConnection] = None


def get_connection(
    database_url: Optional[str] = None, pool_size: int = 5
) -> DatabaseConnection:
    """
    Get or create global database connection instance.

    Args:
        database_url: PostgreSQL connection URL (defaults to DATABASE_URL env var)
        pool_size: Maximum number of connections in pool

    Returns:
        Global DatabaseConnection instance
    """
    global _global_connection

    if _global_connection is None:
        _global_connection = DatabaseConnection(database_url, pool_size)

    return _global_connection
