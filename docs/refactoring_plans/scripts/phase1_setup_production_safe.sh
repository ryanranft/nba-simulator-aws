#!/bin/bash
# Production-Safe Refactoring - Phase 1 Setup Script
# Creates parallel package structure WITHOUT touching existing code
# Generated: October 26, 2025

set -e  # Exit on any error

echo "=========================================="
echo "NBA Simulator - Production Safe Refactor"
echo "Phase 1: Parallel Package Creation"
echo "=========================================="
echo ""

# Verify we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Must run from repository root (nba-simulator-aws/)"
    exit 1
fi

# Safety check: Verify database backup exists
echo "🔍 Checking for database backup..."
if [ ! -d "backups" ] || [ -z "$(ls -A backups/*.sql 2>/dev/null)" ]; then
    echo "⚠️  WARNING: No database backup found in backups/"
    read -p "   Continue without backup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted. Please create database backup first."
        exit 1
    fi
fi

# Create git safety tag
echo "📌 Creating git safety tag..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
git tag -a "pre-phase1-$TIMESTAMP" -m "Safety tag before Phase 1: Parallel structure creation"
echo "✅ Tag created: pre-phase1-$TIMESTAMP"

# Create new branch if not already on one
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "refactor/production-safe-v2" ]; then
    echo "🌿 Creating refactoring branch..."
    git checkout -b refactor/production-safe-v2 || git checkout refactor/production-safe-v2
fi

echo ""
echo "Creating parallel package structure..."
echo "======================================"

# Create main package directory
echo "📁 Creating nba_simulator/ package..."
mkdir -p nba_simulator

# Create __init__.py with version info
cat > nba_simulator/__init__.py << 'EOF'
"""
NBA Simulator AWS - Python Package

Production-safe refactored codebase.
Runs in parallel with existing scripts during migration.

Version: 2.0.0-alpha
Status: Parallel operation mode
"""

__version__ = "2.0.0-alpha"
__status__ = "parallel-operation"

# Verify we're not breaking existing imports
import sys
import warnings

# Warn if old imports still being used
class DeprecationHelper:
    """Helper to warn about deprecated import paths"""
    
    def __init__(self, new_path):
        self.new_path = new_path
    
    def warn(self):
        warnings.warn(
            f"Importing from scripts/ is deprecated. Use {self.new_path} instead.",
            DeprecationWarning,
            stacklevel=3
        )

# Export key modules (will be populated as migration progresses)
__all__ = [
    'config',
    'database',
    'etl',
    'monitoring',
    'box_score',
    'utils'
]
EOF

# Create config module
echo "📁 Creating nba_simulator/config/..."
mkdir -p nba_simulator/config

cat > nba_simulator/config/__init__.py << 'EOF'
"""
Configuration management module.
Backward-compatible with existing .env and config files.
"""

from .loader import ConfigLoader, config

__all__ = ['ConfigLoader', 'config']
EOF

