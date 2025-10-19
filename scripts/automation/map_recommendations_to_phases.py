#!/usr/bin/env python3
"""
Recommendation Mapper

Maps rec_XXX IDs to their corresponding phase directory structure.
Scans all phase directories and creates a JSON mapping file for quick lookup.

Usage:
    python scripts/automation/map_recommendations_to_phases.py
    python scripts/automation/map_recommendations_to_phases.py --output custom_path.json
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class RecommendationMapper:
    """Maps recommendation IDs to phase directory locations."""

    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize the mapper.

        Args:
            workspace_root: Path to workspace root. If None, auto-detects.
        """
        if workspace_root is None:
            # Auto-detect workspace root
            current_file = Path(__file__).resolve()
            self.workspace_root = current_file.parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root)

        self.phases_dir = self.workspace_root / "docs" / "phases"
        self.mapping: Dict[str, Dict[str, str]] = {}

    def scan_phase_directories(self) -> Dict[str, Dict[str, str]]:
        """
        Scan all phase directories and extract recommendation mappings.

        Returns:
            Dictionary mapping rec_XXX to directory info
        """
        mapping = {}

        # Pattern to match rec_XXX in file names
        rec_pattern = re.compile(r"rec_(\d{3})")

        # Scan all phase directories
        for phase_num in range(9):  # Phases 0-8
            phase_dir = self.phases_dir / f"phase_{phase_num}"

            if not phase_dir.exists():
                continue

            # Scan subdirectories
            for subdir in phase_dir.iterdir():
                if not subdir.is_dir():
                    continue

                dir_name = subdir.name

                # Check if directory contains implementation files with rec_XXX pattern
                impl_files = list(subdir.glob("implement_rec_*.py"))
                if not impl_files:
                    continue

                # Extract rec_id from implementation file
                impl_file = impl_files[0]
                match = rec_pattern.search(impl_file.name)

                if match:
                    rec_id = f"rec_{match.group(1)}"

                    # Extract metadata from README.md if exists
                    readme_path = subdir / "README.md"
                    title = "Unknown"
                    priority = "Unknown"
                    status = "Unknown"

                    if readme_path.exists():
                        try:
                            with open(readme_path, "r") as f:
                                content = f.read()

                                # Extract title (first # heading)
                                title_match = re.search(
                                    r"^#\s+(.+)$", content, re.MULTILINE
                                )
                                if title_match:
                                    title = title_match.group(1).strip()

                                # Extract priority
                                priority_match = re.search(
                                    r"\*\*Priority:\*\*\s+(.+)$", content, re.MULTILINE
                                )
                                if priority_match:
                                    priority = priority_match.group(1).strip()

                                # Extract status
                                status_match = re.search(
                                    r"\*\*Status:\*\*\s+(.+)$", content, re.MULTILINE
                                )
                                if status_match:
                                    status = status_match.group(1).strip()

                        except Exception as e:
                            print(f"Warning: Could not read {readme_path}: {e}")

                    # Store mapping
                    mapping[rec_id] = {
                        "phase": f"phase_{phase_num}",
                        "directory": str(subdir.relative_to(self.workspace_root)),
                        "dir_name": dir_name,
                        "title": title,
                        "priority": priority,
                        "status": status,
                        "has_readme": readme_path.exists(),
                        "has_implementation": (
                            subdir / f"implement_{rec_id}.py"
                        ).exists(),
                        "has_tests": (subdir / f"test_{rec_id}.py").exists(),
                        "has_status": (subdir / "STATUS.md").exists(),
                        "has_guide": (subdir / "IMPLEMENTATION_GUIDE.md").exists(),
                    }

        return mapping

    def save_mapping(self, output_path: Optional[str] = None) -> str:
        """
        Save the mapping to a JSON file.

        Args:
            output_path: Path to output file. If None, uses default location.

        Returns:
            Path to saved file
        """
        if output_path is None:
            output_path = self.workspace_root / "data" / "recommendation_mapping.json"
        else:
            output_path = Path(output_path)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Scan if not already done
        if not self.mapping:
            self.mapping = self.scan_phase_directories()

        # Save to JSON
        with open(output_path, "w") as f:
            json.dump(self.mapping, f, indent=2, sort_keys=True)

        return str(output_path)

    def get_recommendation_path(self, rec_id: str) -> Optional[Path]:
        """
        Get the absolute path to a recommendation directory.

        Args:
            rec_id: Recommendation ID (e.g., 'rec_001')

        Returns:
            Path to recommendation directory or None if not found
        """
        if not self.mapping:
            self.mapping = self.scan_phase_directories()

        if rec_id in self.mapping:
            rel_path = self.mapping[rec_id]["directory"]
            return self.workspace_root / rel_path

        return None

    def get_recommendation_info(self, rec_id: str) -> Optional[Dict[str, str]]:
        """
        Get full information about a recommendation.

        Args:
            rec_id: Recommendation ID (e.g., 'rec_001')

        Returns:
            Dictionary with recommendation metadata or None if not found
        """
        if not self.mapping:
            self.mapping = self.scan_phase_directories()

        return self.mapping.get(rec_id)

    def list_recommendations_by_phase(self, phase_num: int) -> List[str]:
        """
        List all recommendation IDs in a specific phase.

        Args:
            phase_num: Phase number (0-8)

        Returns:
            List of recommendation IDs
        """
        if not self.mapping:
            self.mapping = self.scan_phase_directories()

        phase_key = f"phase_{phase_num}"
        return [
            rec_id
            for rec_id, info in self.mapping.items()
            if info["phase"] == phase_key
        ]

    def generate_report(self) -> str:
        """
        Generate a human-readable report of the mapping.

        Returns:
            Formatted report string
        """
        if not self.mapping:
            self.mapping = self.scan_phase_directories()

        report = []
        report.append("=" * 80)
        report.append("RECOMMENDATION MAPPING REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Total Recommendations Found: {len(self.mapping)}")
        report.append("")

        # Count by phase
        phase_counts = {}
        for rec_id, info in self.mapping.items():
            phase = info["phase"]
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

        report.append("Distribution by Phase:")
        for phase_num in range(9):
            phase_key = f"phase_{phase_num}"
            count = phase_counts.get(phase_key, 0)
            report.append(f"  {phase_key}: {count} recommendations")

        report.append("")

        # Count by completeness
        complete_files = {
            "readme": 0,
            "implementation": 0,
            "tests": 0,
            "status": 0,
            "guide": 0,
            "all_files": 0,
        }

        for rec_id, info in self.mapping.items():
            if info["has_readme"]:
                complete_files["readme"] += 1
            if info["has_implementation"]:
                complete_files["implementation"] += 1
            if info["has_tests"]:
                complete_files["tests"] += 1
            if info["has_status"]:
                complete_files["status"] += 1
            if info["has_guide"]:
                complete_files["guide"] += 1
            if all(
                [
                    info["has_readme"],
                    info["has_implementation"],
                    info["has_tests"],
                    info["has_status"],
                    info["has_guide"],
                ]
            ):
                complete_files["all_files"] += 1

        report.append("File Completeness:")
        report.append(f"  README.md: {complete_files['readme']}/{len(self.mapping)}")
        report.append(
            f"  implement_rec_XXX.py: {complete_files['implementation']}/{len(self.mapping)}"
        )
        report.append(
            f"  test_rec_XXX.py: {complete_files['tests']}/{len(self.mapping)}"
        )
        report.append(f"  STATUS.md: {complete_files['status']}/{len(self.mapping)}")
        report.append(
            f"  IMPLEMENTATION_GUIDE.md: {complete_files['guide']}/{len(self.mapping)}"
        )
        report.append(
            f"  All 5 files present: {complete_files['all_files']}/{len(self.mapping)}"
        )

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Map recommendation IDs to phase directories"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path (default: data/recommendation_mapping.json)",
    )
    parser.add_argument(
        "--workspace", "-w", help="Workspace root path (default: auto-detect)"
    )
    parser.add_argument(
        "--report", "-r", action="store_true", help="Print human-readable report"
    )
    parser.add_argument(
        "--phase", "-p", type=int, help="List recommendations in specific phase (0-8)"
    )
    parser.add_argument(
        "--rec", help="Get info for specific recommendation (e.g., rec_001)"
    )

    args = parser.parse_args()

    # Initialize mapper
    mapper = RecommendationMapper(workspace_root=args.workspace)

    # Handle specific commands
    if args.rec:
        # Get info for specific recommendation
        info = mapper.get_recommendation_info(args.rec)
        if info:
            print(json.dumps(info, indent=2))
        else:
            print(f"Recommendation {args.rec} not found.")
            return 1

    elif args.phase is not None:
        # List recommendations in phase
        recs = mapper.list_recommendations_by_phase(args.phase)
        print(f"Recommendations in phase_{args.phase}:")
        for rec_id in sorted(recs):
            info = mapper.get_recommendation_info(rec_id)
            print(f"  {rec_id}: {info['title']}")
        print(f"\nTotal: {len(recs)} recommendations")

    else:
        # Generate mapping and save
        output_path = mapper.save_mapping(output_path=args.output)
        print(f"Mapping saved to: {output_path}")
        print(f"Total recommendations mapped: {len(mapper.mapping)}")

        # Print report if requested
        if args.report:
            print("\n" + mapper.generate_report())

    return 0


if __name__ == "__main__":
    exit(main())
