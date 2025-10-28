# 📋 Complete Refactoring Execution Plan
## NBA Simulator AWS - Full System Reorganization

**Generated:** October 27, 2025  
**Scope:** All 4,055+ files  
**Timeline:** 14 weeks (production-safe)  
**Approach:** MCP-guided incremental migration

---

## 🎯 Executive Summary

### What We're Refactoring

**Current State:**
- 1,672 Python scripts scattered across 10+ directories
- 643 test files with no clear organization
- 1,720 markdown docs in various locations
- 75+ ETL scrapers mixed together
- 8 autonomous agents in scripts/etl/
- No proper Python package structure
- Imports don't work consistently

**Target State:**
- Clean Python package: `nba_simulator/`
- Organized by function: etl/, agents/, monitoring/, ml/
- Centralized configuration
- Import system that works: `from nba_simulator.etl import ESPNScraper`
- All existing functionality preserved
- Zero data loss

### Critical Constraints

1. **Database has 20M+ production records** - Cannot lose any data
2. **DIMS monitoring is active** - Cannot break monitoring
3. **Phase 8 box score generation running** - Must continue working
4. **ADCE autonomous collection 24/7** - Cannot disrupt
5. **Unknown cron jobs may exist** - Must discover before moving files

---

## 📁 Complete File Mapping

### Current Directory Structure (ALL FILES ACCOUNTED FOR)

