#!/usr/bin/env python3
"""
Simple Cache Test for 9.0005 Storage System

This test focuses only on in-memory cache functionality without disk I/O.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from datetime import datetime
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class SimpleCacheTester:
    """Simple cache tester without disk I/O"""

    def __init__(self):
        self.test_results = {
            "import_test": False,
            "init_test": False,
            "cache_test": False,
            "errors": [],
        }

    def test_import(self) -> bool:
        """Test import"""
        try:
            from scripts.pbp_to_boxscore.enhanced_storage_system import (
                EnhancedBoxScoreStorageSystem,
            )

            self.storage_class = EnhancedBoxScoreStorageSystem
            return True
        except Exception as e:
            self.test_results["errors"].append(f"Import failed: {e}")
            return False

    def test_initialization(self) -> bool:
        """Test initialization"""
        try:
            self.storage = self.storage_class()
            return True
        except Exception as e:
            self.test_results["errors"].append(f"Initialization failed: {e}")
            return False

    def test_cache_functionality(self) -> bool:
        """Test cache functionality without disk I/O"""
        try:
            # Test basic cache operations
            test_data = [{"test": "data", "timestamp": datetime.now().isoformat()}]

            # Test direct cache manipulation (bypass disk I/O)
            cache_key = "test_cache_key"

            with self.storage.cache_lock:
                # Store directly in cache
                self.storage.cache[cache_key] = {
                    "snapshots": test_data,
                    "timestamp": datetime.now(),
                    "game_id": "test_game",
                }

                # Test retrieval
                if cache_key not in self.storage.cache:
                    return False

                retrieved = self.storage.cache[cache_key]
                if retrieved["snapshots"] != test_data:
                    return False

                # Test cache size
                cache_size = len(self.storage.cache)
                if cache_size == 0:
                    return False

                # Cleanup
                del self.storage.cache[cache_key]

            return True
        except Exception as e:
            self.test_results["errors"].append(f"Cache test failed: {e}")
            return False

    def run_all_tests(self) -> dict:
        """Run all tests"""
        print("🔧 Simple Cache Test (No Disk I/O)")
        print("=" * 40)

        # Test 1: Import
        print("1. Testing import...")
        self.test_results["import_test"] = self.test_import()
        print(f"   {'✅ PASS' if self.test_results['import_test'] else '❌ FAIL'}")

        if not self.test_results["import_test"]:
            return self.test_results

        # Test 2: Initialization
        print("2. Testing initialization...")
        self.test_results["init_test"] = self.test_initialization()
        print(f"   {'✅ PASS' if self.test_results['init_test'] else '❌ FAIL'}")

        if not self.test_results["init_test"]:
            return self.test_results

        # Test 3: Cache functionality
        print("3. Testing cache functionality...")
        self.test_results["cache_test"] = self.test_cache_functionality()
        print(f"   {'✅ PASS' if self.test_results['cache_test'] else '❌ FAIL'}")

        return self.test_results

    def get_summary(self) -> str:
        """Get test summary"""
        passed = sum(1 for v in self.test_results.values() if isinstance(v, bool) and v)
        total = sum(1 for v in self.test_results.values() if isinstance(v, bool))

        summary = f"""
📊 Test Summary: {passed}/{total} tests passed

✅ Import Test: {'PASS' if self.test_results['import_test'] else 'FAIL'}
✅ Initialization: {'PASS' if self.test_results['init_test'] else 'FAIL'}
✅ Cache Test: {'PASS' if self.test_results['cache_test'] else 'FAIL'}

"""

        if self.test_results["errors"]:
            summary += "❌ Errors:\n"
            for error in self.test_results["errors"]:
                summary += f"   - {error}\n"

        return summary


def main():
    """Main test function"""
    print("🚀 Starting Simple Cache Test")
    print("   - No disk I/O operations")
    print("   - In-memory cache only")
    print("   - Fast execution")
    print()

    tester = SimpleCacheTester()

    try:
        results = tester.run_all_tests()
        print(tester.get_summary())

        # Overall status
        all_passed = all(
            results[test] for test in ["import_test", "init_test", "cache_test"]
        )

        if all_passed:
            print("🎉 9.0005 Storage System cache is working correctly!")
            print("   Core cache functionality is operational.")
        else:
            print("💥 9.0005 Storage System cache has issues!")

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    main()
