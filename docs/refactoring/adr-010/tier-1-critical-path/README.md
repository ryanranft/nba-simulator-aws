# Tier 1: Critical Path

**Status:** ⏸️ PENDING
**Priority:** CRITICAL - MUST COMPLETE BEFORE COMMITTING ADR-010
**Estimated Time:** ~45 minutes
**Completion:** 0/5 tasks (0%)

---

## Overview

Tier 1 contains **absolutely critical** tasks that MUST be completed before committing the ADR-010 refactoring. These tasks fix user-facing documentation and production artifacts that would cause immediate confusion or breakage if left in the old format.

**Why Critical:**
- These files are referenced daily by developers
- CLAUDE.md is the primary guidance document for Claude Code
- SQL migrations are production database artifacts
- QUICKSTART.md is the first file new developers read
- Broken references cause immediate workflow disruption

---

## Tasks in Tier 1

| # | Task | File to Update | Impact | Time | Status |
|---|------|----------------|--------|------|--------|
| 1.1 | [Update CLAUDE.md](01-update-claude-md.md) | `CLAUDE.md` | CRITICAL | 10 min | ⏸️ PENDING |
| 1.2 | [Verify Phase Indexes](02-verify-phase-indexes.md) | 6 `PHASE_N_INDEX.md` files | HIGH | 5 min | ⏸️ PENDING |
| 1.3 | [Update SQL Migrations](11-update-sql-migrations.md) | ~15 `.sql` files | HIGH | 15 min | ⏸️ PENDING |
| 1.4 | [Update validate_phase.py](12-update-validate-phase-py.md) | `validate_phase.py` | MEDIUM | 10 min | ⏸️ PENDING |
| 1.5 | [Update QUICKSTART.md](13-update-quickstart-md.md) | `QUICKSTART.md` | MEDIUM | 5 min | ⏸️ PENDING |

---

## Execution Order

**Recommended sequence:**

1. **Start with #1.2** (Verify Phase Indexes) - Quick validation, sets baseline
2. **Then #1.1** (Update CLAUDE.md) - Most critical documentation
3. **Then #1.3** (Update SQL Migrations) - Production artifacts
4. **Then #1.5** (Update QUICKSTART.md) - Quick win, user-facing
5. **Finally #1.4** (Update validate_phase.py) - Developer tooling

**Alternative: Parallel execution** (if working with multiple people):
- Person A: #1.1 (CLAUDE.md) + #1.5 (QUICKSTART.md)
- Person B: #1.3 (SQL Migrations) + #1.4 (validate_phase.py)
- Person C: #1.2 (Verify Phase Indexes)

---

## Success Criteria

Tier 1 is **complete** when:

✅ All 5 tasks marked as COMPLETED
✅ CLAUDE.md contains zero old-format references
✅ All 6 PHASE_N_INDEX.md files use 4-digit format
✅ All SQL migration comments updated to 4-digit format
✅ validate_phase.py usage examples show 4-digit format
✅ QUICKSTART.md phase references use 4-digit format
✅ Manual validation confirms all changes correct

**Validation command:**
```bash
# Quick validation
grep -r "Phase [0-9]\.[0-9]" CLAUDE.md QUICKSTART.md scripts/automation/validate_phase.py
# Should return 0 results (all old format removed)

# Check SQL migrations
grep "Phase 0\." scripts/db/migrations/*.sql | grep -v "0\.0"
# Should return 0 results (all updated to 4-digit)
```

---

## Time Breakdown

| Task | Research | Execution | Validation | Total |
|------|----------|-----------|------------|-------|
| 1.1 CLAUDE.md | 2 min | 5 min | 3 min | 10 min |
| 1.2 Phase Indexes | 1 min | 2 min | 2 min | 5 min |
| 1.3 SQL Migrations | 2 min | 10 min | 3 min | 15 min |
| 1.4 validate_phase.py | 2 min | 5 min | 3 min | 10 min |
| 1.5 QUICKSTART.md | 1 min | 2 min | 2 min | 5 min |
| **TOTAL** | **8 min** | **24 min** | **13 min** | **45 min** |

