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

try:
    from nba_simulator.database import execute_query
    from nba_simulator.utils import logger
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("This is expected if running before copying to actual project directory")
    sys.exit(1)

def load_baseline():
    """Load baseline counts from file"""
    baseline_file = project_root / 'refactoring_baseline.txt'
    if not baseline_file.exists():
        logger.error("Baseline file not found!")
        return None
    
    baseline = {}
    with open(baseline_file) as f:
        for line in f:
            if ':' in line and not line.startswith(('Refactoring', '====', 'Git', 'Conda', 'Python', 'Safety', 'Total', 'Database Size', 'S3', 'Phase')):
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
    
    tables = ['games', 'play_by_play', 'box_score_players', 'temporal_events', 'hoopr_play_by_play', 'hoopr_schedule']
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

def check_package_structure():
    """Verify package structure is correct"""
    logger.info("\nChecking package structure...")
    
    required_files = [
        'nba_simulator/__init__.py',
        'nba_simulator/config/__init__.py',
        'nba_simulator/config/loader.py',
        'nba_simulator/database/__init__.py',
        'nba_simulator/database/connection.py',
        'nba_simulator/utils/__init__.py',
        'nba_simulator/utils/logging.py',
        'nba_simulator/utils/constants.py',
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            logger.info(f"✅ {file_path} exists")
        else:
            logger.error(f"❌ {file_path} missing!")
            all_exist = False
    
    return all_exist

def main():
    """Run all health checks"""
    logger.info("=" * 60)
    logger.info("PHASE 1 HEALTH CHECK")
    logger.info("=" * 60)
    
    checks = {
        'Package Structure': check_package_structure(),
        'New Package Imports': check_imports(),
        'Database Counts': check_database_counts(),
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