cat > nba_simulator/config/loader.py << 'EOF'
"""
Backward-compatible configuration loader.
Supports both legacy .env format and new YAML configs.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import warnings

class ConfigLoader:
    """
    Configuration loader with backward compatibility.
    
    Supports:
    - Legacy .env files (existing scripts)
    - New YAML config files (refactored code)
    """
    
    def __init__(self, legacy_mode: bool = True):
        self.legacy_mode = legacy_mode
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / 'config'
        
    def load_database_config(self) -> Dict[str, Any]:
        """
        Load database configuration.
        
        Returns:
            Dict with keys: host, port, database, user, password
        """
        if self.legacy_mode or not (self.config_dir / 'database.yaml').exists():
            return self._load_legacy_db_config()
        else:
            return self._load_new_db_config()
    
    def _load_legacy_db_config(self) -> Dict[str, Any]:
        """Load from existing .env format"""
        try:
            from dotenv import load_dotenv
            load_dotenv(self.project_root / '.env')
        except ImportError:
            warnings.warn("python-dotenv not installed. Using environment variables only.")
        
        return {
            'host': os.getenv('DB_HOST', os.getenv('RDS_HOST')),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', os.getenv('RDS_DB_NAME', 'nba_simulator')),
            'user': os.getenv('DB_USER', os.getenv('RDS_USERNAME')),
            'password': os.getenv('DB_PASSWORD', os.getenv('RDS_PASSWORD'))
        }
    
    def _load_new_db_config(self) -> Dict[str, Any]:
        """Load from new config/database.yaml"""
        import yaml
        config_file = self.config_dir / 'database.yaml'
        
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def load_s3_config(self) -> Dict[str, str]:
        """Get S3 bucket configuration"""
        return {
            'bucket': os.getenv('S3_BUCKET', 'nba-sim-raw-data-lake'),
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'prefix': os.getenv('S3_PREFIX', '')
        }
    
    def load_aws_config(self) -> Dict[str, str]:
        """Get general AWS configuration"""
        return {
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'profile': os.getenv('AWS_PROFILE', 'default')
        }

# Singleton instance for easy import
config = ConfigLoader(legacy_mode=True)
EOF

cat > nba_simulator/config/database.py << 'EOF'
"""
Database-specific configuration helpers.
"""

from .loader import config

def get_connection_string() -> str:
    """Get PostgreSQL connection string"""
    db_config = config.load_database_config()
    return (
        f"postgresql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )

def get_sqlalchemy_url() -> str:
    """Get SQLAlchemy-compatible URL"""
    return get_connection_string()
EOF

cat > nba_simulator/config/aws_services.py << 'EOF'
"""
AWS service configuration.
"""

from .loader import config

def get_s3_bucket() -> str:
    """Get configured S3 bucket name"""
    return config.load_s3_config()['bucket']

def get_aws_region() -> str:
    """Get AWS region"""
    return config.load_aws_config()['region']
EOF

# Create database module
echo "📁 Creating nba_simulator/database/..."
mkdir -p nba_simulator/database

cat > nba_simulator/database/__init__.py << 'EOF'
"""
Database connection and query management.
Production-safe wrappers with connection pooling.
"""

from .connection import DatabaseConnection, get_db_connection, execute_query

__all__ = ['DatabaseConnection', 'get_db_connection', 'execute_query']
EOF

cat > nba_simulator/database/connection.py << 'EOF'
"""
Production-safe database connection management.
"""

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging
from ..config.loader import config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Thread-safe database connection pool manager.
    Uses connection pooling to avoid overwhelming database.
    """
    
    _connection_pool: Optional[pool.ThreadedConnectionPool] = None
    
    @classmethod
    def initialize_pool(cls, min_conn: int = 2, max_conn: int = 10):
        """
        Initialize connection pool.
        
        Args:
            min_conn: Minimum connections to maintain
            max_conn: Maximum connections allowed
        """
        if cls._connection_pool is not None:
            logger.warning("Connection pool already initialized")
            return
        
        db_config = config.load_database_config()
        
        try:
            cls._connection_pool = pool.ThreadedConnectionPool(
                min_conn,
                max_conn,
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                connect_timeout=10
            )
            logger.info(f"Database pool initialized: {min_conn}-{max_conn} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Get database connection from pool.
        
        Usage:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM games")
        """
        if cls._connection_pool is None:
            cls.initialize_pool()
        
        conn = cls._connection_pool.getconn()
        try:
            yield conn
        finally:
            cls._connection_pool.putconn(conn)
    
    @classmethod
    def execute_query(cls, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute query and return results as list of dicts.
        
        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)
            
        Returns:
            List of dictionaries, one per row
        """
        with cls.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(query, params)
                    
                    # If query returns results
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        return [dict(zip(columns, row)) for row in cur.fetchall()]
                    
                    # For INSERT/UPDATE/DELETE
                    conn.commit()
                    return []
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Query failed: {e}")
                    raise
    
    @classmethod
    def close_pool(cls):
        """Close all connections in pool"""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            cls._connection_pool = None
            logger.info("Database pool closed")

# Legacy-compatible functions
def get_db_connection():
    """
    Legacy-compatible connection function.
    
    Returns raw psycopg2 connection (not from pool).
    Use DatabaseConnection.get_connection() for pooled connections.
    """
    db_config = config.load_database_config()
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password']
    )

