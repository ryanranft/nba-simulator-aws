# Task 4.1: Create Auto-Generators

**Status:** ⏸️ PENDING | **Time:** 25 minutes

---

## Objective

Create scripts to auto-generate new phases/sub-phases with correct 4-digit format.

---

## Scripts to Create

### 1. `scripts/generators/create_new_phase.sh`

```bash
#!/bin/bash
# Usage: ./scripts/generators/create_new_phase.sh 6 "Model Deployment"

PHASE_NUM=$1
PHASE_NAME=$2

# Create PHASE_N_INDEX.md with 4-digit template
# Create phase_N/ directory
# Create first sub-phase: N.0001_initial_setup/
```

### 2. `scripts/generators/create_new_subphase.sh`

```bash
#!/bin/bash
# Usage: ./scripts/generators/create_new_subphase.sh 5 "optimize_inference"

PHASE_NUM=$1
SUB_PHASE_NAME=$2

# Find next available 4-digit number in PHASE_N_INDEX.md
# Create N.MMMM_name/ directory with README.md
# Update PHASE_N_INDEX.md table
```

---

## Benefits

- Eliminates manual formatting errors
- Ensures 4-digit format always used
- Auto-increments sub-phase numbers

---

[Tier 4 README](README.md)
