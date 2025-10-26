# Task 3.2: Create CONTRIBUTING.md

**Status:** ⏸️ PENDING | **Time:** 15 minutes

---

## Objective

Create `CONTRIBUTING.md` with phase naming convention guidance.

---

## Template

```markdown
# Contributing to NBA Simulator AWS

## Phase Naming Convention (ADR-010)

We use **4-digit zero-padded sub-phase numbering**:

- Format: `N.MMMM_name` (where MMMM is 0001-9999)
- Examples: `0.0001_data_collection`, `5.0121_ab_testing`
- Rationale: See [ADR-010](docs/adr/010-four-digit-subphase-numbering.md)

### Creating New Sub-Phases

1. Find next available number in PHASE_N_INDEX.md
2. Use 4-digit format: `N.0042_my_new_feature`
3. Never use old format (0.1, 0.10) - will fail pre-commit

### Running Validation

```bash
python scripts/maintenance/validate_adr_010_compliance.py
pytest tests/test_adr_010_compliance.py -v
```

## Code Style

[Other contributing guidelines...]
```

---

[Tier 3 README](README.md)
