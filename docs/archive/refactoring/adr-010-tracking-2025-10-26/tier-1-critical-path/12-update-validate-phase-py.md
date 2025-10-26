# Task 1.4: Update validate_phase.py

**Status:** ⏸️ PENDING | **Time:** 10 minutes | **Priority:** MEDIUM

---

## Objective

Update usage examples in `scripts/automation/validate_phase.py` to show 4-digit format.

**File:** `/Users/ryanranft/nba-simulator-aws/scripts/automation/validate_phase.py`

---

## Changes Needed

### Lines 19-22: Update Usage Examples

**Current (OLD):**
```python
Usage:
    python scripts/automation/validate_phase.py 0.1
    python scripts/automation/validate_phase.py 0.1 --generate-only
    python scripts/automation/validate_phase.py 0.1 --validate-only
    python scripts/automation/validate_phase.py 0.1 --verbose
```

**New (4-DIGIT):**
```python
Usage:
    python scripts/automation/validate_phase.py 0.0001
    python scripts/automation/validate_phase.py 0.0001 --generate-only
    python scripts/automation/validate_phase.py 5.0121 --validate-only
    python scripts/automation/validate_phase.py 0.0010 --verbose
```

---

## Additional Update

Check if `_find_sub_phase_readme()` method needs updating to handle 4-digit format.

**If the method uses pattern matching for phase numbers:**
- Update regex to expect 4 digits: `[0-9]\.[0-9]{4}`

**Example:**
```python
# OLD pattern
pattern = r'(\d+)\.(\d+)_'

# NEW pattern
pattern = r'(\d+)\.(\d{4})_'
```

---

## Steps

1. Open `scripts/automation/validate_phase.py`
2. Update lines 19-22 (usage examples)
3. Search for regex patterns matching phase numbers
4. Update any patterns to expect 4 digits
5. Save and test

---

## Validation

```bash
# Check usage examples updated
grep "0\.1" scripts/automation/validate_phase.py
# Should return 0 results in usage section

# Test the script still works
python scripts/automation/validate_phase.py 0.0001 --help
```

---

## Completion Checklist

- [ ] Usage examples updated to 4-digit
- [ ] Regex patterns checked/updated
- [ ] Script tested with 4-digit input
- [ ] No errors when running

---

[Tier 1 README](README.md) | [Next: 1.5 - QUICKSTART.md](13-update-quickstart-md.md)
