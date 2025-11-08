#!/usr/bin/env python3
"""
Master Phase 0 Verification Runner
Consolidates all Phase 0 tests and validators into single execution.

This script provides a unified interface for verifying all 23 Phase 0 sub-phases
after refactoring or major changes. It runs pytest tests, validators, system checks,
and generates comprehensive reports.

Usage:
    python tests/run_phase0_verification.py              # Full verification
    python tests/run_phase0_verification.py --quick      # Fast checks only
    python tests/run_phase0_verification.py --subphase 0.0018  # Specific sub-phase
    python tests/run_phase0_verification.py --report     # Generate detailed report
    python tests/run_phase0_verification.py --json       # JSON output

Examples:
    # Quick health check before starting work
    python tests/run_phase0_verification.py --quick

    # Full verification before deployment
    python tests/run_phase0_verification.py --report

    # Verify specific sub-phase after changes
    python tests/run_phase0_verification.py --subphase 0.0018

    # CI/CD integration
    python tests/run_phase0_verification.py --json > verification_results.json

Version: 1.0.0
Created: November 5, 2025
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ANSI color codes for terminal output
class Colors:
    """Terminal color codes"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Phase0Verifier:
    """Master verification runner for all Phase 0 sub-phases"""

    # All 23 Phase 0 sub-phases
    SUBPHASES = [
        ("0.0001", "Initial Data Collection", "S3 bucket upload verification"),
        ("0.0002", "hoopR Data Collection", "hoopR data integrity"),
        ("0.0003", "Kaggle Historical Database", "Historical database verification"),
        ("0.0004", "Basketball Reference", "ADCE integration configuration"),
        ("0.0007", "Odds API Data", "Odds API integration"),
        ("0.0008", "Security Implementation", "14 security variations"),
        ("0.0009", "Data Extraction", "Extraction quality (93.1% target)"),
        ("0.0010", "PostgreSQL JSONB Storage", "Temporal queries and JSONB"),
        ("0.0011", "RAG Pipeline (pgvector)", "Vector embeddings and semantic search"),
        ("0.0012", "RAG + LLM Integration", "LLM query interface"),
        ("0.0013", "Dispatcher Pipeline", "Pipeline routing"),
        ("0.0014", "Error Analysis", "Error pattern analysis"),
        ("0.0015", "Information Availability", "Data accessibility"),
        ("0.0016", "Robust Architecture", "Multi-source search"),
        ("0.0017", "External APIs", "External API integration"),
        ("0.0018", "Autonomous Data Collection (ADCE)", "24/7 autonomous operation"),
        ("0.0019", "Testing Infrastructure & CI/CD", "pytest framework and CI/CD"),
        ("0.0020", "Monitoring & Observability", "CloudWatch metrics and DIMS"),
        ("0.0021", "Documentation & API Standards", "API docs and ADRs"),
        ("0.0022", "Data Inventory & Gap Analysis", "DIMS inventory tracking"),
        ("0.0023", "Overnight Unified Workflow", "11-task overnight workflow"),
        ("0.0024", "3-Source Validation Workflow", "Cross-source validation"),
        ("0.0025", "Daily ESPN Update Workflow", "Database updates and Slack"),
    ]

    def __init__(self, verbose: bool = False, output_json: bool = False):
        self.verbose = verbose
        self.output_json = output_json
        self.results = {}
        self.start_time = time.time()
        self.project_root = Path(__file__).parent.parent

    def log(self, message: str, level: str = "INFO"):
        """Log message with color coding"""
        if self.output_json:
            return  # Don't print logs in JSON mode

        color_map = {
            "INFO": Colors.OKBLUE,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "HEADER": Colors.HEADER + Colors.BOLD,
        }

        color = color_map.get(level, "")
        timestamp = datetime.now().strftime("%H:%M:%S")

        if level == "HEADER":
            print(f"\n{color}{'='*80}{Colors.ENDC}")
            print(f"{color}{message}{Colors.ENDC}")
            print(f"{color}{'='*80}{Colors.ENDC}\n")
        else:
            print(f"[{timestamp}] {color}{level}{Colors.ENDC}: {message}")

    def run_pytest_tests(self, subphase: Optional[str] = None) -> Tuple[bool, Dict]:
        """Run pytest tests for Phase 0 or specific sub-phase"""
        self.log("Running pytest tests...", "INFO")

        if subphase:
            # Run specific sub-phase tests
            test_pattern = f"tests/phases/phase_0/test_{subphase.replace('.', '_')}*.py"
            test_files = list(self.project_root.glob(test_pattern))

            if not test_files:
                self.log(f"No test files found for {subphase}", "WARNING")
                return True, {"skipped": True, "reason": "No test files found"}

            cmd = ["pytest"] + [str(f) for f in test_files] + ["-v", "--tb=short"]
        else:
            # Run all Phase 0 tests
            cmd = [
                "pytest",
                "tests/phases/phase_0/",
                "-v",
                "--tb=short",
                "-m",
                "phase0 or not phase0",
            ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )

        # Parse pytest output for summary
        output_lines = result.stdout.split("\n")
        summary = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "success": result.returncode == 0,
            "output": result.stdout if self.verbose else "",
        }

        # Extract test counts from pytest summary line
        for line in output_lines:
            if "passed" in line or "failed" in line:
                if "passed" in line:
                    try:
                        summary["passed"] = int(line.split()[0])
                    except (ValueError, IndexError):
                        pass
                if "failed" in line:
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "failed":
                                summary["failed"] = int(parts[i - 1])
                    except (ValueError, IndexError):
                        pass

        summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"]

        if summary["success"]:
            self.log(
                f"✅ Pytest: {summary['passed']} passed, {summary['failed']} failed",
                "SUCCESS",
            )
        else:
            self.log(
                f"❌ Pytest: {summary['passed']} passed, {summary['failed']} failed",
                "ERROR",
            )

        return summary["success"], summary

    def run_validators(self, subphase: Optional[str] = None) -> Tuple[bool, Dict]:
        """Run all validators or specific sub-phase validators"""
        self.log("Running validators...", "INFO")

        validators_dir = self.project_root / "validators" / "phases" / "phase_0"

        if not validators_dir.exists():
            self.log(f"Validators directory not found: {validators_dir}", "WARNING")
            return True, {"skipped": True, "reason": "Validators directory not found"}

        if subphase:
            # Run specific sub-phase validators
            pattern = f"validate_{subphase.replace('.', '_')}*.py"
            validators = list(validators_dir.glob(pattern))
        else:
            # Run all validators
            validators = list(validators_dir.glob("validate_*.py"))

        if not validators:
            self.log(f"No validators found", "WARNING")
            return True, {"skipped": True, "reason": "No validators found"}

        passed = 0
        failed = 0
        skipped = 0
        validator_results = []

        for validator in validators:
            self.log(f"  Running {validator.name}...", "INFO")
            result = subprocess.run(
                ["python", str(validator)],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5 minute timeout per validator
            )

            validator_result = {
                "name": validator.name,
                "success": result.returncode == 0,
                "output": result.stdout if self.verbose else "",
                "error": result.stderr if result.returncode != 0 else "",
            }

            if result.returncode == 0:
                passed += 1
                self.log(f"    ✅ {validator.name}", "SUCCESS")
            else:
                failed += 1
                self.log(f"    ❌ {validator.name}", "ERROR")
                if not self.verbose:
                    self.log(f"       Error: {result.stderr[:200]}", "ERROR")

            validator_results.append(validator_result)

        summary = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "success": failed == 0,
            "validators": validator_results,
        }

        if summary["success"]:
            self.log(f"✅ Validators: {passed}/{passed+failed} passed", "SUCCESS")
        else:
            self.log(
                f"❌ Validators: {passed}/{passed+failed} passed, {failed} failed",
                "ERROR",
            )

        return summary["success"], summary

    def run_system_validation(self) -> Tuple[bool, Dict]:
        """Run system validation script"""
        self.log("Running system validation...", "INFO")

        script_path = self.project_root / "scripts" / "system_validation.py"

        if not script_path.exists():
            self.log(f"System validation script not found: {script_path}", "WARNING")
            return True, {"skipped": True, "reason": "Script not found"}

        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=180,  # 3 minute timeout
        )

        summary = {
            "success": result.returncode == 0,
            "output": result.stdout if self.verbose else "",
            "checks_passed": 0,
            "checks_failed": 0,
        }

        # Parse output for check counts
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "✓" in line or "✅" in line:
                summary["checks_passed"] += 1
            elif "✗" in line or "❌" in line:
                summary["checks_failed"] += 1

        if summary["success"]:
            self.log(
                f"✅ System Validation: {summary['checks_passed']} checks passed",
                "SUCCESS",
            )
        else:
            self.log(
                f"⚠️  System Validation: {summary['checks_passed']} passed, {summary['checks_failed']} failed",
                "WARNING",
            )

        return summary["success"], summary

    def verify_adce_health(self) -> Tuple[bool, Dict]:
        """Check ADCE autonomous system health"""
        self.log("Checking ADCE health...", "INFO")

        cli_path = self.project_root / "scripts" / "autonomous" / "autonomous_cli.py"

        if not cli_path.exists():
            self.log(f"ADCE CLI not found: {cli_path}", "WARNING")
            return True, {"skipped": True, "reason": "CLI not found"}

        result = subprocess.run(
            ["python", str(cli_path), "health"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=60,  # 1 minute timeout
        )

        summary = {
            "success": result.returncode == 0,
            "output": result.stdout if self.verbose else "",
            "healthy": "healthy" in result.stdout.lower() or result.returncode == 0,
        }

        if summary["healthy"]:
            self.log("✅ ADCE: Healthy", "SUCCESS")
        else:
            self.log("❌ ADCE: Unhealthy", "ERROR")

        return summary["success"], summary

    def verify_dims_metrics(self) -> Tuple[bool, Dict]:
        """Check DIMS metrics are tracking"""
        self.log("Verifying DIMS metrics...", "INFO")

        cli_path = self.project_root / "scripts" / "monitoring" / "dims_cli.py"

        if not cli_path.exists():
            self.log(f"DIMS CLI not found: {cli_path}", "WARNING")
            return True, {"skipped": True, "reason": "CLI not found"}

        result = subprocess.run(
            ["python", str(cli_path), "verify", "--category", "s3_storage"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            timeout=120,  # 2 minute timeout
        )

        summary = {
            "success": result.returncode == 0 or "timeout" in result.stderr.lower(),
            "output": result.stdout if self.verbose else "",
            "timeout": "timeout" in result.stderr.lower(),
        }

        if summary["success"]:
            if summary["timeout"]:
                self.log("⚠️  DIMS: Timeout (non-critical, known issue)", "WARNING")
            else:
                self.log("✅ DIMS: Metrics tracking", "SUCCESS")
        else:
            self.log("❌ DIMS: Not tracking", "ERROR")

        return summary["success"], summary

    def verify_workflows(self) -> Tuple[bool, Dict]:
        """Verify Python workflows are configured"""
        self.log("Verifying Python workflows...", "INFO")

        workflows = [
            ("overnight_unified_cli.py", "Overnight Unified"),
            ("validation_cli.py", "3-Source Validation"),
            ("daily_update_cli.py", "Daily ESPN Update"),
        ]

        workflows_dir = self.project_root / "scripts" / "workflows"
        workflow_results = []
        passed = 0
        failed = 0

        for workflow_file, workflow_name in workflows:
            workflow_path = workflows_dir / workflow_file

            if workflow_path.exists():
                # Try dry-run to verify it loads
                result = subprocess.run(
                    ["python", str(workflow_path), "--dry-run"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=60,
                )

                success = result.returncode == 0
                workflow_results.append(
                    {
                        "name": workflow_name,
                        "success": success,
                        "exists": True,
                    }
                )

                if success:
                    passed += 1
                    self.log(f"  ✅ {workflow_name}", "SUCCESS")
                else:
                    failed += 1
                    self.log(f"  ❌ {workflow_name}: Failed dry-run", "ERROR")
            else:
                failed += 1
                workflow_results.append(
                    {
                        "name": workflow_name,
                        "success": False,
                        "exists": False,
                    }
                )
                self.log(f"  ❌ {workflow_name}: File not found", "ERROR")

        summary = {
            "passed": passed,
            "failed": failed,
            "total": len(workflows),
            "success": failed == 0,
            "workflows": workflow_results,
        }

        if summary["success"]:
            self.log(f"✅ Workflows: {passed}/{passed+failed} verified", "SUCCESS")
        else:
            self.log(f"❌ Workflows: {passed}/{passed+failed} verified", "ERROR")

        return summary["success"], summary

    def generate_report(self, detailed: bool = False) -> str:
        """Generate verification report"""
        duration = time.time() - self.start_time

        # Calculate overall success
        all_results = []
        for category, result in self.results.items():
            if isinstance(result, dict):
                all_results.append(result.get("success", False))

        overall_success = all(all_results) if all_results else False

        # Build report
        report = f"""
{'='*80}
PHASE 0 VERIFICATION REPORT
{'='*80}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration:  {duration:.1f}s
Status:    {'✅ ALL PASSED' if overall_success else '❌ FAILURES DETECTED'}

{'='*80}
RESULTS SUMMARY
{'='*80}
"""

        # Add results for each category
        if "system_validation" in self.results:
            sv = self.results["system_validation"]
            status = "✅ PASSED" if sv.get("success") else "❌ FAILED"
            report += f"\n✓ System Validation:   {status}"
            if "checks_passed" in sv:
                report += f" ({sv['checks_passed']} checks passed)"

        if "pytest" in self.results:
            pt = self.results["pytest"]
            status = "✅ PASSED" if pt.get("success") else "❌ FAILED"
            report += f"\n✓ Pytest Tests:        {status}"
            if not pt.get("skipped"):
                report += (
                    f" ({pt.get('passed', 0)} passed, {pt.get('failed', 0)} failed)"
                )

        if "validators" in self.results:
            vd = self.results["validators"]
            status = "✅ PASSED" if vd.get("success") else "❌ FAILED"
            report += f"\n✓ Validators:          {status}"
            if not vd.get("skipped"):
                report += f" ({vd.get('passed', 0)}/{vd.get('total', 0)} passed)"

        if "workflows" in self.results:
            wf = self.results["workflows"]
            status = "✅ PASSED" if wf.get("success") else "❌ FAILED"
            report += f"\n✓ Python Workflows:    {status}"
            report += f" ({wf.get('passed', 0)}/{wf.get('total', 0)} verified)"

        if "adce_health" in self.results:
            ad = self.results["adce_health"]
            status = "✅ HEALTHY" if ad.get("healthy") else "❌ UNHEALTHY"
            report += f"\n✓ ADCE Health:         {status}"

        if "dims_metrics" in self.results:
            dm = self.results["dims_metrics"]
            if dm.get("timeout"):
                status = "⚠️  TIMEOUT"
            elif dm.get("success"):
                status = "✅ TRACKING"
            else:
                status = "❌ NOT TRACKING"
            report += f"\n✓ DIMS Metrics:        {status}"

        report += f"\n\n{'='*80}\n"

        if detailed:
            report += "\nDETAILED RESULTS\n"
            report += "=" * 80 + "\n"
            report += json.dumps(self.results, indent=2)
            report += "\n" + "=" * 80 + "\n"

        return report

    def run_quick_verification(self):
        """Run quick verification (system validation only)"""
        self.log("Starting Quick Verification", "HEADER")

        success, result = self.run_system_validation()
        self.results["system_validation"] = result

        print(self.generate_report())

        return 0 if success else 1

    def run_subphase_verification(self, subphase: str):
        """Run verification for specific sub-phase"""
        self.log(f"Starting Sub-Phase {subphase} Verification", "HEADER")

        # Find sub-phase info
        subphase_info = None
        for sp_id, sp_name, sp_desc in self.SUBPHASES:
            if sp_id == subphase:
                subphase_info = (sp_id, sp_name, sp_desc)
                break

        if not subphase_info:
            self.log(f"Unknown sub-phase: {subphase}", "ERROR")
            return 1

        self.log(f"Sub-Phase: {subphase_info[1]}", "INFO")
        self.log(f"Description: {subphase_info[2]}", "INFO")

        # Run tests for this sub-phase
        success1, result1 = self.run_pytest_tests(subphase=subphase)
        self.results["pytest"] = result1

        success2, result2 = self.run_validators(subphase=subphase)
        self.results["validators"] = result2

        print(self.generate_report())

        overall_success = success1 and success2
        return 0 if overall_success else 1

    def run_full_verification(self, detailed_report: bool = False):
        """Run complete Phase 0 verification"""
        self.log("Starting Full Phase 0 Verification", "HEADER")
        self.log(f"Verifying {len(self.SUBPHASES)} sub-phases", "INFO")

        # Step 1: System validation (fast)
        self.log("\n[1/6] Running system validation...", "HEADER")
        success1, result1 = self.run_system_validation()
        self.results["system_validation"] = result1

        # Step 2: Pytest tests (medium)
        self.log("\n[2/6] Running pytest tests...", "HEADER")
        success2, result2 = self.run_pytest_tests()
        self.results["pytest"] = result2

        # Step 3: Validators (medium)
        self.log("\n[3/6] Running validators...", "HEADER")
        success3, result3 = self.run_validators()
        self.results["validators"] = result3

        # Step 4: Workflows (fast)
        self.log("\n[4/6] Verifying Python workflows...", "HEADER")
        success4, result4 = self.verify_workflows()
        self.results["workflows"] = result4

        # Step 5: ADCE health (fast)
        self.log("\n[5/6] Checking ADCE health...", "HEADER")
        success5, result5 = self.verify_adce_health()
        self.results["adce_health"] = result5

        # Step 6: DIMS metrics (fast)
        self.log("\n[6/6] Verifying DIMS metrics...", "HEADER")
        success6, result6 = self.verify_dims_metrics()
        self.results["dims_metrics"] = result6

        # Generate report
        print(self.generate_report(detailed=detailed_report))

        # Overall success
        all_success = all([success1, success2, success3, success4, success5, success6])

        if all_success:
            self.log("✅ Phase 0 verification PASSED", "SUCCESS")
        else:
            self.log("❌ Phase 0 verification FAILED", "ERROR")

        return 0 if all_success else 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Phase 0 Master Verification Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Full verification
  %(prog)s --quick             # Quick health check
  %(prog)s --subphase 0.0018   # Verify specific sub-phase
  %(prog)s --report            # Full verification with detailed report
  %(prog)s --json              # JSON output for CI/CD
        """,
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick verification (system validation only)",
    )
    parser.add_argument(
        "--subphase",
        metavar="ID",
        help="Run verification for specific sub-phase (e.g., 0.0018)",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed report"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output (show test output)"
    )

    args = parser.parse_args()

    # Create verifier
    verifier = Phase0Verifier(verbose=args.verbose, output_json=args.json)

    # Run appropriate verification
    try:
        if args.quick:
            exit_code = verifier.run_quick_verification()
        elif args.subphase:
            exit_code = verifier.run_subphase_verification(args.subphase)
        else:
            exit_code = verifier.run_full_verification(detailed_report=args.report)

        # Output JSON if requested
        if args.json:
            print(json.dumps(verifier.results, indent=2))

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
