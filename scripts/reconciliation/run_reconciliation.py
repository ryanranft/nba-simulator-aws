#!/usr/bin/env python3
"""
Reconciliation Pipeline - ADCE Phase 2A MVP
Run complete reconciliation cycle: Scan → Analyze → Detect → Generate

This is the main entry point for the reconciliation engine.
Coordinates all components and generates the task queue.

Usage:
    # Run full pipeline (MVP with sampling)
    python run_reconciliation.py

    # Dry run (no task generation)
    python run_reconciliation.py --dry-run

    # Force full S3 scan (slow)
    python run_reconciliation.py --full-scan

    # Run specific steps only
    python run_reconciliation.py --steps scan,analyze

    # Use cached inventory (skip scan)
    python run_reconciliation.py --use-cache
"""

import argparse
import logging
import subprocess  # nosec B404 - Used for calling internal scripts only, no user input
import sys
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
import psutil  # For memory/performance monitoring

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReconciliationPipeline:
    """
    Orchestrates the full reconciliation pipeline

    Steps:
    1. Scan S3 (or use cache)
    2. Analyze coverage (SHOULD vs HAVE)
    3. Detect gaps (prioritize)
    4. Generate task queue (actionable tasks)
    """

    def __init__(self, config_file="config/reconciliation_config.yaml"):
        """
        Initialize reconciliation pipeline

        Args:
            config_file: Path to reconciliation config
        """
        self.config_file = Path(config_file)

        if not self.config_file.exists():
            logger.warning(f"Config file not found: {config_file}, using defaults")
            self.config = self._default_config()
        else:
            logger.info(f"Loading config from: {config_file}")
            with open(self.config_file, "r") as f:
                self.config = yaml.safe_load(f)

        self.project_root = Path.cwd()
        self.results = {}

    def _default_config(self):
        """Default config if file not found"""
        return {
            "s3": {"bucket": "nba-sim-raw-data-lake", "sample_rate": 0.1},
            "performance": {"full_cycle_max_minutes": 10},
            "dry_run": {"enabled": False, "save_results": True},
            "retry": {"max_attempts": 3, "backoff_seconds": 5},
            "health_checks": {"enabled": True, "fail_fast": False},
        }

    def _run_health_checks(self):
        """
        Run pre-flight health checks before starting pipeline.
        
        Returns:
            tuple: (success: bool, issues: list)
        """
        logger.info("Running pre-flight health checks...")
        issues = []
        
        # Check AWS credentials
        try:
            import boto3
            sts = boto3.client('sts')
            sts.get_caller_identity()
            logger.info("✅ AWS credentials valid")
        except Exception as e:
            issues.append(f"AWS credentials check failed: {e}")
            logger.warning(f"⚠️  AWS credentials: {e}")
        
        # Check S3 bucket access
        try:
            import boto3
            s3 = boto3.client('s3')
            bucket = self.config.get("s3", {}).get("bucket", "nba-sim-raw-data-lake")
            s3.head_bucket(Bucket=bucket)
            logger.info(f"✅ S3 bucket accessible: {bucket}")
        except Exception as e:
            issues.append(f"S3 bucket access failed: {e}")
            logger.error(f"❌ S3 bucket: {e}")
        
        # Check disk space
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            if free_gb < 1.0:
                issues.append(f"Low disk space: {free_gb:.2f} GB free")
                logger.warning(f"⚠️  Low disk space: {free_gb:.2f} GB")
            else:
                logger.info(f"✅ Disk space: {free_gb:.2f} GB free")
        except Exception as e:
            logger.warning(f"⚠️  Could not check disk space: {e}")
        
        # Check cache directory
        cache_dir = Path("inventory/cache")
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created cache directory: {cache_dir}")
        else:
            logger.info(f"✅ Cache directory exists: {cache_dir}")
        
        # Check config file
        if not self.config_file.exists():
            logger.warning(f"⚠️  Config file not found, using defaults")
        else:
            logger.info(f"✅ Config file: {self.config_file}")
        
        success = len(issues) == 0
        if success:
            logger.info("✅ All health checks passed")
        else:
            logger.error(f"❌ {len(issues)} health check(s) failed")
            for issue in issues:
                logger.error(f"   - {issue}")
        
        return success, issues

    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries exhausted
        """
        max_attempts = self.config.get("retry", {}).get("max_attempts", 3)
        backoff = self.config.get("retry", {}).get("backoff_seconds", 5)
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts:
                    logger.error(f"❌ Failed after {max_attempts} attempts: {e}")
                    raise
                
                wait_time = backoff * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"⚠️  Attempt {attempt}/{max_attempts} failed: {e}")
                logger.info(f"   Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def run(self, steps="all", use_cache=False, full_scan=False, dry_run=False):
        """
        Run reconciliation pipeline

        Args:
            steps: Which steps to run ('all' or comma-separated list)
            use_cache: Use cached S3 inventory instead of scanning
            full_scan: Force full S3 scan (disable sampling)
            dry_run: Don't save task queue

        Returns:
            dict: Pipeline results
        """
        logger.info("=" * 80)
        logger.info("RECONCILIATION PIPELINE - ADCE Phase 2A MVP (ENHANCED)")
        logger.info("=" * 80)
        
        # Performance tracking
        start_time = datetime.now()
        start_memory = psutil.Process().memory_info().rss / (1024 ** 2)  # MB
        step_times = {}
        
        # Health checks (if enabled)
        if self.config.get("health_checks", {}).get("enabled", True):
            logger.info("\n[Pre-Flight] Running health checks...")
            health_ok, health_issues = self._run_health_checks()
            
            if not health_ok:
                fail_fast = self.config.get("health_checks", {}).get("fail_fast", False)
                if fail_fast:
                    logger.error("❌ Health checks failed and fail_fast=True. Aborting.")
                    return {
                        "success": False,
                        "error": "Health checks failed",
                        "issues": health_issues
                    }
                else:
                    logger.warning("⚠️  Health checks failed but continuing (fail_fast=False)")
        
        logger.info("")

        # Parse steps
        if steps == "all":
            run_steps = ["scan", "analyze", "detect", "generate"]
        else:
            run_steps = [s.strip() for s in steps.split(",")]

        logger.info(f"Running steps: {', '.join(run_steps)}")

        try:
            # Step 1: Scan S3 (or use cache)
            if "scan" in run_steps:
                step_start = datetime.now()
                if use_cache:
                    logger.info("\n[Step 1/4] Loading cached S3 inventory...")
                    self.results["inventory"] = self._load_cached_inventory()
                else:
                    logger.info("\n[Step 1/4] Scanning S3...")
                    # Wrap S3 scan with retry logic
                    self.results["inventory"] = self._retry_with_backoff(
                        self._scan_s3, full_scan=full_scan
                    )
                step_times["scan"] = (datetime.now() - step_start).total_seconds()
                logger.info(f"   ⏱️  Step 1 completed in {step_times['scan']:.1f}s")
            else:
                logger.info("\n[Step 1/4] Skipped (using existing inventory)")
                self.results["inventory"] = self._load_cached_inventory()

            # Step 2: Analyze coverage
            if "analyze" in run_steps:
                step_start = datetime.now()
                logger.info("\n[Step 2/4] Analyzing coverage...")
                self.results["analysis"] = self._retry_with_backoff(self._analyze_coverage)
                step_times["analyze"] = (datetime.now() - step_start).total_seconds()
                logger.info(f"   ⏱️  Step 2 completed in {step_times['analyze']:.1f}s")
            else:
                logger.info("\n[Step 2/4] Skipped")

            # Step 3: Detect gaps
            if "detect" in run_steps:
                step_start = datetime.now()
                logger.info("\n[Step 3/4] Detecting gaps...")
                self.results["gaps"] = self._retry_with_backoff(self._detect_gaps)
                step_times["detect"] = (datetime.now() - step_start).total_seconds()
                logger.info(f"   ⏱️  Step 3 completed in {step_times['detect']:.1f}s")
            else:
                logger.info("\n[Step 3/4] Skipped")

            # Step 4: Generate task queue
            if "generate" in run_steps:
                step_start = datetime.now()
                logger.info("\n[Step 4/4] Generating task queue...")
                self.results["tasks"] = self._generate_tasks(dry_run=dry_run)
                step_times["generate"] = (datetime.now() - step_start).total_seconds()
                logger.info(f"   ⏱️  Step 4 completed in {step_times['generate']:.1f}s")
            else:
                logger.info("\n[Step 4/4] Skipped")

            # Performance summary
            duration = (datetime.now() - start_time).total_seconds()
            end_memory = psutil.Process().memory_info().rss / (1024 ** 2)  # MB
            memory_delta = end_memory - start_memory
            
            self.results["pipeline_duration_seconds"] = duration
            self.results["completed_at"] = datetime.now().isoformat()
            self.results["success"] = True
            self.results["performance"] = {
                "total_seconds": duration,
                "step_times": step_times,
                "memory_used_mb": memory_delta,
                "peak_memory_mb": end_memory
            }

            logger.info("\n" + "=" * 80)
            logger.info(f"✅ PIPELINE COMPLETE - Duration: {duration:.1f}s")
            logger.info(f"   Memory: {memory_delta:+.1f} MB (peak: {end_memory:.1f} MB)")
            logger.info("=" * 80)

            self._print_summary()
            self._print_performance_summary(step_times)

            return self.results

        except Exception as e:
            logger.error(f"\n❌ PIPELINE FAILED: {e}", exc_info=True)
            self.results["success"] = False
            self.results["error"] = str(e)
            return self.results

    def _print_performance_summary(self, step_times):
        """
        Print detailed performance breakdown.
        
        Args:
            step_times: Dict of step names to duration in seconds
        """
        if not step_times:
            return
        
        print("\n" + "=" * 60)
        print("⏱️  PERFORMANCE BREAKDOWN")
        print("=" * 60)
        
        total_time = sum(step_times.values())
        
        for step, duration in step_times.items():
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            bar_length = int(percentage / 2)  # 50 chars = 100%
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            print(f"{step:12} {bar} {duration:6.1f}s ({percentage:5.1f}%)")
        
        print("=" * 60)
        print(f"{'TOTAL':12} {' ' * 50} {total_time:6.1f}s")
        print("=" * 60)

    def _scan_s3(self, full_scan=False):
        """Run S3 inventory scanner"""
        cmd = [
            sys.executable,
            "scripts/reconciliation/scan_s3_inventory.py",
            "--bucket",
            self.config["s3"]["bucket"],
        ]

        if not full_scan and self.config["s3"].get("sample_rate"):
            cmd.extend(["--sample-rate", str(self.config["s3"]["sample_rate"])])
        else:
            cmd.append("--full")

        result = subprocess.run(
            cmd, capture_output=True, text=True
        )  # nosec B603 - cmd is internally constructed, no user input

        if result.returncode != 0:
            raise Exception(f"S3 scan failed: {result.stderr}")

        logger.info("S3 scan completed successfully")
        return self._load_cached_inventory()

    def _load_cached_inventory(self):
        """Load cached S3 inventory"""
        cache_file = Path("inventory/cache/current_inventory.json")

        if not cache_file.exists():
            raise Exception(
                "No cached inventory found. Run with --no-cache to scan S3."
            )

        # Check cache age
        cache_age_hours = (
            datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        ).total_seconds() / 3600
        cache_ttl = self.config["s3"].get("cache_ttl_hours", 24)

        if cache_age_hours > cache_ttl:
            logger.warning(f"Cache is {cache_age_hours:.1f}h old (TTL: {cache_ttl}h)")
            logger.warning("Consider running without --use-cache for fresh data")
        else:
            logger.info(f"Using cache ({cache_age_hours:.1f}h old, TTL: {cache_ttl}h)")

        with open(cache_file, "r") as f:
            return json.load(f)

    def _analyze_coverage(self):
        """Run coverage analyzer"""
        cmd = [
            sys.executable,
            "scripts/reconciliation/analyze_coverage.py",
            "--expected",
            "inventory/data_inventory.yaml",
            "--inventory",
            "inventory/cache/current_inventory.json",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True
        )  # nosec B603 - cmd is internally constructed

        if result.returncode != 0:
            raise Exception(f"Coverage analysis failed: {result.stderr}")

        logger.info("Coverage analysis completed successfully")

        # Load results
        with open("inventory/cache/coverage_analysis.json", "r") as f:
            return json.load(f)

    def _detect_gaps(self):
        """Run gap detector"""
        cmd = [
            sys.executable,
            "scripts/reconciliation/detect_data_gaps.py",
            "--analysis",
            "inventory/cache/coverage_analysis.json",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True
        )  # nosec B603 - cmd is internally constructed

        if result.returncode != 0:
            raise Exception(f"Gap detection failed: {result.stderr}")

        logger.info("Gap detection completed successfully")

        # Load results
        with open("inventory/cache/detected_gaps.json", "r") as f:
            return json.load(f)

    def _generate_tasks(self, dry_run=False):
        """Run task queue generator"""
        cmd = [
            sys.executable,
            "scripts/reconciliation/generate_task_queue.py",
            "--gaps",
            "inventory/cache/detected_gaps.json",
        ]

        if dry_run:
            cmd.append("--dry-run")

        result = subprocess.run(
            cmd, capture_output=True, text=True
        )  # nosec B603 - cmd is internally constructed

        if result.returncode != 0:
            raise Exception(f"Task generation failed: {result.stderr}")

        logger.info("Task queue generated successfully")

        if not dry_run:
            # Load results
            with open("inventory/gaps.json", "r") as f:
                return json.load(f)
        else:
            logger.info("Dry run mode - task queue not saved")
            return None

    def _print_summary(self):
        """Print pipeline summary"""
        print("\n" + "=" * 80)
        print("📊 RECONCILIATION SUMMARY")
        print("=" * 80)

        # S3 Inventory
        if "inventory" in self.results:
            inv = self.results["inventory"]["metadata"]
            print(f"\n📦 S3 Inventory:")
            print(f"  Scan mode: {inv.get('scan_mode', 'unknown')}")
            print(f"  Objects scanned: {inv.get('total_objects_scanned', 0):,}")
            print(f"  Objects kept: {inv.get('total_objects_kept', 0):,}")
            print(f"  Total size: {inv.get('total_size_bytes', 0) / 1024**3:.2f} GB")

        # Coverage Analysis
        if "analysis" in self.results:
            summary = self.results["analysis"]["summary"]
            print(f"\n📊 Coverage Analysis:")
            print(
                f"  Overall completeness: {summary.get('overall_completeness_pct', 0):.1f}%"
            )
            print(
                f"  Sources complete: {summary.get('sources_complete', 0)}/{summary.get('total_sources', 0)}"
            )
            print(f"  Missing files: {summary.get('total_missing_files', 0):,}")
            print(f"  Stale files: {summary.get('total_stale_files', 0):,}")

        # Gap Detection
        if "gaps" in self.results:
            summary = self.results["gaps"]["summary"]
            print(f"\n🔍 Gap Detection:")
            print(f"  Total gaps: {summary.get('total_gaps', 0)}")
            print(f"  🔴 Critical: {summary['by_priority'].get('critical', 0)}")
            print(f"  🟡 High: {summary['by_priority'].get('high', 0)}")
            print(f"  🟢 Medium: {summary['by_priority'].get('medium', 0)}")
            print(f"  ⚪ Low: {summary['by_priority'].get('low', 0)}")

        # Task Queue
        if "tasks" in self.results and self.results["tasks"]:
            print(f"\n✅ Task Queue:")
            print(f"  Total tasks: {self.results['tasks'].get('total_tasks', 0)}")
            print(
                f"  Estimated time: {self.results['tasks'].get('estimated_total_minutes', 0):.0f} min"
            )
            print(f"  Output: inventory/gaps.json")

        # Duration
        print(
            f"\n⏱️  Pipeline Duration: {self.results.get('pipeline_duration_seconds', 0):.1f}s"
        )
        print("=" * 80)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Run complete reconciliation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with MVP sampling
  python run_reconciliation.py

  # Use cached inventory (fast)
  python run_reconciliation.py --use-cache

  # Force full S3 scan (slow)
  python run_reconciliation.py --full-scan

  # Run specific steps only
  python run_reconciliation.py --steps analyze,detect,generate

  # Dry run (don't save task queue)
  python run_reconciliation.py --dry-run
        """,
    )

    parser.add_argument(
        "--config",
        default="config/reconciliation_config.yaml",
        help="Path to reconciliation config",
    )
    parser.add_argument(
        "--steps",
        default="all",
        help="Steps to run: all, or comma-separated (scan,analyze,detect,generate)",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached S3 inventory instead of scanning",
    )
    parser.add_argument(
        "--full-scan", action="store_true", help="Force full S3 scan (disable sampling)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run pipeline but don't save task queue"
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = ReconciliationPipeline(config_file=args.config)

    # Run pipeline
    results = pipeline.run(
        steps=args.steps,
        use_cache=args.use_cache,
        full_scan=args.full_scan,
        dry_run=args.dry_run,
    )

    # Exit with appropriate code
    if results.get("success"):
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
