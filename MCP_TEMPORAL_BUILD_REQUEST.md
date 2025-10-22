# MCP Request: Complete Temporal Data Build Implementation Plan

**Date:** October 20, 2025
**Purpose:** Request comprehensive implementation plan to finish NBA temporal panel data system
**Target:** MCP (Model Context Protocol) Server
**Scope:** All temporal infrastructure combined

---

## Executive Summary

This is a request for a detailed, actionable implementation plan to complete a sophisticated NBA temporal panel data system. The system enables querying cumulative NBA statistics at any exact moment in time with millisecond precision.

**Current Status:** Core infrastructure complete (Phases 0-6), with advanced ML capabilities deployed
**Remaining Work:** Complete snapshot generation pipeline, expand data sources, integrate multi-source data
**Estimated Completion:** 8-12 weeks of implementation work
**Budget:** $150/month AWS infrastructure (currently at $41.53/month)

---

## Section A: Project Context & Vision

### What Is This System?

**Temporal Panel Data System for NBA Basketball**

Unlike traditional sports analytics that provide aggregated statistics, this system maintains a complete temporal history of every NBA game, allowing queries like:

> "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"

The system responds with:
- Exact cumulative statistics up to that millisecond
- His age down to the second
- Game context (score, quarter, time remaining)
- On-court status and lineup composition
- Advanced metrics calculated at that moment

### Core Capabilities Achieved

✅ **Multi-Source Data Collection** (Phase 0)
- 172,600 files across 5 data sources
- ESPN: 70,522 files (1993-2025 play-by-play, box scores)
- NBA API: 22,256 files (2020-2025)
- hoopR: 96 files (2002-2025)
- Basketball Reference: 444 files (1946-2025)
- Kaggle: Historical data (1946-2020)
- Total: ~122 GB raw data in S3

✅ **RDS PostgreSQL Database** (Phase 3)
- 48.4M rows across 20 tables
- 6.78M play-by-play events (2004-2021)
- 408K player box scores
- 44,828 games (1993-2025)
- Optimized for temporal queries

✅ **Machine Learning Models** (Phase 5)
- 75% prediction accuracy with XGBoost
- 214 technical book recommendations implemented (100% success)
- 18 ML frameworks (hyperparameter optimization, feature engineering, model interpretation, etc.)
- 187 ML/AI capabilities (BERT, LoRA, GANs, attention mechanisms, etc.)
- ~150,000 lines of production code generated autonomously

✅ **Advanced Features** (Phase 6)
- Plus/Minus system with possession-based partitions
- 171 ML features (110 temporal + 21 cumulative + 26 plus/minus + 14 base)
- Lineup optimization models
- Player impact prediction

✅ **MLOps Infrastructure** (Completed Oct 2025)
- MLflow model versioning
- Data drift detection
- Automated retraining pipelines
- Comprehensive monitoring

### Architecture Overview

```
Data Sources → S3 Data Lake → RDS PostgreSQL → Temporal Queries
                                    ↓
                            ML Feature Pipeline
                                    ↓
                            Prediction Models
                                    ↓
                         Betting/Analytics API
```

**Key Design Decisions:**
- RDS PostgreSQL instead of Redshift (saves $200-600/month)
- Extract 10% of JSON fields (saves 90% storage)
- Temporal indexing for millisecond-precision queries
- Multi-source conflict resolution strategy

---

## Section B: Current State Analysis

### Completed Phases (✅)

#### Phase 0: Data Collection (COMPLETE)
- **Status:** Initial collection complete, expansion ready
- **Sub-phases:**
  - 0.0: Initial ESPN collection (147K files, 119GB)
  - 0.1: Basketball Reference (444 files, baseline data)
  - 0.2: ESPN Additional (missing PBP for 3,230 games)
  - 0.3: NBA API Enhanced (22,256 files)
- **Next:** Expand Basketball Reference (13 tiers, 234 data types)

#### Phase 2: ETL Pipeline (COMPLETE)
- Bypassed AWS Glue (cost savings)
- Local ETL processing operational
- Multi-source merger implemented

#### Phase 3: Database Infrastructure (COMPLETE)
- RDS PostgreSQL db.t3.small operational
- 20 tables with 48.4M rows
- Cost: $29/month

#### Phase 4: Simulation Engine (COMPLETE)
- EC2 t3.small deployed (8hrs/day)
- Cost: $6.59/month

#### Phase 5: Machine Learning (COMPLETE)
- **19 Sub-phases** (5.0 + 5.1-5.18)
- XGBoost models with 75% accuracy
- 214 book recommendations implemented
- 18 ML frameworks operational
- Expected accuracy after plus/minus integration: 72-75%

#### Phase 6: Enhancements (COMPLETE)
- Monitoring dashboards
- CloudWatch alerts
- Cost: $3/month

