# Task 2.2: Create Phase Templates

**Status:** ⏸️ PENDING | **Time:** 20 minutes

---

## Objective

Create templates for new phases/sub-phases that enforce 4-digit format.

---

## Templates to Create

### 1. `docs/templates/PHASE_INDEX_TEMPLATE.md`

```markdown
# PHASE_N_INDEX.md

**Phase:** N - [Phase Name]
**Status:** ⏸️ PENDING
**Format:** 4-digit sub-phase numbering (ADR-010)

## Sub-Phases

| ID | Sub-Phase | Status | Description |
|----|-----------|--------|-------------|
| N.0001 | [Name](phase_N/N.0001_name/) | ⏸️ PENDING | Description |
| N.0002 | [Name](phase_N/N.0002_name/) | ⏸️ PENDING | Description |

**Format:** N.MMMM (4-digit zero-padded per ADR-010)
**See:** docs/adr/010-four-digit-subphase-numbering.md
```

### 2. `docs/templates/SUB_PHASE_TEMPLATE.md`

```markdown
# Sub-Phase N.MMMM: [Name]

**Parent Phase:** [Phase N: Title](../PHASE_N_INDEX.md)
**Status:** ⏸️ PENDING
**Format:** 4-digit zero-padded (ADR-010)
**ID:** N.MMMM

## Overview

[Description]

## Implementation

[Details]

---

**See also:** [ADR-010](../../adr/010-four-digit-subphase-numbering.md)
```

---

## Completion Checklist

- [ ] PHASE_INDEX_TEMPLATE.md created
- [ ] SUB_PHASE_TEMPLATE.md created
- [ ] Templates use 4-digit format examples
- [ ] Templates reference ADR-010

---

[Tier 2 README](README.md)
