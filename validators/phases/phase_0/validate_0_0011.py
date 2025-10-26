#!/usr/bin/env python3
"""
0.0011: RAG Pipeline Validator

Purpose: Validate RAG pipeline implementation and deployment
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    python validators/phases/phase_0/validate_0_11.py
    python validators/phases/phase_0/validate_0_11.py --verbose
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import psycopg2


class Phase011Validator:
    """Validates 0.0011 RAG Pipeline implementation"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.conn = None
        self.cursor = None

    def log(self, message: str):
        """Log message if verbose"""
        if self.verbose:
            print(message)

    def connect_database(self) -> bool:
        """Connect to database"""
        try:
            config = {
                "host": os.getenv("RDS_HOST", os.getenv("POSTGRES_HOST", "localhost")),
                "port": int(os.getenv("RDS_PORT", os.getenv("POSTGRES_PORT", "5432"))),
                "database": os.getenv(
                    "RDS_DATABASE", os.getenv("POSTGRES_DB", "nba_data")
                ),
                "user": os.getenv("RDS_USER", os.getenv("POSTGRES_USER", "postgres")),
                "password": os.getenv(
                    "RDS_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")
                ),
            }

            self.conn = psycopg2.connect(**config)
            self.cursor = self.conn.cursor()
            self.log("✓ Database connection established")
            return True

        except Exception as e:
            self.failures.append(f"Database connection failed: {e}")
            return False

    def validate_implementation_files(self) -> bool:
        """Validate that all implementation files exist"""
        self.log("\n--- Validating Implementation Files ---")

        required_files = [
            "scripts/db/migrations/0_11_schema.sql",
            "scripts/db/0_11_init.py",
            "scripts/0_11/main.py",
            "scripts/0_11/embedding_pipeline.py",
            "scripts/0_11/openai_embedder.py",
            "scripts/0_11/batch_processor.py",
            "scripts/0_11/vector_search.py",
            "scripts/0_11/rag_queries.py",
            "scripts/0_11/semantic_search.py",
        ]

        all_exist = True

        for file_path in required_files:
            full_path = Path(file_path)
            if full_path.exists():
                self.log(f"✓ {file_path}")
            else:
                self.failures.append(f"Missing file: {file_path}")
                all_exist = False

        return all_exist

    def validate_test_files(self) -> bool:
        """Validate that test files exist"""
        self.log("\n--- Validating Test Files ---")

        required_test_files = [
            "tests/phases/phase_0/test_0_0011.py",
            "validators/phases/phase_0/validate_0_11.py",
        ]

        all_exist = True

        for file_path in required_test_files:
            full_path = Path(file_path)
            if full_path.exists():
                self.log(f"✓ {file_path}")
            else:
                self.failures.append(f"Missing test file: {file_path}")
                all_exist = False

        return all_exist

    def validate_database_schema(self) -> bool:
        """Validate database schema components"""
        if not self.conn:
            self.failures.append("Database not connected")
            return False

        self.log("\n--- Validating Database Schema ---")

        all_valid = True

        # Check schema exists
        try:
            self.cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'rag';
            """
            )
            if self.cursor.fetchone():
                self.log("✓ RAG schema exists")
            else:
                self.failures.append("RAG schema not found")
                all_valid = False
        except Exception as e:
            self.failures.append(f"Schema check failed: {e}")
            all_valid = False

        # Check tables
        required_tables = [
            "nba_embeddings",
            "play_embeddings",
            "document_embeddings",
            "embedding_generation_log",
        ]

        for table in required_tables:
            try:
                self.cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'rag' AND table_name = %s;
                """,
                    (table,),
                )

                if self.cursor.fetchone():
                    self.log(f"✓ Table rag.{table}")
                else:
                    self.failures.append(f"Table rag.{table} not found")
                    all_valid = False
            except Exception as e:
                self.failures.append(f"Table check failed for {table}: {e}")
                all_valid = False

        return all_valid

    def validate_database_functions(self) -> bool:
        """Validate database functions exist"""
        if not self.conn:
            return False

        self.log("\n--- Validating Database Functions ---")

        required_functions = [
            "similarity_search",
            "hybrid_search",
            "get_embedding_stats",
            "refresh_embedding_views",
        ]

        all_exist = True

        for func in required_functions:
            try:
                self.cursor.execute(
                    """
                    SELECT routine_name
                    FROM information_schema.routines
                    WHERE routine_schema = 'rag'
                      AND routine_name = %s
                      AND routine_type = 'FUNCTION';
                """,
                    (func,),
                )

                if self.cursor.fetchone():
                    self.log(f"✓ Function rag.{func}()")
                else:
                    self.failures.append(f"Function rag.{func}() not found")
                    all_exist = False
            except Exception as e:
                self.failures.append(f"Function check failed for {func}: {e}")
                all_exist = False

        return all_exist

    def validate_pgvector_extension(self) -> bool:
        """Validate pgvector extension is installed"""
        if not self.conn:
            return False

        self.log("\n--- Validating pgvector Extension ---")

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
                self.log(f"✓ pgvector extension installed (version: {result[1]})")
                return True
            else:
                self.warnings.append(
                    "pgvector extension not installed (required for production)"
                )
                return False

        except Exception as e:
            self.failures.append(f"pgvector check failed: {e}")
            return False

    def validate_hnsw_indexes(self) -> bool:
        """Validate HNSW indexes exist"""
        if not self.conn:
            return False

        self.log("\n--- Validating HNSW Indexes ---")

        try:
            self.cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'rag'
                  AND indexname LIKE '%hnsw%';
            """
            )

            indexes = self.cursor.fetchall()
            if indexes:
                for idx in indexes:
                    self.log(f"✓ HNSW index: {idx[0]}")
                return True
            else:
                self.warnings.append(
                    "No HNSW indexes found (required for vector search)"
                )
                return False

        except Exception as e:
            self.failures.append(f"HNSW index check failed: {e}")
            return False

    def get_embedding_stats(self) -> Dict:
        """Get current embedding statistics"""
        if not self.conn:
            return {}

        try:
            self.cursor.execute("SELECT * FROM rag.get_embedding_stats();")
            stats_rows = self.cursor.fetchall()

            stats = {"total": 0, "by_type": {}}

            for row in stats_rows:
                entity_type = row[0]
                count = row[1]
                stats["total"] += count
                stats["by_type"][entity_type] = {
                    "count": count,
                    "avg_text_length": float(row[2]) if row[2] else 0,
                }

            return stats

        except Exception as e:
            self.warnings.append(f"Could not retrieve embedding stats: {e}")
            return {}

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*70}")
        print("0.0011: RAG Pipeline Validation")
        print(f"{'='*70}")

        results = {}

        # File validations (don't require database)
        results["implementation_files"] = self.validate_implementation_files()
        results["test_files"] = self.validate_test_files()

        # Database validations
        db_connected = self.connect_database()
        results["database_connection"] = db_connected

        if db_connected:
            results["database_schema"] = self.validate_database_schema()
            results["database_functions"] = self.validate_database_functions()
            results["pgvector_extension"] = self.validate_pgvector_extension()
            results["hnsw_indexes"] = self.validate_hnsw_indexes()

            # Get stats
            stats = self.get_embedding_stats()
            if stats:
                print(f"\n--- Embedding Statistics ---")
                print(f"Total Embeddings: {stats['total']:,}")
                for entity_type, data in stats.get("by_type", {}).items():
                    print(f"  {entity_type}: {data['count']:,} embeddings")
        else:
            print("\n⚠️  Skipping database validations (no connection)")

        # Print summary
        print(f"\n{'='*70}")
        print("Validation Summary")
        print(f"{'='*70}")

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        print(f"\nValidations Passed: {passed}/{total}")

        if self.failures:
            print(f"\n❌ Failures ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  - {failure}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        all_passed = len(self.failures) == 0

        if all_passed:
            print("\n✅ All validations passed!")
        else:
            print("\n❌ Some validations failed")

        print()

        return all_passed, results

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate 0.0011 RAG Pipeline implementation"
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")

    args = parser.parse_args()

    validator = Phase011Validator(verbose=args.verbose)

    try:
        all_passed, results = validator.run_all_validations()
        sys.exit(0 if all_passed else 1)

    finally:
        validator.close()


if __name__ == "__main__":
    main()
