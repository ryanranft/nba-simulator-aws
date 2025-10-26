# Test & Validator Migration Guide

**Date:** October 23, 2025
**Status:** Phase 0.0001 Complete (Proof-of-Concept) | 481 Tests Remaining
**Migration Type:** Reorganization (docs/ → tests/ and validators/)

---

## Overview

This document tracks the migration of 482 test files and validators from `docs/phases/` to proper directories (`tests/` and `validators/`).

**Goal:** Separate code from documentation to follow Python best practices.

---

## Progress

### Completed ✅

**Phase 0.0001:**
- ✅ Moved 2 validators to `validators/phases/phase_0/`
- ✅ Moved 1 test file + conftest to `tests/phases/phase_0/`
- ✅ All tests passing from new locations
- ✅ Old files marked as deprecated
- ✅ README updated with new paths
- ✅ Workflow #53 created
- ✅ Workflow #52 updated

### Remaining

**481 test files in `docs/phases/`:**
- Phase 0: ~12 files
- Phase 1: ~8 files
- Phase 2: ~15 files
- Phase 3: ~380 files (most from book recommendations)
- Phase 4: ~50 files
- Phase 5: ~16 files

---

## Migration Process (Proven)

### For Each Phase:

1. **Identify files:**
   ```bash
   find docs/phases/phase_N/ -name "test_*.py" -o -name "validate_*.py"
   ```

2. **Copy to new location:**
   ```bash
   # Tests
   cp docs/phases/phase_N/N.M.../test_*.py tests/phases/phase_N/test_N_M_name.py

   # Validators
   cp docs/phases/phase_N/N.M.../validate_*.py validators/phases/phase_N/validate_N_M_feature.py
   ```

3. **Update imports** in test files

4. **Verify tests pass:**
   ```bash
   pytest tests/phases/phase_N/test_N_M_name.py -v
   ```

5. **Add deprecation notice** to old files

6. **Update README** with new paths

7. **Remove old files** after verification

---

## Automated Migration Script

**Recommended for bulk migration:**

```python
#!/usr/bin/env python3
"""
Automate test/validator migration from docs/phases/ to new structure.

Usage:
    python scripts/migrate_tests.py --phase 3 --dry-run
    python scripts/migrate_tests.py --phase 3 --execute
"""

# TODO: Create this script for bulk migration of remaining 481 files
```

---

##Statistics

| Category | Before | After (Oct 23) | Remaining |
|----------|--------|----------------|-----------|
| **Tests in `docs/phases/`** | 482 | 481 | 481 |
| **Tests in `tests/phases/`** | 0 | 1 | +481 target |
| **Validators in `docs/phases/`** | 2 | 0 | 0 |
| **Validators in `validators/phases/`** | 0 | 2 | +TBD |

---

## Benefits Realized

✅ **Discoverability:** `pytest tests/` now works as expected
✅ **Clean docs:** `docs/phases/phase_0/0.1.../` contains only README.md
✅ **Standard structure:** Follows Python/pytest conventions
✅ **ADCE compatible:** Validators support dynamic tracking
✅ **Clear workflow:** Workflow #53 guides future phases

---

## Next Steps

**Option A: Phase-by-Phase Migration (Recommended)**
- Migrate one phase at a time
- Verify each phase independently
- Lower risk

**Option B: Automated Bulk Migration**
- Create migration script
- Run on all 481 files
- Higher efficiency, higher risk

**Option C: As-Needed Migration**
- Migrate files when working on specific phases
- Gradual, lowest risk
- Takes longer

---

## References

- **Workflow #53:** Phase Test & Validator Organization (complete guide)
- **Workflow #52:** Phase Index Management (updated with test/validator guidance)
- **Proof-of-concept:** Phase 0.0001 (`tests/phases/phase_0/`, `validators/phases/phase_0/`)

---

**Migration Owner:** Infrastructure Team
**Last Updated:** October 23, 2025
**Next Review:** After next phase migration
