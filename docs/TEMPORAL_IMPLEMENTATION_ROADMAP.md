# NBA Temporal Panel Data - Implementation Roadmap

**Version:** 1.0
**Last Updated:** October 7, 2025
**Timeline:** 8 weeks (Weeks 1-4: Core, Weeks 5-8: Enhancement)

---

## Executive Summary

This roadmap details the phased implementation of the NBA Temporal Panel Data System, transforming traditional game-level analytics into millisecond-precision temporal queries.

**Goal:** Enable snapshot queries like "What were Kobe Bryant's career stats at exactly 7:02:34.56 PM CT on June 19, 2016?"

**Total effort:** 8 weeks (160-200 hours)
**Total cost increase:** +$19-37/month
**Core capability delivery:** Week 4
**Full enhancement delivery:** Week 8

---

## Implementation Phases

### 📋 Phase 1: Foundation (Weeks 1-2)

**Goal:** Set up temporal database schema and data collection infrastructure

#### Week 1: Database Schema & Indexes

**Sub-Phase 1.1: Create Temporal Tables (8 hours)**

```sql
-- Create 4 core temporal tables
CREATE TABLE temporal_events (...);
CREATE TABLE player_snapshots (...);
CREATE TABLE game_states (...);
CREATE TABLE player_biographical (...);

-- See: docs/phases/PHASE_3_DATABASE.md Sub-Phase 3.5
```

**Tasks:**
- [ ] Create `temporal_events` table (500M row capacity)
- [ ] Create `player_snapshots` table (50M row capacity)
- [ ] Create `game_states` table (10M row capacity)
- [ ] Create `player_biographical` table (5K row capacity)
- [ ] Add foreign key constraints
- [ ] Allocate 250-350 GB RDS storage

**Deliverable:** Empty temporal tables ready for data

**Validation:**
```sql
\dt+ temporal_*
\dt+ player_snapshots
\dt+ game_states
\dt+ player_biographical
```

---

**Sub-Phase 1.2: Create BRIN Indexes (4 hours)**

```sql
-- Time-series optimized indexes
CREATE INDEX idx_temporal_events_time_brin
    ON temporal_events USING BRIN (wall_clock_utc);

CREATE INDEX idx_player_snapshots_time_brin
    ON player_snapshots USING BRIN (snapshot_time);
```

**Tasks:**
- [ ] Create BRIN index on `temporal_events.wall_clock_utc`
- [ ] Create BRIN index on `player_snapshots.snapshot_time`
- [ ] Create GIN index on `temporal_events.event_data` (JSONB)
- [ ] Verify index creation with `\di+`

**Deliverable:** Optimized indexes for temporal queries

**Validation:**
```sql
SELECT tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_indexes JOIN pg_class ON indexname = relname
WHERE tablename IN ('temporal_events', 'player_snapshots');
```

---

**Sub-Phase 1.3: Create Stored Procedures (8 hours)**

```sql
-- Snapshot query function
CREATE OR REPLACE FUNCTION get_player_snapshot_at_time(
    p_player_id INTEGER,
    p_timestamp TIMESTAMP(3)
)
RETURNS TABLE (...) AS $$ ... $$;

-- Age calculation function
CREATE OR REPLACE FUNCTION calculate_player_age(
    p_player_id INTEGER,
    p_timestamp TIMESTAMP(3)
)
RETURNS TEXT AS $$ ... $$;
```

**Tasks:**
- [ ] Create `get_player_snapshot_at_time()` function
- [ ] Create `calculate_player_age()` function
- [ ] Test functions with sample data
- [ ] Document function parameters and return types

**Deliverable:** Core temporal query functions

**Validation:**
```sql
SELECT * FROM get_player_snapshot_at_time(977, '2016-06-19 19:02:34'::TIMESTAMPTZ);
SELECT calculate_player_age(977, '2016-06-19 19:02:34'::TIMESTAMPTZ);
```

---

#### Week 2: Data Collection & Birth Dates

**Sub-Phase 1.4: Collect Player Birth Dates (6 hours)**

**Tasks:**
- [ ] Scrape birth dates from NBA.com Stats API
- [ ] Scrape birth dates from Basketball Reference (historical players)
- [ ] Populate `player_biographical` table
- [ ] Flag birth date precision ('day', 'month', 'year')

