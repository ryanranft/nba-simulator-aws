#!/usr/bin/env python3
"""
NBA DDL Server - MCP Server for Database Schema Management

Provides execute_ddl tool for CREATE TABLE and CREATE VIEW operations.
Uses hierarchical secrets management for secure credential handling.
"""

import sys
import os
import json
from pathlib import Path

# Add nba-mcp-synthesis to path for unified_secrets_manager
sys.path.insert(0, "/Users/ryanranft/nba-mcp-synthesis")

from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2 import sql

# Import hierarchical secrets manager
from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)

# Initialize FastMCP server
mcp = FastMCP("nba-ddl-server")

# Load secrets using hierarchical system
load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

# Get database configuration
try:
    DB_CONFIG = get_database_config()
    print(f"✅ Database credentials loaded from hierarchical secrets", file=sys.stderr)
except Exception as e:
    print(f"❌ Failed to load database credentials: {e}", file=sys.stderr)
    sys.exit(1)


def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")


def validate_ddl_safety(ddl_statement: str) -> tuple[bool, str]:
    """
    Validate DDL statement for safety.

    Args:
        ddl_statement: The DDL SQL statement to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Convert to uppercase for checking
    upper_ddl = ddl_statement.upper().strip()

    # Check for dangerous operations
    dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER COLUMN", "RENAME"]
    for keyword in dangerous_keywords:
        if keyword in upper_ddl:
            return False, f"Dangerous operation '{keyword}' is not allowed"

    # Ensure it's a CREATE operation
    if not (
        upper_ddl.startswith("CREATE TABLE")
        or upper_ddl.startswith("CREATE VIEW")
        or upper_ddl.startswith("CREATE MATERIALIZED VIEW")
        or upper_ddl.startswith("CREATE OR REPLACE VIEW")
        or upper_ddl.startswith("CREATE OR REPLACE MATERIALIZED VIEW")
    ):
        return (
            False,
            "Only CREATE TABLE, CREATE VIEW, and CREATE MATERIALIZED VIEW operations are allowed",
        )

    return True, ""


@mcp.tool()
def execute_ddl(ddl_statement: str) -> str:
    """
    Execute a DDL statement (CREATE TABLE or CREATE VIEW only).

    Args:
        ddl_statement: SQL DDL statement to execute

    Returns:
        JSON string with execution status and details

    Examples:
        CREATE TABLE temporal_possession_stats (
            game_id INT,
            team_id INT,
            possession_count INT,
            PRIMARY KEY (game_id, team_id)
        );

        CREATE MATERIALIZED VIEW player_season_summary AS
        SELECT player_id, season, AVG(points) as avg_points
        FROM player_game_stats
        GROUP BY player_id, season;
    """
    try:
        # Validate DDL safety
        is_valid, error_msg = validate_ddl_safety(ddl_statement)
        if not is_valid:
            return json.dumps(
                {
                    "success": False,
                    "error": error_msg,
                    "statement": ddl_statement[:100],
                },
                indent=2,
            )

        # Execute DDL
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(ddl_statement)
            conn.commit()

            # Extract object name from DDL
            upper_ddl = ddl_statement.upper().strip()
            object_type = "TABLE" if "TABLE" in upper_ddl.split()[0:3] else "VIEW"

            # Try to extract name (simple parsing)
            words = ddl_statement.split()
            object_name = "unknown"
            for i, word in enumerate(words):
                if word.upper() in ["TABLE", "VIEW"]:
                    if i + 1 < len(words):
                        object_name = words[i + 1].strip("(;,")
                        break

            result = {
                "success": True,
                "message": f"{object_type} created successfully",
                "object_type": object_type,
                "object_name": object_name,
                "statement": ddl_statement,
            }

            return json.dumps(result, indent=2)

        except psycopg2.Error as e:
            conn.rollback()
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "error_code": e.pgcode,
                    "statement": ddl_statement[:200],
                },
                indent=2,
            )

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "statement": ddl_statement[:100],
            },
            indent=2,
        )


@mcp.tool()
def list_tables() -> str:
    """
    List all tables in the database.

    Returns:
        JSON string with table list
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """
        )

        tables = []
        for row in cursor.fetchall():
            tables.append({"schema": row[0], "name": row[1], "type": row[2]})

        cursor.close()
        conn.close()

        return json.dumps(
            {"success": True, "count": len(tables), "tables": tables}, indent=2
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    Get the schema definition for a table.

    Args:
        table_name: Name of the table

    Returns:
        JSON string with column definitions
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT column_name, data_type, character_maximum_length,
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """,
            (table_name,),
        )

        columns = []
        for row in cursor.fetchall():
            columns.append(
                {
                    "name": row[0],
                    "type": row[1],
                    "max_length": row[2],
                    "nullable": row[3] == "YES",
                    "default": row[4],
                }
            )

        cursor.close()
        conn.close()

        return json.dumps(
            {"success": True, "table": table_name, "columns": columns}, indent=2
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
