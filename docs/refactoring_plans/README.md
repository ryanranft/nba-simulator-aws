# Refactoring Plans - Full Codebase Reorganization

**Status:** 📋 **PLANS IMPORTED** (Not yet started)  
**Scope:** Complete system reorganization (4,055+ files)  
**Timeline:** 14 weeks (production-safe approach)  
**Generated:** October 27, 2025  
**Imported:** October 29, 2025

---

## Overview

This directory contains comprehensive plans for reorganizing the entire NBA Simulator AWS codebase into a proper Python package structure. This is a **separate initiative** from the Phase 0 PostgreSQL restructuring work.

### Current State
- 1,672 Python scripts scattered across 10+ directories
- 643 test files with no clear organization
- 1,720 markdown docs in various locations
- 75+ ETL scrapers mixed together
- 8 autonomous agents in scripts/etl/
- No proper Python package structure
- Imports don't work consistently

### Target State
- Clean Python package: `nba_simulator/`
- Organized by function: etl/, agents/, monitoring/, ml/
- Centralized configuration
- Import system that works: `from nba_simulator.etl import ESPNScraper`
- All existing functionality preserved
- Zero data loss

---

## 📁 Directory Structure

```
refactoring_plans/
├── README.md (this file)
│
├── execution/
│   ├── COMPLETE_REFACTORING_EXECUTION_PLAN.md (14-week timeline)
│   ├── CLAUDE_CODE_REFACTORING_INSTRUCTIONS.md (implementation instructions)
│   └── COMPREHENSIVE_FILE_INVENTORY.md (all 4,055+ files mapped)
│
├── guides/
│   ├── REFACTORING_GUIDE_v2_PRODUCTION.md (production-safe approach)
│   ├── REFACTORING_DELIVERABLES_v2.md (phase deliverables)
│   └── QUICK_REFERENCE.md (quick lookup guide)
│
├── handoff/
│   ├── NEW_CHAT_HANDOFF_INSTRUCTIONS.md (session continuity)
│   └── QUICK_START_NEW_CHAT.md (quick start for new sessions)
│
└── scripts/
    ├── phase1_setup_production_safe.sh (Phase 1 setup script)
    ├── refactor_dashboard.py (monitoring dashboard)
    └── test_comprehensive_validation.py (validation suite)
```

---

## 📋 File Index

### Execution Plans

#### [`execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md`](execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md)
**Primary execution plan** - 864 lines detailing the complete 14-week refactoring timeline.

**Contents:**
- Complete file mapping (4,055+ files)
- Target package structure: `nba_simulator/`
- 7-phase execution timeline (14 weeks)
- Safety protocols and monitoring
- Emergency rollback procedures
- Success metrics and validation

**Timeline:**
- Phase 0: Pre-Flight Safety (Week 0)
- Phase 1: Core Infrastructure (Weeks 1-2)
- Phase 2: ETL Framework (Weeks 3-5)
- Phase 3: Agents & Workflows (Weeks 6-7)
- Phase 4: Monitoring & Validation (Weeks 8-9)
- Phase 5: Testing Infrastructure (Weeks 10-11)
- Phase 6: Phase 8 Box Score (Weeks 12-13)
- Phase 7: Final Validation (Week 14)

#### [`execution/CLAUDE_CODE_REFACTORING_INSTRUCTIONS.md`](execution/CLAUDE_CODE_REFACTORING_INSTRUCTIONS.md)
**Implementation instructions** for Claude Code to execute the refactoring.

**Purpose:**
- Step-by-step instructions for AI assistant
- Safety constraints and guardrails
- Validation requirements
- Rollback procedures

#### [`execution/COMPREHENSIVE_FILE_INVENTORY.md`](execution/COMPREHENSIVE_FILE_INVENTORY.md)
**Complete file inventory** - every file accounted for.

**Contents:**
- All 1,672 Python scripts mapped
- All 643 test files catalogued
- All 1,720 markdown docs listed
- Source → destination mapping
- File dependencies documented

