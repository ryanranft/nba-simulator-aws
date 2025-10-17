#!/usr/bin/env python3
"""
Test security scanning tools

Verifies that git-secrets, detect-secrets, and trufflehog
are properly installed and can detect secrets.
"""

import subprocess
import tempfile
import os
import sys
from pathlib import Path


def test_git_secrets():
    """Test git-secrets catches secrets"""
    print("🧪 Testing git-secrets...")

    # Check if git-secrets is installed
    try:
        result = subprocess.run(
            ["git", "secrets", "--version"], capture_output=True, text=True, check=True
        )
        print(f"   ✅ git-secrets installed: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ git-secrets not installed")
        return False

    # Test with a fake AWS key
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n')
        f.write("# This is a test file\n")
        f.flush()

        try:
            result = subprocess.run(
                ["git", "secrets", "--scan", f.name], capture_output=True, text=True
            )

            if result.returncode != 0:
                print("   ✅ git-secrets detected test secret")
                return True
            else:
                print("   ❌ git-secrets did NOT detect test secret")
                return False
        finally:
            Path(f.name).unlink()


def test_detect_secrets():
    """Test detect-secrets catches secrets"""
    print("🧪 Testing detect-secrets...")

    # Check if detect-secrets is installed
    try:
        result = subprocess.run(
            ["detect-secrets", "--version"], capture_output=True, text=True, check=True
        )
        print(f"   ✅ detect-secrets installed: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ detect-secrets not installed")
        return False

    # Create a test file with a fake secret
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('api_key = "AIzaSyD1234567890ABCDEFGHIJKLMNOPQRST"\n')
        f.write("# This is a test Google API key\n")
        f.flush()

        try:
            result = subprocess.run(
                ["detect-secrets", "scan", f.name], capture_output=True, text=True
            )

            # detect-secrets returns 0 but outputs JSON with findings
            if "AIzaSyD" in result.stdout:
                print("   ✅ detect-secrets detected test secret")
                return True
            else:
                print("   ❌ detect-secrets did NOT detect test secret")
                return False
        finally:
            Path(f.name).unlink()


def test_trufflehog():
    """Test trufflehog is installed"""
    print("🧪 Testing trufflehog...")

    # Check if trufflehog is installed
    try:
        result = subprocess.run(
            ["trufflehog", "--version"], capture_output=True, text=True, check=True
        )
        print(f"   ✅ trufflehog installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ⚠️  trufflehog not installed (optional for local use)")
        return False


def test_pre_commit():
    """Test pre-commit is installed and configured"""
    print("🧪 Testing pre-commit...")

    # Check if pre-commit is installed
    try:
        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True, check=True
        )
        print(f"   ✅ pre-commit installed: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ pre-commit not installed")
        return False

    # Check if .pre-commit-config.yaml exists
    if Path(".pre-commit-config.yaml").exists():
        print("   ✅ .pre-commit-config.yaml exists")
    else:
        print("   ⚠️  .pre-commit-config.yaml not found")
        return False

    # Check if hooks are installed
    git_dir = Path(".git/hooks")
    if git_dir.exists() and (git_dir / "pre-commit").exists():
        print("   ✅ pre-commit hooks installed")
        return True
    else:
        print("   ⚠️  pre-commit hooks not installed (run: pre-commit install)")
        return False


def test_baseline_file():
    """Check if .secrets.baseline exists"""
    print("🧪 Checking .secrets.baseline...")

    if Path(".secrets.baseline").exists():
        print("   ✅ .secrets.baseline exists")
        return True
    else:
        print(
            "   ⚠️  .secrets.baseline not found (run: detect-secrets scan > .secrets.baseline)"
        )
        return False


def test_patterns_file():
    """Check if .git-secrets-patterns exists"""
    print("🧪 Checking .git-secrets-patterns...")

    if Path(".git-secrets-patterns").exists():
        print("   ✅ .git-secrets-patterns exists")
        return True
    else:
        print("   ⚠️  .git-secrets-patterns not found")
        return False


def test_s3_validation():
    """Test S3 validation script exists and can run"""
    print("🧪 Testing S3 validation script...")

    # Check if script exists
    if not Path("scripts/validate_s3_public_access.py").exists():
        print("   ❌ validate_s3_public_access.py not found")
        return False

    # Check if boto3 is available
    try:
        import boto3

        print("   ✅ boto3 installed")
    except ImportError:
        print("   ⚠️  boto3 not installed (required for S3 validation)")
        return False

    # Try to run help
    try:
        result = subprocess.run(
            [sys.executable, "scripts/validate_s3_public_access.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            print("   ✅ S3 validation script can run")
            return True
        else:
            print("   ❌ S3 validation script failed")
            return False
    except Exception as e:
        print(f"   ❌ Error running S3 validation: {e}")
        return False


def main():
    print("=" * 60)
    print("Security Scanning Tools Test Suite")
    print("NBA MCP Synthesis")
    print("=" * 60)
    print()

    results = {
        "git-secrets": test_git_secrets(),
        "detect-secrets": test_detect_secrets(),
        "trufflehog": test_trufflehog(),
        "pre-commit": test_pre_commit(),
        "baseline": test_baseline_file(),
        "patterns": test_patterns_file(),
        "s3-validation": test_s3_validation(),
    }

    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print()

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for tool, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {tool}")

    print()
    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ All security scanning tools are working correctly!")
        print()
        print("Next steps:")
        print("  1. Run: pre-commit run --all-files")
        print("  2. Make a test commit")
        print("  3. Verify hooks block secrets")
        print()
        return 0
    else:
        print("❌ Some security scanning tools need attention.")
        print()
        print("To fix:")
        print("  1. Run: ./scripts/setup_security_scanning.sh")
        print("  2. Re-run this test: python scripts/test_security_scanning.py")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
