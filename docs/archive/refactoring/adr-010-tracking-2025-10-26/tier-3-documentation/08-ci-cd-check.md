# Task 3.3: Add CI/CD Check

**Status:** ⏸️ PENDING | **Time:** 10 minutes

---

## Objective

Add GitHub Actions workflow to validate phase numbering in PRs.

---

## Implementation

**File:** `.github/workflows/phase-format-check.yml`

```yaml
name: Validate Phase Numbering

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate 4-digit format (ADR-010)
        run: bash scripts/maintenance/validate_phase_numbering.sh
```

**Note:** Only create if using GitHub Actions.

---

[Tier 3 README](README.md)