---

### Guides

#### [`guides/REFACTORING_GUIDE_v2_PRODUCTION.md`](guides/REFACTORING_GUIDE_v2_PRODUCTION.md)
**Production-safe refactoring approach** - how to refactor without breaking production systems.

**Key Topics:**
- Zero-downtime strategies
- Database safety (20M+ records)
- DIMS monitoring continuity
- ADCE autonomous loop preservation
- Phase 8 box score generation safety

#### [`guides/REFACTORING_DELIVERABLES_v2.md`](guides/REFACTORING_DELIVERABLES_v2.md)
**Phase deliverables** - what gets delivered at each phase.

**Contents:**
- Weekly deliverables checklist
- Testing requirements per phase
- Documentation requirements
- Validation criteria

#### [`guides/QUICK_REFERENCE.md`](guides/QUICK_REFERENCE.md)
**Quick lookup guide** - common patterns and solutions.

**Contents:**
- Import pattern examples
- Common refactoring patterns
- Troubleshooting guide
- Quick commands reference

---

### Handoff Instructions

#### [`handoff/NEW_CHAT_HANDOFF_INSTRUCTIONS.md`](handoff/NEW_CHAT_HANDOFF_INSTRUCTIONS.md)
**Session continuity instructions** - how to continue work across chat sessions.

**Purpose:**
- Resume refactoring work in new sessions
- Track progress across multiple sessions
- Maintain context between AI assistant sessions
- Prevent work duplication

#### [`handoff/QUICK_START_NEW_CHAT.md`](handoff/QUICK_START_NEW_CHAT.md)
**Quick start guide** - get up to speed quickly in a new chat.

**Contents:**
- Current status check commands
- Quick verification steps
- Where to continue from
- Common gotchas

---

### Scripts

#### [`scripts/phase1_setup_production_safe.sh`](scripts/phase1_setup_production_safe.sh)
**Phase 1 setup script** - creates initial package structure safely.

**Usage:**
```bash
bash docs/refactoring_plans/scripts/phase1_setup_production_safe.sh
```

**What it does:**
- Creates `nba_simulator/` package structure
- Preserves all existing scripts
- Sets up initial imports
- Validates setup

#### [`scripts/refactor_dashboard.py`](scripts/refactor_dashboard.py)
**Monitoring dashboard** - continuous health monitoring during refactoring.

**Usage:**
```bash
python docs/refactoring_plans/scripts/refactor_dashboard.py
```

**Monitors:**
- Database record counts (20M+ records)
- DIMS metrics operational
- Phase 8 box score generation
- ADCE autonomous loop health
- S3 file counts (146,115+ files)

#### [`scripts/test_comprehensive_validation.py`](scripts/test_comprehensive_validation.py)
**Comprehensive validation suite** - validates entire system after refactoring.

**Usage:**
```bash
python docs/refactoring_plans/scripts/test_comprehensive_validation.py
```

**Validates:**
- All 40 database tables
- All 643 tests passing
- Import system working
- Monitoring operational
- Zero data loss

---

## 🚦 Getting Started

### Before You Begin

**⚠️ CRITICAL:** This refactoring touches active production systems:

1. **Database:** 20M+ records across 40 tables
2. **DIMS Monitoring:** Active system health monitoring
3. **Phase 8:** Box score generation running
4. **ADCE:** Autonomous 24/7 data collection
5. **Scheduled Jobs:** Unknown cron jobs may exist

**Must complete Phase 0 (Pre-Flight Safety) before any code changes.**

### Quick Start

1. **Read the execution plan:**
   ```bash
   cat docs/refactoring_plans/execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md
   ```

2. **Review production guide:**
   ```bash
   cat docs/refactoring_plans/guides/REFACTORING_GUIDE_v2_PRODUCTION.md
   ```