### In Progress Phases (🔄)

#### Phase 9: Play-by-Play to Box Score Generation

**Overall Status:** 8 sub-phases defined, 2 complete, 1 in progress (60%)

##### 9.0: System Architecture (✅ COMPLETE)
- Database schema designed (510 lines SQL)
- 4 tables: game_state_snapshots, player_snapshot_stats, quarter_box_scores, box_score_verification
- 2 views: latest_snapshots, verification_summary
- Data structures: PlayerStats, TeamStats, BoxScoreSnapshot, VerificationResult
- Base processor class implemented (514 lines)

##### 9.1: ESPN Processor (✅ COMPLETE)
- ESPN processor implemented (610 lines)
- S3 integration with local caching
- Parses 15+ event types
- Tracks on-court players
- Batch processing for 44,826 games ready

##### 9.2: hoopR Processor (✅ COMPLETE)
- Cross-validation with ESPN
- Handles 13M rows of play-by-play data

##### Option 2A: Snapshot Generation Pipeline (🔄 60% COMPLETE, 4-6 hours remaining)

**Status:** Core pipeline working, needs fixes before production

**What Works:**
- ✅ Play text parser (800 lines, 56.7% success rate on real data)
- ✅ Game state tracker (600 lines, stats tracking accurate)
- ✅ RDS PBP processor (500 lines, 1,247 events/second)
- ✅ Player name extraction from play text
- ✅ Plus/minus calculation accurate
- ✅ End-to-end processing validated

**Known Issues:**
1. ❌ **Substitution handling broken** (HIGH PRIORITY)
   - Lineups grow from 5 to 19 players instead of staying at 5
   - Root cause: Inferred starting lineups don't match actual starters
   - Estimated fix: 2-3 hours

2. ⚠️ **Parser coverage 56.7%** (MEDIUM PRIORITY)
   - 189/436 events failed to parse
   - Missing: Team rebounds, violations, reviews, period events
   - Target: 85%+ coverage
   - Estimated fix: 2-3 hours

3. ⚠️ **Team names parsed as players** (LOW PRIORITY)
   - "Washington" extracted as player name
   - Cosmetic issue, easy fix
   - Estimated fix: 30 minutes

**Performance Metrics:**
- Processing speed: 1,247 events/second
- Per event: 0.80 milliseconds
- Projected time for full dataset: 1.5 hours (14,798 games)

**Files Created:**
- `scripts/pbp_to_boxscore/play_text_parser.py` (800 lines)
- `scripts/pbp_to_boxscore/game_state_tracker.py` (600 lines)
- `scripts/pbp_to_boxscore/rds_pbp_processor.py` (500 lines)
- Documentation: 1,350 lines across 3 files

### Pending Phases (⏸️)

#### Phase 1: Data Quality & Multi-Source Integration
- **Status:** PENDING (ready to start)
- **Sub-phases:**
  - 1.0: Data quality checks
  - 1.1: Multi-source integration (209 features, 28 hours)
- **Value:** Cross-validation, conflict resolution, enhanced feature set

#### Phase 7: Betting Odds Integration
- **Status:** PENDING (optional)
- **Timeline:** 6-8 hours
- **Cost:** +$0-10/month

#### Phase 9 Remaining Sub-phases

##### 9.3: NBA API Processor (⏸️ PENDING)
- Historical data (1995-2006)
- ~22,000 games
- Timeline: 2 weeks

##### 9.4: Kaggle Processor (⏸️ PENDING)
- Legacy data (1946-2020)
- 65,698 games
- Timeline: 1 week

##### 9.5: Storage System (⏸️ PENDING)
- RDS PostgreSQL tables
- S3 Parquet (ML training)
- Local SQLite cache
- Compression target: 10:1 ratio
- Expected storage: ~5 GB
- Timeline: 1 week

##### 9.6: Advanced Metrics Layer (⏸️ PENDING)
- True Shooting % (TS%)
- Player Efficiency Rating (PER)
- Offensive/Defensive Rating (ORtg/DRtg)
- Win Probability at each snapshot
- Four Factors, Usage Rate, Assist Ratio
- Timeline: 2-3 weeks

##### 9.7: ML Integration (⏸️ PENDING)
- Temporal features from snapshots
- Quarter-by-quarter predictions
- Integration with Phase 5 models
- Timeline: 2 weeks

##### 9.8: Betting Integration (⏸️ PENDING)
- Quarter-by-quarter predictions
- ROI tracking
- Real-time model updates
- Timeline: 3 weeks

### Basketball Reference Expansion (⏸️ PENDING)

**Scope:** 234 data types across 13 tiers, 7 basketball domains

**Organization:**
- **Tier 1 (IMMEDIATE):** 5 data types, 150K records, 15-20 hours
  - Advanced box scores, Play-by-play, Shot charts, Player tracking, Lineups
