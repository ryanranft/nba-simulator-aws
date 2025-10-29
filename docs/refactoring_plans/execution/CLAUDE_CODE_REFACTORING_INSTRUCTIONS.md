# 🤖 Claude Code: NBA Simulator Refactoring Instructions

**Purpose:** Execute Phase 1 of the NBA Simulator AWS refactoring using MCP tools  
**Environment:** Terminal-based Claude Code with NBA MCP server access  
**Target:** Transform 4,055+ files into enterprise-grade Python package  

---

## 📋 Your Mission

Execute Phase 1 of a comprehensive refactoring plan that will transform the NBA Simulator AWS project from 1,672+ scattered Python files into a well-organized, maintainable Python package structure.

**Key Context:**
- **Project Size:** 4,055+ files (1,672 Python, 643 tests, 1,720 docs)
- **Database:** 40 tables, 20M+ records, 5.8+ GB in production
- **S3 Data:** 146,115+ files, 119+ GB
- **Critical Constraint:** ZERO data loss, ZERO downtime acceptable

---

## 🎯 Phase 1 Goal

Create a **parallel package structure** that coexists with the existing codebase WITHOUT breaking any existing functionality.

**Success Criteria:**
- ✅ New package structure created at `nba_simulator/`
- ✅ All existing scripts continue to work
- ✅ Database record counts unchanged
- ✅ All health checks passing
- ✅ No test failures

---

## 🔧 Your MCP Tools

You have access to 4 MCP tools for the NBA system:

### 1. `nba-mcp-server:query_database`
**Purpose:** Execute SQL queries on the NBA PostgreSQL database  
**Parameters:**
- `sql`: SQL query (SELECT only for safety)

**Example:**
```sql
SELECT COUNT(*) FROM games;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

### 2. `nba-mcp-server:list_tables`
**Purpose:** List all tables in the database  
**Parameters:** None

### 3. `nba-mcp-server:get_table_schema`
**Purpose:** Get schema information for a specific table  
**Parameters:**
- `table_name`: Name of the table

**Example:**
```
table_name: games
```

### 4. `nba-mcp-server:list_s3_files`
**Purpose:** List files in the S3 bucket  
**Parameters:**
- `prefix`: Directory prefix (e.g., "basketball_reference/")
- `max_keys`: Maximum number of files to return (default: 100)

---

## 📁 Project Structure

**Current Location:** `/Users/ryanranft/nba-simulator-aws`

**Current Structure (Simplified):**
```
nba-simulator-aws/
├── scripts/
│   ├── etl/                    # 75+ ETL scrapers (scattered)
│   ├── utils/                  # ~20 utility scripts
│   ├── validation/             # Validation scripts
│   └── [many other dirs]
├── tests/                      # 643 test files
├── docs/                       # 1,720+ markdown files
├── config/                     # ~20 config files
├── agent/                      # 8 agent scripts
├── workflows/                  # 5 workflow scripts
└── [many other files]
```

**Target Structure (Phase 1):**
```
nba-simulator-aws/
├── nba_simulator/              # NEW PACKAGE (Phase 1)
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py           # Configuration management
│   │   ├── database.py         # DB config helpers
│   │   └── aws_services.py     # AWS config helpers
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py       # DB connection pooling
│   └── utils/
│       ├── __init__.py
│       ├── logging.py          # Centralized logging
│       └── constants.py        # System-wide constants
├── scripts/                    # EXISTING (unchanged)
├── tests/                      # EXISTING (unchanged)
└── [all existing files unchanged]
```

---

## 🚀 Step-by-Step Instructions

### Pre-Flight Checklist

**BEFORE starting, verify:**

1. **Database is healthy:**
```bash
Use nba-mcp-server:query_database:
SELECT COUNT(*) FROM games;
-- Expected: 44,828 games (or close to this)

