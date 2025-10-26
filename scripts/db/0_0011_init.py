#!/usr/bin/env python3
"""
0.0011: RAG Pipeline Database Initialization

Purpose: Initialize pgvector extension and RAG schema in PostgreSQL
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    python scripts/db/0_11_init.py
    python scripts/db/0_11_init.py --verify-only
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import argparse
from pathlib import Path


class RAGDatabaseInitializer:
    """Initialize RAG pipeline database schema with pgvector"""

    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.cursor = None

    def get_db_config(self):
        """Get database configuration from environment"""
        config = {
            "host": os.getenv("RDS_HOST", os.getenv("POSTGRES_HOST", "localhost")),
            "port": int(os.getenv("RDS_PORT", os.getenv("POSTGRES_PORT", "5432"))),
            "database": os.getenv("RDS_DATABASE", os.getenv("POSTGRES_DB", "nba_data")),
            "user": os.getenv("RDS_USER", os.getenv("POSTGRES_USER", "postgres")),
            "password": os.getenv("RDS_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
        }

        # Validate configuration
        if not config["password"]:
            raise ValueError("Database password not found in environment variables")

        return config

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            config = self.get_db_config()
            print(f"Connecting to PostgreSQL at {config['host']}:{config['port']}...")

            self.conn = psycopg2.connect(**config)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()

            print("✅ Connected to PostgreSQL successfully")
            return True

        except psycopg2.Error as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            return False

    def verify_pgvector_installed(self):
        """Check if pgvector extension is installed"""
        try:
            self.cursor.execute(
                """
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = 'vector';
            """
            )
            result = self.cursor.fetchone()

            if result:
                print(f"✅ pgvector extension found (version: {result[1]})")
                return True
            else:
                print("❌ pgvector extension not installed")
                return False

        except psycopg2.Error as e:
            print(f"❌ Error checking pgvector: {e}")
            return False

    def install_pgvector(self):
        """Install pgvector extension"""
        try:
            print("Installing pgvector extension...")
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Verify installation
            if self.verify_pgvector_installed():
                print("✅ pgvector extension installed successfully")
                return True
            else:
                print("❌ Failed to install pgvector extension")
                return False

        except psycopg2.Error as e:
            print(f"❌ Error installing pgvector: {e}")
            print("\nNote: Installing pgvector requires:")
            print("  - PostgreSQL 11+")
            print("  - rds_superuser role (on AWS RDS)")
            print("  - pgvector package installed on database server")
            return False

    def run_schema_migration(self):
        """Run the schema migration SQL file"""
        try:
            schema_file = Path(__file__).parent / "migrations" / "0_11_schema.sql"

            if not schema_file.exists():
                print(f"❌ Schema file not found: {schema_file}")
                return False

            print(f"Running schema migration from {schema_file}...")

            with open(schema_file, "r") as f:
                schema_sql = f.read()

            # Execute schema SQL
            self.cursor.execute(schema_sql)

            print("✅ Schema migration completed successfully")
            return True

        except psycopg2.Error as e:
            print(f"❌ Error running schema migration: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def verify_schema(self):
        """Verify that RAG schema was created correctly"""
        try:
            print("\nVerifying RAG schema...")

            # Check schema exists
            self.cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'rag';
            """
            )
            if not self.cursor.fetchone():
                print("❌ RAG schema not found")
                return False
            print("✅ RAG schema exists")

            # Check tables
            expected_tables = [
                "nba_embeddings",
                "play_embeddings",
                "document_embeddings",
                "embedding_generation_log",
            ]

            for table in expected_tables:
                self.cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'rag' AND table_name = %s;
                """,
                    (table,),
                )

                if self.cursor.fetchone():
                    print(f"✅ Table rag.{table} exists")
                else:
                    print(f"❌ Table rag.{table} not found")
                    return False

            # Check functions
            self.cursor.execute(
                """
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'rag'
                AND routine_type = 'FUNCTION';
            """
            )

            functions = [row[0] for row in self.cursor.fetchall()]
            expected_functions = [
                "similarity_search",
                "hybrid_search",
                "get_embedding_stats",
                "refresh_embedding_views",
            ]

            for func in expected_functions:
                if func in functions:
                    print(f"✅ Function rag.{func}() exists")
                else:
                    print(f"❌ Function rag.{func}() not found")

            # Check materialized views
            self.cursor.execute(
                """
                SELECT matviewname
                FROM pg_matviews
                WHERE schemaname = 'rag';
            """
            )

            views = [row[0] for row in self.cursor.fetchall()]
            expected_views = ["player_embeddings_summary", "game_embeddings_summary"]

            for view in expected_views:
                if view in views:
                    print(f"✅ Materialized view rag.{view} exists")
                else:
                    print(f"⚠️  Materialized view rag.{view} not found (might be empty)")

            # Check HNSW indexes
            self.cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'rag'
                AND indexname LIKE '%hnsw%';
            """
            )

            hnsw_indexes = [row[0] for row in self.cursor.fetchall()]
            print(
                f"\n✅ Found {len(hnsw_indexes)} HNSW indexes for vector similarity search"
            )
            for idx in hnsw_indexes:
                print(f"   - {idx}")

            return True

        except psycopg2.Error as e:
            print(f"❌ Error verifying schema: {e}")
            return False

    def get_stats(self):
        """Display current embedding statistics"""
        try:
            print("\n" + "=" * 70)
            print("Current Embedding Statistics")
            print("=" * 70)

            self.cursor.execute("SELECT * FROM rag.get_embedding_stats();")
            stats = self.cursor.fetchall()

            if stats:
                print(
                    f"\n{'Entity Type':<15} {'Count':<10} {'Avg Length':<12} {'Earliest':<20} {'Latest':<20}"
                )
                print("-" * 70)
                for row in stats:
                    entity_type, count, avg_len, earliest, latest = row
                    earliest_str = (
                        earliest.strftime("%Y-%m-%d %H:%M") if earliest else "N/A"
                    )
                    latest_str = latest.strftime("%Y-%m-%d %H:%M") if latest else "N/A"
                    print(
                        f"{entity_type:<15} {count:<10} {avg_len:<12.1f} {earliest_str:<20} {latest_str:<20}"
                    )
            else:
                print("\n📊 No embeddings have been generated yet.")
                print(
                    "   Use scripts/0_11/embedding_pipeline.py to generate embeddings."
                )

            print()

        except psycopg2.Error as e:
            print(f"⚠️  Could not retrieve statistics: {e}")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("\n✅ Database connection closed")

    def initialize(self, verify_only=False):
        """
        Full initialization workflow

        Args:
            verify_only: If True, only verify installation without making changes
        """
        print("=" * 70)
        print("0.0011: RAG Pipeline Database Initialization")
        print("=" * 70)
        print()

        # Connect to database
        if not self.connect():
            return False

        # Check pgvector
        pgvector_installed = self.verify_pgvector_installed()

        if verify_only:
            print("\n--- Verification Mode (No Changes) ---")
            if pgvector_installed:
                self.verify_schema()
                self.get_stats()
            return pgvector_installed

        # Install pgvector if needed
        if not pgvector_installed:
            if not self.install_pgvector():
                return False

        # Run schema migration
        if not self.run_schema_migration():
            return False

        # Verify installation
        if not self.verify_schema():
            print("\n⚠️  Schema verification found issues")
            return False

        # Display stats
        self.get_stats()

        print("\n" + "=" * 70)
        print("✅ RAG Pipeline Initialization Complete!")
        print("=" * 70)
        print("\nNext Steps:")
        print("  1. Generate embeddings: python scripts/0_11/embedding_pipeline.py")
        print("  2. Run tests: pytest tests/phases/phase_0/test_0_0011.py")
        print("  3. Validate: python validators/phases/phase_0/validate_0_11.py")
        print()

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Initialize RAG Pipeline database schema with pgvector"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify installation without making changes",
    )

    args = parser.parse_args()

    initializer = RAGDatabaseInitializer()

    try:
        success = initializer.initialize(verify_only=args.verify_only)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Initialization interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        initializer.close()


if __name__ == "__main__":
    main()
