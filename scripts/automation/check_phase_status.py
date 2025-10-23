#!/usr/bin/env python3
"""
Check Phase Completion Status

This script checks the status of all phases and sub-phases in the NBA Simulator AWS project.
It provides an overview of completion progress similar to check_recommendation_status.py.

Usage:
    python scripts/automation/check_phase_status.py
    python scripts/automation/check_phase_status.py --phase 0
    python scripts/automation/check_phase_status.py --verbose
    python scripts/automation/check_phase_status.py --next

Author: Claude Code
Created: October 23, 2025
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class PhaseStatusChecker:
    """Check and report phase completion status."""

    def __init__(self, project_root: Path = None):
        """Initialize status checker."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.phases_dir = self.project_root / "docs" / "phases"
        self.phase_data = {}

    def check_all_phases(self) -> Dict[int, Dict]:
        """Check status of all phases."""
        phase_data = {}

        # Check Phase 0 (special location: docs/phases/phase_0/PHASE_0_INDEX.md)
        phase_0_index = self.phases_dir / "phase_0" / "PHASE_0_INDEX.md"
        if phase_0_index.exists():
            phase_data[0] = self._parse_phase_index(phase_0_index, 0)

        # Check Phases 1-9 (docs/phases/PHASE_N_INDEX.md)
        for phase_num in range(1, 10):
            phase_index = self.phases_dir / f"PHASE_{phase_num}_INDEX.md"
            if phase_index.exists():
                phase_data[phase_num] = self._parse_phase_index(phase_index, phase_num)

        self.phase_data = phase_data
        return phase_data

    def _parse_phase_index(self, index_file: Path, phase_num: int) -> Dict:
        """Parse a phase index file and extract sub-phase information."""
        content = index_file.read_text()

        # Extract phase status from overview
        phase_status_match = re.search(
            r"\*\*Status:\*\*\s*([🔄⏸️✅🔵]+)\s*(.*?)(?:\(|$)", content, re.MULTILINE
        )

        phase_status = "Unknown"
        if phase_status_match:
            phase_status = (
                phase_status_match.group(1) + " " + phase_status_match.group(2).strip()
            )

        # Extract sub-phases from table
        # Look for table rows like: | **0.1** | [Name](link) | ✅ COMPLETE ✓ | ⭐ PRIORITY | Oct 1, 2025 |
        sub_phase_pattern = re.compile(
            r"\|\s*\*\*(\d+\.\d+)\*\*\s*\|\s*\[([^\]]+)\]\([^\)]+\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
        )

        sub_phases = []
        for match in sub_phase_pattern.finditer(content):
            sub_phase_id = match.group(1)
            sub_phase_name = match.group(2).strip()
            status = match.group(3).strip()
            priority = match.group(4).strip()
            completed_date = match.group(5).strip()

            # Check if validated (has ✓)
            validated = "✓" in status

            # Determine base status (remove validation checkmark)
            if "✅ COMPLETE" in status:
                base_status = "COMPLETE"
            elif "🔄 IN PROGRESS" in status:
                base_status = "IN_PROGRESS"
            elif "⏸️ PENDING" in status:
                base_status = "PENDING"
            elif "🔵 PLANNED" in status:
                base_status = "PLANNED"
            else:
                base_status = "UNKNOWN"

            sub_phases.append(
                {
                    "id": sub_phase_id,
                    "name": sub_phase_name,
                    "status": base_status,
                    "validated": validated,
                    "priority": priority,
                    "completed_date": completed_date if completed_date != "-" else None,
                }
            )

        # Count sub-phases by status
        complete_count = sum(1 for sp in sub_phases if sp["status"] == "COMPLETE")
        validated_count = sum(1 for sp in sub_phases if sp["validated"])
        in_progress_count = sum(1 for sp in sub_phases if sp["status"] == "IN_PROGRESS")
        pending_count = sum(1 for sp in sub_phases if sp["status"] == "PENDING")
        planned_count = sum(1 for sp in sub_phases if sp["status"] == "PLANNED")
        total_count = len(sub_phases)

        return {
            "phase_num": phase_num,
            "phase_status": phase_status,
            "sub_phases": sub_phases,
            "counts": {
                "total": total_count,
                "complete": complete_count,
                "validated": validated_count,
                "in_progress": in_progress_count,
                "pending": pending_count,
                "planned": planned_count,
            },
        }

    def print_summary(self, verbose: bool = False):
        """Print summary of all phases."""
        if not self.phase_data:
            self.check_all_phases()

        print("\n" + "=" * 70)
        print("Phase Completion Status")
        print("=" * 70 + "\n")

        total_sub_phases = 0
        total_complete = 0
        total_validated = 0
        total_pending = 0
        total_planned = 0

        for phase_num in sorted(self.phase_data.keys()):
            phase = self.phase_data[phase_num]
            counts = phase["counts"]

            total_sub_phases += counts["total"]
            total_complete += counts["complete"]
            total_validated += counts["validated"]
            total_pending += counts["pending"]
            total_planned += counts["planned"]

            # Phase header
            print(f"Phase {phase_num}: {phase['phase_status']}")
            print(f"  Sub-phases: {counts['complete']}/{counts['total']} complete")
            print(f"  Validated: {counts['validated']}/{counts['complete']} (with ✓)")

            if verbose:
                # Show each sub-phase
                for sp in phase["sub_phases"]:
                    status_emoji = {
                        "COMPLETE": "✅",
                        "IN_PROGRESS": "🔄",
                        "PENDING": "⏸️",
                        "PLANNED": "🔵",
                    }.get(sp["status"], "❓")

                    validated_mark = " ✓" if sp["validated"] else ""
                    print(
                        f"    {status_emoji} {sp['id']} - {sp['name']}{validated_mark}"
                    )

            print()

        # Overall summary
        print("=" * 70)
        print(f"Overall Progress:")
        print(f"  Phases: {len(self.phase_data)}/10")
        print(f"  Sub-phases: {total_sub_phases}")
        print(
            f"    ✅ Complete: {total_complete} ({100*total_complete/total_sub_phases if total_sub_phases > 0 else 0:.1f}%)"
        )
        print(
            f"    ✓ Validated: {total_validated} ({100*total_validated/total_complete if total_complete > 0 else 0:.1f}% of complete)"
        )
        print(f"    ⏸️ Pending: {total_pending}")
        print(f"    🔵 Planned: {total_planned}")
        print("=" * 70 + "\n")

    def print_phase_detail(self, phase_num: int):
        """Print detailed status for a specific phase."""
        if not self.phase_data:
            self.check_all_phases()

        if phase_num not in self.phase_data:
            print(f"❌ Phase {phase_num} not found")
            return

        phase = self.phase_data[phase_num]

        print("\n" + "=" * 70)
        print(f"Phase {phase_num} Detailed Status")
        print("=" * 70 + "\n")

        print(f"Status: {phase['phase_status']}")
        print(
            f"Sub-phases: {phase['counts']['complete']}/{phase['counts']['total']} complete\n"
        )

        print(f"{'ID':<8} {'Name':<40} {'Status':<15} {'Validated':<10} {'Date':<15}")
        print("-" * 90)

        for sp in phase["sub_phases"]:
            status_emoji = {
                "COMPLETE": "✅ COMPLETE",
                "IN_PROGRESS": "🔄 IN_PROGRESS",
                "PENDING": "⏸️ PENDING",
                "PLANNED": "🔵 PLANNED",
            }.get(sp["status"], "❓ UNKNOWN")

            validated = "✓" if sp["validated"] else ""
            date = sp["completed_date"] if sp["completed_date"] else "-"

            print(
                f"{sp['id']:<8} {sp['name'][:38]:<40} {status_emoji:<15} {validated:<10} {date:<15}"
            )

        print("=" * 70 + "\n")

    def get_next_sub_phase(self) -> Tuple[int, str, str]:
        """Get the next sub-phase to process."""
        if not self.phase_data:
            self.check_all_phases()

        # Priority order:
        # 1. Complete but not validated
        # 2. In progress
        # 3. Pending
        # 4. Planned (lowest priority)

        for phase_num in sorted(self.phase_data.keys()):
            phase = self.phase_data[phase_num]

            # Check for complete but not validated
            for sp in phase["sub_phases"]:
                if sp["status"] == "COMPLETE" and not sp["validated"]:
                    return phase_num, sp["id"], f"{sp['name']} (needs validation)"

            # Check for in progress
            for sp in phase["sub_phases"]:
                if sp["status"] == "IN_PROGRESS":
                    return phase_num, sp["id"], f"{sp['name']} (in progress)"

        # Check for pending/planned (after all phases checked for complete/in-progress)
        for phase_num in sorted(self.phase_data.keys()):
            phase = self.phase_data[phase_num]

            # Check for pending
            for sp in phase["sub_phases"]:
                if sp["status"] == "PENDING":
                    return phase_num, sp["id"], f"{sp['name']} (pending)"

            # Check for planned
            for sp in phase["sub_phases"]:
                if sp["status"] == "PLANNED":
                    return phase_num, sp["id"], f"{sp['name']} (planned)"

        return None, None, "All sub-phases complete!"

    def export_to_csv(self, output_file: Path):
        """Export phase status to CSV file."""
        if not self.phase_data:
            self.check_all_phases()

        import csv

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Phase",
                    "Sub-Phase ID",
                    "Name",
                    "Status",
                    "Validated",
                    "Priority",
                    "Completed Date",
                ]
            )

            for phase_num in sorted(self.phase_data.keys()):
                phase = self.phase_data[phase_num]
                for sp in phase["sub_phases"]:
                    writer.writerow(
                        [
                            f"Phase {phase_num}",
                            sp["id"],
                            sp["name"],
                            sp["status"],
                            "Yes" if sp["validated"] else "No",
                            sp["priority"],
                            sp["completed_date"] if sp["completed_date"] else "",
                        ]
                    )

        print(f"✅ Exported phase status to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check phase completion status")
    parser.add_argument(
        "--phase", type=int, help="Show detailed status for specific phase"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose output"
    )
    parser.add_argument(
        "--next", action="store_true", help="Show next sub-phase to process"
    )
    parser.add_argument("--export", type=str, help="Export to CSV file")

    args = parser.parse_args()

    checker = PhaseStatusChecker()

    if args.export:
        checker.check_all_phases()
        checker.export_to_csv(Path(args.export))
    elif args.next:
        phase_num, sub_phase_id, description = checker.get_next_sub_phase()
        if phase_num is not None:
            print(f"\n🎯 Next sub-phase to process:")
            print(f"   Phase {phase_num}.{sub_phase_id}: {description}\n")
        else:
            print(f"\n✅ {description}\n")
    elif args.phase is not None:
        checker.check_all_phases()
        checker.print_phase_detail(args.phase)
    else:
        checker.check_all_phases()
        checker.print_summary(verbose=args.verbose)


if __name__ == "__main__":
    main()
