#!/usr/bin/env python3
"""
ADR-010 Compliance Validation Script

Validates that all phase references use 4-digit format.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Exclude patterns
EXCLUDE_PATHS = [
    "docs/archive/",
    "data/",
    "synthesis_output/",
    ".git/",
    "__pycache__/",
]

# Old format pattern (matches 0.1, 0.10, etc but NOT 0.0001)
OLD_FORMAT_PATTERN = (
    r"\b(Phase\s+[0-9]\.([0-9]{1,3})(?![0-9])|phase_[0-9]/([0-9]{1,3})_)"
)


def check_directory_names() -> Tuple[bool, List[str]]:
    """Check all phase directories use 4-digit format."""
    violations = []
    phase_dirs = Path("docs/phases").glob("phase_*/")

    for phase_dir in phase_dirs:
        subdirs = [d for d in phase_dir.iterdir() if d.is_dir()]
        for subdir in subdirs:
            if not re.match(r"^\d+\.\d{4}_", subdir.name):
                violations.append(str(subdir))

    return len(violations) == 0, violations


def check_doc_references() -> Tuple[bool, List[str]]:
    """Check documentation references use 4-digit format."""
    violations = []
    docs_dir = Path("docs")

    for md_file in docs_dir.rglob("*.md"):
        if any(exc in str(md_file) for exc in EXCLUDE_PATHS):
            continue

        content = md_file.read_text()
        matches = re.finditer(OLD_FORMAT_PATTERN, content, re.IGNORECASE)

        for match in matches:
            violations.append(f"{md_file}:{match.group(0)}")

    return len(violations) == 0, violations


def main(verbose: bool = False):
    """Run all validation checks."""
    print("🔍 Validating ADR-010 Compliance...")
    print("=" * 70)

    checks = []

    # Run all checks
    checks.append(("Directory names", check_directory_names()))
    checks.append(("Documentation references", check_doc_references()))

    # Print results
    all_pass = True
    for check_name, (passed, violations) in checks:
        if passed:
            print(f"✅ {check_name}: PASS")
        else:
            print(f"❌ {check_name}: FAIL ({len(violations)} violations)")
            if verbose:
                for v in violations[:10]:
                    print(f"   - {v}")
            all_pass = False

    print("=" * 70)
    if all_pass:
        print("✅ ADR-010 COMPLIANCE: PASSED")
        return 0
    else:
        print("❌ ADR-010 COMPLIANCE: FAILED")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    sys.exit(main(args.verbose))