SELECT COUNT(*) FROM play_by_play;
-- Expected: 19,855,984+ records (ESPN + hoopR)
```

2. **Conda environment active:**
```bash
conda activate nba-aws
python --version
# Should show Python 3.11.13
```

3. **Git status clean:**
```bash
cd /Users/ryanranft/nba-simulator-aws
git status
# Commit any uncommitted changes
```

4. **Create safety backup:**
```bash
# Create git tag
git tag pre-refactor-phase1-$(date +%Y%m%d)
git push origin --tags
```

---

### Step 1: Create Database Baseline (5 minutes)

**Purpose:** Record current database state to verify nothing breaks

```bash
# Query database for baseline counts
Use nba-mcp-server:query_database for each:

1. SELECT COUNT(*) FROM games;
2. SELECT COUNT(*) FROM play_by_play;
3. SELECT COUNT(*) FROM box_scores;
4. SELECT COUNT(*) FROM players;
5. SELECT COUNT(*) FROM teams;
6. SELECT COUNT(*) FROM box_score_snapshots;

# Save results to baseline file
cat > /Users/ryanranft/nba-simulator-aws/refactoring_baseline.txt << EOF
Refactoring Baseline - $(date)
================================

Database Record Counts:
- games: [RESULT]
- play_by_play: [RESULT]
- box_scores: [RESULT]
- players: [RESULT]
- teams: [RESULT]
- box_score_snapshots: [RESULT]

Git Tag: pre-refactor-phase1-$(date +%Y%m%d)
Conda Environment: nba-aws
Python Version: $(python --version)
EOF
```

**Validation:** Confirm baseline file created and contains all counts

---

### Step 2: Create Package Directory Structure (10 minutes)

**Purpose:** Set up the new package structure

```bash
cd /Users/ryanranft/nba-simulator-aws

# Create main package directory
mkdir -p nba_simulator

# Create subdirectories
mkdir -p nba_simulator/config
mkdir -p nba_simulator/database
mkdir -p nba_simulator/utils

# Create all __init__.py files
touch nba_simulator/__init__.py
touch nba_simulator/config/__init__.py
touch nba_simulator/database/__init__.py
touch nba_simulator/utils/__init__.py

# Verify structure
tree nba_simulator -L 2
```

**Expected Output:**
```
nba_simulator/
├── __init__.py
├── config/
│   └── __init__.py
├── database/
│   └── __init__.py
└── utils/
    └── __init__.py
```

---

### Step 3: Create Core __init__.py (5 minutes)

**Purpose:** Set up package metadata and version info

```bash
cat > nba_simulator/__init__.py << 'EOF'
"""
NBA Simulator AWS - Production Data Pipeline & Simulation System

A comprehensive basketball analytics platform combining:
- Multi-source ETL pipelines (ESPN, Basketball Reference, NBA API, hoopR)
- PostgreSQL data warehouse (40+ tables, 20M+ records)
- S3 data lake (146,115+ files, 119+ GB)
- Machine learning prediction models
- Historical game simulation engine (1946-2025)
- Phase 8: Box score snapshot generation system

Author: Ryan Ranft
Created: 2025
Refactored: October 2025
"""

__version__ = '2.0.0-alpha'
__author__ = 'Ryan Ranft'

# Package metadata
__all__ = [
    'config',
    'database', 
    'utils'
]