def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Legacy-compatible query execution"""
    return DatabaseConnection.execute_query(query, params)
EOF

# Create ETL module with wrappers
echo "📁 Creating nba_simulator/etl/..."
mkdir -p nba_simulator/etl/extractors
mkdir -p nba_simulator/etl/transformers
mkdir -p nba_simulator/etl/loaders

cat > nba_simulator/etl/__init__.py << 'EOF'
"""
ETL (Extract, Transform, Load) module.
Currently wraps existing ETL scripts for safety.
"""

from .extractors import LegacyScriptWrapper

__all__ = ['LegacyScriptWrapper']
EOF

cat > nba_simulator/etl/extractors/__init__.py << 'EOF'
"""
Data extraction wrappers.
Safely wraps existing scraper scripts without replacing them.
"""

import subprocess
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class LegacyScriptWrapper:
    """
    Wraps existing ETL scripts for safe parallel operation.
    
    During refactoring, this calls original scripts.
    After validation, can be replaced with native Python implementations.
    """
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent.parent.parent.parent / 'scripts'
        
        if not self.scripts_dir.exists():
            logger.warning(f"Scripts directory not found: {self.scripts_dir}")
    
    def _run_script(self, script_path: Path, args: List[str]) -> str:
        """
        Run a legacy script and return output.
        
        Args:
            script_path: Path to script
            args: Command line arguments
            
        Returns:
            Script stdout
            
        Raises:
            RuntimeError: If script fails
        """
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        logger.info(f"Running legacy script: {script_path}")
        
        result = subprocess.run(
            ['python', str(script_path)] + args,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Script failed: {result.stderr}")
            raise RuntimeError(f"Script {script_path.name} failed: {result.stderr}")
        
        return result.stdout
    
    def run_espn_scraper(self, *args) -> str:
        """Wrapper for ESPN scraper"""
        script_path = self.scripts_dir / 'etl' / 'espn_scraper.py'
        return self._run_script(script_path, list(args))
    
    def run_hoopr_scraper(self, *args) -> str:
        """Wrapper for hoopR scraper"""
        script_path = self.scripts_dir / 'etl' / 'hoopr_scraper.py'
        return self._run_script(script_path, list(args))
    
    def run_basketball_reference_scraper(self, *args) -> str:
        """Wrapper for Basketball Reference scraper"""
        script_path = self.scripts_dir / 'etl' / 'bball_ref_scraper.py'
        return self._run_script(script_path, list(args))

# Singleton instance
legacy_etl = LegacyScriptWrapper()
EOF

cat > nba_simulator/etl/transformers/__init__.py << 'EOF'
"""
Data transformation utilities.
To be populated during migration.
"""
pass
EOF

cat > nba_simulator/etl/loaders/__init__.py << 'EOF'
"""
Data loading utilities.
To be populated during migration.
"""
pass
EOF

# Create monitoring module
echo "📁 Creating nba_simulator/monitoring/..."
mkdir -p nba_simulator/monitoring

cat > nba_simulator/monitoring/__init__.py << 'EOF'
"""
System monitoring and health checks.
Wrappers for DIMS and other monitoring tools.
"""

from .health_checks import system_health_check

__all__ = ['system_health_check']
EOF

cat > nba_simulator/monitoring/health_checks.py << 'EOF'
"""
System health check utilities.
"""

import logging
from typing import Dict, Any
from ..database import DatabaseConnection

logger = logging.getLogger(__name__)

def system_health_check() -> Dict[str, Any]:
    """
    Run comprehensive system health check.
    
    Returns:
        Dict with health status of all components
    """
    health = {
        'database': check_database_health(),
        'timestamp': None,
        'overall_status': 'unknown'
    }
    
    # Overall status
    health['overall_status'] = 'healthy' if health['database']['status'] == 'ok' else 'degraded'
    
    return health

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and basic metrics"""
    try:
        result = DatabaseConnection.execute_query("SELECT COUNT(*) as cnt FROM games")
        games_count = result[0]['cnt']
        
        return {
            'status': 'ok',
            'games_count': games_count,
            'connection': 'active'
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'connection': 'failed'
        }
