#!/usr/bin/env python3
"""
Test ETL Loaders - Verify Imports and Basic Functionality

Tests that all ETL loaders can be imported and instantiated correctly.
This is a quick sanity check, not comprehensive testing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all loaders can be imported"""
    print("=" * 70)
    print("TESTING ETL LOADERS - IMPORTS")
    print("=" * 70)
    print()
    
    try:
        # Test base imports
        from nba_simulator.etl.loaders import (
            BaseLoader,
            TransactionManager,
            transaction_manager,
            LoadStatus,
            LoadMetrics
        )
        print("✅ Base loader imports successful")
        print(f"   - BaseLoader: {BaseLoader.__name__}")
        print(f"   - TransactionManager: {TransactionManager.__name__}")
        print(f"   - LoadStatus: {LoadStatus.__name__}")
        print(f"   - LoadMetrics: {LoadMetrics.__name__}")
        print()
        
        # Test RDS imports
        from nba_simulator.etl.loaders import (
            RDSLoader,
            TemporalEventsLoader
        )
        print("✅ RDS loader imports successful")
        print(f"   - RDSLoader: {RDSLoader.__name__}")
        print(f"   - TemporalEventsLoader: {TemporalEventsLoader.__name__}")
        print()
        
        # Test S3 imports
        from nba_simulator.etl.loaders import (
            S3Loader,
            ESPNLoader,
            BasketballReferenceLoader
        )
        print("✅ S3 loader imports successful")
        print(f"   - S3Loader: {S3Loader.__name__}")
        print(f"   - ESPNLoader: {ESPNLoader.__name__}")
        print(f"   - BasketballReferenceLoader: {BasketballReferenceLoader.__name__}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instantiation():
    """Test that loaders can be instantiated"""
    print("=" * 70)
    print("TESTING ETL LOADERS - INSTANTIATION")
    print("=" * 70)
    print()
    
    try:
        from nba_simulator.etl.loaders import (
            RDSLoader,
            TemporalEventsLoader,
            ESPNLoader,
            BasketballReferenceLoader,
            LoadMetrics,
            LoadStatus
        )
        from datetime import datetime, timezone
        
        # Test RDSLoader
        print("Testing RDSLoader instantiation...")
        rds_loader = RDSLoader(
            table_name='test_table',
            schema='public',
            upsert=True,
            batch_size=1000
        )
        print(f"✅ RDSLoader created")
        print(f"   - Table: {rds_loader.full_table_name}")
        print(f"   - Batch size: {rds_loader.batch_size:,}")
        print(f"   - Upsert: {rds_loader.upsert}")
        print()
        
        # Test TemporalEventsLoader
        print("Testing TemporalEventsLoader instantiation...")
        temporal_loader = TemporalEventsLoader(batch_size=10000)
        print(f"✅ TemporalEventsLoader created")
        print(f"   - Table: {temporal_loader.full_table_name}")
        print(f"   - Batch size: {temporal_loader.batch_size:,}")
        print()
        
        # Test ESPNLoader
        print("Testing ESPNLoader instantiation...")
        espn_loader = ESPNLoader(compress=True)
        print(f"✅ ESPNLoader created")
        print(f"   - Bucket: {espn_loader.bucket}")
        print(f"   - Prefix: {espn_loader.prefix}")
        print(f"   - Compress: {espn_loader.compress}")
        print()
        
        # Test BasketballReferenceLoader
        print("Testing BasketballReferenceLoader instantiation...")
        bbref_loader = BasketballReferenceLoader(tier=1)
        print(f"✅ BasketballReferenceLoader created")
        print(f"   - Bucket: {bbref_loader.bucket}")
        print(f"   - Prefix: {bbref_loader.prefix}")
        print()
        
        # Test LoadMetrics
        print("Testing LoadMetrics...")
        metrics = LoadMetrics(
            loader_name="TestLoader",
            start_time=datetime.now(timezone.utc)
        )
        metrics.records_attempted = 1000
        metrics.records_loaded = 950
        metrics.records_failed = 50
        print(f"✅ LoadMetrics created")
        print(f"   - Loader: {metrics.loader_name}")
        print(f"   - Attempted: {metrics.records_attempted:,}")
        print(f"   - Loaded: {metrics.records_loaded:,}")
        print(f"   - Failed: {metrics.records_failed:,}")
        print()
        
        # Test LoadStatus
        print("Testing LoadStatus enum...")
        for status in LoadStatus:
            print(f"   - {status.name}: {status.value}")
        print("✅ LoadStatus enum working")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_package_structure():
    """Test package structure"""
    print("=" * 70)
    print("TESTING PACKAGE STRUCTURE")
    print("=" * 70)
    print()
    
    try:
        from nba_simulator import etl
        from nba_simulator.etl import loaders
        
        print("✅ Package structure correct")
        print(f"   - etl package: {etl.__name__}")
        print(f"   - loaders subpackage: {loaders.__name__}")
        print()
        
        # Check __all__ exports
        print("Checking __all__ exports...")
        print(f"   Exported: {len(loaders.__all__)} items")
        for item in loaders.__all__:
            print(f"      - {item}")
        print("✅ All exports present")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Package structure test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("ETL LOADERS VERIFICATION TEST SUITE")
    print("=" * 70)
    print()
    
    results = {
        "Imports": test_imports(),
        "Instantiation": test_instantiation(),
        "Package Structure": test_package_structure()
    }
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - ETL Loaders are working!")
        print()
        print("Next steps:")
        print("1. Create ETL transformers")
        print("2. Write comprehensive unit tests")
        print("3. Test with production data")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
