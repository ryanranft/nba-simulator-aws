# Week 2 Implementation Plan - Phase 1 Validation

**Date:** October 28, 2025
**Phase:** Phase 1 Continuation - Database Testing & Validation
**Duration:** Week 2 of 14-week refactoring plan
**Status:** 🔄 IN PROGRESS

---

## 🎯 Week 2 Objectives

Validate the Phase 1 foundation before proceeding to Phase 2 (ETL Framework).

**Goal:** Ensure zero regression and establish baseline metrics for all 40 database tables.

---

## 📋 Week 2 Tasks

### Task 1: Test Database Connection with New Package ✅
**Estimated Time:** 15 minutes
**Priority:** HIGH

**Action Items:**
- [x] Verify `nba_simulator` package imports work
- [x] Test configuration loader with actual environment
- [ ] Test database connection pooling
- [ ] Execute sample queries through new package
- [ ] Verify connection cleanup on exit

**Success Criteria:**
- Database queries work through `nba_simulator.database.execute_query()`
- Connection pool handles concurrent queries
- No connection leaks detected

---

### Task 2: Validate All 40 Tables Baseline
**Estimated Time:** 30 minutes
**Priority:** HIGH

**Action Items:**
- [ ] Query all 40 tables for record counts
- [ ] Document baseline metrics
- [ ] Compare with previous DIMS data
- [ ] Create baseline snapshot file
- [ ] Verify no data loss occurred during Week 1

**Tables to Validate:**
1. games (~44,828 records expected)
2. play_by_play (~19,855,984 records)
3. box_score_players (~408,833 records)
4. box_score_snapshots (Phase 8 table)
5. temporal_events (5.8 GB - needs investigation)
6. [35 other tables...]

**Deliverable:**
- `backups/week2_baseline_$(date +%Y%m%d).json`

---

### Task 3: Test Backward Compatibility
**Estimated Time:** 30 minutes
**Priority:** HIGH

**Action Items:**
- [ ] Verify existing scripts still work
- [ ] Test that old imports don't break
- [ ] Confirm no dependencies on new package yet
- [ ] Run sample ETL script end-to-end
- [ ] Verify DIMS monitoring still operational

**Scripts to Test:**
- `scripts/monitoring/dims_cli.py verify`
- `scripts/autonomous/autonomous_cli.py status`
- Sample scraper (ESPN or Basketball Reference)

**Success Criteria:**
- All existing scripts run without modification
- No import errors from old code
- DIMS metrics unchanged

---

### Task 4: Run Comprehensive Health Checks
**Estimated Time:** 20 minutes
**Priority:** MEDIUM

**Action Items:**
- [ ] Run pytest on all test suites
- [ ] Execute Phase 1 health check
- [ ] Verify DIMS operational
- [ ] Check Phase 8 box score generation
- [ ] Validate ADCE status

**Commands:**
```bash
# Run all tests
pytest tests/ -v --tb=short

# Phase 1 health check
python3 scripts/validation/phase1_health_check.py

# DIMS verification
python scripts/monitoring/dims_cli.py verify

# ADCE status
python scripts/autonomous/autonomous_cli.py status

# Reconciliation test
python scripts/reconciliation/run_reconciliation.py --dry-run
```

---

### Task 5: Answer Critical Questions
**Estimated Time:** 30 minutes
**Priority:** HIGH

These questions must be answered before Phase 2:

#### Q1: What is the `temporal_events` table (5.8 GB)?
**Investigation Steps:**
- [ ] Query table structure
- [ ] Check record count
- [ ] Identify what populates it
- [ ] Determine if it's actively used

**SQL to Run:**
```sql
SELECT COUNT(*) FROM temporal_events;
SELECT pg_size_pretty(pg_total_relation_size('temporal_events'));
SELECT * FROM temporal_events LIMIT 5;
```

#### Q2: Which Phase 8 scripts are actively running?
**Investigation Steps:**
- [ ] Check running processes: `ps aux | grep -i phase | grep python`
- [ ] Review Phase 8 documentation
- [ ] Identify critical scripts
- [ ] Document any dependencies

#### Q3: Is ADCE autonomous loop active?
**Investigation Steps:**
- [ ] Run: `python scripts/autonomous/autonomous_cli.py status`
- [ ] Check cron jobs for ADCE
- [ ] Review last run logs
- [ ] Document operational state

#### Q4: Which scrapers run on schedule?
**Already Documented:**
✅ 4 cron jobs identified:
- Daily audit (9 AM)
- Weekly audit (Monday 9 AM)
- Monthly audit (First Monday 9 AM)
- Odds API quota monitor (hourly)

