# Cleanup Instructions for ADR-010 Tracking System

**Purpose:** Guide for cleaning up temporary tracking documents after ADR-010 implementation is complete

**When to use this:** After ALL required tiers (Tier 1 + Tier 2 minimum) are fully implemented and tested

---

## Overview

This directory (`docs/refactoring/adr-010/`) contains **temporary working documents** for tracking the ADR-010 implementation. These are NOT permanent documentation.

**Permanent Documentation:**
- `docs/adr/010-four-digit-subphase-numbering.md` - Keep this forever as architectural record

**Temporary Tracking:**
- Everything in `docs/refactoring/adr-010/` - Delete after completion

---

## Pre-Cleanup Validation

**CRITICAL: Do NOT delete tracking docs until ALL of these pass:**

### 1. Run Comprehensive Validation

```bash
# Run the validation script
python scripts/maintenance/validate_adr_010_compliance.py --verbose

# Expected output:
✅ All phase directories use 4-digit format
✅ All test files use 4-digit format
✅ All documentation references use 4-digit format
✅ No old format detected in non-archive files
✅ ADR-010 COMPLIANCE: PASSED
```

### 2. Run Full Test Suite

```bash
# Run all tests including regression tests
pytest tests/ -v

# Expected output:
tests/test_adr_010_compliance.py::test_no_old_format_in_docs PASSED
tests/test_adr_010_compliance.py::test_no_old_format_in_code PASSED
tests/test_adr_010_compliance.py::test_phase_directories_use_4digit PASSED
...
====== X passed in Y.YYs ======
```

### 3. Verify Pre-Commit Hook Works

```bash
# Make a test change with old format
echo "Phase 0.1 test" >> /tmp/test.md
git add /tmp/test.md
git commit -m "test"

# Expected output:
❌ ERROR: Old phase numbering format detected (ADR-010 violation)
```

### 4. Check Completion Checklist

```bash
# All boxes should be checked
cat docs/refactoring/adr-010/01-COMPLETION-CHECKLIST.md

# Verify Tier 1 + Tier 2 minimum complete
# Tier 3 and 4 are optional
```

### 5. Verify ADR-010 Updated

```bash
# Check ADR-010 status
grep "Status:" docs/adr/010-four-digit-subphase-numbering.md

# Expected output:
**Status:** Implemented  # Changed from "Accepted" or "In Progress"
```

---

## Cleanup Options

### Option A: Complete Deletion (Recommended)

**When:** All validation passed, implementation complete, no need for historical reference

```bash
# 1. Final check
python scripts/maintenance/validate_adr_010_compliance.py --verbose
pytest tests/test_adr_010_compliance.py -v

# 2. Remove tracking directory
rm -rf docs/refactoring/adr-010/

# 3. Commit deletion
git add -A
git commit -m "chore: Remove ADR-010 tracking docs (implementation complete)"

# 4. Done!
```

**Pros:**
- Clean repository
- No clutter
- ADR-010 remains as the authoritative source

**Cons:**
- Lose detailed implementation notes
- Can't reference step-by-step guides later

---

### Option B: Archive (Alternative)

**When:** Want to keep implementation notes for future reference or similar refactorings

```bash
# 1. Create archive directory
mkdir -p docs/archive/refactoring/

# 2. Move tracking system
mv docs/refactoring/adr-010/ docs/archive/refactoring/adr-010-tracking-$(date +%Y-%m-%d)/

# 3. Remove empty parent directory
rmdir docs/refactoring/ 2>/dev/null || true

# 4. Commit archive
git add -A
git commit -m "chore: Archive ADR-010 tracking docs (implementation complete)"

# 5. Done!
```

**Pros:**
- Preserve detailed implementation notes
- Can reference for future similar refactorings
- Historical record of how implementation was done

**Cons:**
- More files in repository
- Adds to maintenance burden

---

## What to Keep vs Delete

### KEEP (Permanent Documentation)

✅ `docs/adr/010-four-digit-subphase-numbering.md`
- This is the architectural decision record
- Permanent historical documentation
- Referenced by CLAUDE.md

✅ `scripts/maintenance/validate_adr_010_compliance.py`
- Ongoing validation tool
- Prevents regression
- Part of maintenance tooling

✅ `tests/test_adr_010_compliance.py`
- Regression tests
- Run in CI/CD
- Prevents future violations

