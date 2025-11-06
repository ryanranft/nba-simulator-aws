# Sub-Phase 0.0005: Possession Extraction

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ⏸️ PENDING
**Priority:** ⭐ CRITICAL
**Implementation ID:** `temporal_data_transformation_0.0005`
**Started:** TBD
**Completed:** TBD

---

## Overview

Extracts basketball possessions from raw play-by-play events in the `temporal_events` table. This phase transforms 14.1 million individual events into 2-3 million meaningful possessions, serving as the foundation for advanced analytics and machine learning features.

**Data Foundation:**
- **Input:** `temporal_events` table (14.1M events, 5.8 GB, 1946-2025)
- **Output:** `temporal_possession_stats` table (2-3M possessions, ~500 MB)
- **Methodology:** Dean Oliver's "Basketball on Paper" possession definitions

**Key Capabilities:**
- Identifies possession boundaries using event type logic
- Calculates possession-level statistics (duration, points, efficiency)
- Validates against Dean Oliver's expected possession counts
- Provides millisecond-precision temporal accuracy

---

## Capabilities

### Core Features

1. **Possession Boundary Detection**
   - Identifies possession start events (rebounds, steals, inbounds, jump balls)
   - Identifies possession end events (shots, turnovers, end of period)
   - Handles complex edge cases (technical fouls, flagrant fouls, simultaneous possessions)
   - Validates possession chains for logical consistency

2. **Possession Statistics Calculation**
   - **Duration:** Elapsed time in seconds (game clock + real-time)
   - **Points:** Points scored during possession
   - **Efficiency:** Points per possession (PPP)
   - **Shot Quality:** Field goal attempts, 3-point attempts, free throw attempts
   - **Outcomes:** Made shots, turnovers, fouls drawn

3. **Team & Player Attribution**
   - Assigns each possession to offensive team
   - Tracks defensive team
   - Links to player IDs for all participants
   - Maintains home/away context

4. **Temporal Precision**
   - Game clock tracking (minutes, seconds remaining)
   - Period tracking (1-4, OT periods)
   - Score differential at possession start
   - Context flags (clutch time, garbage time, crunch time)

5. **Data Quality Validation**
   - Verifies possession counts match Dean Oliver estimates
   - Checks for orphaned events (events not in any possession)
   - Validates possession duration bounds (0.5 - 35 seconds typical)
   - Cross-references with game totals

### Dean Oliver Validation Framework

**Expected Possessions Formula:**
```
Possessions ≈ FGA + 0.44 × FTA - ORB + TOV
```

**Validation Checks:**
- Per-game possession counts within 5% of Oliver estimate
- Season-level possession counts within 2% of Oliver estimate
- Team pace calculations align with known NBA pace statistics

---

## Quick Start

### Basic Usage

```bash
# Run possession extraction for entire database
cd /Users/ryanranft/nba-simulator-aws
python scripts/workflows/possession_extraction_cli.py

# Run for specific season
python scripts/workflows/possession_extraction_cli.py --season 2024

# Run for date range
python scripts/workflows/possession_extraction_cli.py --start-date 2024-01-01 --end-date 2024-01-31

# Dry run (validation only, no database writes)
python scripts/workflows/possession_extraction_cli.py --dry-run

# Verbose logging with Dean Oliver validation
python scripts/workflows/possession_extraction_cli.py --verbose --validate

# Resume from saved state
python scripts/workflows/possession_extraction_cli.py --resume
```

### Programmatic Usage

```python
from docs.phases.phase_0.possession_extraction.possession_extractor import PossessionExtractor
from docs.phases.phase_0.possession_extraction.config import PossessionConfig

# Load configuration
config = PossessionConfig.from_yaml("config/default_config.yaml")

# Create extractor
extractor = PossessionExtractor(config=config)

# Initialize database connection
if extractor.initialize():
    # Extract possessions for a single game
    game_possessions = extractor.extract_game_possessions(game_id="401584893")
    
    # Validate using Dean Oliver
    validation_results = extractor.validate_possessions(game_possessions)
    
    if validation_results["passes_validation"]:
        # Save to database
        extractor.save_possessions(game_possessions)
        print(f"✅ Extracted {len(game_possessions)} possessions")
    else:
        print(f"❌ Validation failed: {validation_results['errors']}")
    
    # Shutdown
    extractor.shutdown()
```

---

## Architecture

### Data Flow