EOF

cat > nba_simulator/monitoring/dims.py << 'EOF'
"""
DIMS (Data Integrity Monitoring System) wrappers.
Interfaces with existing DIMS monitoring.
"""

from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

class DIMSWrapper:
    """Wrapper for existing DIMS monitoring scripts"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent.parent.parent / 'scripts' / 'monitoring'
    
    def get_dims_status(self):
        """Get current DIMS status"""
        # Placeholder - implement based on actual DIMS scripts
        logger.info("Fetching DIMS status...")
        return {'status': 'operational', 'last_check': 'N/A'}

dims = DIMSWrapper()
EOF

# Create box_score module
echo "📁 Creating nba_simulator/box_score/..."
mkdir -p nba_simulator/box_score

cat > nba_simulator/box_score/__init__.py << 'EOF'
"""
Box score generation module (Phase 8).
Wrappers for existing box score generation logic.
"""

__all__ = []
EOF

cat > nba_simulator/box_score/generator.py << 'EOF'
"""
Box score generation wrappers.
Phase 8 implementation - DO NOT MODIFY during refactoring.
"""

# Placeholder for Phase 8 box score generation
# This module will be populated after refactoring is complete
pass
EOF

# Create utils module
echo "📁 Creating nba_simulator/utils/..."
mkdir -p nba_simulator/utils

cat > nba_simulator/utils/__init__.py << 'EOF'
"""
Shared utility functions.
"""

from .logging import setup_logging, get_logger
from .validation import validate_game_id, validate_season

__all__ = ['setup_logging', 'get_logger', 'validate_game_id', 'validate_season']
EOF

cat > nba_simulator/utils/logging.py << 'EOF'
"""
Centralized logging configuration.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: str = 'logs'
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        level: Logging level (logging.INFO, logging.DEBUG, etc.)
        log_file: Optional log file name
        log_dir: Directory for log files
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_path / log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers
    )
    
    # Quiet noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)
EOF

cat > nba_simulator/utils/validation.py << 'EOF'
"""
Data validation utilities.
"""

import re
from typing import Optional

def validate_game_id(game_id: str) -> bool:
    """
    Validate NBA game ID format.
    
    Args:
        game_id: Game ID to validate
        
    Returns:
        True if valid
    """
    # ESPN format: typically 9-10 digits
    if re.match(r'^\d{9,10}$', str(game_id)):
        return True
    return False

def validate_season(season: str) -> bool:
    """
    Validate season format (e.g., "2023-24").
    
    Args:
        season: Season string
        
    Returns:
        True if valid format
    """
    pattern = r'^\d{4}-\d{2}$'
    return bool(re.match(pattern, season))

def validate_year(year: int) -> bool:
    """
    Validate year is within NBA history.
    
    Args:
        year: Year to validate
        
    Returns:
        True if valid (1946-present)
    """
    return 1946 <= year <= 2025
EOF

cat > nba_simulator/utils/retry.py << 'EOF'
"""
Retry utilities for network operations.
"""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on failure.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator
EOF

# Create tests directory structure
echo "📁 Creating tests/ structure..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/production
mkdir -p tests/fixtures

cat > tests/__init__.py << 'EOF'
"""
Test suite for NBA Simulator.
"""
pass
EOF

