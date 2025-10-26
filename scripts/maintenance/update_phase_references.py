#!/usr/bin/env python3
"""
Update Phase References to 4-Digit Format (ADR-010 STEP 5)

This script updates all documentation and code references from old format
(e.g., "0.0001", "phase_0/0.0001_name/") to new 4-digit format
(e.g., "0.0001", "phase_0/0.0001_name/").

Usage:
    python scripts/maintenance/update_phase_references.py --dry-run
    python scripts/maintenance/update_phase_references.py --execute
    python scripts/maintenance/update_phase_references.py --rename-tests
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Safe directories to scan (whitelist approach)
SAFE_DIRS = [
    "docs",
    "tests",
    "scripts",
    "validators",
]

# Directories to NEVER touch
EXCLUDE_DIRS = [
    "data",
    "synthesis_output",
    "docs/archive",
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
]

# File extensions to process
SAFE_EXTENSIONS = {
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
    ".json",  # Only in safe dirs
}

# Patterns to replace
# Format: (pattern, replacement_function, description)
PATTERNS = []


def format_phase_0(match):
    """Convert Phase 0.X to Phase 0.000X"""
    num = int(match.group(1))
    return f"Phase 0.{num:04d}"


def format_phase_5(match):
    """Convert Phase 5.X to Phase 5.000X"""
    num = int(match.group(1))
    return f"Phase 5.{num:04d}"


def format_phase_8(match):
    """Convert Phase 8.X to Phase 8.000X"""
    num = int(match.group(1))
    return f"Phase 8.{num:04d}"


def format_phase_9(match):
    """Convert Phase 9.X to Phase 9.000X"""
    num = int(match.group(1))
    return f"Phase 9.{num:04d}"


def format_path_phase_0(match):
    """Convert phase_0/0.X_ to phase_0/0.000X_"""
    num = int(match.group(1))
    return f"phase_0/0.{num:04d}_"


def format_path_phase_5(match):
    """Convert phase_5/5.X_ to phase_5/5.000X_"""
    num = int(match.group(1))
    return f"phase_5/5.{num:04d}_"


def format_path_phase_8(match):
    """Convert phase_8/8.X_ to phase_8/8.000X_"""
    num = int(match.group(1))
    return f"phase_8/8.{num:04d}_"


def format_path_phase_9(match):
    """Convert phase_9/9.X_ to phase_9/9.000X_"""
    num = int(match.group(1))
    return f"phase_9/9.{num:04d}_"


def format_test_0(match):
    """Convert test_0_X to test_0_00000X"""
    num = int(match.group(1))
    return f"test_0_{num:04d}"


def format_test_5(match):
    """Convert test_5_X to test_5_0000X"""
    num = int(match.group(1))
    return f"test_5_{num:04d}"


# Define patterns
# Prose text patterns (e.g., "0.0001")
PATTERNS.extend(
    [
        (
            re.compile(r"\bPhase 0\.(\d{1,2})\b"),
            format_phase_0,
            "Prose: Phase 0.X → Phase 0.000X",
        ),
        (
            re.compile(r"\bPhase 5\.(\d{1,3})\b"),
            format_phase_5,
            "Prose: Phase 5.X → Phase 5.000X",
        ),
        (
            re.compile(r"\bPhase 8\.(\d{1,2})\b"),
            format_phase_8,
            "Prose: Phase 8.X → Phase 8.000X",
        ),
        (
            re.compile(r"\bPhase 9\.(\d{1,2})\b"),
            format_phase_9,
            "Prose: Phase 9.X → Phase 9.000X",
        ),
    ]
)

# File path patterns (e.g., "phase_0/0.0001_name/")
PATTERNS.extend(
    [
        (
            re.compile(r"phase_0/0\.(\d{1,2})_"),
            format_path_phase_0,
            "Path: phase_0/0.X_ → phase_0/0.000X_",
        ),
        (
            re.compile(r"phase_5/5\.(\d{1,3})_"),
            format_path_phase_5,
            "Path: phase_5/5.X_ → phase_5/5.000X_",
        ),
        (
            re.compile(r"phase_8/8\.(\d{1,2})_"),
            format_path_phase_8,
            "Path: phase_8/8.X_ → phase_8/8.000X_",
        ),
        (
            re.compile(r"phase_9/9\.(\d{1,2})_"),
            format_path_phase_9,
            "Path: phase_9/9.X_ → phase_9/9.000X_",
        ),
    ]
)

# Test file patterns (e.g., "test_0_0004.py")
PATTERNS.extend(
    [
        (
            re.compile(r"test_0_(\d{1,2})"),
            format_test_0,
            "Test: test_0_X → test_0_00000X",
        ),
        (
            re.compile(r"test_5_(\d{1,3})"),
            format_test_5,
            "Test: test_5_X → test_5_0000X",
        ),
    ]
)


def is_excluded(file_path: Path) -> bool:
    """Check if file path should be excluded"""
    path_str = str(file_path)

    # Check exclude directories
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in path_str:
            return True

    return False


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed"""
    # Check if excluded
    if is_excluded(file_path):
        return False

    # Check if in safe directory
    relative = file_path.relative_to(PROJECT_ROOT)
    in_safe_dir = any(str(relative).startswith(safe_dir) for safe_dir in SAFE_DIRS)

    if not in_safe_dir:
        return False

    # Check file extension
    if file_path.suffix not in SAFE_EXTENSIONS:
        return False

    return True