```
temporal_events (14.1M events)
    ↓
[1] Event Loading & Preprocessing
    - Load events for game/date range
    - Sort by game_id, period, clock
    - Filter out invalid events
    ↓
[2] Possession Boundary Detection
    - Identify START events (rebound, steal, inbound)
    - Identify END events (shot, turnover, period end)
    - Build possession chains
    ↓
[3] Possession Statistics Calculation
    - Calculate duration, points, efficiency
    - Aggregate event-level stats
    - Assign team/player attribution
    ↓
[4] Dean Oliver Validation
    - Compare to FGA + 0.44×FTA - ORB + TOV
    - Check possession count bounds
    - Validate duration distributions
    ↓
[5] Database Storage
    - Insert into temporal_possession_stats
    - Create indexes for fast queries
    - Update DIMS metrics
    ↓
temporal_possession_stats (2-3M possessions)
```

### Possession State Machine

```
IDLE → LOADING_EVENTS → DETECTING_BOUNDARIES → CALCULATING_STATS → VALIDATING → SAVING → COMPLETE
          ↓                    ↓                      ↓                  ↓           ↓
        ERROR                ERROR                  ERROR              ERROR       ERROR
          ↓                    ↓                      ↓                  ↓           ↓
        RETRY                RETRY                  RETRY              RETRY       RETRY
          ↓                    ↓                      ↓                  ↓           ↓
       (3 attempts)         (3 attempts)           (3 attempts)        (3 attempts) (3 attempts)
          ↓                    ↓                      ↓                  ↓           ↓
        FAILED               FAILED                 FAILED             FAILED      FAILED
```

### Database Schema

**New Table: `temporal_possession_stats`**

```sql
CREATE TABLE temporal_possession_stats (
    possession_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    game_date DATE NOT NULL,
    
    -- Possession Identification
    possession_number INTEGER NOT NULL,  -- Sequential within game
    period INTEGER NOT NULL,             -- 1-4, 5+ for OT
    
    -- Team Attribution
    offensive_team_id INTEGER NOT NULL,
    defensive_team_id INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    
    -- Temporal Context
    start_clock_minutes INTEGER,
    start_clock_seconds NUMERIC(4,1),
    end_clock_minutes INTEGER,
    end_clock_seconds NUMERIC(4,1),
    duration_seconds NUMERIC(5,2),       -- Possession duration
    
    -- Score Context
    score_differential_start INTEGER,    -- From offensive team perspective
    home_score_start INTEGER,
    away_score_start INTEGER,
    home_score_end INTEGER,
    away_score_end INTEGER,
    
    -- Possession Outcome
    points_scored INTEGER,               -- Points scored this possession
    possession_result VARCHAR(50),       -- 'made_shot', 'missed_shot', 'turnover', 'foul'
    
    -- Shot Quality
    field_goals_attempted INTEGER,
    field_goals_made INTEGER,
    three_pointers_attempted INTEGER,
    three_pointers_made INTEGER,
    free_throws_attempted INTEGER,
    free_throws_made INTEGER,
    
    -- Efficiency Metrics
    points_per_possession NUMERIC(5,3),
    effective_field_goal_pct NUMERIC(5,3),
    
    -- Event References
    start_event_id BIGINT,               -- FK to temporal_events
    end_event_id BIGINT,                 -- FK to temporal_events
    event_count INTEGER,                 -- Number of events in possession
    
    -- Context Flags
    is_clutch_time BOOLEAN,              -- Last 5 min, score within 5
    is_garbage_time BOOLEAN,             -- >20 point differential, <5 min
    is_fastbreak BOOLEAN,                -- Possession < 8 seconds
    has_timeout BOOLEAN,                 -- Timeout called during possession
    
    -- Data Quality
    validation_status VARCHAR(20),       -- 'valid', 'warning', 'invalid'
    validation_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(game_id, possession_number)
);

CREATE INDEX idx_possession_game ON temporal_possession_stats(game_id);
CREATE INDEX idx_possession_season ON temporal_possession_stats(season);
CREATE INDEX idx_possession_team ON temporal_possession_stats(offensive_team_id, season);
CREATE INDEX idx_possession_date ON temporal_possession_stats(game_date);
CREATE INDEX idx_possession_clutch ON temporal_possession_stats(is_clutch_time);
```

**Storage Estimates:**
- **Row Size:** ~250 bytes per possession
- **Expected Rows:** 2-3 million possessions
- **Total Size:** ~500-750 MB
- **With Indexes:** ~1-1.5 GB total

### Configuration Schema

