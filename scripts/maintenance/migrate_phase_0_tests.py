#!/usr/bin/env python3
"""
Migrate Phase 0 test files from docs/phases/phase_0/ to tests/phases/phase_0/

This script:
1. Finds all test_*.py files in Phase 0 sub-phases
2. Copies them to tests/phases/phase_0/ with proper naming
3. Updates imports to reference implement_*.py files in docs/
4. Adds deprecation notices to original files
5. Creates a migration report

Usage:
    python scripts/maintenance/migrate_phase_0_tests.py --dry-run  # Preview changes
    python scripts/maintenance/migrate_phase_0_tests.py --execute  # Actually migrate
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_PHASE_0 = PROJECT_ROOT / "docs" / "phases" / "phase_0"
TESTS_PHASE_0 = PROJECT_ROOT / "tests" / "phases" / "phase_0"

# Sub-phases to migrate (exclude 0.1 - already migrated, and archived files)
SUB_PHASES = [
    "0.8_security_implementation",
    "0.9_data_extraction",
    "0.13_dispatcher_pipeline",
    "0.14_error_analysis",
    "0.15_information_availability",
    "0.16_robust_architecture",
    "0.17_external_apis",
]

DEPRECATION_NOTICE = '''"""
⚠️ DEPRECATED - This file has been migrated to tests/phases/phase_0/

This file is kept for backward compatibility only.
Please use the new location: tests/phases/phase_0/test_{phase_num}_{name}.py

See docs/TEST_VALIDATOR_MIGRATION_GUIDE.md for details.

Migrated: October 23, 2025
Part of: Phase 0 Complete Reorganization
"""

# Original implementation below (deprecated)
# ===========================================

'''


def find_test_files() -> List[Tuple[str, Path]]:
    """Find all test files in Phase 0 sub-phases."""
    test_files = []

    for sub_phase in SUB_PHASES:
        sub_phase_dir = DOCS_PHASE_0 / sub_phase
        if not sub_phase_dir.exists():
            continue

        for test_file in sub_phase_dir.glob("test_*.py"):
            test_files.append((sub_phase, test_file))

    return test_files


def extract_phase_numbers(sub_phase: str) -> str:
    """Extract phase numbers from sub-phase name."""
    match = re.match(r"(\d+\.\d+)_(.+)", sub_phase)
    if match:
        return match.group(1).replace(".", "_")
    return sub_phase.replace(".", "_")


def get_new_test_name(sub_phase: str, old_path: Path) -> str:
    """Generate new test file name."""
    phase_num = extract_phase_numbers(sub_phase)

    # Extract meaningful name from filename
    old_name = old_path.stem  # e.g., test_rec_044, test_variation_9_63aaebab

    # For security variations, keep the variation identifier
    if "variation" in old_name:
        return f"test_{phase_num}_security_{old_name.replace('test_', '')}.py"
    elif "rec_" in old_name:
        rec_num = re.search(r"rec_(\d+)", old_name)
        if rec_num:
            return f"test_{phase_num}_rec_{rec_num.group(1)}.py"

    # Default: use phase number and simplified name
    return f"test_{phase_num}_{old_path.stem.replace('test_', '')}.py"


def update_imports(content: str, sub_phase: str) -> str:
    """Update imports to reference implementation files in docs/."""
    lines = content.split("\n")
    updated_lines = []

    for line in lines:
        # Update import from local implement_* files
        if "from implement_" in line or "import implement_" in line:
            # Extract the implement filename
            match = re.search(r"(implement_\w+)", line)
            if match:
                impl_file = match.group(1)

                # Add path setup before imports
                if not any("sys.path.insert" in l for l in updated_lines):
                    updated_lines.extend(
                        [
                            "import sys",
                            "from pathlib import Path",
                            "",
                            "# Add implementation directory to path",
                            f"impl_path = Path(__file__).parent.parent.parent.parent / 'docs' / 'phases' / 'phase_0' / '{sub_phase}'",
                            "sys.path.insert(0, str(impl_path))",
                            "",
                        ]
                    )

                updated_lines.append(line)
                continue

        updated_lines.append(line)

    return "\n".join(updated_lines)


def migrate_test_file(sub_phase: str, old_path: Path, dry_run: bool = True) -> dict:
    """Migrate a single test file."""
    result = {
        "sub_phase": sub_phase,
        "old_path": str(old_path),
        "success": False,
        "new_path": None,
        "error": None,
    }

    try:
        # Read original content
        content = old_path.read_text()

        # Generate new path
        new_name = get_new_test_name(sub_phase, old_path)
        new_path = TESTS_PHASE_0 / new_name
        result["new_path"] = str(new_path)

        if not dry_run:
            # Ensure target directory exists
            TESTS_PHASE_0.mkdir(parents=True, exist_ok=True)

            # Update imports in content
            updated_content = update_imports(content, sub_phase)

            # Write new file
            new_path.write_text(updated_content)

            # Add deprecation notice to old file
            deprecated_content = DEPRECATION_NOTICE + content
            old_path.write_text(deprecated_content)

            result["success"] = True
        else:
            result["success"] = True  # Dry run success

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="Migrate Phase 0 test files")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually migrating",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the migration",
    )

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")

    dry_run = args.dry_run

    print(f"\n{'='*70}")
    print(f"Phase 0 Test Migration {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
    print(f"{'='*70}\n")

    # Find all test files
    test_files = find_test_files()
    print(f"Found {len(test_files)} test files to migrate:\n")

    results = []
    for sub_phase, test_file in test_files:
        print(f"Migrating: {sub_phase}/{test_file.name}")
        result = migrate_test_file(sub_phase, test_file, dry_run=dry_run)
        results.append(result)

        if result["success"]:
            print(f"  → {result['new_path']}")
        else:
            print(f"  ✗ ERROR: {result['error']}")
        print()

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\n{'='*70}")
    print(f"Migration {'Preview' if dry_run else 'Complete'}")
    print(f"{'='*70}")
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if dry_run:
        print(f"\nTo execute migration, run:")
        print(f"  python {__file__} --execute")
    else:
        print(f"\nMigration complete! Next steps:")
        print(f"  1. Run tests: pytest tests/phases/phase_0/ -v")
        print(f"  2. Verify all tests pass")
        print(f"  3. Commit changes")

    print(f"{'='*70}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
