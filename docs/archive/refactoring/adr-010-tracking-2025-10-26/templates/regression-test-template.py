#!/usr/bin/env python3
"""
ADR-010 Regression Tests

Automated tests to prevent ADR-010 violations.
Run with: pytest tests/test_adr_010_compliance.py -v
"""

import pytest
import re
from pathlib import Path

# Exclude patterns
EXCLUDE_PATHS = [
    "docs/archive/",
    "data/",
    "synthesis_output/",
    ".git/",
    "__pycache__/",
]

# Old format pattern
OLD_FORMAT_PATTERN = (
    r"\b(Phase\s+[0-9]\.([0-9]{1,3})(?![0-9])|phase_[0-9]/([0-9]{1,3})_)"
)


def test_no_old_format_in_docs():
    """Verify no old format phase references in documentation."""
    violations = []
    docs_dir = Path("docs")

    for md_file in docs_dir.rglob("*.md"):
        # Skip archives
        if any(exc in str(md_file) for exc in EXCLUDE_PATHS):
            continue

        content = md_file.read_text()
        matches = re.finditer(OLD_FORMAT_PATTERN, content, re.IGNORECASE)

        for match in matches:
            violations.append(f"{md_file}:{match.group(0)}")

    assert (
        len(violations) == 0
    ), f"Found {len(violations)} ADR-010 violations in docs:\n" + "\n".join(
        violations[:10]
    )


def test_no_old_format_in_code():
    """Verify no old format phase references in Python code."""
    violations = []

    for py_file in Path(".").rglob("*.py"):
        if any(exc in str(py_file) for exc in EXCLUDE_PATHS):
            continue

        content = py_file.read_text()
        matches = re.finditer(OLD_FORMAT_PATTERN, content)

        for match in matches:
            violations.append(f"{py_file}:{match.group(0)}")

    assert (
        len(violations) == 0
    ), f"Found {len(violations)} violations in code:\n" + "\n".join(violations[:10])


def test_phase_directories_use_4digit():
    """Verify all phase directories use 4-digit format."""
    violations = []
    phase_dirs = Path("docs/phases").glob("phase_*/")

    for phase_dir in phase_dirs:
        subdirs = [d for d in phase_dir.iterdir() if d.is_dir()]
        for subdir in subdirs:
            # Check format: N.MMMM_name (4 digits)
            if not re.match(r"^\d+\.\d{4}_", subdir.name):
                violations.append(str(subdir))

    assert len(violations) == 0, f"Found non-compliant directories:\n" + "\n".join(
        violations
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