**Action:**
- [ ] Verify these are the only scheduled jobs
- [ ] Document any Phase 8 or ADCE schedules

---

### Task 6: Create Week 2 Validation Report
**Estimated Time:** 20 minutes
**Priority:** MEDIUM

**Action Items:**
- [ ] Document all baseline metrics
- [ ] Answer all 4 critical questions
- [ ] Create comparison with Week 1
- [ ] Identify any issues found
- [ ] Create Week 3 readiness checklist

**Deliverable:**
- `WEEK2_VALIDATION_REPORT.md`

---

## 🔧 Implementation Scripts

### Script 1: Database Baseline Validator

**File:** `scripts/validation/week2_database_baseline.py`

**Purpose:** Query all 40 tables and create baseline snapshot

**Features:**
- Query all tables for record counts
- Measure table sizes
- Check for recent updates
- Compare with previous baseline
- Generate JSON report

---

### Script 2: Backward Compatibility Tester

**File:** `scripts/validation/week2_backward_compat.py`

**Purpose:** Verify existing scripts still work

**Features:**
- Test old import paths
- Run sample scripts
- Check DIMS operational
- Verify no new dependencies
- Generate compatibility report

---

### Script 3: Critical Questions Investigator

**File:** `scripts/validation/week2_critical_questions.py`

**Purpose:** Answer the 4 critical questions

**Features:**
- Query temporal_events table
- Check running processes
- Query ADCE status
- Document findings
- Generate investigation report

---

## 📊 Success Metrics

### Technical Validation
- [ ] All 40 tables validated with baseline counts
- [ ] Database connection through new package working
- [ ] All existing scripts work unchanged
- [ ] All tests passing (48 reconciliation + existing tests)
- [ ] Zero data loss detected

### Operational Validation
- [ ] DIMS monitoring operational
- [ ] Phase 8 box score generation working (if active)
- [ ] ADCE status documented
- [ ] All scheduled jobs identified

### Documentation
- [ ] 4 critical questions answered
- [ ] Baseline metrics documented
- [ ] Week 2 validation report created
- [ ] Week 3 readiness checklist complete

---

## ⚠️ Risk Mitigation

### If Issues Found
1. **Database connection fails:**
   - Check credentials in .env
   - Verify RDS endpoint accessible
   - Test with psql directly
   - Fall back to old connection method

2. **Existing scripts break:**
   - Document which scripts affected
   - Identify root cause
   - Create compatibility shim if needed
   - Delay Phase 2 until resolved

3. **Data loss detected:**
   - **STOP IMMEDIATELY**
   - Restore from git tag: `pre-refactor-20251028_050228`
   - Investigate root cause
   - Re-implement with additional safeguards

---

## 📅 Week 2 Timeline

**Monday (Today):**
- Task 1: Database connection testing (15 min)
- Task 2: Validate 40 tables (30 min)
- Task 5: Critical questions (30 min)
- **Total:** 75 minutes

**Tuesday:**
- Task 3: Backward compatibility (30 min)
- Task 4: Health checks (20 min)
- **Total:** 50 minutes

**Wednesday:**
- Task 6: Validation report (20 min)
- Review findings
- Create Week 3 plan
- **Total:** 40 minutes

**Total Week 2 Effort:** ~2.5 hours

---

## 🚦 Go/No-Go Criteria for Week 3 (Phase 2)

**Must Pass ALL of These:**

✅ **Database Integrity:**
- [ ] All 40 tables have expected counts (±5%)
- [ ] No tables dropped or corrupted
- [ ] temporal_events table understood

✅ **Backward Compatibility:**
- [ ] All existing scripts work
- [ ] DIMS monitoring operational
- [ ] No import errors

✅ **New Package Validation:**
- [ ] Database queries work through nba_simulator
- [ ] Configuration loading works
- [ ] No connection leaks

✅ **Operational Status:**
- [ ] Phase 8 status documented (if running)
- [ ] ADCE status documented
- [ ] All scheduled jobs identified

**If ANY criterion fails:** Do NOT proceed to Phase 2 until resolved.

---

## 📚 References

- **Week 1 Completion:** `PHASE1_COMPLETION_REPORT.md`
- **Refactoring Plan:** `docs/refactoring/EXECUTION_PLAN.md`
- **Phase 1 Health Check:** `scripts/validation/phase1_health_check.py`
- **Git Safety Tag:** `pre-refactor-20251028_050228`

---

**Status:** Ready to begin Week 2 validation
**Next:** Execute Task 1 (Database connection testing)

