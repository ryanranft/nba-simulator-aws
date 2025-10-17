#!/usr/bin/env python3
"""
Validate secrets security across codebase.

Checks:
1. No hardcoded API keys
2. All code uses unified_secrets_manager
3. No orphaned .env files
4. Naming convention compliance
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


def scan_for_hardcoded_secrets(directory: str) -> List[Tuple[str, int, str]]:
    """Scan Python files for hardcoded secrets"""
    patterns = [
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        (r"AIza[0-9A-Za-z_-]{35}", "Google API Key"),
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/Anthropic Key"),
        (r"sk-proj-[a-zA-Z0-9_-]{20,}", "OpenAI Project Key"),
        (r"sk-ant-[a-zA-Z0-9_-]{20,}", "Anthropic API Key"),
        (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded Password"),
        (r"lin_api_[a-zA-Z0-9]{40}", "Linear API Key"),
    ]

    findings = []
    exclude_dirs = {"venv", "__pycache__", ".venv", "node_modules", ".git"}
    exclude_files = {
        "validate_secrets_security.py",  # This file
        "test_security_scanning.py",  # Test file
        ".env.example",  # Template file
    }

    for py_file in Path(directory).rglob("*.py"):
        # Skip excluded directories
        if any(excluded in str(py_file) for excluded in exclude_dirs):
            continue

        # Skip excluded files
        if py_file.name in exclude_files:
            continue

        try:
            content = py_file.read_text(errors="ignore")
            for pattern, desc in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    # Get the actual line content
                    lines = content.split("\n")
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                    # Skip if it's clearly a placeholder or example
                    if any(
                        placeholder in line_content.lower()
                        for placeholder in [
                            "example",
                            "placeholder",
                            "your_",
                            "test_",
                            "fake_",
                            "mock_",
                            "sample_",
                            "demo_",
                            "xxx",
                            "yyy",
                            "pragma: allowlist secret",
                        ]
                    ):
                        continue

                    findings.append((str(py_file), line_num, desc, line_content[:80]))
        except Exception as e:
            print(f"Warning: Could not read {py_file}: {e}", file=sys.stderr)

    return findings


def check_unified_secrets_usage(directory: str) -> Dict[str, List[str]]:
    """Check files using os.getenv instead of unified_secrets_manager"""
    issues = {"direct_getenv": [], "load_dotenv": [], "missing_unified_import": []}

    exclude_dirs = {"venv", "__pycache__", ".venv", "node_modules", ".git", "tests"}
    exclude_files = {
        "validate_secrets_security.py",
        "test_security_scanning.py",
        "unified_secrets_manager.py",  # The manager itself
        "load_env_hierarchical.py",  # Loader script
        "env_helper.py",  # Helper that wraps unified manager
    }

    for py_file in Path(directory).rglob("*.py"):
        # Skip excluded directories
        if any(excluded in str(py_file) for excluded in exclude_dirs):
            continue

        # Skip excluded files
        if py_file.name in exclude_files:
            continue

        try:
            content = py_file.read_text(errors="ignore")

            # Check for direct os.getenv() usage with uppercase env vars
            if re.search(r'os\.getenv\([\'"][A-Z_]+[\'"]', content):
                # Check if unified_secrets_manager is imported
                if (
                    "unified_secrets_manager" not in content
                    and "env_helper" not in content
                ):
                    issues["direct_getenv"].append(str(py_file))

            # Check for load_dotenv() usage
            if "load_dotenv()" in content or "load_dotenv(" in content:
                # Check if it's in a legacy file or test
                if (
                    "legacy" not in str(py_file).lower()
                    and "test" not in str(py_file).lower()
                ):
                    issues["load_dotenv"].append(str(py_file))
        except Exception as e:
            print(f"Warning: Could not read {py_file}: {e}", file=sys.stderr)

    return issues


def check_orphaned_env_files(directory: str) -> List[str]:
    """Check for .env files in the project directory"""
    orphaned_files = []
    exclude_dirs = {"venv", "__pycache__", ".venv", "node_modules", ".git"}

    for env_file in Path(directory).rglob(".env*"):
        # Skip excluded directories
        if any(excluded in str(env_file) for excluded in exclude_dirs):
            continue

        # Allow .env.example, .env.template, .secrets.baseline
        if env_file.name in [".env.example", ".env.template", ".secrets.baseline"]:
            continue

        # Allow directories like .env.production
        if env_file.is_dir():
            continue

        orphaned_files.append(str(env_file))

    return orphaned_files


def generate_report(findings, usage_issues, orphaned_files) -> str:
    """Generate security audit report"""
    report = [
        "# Security Audit Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
    ]

    # Summary counts
    total_issues = (
        len(findings) + sum(len(v) for v in usage_issues.values()) + len(orphaned_files)
    )
    if total_issues == 0:
        report.append("✅ **No security issues detected!**")
    else:
        report.append(f"⚠️  **Found {total_issues} potential security issues**")

    report.append("")

    # Hardcoded secrets findings
    report.append("## 1. Hardcoded Secrets Scan")
    report.append("")
    if findings:
        report.append(f"❌ Found {len(findings)} potential hardcoded secrets:")
        report.append("")
        for file, line, desc, content in findings:
            report.append(f"- **{desc}** in `{file}:{line}`")
            report.append(f"  ```")
            report.append(f"  {content}")
            report.append(f"  ```")
        report.append("")
        report.append(
            "**Action Required**: Review and remove hardcoded secrets. Use unified_secrets_manager instead."
        )
    else:
        report.append("✅ No hardcoded secrets detected")

    report.append("")

    # Secrets Manager Usage
    report.append("## 2. Secrets Manager Usage")
    report.append("")

    has_usage_issues = any(usage_issues.values())
    if has_usage_issues:
        if usage_issues["direct_getenv"]:
            report.append(
                f"### Direct os.getenv() Usage ({len(usage_issues['direct_getenv'])} files)"
            )
            report.append("")
            report.append(
                "These files use `os.getenv()` without importing unified_secrets_manager:"
            )
            report.append("")
            for file in usage_issues["direct_getenv"]:
                report.append(f"- `{file}`")
            report.append("")
            report.append(
                "**Action Required**: Import and use `unified_secrets_manager.get_secret()`"
            )
            report.append("")

        if usage_issues["load_dotenv"]:
            report.append(
                f"### load_dotenv() Usage ({len(usage_issues['load_dotenv'])} files)"
            )
            report.append("")
            report.append(
                "These files use `load_dotenv()` instead of hierarchical loading:"
            )
            report.append("")
            for file in usage_issues["load_dotenv"]:
                report.append(f"- `{file}`")
            report.append("")
            report.append(
                "**Action Required**: Replace with `load_secrets_hierarchical()`"
            )
            report.append("")
    else:
        report.append("✅ All files use unified_secrets_manager properly")
        report.append("")

    # Orphaned .env files
    report.append("## 3. Orphaned .env Files")
    report.append("")
    if orphaned_files:
        report.append(
            f"⚠️  Found {len(orphaned_files)} .env files in project directory:"
        )
        report.append("")
        for file in orphaned_files:
            report.append(f"- `{file}`")
        report.append("")
        report.append("**Action Required**: Move secrets to hierarchical structure:")
        report.append("```")
        report.append("/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/")
        report.append(
            "  big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/"
        )
        report.append("```")
    else:
        report.append("✅ No orphaned .env files found")

    report.append("")

    # Recommendations
    report.append("## 4. Recommendations")
    report.append("")
    report.append("1. **Use hierarchical secrets structure** for all sensitive data")
    report.append(
        "2. **Import unified_secrets_manager** in all Python files accessing secrets"
    )
    report.append(
        "3. **Run pre-commit hooks** before committing: `pre-commit run --all-files`"
    )
    report.append(
        "4. **Audit permissions** regularly: `./scripts/audit_secret_permissions.sh`"
    )
    report.append("5. **Review .secrets.baseline** for false positives")
    report.append("")

    # Next steps
    report.append("## 5. Next Steps")
    report.append("")
    if total_issues > 0:
        report.append("```bash")
        report.append("# Fix hardcoded secrets")
        report.append("# Replace with unified_secrets_manager calls")
        report.append("")
        report.append("# Re-run validation")
        report.append("python scripts/validate_secrets_security.py")
        report.append("")
        report.append("# Run pre-commit checks")
        report.append("pre-commit run --all-files")
        report.append("```")
    else:
        report.append("✅ All security checks passed! Ready to commit.")
        report.append("")
        report.append("```bash")
        report.append("git add .")
        report.append('git commit -m "feat: security enhancements"')
        report.append("```")

    return "\n".join(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate secrets security across codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check-usage", action="store_true", help="Check unified_secrets_manager usage"
    )
    parser.add_argument(
        "--check-s3",
        action="store_true",
        help="Check S3 bucket public access (requires AWS credentials)",
    )
    parser.add_argument(
        "--output",
        default="security_audit_report.md",
        help="Output file for report (default: security_audit_report.md)",
    )
    parser.add_argument(
        "--directory",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("NBA MCP Synthesis - Security Validation")
    print("=" * 60)
    print()

    # Scan for hardcoded secrets
    print("🔍 Scanning for hardcoded secrets...")
    findings = scan_for_hardcoded_secrets(args.directory)
    if findings:
        print(f"   ❌ Found {len(findings)} potential secrets")
    else:
        print("   ✅ No hardcoded secrets detected")

    # Check unified secrets usage
    print("🔍 Checking unified_secrets_manager usage...")
    usage_issues = check_unified_secrets_usage("mcp_server")
    total_usage_issues = sum(len(v) for v in usage_issues.values())
    if total_usage_issues > 0:
        print(f"   ⚠️  Found {total_usage_issues} files with usage issues")
    else:
        print("   ✅ All files use unified_secrets_manager properly")

    # Check for orphaned .env files
    print("🔍 Checking for orphaned .env files...")
    orphaned_files = check_orphaned_env_files(args.directory)
    if orphaned_files:
        print(f"   ⚠️  Found {len(orphaned_files)} orphaned .env files")
    else:
        print("   ✅ No orphaned .env files found")

    # Check S3 public access if requested
    s3_issues = 0
    if args.check_s3:
        print("🔍 Checking S3 public access...")
        try:
            # Import here to avoid requiring boto3 unless needed
            import subprocess

            result = subprocess.run(
                [sys.executable, "scripts/validate_s3_public_access.py"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                s3_issues = 1
                print("   ❌ S3 public access issues found")
            else:
                print("   ✅ All S3 resources are private")
        except Exception as e:
            print(f"   ⚠️  Could not check S3: {e}")

    # Generate report
    print()
    print(f"📝 Generating report: {args.output}")
    report = generate_report(findings, usage_issues, orphaned_files)

    # Save report
    Path(args.output).write_text(report)
    print(f"✅ Report saved to {args.output}")
    print()

    # Summary
    total_issues = len(findings) + total_usage_issues + len(orphaned_files) + s3_issues
    if total_issues > 0:
        print("=" * 60)
        print(f"❌ Security issues found: {total_issues}")
        print("=" * 60)
        print()
        print("Please review the report and fix the issues before committing.")
        print(f"Report: {args.output}")
        if args.check_s3 and s3_issues > 0:
            print("S3 Report: s3_security_audit_report.md")
        print()
        sys.exit(1)
    else:
        print("=" * 60)
        print("✅ All security checks passed!")
        print("=" * 60)
        print()
        print("Your code is ready to commit.")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