- **Tier 2 (IMMEDIATE):** 4 data types, 200K records, 20-25 hours
  - Game logs, Schedule, Playoffs, Transactions
- **Tier 3-9 (HIGH-LOW):** 22 data types, 615K records, 68-107 hours
  - Historical data, performance metrics, awards, advanced analytics
- **Tier 10-11 (EXECUTE):** 26 data types, 150K records, 23-30 hours
  - WNBA, G League complete datasets
- **Tier 12-13 (OPTIONAL):** 50 data types, 300K records, 40-70 hours
  - International, College basketball

**Total Estimated Time:** 140-197 hours
**Total Records:** 865K-10.88M
**Storage Impact:** +3-12 GB (+$0.07-0.27/month)

---

## Section C: Remaining Work Inventory

### Workstream 1: Complete Phase 9 Snapshot Generation (4-6 hours)

**Priority:** IMMEDIATE / CRITICAL
**Dependencies:** None (can start immediately)
**Value:** Unlocks temporal queries for 14,798 games

**Tasks:**

1. **Fix Substitution Handling** (2-3 hours) ⚠️ HIGH
   - Modify `game_state_tracker.py` to build lineups from substitution events
   - Remove inferred starting lineup logic
   - Start with empty lineups, build from first 5 substitutions per team
   - Test on test game (verify lineups stay at 5)
   - Validate on 3 additional games

2. **Improve Parser Coverage** (2-3 hours) ⏸️ MEDIUM
   - Log all unparsed plays from multiple test games
   - Identify top 10 missing play type patterns
   - Add regex patterns for: team rebounds, violations, shot clock, reviews, period events
   - Test on 5 diverse games
   - Iterate until 85%+ success rate

3. **Test on 10 Games** (1 hour) ⏸️ MEDIUM
   - Select diverse sample (different eras, teams, game situations)
   - Process each game
   - Validate lineup tracking (5 players constant)
   - Check parse success rates
   - Identify edge cases

4. **Implement Database Save** (1-2 hours) ⏸️ HIGH
   - Design batch INSERT statements for 3 tables
   - Implement transaction handling
   - Add error recovery
   - Test with 10 games
   - Verify data integrity

5. **Scale to Full Dataset** (1.5 hours) ⏸️ FINAL
   - Process 100 games first (validation)
   - Monitor for errors
   - If successful, scale to all 14,798 games
   - Estimated processing time: 1.5 hours at 1,247 events/second
   - Store in RDS + export to S3 Parquet

**Success Criteria:**
- ✅ Lineup tracking 100% accurate (5 players constant)
- ✅ Parser success rate 85%+
- ✅ All 14,798 games processed
- ✅ Data stored in RDS and S3
- ✅ Verification against actual box scores 99%+ accuracy

### Workstream 2: Phase 9 Additional Processors (8-10 weeks)

**Priority:** HIGH (sequenced after Workstream 1)
**Dependencies:** 9.0-9.2 complete (✅), Workstream 1 complete

**Sub-workstreams:**

#### 2A: NBA API Processor (2 weeks)
- Process 1995-2006 historical data (~22,000 games)
- Different event structure than ESPN
- Integration with existing snapshot system
- Cross-validation with ESPN overlapping years

#### 2B: Kaggle Processor (1 week)
- Legacy data (1946-2020)
- Game-level aggregates (no play-by-play for very old games)
- 65,698 games
- Lower priority (very old data)

#### 2C: Storage System (1 week)
- RDS table optimization
- S3 Parquet export pipeline
- Local SQLite caching
- Compression validation (10:1 target)
- Query performance testing (<100ms target)

#### 2D: Advanced Metrics Layer (2-3 weeks)
- Implement 15+ advanced metrics:
  - Efficiency: TS%, eFG%, PER, Usage Rate, Assist Ratio
  - Ratings: ORtg, DRtg, Net Rating, Pace
  - Context: Win Probability, EPA, Clutch performance
  - Situational: Quarter splits, Home/Away, Rest days
- Calculate per snapshot
- Store in separate tables/columns
- Version metrics for future updates
- Document all formulas

#### 2E: ML Integration (2 weeks)
- Extract temporal features from snapshots
- Quarter-by-quarter state features
- Integrate with Phase 5 ML models
- Train new models with snapshot data
- Expected accuracy boost: +3-5%

#### 2F: Betting Integration (3 weeks)
- Quarter-by-quarter prediction models
- ROI tracking system
- Real-time model updates
- Bankroll management
- Performance monitoring

**Success Criteria:**
- ✅ All data sources processed into unified snapshot format
- ✅ Advanced metrics calculated for all snapshots
- ✅ ML models retrained with enhanced features
- ✅ Betting models operational with ROI tracking

### Workstream 3: Basketball Reference Expansion (140-197 hours)

