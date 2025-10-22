# Documentation Archive

**Last Updated:** October 11, 2025

This directory contains archived documentation files that are historical snapshots or superseded planning documents.

## Why Archive Instead of Delete?

These documents provide valuable historical context:
- Show the evolution of the project
- Preserve decision-making processes
- Help future developers understand past approaches
- Maintain complete audit trail for multi-sport replication

**Archive, don't delete** - These files remain accessible via git history and directory structure.

---

## Archive Directory Structure

```
docs/archive/
├── README.md (this file)
├── session_handoffs/           # Session handoff documents (date-specific snapshots)
├── scraper_reports/            # Scraper test results and status reports (point-in-time)
├── planning/                   # Pre-implementation planning documents (superseded)
└── superseded_documentation/   # Large docs replaced by modular structure (Oct 2025)
```

---

## Session Handoffs (`session_handoffs/`)

**Purpose:** Preserve session transition documents from specific dates

**Contents:**
- `SESSION_HANDOFF_YYYYMMDD.md` - Handoff documents between sessions
- `SESSION_SUMMARY_YYYY_MM_DD*.md` - Session summary snapshots

**When archived:** After session completes and information is integrated into permanent docs

**Status:** Historical snapshots - reference only

---

## Scraper Reports (`scraper_reports/`)

**Purpose:** Preserve point-in-time scraper testing and status reports

**Contents:**
- `SCRAPER_QUICK_TEST.md` - Quick test procedures (Oct 7, 2025 snapshot)
- `SCRAPER_TEST_RESULTS.md` - Test results from specific runs
- `SCRAPER_STATUS_REPORT.md` - Status report (Oct 7, 2025 snapshot)
- `ALL_SOURCES_STATUS.md` - All sources status (Oct 6, 2025 snapshot)

**Active replacements:**
- Operational guide: `docs/data_collection/scrapers/MANAGEMENT.md`
- Complete procedures: Workflow #42 (`docs/claude_workflows/workflow_descriptions/42_scraper_management.md`)

**When archived:** After operational procedures are consolidated into active documentation

**Status:** Historical reports - may contain outdated script references

---

## Planning Documents (`planning/`)

**Purpose:** Preserve pre-implementation planning and checklists

**Contents:**
- `IMPLEMENTATION_CHECKLIST.md` - Phase implementation checklist (Oct 6, 2025)
- `PHASE_1_FINDINGS.md` - Phase 1 findings and analysis (Oct 6, 2025)
- `QUICK_START_MULTI_SOURCE.md` - Multi-source quick start (superseded)

**Active replacements:**
- Phase documentation: `docs/phases/PHASE_*.md` files
- Workflows: `docs/claude_workflows/workflow_descriptions/` files
- Quick start: `QUICKSTART.md` (root directory)

**When archived:** After implementation completes and findings are integrated into phase docs

**Status:** Planning artifacts - superseded by implementation

---

## Superseded Documentation (`superseded_documentation/`)

**Purpose:** Preserve large monolithic documentation files replaced by modular structure

**Contents:**
- `PHASE_0_BASKETBALL_REFERENCE_EXPANSION.md` - Original Basketball Reference planning (4,800 lines, Oct 10, 2025)
- `PHASE_0_BASKETBALL_REFERENCE_COMPLETE_EXPANSION.md` - Complete expansion plan (4,800 lines, Oct 11, 2025)
- `PHASE_0_TIER_10_WNBA.md` - WNBA detailed implementation (1,400 lines, Oct 11, 2025)
- `PHASE_0_TIERS_11_12_13_MULTI_LEAGUE.md` - Multi-League planning (1,800 lines, Oct 11, 2025)

**Active replacements:**
- Phase index system: `docs/phases/PHASE_N_INDEX.md` (150 lines each)
- 13-tier modular structure: `docs/phases/phase_0/0.1_basketball_reference/` directory
- Tier Index: `docs/phases/phase_0/0.1_basketball_reference/README.md` (~300 lines)
- Individual tier files: `TIER_1_NBA_HIGH_VALUE.md` through `TIER_13_COLLEGE.md` (300-800 lines each)
- Quick Reference: `docs/phases/phase_0/0.1_basketball_reference/QUICK_REFERENCE_CARDS.md` (~600 lines)
- Organization protocol: Workflow #45 (`docs/claude_workflows/workflow_descriptions/45_documentation_organization_protocol.md`)

