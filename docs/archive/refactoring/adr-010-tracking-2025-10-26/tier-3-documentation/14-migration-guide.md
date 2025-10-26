# Task 3.5: Create Migration Guide

**Status:** ⏸️ PENDING | **Time:** 15 minutes

---

## Objective

Create `docs/migrations/ADR-010-MIGRATION-GUIDE.md` for contributors on old branches.

---

## Template

```markdown
# ADR-010 Migration Guide

## For Contributors

If you have a branch created before October 2025, follow these steps:

### Update Your Branch

\`\`\`bash
# 1. Merge latest main
git checkout main && git pull
git checkout your-branch && git merge main

# 2. Update phase references
python scripts/maintenance/smart_phase_reference_cleanup.py --analyze
python scripts/maintenance/smart_phase_reference_cleanup.py --execute

# 3. Verify compliance
python scripts/maintenance/validate_adr_010_compliance.py
\`\`\`

### Common Scenarios

**New sub-phase added:**
- OLD: `docs/phases/phase_0/0.18_my_feature/`
- NEW: `docs/phases/phase_0/0.0018_my_feature/`

**Tests written:**
- OLD: `tests/phases/phase_0/test_0_18.py`
- NEW: `tests/phases/phase_0/test_0_0018.py`

### Merge Conflicts

- `PHASE_N_INDEX.md` → Accept incoming (main branch)
- Phase README files → Update your references to 4-digit
```

---

[Tier 3 README](README.md)