**Priority:** MEDIUM (parallel with Workstream 2)
**Dependencies:** None (can start anytime)
**Value:** Massive data expansion, cross-validation, historical depth

**Execution Strategy:**

**Phase 1: IMMEDIATE Tiers (35-45 hours, 350K records)**
- Tier 1 (15-20h): Advanced box scores, Play-by-play, Shot charts, Player tracking, Lineups
- Tier 2 (20-25h): Game logs, Schedule, Playoffs, Transactions
- **Value:** High-impact data for immediate ML enhancement

**Phase 2: HIGH Priority Tiers (25-35 hours, 325K records)**
- Tier 3 (10-15h): Historical data (pre-1993)
- Tier 4 (15-20h): Performance metrics, Awards, Streaks
- **Value:** Historical depth, context features

**Phase 3: MEDIUM Priority Tiers (30-42 hours, 225K records)**
- Tier 5 (8-12h): Advanced analytics
- Tier 6 (12-15h): Comparative stats
- Tier 7 (10-15h): Situational stats (clutch, splits)
- **Value:** Advanced features, specialized metrics

**Phase 4: LOW Priority Tiers (13-20 hours, 65K records)**
- Tier 8 (8-12h): NBA complete (referees, transactions)
- Tier 9 (5-8h): Historical leagues (ABA, BAA)
- **Value:** Completeness

**Phase 5: EXECUTE Priority Tiers (23-30 hours, 150K records)**
- Tier 10 (15-20h): WNBA complete (16 data types)
- Tier 11 (8-10h): G League complete (10 data types)
- **Value:** Multi-league panel data

**Phase 6: OPTIONAL Tiers (40-70 hours, 300K records)**
- Tier 12 (10-30h): International (FIBA, EuroLeague, Olympics)
- Tier 13 (30-40h): College (NCAA Men's/Women's)
- **Value:** Global basketball, developmental data

**Technical Approach:**
- Rate limiting: 12s ± 2s jitter (anti-blocking)
- Checkpoint-based scraper (resume capability)
- Atomic writes (no data loss)
- Error recovery with exponential backoff
- User-Agent rotation
- Session management
- Response validation
- Progress tracking

**Success Criteria:**
- ✅ Minimum: Tiers 1-2 complete (350K records, 35-45 hours)
- ✅ Target: Tiers 1-9 complete (1.115M records, 103-162 hours)
- ✅ Stretch: All tiers complete (1.415M-10.88M records, 140-197 hours)

### Workstream 4: Multi-Source Integration (28 hours)

**Priority:** MEDIUM (after Workstream 1, parallel with 2 & 3)
**Dependencies:** Workstream 1 complete, Basketball Reference Tiers 1-2 complete

**Phase 1.1: Multi-Source Integration**

**Goal:** Integrate 209 features across 5 data sources with conflict resolution

**Data Sources:**
1. ESPN (70,522 files)
2. NBA Stats (22,256 files)
3. hoopR (96 files)
4. Basketball Reference (444+ files, expanding)
5. Kaggle (65,698 games)

**Integration Strategy:**

1. **Conflict Resolution** (8 hours)
   - Timestamp synchronization
   - Source priority hierarchy (ESPN > NBA Stats > hoopR > Basketball Reference > Kaggle)
   - Deviation thresholds (flag discrepancies >5%)
   - Reconciliation logic

2. **Feature Extraction** (12 hours)
   - 209 unified features across sources
   - Missing data imputation
   - Cross-validation rules
   - Quality scoring per record

3. **Data Quality Checks** (4 hours)
   - Completeness validation
   - Consistency checks
   - Outlier detection
   - Gap analysis

4. **Pipeline Implementation** (4 hours)
   - Batch processing
   - Error handling
   - Progress tracking
   - Logging and monitoring

**Success Criteria:**
- ✅ 209 features extracted for all games
- ✅ Conflict resolution working (< 1% unresolvable)
- ✅ Quality score ≥ 90% for all records
- ✅ Pipeline processes 1,000 games/hour

---

## Section D: Technical Context for MCP

### Current AWS Infrastructure

**Costs (October 2025):** $41.53/month

| Service | Configuration | Cost/Month | Purpose |
|---------|--------------|------------|---------|
| S3 | 122 GB, Standard | $2.74 | Data lake |
| RDS PostgreSQL | db.t3.small, 20GB | $29.00 | Temporal queries |
| EC2 | t3.small, 8hrs/day | $6.59 | Simulation engine |
| CloudWatch + API | Monitoring | $3.20 | Alerts, dashboards |

**Budget:** $150/month target (currently 72% under budget)

**Projected Costs After Completion:**
- S3: +$0.50-1.30/month (snapshots + Basketball Reference)
- RDS: +$0.20/month (new tables)
- Total projected: $42-43/month (still well under budget)

### Database Schema

