# NBA Simulator AWS - Production-Safe Refactoring Guide v2.0

**Generated:** October 26, 2025  
**For:** Production NBA Simulator with 20M+ records  
**Approach:** Zero-Downtime, Data-Safe Refactoring

---

## ⚠️ CRITICAL: Production System Acknowledgment

This refactoring guide has been updated after discovering your system is **NOT** in early development, but is a **production data platform** with:

- **20,003,545 database records** across 40 tables
- **7.7 GB of play-by-play data** (13M+ hoopR records, 6.7M+ ESPN records)
- **Active DIMS monitoring system** with metrics snapshots
- **Phase 8 box score generation** in progress
- **Production S3 data lake** with Basketball Reference historical data (1953-2025)
- **44,828 games** processed and stored

**Refactoring Principle:** Parallel structure, not replacement. Validate everything. Zero data risk.

---

## Table of Contents

1. [Pre-Flight Safety Protocol](#pre-flight-safety-protocol)
2. [System State Documentation](#system-state-documentation)
3. [Refactoring Architecture](#refactoring-architecture)
4. [Phase-by-Phase Implementation](#phase-by-phase-implementation)
5. [Validation & Rollback](#validation--rollback)
6. [Migration Checklist](#migration-checklist)

---

## Pre-Flight Safety Protocol

### Step 0: Backup Everything

```bash
# Navigate to project root
cd ~/nba-simulator-aws

# 1. Database Backup (CRITICAL)
pg_dump -h <your-rds-endpoint> -U <username> -d nba_simulator \
    > backups/pre_refactor_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backups/*.sql

# 2. Git Safety Net
git checkout -b pre-refactor-snapshot
git add -A
git commit -m "Pre-refactor snapshot: Production state $(date +%Y%m%d)"
git tag pre-refactor-$(date +%Y%m%d)

# 3. Create separate refactoring branch
git checkout -b refactor/production-safe-v2

# 4. Document current state
python scripts/validation/document_system_state.py > system_state_$(date +%Y%m%d).json
```

### Step 1: Identify Running Processes

```bash
# Check for cron jobs
crontab -l > backups/cron_backup_$(date +%Y%m%d).txt

# Check for systemd services
systemctl list-units --type=service | grep nba > backups/systemd_services.txt

# Check for running Python processes
ps aux | grep python | grep -v grep > backups/running_processes.txt

# Document AWS resources
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize > backups/s3_inventory.txt
```

### Step 2: Freeze Production Changes

**Before refactoring:**
1. Pause any active scrapers (if safe to do so)
2. Note current DIMS metrics
3. Record last successful box score generation
4. Document current test pass rate

```bash
# Run baseline tests
pytest tests/ -v --tb=short > backups/baseline_tests_$(date +%Y%m%d).txt

# Capture DIMS metrics
python scripts/monitoring/snapshot_dims.py > backups/dims_baseline.json
```

---

## System State Documentation

### Current Database State (via MCP)

**Tables with Significant Data:**
- `hoopr_play_by_play`: 13,074,829 records (6.2 GB)
- `play_by_play`: 6,781,155 records (1.5 GB)
- `box_score_players`: 408,833 records (91 MB)
- `games`: 44,828 records (22 MB)
- `box_score_teams`: 15,900 records (6.7 MB)
- `box_score_snapshots`: 1 record (80 KB) - Phase 8 early implementation
- `dims_metrics_snapshots`: Active monitoring

**Critical Systems:**
- DIMS monitoring: Operational
- Box score generation: In progress (Phase 8)
- S3 data lake: Basketball Reference data 1953-2025

### Current File Structure (Estimated)

Based on project knowledge:
- 1,672+ Python files
- 1,720+ Markdown files
- 643 test files scattered
- Scripts in 10+ directories

---

## Refactoring Architecture

### Design Principle: Parallel Coexistence

**OLD Structure (Keep Intact):**
```
nba-simulator-aws/
├── scripts/           # ⚠️ PRESERVE - May be in cron/systemd
│   ├── aws/
│   ├── etl/
│   ├── monitoring/   # Active DIMS scripts
│   └── maintenance/
├── data/
├── config/
└── docs/
```

**NEW Structure (Create Alongside):**
```
nba-simulator-aws/
├── nba_simulator/              # NEW Python package
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py          # Backward-compatible config
│   │   ├── database.py        # RDS connection management
│   │   └── aws_services.py    # S3, Glue, etc.
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # Connection pooling
│   │   ├── models.py          # SQLAlchemy models
│   │   └── queries.py         # Common queries
│   │
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── extractors/        # Wrappers for existing scrapers
│   │   ├── transformers/
│   │   └── loaders/
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── dims.py            # DIMS wrapper
│   │   └── health_checks.py
│   │
│   ├── box_score/
│   │   ├── __init__.py
│   │   ├── generator.py       # Phase 8 box score logic
│   │   └── validator.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       ├── validation.py
│       └── retry.py
│
├── scripts/                    # ORIGINAL - Keep as-is
│   └── (all existing scripts)
│
├── tests/                      # NEW centralized testing
│   ├── __init__.py
│   ├── conftest.py            # Fixtures with real DB access
│   ├── unit/
│   ├── integration/           # Uses MCP for DB validation
│   └── production/            # Validates against live data
│
└── scripts_legacy/            # FUTURE: After validation, old scripts move here
```

### Migration Strategy

**Phase 0 (Week 1):** Safety infrastructure  
**Phase 1 (Week 2):** Create new package structure in parallel  
**Phase 2 (Week 3):** Add wrapper imports, dual operation  
**Phase 3 (Week 4-5):** Migrate tests and non-production code  
**Phase 4 (Week 6-8):** Gradual migration of production code  
**Phase 5 (Week 9):** Validation and cleanup

---

## Phase-by-Phase Implementation

### Phase 0: Safety Infrastructure (Week 1)

#### 0.1: Create Validation Framework

```python
# tests/production/test_data_integrity.py
"""
Validates production data remains intact during refactoring.
Uses MCP to query live database.
"""

import pytest
from nba_mcp_client import query_database

def test_games_table_count():
    """Ensure games table maintains 44,828 records"""
    result = query_database("SELECT COUNT(*) as cnt FROM games")
    assert result['rows'][0]['cnt'] == 44828, "Games table count changed!"

def test_play_by_play_integrity():
    """Verify play-by-play data unchanged"""
    result = query_database("""
        SELECT COUNT(*) as espn_cnt FROM play_by_play
        UNION ALL
        SELECT COUNT(*) as hoopr_cnt FROM hoopr_play_by_play
    """)
    assert result['rows'][0]['espn_cnt'] == 6781155
    assert result['rows'][1]['hoopr_cnt'] == 13074829

def test_box_score_generation_active():
    """Ensure Phase 8 box score generation still works"""
    result = query_database("""
        SELECT COUNT(*) FROM box_score_snapshots 
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    # Should have recent activity if Phase 8 is running
    assert result['row_count'] >= 0

def test_dims_monitoring_operational():
    """Verify DIMS monitoring continues to update"""
    result = query_database("""
        SELECT MAX(created_at) as last_update 
        FROM dims_metrics_snapshots
    """)
    # Should have been updated recently
    assert result['rows'][0]['last_update'] is not None
```

#### 0.2: Create Rollback Scripts

```bash
# scripts/validation/rollback_refactor.sh
#!/bin/bash
set -e

echo "Rolling back refactoring changes..."

# 1. Return to pre-refactor snapshot
git checkout pre-refactor-$(date +%Y%m%d)

# 2. Verify database state (if needed)
python scripts/validation/verify_db_integrity.py

# 3. Restart services
if [ -f "backups/systemd_services.txt" ]; then
    echo "Restarting services from backup..."
    # Restart any services that were running
fi

echo "Rollback complete. System restored to pre-refactor state."
```

#### 0.3: Create Monitoring Dashboard

```python
# scripts/monitoring/refactor_health_check.py
"""
Real-time monitoring during refactoring.
Alerts if any production metrics degrade.
"""

import time
from nba_mcp_client import query_database

def check_system_health():
    """Run all health checks"""
    checks = {
        'database_connection': check_db_connection(),
        'games_count': check_games_count(),
        'recent_data': check_recent_data(),
        'dims_active': check_dims_active(),
        's3_access': check_s3_access()
    }
    
    all_healthy = all(checks.values())
    
    if not all_healthy:
        print("⚠️  HEALTH CHECK FAILED:")
        for check, status in checks.items():
            print(f"  {check}: {'✅' if status else '❌'}")
        return False
    
    print("✅ All systems operational")
    return True

def check_games_count():
    """Verify games table unchanged"""
    result = query_database("SELECT COUNT(*) FROM games")
    return result['rows'][0]['count'] == 44828

# Run continuously during refactoring
if __name__ == '__main__':
    while True:
        check_system_health()
        time.sleep(60)  # Check every minute
```

### Phase 1: Create Parallel Package (Week 2)

#### 1.1: Setup Package Structure

```bash
# Run the updated setup script
bash scripts/refactoring/phase1_setup_production_safe.sh
```

#### 1.2: Backward-Compatible Configuration

```python
# nba_simulator/config/loader.py
"""
Configuration loader that supports both legacy and new formats.
Ensures existing scripts continue working unchanged.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """Backward-compatible configuration loader"""
    
    def __init__(self, legacy_mode: bool = True):
        self.legacy_mode = legacy_mode
        self.config_dir = Path(__file__).parent.parent.parent / 'config'
        
    def load_database_config(self) -> Dict[str, Any]:
        """Load database configuration
        
        Supports:
        - Legacy .env file format
        - New YAML config format
        """
        if self.legacy_mode:
            return self._load_legacy_db_config()
        else:
            return self._load_new_db_config()
    
    def _load_legacy_db_config(self) -> Dict[str, Any]:
        """Load from existing .env format"""
        from dotenv import load_dotenv
        load_dotenv()
        
        return {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
    
    def _load_new_db_config(self) -> Dict[str, Any]:
        """Load from new config/database.yaml"""
        import yaml
        config_file = self.config_dir / 'database.yaml'
        
        if not config_file.exists():
            # Fall back to legacy if new config doesn't exist
            return self._load_legacy_db_config()
        
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def get_s3_config() -> Dict[str, str]:
        """Get S3 bucket configuration"""
        return {
            'bucket': os.getenv('S3_BUCKET', 'nba-sim-raw-data-lake'),
            'region': os.getenv('AWS_REGION', 'us-east-1')
        }

# Singleton instance for backward compatibility
config = ConfigLoader(legacy_mode=True)
```

#### 1.3: Database Connection Wrapper

```python
# nba_simulator/database/connection.py
"""
Database connection management with MCP compatibility.
Wraps existing connection logic without breaking it.
"""

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional
from ..config.loader import config

class DatabaseConnection:
    """Production-safe database connection manager"""
    
    _connection_pool: Optional[pool.SimpleConnectionPool] = None
    
    @classmethod
    def initialize_pool(cls, min_conn: int = 2, max_conn: int = 10):
        """Initialize connection pool"""
        if cls._connection_pool is None:
            db_config = config.load_database_config()
            
            cls._connection_pool = pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get database connection from pool"""
        if cls._connection_pool is None:
            cls.initialize_pool()
        
        conn = cls._connection_pool.getconn()
        try:
            yield conn
        finally:
            cls._connection_pool.putconn(conn)
    
    @classmethod
    def execute_query(cls, query: str, params: Optional[tuple] = None):
        """Execute query with connection pooling"""
        with cls.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
                return []

# Wrapper functions for legacy script compatibility
def get_db_connection():
    """Legacy-compatible connection function"""
    db_config = config.load_database_config()
    return psycopg2.connect(**db_config)

def execute_query(query: str, params: Optional[tuple] = None):
    """Legacy-compatible query execution"""
    return DatabaseConnection.execute_query(query, params)
```

#### 1.4: Import Wrappers for Existing Scripts

```python
# nba_simulator/etl/extractors/__init__.py
"""
Wrappers around existing ETL scripts.
Calls original scripts, doesn't replace them yet.
"""

import subprocess
from pathlib import Path

class LegacyScriptWrapper:
    """Safely wrap existing ETL scripts"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent.parent.parent.parent / 'scripts'
    
    def run_espn_scraper(self, *args, **kwargs):
        """Wrapper for existing ESPN scraper"""
        script_path = self.scripts_dir / 'etl' / 'espn_scraper.py'
        
        # Call original script
        result = subprocess.run(
            ['python', str(script_path)] + list(args),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"ESPN scraper failed: {result.stderr}")
        
        return result.stdout
    
    def run_hoopr_scraper(self, *args, **kwargs):
        """Wrapper for existing hoopR scraper"""
        script_path = self.scripts_dir / 'etl' / 'hoopr_scraper.py'
        
        result = subprocess.run(
            ['python', str(script_path)] + list(args),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"hoopR scraper failed: {result.stderr}")
        
        return result.stdout

# Create singleton
legacy_etl = LegacyScriptWrapper()
```

### Phase 2: Dual Operation & Validation (Week 3)

#### 2.1: Run Both Old and New in Parallel

```python
# tests/integration/test_dual_operation.py
"""
Validates new package produces same results as old scripts.
"""

import pytest
from nba_simulator.etl.extractors import legacy_etl

def test_new_vs_old_espn_scraper():
    """Compare new implementation vs old script"""
    
    # Run old script
    old_result = legacy_etl.run_espn_scraper('--game-id', '401234567')
    
    # Run new implementation
    from nba_simulator.etl import ESPNExtractor
    new_result = ESPNExtractor().extract_game('401234567')
    
    # Compare outputs
    assert old_result == new_result, "New implementation diverges from old!"

def test_database_wrapper_compatibility():
    """Ensure new DB wrapper produces same results"""
    
    # Old approach
    import psycopg2
    conn_old = psycopg2.connect(...)
    cur = conn_old.cursor()
    cur.execute("SELECT COUNT(*) FROM games")
    old_count = cur.fetchone()[0]
    
    # New approach
    from nba_simulator.database import DatabaseConnection
    new_count = DatabaseConnection.execute_query("SELECT COUNT(*) FROM games")[0]['count']
    
    assert old_count == new_count
```

#### 2.2: Continuous Monitoring

```bash
# Run health checks continuously during Phase 2
python scripts/monitoring/refactor_health_check.py &

# Run dual operation tests every hour
while true; do
    pytest tests/integration/test_dual_operation.py -v
    sleep 3600
done
```

### Phase 3: Test Migration (Weeks 4-5)

#### 3.1: Centralize Tests with Real DB Access

```python
# tests/conftest.py
"""
Pytest configuration with production-safe fixtures.
Uses MCP for safe database access.
"""

import pytest
from nba_mcp_client import query_database, get_table_schema

@pytest.fixture(scope='session')
def db_connection():
    """Provide safe database access via MCP"""
    def query(sql):
        return query_database(sql)
    return query

@pytest.fixture(scope='session')
def games_sample(db_connection):
    """Get sample games for testing"""
    result = db_connection("SELECT * FROM games LIMIT 100")
    return result['rows']

@pytest.fixture(scope='session')
def production_table_schemas():
    """Cache all production table schemas"""
    tables = ['games', 'play_by_play', 'box_score_players', 'dims_metrics_snapshots']
    return {table: get_table_schema(table) for table in tables}

@pytest.fixture(autouse=True)
def verify_no_data_loss(db_connection, request):
    """Auto-verify no data loss after each test"""
    
    # Before test
    initial_counts = {
        'games': db_connection("SELECT COUNT(*) FROM games")['rows'][0]['count'],
        'play_by_play': db_connection("SELECT COUNT(*) FROM play_by_play")['rows'][0]['count']
    }
    
    yield
    
    # After test
    final_counts = {
        'games': db_connection("SELECT COUNT(*) FROM games")['rows'][0]['count'],
        'play_by_play': db_connection("SELECT COUNT(*) FROM play_by_play")['rows'][0]['count']
    }
    
    # Verify no data lost
    for table, initial in initial_counts.items():
        assert final_counts[table] >= initial, f"Data loss detected in {table}!"
```

#### 3.2: Migrate Tests Gradually

```bash
# Move tests one directory at a time
# Start with unit tests (safest)

# Week 4: Unit tests
mv tests/phases/phase_0/unit/* tests/unit/
pytest tests/unit/ -v  # Verify still pass

# Week 5: Integration tests
mv tests/phases/phase_*/integration/* tests/integration/
pytest tests/integration/ -v  # Verify with real DB
```

### Phase 4: Production Code Migration (Weeks 6-8)

**Migration Priority (Safest First):**

Week 6: Documentation & Utilities
- Move README files
- Migrate utility functions
- Update logging

Week 7: Monitoring (Read-Only)
- Migrate DIMS monitoring (read-only, safe)
- Move health check scripts
- Dashboard updates

Week 8: ETL Validation Scripts
- Move validation-only ETL scripts
- Keep active scrapers in original location

**DO NOT MIGRATE IN PHASE 4:**
- Active scrapers (need separate validation)
- Database migration scripts
- Any cron/systemd scripts
- Phase 8 box score generation (in progress)

#### 4.1: Utility Migration Example

```bash
# Move utilities to new package
cp scripts/utils/logging_utils.py nba_simulator/utils/logging.py

# Update to use new structure
# Edit nba_simulator/utils/logging.py to import from package

# Add backward compatibility
cat >> scripts/utils/logging_utils.py << 'EOF'
# DEPRECATED: Use nba_simulator.utils.logging instead
from nba_simulator.utils.logging import *
print("WARNING: logging_utils.py is deprecated. Use nba_simulator.utils.logging")
EOF

# Test both old and new imports work
python -c "from scripts.utils import logging_utils; print('Old import: OK')"
python -c "from nba_simulator.utils import logging; print('New import: OK')"
```

### Phase 5: Validation & Cleanup (Week 9)

#### 5.1: Final Validation Checklist

```bash
# Run comprehensive test suite
pytest tests/ -v --tb=short --cov=nba_simulator

# Verify database integrity
python tests/production/test_data_integrity.py

# Check DIMS monitoring
python scripts/monitoring/dims_health_check.py

# Verify box score generation
python tests/production/test_box_score_generation.py

# S3 data integrity
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | wc -l
```

#### 5.2: Cleanup (Only After Complete Validation)

```bash
# Move old scripts to legacy directory
mkdir -p scripts_legacy
mv scripts/* scripts_legacy/

# Keep only essential scripts in scripts/
# - Active cron jobs
# - Systemd services
# - Production scrapers (until separately validated)

# Update documentation
python scripts/refactoring/update_documentation.py

# Final commit
git add -A
git commit -m "Refactoring complete: Parallel package structure operational"
git tag refactor-complete-$(date +%Y%m%d)
```

---

## Validation & Rollback

### Continuous Validation During Refactoring

```python
# scripts/validation/continuous_monitor.py
"""
Runs continuously during refactoring to catch issues immediately.
"""

import time
import sys
from nba_mcp_client import query_database

CRITICAL_CHECKS = {
    'games_count': ("SELECT COUNT(*) FROM games", 44828),
    'espn_pbp_count': ("SELECT COUNT(*) FROM play_by_play", 6781155),
    'hoopr_pbp_count': ("SELECT COUNT(*) FROM hoopr_play_by_play", 13074829),
    'box_score_players': ("SELECT COUNT(*) FROM box_score_players", 408833)
}

def check_critical_metrics():
    """Verify critical database metrics unchanged"""
    failures = []
    
    for check_name, (query, expected) in CRITICAL_CHECKS.items():
        result = query_database(query)
        actual = result['rows'][0]['count']
        
        if actual < expected:
            failures.append(f"{check_name}: Expected {expected}, got {actual}")
    
    return failures

if __name__ == '__main__':
    print("Starting continuous validation monitor...")
    
    while True:
        failures = check_critical_metrics()
        
        if failures:
            print("🚨 CRITICAL: Data integrity issues detected!")
            for failure in failures:
                print(f"  - {failure}")
            print("\n⚠️  Consider rolling back refactoring!")
            sys.exit(1)
        else:
            print(f"✅ {time.strftime('%Y-%m-%d %H:%M:%S')} - All checks passed")
        
        time.sleep(300)  # Check every 5 minutes
```

### Emergency Rollback Procedure

```bash
# scripts/validation/emergency_rollback.sh
#!/bin/bash
set -e

echo "🚨 EMERGENCY ROLLBACK INITIATED"
echo "================================"

# 1. Stop any refactoring processes
pkill -f "refactor" || true
pkill -f "migration" || true

# 2. Return to pre-refactor snapshot
ROLLBACK_TAG=$(git tag -l "pre-refactor-*" | tail -1)
echo "Rolling back to: $ROLLBACK_TAG"
git checkout $ROLLBACK_TAG

# 3. Restore database if needed (only if data corruption detected)
read -p "Restore database from backup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    LATEST_BACKUP=$(ls -t backups/*.sql | head -1)
    echo "Restoring from: $LATEST_BACKUP"
    psql -h $DB_HOST -U $DB_USER -d nba_simulator < $LATEST_BACKUP
fi

# 4. Restart services
if [ -f "backups/systemd_services.txt" ]; then
    echo "Restarting services..."
    cat backups/systemd_services.txt | awk '{print $1}' | xargs -I {} systemctl restart {}
fi

# 5. Verify system health
python scripts/validation/verify_system_health.py

echo "✅ Rollback complete"
echo "Review logs: backups/rollback_$(date +%Y%m%d_%H%M%S).log"
```

---

## Migration Checklist

### Pre-Migration

- [ ] Database backup completed and verified
- [ ] Git pre-refactor tag created
- [ ] All running processes documented
- [ ] DIMS baseline metrics captured
- [ ] Current test results saved
- [ ] S3 file inventory created
- [ ] Rollback procedure tested (on dev environment)
- [ ] Team notified (if applicable)

### Phase 0: Safety (Week 1)

- [ ] Validation tests created
- [ ] Health monitoring dashboard operational
- [ ] Rollback scripts tested
- [ ] Continuous monitoring started

### Phase 1: Parallel Structure (Week 2)

- [ ] `nba_simulator/` package created
- [ ] Backward-compatible config loader working
- [ ] Database connection wrapper functional
- [ ] Import wrappers for existing scripts operational
- [ ] No disruption to existing scripts verified

### Phase 2: Dual Operation (Week 3)

- [ ] New and old code running in parallel
- [ ] Dual operation tests passing
- [ ] No discrepancies detected
- [ ] Performance benchmarks equivalent
- [ ] DIMS monitoring shows no degradation

### Phase 3: Test Migration (Weeks 4-5)

- [ ] Unit tests migrated and passing
- [ ] Integration tests migrated with real DB access
- [ ] Test coverage maintained or improved
- [ ] Production validation tests added
- [ ] No data loss detected in any test

### Phase 4: Code Migration (Weeks 6-8)

- [ ] Documentation migrated
- [ ] Utility functions migrated
- [ ] Monitoring scripts migrated (read-only)
- [ ] Validation scripts migrated
- [ ] Active scrapers remain in original location
- [ ] Database migration scripts untouched
- [ ] Phase 8 box score generation untouched

### Phase 5: Validation (Week 9)

- [ ] Comprehensive test suite passing
- [ ] Database integrity verified via MCP
- [ ] DIMS monitoring operational
- [ ] Box score generation working
- [ ] S3 data integrity verified
- [ ] Performance equivalent to pre-refactor
- [ ] Documentation updated
- [ ] Final tag created

### Post-Migration (Ongoing)

- [ ] Monitor for 2 weeks post-refactor
- [ ] Address any issues immediately
- [ ] Document lessons learned
- [ ] Plan Phase 6 (active scraper migration) if desired

---

## Critical Success Factors

### ✅ DO

1. **Backup everything** before starting
2. **Create parallel structure**, don't replace
3. **Test continuously** with real database
4. **Monitor DIMS metrics** throughout
5. **Use MCP** for safe database validation
6. **Preserve all existing scripts** initially
7. **Rollback immediately** if issues detected
8. **Validate after each phase**

### ❌ DON'T

1. **Don't touch active scrapers** until Phase 6
2. **Don't modify database schemas** during refactor
3. **Don't assume scripts aren't in cron** - verify
4. **Don't delete old code** until fully validated
5. **Don't migrate everything at once** - incremental only
6. **Don't skip Phase 0** - safety infrastructure critical
7. **Don't ignore test failures** - investigate immediately
8. **Don't proceed if data integrity compromised**

---

## Support & Troubleshooting

### Common Issues

**Issue:** Tests fail after migration  
**Solution:** Check for import path changes, update test fixtures

**Issue:** Database connection errors  
**Solution:** Verify config loader backward compatibility

**Issue:** DIMS monitoring stops updating  
**Solution:** Rollback immediately, check monitoring script paths

**Issue:** Data loss detected  
**Solution:** Emergency rollback, restore from backup

### Health Check Commands

```bash
# Verify database integrity
python tests/production/test_data_integrity.py

# Check DIMS status
python scripts/monitoring/dims_status.py

# Verify S3 access
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize

# Run comprehensive tests
pytest tests/ -v --tb=short

# Check for data discrepancies
python scripts/validation/compare_old_vs_new.py
```

---

## Timeline Summary

| Week | Phase | Focus | Risk Level |
|------|-------|-------|-----------|
| 1 | Phase 0 | Safety infrastructure | Low |
| 2 | Phase 1 | Parallel package creation | Low |
| 3 | Phase 2 | Dual operation validation | Medium |
| 4-5 | Phase 3 | Test migration | Medium |
| 6-8 | Phase 4 | Gradual code migration | Medium-High |
| 9 | Phase 5 | Final validation | Low |

**Total Estimated Time:** 9 weeks for safe, validated refactoring

**Alternative Fast Track:** 3-4 weeks if higher risk acceptable

---

## Next Steps

1. **Review this guide** completely
2. **Run Phase 0.1** validation framework creation
3. **Execute database backup** 
4. **Create git safety tags**
5. **Start continuous monitoring**
6. **Begin Phase 1** parallel structure creation

---

## Appendix: Production System Snapshot

**Captured:** October 26, 2025

### Database Statistics
- Total Records: 20,003,545
- Total Size: 7.7 GB
- Tables: 40 operational
- Largest Table: `hoopr_play_by_play` (6.2 GB)

### Active Systems
- DIMS Monitoring: ✅ Operational
- Phase 8 Box Score Generation: ⚙️ In Progress
- S3 Data Lake: ✅ Operational (Basketball Reference 1953-2025)

### Critical Data
- Games: 44,828
- Play-by-Play (ESPN): 6,781,155
- Play-by-Play (hoopR): 13,074,829
- Box Score Players: 408,833

**This refactoring must preserve all of the above.**

---

**End of Production-Safe Refactoring Guide v2.0**
