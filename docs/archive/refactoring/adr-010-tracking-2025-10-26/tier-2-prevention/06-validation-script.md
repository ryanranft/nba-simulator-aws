# Task 2.3: Create Validation Script

**Status:** ⏸️ PENDING | **Time:** 30 minutes

---

## Objective

Create comprehensive validation script `scripts/maintenance/validate_adr_010_compliance.py`

---

## Script Template

See `docs/refactoring/adr-010/templates/validation-script-template.py` for full implementation.

**Key features:**
- Check directory names use 4-digit format
- Check test file names
- Check validator file names
- Check documentation references
- Check phase indexes
- Check import statements
- Verify no old format in non-archive files

**Usage:**
```bash
python scripts/maintenance/validate_adr_010_compliance.py
python scripts/maintenance/validate_adr_010_compliance.py --verbose
```

---

## Completion Checklist

- [ ] Script created
- [ ] All 7 validation checks implemented
- [ ] Script runs without errors
- [ ] Returns PASS on compliant codebase
- [ ] Returns FAIL with details on violations

---

[Tier 2 README](README.md) | [Template](../templates/validation-script-template.py)
