# Repository Organization

**Version:** 1.0
**Last Updated:** October 12, 2025
**Status:** ✅ COMPLETE

---

## 📊 Overview

This document describes the repository organization structure and file management practices for the NBA Simulator AWS project.

---

## 🎯 Organization Results

### Root Directory Cleanup

**Before:** 89 items (cluttered with logs, PIDs, old status files)
**After:** 28 items (68% reduction)
**Status:** ✅ Clean, maintainable structure

---

## 📁 Root Directory Structure

```
nba-simulator-aws/
├── README.md                      # Project overview & architecture
├── PROGRESS.md                    # Master project status & phase tracking
├── CLAUDE.md                      # AI assistant instructions & protocols
├── QUICKSTART.md                  # Common commands & daily workflow
├── LICENSE                        # MIT License
├── Makefile                       # Build automation
├── requirements.txt               # Python dependencies
├── CHANGELOG.md                   # Version history
├── .env.example                   # Environment template (no secrets)
├── .gitignore                     # Git exclusions
├── .gitmessage                    # Commit message template
├── .mlflowrc                      # MLflow configuration
│
├── config/                        # Configuration files
├── data/                          # Local data cache (gitignored)
├── docs/                          # Documentation (see structure below)
├── logs/                          # Current operational logs
├── notebooks/                     # Jupyter notebooks for analysis
├── reports/                       # Generated reports
├── scripts/                       # Automation scripts
├── sql/                           # Database schemas & queries
├── tests/                         # Test suites
├── synthesis_output/              # AI-generated analysis files
├── backups/                       # Local backups (gitignored)
└── lambda/                        # AWS Lambda functions
```

---

## 📚 Documentation Structure

```
docs/
├── README.md                              # Documentation index
├── SETUP.md                               # Environment setup
├── PROJECT_VISION.md                      # Project goals & scope
├── DATA_STRUCTURE_GUIDE.md                # S3 bucket organization
├── MASTER_DATA_INVENTORY.md               # Complete data catalog
├── CONTEXT_MANAGEMENT_GUIDE.md            # AI context strategies
├── EMERGENCY_RECOVERY.md                  # Disaster recovery procedures
├── SECURITY_PROTOCOLS.md                  # Git & credential security
├── SCRAPER_MONITORING_SYSTEM.md           # Scraper operations
├── data_collection/scrapers/MANAGEMENT.md # Scraper deployment
├── REPO_ORGANIZATION.md                   # This file
│
├── phases/                                # Phase-specific documentation
│   ├── PHASE_0_INDEX.md                   # Data Collection
│   ├── PHASE_1_INDEX.md                   # Quality & Validation
│   ├── PHASE_2_INDEX.md                   # ETL Pipelines
│   ├── PHASE_3_INDEX.md                   # Database Loading
│   ├── PHASE_4_INDEX.md                   # Game Simulation
│   ├── PHASE_5_INDEX.md                   # ML Models
│   ├── PHASE_6_INDEX.md                   # Enhancements
│   ├── PHASE_7_INDEX.md                   # Betting Odds
│   ├── PHASE_8_INDEX.md                   # Data Audit
│   ├── PHASE_9_INDEX.md                   # PBP to Box Score
│   └── phase_N/                           # Detailed sub-phase docs
│
├── claude_workflows/                      # AI workflow procedures
│   ├── CLAUDE_WORKFLOW_ORDER.md           # Workflow index
│   └── workflow_descriptions/             # 51 detailed workflows
│       ├── 01_session_start.md
│       ├── 14_session_end.md
│       ├── 38_overnight_scraper_handoff.md
│       ├── 51_phase9_overnight_processing.md
│       └── ... (47 more)
│
└── archive/                               # Historical files
    ├── session_handoffs/                  # Session summaries
    │   ├── SESSION_HANDOFF_20251012_OVERNIGHT.md
    │   └── OVERNIGHT_STATUS_20251012.md
    ├── old_logs/                          # Archived log files (15 files)
    ├── old_pids/                          # Archived PID files (6 files)
    ├── old_status_files/                  # Archived status docs (20 files)
    └── [other archived files]
```

---

## 🗂️ File Categories

