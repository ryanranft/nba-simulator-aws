# Documentation Index - Quick Reference

**Last Updated:** October 8, 2025

This index helps Claude Code and developers find the right documentation efficiently. Files are organized by task type and size to optimize context usage.

---

## Quick Navigation

### Starting a New Session
1. Read **CLAUDE.md** (~300 lines) - Core instructions and navigation
2. Read **PROGRESS.md** (~685 lines) - Current project state
3. Read **this file** (~100 lines) - Documentation map
4. **Total: ~1,085 lines** (5% of 200K context budget)

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
- **docs/phases/PHASE_0_DATA_COLLECTION.md** - Data collection (✅ Complete)
- **docs/phases/PHASE_1_DATA_QUALITY.md** - Multi-source integration (⏸️ Pending)
- **docs/phases/PHASE_2_AWS_GLUE.md** - ETL pipeline (✅ Complete)
- **docs/phases/PHASE_3_DATABASE.md** - RDS setup (✅ Complete)
- **docs/phases/PHASE_4_SIMULATION_ENGINE.md** - Simulation (✅ Complete)
- **docs/phases/PHASE_5_MACHINE_LEARNING.md** - ML models (✅ Complete)
- **docs/phases/PHASE_6_ENHANCEMENTS.md** - Advanced features (✅ Complete)
- **docs/phases/PHASE_7_BETTING_ODDS.md** - Betting odds (⏸️ Optional)

### Workflows
- **docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md** - Workflow index (38 workflows)
- **docs/claude_workflows/workflow_descriptions/** - Individual workflow procedures

### Daily Operations
- **QUICKSTART.md** - Common commands, daily workflow, make targets
- **docs/CLAUDE_QUICK_COMMANDS.md** - Claude-specific command patterns
- **docs/SCRAPER_MANAGEMENT.md** - Scraper operations guide
- **docs/SCRAPER_MONITORING_SYSTEM.md** - Monitoring tools and procedures

### Setup & Configuration
- **docs/SETUP.md** - Environment setup, AWS configuration, credentials
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
- **CLAUDE.md** (300 lines after optimization)
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
- **PROGRESS.md** (685 lines)
- **Phase files** (300-500 lines each)
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
- CLAUDE.md (~300 lines)
- PROGRESS.md (~685 lines)
- docs/README.md (~100 lines)
- **Total: ~1,085 lines (5% context)**

### Tier 2 - Read When Needed (Task-Specific)
- Specific phase file for current work (~400-500 lines)
- Referenced workflows for current sub-phase (~300 lines each)
- CLAUDE_OPERATIONAL_GUIDE.md (~200 lines) - only if doing session management
- **Total: +900-1,000 lines per task**

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

---

## Optimization Strategies

**For Claude Code:**
1. **Start lean:** 1,085 lines (Tier 1) = 5% context
2. **Add incrementally:** Read phase + workflows as needed
3. **Search, don't read:** Use grep for large files
4. **Track what you've read:** Don't re-read files in same session
5. **Target: Stay under 4,000 lines** per session (comfortable limit)

**Context Budget Examples:**
- **Minimal session:** 1,085 lines (orientation only)
- **Light work:** 1,985 lines (+ 1 phase + 1 workflow)
- **Moderate work:** 2,585 lines (+ 1 phase + 3 workflows)
- **Heavy work:** 3,485 lines (+ 2 phases + 3 workflows)
- **Maximum recommended:** 4,000 lines (stay under 200K tokens)

---

## Recent Changes

**October 8, 2025 - Context Optimization:**
- Created this index file for efficient navigation
- Consolidated CLAUDE_*.md files → CLAUDE_OPERATIONAL_GUIDE.md (4 files → 1)
- Extracted content from CLAUDE.md to specialized files (779 → 300 lines, 61% reduction)
- Added lazy-loading warnings to 6 large files (>800 lines)
- Split QUICKSTART.md → user commands + Claude-specific guide
- **Session start context reduced: 1,870 → 1,085 lines (42% reduction)**

---

*For questions about documentation organization, see CLAUDE.md or docs/DOCUMENTATION_SYSTEM.md*