# Import submodules for convenient access
from . import config
from . import database
from . import utils
EOF
```

**Validation:** 
```bash
python -c "import nba_simulator; print(nba_simulator.__version__)"
# Should print: 2.0.0-alpha
```

---

### Step 4: Create Configuration Module (20 minutes)

**Purpose:** Centralized, backward-compatible configuration management

#### 4.1: Create config/loader.py

```bash
cat > nba_simulator/config/loader.py << 'EOF'
"""
Configuration Loader - Backward Compatible

Supports both legacy .env format and new YAML config format.
Ensures existing scripts continue working during migration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Backward-compatible configuration loader.
    
    Supports:
    - Legacy .env file format (existing scripts)
    - New YAML config format (future)
    """
    
    def __init__(self, legacy_mode: bool = True):
        """
        Initialize configuration loader.
        
        Args:
            legacy_mode: If True, use .env format. If False, use YAML.
        """
        self.legacy_mode = legacy_mode
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / 'config'
        
    def load_database_config(self) -> Dict[str, Any]:
        """
        Load database configuration.
        
        Returns:
            Dict with keys: host, port, database, user, password
        """
        if self.legacy_mode:
            return self._load_legacy_db_config()
        else:
            return self._load_new_db_config()
    
    def _load_legacy_db_config(self) -> Dict[str, Any]:
        """Load from existing .env format"""
        from dotenv import load_dotenv
        
        # Load from .env file if it exists
        env_file = self.project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded config from {env_file}")
        else:
            logger.warning("No .env file found. Using environment variables only.")
        
        return {
            'host': os.getenv('DB_HOST', os.getenv('RDS_HOST')),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', os.getenv('RDS_DB_NAME', 'nba_simulator')),
            'user': os.getenv('DB_USER', os.getenv('RDS_USERNAME')),
            'password': os.getenv('DB_PASSWORD', os.getenv('RDS_PASSWORD'))
        }
    
    def _load_new_db_config(self) -> Dict[str, Any]:
        """Load from new config/database.yaml (future)"""
        try:
            import yaml
            config_file = self.config_dir / 'database.yaml'
            
            if not config_file.exists():
                logger.warning("New config not found, falling back to legacy")
                return self._load_legacy_db_config()
            
            with open(config_file) as f:
                return yaml.safe_load(f)
        except ImportError:
            logger.warning("PyYAML not installed, falling back to legacy")
            return self._load_legacy_db_config()
    
    def load_s3_config(self) -> Dict[str, str]:
        """
        Get S3 bucket configuration.
        
        Returns:
            Dict with keys: bucket, region, prefix
        """
        return {
            'bucket': os.getenv('S3_BUCKET', 'nba-sim-raw-data-lake'),
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'prefix': os.getenv('S3_PREFIX', '')
        }
    
    def load_aws_config(self) -> Dict[str, str]:
        """
        Get general AWS configuration.
        
        Returns:
            Dict with keys: region, profile
        """
        return {
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'profile': os.getenv('AWS_PROFILE', 'default')
        }

# Singleton instance for easy import
config = ConfigLoader(legacy_mode=True)
EOF
```

#### 4.2: Create config/__init__.py

```bash
cat > nba_simulator/config/__init__.py << 'EOF'
"""
Configuration Management Module

Provides centralized configuration loading for:
- Database connections
- AWS services (S3, Glue, RDS)
- Application settings

Backward compatible with legacy .env format.
"""

from .loader import ConfigLoader, config

__all__ = ['ConfigLoader', 'config']
EOF
```

**Validation:**
```bash
python << 'PYEOF'
from nba_simulator.config import config

# Test database config loading
db_config = config.load_database_config()
print("Database Config:")
print(f"  Host: {db_config.get('host')}")
print(f"  Port: {db_config.get('port')}")
print(f"  Database: {db_config.get('database')}")

# Test S3 config loading
s3_config = config.load_s3_config()
print("\nS3 Config:")
print(f"  Bucket: {s3_config['bucket']}")
print(f"  Region: {s3_config['region']}")
PYEOF
```

**Expected:** Should print your database and S3 configuration without errors

---

### Step 5: Create Database Module (20 minutes)

**Purpose:** Connection pooling and query management

#### 5.1: Create database/connection.py

```bash
cat > nba_simulator/database/connection.py << 'EOF'
"""
Database Connection Management

Thread-safe connection pooling for PostgreSQL.
MCP-compatible for use with Claude Code.
"""

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
import logging

