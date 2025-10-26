# Workflow #45: Documentation Organization Protocol

**Version:** 1.0
**Created:** October 11, 2025
**Purpose:** Maintain modular, context-efficient documentation as project grows
**Trigger:** When creating/updating phase files, tier files, or large documentation
**Frequency:** Every documentation creation or major update

---

## Overview

This workflow ensures documentation stays modular, navigable, and context-efficient. It prevents documentation bloat and maintains the 80/20 rule: read 20% of docs to do 80% of work.

**Core Principle:** Progressive detail levels - users read only what they need at each stage.

---

## File Size Guidelines

### Optimal Sizes

| File Type | Target Size | Max Size | Context % | Purpose |
|-----------|-------------|----------|-----------|---------|
| **PROGRESS.md** | 500-1,000 lines | 1,500 lines | 2-7% | Master index, navigation |
| **Phase README** | 400-600 lines | 800 lines | 2-4% | Phase/tier navigation index |
| **Tier/Sub-phase** | 300-800 lines | 1,200 lines | 1.5-6% | Implementation details |
| **Quick Reference** | 50-100 lines | 150 lines | 0.25-0.75% | Summary cards |
| **Workflow** | 200-400 lines | 600 lines | 1-3% | Procedures |
| **Large Reference** | 1,000-1,500 lines | 2,000 lines | 5-10% | Lazy-load with grep |

### Context Budget Limits

**Per session:**
- ✅ Session startup: <1,500 lines (7% context)
- ✅ Single task: <1,000 lines (5% context)
- ✅ Heavy work: <3,000 lines (15% context)
- ⚠️ Approaching limit: 4,000 lines (20% context)
- ❌ Too much: >4,000 lines (>20% context)

**Total context budget:** 20,000 lines (~200K tokens)

---

## When to Split a File

### Triggers for Splitting

**Automatic triggers (MUST split):**
1. File exceeds 1,500 lines (phase/tier file)
2. File exceeds 2,000 lines (any file)
3. File contains 5+ distinct sub-phases/sections
4. Reading file takes >10% of context budget

**Judgment triggers (SHOULD split):**
1. File contains multiple independent topics
2. Users rarely need entire file at once
3. File has natural breakpoints (tiers, phases, categories)
4. Updates frequently modify only specific sections

### Don't Split If

- File is reference material (grep/search usage)
- File is cohesive single topic
- Splitting would create excessive cross-references
- File is <1,000 lines and logically unified

---

## Organization Structure

### Multi-Tier Projects (Like Basketball Reference)

```
docs/phases/project_name/
├── README.md                    # Tier index (400-600 lines)
├── QUICK_REFERENCE.md           # Summary cards (50 lines × N tiers)
├── TIER_01_NAME.md             # Tier 1 details (300-800 lines)
├── TIER_02_NAME.md             # Tier 2 details
├── ...
└── TIER_NN_NAME.md             # Tier N details
```

### Single-Phase Projects

```
docs/phases/
├── PHASE_X_NAME.md             # Phase overview (400-800 lines)
├── PHASE_X_SUB_1.md            # Sub-phase details (if needed)
└── PHASE_X_SUB_2.md
```

### Large Reference Documents

```
docs/
├── LARGE_REFERENCE.md          # Keep as single file (1,000-2,000 lines)
└── README.md                   # Document index with grep instructions
```

---

## Progressive Detail Levels

### Level 1: PROGRESS.md (1-2 lines per item)

```markdown
- ⏸️ [Basketball Reference - All Basketball](docs/phases/phase_0/0.0001_basketball_reference/README.md) - 13 tiers, 234 types
  - ⏸️ Tier 1: NBA High Value (5 types, 15-20h)
  - ⏸️ Tier 10: WNBA (16 types, 15-20h)
```

### Level 2: Tier Index README (1 table row per tier)

```markdown
| Tier | Domain | Types | Records | Time | Priority | File |
|------|--------|-------|---------|------|----------|------|
| 1 | NBA High Value | 5 | 150K | 15-20h | IMMEDIATE | [TIER_01](TIER_01_NBA_HIGH_VALUE.md) |
```

### Level 3: Quick Reference Card (~50 lines per tier)

```markdown
# Tier 1 Quick Reference

**Time:** 15-20 hours
**Records:** ~150,000

## Data Types (5)
1. Adjusted Shooting
2. Per 100 Possessions
3. Schedule/Game Results
4. Rookies Stats
5. All-Rookie Teams

## Quick Start
```bash
python scripts/etl/scrape_tier1.py
```

## Full Details
See: TIER_01_NBA_HIGH_VALUE.md
```

### Level 4: Full Tier File (300-800 lines)

- Complete implementation steps
- Scraper configuration
- Testing procedures
- Troubleshooting
- Success criteria