**Script:** `scripts/etl/collect_player_birth_dates.py`

**Expected output:**
- ~5,000 player birth dates
- 90%+ with 'day' precision (modern players)
- 70%+ with 'month' or better precision (historical players)

**Deliverable:** Birth dates for age calculations

**Validation:**
```sql
SELECT
    birth_date_precision,
    COUNT(*) AS players,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM player_biographical
GROUP BY birth_date_precision
ORDER BY birth_date_precision;
```

---

**Sub-Phase 1.5: Extract Wall Clock Timestamps (8 hours)**

**Tasks:**
- [ ] Parse ESPN play-by-play for minute-level timestamps
- [ ] Parse NBA.com Stats PlayByPlayV2 for second-level timestamps
- [ ] Extract game start times for timestamp inference
- [ ] Handle timezone conversions (local to UTC)

**Script:** `scripts/etl/extract_wall_clock_timestamps.py`

**Expected output:**
- 6.78M+ events with timestamps (2004-2021 from ESPN data)
- Additional 5M+ events with second precision (2013-2019 from NBA Stats)

**Deliverable:** Raw timestamp data ready for loading

**Validation:**
```bash
# Check output files
ls -lh /tmp/temporal_events_extracted/
wc -l /tmp/temporal_events_extracted/*.jsonl
```

---

**Week 1-2 Milestones:**
- ✅ Temporal database schema created
- ✅ BRIN indexes operational
- ✅ Stored procedures tested
- ✅ Player birth dates collected
- ✅ Wall clock timestamps extracted

**Cost at end of Week 2:** +$11.57-23.57/month (RDS storage upgrade)

---

### 🔧 Phase 2: Data Loading (Week 3)

**Goal:** Load temporal_events and generate initial player_snapshots

#### Week 3: Bulk Load & Snapshot Generation

**Sub-Phase 2.1: Load temporal_events Table (12 hours)**

**Tasks:**
- [ ] Create bulk load script with batching (10K rows per batch)
- [ ] Load ESPN data (6.78M events, minute precision)
- [ ] Load NBA Stats data (5M events, second precision)
- [ ] Set `precision_level` flag for each event
- [ ] Set `data_source` field ('espn', 'nba_stats')
- [ ] Monitor load progress and error rates

**Script:** `scripts/etl/load_temporal_events.py`

**Expected load time:** 8-12 hours (for 12M events)

**Deliverable:** temporal_events table populated

**Validation:**
```sql
SELECT
    data_source,
    precision_level,
    COUNT(*) AS events,
    pg_size_pretty(pg_total_relation_size('temporal_events')) AS size
FROM temporal_events
GROUP BY data_source, precision_level
ORDER BY data_source, precision_level;
```

---

**Sub-Phase 2.2: Generate Player Snapshots (16 hours)**

**Tasks:**
- [ ] Create snapshot generation script
- [ ] Generate snapshots after each game (~18M snapshots)
- [ ] Generate snapshots after each quarter (~200K snapshots)
- [ ] Batch process by season (parallel jobs)
- [ ] Validate snapshot accuracy against raw events

**Script:** `scripts/etl/generate_player_snapshots.py`

**Expected generation time:** 12-16 hours (for 18.2M snapshots)

**Deliverable:** player_snapshots table populated

**Validation:**
```sql
SELECT
    DATE_TRUNC('year', snapshot_time) AS year,
    COUNT(DISTINCT player_id) AS players,
    COUNT(*) AS snapshots,
    pg_size_pretty(pg_total_relation_size('player_snapshots')) AS size
FROM player_snapshots
GROUP BY year
ORDER BY year;
```

---

**Sub-Phase 2.3: Generate Game States (8 hours)**

**Tasks:**
- [ ] Extract game state at 1-minute intervals
- [ ] Store current scores, quarter, time remaining
- [ ] Store active lineups (starting 5 + substitutions)
- [ ] Link to temporal_events for reconstruction

**Script:** `scripts/etl/generate_game_states.py`

**Expected output:** ~10M game state snapshots

**Deliverable:** game_states table populated

**Validation:**
```sql
SELECT
    COUNT(*) AS states,
    COUNT(DISTINCT game_id) AS games,
    pg_size_pretty(pg_total_relation_size('game_states')) AS size
FROM game_states;
```

---

