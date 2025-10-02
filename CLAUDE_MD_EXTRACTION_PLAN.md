# CLAUDE.md Extraction Plan

**Date:** 2025-10-02
**Current Size:** 436 lines
**Goal:** Further streamline by extracting project-specific content to appropriate docs

---

## Analysis: Content Categories in CLAUDE.md

### ✅ KEEP in CLAUDE.md (Claude-specific instructions)
- Lines 1-24: Quick Decision Tree (Claude behavior)
- Lines 25-60: Critical Workflows references (pointers to docs)
- Lines 150-235: Security Protocol (Claude commit behavior) - **ALREADY IN docs/SECURITY_PROTOCOLS.md BUT KEEP HERE TOO**
- Lines 350-352: Pointers to detailed procedures

**Rationale:** These are instructions for how Claude should behave and make decisions.

---

## 🔄 EXTRACT to Existing Docs (Project-specific information)

### 1. **Lines 61-76: Project Overview** → Should be in `README.md`
**Current location:** CLAUDE.md lines 61-76
**Target:** `README.md` (currently empty per line 434)
**Content:**
```markdown
NBA Game Simulator & ML Platform - A Python-based AWS data pipeline that:
- Ingests 146K+ historical NBA game JSON files (1999-2025, 119 GB) from ESPN
- Extracts 10% of relevant fields via AWS Glue ETL
- Stores processed data in RDS PostgreSQL (~12 GB after extraction)
- Simulates NBA games using statistical models on EC2
- Trains ML prediction models using SageMaker

Current Status: Phase 1 Complete - S3 data lake operational with 119 GB uploaded

Development Machine: MacBook Pro 16-inch, 2023 (M2 Max, 96GB RAM, macOS Sequoia 15.6.1)
- See MACHINE_SPECS.md for complete hardware/software specifications
- Code is optimized for Apple Silicon (ARM64) architecture
- Uses Homebrew for system packages and Miniconda for Python environment
```

**Action:** Move to README.md, replace in CLAUDE.md with:
```markdown
## Project Overview

See `README.md` for complete project description, architecture, and current status.
```

---

### 2. **Lines 77-93: Essential Setup** → Already in `docs/SETUP.md`
**Current location:** CLAUDE.md lines 77-93
**Target:** `docs/SETUP.md` (exists, checked)
**Duplication:** This is basic environment activation

**Action:** Replace with pointer:
```markdown
## Essential Setup

See `docs/SETUP.md` for complete environment setup and verification.

**Quick activation:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
```

---

### 3. **Lines 95-109: Critical Paths** → Should be in `docs/SETUP.md` or `QUICKSTART.md`
**Current location:** CLAUDE.md lines 95-109
**Target:** `docs/SETUP.md` (paths section)
**Content:** File paths, bucket names, directory structure

**Action:** Extract to `docs/SETUP.md` under "Project Paths", replace in CLAUDE.md with:
```markdown
## Critical Paths

See `docs/SETUP.md` for all project paths and directory locations.

**Most critical:**
- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **S3 Bucket:** `s3://nba-sim-raw-data-lake`
- **Archives:** `~/sports-simulator-archives/nba/`
```

---

### 4. **Lines 111-134: Architecture** → Should be in `README.md` or `docs/ARCHITECTURE.md`
**Current location:** CLAUDE.md lines 111-134
**Target:** `README.md` (high-level) or new `docs/ARCHITECTURE.md` (detailed)
**Content:** 5-phase pipeline diagram

**Action:** Move to README.md architecture section, replace in CLAUDE.md with:
```markdown
## Architecture

See `README.md` for complete 5-phase pipeline architecture and current status.
```

---

### 5. **Lines 136-148: Git & GitHub Configuration** → Already in `QUICKSTART.md`
**Current location:** CLAUDE.md lines 136-148
**Target:** `QUICKSTART.md` (git section)
**Duplication:** Basic git config info

**Action:** Replace with pointer:
```markdown
## Git & GitHub Configuration

