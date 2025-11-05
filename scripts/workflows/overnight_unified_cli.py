#!/usr/bin/env python3
"""
Overnight Unified Workflow - Command Line Interface

CLI runner for the overnight unified workflow that collects data from multiple
sources, rebuilds unified database, detects discrepancies, and exports ML datasets.

Usage:
    python overnight_unified_cli.py                    # Run with default config
    python overnight_unified_cli.py --config custom.yaml
    python overnight_unified_cli.py --dry-run
    python overnight_unified_cli.py --resume
    python overnight_unified_cli.py --status
    python overnight_unified_cli.py --validate-config

Examples:
    # Run workflow
    python overnight_unified_cli.py

    # Dry run (validate only, no execution)
    python overnight_unified_cli.py --dry-run

    # Resume from saved state
    python overnight_unified_cli.py --resume

    # Check workflow status
    python overnight_unified_cli.py --status

    # Validate configuration file
    python overnight_unified_cli.py --validate-config --config my_config.yaml

Author: NBA Simulator AWS Team
Version: 2.0.0
Created: [Date TBD]
"""

import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import workflow class
import importlib.util
import sys

# Load workflow module dynamically (handles directory names with dots)
workflow_path = (
    PROJECT_ROOT
    / "docs"
    / "phases"
    / "phase_0"
    / "0.0023_overnight_unified"
    / "overnight_unified_workflow.py"
)
spec = importlib.util.spec_from_file_location(
    "overnight_unified_workflow", workflow_path
)
workflow_module = importlib.util.module_from_spec(spec)
sys.modules["overnight_unified_workflow"] = workflow_module
spec.loader.exec_module(workflow_module)

OvernightUnifiedWorkflow = workflow_module.OvernightUnifiedWorkflow


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        try:
            config = yaml.safe_load(f)
            return config or {}
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML configuration: {e}")
            sys.exit(1)


def validate_config_command(config_path: Path) -> int:
    """
    Validate configuration file.

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print(f"Validating configuration: {config_path}")

    config = load_config(config_path)

    # Create workflow (initializes and validates)
    workflow = OvernightUnifiedWorkflow(config=config)

    if workflow.initialize():
        print("✅ Configuration is valid!")
        print()
        print("Workflow Info:")
        info = workflow.get_workflow_info()
        for key, value in info.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"  {key}: {value}")

        workflow.shutdown()
        return 0
    else:
        print("❌ Configuration validation failed")
        print("   Check logs for details")
        return 1


def status_command() -> int:
    """
    Check workflow status.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    state_file = PROJECT_ROOT / ".workflow_state" / "overnight_unified_state.json"

    if not state_file.exists():
        print("No saved workflow state found")
        print("Workflow has not been run or state was cleared")
        return 1

    import json

    with open(state_file) as f:
        state = json.load(f)

    print(f"Workflow Status: {state.get('state', 'UNKNOWN')}")
    print(f"Last Run: {state.get('last_run', 'N/A')}")
    print(
        f"Tasks Completed: {state.get('tasks_completed', 0)}/{state.get('total_tasks', 0)}"
    )

    if state.get("state") == "FAILED":
        print(f"Failure Reason: {state.get('error', 'Unknown')}")
        print()
        print("To resume from last successful task:")
        print("  python overnight_unified_cli.py --resume")

    return 0


def run_workflow(
    config_path: Path,
    dry_run: bool = False,
    resume: bool = False,
    verbose: bool = False,
) -> int:
    """
    Run the overnight unified workflow.

    Args:
        config_path: Path to configuration file
        dry_run: If True, validate only (no execution)
        resume: If True, resume from saved state
        verbose: If True, enable verbose logging

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 80)
    print("Overnight Multi-Source Unified Workflow")
    print("Version: 2.0.0")
    print("=" * 80)
    print()

    # Load configuration
    config = load_config(config_path)

    # Create workflow
    workflow = OvernightUnifiedWorkflow(config=config)

    # Set verbose logging
    if verbose:
        import logging

        workflow.logger.setLevel(logging.DEBUG)

    # Initialize
    print("Initializing workflow...")
    if not workflow.initialize():
        print("❌ Workflow initialization failed")
        return 1

    print("✅ Workflow initialized")
    print()

    # Dry run - stop here
    if dry_run:
        print("🔍 DRY RUN MODE - No execution")
        print()
        print("Tasks to execute:")
        for task in workflow.tasks:
            deps = (
                f" (depends on: {', '.join(task.dependencies)})"
                if task.dependencies
                else ""
            )
            critical = " [CRITICAL]" if task.is_critical else ""
            print(f"  - {task.task_name}{deps}{critical}")

        workflow.shutdown()
        print()
        print("✅ Dry run complete - configuration is valid")
        return 0

    # Resume from saved state
    if resume:
        state_file = PROJECT_ROOT / ".workflow_state" / "overnight_unified_state.json"
        if state_file.exists():
            print("📂 Resuming from saved state...")
            workflow.load_state(str(state_file))
        else:
            print("⚠️  No saved state found, starting fresh run")

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

    # Save report to file
    report_file = (
        PROJECT_ROOT
        / "reports"
        / f"overnight_workflow_report_{workflow.start_time.strftime('%Y%m%d_%H%M%S')}.md"
    )
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w") as f:
        f.write(report)

    print()
    print(f"📄 Full report saved to: {report_file}")

    # Shutdown
    workflow.shutdown()

    # Final status
    print()
    if success:
        print("✅ Workflow completed successfully!")
        return 0
    else:
        print("❌ Workflow failed - check logs for details")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Overnight Multi-Source Unified Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python overnight_unified_cli.py

  # Run with custom configuration
  python overnight_unified_cli.py --config my_config.yaml

  # Dry run (validate only)
  python overnight_unified_cli.py --dry-run

  # Resume from saved state
  python overnight_unified_cli.py --resume

  # Check workflow status
  python overnight_unified_cli.py --status

  # Validate configuration
  python overnight_unified_cli.py --validate-config
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "phases"
        / "phase_0"
        / "0.0023_overnight_unified"
        / "config"
        / "default_config.yaml",
        help="Path to configuration file (default: config/default_config.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and show tasks without executing",
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume from saved workflow state"
    )

    parser.add_argument(
        "--status", action="store_true", help="Show workflow status and exit"
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration file and exit",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Handle commands
    if args.status:
        return status_command()

    if args.validate_config:
        return validate_config_command(args.config)

    # Run workflow
    return run_workflow(
        config_path=args.config,
        dry_run=args.dry_run,
        resume=args.resume,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