**Week 3 Milestones:**
- ✅ 12M+ temporal events loaded
- ✅ 18M+ player snapshots generated
- ✅ 10M+ game states created
- ✅ All tables indexed and optimized

**Cost at end of Week 3:** +$16.54-31.18/month (RDS + S3 temporal data)

---

### ✅ Phase 3: Validation & Testing (Week 4)

**Goal:** Validate data integrity and query performance

#### Week 4: Testing & Optimization

**Sub-Phase 3.1: Run Validation Test Suite (4 hours)**

**Tasks:**
- [ ] Install pytest and dependencies
- [ ] Configure test database credentials
- [ ] Run full test suite (25 tests)
- [ ] Fix any test failures
- [ ] Document test results

**Command:**
```bash
pytest tests/test_temporal_queries.py -v --tb=short
```

**Expected results:** 23-25 tests pass (92-100%)

**Deliverable:** Validation report

**See:** `docs/TEMPORAL_VALIDATION_GUIDE.md`

---

**Sub-Phase 3.2: Manual Data Quality Checks (4 hours)**

**Tasks:**
- [ ] Verify precision coverage by era
- [ ] Check birth date completeness
- [ ] Validate snapshot accuracy (< 5% error)
- [ ] Cross-check ESPN vs NBA Stats timestamps
- [ ] Flag discrepancies for resolution

**Deliverable:** Data quality report

**Validation queries:** See `docs/TEMPORAL_VALIDATION_GUIDE.md` Section: Manual Validation Procedures

---

**Sub-Phase 3.3: Query Performance Benchmarking (4 hours)**

**Tasks:**
- [ ] Benchmark snapshot queries (target: < 5s)
- [ ] Benchmark time-range queries (target: < 10s)
- [ ] Benchmark career aggregations (target: < 15s)
- [ ] Identify slow queries for optimization
- [ ] Run VACUUM ANALYZE on all tables

**Deliverable:** Performance benchmark report

**Validation:**
```sql
EXPLAIN ANALYZE SELECT * FROM get_player_snapshot_at_time(977, '2016-06-19 19:02:34'::TIMESTAMPTZ);
```

---

**Sub-Phase 3.4: Documentation & Examples (4 hours)**

**Tasks:**
- [ ] Create query examples in docs
- [ ] Document common pitfalls
- [ ] Write troubleshooting guide
- [ ] Create Python helper function library
- [ ] Add examples to TEMPORAL_QUERY_GUIDE.md

**Deliverable:** Complete query guide

**See:** `docs/TEMPORAL_QUERY_GUIDE.md`

---

**Week 4 Milestones:**
- ✅ All validation tests pass
- ✅ Query performance meets targets
- ✅ Documentation complete
- ✅ **Core temporal capability operational**

**Cost at end of Week 4:** +$18.54-36.18/month (steady state)

---

### 🚀 Phase 4: Enhancement (Weeks 5-8)

**Goal:** Add advanced features and optimization

#### Week 5-6: Temporal Simulation Features

**Sub-Phase 4.1: Implement Temporal Simulation (Week 5, 16 hours)**

**Tasks:**
- [ ] Add fatigue calculation at timestamp
- [ ] Add age-adjusted stats at timestamp
- [ ] Add momentum detection (scoring runs)
- [ ] Add clutch situation identification
- [ ] Integrate with existing simulation engine

**Deliverable:** Temporal-aware simulation

**See:** `docs/phases/PHASE_4_SIMULATION_ENGINE.md` Sub-Phase 4.5

---

**Sub-Phase 4.2: Implement Temporal ML Features (Week 6, 16 hours)**

**Tasks:**
- [ ] Extract age features at game time
- [ ] Extract fatigue features during game
- [ ] Extract momentum features (last 5 min)
- [ ] Extract clutch performance features
- [ ] Integrate with ML pipeline

**Deliverable:** 50+ temporal features for ML

**See:** `docs/phases/PHASE_5_MACHINE_LEARNING.md` Sub-Phase 5.5

---

#### Week 7: Advanced Queries & Optimization

**Sub-Phase 4.3: Advanced Query Patterns (8 hours)**

**Tasks:**
- [ ] Multi-player snapshot comparison
- [ ] League-wide pace at timestamp
- [ ] Milestone achievement tracking
- [ ] Career trajectory analysis
- [ ] Hot/cold streak detection

**Deliverable:** Advanced query library