See `QUICKSTART.md` for Git configuration and common commands.
See `docs/SECURITY_PROTOCOLS.md` for security scan procedures.
```

---

### 6. **Lines 237-272: Common Commands** → Already in `QUICKSTART.md`
**Current location:** CLAUDE.md lines 237-272
**Target:** `QUICKSTART.md` (exists, checked)
**Content:** S3 commands, database commands, AWS resource management

**Action:** Replace with pointer:
```markdown
## Common Commands

See `QUICKSTART.md` for all common commands (S3, database, AWS resources).
```

---

### 7. **Lines 274-303: Data Structure** → Already in `docs/DATA_STRUCTURE_GUIDE.md`
**Current location:** CLAUDE.md lines 274-303
**Target:** `docs/DATA_STRUCTURE_GUIDE.md` (exists, checked)
**Content:** S3 bucket layout, data extraction strategy, file characteristics

**Action:** Replace with pointer:
```markdown
## Data Structure

See `docs/DATA_STRUCTURE_GUIDE.md` for complete S3 bucket layout, data extraction strategy, and file characteristics.
```

---

### 8. **Lines 305-352: Important Notes** → Split to multiple docs
**Current location:** CLAUDE.md lines 305-352
**Targets:**
- **AWS Configuration** (307-310) → `docs/SETUP.md`
- **AWS Credentials** (312-320) → `docs/SECURITY_PROTOCOLS.md` (already there)
- **Critical Constraints** (322-328) → `docs/SETUP.md`
- **Cost Awareness** (330-341) → New `docs/COST_MANAGEMENT.md` or `PROGRESS.md`
- **Data Safety Protocol** (343-348) → `docs/SECURITY_PROTOCOLS.md`

**Action:** Replace with pointers:
```markdown
## Important Notes

- **AWS Configuration:** See `docs/SETUP.md`
- **Security & Credentials:** See `docs/SECURITY_PROTOCOLS.md`
- **Cost Estimates:** See `PROGRESS.md` for phase-by-phase costs
- **Data Safety:** See `docs/SECURITY_PROTOCOLS.md`
```

---

### 9. **Lines 354-361: Next Steps** → Already in `PROGRESS.md`
**Current location:** CLAUDE.md lines 354-361
**Target:** `PROGRESS.md` (detailed implementation plan)

**Action:** Replace with pointer:
```markdown
## Next Steps

See `PROGRESS.md` for complete phase-by-phase implementation plan with time estimates and cost breakdowns.
```

---

### 10. **Lines 363-428: Development Workflow** → Already in `QUICKSTART.md`
**Current location:** CLAUDE.md lines 363-428
**Target:** `QUICKSTART.md` (daily workflow section)
**Content:** Before starting work, credentials, maintenance, archives, Makefile

**Action:** Replace with pointer:
```markdown
## Development Workflow

See `QUICKSTART.md` for complete daily workflow, maintenance commands, and archive management.
```

---

### 11. **Lines 432-436: Known Documentation Gaps** → Not needed in CLAUDE.md
**Current location:** CLAUDE.md lines 432-436
**Content:** README.md is empty note

**Action:** Remove entirely (will be fixed when we create README.md)

---

## Summary: Proposed New CLAUDE.md Structure

**Target Size:** ~150-200 lines (down from 436 lines, 54-60% reduction)

### New Structure:

```markdown
# CLAUDE.md (150-200 lines total)

## Quick Decision Tree (24 lines) - KEEP
- When user asks to do something
- During the session
- When a command fails

## Critical Workflows (See Detailed Docs) (26 lines) - KEEP
- Security & Git → docs/SECURITY_PROTOCOLS.md
- Archiving → docs/ARCHIVE_PROTOCOLS.md
- Session Startup → docs/SESSION_INITIALIZATION.md
- Documentation → docs/DOCUMENTATION_SYSTEM.md

## Instructions for Claude (9 lines) - KEEP
- Pointers to Claude-specific instruction docs

## Project Overview (4 lines) - SIMPLIFY
- See README.md for complete description

## Essential Setup (8 lines) - SIMPLIFY
- See docs/SETUP.md
- Quick conda activation command

