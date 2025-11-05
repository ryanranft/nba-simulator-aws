#!/usr/bin/env python3
"""
Robust Test for 9.0005 Storage System with Timeouts and Circuit Breakers

This test includes:
- Timeout handling for all operations
- Circuit breaker pattern for external services
- Fast failure detection
- Non-blocking initialization
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import signal
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout exception"""

    pass


class CircuitBreaker:
    """Simple circuit breaker for external service calls"""

    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise e


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutError("Operation timed out")


def with_timeout(timeout_seconds: int):
    """Decorator to add timeout to functions"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Set up signal handler for timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Restore original signal handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


class RobustStorageTester:
    """Robust tester with timeout and circuit breaker protection"""

    def __init__(self):
        self.rds_breaker = CircuitBreaker(failure_threshold=2, timeout=30)
        self.s3_breaker = CircuitBreaker(failure_threshold=2, timeout=30)
        self.test_results = {
            "import_test": False,
            "init_test": False,
            "cache_test": False,
            "rds_test": False,
            "s3_test": False,
            "errors": [],
        }

    @with_timeout(5)
    def test_import(self) -> bool:
        """Test import with timeout"""
        try:
            from scripts.pbp_to_boxscore.enhanced_storage_system import (
                EnhancedBoxScoreStorageSystem,
            )

            self.storage_class = EnhancedBoxScoreStorageSystem
            return True
        except Exception as e:
            self.test_results["errors"].append(f"Import failed: {e}")
            return False

    @with_timeout(10)
    def test_initialization(self) -> bool:
        """Test initialization with timeout"""
        try:
            self.storage = self.storage_class()
            return True
        except Exception as e:
            self.test_results["errors"].append(f"Initialization failed: {e}")
            return False

    @with_timeout(5)
    def test_cache_functionality(self) -> bool:
        """Test cache functionality with timeout"""
        try:
            test_data = [{"test": "data", "timestamp": datetime.now().isoformat()}]

            # Test store
            store_result = self.storage.store_to_local_cache(test_data, "robust_test")
            if not store_result:
                return False

            # Test retrieve
            retrieved = self.storage.get_from_cache("robust_test")
            if retrieved is None:
                return False

            # Test stats
            stats = self.storage.get_storage_stats()
            if not isinstance(stats, dict):
                return False

            # Cleanup
            with self.storage.cache_lock:
                if "robust_test" in self.storage.cache:
                    del self.storage.cache["robust_test"]

            return True
        except Exception as e:
            self.test_results["errors"].append(f"Cache test failed: {e}")
            return False

    @with_timeout(15)
    def test_rds_connection(self) -> bool:
        """Test RDS connection with circuit breaker"""
        try:
            return self.rds_breaker.call(self._test_rds_direct)
        except Exception as e:
            self.test_results["errors"].append(f"RDS test failed: {e}")
            return False

    def _test_rds_direct(self) -> bool:
        """Direct RDS test"""
        try:
            # Try to initialize storage (this will attempt RDS connection)
            self.storage._ensure_storage_initialized()

            # Test basic RDS functionality
            if not self.storage.connection_pool:
                return False

            # Quick connection test
            conn = self.storage.connection_pool.getconn()
            if not conn:
                return False

            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            self.storage.connection_pool.putconn(conn)

            return result[0] == 1
        except Exception as e:
            raise e

    @with_timeout(15)
    def test_s3_connection(self) -> bool:
        """Test S3 connection with circuit breaker"""
        try:
            return self.s3_breaker.call(self._test_s3_direct)
        except Exception as e:
            self.test_results["errors"].append(f"S3 test failed: {e}")
            return False

    def _test_s3_direct(self) -> bool:
        """Direct S3 test"""
        try:
            # Test S3 connectivity
            self.storage.s3_client.head_bucket(Bucket=self.storage.s3_bucket)
            return True
        except Exception as e:
            raise e

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests with proper timeout handling"""
        print("🔧 Robust Storage System Test with Timeouts")
        print("=" * 50)

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

        # Test 4: RDS connection (with circuit breaker)
        print("4. Testing RDS connection...")
        try:
            self.test_results["rds_test"] = self.test_rds_connection()
            print(f"   {'✅ PASS' if self.test_results['rds_test'] else '❌ FAIL'}")
        except Exception as e:
            print(f"   ❌ FAIL (Circuit breaker: {e})")
            self.test_results["rds_test"] = False

        # Test 5: S3 connection (with circuit breaker)
        print("5. Testing S3 connection...")
        try:
            self.test_results["s3_test"] = self.test_s3_connection()
            print(f"   {'✅ PASS' if self.test_results['s3_test'] else '❌ FAIL'}")
        except Exception as e:
            print(f"   ❌ FAIL (Circuit breaker: {e})")
            self.test_results["s3_test"] = False

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
✅ RDS Test: {'PASS' if self.test_results['rds_test'] else 'FAIL'}
✅ S3 Test: {'PASS' if self.test_results['s3_test'] else 'FAIL'}

"""

        if self.test_results["errors"]:
            summary += "❌ Errors:\n"
            for error in self.test_results["errors"]:
                summary += f"   - {error}\n"

        return summary


def main():
    """Main test function"""
    print("🚀 Starting Robust Storage System Test")
    print("   - Timeouts: 5-15 seconds per test")
    print("   - Circuit breakers: 2 failures = OPEN")
    print("   - Fast failure detection")
    print()

    tester = RobustStorageTester()

    try:
        results = tester.run_all_tests()
        print(tester.get_summary())

        # Overall status
        critical_tests = ["import_test", "init_test", "cache_test"]
        critical_passed = all(results[test] for test in critical_tests)

        if critical_passed:
            print("🎉 9.0005 Storage System is working correctly!")
            print("   Core functionality (import, init, cache) is operational.")
            if not results["rds_test"]:
                print("   ⚠️  RDS connection failed - system will work with cache only")
            if not results["s3_test"]:
                print("   ⚠️  S3 connection failed - system will work with cache only")
        else:
            print("💥 9.0005 Storage System has critical issues!")

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    main()