---

**Sub-Phase 4.4: Performance Optimization (8 hours)**

**Tasks:**
- [ ] Partition temporal_events by year (if needed)
- [ ] Tune BRIN page ranges
- [ ] Archive old snapshots to S3 Glacier
- [ ] Create materialized views for common queries
- [ ] Set up automated VACUUM schedule

**Deliverable:** Optimized performance

---

#### Week 8: Production Readiness

**Sub-Phase 4.5: Production Deployment (8 hours)**

**Tasks:**
- [ ] Set up automated snapshot generation (daily)
- [ ] Create monitoring dashboards
- [ ] Set up data quality alerts
- [ ] Create backup/recovery procedures
- [ ] Write operational runbook

**Deliverable:** Production-ready system

---

**Sub-Phase 4.6: Future Enhancements Planning (4 hours)**

**Tasks:**
- [ ] Plan NBA Live API integration (millisecond precision)
- [ ] Plan video synchronization (30fps)
- [ ] Plan real-time stat tracking
- [ ] Estimate costs and timelines
- [ ] Document enhancement roadmap

**Deliverable:** Future roadmap document

---

**Weeks 5-8 Milestones:**
- ✅ Temporal simulation operational
- ✅ Temporal ML features integrated
- ✅ Advanced queries documented
- ✅ System optimized and production-ready
- ✅ Future enhancements planned

**Final cost:** +$19-37/month (with optimizations)

---

## Resource Requirements

### Team & Skills

| Role | Weeks 1-4 | Weeks 5-8 | Skills Required |
|------|-----------|-----------|-----------------|
| **Database Engineer** | 80 hours | 20 hours | PostgreSQL, BRIN indexes, SQL optimization |
| **Data Engineer** | 60 hours | 20 hours | ETL, Python, pandas, data validation |
| **ML Engineer** | 20 hours | 40 hours | Feature engineering, scikit-learn, temporal features |
| **QA Engineer** | 20 hours | 20 hours | pytest, SQL testing, performance benchmarking |

**Total effort:** 180 hours (core) + 100 hours (enhancement) = 280 hours

---

### Infrastructure

| Resource | Weeks 1-4 | Weeks 5-8 | Cost/Month |
|----------|-----------|-----------|------------|
| **RDS Storage** | 250 GB | 300 GB | $11.57-23.57 |
| **S3 Temporal Data** | 215 GB | 250 GB | $4.97-5.75 |
| **Snapshot Generation** | Lambda | EC2 scheduled | $2-5 |
| **Total** | | | **$18.54-34.32/month** |

---

### External Dependencies

- **Data sources:** ESPN API, NBA.com Stats API, Basketball Reference
- **Tools:** PostgreSQL 15.14, Python 3.11, psycopg2, pandas, pytest
- **Services:** AWS RDS, S3, Lambda (or EC2 for batch jobs)

---

## Risk Management

### High-Priority Risks

#### Risk 1: Query Performance Degradation

**Likelihood:** Medium
**Impact:** High (slow queries unusable)

**Mitigation:**
1. Pre-compute snapshots at optimal frequency
2. Use BRIN indexes (70% storage savings)
3. Partition by year if > 500M events
4. Monitor query times weekly

**Contingency:** Add read replicas if needed (+$17-29/month)

---

#### Risk 2: Snapshot Generation Time

**Likelihood:** Medium
**Impact:** Medium (delays data availability)

**Mitigation:**
1. Parallelize snapshot generation by season
2. Use EC2 larger instance for batch jobs
3. Generate incrementally (only new games)

**Contingency:** Use Lambda for distributed processing

---

#### Risk 3: Birth Date Unavailability

**Likelihood:** High (historical players)
**Impact:** Low (age calculations return NULL)

**Mitigation:**
1. Document data completeness by era
2. Store birth date precision flag
3. Return NULL for missing data
4. Gradually improve coverage

**Contingency:** Estimate birth dates from draft year (±6 months accuracy)

---

#### Risk 4: Timestamp Precision Inconsistency

**Likelihood:** Medium
**Impact:** Medium (query accuracy issues)

**Mitigation:**
1. Store `precision_level` with each event
2. Store `data_source` for traceability
3. Allow filtering by precision
4. Document limitations

**Contingency:** Provide confidence intervals for imprecise data

---

