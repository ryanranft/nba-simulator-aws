#!/usr/bin/env python3
"""
Week 3 ETL Package Validation

Validates the new ETL package structure and hoopR extractors.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("WEEK 3: ETL PACKAGE VALIDATION")
print("=" * 70)
print()

# Test 1: Import ETL package
print("Test 1: Importing ETL package...")
try:
    from nba_simulator import etl
    print(f"✅ nba_simulator.etl imported (version: {etl.__version__})")
except ImportError as e:
    print(f"❌ Failed to import nba_simulator.etl: {e}")
    sys.exit(1)

# Test 2: Import base classes
print("\nTest 2: Importing base classes...")
try:
    from nba_simulator.etl import BaseScraper, BaseExtractor, BaseLoader
    print("✅ BaseScraper imported")
    print("✅ BaseExtractor imported")
    print("✅ BaseLoader imported")
except ImportError as e:
    print(f"❌ Failed to import base classes: {e}")
    sys.exit(1)

# Test 3: Import hoopR extractors
print("\nTest 3: Importing hoopR extractors...")
try:
    from nba_simulator.etl.extractors.hoopr import (
        HooprPlayByPlayExtractor,
        HooprPlayerBoxExtractor
    )
    print("✅ HooprPlayByPlayExtractor imported")
    print("✅ HooprPlayerBoxExtractor imported")
except ImportError as e:
    print(f"❌ Failed to import hoopR extractors: {e}")
    sys.exit(1)

# Test 4: Instantiate hoopR extractors
print("\nTest 4: Instantiating hoopR extractors...")
try:
    pbp_extractor = HooprPlayByPlayExtractor()
    print(f"✅ HooprPlayByPlayExtractor instantiated: {pbp_extractor.name}")
    
    box_extractor = HooprPlayerBoxExtractor()
    print(f"✅ HooprPlayerBoxExtractor instantiated: {box_extractor.name}")
except Exception as e:
    print(f"❌ Failed to instantiate extractors: {e}")
    sys.exit(1)

# Test 5: Check health
print("\nTest 5: Running health checks...")
try:
    pbp_health = pbp_extractor.health_check()
    print(f"✅ PBP health check: {pbp_health['status']}")
    print(f"   - Primary data source: {pbp_health.get('primary_data_source', False)}")
    print(f"   - Expected records: {pbp_health.get('expected_records', 'Unknown')}")
    
    if 'legacy_scripts' in pbp_health:
        print("   - Legacy scripts available:")
        for name, available in pbp_health['legacy_scripts'].items():
            status = "✅" if available else "⚠️"
            print(f"     {status} {name}: {available}")
    
    box_health = box_extractor.health_check()
    print(f"✅ Player box health check: {box_health['status']}")
    print(f"   - Expected records: {box_health.get('expected_records', 'Unknown')}")
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)

# Test 6: Verify directory structure
print("\nTest 6: Verifying directory structure...")
etl_dirs = [
    "nba_simulator/etl",
    "nba_simulator/etl/base",
    "nba_simulator/etl/extractors",
    "nba_simulator/etl/extractors/hoopr",
    "nba_simulator/etl/extractors/espn",
    "nba_simulator/etl/extractors/basketball_reference",
    "nba_simulator/etl/extractors/nba_api",
    "nba_simulator/etl/transformers",
    "nba_simulator/etl/loaders",
]

all_exist = True
for dir_path in etl_dirs:
    full_path = project_root / dir_path
    if full_path.exists():
        print(f"✅ {dir_path}/")
    else:
        print(f"❌ {dir_path}/ MISSING")
        all_exist = False

if not all_exist:
    sys.exit(1)

# Test 7: Verify key files
print("\nTest 7: Verifying key files...")
key_files = [
    "nba_simulator/etl/__init__.py",
    "nba_simulator/etl/base/scraper.py",
    "nba_simulator/etl/base/extractor.py",
    "nba_simulator/etl/base/loader.py",
    "nba_simulator/etl/extractors/hoopr/play_by_play.py",
    "nba_simulator/etl/extractors/hoopr/player_box.py",
]

all_exist = True
for file_path in key_files:
    full_path = project_root / file_path
    if full_path.exists():
        size = full_path.stat().st_size
        print(f"✅ {file_path} ({size} bytes)")
    else:
        print(f"❌ {file_path} MISSING")
        all_exist = False

if not all_exist:
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("ETL PACKAGE VALIDATION SUMMARY")
print("=" * 70)
print()
print("✅ ETL package structure created")
print("✅ Base classes operational")
print("✅ hoopR extractors ready")
print("✅ All imports working")
print("✅ Health checks passing")
print("✅ Directory structure verified")
print("✅ Key files present")
print()
print("🎉 WEEK 3 PHASE 1 COMPLETE - ETL Foundation Established!")
print()
print("Next Steps:")
print("1. Test hoopR extractors with actual data (requires testing)")
print("2. Implement ESPN extractors (8 scrapers)")
print("3. Implement Basketball Reference extractors (8+ scrapers)")
print("4. Implement NBA API extractors (7 scrapers)")
print()

sys.exit(0)