```
nba-simulator-aws/ (4,055+ files)
├── scripts/ (1,692+ Python files)
│   ├── etl/ (75+ scrapers + 8 agents + 15+ infrastructure)
│   │   ├── ESPN Scrapers (8 files):
│   │   │   ├── espn_async_scraper.py
│   │   │   ├── espn_incremental_scraper.py
│   │   │   ├── espn_missing_pbp_scraper.py
│   │   │   ├── extract_pbp_local.py
│   │   │   ├── extract_boxscores_local.py
│   │   │   ├── extract_schedule_local.py
│   │   │   ├── validate_espn_pbp_files.py
│   │   │   └── load_espn_pbp_to_rds.py
│   │   │
│   │   ├── Basketball Reference Scrapers (8+ files):
│   │   │   ├── basketball_reference_async_scraper.py
│   │   │   ├── basketball_reference_daily_pbp.py
│   │   │   ├── basketball_reference_pbp_discovery.py
│   │   │   ├── basketball_reference_pbp_backfill.py
│   │   │   ├── build_master_game_list_robust.py
│   │   │   ├── scrape_basketball_reference_comprehensive.py
│   │   │   ├── scrape_bref_tier1_incremental.py
│   │   │   └── bbref_tier_1_agent.py
│   │   │
│   │   ├── hoopR Scrapers (4 files):
│   │   │   ├── hoopr_async_scraper.py
│   │   │   ├── hoopr_incremental_scraper.py
│   │   │   ├── load_hoopr_to_rds.py
│   │   │   └── hoopr_pbp_scraper.py
│   │   │
│   │   ├── NBA API Scrapers (7 files):
│   │   │   ├── nba_api_async_scraper.py
│   │   │   ├── nba_api_comprehensive.py
│   │   │   ├── nba_api_player_dashboards.py
│   │   │   ├── nba_api_team_dashboards.py
│   │   │   ├── load_nba_api_to_rds.py
│   │   │   ├── phase_1_7_nba_stats_agent.py
│   │   │   └── nba_api_extractor.py
│   │   │
│   │   ├── Autonomous Agents (8 files):
│   │   │   ├── master_data_collection_agent.py
│   │   │   ├── phase_1_0_quality_agent.py
│   │   │   ├── phase_1_1_integration_agent.py
│   │   │   ├── phase_1_7_nba_stats_agent.py
│   │   │   ├── phase_1_11_deduplication_agent.py
│   │   │   ├── phase_1c_historical_agent.py
│   │   │   ├── phase_9_2_hoopr_agent.py
│   │   │   └── bbref_tier_1_agent.py
│   │   │
│   │   ├── Infrastructure Scripts (15+ files):
│   │   │   ├── async_scraper_base.py
│   │   │   ├── scraper_config.py
│   │   │   ├── scraper_telemetry.py
│   │   │   ├── scraper_error_handler.py
│   │   │   ├── adaptive_rate_limiter.py
│   │   │   ├── smart_retry_strategies.py
│   │   │   ├── data_validators.py
│   │   │   ├── deduplication_manager.py
│   │   │   ├── provenance_tracker.py
│   │   │   ├── intelligent_extraction.py
│   │   │   ├── structured_output_framework.py
│   │   │   ├── data_dispatcher.py  # ⭐ Dispatcher pattern
│   │   │   ├── create_player_id_mapping.py
│   │   │   ├── gap_detection.py
│   │   │   └── gap_filling.py
│   │   │
│   │   └── Database Loaders (10+ files):
│   │       ├── load_espn_pbp_to_rds.py
│   │       ├── load_hoopr_to_rds.py
│   │       ├── load_nba_api_to_rds.py
│   │       ├── load_box_scores_to_rds.py
│   │       ├── create_unified_views.py
│   │       ├── refresh_materialized_views.py
│   │       └── [other loaders...]
│   │
│   ├── monitoring/ (20+ files)
│   │   ├── dims_cli.py  # ⭐ Active monitoring
│   │   ├── scraper_health_monitor.py
│   │   ├── publish_test_metrics.py
│   │   ├── cloudwatch_metrics.py
│   │   ├── realtime_dashboard.py
│   │   ├── telemetry_collector.py
│   │   └── [other monitoring...]
│   │
│   ├── validation/ (30+ files)
│   │   ├── cross_validate_espn_hoopr.py
│   │   ├── cross_validate_sources.py
│   │   ├── validate_data_quality.py
│   │   ├── validate_schema.py
│   │   ├── data_quality_checker.py
│   │   ├── completeness_checker.py
│   │   ├── verify_system_health.py
│   │   └── [other validators...]
│   │
│   ├── orchestration/ (10+ files)
│   │   ├── scraper_orchestrator.py
│   │   ├── task_queue.py
│   │   ├── priority_scheduler.py
│   │   └── [other orchestration...]
│   │
│   ├── autonomous/ (15+ files)
│   │   ├── autonomous_cli.py  # ⭐ ADCE CLI
│   │   ├── autonomous_loop.py
│   │   ├── reconciliation_engine.py
│   │   ├── gap_detector.py
│   │   ├── health_monitor.py
│   │   └── [other autonomous...]
│   │
│   ├── workflows/ (5+ files)
│   │   ├── overnight_4_source_collection.sh
│   │   ├── incremental_update.sh
│   │   ├── backfill_historical.sh
│   │   └── [other workflows...]
│   │
│   ├── db/ (20+ files)
│   │   ├── schema_migrations/
│   │   ├── create_tables.sql
│   │   ├── create_indexes.sql
│   │   ├── maintenance_scripts/
│   │   └── [other db scripts...]
│   │
│   ├── utils/ (20+ files)
│   │   ├── compare_box_scores.py
│   │   ├── compare_stats.py
│   │   ├── gap_analysis.py
│   │   ├── feature_extractor.py
│   │   ├── date_utils.py
│   │   └── [other utilities...]
│   │
│   └── [other script directories...]
│
├── docs/ (1,720+ markdown files)
│   ├── phases/
│   │   ├── phase_0/ (22 sub-phases, 500+ docs)
│   │   │   ├── 0.0001_initial_data_collection/
│   │   │   ├── 0.0002_[...]/
│   │   │   ├── ...
│   │   │   └── 0.0022_data_inventory_gap_analysis/
│   │   ├── phase_1/ (100+ docs)
│   │   ├── phase_8/ (50+ docs) # ⭐ Box score generation
│   │   └── phase_9/ (50+ docs)
│   │
│   ├── data_sources/ (200+ docs)
│   │   ├── espn/
│   │   ├── basketball_reference/
│   │   ├── hoopr/
│   │   └── nba_api/
│   │
│   ├── adr/ (50+ Architecture Decision Records)
│   ├── claude_workflows/ (50+ workflow docs)
│   ├── architecture/ (100+ docs)
│   ├── guides/ (100+ docs)
│   └── [other doc directories...]
│
├── tests/ (643 test files)
│   ├── phases/
│   │   └── phase_0/ (500+ test files)
│   │       ├── test_0_0001_initial_data_collection.py
│   │       ├── test_0_0002_[...].py
│   │       ├── ...
│   │       └── test_0_0022_data_inventory.py
│   ├── unit/ (50+ files)
│   ├── integration/ (50+ files)
│   └── [other test directories...]
│
├── validators/ (100+ validators)
│   └── phases/
│       └── phase_0/ (100+ validator scripts)
│
├── config/ (20+ configuration files)
│   ├── scraper_config.yaml
│   ├── database.yaml
│   ├── aws_services.yaml
│   ├── logging.yaml
│   └── [other configs...]
│
├── data/ (local data cache)
├── notebooks/ (analysis notebooks)
├── reports/ (generated reports)
├── inventory/ (ADCE reconciliation)
├── backups/ (database backups)
└── .github/workflows/ (CI/CD)

TOTAL: 4,055+ files
```