**Current Tables (20 tables, 48.4M rows):**

**Core Tables:**
- `games`: 44,828 rows (1993-2025)
- `play_by_play`: 6,781,155 rows (2004-2021)
- `box_score_players`: 408,833 rows
- `box_score_teams`: 15,900 rows
- `teams`: 87 rows
- `players`: ~5,000 rows

**Phase 9 Tables (NEW):**
- `game_state_snapshots`: ~6.4M rows projected (436 snapshots × 14,798 games)
- `player_snapshot_stats`: ~43M rows projected (6-7 players × 436 × 14,798)
- `quarter_box_scores`: ~236K rows (4 quarters × 2 teams × 29,596 game-teams)
- `box_score_verification`: ~14,798 rows (1 per game)

**Plus/Minus Tables (Deployed Oct 2025):**
- `lineup_snapshots`: 400+ rows per game
- `player_plus_minus_snapshots`: 2,159+ rows per game
- `possession_metadata`: 20+ rows per game

**Performance Targets:**
- Query response: <100ms for single game
- Bulk query: <5 seconds for 1,000 games
- Insert performance: 1,000 snapshots/second

### Data Inventory

**S3 Bucket:** `s3://nba-sim-raw-data-lake`
- Total files: 172,600
- Total size: ~122 GB
- Sources: ESPN, NBA API, Basketball Reference, hoopR, Kaggle

**Local Storage:** 147,382 files synchronized

**Key Data Characteristics:**
- **Temporal Precision:**
  - 2020-2025: Millisecond (future - NBA Live API)
  - 1993-2019: Minute-level (NBA Stats PlayByPlayV2)
  - 1946-1992: Game-level aggregates (Basketball Reference)

### Code Base Structure

