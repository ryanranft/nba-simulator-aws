#!/usr/bin/env python3
"""
Validation Error Analysis Script

Analyzes the 48 MB validation report JSON to extract:
- Error patterns by schema and source
- Frequency distribution
- Root causes
- Sample files for each error type

Generated: 2025-10-24
Purpose: Deep dive into validation failures to guide adapter fixes
"""

import json
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
from pathlib import Path


class ValidationErrorAnalyzer:
    """Analyzes validation report to extract error patterns."""

    def __init__(self, report_path: str):
        self.report_path = report_path
        self.report = None
        self.error_patterns = defaultdict(list)
        self.error_counts = Counter()
        self.sample_files = defaultdict(list)

    def load_report(self):
        """Load validation report JSON."""
        print(f"Loading validation report: {self.report_path}")
        print(
            f"File size: {Path(self.report_path).stat().st_size / 1024 / 1024:.1f} MB"
        )

        with open(self.report_path, "r") as f:
            self.report = json.load(f)

        total_files = len(self.report.get("detailed_results", []))
        print(f"Loaded report with {total_files:,} validation results\n")

    def analyze_errors(self):
        """Extract and categorize all errors from validation results."""
        print("Analyzing error patterns...")
        print("=" * 80)

        results = self.report.get("detailed_results", [])

        for idx, result in enumerate(results):
            if idx % 10000 == 0:
                print(
                    f"  Progress: {idx:,}/{len(results):,} ({idx/len(results)*100:.1f}%)"
                )

            file_path = result.get("key", "unknown")
            source = result.get("source", "unknown")
            success = result.get("success", False)

            # Analyze each schema validation
            schemas = result.get("schemas_validated", {})

            for schema_name, schema_result in schemas.items():
                if not schema_result.get("valid", False):
                    error = schema_result.get("error", "No error message")
                    error_key = self._extract_error_pattern(error)
                    full_key = f"{schema_name}:{source}:{error_key}"

                    self.error_counts[full_key] += 1
                    self.error_patterns[full_key].append(
                        {
                            "file": file_path,
                            "error": error,
                            "quality_score": schema_result.get("quality_score", 0.0),
                        }
                    )

                    # Keep sample files (max 5 per error type)
                    if len(self.sample_files[full_key]) < 5:
                        self.sample_files[full_key].append(file_path)

        print(f"\nAnalysis complete!")
        print(f"  Total error patterns: {len(self.error_counts)}")
        print(f"  Total failed validations: {sum(self.error_counts.values()):,}\n")

    def _extract_error_pattern(self, error) -> str:
        """Extract error pattern from error message."""
        if isinstance(error, str):
            # Truncate to first 60 chars and normalize
            error_str = error[:60]
            # Remove file paths and numbers to group similar errors
            error_str = error_str.replace("\\", "/").split("/")[-1]
            return error_str
        elif isinstance(error, dict):
            error_type = error.get("type", "unknown")
            error_msg = error.get("message", "")[:40]
            return f"{error_type}:{error_msg}"
        else:
            return str(type(error))

    def print_summary(self):
        """Print error analysis summary."""
        print("\n" + "=" * 80)
        print("ERROR ANALYSIS SUMMARY")
        print("=" * 80)

        # Group by schema
        schema_errors = defaultdict(lambda: defaultdict(int))
        for error_key, count in self.error_counts.items():
            parts = error_key.split(":", 2)
            if len(parts) >= 2:
                schema = parts[0]
                source = parts[1]
                schema_errors[schema][source] += count

        print("\n📊 Errors by Schema:")
        for schema in sorted(schema_errors.keys()):
            sources = schema_errors[schema]
            total = sum(sources.values())
            print(f"\n  {schema}: {total:,} failures")
            for source, count in sorted(sources.items(), key=lambda x: -x[1]):
                print(f"    - {source}: {count:,} ({count/total*100:.1f}%)")

        print("\n\n🔝 Top 20 Error Patterns:")
        print("-" * 80)
        for i, (error_key, count) in enumerate(self.error_counts.most_common(20), 1):
            parts = error_key.split(":", 2)
            schema = parts[0] if len(parts) > 0 else "unknown"
            source = parts[1] if len(parts) > 1 else "unknown"
            pattern = parts[2] if len(parts) > 2 else error_key

            print(f"\n{i}. [{schema}] {source}")
            print(f"   Count: {count:,}")
            print(f"   Pattern: {pattern}")
            print(f"   Sample files:")
            for sample in self.sample_files[error_key][:3]:
                print(f"     • {sample}")

        print("\n" + "=" * 80)

    def export_analysis(self, output_path: str):
        """Export detailed analysis to JSON."""
        analysis = {
            "timestamp": self.report.get("summary", {}).get("end_time", "unknown"),
            "total_files": len(self.report.get("detailed_results", [])),
            "total_error_patterns": len(self.error_counts),
            "error_patterns": [],
        }

        for error_key, count in self.error_counts.most_common():
            parts = error_key.split(":", 2)
            analysis["error_patterns"].append(
                {
                    "schema": parts[0] if len(parts) > 0 else "unknown",
                    "source": parts[1] if len(parts) > 1 else "unknown",
                    "pattern": parts[2] if len(parts) > 2 else error_key,
                    "count": count,
                    "sample_files": self.sample_files[error_key],
                }
            )

        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"\nDetailed analysis exported to: {output_path}")
        print(f"File size: {Path(output_path).stat().st_size / 1024:.1f} KB")


def main():
    """Run error analysis."""
    print("\n" + "=" * 80)
    print("VALIDATION ERROR ANALYSIS")
    print("=" * 80 + "\n")

    # Find most recent validation report
    report_pattern = "validation_report_20251023_235030.json"

    if not Path(report_pattern).exists():
        print(f"❌ Report not found: {report_pattern}")
        return 1

    # Initialize analyzer
    analyzer = ValidationErrorAnalyzer(report_pattern)

    # Load report
    analyzer.load_report()

    # Analyze errors
    analyzer.analyze_errors()

    # Print summary
    analyzer.print_summary()

    # Export detailed analysis
    output_path = "validation_error_analysis.json"
    analyzer.export_analysis(output_path)

    print("\n✅ Error analysis complete!")
    print("\nNext steps:")
    print("  1. Review top error patterns above")
    print("  2. Download sample files for each pattern")
    print("  3. Examine actual JSON structure vs adapter expectations")
    print("  4. Design adapter fixes based on findings")

    return 0


if __name__ == "__main__":
    sys.exit(main())