---

## 🎯 Target Package Structure

### New `nba_simulator/` Package (To Be Created)

```
nba_simulator/
├── __init__.py
│
├── config/  # Configuration management
│   ├── __init__.py
│   ├── loader.py  # Backward-compatible config loader
│   ├── database.py
│   ├── aws_services.py
│   └── scrapers.py
│
├── database/  # Database operations
│   ├── __init__.py
│   ├── connection.py  # Connection pooling
│   ├── models.py  # 40 table models
│   ├── queries.py
│   └── migrations/
│
├── aws/  # AWS service wrappers
│   ├── __init__.py
│   ├── s3.py
│   ├── glue.py
│   ├── rds.py
│   └── cloudwatch.py
│
├── etl/  # ETL pipeline (Phase 2)
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   ├── async_scraper.py  # From async_scraper_base.py
│   │   ├── rate_limiter.py
│   │   ├── retry_strategies.py
│   │   └── error_handler.py
│   │
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── espn/
│   │   │   ├── __init__.py
│   │   │   ├── scraper.py  # Unified ESPN scraper
│   │   │   ├── pbp.py
│   │   │   ├── box_scores.py
│   │   │   └── schedule.py
│   │   ├── basketball_reference/
│   │   │   ├── __init__.py
│   │   │   ├── tier_system.py  # 13-tier system
│   │   │   ├── tiers/
│   │   │   │   ├── tier_1.py
│   │   │   │   ├── tier_2.py
│   │   │   │   └── [...13 tiers...]
│   │   │   ├── pbp.py
│   │   │   └── box_scores.py
│   │   ├── hoopr/
│   │   │   ├── __init__.py
│   │   │   └── scraper.py
│   │   └── nba_api/
│   │       ├── __init__.py
│   │       └── scraper.py
│   │
│   ├── transformers/
│   │   ├── __init__.py
│   │   ├── normalizer.py
│   │   ├── temporal_events.py  # For 5.8 GB table
│   │   └── deduplicator.py
│   │
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── s3_loader.py
│   │   ├── rds_loader.py
│   │   └── bulk_loader.py
│   │
│   └── validation/
│       ├── __init__.py
│       ├── schema_validator.py
│       ├── quality_scorer.py
│       └── cross_validator.py
│
├── agents/  # Autonomous agents (Phase 3)
│   ├── __init__.py
│   ├── base_agent.py
│   ├── master.py  # master_data_collection_agent
│   ├── quality.py  # phase_1_0_quality_agent
│   ├── integration.py
│   ├── nba_stats.py
│   ├── deduplication.py
│   ├── historical.py
│   ├── hoopr.py
│   └── bbref.py
│
├── workflows/  # Workflow orchestration (Phase 3)
│   ├── __init__.py
│   ├── dispatcher.py  # From data_dispatcher.py
│   ├── orchestrator.py
│   ├── task_queue.py
│   ├── overnight_collection.py  # From .sh
│   ├── incremental_update.py
│   └── backfill.py
│
├── adce/  # Autonomous Data Collection Ecosystem (Phase 3)
│   ├── __init__.py
│   ├── autonomous_loop.py
│   ├── reconciliation.py
│   ├── gap_detector.py
│   └── health_monitor.py
│
├── monitoring/  # Monitoring systems (Phase 4)
│   ├── __init__.py
│   ├── dims/
│   │   ├── __init__.py
│   │   ├── cli.py  # From dims_cli.py
│   │   ├── metrics.py
│   │   └── verification.py
│   ├── health/
│   │   ├── __init__.py
│   │   ├── scraper_monitor.py
│   │   ├── database_monitor.py
│   │   └── system_health.py
│   ├── telemetry/
│   │   ├── __init__.py
│   │   └── collector.py
│   └── dashboards/
│       ├── __init__.py
│       └── realtime.py
│
├── validation/  # Data validation (Phase 4)
│   ├── __init__.py
│   ├── data_quality/
│   ├── schema/
│   └── pipeline/
│
├── ml/  # Machine learning (Phase 5)
│   ├── __init__.py
│   ├── features/
│   ├── models/
│   ├── training/
│   └── inference/
│
├── simulation/  # Simulation engine (Phase 6)
│   ├── __init__.py
│   ├── engine/
│   ├── era_adjustments/
│   ├── player_models/
│   └── output/
│       └── box_score_generator.py  # Phase 8
│
└── utils/  # Common utilities
    ├── __init__.py
    ├── logging.py
    ├── retry.py
    ├── timing.py
    ├── constants.py
    └── helpers.py
```

