#!/usr/bin/env python3
"""
Analyze Kaggle SQLite Schema

Extracts comprehensive schema information from Kaggle SQLite database
to inform PostgreSQL migration.

Outputs:
1. Detailed schema report (markdown)
2. Row counts for all tables
3. Data type mappings (SQLite → PostgreSQL)
4. Sample data for validation
5. Suggested PostgreSQL DDL

Usage:
    python scripts/analysis/analyze_kaggle_schema.py
    python scripts/analysis/analyze_kaggle_schema.py --output docs/schemas/
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import argparse


class KaggleSchemaAnalyzer:
    """Analyze Kaggle SQLite database schema"""

    # SQLite to PostgreSQL type mapping
    TYPE_MAPPING = {
        "INTEGER": "INTEGER",
        "TEXT": "TEXT",
        "REAL": "DOUBLE PRECISION",
        "NUMERIC": "NUMERIC",
        "BLOB": "BYTEA",
        "VARCHAR": "VARCHAR",
        "DATE": "DATE",
        "TIMESTAMP": "TIMESTAMP WITH TIME ZONE",
    }

    def __init__(self, db_path: Path):
        """Initialize analyzer with database path"""
        self.db_path = db_path
        self.conn = None
        self.tables = []
        self.schema_info = {}

    def connect(self):
        """Connect to SQLite database"""
        print(f"Connecting to: {self.db_path}")
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print("✓ Connected\n")

    def get_all_tables(self) -> List[str]:
        """Get list of all tables in database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        self.tables = tables
        return tables

    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        """Get schema information for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")

        columns = []
        for row in cursor.fetchall():
            col_info = {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default_value": row[4],
                "pk": bool(row[5]),
            }
            columns.append(col_info)

        return columns

    def get_row_count(self, table: str) -> int:
        """Get row count for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]

    def get_sample_data(self, table: str, limit: int = 5) -> List[Dict]:
        """Get sample rows from table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")

        columns = [desc[0] for desc in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))

        return rows

    def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        """Get foreign key constraints for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list({table})")

        fks = []
        for row in cursor.fetchall():
            fk_info = {
                "id": row[0],
                "seq": row[1],
                "table": row[2],
                "from": row[3],
                "to": row[4],
                "on_update": row[5],
                "on_delete": row[6],
                "match": row[7],
            }
            fks.append(fk_info)

        return fks

    def get_indexes(self, table: str) -> List[str]:
        """Get indexes for a table"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA index_list({table})")

        indexes = []
        for row in cursor.fetchall():
            indexes.append(row[1])  # Index name

        return indexes

    def analyze_all_tables(self):
        """Analyze all tables and store information"""
        print("Analyzing tables...\n")

        for table in self.tables:
            print(f"  Analyzing: {table}")

            schema = self.get_table_schema(table)
            row_count = self.get_row_count(table)
            sample_data = self.get_sample_data(table, limit=3)
            foreign_keys = self.get_foreign_keys(table)
            indexes = self.get_indexes(table)

            self.schema_info[table] = {
                "name": table,
                "row_count": row_count,
                "columns": schema,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "sample_data": sample_data,
            }

        print(f"\n✓ Analyzed {len(self.tables)} tables\n")

    def map_sqlite_to_postgres_type(self, sqlite_type: str) -> str:
        """Map SQLite type to PostgreSQL type"""
        # Handle parameterized types like VARCHAR(50)
        base_type = sqlite_type.split("(")[0].upper()

        if base_type in self.TYPE_MAPPING:
            pg_type = self.TYPE_MAPPING[base_type]
            # Preserve parameters for VARCHAR
            if "(" in sqlite_type and base_type == "VARCHAR":
                return sqlite_type
            return pg_type

        # Default to TEXT for unknown types
        return "TEXT"

    def generate_postgres_ddl(self, table: str) -> str:
        """Generate PostgreSQL CREATE TABLE DDL for a table"""
        info = self.schema_info[table]
        columns = info["columns"]

        ddl = f"CREATE TABLE IF NOT EXISTS kaggle.{table}_nba_kaggle (\n"
        ddl += "    id SERIAL PRIMARY KEY,\n"

        # Add columns from SQLite
        for col in columns:
            col_name = col["name"]
            sqlite_type = col["type"] if col["type"] else "TEXT"
            pg_type = self.map_sqlite_to_postgres_type(sqlite_type)

            # Skip if column is 'id' (we're using SERIAL)
            if col_name.lower() == "id":
                continue

            null_constraint = " NOT NULL" if col["notnull"] else ""
            unique_constraint = " UNIQUE" if col["pk"] and col_name.lower() != "id" else ""

            ddl += f"    {col_name} {pg_type}{null_constraint}{unique_constraint},\n"

        # Add JSONB data column
        ddl += "    data JSONB NOT NULL,\n"
        ddl += "    metadata JSONB,\n"
        ddl += "    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),\n"
        ddl += "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()\n"
        ddl += ");\n"

        return ddl

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report"""
        report = []
        report.append("# Kaggle SQLite Schema Analysis Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Database:** {self.db_path}\n")
        report.append(f"**Tables:** {len(self.tables)}\n")

        total_rows = sum(info["row_count"] for info in self.schema_info.values())
        report.append(f"**Total Rows:** {total_rows:,}\n")
        report.append("\n---\n\n")

        # Summary table
        report.append("## Table Summary\n\n")
        report.append("| # | Table Name | Rows | Columns | Foreign Keys | Indexes |\n")
        report.append("|---|------------|------|---------|--------------|----------|\n")

        for idx, table in enumerate(self.tables, 1):
            info = self.schema_info[table]
            report.append(
                f"| {idx} | `{table}` | {info['row_count']:,} | "
                f"{len(info['columns'])} | {len(info['foreign_keys'])} | "
                f"{len(info['indexes'])} |\n"
            )

        report.append("\n---\n\n")

        # Detailed table information
        report.append("## Detailed Table Schemas\n\n")

        for table in self.tables:
            info = self.schema_info[table]
            report.append(f"### {table}\n\n")
            report.append(f"**Rows:** {info['row_count']:,}\n\n")

            # Columns
            report.append("**Columns:**\n\n")
            report.append("| Column | SQLite Type | PostgreSQL Type | Nullable | Primary Key |\n")
            report.append("|--------|-------------|-----------------|----------|-------------|\n")

            for col in info["columns"]:
                sqlite_type = col["type"] if col["type"] else "TEXT"
                pg_type = self.map_sqlite_to_postgres_type(sqlite_type)
                nullable = "No" if col["notnull"] else "Yes"
                pk = "Yes" if col["pk"] else "No"

                report.append(
                    f"| `{col['name']}` | {sqlite_type} | {pg_type} | "
                    f"{nullable} | {pk} |\n"
                )

            # Foreign keys
            if info["foreign_keys"]:
                report.append("\n**Foreign Keys:**\n\n")
                for fk in info["foreign_keys"]:
                    report.append(
                        f"- `{fk['from']}` → `{fk['table']}.{fk['to']}` "
                        f"(ON DELETE: {fk['on_delete']}, ON UPDATE: {fk['on_update']})\n"
                    )

            # Sample data
            if info["sample_data"]:
                report.append("\n**Sample Data (first 3 rows):**\n\n")
                report.append("```json\n")
                report.append(json.dumps(info["sample_data"], indent=2, default=str))
                report.append("\n```\n")

            report.append("\n---\n\n")

        # Type mapping reference
        report.append("## SQLite to PostgreSQL Type Mapping\n\n")
        report.append("| SQLite Type | PostgreSQL Type |\n")
        report.append("|-------------|----------------|\n")
        for sqlite_type, pg_type in sorted(self.TYPE_MAPPING.items()):
            report.append(f"| {sqlite_type} | {pg_type} |\n")

        report.append("\n---\n\n")

        # Suggested DDL
        report.append("## Suggested PostgreSQL DDL (Sample)\n\n")
        report.append("Sample DDL for first table:\n\n")
        report.append("```sql\n")
        if self.tables:
            report.append(self.generate_postgres_ddl(self.tables[0]))
        report.append("```\n")

        return "".join(report)

    def save_report(self, output_path: Path):
        """Save analysis report to file"""
        report = self.generate_markdown_report()
        output_file = output_path / "KAGGLE_SQLITE_SCHEMA_REPORT.md"

        output_path.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(report)

        print(f"✓ Report saved: {output_file}")
        return output_file

    def save_schema_json(self, output_path: Path):
        """Save schema information as JSON"""
        output_file = output_path / "kaggle_schema.json"

        with open(output_file, "w") as f:
            json.dump(self.schema_info, f, indent=2, default=str)

        print(f"✓ Schema JSON saved: {output_file}")
        return output_file

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 70)
        print("Schema Analysis Summary")
        print("=" * 70)
        print(f"\nDatabase: {self.db_path}")
        print(f"Tables: {len(self.tables)}")

        total_rows = sum(info["row_count"] for info in self.schema_info.values())
        print(f"Total rows: {total_rows:,}\n")

        print("Table                          Rows        Columns  FK  Indexes")
        print("-" * 70)

        for table in self.tables:
            info = self.schema_info[table]
            print(
                f"{table:<30} {info['row_count']:>10,}  {len(info['columns']):>7}  "
                f"{len(info['foreign_keys']):>2}  {len(info['indexes']):>7}"
            )

        print("=" * 70 + "\n")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Analyze Kaggle SQLite schema for PostgreSQL migration"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("/Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite"),
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/schemas"),
        help="Output directory for reports",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Kaggle SQLite Schema Analysis")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run analysis
    analyzer = KaggleSchemaAnalyzer(args.db)

    try:
        analyzer.connect()
        analyzer.get_all_tables()
        analyzer.analyze_all_tables()

        # Generate outputs
        analyzer.print_summary()
        analyzer.save_report(args.output)
        analyzer.save_schema_json(args.output)

        print("\n" + "=" * 70)
        print("Analysis Complete!")
        print("=" * 70)
        print(f"\nNext steps:")
        print("1. Review schema report: docs/schemas/KAGGLE_SQLITE_SCHEMA_REPORT.md")
        print("2. Create PostgreSQL DDL: scripts/db/migrations/0_20_kaggle_schema.sql")
        print("3. Build ETL script: scripts/db/migrations/0_21_kaggle_data_migration.py")
        print("=" * 70 + "\n")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
