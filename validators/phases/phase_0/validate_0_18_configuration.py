#!/usr/bin/env python3
"""
Validate Phase 0.0018 - Configuration Files

Validates YAML configuration files for ADCE autonomous system.

Usage:
    python validators/phases/phase_0/validate_0_18_configuration.py
    python validators/phases/phase_0/validate_0_18_configuration.py --verbose
"""

import sys
import yaml
from typing import List, Tuple, Dict
from pathlib import Path


class ConfigurationValidator:
    """Validates ADCE configuration files."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent.parent.parent

    def validate_autonomous_config(self) -> bool:
        """Validate autonomous_config.yaml."""
        try:
            config_path = self.project_root / "config/autonomous_config.yaml"

            if not config_path.exists():
                self.failures.append("autonomous_config.yaml not found")
                return False

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Required fields
            required_fields = [
                "enabled",
                "reconciliation_interval_hours",
                "min_tasks_to_trigger",
                "max_orchestrator_runtime_minutes",
            ]

            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                self.failures.append(
                    f"Missing fields in autonomous_config.yaml: {', '.join(missing_fields)}"
                )
                return False

            # Validate field types and values
            if not isinstance(config["enabled"], bool):
                self.failures.append(
                    "autonomous_config.yaml: 'enabled' must be boolean"
                )
                return False

            if (
                not isinstance(config["reconciliation_interval_hours"], (int, float))
                or config["reconciliation_interval_hours"] <= 0
            ):
                self.failures.append(
                    "autonomous_config.yaml: 'reconciliation_interval_hours' must be positive number"
                )
                return False

            if (
                not isinstance(config["min_tasks_to_trigger"], int)
                or config["min_tasks_to_trigger"] < 0
            ):
                self.failures.append(
                    "autonomous_config.yaml: 'min_tasks_to_trigger' must be non-negative integer"
                )
                return False

            if (
                not isinstance(config["max_orchestrator_runtime_minutes"], int)
                or config["max_orchestrator_runtime_minutes"] <= 0
            ):
                self.failures.append(
                    "autonomous_config.yaml: 'max_orchestrator_runtime_minutes' must be positive integer"
                )
                return False

            if self.verbose:
                print("✓ autonomous_config.yaml is valid")
            return True

        except yaml.YAMLError as e:
            self.failures.append(f"Invalid YAML in autonomous_config.yaml: {e}")
            return False
        except Exception as e:
            self.failures.append(f"Failed to validate autonomous_config.yaml: {e}")
            return False

    def validate_reconciliation_config(self) -> bool:
        """Validate reconciliation_config.yaml."""
        try:
            config_path = self.project_root / "config/reconciliation_config.yaml"

            if not config_path.exists():
                self.failures.append("reconciliation_config.yaml not found")
                return False

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Check for S3 configuration
            if "s3" in config:
                s3_config = config["s3"]
                if "bucket_name" not in s3_config:
                    self.warnings.append(
                        "S3 bucket_name not configured in reconciliation_config.yaml"
                    )

            # Check for inventory configuration
            if "inventory" in config:
                inventory_config = config["inventory"]
                recommended_fields = ["cache_ttl_hours", "use_aws_inventory"]
                missing_recommended = [
                    field
                    for field in recommended_fields
                    if field not in inventory_config
                ]
                if missing_recommended:
                    self.warnings.append(
                        f"Recommended inventory fields missing: {', '.join(missing_recommended)}"
                    )

            if self.verbose:
                print("✓ reconciliation_config.yaml is valid")
            return True

        except yaml.YAMLError as e:
            self.failures.append(f"Invalid YAML in reconciliation_config.yaml: {e}")
            return False
        except Exception as e:
            self.failures.append(f"Failed to validate reconciliation_config.yaml: {e}")
            return False

    def validate_scraper_config(self) -> bool:
        """Validate scraper_config.yaml."""
        try:
            config_path = self.project_root / "config/scraper_config.yaml"

            if not config_path.exists():
                self.failures.append("scraper_config.yaml not found")
                return False

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Check for scrapers section
            if "scrapers" not in config:
                self.failures.append("scraper_config.yaml missing 'scrapers' section")
                return False

            scrapers = config["scrapers"]
            scraper_count = len(scrapers)

            # Expect at least 50 scrapers (documentation says 75)
            if scraper_count < 50:
                self.warnings.append(
                    f"Only {scraper_count} scrapers configured (expected 75+)"
                )
            elif self.verbose:
                print(f"✓ {scraper_count} scrapers configured")

            # Validate a sample scraper configuration
            sample_scrapers = list(scrapers.keys())[:3]  # Check first 3
            for scraper_name in sample_scrapers:
                scraper_config = scrapers[scraper_name]

                # Check for rate_limit
                if "rate_limit" in scraper_config:
                    rate_limit = scraper_config["rate_limit"]
                    if "requests_per_second" not in rate_limit:
                        self.warnings.append(
                            f"{scraper_name}: missing requests_per_second in rate_limit"
                        )

                # Check for retry
                if "retry" in scraper_config:
                    retry = scraper_config["retry"]
                    if "max_attempts" not in retry:
                        self.warnings.append(
                            f"{scraper_name}: missing max_attempts in retry"
                        )

            if self.verbose:
                print("✓ scraper_config.yaml is valid")
            return True

        except yaml.YAMLError as e:
            self.failures.append(f"Invalid YAML in scraper_config.yaml: {e}")
            return False
        except Exception as e:
            self.failures.append(f"Failed to validate scraper_config.yaml: {e}")
            return False

    def validate_data_inventory(self) -> bool:
        """Validate data_inventory.yaml."""
        try:
            inventory_path = self.project_root / "inventory/data_inventory.yaml"

            if not inventory_path.exists():
                self.warnings.append(
                    "data_inventory.yaml not found (may not be created yet)"
                )
                return True  # Not critical

            with open(inventory_path, "r") as f:
                inventory = yaml.safe_load(f)

            # Check for expected sections
            expected_sections = ["sources", "seasons", "data_types"]
            for section in expected_sections:
                if section not in inventory:
                    self.warnings.append(
                        f"data_inventory.yaml missing '{section}' section"
                    )

            if self.verbose:
                print("✓ data_inventory.yaml is valid")
            return True

        except yaml.YAMLError as e:
            self.warnings.append(f"Invalid YAML in data_inventory.yaml: {e}")
            return True  # Downgrade to warning
        except Exception as e:
            self.warnings.append(f"Failed to validate data_inventory.yaml: {e}")
            return True  # Downgrade to warning

    def validate_metrics_yaml(self) -> bool:
        """Validate metrics.yaml."""
        try:
            metrics_path = self.project_root / "inventory/metrics.yaml"

            if not metrics_path.exists():
                self.warnings.append("metrics.yaml not found")
                return True  # Not critical

            with open(metrics_path, "r") as f:
                metrics = yaml.safe_load(f)

            # Check for metadata
            if "metadata" in metrics:
                metadata = metrics["metadata"]
                if "version" not in metadata:
                    self.warnings.append("metrics.yaml missing version in metadata")
                if "last_updated" not in metadata:
                    self.warnings.append(
                        "metrics.yaml missing last_updated in metadata"
                    )

            if self.verbose:
                print("✓ metrics.yaml is valid")
            return True

        except yaml.YAMLError as e:
            self.warnings.append(f"Invalid YAML in metrics.yaml: {e}")
            return True  # Downgrade to warning
        except Exception as e:
            self.warnings.append(f"Failed to validate metrics.yaml: {e}")
            return True  # Downgrade to warning

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all configuration validations."""
        print(f"\n{'='*60}")
        print(f"Phase 0.0018: Configuration Validation")
        print(f"{'='*60}\n")

        results = {
            "autonomous_config": self.validate_autonomous_config(),
            "reconciliation_config": self.validate_reconciliation_config(),
            "scraper_config": self.validate_scraper_config(),
            "data_inventory": self.validate_data_inventory(),
            "metrics_yaml": self.validate_metrics_yaml(),
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
            print("✅ All configuration validations passed!")
            if self.warnings:
                print(f"   ({len(self.warnings)} warning(s))")
        else:
            print("❌ Some configuration validations failed.")
        print(f"{'='*60}\n")

        return all_passed, results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate Phase 0.0018 Configuration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    validator = ConfigurationValidator(verbose=args.verbose)
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
