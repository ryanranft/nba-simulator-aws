#!/usr/bin/env python3
"""
Phase Reorganization Refactoring Tool

Refactors old phase numbers (6, 8, 9) to their new locations per October 2025 reorganization:
- Old Phase 6 → Phase 0 sub-phases (0.0019, 0.0020, 0.0021)
- Old Phase 8 → Phase 0 sub-phase (0.0022)
- Old Phase 9 → Phase 2

Usage:
    python refactor_phase_reorganization.py --dry-run  # Preview changes (default)
    python refactor_phase_reorganization.py --execute   # Apply changes

Created: October 26, 2025
Related: ADR-010, SESSION_HANDOFF_2025-10-25_phase_reorganization.md
"""

import re
import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import shutil

# Colors for output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color

# Files to skip (intentional historical references)
SKIP_FILES = {
    "SESSION_HANDOFF_2025-10-25_phase_reorganization.md",
    "docs/phases/archive/",  # Skip all archived phase indexes
    "scripts/maintenance/refactor_phase_reorganization.py",  # This script
}

# Directories to skip
SKIP_DIRS = {
    "archive",
    ".git",
    "__pycache__",
    "venv",
    "env",
    ".pytest_cache",
}

# Phase reorganization mappings
PHASE_6_MAPPING = {
    "6.0": "0.0019",  # Testing/CI/CD
    "6.1": "0.0020",  # Monitoring
    "6.2": "0.0021",  # Documentation
}

PHASE_8_MAPPING = {
    "8.0": "0.0022",  # Data Audit (first sub-phase)
    "8.1": "0.0022",  # Data Audit (second sub-phase, same target)
}

# Phase 9 → Phase 2 (direct mapping)
PHASE_9_MAPPING = {
    "9.0": "2.0000",
    "9.1": "2.0001",
    "9.2": "2.0002",
    "9.3": "2.0003",
    "9.4": "2.0004",
    "9.5": "2.0005",
    "9.6": "2.0006",
    "9.7": "2.0007",
    "9.8": "2.0008",
}


def should_skip_file(file_path: Path, project_root: Path) -> bool:
    """Check if file should be skipped."""
    relative_path = str(file_path.relative_to(project_root))

    # Skip specific files
    for skip_file in SKIP_FILES:
        if skip_file in relative_path:
            return True

    # Skip archive directories
    path_parts = file_path.parts
    if any(skip_dir in path_parts for skip_dir in SKIP_DIRS):
        return True

    return False


