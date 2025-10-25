#!/usr/bin/env python3
"""
Generate Basketball Reference scraper configurations for ADCE integration.

Purpose: Convert data type catalog into YAML scraper configurations
         that can be loaded by the ADCE autonomous collection system.

Usage:
    python scripts/automation/generate_bbref_scrapers.py
    python scripts/automation/generate_bbref_scrapers.py --catalog catalog.json --output scrapers.yaml
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
import argparse


class BasketballReferenceScraperGenerator:
    """Generate scraper configurations for Basketball Reference data types"""

    def __init__(self, catalog_path: str):
        """
        Initialize generator.

        Args:
            catalog_path: Path to data types catalog JSON
        """
        self.catalog_path = Path(catalog_path)
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        """Load data types catalog"""
        with open(self.catalog_path, "r") as f:
            return json.load(f)

    def generate_scraper_config(self, data_type: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate scraper configuration for a single data type.

        Args:
            data_type: Data type specification from catalog

        Returns:
            Scraper configuration dict
        """
        identifier = data_type["identifier"]

        # Base configuration inheriting from basketball_reference defaults
        config = {
            "base_url": "https://www.basketball-reference.com",
            "data_type": identifier,
            "tier": data_type["tier"],
            "priority": data_type["priority"].lower(),
            "rate_limit": {
                "requests_per_second": 0.5,  # 12 second delay
                "burst_size": 5,
                "adaptive": True,
                "retry_after_header": True,
            },
            "retry": {
                "max_attempts": 5,
                "base_delay": 2.0,
                "max_delay": 120.0,
                "exponential_backoff": True,
                "jitter": True,
            },
            "timeout": 45,
            "user_agent": "NBA-Simulator-ADCE/1.0",
            "max_concurrent": 5,
            "storage": {
                "s3_bucket": "nba-sim-raw-data-lake",
                "local_output_dir": f"/tmp/bbref_scraper/{identifier}",
                "upload_to_s3": True,
                "compression": False,
            },
            "monitoring": {
                "enable_telemetry": True,
                "log_level": "INFO",
                "track_progress": True,
            },
        }

        # Add URL pattern if available
        if data_type.get("url_pattern"):
            config["url_pattern"] = data_type["url_pattern"]

        # Add table ID if available
        if data_type.get("table_id"):
            config["table_id"] = data_type["table_id"]

        # Add S3 path if available
        if data_type.get("s3_path"):
            # Extract path from full S3 URL
            s3_path = data_type["s3_path"]
            if "s3://" in s3_path:
                s3_path = s3_path.split("s3://nba-sim-raw-data-lake/")[-1]
            config["storage"]["s3_prefix"] = s3_path

        # Add coverage info as metadata
        config["metadata"] = {
            "name": data_type["name"],
            "coverage": data_type.get("coverage", "Unknown"),
            "estimated_records": data_type.get("estimated_records", "Unknown"),
            "estimated_hours": data_type.get("estimated_hours", "0"),
            "description": data_type.get("description", "")[:200],
        }

        return config

    def generate_all_configs(self) -> Dict[str, Any]:
        """Generate configurations for all data types"""
        print(f"\n🔧 Generating scraper configurations...")
        print("=" * 70)

        scrapers = {}

        for data_type in self.catalog["data_types"]:
            identifier = data_type["identifier"]
            scraper_name = f"basketball_reference_{identifier}"

            config = self.generate_scraper_config(data_type)
            scrapers[scraper_name] = config

            tier = data_type["tier"]
            priority = data_type["priority"]
            print(f"  ✅ {scraper_name}")
            print(f"     Tier {tier} | {priority} priority")

        print("=" * 70)
        print(f"\n✅ Generated {len(scrapers)} scraper configurations")

        return scrapers

    def save_yaml(self, output_path: str):
        """Save scraper configurations to YAML"""
        scrapers = self.generate_all_configs()

        # Wrap in scrapers: key for compatibility with scraper_config.yaml
        output = {
            "scrapers": scrapers,
            "metadata": {
                "generated_from": str(self.catalog_path),
                "total_scrapers": len(scrapers),
                "basketball_reference_tiers": self.catalog["metadata"]["total_tiers"],
                "total_estimated_hours": self.catalog["metadata"][
                    "total_estimated_hours"
                ],
            },
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False, width=120)

        print(f"\n✅ Scraper configurations saved to: {output_file}")
        print(f"   {len(scrapers)} scrapers ready for ADCE integration")

        return output_file

    def merge_with_existing_config(self, existing_config_path: str, output_path: str):
        """Merge new scrapers with existing scraper_config.yaml"""
        print(f"\n🔗 Merging with existing config: {existing_config_path}")

        # Load existing config
        with open(existing_config_path, "r") as f:
            existing = yaml.safe_load(f)

        # Generate new scrapers
        new_scrapers = self.generate_all_configs()

        # Merge
        if "scrapers" not in existing:
            existing["scrapers"] = {}

        for scraper_name, config in new_scrapers.items():
            if scraper_name in existing["scrapers"]:
                print(f"  ⚠️  Skipping {scraper_name} (already exists)")
            else:
                existing["scrapers"][scraper_name] = config
                print(f"  ✅ Added {scraper_name}")

        # Save merged config
        output_file = Path(output_path)
        with open(output_file, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False, width=120)

        print(f"\n✅ Merged config saved to: {output_file}")
        print(f"   Total scrapers: {len(existing['scrapers'])}")

        return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate Basketball Reference scraper configurations for ADCE"
    )
    parser.add_argument(
        "--catalog",
        default="config/basketball_reference_data_types_catalog.json",
        help="Path to data types catalog JSON",
    )
    parser.add_argument(
        "--output",
        default="config/basketball_reference_scrapers.yaml",
        help="Output path for scraper configurations YAML",
    )
    parser.add_argument(
        "--merge", help="Merge with existing scraper_config.yaml (provide path)"
    )

    args = parser.parse_args()

    print("\n🏀 Basketball Reference Scraper Configuration Generator")
    print("=" * 70)

    generator = BasketballReferenceScraperGenerator(args.catalog)

    if args.merge:
        # Merge with existing config
        output_file = generator.merge_with_existing_config(
            args.merge,
            (
                args.output
                if args.output != "config/basketball_reference_scrapers.yaml"
                else args.merge
            ),
        )
    else:
        # Generate standalone config
        output_file = generator.save_yaml(args.output)

    print("\n✅ Configuration generation complete!")
    print("\nNext steps:")
    print("  1. Review configs: cat", output_file)
    print(
        "  2. Update ADCE reconciliation: python scripts/automation/update_adce_reconciliation.py"
    )
    print("  3. Deploy to ADCE: python scripts/autonomous/deploy_new_scrapers.py")


if __name__ == "__main__":
    main()
