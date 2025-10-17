# Repository Organization Plan

**Date:** October 12, 2025
**Status:** IN PROGRESS

---

## 📊 Current Issues Identified

### Root Directory Clutter (89 items)
1. **Old log files** (14 files) - Need archival
   - `extract_*.log`, `partition_overnight.log`, `crawler_overnight.log`, etc.

2. **Old PID files** (6 files) - Can be deleted
   - `crawler.pid`, `extract.pid`, `partition.pid`, etc.

3. **Old status files** (15+ files) - Need archival
   - `OVERNIGHT_*.md`, `EXTRACTION_*.md`, `WORKFLOW_*.md`, `SESSION_SUMMARY_*.md`

4. **Hidden files** (10+ files) - Review and clean
   - `.session-history.md`, `.test_archive_system.txt`, `.documentation-triggers.md`

5. **Test files in root** - Should be in tests/
   - `test_cursor_secrets.py`

6. **Duplicate directories**
   - `synthesis_output/` and `synthesis_outputs/`

7. **Empty directories**
   - `mlartifacts/`, `mlruns/`, `models/` (MLflow artifacts)

---

## ✅ Organization Actions

### Phase 1: Archive Old Files

**Target: `docs/archive/old_logs/`**
```bash
# Create archive structure
mkdir -p docs/archive/old_logs
mkdir -p docs/archive/old_status_files
mkdir -p docs/archive/old_pids

# Move log files
mv *.log docs/archive/old_logs/ 2>/dev/null

# Move PID files
mv *.pid docs/archive/old_pids/ 2>/dev/null

# Move old status files
mv OVERNIGHT_*.md EXTRACTION_*.md WORKFLOW_*.md SESSION_SUMMARY_*.md docs/archive/old_status_files/ 2>/dev/null
```

### Phase 2: Clean Up Test Files

```bash
# Move test file to tests/
mv test_cursor_secrets.py tests/manual/

# Clean up test JSON
mv tier1_progress.json docs/archive/old_status_files/
```

### Phase 3: Consolidate Directories

```bash
# Keep synthesis_output, remove synthesis_outputs if redundant
# Review contents first
```

### Phase 4: Update .gitignore

Add patterns for:
- `*.pid` - Process ID files
- `*.log` - Log files (except specific ones)
- `mlartifacts/`, `mlruns/` - MLflow temp files
- `synthesis_outputs/` - If keeping synthesis_output

### Phase 5: Hidden Files Review

Keep:
- `.env`, `.env.example` ✅
- `.gitignore`, `.gitmessage` ✅
- `.mlflowrc` ✅
- `.archive-location` ✅

Archive:
- `.session-history.md` → `docs/archive/`
- `.test_archive_system.txt` → `docs/archive/`
- `.documentation-triggers.md` → `docs/archive/`

Delete:
- `.DS_Store` (Mac metadata)

---

## 📁 Target Directory Structure

```
nba-simulator-aws/
├── README.md                      ✅ Keep
├── PROGRESS.md                    ✅ Keep
├── CLAUDE.md                      ✅ Keep
├── QUICKSTART.md                  ✅ Keep
├── LICENSE                        ✅ Keep
├── Makefile                       ✅ Keep
├── requirements.txt               ✅ Keep
├── .env.example                   ✅ Keep
├── .gitignore                     ✅ Update
├── .gitmessage                    ✅ Keep
├── config/                        ✅ Keep
├── data/                          ✅ Keep
├── docs/                          ✅ Keep (expanded)
│   ├── archive/                   ✅ Expanded
│   │   ├── old_logs/              🆕 New
│   │   ├── old_pids/              🆕 New
│   │   ├── old_status_files/      🆕 New
│   │   └── session_handoffs/      ✅ Exists
│   └── [other docs]               ✅ Keep
├── logs/                          ✅ Keep (current logs)
├── notebooks/                     ✅ Keep
├── reports/                       ✅ Keep
├── scripts/                       ✅ Keep
├── sql/                           ✅ Keep
├── tests/                         ✅ Keep
│   └── manual/                    🆕 New (for ad-hoc tests)
└── backups/                       ✅ Keep

Remove from root:
├── *.log files                    → docs/archive/old_logs/
├── *.pid files                    → docs/archive/old_pids/
├── OVERNIGHT_*.md                 → docs/archive/old_status_files/
├── EXTRACTION_*.md                → docs/archive/old_status_files/
├── WORKFLOW_*.md                  → docs/archive/old_status_files/
├── SESSION_SUMMARY_*.md           → docs/archive/old_status_files/
├── test_cursor_secrets.py         → tests/manual/
├── .session-history.md            → docs/archive/
├── mlartifacts/ (if empty)        → Delete
├── mlruns/ (if empty)             → Delete
├── synthesis_outputs/ (if dupe)   → Delete
```

---

## 🎯 Expected Results

**Before:** 89 items in root
**After:** ~40 items in root (53% reduction)

**Benefits:**
- ✅ Cleaner root directory
- ✅ Easier navigation
- ✅ Better git status readability
- ✅ Archived old files (preserved history)
- ✅ Improved .gitignore patterns

---

## ⚠️ Safety Checks

1. **Never delete** without archiving first
2. **Verify** directory contents before removing
3. **Test** .gitignore changes don't affect important files
4. **Commit** incrementally for easy rollback

---

## 📝 Execution Log

**Completed:** October 12, 2025

### Phase 1: Archive Old Files ✅
- Created `docs/archive/old_logs/`
- Created `docs/archive/old_pids/`
- Created `docs/archive/old_status_files/`
- Moved 15 log files to archive
- Moved 6 PID files to archive
- Moved 19 status/session markdown files to archive

### Phase 2: Clean Up Test Files ✅
- Moved `test_cursor_secrets.py` to `tests/manual/`
- Moved `tier1_progress.json` to archive
- Archived 3 hidden files (`.session-history.md`, `.test_archive_system.txt`, `.documentation-triggers.md`)
- Removed `.DS_Store`

### Phase 3: Consolidate Directories ✅
- Removed `synthesis_outputs/` (duplicate, empty)
- Removed `mlartifacts/` (empty MLflow directory)
- Removed `mlruns/` (empty MLflow directory)
- Removed `models/` (empty directory)
- Kept `synthesis_output/` (has 16 analysis files)

### Phase 4: Update .gitignore ✅
- Added MLflow artifact patterns
- Added synthesis output patterns
- Consolidated archived file patterns
- Added scraper temp file patterns
- Improved organization and comments

### Phase 5: Final Documentation ✅
- Created `docs/REPO_ORGANIZATION.md` (comprehensive guide)
- Updated `REPO_ORGANIZATION_PLAN.md` (this file)

---

## ✅ Results

**Root Directory:**
- **Before:** 89 items
- **After:** 28 items
- **Reduction:** 68%

**Files Archived:** 40 total
- Logs: 15
- PIDs: 6
- Status files: 19

**Directories Cleaned:** 4 removed (duplicate/empty)

**Time:** ~30 minutes

---

**Status:** ✅ COMPLETE