cat > tests/conftest.py << 'EOF'
"""
Pytest configuration with production-safe fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope='session')
def project_root_path():
    """Provide project root path"""
    return project_root

@pytest.fixture(scope='session')
def sample_game_id():
    """Provide a sample game ID for testing"""
    return '401234567'

@pytest.fixture(scope='session')
def sample_season():
    """Provide a sample season for testing"""
    return '2023-24'

# Database fixtures would use MCP here
# (to be populated during test migration phase)
EOF

cat > tests/unit/__init__.py << 'EOF'
"""Unit tests - no external dependencies."""
pass
EOF

cat > tests/integration/__init__.py << 'EOF'
"""Integration tests - uses database and S3."""
pass
EOF

cat > tests/production/__init__.py << 'EOF'
"""Production validation tests - verifies live system health."""
pass
EOF

cat > tests/production/test_data_integrity.py << 'EOF'
"""
Production data integrity tests.
Validates database state during refactoring.
"""

import pytest

# Note: These tests would use MCP in actual implementation
# Placeholder implementations for now

def test_games_table_count():
    """Verify games table has expected record count"""
    # Would use: result = query_database("SELECT COUNT(*) FROM games")
    # assert result['rows'][0]['count'] == 44828
    pass

def test_play_by_play_integrity():
    """Verify play-by-play data unchanged"""
    # Would verify ESPN and hoopR counts
    pass

def test_box_score_generation_active():
    """Ensure Phase 8 still operational"""
    # Would check box_score_snapshots recent updates
    pass

def test_dims_monitoring_operational():
    """Verify DIMS monitoring continues"""
    # Would check dims_metrics_snapshots
    pass
EOF

# Create validation scripts directory
echo "📁 Creating scripts/validation/..."
mkdir -p scripts/validation

cat > scripts/validation/verify_system_health.py << 'EOF'
#!/usr/bin/env python3
"""
System health verification script.
Run before and after refactoring phases.
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba_simulator.monitoring import system_health_check

def main():
    print("Running system health check...")
    print("=" * 50)
    
    health = system_health_check()
    
    print(f"\nOverall Status: {health['overall_status'].upper()}")
    print(f"Database: {health['database']['status']}")
    
    if health['database']['status'] == 'ok':
        print(f"  Games Count: {health['database']['games_count']}")
    
    # Exit with appropriate code
    sys.exit(0 if health['overall_status'] == 'healthy' else 1)

if __name__ == '__main__':
    main()
EOF

chmod +x scripts/validation/verify_system_health.py

# Create backup directory
echo "📁 Creating backups/ directory..."
mkdir -p backups

# Create pytest configuration
echo "📁 Creating pytest.ini..."
cat > pytest.ini << 'EOF'
[pytest]
# Production-safe pytest configuration

# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output options
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    -ra

# Markers for test categorization
markers =
    unit: Unit tests (no external dependencies)
    integration: Integration tests (uses database/S3)
    production: Production validation tests (verifies live system)
    slow: Tests that take more than 1 second
    refactor: Tests specific to refactoring validation

# Logging
log_cli = false
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Coverage (optional)
# addopts = --cov=nba_simulator --cov-report=html
EOF

# Create .gitignore additions
echo "📁 Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Refactoring artifacts
backups/
scripts_legacy/
refactoring_logs/
.refactoring_state

# Python package artifacts
nba_simulator.egg-info/
*.egg-info/

# Test artifacts
.pytest_cache/
htmlcov/
.coverage

# Logs
logs/
*.log

EOF

echo ""
echo "✅ Phase 1 setup complete!"
echo ""
echo "Next steps:"
echo "1. Review created structure: ls -la nba_simulator/"
echo "2. Run health check: python scripts/validation/verify_system_health.py"
echo "3. Run baseline tests: pytest tests/ -v"
echo "4. Review REFACTORING_GUIDE_v2_PRODUCTION.md for next phases"
echo ""
echo "⚠️  Remember: Old scripts in scripts/ are UNTOUCHED and still functional"
echo ""
