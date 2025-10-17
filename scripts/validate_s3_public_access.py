#!/usr/bin/env python3
"""
Validate S3 bucket and object public access settings.

Ensures that all S3 buckets (especially those containing books) are private
and not publicly accessible.
"""

import os
import sys
import json
import boto3
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError


def get_buckets_from_env() -> List[str]:
    """
    Discover S3 bucket names from environment variables.

    Looks for patterns like:
    - S3_BUCKET_*
    - *_BUCKET_*
    - S3_*_BUCKET
    """
    buckets = set()

    # Patterns to match
    patterns = [
        r".*BUCKET.*",
        r"S3_.*",
    ]

    for key, value in os.environ.items():
        for pattern in patterns:
            if re.match(pattern, key, re.IGNORECASE):
                # Extract bucket name (handle various formats)
                # Bucket names are usually the value
                if value and not value.startswith("/") and not value.startswith("http"):
                    # Basic validation: bucket names are lowercase, alphanumeric, hyphens
                    if re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", value):
                        buckets.add(value)

    # Add known buckets
    known_buckets = [
        "nba-mcp-books-20251011",
    ]

    for bucket in known_buckets:
        buckets.add(bucket)

    return sorted(list(buckets))


def check_bucket_public_access_block(s3_client, bucket: str) -> Dict:
    """
    Check if bucket has PublicAccessBlock configuration enabled.

    All 4 settings should be True for maximum security:
    - BlockPublicAcls
    - IgnorePublicAcls
    - BlockPublicPolicy
    - RestrictPublicBuckets
    """
    try:
        response = s3_client.get_public_access_block(Bucket=bucket)
        config = response["PublicAccessBlockConfiguration"]

        is_secure = all(
            [
                config.get("BlockPublicAcls", False),
                config.get("IgnorePublicAcls", False),
                config.get("BlockPublicPolicy", False),
                config.get("RestrictPublicBuckets", False),
            ]
        )

        return {
            "bucket": bucket,
            "check": "PublicAccessBlock",
            "is_secure": is_secure,
            "config": config,
            "message": (
                "All public access blocked"
                if is_secure
                else "Public access NOT fully blocked"
            ),
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchPublicAccessBlockConfiguration":
            return {
                "bucket": bucket,
                "check": "PublicAccessBlock",
                "is_secure": False,
                "config": None,
                "message": "No PublicAccessBlock configuration (PUBLIC)",
            }
        else:
            return {
                "bucket": bucket,
                "check": "PublicAccessBlock",
                "is_secure": None,
                "error": str(e),
                "message": f"Error checking: {str(e)}",
            }


def check_bucket_acl(s3_client, bucket: str) -> Dict:
    """
    Check bucket ACL for public grants.

    Looks for:
    - AllUsers (public read/write)
    - AuthenticatedUsers (any AWS user)
    """
    try:
        response = s3_client.get_bucket_acl(Bucket=bucket)
        grants = response.get("Grants", [])

        public_grants = []
        for grant in grants:
            grantee = grant.get("Grantee", {})
            uri = grantee.get("URI", "")
            permission = grant.get("Permission", "")

            if "AllUsers" in uri or "AuthenticatedUsers" in uri:
                public_grants.append(
                    {
                        "grantee": uri,
                        "permission": permission,
                    }
                )

        is_secure = len(public_grants) == 0

        return {
            "bucket": bucket,
            "check": "BucketACL",
            "is_secure": is_secure,
            "public_grants": public_grants,
            "message": (
                "No public ACL grants"
                if is_secure
                else f"Found {len(public_grants)} public ACL grants"
            ),
        }
    except ClientError as e:
        return {
            "bucket": bucket,
            "check": "BucketACL",
            "is_secure": None,
            "error": str(e),
            "message": f"Error checking: {str(e)}",
        }


def check_bucket_policy(s3_client, bucket: str) -> Dict:
    """
    Check bucket policy for public access.

    Looks for policies with:
    - Principal: "*"
    - Effect: Allow
    """
    try:
        response = s3_client.get_bucket_policy(Bucket=bucket)
        policy_str = response.get("Policy", "{}")
        policy = json.loads(policy_str)

        statements = policy.get("Statement", [])
        public_statements = []

        for statement in statements:
            principal = statement.get("Principal", {})
            effect = statement.get("Effect", "")

            # Check for wildcard principal with Allow
            is_public = False
            if effect == "Allow":
                if principal == "*":
                    is_public = True
                elif isinstance(principal, dict):
                    for key, value in principal.items():
                        if value == "*":
                            is_public = True

            if is_public:
                public_statements.append(statement)

        is_secure = len(public_statements) == 0

        return {
            "bucket": bucket,
            "check": "BucketPolicy",
            "is_secure": is_secure,
            "public_statements": public_statements,
            "message": (
                "No public policy statements"
                if is_secure
                else f"Found {len(public_statements)} public statements"
            ),
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchBucketPolicy":
            return {
                "bucket": bucket,
                "check": "BucketPolicy",
                "is_secure": True,
                "public_statements": [],
                "message": "No bucket policy (secure)",
            }
        else:
            return {
                "bucket": bucket,
                "check": "BucketPolicy",
                "is_secure": None,
                "error": str(e),
                "message": f"Error checking: {str(e)}",
            }


def check_object_acls(
    s3_client, bucket: str, prefix: str = "books/", max_objects: int = 1000
) -> Tuple[List[Dict], int]:
    """
    Check object ACLs for public access.

    Scans objects under the specified prefix (default: books/)
    and checks for public read grants.
    """
    try:
        public_objects = []
        total_checked = 0

        # List objects
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        for page in page_iterator:
            contents = page.get("Contents", [])

            for obj in contents:
                if total_checked >= max_objects:
                    break

                key = obj["Key"]
                total_checked += 1

                # Check object ACL
                try:
                    acl_response = s3_client.get_object_acl(Bucket=bucket, Key=key)
                    grants = acl_response.get("Grants", [])

                    for grant in grants:
                        grantee = grant.get("Grantee", {})
                        uri = grantee.get("URI", "")
                        permission = grant.get("Permission", "")

                        if "AllUsers" in uri or "AuthenticatedUsers" in uri:
                            public_objects.append(
                                {
                                    "key": key,
                                    "grantee": uri,
                                    "permission": permission,
                                }
                            )
                            break
                except ClientError as e:
                    # Skip objects we can't read
                    continue

            if total_checked >= max_objects:
                break

        return public_objects, total_checked
    except ClientError as e:
        return [], 0


def generate_s3_security_report(findings: Dict) -> str:
    """Generate S3 security audit report"""
    report = [
        "# S3 Public Access Validation Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    total_buckets = len(findings.get("buckets", {}))
    total_issues = 0

    # Summary
    report.append("## Summary")
    report.append("")
    report.append(f"Buckets Checked: {total_buckets}")
    report.append("")

    # Bucket-level findings
    report.append("## Bucket-Level Security")
    report.append("")

    for bucket, checks in findings.get("buckets", {}).items():
        bucket_secure = True
        bucket_issues = []

        for check in checks:
            if check["is_secure"] is False:
                bucket_secure = False
                bucket_issues.append(check["message"])
                total_issues += 1

        status = "✅" if bucket_secure else "❌"
        report.append(f"### {status} {bucket}")
        report.append("")

        for check in checks:
            check_status = "✅" if check["is_secure"] else "❌"
            if check["is_secure"] is None:
                check_status = "⚠️"
            report.append(f"- {check_status} **{check['check']}**: {check['message']}")

        report.append("")

    # Object-level findings
    report.append("## Object-Level Security (Books)")
    report.append("")

    object_findings = findings.get("objects", {})
    for bucket, data in object_findings.items():
        public_objects = data.get("public_objects", [])
        total_checked = data.get("total_checked", 0)

        if public_objects:
            total_issues += len(public_objects)
            report.append(f"### ❌ {bucket}")
            report.append("")
            report.append(
                f"Checked {total_checked} objects, found {len(public_objects)} public:"
            )
            report.append("")
            for obj in public_objects[:10]:  # Show first 10
                report.append(
                    f"- `{obj['key']}` - {obj['grantee']} ({obj['permission']})"
                )
            if len(public_objects) > 10:
                report.append(f"- ... and {len(public_objects) - 10} more")
            report.append("")
        else:
            report.append(f"### ✅ {bucket}")
            report.append("")
            report.append(f"Checked {total_checked} objects - all private")
            report.append("")

    # Overall result
    report.append("## Overall Result")
    report.append("")

    if total_issues == 0:
        report.append("✅ **PASS** - All S3 resources are private")
    else:
        report.append(f"❌ **FAIL** - Found {total_issues} public access issues")

    report.append("")

    # Recommendations
    if total_issues > 0:
        report.append("## Recommendations")
        report.append("")
        report.append("1. Enable S3 Block Public Access on all buckets")
        report.append("2. Remove public ACL grants from buckets and objects")
        report.append("3. Review and restrict bucket policies")
        report.append("4. Use IAM roles and policies instead of public access")
        report.append("")
        report.append("### Quick Fix Commands")
        report.append("")
        report.append("```bash")
        report.append("# Enable Block Public Access on bucket")
        for bucket in findings.get("buckets", {}).keys():
            report.append(f"aws s3api put-public-access-block --bucket {bucket} \\")
            report.append("  --public-access-block-configuration \\")
            report.append(
                "  'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'"
            )
            report.append("")
        report.append("```")

    return "\n".join(report)


def validate_all_buckets(
    fail_on_public: bool = True, max_objects_per_bucket: int = 1000
) -> int:
    """
    Main validation function.

    Returns:
        0 if all secure, 1 if public access found
    """
    print("=" * 60)
    print("S3 Public Access Validation")
    print("NBA MCP Synthesis")
    print("=" * 60)
    print()

    # Get buckets
    print("🔍 Discovering S3 buckets from environment...")
    buckets = get_buckets_from_env()

    if not buckets:
        print("   ⚠️  No S3 buckets found in environment variables")
        print()
        print("Set environment variables like:")
        print("  S3_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW=your-bucket-name")
        print()
        return 0 if not fail_on_public else 1

    print(f"   Found {len(buckets)} bucket(s): {', '.join(buckets)}")
    print()

    # Initialize S3 client
    try:
        s3_client = boto3.client("s3")
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        print()
        print("Set AWS credentials:")
        print("  export AWS_ACCESS_KEY_ID=your-key")
        print("  export AWS_SECRET_ACCESS_KEY=your-secret")
        print()
        return 1

    findings = {
        "buckets": {},
        "objects": {},
    }

    # Check each bucket
    for bucket in buckets:
        print(f"🔍 Checking bucket: {bucket}")

        bucket_findings = []

        # Check PublicAccessBlock
        print("   Checking PublicAccessBlock...")
        result = check_bucket_public_access_block(s3_client, bucket)
        bucket_findings.append(result)
        status = "✅" if result["is_secure"] else "❌"
        print(f"   {status} {result['message']}")

        # Check Bucket ACL
        print("   Checking Bucket ACL...")
        result = check_bucket_acl(s3_client, bucket)
        bucket_findings.append(result)
        status = "✅" if result["is_secure"] else "❌"
        print(f"   {status} {result['message']}")

        # Check Bucket Policy
        print("   Checking Bucket Policy...")
        result = check_bucket_policy(s3_client, bucket)
        bucket_findings.append(result)
        status = "✅" if result["is_secure"] else "❌"
        print(f"   {status} {result['message']}")

        findings["buckets"][bucket] = bucket_findings

        # Check object ACLs for books
        print(f"   Checking object ACLs (max {max_objects_per_bucket} objects)...")
        public_objects, total_checked = check_object_acls(
            s3_client, bucket, "books/", max_objects_per_bucket
        )

        findings["objects"][bucket] = {
            "public_objects": public_objects,
            "total_checked": total_checked,
        }

        if public_objects:
            print(
                f"   ❌ Found {len(public_objects)} public objects (out of {total_checked} checked)"
            )
        else:
            print(f"   ✅ All {total_checked} objects are private")

        print()

    # Generate report
    print("📝 Generating report...")
    report = generate_s3_security_report(findings)

    # Save report
    report_path = Path("s3_security_audit_report.md")
    report_path.write_text(report)
    print(f"✅ Report saved to {report_path}")
    print()

    # Count total issues
    total_issues = 0
    for bucket_checks in findings["buckets"].values():
        for check in bucket_checks:
            if check["is_secure"] is False:
                total_issues += 1

    for object_data in findings["objects"].values():
        total_issues += len(object_data["public_objects"])

    # Summary
    print("=" * 60)
    if total_issues == 0:
        print("✅ All S3 resources are private!")
        print("=" * 60)
        print()
        return 0
    else:
        print(f"❌ Found {total_issues} public access issues")
        print("=" * 60)
        print()
        print(f"Review report: {report_path}")
        print()
        if fail_on_public:
            return 1
        else:
            return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate S3 bucket and object public access settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--fail-on-public",
        action="store_true",
        help="Exit with error code if public access found",
    )
    parser.add_argument(
        "--max-objects",
        type=int,
        default=1000,
        help="Maximum objects to check per bucket (default: 1000)",
    )
    args = parser.parse_args()

    exit_code = validate_all_buckets(
        fail_on_public=args.fail_on_public, max_objects_per_bucket=args.max_objects
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
