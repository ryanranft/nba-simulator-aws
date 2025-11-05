#!/usr/bin/env python3
"""
Test Phase 2 Transformer Imports and Basic Functionality

Validates that all ETL transformers are properly implemented:
- BaseTransformer abstract class
- ESPNTransformer (play-by-play and box scores)
- BasketballReferenceTransformer (13-tier system)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all transformers can be imported"""
    print("🔍 Testing Phase 2 Transformer Imports...")
    print("=" * 60)
    
    try:
        from nba_simulator.etl.transformers import (
            BaseTransformer,
            ESPNTransformer,
            ESPNPlayByPlayTransformer,
            ESPNBoxScoreTransformer,
            BasketballReferenceTransformer
        )
        
        print("✅ BaseTransformer imported successfully")
        print("✅ ESPNTransformer imported successfully")
        print("✅ ESPNPlayByPlayTransformer imported successfully")
        print("✅ ESPNBoxScoreTransformer imported successfully")
        print("✅ BasketballReferenceTransformer imported successfully")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_instantiation():
    """Test that transformers can be instantiated"""
    print("🔍 Testing Transformer Instantiation...")
    print("=" * 60)
    
    try:
        from nba_simulator.etl.transformers import (
            ESPNTransformer,
            BasketballReferenceTransformer
        )
        
        # Test ESPN transformer
        espn = ESPNTransformer()
        print(f"✅ ESPNTransformer instantiated: {espn.__class__.__name__}")
        print(f"   Source: {espn.source_name}")
        
        # Test BBRef transformer
        bbref = BasketballReferenceTransformer()
        print(f"✅ BasketballReferenceTransformer instantiated: {bbref.__class__.__name__}")
        print(f"   Source: {bbref.source_name}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        return False


def test_basic_functionality():
    """Test basic transformer functionality"""
    print("🔍 Testing Basic Transformer Functionality...")
    print("=" * 60)
    
    try:
        from nba_simulator.etl.transformers import ESPNTransformer
        
        # Create transformer
        transformer = ESPNTransformer()
        
        # Test with sample ESPN play-by-play data
        sample_data = {
            'header': {
                'id': '401234567',
                'competitions': [
                    {
                        'id': '401234567',
                        'date': '2024-11-04T00:00:00Z'
                    }
                ]
            },
            'plays': [
                {
                    'clock': {'displayValue': '11:45'},
                    'period': {'number': 1},
                    'team': {'id': '1'},
                    'text': 'LeBron James makes 3-pt jump shot',
                    'scoreValue': 3
                }
            ]
        }
        
        # Test validation
        is_valid, error_msg = transformer.validate_input(sample_data)
        if is_valid:
            print("✅ ESPN data validation passed")
        else:
            print(f"❌ ESPN data validation failed: {error_msg}")
            return False
        
        # Test transformation
        transformed, metrics = transformer.transform(sample_data)
        print(f"✅ Transformation completed:")
        print(f"   Input records: {metrics.records_input}")
        print(f"   Output records: {metrics.records_output}")
        print(f"   Status: {metrics.status.value}")
        print(f"   Duration: {metrics.duration_seconds:.3f}s")
        
        if transformed:
            print(f"✅ Sample transformed event:")
            event = transformed[0]
            print(f"   Game ID: {event.get('game_id')}")
            print(f"   Event type: {event.get('event_type')}")
            print(f"   Quarter: {event.get('quarter')}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bbref_functionality():
    """Test Basketball Reference transformer functionality"""
    print("🔍 Testing Basketball Reference Transformer...")
    print("=" * 60)
    
    try:
        from nba_simulator.etl.transformers import BasketballReferenceTransformer
        
        # Create transformer
        transformer = BasketballReferenceTransformer(tier=1)
        
        # Test with sample schedule data (Tier 1)
        sample_data = {
            'tier': 1,
            'games': [
                {
                    'game_id': 'BOS202411040LAL',
                    'date': '2024-11-04',
                    'season': 2025,
                    'home_team': 'LAL',
                    'away_team': 'BOS',
                    'home_score': 110,
                    'away_score': 108
                }
            ]
        }
        
        # Test validation
        is_valid, error_msg = transformer.validate_input(sample_data)
        if is_valid:
            print("✅ BBRef data validation passed")
        else:
            print(f"❌ BBRef data validation failed: {error_msg}")
            return False
        
        # Test transformation
        transformed, metrics = transformer.transform(sample_data)
        print(f"✅ Transformation completed:")
        print(f"   Input records: {metrics.records_input}")
        print(f"   Output records: {metrics.records_output}")
        print(f"   Status: {metrics.status.value}")
        
        if transformed:
            print(f"✅ Sample transformed game:")
            game = transformed[0]
            print(f"   Game ID: {game.get('game_id')}")
            print(f"   Home: {game.get('home_team')} ({game.get('home_score')})")
            print(f"   Away: {game.get('away_team')} ({game.get('away_score')})")
            print(f"   Tier: {game.get('bbref_tier')}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ BBRef functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PHASE 2 TRANSFORMER VALIDATION")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Instantiation", test_instantiation),
        ("ESPN Functionality", test_basic_functionality),
        ("BBRef Functionality", test_bbref_functionality)
    ]
    
    results = {}
    for test_name, test_fn in tests:
        results[test_name] = test_fn()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Phase 2 Transformers Complete!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
