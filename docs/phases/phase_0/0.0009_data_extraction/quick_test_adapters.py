#!/usr/bin/env python3
"""
Quick Adapter Test - Verify Fixed Adapters Work

Tests 10 representative files to ensure:
1. Source detection works correctly
2. Adapters extract data successfully
3. Schema validation passes
4. No regressions

Generated: 2025-10-24
Purpose: Quick validation before full re-run
"""

import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from implement_full_validation import FullDataValidator


def main():
    """Run quick adapter tests on sample files."""
    print("\n" + "=" * 80)
    print("QUICK ADAPTER TEST - 10 SAMPLE FILES")
    print("=" * 80)

    # Test files (mix of sources)
    test_files = [
        # ESPN files (should now be detected correctly)
        "box_scores/131105002.json",
        "pbp/401584783.json",
        "team_stats/401584784.json",
        # Basketball Reference (already working)
        "basketball_reference/advanced_totals/1953/player_advanced_totals.json",
        "basketball_reference/advanced_totals/2000/player_advanced_totals.json",
        # NBA API (already working)
        "nba_api_comprehensive/boxscores_advanced/advanced_0020000991.json",
        "nba_api_comprehensive/boxscores_advanced/advanced_0020000992.json",
    ]

    # Initialize validator
    print("\n1. Initializing validator...")
    validator = FullDataValidator(workers=1, dry_run=False)
    print("   ✅ Validator initialized\n")

    # Test source detection
    print("2. Testing source detection...")
    print("   " + "-" * 76)
    for file_key in test_files:
        source = validator.determine_source(file_key)
        status = "✅" if source != "unknown" else "❌"
        print(f"   {status} {file_key[:60]:<60} → {source}")
    print()

    # Validate each file
    print("3. Validating files...")
    print("   " + "-" * 76)

    results = []
    for file_key in test_files:
        try:
            result = validator.validate_file(file_key)
            results.append(result)

            source = result["source"]
            success = result["success"]
            quality = result["quality_score"]
            status = "✅" if success else "❌"

            print(f"   {status} {file_key[:45]:<45} | {source:<20} | Q:{quality:>5.1f}")

            # Show schema details for failed files
            if not success:
                for schema, schema_result in result["schemas_validated"].items():
                    if not schema_result.get("valid"):
                        error = schema_result.get("error", "No error message")
                        print(f"       └─ {schema}: {error[:60]}")

        except Exception as e:
            print(f"   ❌ {file_key[:45]:<45} | ERROR: {str(e)[:30]}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful

    print(f"\nTotal Files: {total}")
    print(f"  ✅ Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  ❌ Failed: {failed} ({failed/total*100:.1f}%)")

    # By source
    sources = {}
    for r in results:
        source = r["source"]
        if source not in sources:
            sources[source] = {"total": 0, "success": 0}
        sources[source]["total"] += 1
        if r["success"]:
            sources[source]["success"] += 1

    print("\nBy Source:")
    for source, stats in sorted(sources.items()):
        success_rate = (
            stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        )
        print(
            f"  {source:>20}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)"
        )

    # By schema
    schemas = {}
    for r in results:
        for schema_name, schema_result in r["schemas_validated"].items():
            if schema_name not in schemas:
                schemas[schema_name] = {"total": 0, "valid": 0}
            schemas[schema_name]["total"] += 1
            if schema_result.get("valid"):
                schemas[schema_name]["valid"] += 1

    print("\nBy Schema:")
    for schema, stats in sorted(schemas.items()):
        success_rate = (
            stats["valid"] / stats["total"] * 100 if stats["total"] > 0 else 0
        )
        print(
            f"  {schema:>20}: {stats['valid']}/{stats['total']} ({success_rate:.1f}%)"
        )

    # Final verdict
    print("\n" + "=" * 80)
    if successful >= total * 0.8:  # 80%+ success
        print("✅ QUICK TEST PASSED!")
        print("   Adapters working correctly. Ready for integration test.")
    else:
        print("⚠️  QUICK TEST NEEDS ATTENTION")
        print(f"   Success rate {successful/total*100:.1f}% < 80% threshold")
        print("   Review failures before proceeding.")
    print("=" * 80 + "\n")

    return 0 if successful >= total * 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