---

## Dependencies

**Before starting Tier 1:**
- ✅ ADR-010 document created
- ✅ Directory/file renaming complete (STEP 5)
- ✅ Understanding of 4-digit format

**Tier 1 blocks:**
- Tier 2 (Prevention)
- Tier 3 (Documentation)
- Final commit of ADR-010

**No dependencies between Tier 1 tasks** - can be done in any order or in parallel

---

## Risk Mitigation

### Risk: Breaking links in documentation
**Mitigation:** Use find/replace carefully, validate all links manually

### Risk: Missing references
**Mitigation:** Use comprehensive grep searches before and after

### Risk: SQL syntax errors
**Mitigation:** Only update comments (not SQL code), verify syntax

### Risk: Incomplete updates
**Mitigation:** Run validation after each task

---

## Quick Start

To begin Tier 1:

1. **Read all 5 task documents** (~10 minutes)
2. **Choose execution order** (recommended: 1.2 → 1.1 → 1.3 → 1.5 → 1.4)
3. **Start with first task**
4. **Validate after each task**
5. **Update completion checklist**
6. **Move to next task**

---

## Validation After Tier 1

Run these commands before marking Tier 1 complete:

```bash
# 1. Check CLAUDE.md
grep -n "Phase [0-9]\.[0-9]" CLAUDE.md
grep -n "phase_[0-9]/[0-9]\.[0-9]" CLAUDE.md
# Both should return 0 results

# 2. Check QUICKSTART.md
grep -n "Phase 0\.[0-9]" QUICKSTART.md
# Should return 0 results

# 3. Check SQL migrations
grep "Phase 0\.[0-9]" scripts/db/migrations/*.sql | grep -v "0\.0[0-9][0-9][0-9]"
# Should return 0 results

# 4. Check validate_phase.py
grep "0\.[0-9]\"" scripts/automation/validate_phase.py
# Should return 0 results in usage examples

# 5. Verify phase indexes
for f in docs/phases/PHASE_*_INDEX.md; do
  echo "=== $f ==="
  grep "| [0-9]\.[0-9] " "$f" | grep -v "0\.[0-9][0-9][0-9][0-9]"
done
# Should return 0 results
```

---

## Common Issues

### Issue: Find/replace changes too much
**Solution:** Use specific patterns, validate before saving

### Issue: Unsure if a reference should be updated
**Solution:** Check context - if it's a phase reference, update it

### Issue: SQL file has syntax after change
**Solution:** Only change comments (lines starting with `--`)

### Issue: Can't find all references
**Solution:** Use multiple grep patterns, check all file types

---

## After Tier 1 Complete

1. ✅ Mark all 5 tasks as COMPLETED
2. ✅ Run full validation suite
3. ✅ Update `01-COMPLETION-CHECKLIST.md`
4. ✅ Update `00-MASTER-TRACKER.md`
5. ✅ Commit Tier 1 changes (or proceed to Tier 2 first)
6. ✅ Begin Tier 2 (recommended) or commit now

---

## Links

- [Master Tracker](../00-MASTER-TRACKER.md)
- [Completion Checklist](../01-COMPLETION-CHECKLIST.md)
- [ADR-010 Document](../../../adr/010-four-digit-subphase-numbering.md)

### Individual Task Guides
- [1.1 - Update CLAUDE.md](01-update-claude-md.md)
- [1.2 - Verify Phase Indexes](02-verify-phase-indexes.md)
- [1.3 - Update SQL Migrations](11-update-sql-migrations.md)
- [1.4 - Update validate_phase.py](12-update-validate-phase-py.md)
- [1.5 - Update QUICKSTART.md](13-update-quickstart-md.md)

---

**Last Updated:** October 26, 2025
**Status:** Ready for execution
