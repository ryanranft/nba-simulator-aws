# Task 1.3: Update SQL Migration Comments

**Status:** ⏸️ PENDING | **Time:** 15 minutes | **Priority:** HIGH

---

## Objective

Update header comments in ~15 SQL migration files to use 4-digit phase numbering.

**IMPORTANT:** Only update comments (lines starting with `--`), never SQL code.

---

## Files to Update

Located in: `scripts/db/migrations/`

**Known files with old format:**
- `0_10_schema.sql` - Comment says "Phase 0.10"
- `0_10_temporal_views.sql`
- `0_11_schema.sql` - Comment says "Phase 0.11"
- Plus ~12 more

---

## Steps

### 1. Find all migrations with old format

```bash
grep -l "Phase [0-9]\.[0-9]" scripts/db/migrations/*.sql
```

### 2. Update each file's header comment

**Old format:**
```sql
-- ============================================================================
-- Phase 0.10: PostgreSQL JSONB Storage Schema
-- ============================================================================
```

**New format:**
```sql
-- ============================================================================
-- Phase 0.0010: PostgreSQL JSONB Storage Schema
-- ============================================================================
```

### 3. Pattern to search/replace

**Search for:** `-- Phase 0.10:`
**Replace with:** `-- Phase 0.0010:`

**Search for:** `-- Phase 0.11:`
**Replace with:** `-- Phase 0.0011:`

(Repeat for all files)

### 4. Validate SQL syntax unchanged

```bash
# Verify only comments changed
git diff scripts/db/migrations/*.sql
```

---

## Automation Option

```bash
# For each file, update the comment
for file in scripts/db/migrations/*.sql; do
  # Only update comments, not SQL code
  sed -i.bak 's/-- Phase 0\.\([0-9]\{1,2\}\):/-- Phase 0.00\1:/g' "$file"
  sed -i.bak 's/-- Phase \([1-9]\)\.\([0-9]\{1,2\}\):/-- Phase \1.00\2:/g' "$file"
done
```

**Warning:** Test on one file first! Verify it works correctly.

---

## Validation

```bash
# Should return 0 results:
grep "-- Phase [0-9]\.[0-9]:" scripts/db/migrations/*.sql | grep -v "\.0[0-9][0-9][0-9]"

# Verify no SQL code changed (only comments):
git diff scripts/db/migrations/ | grep "^-CREATE\|^+CREATE"
# Should return nothing (no SQL statements changed)
```

---

## Completion Checklist

- [ ] All migration files identified
- [ ] All header comments updated
- [ ] Only comments changed (no SQL code)
- [ ] Validation shows no old format
- [ ] Git diff verified

---

[Tier 1 README](README.md) | [Next: 1.4 - validate_phase.py](12-update-validate-phase-py.md)
