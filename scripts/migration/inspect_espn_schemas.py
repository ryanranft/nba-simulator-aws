#!/usr/bin/env python3
"""
Inspect ESPN Table Schemas in Both Databases

This script inspects the table schemas in nba_simulator and nba_mcp_synthesis
to understand column differences and create proper sync mappings.

Usage:
    python scripts/migration/inspect_espn_schemas.py

Output:
    - schemas_comparison_report.md - Detailed comparison report
    - JSON file with column mappings for sync script
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SchemaInspector:
    """Inspect and compare database schemas."""

    def __init__(self):
        """Initialize inspector."""
        self.nba_simulator_config = {
            "dbname": "nba_simulator",
            "user": os.getenv("POSTGRES_USER", "ryanranft"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

        self.nba_mcp_config = {
            "dbname": "nba_mcp_synthesis",
            "user": os.getenv("POSTGRES_USER", "ryanranft"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    def get_table_schema(self, conn, schema: str, table: str) -> List[Dict]:
        """
        Get table schema information.

        Returns:
            List of column info dicts with keys: column_name, data_type, is_nullable
        """
        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (schema, table))
            return cur.fetchall()

    def get_table_row_count(self, conn, schema: str, table: str) -> int:
        """Get row count for a table."""
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                return cur.fetchone()[0]
        except Exception as e:
            logger.warning(f"Could not count {schema}.{table}: {e}")
            return 0

    def get_sample_row(self, conn, schema: str, table: str) -> Dict:
        """Get a sample row from table."""
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {schema}.{table} LIMIT 1")
                row = cur.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            logger.warning(f"Could not get sample from {schema}.{table}: {e}")
            return {}

    def inspect_database(self, db_name: str, config: Dict, tables: Dict[str, str]) -> Dict:
        """
        Inspect all tables in a database.

        Args:
            db_name: Database name
            config: Database connection config
            tables: Dict of {schema: [table_names]}

        Returns:
            Dict with schema information
        """
        logger.info(f"Inspecting {db_name}...")

        results = {}

        try:
            conn = psycopg2.connect(**config)
            logger.info(f"✓ Connected to {db_name}")

            for schema, table_list in tables.items():
                results[schema] = {}

                for table in table_list:
                    logger.info(f"  Inspecting {schema}.{table}...")

                    # Get schema
                    columns = self.get_table_schema(conn, schema, table)

                    # Get row count
                    row_count = self.get_table_row_count(conn, schema, table)

                    # Get sample
                    sample = self.get_sample_row(conn, schema, table)

                    results[schema][table] = {
                        "columns": [dict(col) for col in columns],
                        "row_count": row_count,
                        "sample_row": sample,
                        "column_names": [col["column_name"] for col in columns],
                    }

                    logger.info(f"    Columns: {len(columns)}")
                    logger.info(f"    Rows: {row_count:,}")

            conn.close()

        except Exception as e:
            logger.error(f"Error inspecting {db_name}: {e}")
            raise

        return results

    def compare_schemas(self):
        """Compare schemas between both databases."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("INSPECTING ESPN SCHEMAS")
        logger.info("=" * 70)

        # Define tables to inspect
        nba_simulator_tables = {
            "espn": ["espn_games", "espn_team_stats", "espn_plays", "espn_schedules"]
        }

        nba_mcp_tables = {
            "espn_raw": ["box_score_nba_espn", "team_stats_nba_espn", "pbp_nba_espn"]
        }

        # Inspect both databases
        nba_simulator_schema = self.inspect_database(
            "nba_simulator", self.nba_simulator_config, nba_simulator_tables
        )

        nba_mcp_schema = self.inspect_database(
            "nba_mcp_synthesis", self.nba_mcp_config, nba_mcp_tables
        )

        # Generate comparison report
        self.generate_report(nba_simulator_schema, nba_mcp_schema)

        # Save to JSON
        output = {
            "inspection_date": datetime.now().isoformat(),
            "nba_simulator": nba_simulator_schema,
            "nba_mcp_synthesis": nba_mcp_schema,
        }

        output_file = "espn_schemas_inspection.json"
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2, default=str)

        logger.info(f"✓ Saved detailed inspection to {output_file}")

        return nba_simulator_schema, nba_mcp_schema

    def generate_report(self, nba_sim: Dict, nba_mcp: Dict):
        """Generate markdown comparison report."""
        report_lines = []
        report_lines.append("# ESPN Database Schema Comparison Report")
        report_lines.append(f"\n**Generated:** {datetime.now().isoformat()}\n")

        report_lines.append("## nba_simulator (espn schema)\n")
        for schema, tables in nba_sim.items():
            for table, info in tables.items():
                report_lines.append(f"### {schema}.{table}\n")
                report_lines.append(f"**Rows:** {info['row_count']:,}\n")
                report_lines.append("**Columns:**")
                for col in info["columns"]:
                    nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                    report_lines.append(
                        f"- `{col['column_name']}` {col['data_type']} {nullable}"
                    )
                report_lines.append("")

        report_lines.append("## nba_mcp_synthesis (espn_raw schema)\n")
        for schema, tables in nba_mcp.items():
            for table, info in tables.items():
                report_lines.append(f"### {schema}.{table}\n")
                report_lines.append(f"**Rows:** {info['row_count']:,}\n")
                report_lines.append("**Columns:**")
                for col in info["columns"]:
                    nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                    report_lines.append(
                        f"- `{col['column_name']}` {col['data_type']} {nullable}"
                    )
                report_lines.append("")

        report_lines.append("## Table Mappings\n")
        report_lines.append("| nba_simulator | nba_mcp_synthesis |")
        report_lines.append("|---------------|-------------------|")
        report_lines.append("| espn.espn_games | espn_raw.box_score_nba_espn |")
        report_lines.append("| espn.espn_team_stats | espn_raw.team_stats_nba_espn |")
        report_lines.append("| espn.espn_plays | espn_raw.pbp_nba_espn |")
        report_lines.append("| espn.espn_schedules | [MISSING] |")

        # Write report
        report_file = "espn_schemas_comparison_report.md"
        with open(report_file, "w") as f:
            f.write("\n".join(report_lines))

        logger.info(f"✓ Saved comparison report to {report_file}")


def main():
    """Main entry point."""
    inspector = SchemaInspector()
    inspector.compare_schemas()

    logger.info("")
    logger.info("=" * 70)
    logger.info("INSPECTION COMPLETE")
    logger.info("=" * 70)
    logger.info("Files created:")
    logger.info("  - espn_schemas_inspection.json")
    logger.info("  - espn_schemas_comparison_report.md")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Review the comparison report")
    logger.info("  2. Run sync script with mappings")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
