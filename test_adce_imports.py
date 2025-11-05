#!/usr/bin/env python3
"""
Test ADCE imports and basic functionality
"""

def test_imports():
    """Test that all ADCE components can be imported"""
    print("=" * 60)
    print("TESTING ADCE IMPORTS")
    print("=" * 60)
    
    try:
        from nba_simulator.adce import (
            AutonomousLoop, 
            GapDetector, 
            ReconciliationDaemon, 
            Priority
        )
        print("✅ All ADCE imports successful!")
        print(f"  - AutonomousLoop: {AutonomousLoop.__name__}")
        print(f"  - GapDetector: {GapDetector.__name__}")
        print(f"  - ReconciliationDaemon: {ReconciliationDaemon.__name__}")
        print(f"  - Priority enum: {Priority.__name__}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_package_info():
    """Test package metadata"""
    print("\n" + "=" * 60)
    print("TESTING PACKAGE INFO")
    print("=" * 60)
    
    try:
        from nba_simulator import adce
        print(f"✅ Package location: {adce.__file__}")
        print(f"✅ Package exports: {adce.__all__}")
        print(f"\n📖 Package docstring:")
        print(adce.__doc__)
        return True
    except Exception as e:
        print(f"❌ Package info failed: {e}")
        return False


def test_priority_enum():
    """Test Priority enum values"""
    print("\n" + "=" * 60)
    print("TESTING PRIORITY ENUM")
    print("=" * 60)
    
    try:
        from nba_simulator.adce import Priority
        
        print(f"✅ Priority.CRITICAL = {Priority.CRITICAL.value}")
        print(f"✅ Priority.HIGH = {Priority.HIGH.value}")
        print(f"✅ Priority.MEDIUM = {Priority.MEDIUM.value}")
        print(f"✅ Priority.LOW = {Priority.LOW.value}")
        return True
    except Exception as e:
        print(f"❌ Priority enum test failed: {e}")
        return False


def test_class_instantiation():
    """Test that classes can be instantiated"""
    print("\n" + "=" * 60)
    print("TESTING CLASS INSTANTIATION")
    print("=" * 60)
    
    try:
        from nba_simulator.adce import (
            AutonomousLoop,
            ReconciliationDaemon
        )
        
        # Test AutonomousLoop (dry run mode)
        print("Testing AutonomousLoop instantiation...")
        loop = AutonomousLoop(
            config_file="config/autonomous_config.yaml",
            dry_run=True,
            test_mode=True
        )
        print(f"✅ AutonomousLoop created: {loop.__class__.__name__}")
        print(f"  - Config file: {loop.config_file}")
        print(f"  - Dry run: {loop.dry_run}")
        print(f"  - Status: {loop.state['status']}")
        
        # Test ReconciliationDaemon
        print("\nTesting ReconciliationDaemon instantiation...")
        daemon = ReconciliationDaemon(
            interval_hours=1.0,
            dry_run=True
        )
        print(f"✅ ReconciliationDaemon created: {daemon.__class__.__name__}")
        print(f"  - Interval: {daemon.interval_seconds}s")
        print(f"  - Dry run: {daemon.dry_run}")
        
        return True
    except Exception as e:
        print(f"❌ Class instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Verify file structure"""
    print("\n" + "=" * 60)
    print("TESTING FILE STRUCTURE")
    print("=" * 60)
    
    from pathlib import Path
    
    adce_dir = Path("nba_simulator/adce")
    expected_files = [
        "__init__.py",
        "autonomous_loop.py",
        "gap_detector.py",
        "reconciliation.py",
        "health_monitor.py"
    ]
    
    all_exist = True
    for filename in expected_files:
        filepath = adce_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename} ({size:,} bytes)")
        else:
            print(f"❌ {filename} MISSING")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 ADCE MIGRATION VERIFICATION TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Package Info", test_package_info()))
    results.append(("Priority Enum", test_priority_enum()))
    results.append(("File Structure", test_file_structure()))
    results.append(("Class Instantiation", test_class_instantiation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - ADCE migration successful!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
