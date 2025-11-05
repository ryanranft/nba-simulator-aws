#!/usr/bin/env python3
"""
3-Source Validation Workflow - Command Line Interface

CLI runner for cross-validating ESPN, hoopR, and NBA API data sources.

Usage:
    python validation_cli.py
    python validation_cli.py --days 7
    python validation_cli.py --dry-run

Author: NBA Simulator AWS Team
Version: 2.0.0
Created: [Date TBD]
"""

import sys
import argparse
import yaml
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import workflow class dynamically
import importlib.util

workflow_path = (
    PROJECT_ROOT
    / "docs"
    / "phases"
    / "phase_0"
    / "0.0024_validation_workflow"
    / "validation_workflow.py"
)
spec = importlib.util.spec_from_file_location("validation_workflow", workflow_path)
workflow_module = importlib.util.module_from_spec(spec)
sys.modules["validation_workflow"] = workflow_module
spec.loader.exec_module(workflow_module)

ValidationWorkflow = workflow_module.ValidationWorkflow


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="3-Source Validation Workflow")

    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0024_validation_workflow"
        / "config"
        / "default_config.yaml",
        help="Path to configuration file",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days back to scrape (overrides config)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without executing",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    print("=" * 80)
    print("3-Source Validation Workflow")
    print("Version: 2.0.0")
    print("=" * 80)
    print()

    # Load configuration
    config = load_config(args.config)

    # Override days if specified
    if args.days is not None:
        config.setdefault("scraping", {})["days_back"] = args.days

    # Create workflow
    workflow = ValidationWorkflow(config=config)

    # Set verbose logging
    if args.verbose:
        import logging

        workflow.logger.setLevel(logging.DEBUG)

    # Initialize
    print("Initializing workflow...")
    if not workflow.initialize():
        print("❌ Workflow initialization failed")
        return 1

    print("✅ Workflow initialized")
    print()

    # Dry run
    if args.dry_run:
        print("🔍 DRY RUN MODE - No execution")
        print()
        print("Tasks to execute:")
        for task in workflow.tasks:
            print(f"  - {task.task_name}")

        workflow.shutdown()
        print()
        print("✅ Dry run complete")
        return 0

    # Execute workflow
    print("Executing workflow...")
    print()

    success = workflow.execute()

    # Generate report
    print()
    print("=" * 80)
    print("WORKFLOW REPORT")
    print("=" * 80)
    print()

    report = workflow.generate_report(format="markdown")
    print(report)

    # Shutdown
    workflow.shutdown()

    # Final status
    print()
    if success:
        print("✅ Workflow completed successfully!")
        if workflow.failed_sources:
            print(
                f"⚠️  Warning: {len(workflow.failed_sources)} sources failed: {', '.join(workflow.failed_sources)}"
            )
        return 0
    else:
        print("❌ Workflow failed - check logs for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
