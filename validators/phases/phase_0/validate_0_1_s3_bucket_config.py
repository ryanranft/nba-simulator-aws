#!/usr/bin/env python3
"""
Validate S3 Bucket Configuration - Phase 0.0001

Verifies that the S3 bucket meets all specifications from Phase 0.0001:
- Bucket exists in correct region (us-east-1)
- Encryption enabled (SSE-S3)
- Public access blocked
- Versioning disabled (cost optimization)

Usage:
    python validate_s3_bucket_config.py
    python validate_s3_bucket_config.py --bucket nba-sim-raw-data-lake
"""

import boto3
import sys
from typing import Dict, List, Tuple
from botocore.exceptions import ClientError, NoCredentialsError


class S3BucketConfigValidator:
    """Validates S3 bucket configuration against Phase 0.0001 specifications."""

    def __init__(self, bucket_name: str = "nba-sim-raw-data-lake"):
        """
        Initialize validator.

        Args:
            bucket_name: Name of S3 bucket to validate
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")
        self.expected_region = "us-east-1"
        self.failures: List[str] = []
        self.warnings: List[str] = []

    def validate_bucket_exists(self) -> bool:
        """Check if bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Bucket '{self.bucket_name}' exists and is accessible")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                self.failures.append(f"Bucket '{self.bucket_name}' does not exist")
            elif error_code == "403":
                self.failures.append(f"Access denied to bucket '{self.bucket_name}'")
            else:
                self.failures.append(f"Error accessing bucket: {e}")
            print(f"✗ {self.failures[-1]}")
            return False

    def validate_region(self) -> bool:
        """Verify bucket is in correct region (us-east-1)."""
        try:
            response = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            # Note: us-east-1 returns None for LocationConstraint
            actual_region = response.get("LocationConstraint") or "us-east-1"

            if actual_region == self.expected_region:
                print(f"✓ Bucket in correct region: {self.expected_region}")
                return True
            else:
                self.failures.append(
                    f"Bucket in wrong region. Expected: {self.expected_region}, "
                    f"Actual: {actual_region}"
                )
                print(f"✗ {self.failures[-1]}")
                return False
        except ClientError as e:
            self.failures.append(f"Failed to check bucket region: {e}")
            print(f"✗ {self.failures[-1]}")
            return False

    def validate_encryption(self) -> bool:
        """Verify encryption is enabled (SSE-S3)."""
        try:
            response = self.s3_client.get_bucket_encryption(Bucket=self.bucket_name)
            rules = response.get("ServerSideEncryptionConfiguration", {}).get(
                "Rules", []
            )

            if not rules:
                self.failures.append("No encryption rules configured")
                print(f"✗ {self.failures[-1]}")
                return False

            # Check for SSE-S3 (AES256)
            has_sse_s3 = any(
                rule.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm")
                == "AES256"
                for rule in rules
            )

            if has_sse_s3:
                print("✓ Encryption enabled (SSE-S3/AES256)")
                return True
            else:
                algo = (
                    rules[0]
                    .get("ApplyServerSideEncryptionByDefault", {})
                    .get("SSEAlgorithm", "Unknown")
                )
                self.warnings.append(
                    f"Encryption enabled but using {algo} instead of AES256 (SSE-S3)"
                )
                print(f"⚠ {self.warnings[-1]}")
                return True  # Still encrypted, just different algorithm

        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ServerSideEncryptionConfigurationNotFoundError"
            ):
                self.failures.append("Encryption is NOT enabled")
                print(f"✗ {self.failures[-1]}")
            else:
                self.failures.append(f"Failed to check encryption: {e}")
                print(f"✗ {self.failures[-1]}")
            return False

    def validate_public_access_block(self) -> bool:
        """Verify public access is blocked."""
        try:
            response = self.s3_client.get_public_access_block(Bucket=self.bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})

            all_blocked = (
                config.get("BlockPublicAcls", False)
                and config.get("IgnorePublicAcls", False)
                and config.get("BlockPublicPolicy", False)
                and config.get("RestrictPublicBuckets", False)
            )

            if all_blocked:
                print("✓ Public access blocked (all 4 settings enabled)")
                return True
            else:
                unblocked = [
                    setting
                    for setting, value in {
                        "BlockPublicAcls": config.get("BlockPublicAcls"),
                        "IgnorePublicAcls": config.get("IgnorePublicAcls"),
                        "BlockPublicPolicy": config.get("BlockPublicPolicy"),
                        "RestrictPublicBuckets": config.get("RestrictPublicBuckets"),
                    }.items()
                    if not value
                ]
                self.failures.append(
                    f"Public access not fully blocked. Disabled settings: {', '.join(unblocked)}"
                )
                print(f"✗ {self.failures[-1]}")
                return False

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
                self.failures.append(
                    "No public access block configuration (bucket may be public!)"
                )
                print(f"✗ {self.failures[-1]}")
            else:
                self.failures.append(f"Failed to check public access block: {e}")
                print(f"✗ {self.failures[-1]}")
            return False

    def validate_versioning_disabled(self) -> bool:
        """Verify versioning is disabled (cost optimization from Phase 0.0001)."""
        try:
            response = self.s3_client.get_bucket_versioning(Bucket=self.bucket_name)
            status = response.get("Status", "Disabled")  # Default is disabled

            if status == "Enabled":
                self.warnings.append(
                    "Versioning is ENABLED. Phase 0.0001 specifies disabled for cost optimization. "
                    "This will increase storage costs."
                )
                print(f"⚠ {self.warnings[-1]}")
                return False
            elif status == "Suspended":
                self.warnings.append(
                    "Versioning is SUSPENDED (should be disabled, not just suspended)"
                )
                print(f"⚠ {self.warnings[-1]}")
                return True  # Acceptable
            else:
                print("✓ Versioning disabled (cost optimized)")
                return True

        except ClientError as e:
            self.failures.append(f"Failed to check versioning: {e}")
            print(f"✗ {self.failures[-1]}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """
        Run all validation checks.

        Returns:
            Tuple of (all_passed: bool, results: Dict)
        """
        print(f"\n{'='*70}")
        print(f"S3 Bucket Configuration Validation - Phase 0.0001")
        print(f"Bucket: {self.bucket_name}")
        print(f"{'='*70}\n")

        results = {
            "bucket_exists": self.validate_bucket_exists(),
        }

        # Only continue if bucket exists
        if results["bucket_exists"]:
            results.update(
                {
                    "correct_region": self.validate_region(),
                    "encryption_enabled": self.validate_encryption(),
                    "public_access_blocked": self.validate_public_access_block(),
                    "versioning_disabled": self.validate_versioning_disabled(),
                }
            )

        # Summary
        print(f"\n{'='*70}")
        print("VALIDATION SUMMARY")
        print(f"{'='*70}")

        total_checks = len(results)
        passed_checks = sum(1 for v in results.values() if v)

        print(f"\nChecks Passed: {passed_checks}/{total_checks}")

        if self.failures:
            print(f"\n❌ FAILURES ({len(self.failures)}):")
            for i, failure in enumerate(self.failures, 1):
                print(f"  {i}. {failure}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        all_passed = all(results.values())
        if all_passed and not self.failures:
            print("\n✅ All validations PASSED")
        else:
            print("\n❌ Some validations FAILED")

        print(f"{'='*70}\n")

        return all_passed, results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate S3 bucket configuration for Phase 0.0001"
    )
    parser.add_argument(
        "--bucket",
        default="nba-sim-raw-data-lake",
        help="S3 bucket name to validate (default: nba-sim-raw-data-lake)",
    )
    args = parser.parse_args()

    try:
        validator = S3BucketConfigValidator(bucket_name=args.bucket)
        all_passed, results = validator.run_all_validations()

        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)

    except NoCredentialsError:
        print("\n❌ ERROR: AWS credentials not found")
        print("Please configure AWS credentials using 'aws configure'")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