✅ `.pre-commit-config.yaml` (updated hook)
- Active pre-commit hook
- Enforces 4-digit format
- Production tooling

✅ `docs/templates/PHASE_INDEX_TEMPLATE.md`
- Moved to templates directory
- Used for creating new phases
- Production tooling

✅ `CONTRIBUTING.md` (if created)
- Onboarding documentation
- Contributor guidelines
- Permanent documentation

### DELETE (Temporary Tracking)

❌ `docs/refactoring/adr-010/00-MASTER-TRACKER.md`
- Temporary progress tracking
- No longer needed after completion

❌ `docs/refactoring/adr-010/01-COMPLETION-CHECKLIST.md`
- Temporary checklist
- Superseded by actual completion

❌ `docs/refactoring/adr-010/tier-*/README.md`
- Temporary tier overviews
- Implementation complete

❌ `docs/refactoring/adr-010/tier-*/XX-*.md`
- All individual task guides
- Implementation complete

❌ `docs/refactoring/adr-010/templates/` (if still in tracking dir)
- Temporary templates
- Should be moved to permanent location first

❌ `docs/refactoring/adr-010/CLEANUP-INSTRUCTIONS.md` (this file!)
- Self-referential cleanup guide
- Delete last

---

## Post-Cleanup Tasks

### 1. Update PROGRESS.md

```markdown
## Recent Completions

**ADR-010 Implementation (October 2025):**
- ✅ Migrated to 4-digit sub-phase numbering system
- ✅ Updated all documentation, tests, and code
- ✅ Added validation and regression tests
- 📖 See: docs/adr/010-four-digit-subphase-numbering.md
```

### 2. Update CLAUDE.md (if not already done)

```markdown
**Sub-phase naming:** `N.MMMM_name` (4-digit format per ADR-010)
```

### 3. Final Git Commit

```bash
# Commit cleanup
git add -A
git commit -m "chore: Complete ADR-010 cleanup

- Removed temporary tracking documents
- ADR-010 implementation fully complete
- All validation passing
- See docs/adr/010-four-digit-subphase-numbering.md for details"

# Push to remote
git push origin main
```

---

## Rollback (If Cleanup Was Premature)

If you deleted tracking docs but need them back:

```bash
# Find the commit before deletion
git log --oneline | grep "ADR-010 tracking"

# Restore from that commit
git checkout <commit-sha> -- docs/refactoring/adr-010/

# The tracking docs are back!
```

---

## Verification After Cleanup

Run these commands to verify everything still works:

```bash
# 1. Validation still passes
python scripts/maintenance/validate_adr_010_compliance.py --verbose

# 2. Tests still pass
pytest tests/test_adr_010_compliance.py -v

# 3. Pre-commit hook still works
# (Try committing a file with old format - should fail)

# 4. ADR-010 still accessible
cat docs/adr/010-four-digit-subphase-numbering.md

# 5. Templates still exist
ls -la docs/templates/PHASE*.md
```

---

## Cleanup Checklist

Use this checklist when performing cleanup:

- [ ] All Tier 1 tasks complete
- [ ] All Tier 2 tasks complete (recommended)
- [ ] All validation scripts passing
- [ ] All tests passing
- [ ] Pre-commit hook tested and working
- [ ] ADR-010 status updated to "Implemented"
- [ ] Moved templates to permanent location
- [ ] Moved validation scripts to permanent location
- [ ] Moved tests to permanent location
- [ ] Updated PROGRESS.md
- [ ] Created final git commit
- [ ] Deleted/archived tracking directory
- [ ] Verified everything still works post-cleanup
- [ ] Celebrated completion! 🎉

---

## Questions?

If unsure whether to clean up:

**Safe to clean up if:**
- ✅ All required tiers complete (Tier 1+2 minimum)
- ✅ All tests passing
- ✅ ADR-010 updated to "Implemented"
- ✅ No ongoing work referencing these docs

**NOT safe to clean up if:**
- ❌ Any Tier 1 tasks incomplete
- ❌ Tests failing
- ❌ Validation scripts failing
- ❌ Active work in progress using these guides

**When in doubt:** Archive instead of delete

---

**Last Updated:** October 26, 2025
**Related:** [ADR-010](../../adr/010-four-digit-subphase-numbering.md)
