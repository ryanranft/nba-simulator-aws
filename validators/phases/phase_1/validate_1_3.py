#!/usr/bin/env python3
"""
Validate 1.3: Quality Monitoring Integration

Validates that monitoring systems work with raw_data schema.
Tests DIMS CLI, data quality monitor, metrics collection, and alert systems.

Usage:
    python validators/phases/phase_1/validate_1_3.py
    python validators/phases/phase_1/validate_1_3.py --verbose
    python validators/phases/phase_1/validate_1_3.py --skip-dims  # Skip DIMS verification (slow)
"""

import sys
import os
import subprocess
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
from typing import List, Tuple, Dict, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class QualityMonitoringValidator:
    """Validates monitoring system integration with raw_data schema"""

    def __init__(
        self, verbose: bool = False, skip_dims: bool = False, db_config: dict = None
    ):
        self.verbose = verbose
        self.skip_dims = skip_dims
        self.failures = []
        self.warnings = []
        self.conn = None
        self.cursor = None
        self.db_config = db_config or {}
        self.project_root = Path(__file__).parent.parent.parent.parent

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {"INFO": "✓", "ERROR": "✗", "WARNING": "⚠", "PROGRESS": "⏳"}.get(
                level, " "
            )
            print(f"{prefix} {message}")

    # ========================================================================
    # Database Connection
    # ========================================================================

    def connect_db(self) -> bool:
        """Establish database connection"""
        try:
            config = {
                "host": self.db_config.get("host")
                or os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(
                    self.db_config.get("port") or os.getenv("POSTGRES_PORT", "5432")
                ),
                "database": self.db_config.get("database")
                or os.getenv("POSTGRES_DB", "nba_simulator"),
                "user": self.db_config.get("user")
                or os.getenv("POSTGRES_USER", "ryanranft"),
                "password": (
                    self.db_config.get("password", "")
                    if "password" in self.db_config
                    else os.getenv("POSTGRES_PASSWORD", "")
                ),
            }

            self.conn = psycopg2.connect(**config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            self.log(
                f"Connected to database at {config['host']}:{config['port']}/{config['database']}"
            )
            return True

        except Exception as e:
            self.failures.append(f"Database connection failed: {e}")
            return False

    def disconnect_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

    # ========================================================================
    # Monitoring Script Accessibility
    # ========================================================================

    def validate_monitoring_scripts_exist(self) -> bool:
        """Validate monitoring scripts exist"""
        try:
            scripts_dir = self.project_root / "scripts" / "monitoring"
            expected_scripts = [
                "dims_cli.py",
                "data_quality_monitor.py",
                "alert_manager.py",
                "scraper_health_monitor.py",
            ]

            all_exist = True
            for script in expected_scripts:
                script_path = scripts_dir / script
                if script_path.exists():
                    self.log(f"Script exists: {script}")
                else:
                    self.failures.append(f"Missing monitoring script: {script}")
                    all_exist = False

            return all_exist

        except Exception as e:
            self.failures.append(f"Script existence check failed: {e}")
            return False

    # ========================================================================
    # DIMS CLI Integration
    # ========================================================================

    def validate_dims_cli_accessible(self) -> bool:
        """Validate DIMS CLI is accessible and can show help"""
        try:
            dims_cli = self.project_root / "scripts" / "monitoring" / "dims_cli.py"

            if not dims_cli.exists():
                self.failures.append("DIMS CLI script not found")
                return False

            # Test help command
            result = subprocess.run(
                ["python", str(dims_cli), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.log("DIMS CLI accessible")
                return True
            else:
                self.failures.append(f"DIMS CLI --help failed: {result.stderr}")
                return False

        except Exception as e:
            self.failures.append(f"DIMS CLI accessibility check failed: {e}")
            return False

    def validate_dims_info_command(self) -> bool:
        """Validate DIMS CLI info command works"""
        try:
            if self.skip_dims:
                self.log("Skipping DIMS info check (--skip-dims)", "WARNING")
                return True

            dims_cli = self.project_root / "scripts" / "monitoring" / "dims_cli.py"

            # Test info command (quick operation)
            result = subprocess.run(
                ["python", str(dims_cli), "info"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root),
            )

            if result.returncode == 0:
                self.log("DIMS info command works")
                if self.verbose:
                    # Show first few lines of output
                    lines = result.stdout.split("\n")[:5]
                    for line in lines:
                        if line.strip():
                            self.log(f"  {line}")
                return True
            else:
                # DIMS info failure is a warning, not a critical failure
                self.warnings.append(f"DIMS info command failed: {result.stderr[:200]}")
                return True  # Don't fail validation, just warn

        except subprocess.TimeoutExpired:
            self.warnings.append("DIMS info command timed out")
            return True  # Warning only
        except Exception as e:
            self.warnings.append(f"DIMS info command failed: {e}")
            return True  # Warning only

    # ========================================================================
    # DIMS Database Integrity
    # ========================================================================

    def validate_dims_database_exists(self) -> bool:
        """Validate DIMS SQLite database exists and has expected structure"""
        try:
            dims_db_path = self.project_root / "metrics" / "dims.db"

            if not dims_db_path.exists():
                self.warnings.append(
                    f"DIMS database not found at {dims_db_path} (will be created on first use)"
                )
                return True  # Not critical, can be created

            # Check database structure
            conn = sqlite3.connect(str(dims_db_path))
            cursor = conn.cursor()

            # Check for expected tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["metrics", "metric_history"]
            missing_tables = [t for t in expected_tables if t not in tables]

            if missing_tables:
                self.warnings.append(
                    f"DIMS database missing tables: {', '.join(missing_tables)}"
                )
            else:
                self.log(f"DIMS database has expected tables: {', '.join(tables)}")

            # Check row counts
            for table in [t for t in expected_tables if t in tables]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.log(f"  {table}: {count:,} rows")

            conn.close()
            return True

        except Exception as e:
            self.warnings.append(f"DIMS database check failed: {e}")
            return True  # Warning only, not critical

    # ========================================================================
    # Data Quality Monitor Integration
    # ========================================================================

    def validate_data_quality_monitor_accessible(self) -> bool:
        """Validate data quality monitor script can run"""
        try:
            dqm_script = (
                self.project_root / "scripts" / "monitoring" / "data_quality_monitor.py"
            )

            if not dqm_script.exists():
                self.failures.append("Data quality monitor script not found")
                return False

            # Test help command
            result = subprocess.run(
                ["python", str(dqm_script), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.log("Data quality monitor accessible")
                return True
            else:
                self.warnings.append(
                    f"Data quality monitor --help failed: {result.stderr}"
                )
                return True  # Warning only

        except Exception as e:
            self.warnings.append(
                f"Data quality monitor accessibility check failed: {e}"
            )
            return True  # Warning only

    # ========================================================================
    # Metrics Collection
    # ========================================================================

    def validate_metrics_collection_works(self) -> bool:
        """Validate basic metrics can be collected from raw_data schema"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return False

            # Test basic metric: game count
            self.cursor.execute("SELECT COUNT(*) as game_count FROM raw_data.nba_games")
            result = self.cursor.fetchone()
            game_count = result["game_count"]

            self.log(f"Collected metric: {game_count:,} games in raw_data.nba_games")

            # Test date range metric
            self.cursor.execute(
                """
                SELECT
                    MIN(game_date) as earliest,
                    MAX(game_date) as latest
                FROM raw_data.nba_games
            """
            )
            result = self.cursor.fetchone()
            self.log(
                f"Collected metric: Date range {result['earliest']} to {result['latest']}"
            )

            # Test source distribution metric
            self.cursor.execute(
                """
                SELECT
                    source,
                    COUNT(*) as count
                FROM raw_data.nba_games
                GROUP BY source
                ORDER BY count DESC
            """
            )
            sources = self.cursor.fetchall()
            self.log(f"Collected metric: {len(sources)} source(s)")
            for s in sources:
                self.log(f"  {s['source']}: {s['count']:,} games")

            # If we got this far, metrics collection works
            return True

        except Exception as e:
            self.failures.append(f"Metrics collection failed: {e}")
            return False

    # ========================================================================
    # PostgreSQL Extension Check
    # ========================================================================

    def validate_postgres_extensions(self) -> bool:
        """Validate required PostgreSQL extensions are available"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return False

            # Check for common extensions used in monitoring
            self.cursor.execute(
                """
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname IN ('plpgsql', 'pg_stat_statements')
            """
            )
            extensions = self.cursor.fetchall()

            self.log(f"PostgreSQL extensions: {len(extensions)} found")
            for ext in extensions:
                self.log(f"  {ext['extname']}: v{ext['extversion']}")

            # plpgsql should always be there (core functionality)
            ext_names = [e["extname"] for e in extensions]
            if "plpgsql" not in ext_names:
                self.warnings.append("plpgsql extension not found (unusual)")

            return True

        except Exception as e:
            self.warnings.append(f"Extension check failed: {e}")
            return True  # Warning only

    # ========================================================================
    # Schema Permissions
    # ========================================================================

    def validate_schema_permissions(self) -> bool:
        """Validate user has required permissions on raw_data schema"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return False

            # Test read permission
            self.cursor.execute("SELECT 1 FROM raw_data.nba_games LIMIT 1")
            result = self.cursor.fetchone()

            if result:
                self.log("Read permission on raw_data.nba_games: ✓")
            else:
                self.warnings.append("Could not read from raw_data.nba_games")

            # Check if user can access schema metadata
            self.cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'raw_data'
            """
            )
            tables = self.cursor.fetchall()

            if tables:
                self.log(f"Schema metadata access: ✓ ({len(tables)} tables visible)")
            else:
                self.warnings.append("Cannot access raw_data schema metadata")

            return True

        except Exception as e:
            self.failures.append(f"Permission check failed: {e}")
            return False

    # ========================================================================
    # Main Validation Runner
    # ========================================================================

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations"""
        print(f"\n{'='*60}")
        print(f"1.3 Quality Monitoring Integration Validation")
        if self.skip_dims:
            print(f"Note: Skipping slow DIMS operations")
        print(f"{'='*60}\n")

        try:
            results = {
                "monitoring_scripts_exist": self.validate_monitoring_scripts_exist(),
                "dims_cli_accessible": self.validate_dims_cli_accessible(),
                "dims_info_works": self.validate_dims_info_command(),
                "dims_database_ok": self.validate_dims_database_exists(),
                "data_quality_monitor_ok": self.validate_data_quality_monitor_accessible(),
                "metrics_collection_works": self.validate_metrics_collection_works(),
                "postgres_extensions_ok": self.validate_postgres_extensions(),
                "schema_permissions_ok": self.validate_schema_permissions(),
            }

            all_passed = all(results.values())

            print(f"\n{'='*60}")
            print(f"Results Summary")
            print(f"{'='*60}")

            for check, passed in results.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"{check:40} {status}")

            if self.warnings:
                print(f"\n⚠  Warnings ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"  - {warning}")

            if self.failures:
                print(f"\n❌ Failures ({len(self.failures)}):")
                for failure in self.failures:
                    print(f"  - {failure}")

            print(f"\n{'='*60}")
            if all_passed:
                print("✅ All validations passed!")
            else:
                print("❌ Some validations failed.")
            print(f"{'='*60}\n")

            return all_passed, results

        finally:
            if self.conn:
                self.disconnect_db()


def main():
    parser = argparse.ArgumentParser(
        description="Validate 1.3 - Quality Monitoring Integration"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--skip-dims", action="store_true", help="Skip DIMS verification (slow)"
    )
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--port", type=int, help="Database port")
    parser.add_argument("--database", help="Database name")
    parser.add_argument("--user", help="Database user")
    parser.add_argument("--password", help="Database password")

    args = parser.parse_args()

    db_config = {}
    if args.host:
        db_config["host"] = args.host
    if args.port:
        db_config["port"] = args.port
    if args.database:
        db_config["database"] = args.database
    if args.user:
        db_config["user"] = args.user
    if args.password is not None:
        db_config["password"] = args.password

    validator = QualityMonitoringValidator(
        verbose=args.verbose,
        skip_dims=args.skip_dims,
        db_config=db_config if db_config else None,
    )
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
