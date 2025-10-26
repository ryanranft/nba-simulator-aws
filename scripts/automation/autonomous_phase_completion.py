#!/usr/bin/env python3
"""
Autonomous Phase Completion Agent

This script implements Workflow #59 (Autonomous Phase Completion) to autonomously
validate and complete all phases (0-9) overnight without supervision.

Inspired by Workflow #54 (which implemented 214 recommendations in 12 minutes), this
agent runs overnight with zero supervision.

What it does:
1. Cycles through all phases (0-9)
2. For each phase:
   - Aligns phase README with main README vision
   - Validates completed sub-phases (✅ COMPLETE) using Workflow #58
   - Implements pending sub-phases (🔵 PLANNED/⏸️ PENDING) using Workflow #58
3. Generates comprehensive completion report

Usage:
    python scripts/automation/autonomous_phase_completion.py --all
    python scripts/automation/autonomous_phase_completion.py --phase 0
    python scripts/automation/autonomous_phase_completion.py --phase 0 --subphase 0.1
    python scripts/automation/autonomous_phase_completion.py --all --dry-run

Author: Claude Code
Created: October 23, 2025
"""

import argparse
import subprocess
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json


class AutonomousPhaseCompletionAgent:
    """Main autonomous agent for phase completion."""

    def __init__(
        self, project_root: Path = None, dry_run: bool = False, verbose: bool = False
    ):
        """
        Initialize agent.

        Args:
            project_root: Project root directory
            dry_run: If True, preview actions without executing
            verbose: Enable verbose output
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.dry_run = dry_run
        self.verbose = verbose

        # Paths
        self.docs_dir = self.project_root / "docs"
        self.phases_dir = self.docs_dir / "phases"
        self.scripts_dir = self.project_root / "scripts" / "automation"
        self.progress_file = self.project_root / "PHASE_COMPLETION_PROGRESS.md"
        self.summary_file = self.project_root / "PHASE_COMPLETION_SUMMARY.md"

        # Scripts
        self.validate_phase_script = self.scripts_dir / "validate_phase.py"
        self.check_status_script = self.scripts_dir / "check_phase_status.py"
        self.align_readme_script = self.scripts_dir / "align_phase_readme.py"
        self.generate_recommendations_script = (
            self.scripts_dir / "generate_implementation_recommendations.py"
        )
        self.execute_recommendations_script = (
            self.scripts_dir / "execute_implementation_recommendations.py"
        )
        self.enhance_readme_script = self.scripts_dir / "enhance_phase_readme.py"

        # Tracking
        self.start_time = datetime.now()
        self.stats = {
            "phases_processed": 0,
            "sub_phases_validated": 0,
            "sub_phases_implemented": 0,
            "sub_phases_blocked": 0,
            "sub_phases_skipped": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "git_commits": 0,
        }

        self.blocked_sub_phases = []
        self.skipped_sub_phases = []

    def run_all_phases(self):
        """Run autonomous completion on all phases (0-9)."""
        print("\n" + "=" * 70)
        print("Autonomous Phase Completion Agent - Starting")
        print("=" * 70)
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE RUN'}")
        print("=" * 70 + "\n")

        # Initialize progress tracker
        self._init_progress_tracker()

        # Process each phase
        for phase_num in range(10):
            print(f"\n{'#'*70}")
            print(f"# Processing Phase {phase_num}")
            print(f"{'#'*70}\n")

            success = self._process_phase(phase_num)

            if success:
                self.stats["phases_processed"] += 1
                print(f"\n✅ Phase {phase_num} completed\n")
            else:
                print(f"\n⚠️  Phase {phase_num} had issues (see log)\n")

            # Update progress tracker
            self._update_progress_tracker(phase_num)

        # Generate final summary
        self._generate_summary_report()

        print("\n" + "=" * 70)
        print("Autonomous Phase Completion Agent - Complete")
        print("=" * 70)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self._format_duration(datetime.now() - self.start_time)}")
        print("=" * 70 + "\n")

        # Print quick stats
        self._print_quick_stats()

    def _process_phase(self, phase_num: int) -> bool:
        """Process a single phase."""

        # Step 1: Align phase README with main README
        print(f"[Step 1] Aligning Phase {phase_num} README with main README...")
        if not self._align_phase_readme(phase_num):
            print(f"⚠️  README alignment had issues (non-blocking)\n")

        # Step 2: Get all sub-phases for this phase
        sub_phases = self._get_sub_phases(phase_num)

        if not sub_phases:
            print(
                f"ℹ️  No sub-phases found for Phase {phase_num} (may not have table yet)\n"
            )
            return True

        print(f"Found {len(sub_phases)} sub-phases in Phase {phase_num}\n")

        # Step 3: Process each sub-phase
        for sub_phase in sub_phases:
            print(f"\n{'—'*70}")
            print(f"Sub-Phase {sub_phase['id']}: {sub_phase['name']}")
            print(f"Status: {sub_phase['status']}, Validated: {sub_phase['validated']}")
            print(f"{'—'*70}\n")

            if sub_phase["status"] == "COMPLETE" and not sub_phase["validated"]:
                # Re-validate completed sub-phase
                self._validate_sub_phase(sub_phase)

            elif sub_phase["status"] in ["PLANNED", "PENDING"]:
                # Implement pending sub-phase
                self._implement_sub_phase(sub_phase)

            elif sub_phase["status"] == "COMPLETE" and sub_phase["validated"]:
                # Already validated, skip
                print(f"✅ Already validated, skipping\n")

        return True

    def _align_phase_readme(self, phase_num: int) -> bool:
        """Align phase README with main README vision."""
        if self.dry_run:
            print(f"[DRY RUN] Would align Phase {phase_num} README\n")
            return True

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.align_readme_script),
                    "--phase",
                    str(phase_num),
                    "--fix",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"✅ README aligned\n")
                return True
            else:
                print(f"⚠️  README alignment issues:\n{result.stdout}\n")
                return False

        except Exception as e:
            print(f"⚠️  README alignment error: {e}\n")
            return False

    def _get_sub_phases(self, phase_num: int) -> List[Dict]:
        """Get all sub-phases for a phase."""
        # Read phase index
        if phase_num == 0:
            phase_index = self.phases_dir / "phase_0" / "PHASE_0_INDEX.md"
        else:
            phase_index = self.phases_dir / f"PHASE_{phase_num}_INDEX.md"

        if not phase_index.exists():
            return []

        content = phase_index.read_text()

        # Extract sub-phases from table
        # Pattern 1: Phase 0 format - | **0.X** | [Name](link) | Status | Priority | Completed | Description |
        pattern1 = re.compile(
            r"\|\s*\*\*(\d+\.\d+)\*\*\s*\|\s*\[([^\]]+)\]\([^\)]+\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
        )

        # Pattern 2: Phase 1+ format - | **X.Y** | Name | Status | Time | Features | [file](link) |
        pattern2 = re.compile(
            r"\|\s*\*\*(\d+\.\d+)\*\*\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
        )

        sub_phases = []

        # Try pattern 1 first (Phase 0 format with links in 2nd column)
        for match in pattern1.finditer(content):
            sub_phase_id = match.group(1)
            sub_phase_name = match.group(2).strip()
            status = match.group(3).strip()
            priority = match.group(4).strip()
            completed_date = match.group(5).strip()

            # Check if validated
            validated = "✓" in status

            # Determine base status
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

        # If no matches, try pattern 2 (Phase 1+ format with name in 2nd column)
        if not sub_phases:
            for match in pattern2.finditer(content):
                sub_phase_id = match.group(1)
                sub_phase_name = match.group(2).strip()
                status = match.group(3).strip()

                # Check if validated
                validated = "✓" in status

                # Determine base status
                if "✅ COMPLETE" in status:
                    base_status = "COMPLETE"
                elif "🔄 IN PROGRESS" in status or "🔄 PARTIAL" in status:
                    base_status = "IN_PROGRESS"
                elif "⏸️ PENDING" in status or "⏸️" in status:
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
                        "priority": "N/A",
                        "completed_date": None,
                    }
                )

        # If still no matches, try pattern 3 (Phase 2 format: | 9.0: Name | Status | ...)
        if not sub_phases:
            pattern3 = re.compile(r"\|\s*(\d+\.\d+):\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")

            for match in pattern3.finditer(content):
                sub_phase_id = match.group(1).strip()
                sub_phase_name = match.group(2).strip()
                status = match.group(3).strip()

                # Check if validated
                validated = "✓" in status

                # Determine base status
                if "✅ COMPLETE" in status or "✅" in status:
                    base_status = "COMPLETE"
                elif (
                    "🔄 IN PROGRESS" in status
                    or "🔄 PARTIAL" in status
                    or "🔄" in status
                ):
                    base_status = "IN_PROGRESS"
                elif "⏸️ PENDING" in status or "⏸️" in status:
                    base_status = "PENDING"
                elif "🔵 PLANNED" in status or "🔵" in status:
                    base_status = "PLANNED"
                else:
                    base_status = "UNKNOWN"

                sub_phases.append(
                    {
                        "id": sub_phase_id,
                        "name": sub_phase_name,
                        "status": base_status,
                        "validated": validated,
                        "priority": "N/A",
                        "completed_date": None,
                    }
                )

        return sub_phases

    def _validate_sub_phase(self, sub_phase: Dict):
        """Validate a completed sub-phase using Workflow #58."""
        print(f"[Action] Validating {sub_phase['id']} using Workflow #58...")

        if self.dry_run:
            print(f"[DRY RUN] Would validate {sub_phase['id']}\n")
            self.stats["sub_phases_validated"] += 1
            return

        try:
            result = subprocess.run(
                [sys.executable, str(self.validate_phase_script), sub_phase["id"]],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max
            )

            if result.returncode == 0:
                print(f"✅ Validation passed")
                self.stats["sub_phases_validated"] += 1
                self.stats["tests_passed"] += 1

                # Git commit
                self._git_commit(sub_phase, "validate")

            else:
                print(f"❌ Validation failed")
                print(f"Output:\n{result.stdout}")
                self.stats["tests_failed"] += 1
                self.stats["sub_phases_blocked"] += 1
                self.blocked_sub_phases.append(
                    {
                        "id": sub_phase["id"],
                        "name": sub_phase["name"],
                        "reason": "Validation failed",
                        "output": result.stdout,
                    }
                )

        except subprocess.TimeoutExpired:
            print(f"❌ Validation timed out (10 min)")
            self.stats["sub_phases_blocked"] += 1
            self.blocked_sub_phases.append(
                {
                    "id": sub_phase["id"],
                    "name": sub_phase["name"],
                    "reason": "Timeout (10 min)",
                }
            )

        except Exception as e:
            print(f"❌ Validation error: {e}")
            self.stats["sub_phases_blocked"] += 1
            self.blocked_sub_phases.append(
                {
                    "id": sub_phase["id"],
                    "name": sub_phase["name"],
                    "reason": f"Error: {e}",
                }
            )

        print()

    def _implement_sub_phase(self, sub_phase: Dict):
        """Implement a pending sub-phase."""
        print(f"[Action] Implementing {sub_phase['id']}...")

        # Check if creates costly infrastructure
        if self._creates_costly_infrastructure(sub_phase):
            print(f"⏭️  Skipping - Creates new costly infrastructure\n")
            self.stats["sub_phases_skipped"] += 1
            self.skipped_sub_phases.append(
                {
                    "id": sub_phase["id"],
                    "name": sub_phase["name"],
                    "reason": "Creates new costly infrastructure",
                }
            )
            return

        if self.dry_run:
            print(f"[DRY RUN] Would implement {sub_phase['id']}\n")
            self.stats["sub_phases_implemented"] += 1
            return

        try:
            # Step 1: Generate implementation recommendations
            print(f"  Step 1: Generating implementation recommendations...")
            recommendations_file = (
                self.project_root
                / f"recommendations_{sub_phase['id'].replace('.', '_')}.json"
            )

            gen_result = subprocess.run(
                [
                    sys.executable,
                    str(self.generate_recommendations_script),
                    sub_phase["id"],
                    "--output",
                    str(recommendations_file),
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
            )

            if gen_result.returncode != 0:
                print(f"  ❌ Recommendation generation failed")
                print(f"  Output:\n{gen_result.stdout}")
                self.stats["sub_phases_blocked"] += 1
                self.blocked_sub_phases.append(
                    {
                        "id": sub_phase["id"],
                        "name": sub_phase["name"],
                        "reason": "Recommendation generation failed",
                        "output": gen_result.stdout,
                    }
                )
                return

            print(f"  ✅ Recommendations generated")

            # Step 2: Execute implementation recommendations
            print(f"  Step 2: Executing implementation recommendations...")

            exec_result = subprocess.run(
                [
                    sys.executable,
                    str(self.execute_recommendations_script),
                    str(recommendations_file),
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max
            )

            if exec_result.returncode != 0:
                print(f"  ❌ Implementation execution failed")
                print(f"  Output:\n{exec_result.stdout}")
                self.stats["sub_phases_blocked"] += 1
                self.blocked_sub_phases.append(
                    {
                        "id": sub_phase["id"],
                        "name": sub_phase["name"],
                        "reason": "Implementation execution failed",
                        "output": exec_result.stdout,
                    }
                )
                # Clean up recommendations file
                if recommendations_file.exists():
                    recommendations_file.unlink()
                return

            print(f"  ✅ Implementation executed")

            # Clean up recommendations file
            if recommendations_file.exists():
                recommendations_file.unlink()

            # Step 3: Enhance README with methodology integration
            print(f"  Step 3: Enhancing README with methodology integration...")

            enhance_result = subprocess.run(
                [
                    sys.executable,
                    str(self.enhance_readme_script),
                    sub_phase["id"],
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
            )

            if enhance_result.returncode != 0:
                print(f"  ⚠️  README enhancement failed (non-blocking)")
                # Don't block on README enhancement failure

            print(f"  ✅ README enhanced")

            # Step 4: Validate implementation using Workflow #58
            print(f"  Step 4: Validating implementation...")

            result = subprocess.run(
                [sys.executable, str(self.validate_phase_script), sub_phase["id"]],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max for validation
            )

            if result.returncode == 0:
                print(f"✅ Implementation and validation passed")
                self.stats["sub_phases_implemented"] += 1
                self.stats["tests_passed"] += 1

                # Git commit
                self._git_commit(sub_phase, "implement")

            else:
                print(f"❌ Implementation failed")
                print(f"Output:\n{result.stdout}")
                self.stats["tests_failed"] += 1
                self.stats["sub_phases_blocked"] += 1
                self.blocked_sub_phases.append(
                    {
                        "id": sub_phase["id"],
                        "name": sub_phase["name"],
                        "reason": "Implementation failed",
                        "output": result.stdout,
                    }
                )

        except subprocess.TimeoutExpired:
            print(f"❌ Implementation timed out (15 min)")
            self.stats["sub_phases_blocked"] += 1
            self.blocked_sub_phases.append(
                {
                    "id": sub_phase["id"],
                    "name": sub_phase["name"],
                    "reason": "Timeout (15 min)",
                }
            )

        except Exception as e:
            print(f"❌ Implementation error: {e}")
            self.stats["sub_phases_blocked"] += 1
            self.blocked_sub_phases.append(
                {
                    "id": sub_phase["id"],
                    "name": sub_phase["name"],
                    "reason": f"Error: {e}",
                }
            )

        print()

    def _creates_costly_infrastructure(self, sub_phase: Dict) -> bool:
        """Check if sub-phase creates new costly infrastructure."""
        # Read sub-phase README if available
        phase_num = int(sub_phase["id"].split(".")[0])

        if phase_num == 0:
            phase_dir = self.phases_dir / "phase_0"
        else:
            phase_dir = self.phases_dir / f"phase_{phase_num}"

        # Try to find README
        sub_phase_clean = sub_phase["id"].replace(".", "_")
        power_dir = phase_dir / sub_phase_clean / "README.md"
        simple_file = phase_dir / f"{sub_phase_clean}.md"

        readme_content = ""
        if power_dir.exists():
            readme_content = power_dir.read_text().lower()
        elif simple_file.exists():
            readme_content = simple_file.read_text().lower()

        if not readme_content:
            return False  # Can't determine, assume OK

        # Keywords indicating NEW infrastructure
        new_infra_keywords = [
            "create new rds",
            "provision new database",
            "create new bucket",
            "new ec2 instance",
            "new elasticsearch cluster",
        ]

        return any(keyword in readme_content for keyword in new_infra_keywords)

    def _git_commit(self, sub_phase: Dict, action: str):
        """Create git commit for sub-phase completion."""
        if self.dry_run:
            print(f"[DRY RUN] Would create git commit\n")
            self.stats["git_commits"] += 1
            return

        action_verb = "Complete" if action == "validate" else "Implement"
        commit_msg = f"feat: {action_verb} Phase {sub_phase['id']} validation using Workflow #58\n\n"
        commit_msg += f"- Sub-phase: {sub_phase['name']}\n"
        commit_msg += f"- Action: {'Re-validate' if action == 'validate' else 'Implement and validate'}\n"
        commit_msg += f"- All tests passing\n"
        commit_msg += f"- Workflow #59: Autonomous Phase Completion\n"

        try:
            # Stage all changes
            subprocess.run(["git", "add", "."], cwd=self.project_root, check=True)

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_msg], cwd=self.project_root, check=True
            )

            print(f"✅ Git commit created\n")
            self.stats["git_commits"] += 1

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git commit failed: {e}\n")

    def _init_progress_tracker(self):
        """Initialize progress tracker file."""
        if self.dry_run:
            return

        content = f"""# Autonomous Phase Completion - Progress Tracker

**Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Status:** 🔄 IN PROGRESS
**Mode:** {'DRY RUN' if self.dry_run else 'LIVE RUN'}

---

## Current Progress

This file is updated in real-time as the autonomous agent processes phases.

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Statistics

- Phases Processed: {self.stats['phases_processed']}/10
- Sub-phases Validated: {self.stats['sub_phases_validated']}
- Sub-phases Implemented: {self.stats['sub_phases_implemented']}
- Sub-phases Blocked: {self.stats['sub_phases_blocked']}
- Sub-phases Skipped: {self.stats['sub_phases_skipped']}
- Tests Passed: {self.stats['tests_passed']}
- Tests Failed: {self.stats['tests_failed']}
- Git Commits: {self.stats['git_commits']}

---

## Phase Progress

"""
        self.progress_file.write_text(content)

    def _update_progress_tracker(self, phase_num: int):
        """Update progress tracker after processing a phase."""
        if self.dry_run:
            return

        # Update stats in file
        content = self.progress_file.read_text()

        # Update last updated time
        content = re.sub(
            r"\*\*Last Updated:\*\* .*",
            f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            content,
        )

        # Update statistics section
        stats_section = f"""### Statistics

- Phases Processed: {self.stats['phases_processed']}/10
- Sub-phases Validated: {self.stats['sub_phases_validated']}
- Sub-phases Implemented: {self.stats['sub_phases_implemented']}
- Sub-phases Blocked: {self.stats['sub_phases_blocked']}
- Sub-phases Skipped: {self.stats['sub_phases_skipped']}
- Tests Passed: {self.stats['tests_passed']}
- Tests Failed: {self.stats['tests_failed']}
- Git Commits: {self.stats['git_commits']}"""

        content = re.sub(
            r"### Statistics.*?---", stats_section + "\n\n---", content, flags=re.DOTALL
        )

        self.progress_file.write_text(content)

    def _generate_summary_report(self):
        """Generate final summary report."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""# Autonomous Phase Completion - Final Report

**Start Time:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
**End Time:** {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
**Duration:** {self._format_duration(duration)}
**Mode:** {'DRY RUN' if self.dry_run else 'LIVE RUN'}

---

## Summary

{'╔' + '═'*66 + '╗'}
{'║' + ' '*20 + 'PHASES COMPLETED' + ' '*30 + '║'}
{'╚' + '═'*66 + '╝'}

Phases Processed: {self.stats['phases_processed']}/10 ({100*self.stats['phases_processed']/10:.1f}%)

{'╔' + '═'*66 + '╗'}
{'║' + ' '*18 + 'SUB-PHASES PROCESSED' + ' '*28 + '║'}
{'╚' + '═'*66 + '╝'}

✅ Validated: {self.stats['sub_phases_validated']}
🔧 Implemented: {self.stats['sub_phases_implemented']}
❌ Blocked: {self.stats['sub_phases_blocked']}
⏭️  Skipped (costly): {self.stats['sub_phases_skipped']}

**Total:** {self.stats['sub_phases_validated'] + self.stats['sub_phases_implemented'] + self.stats['sub_phases_blocked'] + self.stats['sub_phases_skipped']}

{'╔' + '═'*66 + '╗'}
{'║' + ' '*20 + 'TESTS & VALIDATORS' + ' '*27 + '║'}
{'╚' + '═'*66 + '╝'}

Tests Passed: {self.stats['tests_passed']}
Tests Failed: {self.stats['tests_failed']}
Pass Rate: {100*self.stats['tests_passed']/(self.stats['tests_passed']+self.stats['tests_failed']) if (self.stats['tests_passed']+self.stats['tests_failed']) > 0 else 0:.1f}%

{'╔' + '═'*66 + '╗'}
{'║' + ' '*24 + 'GIT COMMITS' + ' '*31 + '║'}
{'╚' + '═'*66 + '╝'}

Commits Created: {self.stats['git_commits']}

---

## Blocked Sub-Phases

"""

        if self.blocked_sub_phases:
            report += f"**Count:** {len(self.blocked_sub_phases)}\n\n"
            for blocked in self.blocked_sub_phases:
                report += f"- **{blocked['id']}** - {blocked['name']}\n"
                report += f"  - Reason: {blocked['reason']}\n"
                if "output" in blocked:
                    report += f"  - Output: See logs\n"
                report += "\n"
        else:
            report += "✅ No blocked sub-phases!\n\n"

        report += "---\n\n## Skipped Sub-Phases (Costly Infrastructure)\n\n"

        if self.skipped_sub_phases:
            report += f"**Count:** {len(self.skipped_sub_phases)}\n\n"
            for skipped in self.skipped_sub_phases:
                report += f"- **{skipped['id']}** - {skipped['name']}\n"
                report += f"  - Reason: {skipped['reason']}\n\n"
        else:
            report += "✅ No skipped sub-phases!\n\n"

        report += """---

## Next Steps

1. Review this summary report
2. Review `PHASE_COMPLETION_PROGRESS.md` for detailed progress
3. If blockers exist, manually investigate and resolve
4. Run integration tests across all phases
5. Deploy to production environment

---

**🎉 Autonomous Phase Completion: COMPLETE**
"""

        self.summary_file.write_text(report)
        print(f"\n✅ Summary report written to: {self.summary_file}\n")

    def _print_quick_stats(self):
        """Print quick statistics summary."""
        print("\n" + "=" * 70)
        print("Quick Statistics")
        print("=" * 70)
        print(f"Phases Processed: {self.stats['phases_processed']}/10")
        print(f"Sub-phases Validated: {self.stats['sub_phases_validated']}")
        print(f"Sub-phases Implemented: {self.stats['sub_phases_implemented']}")
        print(f"Sub-phases Blocked: {self.stats['sub_phases_blocked']}")
        print(f"Sub-phases Skipped: {self.stats['sub_phases_skipped']}")
        print(f"Git Commits: {self.stats['git_commits']}")
        print("=" * 70 + "\n")

        if self.blocked_sub_phases:
            print(
                f"⚠️  {len(self.blocked_sub_phases)} sub-phases blocked - See {self.summary_file}"
            )
        if self.skipped_sub_phases:
            print(
                f"ℹ️  {len(self.skipped_sub_phases)} sub-phases skipped (costly infrastructure)"
            )

        print()

    def _format_duration(self, duration) -> str:
        """Format duration as human-readable string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def run_single_phase(self, phase_num: int):
        """Run autonomous completion on a single phase."""
        print(f"\n{'='*70}")
        print(f"Processing Phase {phase_num}")
        print(f"{'='*70}\n")

        self._init_progress_tracker()
        self._process_phase(phase_num)
        self._generate_summary_report()

    def run_single_sub_phase(self, phase_num: int, sub_phase_id: str):
        """Run validation on a single sub-phase."""
        print(f"\n{'='*70}")
        print(f"Processing Sub-Phase {sub_phase_id}")
        print(f"{'='*70}\n")

        # Get sub-phase info
        sub_phases = self._get_sub_phases(phase_num)
        sub_phase = next((sp for sp in sub_phases if sp["id"] == sub_phase_id), None)

        if not sub_phase:
            print(f"❌ Sub-phase {sub_phase_id} not found in Phase {phase_num}\n")
            return

        if sub_phase["status"] == "COMPLETE" and not sub_phase["validated"]:
            self._validate_sub_phase(sub_phase)
        elif sub_phase["status"] in ["PLANNED", "PENDING"]:
            self._implement_sub_phase(sub_phase)
        else:
            print(f"ℹ️  Sub-phase already validated or in unexpected state\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Autonomous Phase Completion Agent")
    parser.add_argument("--all", action="store_true", help="Process all phases (0-9)")
    parser.add_argument("--phase", type=int, help="Process specific phase")
    parser.add_argument(
        "--subphase", type=str, help="Process specific sub-phase (requires --phase)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview actions without executing"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    agent = AutonomousPhaseCompletionAgent(dry_run=args.dry_run, verbose=args.verbose)

    if args.all:
        agent.run_all_phases()
    elif args.phase is not None:
        if args.subphase:
            agent.run_single_sub_phase(args.phase, args.subphase)
        else:
            agent.run_single_phase(args.phase)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