---

## 📅 14-Week Execution Timeline

### Phase 0: Pre-Flight Safety (Week 0 - THIS WEEK)

**Goal:** Ensure zero risk before touching any code

#### Step 1: Discover Active Systems
```sql
-- Use MCP to find active processes
SELECT 
    schemaname,
    relname as table_name,
    n_tup_ins as recent_inserts,
    n_tup_upd as recent_updates,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_tup_ins > 0 OR n_tup_upd > 0
ORDER BY last_autoanalyze DESC
LIMIT 20;
```

#### Step 2: Document Cron Jobs
```bash
# Check for scheduled tasks
crontab -l > /mnt/user-data/outputs/cron_backup.txt
systemctl list-units --type=timer > /mnt/user-data/outputs/systemd_timers.txt
launchctl list | grep nba > /mnt/user-data/outputs/launchd_services.txt
```

#### Step 3: Create Baseline
```bash
# Database baseline
pg_dump > backups/pre_refactor_$(date +%Y%m%d).sql

# Git baseline
git tag pre-refactor-comprehensive-$(date +%Y%m%d)
git push origin --tags

# File structure baseline
tree -L 3 -I '__pycache__|*.pyc' > structure_before_refactoring.txt
find . -name "*.py" | wc -l > python_file_count.txt
```

#### Step 4: Answer Critical Questions
- [ ] What is the `temporal_events` table (5.8 GB)?
- [ ] Which Phase 8 scripts are running?
- [ ] Is ADCE autonomous loop active?
- [ ] Which scrapers run on schedule?

**Deliverables:**
- [ ] Complete system inventory
- [ ] Active process documentation
- [ ] Database backup
- [ ] Git safety tag

---

### Phase 1: Core Infrastructure (Weeks 1-2)

**Goal:** Create foundation package with zero impact on existing code

#### What Gets Created:
```
nba_simulator/
├── __init__.py
├── config/
│   ├── loader.py (backward-compatible)
│   ├── database.py
│   └── aws_services.py
├── database/
│   ├── connection.py (connection pooling)
│   └── queries.py
└── utils/
    ├── logging.py
    ├── constants.py
    └── helpers.py
```

#### Migration Strategy:
1. Create empty package structure
2. Extract common utilities from existing scripts
3. Make config loader work with existing .env files
4. Test: `from nba_simulator.config import config`

#### Success Criteria:
- [ ] Package imports work
- [ ] Database queries work through new module
- [ ] ALL existing scripts still work unchanged
- [ ] All 40 tables have same record counts
- [ ] DIMS monitoring operational
- [ ] Phase 8 box score generation working

**Time:** 2 weeks  
**Risk:** LOW (purely additive)

---

### Phase 2: ETL Framework (Weeks 3-5)

**Goal:** Consolidate 75+ scrapers into organized structure

#### What Gets Migrated:
- 8 ESPN scrapers → `nba_simulator/etl/extractors/espn/`
- 8 Basketball Reference scrapers → `nba_simulator/etl/extractors/basketball_reference/`
- 4 hoopR scrapers → `nba_simulator/etl/extractors/hoopr/`
- 7 NBA API scrapers → `nba_simulator/etl/extractors/nba_api/`
- 15+ infrastructure scripts → `nba_simulator/etl/base/`

#### Migration Strategy:
1. Create unified ESPN scraper that CALLS existing scripts
2. Create unified BBRef scraper (13-tier system)
3. Test equivalence: new scrapers produce identical results
4. Keep old scripts as fallback

#### Success Criteria:
- [ ] New scrapers produce same data as old
- [ ] Data integrity checks pass
- [ ] Can switch between old/new scrapers
- [ ] No data loss in any table

**Time:** 3 weeks  
**Risk:** MEDIUM (touching active scrapers)

---

### Phase 3: Agents & Workflows (Weeks 6-7)

**Goal:** Move orchestration systems to package

