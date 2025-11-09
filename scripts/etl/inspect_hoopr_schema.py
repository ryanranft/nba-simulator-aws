#!/usr/bin/env python3
"""
Inspect hoopR schema in nba_mcp_synthesis
Extract actual table structure to create corrected nba_simulator schema

Usage:
    python scripts/etl/inspect_hoopr_schema.py
"""

import psycopg2
import json

def inspect_schema():
    """Inspect nba_mcp_synthesis.hoopr_raw schema"""

    # Connect to nba_mcp_synthesis
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='nba_mcp_synthesis',
        user='ryanranft'
    )

    cursor = conn.cursor()

    # Get all tables in hoopr_raw schema
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'hoopr_raw'
        AND table_name LIKE '%hoopr_nba'
        ORDER BY table_name
    """)

    tables = [row[0] for row in cursor.fetchall()]

    print("=" * 80)
    print("nba_mcp_synthesis.hoopr_raw Schema Inspection")
    print("=" * 80)
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")

    # For each table, get column details
    for table in tables:
        print(f"\n{'=' * 80}")
        print(f"Table: hoopr_raw.{table}")
        print(f"{'=' * 80}")

        # Get columns
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'hoopr_raw'
            AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))

        columns = cursor.fetchall()

        print(f"\nColumns ({len(columns)}):")
        for col_name, data_type, max_len, nullable, default in columns:
            type_str = data_type
            if max_len:
                type_str = f"{data_type}({max_len})"
            nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"  {col_name:30s} {type_str:20s} {nullable_str:10s}{default_str}")

        # Get primary key
        cursor.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = ('hoopr_raw.' || %s)::regclass
            AND i.indisprimary
        """, (table,))

        pk_cols = [row[0] for row in cursor.fetchall()]
        if pk_cols:
            print(f"\nPrimary Key: {', '.join(pk_cols)}")

        # Get indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'hoopr_raw'
            AND tablename = %s
            AND indexname NOT LIKE '%pkey'
        """, (table,))

        indexes = cursor.fetchall()
        if indexes:
            print(f"\nIndexes ({len(indexes)}):")
            for idx_name, idx_def in indexes:
                print(f"  {idx_name}")
                print(f"    {idx_def}")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM hoopr_raw.{table}")
        count = cursor.fetchone()[0]
        print(f"\nRow count: {count:,}")

        # Get sample data for first 3 rows
        cursor.execute(f"SELECT * FROM hoopr_raw.{table} LIMIT 3")
        sample_rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]

        if sample_rows:
            print(f"\nSample data (first row):")
            for col_name, value in zip(col_names, sample_rows[0]):
                value_str = str(value)[:50] if value is not None else "NULL"
                print(f"  {col_name:30s} = {value_str}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("Schema inspection complete")
    print("=" * 80)


if __name__ == '__main__':
    try:
        inspect_schema()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. nba_mcp_synthesis database exists")
        print("  3. hoopr_raw schema has tables")