```yaml
# config/default_config.yaml

project_dir: /Users/ryanranft/nba-simulator-aws
log_dir: logs/possession_extraction
reports_dir: reports/possession_extraction

database:
  host: localhost
  port: 5432
  dbname: nba_data
  user: nba_admin
  
source_table: temporal_events
target_table: temporal_possession_stats

possession_detection:
  # Minimum possession duration (seconds)
  min_duration: 0.5
  
  # Maximum possession duration (seconds)
  max_duration: 35.0
  
  # Start events (possession begins)
  start_events:
    - defensive_rebound
    - steal
    - inbound
    - jump_ball_won
    - technical_foul_shot_made  # Offense retains possession
    
  # End events (possession terminates)
  end_events:
    - shot_made
    - shot_missed
    - turnover
    - end_of_period
    - foul_before_shot  # If it gives possession to defense
    
  # Edge cases requiring special handling
  edge_cases:
    - offensive_rebound  # Possession continues
    - technical_foul     # May or may not change possession
    - flagrant_foul      # Complex possession rules
    - double_foul        # Jump ball situation

validation:
  # Dean Oliver validation
  enable_oliver_validation: true
  oliver_tolerance_pct: 5.0  # Within 5% is acceptable
  
  # Duration validation
  check_duration_bounds: true
  warn_if_duration_outlier: true
  
  # Logical consistency checks
  verify_possession_chains: true
  check_orphaned_events: true

processing:
  # Batch size for database queries
  batch_size: 1000
  
  # Number of games to process in parallel
  parallel_games: 4
  
  # Retry configuration
  max_retries: 3
  retry_delay_seconds: 5

output:
  # Save validation reports
  save_reports: true
  report_format: markdown  # or 'json', 'csv'
  
  # Save detailed logs
  detailed_logging: true
  
dims:
  enabled: true
  report_metrics: true
  metrics:
    - possessions_extracted
    - games_processed
    - validation_pass_rate
    - avg_possessions_per_game
    - processing_duration
```

---

## Implementation Files

| File | Purpose | Lines | Tests |
|------|---------|-------|-------|
| `possession_extractor.py` | Main extraction logic | ~1000 | 100% |
| `possession_detector.py` | Boundary detection algorithms | ~500 | 100% |
| `possession_statistics.py` | Stats calculation | ~400 | 100% |
| `dean_oliver_validator.py` | Validation framework | ~300 | 100% |
| `config/default_config.yaml` | Default configuration | ~100 | N/A |
| `test_possession_extraction.py` | Unit and integration tests | ~800 | 105 tests |
| CLI: `scripts/workflows/possession_extraction_cli.py` | Command-line interface | ~250 | N/A |

**Total Production Code:** ~2,400 lines  
**Total Test Code:** ~800 lines  
**Test Coverage Target:** 95%+

---

## Testing

### Test Organization

```
tests/phases/phase_0/test_0_0005_possession_extraction.py
├── Unit Tests (60 tests)
│   ├── test_event_loading()
│   ├── test_start_event_detection()
│   ├── test_end_event_detection()
│   ├── test_possession_chain_building()
│   ├── test_duration_calculation()
│   ├── test_points_calculation()
│   ├── test_efficiency_calculation()
│   ├── test_team_attribution()
│   └── ...
│
├── Integration Tests (30 tests)
│   ├── test_full_game_extraction()
│   ├── test_season_extraction()
│   ├── test_date_range_extraction()
│   ├── test_dean_oliver_validation()
│   ├── test_database_storage()
│   └── ...
│
└── Edge Case Tests (15 tests)
    ├── test_overtime_possessions()
    ├── test_technical_foul_possession()
    ├── test_flagrant_foul_possession()
    ├── test_end_of_period_possession()
    ├── test_fastbreak_possession()
    └── ...
```

### Run Tests

```bash
# Run all possession extraction tests
pytest tests/phases/phase_0/test_0_0005_possession_extraction.py -v

# Run specific test category
pytest tests/phases/phase_0/test_0_0005_possession_extraction.py -k "unit" -v

# Run with coverage report
pytest tests/phases/phase_0/test_0_0005_possession_extraction.py \
    --cov=docs.phases.phase_0.possession_extraction \
    --cov-report=html \
    --cov-report=term

# Run integration tests only (requires database)
pytest tests/phases/phase_0/test_0_0005_possession_extraction.py -k "integration" -v
```

### Test Coverage Goals

- ✅ **Unit Tests:** 95%+ coverage
- ✅ **Integration Tests:** All major workflows
- ✅ **Edge Cases:** All known edge cases documented
- ✅ **Performance:** <1 second per game extraction
- ✅ **Validation:** 100% of games pass Dean Oliver validation

---

## DIMS Integration

### Metrics Reported

The possession extraction workflow automatically reports these metrics to DIMS:

