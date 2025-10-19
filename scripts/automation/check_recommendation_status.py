#!/usr/bin/env python3
"""
Recommendation Status Checker

Scans all phase directories for STATUS.md files and reports on implementation status.
Identifies completed, in-progress, blocked, and next available recommendations.

Usage:
    python scripts/automation/check_recommendation_status.py
    python scripts/automation/check_recommendation_status.py --verbose
    python scripts/automation/check_recommendation_status.py --rec rec_001
    python scripts/automation/check_recommendation_status.py --next
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from datetime import datetime


class RecommendationStatusChecker:
    """Checks and reports on recommendation implementation status."""

    # Status emoji patterns
    STATUS_PATTERNS = {
        "PLANNED": r"🔵.*PLANNED",
        "IN_PROGRESS": r"🔄.*IN PROGRESS",
        "COMPLETE": r"✅.*COMPLETE",
        "BLOCKED": r"⚠️.*BLOCKED",
    }

    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize the status checker.

        Args:
            workspace_root: Path to workspace root. If None, auto-detects.
        """
        if workspace_root is None:
            current_file = Path(__file__).resolve()
            self.workspace_root = current_file.parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root)

        self.phases_dir = self.workspace_root / "docs" / "phases"
        self.progress_file = self.workspace_root / "BOOK_RECOMMENDATIONS_PROGRESS.md"
        self.mapping_file = self.workspace_root / "data" / "recommendation_mapping.json"

        self.statuses: Dict[str, Dict] = {}
        self.mapping: Dict[str, Dict] = {}

    def load_mapping(self) -> bool:
        """
        Load recommendation mapping from JSON file.

        Returns:
            True if mapping loaded successfully
        """
        if self.mapping_file.exists():
            with open(self.mapping_file, "r") as f:
                self.mapping = json.load(f)
            return True
        return False

    def scan_statuses(self) -> Dict[str, Dict]:
        """
        Scan all STATUS.md files and extract status information.

        Returns:
            Dictionary mapping rec_XXX to status info
        """
        statuses = {}
        rec_pattern = re.compile(r"rec_(\d{3})")

        # Load mapping if available
        if not self.mapping:
            self.load_mapping()

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

                if not match:
                    continue

                rec_id = f"rec_{match.group(1)}"
                status_path = subdir / "STATUS.md"

                if not status_path.exists():
                    statuses[rec_id] = {
                        "status": "MISSING",
                        "phase": phase_num,
                        "directory": str(subdir),
                        "has_status_file": False,
                    }
                    continue

                # Read STATUS.md
                try:
                    with open(status_path, "r") as f:
                        content = f.read()

                    # Determine status
                    status = "UNKNOWN"
                    for status_name, pattern in self.STATUS_PATTERNS.items():
                        if re.search(pattern, content):
                            status = status_name
                            break

                    # Extract additional info
                    priority = "Unknown"
                    priority_match = re.search(
                        r"\*\*Priority:\*\*\s+(.+)$", content, re.MULTILINE
                    )
                    if priority_match:
                        priority = priority_match.group(1).strip()

                    estimated_time = "Unknown"
                    time_match = re.search(
                        r"\*\*Estimated Time:\*\*\s+(.+)$", content, re.MULTILINE
                    )
                    if time_match:
                        estimated_time = time_match.group(1).strip()

                    risk = "Unknown"
                    risk_match = re.search(
                        r"\*\*Risk Level:\*\*\s+(.+)$", content, re.MULTILINE
                    )
                    if risk_match:
                        risk = risk_match.group(1).strip()

                    # Extract dependencies
                    dependencies = []
                    dep_section = re.search(
                        r"\*\*Prerequisites:\*\*\s*\n(.*?)(?:\n\n|\*\*|$)",
                        content,
                        re.DOTALL,
                    )
                    if dep_section:
                        dep_text = dep_section.group(1)
                        # Extract rec_XXX patterns
                        dependencies = re.findall(r"rec_\d{3}", dep_text)

                    statuses[rec_id] = {
                        "status": status,
                        "phase": phase_num,
                        "directory": str(subdir),
                        "priority": priority,
                        "estimated_time": estimated_time,
                        "risk": risk,
                        "dependencies": dependencies,
                        "has_status_file": True,
                    }

                except Exception as e:
                    statuses[rec_id] = {
                        "status": "ERROR",
                        "phase": phase_num,
                        "directory": str(subdir),
                        "error": str(e),
                        "has_status_file": True,
                    }

        return statuses

    def get_summary(self) -> Dict[str, int]:
        """
        Get summary counts of recommendations by status.

        Returns:
            Dictionary with status counts
        """
        if not self.statuses:
            self.statuses = self.scan_statuses()

        summary = {
            "total": len(self.statuses),
            "COMPLETE": 0,
            "IN_PROGRESS": 0,
            "BLOCKED": 0,
            "PLANNED": 0,
            "MISSING": 0,
            "UNKNOWN": 0,
            "ERROR": 0,
        }

        for rec_id, info in self.statuses.items():
            status = info.get("status", "UNKNOWN")
            if status in summary:
                summary[status] += 1
            else:
                summary["UNKNOWN"] += 1

        summary["remaining"] = summary["total"] - summary["COMPLETE"]

        return summary

    def get_next_available(self, count: int = 10) -> List[Tuple[str, Dict]]:
        """
        Get next available recommendations (dependencies met, not complete).

        Args:
            count: Maximum number to return

        Returns:
            List of (rec_id, info) tuples
        """
        if not self.statuses:
            self.statuses = self.scan_statuses()

        # Find completed recommendations
        completed = set(
            [
                rec_id
                for rec_id, info in self.statuses.items()
                if info.get("status") == "COMPLETE"
            ]
        )

        # Find available recommendations
        available = []

        for rec_id, info in self.statuses.items():
            status = info.get("status")

            # Skip if already complete, in progress, or blocked
            if status in ["COMPLETE", "IN_PROGRESS", "BLOCKED"]:
                continue

            # Check if dependencies are met
            dependencies = info.get("dependencies", [])
            if dependencies:
                unmet_deps = [dep for dep in dependencies if dep not in completed]
                if unmet_deps:
                    continue

            available.append((rec_id, info))

        # Sort by priority (CRITICAL first), then by rec_id
        def sort_key(item):
            rec_id, info = item
            priority = info.get("priority", "")

            # Priority score: CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3, Unknown=4
            if "CRITICAL" in priority or "⭐" in priority:
                priority_score = 0
            elif "HIGH" in priority or "🟡" in priority:
                priority_score = 1
            elif "MEDIUM" in priority:
                priority_score = 2
            elif "LOW" in priority:
                priority_score = 3
            else:
                priority_score = 4

            # Secondary sort by rec_id number
            rec_num = int(re.search(r"rec_(\d+)", rec_id).group(1))

            return (priority_score, rec_num)

        available.sort(key=sort_key)

        return available[:count]

    def get_blocked_recommendations(self) -> List[Tuple[str, Dict]]:
        """
        Get all blocked recommendations with their blocking dependencies.

        Returns:
            List of (rec_id, info) tuples
        """
        if not self.statuses:
            self.statuses = self.scan_statuses()

        blocked = []

        for rec_id, info in self.statuses.items():
            status = info.get("status")
            if status == "BLOCKED":
                blocked.append((rec_id, info))

        return blocked

    def generate_report(self, verbose: bool = False) -> str:
        """
        Generate a human-readable status report.

        Args:
            verbose: Include detailed information

        Returns:
            Formatted report string
        """
        if not self.statuses:
            self.statuses = self.scan_statuses()

        summary = self.get_summary()
        next_available = self.get_next_available(count=10)
        blocked = self.get_blocked_recommendations()

        report = []
        report.append("=" * 80)
        report.append("BOOK RECOMMENDATIONS STATUS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Recommendations: {summary['total']}")

        if summary["total"] > 0:
            complete_pct = summary["COMPLETE"] / summary["total"] * 100
        else:
            complete_pct = 0.0

        report.append(f"  ✅ Complete: {summary['COMPLETE']} ({complete_pct:.1f}%)")
        report.append(f"  🔄 In Progress: {summary['IN_PROGRESS']}")
        report.append(f"  ⚠️ Blocked: {summary['BLOCKED']}")
        report.append(f"  🔵 Planned: {summary['PLANNED']}")
        report.append(f"  ❓ Unknown: {summary['UNKNOWN']}")
        report.append(f"  ❌ Missing Status: {summary['MISSING']}")
        report.append(f"  ⚠️ Error: {summary['ERROR']}")
        report.append(f"  📋 Remaining: {summary['remaining']}")
        report.append("")

        # Next Available
        report.append("NEXT AVAILABLE (Top 10)")
        report.append("-" * 80)
        if next_available:
            for i, (rec_id, info) in enumerate(next_available, 1):
                priority = info.get("priority", "Unknown")
                estimated_time = info.get("estimated_time", "Unknown")
                risk = info.get("risk", "Unknown")
                phase = info.get("phase", "?")

                report.append(f"{i:2d}. {rec_id} (phase_{phase})")
                report.append(f"    Priority: {priority}")
                report.append(f"    Estimated Time: {estimated_time}")
                report.append(f"    Risk: {risk}")
                if verbose:
                    report.append(f"    Directory: {info['directory']}")
                report.append("")
        else:
            report.append("No recommendations available (all complete or blocked)")
            report.append("")

        # Blocked
        if blocked:
            report.append("BLOCKED RECOMMENDATIONS")
            report.append("-" * 80)
            for rec_id, info in blocked:
                dependencies = info.get("dependencies", [])
                report.append(f"{rec_id} (phase_{info.get('phase', '?')})")
                report.append(
                    f"  Dependencies: {', '.join(dependencies) if dependencies else 'Unknown'}"
                )
                if verbose:
                    report.append(f"  Directory: {info['directory']}")
                report.append("")

        # Verbose details
        if verbose:
            report.append("DETAILED STATUS BY PHASE")
            report.append("-" * 80)
            for phase_num in range(9):
                phase_recs = [
                    (rec_id, info)
                    for rec_id, info in self.statuses.items()
                    if info.get("phase") == phase_num
                ]
                if phase_recs:
                    report.append(
                        f"\nPhase {phase_num}: {len(phase_recs)} recommendations"
                    )
                    for rec_id, info in sorted(phase_recs):
                        status = info.get("status", "UNKNOWN")
                        report.append(f"  {rec_id}: {status}")

        report.append("=" * 80)

        return "\n".join(report)

    def update_progress_file(self, rec_id: str, status: str = "COMPLETE") -> bool:
        """
        Update the BOOK_RECOMMENDATIONS_PROGRESS.md file after completing a recommendation.

        Args:
            rec_id: Recommendation ID
            status: New status (default: COMPLETE)

        Returns:
            True if update successful
        """
        if not self.progress_file.exists():
            print(f"Warning: Progress file not found: {self.progress_file}")
            return False

        try:
            # Read current content
            with open(self.progress_file, "r") as f:
                content = f.read()

            # Update completion counts
            summary = self.get_summary()

            # Update the summary table
            # This is a simplified version - could be made more sophisticated
            content = re.sub(
                r"\| \*\*Completed\*\* \| \d+ \|",
                f"| **Completed** | {summary['COMPLETE']} |",
                content,
            )
            content = re.sub(
                r"\| \*\*In Progress\*\* \| \d+ \|",
                f"| **In Progress** | {summary['IN_PROGRESS']} |",
                content,
            )
            content = re.sub(
                r"\| \*\*Blocked\*\* \| \d+ \|",
                f"| **Blocked** | {summary['BLOCKED']} |",
                content,
            )
            content = re.sub(
                r"\| \*\*Remaining\*\* \| \d+ \|",
                f"| **Remaining** | {summary['remaining']} |",
                content,
            )

            # Update last updated timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = re.sub(
                r"\*\*Last Updated:\*\* .+", f"**Last Updated:** {timestamp}", content
            )

            # Write back
            with open(self.progress_file, "w") as f:
                f.write(content)

            print(f"Updated progress file: {self.progress_file}")
            return True

        except Exception as e:
            print(f"Error updating progress file: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check recommendation implementation status"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--workspace", "-w", help="Workspace root path (default: auto-detect)"
    )
    parser.add_argument(
        "--rec", help="Check status of specific recommendation (e.g., rec_001)"
    )
    parser.add_argument(
        "--next",
        "-n",
        action="store_true",
        help="Show only next available recommendations",
    )
    parser.add_argument(
        "--update", "-u", help="Update progress file after completing recommendation"
    )
    parser.add_argument(
        "--json", "-j", action="store_true", help="Output in JSON format"
    )

    args = parser.parse_args()

    # Initialize checker
    checker = RecommendationStatusChecker(workspace_root=args.workspace)

    # Handle update command
    if args.update:
        success = checker.update_progress_file(args.update)
        return 0 if success else 1

    # Scan statuses
    checker.scan_statuses()

    # Handle specific commands
    if args.rec:
        # Check specific recommendation
        if args.rec in checker.statuses:
            info = checker.statuses[args.rec]
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print(f"Recommendation: {args.rec}")
                print(f"Status: {info.get('status', 'UNKNOWN')}")
                print(f"Phase: phase_{info.get('phase', '?')}")
                print(f"Priority: {info.get('priority', 'Unknown')}")
                print(f"Estimated Time: {info.get('estimated_time', 'Unknown')}")
                print(f"Risk: {info.get('risk', 'Unknown')}")
                print(
                    f"Dependencies: {', '.join(info.get('dependencies', [])) or 'None'}"
                )
                print(f"Directory: {info['directory']}")
        else:
            print(f"Recommendation {args.rec} not found.")
            return 1

    elif args.next:
        # Show only next available
        next_available = checker.get_next_available(count=10)
        if args.json:
            output = [{"rec_id": rec_id, **info} for rec_id, info in next_available]
            print(json.dumps(output, indent=2))
        else:
            print("Next Available Recommendations:")
            print("-" * 80)
            for i, (rec_id, info) in enumerate(next_available, 1):
                print(f"{i:2d}. {rec_id} (phase_{info.get('phase', '?')})")
                print(f"    Priority: {info.get('priority', 'Unknown')}")
                print(f"    Estimated Time: {info.get('estimated_time', 'Unknown')}")
                print("")

    else:
        # Generate full report
        if args.json:
            output = {
                "summary": checker.get_summary(),
                "statuses": checker.statuses,
                "next_available": [
                    {"rec_id": rec_id, **info}
                    for rec_id, info in checker.get_next_available(count=10)
                ],
                "blocked": [
                    {"rec_id": rec_id, **info}
                    for rec_id, info in checker.get_blocked_recommendations()
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(checker.generate_report(verbose=args.verbose))

    return 0


if __name__ == "__main__":
    exit(main())
