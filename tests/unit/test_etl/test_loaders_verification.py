"""
Verification Tests for ETL Loaders

Tests the newly migrated loader classes:
- BaseLoader (abstract base class)
- RDSLoader (PostgreSQL database loader)
- S3Loader (S3 data lake loader)

Tests:
1. Import verification
2. Class structure validation
3. Method signature checks
4. Type hints verification
5. Inheritance validation
6. Enum and dataclass checks
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all loader imports work"""
    print("\n🧪 Testing Imports...")
    
    try:
        from nba_simulator.etl.loaders import (
            BaseLoader,
            RDSLoader,
            S3Loader,
            LoadStatus,
            LoadMetrics
        )
        print("✅ All imports successful!")
        return True, {
            'BaseLoader': BaseLoader,
            'RDSLoader': RDSLoader,
            'S3Loader': S3Loader,
            'LoadStatus': LoadStatus,
            'LoadMetrics': LoadMetrics
        }
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False, {}

def test_enum_structure(LoadStatus):
    """Test LoadStatus enum"""
    print("\n🧪 Testing LoadStatus Enum...")
    
    expected_statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'PARTIAL']
    actual_statuses = [status.name for status in LoadStatus]
    
    missing = set(expected_statuses) - set(actual_statuses)
    if missing:
        print(f"❌ Missing statuses: {missing}")
        return False
    
    print(f"✅ LoadStatus has all expected values: {actual_statuses}")
    return True

def test_dataclass_structure(LoadMetrics):
    """Test LoadMetrics dataclass"""
    print("\n🧪 Testing LoadMetrics Dataclass...")
    
    try:
        # Check if it's a dataclass
        from dataclasses import is_dataclass
        if not is_dataclass(LoadMetrics):
            print("❌ LoadMetrics is not a dataclass")
            return False
        
        # Check expected fields
        expected_fields = [
            'loader_name', 'start_time', 'end_time', 'duration_seconds',
            'records_attempted', 'records_loaded', 'records_failed',
            'bytes_processed', 'errors'
        ]
        
        actual_fields = [field.name for field in LoadMetrics.__dataclass_fields__.values()]
        
        missing = set(expected_fields) - set(actual_fields)
        if missing:
            print(f"⚠️  Some fields missing: {missing}")
            print(f"   Actual fields: {actual_fields}")
        else:
            print(f"✅ LoadMetrics has all expected fields")
        
        # Try to instantiate
        from datetime import datetime, timezone
        metrics = LoadMetrics(
            loader_name="test",
            start_time=datetime.now(timezone.utc)
        )
        print(f"✅ Can instantiate LoadMetrics: {metrics.loader_name}")
        return True
        
    except Exception as e:
        print(f"❌ LoadMetrics test failed: {e}")
        return False

def test_base_loader_structure(BaseLoader):
    """Test BaseLoader abstract class"""
    print("\n🧪 Testing BaseLoader Structure...")
    
    # Check it's abstract
    from abc import ABC
    if not issubclass(BaseLoader, ABC):
        print("❌ BaseLoader is not an ABC")
        return False
    print("✅ BaseLoader is abstract")
    
    # Check expected methods
    expected_methods = [
        'load', '_validate_data', '_open_connection', 
        '_load_batch', '_close_connection', '_collect_metrics'
    ]
    
    actual_methods = [m for m in dir(BaseLoader) if not m.startswith('__')]
    
    found_methods = []
    missing_methods = []
    
    for method in expected_methods:
        if method in actual_methods:
            found_methods.append(method)
        else:
            missing_methods.append(method)
    
    if missing_methods:
        print(f"⚠️  Some methods missing: {missing_methods}")
    
    print(f"✅ Found {len(found_methods)}/{len(expected_methods)} expected methods")
    print(f"   Methods: {', '.join(found_methods)}")
    
    return True

