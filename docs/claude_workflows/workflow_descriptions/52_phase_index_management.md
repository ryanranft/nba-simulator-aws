# Workflow #52: Phase Index Management

**Version:** 1.0 (SUPERSEDED by Workflow #58)
**Created:** October 11, 2025
**Status:** ⚠️ **DEPRECATED** - See [Workflow #58: Phase Completion & Validation](58_phase_completion_validation.md)
**Purpose:** Manage phase index files and sub-phase organization
**Trigger:** When creating/updating phases or sub-phases
**Frequency:** As needed during phase work

> **⚠️ DEPRECATION NOTICE (October 23, 2025)**
>
> This workflow has been consolidated into **[Workflow #58: Phase Completion & Validation](58_phase_completion_validation.md)**.
>
> **Why:** Workflow #58 provides a unified end-to-end process that includes:
> - Test & validator generation (the missing piece)
> - Test & validator organization (Workflow #53)
> - Phase index management (this workflow - Workflow #52)
> - README alignment (Workflow #57)
> - DIMS integration (Workflow #56)
>
> **What to do:** Use Workflow #58 instead. This file is kept for reference only.
>
> **Phase index management is now:** Phase 7 of Workflow #58

---

## Overview

This workflow ensures consistent management of the phase index system implemented in October 2025. It provides guidelines for creating, updating, and maintaining the 4-level documentation hierarchy.

**4-Level Hierarchy:**
1. **PROGRESS.md** (~390 lines) - Master index, high-level status
2. **PHASE_N_INDEX.md** (~150 lines) - Phase overview + sub-phase table
3. **phase_N/N.M_name.md** (300-800 lines) - Sub-phase implementation details
4. **Workflows** (200-400 lines) - Specific procedures

---

## When to Use This Workflow

**Use this workflow when:**
- Creating a new phase (PHASE_N_INDEX.md)
- Adding a new sub-phase to an existing phase
- Updating sub-phase status
- Reorganizing sub-phases within a phase
- Splitting a large sub-phase into multiple sub-phases
- Archiving completed sub-phases

**Don't use for:**
- Minor content updates within existing sub-phases (just edit the file)
- Workflow updates (use Workflow #45 instead)
- PROGRESS.md master index updates (update directly)

---

## Phase Index Structure

### Directory Structure

```
docs/phases/
├── PHASE_0_INDEX.md              # Phase 0 overview
├── phase_0/                      # Phase 0 subdirectory
│   ├── 0.0_initial_data_collection.md
│   └── 0.1_basketball_reference/
│       ├── README.md             # Tier index
│       ├── TIER_01_NBA_HIGH_VALUE.md
│       └── [other tiers...]
├── PHASE_1_INDEX.md              # Phase 1 overview
├── phase_1/                      # Phase 1 subdirectory
│   ├── 1.0_data_quality_checks.md
│   └── 1.1_multi_source_integration.md
├── PHASE_2_INDEX.md through PHASE_7_INDEX.md
└── phase_2/ through phase_7/     # Corresponding subdirectories
```

### Naming Conventions

**Phase index files:**
- Format: `PHASE_N_INDEX.md` (where N = 0-7)
- Location: `docs/phases/`
- Size: ~150 lines

**Phase subdirectories:**
- Format: `phase_N/` (where N = 0-7)
- Location: `docs/phases/`

**Sub-phase files:**
- Format: `N.M_name.md` (e.g., `1.0_data_quality_checks.md`)
- Location: `docs/phases/phase_N/`
- Size: 300-800 lines (target), max 1,200 lines
- N = phase number (0-7)
- M = sub-phase number (0, 1, 2, ...)
- name = descriptive_snake_case

**Special structures (multi-tier projects):**
- Format: `N.M_project_name/` subdirectory
- Contains: README.md (tier index) + individual tier files
- Example: `phase_0/0.1_basketball_reference/`

---

## Step-by-Step: Creating a New Phase

### Step 1: Create Phase Index File

**Template for PHASE_N_INDEX.md:**

```markdown
# Phase N: [Phase Name]

**Status:** ⏸️ PENDING / 🔄 IN PROGRESS / ✅ COMPLETE
**Priority:** IMMEDIATE / HIGH / MEDIUM / LOW / OPTIONAL
**Prerequisites:** Phase 0-[N-1] complete
**Estimated Time:** X-Y hours
**Cost Impact:** $X-Y/month
**Started:** Not yet started / YYYY-MM-DD
**Completion:** Not yet complete / YYYY-MM-DD

---

## Overview

[Brief description of what this phase delivers]

**This phase delivers:**
- Feature 1
- Feature 2
- Feature 3

**Why [phase name] matters:**
- Benefit 1
- Benefit 2
- Benefit 3

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | File |
|-----------|------|--------|------|------|
| **N.0** | [Sub-phase name] | ⏸️ PENDING | X-Yh | [N.0_name.md](phase_N/N.0_name.md) |
| **N.1** | [Sub-phase name] | ⏸️ PENDING | X-Yh | [N.1_name.md](phase_N/N.1_name.md) |

---

## Sub-Phase N.0: [Name]

**Status:** ⏸️ PENDING (not yet started)

**What this sub-phase includes:**
- Task 1
- Task 2
- Task 3

**See:** [Sub-Phase N.0 Details](phase_N/N.0_name.md)

---

## Success Criteria

### Sub-Phase N.0
- [ ] Criterion 1
- [ ] Criterion 2

### Sub-Phase N.1
- [ ] Criterion 1
- [ ] Criterion 2

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| Resource 1 | Config | $X/mo | Notes |
| **Total Phase Cost** | | **$X-Y/month** | Summary |

---

## Prerequisites

**Before starting Phase N:**
- [x] Phase 0-[N-1] complete
- [ ] Prerequisite 1
- [ ] Prerequisite 2

---

## Key Workflows

**For Sub-Phase N.0:**
- Workflow #X: [Name]
- Workflow #Y: [Name]

---

## Next Steps

**After Phase N complete:**
- ✅ [Phase name] operational
- → Proceed to [Phase N+1: Name](PHASE_[N+1]_INDEX.md)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** [Phase [N-1]: Name](PHASE_[N-1]_INDEX.md)
**Next Phase:** [Phase [N+1]: Name](PHASE_[N+1]_INDEX.md)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

---

**Last Updated:** YYYY-MM-DD
**Phase Owner:** [Team/Person]
**Total Sub-Phases:** [N]
**Status:** [% complete] ([M] of [N] sub-phases done)
```

### Step 2: Create Phase Subdirectory

```bash
mkdir -p docs/phases/phase_N
```

### Step 3: Create Sub-Phase Files

For each sub-phase, create a file using the naming convention:

```bash
touch docs/phases/phase_N/N.0_name.md
touch docs/phases/phase_N/N.1_name.md
```

Use the sub-phase template (see section below).

### Step 4: Update PROGRESS.md

Add phase to master index:

```markdown
- ⏸️ [Phase N: Name](docs/phases/PHASE_N_INDEX.md) - **PENDING**
  - ⏸️ [N.0 Name](docs/phases/phase_N/N.0_name.md) - Description
  - ⏸️ [N.1 Name](docs/phases/phase_N/N.1_name.md) - Description
```

---

## Step-by-Step: Adding a New Sub-Phase

### Step 1: Create Sub-Phase File

```bash
# Determine next sub-phase number (M)
# If phase has 0.0 and 0.1, next is 0.2

touch docs/phases/phase_N/N.M_name.md
```

### Step 2: Update Phase Index

Add row to sub-phase table in PHASE_N_INDEX.md:

```markdown
| Sub-Phase | Name | Status | Time | File |
|-----------|------|--------|------|------|
| **N.M** | [Sub-phase name] | ⏸️ PENDING | X-Yh | [N.M_name.md](phase_N/N.M_name.md) |
```

Add new section with overview:

```markdown
## Sub-Phase N.M: [Name]

**Status:** ⏸️ PENDING (not yet started)

**What this sub-phase includes:**
- Task 1
- Task 2

**See:** [Sub-Phase N.M Details](phase_N/N.M_name.md)
```

### Step 3: Add to Success Criteria

```markdown
### Sub-Phase N.M
- [ ] Criterion 1
- [ ] Criterion 2
```

### Step 4: Update PROGRESS.md

Add to phase's sub-phase list:

```markdown
- ⏸️ [Phase N: Name](docs/phases/PHASE_N_INDEX.md)
  - ...
  - ⏸️ [N.M Name](docs/phases/phase_N/N.M_name.md) - Description
```

---

## Tests & Validators for Phases

**New as of October 2025:** Tests and validators are now organized separately from phase documentation.

###Where to Put Tests & Validators

**Tests:** `tests/phases/phase_N/test_N_M_name.py`
- Example: `tests/phases/phase_0/test_0_1_initial_data_collection.py`
- Run via: `pytest tests/phases/phase_N/test_N_M_name.py -v`

**Validators:** `validators/phases/phase_N/validate_N_M_feature.py`
- Example: `validators/phases/phase_0/validate_0_1_s3_bucket_config.py`
- Run via: `python validators/phases/phase_N/validate_N_M_feature.py`

**Documentation:** `docs/phases/phase_N/N.M_name/README.md`
- Contains ONLY documentation (no .py files)
- References tests/validators with example commands

**See Workflow #53 (Phase Test & Validator Organization) for complete guidance.**

---

## Sub-Phase File Template

**Use this template for all sub-phase files:**

```markdown
# Phase N - Sub-Phase N.M: [Name]

**Phase:** [Phase Number]
**Sub-Phase:** N.M
**Status:** ⏸️ PENDING / 🔄 IN PROGRESS / ✅ COMPLETE
**Priority:** IMMEDIATE / HIGH / MEDIUM / LOW
**Estimated Time:** X-Y hours
**Cost Impact:** +$X.XX/month
**Started:** Not yet started / YYYY-MM-DD
**Completed:** Not yet complete / YYYY-MM-DD

**📊 Context Budget:** ~[N] lines (~X% of context)
**⏱️ Read Time:** X-Y minutes
**🎯 Use When:** [When to read this file]

---

## Overview

**Purpose:** [1-2 sentences]

**What This Adds:** [Key benefits]

**Deliverables:**
1. Deliverable 1
2. Deliverable 2
3. Deliverable 3

---

## Prerequisites

**Before starting this sub-phase:**
- [ ] Phase N.0 through N.[M-1] complete (if applicable)
- [ ] Prerequisite 1
- [ ] Prerequisite 2

---

## Implementation Steps

### Step 1: [Name]

**What to do:**
1. Action 1
2. Action 2

**Commands:**
```bash
# Commands here
```

**Expected outcome:** [What success looks like]

### Step 2: [Name]

[Repeat pattern]

---

## Success Criteria

- [ ] Criterion 1 complete
- [ ] Criterion 2 complete
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Status updated in phase index

**Total:** [N] criteria

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| Resource 1 | Config | $X/mo | Notes |
| **Total Sub-Phase Cost** | | **$X/month** | Summary |

---

## Troubleshooting

**Common issues:**

1. **Issue description**
   - Solution: [Fix]

2. **Issue description**
   - Solution: [Fix]

---

## Key Workflows

**For this sub-phase:**
- Workflow #X: [Name] - [When to use]
- Workflow #Y: [Name] - [When to use]

---

## Related Documentation

- **Phase Index:** [PHASE_N_INDEX.md](../PHASE_N_INDEX.md)
- **Previous Sub-Phase:** [N.[M-1]_name.md](N.[M-1]_name.md)
- **Next Sub-Phase:** [N.[M+1]_name.md](N.[M+1]_name.md)
- **Workflows:** [CLAUDE_WORKFLOW_ORDER.md](../../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

---

**Sub-Phase Owner:** [Team/Person]
**Last Updated:** YYYY-MM-DD
**Next Action:** [What to do next]
```

---

## Status Tracking Protocol

### Status Emojis

**Use these consistently:**
- ⏸️ **PENDING** - Not yet started
- 🔄 **IN PROGRESS** - Currently working on
- ✅ **COMPLETE** - Finished and verified
- 🔧 **BLOCKED** - Waiting on dependency
- ⚠️ **ISSUES** - Has problems, needs attention

### Update Hierarchy

**When a sub-phase status changes:**

1. **Update sub-phase file** (phase_N/N.M_name.md) - Change status at top
2. **Update phase index** (PHASE_N_INDEX.md) - Update sub-phase table + section
3. **Update PROGRESS.md** - Only when full phase status changes

**Example:**
```markdown
# Sub-phase file (N.M_name.md)
**Status:** ⏸️ PENDING → 🔄 IN PROGRESS

# Phase index (PHASE_N_INDEX.md)
| **N.M** | Name | 🔄 IN PROGRESS | Xh | [file] |

## Sub-Phase N.M: Name
**Status:** 🔄 IN PROGRESS (started YYYY-MM-DD)

# PROGRESS.md (only if full phase changes)
- 🔄 [Phase N: Name](docs/phases/PHASE_N_INDEX.md) - **IN PROGRESS**
```

### Completion Checklist

**Before marking sub-phase complete:**
- [ ] All implementation steps completed
- [ ] All success criteria met
- [ ] Tests passing (if applicable)
- [ ] Documentation updated
- [ ] Cost tracking updated
- [ ] Status updated in all 3 locations

---

## Context Budget Guidelines

### Target File Sizes

| File Type | Target Size | Max Size | Context % |
|-----------|-------------|----------|-----------|
| Phase index | 150 lines | 200 lines | 0.75-1% |
| Sub-phase | 300-800 lines | 1,200 lines | 1.5-6% |
| Multi-tier README | 300 lines | 500 lines | 1.5-2.5% |
| Tier file | 300-800 lines | 1,200 lines | 1.5-6% |

### Context Budget Per Session

**Reading pattern:**
- PROGRESS.md: 390 lines (1.95%)
- PHASE_N_INDEX.md: 150 lines (0.75%)
- One sub-phase: 300-800 lines (1.5-4%)
- Workflows (2-3): 400-1,200 lines (2-6%)
- **Total: 1,240-2,540 lines (6.2-12.7% context)**

**Leave buffer:** 10-15% for tool outputs, thinking, conversation

### When to Split a Sub-Phase

**Split if:**
- Sub-phase file exceeds 1,200 lines
- Contains 5+ distinct sections
- Takes >20 minutes to read
- Contains independent topics that could stand alone

**How to split:**
```
N.M_large_subphase.md (1,500 lines) →

N.M_subphase_index.md (200 lines) - Overview + links
N.M.0_topic_1.md (500 lines)
N.M.1_topic_2.md (600 lines)
N.M.2_topic_3.md (400 lines)
```

---

## Maintenance Rules

### Weekly

- [ ] Review all 🔄 IN PROGRESS sub-phases - still active?
- [ ] Update any stale "Last Updated" dates
- [ ] Check for broken links in phase indexes

### Monthly

- [ ] Review all phase indexes for accuracy
- [ ] Check file sizes - any approaching 1,200 lines?
- [ ] Update context budget labels if sizes changed
- [ ] Verify navigation links work end-to-end

### When Adding Content

**Small addition (<100 lines):**
- Add to existing sub-phase file
- Update context budget label

**Medium addition (100-300 lines):**
- Check if sub-phase approaching 1,200 lines
- If yes: Split into multiple sub-phases
- If no: Add to existing file

**Large addition (>300 lines):**
- Create new sub-phase
- Update phase index
- Add to PROGRESS.md
- Update context budget

---

## Troubleshooting

### Issue: Phase index getting too large (>200 lines)

**Cause:** Too many sub-phases or too much detail in overview

**Solution:**
- Move detailed content to sub-phase files
- Use progressive detail levels
- Consider if sub-phases can be combined

### Issue: Unclear which sub-phase to work on

**Cause:** Poor organization or naming

**Solution:**
- Add "Use When" column to sub-phase table
- Improve sub-phase names to be more descriptive
- Add implementation order section

### Issue: Broken links after reorganization

**Cause:** Paths not updated

**Solution:**
```bash
# Find broken links
grep -r "docs/phases/PHASE_N_[A-Z]" . --include="*.md"

# Update to new paths
# Use Edit tool for important files
```

---

## Related Workflows

- **Workflow #1:** Session Start - Navigate using phase indexes
- **Workflow #14:** Session End - Update phase/sub-phase status
- **Workflow #45:** Documentation Organization - File size management
- **Workflow #52:** This workflow - Phase index management

---

## Success Metrics

**Good phase index system achieves:**
- ✅ Phase indexes: 150-200 lines (within target)
- ✅ Sub-phases: 300-800 lines (90%+ in range)
- ✅ Navigation: 3 clicks from PROGRESS.md to implementation
- ✅ Context efficiency: Read only what's needed (<15% per session)
- ✅ Consistent naming: All files follow N.M_name.md convention

---

**Workflow Owner:** Documentation Team
**Last Updated:** October 11, 2025
**Status:** Active
**Next Review:** November 2025

---

*For questions about phase organization, see CLAUDE.md or this workflow.*
