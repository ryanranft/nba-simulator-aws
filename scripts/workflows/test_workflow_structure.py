#!/usr/bin/env python3
"""
Workflow Structure Validator

Tests the structure and basic functionality of migrated workflows
without requiring full BaseWorkflow infrastructure.

This is a lightweight validation script that checks:
- Files exist and are readable
- Configuration files are valid YAML
- Workflow classes have required methods
- Documentation is complete

Usage:
    python scripts/workflows/test_workflow_structure.py
"""

import sys
import yaml
import ast
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_file_exists(file_path: Path, description: str) -> bool:
    """Test if a file exists"""
    if file_path.exists():
        print(f"  ✅ {description}: {file_path.name}")
        return True
    else:
        print(f"  ❌ {description} NOT FOUND: {file_path}")
        return False


def test_yaml_valid(yaml_path: Path) -> bool:
    """Test if YAML file is valid"""
    try:
        with open(yaml_path) as f:
            yaml.safe_load(f)
        print(f"  ✅ Valid YAML: {yaml_path.name}")
        return True
    except Exception as e:
        print(f"  ❌ Invalid YAML: {yaml_path.name} - {e}")
        return False


def test_python_syntax(py_path: Path) -> bool:
    """Test if Python file has valid syntax"""
    try:
        with open(py_path) as f:
            ast.parse(f.read())
        print(f"  ✅ Valid Python syntax: {py_path.name}")
        return True
    except SyntaxError as e:
        print(f"  ❌ Syntax error in {py_path.name}: {e}")
        return False


def test_class_has_methods(
    py_path: Path, class_name: str, required_methods: List[str]
) -> bool:
    """Test if a class has required methods"""
    try:
        with open(py_path) as f:
            tree = ast.parse(f.read())

        # Find the class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # Get method names
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]

                missing_methods = [m for m in required_methods if m not in methods]

                if not missing_methods:
                    print(f"  ✅ Class {class_name} has all required methods")
                    return True
                else:
                    print(
                        f"  ❌ Class {class_name} missing methods: {', '.join(missing_methods)}"
                    )
                    return False

        print(f"  ❌ Class {class_name} not found in {py_path.name}")
        return False

    except Exception as e:
        print(f"  ❌ Error checking {class_name}: {e}")
        return False


def test_workflow(
    workflow_dir: Path, workflow_name: str, class_name: str
) -> Dict[str, bool]:
    """Test a complete workflow"""
    print(f"\n{'=' * 80}")
    print(f"Testing Workflow: {workflow_name}")
    print(f"{'=' * 80}\n")

    results = {}

    # Test file structure
    print("📁 File Structure:")
    results["readme"] = test_file_exists(workflow_dir / "README.md", "README.md")
    results["workflow_py"] = test_file_exists(
        workflow_dir / f"{workflow_name}_workflow.py", "Workflow Python file"
    )
    results["config"] = test_file_exists(
        workflow_dir / "config" / "default_config.yaml", "Config file"
    )

    # Test YAML validity
    print("\n📄 Configuration:")
    if results["config"]:
        results["yaml_valid"] = test_yaml_valid(
            workflow_dir / "config" / "default_config.yaml"
        )

    # Test Python syntax
    print("\n🐍 Python Syntax:")
    workflow_py = workflow_dir / f"{workflow_name}_workflow.py"
    if results["workflow_py"]:
        results["python_syntax"] = test_python_syntax(workflow_py)

    # Test class structure
    print("\n🏗️  Class Structure:")
    if results.get("python_syntax"):
        required_methods = [
            "__init__",
            "_validate_config",
            "_build_tasks",
            "_execute_task",
            "get_workflow_info",
        ]
        results["class_methods"] = test_class_has_methods(
            workflow_py, class_name, required_methods
        )

    # Summary
    print(f"\n📊 Summary:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"  Passed: {passed}/{total} checks")

    return results


def main():
    """Main test runner"""
    print(f"\n{'#' * 80}")
    print(f"# Workflow Structure Validation")
    print(f"# Project: {PROJECT_ROOT}")
    print(f"{'#' * 80}\n")

    all_results = {}

    # Test Workflow 1: Overnight Unified (0.0023)
    all_results["overnight_unified"] = test_workflow(
        workflow_dir=PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0023_overnight_unified",
        workflow_name="overnight_unified",
        class_name="OvernightUnifiedWorkflow",
    )

    # Test Workflow 2: Validation (0.0024)
    all_results["validation"] = test_workflow(
        workflow_dir=PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0024_validation_workflow",
        workflow_name="validation",
        class_name="ValidationWorkflow",
    )

    # Test Workflow 3: Daily Update (0.0025)
    all_results["daily_update"] = test_workflow(
        workflow_dir=PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0025_daily_update",
        workflow_name="daily_update",
        class_name="DailyUpdateWorkflow",
    )

    # Final summary
    print(f"\n{'=' * 80}")
    print(f"FINAL RESULTS")
    print(f"{'=' * 80}\n")

    for workflow_name, results in all_results.items():
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        status = (
            "✅ PASS" if passed == total else "⚠️  PARTIAL" if passed > 0 else "❌ FAIL"
        )
        print(f"  {status} {workflow_name}: {passed}/{total} checks passed")

    # Overall result
    all_passed = all(all(r.values()) for r in all_results.values())

    if all_passed:
        print(f"\n✅ All workflows passed structure validation!")
        return 0
    else:
        print(f"\n⚠️  Some workflows have issues - see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
