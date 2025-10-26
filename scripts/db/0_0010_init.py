#!/usr/bin/env python3
"""
0.0010: PostgreSQL JSONB Storage - Database Initialization

Purpose: Initialize PostgreSQL database schema for JSONB storage
Created: October 25, 2025
Implementation ID: rec_033_postgresql

Usage:
    python scripts/db/0_10_init.py
    python scripts/db/0_10_init.py --verbose
    python scripts/db/0_10_init.py --check-only
"""

import os
import sys
import argparse
import psycopg2
from pathlib import Path
from typing import Tuple, Dict, Optional


class DatabaseInitializer:
    """Initialize PostgreSQL database with JSONB schema"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.conn = None
        self.cursor = None

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose is enabled"""
        if self.verbose or level == "ERROR":
            prefix = "✓" if level == "INFO" else "✗" if level == "ERROR" else "⚠"
            print(f"{prefix} {message}")

    def get_db_config(self) -> Dict[str, str]:
        """Get database configuration from environment variables"""
        # Load secrets using hierarchical manager
        import sys

        home_dir = os.path.expanduser("~")
        if home_dir not in sys.path:
            sys.path.insert(0, home_dir)

        try:
            from mcp_server.unified_secrets_manager import load_secrets_hierarchical

            load_secrets_hierarchical("nba-simulator-aws", "NBA", "WORKFLOW")
        except ImportError:
            # Fallback if mcp_server not available
            pass

        config = {
            "host": os.getenv(
                "RDS_HOST_NBA_SIMULATOR_AWS_WORKFLOW",
                os.getenv("RDS_HOST", os.getenv("POSTGRES_HOST", "localhost")),
            ),
            "port": int(os.getenv("RDS_PORT", os.getenv("POSTGRES_PORT", "5432"))),
            "database": os.getenv(
                "RDS_DATABASE_NBA_SIMULATOR_AWS_WORKFLOW",
                os.getenv("RDS_DATABASE", os.getenv("POSTGRES_DB", "nba_data")),
            ),
            "user": os.getenv(
                "RDS_USERNAME_NBA_SIMULATOR_AWS_WORKFLOW",
                os.getenv("RDS_USER", os.getenv("POSTGRES_USER", "postgres")),
            ),
            "password": os.getenv(
                "RDS_PASSWORD_NBA_SIMULATOR_AWS_WORKFLOW",
                os.getenv("RDS_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
            ),
        }

        # Validate required fields
        if not config["password"]:
            raise ValueError(
                "Database password not found. Set RDS_PASSWORD_NBA_SIMULATOR_AWS_WORKFLOW environment variable."
            )

        return config

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            config = self.get_db_config()
            self.log(f"Connecting to database at {config['host']}:{config['port']}")

            self.conn = psycopg2.connect(
                host=config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"],
                connect_timeout=10,
            )
            self.cursor = self.conn.cursor()
            self.log("Database connection established")
            return True

        except psycopg2.Error as e:
            self.log(f"Database connection failed: {e}", "ERROR")
            return False
        except ValueError as e:
            self.log(str(e), "ERROR")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

    def check_postgres_version(self) -> Tuple[bool, str]:
        """Check PostgreSQL version (need 13+ for JSONB features)"""
        try:
            self.cursor.execute("SELECT version();")
            version_string = self.cursor.fetchone()[0]
            self.log(f"PostgreSQL version: {version_string}")

            # Extract major version number
            if "PostgreSQL" in version_string:
                version_num = int(version_string.split()[1].split(".")[0])
                if version_num >= 13:
                    return True, version_string
                else:
                    return (
                        False,
                        f"PostgreSQL 13+ required, found version {version_num}",
                    )
            return False, "Could not parse PostgreSQL version"

        except Exception as e:
            return False, f"Version check failed: {e}"

    def load_schema_file(self) -> Optional[str]:
        """Load SQL schema file"""
        schema_path = Path(__file__).parent / "migrations" / "0_10_schema.sql"

        if not schema_path.exists():
            self.log(f"Schema file not found: {schema_path}", "ERROR")
            return None

        try:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            self.log(f"Schema file loaded: {schema_path} ({len(schema_sql)} bytes)")
            return schema_sql
        except Exception as e:
            self.log(f"Failed to read schema file: {e}", "ERROR")
            return None

    def execute_schema(self, schema_sql: str) -> bool:
        """Execute schema SQL"""
        try:
            self.log("Executing schema SQL...")
            self.cursor.execute(schema_sql)
            self.conn.commit()
            self.log("Schema created successfully")
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            self.log(f"Schema creation failed: {e}", "ERROR")
            return False

    def verify_schema(self) -> Dict[str, bool]:
        """Verify schema was created correctly"""
        checks = {}

        try:
            # Check schema exists
            self.cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'raw_data';
            """
            )
            checks["schema_exists"] = self.cursor.fetchone() is not None
            self.log(f"Schema exists: {checks['schema_exists']}")

            # Check tables exist
            expected_tables = [
                "nba_games",
                "nba_players",
                "nba_teams",
                "nba_misc",
                "schema_version",
            ]
            for table in expected_tables:
                self.cursor.execute(
                    f"""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'raw_data'
                      AND table_name = '{table}';
                """
                )
                exists = self.cursor.fetchone() is not None
                checks[f"table_{table}"] = exists
                self.log(f"Table {table} exists: {exists}")

            # Check materialized views exist
            expected_views = ["games_summary", "players_summary"]
            for view in expected_views:
                self.cursor.execute(
                    f"""
                    SELECT matviewname
                    FROM pg_matviews
                    WHERE schemaname = 'raw_data'
                      AND matviewname = '{view}';
                """
                )
                exists = self.cursor.fetchone() is not None
                checks[f"view_{view}"] = exists
                self.log(f"Materialized view {view} exists: {exists}")

            # Check GIN indexes exist
            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'raw_data'
                  AND indexdef LIKE '%USING gin%';
            """
            )
            gin_index_count = self.cursor.fetchone()[0]
            checks["gin_indexes"] = (
                gin_index_count >= 8
            )  # Should have at least 8 GIN indexes
            self.log(f"GIN indexes created: {gin_index_count} found")

            # Check triggers exist
            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.triggers
                WHERE trigger_schema = 'raw_data';
            """
            )
            trigger_count = self.cursor.fetchone()[0]
            checks["triggers"] = trigger_count >= 4  # Should have 4 update triggers
            self.log(f"Triggers created: {trigger_count} found")

        except psycopg2.Error as e:
            self.log(f"Verification failed: {e}", "ERROR")
            return checks

        return checks

    def check_existing_schema(self) -> Tuple[bool, str]:
        """Check if schema already exists"""
        try:
            self.cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'raw_data';
            """
            )
            exists = self.cursor.fetchone() is not None

            if exists:
                # Check schema version
                self.cursor.execute(
                    """
                    SELECT version, applied_at
                    FROM raw_data.schema_version
                    ORDER BY applied_at DESC
                    LIMIT 1;
                """
                )
                result = self.cursor.fetchone()
                if result:
                    version, applied_at = result
                    return (
                        True,
                        f"Schema exists (version {version}, applied {applied_at})",
                    )
                else:
                    return True, "Schema exists (version unknown)"
            else:
                return False, "Schema does not exist"

        except psycopg2.Error as e:
            return False, f"Check failed: {e}"

    def run_initialization(self, force: bool = False, check_only: bool = False) -> bool:
        """Run complete initialization process"""
        print("\n" + "=" * 70)
        print("0.0010: PostgreSQL JSONB Storage - Database Initialization")
        print("=" * 70 + "\n")

        # Connect to database
        if not self.connect():
            return False

        try:
            # Check PostgreSQL version
            version_ok, version_msg = self.check_postgres_version()
            if not version_ok:
                self.log(version_msg, "ERROR")
                return False

            # Check existing schema
            schema_exists, schema_msg = self.check_existing_schema()
            self.log(schema_msg)

            if check_only:
                print("\n" + "=" * 70)
                print("Check-only mode: No changes made")
                print("=" * 70 + "\n")
                return schema_exists

            if schema_exists and not force:
                print("\n" + "=" * 70)
                print("Schema already exists. Use --force to recreate.")
                print("=" * 70 + "\n")
                return True

            # Load schema file
            schema_sql = self.load_schema_file()
            if not schema_sql:
                return False

            # Execute schema
            if not self.execute_schema(schema_sql):
                return False

            # Verify schema
            print("\n" + "-" * 70)
            print("Verifying Schema Installation")
            print("-" * 70 + "\n")

            checks = self.verify_schema()
            all_passed = all(checks.values())

            print("\n" + "=" * 70)
            print("Verification Results")
            print("=" * 70)

            for check_name, passed in checks.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"{check_name:40} {status}")

            print("=" * 70)

            if all_passed:
                print("\n✅ Database initialization completed successfully!\n")
            else:
                print("\n❌ Some verification checks failed.\n")

            return all_passed

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Initialize PostgreSQL database for 0.0010 JSONB storage"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force recreation of schema if it already exists",
    )
    parser.add_argument(
        "--check-only",
        "-c",
        action="store_true",
        help="Only check if schema exists, don't create",
    )

    args = parser.parse_args()

    initializer = DatabaseInitializer(verbose=args.verbose)
    success = initializer.run_initialization(
        force=args.force, check_only=args.check_only
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
