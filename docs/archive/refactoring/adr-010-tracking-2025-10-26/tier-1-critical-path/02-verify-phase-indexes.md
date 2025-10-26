# Task 1.2: Verify Phase Indexes

**Status:** ⏸️ PENDING | **Time:** 5 minutes | **Priority:** HIGH

---

## Objective

Verify all 6 `PHASE_N_INDEX.md` files use 4-digit format in their sub-phase tables.

---

## Files to Check

```
docs/phases/PHASE_0_INDEX.md
docs/phases/PHASE_1_INDEX.md
docs/phases/PHASE_2_INDEX.md
docs/phases/PHASE_3_INDEX.md
docs/phases/PHASE_4_INDEX.md
docs/phases/PHASE_5_INDEX.md
```

---

## Steps

### 1. Check each phase index for old format

```bash
for file in docs/phases/PHASE_*_INDEX.md; do
  echo "=== $file ==="
  grep -E "^\| [0-9]\.[0-9]{1,3} " "$file" | grep -v "\.[0-9]{4}"
done
```

**Expected:** No output (all use 4-digit format)

### 2. If old format found, update the table

**Old format example:**
```markdown
| 0.1 | [Name](phase_0/0.1_name/) | Status | Description |
```

**New format:**
```markdown
| 0.0001 | [Name](phase_0/0.0001_name/) | Status | Description |
```

### 3. Update directory paths in links

Ensure all links use 4-digit format:
- `phase_0/0.1_name/` → `phase_0/0.0001_name/`
- `phase_5/5.19_name/` → `phase_5/5.0019_name/`

---

## Validation

```bash
# Should return 0 results (all updated):
grep -h "| [0-9]\.[0-9] " docs/phases/PHASE_*_INDEX.md | grep -v "\.[0-9]{4}"
```

---

## Completion Checklist

- [ ] All 6 phase indexes checked
- [ ] All sub-phase IDs use 4-digit format
- [ ] All directory links updated
- [ ] Validation command returns 0 results

---

[Tier 1 README](README.md) | [Next: 1.3 - SQL Migrations](11-update-sql-migrations.md)