### Low-Priority Risks

- **Cost overruns:** Monitor storage growth weekly, archive old data to Glacier
- **Data quality issues:** Set up automated validation tests (daily)
- **Integration complexity:** Start with core features, add enhancements later

---

## Success Metrics

### Week 4 (Core Delivery)

**Data completeness:**
- ✅ 12M+ temporal events loaded
- ✅ 18M+ player snapshots generated
- ✅ 90%+ birth date coverage (modern players)
- ✅ 95%+ precision flags set

**Query performance:**
- ✅ Snapshot queries: < 5 seconds
- ✅ Time-range queries: < 10 seconds
- ✅ Career aggregations: < 15 seconds

**Data quality:**
- ✅ Snapshot accuracy: < 5% error vs raw events
- ✅ No duplicate events at same timestamp
- ✅ All precision levels valid

---

### Week 8 (Full Enhancement)

**Advanced features:**
- ✅ Temporal simulation operational
- ✅ 50+ temporal ML features extracted
- ✅ Advanced query library complete

**System health:**
- ✅ 100% uptime
- ✅ Automated daily snapshot generation
- ✅ Monitoring dashboards operational
- ✅ < 1% data quality errors

**Cost efficiency:**
- ✅ Cost within $20-40/month increase
- ✅ BRIN indexes save 70%+ storage
- ✅ Archived data to Glacier (save $3-5/month)

---

## Go-Live Checklist

**Before enabling production queries:**

### Technical Readiness
- [ ] All 4 temporal tables created and populated
- [ ] BRIN indexes created and tested
- [ ] Stored procedures tested with sample queries
- [ ] All validation tests pass (23-25/25)
- [ ] Query performance benchmarks met
- [ ] Data quality checks complete

### Data Quality
- [ ] Precision coverage by era documented
- [ ] Birth date completeness > 90% (modern)
- [ ] Snapshot accuracy < 5% error
- [ ] Cross-source validation complete
- [ ] Discrepancies logged and resolved

### Documentation
- [ ] Query guide complete (`TEMPORAL_QUERY_GUIDE.md`)
- [ ] Validation guide complete (`TEMPORAL_VALIDATION_GUIDE.md`)
- [ ] Troubleshooting guide complete
- [ ] Python helper functions documented
- [ ] Examples added to QUICKSTART.md

### Operations
- [ ] Automated snapshot generation scheduled
- [ ] Monitoring dashboards set up
- [ ] Data quality alerts configured
- [ ] Backup/recovery procedures documented
- [ ] Runbook created

### Budget
- [ ] Cost projections confirmed (+$19-37/month)
- [ ] Budget approved
- [ ] Monitoring set up (cost alerts)

---

## Post-Launch Activities

### Week 9-12: Stabilization

**Tasks:**
- Monitor query performance and optimize slow queries
- Fix any data quality issues discovered
- Collect user feedback on query patterns
- Adjust snapshot frequency based on usage
- Fine-tune BRIN indexes

**Deliverable:** Stable production system

---

### Month 3-6: Enhancement

**Tasks:**
- Integrate temporal simulation with betting odds
- Add real-time stat tracking (future)
- Plan NBA Live API integration (millisecond precision)
- Plan video synchronization (30fps)
- Expand to other sports (NFL, MLB)

**Deliverable:** Enhanced capabilities roadmap

---

## Related Documentation

**Core implementation:**
- `docs/phases/PHASE_3_DATABASE.md` Sub-Phase 3.5 - Temporal schema
- `docs/adr/009-temporal-panel-data-architecture.md` - Architecture decisions
- `docs/TEMPORAL_QUERY_GUIDE.md` - Query examples
- `docs/TEMPORAL_VALIDATION_GUIDE.md` - Testing procedures

**Enhancement implementation:**
- `docs/phases/PHASE_4_SIMULATION_ENGINE.md` Sub-Phase 4.5 - Temporal simulation
- `docs/phases/PHASE_5_MACHINE_LEARNING.md` Sub-Phase 5.5 - Temporal ML features

**Project overview:**
- `docs/PROJECT_VISION.md` - Complete temporal vision
- `README.md` - Project overview with temporal focus
- `PROGRESS.md` - Cost projections and status

---

*Last updated: October 7, 2025*
*Version: 1.0*
*Maintained by: NBA Temporal Panel Data Team*
