# NBA Simulator Refactoring - Quick Reference Card

**Generated:** October 26, 2025  
**Production System:** 20M+ records, 7.7 GB database  
**Keep this handy during refactoring!**

---

## 🚨 Emergency Contacts

### Rollback Immediately If:
- ❌ Any table shows data loss (COUNT decreases)
- ❌ DIMS monitoring stops updating
- ❌ Phase 8 box score generation fails
- ❌ Health checks show "critical" status
- ❌ Database connection errors persist

### Emergency Rollback Command:
```bash
# STOP EVERYTHING
pkill -f refactor

# ROLLBACK CODE
git checkout pre-refactor-$(date +%Y%m%d)

# VERIFY HEALTH
python scripts/validation/verify_system_health.py

# RESTORE DB (only if corrupted)
psql -h $DB_HOST -U $DB_USER -d nba_simulator < backups/pre_refactor_*.sql
```

---

## ✅ Pre-Flight Checklist (Run Before Starting)

```bash
# 1. Backup database
pg_dump -h $DB_HOST -U $DB_USER -d nba_simulator > backups/pre_refactor_$(date +%Y%m%d).sql

# 2. Create safety tag
git tag pre-refactor-$(date +%Y%m%d)

# 3. Document current state
python -c "from nba_mcp_client import query_database; 
print(f'Games: {query_database(\"SELECT COUNT(*) FROM games\")[\"rows\"][0][\"count\"]}')"

# 4. Verify health
python scripts/validation/verify_system_health.py

# 5. Check for running processes
crontab -l > backups/cron_backup.txt
ps aux | grep python > backups/running_processes.txt
```

---

## 📊 Critical Baseline Metrics

**Never allow these to decrease:**

| Table | Count | Status |
|-------|-------|--------|
| games | 44,828 | ✅ CRITICAL |
| play_by_play | 6,781,155 | ✅ CRITICAL |
| hoopr_play_by_play | 13,074,829 | ✅ CRITICAL |
| box_score_players | 408,833 | ⚠️ Important |
| box_score_teams | 15,900 | ⚠️ Important |

---

## 🔍 Quick Health Checks

### One-Line Health Check
```bash
python scripts/validation/verify_system_health.py
```

### Continuous Monitoring (Recommended)
```bash
python refactor_dashboard.py --continuous --interval 300 &
```

### Check Specific Table
```python
python -c "
from nba_simulator.database import DatabaseConnection
DatabaseConnection.initialize_pool()
result = DatabaseConnection.execute_query('SELECT COUNT(*) FROM games')
print(f'Games: {result[0][\"count\"]:,}')
"
```

### View Latest Health Log
```bash
cat refactoring_logs/latest.json | jq '.overall_status'
```

---

## 📁 Key File Locations

### Documentation
- **Comprehensive Guide:** `REFACTORING_GUIDE_v2_PRODUCTION.md`
- **Executive Summary:** `REFACTORING_DELIVERABLES_v2.md`
- **This Card:** `QUICK_REFERENCE.md`

### Scripts
- **Phase 1 Setup:** `phase1_setup_production_safe.sh`
- **Health Monitor:** `refactor_dashboard.py`
- **System Health:** `scripts/validation/verify_system_health.py`
- **Tests:** `test_comprehensive_validation.py`

### Logs
- **Health Logs:** `refactoring_logs/`
- **Backups:** `backups/`
- **Test Results:** `.pytest_cache/`

---

## 🎯 Phase-by-Phase Quick Guide

### Phase 0: Safety (Week 1)
```bash
# Backup and safety infrastructure
pg_dump ... > backups/
git tag pre-refactor-$(date +%Y%m%d)
python refactor_dashboard.py --continuous &
```

### Phase 1: Parallel Structure (Week 2)
```bash
# Create new package alongside old
bash phase1_setup_production_safe.sh
python scripts/validation/verify_system_health.py
pytest tests/ -v
```

### Phase 2: Dual Operation (Week 3)
```bash
# Both old and new running
pytest tests/integration/test_dual_operation.py -v
python refactor_dashboard.py  # Check for discrepancies
```

### Phase 3: Test Migration (Weeks 4-5)
```bash
# Move tests to centralized structure
mv tests/phases/phase_*/unit/* tests/unit/
pytest tests/ -v --cov=nba_simulator
```

### Phase 4: Code Migration (Weeks 6-8)
```bash
# Gradual migration: utilities → monitoring → ETL
# NEVER touch: active scrapers, Phase 8, database migrations
```

### Phase 5: Validation (Week 9)
```bash
# Final checks
pytest tests/ -v --tb=short
python scripts/validation/verify_system_health.py
python refactor_dashboard.py
```

---

## 🧪 Testing Commands

### Run All Tests
```bash
pytest tests/ -v
```

### Critical Tests Only
```bash
pytest tests/production/ -v -m critical
```

### Production Validation
```bash
pytest tests/production/test_comprehensive_validation.py -v
```

### Single Test with Details
```bash
pytest tests/production/test_data_integrity.py::test_games_count -v --tb=long
```

### Generate Coverage Report
```bash
pytest tests/ -v --cov=nba_simulator --cov-report=html
```

---

## 🔧 Common Queries

