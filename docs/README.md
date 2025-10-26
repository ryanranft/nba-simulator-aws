# Documentation Index - Quick Reference

**Last Updated:** October 21, 2025

This index helps Claude Code and developers find the right documentation efficiently. Files are organized by task type and size to optimize context usage.

---

## Quick Navigation

### Starting a New Session
1. Read **CLAUDE.md** (~395 lines) - Core instructions and navigation
2. Read **PROGRESS.md** (~390 lines) - Current project state
3. Read **this file** (~100 lines) - Documentation map
4. **Total: ~885 lines** (4.5% of 200K context budget)

### Working on a Specific Task
- **Phase work:** `docs/phases/PHASE_X.md` (400-500 lines)
- **Workflow execution:** `docs/claude_workflows/workflow_descriptions/XX_name.md` (200-400 lines)
- **Operational procedures:** `docs/CLAUDE_OPERATIONAL_GUIDE.md` (200 lines)

---

## By Task Type

### Session Management
- **CLAUDE.md** - Core instructions, navigation patterns, decision trees
- **docs/CLAUDE_OPERATIONAL_GUIDE.md** - Session init, progress tracking, command logging
- **PROGRESS.md** - Current phase status, session context, cost tracking

### Phase Implementation
- **docs/phases/phase_0/PHASE_0_INDEX.md** - Data Foundation & Infrastructure (🔄 IN PROGRESS 17/20 complete)
  - Includes: Data collection, Testing, Monitoring, Documentation, Data Audit
  - **NEW:** [Phase 0.18: Autonomous Data Collection](phases/phase_0/0.18_autonomous_data_collection/README.md) - 24/7 self-healing system
- **docs/phases/PHASE_1_INDEX.md** - Multi-source integration (⏸️ Pending)
- **docs/phases/PHASE_2_INDEX.md** - Play-by-Play to Box Score (⏸️ Pending, 9 sub-phases, ~12 weeks)
- **docs/phases/PHASE_3_INDEX.md** - RDS setup (✅ Complete)
- **docs/phases/PHASE_4_INDEX.md** - Simulation (✅ Complete)
- **docs/phases/PHASE_5_INDEX.md** - ML models (✅ Complete)
- **docs/phases/PHASE_6_INDEX.md** - AWS Glue ETL (⏸️ Deferred - Python ETL working)
- **docs/phases/PHASE_7_INDEX.md** - Betting odds (⏸️ Optional)