---

## Step-by-Step: Creating Multi-Tier Documentation

### Step 1: Plan the Structure

**Before creating files:**

1. **Identify logical tiers/groupings**
   - By priority (Tier 1 = highest value)
   - By domain (NBA, WNBA, International)
   - By implementation order
   - By data type similarity

2. **Estimate file sizes**
   - Count sections × average section size
   - Aim for 300-800 lines per tier
   - If >800 lines projected, split further

3. **Create naming convention**
   - `TIER_01_DESCRIPTIVE_NAME.md`
   - `TIER_10_WNBA.md`
   - `TIER_11_12_13_MULTI_LEAGUE.md` (combined if closely related)

### Step 2: Create Directory Structure

```bash
mkdir -p docs/phases/project_name
```

### Step 3: Create Tier Index (README.md)

**Template:**

```markdown
# [Project Name] - Implementation Index

**Version:** 1.0
**Date:** [Date]
**Status:** ⏸️ PENDING / 🔄 IN PROGRESS / ✅ COMPLETE

---

## Quick Navigation

**From PROGRESS.md:**
1. Check current tier in progress
2. Click link to this index
3. Click link to specific tier file
4. Follow implementation steps

---

## Tier Summary Table

| Tier | Domain | Types | Records | Time | Priority | Status | File |
|------|--------|-------|---------|------|----------|--------|------|
| 1 | Description | N | Xk | Yh | IMMEDIATE | ⏸️ | [TIER_01](TIER_01_NAME.md) |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Total:** N types, X hours, Y records

---

## Implementation Order

**Recommended path:** Tier 1 → 2 → 3 → ...

**Parallel opportunities:** Tiers X and Y can run simultaneously

---

## Progress Tracking

- [ ] Tier 1 (0/N types)
- [ ] Tier 2 (0/N types)
- [ ] ...

---

## Context Budget

**Reading tier index:** ~500 lines (2% context)
**Reading one tier:** ~600 lines (3% context)
**Total for tier execution:** ~1,100 lines (5% context)

---

## Related Documentation

- **Complete catalog:** Link to exhaustive reference
- **Original plan:** Link to superseded docs (if any)
- **Quick reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
```

### Step 4: Create Quick Reference Cards

**One card per tier (50 lines each):**

```markdown
# Quick Reference Cards

## Tier 1: [Name]

**Status:** ⏸️ PENDING
**Time:** X hours
**Records:** Y

### Data Types (N)
1. Type 1
2. Type 2

### Quick Start
```bash
command here
```

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Full Details
[TIER_01_NAME.md](TIER_01_NAME.md)

---

## Tier 2: [Name]
...
```

### Step 5: Create Individual Tier Files

**Use tier template (see section below)**

### Step 6: Update PROGRESS.md

**Add navigation hierarchy:**

```markdown
## Phase Details

- ✅ [Phase 0: Data Collection](docs/phases/phase_0/PHASE_0_INDEX.md) - COMPLETE
  - 🔄 **[Project Name](docs/phases/phase_N/N.M_project_name/README.md)** - N tiers
    - ⏸️ [Tier 1: Name](docs/phases/phase_N/N.M_project_name/TIER_01_NAME.md) - X types, Y hours
    - ⏸️ [Tier 2: Name](docs/phases/phase_N/N.M_project_name/TIER_02_NAME.md) - X types, Y hours
```

### Step 7: Archive Superseded Documents (If Applicable)

```bash
# Move old large file
mv docs/phases/OLD_LARGE_FILE.md docs/archive/superseded/

# Update archive README
echo "- OLD_LARGE_FILE.md → Split into TIER_01-NN files (Oct 2025)" >> docs/archive/README.md
```

---

## Tier File Template

**Use this template for creating new tier files:**