def find_files_to_process() -> List[Path]:
    """Find all files that should be processed"""
    files = []

    for safe_dir in SAFE_DIRS:
        dir_path = PROJECT_ROOT / safe_dir
        if not dir_path.exists():
            continue

        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and should_process_file(file_path):
                files.append(file_path)

    return sorted(files)


def process_file(file_path: Path, dry_run: bool = True) -> Tuple[bool, int]:
    """
    Process a single file

    Returns:
        (changed, num_replacements)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return False, 0

    original_content = content
    total_replacements = 0

    # Apply all patterns
    for pattern, replacement_func, description in PATTERNS:
        new_content, num_subs = pattern.subn(replacement_func, content)
        if num_subs > 0:
            content = new_content
            total_replacements += num_subs

    # Check if changed
    if content != original_content:
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        return True, total_replacements

    return False, 0


def find_test_files_to_rename() -> List[Tuple[Path, Path]]:
    """Find test files that need to be renamed"""
    renames = []

    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        return renames

    # Pattern: test_0_X.py or test_0_X_name.py
    pattern_0 = re.compile(r"test_0_(\d{1,2})(?:_(.+))?\.py$")
    pattern_5 = re.compile(r"test_5_(\d{1,3})(?:_(.+))?\.py$")

    for test_file in tests_dir.rglob("test_*.py"):
        filename = test_file.name

        # Check Phase 0 tests
        match = pattern_0.match(filename)
        if match:
            num = int(match.group(1))
            suffix = match.group(2)
            if suffix:
                new_name = f"test_0_{num:04d}_{suffix}.py"
            else:
                new_name = f"test_0_{num:04d}.py"

            new_path = test_file.parent / new_name
            if new_path != test_file:
                renames.append((test_file, new_path))
            continue

        # Check Phase 5 tests
        match = pattern_5.match(filename)
        if match:
            num = int(match.group(1))
            suffix = match.group(2)
            if suffix:
                new_name = f"test_5_{num:04d}_{suffix}.py"
            else:
                new_name = f"test_5_{num:04d}.py"

            new_path = test_file.parent / new_name
            if new_path != test_file:
                renames.append((test_file, new_path))

    return sorted(renames)


def main():
    parser = argparse.ArgumentParser(
        description="Update phase references to 4-digit format (ADR-010 STEP 5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed changes without applying them",
    )
    parser.add_argument("--execute", action="store_true", help="Execute the updates")
    parser.add_argument(
        "--rename-tests", action="store_true", help="Generate test file rename commands"
    )

    args = parser.parse_args()

    # Require exactly one action
    if sum([args.dry_run, args.execute, args.rename_tests]) != 1:
        parser.error(
            "Must specify exactly one of: --dry-run, --execute, --rename-tests"
        )

    if args.rename_tests:
        print("🔍 Finding test files to rename...")
        renames = find_test_files_to_rename()

        if not renames:
            print("✅ No test files need renaming")
            return 0

        print(f"\n📋 Found {len(renames)} test files to rename:\n")

        for old_path, new_path in renames:
            old_rel = old_path.relative_to(PROJECT_ROOT)
            new_rel = new_path.relative_to(PROJECT_ROOT)
            print(f"  {old_rel} → {new_rel}")

        # Generate rename script
        script_path = Path("/tmp/rename_tests.sh")
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated test file rename script\n")
            f.write(f"cd {PROJECT_ROOT}\n\n")

            for old_path, new_path in renames:
                f.write(f'git mv "{old_path}" "{new_path}"\n')

        script_path.chmod(0o755)
        print(f"\n✅ Rename script generated: {script_path}")
        print(f"   Execute with: bash {script_path}")

        return 0

    # Process files
    dry_run = args.dry_run
    mode_str = "DRY RUN" if dry_run else "EXECUTE"

    print(f"🔍 {mode_str}: Finding files to process...")
    files = find_files_to_process()
    print(f"   Found {len(files)} files in safe directories")

    print(f"\n📝 {mode_str}: Processing files...")

    changed_files = []
    total_changes = 0

    for file_path in files:
        changed, num_replacements = process_file(file_path, dry_run=dry_run)
        if changed:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            changed_files.append((rel_path, num_replacements))
            total_changes += num_replacements

    # Print summary
    print(f"\n{'═' * 70}")
    print(f"  {mode_str} SUMMARY")
    print(f"{'═' * 70}")
    print(f"  Files processed: {len(files)}")
    print(f"  Files changed: {len(changed_files)}")
    print(f"  Total replacements: {total_changes}")
    print(f"{'═' * 70}\n")

    if changed_files:
        print("📋 Changed files:\n")
        for rel_path, num_replacements in changed_files:
            print(f"  {rel_path} ({num_replacements} replacements)")
        print()

    if dry_run:
        print("💡 To execute updates, run:")
        print("   python scripts/maintenance/update_phase_references.py --execute")
    else:
        print("✅ Updates complete!")
        print("\n💡 Next steps:")
        print("   1. Review changes: git diff --stat")
        print(
            "   2. Rename tests: python scripts/maintenance/update_phase_references.py --rename-tests"
        )
        print(
            "   3. Commit: git commit -am 'refactor: STEP 5 - Update phase references (ADR-010)'"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
