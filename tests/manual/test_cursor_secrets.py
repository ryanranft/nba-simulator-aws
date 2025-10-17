#!/usr/bin/env python3
"""
Test script to verify Cursor Background Agent environment variables
Run this as a Background Agent task to test secret access
"""

import os
import sys


def test_environment_variables():
    """Test that environment variables are accessible"""
    print("=== Environment Variable Test ===")

    # List of expected environment variables
    expected_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION",
        "S3_BUCKET",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    found_vars = []
    missing_vars = []

    for var in expected_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values for security
            if "KEY" in var or "PASSWORD" in var or "SECRET" in var:
                masked_value = (
                    value[:4] + "*" * (len(value) - 8) + value[-4:]
                    if len(value) > 8
                    else "*" * len(value)
                )
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
            found_vars.append(var)
        else:
            print(f"❌ {var}: Not found")
            missing_vars.append(var)

    print(f"\n=== Summary ===")
    print(f"Found: {len(found_vars)} variables")
    print(f"Missing: {len(missing_vars)} variables")

    if missing_vars:
        print(f"Missing variables: {', '.join(missing_vars)}")

    return len(missing_vars) == 0


if __name__ == "__main__":
    success = test_environment_variables()
    sys.exit(0 if success else 1)
