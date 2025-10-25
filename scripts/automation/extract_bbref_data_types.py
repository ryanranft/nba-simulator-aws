#!/usr/bin/env python3
"""
Extract all Basketball Reference data type specifications from tier documentation.

Purpose: Parse all 13 TIER_*.md files and extract scraping specifications
         for integration into ADCE autonomous collection system.

Output: Master catalog JSON with all data types, URL patterns, priorities

Usage:
    python scripts/automation/extract_bbref_data_types.py
    python scripts/automation/extract_bbref_data_types.py --output catalog.json
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse


class BasketballReferenceCatalogExtractor:
    """Extract data type specifications from Basketball Reference tier documentation"""

    def __init__(self, tier_docs_dir: str):
        """
        Initialize extractor.

        Args:
            tier_docs_dir: Path to directory containing TIER_*.md files
        """
        self.tier_docs_dir = Path(tier_docs_dir)
        self.data_types = []

    def extract_from_tier(self, tier_file: Path) -> List[Dict[str, Any]]:
        """
        Extract data type specifications from a single tier file.

        Args:
            tier_file: Path to TIER_N_*.md file

        Returns:
            List of data type specifications
        """
        print(f"📖 Reading {tier_file.name}...")

        with open(tier_file, "r") as f:
            content = f.read()

        # Extract tier metadata
        tier_match = re.search(r"\*\*Tier:\*\* (\d+) of 13", content)
        priority_match = re.search(r"\*\*Priority:\*\* (\w+)", content)
        data_types_match = re.search(r"\*\*Data Types:\*\* (\d+)", content)
        time_match = re.search(r"\*\*Estimated Time:\*\* ([\d-]+) hours", content)

        tier_num = int(tier_match.group(1)) if tier_match else 0
        priority = priority_match.group(1) if priority_match else "UNKNOWN"
        num_types = int(data_types_match.group(1)) if data_types_match else 0
        time_est = time_match.group(1) if time_match else "0"

        print(
            f"   Tier {tier_num}: {priority} priority, {num_types} data types, {time_est}h"
        )

        # Extract individual data type sections
        # Pattern: ### N. Data Type Name
        data_type_sections = re.split(r"###\s+\d+\.\s+", content)[1:]  # Skip header

        tier_data_types = []

        for section in data_type_sections:
            data_type = self._parse_data_type_section(section, tier_num, priority)
            if data_type:
                tier_data_types.append(data_type)

        print(f"   ✅ Extracted {len(tier_data_types)} data types")
        return tier_data_types

    def _parse_data_type_section(
        self, section: str, tier: int, priority: str
    ) -> Dict[str, Any]:
        """Parse a single data type section"""
        # Extract name (first line before newline)
        name_match = re.match(r"([^\n]+)", section)
        if not name_match:
            return None

        name = name_match.group(1).strip()

        # Extract URL pattern
        url_pattern = None
        url_match = re.search(r"\*\*URL Pattern:\*\*\s+`([^`]+)`", section)
        if url_match:
            url_pattern = url_match.group(1)

        # Extract table ID
        table_id = None
        table_match = re.search(r"\*\*Table ID:\*\*\s+`([^`]+)`", section)
        if table_match:
            table_id = table_match.group(1)

        # Extract coverage
        coverage_match = re.search(r"\*\*Coverage:\*\*\s+([^\n]+)", section)
        coverage = coverage_match.group(1) if coverage_match else "Unknown"

        # Extract records estimate
        records_match = re.search(r"\*\*Records:\*\*\s+([^\n]+)", section)
        records = records_match.group(1) if records_match else "Unknown"

        # Extract time estimate
        time_match = re.search(r"\*\*Time:\*\*\s+([\d-]+)\s*hours?", section)
        time_hours = time_match.group(1) if time_match else "0"

        # Extract S3 path
        s3_match = re.search(r"\*\*S3 Path:\*\*\s+`([^`]+)`", section)
        s3_path = s3_match.group(1) if s3_match else None

        # Convert name to snake_case identifier
        identifier = name.lower()
        identifier = re.sub(r"[^a-z0-9]+", "_", identifier)
        identifier = identifier.strip("_")

        return {
            "name": name,
            "identifier": identifier,
            "tier": tier,
            "priority": priority,
            "url_pattern": url_pattern,
            "table_id": table_id,
            "coverage": coverage,
            "estimated_records": records,
            "estimated_hours": time_hours,
            "s3_path": s3_path,
            "description": (
                section[:200].strip() + "..." if len(section) > 200 else section.strip()
            ),
        }

    def extract_all_tiers(self) -> List[Dict[str, Any]]:
        """Extract from all TIER_*.md files"""
        tier_files = sorted(self.tier_docs_dir.glob("TIER_*.md"))

        if not tier_files:
            raise FileNotFoundError(f"No TIER_*.md files found in {self.tier_docs_dir}")

        print(f"\n🔍 Found {len(tier_files)} tier files")
        print("=" * 70)

        all_data_types = []

        for tier_file in tier_files:
            tier_data_types = self.extract_from_tier(tier_file)
            all_data_types.extend(tier_data_types)

        return all_data_types

    def generate_catalog(self) -> Dict[str, Any]:
        """Generate master catalog with statistics"""
        data_types = self.extract_all_tiers()

        # Calculate statistics
        by_tier = {}
        by_priority = {}
        total_hours = 0

        for dt in data_types:
            # By tier
            tier = dt["tier"]
            if tier not in by_tier:
                by_tier[tier] = []
            by_tier[tier].append(dt["identifier"])

            # By priority
            priority = dt["priority"]
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(dt["identifier"])

            # Total hours
            hours_str = dt["estimated_hours"]
            if "-" in hours_str:
                hours = sum(map(float, hours_str.split("-"))) / 2
            else:
                hours = float(hours_str) if hours_str.replace(".", "").isdigit() else 0
            total_hours += hours

        catalog = {
            "metadata": {
                "total_data_types": len(data_types),
                "total_tiers": len(by_tier),
                "total_estimated_hours": round(total_hours, 1),
                "priorities": {k: len(v) for k, v in by_priority.items()},
                "data_types_by_tier": {k: len(v) for k, v in by_tier.items()},
            },
            "data_types": data_types,
            "by_tier": by_tier,
            "by_priority": by_priority,
        }

        return catalog

    def save_catalog(self, output_path: str):
        """Save catalog to JSON file"""
        catalog = self.generate_catalog()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(catalog, f, indent=2)

        print("\n" + "=" * 70)
        print("📊 CATALOG STATISTICS")
        print("=" * 70)
        print(f"Total Data Types: {catalog['metadata']['total_data_types']}")
        print(f"Total Tiers: {catalog['metadata']['total_tiers']}")
        print(f"Total Estimated Hours: {catalog['metadata']['total_estimated_hours']}")
        print(f"\nBy Priority:")
        for priority, count in catalog["metadata"]["priorities"].items():
            print(f"  {priority}: {count} data types")
        print(f"\nBy Tier:")
        for tier, count in sorted(catalog["metadata"]["data_types_by_tier"].items()):
            print(f"  Tier {tier}: {count} data types")
        print("=" * 70)
        print(f"\n✅ Catalog saved to: {output_file}")
        print(f"   {len(catalog['data_types'])} data types ready for ADCE integration")


def main():
    parser = argparse.ArgumentParser(
        description="Extract Basketball Reference data type specifications from tier documentation"
    )
    parser.add_argument(
        "--tier-docs-dir",
        default="docs/phases/phase_0/0.4_basketball_reference",
        help="Directory containing TIER_*.md files",
    )
    parser.add_argument(
        "--output",
        default="config/basketball_reference_data_types_catalog.json",
        help="Output path for catalog JSON",
    )

    args = parser.parse_args()

    print("\n🏀 Basketball Reference Data Type Catalog Extractor")
    print("=" * 70)

    extractor = BasketballReferenceCatalogExtractor(args.tier_docs_dir)
    extractor.save_catalog(args.output)

    print("\n✅ Extraction complete!")
    print("\nNext steps:")
    print("  1. Review catalog: cat", args.output)
    print(
        "  2. Generate scraper configs: python scripts/automation/generate_bbref_scrapers.py"
    )
    print("  3. Deploy to ADCE: python scripts/autonomous/deploy_new_scrapers.py")


if __name__ == "__main__":
    main()
