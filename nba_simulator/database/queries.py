"""
Database Query Utilities

Provides convenient functions for executing database queries using the
connection pool.
"""

from typing import Optional, Any, List, Dict, Union
from nba_simulator.database.connection import get_connection


def execute_query(
    sql: str,
    params: Optional[Union[tuple, dict]] = None,
    fetch_one: bool = False,
    as_dict: bool = True,
) -> Any:
    """
    Execute SQL query and return results.

    Args:
        sql: SQL query
        params: Query parameters (tuple or dict for named parameters)
        fetch_one: If True, return single row; if False, return all rows
        as_dict: If True, return dicts; if False, return tuples

    Returns:
        Query results

    Example:
        # Get all games
        games = execute_query("SELECT * FROM games LIMIT 10")

        # Get single game
        game = execute_query(
            "SELECT * FROM games WHERE game_id = %s",
            params=("401584893",),
            fetch_one=True
        )

        # Get count
        count = execute_query(
            "SELECT COUNT(*) as count FROM games",
            fetch_one=True
        )
    """
    db = get_connection()

    if as_dict:
        return db.execute_query_dict(sql, params, fetch_one)
    else:
        return db.execute_query(sql, params, fetch_one)


def execute_many(sql: str, params_list: List[tuple]) -> int:
    """
    Execute SQL query multiple times with different parameters.

    Args:
        sql: SQL query with parameter placeholders
        params_list: List of parameter tuples

    Returns:
        Number of rows affected

    Example:
        # Insert multiple rows
        affected = execute_many(
            "INSERT INTO table (col1, col2) VALUES (%s, %s)",
            [("val1", "val2"), ("val3", "val4")]
        )
    """
    db = get_connection()
    return db.execute_many(sql, params_list)


def get_table_count(table_name: str) -> int:
    """
    Get row count for a table.

    Args:
        table_name: Name of table

    Returns:
        Number of rows in table

    Example:
        count = get_table_count("games")
    """
    # Validate table name to prevent SQL injection
    import re

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    result = execute_query(
        f'SELECT COUNT(*) as count FROM "{table_name}"',  # nosec B608
        fetch_one=True,
    )
    return result["count"] if result else 0


def table_exists(table_name: str) -> bool:
    """
    Check if table exists in database.

    Args:
        table_name: Name of table to check

    Returns:
        True if table exists, False otherwise
    """
    result = execute_query(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        ) as exists
        """,
        params=(table_name,),
        fetch_one=True,
    )
    return result["exists"] if result else False


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    Get schema information for a table.

    Args:
        table_name: Name of table

    Returns:
        List of column information dicts
    """
    return execute_query(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
        """,
        params=(table_name,),
    )


def get_all_tables() -> List[str]:
    """
    Get list of all tables in public schema.

    Returns:
        List of table names
    """
    results = execute_query(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
    )
    return [row["table_name"] for row in results]