### Core Documentation (Root)
- **PROGRESS.md** - Primary project status (read first)
- **CLAUDE.md** - AI assistant protocols
- **README.md** - Project architecture
- **QUICKSTART.md** - Common operations

### Current Operations
- **logs/** - Active logs (current session)
- **CHAT_LOG.md** - Current conversation log
- **COMMAND_LOG.md** - Command execution history

### Archived (docs/archive/)
- **old_logs/** - Historical extraction/scraper logs
- **old_pids/** - Old process ID files
- **old_status_files/** - Superseded status documents
- **session_handoffs/** - Session transition documents

### Generated
- **synthesis_output/** - AI-generated analysis files
- **reports/** - System-generated reports

---

## 🚫 What's Gitignored

### Automatically Ignored
- `*.log` - All log files
- `*.pid` - All process ID files
- `*.csv`, `*.json`, `*.parquet` - Data files (too large)
- `data/` - Local data cache
- `backups/` - Local backups
- `.env` - Environment secrets
- `__pycache__/` - Python bytecode
- `.DS_Store` - Mac metadata

### Archived Pattern Ignored
- `OVERNIGHT*.md` - Old overnight status files
- `EXTRACTION*.md` - Old extraction status files
- `WORKFLOW*.md` - Old workflow comparison files
- `*_STATUS.md` - Old status documents
- `SESSION_SUMMARY*.md` - Old session summaries

---

## ✅ Best Practices

### File Placement

**Root Directory - Keep Only:**
- Essential documentation (README, PROGRESS, CLAUDE, QUICKSTART)
- Project metadata (LICENSE, requirements.txt, Makefile)
- Configuration templates (.env.example, .gitignore)

**Archive Instead of Delete:**
- Old log files → `docs/archive/old_logs/`
- Old status files → `docs/archive/old_status_files/`
- Session summaries → `docs/archive/session_handoffs/`

**Never Commit:**
- `.env` files with secrets
- PID files
- Log files (except in archives)
- Large data files (use S3)

### Naming Conventions

**Status Files:**
- Use `docs/archive/session_handoffs/SESSION_HANDOFF_YYYYMMDD.md`
- Not `SESSION_SUMMARY_YYYY-MM-DD.md` in root

**Logs:**
- Current logs: `logs/[component]_[date].log`
- Archived logs: `docs/archive/old_logs/[name].log`

**Temporary Files:**
- Use `/tmp/` for temporary files (not repo root)
- Use `.gitignore` to exclude temp patterns

---

## 🔧 Maintenance

### Weekly Cleanup
```bash
# Move current logs to archive (if needed)
mv logs/*.log docs/archive/old_logs/ 2>/dev/null

# Remove old PID files
rm -f *.pid 2>/dev/null

# Clean Mac metadata
rm -f .DS_Store 2>/dev/null
```

### Monthly Review
- Check `docs/archive/` size (consider compressing old files)
- Review `.gitignore` patterns
- Update documentation index

### Before Major Commits
- Run: `git status --short`
- Verify no secrets: `bash scripts/shell/pre_push_inspector.sh`
- Archive old status files
- Update `PROGRESS.md`

---

## 📈 Metrics

**Organization Session (October 12, 2025):**
- Files archived: 40 (logs, PIDs, status files)
- Directories removed: 4 (empty/duplicate)
- Root items: 89 → 28 (68% reduction)
- .gitignore patterns added: 12

**Storage Savings:**
- Root directory: Cleaner, faster navigation
- Git status: More readable
- Context loading: Faster file discovery

---

## 🎯 Future Improvements

1. **Automated Cleanup Script**
   - Schedule weekly log archival
   - Auto-remove old PID files
   - Clean temporary files

2. **Documentation Generator**
   - Auto-update file inventory
   - Generate structure diagrams
   - Track documentation coverage

3. **Size Monitoring**
   - Alert when root > 40 items
   - Track archive growth
   - Compress old files

---

## 📝 Change Log

### October 12, 2025 - Initial Organization
- Archived 15 log files
- Archived 6 PID files
- Archived 19 status/session files
- Removed 4 duplicate/empty directories
- Updated .gitignore with comprehensive patterns
- Created this documentation

---

For questions or suggestions, see `docs/README.md` or `CLAUDE.md`.

*Last updated: October 12, 2025*