3. **Understand current state:**
   ```bash
   cat docs/refactoring_plans/execution/COMPREHENSIVE_FILE_INVENTORY.md
   ```

4. **Start with Phase 0 (Pre-Flight Safety):**
   - Discover active systems
   - Document cron jobs
   - Create database baseline
   - Answer critical questions

---

## 📊 Current Status

### Refactoring Status: NOT STARTED

- [ ] Phase 0: Pre-Flight Safety
- [ ] Phase 1: Core Infrastructure (Weeks 1-2)
- [ ] Phase 2: ETL Framework (Weeks 3-5)
- [ ] Phase 3: Agents & Workflows (Weeks 6-7)
- [ ] Phase 4: Monitoring & Validation (Weeks 8-9)
- [ ] Phase 5: Testing Infrastructure (Weeks 10-11)
- [ ] Phase 6: Phase 8 Box Score (Weeks 12-13)
- [ ] Phase 7: Final Validation (Week 14)

### Prerequisites

Before starting refactoring, complete:
- [ ] Phase 0 PostgreSQL restructuring (separate initiative)
- [ ] Full database backup
- [ ] Active process discovery
- [ ] Cron job documentation
- [ ] Git safety tag created

---

## 🔗 Related Documentation

### Project Documentation
- [Project Root](../../README.md)
- [CLAUDE.md](../../CLAUDE.md) - AI assistant instructions
- [PROGRESS.md](../../PROGRESS.md) - Overall project progress

### Phase 0 (Separate from Refactoring)
- [Phase 0 Index](../phases/phase_0/PHASE_0_INDEX.md)
- [Phase 0 PostgreSQL Work](../phases/phase_0/0.0023_postgresql_jsonb_storage/README.md)

### Architecture
- [Architecture Decision Records](../adr/)
- [ADR-010: 4-Digit Phase Numbering](../adr/010-four-digit-subphase-numbering.md)

---

## ⚠️ Important Notes

### This is NOT Phase 0 PostgreSQL Work

**Two Separate Initiatives:**

1. **Phase 0 PostgreSQL Restructuring** (Current - In Progress)
   - Scope: Archive MongoDB sub-phases, document PostgreSQL alternatives
   - Timeline: 2 hours documentation, 6-7 weeks implementation
   - Status: Documentation complete (October 29, 2025)

2. **Full Codebase Refactoring** (This Plan - Not Started)
   - Scope: Reorganize entire 4,055+ file codebase
   - Timeline: 14 weeks
   - Status: Plans imported, awaiting start

### Safety First

- All plans emphasize production safety
- Zero-downtime approach required
- Continuous monitoring mandatory
- Emergency rollback procedures documented
- Database integrity paramount (20M+ records)

### MCP Integration

Plans designed for MCP (Model Context Protocol) assisted execution:
- Database queries via MCP
- Active process discovery
- Real-time monitoring
- Validation automation

---

## 📞 Next Steps

### When Ready to Begin Refactoring:

1. **Complete Phase 0 Pre-Flight:**
   ```bash
   # Discover active systems
   crontab -l
   systemctl list-units --type=timer | grep nba
   launchctl list | grep nba
   
   # Create baseline
   pg_dump > backups/pre_refactor_$(date +%Y%m%d).sql
   git tag pre-refactor-comprehensive-$(date +%Y%m%d)
   ```

2. **Start monitoring dashboard:**
   ```bash
   python docs/refactoring_plans/scripts/refactor_dashboard.py
   ```

3. **Begin Phase 1 (Core Infrastructure):**
   ```bash
   bash docs/refactoring_plans/scripts/phase1_setup_production_safe.sh
   ```

4. **Follow execution plan step-by-step:**
   See `execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md`

---

**Plans Imported:** October 29, 2025  
**Status:** Ready for execution (awaiting Phase 0 PostgreSQL completion)  
**Next Action:** Complete Phase 0 work, then begin refactoring Phase 0 (Pre-Flight Safety)