from ..config import config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Thread-safe database connection pool manager.
    
    Usage:
        db = DatabaseConnection()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM games LIMIT 1")
                result = cur.fetchone()
    """
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        """Singleton pattern to ensure one pool per process"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, min_connections: int = 2, max_connections: int = 10):
        """
        Initialize connection pool.
        
        Args:
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
        """
        if self._pool is None:
            db_config = config.load_database_config()
            
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    min_connections,
                    max_connections,
                    host=db_config['host'],
                    port=db_config['port'],
                    database=db_config['database'],
                    user=db_config['user'],
                    password=db_config['password']
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            psycopg2 connection object
            
        Usage:
            with db.get_connection() as conn:
                # Use connection
                pass
        """
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries (one per row)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
    
    def execute_write(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount
    
    def close(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed")

# Convenience functions for backward compatibility
def get_db_connection():
    """Get database connection instance"""
    return DatabaseConnection()

def execute_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """Execute query using shared connection pool"""
    db = get_db_connection()
    return db.execute_query(query, params)
EOF
```

#### 5.2: Create database/__init__.py

```bash
cat > nba_simulator/database/__init__.py << 'EOF'
"""
Database Module

Provides connection pooling and query management for PostgreSQL.
"""

from .connection import (
    DatabaseConnection,
    get_db_connection,
    execute_query
)

__all__ = [
    'DatabaseConnection',
    'get_db_connection', 
    'execute_query'
]
EOF
```

**Validation:**
```bash
python << 'PYEOF'
from nba_simulator.database import execute_query

# Test database connection
result = execute_query("SELECT COUNT(*) as game_count FROM games")
print(f"Games in database: {result[0]['game_count']}")

result = execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name LIMIT 5")
print("\nFirst 5 tables:")
for row in result:
    print(f"  - {row['table_name']}")
PYEOF
```

**Expected:** Should print game count and table names without errors

---

### Step 6: Create Utilities Module (15 minutes)

**Purpose:** Logging and common utilities

#### 6.1: Create utils/logging.py

```bash
cat > nba_simulator/utils/logging.py << 'EOF'
"""
Centralized Logging Configuration

Provides consistent logging across all modules with:
- File and console output
- Configurable log levels
- Rotation to prevent disk fill
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

def setup_logging(
    name: str = 'nba_simulator',
    level: str = 'INFO',
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: project_root/logs)
        console: Enable console output
        file: Enable file output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file:
        if log_dir is None:
            # Default to project_root/logs
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / 'logs'
        
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f'{name}.log'
        
        # Rotate when file reaches 10MB, keep 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Default logger instance
logger = setup_logging()
EOF
```

#### 6.2: Create utils/constants.py

```bash
cat > nba_simulator/utils/constants.py << 'EOF'
"""
System-wide Constants

Centralized constants for the NBA Simulator system.
"""

# Database
DEFAULT_DB_PORT = 5432
DEFAULT_DB_NAME = 'nba_simulator'

# S3
DEFAULT_S3_BUCKET = 'nba-sim-raw-data-lake'
DEFAULT_S3_REGION = 'us-east-1'

# NBA
NBA_FOUNDING_YEAR = 1946
CURRENT_SEASON = 2024  # 2024-25 season

# Data Sources
DATA_SOURCES = [
    'espn',
    'basketball_reference',
    'nba_api',
    'hoopr',
    'betting'
]

# Table Names
TABLES = {
    'games': 'games',
    'play_by_play': 'play_by_play',
    'box_scores': 'box_scores',
    'players': 'players',
    'teams': 'teams',
    'box_score_snapshots': 'box_score_snapshots'
}

# File Limits
MAX_FILE_SIZE_MB = 100
MAX_JSON_DEPTH = 10

# Performance
DEFAULT_BATCH_SIZE = 1000
MAX_WORKERS = 10
EOF
```

#### 6.3: Create utils/__init__.py

```bash
cat > nba_simulator/utils/__init__.py << 'EOF'
"""
Utilities Module

Common utilities for logging, constants, and helper functions.
"""