### Workflows
- **docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md** - Workflow index (38 workflows)
- **docs/claude_workflows/workflow_descriptions/** - Individual workflow procedures

### Daily Operations
- **QUICKSTART.md** - Common commands, daily workflow, make targets
- **scripts/autonomous/autonomous_cli.py** - Manage autonomous data collection (start, stop, status, health, logs, tasks)
- **docs/AUTONOMOUS_OPERATION.md** - Complete guide to 24/7 autonomous operation
- **docs/CLAUDE_QUICK_COMMANDS.md** - Claude-specific command patterns
- **docs/data_collection/scrapers/MANAGEMENT.md** - Scraper operations guide
- **docs/SCRAPER_MONITORING_SYSTEM.md** - Monitoring tools and procedures

### Setup & Configuration
- **docs/SETUP.md** - Environment setup, AWS configuration, credentials
- **docs/AWS_GLUE_DATA_CATALOG_STRATEGY.md** - Cloud-based data indexing strategy (planned)
- **README.md** - Project overview, architecture, quick start
- **docs/PROJECT_VISION.md** - Temporal panel data system vision

### Security & Git
- **docs/SECURITY_PROTOCOLS.md** - Pre-commit scans, pre-push inspection, secrets
- **docs/ARCHIVE_PROTOCOLS.md** - File archiving, conversation history
- **docs/archive/README.md** - Documentation archive structure

### Troubleshooting & Reference
- **⚠️ docs/TROUBLESHOOTING.md** (1,025 lines) - Error solutions (search first, read selectively)
- **⚠️ docs/LESSONS_LEARNED.md** (1,002 lines) - Historical context (read only when requested)
- **docs/EMERGENCY_RECOVERY.md** - Lost context, wrong file edits, recovery procedures

### Architecture & Design
- **⚠️ docs/TEMPORAL_QUERY_GUIDE.md** (996 lines) - Implementation reference (read sections only)
- **⚠️ docs/ADVANCED_SIMULATION_FRAMEWORK.md** (903 lines) - Simulation details (read when implementing)
- **docs/TEMPORAL_VS_TRADITIONAL.md** - Temporal vs traditional architecture
- **docs/adr/** - Architecture Decision Records

### Data & Sources
- **docs/DATA_SOURCES.md** - 5 data sources, coverage, status
- **docs/DATA_STRUCTURE_GUIDE.md** - S3 bucket layout, file characteristics
- **docs/DATA_SOURCE_BASELINES.md** - Verified baseline statistics
- **docs/DATA_SOURCE_MAPPING.md** - Multi-source integration mapping

### Testing & Quality
- **⚠️ docs/TESTING.md** (862 lines) - Testing philosophy (read when writing tests)
- **⚠️ docs/STYLE_GUIDE.md** (846 lines) - Code style (read when style question arises)
- **docs/claude_workflows/workflow_descriptions/41_testing_framework.md** - Testing procedures

### Context Management
- **docs/CONTEXT_MANAGEMENT_GUIDE.md** - Strategies for extending session length
- **docs/DOCUMENTATION_SYSTEM.md** - Documentation trigger system

---

## By File Size (Context Planning)

### Small (<200 lines) - Safe to Read Freely
- **docs/README.md** (this file, 100 lines)
- **docs/CLAUDE_OPERATIONAL_GUIDE.md** (200 lines)
- **docs/CLAUDE_QUICK_COMMANDS.md** (150 lines)
- **docs/EMERGENCY_RECOVERY.md** (100 lines)
- **docs/SCRAPER_MONITORING_SYSTEM.md** (200 lines)
- **docs/CONTEXT_MANAGEMENT_GUIDE.md** (200 lines)
- **Workflow files** (average 200-400 lines each)

### Medium (200-500 lines) - Read When Needed
- **README.md** (342 lines)
- **QUICKSTART.md** (250 lines after split)
- **CLAUDE.md** (395 lines)
- **PROGRESS.md** (390 lines)
- **Phase index files** (PHASE_N_INDEX.md, ~150 lines each)
- **Phase sub-phase files** (phase_N/N.M_name.md, 300-800 lines)
- **docs/SETUP.md** (697 lines)
- **docs/DATA_SOURCES.md** (595 lines)

### Large (500-1000 lines) - Read Specific Sections Only
- **docs/TEMPORAL_IMPLEMENTATION_ROADMAP.md** (717 lines)
- **docs/DATA_SOURCE_MAPPING.md** (711 lines)
- **docs/TEMPORAL_VS_TRADITIONAL.md** (626 lines)
- **docs/ML_FEATURE_CATALOG.md** (621 lines)
- **docs/PHASE_2.2_ETL_PLAN.md** (613 lines)
- **docs/REPRODUCTION_GUIDE.md** (573 lines)
- **docs/TEMPORAL_VALIDATION_GUIDE.md** (572 lines)
- **docs/DATA_DEDUPLICATION_RULES.md** (567 lines)
- **docs/TEMPORAL_ENHANCEMENT_SUMMARY.md** (566 lines)
- **docs/NBA_API_SCRAPER_OPTIMIZATION.md** (543 lines)

### Very Large (>1000 lines) - Search/Grep Only, Never Read Fully
- **⚠️ docs/TROUBLESHOOTING.md** (1,025 lines) - Use grep to find error
- **⚠️ docs/LESSONS_LEARNED.md** (1,002 lines) - Historical reference only
- **⚠️ docs/TEMPORAL_QUERY_GUIDE.md** (996 lines) - Read sections when implementing
- **⚠️ docs/ADVANCED_SIMULATION_FRAMEWORK.md** (903 lines) - Reference during simulation work
- **⚠️ docs/TESTING.md** (862 lines) - Reference when writing tests
- **⚠️ docs/STYLE_GUIDE.md** (846 lines) - Reference when style question arises
- **⚠️ docs/HOOPR_152_ENDPOINTS_GUIDE.md** (846 lines) - hoopR reference

---

## Reading Protocols for Claude Code

### Tier 1 - Always Read (Session Start)
- CLAUDE.md (~395 lines)
- PROGRESS.md (~390 lines)
- docs/README.md (~100 lines)
- **Total: ~885 lines (4.5% context)**

### Tier 2 - Read When Needed (Task-Specific)
- PHASE_N_INDEX.md for current phase (~150 lines)
- Specific sub-phase file phase_N/N.M_name.md (~300-800 lines)
- Referenced workflows for current sub-phase (~300 lines each)
- CLAUDE_OPERATIONAL_GUIDE.md (~200 lines) - only if doing session management
- **Total: +650-1,450 lines per task**

### Tier 3 - Search First, Read Selectively (Reference Only)
- **TROUBLESHOOTING.md** - Use grep to find error, read that section only
- **Large guides (>500 lines)** - Read specific sections, not entire file
- **QUICKSTART.md** - Only when user asks "what's the command for X?"

### Tier 4 - Never Read Unless Explicitly Requested
- **LESSONS_LEARNED.md** - Historical context only
- **TEMPORAL_QUERY_GUIDE.md** - Implementation reference (read sections)
- **TESTING.md** - Read when writing tests
- **STYLE_GUIDE.md** - Read when style question arises
- **ADVANCED_SIMULATION_FRAMEWORK.md** - Read during simulation implementation

---

## Common Task Patterns

### "Continue where we left off"
1. Read PROGRESS.md → Find 🔄 IN PROGRESS or ⏸️ PENDING phase
2. Read that phase file
3. Ask user what they completed since last session
4. Resume work

### "Work on [specific task]"
1. Read PROGRESS.md → Find which phase contains task
2. Read that phase file
3. Read referenced workflows
4. Execute task

### "Fix error: [error message]"
1. **Don't read TROUBLESHOOTING.md fully** (1,025 lines)
2. Use: `grep -i "error keyword" docs/TROUBLESHOOTING.md`
3. Read only the matching section
4. If not found, troubleshoot and ask if should be added

### "How do I [command/operation]?"
1. Check QUICKSTART.md or docs/CLAUDE_QUICK_COMMANDS.md
2. If not found, check relevant workflow
3. Don't read multiple large files looking for it

### "Run tests"
1. Read docs/claude_workflows/workflow_descriptions/41_testing_framework.md (not TESTING.md)
2. Execute test procedures
3. Only read TESTING.md if writing new tests

---

## File Organization

### Root Directory
- **CLAUDE.md** - Primary instructions for Claude Code
- **README.md** - Project overview and architecture
- **QUICKSTART.md** - User-focused commands
- **PROGRESS.md** - Phase tracking and session context

### docs/ Directory
- **CLAUDE_*.md** - Claude Code operational guides (consolidated to 1 file)
- **SETUP.md, SECURITY_PROTOCOLS.md, ARCHIVE_PROTOCOLS.md** - System configuration
- **DATA_*.md** - Data source documentation
- **TEMPORAL_*.md** - Temporal architecture documentation
- **Large guides** - Reference documentation (>800 lines, marked with ⚠️)

### docs/phases/
- Phase implementation guides (400-500 lines each)

### docs/claude_workflows/
- **CLAUDE_WORKFLOW_ORDER.md** - Workflow index
- **workflow_descriptions/** - Individual workflows (38 total)

### docs/archive/
- **session_handoffs/** - Historical session documents
- **scraper_reports/** - Point-in-time scraper status
- **planning/** - Pre-implementation planning docs
- **superseded_documentation/** - Archived documentation from Oct 2-19, 2025 (17 files)

---

## New Documentation Organization (October 21, 2025)

**Major reorganization completed:** 66 files reorganized, 40% reduction in docs/ root (142 → 85 files)

### Specialized System Documentation

**Monitoring Systems:**
- **docs/monitoring/dims/** - Data Inventory Management System (v3.1.0, 7 files)
  - PostgreSQL-backed metrics tracking with Jupyter integration
  - Production-ready DIMS implementation

**ML Systems:**
- **docs/ml_systems/book_recommendations/** - 214 ML implementations (9 files)
  - 100% complete autonomous deployment (12 minutes, Oct 19, 2025)
  - 1,284/1,284 tests passed, ~150,000+ lines of production code
  - Deployment, testing, and recommendations documentation

**Data Collection:**
- **docs/data_collection/scrapers/** - Scraper systems & monitoring (10 files)
  - ESPN, NBA API, Basketball Reference scrapers
  - Test results: 100% success rate on ESPN, 98.5% on NBA API
  - Monitoring, deployment, and operations guides
  - **test_results/** subdirectory with scraper validation reports

**Feature Systems:**
- **docs/features/shot_charts/** - Shot chart extraction & temporal integration (5 files)
- **docs/features/box_scores/** - Temporal box score systems (4 files)
- **docs/features/statistics/** - Advanced statistics (3 files)

### Enhanced Phase Organization

**Phase-Specific Enhancements:**
- **docs/phases/phase_9/9.0_plus_minus/** - Plus/Minus analysis system (7 files)
  - 26 ML features for lineup efficiency and player impact
  - Production-ready implementation

- **docs/phases/phase_0/0.1_basketball_reference/documentation/** - Technical documentation (7 files)
  - Box score system, PBP discovery, scraping notes
  - Comparison analysis, test plans, workflow integration

**Phase 5 Cleanup:**
- Reduced from 11 loose files to 3 essential files
- Organized ML summaries into proper subdirectories (5.19_drift_detection, 5.2_model_versioning)
- Removed duplicate implementation guides

### Archive Structure

**docs/archive/superseded_documentation/** - Historical documentation (17 files in 4 categories)
- **session_summaries/** - Session work from Oct 16-19 (3 files)
- **validation_summaries/** - Validation reports (2 files)
- **implementation_summaries/** - Implementation work (7 files)
- **planning/** - Planning documents from Oct 7-19 (5 files)

**Benefits Achieved:**
1. ✅ Improved discoverability - Logical grouping by system/feature
2. ✅ Reduced clutter - 40% reduction in docs/ root
3. ✅ Better navigation - 14 README files as entry points
4. ✅ Scalable structure - Easy to add new features/systems
5. ✅ Context savings - Easier to find relevant documentation

**See also:** docs/DOCUMENTATION_REORGANIZATION_SUMMARY.md for complete details

---

## Optimization Strategies

**For Claude Code:**
1. **Start lean:** 885 lines (Tier 1) = 4.5% context
2. **Add incrementally:** Read phase indexes + sub-phases + workflows as needed
3. **Search, don't read:** Use grep for large files
4. **Track what you've read:** Don't re-read files in same session
5. **Target: Stay under 4,000 lines** per session (comfortable limit)

**Context Budget Examples:**
- **Minimal session:** 885 lines (orientation only)
- **Light work:** 1,335 lines (+ 1 phase index + 1 sub-phase)
- **Moderate work:** 1,935 lines (+ 1 phase index + 1 sub-phase + 2 workflows)
- **Heavy work:** 2,835 lines (+ 2 phase indexes + 2 sub-phases + 2 workflows)
- **Maximum recommended:** 4,000 lines (stay under 200K tokens)

---

## Recent Changes

**October 21, 2025 - Comprehensive Documentation Reorganization:**
- **Reorganized 66 files** across 6 priorities + 3 enhancements
- **Reduced docs/ root: 142 → 85 files (40% reduction)**
- **Created 8 new directories** for specialized systems:
  - monitoring/dims/, ml_systems/book_recommendations/, data_collection/scrapers/
  - features/ (shot_charts, box_scores, statistics)
  - archive/superseded_documentation/, phase_9/9.0_plus_minus/
  - phase_0/0.1_basketball_reference/documentation/
- **Created 14 README navigation files** for improved discoverability
- **Phase 5 cleanup: 11 → 3 essential files** (moved summaries to subdirectories)
- **Archived 17 superseded files** from Oct 2-19, 2025
- **See:** docs/DOCUMENTATION_REORGANIZATION_SUMMARY.md

**October 11, 2025 - Phase Index Reorganization:**
- Created phase index system (PHASE_N_INDEX.md) with 4-level hierarchy
- Reorganized phase files into subdirectories (phase_0/ through phase_7/)
- Sub-phase naming: N.M_name.md (e.g., 0.0_initial_data_collection.md)
- PROGRESS.md reduction: 1,094 → 391 lines (64% reduction)
- CLAUDE.md reduction: 546 → 395 lines (28% reduction)
- **Session start context reduced: 1,085 → 885 lines (18% additional reduction)**
- **Phase navigation context: -78% (17% → 3.75%)**

**October 8, 2025 - Context Optimization:**
- Created this index file for efficient navigation
- Consolidated CLAUDE_*.md files → CLAUDE_OPERATIONAL_GUIDE.md (4 files → 1)
- Extracted content from CLAUDE.md to specialized files (779 → 300 lines, 61% reduction)
- Added lazy-loading warnings to 6 large files (>800 lines)
- Split QUICKSTART.md → user commands + Claude-specific guide
- **Session start context reduced: 1,870 → 1,085 lines (42% reduction)**

---

*For questions about documentation organization, see CLAUDE.md or docs/DOCUMENTATION_SYSTEM.md*