```markdown
# [Phase/Project Name] - TIER [N]: [Descriptive Name]

**Phase:** [Phase Number]
**Tier:** [N]
**Status:** ⏸️ PENDING / 🔄 IN PROGRESS / ✅ COMPLETE
**Scope:** [Brief description]
**Priority:** IMMEDIATE / HIGH / MEDIUM / LOW / OPTIONAL
**Estimated Time:** X-Y hours
**Records:** ~Z
**Cost Impact:** +$X.XX/month

**📊 Context Budget:** ~[N] lines (~X% of context)
**⏱️ Read Time:** X-Y minutes
**🎯 Use When:** [When to read this file]

---

## Overview

**Purpose:** [1-2 sentences]

**What This Adds:** [Key benefits]

---

## Sub-Phases / Data Types

### Sub-Phase N.X.1: [Name]

**Coverage:** [Years, seasons, etc.]
**Records:** ~[N]
**Time:** X-Y hours

#### Data Type 1

- **URL:** [URL pattern]
- **Table ID:** [Table ID if applicable]
- **Data:** [What data this contains]
- **Value:** [Why this matters]

**Implementation Steps:**
1. Step 1
2. Step 2
3. ...

---

## Implementation Timeline

**Week 1:** [Tasks]
**Week 2:** [Tasks]

**Total:** X-Y hours over Z weeks

---

## Technical Implementation

**Scraper Configuration:**
```python
# Code example
```

**S3 Structure:**
```
s3://bucket/path/
├── subdir1/
└── subdir2/
```

---

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] ...

**Total:** N types, X records, Y hours

---

## Related Documentation

- **Tier Index:** [README.md](README.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Next Tier:** [TIER_[N+1]_NAME.md](TIER_[N+1]_NAME.md)

---

**Tier Owner:** [Team/Person]
**Last Updated:** [Date]
**Next Action:** [What to do next]
```

---

## Adding Context Budget Labels

**Add to every documentation file header:**

```markdown
**📊 Context Budget:** ~[N] lines (~X% of 20K line budget)
**⏱️ Read Time:** X-Y minutes
**🎯 Use When:** [Specific trigger]

**Prerequisites to read first:**
- File 1 (X lines, Y%)
- File 2 (X lines, Y%)
- **Total session startup:** X lines (Y% context)
```

**Calculate percentages:**
- 200 lines = 1% context
- 1,000 lines = 5% context
- 2,000 lines = 10% context
- 4,000 lines = 20% context

---

## Maintenance Rules

### When Adding New Content

**Small addition (<100 lines):**
- Add to existing tier file
- Update tier index table
- Update context budget label

**Medium addition (100-300 lines):**
- Check if tier file approaching 1,200 lines
- If yes: Split into sub-phases
- If no: Add to existing file

**Large addition (>300 lines):**
- Create new tier file
- Update tier index
- Add to PROGRESS.md
- Create quick reference card

### When Updating Content

**Always update:**
1. Tier file content
2. Tier index README (if status changed)
3. PROGRESS.md (if status changed)
4. Quick reference card (if scope changed)
5. Context budget label (if size changed significantly)

### Monthly Review

**Check each phase:**
1. Any files >1,500 lines? → Split
2. Any files with 5+ distinct sections? → Consider splitting
3. Quick reference cards accurate? → Update
4. Tier index progress tracking current? → Update
5. Context budget labels accurate? → Recalculate

---

## Context Management During Sessions

### Session Planning

**Before starting work:**

1. **Estimate context needed:**
   - PROGRESS.md: 500 lines (2%)
   - Tier index: 500 lines (2%)
   - One tier file: 600 lines (3%)
   - **Total:** 1,600 lines (8% context)

2. **Reserve buffer:**
   - Tool outputs: 2,000 lines (10%)
   - Thinking/conversation: 2,000 lines (10%)
   - **Total available for work:** 14,400 lines (72% context)

3. **If approaching 75% context:**
   - Commit current work
   - Update PROGRESS.md
   - End session
   - Start fresh session with 0% context

### Context Budget Tracking

**Monitor throughout session:**

```
Current usage: [X]/20,000 lines ([Y]% context)

Breakdown:
- PROGRESS.md: 500 lines (2%)
- Tier index: 500 lines (2%)
- Tier 1 file: 600 lines (3%)
- Tool outputs: 1,500 lines (7%)
- Total: 3,100 lines (15%)

Remaining: 16,900 lines (85%)
```

**Context warning thresholds:**
- 50% (10,000 lines): Normal, plenty of room
- 75% (15,000 lines): Commit soon, prepare to end session
- 90% (18,000 lines): Commit immediately, end session
- 100% (20,000 lines): STOP - cannot continue

---

## Examples

### Example 1: Basketball Reference Multi-Tier Project

**Structure created:**
```
docs/phases/phase_0/0.0001_basketball_reference/
├── README.md (500 lines) - Tier index
├── QUICK_REFERENCE.md (650 lines) - 13 tier cards × 50 lines
├── TIER_01_NBA_HIGH_VALUE.md (400 lines)
├── TIER_02_NBA_STRATEGIC.md (400 lines)
├── TIER_03_NBA_SPECIALIZED.md (300 lines)
├── TIER_04_NBA_PLAYER_GRANULAR.md (500 lines)
├── TIER_05_NBA_ENHANCEMENTS.md (600 lines)
├── TIER_06_NBA_AWARDS.md (500 lines)
├── TIER_07_ABA_HISTORICAL.md (400 lines)
├── TIER_08_BAA_HISTORICAL.md (300 lines)
├── TIER_09_NBA_MISC_TOOLS.md (800 lines)
├── TIER_10_WNBA.md (1,400 lines)
└── TIER_11_12_13_MULTI_LEAGUE.md (1,600 lines)
```

