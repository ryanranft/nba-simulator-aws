#!/usr/bin/env python3
"""
Phase Reference Refactoring Tool

Automatically refactors old phase format references (N.M) to new 4-digit format (N.MMMM)
throughout the codebase per ADR-010.

Usage:
    python refactor_phase_references.py --dry-run  # Preview changes (default)
    python refactor_phase_references.py --execute   # Apply changes
    python refactor_phase_references.py --help      # Show help

Created: October 26, 2025
ADR: 010 (4-digit sub-phase numbering)
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

# Patterns to skip (intentional examples in migration docs)
SKIP_FILES = {
    "docs/migrations/ADR-010-MIGRATION-GUIDE.md",
    "docs/adr/010-four-digit-subphase-numbering.md",
    "scripts/maintenance/refactor_phase_references.py",  # This script
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


def should_skip_file(file_path: Path, project_root: Path) -> bool:
    """Check if file should be skipped."""
    relative_path = str(file_path.relative_to(project_root))

    # Skip specific files
    if relative_path in SKIP_FILES:
        return True

    # Skip archive directories
    path_parts = file_path.parts
    if any(skip_dir in path_parts for skip_dir in SKIP_DIRS):
        return True

    return False


def zero_pad_subphase(match: re.Match) -> str:
    """Convert N.M format to N.MMMM format (4-digit zero-padded)."""
    phase = match.group(1)
    subphase = match.group(2)
    suffix = match.group(3) if match.lastindex >= 3 else ""

    # Zero-pad to 4 digits
    subphase_padded = subphase.zfill(4)

    return f"{phase}.{subphase_padded}{suffix}"


def refactor_content(content: str, file_path: Path) -> Tuple[str, List[Dict[str, str]]]:
    """
    Refactor old phase format to new 4-digit format.

    Returns:
        Tuple of (new_content, list_of_changes)
    """
    changes = []
    new_content = content

    # Pattern 1: "Phase N.M" (in text)
    # Example: "Phase 0.1" → "Phase 0.0001"
    pattern1 = re.compile(r"\bPhase (\d+)\.(\d+)\b")
    matches1 = list(pattern1.finditer(content))
    for match in matches1:
        old = match.group(0)
        new = zero_pad_subphase(match)
        if old != new:
            changes.append({"pattern": "Phase N.M", "old": old, "new": new})
    new_content = pattern1.sub(zero_pad_subphase, new_content)

    # Pattern 2: "Sub-Phase N.M" (in text)
    # Example: "Sub-Phase 3.5" → "Sub-Phase 3.0005"
    pattern2 = re.compile(r"\bSub-Phase (\d+)\.(\d+)\b")
    matches2 = list(pattern2.finditer(content))
    for match in matches2:
        old = match.group(0)
        new = zero_pad_subphase(match)
        if old != new:
            changes.append({"pattern": "Sub-Phase N.M", "old": old, "new": new})
    new_content = pattern2.sub(zero_pad_subphase, new_content)

    # Pattern 3: "phase_N/N.M_name" (in paths)
    # Example: "phase_0/0.1_basketball" → "phase_0/0.0001_basketball"
    pattern3 = re.compile(r"phase_(\d+)/(\d+)\.(\d+)_")
    matches3 = list(pattern3.finditer(new_content))
    for match in matches3:
        phase = match.group(1)
        major = match.group(2)
        minor = match.group(3)
        old = f"phase_{phase}/{major}.{minor}_"
        minor_padded = minor.zfill(4)
        new = f"phase_{phase}/{major}.{minor_padded}_"
        if old != new:
            changes.append({"pattern": "phase_N/N.M_name", "old": old, "new": new})

    def replace_path_pattern(match: re.Match) -> str:
        phase = match.group(1)
        major = match.group(2)
        minor = match.group(3)
        minor_padded = minor.zfill(4)
        return f"phase_{phase}/{major}.{minor_padded}_"

    new_content = pattern3.sub(replace_path_pattern, new_content)

    # Pattern 4: "N.M_name" (standalone, not in path)
    # Example: "0.18_api_integration" → "0.0018_api_integration"
    # BUT: Skip if preceded by "/" (covered by pattern 3)
    pattern4 = re.compile(r"(?<![/\d])(\d+)\.(\d{1,3})_([a-z_]+)")
    matches4 = list(pattern4.finditer(new_content))
    for match in matches4:
        major = match.group(1)
        minor = match.group(2)
        name = match.group(3)
        old = f"{major}.{minor}_{name}"
        minor_padded = minor.zfill(4)
        new = f"{major}.{minor_padded}_{name}"
        if old != new and len(minor) < 4:  # Only if not already 4-digit
            changes.append({"pattern": "N.M_name", "old": old, "new": new})

    def replace_standalone_pattern(match: re.Match) -> str:
        major = match.group(1)
        minor = match.group(2)
        name = match.group(3)
        if len(minor) >= 4:  # Already padded
            return match.group(0)
        minor_padded = minor.zfill(4)
        return f"{major}.{minor_padded}_{name}"

    new_content = pattern4.sub(replace_standalone_pattern, new_content)

    # Pattern 5: "phase_N.M" (in text, variable names)
    # Example: "phase_1.0" → "phase_1.0000"
    pattern5 = re.compile(r"\bphase_(\d+)\.(\d+)\b")
    matches5 = list(pattern5.finditer(new_content))
    for match in matches5:
        old = match.group(0)
        new = zero_pad_subphase(match)
        if old != new:
            changes.append({"pattern": "phase_N.M", "old": old, "new": new})
    new_content = pattern5.sub(zero_pad_subphase, new_content)

    return new_content, changes


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
        description="Refactor old phase format references (N.M) to new 4-digit format (N.MMMM)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python refactor_phase_references.py --dry-run   # Preview changes (default)
  python refactor_phase_references.py --execute    # Apply changes
  python refactor_phase_references.py --file scripts/analysis/data_quality_validator.py --execute
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
    print(f"{BLUE}Phase Reference Refactoring Tool (ADR-010){NC}")
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
        print(f"{GREEN}Files with changes:{NC}")
        print()
        for file_path, changes in sorted(all_changes_by_file.items()):
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
                # Show first 3 examples
                for change in pattern_changes[:3]:
                    print(
                        f"        {YELLOW}{change['old']}{NC} → {GREEN}{change['new']}{NC}"
                    )
                if len(pattern_changes) > 3:
                    print(f"        ... and {len(pattern_changes) - 3} more")
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
        print(f"  2. Validate: bash scripts/maintenance/validate_phase_numbering.sh")
        print(f"  3. Test: pytest tests/ -v")
        print(
            f"  4. Commit: git add . && git commit -m 'refactor: Convert phase references to 4-digit format (ADR-010)'"
        )
        print()
    elif total_modified == 0:
        print(f"{GREEN}✓ No old phase format references found!{NC}")
        print()


if __name__ == "__main__":
    main()