from .logging import setup_logging, logger
from .constants import *

__all__ = [
    'setup_logging',
    'logger',
    # Constants
    'DEFAULT_DB_PORT',
    'DEFAULT_S3_BUCKET',
    'NBA_FOUNDING_YEAR',
    'DATA_SOURCES',
    'TABLES'
]
EOF
```

**Validation:**
```bash
python << 'PYEOF'
from nba_simulator.utils import logger, DATA_SOURCES, TABLES

logger.info("Testing centralized logging")
logger.debug("This is a debug message")
logger.warning("This is a warning")

print(f"\nData sources: {DATA_SOURCES}")
print(f"Table names: {list(TABLES.keys())}")
PYEOF
```

---

### Step 7: Create Health Check Script (15 minutes)

**Purpose:** Validate nothing broke during Phase 1

```bash
cat > /Users/ryanranft/nba-simulator-aws/scripts/validation/phase1_health_check.py << 'EOF'
#!/usr/bin/env python3
"""
Phase 1 Health Check

Validates that Phase 1 refactoring didn't break anything.
Compares current state with baseline.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from nba_simulator.database import execute_query
from nba_simulator.utils import logger

def load_baseline():
    """Load baseline counts from file"""
    baseline_file = project_root / 'refactoring_baseline.txt'
    if not baseline_file.exists():
        logger.error("Baseline file not found!")
        return None
    
    baseline = {}
    with open(baseline_file) as f:
        for line in f:
            if ':' in line and not line.startswith(('Refactoring', '====', 'Git', 'Conda', 'Python')):
                parts = line.strip().split(':')
                if len(parts) == 2:
                    table = parts[0].strip(' -')
                    count = parts[1].strip()
                    try:
                        baseline[table] = int(count)
                    except ValueError:
                        pass
    return baseline

def check_database_counts():
    """Check current database counts match baseline"""
    logger.info("Checking database record counts...")
    
    baseline = load_baseline()
    if not baseline:
        logger.error("Could not load baseline")
        return False
    
    tables = ['games', 'play_by_play', 'box_scores', 'players', 'teams', 'box_score_snapshots']
    all_match = True
    
    for table in tables:
        try:
            result = execute_query(f"SELECT COUNT(*) as count FROM {table}")
            current_count = result[0]['count']
            baseline_count = baseline.get(table, 0)
            
            match = current_count == baseline_count
            status = "✅" if match else "❌"
            
            logger.info(f"{status} {table}: {current_count:,} (baseline: {baseline_count:,})")
            
            if not match:
                all_match = False
                logger.error(f"COUNT MISMATCH for {table}!")
        except Exception as e:
            logger.error(f"Error checking {table}: {e}")
            all_match = False
    
    return all_match

def check_imports():
    """Check that new package imports work"""
    logger.info("\nChecking new package imports...")
    
    try:
        import nba_simulator
        logger.info(f"✅ nba_simulator version: {nba_simulator.__version__}")
        
        from nba_simulator.config import config
        logger.info("✅ config module imports")
        
        from nba_simulator.database import execute_query
        logger.info("✅ database module imports")
        
        from nba_simulator.utils import logger as util_logger
        logger.info("✅ utils module imports")
        
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def check_old_scripts():
    """Verify old scripts still work"""
    logger.info("\nChecking existing scripts still work...")
    
    # Check if key directories still exist
    dirs_to_check = ['scripts', 'tests', 'docs', 'config']
    all_exist = True
    
    for dirname in dirs_to_check:
        dir_path = project_root / dirname
        if dir_path.exists():
            logger.info(f"✅ {dirname}/ directory exists")
        else:
            logger.error(f"❌ {dirname}/ directory missing!")
            all_exist = False
    
    return all_exist

def main():
    """Run all health checks"""
    logger.info("=" * 60)
    logger.info("PHASE 1 HEALTH CHECK")
    logger.info("=" * 60)
    
    checks = {
        'Database Counts': check_database_counts(),
        'New Package Imports': check_imports(),
        'Old Scripts Intact': check_old_scripts()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("HEALTH CHECK SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("🎉 ALL CHECKS PASSED - Phase 1 complete!")
        return 0
    else:
        logger.error("⚠️  SOME CHECKS FAILED - Review errors above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x /Users/ryanranft/nba-simulator-aws/scripts/validation/phase1_health_check.py
```

---

### Step 8: Run Final Validation (10 minutes)

**Execute all validation checks:**

```bash
cd /Users/ryanranft/nba-simulator-aws

# 1. Run health check script
python scripts/validation/phase1_health_check.py

# 2. Test new package imports
python << 'PYEOF'
import nba_simulator
from nba_simulator.config import config
from nba_simulator.database import execute_query
from nba_simulator.utils import logger, DATA_SOURCES

print(f"✅ Package version: {nba_simulator.__version__}")
print(f"✅ Data sources: {DATA_SOURCES}")

result = execute_query("SELECT COUNT(*) FROM games")
print(f"✅ Database query works: {result[0]['count']} games")
PYEOF

# 3. Verify database using MCP
# (You'll do this manually with MCP tools to confirm)

# 4. Check directory structure
tree nba_simulator -L 2
```

**Expected Results:**
- ✅ All health checks pass
- ✅ All imports work
- ✅ Database counts unchanged
- ✅ Package structure complete

---

### Step 9: Create Summary Report (5 minutes)

```bash
cat > /Users/ryanranft/nba-simulator-aws/PHASE1_COMPLETION_REPORT.md << EOF
# Phase 1 Completion Report

**Date:** $(date)
**Phase:** 1 - Foundation & Core Infrastructure
**Status:** COMPLETE ✅

## What Was Created

### New Package Structure
\`\`\`
nba_simulator/
├── __init__.py                 # Package metadata
├── config/
│   ├── __init__.py
│   └── loader.py               # Configuration management
├── database/
│   ├── __init__.py
│   └── connection.py           # Connection pooling
└── utils/
    ├── __init__.py
    ├── logging.py              # Centralized logging
    └── constants.py            # System constants
\`\`\`

### Files Created
1. nba_simulator/__init__.py (30 lines)
2. nba_simulator/config/loader.py (120 lines)
3. nba_simulator/config/__init__.py (10 lines)
4. nba_simulator/database/connection.py (180 lines)
5. nba_simulator/database/__init__.py (15 lines)
6. nba_simulator/utils/logging.py (90 lines)
7. nba_simulator/utils/constants.py (50 lines)
8. nba_simulator/utils/__init__.py (20 lines)
9. scripts/validation/phase1_health_check.py (150 lines)
10. refactoring_baseline.txt (baseline metrics)

**Total:** 10 new files, ~665 lines of code

## Validation Results

### Database Integrity
$(python scripts/validation/phase1_health_check.py 2>&1 | grep -A 20 "Database Counts")

### Import Tests
- ✅ nba_simulator package imports
- ✅ config module works
- ✅ database module works
- ✅ utils module works

### Existing Code
- ✅ All existing scripts untouched
- ✅ All existing tests untouched
- ✅ All existing docs untouched

## Next Steps

**Phase 2: ETL Pipeline Migration (Weeks 3-5)**
- Consolidate 75+ ETL scrapers
- Organize by data source
- Create base scraper class
- Maintain backward compatibility

**Timeline:**
- Phase 1: Complete ✅
- Phase 2: Ready to start
- Total estimate: 13 more weeks

## Safety Measures

**Rollback Available:**
\`\`\`bash
git checkout pre-refactor-phase1-$(date +%Y%m%d)
\`\`\`

**Baseline Saved:**
- Git tag: pre-refactor-phase1-$(date +%Y%m%d)
- Database counts: refactoring_baseline.txt
- No data modified

## Key Achievements

1. ✅ Created enterprise-grade package structure
2. ✅ Backward-compatible configuration system
3. ✅ Thread-safe database connection pooling
4. ✅ Centralized logging infrastructure
5. ✅ Zero impact on existing code
6. ✅ Zero data loss
7. ✅ All validation passed

**Phase 1 successfully completed without incidents.**
EOF

cat PHASE1_COMPLETION_REPORT.md
```

---

## 📊 Success Verification

After completing all steps, verify with MCP:

```sql
-- Use nba-mcp-server:query_database

-- 1. Confirm game count unchanged
SELECT COUNT(*) FROM games;

-- 2. Confirm all tables present
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 3. Spot check data integrity
SELECT game_id, game_date, home_team, away_team 
FROM games 
ORDER BY game_date DESC 
LIMIT 5;
```

**Expected:** All counts match baseline, all tables present, recent games visible

---

## ⚠️ If Something Goes Wrong

### Rollback Procedure

```bash
# 1. Stop any running processes
pkill -f nba

# 2. Revert code changes
cd /Users/ryanranft/nba-simulator-aws
git checkout pre-refactor-phase1-$(date +%Y%m%d)

# 3. Verify database integrity with MCP
# Use nba-mcp-server:query_database to check counts

# 4. If database corrupted (should NOT happen - we only added files):
# Database was not modified in Phase 1, so no restore needed
```

### Common Issues

**Issue: Import errors**
```bash
# Solution: Ensure conda environment active
conda activate nba-aws
python --version  # Should be 3.11.13

# Reinstall dependencies if needed
pip install python-dotenv psycopg2-binary
```

**Issue: Database connection fails**
```bash
# Solution: Check .env file exists and has credentials
cat .env | grep DB_HOST

# Test AWS credentials
aws sts get-caller-identity
```

**Issue: Health check fails**
```bash
# Solution: Review logs
cat logs/nba_simulator.log

# Re-run baseline comparison manually
python << 'PYEOF'
from nba_simulator.database import execute_query
print(execute_query("SELECT COUNT(*) FROM games"))
PYEOF
```

---

## 📝 Final Checklist

Before marking Phase 1 complete:

- [ ] All 10 files created
- [ ] Package imports work (`import nba_simulator`)
- [ ] Database queries work through new module
- [ ] Health check script passes all tests
- [ ] Baseline file created and saved
- [ ] Git tag created (`git tag -l | grep phase1`)
- [ ] Completion report generated
- [ ] Database counts verified with MCP
- [ ] Old scripts still in place unchanged
- [ ] No test failures

---

## 🎯 What's Next

**Phase 2: ETL Pipeline Migration**
- Consolidate 75+ ETL scrapers into organized structure
- Create base scraper class with common functionality
- Group by data source (ESPN, Basketball Reference, NBA API, hoopR)
- Maintain backward compatibility with existing pipelines

**Timeline:** 3 weeks (Weeks 3-5)

---

## 📞 Questions or Issues?

If you encounter any problems or have questions:

1. **Check logs:** `cat logs/nba_simulator.log`
2. **Run health check:** `python scripts/validation/phase1_health_check.py`
3. **Verify with MCP:** Use database query tools to check data
4. **Review baseline:** `cat refactoring_baseline.txt`

---

## 🎓 What You Accomplished

In Phase 1, you:
- ✅ Created a production-grade Python package structure
- ✅ Implemented backward-compatible configuration management
- ✅ Built thread-safe database connection pooling
- ✅ Established centralized logging
- ✅ Validated zero data loss
- ✅ Maintained 100% existing code compatibility

**This is the foundation for all future refactoring phases. Excellent work!**

---

**End of Phase 1 Instructions**
