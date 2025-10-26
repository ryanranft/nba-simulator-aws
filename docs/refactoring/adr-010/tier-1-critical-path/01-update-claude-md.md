# Task 1.1: Update CLAUDE.md

**Status:** ⏸️ PENDING
**Priority:** CRITICAL
**Estimated Time:** 10 minutes
**Dependencies:** None

---

## Context

CLAUDE.md is the **primary guidance document** for Claude Code when working in this repository. It's read at the start of every session and contains core instructions, examples, and conventions.

**Problem:** CLAUDE.md currently uses old 2-digit format in:
- Line 67: Sub-phase naming format
- Lines 94-99: Recent power directories examples
- Missing documentation of 4-digit format
- No reference to ADR-010

**Impact:** HIGH - This file guides all AI-assisted development

---

## Current State

**File:** `/Users/ryanranft/nba-simulator-aws/CLAUDE.md`

**Problematic sections:**
1. Line 67: `**Sub-phase naming:** N.M_name.md OR N.M_name/`
2. Lines 94-99: Examples use `0.1_`, `0.4_`, `5.1_`
3. No mention of "4-digit", "ADR-010", or rationale

---

## Desired State

After completion, CLAUDE.md should:
✅ Document 4-digit format explicitly
✅ Update all examples to use 4-digit format
✅ Reference ADR-010
✅ Explain why 4-digit format was chosen

---

## Step-by-Step Instructions

### Step 1: Update Line 67 (Sub-phase Naming)

**Find:**
```markdown
**Sub-phase naming:** `N.M_name.md` OR `N.M_name/` (e.g., `0.0_initial_data_collection.md`, `1.1_multi_source_integration.md`)
```

**Replace with:**
```markdown
**Sub-phase naming:** `N.MMMM_name.md` OR `N.MMMM_name/` (4-digit zero-padded format per ADR-010)

Examples:
- `0.0001_initial_data_collection.md`
- `1.0001_multi_source_integration.md`
- `5.0121_implement_ab_testing/`

**Format:** N.MMMM where MMMM is 0001-9999 (4 digits, zero-padded)
```

### Step 2: Add Format Details After Line 67

**Insert new section:**
```markdown

**Format Details (ADR-010):**
- **4-digit zero-padded:** Phase 0 uses 0.0001-0.0099, Phase 5 uses 5.0001-5.9999
- **Filesystem sort matches logical sort:** No natural sort needed
- **Supports up to 9,999 sub-phases per phase**
- **Rationale:** See `docs/adr/010-four-digit-subphase-numbering.md`
```

### Step 3: Update Lines 94-99 (Recent Power Directories)

**Find:**
```markdown
**Recent Power Directories (October 2025):**
- `phase_0/0.1_basketball_reference/` (13-tier structure, 234 data types)
- `phase_0/0.4_security_implementation/` (13 security variations)
- `phase_0/0.5_data_extraction/` (structured data output)
- `phase_5/5.1_feature_engineering/` (rec_11 - 80+ temporal features)
- `phase_5/5.2_model_versioning/` (ml_systems_1 - MLflow integration)
- `phase_5/5.19_drift_detection/` (ml_systems_2 - data drift detection)
- `phase_5/5.20_panel_data/` (rec_22 - temporal panel data system)
```

**Replace with:**
```markdown
**Recent Power Directories (October 2025):**
- `phase_0/0.0001_basketball_reference/` (13-tier structure, 234 data types)
- `phase_0/0.0004_security_implementation/` (13 security variations)
- `phase_0/0.0005_data_extraction/` (structured data output)
- `phase_5/5.0001_feature_engineering/` (rec_11 - 80+ temporal features)
- `phase_5/5.0002_model_versioning/` (ml_systems_1 - MLflow integration)
- `phase_5/5.0019_drift_detection/` (ml_systems_2 - data drift detection)
- `phase_5/5.0020_panel_data/` (rec_22 - temporal panel data system)
```

### Step 4: Verify No Other Old Format References

**Search for potential old format:**
```bash
grep -n "Phase [0-9]\.[0-9]" CLAUDE.md
grep -n "phase_[0-9]/[0-9]\.[0-9]" CLAUDE.md
```

**Expected:** No results (all updated to 4-digit)

### Step 5: Validation

**Manual check:**
1. Read updated sections to ensure clarity
2. Verify examples are correct
3. Ensure formatting is consistent

**Automated check:**
```bash
# Should return 0 results
grep "0\.1_\|0\.4_\|0\.5_\|5\.1_\|5\.2_\|5\.19_\|5\.20_" CLAUDE.md
```

---

## Expected Changes

**Lines modified:** ~15 lines
**New lines added:** ~8 lines
**Files affected:** 1 (CLAUDE.md)

**Before:**
- Sub-phase format: N.M (variable length)
- Examples: 0.1, 0.4, 5.1

**After:**
- Sub-phase format: N.MMMM (4-digit fixed length)
- Examples: 0.0001, 0.0004, 5.0001
- Clear rationale and reference to ADR-010

---

## Validation Checklist

Before marking complete:

- [ ] Line 67 updated to show 4-digit format
- [ ] Format details added after line 67
- [ ] All power directory examples updated (lines 94-99)
- [ ] No old format references remain
- [ ] ADR-010 referenced
- [ ] File still reads naturally
- [ ] No markdown formatting errors

**Final validation command:**
```bash
# This should return NOTHING:
grep -E "(0\.[1-9]_|5\.[1-9]_|phase_0/0\.[1-9])" CLAUDE.md | grep -v "0\.0[0-9][0-9][0-9]"
```

---

## Common Issues

### Issue: Unsure about exact format
**Solution:** Use `N.MMMM` where MMMM is always 4 digits (0001, 0010, 0121, etc.)

### Issue: Breaking markdown formatting
**Solution:** Keep existing markdown structure, only change numbers

### Issue: Missing a reference
**Solution:** Use grep commands above to find all instances

---

## Time Breakdown

- **Research:** 2 minutes (read current CLAUDE.md)
- **Execution:** 5 minutes (make changes)
- **Validation:** 3 minutes (test and verify)
- **Total:** 10 minutes

---

## After Completion

1. ✅ Mark task as COMPLETED
2. ✅ Update `01-COMPLETION-CHECKLIST.md`
3. ✅ Update `00-MASTER-TRACKER.md`
4. ✅ Move to next task (1.2 or 1.3)

---

## Links

- [Tier 1 README](README.md)
- [Master Tracker](../00-MASTER-TRACKER.md)
- [ADR-010](../../../adr/010-four-digit-subphase-numbering.md)
- [Next Task: 1.2 - Verify Phase Indexes](02-verify-phase-indexes.md)

---

**Last Updated:** October 26, 2025