def refactor_phase_6(content: str) -> Tuple[str, List[Dict[str, str]]]:
    """Refactor Phase 6 references to Phase 0 sub-phases."""
    changes = []
    new_content = content

    # Pattern: "Phase 6.0", "Phase 6.1", "Phase 6.2"
    for old_phase, new_phase in PHASE_6_MAPPING.items():
        pattern = re.compile(rf"\bPhase {old_phase}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"Phase {new_phase}"
            changes.append({"pattern": "Phase 6.X → 0.00XX", "old": old, "new": new})
        new_content = pattern.sub(f"Phase {new_phase}", new_content)

    # Pattern: "phase_6" directory references
    for old_phase, new_phase in PHASE_6_MAPPING.items():
        old_num = old_phase.replace(".", "_")
        new_num = new_phase.replace(".", "_")
        pattern = re.compile(rf"\bphase_6/{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"phase_0/{new_num}"
            changes.append(
                {"pattern": "phase_6/path → phase_0/path", "old": old, "new": new}
            )
        new_content = pattern.sub(f"phase_0/{new_num}", new_content)

    # Pattern: "6.0", "6.1", "6.2" standalone (in file names, test names, etc.)
    for old_phase, new_phase in PHASE_6_MAPPING.items():
        old_num = old_phase.replace(".", "_")
        new_num = new_phase.replace(".", "_")
        # Match test files: test_6_0 → test_0_0019
        pattern = re.compile(rf"\btest_{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"test_{new_num}"
            changes.append(
                {"pattern": "test_6_X → test_0_00XX", "old": old, "new": new}
            )
        new_content = pattern.sub(f"test_{new_num}", new_content)

        # Match validator files: validate_6_0 → validate_0_0019
        pattern = re.compile(rf"\bvalidate_{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"validate_{new_num}"
            changes.append(
                {"pattern": "validate_6_X → validate_0_00XX", "old": old, "new": new}
            )
        new_content = pattern.sub(f"validate_{new_num}", new_content)

    return new_content, changes


def refactor_phase_8(content: str) -> Tuple[str, List[Dict[str, str]]]:
    """Refactor Phase 8 references to Phase 0.0022."""
    changes = []
    new_content = content

    # Pattern: "Phase 8.0", "Phase 8.1", "Phase 8" (generic)
    for old_phase, new_phase in PHASE_8_MAPPING.items():
        pattern = re.compile(rf"\bPhase {old_phase}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"Phase {new_phase}"
            changes.append({"pattern": "Phase 8.X → 0.0022", "old": old, "new": new})
        new_content = pattern.sub(f"Phase {new_phase}", new_content)

    # Generic "Phase 8" (without sub-phase number)
    pattern = re.compile(r"\bPhase 8\b(?!\.\d)")
    matches = list(pattern.finditer(new_content))
    for match in matches:
        old = match.group(0)
        new = "Phase 0.0022"
        changes.append({"pattern": "Phase 8 → 0.0022", "old": old, "new": new})
    new_content = pattern.sub("Phase 0.0022", new_content)

    # Pattern: "phase_8" directory references
    for old_phase, new_phase in PHASE_8_MAPPING.items():
        old_num = old_phase.replace(".", "_")
        new_num = new_phase.replace(".", "_")
        pattern = re.compile(rf"\bphase_8/{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"phase_0/{new_num}"
            changes.append(
                {"pattern": "phase_8/path → phase_0/path", "old": old, "new": new}
            )
        new_content = pattern.sub(f"phase_0/{new_num}", new_content)

    # Pattern: test and validator files
    for old_phase, new_phase in PHASE_8_MAPPING.items():
        old_num = old_phase.replace(".", "_")
        new_num = new_phase.replace(".", "_")
        # Match test files: test_8_0 → test_0_0022
        pattern = re.compile(rf"\btest_{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"test_{new_num}"
            changes.append(
                {"pattern": "test_8_X → test_0_0022", "old": old, "new": new}
            )
        new_content = pattern.sub(f"test_{new_num}", new_content)

        # Match validator files: validate_8_0 → validate_0_0022
        pattern = re.compile(rf"\bvalidate_{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"validate_{new_num}"
            changes.append(
                {"pattern": "validate_8_X → validate_0_0022", "old": old, "new": new}
            )
        new_content = pattern.sub(f"validate_{new_num}", new_content)

    return new_content, changes


def refactor_phase_9(content: str) -> Tuple[str, List[Dict[str, str]]]:
    """Refactor Phase 9 references to Phase 2."""
    changes = []
    new_content = content

    # Pattern: "Phase 9.0" through "Phase 9.8"
    for old_phase, new_phase in PHASE_9_MAPPING.items():
        pattern = re.compile(rf"\bPhase {old_phase}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"Phase {new_phase}"
            changes.append({"pattern": "Phase 9.X → 2.000X", "old": old, "new": new})
        new_content = pattern.sub(f"Phase {new_phase}", new_content)

    # Generic "Phase 9" (without sub-phase number)
    pattern = re.compile(r"\bPhase 9\b(?!\.\d)")
    matches = list(pattern.finditer(new_content))
    for match in matches:
        old = match.group(0)
        new = "Phase 2"
        changes.append({"pattern": "Phase 9 → 2", "old": old, "new": new})
    new_content = pattern.sub("Phase 2", new_content)

    # Pattern: "phase_9" directory references
    for old_phase, new_phase in PHASE_9_MAPPING.items():
        old_num = old_phase.replace(".", "_")
        new_num = new_phase.replace(".", "_")
        pattern = re.compile(rf"\bphase_9/{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"phase_2/{new_num}"
            changes.append(
                {"pattern": "phase_9/path → phase_2/path", "old": old, "new": new}
            )
        new_content = pattern.sub(f"phase_2/{new_num}", new_content)

    # Pattern: test and validator files
    for old_phase, new_phase in PHASE_9_MAPPING.items():
        old_num = old_phase.replace(".", "_")
        new_num = new_phase.replace(".", "_")
        # Match test files: test_9_0 → test_2_0000
        pattern = re.compile(rf"\btest_{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"test_{new_num}"
            changes.append(
                {"pattern": "test_9_X → test_2_000X", "old": old, "new": new}
            )
        new_content = pattern.sub(f"test_{new_num}", new_content)

        # Match validator files: validate_9_0 → validate_2_0000
        pattern = re.compile(rf"\bvalidate_{old_num}\b")
        matches = list(pattern.finditer(new_content))
        for match in matches:
            old = match.group(0)
            new = f"validate_{new_num}"
            changes.append(
                {"pattern": "validate_9_X → validate_2_000X", "old": old, "new": new}
            )
        new_content = pattern.sub(f"validate_{new_num}", new_content)

    # Generic phase_9 references (without specific sub-phase)
    pattern = re.compile(r"\bphase_9\b(?!/)")
    matches = list(pattern.finditer(new_content))
    for match in matches:
        old = match.group(0)
        new = "phase_2"
        changes.append({"pattern": "phase_9 → phase_2", "old": old, "new": new})
    new_content = pattern.sub("phase_2", new_content)

    return new_content, changes


def refactor_content(content: str, file_path: Path) -> Tuple[str, List[Dict[str, str]]]:
    """
    Refactor phase reorganization references.

    Returns:
        Tuple of (new_content, list_of_changes)
    """
    all_changes = []

    # Apply Phase 6 refactoring
    content, changes_6 = refactor_phase_6(content)
    all_changes.extend(changes_6)

    # Apply Phase 8 refactoring
    content, changes_8 = refactor_phase_8(content)
    all_changes.extend(changes_8)

    # Apply Phase 9 refactoring
    content, changes_9 = refactor_phase_9(content)
    all_changes.extend(changes_9)

    return content, all_changes


def find_files_to_refactor(project_root: Path) -> List[Path]:
    """Find all files that may contain old phase references."""
    extensions = {".py", ".md", ".sh", ".yaml", ".yml", ".txt", ".rst"}
    files_to_check = []

    for ext in extensions:
        files_to_check.extend(project_root.rglob(f"*{ext}"))

    # Filter out skipped files/directories
    return [f for f in files_to_check if not should_skip_file(f, project_root)]


def refactor_file(
    file_path: Path, dry_run: bool, project_root: Path
) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Refactor a single file.

    Returns:
        Tuple of (was_modified, list_of_changes)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        print(
            f"{YELLOW}⚠ Warning: Could not read {file_path.relative_to(project_root)}: {e}{NC}"
        )
        return False, []

    new_content, changes = refactor_content(original_content, file_path)

    if not changes:
        return False, []

    if not dry_run:
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            print(
                f"{RED}✗ Error writing {file_path.relative_to(project_root)}: {e}{NC}"
            )
            # Restore backup
            shutil.move(str(backup_path), str(file_path))
            return False, []

    return True, changes


def main():
    parser = argparse.ArgumentParser(
        description="Refactor old phase numbers (6, 8, 9) to new locations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase Reorganization Mapping:
  Phase 6.0 → Phase 0.0019 (Testing/CI/CD)
  Phase 6.1 → Phase 0.0020 (Monitoring)
  Phase 6.2 → Phase 0.0021 (Documentation)
  Phase 8   → Phase 0.0022 (Data Audit)
  Phase 9   → Phase 2      (Play-by-Play to Box Score)

Examples:
  python refactor_phase_reorganization.py --dry-run   # Preview changes (default)
  python refactor_phase_reorganization.py --execute    # Apply changes
        """,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute refactoring (default is dry-run)",
    )
    parser.add_argument("--file", type=str, help="Refactor specific file only")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without modifying files (default)",
    )

    args = parser.parse_args()

    # If --execute is provided, turn off dry-run
    if args.execute:
        args.dry_run = False

    # Find project root
    project_root = Path(__file__).resolve().parent.parent.parent

    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BLUE}Phase Reorganization Refactoring Tool{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()

    if args.dry_run:
        print(f"{YELLOW}Mode: DRY RUN (preview only, no changes will be made){NC}")
    else:
        print(f"{GREEN}Mode: EXECUTE (files will be modified with .bak backups){NC}")
    print()

    # Find files to refactor
    if args.file:
        file_path = project_root / args.file
        if not file_path.exists():
            print(f"{RED}✗ Error: File not found: {args.file}{NC}")
            sys.exit(1)
        files_to_check = [file_path]
    else:
        print(f"Scanning for files to refactor...")
        files_to_check = find_files_to_refactor(project_root)
        print(f"Found {len(files_to_check)} files to check")
        print()

    # Refactor files
    total_modified = 0
    total_changes = 0
    all_changes_by_file = {}

    for file_path in files_to_check:
        was_modified, changes = refactor_file(file_path, args.dry_run, project_root)

        if was_modified:
            total_modified += 1
            total_changes += len(changes)
            relative_path = str(file_path.relative_to(project_root))
            all_changes_by_file[relative_path] = changes

    # Print summary
    print()
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BLUE}Summary{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()
    print(f"Files scanned: {len(files_to_check)}")
    print(f"Files modified: {total_modified}")
    print(f"Total changes: {total_changes}")
    print()

    if all_changes_by_file:
        print(f"{GREEN}Files with changes (showing first 20):{NC}")
        print()
        for i, (file_path, changes) in enumerate(
            sorted(all_changes_by_file.items())[:20]
        ):
            print(f"  {file_path}")
            print(f"    Changes: {len(changes)}")

            # Group changes by pattern
            changes_by_pattern = {}
            for change in changes:
                pattern = change["pattern"]
                if pattern not in changes_by_pattern:
                    changes_by_pattern[pattern] = []
                changes_by_pattern[pattern].append(change)

            for pattern, pattern_changes in sorted(changes_by_pattern.items()):
                print(f"      {pattern}: {len(pattern_changes)} replacement(s)")
                # Show first 2 examples
                for change in pattern_changes[:2]:
                    print(
                        f"        {YELLOW}{change['old']}{NC} → {GREEN}{change['new']}{NC}"
                    )
                if len(pattern_changes) > 2:
                    print(f"        ... and {len(pattern_changes) - 2} more")
            print()

        if len(all_changes_by_file) > 20:
            print(f"  ... and {len(all_changes_by_file) - 20} more files")
            print()

    if args.dry_run and total_modified > 0:
        print(f"{YELLOW}This was a dry run. To apply changes, run:{NC}")
        print(f"  python {Path(__file__).name} --execute")
        print()
    elif not args.dry_run and total_modified > 0:
        print(f"{GREEN}✓ Refactoring complete!{NC}")
        print()
        print(f"Backup files created with .bak extension")
        print()
        print(f"Next steps:")
        print(f"  1. Review changes: git diff")
        print(f"  2. Move test/validator directories (see plan)")
        print(f"  3. Validate: bash scripts/maintenance/validate_phase_numbering.sh")
        print(f"  4. Commit changes")
        print()
    elif total_modified == 0:
        print(f"{GREEN}✓ No old phase references found!{NC}")
        print()


if __name__ == "__main__":
    main()
