# Task 4.2: Review Session Manager

**Status:** ⏸️ PENDING | **Time:** 5 minutes

---

## Objective

Verify `scripts/shell/session_manager.sh` doesn't have hardcoded phase patterns.

---

## Steps

### 1. Review script for hardcoded patterns

```bash
grep -n "0\.[0-9]" scripts/shell/session_manager.sh
grep -n "phase_[0-9]/[0-9]\.[0-9]" scripts/shell/session_manager.sh
```

### 2. Check if phase discovery is dynamic

**Good (dynamic):**
```bash
# Discovers phases automatically
find docs/phases/phase_*/ -name "*.md"
```

**Bad (hardcoded):**
```bash
# Hardcoded phase numbers
if [ "$phase" == "0.1" ]; then
```

### 3. If hardcoded patterns found

Update to use 4-digit format OR make dynamic.

---

## Validation

- [ ] No hardcoded old format patterns
- [ ] Phase discovery is dynamic
- [ ] Script still works correctly

---

[Tier 4 README](README.md)