**Before:** 1 file × 4,800 lines = 24% context to read all
**After:** Read tier index (500 lines, 2%) + one tier (400-800 lines, 2-4%) = 4-6% context per task

**Context savings:** 18-20% (enables 3-5x more work per session)

---

### Example 2: Simple Phase (No Need to Split)

**PHASE_1_DATA_QUALITY.md (800 lines)**

- Single cohesive topic
- All sections related
- Users typically read entire file
- Below 1,200 line threshold

**Decision:** Keep as single file, no splitting needed

---

### Example 3: Large Reference Document

**TROUBLESHOOTING.md (1,025 lines)**

- Reference material (grep/search usage)
- Users rarely read entire file
- Cohesive topic

**Decision:** Keep as single file, add grep instructions to README.md:

```markdown
## Large Reference Documents

**TROUBLESHOOTING.md** (1,025 lines)
- **Do not read entire file** - use grep
- Example: `grep -A 10 "error message" docs/TROUBLESHOOTING.md`
```

---

## Integration with Existing Workflows

### Related Workflows

- **Workflow #1:** Session Start - Read PROGRESS.md → Tier index → Specific tier
- **Workflow #14:** Session End - Update tier file, tier index, PROGRESS.md
- **Workflow #44:** Reference Path Validator - Validate links after restructuring

### CLAUDE.md Integration

Add to CLAUDE.md "Common Pitfalls to Avoid" section:

```markdown
**Documentation organization mistakes:**
1. ❌ Creating files >1,500 lines → ✅ Split into multiple files
2. ❌ Reading entire large file → ✅ Read tier index + specific tier only
3. ❌ Not updating context budget labels → ✅ Update when file size changes
```

---

## Checklist: Creating New Multi-Tier Documentation

**Planning:**
- [ ] Identified logical tiers/groupings
- [ ] Estimated file sizes (target 300-800 lines per tier)
- [ ] Created naming convention

**Structure:**
- [ ] Created project directory (`docs/phases/project_name/`)
- [ ] Created tier index README.md (400-600 lines)
- [ ] Created quick reference cards (50 lines per tier)
- [ ] Created individual tier files (300-800 lines each)

**Integration:**
- [ ] Updated PROGRESS.md navigation hierarchy
- [ ] Added context budget labels to all files
- [ ] Moved superseded docs to archive (if applicable)
- [ ] Updated archive README with superseded file notes

**Verification:**
- [ ] All links working (run validate_references.sh)
- [ ] File sizes within guidelines
- [ ] Context budget calculations accurate
- [ ] Test navigation from PROGRESS.md → Tier index → Tier file

---

## Troubleshooting

### Problem: Tier file too large (>1,200 lines)

**Solution:** Split into sub-phases

```
TIER_05_NBA_ENHANCEMENTS.md (1,800 lines) →

TIER_05_NBA_ENHANCEMENTS_README.md (200 lines)
TIER_05A_SALARIES.md (600 lines)
TIER_05B_SHOOTING_DETAIL.md (500 lines)
TIER_05C_PBP_DETAIL.md (500 lines)
```

### Problem: Too many small files (>20 tier files)

**Solution:** Combine related tiers

```
TIER_11_G_LEAGUE.md (300 lines)
TIER_12_INTERNATIONAL.md (400 lines)
TIER_13_COLLEGE.md (400 lines)

→ TIER_11_12_13_MULTI_LEAGUE.md (1,200 lines combined)
```

### Problem: Unclear which file to read

**Solution:** Improve tier index README.md with "Use When" column:

```markdown
| Tier | Use When | File |
|------|----------|------|
| 1 | Starting NBA high-value collection | TIER_01 |
| 10 | Starting WNBA collection | TIER_10 |
```

---

## Success Metrics

**Good documentation organization achieves:**

✅ Session startup: <1,500 lines (<7% context)
✅ Single task: <1,000 lines per tier (<5% context)
✅ File sizes: 90%+ files <1,200 lines
✅ Navigation: 3 clicks from PROGRESS.md to implementation details
✅ Context savings: 15-20% vs. monolithic files

---

## Related Documentation

- **CLAUDE.md:** Master instructions for Claude
- **CONTEXT_MANAGEMENT_GUIDE.md:** Strategies for context efficiency
- **Workflow #1:** Session Start (uses this protocol)
- **Workflow #14:** Session End (updates using this protocol)
- **Workflow #44:** Reference Path Validator

---

**Workflow Owner:** Documentation Team
**Last Updated:** October 11, 2025
**Status:** Active
**Next Review:** November 2025 (monthly maintenance check)