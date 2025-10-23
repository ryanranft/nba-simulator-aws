# Workflow #53: Phase Test & Validator Organization

**Version:** 1.0
**Created:** October 23, 2025
**Purpose:** Organize tests and validators for phase-specific validation
**Trigger:** When creating tests/validators for any phase
**Frequency:** Every new phase or sub-phase

---

## Overview

This workflow defines the standard organization for phase tests and validators, implemented in October 2025 to separate code from documentation in the `docs/` directory.

**Key Principle:** `docs/` contains ONLY documentation. Tests go in `tests/`, validators go in `validators/`.

---

## Directory Structure

```
nba-simulator-aws/
├── tests/                          # All test files (pytest discovers here)
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── phases/                     # Phase validation tests ⭐
│   │   ├── phase_0/
│   │   │   ├── conftest.py         # Phase 0 shared fixtures
│   │   │   ├── test_0_1_initial_data_collection.py
│   │   │   ├── test_0_2_hoopr_data.py
│   │   │   └── ...
│   │   ├── phase_1/
│   │   ├── phase_2/
│   │   └── ...
│   └── manual/                     # Manual tests
│
├── validators/                     # All validator scripts ⭐
│   ├── phases/                     # Phase-specific validators
│   │   ├── phase_0/
│   │   │   ├── validate_0_1_s3_bucket_config.py
│   │   │   ├── validate_0_1_upload_completeness.py
│   │   │   └── ...
│   │   └── ...
│   ├── data/                       # Data validation
│   │   ├── validate_espn_pbp_files.py
│   │   ├── validate_nba_api_files.py
│   │   └── ...
│   └── security/                   # Security validators
│       ├── validate_secrets_security.py
│       ├── validate_s3_public_access.py
│       └── ...
│
└── docs/                           # DOCUMENTATION ONLY
    └── phases/
        ├── PHASE_N_INDEX.md
        └── phase_N/
            └── N.M_name/
                ├── README.md       # Documentation
                └── ...             # No .py files (except deprecated)
```

---

## Naming Conventions

### Tests

**Format:** `test_N_M_descriptive_name.py`

**Examples:**
- `test_0_1_initial_data_collection.py` (Phase 0, Sub-phase 1)
- `test_1_2_data_quality_checks.py` (Phase 1, Sub-phase 2)
- `test_3_0_database_setup.py` (Phase 3, Sub-phase 0)

**Class names:** Follow pytest conventions
```python
class TestS3BucketConfiguration:
    """Tests for S3 bucket config."""

class TestUploadCompleteness:
    """Tests for upload completeness."""
```

###Validators

**Format:** `validate_N_M_feature.py`

**Examples:**
- `validate_0_1_s3_bucket_config.py`
- `validate_0_1_upload_completeness.py`
- `validate_1_2_data_quality.py`

---

## When to Create Tests vs Validators

### Validators (Operational Scripts)

**Use validators when:**
- Need standalone executable script
- Running manual validation/verification
- Live system health checks
- ADCE integration (dynamic data tracking)
- CI/CD pre-deployment checks

**Example:** `validate_0_1_upload_completeness.py`
- Runs independently: `python validators/phases/phase_0/validate_0_1_upload_completeness.py`
- Shows live S3 metrics
- Returns exit code for CI/CD
- Displays user-friendly output

### Tests (Pytest Suite)

**Use tests when:**
- Automated test suite execution
- Unit/integration testing
- Regression testing
- Part of CI/CD test phase

**Example:** `test_0_1_initial_data_collection.py`
- Runs via pytest: `pytest tests/phases/phase_0/test_0_1_initial_data_collection.py`
- Uses pytest fixtures and markers
- Generates test reports
- Integration with test frameworks

**Both can coexist:** Tests often import and call validators!

---

## Step-by-Step: Creating Phase Tests

### Step 1: Create Test File

```bash
# Determine phase and sub-phase numbers
# Example: Phase 0, Sub-phase 1
touch tests/phases/phase_0/test_0_1_initial_data_collection.py
```

### Step 2: Add Imports

```python
import pytest
import sys
from pathlib import Path

# Import validators from new location
validators_path = Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_0"
sys.path.insert(0, str(validators_path))

from validate_0_1_s3_bucket_config import S3BucketConfigValidator
from validate_0_1_upload_completeness import S3UploadCompletenessValidator
```

### Step 3: Create Test Classes

```python
class TestPhaseNSubphaseM:
    """Tests for Phase N, Sub-phase M."""

    def test_feature_validation(self, fixture):
        """Test specific feature."""
        assert True
```

### Step 4: Add Markers (Optional)

```python
@pytest.mark.slow
def test_expensive_operation(self):
    """Slow test - mark for selective running."""
    pass

@pytest.mark.phase_0
def test_phase_specific(self):
    """Phase-specific test."""
    pass
```

---

## Step-by-Step: Creating Phase Validators

### Step 1: Create Validator File

```bash
touch validators/phases/phase_0/validate_0_1_feature.py
```

### Step 2: Validator Template

