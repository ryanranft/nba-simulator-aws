"""
Database Connection Management

Thread-safe connection pooling for PostgreSQL.
MCP-compatible for use with Claude Code.
"""

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
import logging

from ..config import config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Thread-safe database connection pool manager.
    
    Usage:
        db = DatabaseConnection()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM games LIMIT 1")
                result = cur.fetchone()
    """
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        """Singleton pattern to ensure one pool per process"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, min_connections: int = 2, max_connections: int = 10):
        """
        Initialize connection pool.
        
        Args:
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
        """
        if self._pool is None:
            db_config = config.load_database_config()
            
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    min_connections,
                    max_connections,
                    host=db_config['host'],
                    port=db_config['port'],
                    database=db_config['database'],
                    user=db_config['user'],
                    password=db_config['password']
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            psycopg2 connection object
            
        Usage:
            with db.get_connection() as conn:
                # Use connection
                pass
        """
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries (one per row)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
    
    def execute_write(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount
    
    def close(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed")

# Convenience functions for backward compatibility
def get_db_connection():
    """Get database connection instance"""
    return DatabaseConnection()

def execute_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """Execute query using shared connection pool"""
    db = get_db_connection()
    return db.execute_query(query, params)