**Why replaced:**
- Original files consumed 20-24% of context budget (4,800+ lines)
- Made it inefficient to work on specific tasks
- New modular structure reduces context usage to 1.5-6% per session
- Enables progressive detail levels and faster file operations
- Scalable for future additions

**When archived:** October 11, 2025 (phase index reorganization)

**Status:** Historical documentation - replaced by phase index system

**Phase Index Reorganization (October 11, 2025):**

Complete documentation structure reorganization to reduce context usage:

1. **Phase Index System:** Created PHASE_N_INDEX.md files (0-7) as navigation hubs
2. **Subdirectory Organization:** Moved all phase content to phase_N/ subdirectories
3. **Sub-phase Naming:** Standardized N.M_name.md format (e.g., 0.0_initial_data_collection.md)
4. **Basketball Reference:** Moved to phase_0/0.1_basketball_reference/ with 13-tier structure

**Context impact reduction:**
- Before: Reading Phase 0 content = ~3,362 lines (17% context)
- After: Reading PHASE_0_INDEX.md + 1 sub-phase = ~750 lines (3.75% context)
- **Phase navigation savings:** -78% context reduction
- **Overall session start:** 1,085 → 885 lines (-18% additional reduction)
- **PROGRESS.md:** 1,094 → 391 lines (-64% reduction)
- **CLAUDE.md:** 546 → 395 lines (-28% reduction)

---

## Finding Archived Documents

### Method 1: Browse by Category

```bash
# List session handoffs
ls -lt docs/archive/session_handoffs/

# List scraper reports
ls -lt docs/archive/scraper_reports/

# List planning docs
ls -lt docs/archive/planning/

# List superseded documentation
ls -lt docs/archive/superseded_documentation/
```

### Method 2: Search by Keyword

```bash
# Search all archived docs
grep -r "keyword" docs/archive/

# Search specific category
grep -r "keyword" docs/archive/scraper_reports/
```

### Method 3: Git History

```bash
# Find when file was moved to archive
git log --follow --oneline -- docs/archive/<category>/<filename>

# View file content from before archiving
git log --all --full-history -- "*/<filename>"
```

---

## Archive Policies

### What Gets Archived

✅ **Archive these:**
- Session handoffs/summaries from completed sessions
- Point-in-time status reports (dated snapshots)
- Pre-implementation planning documents (after implementation)
- Test results from specific dates
- Superseded quick-start guides
- Large monolithic documentation files replaced by modular structure

### What Stays Active

⛔ **Keep in docs/ root:**
- Operational guides (data_collection/scrapers/MANAGEMENT.md, DATA_SOURCES.md)
- Active workflows (all files in `claude_workflows/`)
- Architecture decisions (ADR files)
- Phase documentation (PHASE_N_INDEX.md and phase_N/ subdirectories in `phases/`)
- Current setup guides (SETUP.md, SECURITY_PROTOCOLS.md)

### Archiving Workflow

**When archiving documentation:**

1. ✅ Use `git mv` (preserves history)
2. ✅ Update this README if adding new category
3. ✅ Check for references in active docs
4. ✅ Commit with descriptive message
5. ❌ Don't delete (archive preserves context)

**Example:**
```bash
# Move file to appropriate archive subdirectory
git mv docs/OLD_DOC.md docs/archive/planning/

# Update this README if needed
# (Add to category list)

# Commit
git commit -m "docs(archive): archive OLD_DOC.md

Reason: Superseded by NEW_DOC.md
Category: planning
Date: YYYY-MM-DD"
```

---

## Related Documentation

**Archive systems:**
- `docs/ARCHIVE_PROTOCOLS.md` - Complete archive protocols (for all file types)
- Workflow #9: Archive Management - Gitignored files and conversations

**Active documentation index:**
- `CLAUDE.md` - Documentation system overview
- `docs/DOCUMENTATION_SYSTEM.md` - Documentation trigger system

---

*For current operational documentation, see root `docs/` directory and `docs/phases/` subdirectory.*
