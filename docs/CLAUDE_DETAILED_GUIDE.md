# CLAUDE Detailed Guide

**Version:** 1.0  
**Last Updated:** November 5, 2025  
**Purpose:** Detailed explanations and context for Claude Code sessions

This document contains the detailed content that was moved from CLAUDE.md to reduce its size and improve session efficiency. This is a **reference document** - you don't need to read this at session start. Refer to it when you need deeper context on specific topics.

---

## Table of Contents

1. [Phase Index Documentation System](#phase-index-documentation-system)
2. [ML Framework Navigation](#ml-framework-navigation)
3. [Background Agent Operations](#background-agent-operations)
4. [The Automation Triad](#the-automation-triad)
5. [File Size Reference](#file-size-reference)
6. [Complete Development Examples](#complete-development-examples)
7. [Detailed Architecture](#detailed-architecture)
8. [Testing Framework Details](#testing-framework-details)

---

## Phase Index Documentation System

**✅ Implemented October 2025** - Hierarchical modular documentation system

### Overview

The project uses a hierarchical documentation system that breaks down complex work into manageable pieces:

- **PROGRESS.md** (~390 lines) - Master index, high-level status tracker
- **PHASE_N_INDEX.md** (~150 lines each) - Phase overview with sub-phase table
- **phase_N/** subdirectories - Individual sub-phase implementation files (300-800 lines)
- **Workflows** - Specific procedures and operations (200-400 lines)

### Phase Indexes Available

- **PHASE_0_INDEX.md** - Data collection and infrastructure (initial complete, expansion ready - 4 sub-phases)
- **PHASE_1_INDEX.md** through **PHASE_7_INDEX.md** - Various phases (1-2 sub-phases each)

### Sub-phase Naming Convention

**Format:** `N.MMMM_name.md` OR `N.MMMM_name/` (4-digit zero-padded format per ADR-010)

**Examples:**
- `0.0001_initial_data_collection.md`
- `1.0001_multi_source_integration.md`
- `5.0121_implement_ab_testing/`

**Format Details:** `N.MMMM` where:
- `N` = Phase number (0-9)
- `MMMM` = Sub-phase number (0001-9999, zero-padded to 4 digits)

### Rationale

The 4-digit format eliminates filesystem sorting ambiguity and supports up to 9,999 sub-phases per phase. This prevents confusion between single and double-digit numbers when viewing in file explorers.

**See:** `docs/adr/010-four-digit-subphase-numbering.md` for complete rationale.

### Power Directory Structure

**Definition:** Complex sub-phases that require multiple files use a power directory structure.

**When to Use:**
- Complex implementations requiring multiple files
- Sub-phases with tests, documentation, and code
- Implementations from book recommendations (rec_N, ml_systems_N)
- Any sub-phase with >500 lines of implementation code

**Required Files in Power Directories:**

1. **README.md** (REQUIRED)
   - Sub-phase header with parent phase link back
   - Status, priority, implementation ID
   - Overview and capabilities
   - Quick start code examples
   - Architecture details
   - Implementation files table
   - Related documentation links
   - Navigation (return to phase, prerequisites, integrates with)

2. **implement_*.py** (one or more implementation files)

3. **test_*.py** (one or more test suites)

4. **STATUS.md** (optional but recommended)
   - Detailed status and metrics

5. **RECOMMENDATIONS_FROM_BOOKS.md** (optional)
   - Source references from technical books

### Recent Power Directory Examples

**October 2025 implementations:**
- `phase_0/0.0001_basketball_reference/` - 13-tier structure, 234 data types
- `phase_0/0.0004_security_implementation/` - 13 security variations
- `phase_0/0.0005_data_extraction/` - Structured data output
- `phase_5/5.0001_feature_engineering/` - rec_11 - 80+ temporal features
- `phase_5/5.0002_model_versioning/` - ml_systems_1 - MLflow integration
- `phase_5/5.0019_drift_detection/` - ml_systems_2 - Data drift detection
- `phase_5/5.0020_panel_data/` - rec_22 - Temporal panel data system

**Reference Example:** `docs/phases/phase_0/0.0001_basketball_reference/README.md` (canonical example of power directory structure)

### Benefits

The phase index system provides:
- **64% reduction** in PROGRESS.md size
- **78% reduction** in phase navigation context
- **96% context** available for actual work
- **Consistent navigation** patterns across all phases

### Critical Project Scope Note

**⚠️ IMPORTANT:** This project is **NBA-only**. 

Sub-phases 0.0005 and 0.0006 are **NOT** awaiting NCAA/International data - they were permanently superseded by PostgreSQL implementations (0.0010/0.0011). 

**Never suggest** filling these with non-NBA data. Other sports will be built as **separate projects** in separate directories using this NBA infrastructure as a template.

---

## ML Framework Navigation

**✅ Implemented October 2025** - Phase 5 enhanced with 13 specialized ML frameworks

### Overview

Phase 5 was expanded with Block 2, implementing Recommendations #14-25 from technical books. This created 13 specialized ML frameworks that work together to provide enterprise-grade machine learning capabilities.

### Phase 5 Structure

- **PHASE_5_INDEX.md** - Phase overview with 14 sub-phases (5.0000 + 5.0001-5.0013)
- **phase_5/5.0000_machine_learning_models.md** - Initial ML pipeline
- **phase_5/5.{0001-0013}_*/README.md** - 13 ML framework subdirectories with comprehensive guides

### Framework Categories

#### 1. Optimization & Tuning
- **5.0001 - Hyperparameter Optimization:** Systematic hyperparameter tuning
- **5.0007 - Learning Curves:** Diagnose model learning behavior
- **5.0013 - Performance Profiling:** Optimize model performance

#### 2. Interpretability
- **5.0002 - Model Interpretation:** Understand what models learn
- **5.0012 - Model Explainability:** Explain predictions to stakeholders

#### 3. Data Management
- **5.0003 - Feature Store:** Centralized feature management
- **5.0005 - Feature Selection:** Identify most important features

#### 4. MLOps
- **5.0004 - Automated Retraining:** Keep models up-to-date automatically
- **5.0010 - Model Comparison:** Compare multiple models systematically

#### 5. Model Enhancement
- **5.0006 - Ensemble Learning:** Combine multiple models
- **5.0008 - Model Calibration:** Calibrate probability predictions

#### 6. Validation
- **5.0009 - Cross-Validation Strategies:** Robust model validation
- **5.0011 - Error Analysis:** Systematic error analysis

### When to Use Each Framework

#### 5.0001 (Hyperparameter Optimization)
**Use when:**
- Before production deployment
- Model performance has plateaued
- Need to squeeze out last few % of accuracy

**Don't use when:**
- Model is still underfitting badly (add features first)
- Don't have enough data for validation
- Computational budget is very limited

#### 5.0002 (Model Interpretation)
**Use when:**
- Debugging unexpected predictions
- Validating that model learned correct features
- Need to understand model behavior

**Don't use when:**
- Model is obviously broken (fix first)
- Only care about predictions, not interpretations

#### 5.0003 (Feature Store)
**Use when:**
- Multiple models share features
- Ready for production deployment
- Need consistency across models

**Don't use when:**
- Still prototyping
- Only one model in use
- Features change frequently

#### 5.0004 (Automated Retraining)
**Use when:**
- Deploying to production
- Data drift detection needed
- Model needs regular updates

**Don't use when:**
- Still in development
- Model is static/historical only
- Manual retraining is sufficient

#### 5.0005 (Feature Selection)
**Use when:**
- High-dimensional data (>100 features)
- Overfitting is an issue
- Need to reduce model complexity

**Don't use when:**
- Have few features (<20)
- Model is underfitting
- Need all features for interpretability

#### 5.0006 (Ensemble Learning)
**Use when:**
- Multiple strong models available
- Need prediction stability
- Can afford computational cost

**Don't use when:**
- Only one good model
- Latency is critical
- Interpretability required

#### 5.0007 (Learning Curves)
**Use when:**
- Diagnosing overfitting/underfitting
- Planning data collection efforts
- Understanding training dynamics

**Don't use when:**
- Model is obviously working well
- Data collection is fixed

#### 5.0008 (Model Calibration)
**Use when:**
- Need reliable probability estimates
- Building betting/risk models
- Combining multiple models

**Don't use when:**
- Only care about class predictions
- Probabilities not used downstream

#### 5.0009 (Cross-Validation Strategies)
**Use when:**
- **ALWAYS** for NBA temporal data (use time series CV)
- Need robust performance estimates
- Selecting between models

**Don't use when:**
- Data is truly IID (rare in NBA)
- Computational budget very limited

**CRITICAL:** Always use time series cross-validation for NBA data due to temporal structure.

#### 5.0010 (Model Comparison)
**Use when:**
- Selecting best model for production
- A/B testing different approaches
- Validating model improvements

**Don't use when:**
- Only one viable model
- Comparison criteria unclear

#### 5.0011 (Error Analysis)
**Use when:**
- Model underperforming on production data
- Systematic errors detected
- Need to identify model weaknesses

**Don't use when:**
- Model working satisfactorily
- Errors are random noise

#### 5.0012 (Model Explainability)
**Use when:**
- Communicating with stakeholders
- Regulatory compliance needed
- Building trust in predictions

**Don't use when:**
- Internal use only
- Speed is critical
- Model is obviously correct

#### 5.0013 (Performance Profiling)
**Use when:**
- Preparing for production deployment
- Latency/memory issues
- Need to optimize inference

**Don't use when:**
- Development phase
- Performance is acceptable
- Model hasn't been tested yet

### Navigation Pattern

```
PROGRESS.md → PHASE_5_INDEX.md → phase_5/5.XXXX_name/README.md → Execute framework
```

### What Each Framework README Includes

Every ML framework README contains:
1. **Overview & capabilities** - What the framework does
2. **When to use / When NOT to use** - Decision criteria
3. **How to use** - Quick start + advanced examples
4. **Integration with NBA temporal panel data** - NBA-specific patterns
5. **Common patterns for NBA use cases** - Practical examples
6. **Workflow references** - Related workflows
7. **Troubleshooting guide** - Common issues and solutions

### Total Implementation

- **Production code:** ~7,700 lines
- **Documentation:** ~5,500 lines
- **13 frameworks** fully integrated
- **100% test coverage** across all frameworks

---

## Background Agent Operations

**✅ COMPLETE - October 19, 2025** - Autonomous recommendation implementation system

### Mission

Implement 214 technical book recommendations to enhance prediction accuracy and system architecture through autonomous overnight deployment.

### System Overview

The Background Agent Operations system was designed to autonomously implement technical recommendations from authoritative sources (Wooldridge econometrics, Hastie ML, Goodfellow deep learning books) without human intervention.

### Final Results

**Completion Date:** October 19, 2025, 04:30-04:42 AM CDT  
**Duration:** 12 minutes  
**Success Rate:** 100% (214/214 recommendations, 1,284/1,284 tests)

### What Was Achieved

- ✅ **214 recommendations implemented** (100% completion)
- ✅ **1,284 tests passed** (100% pass rate)
- ✅ **212 individual git commits** created
- ✅ **Zero failures, zero escalations** throughout deployment
- ✅ **Enterprise-grade MLOps infrastructure** deployed
- ✅ **187 advanced ML/AI capabilities** added
- ✅ **~150,000+ lines** of production-ready code generated
- ✅ **Full documentation** auto-generated for all implementations

### Performance Metrics

| Metric | Original Estimate | Actual Result | Efficiency Gain |
|--------|------------------|---------------|-----------------|
| **Duration** | 2-4 weeks | 12 minutes | 1,440-2,880x faster |
| **Implementation Time** | 4,967 hours | 0.2 hours | 99.996% time savings |
| **Success Rate** | 85-90% expected | 100% achieved | Perfect execution |
| **Code Generated** | ~150,000 lines | ~150,000 lines | As estimated |
| **Tests Created** | 1,284 tests | 1,284 tests | 100% coverage |

### How It Worked

1. **Planning Phase** (Weeks before)
   - Analyzed 214 recommendations from technical books
   - Created implementation specifications
   - Designed test frameworks
   - Prepared autonomous execution system

2. **Execution Phase** (12 minutes overnight)
   - Autonomous agent activated at 4:30 AM
   - Implemented all 214 recommendations sequentially
   - Generated tests for each implementation
   - Created individual git commits
   - Validated each implementation
   - Completed at 4:42 AM

3. **Validation Phase** (Immediate)
   - All 1,284 tests passed
   - Zero failures detected
   - Full coverage verified
   - Documentation generated

### Checking Completion Status

**View final status:**
```bash
python scripts/automation/check_recommendation_status.py
```

**Expected output:**
```
Total Recommendations: 214
  ✅ Complete: 214 (100.0%)
  📋 Remaining: 0
```

### What This Enabled

The autonomous implementation system deployed:

1. **Advanced Econometrics** (Wooldridge recommendations)
   - Fixed effects models
   - Random effects models
   - Instrumental variables
   - Panel data methods
   - Heteroscedasticity corrections

2. **Machine Learning Systems** (Hastie recommendations)
   - Regularization techniques
   - Cross-validation strategies
   - Feature engineering frameworks
   - Model selection procedures
   - Ensemble methods

3. **Deep Learning** (Goodfellow recommendations)
   - Neural network architectures
   - Optimization algorithms
   - Regularization techniques
   - Training strategies

4. **MLOps Infrastructure**
   - Automated testing
   - Model versioning
   - Feature stores
   - Monitoring systems
   - Deployment pipelines

### Next Steps

The autonomous implementation system has completed its mission. Next steps involve:

1. **Integration Testing** - Test all 214 implementations together
2. **Production Deployment** - Deploy ML capabilities to AWS infrastructure
3. **Performance Optimization** - Scale for production workloads
4. **Accuracy Measurement** - Measure prediction improvements from new capabilities

### Documentation References

- **BOOK_RECOMMENDATIONS_PROGRESS.md** - Full completion summary
- **docs/claude_workflows/workflow_descriptions/54_autonomous_recommendation_implementation.md** - Deployment details
- **docs/BOOK_RECOMMENDATIONS_COMPLETION_SUMMARY.md** - Morning summary report

### Key Lessons

1. **Autonomous systems work** - When properly designed, autonomous implementation is viable
2. **Planning matters** - The 12-minute execution required weeks of planning
3. **Testing is critical** - 1,284 tests ensured perfect execution
4. **Documentation scales** - Auto-generated documentation maintained quality
5. **Human review still needed** - Integration and production deployment require human oversight

---

## The Automation Triad

**✅ COMPLETE - October 26, 2025** - Self-maintaining codebase infrastructure

### Overview

The codebase has three integrated automation systems that work together to maintain quality and prevent technical debt. These systems operate autonomously 24/7 to ensure data quality, code quality, and system health.

### System 1: DIMS - Data Inventory Management System

**Purpose:** Track and validate data metrics across the entire system

**Detailed Capabilities:**

1. **Metrics Tracking**
   - PostgreSQL-backed storage of 25+ metrics
   - Historical tracking of all key data points
   - Automated baseline creation and updates
   - Drift detection with configurable thresholds

2. **Verification System**
   - Session start verification (auto-runs)
   - Session end verification (auto-runs)
   - On-demand verification anytime
   - Detailed reports of any discrepancies

3. **Integration Points**
   - Session manager integration
   - Jupyter notebook integration for analysis
   - ADCE health monitoring integration
   - PRMS integration for code quality

4. **Reporting**
   - Markdown reports (human-readable)
   - JSON reports (machine-readable)
   - HTML dashboards (visual)
   - Trend analysis over time

**Status:** ✅ Production (v3.1.0)  
**Documentation:** `docs/monitoring/dims/` and Workflow #56  
**Usage:** `python scripts/monitoring/dims_cli.py [verify|update|report]`

**Configuration:**
```yaml
# config/dims_config.yaml
metrics:
  - name: total_games
    query: "SELECT COUNT(*) FROM games"
    threshold: 0.01  # 1% deviation allowed
  
  - name: total_play_by_play
    query: "SELECT COUNT(*) FROM play_by_play"
    threshold: 0.001  # 0.1% deviation allowed
  
  # ... 23 more metrics
```

### System 2: ADCE - Autonomous Data Collection Engine

**Purpose:** 24/7 self-healing data collection and scraping

**Detailed Capabilities:**

1. **Multi-Source Orchestration**
   - **ESPN scraper** - Primary play-by-play source
   - **NBA API scraper** - Advanced stats and tracking data
   - **Basketball Reference scraper** - Historical data and player info
   - **hoopR scraper** - Alternative play-by-play source
   - Automatic source selection based on data gaps

2. **Error Recovery**
   - Exponential backoff retry logic
   - Automatic failover between sources
   - Rate limit detection and adaptation
   - Circuit breaker pattern for failing sources

3. **Health Monitoring**
   - Real-time health checks
   - Automated alerting on failures
   - Performance metrics tracking
   - Success rate monitoring per source

4. **Zero-Downtime Operation**
   - Graceful degradation
   - No single point of failure
   - Automatic restart on crashes
   - Continuous operation guarantees

**Status:** ✅ Production (Phase 0.0018)  
**Documentation:** `docs/data_collection/scrapers/` and Workflow #42  
**Usage:** `python scripts/autonomous/autonomous_cli.py [start|stop|status|health]`

**Operation Modes:**
```bash
# Start autonomous collection
python scripts/autonomous/autonomous_cli.py start

# Stop gracefully
python scripts/autonomous/autonomous_cli.py stop

# Check health
python scripts/autonomous/autonomous_cli.py health

# Get detailed status
python scripts/autonomous/autonomous_cli.py status --verbose
```

### System 3: PRMS - Path Reference Management System

**Purpose:** Prevent outdated path references and maintain code quality

**Detailed Capabilities:**

1. **Automated Scanning**
   - Scans all Python, Markdown, YAML, JSON files
   - Identifies all path references in codebase
   - Classifies references by type and context
   - Generates comprehensive audit reports

2. **Intelligent Classification**
   - **MUST_UPDATE** (≥80% confidence) - Definitely outdated
   - **SKIP** - Intentionally old (archives, examples)
   - **MANUAL_REVIEW** (<80% confidence) - Needs human review
   - Context-aware classification using heuristics

3. **Auto-Correction**
   - Fixes high-confidence outdated references
   - Preserves formatting and context
   - Creates backup before changes
   - Generates diff reports

4. **Pre-Commit Integration**
   - Git hook blocks commits with outdated references
   - Provides clear error messages
   - Suggests fixes automatically
   - Allows informed bypasses when appropriate

5. **Session Integration**
   - Runs automatically at session start
   - Validates code quality at session end
   - Integrates with session manager workflow
   - Reports issues in unified dashboard

6. **DIMS Integration**
   - Path reference health tracked as DIMS metric
   - Historical trend analysis
   - Alerts on degrading code quality
   - Dashboard visualization

**Status:** ✅ Production (v1.0.0)  
**Documentation:** Workflow #60  
**Usage:** `python scripts/maintenance/prms_cli.py [scan|fix|report]`

**Command Examples:**
```bash
# Scan for outdated references
python scripts/maintenance/prms_cli.py scan

# Auto-fix high-confidence issues
python scripts/maintenance/prms_cli.py fix --confidence 80

# Generate detailed report
python scripts/maintenance/prms_cli.py report --format html

# Check specific files
python scripts/maintenance/prms_cli.py scan --path scripts/etl/
```

**Pre-commit Hook:**
```bash
# Install hook
python scripts/maintenance/prms_cli.py install-hook

# The hook will automatically:
# 1. Scan staged files for outdated references
# 2. Block commit if issues found
# 3. Provide clear error messages
# 4. Suggest fixes
```

### Integration: Self-Maintaining Codebase

The three systems work together to create a self-maintaining codebase:

1. **Data Integrity (DIMS)**
   - Tracks all key metrics
   - Detects data drift automatically
   - Validates data quality continuously
   - Provides single-pane-of-glass health view

2. **Data Freshness (ADCE)**
   - Keeps data collection running 24/7
   - Automatically recovers from failures
   - Adapts to changing conditions
   - Ensures continuous data flow

3. **Code Quality (PRMS)**
   - Prevents path reference drift
   - Maintains code maintainability
   - Blocks commits with quality issues
   - Provides automated fixes

### Benefits

**Reduced Manual Intervention:**
- DIMS: Automatic health checks (no manual verification needed)
- ADCE: Self-healing data collection (no manual scraper management)
- PRMS: Prevents technical debt (no manual path updates)

**Unified Dashboard:**
- Single view of all system health metrics
- Integrated alerting across all systems
- Historical trend analysis
- Proactive issue detection

**Quality Guarantees:**
- Data quality maintained automatically
- Code quality enforced automatically
- System health monitored continuously
- Issues caught before they become problems

### Quick Reference Commands

```bash
# Check all systems at once
python scripts/monitoring/dims_cli.py verify          # DIMS health
python scripts/autonomous/autonomous_cli.py status    # ADCE status
python scripts/maintenance/prms_cli.py scan           # PRMS scan

# Session management (runs all checks automatically)
bash scripts/shell/session_manager.sh start
bash scripts/shell/session_manager.sh end
```

### Monitoring Dashboard

The unified dashboard shows:
- **DIMS Metrics:** All 25+ data metrics with status
- **ADCE Status:** Scraper health and success rates
- **PRMS Health:** Path reference quality score
- **Historical Trends:** All metrics over time
- **Alerts:** Active issues requiring attention

Access dashboard:
```bash
python scripts/monitoring/unified_dashboard.py
```

---

## File Size Reference

Complete file size reference for context planning. This helps you understand which files to read fully vs. grep/search only.

### Core Files (Read Every Session)

| File | Lines | % Context | Notes |
|------|-------|-----------|-------|
| CLAUDE.md | ~500 | 2.5% | Core instructions (v4.0, updated for v2.0) |
| PROGRESS.md | ~390 | 1.95% | Current project state |
| docs/README.md | ~100 | 0.5% | Documentation index |
| **Total** | **~990** | **4.95%** | **Leaves 95% for work** |

### v2.0 Documentation (Read As Needed)

| File | Lines | % Context | When to Read |
|------|-------|-----------|--------------|
| FINAL_DOCUMENTATION.md | ~1,000 | 5% | Complete v2.0 architecture reference |
| PRODUCTION_DEPLOYMENT_GUIDE.md | ~800 | 4% | When deploying to production |
| PROJECT_COMPLETION_REPORT.md | ~1,200 | 6% | Project history and achievements |
| QUICK_REFERENCE_GUIDE.md | ~400 | 2% | Quick v2.0 package usage |

### Phase Files (Read When Working on Phase)

| File Type | Lines | % Context | Notes |
|-----------|-------|-----------|-------|
| PHASE_N_INDEX.md | ~150 | 0.75% | Phase overview + sub-phase table |
| Sub-phase files | 300-800 | 1.5-4% | Implementation details |
| Workflows | 200-400 | 1-2% | Specific procedures |

### Large Files (Grep Only - Don't Read Fully)

| File | Lines | % Context | Strategy |
|------|-------|-----------|----------|
| TROUBLESHOOTING.md | 1,025 | 5% | **Grep for keywords**, don't read fully |
| LESSONS_LEARNED.md | 1,002 | 5% | Grep for relevant lessons |
| TEMPORAL_QUERY_GUIDE.md | 996 | 5% | Reference when doing temporal queries |
| TESTING.md | 862 | 4% | Reference when setting up tests |
| STYLE_GUIDE.md | 846 | 4% | Reference when writing code |
| COMMAND_LOG.md | 500+ | 2.5%+ | Search for specific commands |

### Configuration Files (Quick Reference)

| File | Lines | % Context | Notes |
|------|-------|-----------|-------|
| .env | 20-30 | 0.1% | Don't commit! |
| config/*.yaml | 50-200 | 0.25-1% | Read specific configs as needed |
| QUICKSTART.md | ~400 | 2% | Command reference |

### Documentation Structure

| Directory | File Count | Total Lines | Notes |
|-----------|------------|-------------|-------|
| docs/phases/ | 50+ | 15,000+ | Don't read all at once |
| docs/claude_workflows/ | 60+ | 24,000+ | Reference specific workflows |
| docs/adr/ | 20+ | 5,000+ | Architecture decisions |
| docs/data_sources/ | 10+ | 3,000+ | Data source details |

### Context Planning Examples

**Minimal session (4.95% context):**
```
CLAUDE.md (500 lines)
PROGRESS.md (390 lines)
docs/README.md (100 lines)
Total: 990 lines
```

**Light session (7.45% context):**
```
Core files (990 lines)
+ PHASE_5_INDEX.md (150 lines)
+ Sub-phase file (500 lines)
Total: 1,640 lines
```

**Moderate session (10.45% context):**
```
Core files (990 lines)
+ Phase index (150 lines)
+ Sub-phase file (500 lines)
+ 2 workflows (400 lines)
Total: 2,040 lines
```

**Heavy session (16.45% context):**
```
Core files (990 lines)
+ 2 phase indexes (300 lines)
+ 2 sub-phase files (1,000 lines)
+ 2 workflows (400 lines)
+ FINAL_DOCUMENTATION.md (1,000 lines)
Total: 3,690 lines
```

**Maximum recommended (20% context):**
```
Don't exceed 4,000 lines (20,000 tokens)
If approaching limit:
- Stop reading new files
- Commit work
- Update PROGRESS.md
- End session
- Start fresh
```

### Grep Strategies

For large files, use targeted searches:

```bash
# Find scraper errors
grep -i "error" TROUBLESHOOTING.md

# Find specific commands
grep "pytest" COMMAND_LOG.md

# Find temporal query examples
grep -A 5 "example" TEMPORAL_QUERY_GUIDE.md

# Find style guidelines for functions
grep -A 10 "function" STYLE_GUIDE.md
```

---

## Complete Development Examples

Detailed code examples for common development patterns in the v2.0 package.

### Database Operations

**Basic Query:**
```python
from nba_simulator.database import execute_query

# Simple query
results = await execute_query("SELECT * FROM games WHERE season = 2024")
for game in results:
    print(f"{game['game_date']}: {game['home_team']} vs {game['away_team']}")

# Parameterized query
query = "SELECT * FROM games WHERE season = ? AND game_date > ?"
results = await execute_query(query, (2024, "2024-10-01"))
```

**Connection Pooling:**
```python
from nba_simulator.database import DatabaseConnection

db = DatabaseConnection()

# Use context manager for automatic connection handling
async with db.get_connection() as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM games")
        count = await cur.fetchone()
        print(f"Total games: {count[0]}")
```

**Bulk Operations:**
```python
from nba_simulator.database import execute_query

# Bulk insert
games_data = [
    ("2024-10-01", "LAL", "BOS", ...),
    ("2024-10-02", "GSW", "LAC", ...),
    # ... more games
]

query = """
    INSERT INTO games (game_date, home_team, away_team, ...)
    VALUES (?, ?, ?, ...)
"""

for game in games_data:
    await execute_query(query, game)
```

### ETL Operations

**ESPN Scraper:**
```python
from nba_simulator.etl.extractors.espn import ESPNScraper
from nba_simulator.utils import logger

# Initialize scraper
scraper = ESPNScraper()

# Scrape game data
game_id = "401584948"
try:
    play_by_play = await scraper.scrape_play_by_play(game_id)
    box_score = await scraper.scrape_box_score(game_id)
    
    logger.info(f"Scraped {len(play_by_play)} plays")
    logger.info(f"Got box score for {box_score['home_team']} vs {box_score['away_team']}")
except Exception as e:
    logger.error(f"Scraping failed: {e}")
```

**Basketball Reference Scraper:**
```python
from nba_simulator.etl.extractors.basketball_reference import BBRefScraper

scraper = BBRefScraper()

# Scrape player stats
player_url = "https://www.basketball-reference.com/players/j/jamesle01.html"
stats = await scraper.scrape_player_stats(player_url)

print(f"Career stats for {stats['player_name']}:")
print(f"  Points: {stats['total_points']}")
print(f"  Rebounds: {stats['total_rebounds']}")
print(f"  Assists: {stats['total_assists']}")
```

### Agent Operations

**Master Agent:**
```python
from nba_simulator.agents import MasterAgent
from nba_simulator.utils import logger

# Initialize and start master agent
agent = MasterAgent()

try:
    # Start autonomous operation
    await agent.start()
    
    # Agent will coordinate:
    # - Data collection
    # - Quality checks
    # - Integration
    # - Deduplication
    # - Monitoring
    
    # Check status
    status = await agent.get_status()
    logger.info(f"Agent status: {status}")
    
except KeyboardInterrupt:
    # Graceful shutdown
    await agent.stop()
    logger.info("Agent stopped")
```

**Quality Agent:**
```python
from nba_simulator.agents import QualityAgent

agent = QualityAgent()

# Run quality checks
results = await agent.run_checks([
    "completeness",
    "accuracy",
    "consistency",
    "timeliness"
])

for check, result in results.items():
    if result['passed']:
        print(f"✅ {check}: PASSED")
    else:
        print(f"❌ {check}: FAILED - {result['reason']}")
```

### Workflow Orchestration

**Create and Execute Workflow:**
```python
from nba_simulator.workflows import WorkflowOrchestrator, Workflow, WorkflowStep

# Create orchestrator
orchestrator = WorkflowOrchestrator()

# Define workflow steps
steps = [
    WorkflowStep(
        name="scrape_data",
        handler=scrape_espn_data,
        dependencies=[]
    ),
    WorkflowStep(
        name="validate_data",
        handler=validate_scraped_data,
        dependencies=["scrape_data"]
    ),
    WorkflowStep(
        name="load_to_db",
        handler=load_to_database,
        dependencies=["validate_data"]
    )
]

# Create workflow
workflow = orchestrator.create_workflow(
    name="data_collection",
    steps=steps
)

# Execute
try:
    result = await orchestrator.execute_workflow(workflow.id)
    print(f"Workflow completed: {result}")
except Exception as e:
    print(f"Workflow failed: {e}")
    # Automatic rollback on failure
```

**ADCE Coordinator:**
```python
from nba_simulator.workflows import ADCECoordinator, WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
coordinator = ADCECoordinator(orchestrator)

# Start autonomous data collection
await coordinator.start()

# Monitor status
status = await coordinator.get_status()
print(f"Collection active: {status.is_active}")
print(f"Last run: {status.last_run}")
print(f"Success rate: {status.success_rate}%")

# Stop when done
await coordinator.stop()
```

### Configuration Management

**Load Configuration:**
```python
from nba_simulator.config import config

# Database config
db_config = config.load_database_config()
print(f"Connecting to {db_config['host']}:{db_config['port']}")

# S3 config
s3_config = config.load_s3_config()
print(f"S3 bucket: {s3_config['bucket']}")

# AWS config
aws_config = config.load_aws_config()
print(f"Region: {aws_config['region']}")
```

**Custom Configuration:**
```python
from nba_simulator.config import ConfigLoader

# Create custom loader
config = ConfigLoader(legacy_mode=False)  # Use new YAML format

# Load config
db_config = config.load_database_config()
```

### Logging

**Basic Logging:**
```python
from nba_simulator.utils import logger

logger.info("Starting data collection")
logger.debug("Detailed debug information")
logger.warning("Something might be wrong")
logger.error("An error occurred")
logger.critical("Critical failure!")
```

**Custom Logger:**
```python
from nba_simulator.utils import setup_logging

# Create custom logger
my_logger = setup_logging(
    name="my_script",
    level="DEBUG",
    log_dir="/custom/path/logs",
    console=True,
    file=True
)

my_logger.info("Using custom logger")
```

### Testing

**Unit Test Example:**
```python
import pytest
from nba_simulator.etl.extractors.espn import ESPNScraper

@pytest.fixture
async def scraper():
    return ESPNScraper()

@pytest.mark.asyncio
async def test_scrape_play_by_play(scraper):
    """Test ESPN play-by-play scraping"""
    game_id = "401584948"
    result = await scraper.scrape_play_by_play(game_id)
    
    assert result is not None
    assert len(result) > 0
    assert "game_id" in result[0]
    assert "play_description" in result[0]

@pytest.mark.asyncio
async def test_scrape_invalid_game(scraper):
    """Test scraping with invalid game ID"""
    with pytest.raises(ValueError):
        await scraper.scrape_play_by_play("invalid")
```

**Integration Test Example:**
```python
import pytest
from nba_simulator.workflows import WorkflowOrchestrator

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_data_pipeline():
    """Test complete data collection pipeline"""
    orchestrator = WorkflowOrchestrator()
    
    # Create workflow
    workflow = orchestrator.create_workflow(
        name="test_pipeline",
        steps=[...steps...]
    )
    
    # Execute
    result = await orchestrator.execute_workflow(workflow.id)
    
    # Verify
    assert result.status == "completed"
    assert result.steps_completed == len(result.steps)
```

---

## Detailed Architecture

Complete system architecture details beyond the high-level overview in README.md.

### Package Structure Details

The `nba_simulator/` package follows a modular architecture with clear separation of concerns:

**Core Modules:**
- `config/` - Configuration management (backward compatible)
- `database/` - Database layer with connection pooling
- `utils/` - Common utilities (logging, constants, helpers)

**Data Pipeline Modules:**
- `etl/` - Extract, Transform, Load operations
  - `base/` - Base classes and common functionality
  - `extractors/` - Data source-specific extractors
  - `transformers/` - Data transformation logic
  - `loaders/` - Database and S3 loaders
  - `validation/` - Data quality validation

**Autonomous System Modules:**
- `agents/` - Autonomous agent implementations
  - 8 specialized agents for different tasks
  - Base agent with common functionality
  - Agent coordination and communication

- `workflows/` - Workflow orchestration
  - Template method pattern for workflows
  - Dispatcher for task distribution
  - Orchestrator for multi-step coordination
  - ADCE integration for autonomous operation

**Quality Assurance Modules:**
- `monitoring/` - System monitoring
  - DIMS integration
  - Health checks
  - Metrics collection
  - Alerting

- `validation/` - Data validation
  - Schema validation
  - Data quality checks
  - Cross-source validation

### Design Patterns Used

1. **Template Method Pattern** (Base Workflow)
   - Abstract workflow defines algorithm structure
   - Concrete workflows implement specific steps
   - Ensures consistent workflow execution

2. **Strategy Pattern** (Extractors)
   - Different extraction strategies for each data source
   - Pluggable extractors
   - Easy to add new sources

3. **Observer Pattern** (Monitoring)
   - Agents notify monitors of events
   - Monitors aggregate and report metrics
   - Decoupled monitoring from operations

4. **Factory Pattern** (Workflow Creation)
   - Orchestrator creates workflows
   - Centralized workflow management
   - Consistent workflow initialization

5. **Singleton Pattern** (Database Connection)
   - Single connection pool per process
   - Efficient resource usage
   - Thread-safe access

### Data Flow

```
1. Data Sources (ESPN, NBA API, etc.)
   ↓
2. Extractors (scrape/fetch data)
   ↓
3. Transformers (clean/normalize)
   ↓
4. Validators (quality checks)
   ↓
5. Loaders (persist to DB/S3)
   ↓
6. Monitoring (track metrics)
```

### Agent Coordination

```
Master Agent
├── Quality Agent (data quality)
├── Integration Agent (data integration)
├── NBA Stats Agent (NBA API data)
├── Deduplication Agent (remove duplicates)
├── Historical Agent (historical backfill)
├── hoopR Agent (hoopR data)
└── BBRef Agent (Basketball Reference)
```

### Workflow Orchestration

```
Orchestrator
├── Create Workflow
├── Validate Steps
├── Execute Steps (in order)
│   ├── Check dependencies
│   ├── Run step
│   ├── Validate output
│   └── Update state
├── Monitor Progress
└── Handle Failures
    ├── Rollback
    ├── Retry
    └── Alert
```

### Error Handling Strategy

1. **Retry Logic**
   - Exponential backoff for transient errors
   - Maximum retry attempts configurable
   - Circuit breaker for persistent failures

2. **Fallback Mechanisms**
   - Multiple data sources (ESPN, hoopR)
   - Graceful degradation
   - Cached data when fresh data unavailable

3. **Alerting**
   - Critical errors alert immediately
   - Warning errors aggregate and report
   - Info errors log only

---

## Testing Framework Details

Complete testing strategy and implementation details.

### Test Organization

```
tests/
├── unit/                   # 150+ unit tests
│   ├── test_agents/        # Agent tests
│   ├── test_workflows/     # Workflow tests
│   ├── test_etl/          # ETL tests
│   └── test_database/     # Database tests
│
├── integration/            # 66+ integration tests
│   ├── test_integration_e2e.py  # End-to-end tests
│   ├── test_pipelines/    # Pipeline integration
│   └── test_workflows/    # Workflow integration
│
└── validators/            # Validation tests
    └── phase_0/          # Phase-specific validators
```

### Testing Principles

1. **Test Coverage**
   - Maintain 95%+ coverage
   - Test all critical paths
   - Test error conditions
   - Test edge cases

2. **Test Independence**
   - Tests don't depend on each other
   - Each test sets up its own data
   - Tests can run in any order

3. **Test Speed**
   - Unit tests: <1s each
   - Integration tests: <10s each
   - E2E tests: <60s each

4. **Test Clarity**
   - Clear test names
   - Arrange-Act-Assert pattern
   - Minimal setup/teardown
   - Good error messages

### Running Tests

**All Tests:**
```bash
pytest tests/ -v --cov
```

**Specific Suites:**
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_agents/test_master_agent.py -v

# Specific test function
pytest tests/unit/test_agents/test_master_agent.py::test_start_agent -v
```

**Coverage Reports:**
```bash
# Terminal report
pytest tests/ --cov=nba_simulator --cov-report=term

# HTML report
pytest tests/ --cov=nba_simulator --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest tests/ --cov=nba_simulator --cov-report=xml
```

**Test Markers:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Writing Tests

**Unit Test Template:**
```python
import pytest
from nba_simulator.module import Class

@pytest.fixture
def instance():
    """Create test instance"""
    return Class()

def test_function(instance):
    """Test specific function"""
    # Arrange
    input_data = {...}
    expected = {...}
    
    # Act
    result = instance.function(input_data)
    
    # Assert
    assert result == expected
```

**Integration Test Template:**
```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline():
    """Test complete pipeline"""
    # Arrange
    pipeline = create_pipeline()
    
    # Act
    result = await pipeline.execute()
    
    # Assert
    assert result.status == "success"
    assert result.records_processed > 0
```

**Async Test Template:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    # Arrange
    async_obj = AsyncObject()
    
    # Act
    result = await async_obj.async_method()
    
    # Assert
    assert result is not None
```

### Test Fixtures

**Common Fixtures:**
```python
# conftest.py

@pytest.fixture
async def db_connection():
    """Provide database connection"""
    from nba_simulator.database import DatabaseConnection
    db = DatabaseConnection()
    yield db
    await db.close()

@pytest.fixture
def sample_game_data():
    """Provide sample game data"""
    return {
        "game_id": "401584948",
        "game_date": "2024-10-01",
        "home_team": "LAL",
        "away_team": "BOS",
        # ... more data
    }

@pytest.fixture
async def scraper():
    """Provide scraper instance"""
    from nba_simulator.etl.extractors.espn import ESPNScraper
    return ESPNScraper()
```

### Mocking

**Mock External Services:**
```python
from unittest.mock import Mock, patch

@patch('nba_simulator.etl.extractors.espn.requests.get')
def test_scraper_with_mock(mock_get):
    """Test scraper with mocked HTTP"""
    # Setup mock
    mock_response = Mock()
    mock_response.json.return_value = {...}
    mock_get.return_value = mock_response
    
    # Test
    scraper = ESPNScraper()
    result = scraper.scrape_game("123")
    
    # Verify
    assert result is not None
    mock_get.assert_called_once()
```

---

**Last Updated:** November 5, 2025  
**Version:** 1.0  
**Maintained by:** Ryan Ranft

For quick reference information, see CLAUDE.md in the project root.