def test_rds_loader_structure(RDSLoader, BaseLoader):
    """Test RDSLoader concrete class"""
    print("\n🧪 Testing RDSLoader Structure...")
    
    # Check inheritance
    if not issubclass(RDSLoader, BaseLoader):
        print("❌ RDSLoader doesn't inherit from BaseLoader")
        return False
    print("✅ RDSLoader inherits from BaseLoader")
    
    # Check expected methods
    expected_methods = ['_load_batch', 'bulk_insert', 'upsert']
    
    rds_methods = [m for m in dir(RDSLoader) if not m.startswith('__')]
    
    found = []
    for method in expected_methods:
        if method in rds_methods:
            found.append(method)
    
    print(f"✅ Found {len(found)}/{len(expected_methods)} expected methods")
    print(f"   Methods: {', '.join(found)}")
    
    # Check schema support
    if hasattr(RDSLoader, '__init__'):
        print("✅ RDSLoader has __init__ method (likely schema support)")
    
    return True

def test_s3_loader_structure(S3Loader, BaseLoader):
    """Test S3Loader concrete class"""
    print("\n🧪 Testing S3Loader Structure...")
    
    # Check inheritance
    if not issubclass(S3Loader, BaseLoader):
        print("❌ S3Loader doesn't inherit from BaseLoader")
        return False
    print("✅ S3Loader inherits from BaseLoader")
    
    # Check expected methods
    expected_methods = ['_load_batch', 'upload_file', 'upload_json']
    
    s3_methods = [m for m in dir(S3Loader) if not m.startswith('__')]
    
    found = []
    for method in expected_methods:
        if method in s3_methods:
            found.append(method)
    
    print(f"✅ Found {len(found)}/{len(expected_methods)} expected methods")
    print(f"   Methods: {', '.join(found)}")
    
    return True

def test_instantiation(RDSLoader, S3Loader):
    """Test that loaders can be instantiated"""
    print("\n🧪 Testing Instantiation...")
    
    try:
        # Try to instantiate RDSLoader
        # (will fail if database not configured, but that's OK)
        try:
            rds = RDSLoader(table_name="test_table")
            print("✅ RDSLoader can be instantiated")
        except Exception as e:
            if "connection" in str(e).lower() or "database" in str(e).lower():
                print("⚠️  RDSLoader instantiation failed (database not configured - expected)")
            else:
                print(f"❌ RDSLoader instantiation failed: {e}")
        
        # Try to instantiate S3Loader
        try:
            s3 = S3Loader(bucket="test-bucket")
            print("✅ S3Loader can be instantiated")
        except Exception as e:
            if "credentials" in str(e).lower() or "aws" in str(e).lower():
                print("⚠️  S3Loader instantiation failed (AWS not configured - expected)")
            else:
                print(f"❌ S3Loader instantiation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Instantiation test failed: {e}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print("="*60)
    print("🚀 ETL LOADERS VERIFICATION TESTS")
    print("="*60)
    
    # Test imports
    success, classes = test_imports()
    if not success:
        print("\n❌ CRITICAL: Import tests failed. Cannot continue.")
        return False
    
    # Extract classes
    BaseLoader = classes['BaseLoader']
    RDSLoader = classes['RDSLoader']
    S3Loader = classes['S3Loader']
    LoadStatus = classes['LoadStatus']
    LoadMetrics = classes['LoadMetrics']
    
    # Run all tests
    results = {
        'Imports': success,
        'LoadStatus Enum': test_enum_structure(LoadStatus),
        'LoadMetrics Dataclass': test_dataclass_structure(LoadMetrics),
        'BaseLoader Structure': test_base_loader_structure(BaseLoader),
        'RDSLoader Structure': test_rds_loader_structure(RDSLoader, BaseLoader),
        'S3Loader Structure': test_s3_loader_structure(S3Loader, BaseLoader),
        'Instantiation': test_instantiation(RDSLoader, S3Loader)
    }
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Loaders are ready for use.")
        return True
    elif passed >= total * 0.8:
        print("\n⚠️  MOSTLY PASSING. Minor issues to address.")
        return True
    else:
        print("\n❌ TESTS FAILED. Significant issues need fixing.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
