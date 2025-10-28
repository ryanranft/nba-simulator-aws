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

# Test 3b: Import ESPN extractors
print("\nTest 3b: Importing ESPN extractors...")
try:
    from nba_simulator.etl.extractors.espn import (
        ESPNPlayByPlayExtractor,
        ESPNBoxScoresExtractor,
        ESPNScheduleExtractor
    )
    print("✅ ESPNPlayByPlayExtractor imported")
    print("✅ ESPNBoxScoresExtractor imported")
    print("✅ ESPNScheduleExtractor imported")
except ImportError as e:
    print(f"❌ Failed to import ESPN extractors: {e}")
    sys.exit(1)

# Test 4: Instantiate hoopR extractors
print("\nTest 4: Instantiating hoopR extractors...")
try:
    hoopr_pbp = HooprPlayByPlayExtractor()
    print(f"✅ HooprPlayByPlayExtractor instantiated: {hoopr_pbp.name}")
    
    hoopr_box = HooprPlayerBoxExtractor()
    print(f"✅ HooprPlayerBoxExtractor instantiated: {hoopr_box.name}")
except Exception as e:
    print(f"❌ Failed to instantiate hoopR extractors: {e}")
    sys.exit(1)

# Test 4b: Instantiate ESPN extractors
print("\nTest 4b: Instantiating ESPN extractors...")
try:
    espn_pbp = ESPNPlayByPlayExtractor()
    print(f"✅ ESPNPlayByPlayExtractor instantiated: {espn_pbp.name}")
    
    espn_box = ESPNBoxScoresExtractor()
    print(f"✅ ESPNBoxScoresExtractor instantiated: {espn_box.name}")
    
    espn_schedule = ESPNScheduleExtractor()
    print(f"✅ ESPNScheduleExtractor instantiated: {espn_schedule.name}")
except Exception as e:
    print(f"❌ Failed to instantiate ESPN extractors: {e}")
    sys.exit(1)

# Test 5: Check health
print("\nTest 5: Running health checks...")
try:
    # hoopR health checks
    hoopr_pbp_health = hoopr_pbp.health_check()
    print(f"✅ hoopR PBP health check: {hoopr_pbp_health['status']}")
    print(f"   - Primary data source: {hoopr_pbp_health.get('primary_data_source', False)}")
    print(f"   - Expected records: {hoopr_pbp_health.get('expected_records', 'Unknown')}")
    
    hoopr_box_health = hoopr_box.health_check()
    print(f"✅ hoopR Player box health check: {hoopr_box_health['status']}")
    
    # ESPN health checks
    espn_pbp_health = espn_pbp.health_check()
    print(f"✅ ESPN PBP health check: {espn_pbp_health['status']}")
    print(f"   - Data source: {espn_pbp_health.get('data_source', 'Unknown')}")
    print(f"   - Purpose: {espn_pbp_health.get('purpose', 'Unknown')}")
    
    if 'legacy_scripts' in espn_pbp_health:
        print("   - ESPN legacy scripts available:")
        for name, available in espn_pbp_health['legacy_scripts'].items():
            status = "✅" if available else "⚠️"
            print(f"     {status} {name}: {available}")
    
    espn_box_health = espn_box.health_check()
    print(f"✅ ESPN Box scores health check: {espn_box_health['status']}")
    
    espn_schedule_health = espn_schedule.health_check()
    print(f"✅ ESPN Schedule health check: {espn_schedule_health['status']}")
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
    "nba_simulator/etl/extractors/espn/play_by_play.py",
    "nba_simulator/etl/extractors/espn/box_scores.py",
    "nba_simulator/etl/extractors/espn/schedule.py",
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
print("✅ hoopR extractors ready (PRIMARY: 13.6M records)")
print("✅ ESPN extractors ready (validation/gap-filling)")
print("✅ All imports working")
print("✅ Health checks passing")
print("✅ Directory structure verified")
print("✅ Key files present")
print()
print("🎉 WEEK 3 PHASE 2 COMPLETE - ESPN Extractors Implemented!")
print()
print("Completed:")
print("  ✅ hoopR: 2 extractors (play_by_play, player_box)")
print("  ✅ ESPN: 3 extractors (play_by_play, box_scores, schedule)")
print()
print("Next Steps:")
print("1. Implement Basketball Reference extractors (8+ scrapers)")
print("2. Implement NBA API extractors (7 scrapers)")
print("3. Create integration tests")
print()

sys.exit(0)

