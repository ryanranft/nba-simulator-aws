# Task 2.1: Add Pre-Commit Hook

**Status:** ⏸️ PENDING | **Time:** 15 minutes | **Priority:** HIGH

---

## Objective

Add pre-commit hook to `.pre-commit-config.yaml` that blocks commits containing old phase numbering format.

---

## Implementation

### 1. Create validation script

**File:** `scripts/maintenance/validate_phase_numbering.sh`

```bash
#!/bin/bash
# Validates phase numbering follows 4-digit format (ADR-010)

# Check for old format patterns in docs/phases/
OLD_FORMAT=$(grep -rE "(Phase [0-9]\.[0-9]{1,3}[^0-9]|phase_[0-9]/[0-9]\.[0-9]{1,3}_)" \
  docs/phases/ tests/phases/ validators/phases/ 2>/dev/null | \
  grep -v "docs/archive/" | \
  grep -v "\.0[0-9]{4}")

if [ -n "$OLD_FORMAT" ]; then
  echo "❌ ERROR: Old phase numbering format detected (ADR-010 violation)"
  echo "Expected: 4-digit format (e.g., 0.0001, 5.0121)"
  echo "Found:"
  echo "$OLD_FORMAT"
  exit 1
fi

echo "✅ Phase numbering format validated (4-digit)"
exit 0
```

### 2. Make script executable

```bash
chmod +x scripts/maintenance/validate_phase_numbering.sh
```

### 3. Add to `.pre-commit-config.yaml`

Add this hook after existing hooks:

```yaml
  - repo: local
    hooks:
      - id: validate-phase-numbering
        name: Validate 4-digit phase numbering (ADR-010)
        entry: scripts/maintenance/validate_phase_numbering.sh
        language: script
        files: '^(docs/phases/|tests/phases/|validators/phases/)'
        pass_filenames: false
```

---

## Testing

```bash
# Test the hook
echo "Phase 0.1 test" > /tmp/test_old_format.md
git add /tmp/test_old_format.md
git commit -m "test: old format"
# Should FAIL with error message

# Clean up
git reset HEAD /tmp/test_old_format.md
rm /tmp/test_old_format.md
```

---

## Completion Checklist

- [ ] Validation script created
- [ ] Script made executable
- [ ] Hook added to `.pre-commit-config.yaml`
- [ ] Hook tested and blocks old format
- [ ] Hook allows 4-digit format through

---

[Tier 2 README](README.md) | [Template](../templates/pre-commit-hook-template.yaml)