| Metric | Description | Type |
|--------|-------------|------|
| `possessions_extracted` | Total possessions extracted | Counter |
| `games_processed` | Total games processed | Counter |
| `events_processed` | Total events analyzed | Counter |
| `validation_pass_rate` | % of games passing validation | Gauge |
| `avg_possessions_per_game` | Average possessions extracted per game | Gauge |
| `processing_duration_seconds` | Time to process all games | Timer |
| `database_write_duration` | Time to write to database | Timer |
| `oliver_validation_errors` | Count of Dean Oliver validation failures | Counter |
| `orphaned_events_count` | Events not assigned to possessions | Counter |

### Query DIMS Metrics

```bash
# View possession extraction metrics
python scripts/monitoring/dims_cli.py report \
    --category possession_extraction \
    --time-range 7d

# Verify extraction health
python scripts/monitoring/dims_cli.py verify \
    --category possession_extraction

# Compare possessions vs Oliver estimates
python scripts/monitoring/dims_cli.py analyze \
    --metric possessions_extracted \
    --compare-to oliver_estimate
```

### Health Monitoring

```bash
# Check if extraction is running
python scripts/monitoring/dims_cli.py status \
    --service possession_extraction

# View recent extraction jobs
python scripts/monitoring/dims_cli.py jobs \
    --service possession_extraction \
    --limit 10
```

---

## Related Documentation

### Phase 0 Data Collection
- [0.0001: Initial Data Collection](../0.0001_initial_data_collection/README.md) - Source of temporal_events table
- [0.0006: Temporal Features](../0.0006_temporal_features/README.md) - Uses possessions for feature engineering
- [0.0018: Autonomous Data Collection (ADCE)](../0.0018_autonomous_data_collection/README.md) - Integration point
- [0.0022: Data Inventory & Gap Analysis](../0.0022_data_inventory_gap_analysis/README.md) - DIMS system

### Methodologies
- [KENPOM_TEMPORAL_FEATURES_IMPLEMENTATION_GUIDE.md](../KENPOM_TEMPORAL_FEATURES_IMPLEMENTATION_GUIDE.md) - Full technical guide
- Dean Oliver's "Basketball on Paper" - Possession definitions (Chapter 3)
- KenPom.com methodology - Tempo-free statistics

### Infrastructure
- [DATABASE_SCHEMA.md](../../../DATABASE_SCHEMA.md) - Complete schema documentation
- [AUTONOMOUS_OPERATION.md](../../../AUTONOMOUS_OPERATION.md) - ADCE integration
- [SCRAPER_MONITORING_SYSTEM.md](../../../SCRAPER_MONITORING_SYSTEM.md) - Monitoring procedures

---

## Troubleshooting

### Extraction Fails with "Orphaned Events"

**Symptom:** Many events not assigned to any possession

**Causes:**
- Missing start/end events in database
- Event sequence corruption
- Incorrect event type mappings

**Solution:**
```bash
# Run diagnostic report
python scripts/workflows/possession_extraction_cli.py --diagnose --game-id 401584893

# Check event sequence
python scripts/analysis/event_sequence_analyzer.py --game-id 401584893

# Re-extract with verbose logging
python scripts/workflows/possession_extraction_cli.py --game-id 401584893 --verbose
```

### Dean Oliver Validation Fails

**Symptom:** Possession counts >5% off from Oliver estimate

**Causes:**
- Incorrect FGA, FTA, ORB, or TOV counts in source data
- Missing events (incomplete data)
- Double-counting possessions

**Solution:**
```bash
# Run detailed validation report
python scripts/workflows/possession_extraction_cli.py \
    --game-id 401584893 \
    --validate \
    --detailed-report

# Compare source data to box score
python scripts/analysis/box_score_reconciliation.py --game-id 401584893

# Check for duplicate possessions
python scripts/analysis/possession_duplicates_checker.py --game-id 401584893
```

### Extraction Performance Issues

**Symptom:** Taking >5 seconds per game

**Causes:**
- Database not indexed properly
- Too many events per possession
- Inefficient queries

**Solution:**
```bash
# Check database indexes
python scripts/maintenance/check_indexes.py --table temporal_events

# Profile extraction performance
python scripts/workflows/possession_extraction_cli.py \
    --game-id 401584893 \
    --profile

# Optimize batch size
# Edit config/default_config.yaml: processing.batch_size = 500
```

### Database Write Errors

**Symptom:** "duplicate key value violates unique constraint"

**Causes:**
- Re-running extraction without cleanup
- Possession numbering collision
- Concurrent writes

**Solution:**
```bash
# Clear existing possessions for game
python scripts/maintenance/clear_possessions.py --game-id 401584893

# Run with force flag
python scripts/workflows/possession_extraction_cli.py \
    --game-id 401584893 \
    --force-overwrite

# Check for concurrent processes
ps aux | grep possession_extraction
```