**Key Directories:**
- `/scripts/pbp_to_boxscore/` - Phase 9 snapshot generation (1,900 lines)
- `/scripts/ml/` - ML models and feature engineering (14,000+ lines)
- `/scripts/etl/` - Data extraction and loading
- `/scripts/analysis/` - Data quality validation
- `/sql/` - Database schemas (master_schema.sql, phase9_*.sql, plus_minus/*.sql)
- `/docs/phases/` - Phase documentation (PHASE_N_INDEX.md, phase_N/*.md)

**Programming Languages:**
- Python 3.11.13 (primary)
- SQL (PostgreSQL 15.14)
- Bash (automation)

**Key Dependencies:**
- pandas, numpy, scikit-learn
- psycopg2 (PostgreSQL)
- boto3 (AWS SDK)
- beautifulsoup4 (scraping)
- MLflow (model versioning)

### Performance Constraints

**Processing Speed:**
- Current: 1,247 events/second (snapshot generation)
- Target: 500-1,000 events/second minimum
- Stretch: 2,000+ events/second

**Storage Efficiency:**
- Parquet compression: 10:1 minimum
- Query indexing: <100ms single game
- Bulk operations: 1,000 games/hour

**Accuracy:**
- Verification against actual box scores: 99%+ for 2023-2025
- Parse success rate: 85%+ target
- Multi-source conflict resolution: <1% unresolvable

**Availability:**
- RDS: 99.9% uptime (AWS SLA)
- Query latency: <100ms p95
- Batch processing: Resumable on failure

---

## Section E: Success Criteria

### What "Complete Temporal Data Build" Means

#### Tier 1: Minimum Viable Complete (MVC)

**Timeline:** 2-3 weeks
**Effort:** 35-50 hours

✅ **Snapshot Generation Complete**
- All 14,798 ESPN games (1993-2025) processed into snapshots
- Substitution handling 100% accurate
- Parser coverage 85%+
- Data stored in RDS and S3 Parquet
- Verification accuracy 99%+

✅ **Basketball Reference Tiers 1-2**
- 350K records collected
- 9 high-value data types
- 35-45 hours of scraping complete

✅ **Basic Temporal Queries Working**
- Can query player stats at any moment (minute-level precision)
- Response time <100ms
- Covering 1993-2025 games

#### Tier 2: Production Ready (PR)

**Timeline:** 6-8 weeks
**Effort:** 100-150 hours

✅ **All Phase 9 Sub-phases Complete**
- 9.0-9.8 all complete
- ESPN, hoopR, NBA API, Kaggle processors operational
- Storage system optimized
- Advanced metrics layer complete
- ML integration operational

✅ **Basketball Reference Tiers 1-9**
- 1.115M records collected
- 30 NBA data types complete
- Historical depth (1946-2025)

✅ **Multi-Source Integration**
- Phase 1.1 complete (209 features)
- Conflict resolution working
- Quality scores 90%+

✅ **Temporal Queries Enhanced**
- Millisecond precision for modern games
- Advanced metrics available
- Cross-source validation

#### Tier 3: Comprehensive System (CS)

**Timeline:** 12+ weeks
**Effort:** 200+ hours

✅ **All Basketball Reference Tiers**
- Tiers 1-13 complete
- 1.415M-10.88M records
- Multi-league coverage (NBA, WNBA, G League)
- International and college data

✅ **Betting Integration**
- Phase 7 complete
- Quarter-by-quarter predictions
- ROI tracking operational

✅ **Full MLOps Pipeline**
- Automated retraining
- Drift detection
- Model monitoring
- A/B testing framework

### Measurable Success Metrics

**Data Coverage:**
- ✅ ESPN games: 14,798/14,798 (100%)
- ✅ Snapshot accuracy: 99%+
- ✅ Parser coverage: 85%+
- ✅ Basketball Reference records: 350K minimum (Tier 1: MVC)

**Performance:**
- ✅ Query latency: <100ms p95
- ✅ Processing speed: 500+ events/second
- ✅ Storage compression: 10:1 ratio
- ✅ Uptime: 99.9%

**Accuracy:**
- ✅ Verification vs actual box scores: 99%+
- ✅ Multi-source conflict resolution: <1% unresolvable
- ✅ ML model accuracy: 75%+ (with snapshot features: 78-80%)

**Cost:**
- ✅ Stay within $150/month budget
- ✅ Current: $41.53/month
- ✅ Projected after completion: $42-50/month

**Code Quality:**
- ✅ Test coverage: 80%+
- ✅ Documentation: All major components documented
- ✅ Error handling: Graceful degradation
- ✅ Logging: Comprehensive monitoring

---

## Section F: Request to MCP

### What We Need from MCP

**Primary Deliverable:** A comprehensive, prioritized, actionable implementation plan to complete the temporal data build system.

### Specific Requirements for the Plan

#### 1. Prioritized Implementation Sequence

**Required Output:**
- Complete ordering of all tasks from Workstreams 1-4
- Identification of parallel vs. sequential work
- Critical path analysis (what blocks what)
- Dependency graph visualization (text-based is fine)

**Key Questions to Answer:**
- What order maximizes value delivery?
- What can be done in parallel to reduce total calendar time?
- What are the key decision points and checkpoints?
- Which tasks are on the critical path vs. can be deferred?

**Example Format:**
```
Week 1:
  [CRITICAL PATH] Workstream 1: Fix substitution handling (3 days)
  [PARALLEL] Workstream 3: Begin Basketball Reference Tier 1 (2 days setup)

Week 2:
  [CRITICAL PATH] Workstream 1: Improve parser, test, scale (5 days)
  [PARALLEL] Workstream 3: Basketball Reference Tier 1 continued

Week 3:
  [CRITICAL PATH] Workstream 2: Storage system implementation (5 days)
  [PARALLEL] Workstream 3: Basketball Reference Tier 2 (5 days)
  [PARALLEL] Workstream 4: Multi-source integration design (2 days)
...
```

#### 2. Detailed Work Breakdown

For **each task** in Workstreams 1-4, provide:

**A. Task Definition**
- Clear, specific description
- Acceptance criteria (what "done" means)
- Files to modify/create
- Estimated lines of code

**B. Time Estimation**
- Optimistic (best case)
- Realistic (most likely)
- Pessimistic (worst case)
- 3-point estimate

**C. Dependencies**
- What must complete before this task
- What this task blocks
- External dependencies (AWS, data, etc.)

**D. Risk Assessment**
- Technical risks
- Data quality risks
- Performance risks
- Mitigation strategies for each

**E. Success Metrics**
- How to validate task completion
- Automated tests to write
- Manual verification steps
- Performance benchmarks

**Example Format:**
```
Task: 1.1 - Fix Substitution Handling in GameStateTracker

Description:
  Modify game_state_tracker.py to build lineups from substitution events
  instead of inferring from early plays. Start with empty lineups,
  populate with first 5 subs per team.

Files to Modify:
  - scripts/pbp_to_boxscore/game_state_tracker.py (modify: 60 lines)
  - scripts/pbp_to_boxscore/rds_pbp_processor.py (delete: 30 lines)
  - Add test: tests/test_substitution_handling.py (new: 150 lines)

Estimated Time:
  - Optimistic: 1.5 hours
  - Realistic: 2.5 hours
  - Pessimistic: 4 hours
  - 3-point: 2.7 hours

Dependencies:
  - None (can start immediately)

Blocks:
  - Task 1.2 (Improve parser coverage)
  - Task 1.3 (Test on 10 games)

Risks:
  - Some games may not have substitution events (mitigation: fallback logic)
  - Edge case: players ejected mid-game (mitigation: handle in separate logic)

Success Metrics:
  - All test games maintain 5 players per team (100% pass rate)
  - Unit tests pass
  - No lineups with <5 or >5 players logged
```

#### 3. Resource Planning

**AWS Cost Projections:**
- Cost per workstream
- Monthly cost trajectory
- Peak cost periods
- Cost optimization opportunities

**Development Time:**
- Total hours per workstream
- Calendar weeks (assuming X hours/week - specify assumption)
- Parallel work opportunities

**Testing Requirements:**
- Unit tests per component
- Integration tests per workstream
- Performance tests
- Data validation tests

**Monitoring & Validation:**
- What to monitor during each phase
- Alert thresholds
- Quality gates before moving to next phase

#### 4. Integration Strategy

**How Components Fit Together:**
- Data flow diagrams (text-based)
- API/interface contracts between components
- Schema changes required
- Backward compatibility considerations

**Migration/Rollout Approach:**
- How to deploy without breaking existing system
- Rollback procedures for each phase
- Blue/green deployment strategy if applicable

**Example Integration Points:**
```
Snapshot Generation → Storage System:
  Interface: BoxScoreSnapshot objects
  Contract: Must include all required fields (game_id, event_id, timestamp, stats)
  Schema: game_state_snapshots table in RDS
  Rollback: If snapshot validation fails, revert to previous processing logic

Storage System → ML Integration:
  Interface: Parquet files in S3 with standard schema
  Contract: Partitioned by season/month, compressed with Snappy
  Access: ML pipeline reads from S3, not RDS (avoid query load)
  Rollback: ML pipeline continues using old data source until validation complete
```

#### 5. Implementation Roadmap

**Week-by-Week Milestones:**
- What should be complete each week
- Deliverables per week
- Progress indicators

**Decision Points:**
- Go/no-go checkpoints
- Alternative paths if something fails
- When to escalate vs. continue

**Quality Gates:**
- Must-pass criteria before moving to next phase
- Automated checks
- Manual reviews required

**Rollback Procedures:**
- For each major integration
- Data backup strategy
- How to revert without data loss

**Example Roadmap Structure:**
```
Week 1: Workstream 1 Sprint 1
  Goal: Fix critical bugs in snapshot generation
  Deliverables:
    - Substitution handling fixed
    - Unit tests passing
    - 3 test games validate successfully
  Decision Point: Is lineup tracking 100% accurate?
    - YES → Proceed to Week 2
    - NO → Spend 2 more days debugging, reassess
  Quality Gate: 100% accuracy on lineup tracking (no exceptions)
  Rollback: Not needed (no production deployment yet)

Week 2: Workstream 1 Sprint 2 + Workstream 3 Kickoff
  Goal: Improve parser coverage, begin Basketball Reference scraping
  Deliverables:
    - Parser at 85%+ coverage
    - 10 test games validate successfully
    - Basketball Reference Tier 1 setup complete, first data type scraped
  Decision Point: Is parser good enough for production?
    - YES → Proceed to Week 3 scaling
    - NO → Identify which play types still failing, add patterns
  Quality Gate: 85% parse success on 10 diverse test games
  Rollback: Can continue with 75%+ if critical path blocked

Week 3: Workstream 1 Scaling + Workstream 2A + Workstream 3 Tier 1
  Goal: Scale snapshot generation to full dataset, implement storage, continue scraping
  ...
```

### Additional Context for MCP

**Assumptions to Use:**
- Development hours available: 20-30 hours/week
- AWS costs can increase up to $150/month
- Data quality is more important than speed
- Backward compatibility required (don't break existing system)

**Preferred Approach:**
- Start with Minimum Viable Complete (Tier 1 success criteria)
- Then expand to Production Ready (Tier 2)
- Comprehensive System (Tier 3) is optional/stretch

**Risk Tolerance:**
- Low risk tolerance for data loss or corruption
- Medium risk tolerance for cost overruns (within budget)
- High risk tolerance for timeline slips (quality over speed)

**Open Questions for MCP to Address:**
1. Should Basketball Reference scraping start immediately in parallel, or wait until snapshot generation complete?
2. Is multi-source integration (Workstream 4) necessary before advanced metrics (Workstream 2D), or can we skip and revisit later?
3. What's the optimal batch size for processing snapshots (100 games, 1000 games, all at once)?
4. Should we implement all advanced metrics at once, or prioritize the top 5 most valuable ones first?

### Output Format Preferences

**Preferred Formats:**
- Markdown documents (easy to read and version control)
- Mermaid diagrams for visualizations (if supported)
- Tables for task breakdowns
- Numbered lists for sequences
- Bullet points for non-ordered items

**Structure:**
```
1. EXECUTIVE_SUMMARY.md (1-2 pages)
   - High-level plan
   - Total time/cost estimates
   - Key milestones
   - Major risks

2. PRIORITIZED_TASK_LIST.md (5-10 pages)
   - All tasks ordered by sequence
   - Dependencies clearly marked
   - Parallel work identified

3. DETAILED_WORKSTREAM_PLANS.md (20-40 pages)
   - Workstream 1: Complete Phase 9 Snapshot Generation
   - Workstream 2: Phase 9 Additional Processors
   - Workstream 3: Basketball Reference Expansion
   - Workstream 4: Multi-Source Integration
   - Each with full task breakdowns as specified above

4. INTEGRATION_STRATEGY.md (5-10 pages)
   - How components integrate
   - Data flows
   - API contracts
   - Migration approach

5. WEEK_BY_WEEK_ROADMAP.md (10-15 pages)
   - Weekly milestones
   - Decision points
   - Quality gates
   - Rollback procedures

6. RESOURCE_PLAN.md (3-5 pages)
   - Time estimates
   - Cost projections
   - Testing requirements
   - Monitoring plan

7. RISK_REGISTER.md (3-5 pages)
   - All identified risks
   - Likelihood and impact
   - Mitigation strategies
   - Contingency plans
```

---

## Section G: Supporting Files Reference

For the MCP's context, the following files contain additional details:

**Core Documentation:**
- `PROGRESS.md` - Current phase status and session context
- `CLAUDE.md` - Project instructions and navigation
- `docs/README.md` - Documentation index

**Phase 9 Documentation:**
- `docs/phases/PHASE_9_INDEX.md` - Phase overview
- `docs/phases/phase_9/9.0_system_architecture.md` - System design
- `docs/phases/phase_9/9.1_espn_processor.md` - ESPN processor details
- `docs/phases/phase_9/9.2_hoopr_processor.md` - hoopR processor details
- `docs/phases/phase_9/9.3_nba_api_processor.md` - NBA API processor details
- `docs/phases/phase_9/9.4_kaggle_processor.md` - Kaggle processor details
- `docs/phases/phase_9/9.5_storage_system.md` - Storage architecture
- `docs/phases/phase_9/9.6_advanced_metrics.md` - Advanced metrics details
- `docs/phases/phase_9/9.7_ml_integration.md` - ML integration approach
- `docs/phases/phase_9/9.8_betting_integration.md` - Betting integration approach

**Option 2A Status:**
- `docs/OPTION_2A_STATUS.md` - Current snapshot generation status (60% complete)
- `docs/OPTION_2A_SESSION_SUMMARY.md` - Implementation details

**Basketball Reference:**
- `docs/phases/phase_0/0.1_basketball_reference/README.md` - Overview of 13 tiers
- `docs/phases/phase_0/0.1_basketball_reference/TIER_1_NBA_HIGH_VALUE.md` - Tier 1 details
- `docs/phases/phase_0/0.1_basketball_reference/TIER_2_NBA_STRATEGIC.md` - Tier 2 details
- `docs/phases/phase_0/0.1_basketball_reference/IMPLEMENTATION_SUMMARY.md` - Technical approach

**Multi-Source Integration:**
- `docs/phases/PHASE_1_INDEX.md` - Phase 1 overview
- `docs/phases/phase_1/1.1_multi_source_integration.md` - Integration details

**ML and Plus/Minus:**
- `docs/PLUS_MINUS_IMPLEMENTATION_SUMMARY.md` - Plus/minus system details
- `docs/REC_11_PLUS_MINUS_INTEGRATION.md` - ML feature integration
- `docs/phases/PHASE_5_INDEX.md` - ML frameworks overview

**Implementation Code:**
- `scripts/pbp_to_boxscore/play_text_parser.py` - Current parser (800 lines)
- `scripts/pbp_to_boxscore/game_state_tracker.py` - Current state tracker (600 lines)
- `scripts/pbp_to_boxscore/rds_pbp_processor.py` - Current processor (500 lines)
- `sql/phase9_box_score_snapshots.sql` - Database schema (510 lines)

**Workflow References:**
- `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` - 54 workflow index
- `docs/claude_workflows/workflow_descriptions/` - Individual workflow procedures

---

## Section H: Final MCP Instructions

**Please generate:**

1. A comprehensive implementation plan following the structure in Section F
2. Prioritized task sequencing that maximizes value delivery
3. Realistic time and cost estimates
4. Risk mitigation strategies
5. Clear decision points and quality gates
6. Week-by-week roadmap to completion

**Optimize for:**
- Delivering Minimum Viable Complete (Tier 1) as quickly as possible
- Identifying parallel work to reduce calendar time
- Maintaining data quality and system stability
- Staying within $150/month AWS budget

**Provide alternatives for:**
- Aggressive timeline (sacrifice some features for speed)
- Comprehensive timeline (include all optional work)
- Cost-optimized approach (minimize AWS spending)

**Thank you for generating this implementation plan!**

---

**Document Version:** 1.0
**Created:** October 20, 2025
**Purpose:** MCP input for temporal data build completion plan
**Next Step:** Provide this document to MCP server for analysis and planning
