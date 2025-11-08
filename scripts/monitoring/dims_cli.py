#!/usr/bin/env python3
"""
DIMS CLI - Data Inventory Management System Command-Line Interface

Usage:
    dims_cli.py verify [--update] [--category CATEGORY] [--metric METRIC]
    dims_cli.py update [--category CATEGORY] [--metric METRIC]
    dims_cli.py generate [--format FORMAT]
    dims_cli.py cache [info|clear|cleanup]
    dims_cli.py history METRIC_PATH [--days DAYS]
    dims_cli.py info
    dims_cli.py snapshot
    dims_cli.py workflow [file-inventory|local-inventory|aws-inventory|gap-analysis|sync-status|all]

Examples:
    # Verify all metrics
    dims_cli.py verify

    # Verify and auto-update metrics with drift
    dims_cli.py verify --update

    # Verify specific metric
    dims_cli.py verify --category s3_storage --metric total_objects

    # Update a specific metric
    dims_cli.py update --category s3_storage --metric total_objects

    # Update all metrics
    dims_cli.py update

    # Generate all outputs
    dims_cli.py generate

    # Generate specific format
    dims_cli.py generate --format markdown

    # View cache info
    dims_cli.py cache info

    # Clear all cache
    dims_cli.py cache clear

    # Cleanup expired cache
    dims_cli.py cache cleanup

    # View metric history
    dims_cli.py history s3_storage.total_objects --days 30

    # Show system info
    dims_cli.py info

    # Create snapshot
    dims_cli.py snapshot

    # Run workflow integrations
    dims_cli.py workflow file-inventory
    dims_cli.py workflow aws-inventory
    dims_cli.py workflow all
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.monitoring.dims.core import DIMSCore
from scripts.monitoring.dims.cache import DIMSCache
from scripts.monitoring.dims.outputs import DIMSOutputManager
from scripts.monitoring.dims.workflow_integration import WorkflowIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cmd_verify(core: DIMSCore, cache: DIMSCache, args) -> int:
    """Verify metrics command."""
    logger.info("Starting metric verification...")

    if args.category and args.metric:
        # Verify single metric
        logger.info(f"Verifying {args.category}.{args.metric}...")
        result = core.verify_metric(args.category, args.metric)

        print("\n" + "=" * 80)
        print(f"METRIC: {result['metric']}")
        print("=" * 80)
        print(f"Documented Value: {result['documented']}")
        print(f"Actual Value:     {result['actual']}")
        print(f"Drift:            {result['drift']}")
        print(
            f"Drift %:          {result['drift_pct']}%"
            if result["drift_pct"] is not None
            else ""
        )
        print(f"Status:           {result['status'].upper()}")
        print(f"Severity:         {result['severity'].upper()}")
        print(f"Message:          {result['message']}")
        print("=" * 80)

        if args.update and result["status"] not in ("ok", "error"):
            logger.info(f"Auto-updating {args.category}.{args.metric}...")
            core.update_metric(
                args.category,
                args.metric,
                result["actual"],
                verification_method="automated",
                verified_by="dims_cli",
            )
            core.save_metrics()
            print(
                f"\n✓ Updated {args.category}.{args.metric}: {result['documented']} → {result['actual']}"
            )

        return 0 if result["status"] in ("ok", "minor") else 1

    else:
        # Verify all metrics
        results = core.verify_all_metrics()

        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Timestamp:       {results['timestamp']}")
        print(f"Total Metrics:   {results['total_metrics']}")
        print(f"Verified:        {results['verified']}")
        print(f"Drift Detected:  {'YES' if results['drift_detected'] else 'NO'}")
        print()
        print("Status Breakdown:")
        print(f"  ✓ OK:          {results['summary']['ok']}")
        print(f"  ⚠ Minor:       {results['summary']['minor']}")
        print(f"  ⚠ Moderate:    {results['summary']['moderate']}")
        print(f"  ⚠ Major:       {results['summary']['major']}")
        print(f"  ✗ Error:       {results['summary']['error']}")
        print(f"  ℹ New:         {results['summary']['new']}")
        print("=" * 80)

        if results["discrepancies"]:
            print("\nDISCREPANCIES:")
            print("-" * 80)

            for disc in results["discrepancies"]:
                print(f"\n{disc['metric']}")
                print(f"  Documented: {disc['documented']}")
                print(f"  Actual:     {disc['actual']}")
                print(f"  Drift:      {disc['drift']}")
                if disc["drift_pct"] is not None:
                    print(f"  Drift %:    {disc['drift_pct']}%")
                print(f"  Status:     {disc['status'].upper()}")
                print(f"  Severity:   {disc['severity'].upper()}")
                print(f"  Message:    {disc['message']}")

                if args.update and disc["status"] not in ("ok", "error", "new"):
                    # Extract category and metric name
                    parts = disc["metric"].split(".")
                    if len(parts) >= 2:
                        category = parts[0]
                        metric = ".".join(parts[1:])

                        logger.info(f"Auto-updating {category}.{metric}...")
                        core.update_metric(
                            category,
                            metric,
                            disc["actual"],
                            verification_method="automated",
                            verified_by="dims_cli",
                        )
                        print(f"    → Updated to {disc['actual']}")

            if args.update:
                core.save_metrics()
                print("\n✓ Metrics saved")

        return 0 if not results["drift_detected"] else 1


def cmd_update(core: DIMSCore, cache: DIMSCache, args) -> int:
    """Update metrics command."""
    if args.category and args.metric:
        # Update single metric
        logger.info(f"Updating {args.category}.{args.metric}...")

        # Calculate new value
        new_value = core.calculate_metric(args.category, args.metric)

        if new_value is None:
            logger.error(f"Failed to calculate {args.category}.{args.metric}")
            return 1

        # Get old value
        old_value = core.get_metric_value(f"{args.category}.{args.metric}")

        # Update metric
        core.update_metric(
            args.category,
            args.metric,
            new_value,
            verification_method="automated",
            verified_by="dims_cli",
        )
        core.save_metrics()

        print(f"\n✓ Updated {args.category}.{args.metric}")
        print(f"  Old value: {old_value}")
        print(f"  New value: {new_value}")

        return 0

    elif args.category:
        # Update all metrics in a specific category
        logger.info(f"Updating all metrics in category: {args.category}...")

        metrics_config = core.config.get("metrics", {})

        if args.category not in metrics_config:
            logger.error(f"Category not found: {args.category}")
            print(f"\n✗ Category '{args.category}' not found in config")
            print(f"  Available categories: {', '.join(metrics_config.keys())}")
            return 1

        updated = 0
        failed = 0

        for metric_name, metric_def in metrics_config[args.category].items():
            if not metric_def.get("enabled", True):
                continue

            logger.info(f"Updating {args.category}.{metric_name}...")

            new_value = core.calculate_metric(args.category, metric_name)

            if new_value is None:
                logger.error(f"Failed to calculate {args.category}.{metric_name}")
                failed += 1
                continue

            core.update_metric(
                args.category,
                metric_name,
                new_value,
                verification_method="automated",
                verified_by="dims_cli",
            )
            updated += 1

        core.save_metrics()

        print(f"\n✓ Update complete for category: {args.category}")
        print(f"  Updated: {updated}")
        print(f"  Failed:  {failed}")

        return 0 if failed == 0 else 1

    else:
        # Update all metrics
        logger.info("Updating all metrics...")

        metrics_config = core.config.get("metrics", {})
        updated = 0
        failed = 0

        for category, metrics in metrics_config.items():
            for metric_name, metric_def in metrics.items():
                if not metric_def.get("enabled", True):
                    continue

                logger.info(f"Updating {category}.{metric_name}...")

                new_value = core.calculate_metric(category, metric_name)

                if new_value is None:
                    logger.error(f"Failed to calculate {category}.{metric_name}")
                    failed += 1
                    continue

                core.update_metric(
                    category,
                    metric_name,
                    new_value,
                    verification_method="automated",
                    verified_by="dims_cli",
                )
                updated += 1

        core.save_metrics()

        print(f"\n✓ Update complete")
        print(f"  Updated: {updated}")
        print(f"  Failed:  {failed}")

        return 0 if failed == 0 else 1


def cmd_generate(core: DIMSCore, output_manager: DIMSOutputManager, args) -> int:
    """Generate outputs command."""
    logger.info("Generating outputs...")

    if args.format:
        # Generate specific format
        if args.format == "markdown":
            success = output_manager.generate_markdown(core.metrics, "master_inventory")
            success &= output_manager.generate_markdown(
                core.metrics, "collection_inventory"
            )
        elif args.format == "json":
            success = output_manager.generate_json(core.metrics)
        else:
            logger.error(f"Unknown format: {args.format}")
            return 1

        if success:
            print(f"\n✓ Generated {args.format} output")
            return 0
        else:
            print(f"\n✗ Failed to generate {args.format} output")
            return 1

    else:
        # Generate all outputs
        results = output_manager.generate_all(core.metrics)

        print("\n" + "=" * 80)
        print("GENERATION RESULTS")
        print("=" * 80)

        for output_type, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {output_type}")

        print("=" * 80)

        # Return 0 if all succeeded
        return 0 if all(results.values()) else 1


def cmd_cache(cache: DIMSCache, args) -> int:
    """Cache management command."""
    if args.operation == "info":
        # Show cache info
        info = cache.get_cache_info()

        print("\n" + "=" * 80)
        print("CACHE INFORMATION")
        print("=" * 80)
        print(f"Enabled:              {info['enabled']}")
        print(f"Backend:              {info.get('backend', 'N/A')}")
        print(f"Entries:              {info.get('entries', 0)}")
        print(f"Default TTL (hours):  {info.get('default_ttl_hours', 'N/A')}")

        ttl_overrides = info.get("ttl_overrides", {})
        if ttl_overrides:
            print("\nTTL Overrides:")
            for metric, ttl in ttl_overrides.items():
                print(f"  {metric}: {ttl}h")

        print("=" * 80)

        return 0

    elif args.operation == "clear":
        # Clear all cache
        logger.info("Clearing all cache...")
        cache.clear_all()
        print("\n✓ Cache cleared")
        return 0

    elif args.operation == "cleanup":
        # Cleanup expired cache
        logger.info("Cleaning up expired cache...")
        count = cache.cleanup()
        print(f"\n✓ Removed {count} expired cache entries")
        return 0

    else:
        logger.error(f"Unknown cache operation: {args.operation}")
        return 1


def cmd_history(core: DIMSCore, args) -> int:
    """View metric history command."""
    logger.info(f"Retrieving history for {args.metric_path}...")

    history = core.get_metric_history(args.metric_path, days=args.days)

    if not history:
        print(f"\nNo history found for {args.metric_path}")
        return 1

    print("\n" + "=" * 80)
    print(f"METRIC HISTORY: {args.metric_path}")
    print("=" * 80)
    print(f"Period: Last {args.days} days")
    print()
    print("Date           Value")
    print("-" * 40)

    for entry in history:
        print(f"{entry['date']}    {entry['value']}")

    print("=" * 80)

    return 0


def cmd_info(core: DIMSCore, cache: DIMSCache) -> int:
    """Show system info command."""
    sys_info = core.get_system_info()
    cache_info = cache.get_cache_info()

    print("\n" + "=" * 80)
    print("DIMS SYSTEM INFORMATION")
    print("=" * 80)
    print(f"Version:                  {sys_info['version']}")
    print(f"System Name:              {sys_info['system_name']}")
    print(f"Project Root:             {sys_info['project_root']}")
    print(f"Config Path:              {sys_info['config_path']}")
    print(f"Metrics Path:             {sys_info['metrics_path']}")
    print()
    print("Features:")
    for feature, enabled in sys_info["features"].items():
        status = "✓" if enabled else "✗"
        print(f"  {status} {feature}")
    print()
    print(f"Cache Enabled:            {cache_info['enabled']}")
    print(f"Cache Backend:            {cache_info.get('backend', 'N/A')}")
    print(f"Cache Entries:            {cache_info.get('entries', 0)}")
    print(f"Verification Enabled:     {sys_info['verification_enabled']}")
    print(f"Total Metrics Defined:    {sys_info['total_metrics_defined']}")
    print(f"Total Metrics Documented: {sys_info['total_metrics_documented']}")
    print("=" * 80)

    return 0


def cmd_snapshot(core: DIMSCore) -> int:
    """Create snapshot command."""
    logger.info("Creating snapshot...")

    success = core.create_snapshot()

    if success:
        print("\n✓ Snapshot created")
        return 0
    else:
        print("\n✗ Failed to create snapshot")
        return 1


def cmd_migrate(core: DIMSCore) -> int:
    """Run database migration command."""
    if not core.database:
        print("\n✗ Database backend not enabled")
        print("Enable it in inventory/config.yaml: features.database_backend: true")
        return 1

    logger.info("Running database migration...")

    from pathlib import Path

    schema_path = core.project_root / "sql" / "dims_schema.sql"

    if not schema_path.exists():
        print(f"\n✗ Schema file not found: {schema_path}")
        return 1

    # Test connection first
    if not core.database.test_connection():
        print("\n✗ Database connection failed")
        print("Check your database credentials in .env")
        return 1

    # Run migration
    success = core.database.run_migration(schema_path)

    if success:
        print("\n✓ Database migration completed successfully")
        return 0
    else:
        print("\n✗ Database migration failed")
        return 1


def cmd_approve(core: DIMSCore, args) -> int:
    """Approval workflow commands."""
    if not core.approval:
        print("\n✗ Approval workflow not enabled")
        print("Enable it in inventory/config.yaml: features.approval_workflow: true")
        return 1

    if args.action == "list":
        # List pending approvals
        pending = core.approval.get_pending_approvals()

        if not pending:
            print("\nNo pending approvals")
            return 0

        print("\n" + "=" * 80)
        print(f"PENDING APPROVALS ({len(pending)})")
        print("=" * 80)

        for approval in pending:
            print(f"\nID: {approval['id']}")
            print(f"Metric: {approval['metric_category']}.{approval['metric_name']}")
            print(f"Old Value: {approval['old_value']}")
            print(f"New Value: {approval['new_value']}")
            print(f"Drift: {approval['drift_pct']}%")
            print(f"Severity: {approval['severity'].upper()}")
            print(f"Requested: {approval['requested_at']}")
            print(f"Pending For: {approval['hours_pending']:.1f} hours")
            print("-" * 80)

        return 0

    elif args.action == "review":
        # Review specific approval
        if not args.id:
            print("\n✗ Approval ID required (use --id)")
            return 1

        approval = core.approval.get_approval(args.id)

        if not approval:
            print(f"\n✗ Approval {args.id} not found")
            return 1

        print("\n" + "=" * 80)
        print(f"APPROVAL REQUEST #{approval['id']}")
        print("=" * 80)
        print(f"Metric: {approval['metric_category']}.{approval['metric_name']}")
        print(f"Old Value: {approval['old_value']}")
        print(f"New Value: {approval['new_value']}")
        print(f"Drift: {approval['drift_pct']}%")
        print(f"Status: {approval['status'].upper()}")
        print(f"Severity: {approval['severity'].upper()}")
        print(f"Requested By: {approval['requested_by']}")
        print(f"Requested At: {approval['requested_at']}")

        if approval["reviewed_by"]:
            print(f"Reviewed By: {approval['reviewed_by']}")
            print(f"Reviewed At: {approval['reviewed_at']}")
            if approval["review_notes"]:
                print(f"Notes: {approval['review_notes']}")

        print("=" * 80)

        return 0

    elif args.action == "accept":
        # Accept approval
        if not args.id:
            print("\n✗ Approval ID required (use --id)")
            return 1

        success = core.approval.approve(
            args.id,
            reviewed_by=args.reviewer or "dims_cli",
            review_notes=args.notes,
            auto_apply=not args.no_auto_apply,
        )

        if success:
            print(f"\n✓ Approval {args.id} accepted")

            if not args.no_auto_apply:
                # Apply the change
                approval = core.approval.get_approval(args.id)
                if approval:
                    core.update_metric(
                        approval["metric_category"],
                        approval["metric_name"],
                        approval["new_value"],
                        verification_method="approved",
                        verified_by=args.reviewer or "dims_cli",
                    )
                    core.save_metrics()
                    print(
                        f"✓ Change applied: {approval['metric_category']}.{approval['metric_name']}"
                    )

            return 0
        else:
            print(f"\n✗ Failed to accept approval {args.id}")
            return 1

    elif args.action == "reject":
        # Reject approval
        if not args.id:
            print("\n✗ Approval ID required (use --id)")
            return 1

        success = core.approval.reject(
            args.id, reviewed_by=args.reviewer or "dims_cli", review_notes=args.notes
        )

        if success:
            print(f"\n✓ Approval {args.id} rejected")
            return 0
        else:
            print(f"\n✗ Failed to reject approval {args.id}")
            return 1

    else:
        print(f"\n✗ Unknown approval action: {args.action}")
        return 1


def cmd_events(core: DIMSCore, args) -> int:
    """Event management commands."""
    if not core.events:
        print("\n✗ Event-driven updates not enabled")
        print("Enable it in inventory/config.yaml: features.event_driven: true")
        return 1

    if args.action == "status":
        # Show event stats
        stats = core.events.get_stats()

        print("\n" + "=" * 80)
        print("EVENT HANDLER STATUS")
        print("=" * 80)
        print(f"Enabled: {stats['enabled']}")
        print(f"Hooks Configured: {stats.get('hooks_configured', 0)}")
        print(f"Cooldown: {stats.get('cooldown_seconds', 0)} seconds")
        print()
        print("Recent Activity (Last 7 days):")
        print(f"  Total Events: {stats.get('total_events', 0)}")
        print(f"  Successful: {stats.get('successful_events', 0)}")
        print(f"  Failed: {stats.get('failed_events', 0)}")
        print("=" * 80)

        return 0

    elif args.action == "test":
        # Test event handler
        if not args.event_type:
            print("\n✗ Event type required (use --event-type)")
            return 1

        result = core.events.test_event(args.event_type)

        print("\n" + "=" * 80)
        print(f"EVENT TEST: {args.event_type}")
        print("=" * 80)

        if result["success"]:
            print(f"✓ Hook configured: {result['hook_name']}")
            print(f"Metric Patterns: {result['metric_patterns']}")
            print(f"Would Trigger: {result['trigger_count']} metrics")
            print()
            print("Metrics:")
            for metric in result["metrics_would_trigger"]:
                print(f"  - {metric}")
        else:
            print(f"✗ Error: {result['error']}")

        print("=" * 80)

        return 0 if result["success"] else 1

    elif args.action == "trigger":
        # Manually trigger event
        if not args.event_type:
            print("\n✗ Event type required (use --event-type)")
            return 1

        result = core.events.handle_event(args.event_type, "manual_trigger")

        print(f"\n✓ Event triggered: {args.event_type}")
        print(f"Metrics triggered: {len(result['metrics_triggered'])}")

        return 0 if result["success"] else 1

    else:
        print(f"\n✗ Unknown events action: {args.action}")
        return 1


def cmd_notebook(core: DIMSCore, args) -> int:
    """
    Launch or export Jupyter notebook.

    Args:
        core: DIMSCore instance
        args: Command arguments

    Returns:
        Exit code (0 for success)
    """
    import subprocess
    import shutil

    notebook_path = Path(core.project_root) / "notebooks" / "dims_explorer.ipynb"

    if not notebook_path.exists():
        print(f"\n✗ Notebook not found: {notebook_path}")
        return 1

    if args.action == "launch":
        # Launch Jupyter notebook
        print("\n🚀 Launching DIMS Explorer Notebook...")
        print(f"Notebook: {notebook_path}")
        print("\nOpening in Jupyter Lab...")
        print("(Press Ctrl+C to stop the server)")
        print("=" * 80)

        try:
            subprocess.run(
                ["jupyter", "lab", str(notebook_path)], cwd=str(core.project_root)
            )
            return 0
        except KeyboardInterrupt:
            print("\n\n✓ Jupyter server stopped")
            return 0
        except FileNotFoundError:
            print("\n✗ Jupyter not installed. Install with:")
            print("  pip install jupyterlab")
            return 1

    elif args.action == "export":
        # Export notebook as HTML
        output_dir = Path(core.project_root) / "inventory" / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"dims_report_{timestamp}.html"

        print(f"\n📊 Exporting notebook to HTML...")
        print(f"Output: {output_path}")

        try:
            result = subprocess.run(
                [
                    "jupyter",
                    "nbconvert",
                    "--to",
                    "html",
                    "--execute",
                    "--output",
                    str(output_path),
                    str(notebook_path),
                ],
                cwd=str(core.project_root),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"\n✓ Notebook exported successfully")
                print(f"  File: {output_path}")
                print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
                return 0
            else:
                print(f"\n✗ Export failed: {result.stderr}")
                return 1

        except FileNotFoundError:
            print("\n✗ Jupyter nbconvert not installed. Install with:")
            print("  pip install jupyter")
            return 1

    else:
        print(f"\n✗ Unknown notebook action: {args.action}")
        return 1


def cmd_workflow(core: DIMSCore, args) -> int:
    """
    Run workflow integration commands.

    Integrates existing data inventory workflows with DIMS.

    Args:
        core: DIMSCore instance
        args: Command arguments

    Returns:
        Exit code (0 for success)
    """
    import json

    integration = WorkflowIntegration(core.project_root)

    print(f"\n🔧 Running workflow: {args.workflow}")
    print("=" * 80)

    try:
        if args.workflow == "file-inventory":
            result = integration.run_file_inventory(update=True)
            print(f"\n✓ File inventory complete")
            print(f"  Total files documented: {result['total_files']}")
            print(f"  Last updated: {result['last_updated']}")
            print(f"\n  Categories:")
            for category, count in result["categories"].items():
                print(f"    - {category}: {count}")

        elif args.workflow == "local-inventory":
            mode = args.mode or "quick"
            result = integration.run_local_data_inventory(mode=mode)
            print(f"\n✓ Local data inventory complete ({mode} mode)")
            print(f"  Archives: {result['archives_size_gb']} GB")
            print(f"  Temp data: {result['temp_size_gb']} GB")
            print(f"  Project: {result['project_size_gb']} GB")
            if mode == "full":
                print(f"  Total files: {result['total_files']}")

        elif args.workflow == "aws-inventory":
            result = integration.run_aws_data_inventory()
            print(f"\n✓ AWS data inventory complete")
            print(f"\n  S3:")
            print(f"    Objects: {result['s3_objects']:,}")
            print(f"    Size: {result['s3_size_gb']:.2f} GB")
            print(f"\n  RDS:")
            print(f"    Database size: {result['rds_size_gb']:.2f} GB")
            print(f"    Allocated storage: {result['rds_allocated_gb']} GB")
            print(f"\n  💰 Estimated cost: ${result['estimated_cost_usd']:.2f}/month")

        elif args.workflow == "gap-analysis":
            result = integration.run_data_gap_analysis()
            print(f"\n✓ Data gap analysis complete")
            print(f"  Total games: {result['total_games']}")
            print(f"  Missing box scores: {result['missing_games']}")
            print(f"  Missing play-by-play: {result['games_without_pbp']}")

            if result["missing_games"] > 0 or result["games_without_pbp"] > 0:
                print(f"\n  ⚠️  Data gaps detected!")
            else:
                print(f"\n  ✅ No data gaps found")

        elif args.workflow == "sync-status":
            result = integration.run_sync_status_check()
            print(f"\n✓ Sync status check complete")
            print(f"  S3 files: {result['s3_files']:,}")
            print(f"  Local files: {result['local_files']:,}")
            print(f"  Drift: {result['drift_pct']:.1f}%")
            print(f"  Status: {result['status'].upper()}")

            if result["status"] == "synced":
                print(f"\n  ✅ Local and S3 are synchronized")
            elif result["status"] in ["minor_drift", "moderate_drift"]:
                print(f"\n  ⚠️  Drift detected - consider running sync")
            elif result["status"] == "major_drift":
                print(f"\n  🔴 MAJOR drift - URGENT sync recommended")

        elif args.workflow == "all":
            print("\n📊 Running all workflow integrations...\n")
            result = integration.run_all_workflows()

            print("\n" + "=" * 80)
            print("WORKFLOW INTEGRATION RESULTS")
            print("=" * 80)
            print(json.dumps(result, indent=2))

        else:
            print(f"\n✗ Unknown workflow: {args.workflow}")
            return 1

        print("\n" + "=" * 80)
        return 0

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DIMS - Data Inventory Management System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify metrics")
    verify_parser.add_argument(
        "--update", action="store_true", help="Auto-update metrics with drift"
    )
    verify_parser.add_argument("--category", help="Metric category to verify")
    verify_parser.add_argument("--metric", help="Metric name to verify")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update metrics")
    update_parser.add_argument("--category", help="Metric category to update")
    update_parser.add_argument("--metric", help="Metric name to update")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate outputs")
    generate_parser.add_argument(
        "--format",
        choices=["markdown", "json", "html", "jupyter"],
        help="Output format",
    )

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_parser.add_argument(
        "operation", choices=["info", "clear", "cleanup"], help="Cache operation"
    )

    # History command
    history_parser = subparsers.add_parser("history", help="View metric history")
    history_parser.add_argument(
        "metric_path", help="Metric path (e.g., s3_storage.total_objects)"
    )
    history_parser.add_argument(
        "--days", type=int, default=30, help="Number of days to look back"
    )

    # Info command
    subparsers.add_parser("info", help="Show system information")

    # Snapshot command
    subparsers.add_parser("snapshot", help="Create snapshot of current metrics")

    # Migrate command (Phase 2)
    subparsers.add_parser("migrate", help="Run database schema migration")

    # Approve command (Phase 2)
    approve_parser = subparsers.add_parser(
        "approve", help="Approval workflow management"
    )
    approve_parser.add_argument(
        "action", choices=["list", "review", "accept", "reject"], help="Approval action"
    )
    approve_parser.add_argument("--id", type=int, help="Approval request ID")
    approve_parser.add_argument("--reviewer", help="Reviewer name")
    approve_parser.add_argument("--notes", help="Review notes")
    approve_parser.add_argument(
        "--no-auto-apply", action="store_true", help="Don't auto-apply approved changes"
    )

    # Events command (Phase 2)
    events_parser = subparsers.add_parser("events", help="Event handler management")
    events_parser.add_argument(
        "action", choices=["status", "test", "trigger"], help="Event action"
    )
    events_parser.add_argument(
        "--event-type", help="Event type (git_post_commit, s3_upload, etc.)"
    )

    # Notebook command (Phase 3)
    notebook_parser = subparsers.add_parser(
        "notebook", help="Interactive Jupyter notebook"
    )
    notebook_parser.add_argument(
        "action",
        nargs="?",
        default="launch",
        choices=["launch", "export"],
        help="Notebook action",
    )

    # Workflow command (Phase 3 Integration)
    workflow_parser = subparsers.add_parser(
        "workflow", help="Run workflow integrations"
    )
    workflow_parser.add_argument(
        "workflow",
        choices=[
            "file-inventory",
            "local-inventory",
            "aws-inventory",
            "gap-analysis",
            "sync-status",
            "all",
        ],
        help="Workflow to run",
    )
    workflow_parser.add_argument(
        "--mode", choices=["quick", "full"], help="Mode for local inventory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize DIMS
    try:
        core = DIMSCore()
        cache = DIMSCache(core.config, core.project_root)
        output_manager = DIMSOutputManager(core.config, core.project_root)
    except Exception as e:
        logger.error(f"Failed to initialize DIMS: {e}")
        return 1

    # Execute command
    try:
        if args.command == "verify":
            return cmd_verify(core, cache, args)
        elif args.command == "update":
            return cmd_update(core, cache, args)
        elif args.command == "generate":
            return cmd_generate(core, output_manager, args)
        elif args.command == "cache":
            return cmd_cache(cache, args)
        elif args.command == "history":
            return cmd_history(core, args)
        elif args.command == "info":
            return cmd_info(core, cache)
        elif args.command == "snapshot":
            return cmd_snapshot(core)
        elif args.command == "migrate":
            return cmd_migrate(core)
        elif args.command == "approve":
            return cmd_approve(core, args)
        elif args.command == "events":
            return cmd_events(core, args)
        elif args.command == "notebook":
            return cmd_notebook(core, args)
        elif args.command == "workflow":
            return cmd_workflow(core, args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Command failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
