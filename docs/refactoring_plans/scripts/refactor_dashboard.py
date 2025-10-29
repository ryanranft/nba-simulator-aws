#!/usr/bin/env python3
"""
Production Refactoring Monitoring Dashboard

Real-time monitoring of system health during refactoring.
Alerts if any production metrics degrade.

Usage:
    python scripts/monitoring/refactor_dashboard.py

Or run continuously:
    python scripts/monitoring/refactor_dashboard.py --continuous --interval 300
"""

import time
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from nba_simulator.database import DatabaseConnection

    PACKAGE_AVAILABLE = True
except ImportError:
    PACKAGE_AVAILABLE = False
    print("⚠️  nba_simulator package not yet available - using legacy mode")

# Production baseline metrics (from MCP discovery)
BASELINE_METRICS = {
    "games": 44828,
    "play_by_play_espn": 6781155,
    "play_by_play_hoopr": 13074829,
    "box_score_players": 408833,
    "box_score_teams": 15900,
}


class ProductionMonitor:
    """Monitor production system health during refactoring"""

    def __init__(self):
        self.checks_run = 0
        self.failures = []
        self.last_check = None

    def run_all_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        self.checks_run += 1
        self.last_check = datetime.now()

        results = {
            "timestamp": self.last_check.isoformat(),
            "check_number": self.checks_run,
            "checks": {},
            "overall_status": "unknown",
            "degraded_checks": [],
        }

        # Run each check
        checks = [
            ("database_connection", self.check_db_connection),
            ("games_count", self.check_games_count),
            ("espn_pbp_count", self.check_espn_pbp),
            ("hoopr_pbp_count", self.check_hoopr_pbp),
            ("box_score_players", self.check_box_score_players),
            ("box_score_teams", self.check_box_score_teams),
            ("recent_data_activity", self.check_recent_activity),
            ("dims_monitoring", self.check_dims_status),
        ]

        for check_name, check_func in checks:
            try:
                check_result = check_func()
                results["checks"][check_name] = check_result

                if check_result["status"] != "ok":
                    results["degraded_checks"].append(check_name)

            except Exception as e:
                results["checks"][check_name] = {"status": "error", "error": str(e)}
                results["degraded_checks"].append(check_name)

        # Overall status
        if len(results["degraded_checks"]) == 0:
            results["overall_status"] = "healthy"
        elif len(results["degraded_checks"]) <= 2:
            results["overall_status"] = "warning"
        else:
            results["overall_status"] = "critical"

        return results

    def check_db_connection(self) -> Dict[str, Any]:
        """Test database connectivity"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            DatabaseConnection.initialize_pool(min_conn=1, max_conn=2)
            result = DatabaseConnection.execute_query("SELECT 1 as test")

            return {
                "status": "ok",
                "message": "Database connection active",
                "test_query": "passed",
            }
        except Exception as e:
            return {"status": "error", "message": f"Database connection failed: {e}"}

    def check_games_count(self) -> Dict[str, Any]:
        """Verify games table record count"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            result = DatabaseConnection.execute_query(
                "SELECT COUNT(*) as cnt FROM games"
            )
            actual = result[0]["cnt"]
            expected = BASELINE_METRICS["games"]

            if actual < expected:
                return {
                    "status": "critical",
                    "expected": expected,
                    "actual": actual,
                    "message": f"⚠️  DATA LOSS: Games count decreased by {expected - actual}",
                }
            elif actual > expected:
                return {
                    "status": "ok",
                    "expected": expected,
                    "actual": actual,
                    "message": f"Games count increased by {actual - expected} (normal if ingesting new data)",
                }
            else:
                return {
                    "status": "ok",
                    "expected": expected,
                    "actual": actual,
                    "message": "Games count unchanged",
                }
        except Exception as e:
            return {"status": "error", "message": f"Failed to check games count: {e}"}

    def check_espn_pbp(self) -> Dict[str, Any]:
        """Verify ESPN play-by-play count"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            result = DatabaseConnection.execute_query(
                "SELECT COUNT(*) as cnt FROM play_by_play"
            )
            actual = result[0]["cnt"]
            expected = BASELINE_METRICS["play_by_play_espn"]

            if actual < expected:
                return {
                    "status": "critical",
                    "expected": expected,
                    "actual": actual,
                    "message": f"⚠️  DATA LOSS: ESPN PBP decreased by {expected - actual}",
                }
            else:
                return {
                    "status": "ok",
                    "expected": expected,
                    "actual": actual,
                    "delta": actual - expected,
                }
        except Exception as e:
            return {"status": "error", "message": f"Failed to check ESPN PBP: {e}"}

    def check_hoopr_pbp(self) -> Dict[str, Any]:
        """Verify hoopR play-by-play count"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            result = DatabaseConnection.execute_query(
                "SELECT COUNT(*) as cnt FROM hoopr_play_by_play"
            )
            actual = result[0]["cnt"]
            expected = BASELINE_METRICS["play_by_play_hoopr"]

            if actual < expected:
                return {
                    "status": "critical",
                    "expected": expected,
                    "actual": actual,
                    "message": f"⚠️  DATA LOSS: hoopR PBP decreased by {expected - actual}",
                }
            else:
                return {
                    "status": "ok",
                    "expected": expected,
                    "actual": actual,
                    "delta": actual - expected,
                }
        except Exception as e:
            return {"status": "error", "message": f"Failed to check hoopR PBP: {e}"}

    def check_box_score_players(self) -> Dict[str, Any]:
        """Verify box score players count"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            result = DatabaseConnection.execute_query(
                "SELECT COUNT(*) as cnt FROM box_score_players"
            )
            actual = result[0]["cnt"]
            expected = BASELINE_METRICS["box_score_players"]

            if actual < expected:
                return {
                    "status": "warning",
                    "expected": expected,
                    "actual": actual,
                    "message": f"Box score players decreased by {expected - actual}",
                }
            else:
                return {"status": "ok", "actual": actual, "expected": expected}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_box_score_teams(self) -> Dict[str, Any]:
        """Verify box score teams count"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            result = DatabaseConnection.execute_query(
                "SELECT COUNT(*) as cnt FROM box_score_teams"
            )
            actual = result[0]["cnt"]
            expected = BASELINE_METRICS["box_score_teams"]

            if actual < expected:
                return {"status": "warning", "expected": expected, "actual": actual}
            else:
                return {"status": "ok", "actual": actual, "expected": expected}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_recent_activity(self) -> Dict[str, Any]:
        """Check for recent database activity"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            # Check if Phase 8 box score generation is active
            result = DatabaseConnection.execute_query(
                """
                SELECT 
                    COUNT(*) as recent_count,
                    MAX(created_at) as last_update
                FROM box_score_snapshots
                WHERE created_at > NOW() - INTERVAL '7 days'
            """
            )

            recent_count = result[0]["recent_count"]
            last_update = result[0]["last_update"]

            return {
                "status": "ok",
                "box_score_snapshots_7d": recent_count,
                "last_update": str(last_update) if last_update else "No recent updates",
                "message": "Phase 8 activity tracked",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_dims_status(self) -> Dict[str, Any]:
        """Check DIMS monitoring status"""
        if not PACKAGE_AVAILABLE:
            return {"status": "skip", "reason": "Package not available yet"}

        try:
            result = DatabaseConnection.execute_query(
                """
                SELECT 
                    MAX(created_at) as last_snapshot,
                    COUNT(*) as total_snapshots
                FROM dims_metrics_snapshots
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """
            )

            last_snapshot = result[0]["last_snapshot"]
            snapshots_24h = result[0]["total_snapshots"]

            if last_snapshot is None:
                return {
                    "status": "warning",
                    "message": "No DIMS snapshots in last 24 hours",
                }

            return {
                "status": "ok",
                "last_snapshot": str(last_snapshot),
                "snapshots_24h": snapshots_24h,
                "message": "DIMS monitoring active",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def print_results(self, results: Dict[str, Any]):
        """Print formatted results to console"""
        print("\n" + "=" * 70)
        print(f"Production System Health Check #{results['check_number']}")
        print(f"Timestamp: {results['timestamp']}")
        print("=" * 70)

        # Overall status with emoji
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️ ",
            "critical": "🚨",
            "unknown": "❓",
        }

        print(
            f"\nOVERALL STATUS: {status_emoji[results['overall_status']]} {results['overall_status'].upper()}"
        )

        if results["degraded_checks"]:
            print(f"\nDegraded Checks: {', '.join(results['degraded_checks'])}")

        print("\nDetailed Check Results:")
        print("-" * 70)

        for check_name, check_result in results["checks"].items():
            status = check_result["status"]

            # Status symbol
            symbol = {
                "ok": "✅",
                "warning": "⚠️ ",
                "critical": "🚨",
                "error": "❌",
                "skip": "⏭️ ",
            }.get(status, "❓")

            print(f"\n{symbol} {check_name}: {status.upper()}")

            # Print details
            for key, value in check_result.items():
                if key != "status":
                    print(f"   {key}: {value}")

        print("\n" + "=" * 70)

        # Critical warnings
        if results["overall_status"] == "critical":
            print("\n🚨 CRITICAL: System health degraded significantly!")
            print("   Consider pausing refactoring and investigating.")
            print(
                "   Run rollback if data loss detected: bash scripts/validation/emergency_rollback.sh"
            )
        elif results["overall_status"] == "warning":
            print("\n⚠️  WARNING: Some checks degraded, monitor closely.")

    def save_results(self, results: Dict[str, Any], log_dir: str = "refactoring_logs"):
        """Save results to JSON log file"""
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        log_file = (
            log_path / f"health_check_{results['timestamp'].replace(':', '-')}.json"
        )

        with open(log_file, "w") as f:
            json.dump(results, f, indent=2)

        # Also maintain a latest.json
        latest_file = log_path / "latest.json"
        with open(latest_file, "w") as f:
            json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Production refactoring health monitor"
    )
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON only")

    args = parser.parse_args()

    monitor = ProductionMonitor()

    if args.continuous:
        print(f"Starting continuous monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop")

        try:
            while True:
                results = monitor.run_all_checks()

                if args.json:
                    print(json.dumps(results, indent=2))
                else:
                    monitor.print_results(results)

                monitor.save_results(results)

                # Exit if critical
                if results["overall_status"] == "critical":
                    print("\n🚨 Exiting due to critical status")
                    sys.exit(1)

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            sys.exit(0)
    else:
        # Single run
        results = monitor.run_all_checks()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            monitor.print_results(results)

        monitor.save_results(results)

        # Exit code based on status
        exit_codes = {"healthy": 0, "warning": 1, "critical": 2, "unknown": 3}
        sys.exit(exit_codes[results["overall_status"]])


if __name__ == "__main__":
    main()
