#!/usr/bin/env python3
"""
Week 2 Backward Compatibility Tester

Verifies that existing scripts still work after Phase 1 refactoring.
Tests that no existing code was broken by the new package structure.
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

project_root = Path(__file__).parent.parent.parent

print("=" * 70)
print("WEEK 2: BACKWARD COMPATIBILITY VALIDATION")
print("=" * 70)
print()


def test_dims_cli() -> Tuple[bool, str]:
    """Test DIMS monitoring is still operational"""
    print("Testing DIMS CLI...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/monitoring/dims_cli.py", "verify"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ DIMS CLI operational")
            return True, "DIMS CLI working"
        else:
            print(f"⚠️  DIMS CLI returned non-zero: {result.returncode}")
            return False, f"Exit code: {result.returncode}, stderr: {result.stderr[:200]}"
    
    except subprocess.TimeoutExpired:
        print("⚠️  DIMS CLI timed out")
        return False, "Timeout after 30 seconds"
    except Exception as e:
        print(f"❌ DIMS CLI error: {e}")
        return False, str(e)


def test_autonomous_cli() -> Tuple[bool, str]:
    """Test ADCE CLI is still operational"""
    print("Testing ADCE CLI...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/autonomous/autonomous_cli.py", "status"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ ADCE CLI operational")
            # Parse output to document ADCE status (Critical Question #3)
            return True, result.stdout
        else:
            print(f"⚠️  ADCE CLI returned non-zero: {result.returncode}")
            return False, f"Exit code: {result.returncode}"
    
    except subprocess.TimeoutExpired:
        print("⚠️  ADCE CLI timed out")
        return False, "Timeout after 30 seconds"
    except Exception as e:
        print(f"❌ ADCE CLI error: {e}")
        return False, str(e)


def test_phase1_health_check() -> Tuple[bool, str]:
    """Test Phase 1 health check script"""
    print("Testing Phase 1 health check...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/validation/phase1_health_check.py"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Phase 1 health check passed")
            return True, "All checks passed"
        else:
            print(f"⚠️  Phase 1 health check failed")
            return False, result.stdout + result.stderr
    
    except subprocess.TimeoutExpired:
        print("⚠️  Health check timed out")
        return False, "Timeout after 30 seconds"
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False, str(e)


def test_old_imports() -> Tuple[bool, str]:
    """Test that old import patterns still work"""
    print("Testing old import patterns...")
    
    import_tests = []
    
    # Test 1: Old psycopg2 patterns (if they exist)
    try:
        import psycopg2
        import_tests.append(("psycopg2", True, ""))
        print("  ✅ psycopg2 import works")
    except ImportError as e:
        import_tests.append(("psycopg2", False, str(e)))
        print(f"  ⚠️  psycopg2 import: {e}")
    
    # Test 2: AWS boto3
    try:
        import boto3
        import_tests.append(("boto3", True, ""))
        print("  ✅ boto3 import works")
    except ImportError as e:
        import_tests.append(("boto3", False, str(e)))
        print(f"  ⚠️  boto3 import: {e}")
    
    # Test 3: Common packages
    for package in ['pandas', 'numpy', 'pytest']:
        try:
            __import__(package)
            import_tests.append((package, True, ""))
            print(f"  ✅ {package} import works")
        except ImportError as e:
            import_tests.append((package, False, str(e)))
            print(f"  ⚠️  {package} import: {e}")
    
    failures = [t for t in import_tests if not t[1]]
    
    if not failures:
        print("✅ All old import patterns work")
        return True, "All imports successful"
    else:
        return False, f"{len(failures)} import(s) failed: {failures}"


def test_new_package_imports() -> Tuple[bool, str]:
    """Test that new package imports work"""
    print("Testing new package imports...")
    
    try:
        from nba_simulator import config, database, utils
        print("  ✅ nba_simulator base imports work")
        
        from nba_simulator.config import ConfigLoader
        print("  ✅ nba_simulator.config imports work")
        
        from nba_simulator.database import DatabaseConnection
        print("  ✅ nba_simulator.database imports work")
        
        from nba_simulator.utils import logger
        print("  ✅ nba_simulator.utils imports work")
        
        print("✅ All new package imports work")
        return True, "All new imports successful"
    
    except ImportError as e:
        print(f"❌ New package import failed: {e}")
        return False, str(e)


def check_running_processes() -> Dict[str, List[str]]:
    """Check for running NBA-related processes (Critical Question #2)"""
    print("\n" + "=" * 70)
    print("CRITICAL QUESTION #2: Which Phase 8 scripts are running?")
    print("=" * 70)
    
    findings = {
        'phase8_processes': [],
        'nba_processes': [],
        'python_processes': []
    }
    
    try:
        # Get all NBA-related Python processes
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'python' in line.lower() and 'nba' in line.lower():
                    findings['nba_processes'].append(line.strip())
                    
                    # Check specifically for Phase 8
                    if 'phase' in line.lower() and '8' in line:
                        findings['phase8_processes'].append(line.strip())
            
            if findings['phase8_processes']:
                print(f"\n✅ Found {len(findings['phase8_processes'])} Phase 8 process(es):")
                for proc in findings['phase8_processes']:
                    print(f"  • {proc[:100]}...")
            else:
                print("\n✅ No Phase 8 processes currently running")
            
            if findings['nba_processes']:
                print(f"\n✅ Found {len(findings['nba_processes'])} NBA-related process(es) total")
    
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        findings['error'] = str(e)
    
    return findings


def main():
    """Main validation workflow"""
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'week': 2,
        'phase': '1_validation',
        'compatibility_tests': {},
        'critical_questions': {},
        'summary': {
            'all_passed': False,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0
        }
    }
    
    print("Running backward compatibility tests...")
    print("-" * 70)
    print()
    
    # Test suite
    tests = [
        ('old_imports', test_old_imports),
        ('new_package_imports', test_new_package_imports),
        ('dims_cli', test_dims_cli),
        ('autonomous_cli', test_autonomous_cli),
        ('phase1_health_check', test_phase1_health_check),
    ]
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        print("-" * 70)
        
        try:
            passed, message = test_func()
            results['compatibility_tests'][test_name] = {
                'passed': passed,
                'message': message
            }
            
            results['summary']['tests_run'] += 1
            if passed:
                results['summary']['tests_passed'] += 1
            else:
                results['summary']['tests_failed'] += 1
        
        except Exception as e:
            print(f"❌ Test {test_name} raised exception: {e}")
            results['compatibility_tests'][test_name] = {
                'passed': False,
                'message': f"Exception: {e}"
            }
            results['summary']['tests_run'] += 1
            results['summary']['tests_failed'] += 1
        
        print()
    
    # Check running processes (Critical Question #2)
    results['critical_questions']['phase8_processes'] = check_running_processes()
    
    # Summary
    print("\n" + "=" * 70)
    print("COMPATIBILITY VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"\nTests run: {results['summary']['tests_run']}")
    print(f"Tests passed: {results['summary']['tests_passed']}")
    print(f"Tests failed: {results['summary']['tests_failed']}")
    print()
    
    if results['summary']['tests_failed'] == 0:
        print("✅ ALL COMPATIBILITY TESTS PASSED")
        results['summary']['all_passed'] = True
    else:
        print(f"❌ {results['summary']['tests_failed']} TEST(S) FAILED")
        print("\nFailed tests:")
        for test_name, test_result in results['compatibility_tests'].items():
            if not test_result['passed']:
                print(f"  • {test_name}: {test_result['message'][:100]}")
    
    # Save results
    output_dir = project_root / "backups"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"week2_compat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print(f"📁 Results saved to: {output_file}")
    print()
    
    # Exit code
    sys.exit(0 if results['summary']['all_passed'] else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

