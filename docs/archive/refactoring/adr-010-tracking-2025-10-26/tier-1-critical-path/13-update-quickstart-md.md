# Task 1.5: Update QUICKSTART.md

**Status:** ⏸️ PENDING | **Time:** 5 minutes | **Priority:** MEDIUM

---

## Objective

Update phase references in QUICKSTART.md to use 4-digit format.

**File:** `/Users/ryanranft/nba-simulator-aws/QUICKSTART.md`

---

## Known Issues

**Line 62:**
```markdown
**Phase Documentation:** [Phase 0.9: ADCE](docs/phases/phase_0/0.9_autonomous_data_collection/README.md)
```

**Should be:**
```markdown
**Phase Documentation:** [Phase 0.0009: ADCE](docs/phases/phase_0/0.0009_autonomous_data_collection/README.md)
```

---

## Steps

### 1. Find all old format references

```bash
grep -n "Phase [0-9]\.[0-9]" QUICKSTART.md
grep -n "phase_[0-9]/[0-9]\.[0-9]" QUICKSTART.md
```

### 2. Update each reference

Pattern: `Phase X.Y` → `Phase X.000Y`
Pattern: `phase_X/X.Y_` → `phase_X/X.000Y_`

### 3. Verify links work

After updating, verify the file paths exist:
```bash
# Test link from line 62
ls -la docs/phases/phase_0/0.0009_autonomous_data_collection/README.md
```

---

## Validation

```bash
# Should return 0 results:
grep "Phase 0\.[0-9]" QUICKSTART.md | grep -v "0\.0[0-9][0-9][0-9]"
```

---

## Completion Checklist

- [ ] All phase references updated
- [ ] All file paths verified to exist
- [ ] No broken links
- [ ] Validation passed

---

[Tier 1 README](README.md) | [Completion Checklist](../01-COMPLETION-CHECKLIST.md)