```python
#!/usr/bin/env python3
"""
Validate Phase N.M: Feature Name

Description of what this validator checks.

Usage:
    python validators/phases/phase_N/validate_N_M_feature.py
    python validators/phases/phase_N/validate_N_M_feature.py --option value
"""

import sys
from typing import List, Tuple, Dict

class PhaseNMFeatureValidator:
    """Validates feature for Phase N.M."""

    def __init__(self, **kwargs):
        self.failures: List[str] = []
        self.warnings: List[str] = []

    def validate_feature(self) -> bool:
        """Validate specific feature."""
        try:
            # Validation logic
            return True
        except Exception as e:
            self.failures.append(f"Validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations."""
        results = {
            'feature_valid': self.validate_feature(),
        }

        all_passed = all(results.values())
        return all_passed, results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate Phase N.M feature')
    parser.add_argument('--option', help='Optional parameter')
    args = parser.parse_args()

    validator = PhaseNMFeatureValidator()
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
```

---

## Integration with Phase Documentation

### Update Phase README

**Add validation section to phase README:**

```markdown
## Validation

### Run Validators

```bash
# Phase 0.1 validators
python validators/phases/phase_0/validate_0_1_s3_bucket_config.py
python validators/phases/phase_0/validate_0_1_upload_completeness.py
```

### Run Tests

```bash
# All Phase 0.1 tests
pytest tests/phases/phase_0/test_0_1_initial_data_collection.py -v

# Fast tests only
pytest tests/phases/phase_0/test_0_1_initial_data_collection.py -v -m "not slow"
```
```

---

## Migration from docs/phases/

**If existing tests/validators in `docs/phases/`:**

1. **Copy** files to new location (don't delete originals yet)
2. **Rename** to follow naming convention
3. **Update imports** in test files
4. **Verify** tests pass from new location
5. **Add deprecation notice** to old files
6. **Update documentation** to reference new paths
7. **Remove old files** after 1-2 sessions of verification

**Deprecation notice template:**
```python
"""
⚠️ DEPRECATED: This file has moved to [new_path]

This copy is kept for backward compatibility but will be removed in a future update.
Please use the new location:
    [new_path]

---
[original docstring]
"""
```

---

## Pytest Configuration

**Add to `pyproject.toml` or `pytest.ini`:**

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "phase_0: Phase 0 tests",
    "phase_1: Phase 1 tests",
    "phase_2: Phase 2 tests",
    # ... add more as needed
]
```

**Run tests by phase:**
```bash
pytest -m phase_0              # All Phase 0 tests
pytest tests/phases/phase_0/   # All Phase 0 tests (path-based)
pytest -m "phase_0 and not slow"  # Fast Phase 0 tests only
```

---

## ADCE Integration

**Validators should support ADCE (Autonomous Data Collection Ecosystem) tracking:**

```python
class Validator:
    def __init__(self):
        # Track initial baseline
        self.initial_total = 146_115

        # Exclude artifacts from counting
        self.exclude_prefixes = ['athena-results/', 'ml-models/']

        # ADCE data sources
        self.adce_sources = ['nba_api_comprehensive', ...]

    def get_adce_growth_metrics(self) -> Dict:
        """Calculate growth from ADCE autonomous collection."""
        # Query current state
        current = self.count_files()

        # Calculate growth
        growth = current - self.initial_total
        growth_pct = (growth / self.initial_total) * 100

        return {'current': current, 'growth': growth, 'growth_pct': growth_pct}
```

---

## Best Practices

### Tests

✅ **DO:**
- Use descriptive test names
- Group related tests in classes
- Use pytest fixtures for shared setup
- Add markers for slow/expensive tests
- Test one thing per test function
- Use clear assertion messages

❌ **DON'T:**
- Put tests in `docs/` directory
- Mix test logic with implementation
- Create tests without assertions
- Forget to import validators correctly

### Validators

✅ **DO:**
- Make validators runnable standalone
- Return proper exit codes (0 = success, 1 = failure)
- Track failures and warnings separately
- Provide user-friendly output
- Support command-line arguments
- Integrate with ADCE for live tracking

❌ **DON'T:**
- Put validators in `docs/` directory
- Hard-code paths or credentials
- Fail silently without clear error messages
- Mix validation logic with test framework

---

## Related Workflows

- **Workflow #52:** Phase Index Management - Phase documentation structure
- **Workflow #41:** Testing Framework - General testing best practices
- **Workflow #53:** This workflow - Test & validator organization

---

## Success Metrics

**Good test/validator organization achieves:**
- ✅ All tests discoverable via `pytest tests/`
- ✅ All validators executable from `validators/`
- ✅ `docs/` contains only documentation (no .py files except deprecated)
- ✅ Clear naming: `test_N_M_name.py`, `validate_N_M_feature.py`
- ✅ Easy migration path documented
- ✅ ADCE integration for dynamic tracking

---

**Workflow Owner:** Infrastructure Team
**Last Updated:** October 23, 2025
**Status:** Active
**Next Review:** November 2025

---

*For questions about test organization, see this workflow or TESTING.md.*