### Check All Table Counts
```python
python -c "
from nba_simulator.database import DatabaseConnection
DatabaseConnection.initialize_pool()

tables = ['games', 'play_by_play', 'hoopr_play_by_play', 
          'box_score_players', 'box_score_teams']
for table in tables:
    result = DatabaseConnection.execute_query(f'SELECT COUNT(*) FROM {table}')
    print(f'{table:25} {result[0][\"count\"]:>12,}')
"
```

### Check DIMS Status
```python
python -c "
from nba_simulator.database import DatabaseConnection
DatabaseConnection.initialize_pool()
result = DatabaseConnection.execute_query('''
    SELECT MAX(created_at) as last_update 
    FROM dims_metrics_snapshots
''')
print(f'DIMS last update: {result[0][\"last_update\"]}')
"
```

### Check Phase 8 Activity
```python
python -c "
from nba_simulator.database import DatabaseConnection
DatabaseConnection.initialize_pool()
result = DatabaseConnection.execute_query('''
    SELECT COUNT(*) as count, MAX(created_at) as last_update
    FROM box_score_snapshots
    WHERE created_at > NOW() - INTERVAL '7 days'
''')
print(f'Phase 8 activity (7d): {result[0]}')
"
```

---

## 🚦 Status Indicators

### Health Check Output
- ✅ **Healthy:** All systems operational, proceed with confidence
- ⚠️  **Warning:** Some degradation, monitor closely
- 🚨 **Critical:** Significant issues, consider rollback
- ❌ **Error:** System failure, immediate rollback required

### Test Status
- ✅ **PASSED:** Test successful
- ⚠️  **SKIPPED:** Test skipped (package not available yet)
- ❌ **FAILED:** Test failed (investigate immediately)
- 🔄 **XFAIL:** Expected failure (documented issue)

---

## 📋 Daily Refactoring Checklist

### Start of Day
- [ ] Check health dashboard
- [ ] Review overnight logs
- [ ] Run quick health check
- [ ] Check git status
- [ ] Verify backups exist

### During Work
- [ ] Monitor health dashboard continuously
- [ ] Run tests after each change
- [ ] Commit frequently with clear messages
- [ ] Document any issues
- [ ] Keep refactoring log updated

### End of Day
- [ ] Run full test suite
- [ ] Check health summary
- [ ] Review logs for anomalies
- [ ] Commit all changes
- [ ] Update progress tracking

---

## 🐛 Troubleshooting Quick Fixes

### Import Error
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/nba-simulator-aws"
python -c "import nba_simulator; print('OK')"
```

### Database Connection Error
```bash
# Check environment variables
echo $DB_HOST $DB_USER $DB_NAME

# Test connection
psql -h $DB_HOST -U $DB_USER -d nba_simulator -c "SELECT 1"

# Restart connection pool
python -c "from nba_simulator.database import DatabaseConnection; DatabaseConnection.initialize_pool()"
```

### Test Failures
```bash
# Run with verbose output
pytest tests/failing_test.py -v --tb=long

# Check database state
python scripts/validation/verify_system_health.py

# Compare with baseline
git diff pre-refactor-$(date +%Y%m%d) -- tests/
```

### Health Check Shows Warning
```bash
# View detailed status
python refactor_dashboard.py

# Check specific metric
python -c "
from nba_simulator.database import execute_query
result = execute_query('SELECT COUNT(*) FROM games')
print(f'Current: {result[0][\"count\"]}, Expected: 44,828')
"
```

---

## 🎯 Success Criteria Quick Check

### Phase 1 Complete When:
- [ ] `nba_simulator/` package created
- [ ] Old `scripts/` unchanged and functional
- [ ] `pytest tests/ -v` passes
- [ ] `python scripts/validation/verify_system_health.py` returns 0
- [ ] All table counts >= baseline

### Overall Success When:
- [ ] All tests passing (100%)
- [ ] All table counts >= baseline
- [ ] DIMS operational
- [ ] Phase 8 working
- [ ] Performance equivalent or better
- [ ] Documentation updated

---

## 💡 Pro Tips

1. **Run health checks before AND after each change**
2. **Commit frequently** with descriptive messages
3. **Never delete old code** until fully validated
4. **Monitor continuously** during active migration
5. **Test on dev/staging first** if available
6. **Keep rollback procedure handy**
7. **Document any deviations** from plan
8. **Ask for help early** if unsure

---

## 📞 Quick Help

### Get System Status
```bash
python refactor_dashboard.py
```

### View Comprehensive Guide
```bash
less REFACTORING_GUIDE_v2_PRODUCTION.md
```

### Check What Changed
```bash
git diff pre-refactor-$(date +%Y%m%d)
```

### Rollback One File
```bash
git checkout pre-refactor-$(date +%Y%m%d) -- path/to/file.py
```

---

## 🎓 Remember

- **Production system with 20M+ records** - treat with care
- **Parallel structure, not replacement** - old code stays
- **Validate everything** - trust but verify
- **Rollback immediately** if any data loss detected
- **Document as you go** - future you will thank you

---

**When in doubt, run the health check and consult the comprehensive guide!**

```bash
python scripts/validation/verify_system_health.py
cat REFACTORING_GUIDE_v2_PRODUCTION.md
```

---

**Generated:** October 26, 2025  
**For:** NBA Simulator AWS Production Refactoring  
**Keep this accessible during all refactoring work!**