## Critical Paths (8 lines) - SIMPLIFY
- 3 most critical paths only
- See docs/SETUP.md for complete list

## Architecture (4 lines) - SIMPLIFY
- See README.md for 5-phase pipeline

## Git & GitHub Configuration (6 lines) - SIMPLIFY
- See QUICKSTART.md for commands
- See docs/SECURITY_PROTOCOLS.md for security

## Security Protocol (85 lines) - KEEP AS-IS
- Critical pre-commit security scan procedure
- Must be immediately visible to Claude
- Already documented in docs/SECURITY_PROTOCOLS.md but duplicated here intentionally

## Common Commands (4 lines) - SIMPLIFY
- See QUICKSTART.md

## Data Structure (4 lines) - SIMPLIFY
- See docs/DATA_STRUCTURE_GUIDE.md

## Important Notes (8 lines) - SIMPLIFY
- Pointers to relevant docs

## Next Steps (4 lines) - SIMPLIFY
- See PROGRESS.md

## Development Workflow (4 lines) - SIMPLIFY
- See QUICKSTART.md

TOTAL: ~150-200 lines (54-60% reduction)
```

---

## Files to Create

1. **README.md** (NEW - high priority)
   - Project overview
   - Architecture diagram (5-phase pipeline)
   - Current status
   - Quick links to docs
   - Development machine info

---

## Files to Update

1. **CLAUDE.md** (436 → 150-200 lines)
   - Remove detailed project info
   - Replace with pointers to appropriate docs
   - Keep Claude-specific behavior instructions
   - Keep security protocol (intentional duplication)

2. **docs/SETUP.md** (enhance)
   - Add complete critical paths section
   - Add AWS configuration section
   - Add critical constraints section

3. **QUICKSTART.md** (minor updates if needed)
   - Ensure has all common commands
   - Ensure has development workflow

4. **docs/DATA_STRUCTURE_GUIDE.md** (verify completeness)
   - Ensure has all content from CLAUDE.md lines 274-303

---

## Rationale

**Why this helps Claude:**
1. **Faster parsing:** 150-200 lines vs 436 lines = 54-60% less context consumed
2. **Clearer purpose:** CLAUDE.md is for Claude behavior, other docs for project info
3. **Easier updates:** Project info changes go to appropriate docs, not CLAUDE.md
4. **Better organization:** Information is where users/Claude expect to find it

**Why keep security protocol duplicated:**
- Critical for Claude to see immediately without looking elsewhere
- Must be impossible to miss
- Short enough to justify duplication

---

## Implementation Order

1. ✅ Create README.md (project overview + architecture)
2. ✅ Update docs/SETUP.md (add paths, config, constraints)
3. ✅ Verify QUICKSTART.md has all workflow content
4. ✅ Verify DATA_STRUCTURE_GUIDE.md is complete
5. ✅ Streamline CLAUDE.md (replace sections with pointers)
6. ✅ Test: Verify Claude can still find all information via pointers
7. ✅ Commit with detailed changelog
8. ✅ Push to GitHub

---

## Testing Checklist

After implementation:
- [ ] Can Claude find project overview? (README.md)
- [ ] Can Claude find setup instructions? (docs/SETUP.md)
- [ ] Can Claude find critical paths? (docs/SETUP.md)
- [ ] Can Claude find architecture? (README.md)
- [ ] Can Claude find common commands? (QUICKSTART.md)
- [ ] Can Claude find data structure info? (docs/DATA_STRUCTURE_GUIDE.md)
- [ ] Can Claude find cost information? (PROGRESS.md)
- [ ] Can Claude find development workflow? (QUICKSTART.md)
- [ ] Does security protocol still work? (in CLAUDE.md)

---

## Expected Benefits

**Before:**
- CLAUDE.md: 436 lines
- Mixes Claude behavior + project info
- Hard to maintain (update same info in multiple places)

**After:**
- CLAUDE.md: 150-200 lines (54-60% smaller)
- Pure Claude behavior instructions + pointers
- Easy to maintain (project info in dedicated docs)
- README.md provides GitHub landing page
- Better information architecture