#### What Gets Migrated:
- 8 autonomous agents → `nba_simulator/agents/`
- `data_dispatcher.py` → `nba_simulator/workflows/`
- 5 workflow .sh scripts → Python in `nba_simulator/workflows/`
- ADCE system → `nba_simulator/adce/`

#### Migration Strategy:
1. Move dispatcher to package (already well-structured)
2. Convert shell workflows to Python
3. Migrate agents one at a time
4. Test ADCE autonomous loop

#### Success Criteria:
- [ ] Dispatcher works from package
- [ ] Agents operational in new location
- [ ] ADCE 24/7 loop running
- [ ] Gap detection working
- [ ] Reconciliation engine operational

**Time:** 2 weeks  
**Risk:** MEDIUM-HIGH (core orchestration)

---

### Phase 4: Monitoring & Validation (Weeks 8-9)

**Goal:** Move monitoring infrastructure to package

#### What Gets Migrated:
- DIMS CLI → `nba_simulator/monitoring/dims/`
- Scraper health monitor → `nba_simulator/monitoring/health/`
- Telemetry → `nba_simulator/monitoring/telemetry/`
- 30+ validation scripts → `nba_simulator/validation/`

#### Success Criteria:
- [ ] DIMS metrics unchanged
- [ ] Health monitoring operational
- [ ] All validators working
- [ ] No monitoring gaps

**Time:** 2 weeks  
**Risk:** MEDIUM (DIMS is critical)

---

### Phase 5: Testing Infrastructure (Weeks 10-11)

**Goal:** Reorganize 643 test files

#### What Gets Reorganized:
```
tests/
├── unit/
│   ├── test_etl/
│   ├── test_agents/
│   ├── test_monitoring/
│   └── test_ml/
├── integration/
│   ├── test_pipelines/
│   ├── test_workflows/
│   └── test_database/
├── validators/
│   └── phase_0/ (keep existing 100+ validators)
└── fixtures/
```

#### Success Criteria:
- [ ] All 643 tests pass
- [ ] Test coverage ≥80%
- [ ] Organized by component
- [ ] Centralized fixtures

