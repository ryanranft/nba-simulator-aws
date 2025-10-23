#!/usr/bin/env python3
"""
Phase README Alignment Tool

This script implements Workflow #57 (Phase-README Alignment) to ensure phase READMEs
align with the main README vision. It checks 6 key areas and can automatically fix
common issues.

6-Point Validation Checklist:
1. Temporal precision alignment
2. Data tracking (use DIMS, not static numbers)
3. Project vision alignment
4. Methodology references
5. Cost & resource alignment
6. Cross-references work

Usage:
    python scripts/automation/align_phase_readme.py --phase 0
    python scripts/automation/align_phase_readme.py --phase 0 --check-only
    python scripts/automation/align_phase_readme.py --all
    python scripts/automation/align_phase_readme.py --phase 0 --fix

Author: Claude Code
Created: October 23, 2025
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple


class PhaseReadmeAligner:
    """Align phase README with main README vision."""

    def __init__(self, project_root: Path = None):
        """Initialize aligner."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.main_readme = self.project_root / "README.md"
        self.phases_dir = self.project_root / "docs" / "phases"

        # Load main README vision
        self.main_readme_content = (
            self.main_readme.read_text() if self.main_readme.exists() else ""
        )

        # Track issues found
        self.issues = []

    def check_phase(
        self, phase_num: int, check_only: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Check (and optionally fix) phase README alignment.

        Args:
            phase_num: Phase number (0-9)
            check_only: If True, only check (don't modify). If False, attempt to fix issues.

        Returns:
            Tuple of (all_checks_passed, issues_list)
        """
        self.issues = []

        # Find phase README
        if phase_num == 0:
            # Phase 0 is in subdirectory
            phase_readme = self.phases_dir / "phase_0" / "PHASE_0_INDEX.md"
        else:
            # Phases 1-9 are directly in docs/phases/
            phase_readme = self.phases_dir / f"PHASE_{phase_num}_INDEX.md"

        if not phase_readme.exists():
            self.issues.append(
                f"❌ Phase {phase_num} README not found at {phase_readme}"
            )
            return False, self.issues

        phase_content = phase_readme.read_text()

        # Run 6-point validation checklist
        self._check_temporal_precision(phase_content, phase_num)
        self._check_data_tracking(phase_content, phase_num)
        self._check_vision_alignment(phase_content, phase_num)
        self._check_methodology_references(phase_content, phase_num)
        self._check_cost_alignment(phase_content, phase_num)
        self._check_cross_references(phase_content, phase_readme, phase_num)

        all_passed = all(not issue.startswith("❌") for issue in self.issues)

        # If not check-only and issues found, attempt fixes
        if not check_only and not all_passed:
            fixed_content = self._apply_fixes(phase_content, phase_num)
            if fixed_content != phase_content:
                phase_readme.write_text(fixed_content)
                self.issues.append(
                    f"✅ Applied automatic fixes to Phase {phase_num} README"
                )

        return all_passed, self.issues

    def _check_temporal_precision(self, content: str, phase_num: int):
        """Check #1: Temporal precision alignment."""

        # Check for outdated temporal precision statements
        outdated_patterns = [
            (
                r"2020-2025.*millisecond",
                "States '2020-2025: millisecond' when precision available for entire play-by-play era (~1996-present)",
            ),
            (
                r"minute-level precision",
                "Claims 'minute-level precision' when wall clock + game clock enables millisecond precision",
            ),
            (
                r"game-level aggregates",
                "States 'game-level aggregates' without mentioning simulation-based reconstruction for pre-PBP era",
            ),
        ]

        for pattern, issue_desc in outdated_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.issues.append(f"❌ Temporal Precision: {issue_desc}")

        # Check for correct temporal precision statements
        correct_patterns = [
            r"play-by-play.*millisecond",
            r"simulation-based.*reconstruction",
            r"econometric.*nonparametric",
        ]

        has_correct = any(
            re.search(p, content, re.IGNORECASE) for p in correct_patterns
        )
        if not has_correct:
            self.issues.append(
                f"⚠️  Temporal Precision: Missing correct temporal precision description"
            )

    def _check_data_tracking(self, content: str, phase_num: int):
        """Check #2: Data tracking (use DIMS, not static numbers)."""

        # Check for static number tables
        static_table_pattern = r"\|\s*Current\s*Total\s*\|.*\d+\s*\|.*\d+.*\|"
        if re.search(static_table_pattern, content, re.IGNORECASE):
            self.issues.append(
                f"❌ Data Tracking: Found static number table (should use DIMS commands)"
            )

        # Check for DIMS integration
        dims_patterns = [r"dims_cli\.py", r"inventory/metrics\.yaml", r"Workflow #56"]

        has_dims = any(re.search(p, content, re.IGNORECASE) for p in dims_patterns)
        if not has_dims:
            self.issues.append(f"❌ Data Tracking: Missing DIMS integration")
        else:
            self.issues.append(f"✅ Data Tracking: DIMS integration present")

    def _check_vision_alignment(self, content: str, phase_num: int):
        """Check #3: Project vision alignment."""

        # Check for "How This Phase Enables Vision" section
        vision_section_pattern = r"##.*How.*Phase.*Enables.*Vision"
        has_vision_section = re.search(vision_section_pattern, content, re.IGNORECASE)

        if not has_vision_section:
            self.issues.append(
                f"❌ Vision Alignment: Missing 'How This Phase Enables Vision' section"
            )
        else:
            self.issues.append(
                f"✅ Vision Alignment: 'How This Phase Enables Vision' section present"
            )

        # Check for references to main README
        main_readme_refs = [
            r"\[main README\]",
            r"README\.md",
            r"simulation methodology",
        ]

        has_main_readme_ref = any(
            re.search(p, content, re.IGNORECASE) for p in main_readme_refs
        )
        if not has_main_readme_ref:
            self.issues.append(
                f"⚠️  Vision Alignment: Missing references to main README"
            )

    def _check_methodology_references(self, content: str, phase_num: int):
        """Check #4: Methodology references."""

        # Check for specific terminology
        correct_terms = {
            "econometric": r"econometric",
            "nonparametric": r"nonparametric",
            "panel data": r"panel\s+data",
            "causal inference": r"causal\s+inference",
        }

        has_correct_terms = {
            term: bool(re.search(pattern, content, re.IGNORECASE))
            for term, pattern in correct_terms.items()
        }

        missing_terms = [
            term for term, present in has_correct_terms.items() if not present
        ]

        if missing_terms:
            self.issues.append(
                f"⚠️  Methodology: Missing terminology: {', '.join(missing_terms)}"
            )

        # Check for generic terms that should be more specific
        generic_patterns = [
            (
                r"\bML\b",
                "Uses 'ML' (should be more specific: panel data regression, etc.)",
            ),
            (
                r"\bAI\b",
                "Uses 'AI' (should be more specific: econometric causal inference, etc.)",
            ),
        ]

        for pattern, issue in generic_patterns:
            if re.search(pattern, content):
                self.issues.append(f"⚠️  Methodology: {issue}")

    def _check_cost_alignment(self, content: str, phase_num: int):
        """Check #5: Cost & resource alignment."""

        # Check for cost mentions
        cost_pattern = r"\$\s*\d+.*month"
        has_cost_info = bool(re.search(cost_pattern, content))

        # Check main README for phase-specific cost info
        main_cost_pattern = rf"Phase\s+{phase_num}.*\$\s*\d+"
        main_has_cost = bool(re.search(main_cost_pattern, self.main_readme_content))

        if main_has_cost and not has_cost_info:
            self.issues.append(
                f"⚠️  Cost Alignment: Main README mentions cost for Phase {phase_num}, but phase README doesn't"
            )

        # Check for AWS resource names consistency
        aws_resources = {"S3": r"nba-sim-raw-data-lake", "RDS": r"rds.*database"}

        for resource, pattern in aws_resources.items():
            if re.search(pattern, content, re.IGNORECASE):
                # Check if same resource name in main README
                if not re.search(pattern, self.main_readme_content, re.IGNORECASE):
                    self.issues.append(
                        f"⚠️  Cost Alignment: Phase README mentions {resource} not in main README"
                    )

    def _check_cross_references(self, content: str, readme_path: Path, phase_num: int):
        """Check #6: Cross-references work."""

        # Extract all markdown links
        link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        links = re.findall(link_pattern, content)

        broken_links = []

        for link_text, link_target in links:
            # Skip external links (http/https)
            if link_target.startswith("http"):
                continue

            # Skip anchors within same document
            if link_target.startswith("#"):
                continue

            # Resolve relative path
            # readme_path is the path to the phase README
            # link_target is relative to that README
            readme_dir = readme_path.parent
            target_path = (readme_dir / link_target).resolve()

            if not target_path.exists():
                broken_links.append(f"{link_text} -> {link_target}")

        if broken_links:
            self.issues.append(
                f"❌ Cross-References: {len(broken_links)} broken links found:"
            )
            for link in broken_links[:5]:  # Show first 5
                self.issues.append(f"    - {link}")
        else:
            self.issues.append(f"✅ Cross-References: All links working")

    def _apply_fixes(self, content: str, phase_num: int) -> str:
        """Apply automatic fixes to phase README."""

        fixed_content = content

        # Fix #1: Add DIMS integration if missing
        if "dims_cli.py" not in content:
            # Find data section or create one
            dims_snippet = """
**Get current S3 metrics (always up-to-date):**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**See also:** [Workflow #56: DIMS Management](../../claude_workflows/workflow_descriptions/56_dims_management.md), `inventory/metrics.yaml`
"""
            # Try to insert after ## Data or ## Overview section
            data_section_pattern = r"(##\s+Data.*?\n)"
            if re.search(data_section_pattern, content, re.IGNORECASE | re.DOTALL):
                fixed_content = re.sub(
                    data_section_pattern,
                    r"\1\n" + dims_snippet + "\n",
                    fixed_content,
                    count=1,
                    flags=re.IGNORECASE,
                )

        # Fix #2: Add "How This Phase Enables Vision" section if missing
        if not re.search(r"##.*How.*Phase.*Enables.*Vision", content, re.IGNORECASE):
            vision_snippet = f"""
## How Phase {phase_num} Enables the Simulation Vision

This phase provides [data/infrastructure/capability] that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference
From this phase's outputs, we can:
- [Specific econometric technique enabled]
- [Example: PPP estimation using panel data regression]

### 2. Nonparametric Event Modeling
From this phase's data, we build:
- [Specific nonparametric technique enabled]
- [Example: Kernel density estimation for technical fouls]

### 3. Context-Adaptive Simulations
Using this phase's data, simulations can adapt to:
- [Game situation context]
- [Player/team specific factors]

**See [main README](../../README.md) for complete methodology.**
"""
            # Insert before ## Related Documentation or at end
            if "## Related Documentation" in fixed_content:
                fixed_content = fixed_content.replace(
                    "## Related Documentation",
                    vision_snippet + "\n## Related Documentation",
                )
            else:
                fixed_content += "\n" + vision_snippet

        # Fix #3: Replace static tables with DIMS reference
        static_table_pattern = r"\|.*Current\s*Total.*\|.*\n\|.*\n\|.*\|"
        if re.search(static_table_pattern, fixed_content, re.IGNORECASE):
            dims_replacement = """
**Get current metrics (always up-to-date):**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**Historical milestones:**
- [Date]: [Metric] (baseline)

**See:** `inventory/metrics.yaml`
"""
            fixed_content = re.sub(
                static_table_pattern,
                dims_replacement,
                fixed_content,
                count=1,
                flags=re.IGNORECASE,
            )

        return fixed_content

    def print_report(self, phase_num: int, all_passed: bool):
        """Print alignment report."""
        print(f"\n{'='*70}")
        print(f"Phase {phase_num} README Alignment Report")
        print(f"{'='*70}\n")

        if all_passed:
            print("✅ All checks passed! Phase README is aligned with main README.\n")
        else:
            print("❌ Some issues found. See details below:\n")

        for issue in self.issues:
            print(f"  {issue}")

        print(f"\n{'='*70}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Align phase README with main README vision"
    )
    parser.add_argument("--phase", type=int, help="Phase number to check (0-9)")
    parser.add_argument("--all", action="store_true", help="Check all phases")
    parser.add_argument(
        "--check-only", action="store_true", help="Only check, do not fix"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )
    args = parser.parse_args()

    aligner = PhaseReadmeAligner()

    # Default to check-only unless --fix specified
    check_only = not args.fix

    if args.all:
        # Check all phases
        print("\n" + "=" * 70)
        print("Checking all phases...")
        print("=" * 70)

        results = {}
        for phase_num in range(10):
            all_passed, issues = aligner.check_phase(phase_num, check_only=check_only)
            results[phase_num] = (all_passed, issues)

        # Summary
        print("\n" + "=" * 70)
        print("Summary - All Phases")
        print("=" * 70 + "\n")

        for phase_num, (all_passed, issues) in results.items():
            status = "✅ PASS" if all_passed else "❌ ISSUES"
            print(f"Phase {phase_num}: {status} ({len(issues)} checks)")

        print()

    elif args.phase is not None:
        # Check specific phase
        all_passed, issues = aligner.check_phase(args.phase, check_only=check_only)
        aligner.print_report(args.phase, all_passed)

        if not check_only and not all_passed:
            print("✅ Attempted automatic fixes. Re-run with --check-only to verify.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