---

## Validation Reports

### Sample Dean Oliver Validation Report

```markdown
# Possession Extraction Validation Report
**Game:** PHI @ BOS (2024-03-05)
**Game ID:** 401584893

## Possession Counts

| Metric | Home (BOS) | Away (PHI) | Total |
|--------|-----------|-----------|-------|
| Extracted Possessions | 98 | 97 | 195 |
| Oliver Estimate | 99.2 | 98.8 | 198.0 |
| Difference | -1.2 (-1.2%) | -1.8 (-1.8%) | -3.0 (-1.5%) |
| Status | ✅ PASS | ✅ PASS | ✅ PASS |

## Oliver Formula Breakdown (BOS)

```
Possessions = FGA + 0.44 × FTA - ORB + TOV
            = 88 + 0.44 × 25 - 10 + 12
            = 88 + 11.0 - 10 + 12
            = 101.0
```

**Tolerance:** 5% = ±5.05 possessions  
**Actual Difference:** -3.0 possessions (2.97%)  
**Result:** ✅ Within tolerance

## Data Quality Checks

| Check | Status | Details |
|-------|--------|---------|
| Orphaned Events | ✅ PASS | 0 events not in possessions |
| Duration Bounds | ✅ PASS | All possessions 0.5-35s |
| Possession Chains | ✅ PASS | All chains logically consistent |
| Event Counts | ✅ PASS | 1,247 events → 195 possessions |

## Summary

✅ **VALIDATION PASSED** - All checks passed  
📊 Possessions extracted: 195  
⏱️ Avg possession duration: 14.3s  
🎯 Points per possession: BOS 1.12, PHI 1.08
```

---

## Performance Benchmarks

### Expected Performance

| Scenario | Games | Time | Rate |
|----------|-------|------|------|
| Single Game | 1 | <1s | - |
| Season (1,230 games) | 1,230 | ~15 min | 82 games/min |
| Full Database (66K games) | 66,000 | ~13 hrs | 85 games/min |

### Optimization Strategies

1. **Database Indexes** - Critical for fast event queries
2. **Batch Processing** - Process multiple games in parallel
3. **Query Optimization** - Load only necessary columns
4. **Connection Pooling** - Reuse database connections
5. **Caching** - Cache team mappings, event type lookups

---

## Implementation Timeline

### Week 1: Core Extraction (5 days)

**Day 1-2:** Database schema & config
- Create `temporal_possession_stats` table
- Write configuration YAML
- Set up database indexes

**Day 3-4:** Possession detection
- Implement start/end event detection
- Build possession chains
- Handle edge cases

**Day 5:** Statistics calculation
- Calculate duration, points, efficiency
- Team/player attribution
- Context flags

### Week 2: Validation & Testing (5 days)

**Day 6-7:** Dean Oliver validation
- Implement Oliver formula
- Write validation logic
- Create validation reports

**Day 8-9:** Comprehensive testing
- Write 105 unit/integration tests
- Edge case coverage
- Performance benchmarks

**Day 10:** Integration & deployment
- DIMS metric integration
- CLI tool finalization
- Documentation completion

**Total:** 10 working days (2 weeks)

---

## Success Criteria

### Must Have (Blocking)
- ✅ Extract possessions for all 66K games
- ✅ 95%+ of games pass Dean Oliver validation
- ✅ <1 second per game extraction time
- ✅ <1% orphaned events across database
- ✅ All 105 tests passing

### Should Have (Important)
- ✅ Detailed validation reports for all games
- ✅ DIMS metrics integration
- ✅ Performance benchmarks documented
- ✅ Comprehensive error handling

### Nice to Have (Optional)
- ⭐ Real-time possession extraction during live games
- ⭐ Interactive possession explorer UI
- ⭐ Possession-level video clips

---

## Navigation

**Parent:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)  
**Prerequisites:** [0.0001: Initial Data Collection](../0.0001_initial_data_collection/README.md) (temporal_events table)  
**Enables:** [0.0006: Temporal Features](../0.0006_temporal_features/README.md) (KenPom metrics)  
**Integrates With:** [0.0018: ADCE](../0.0018_autonomous_data_collection/README.md), [0.0022: DIMS](../0.0022_data_inventory_gap_analysis/README.md)

---

**Last Updated:** November 5, 2025  
**Version:** 1.0.0 (Initial Implementation)  
**Maintained By:** NBA Simulator AWS Team  
**Estimated Effort:** 2 weeks (80 hours)  
**Estimated Cost:** $0.60 one-time processing + $0.10/month storage
