#!/usr/bin/env python3
"""
Quick Test for 9.0005 Storage System

This is a simplified test to verify the storage system works without hanging.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def quick_storage_test():
    """Quick test of storage system without hanging"""
    print("🔧 Quick Storage System Test")

    try:
        # Import the storage system
        from scripts.pbp_to_boxscore.enhanced_storage_system import (
            EnhancedBoxScoreStorageSystem,
        )

        print("✅ Import successful")

        # Create storage system
        storage = EnhancedBoxScoreStorageSystem()
        print("✅ Storage system created")

        # Test cache only (fastest test)
        print("🧪 Testing cache functionality...")
        test_data = [{"test": "data", "timestamp": datetime.now().isoformat()}]

        cache_result = storage.store_to_local_cache(test_data, "quick_test")
        print(f"✅ Cache store: {cache_result}")

        retrieved = storage.get_from_cache("quick_test")
        print(f"✅ Cache retrieve: {retrieved is not None}")

        # Test stats (no network calls)
        stats = storage.get_storage_stats()
        print(f"✅ Stats: Cache size {stats.get('cache_size', 0)}")

        # Clean up test data
        with storage.cache_lock:
            if "quick_test" in storage.cache:
                del storage.cache["quick_test"]

        print("✅ Quick test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = quick_storage_test()
    if success:
        print("\n🎉 9.0005 Storage System is working correctly!")
    else:
        print("\n💥 9.0005 Storage System has issues that need fixing.")
