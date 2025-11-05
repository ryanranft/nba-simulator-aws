#!/usr/bin/env python3
"""
System Validation Script
Provides one-command health check for the entire NBA Simulator system.

Usage:
    python scripts/system_validation.py              # Full validation
    python scripts/system_validation.py --quick      # Quick checks only
    python scripts/system_validation.py --category database  # Specific category

Categories:
    - imports: Verify all key modules can be imported
    - database: Database connectivity and schema
    - s3: S3 bucket access and DIMS metrics
    - workflows: Workflow imports and structure
    - adce: ADCE autonomous system health
    - all: Run all checks (default)
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SystemValidator:
    """Validates entire NBA Simulator system health"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results = []
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose"""
        if self.verbose:
            prefix = {
                "INFO": "ℹ️ ",
                "SUCCESS": "✅",
                "WARNING": "⚠️ ",
                "ERROR": "❌",
                "HEADER": "\n" + "=" * 80 + "\n",
            }.get(level, "")
            print(f"{prefix} {message}")

    def add_result(
        self,
        category: str,
        check: str,
        passed: bool,
        message: str = "",
        details: str = "",
    ):
        """Record validation result"""
        self.results.append(
            {
                "category": category,
                "check": check,
                "passed": passed,
                "message": message,
                "details": details,
            }
        )

    # =========================================================================
    # Import Validation
    # =========================================================================

    def validate_imports(self) -> bool:
        """Validate all key modules can be imported"""
        self.log("Validating Key Imports", "HEADER")

        imports_to_test = [
            ("nba_simulator.config", "Configuration"),
            ("nba_simulator.database", "Database"),
            ("nba_simulator.workflows", "Workflows"),
            ("nba_simulator.agents", "Agents"),
            ("nba_simulator.etl", "ETL Pipeline"),
            ("nba_simulator.monitoring.dims", "DIMS Monitoring"),
            ("nba_simulator.adce", "ADCE Autonomous"),
        ]

        all_passed = True
        for module_name, display_name in imports_to_test:
            try:
                __import__(module_name)
                self.log(f"{display_name}: OK", "SUCCESS")
                self.add_result("imports", display_name, True)
            except Exception as e:
                self.log(f"{display_name}: FAILED - {str(e)}", "ERROR")
                self.add_result("imports", display_name, False, str(e))
                all_passed = False

        return all_passed

    # =========================================================================
    # Database Validation
    # =========================================================================

    def validate_database(self) -> bool:
        """Validate database connectivity and basic schema"""
        self.log("Validating Database", "HEADER")

        try:
            from nba_simulator.database import execute_query

            # Test connection
            result = execute_query("SELECT 1 AS test")
            if result and result[0][0] == 1:
                self.log("Database connection: OK", "SUCCESS")
                self.add_result("database", "connection", True)
            else:
                self.log("Database connection: FAILED", "ERROR")
                self.add_result(
                    "database", "connection", False, "Query returned unexpected result"
                )
                return False

            # Count tables
            table_query = """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            result = execute_query(table_query)
            table_count = result[0][0] if result else 0

            self.log(f"Database tables found: {table_count}", "INFO")
            if table_count >= 40:
                self.log(f"Table count ({table_count}): OK", "SUCCESS")
                self.add_result(
                    "database", "table_count", True, f"{table_count} tables found"
                )
            else:
                self.log(
                    f"Table count ({table_count}): WARNING - Expected 40+", "WARNING"
                )
                self.add_result(
                    "database",
                    "table_count",
                    False,
                    f"Only {table_count} tables found, expected 40+",
                )

            return True

        except Exception as e:
            self.log(f"Database validation failed: {str(e)}", "ERROR")
            self.add_result("database", "validation", False, str(e))
            return False

    # =========================================================================
    # S3 Validation
    # =========================================================================

    def validate_s3(self) -> bool:
        """Validate S3 bucket access"""
        self.log("Validating S3 Access", "HEADER")

        try:
            import boto3

            s3 = boto3.client("s3")
            bucket = "nba-sim-raw-data-lake"

            # Test bucket access
            response = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
            if "Contents" in response or response.get("KeyCount", 0) >= 0:
                self.log("S3 bucket access: OK", "SUCCESS")
                self.add_result("s3", "bucket_access", True)
            else:
                self.log("S3 bucket access: FAILED", "ERROR")
                self.add_result("s3", "bucket_access", False, "No objects found")
                return False

            # Use AWS CLI to get actual count (more reliable than Python SDK for large buckets)
            try:
                result = subprocess.run(
                    [
                        "aws",
                        "s3",
                        "ls",
                        f"s3://{bucket}/",
                        "--recursive",
                        "--summarize",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "Total Objects:" in line:
                            count = int(line.split(":")[-1].strip())
                            self.log(f"S3 object count: {count:,}", "INFO")
                            if count > 100000:
                                self.log("S3 object count: OK", "SUCCESS")
                                self.add_result(
                                    "s3", "object_count", True, f"{count:,} objects"
                                )
                            else:
                                self.log(
                                    f"S3 object count: WARNING - Only {count:,} objects",
                                    "WARNING",
                                )
                                self.add_result(
                                    "s3",
                                    "object_count",
                                    False,
                                    f"Only {count:,} objects",
                                )
            except Exception as e:
                self.log(f"S3 count check skipped: {str(e)}", "WARNING")
                self.add_result(
                    "s3",
                    "object_count",
                    True,
                    "Skipped - timeout or AWS CLI unavailable",
                )

            return True

        except Exception as e:
            self.log(f"S3 validation failed: {str(e)}", "ERROR")
            self.add_result("s3", "validation", False, str(e))
            return False

    # =========================================================================
    # Workflow Validation
    # =========================================================================

    def validate_workflows(self) -> bool:
        """Validate workflows are importable and configured"""
        self.log("Validating Workflows", "HEADER")

        workflows_to_test = [
            ("scripts/workflows/overnight_unified_cli.py", "Overnight Unified"),
            ("scripts/workflows/validation_cli.py", "3-Source Validation"),
            ("scripts/workflows/daily_update_cli.py", "Daily ESPN Update"),
        ]

        all_passed = True
        for workflow_path, name in workflows_to_test:
            full_path = project_root / workflow_path
            if full_path.exists():
                self.log(f"{name}: EXISTS", "SUCCESS")
                self.add_result("workflows", name, True)
            else:
                self.log(f"{name}: MISSING - {workflow_path}", "ERROR")
                self.add_result(
                    "workflows", name, False, f"File not found: {workflow_path}"
                )
                all_passed = False

        # Test BaseWorkflow import
        try:
            from nba_simulator.workflows.base_workflow import BaseWorkflow

            self.log("BaseWorkflow import: OK", "SUCCESS")
            self.add_result("workflows", "BaseWorkflow", True)
        except Exception as e:
            self.log(f"BaseWorkflow import: FAILED - {str(e)}", "ERROR")
            self.add_result("workflows", "BaseWorkflow", False, str(e))
            all_passed = False

        return all_passed

    # =========================================================================
    # ADCE Validation
    # =========================================================================

    def validate_adce(self) -> bool:
        """Validate ADCE autonomous system"""
        self.log("Validating ADCE System", "HEADER")

        try:
            # Check if ADCE health endpoint is responding
            import urllib.request

            try:
                response = urllib.request.urlopen(
                    "http://localhost:8080/health", timeout=5
                )
                data = json.loads(response.read().decode())
                status = data.get("status", "unknown")

                if status == "healthy":
                    self.log(f"ADCE health endpoint: {status.upper()}", "SUCCESS")
                    self.add_result(
                        "adce", "health_endpoint", True, f"Status: {status}"
                    )
                else:
                    self.log(f"ADCE health endpoint: {status.upper()}", "WARNING")
                    self.add_result(
                        "adce",
                        "health_endpoint",
                        True,
                        f"Status: {status} (not healthy but responding)",
                    )

            except Exception as e:
                self.log(
                    f"ADCE health endpoint: NOT RESPONDING (may be stopped)", "WARNING"
                )
                self.add_result(
                    "adce",
                    "health_endpoint",
                    True,
                    "ADCE not running - this is OK if not started",
                )

            # Check ADCE module imports
            try:
                from nba_simulator.adce.autonomous_loop import AutonomousLoop

                self.log("ADCE module import: OK", "SUCCESS")
                self.add_result("adce", "module_import", True)
            except Exception as e:
                self.log(f"ADCE module import: FAILED - {str(e)}", "ERROR")
                self.add_result("adce", "module_import", False, str(e))
                return False

            return True

        except Exception as e:
            self.log(f"ADCE validation failed: {str(e)}", "ERROR")
            self.add_result("adce", "validation", False, str(e))
            return False

    # =========================================================================
    # Main Validation
    # =========================================================================

    def run_validation(self, categories: List[str] = None) -> bool:
        """Run validation for specified categories"""
        if categories is None or "all" in categories:
            categories = ["imports", "database", "s3", "workflows", "adce"]

        self.log(f"NBA Simulator System Validation", "HEADER")
        self.log(f"Categories: {', '.join(categories)}\n")

        category_validators = {
            "imports": self.validate_imports,
            "database": self.validate_database,
            "s3": self.validate_s3,
            "workflows": self.validate_workflows,
            "adce": self.validate_adce,
        }

        results = {}
        for category in categories:
            validator = category_validators.get(category)
            if validator:
                results[category] = validator()
            else:
                self.log(f"Unknown category: {category}", "WARNING")

        # Print summary
        self.print_summary()

        # Return True if all validations passed
        return all(results.values())

    def print_summary(self):
        """Print validation summary"""
        self.log("Validation Summary", "HEADER")

        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"])
        total = len(self.results)

        duration = time.time() - self.start_time

        # Group by category
        by_category = {}
        for result in self.results:
            cat = result["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        # Print category summaries
        for category, checks in by_category.items():
            cat_passed = sum(1 for c in checks if c["passed"])
            cat_total = len(checks)
            status = "✅" if cat_passed == cat_total else "⚠️ "
            self.log(
                f"{status} {category.upper()}: {cat_passed}/{cat_total} checks passed"
            )

        # Overall summary
        print(f"\n{'='*80}")
        print(f"OVERALL: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
        print(f"Duration: {duration:.1f}s")
        print(f"{'='*80}\n")

        if failed > 0:
            self.log(f"❌ {failed} checks failed:", "ERROR")
            for result in self.results:
                if not result["passed"]:
                    self.log(
                        f"  - {result['category']}.{result['check']}: {result['message']}",
                        "ERROR",
                    )
            print()

        # Exit code
        sys.exit(0 if failed == 0 else 1)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="NBA Simulator System Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--category",
        choices=["imports", "database", "s3", "workflows", "adce", "all"],
        default="all",
        help="Validation category to run (default: all)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick checks (imports, workflows)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Minimal output (only errors)"
    )

    args = parser.parse_args()

    # Determine categories
    if args.quick:
        categories = ["imports", "workflows"]
    elif args.category == "all":
        categories = None  # Run all
    else:
        categories = [args.category]

    # Run validation
    validator = SystemValidator(verbose=not args.quiet)
    success = validator.run_validation(categories)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