**Time:** 2 weeks  
**Risk:** LOW (tests don't affect production)

---

### Phase 6: Phase 8 Box Score (Weeks 12-13)

**Goal:** Move Phase 8 system to package

⚠️ **CRITICAL:** Phase 8 is actively generating box score snapshots

#### What Gets Migrated:
- Box score generation scripts → `nba_simulator/simulation/output/`
- Snapshot system → `nba_simulator/simulation/output/box_score_generator.py`

#### Migration Strategy:
1. PAUSE Phase 8 generation
2. Move scripts to package
3. Test on historical games first
4. Verify output identical
5. Resume Phase 8

#### Success Criteria:
- [ ] Snapshot generation working
- [ ] Output format unchanged
- [ ] `box_score_snapshots` table active
- [ ] Same quality as before migration

**Time:** 2 weeks  
**Risk:** HIGH (active system)

---

### Phase 7: Final Validation (Week 14)

**Goal:** Comprehensive system validation

#### Validation Checklist:
- [ ] All 40 database tables validated
- [ ] S3 file counts match (146,115+ files)
- [ ] All 643 tests passing
- [ ] DIMS operational
- [ ] Phase 8 operational
- [ ] ADCE autonomous loop running
- [ ] Performance equivalent or better
- [ ] Documentation updated
- [ ] All imports work

#### Final Actions:
```bash
# Run comprehensive validation
pytest tests/ -v --tb=short

# Verify database integrity
python scripts/validation/verify_system_health.py

# Check all table counts
python scripts/validation/validate_all_tables.py

# Verify S3 data intact
python scripts/validation/verify_s3_integrity.py

# Create completion tag
git tag refactor-complete-$(date +%Y%m%d)
```

**Time:** 1 week  
**Risk:** LOW (validation only)

---

## 🛡️ Safety Protocols

### Continuous Monitoring

Run this dashboard script throughout refactoring:

```python
# refactor_monitoring_dashboard.py
from nba_simulator.database import execute_query
import time

def monitor_continuously():
    """Monitor key metrics every 5 minutes during refactoring"""
    
    baseline = {
        'games': 44828,
        'play_by_play': 19855984,  # ESPN + hoopR combined
        'box_score_players': 408833,
        'box_score_snapshots': 1
    }
    
    while True:
        print(f"\n{'='*60}")
        print(f"Refactoring Health Check - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        for table, expected in baseline.items():
            result = execute_query(f"SELECT COUNT(*) as count FROM {table}")
            actual = result[0]['count']
            status = "✅" if actual >= expected else "❌"
            print(f"{status} {table}: {actual:,} (baseline: {expected:,})")
        
        time.sleep(300)  # Check every 5 minutes

if __name__ == '__main__':
    monitor_continuously()
```

### Emergency Rollback

If anything goes wrong:

```bash
# 1. Stop all refactoring work
pkill -f nba

# 2. Rollback code
git checkout pre-refactor-comprehensive-$(date +%Y%m%d)

# 3. Verify database (should be unchanged - we only added files)
python scripts/validation/verify_system_health.py

# 4. Restart services
# [restart any services that were running]
```

---

## 📊 Progress Tracking

### Weekly Checklist

**Week 0 (Pre-Flight):**
- [ ] System inventory complete
- [ ] Active processes documented
- [ ] Database backup created
- [ ] Git safety tag created
- [ ] Critical questions answered

**Week 1-2 (Phase 1):**
- [ ] Package structure created
- [ ] Config system working
- [ ] Database module working
- [ ] All existing scripts unchanged
- [ ] Health check passing

**Week 3-5 (Phase 2):**
- [ ] ESPN scrapers consolidated
- [ ] BBRef scrapers consolidated
- [ ] hoopR scrapers consolidated
- [ ] NBA API scrapers consolidated
- [ ] Data equivalence verified

**Week 6-7 (Phase 3):**
- [ ] Agents migrated
- [ ] Workflows converted
- [ ] ADCE operational
- [ ] Dispatcher working

**Week 8-9 (Phase 4):**
- [ ] DIMS migrated
- [ ] Monitoring operational
- [ ] Validation scripts migrated

**Week 10-11 (Phase 5):**
- [ ] Tests reorganized
- [ ] All tests passing
- [ ] Coverage ≥80%

**Week 12-13 (Phase 6):**
- [ ] Phase 8 migrated
- [ ] Box score generation working
- [ ] Snapshot quality verified

**Week 14 (Phase 7):**
- [ ] Final validation complete
- [ ] Documentation updated
- [ ] Completion tag created

---

## 🎯 Success Metrics

### Technical Metrics
- ✅ All 4,055+ files accounted for
- ✅ Zero data loss (all table counts preserved)
- ✅ All 643 tests passing
- ✅ Test coverage ≥80%
- ✅ All imports working
- ✅ Performance equivalent or better

### Operational Metrics
- ✅ DIMS monitoring operational
- ✅ Phase 8 box score generation working
- ✅ ADCE autonomous collection running
- ✅ All scheduled jobs working
- ✅ Zero downtime

### Code Quality Metrics
- ✅ Proper Python package structure
- ✅ Clear module organization
- ✅ Consistent import patterns
- ✅ Centralized configuration
- ✅ Comprehensive documentation

---

## 🚨 Risk Assessment

### High Risk Items
1. **Phase 8 Box Score Generation** - Active system
2. **DIMS Monitoring** - Cannot break
3. **ADCE Autonomous Loop** - 24/7 operation
4. **Database with 20M+ records** - Cannot corrupt

### Medium Risk Items
1. **75+ Active Scrapers** - Some may be in cron
2. **8 Autonomous Agents** - Complex orchestration
3. **Unknown Scheduled Jobs** - Must discover first

### Low Risk Items
1. **Documentation** - Can't break anything
2. **Test Organization** - Isolated from production
3. **Configuration Files** - Well-understood

---

## 📞 Next Steps

### Immediate Actions (This Week):

1. **Run Phase 0 Discovery**
   ```bash
   # Check for cron jobs
   crontab -l
   
   # Check for systemd timers
   systemctl list-units --type=timer | grep nba
   
   # Check for LaunchAgents (macOS)
   launchctl list | grep nba
   ```

2. **Answer Critical Questions**
   - What is `temporal_events` table?
   - Which scripts populate it?
   - Is Phase 8 actively running?
   - Is ADCE loop active?

3. **Create Baselines**
   ```bash
   # Database
   pg_dump > backups/pre_refactor_$(date +%Y%m%d).sql
   
   # Git
   git tag pre-refactor-comprehensive-$(date +%Y%m%d)
   
   # File structure
   tree -L 3 > structure_before.txt
   ```

4. **Review This Plan**
   - Read through entire plan
   - Note any concerns
   - Identify any missing components

---

**Ready to begin Phase 0?** Let me know when you want to start the discovery process!
