# Documentation Archive

**Last Updated:** October 8, 2025

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
├── session_handoffs/       # Session handoff documents (date-specific snapshots)
├── scraper_reports/        # Scraper test results and status reports (point-in-time)
└── planning/               # Pre-implementation planning documents (superseded)
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
- Operational guide: `docs/SCRAPER_MANAGEMENT.md`
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

## Finding Archived Documents

### Method 1: Browse by Category

```bash
# List session handoffs
ls -lt docs/archive/session_handoffs/

# List scraper reports
ls -lt docs/archive/scraper_reports/

# List planning docs
ls -lt docs/archive/planning/
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

### What Stays Active

⛔ **Keep in docs/ root:**
- Operational guides (SCRAPER_MANAGEMENT.md, DATA_SOURCES.md)
- Active workflows (all files in `claude_workflows/`)
- Architecture decisions (ADR files)
- Phase documentation (PHASE_*.md in `phases/`)
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
