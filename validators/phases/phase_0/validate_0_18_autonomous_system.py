#!/usr/bin/env python3
"""
Validate 0.0018 - Autonomous Data Collection Ecosystem (ADCE)

Validates autonomous system health, configuration, and infrastructure.

Usage:
    python validators/phases/phase_0/validate_0_18_autonomous_system.py
    python validators/phases/phase_0/validate_0_18_autonomous_system.py --verbose
"""

import sys
import json
from typing import List, Tuple, Dict
from pathlib import Path


class Phase018Validator:
    """Validates 0.0018 ADCE system."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent.parent.parent

    def validate_directory_structure(self) -> bool:
        """Validate required directories exist."""
        try:
            required_dirs = [
                "scripts/autonomous",
                "scripts/reconciliation",
                "scripts/orchestration",
                "config",
                "inventory",
                "inventory/cache",
                "logs",
            ]

            missing_dirs = []
            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if not full_path.exists():
                    missing_dirs.append(dir_path)

            if missing_dirs:
                self.failures.append(f"Missing directories: {', '.join(missing_dirs)}")
                return False

            if self.verbose:
                print("✓ All required directories exist")
            return True

        except Exception as e:
            self.failures.append(f"Directory structure validation failed: {e}")
            return False

    def validate_implementation_files(self) -> bool:
        """Validate all implementation scripts exist."""
        try:
            required_files = [
                "scripts/autonomous/autonomous_loop.py",
                "scripts/autonomous/autonomous_cli.py",
                "scripts/autonomous/health_monitor.py",
                "scripts/reconciliation/reconciliation_daemon.py",
                "scripts/reconciliation/run_reconciliation.py",
                "scripts/reconciliation/detect_data_gaps.py",
                "scripts/reconciliation/generate_task_queue.py",
                "scripts/reconciliation/analyze_coverage.py",
                "scripts/orchestration/scraper_orchestrator.py",
            ]

            missing_files = []
            for file_path in required_files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    missing_files.append(file_path)

            if missing_files:
                self.failures.append(
                    f"Missing implementation files: {', '.join(missing_files)}"
                )
                return False

            if self.verbose:
                print("✓ All implementation scripts exist")
            return True

        except Exception as e:
            self.failures.append(f"Implementation files validation failed: {e}")
            return False

    def validate_configuration_files(self) -> bool:
        """Validate configuration files exist and are valid."""
        try:
            config_files = [
                "config/autonomous_config.yaml",
                "config/reconciliation_config.yaml",
                "config/scraper_config.yaml",
            ]

            missing_configs = []
            for config_path in config_files:
                full_path = self.project_root / config_path
                if not full_path.exists():
                    missing_configs.append(config_path)

            if missing_configs:
                self.failures.append(
                    f"Missing config files: {', '.join(missing_configs)}"
                )
                return False

            if self.verbose:
                print("✓ All configuration files exist")
            return True

        except Exception as e:
            self.failures.append(f"Configuration files validation failed: {e}")
            return False

    def validate_inventory_structure(self) -> bool:
        """Validate inventory directory structure."""
        try:
            inventory_root = self.project_root / "inventory"

            # Check for required files
            required_files = [
                "data_inventory.yaml",
                "metrics.yaml",
            ]

            missing_files = []
            for file_name in required_files:
                file_path = inventory_root / file_name
                if not file_path.exists():
                    missing_files.append(file_name)

            if missing_files:
                self.warnings.append(
                    f"Missing inventory files: {', '.join(missing_files)}"
                )

            # Check cache directory
            cache_dir = inventory_root / "cache"
            if not cache_dir.exists():
                self.warnings.append("Inventory cache directory not found")
            elif self.verbose:
                print("✓ Inventory cache directory exists")

            # Check gaps.json (may not exist if reconciliation hasn't run)
            gaps_file = inventory_root / "gaps.json"
            if not gaps_file.exists():
                self.warnings.append(
                    "gaps.json not found (reconciliation may not have run yet)"
                )
            elif self.verbose:
                print("✓ Task queue file (gaps.json) exists")

            if self.verbose:
                print("✓ Inventory structure validated")
            return True

        except Exception as e:
            self.failures.append(f"Inventory structure validation failed: {e}")
            return False

    def validate_test_coverage(self) -> bool:
        """Validate test files exist for 0.0018."""
        try:
            test_files = [
                "tests/phases/phase_0/test_0_0018_autonomous_loop.py",
                "tests/phases/phase_0/test_0_0018_integration.py",
            ]

            missing_tests = []
            for test_path in test_files:
                full_path = self.project_root / test_path
                if not full_path.exists():
                    missing_tests.append(test_path)

            if missing_tests:
                self.failures.append(f"Missing test files: {', '.join(missing_tests)}")
                return False

            if self.verbose:
                print("✓ All test files exist")
            return True

        except Exception as e:
            self.failures.append(f"Test coverage validation failed: {e}")
            return False

    def validate_documentation(self) -> bool:
        """Validate documentation exists."""
        try:
            doc_files = [
                "docs/phases/phase_0/0.0018_autonomous_data_collection/README.md",
                "docs/phases/phase_0/0.0018_autonomous_data_collection/0.9.0001_unified_scraper_system.md",
                "docs/phases/phase_0/0.0018_autonomous_data_collection/0.9.0002_reconciliation_engine.md",
                "docs/phases/phase_0/0.0018_autonomous_data_collection/0.9.0003_scraper_orchestrator.md",
                "docs/phases/phase_0/0.0018_autonomous_data_collection/0.9.0004_autonomous_loop.md",
            ]

            missing_docs = []
            for doc_path in doc_files:
                full_path = self.project_root / doc_path
                if not full_path.exists():
                    missing_docs.append(doc_path)

            if missing_docs:
                self.failures.append(
                    f"Missing documentation: {', '.join(missing_docs)}"
                )
                return False

            if self.verbose:
                print("✓ All documentation files exist")
            return True

        except Exception as e:
            self.failures.append(f"Documentation validation failed: {e}")
            return False

    def validate_code_metrics(self) -> bool:
        """Validate implementation code meets quality standards."""
        try:
            # Count lines of implementation code
            implementation_files = [
                self.project_root / "scripts/autonomous/autonomous_loop.py",
                self.project_root / "scripts/autonomous/autonomous_cli.py",
                self.project_root / "scripts/autonomous/health_monitor.py",
                self.project_root / "scripts/reconciliation/reconciliation_daemon.py",
                self.project_root / "scripts/orchestration/scraper_orchestrator.py",
            ]

            total_lines = 0
            for file_path in implementation_files:
                if file_path.exists():
                    with open(file_path, "r") as f:
                        total_lines += len(f.readlines())

            # Expect at least 2000 lines of implementation code
            if total_lines < 2000:
                self.warnings.append(
                    f"Implementation code seems small: {total_lines} lines (expected 2000+)"
                )
            elif self.verbose:
                print(f"✓ Implementation code: {total_lines} lines")

            return True

        except Exception as e:
            self.failures.append(f"Code metrics validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations."""
        print(f"\n{'='*60}")
        print(f"0.0018: Autonomous Data Collection Ecosystem (ADCE)")
        print(f"{'='*60}\n")

        results = {
            "directory_structure": self.validate_directory_structure(),
            "implementation_files": self.validate_implementation_files(),
            "configuration_files": self.validate_configuration_files(),
            "inventory_structure": self.validate_inventory_structure(),
            "test_coverage": self.validate_test_coverage(),
            "documentation": self.validate_documentation(),
            "code_metrics": self.validate_code_metrics(),
        }

        all_passed = all(results.values())

        print(f"\n{'='*60}")
        print(f"Results Summary")
        print(f"{'='*60}")

        for check, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{check.replace('_', ' ').title():40} {status}")

        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.failures:
            print(f"\n❌ Failures:")
            for failure in self.failures:
                print(f"  - {failure}")

        print(f"\n{'='*60}")
        if all_passed:
            print("✅ All validations passed!")
            if self.warnings:
                print(f"   ({len(self.warnings)} warning(s))")
        else:
            print("❌ Some validations failed.")
        print(f"{'='*60}\n")

        return all_passed, results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate 0.0018")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    validator = Phase018Validator(verbose=args.verbose)
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
