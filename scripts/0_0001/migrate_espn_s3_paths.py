#!/usr/bin/env python3
"""
Phase 0.0001: ESPN S3 Path Migration Script

Migrates ESPN data from flat folder structure to espn_* prefixed folders:
- pbp/ → espn_play_by_play/
- box_scores/ → espn_box_scores/
- team_stats/ → espn_team_stats/
- schedule/ → espn_schedules/

This script uses S3 copy operations (no download/re-upload) to preserve data
and minimize costs. Original folders are kept for rollback capability.

Usage:
    python scripts/0_0001/migrate_espn_s3_paths.py --dry-run  # Preview changes
    python scripts/0_0001/migrate_espn_s3_paths.py            # Execute migration
    python scripts/0_0001/migrate_espn_s3_paths.py --verify   # Verify only
"""

import argparse
import boto3
import sys
from datetime import datetime
from typing import Dict, List, Tuple
from botocore.exceptions import ClientError


# S3 Configuration
BUCKET_NAME = "nba-sim-raw-data-lake"
REGION = "us-east-1"

# Path mappings: old_prefix → new_prefix
PATH_MAPPINGS = {
    "pbp/": "espn_play_by_play/",
    "box_scores/": "espn_box_scores/",
    "team_stats/": "espn_team_stats/",
    "schedule/": "espn_schedules/",
}

# Expected baseline counts from Phase 0.0001
EXPECTED_COUNTS = {
    "pbp/": 44826,
    "box_scores/": 44828,
    "team_stats/": 44828,
    "schedule/": 11633,
}


class S3PathMigrator:
    """Handles S3 path migration for ESPN data."""

    def __init__(self, bucket_name: str, dry_run: bool = False):
        """
        Initialize migrator.

        Args:
            bucket_name: S3 bucket name
            dry_run: If True, only preview changes without executing
        """
        self.bucket_name = bucket_name
        self.dry_run = dry_run
        self.s3_client = boto3.client("s3", region_name=REGION)
        self.s3_resource = boto3.resource("s3", region_name=REGION)
        self.bucket = self.s3_resource.Bucket(bucket_name)

    def count_objects(self, prefix: str) -> int:
        """
        Count objects with given prefix.

        Args:
            prefix: S3 prefix to count

        Returns:
            Number of objects
        """
        count = 0
        paginator = self.s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if "Contents" in page:
                count += len(page["Contents"])

        return count

    def get_total_size(self, prefix: str) -> int:
        """
        Get total size of objects with given prefix.

        Args:
            prefix: S3 prefix to measure

        Returns:
            Total size in bytes
        """
        total_size = 0
        paginator = self.s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if "Contents" in page:
                total_size += sum(obj["Size"] for obj in page["Contents"])

        return total_size

    def verify_source_paths(self) -> Dict[str, Dict[str, int]]:
        """
        Verify source paths exist and match expected counts.

        Returns:
            Dictionary mapping old_prefix → {count, size_gb, expected}
        """
        print("\n=== Verifying Source Paths ===")
        results = {}

        for old_prefix, expected_count in EXPECTED_COUNTS.items():
            count = self.count_objects(old_prefix)
            size_bytes = self.get_total_size(old_prefix)
            size_gb = size_bytes / (1024**3)

            results[old_prefix] = {
                "count": count,
                "size_gb": size_gb,
                "expected": expected_count,
                "match": count == expected_count,
            }

            status = "✓" if count == expected_count else "✗"
            print(
                f"{status} {old_prefix:20s} {count:6d} files ({size_gb:6.2f} GB) "
                f"[expected: {expected_count:6d}]"
            )

        return results

    def check_destination_paths(self) -> Dict[str, int]:
        """
        Check if destination paths already exist.

        Returns:
            Dictionary mapping new_prefix → file count
        """
        print("\n=== Checking Destination Paths ===")
        results = {}

        for new_prefix in PATH_MAPPINGS.values():
            count = self.count_objects(new_prefix)
            results[new_prefix] = count

            status = "⚠" if count > 0 else "✓"
            print(
                f"{status} {new_prefix:25s} {count:6d} files "
                f"{'(already exists!)' if count > 0 else '(empty, ready)'}"
            )

        return results

    def migrate_path(self, old_prefix: str, new_prefix: str) -> Tuple[int, int]:
        """
        Migrate objects from old prefix to new prefix.

        Args:
            old_prefix: Source prefix
            new_prefix: Destination prefix

        Returns:
            Tuple of (successful_copies, failed_copies)
        """
        print(
            f"\n{'[DRY RUN] ' if self.dry_run else ''}Migrating: {old_prefix} → {new_prefix}"
        )

        successful = 0
        failed = 0
        paginator = self.s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=old_prefix):
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                old_key = obj["Key"]

                # Skip if it's just the prefix itself (directory marker)
                if old_key == old_prefix:
                    continue

                # Generate new key by replacing prefix
                new_key = new_prefix + old_key[len(old_prefix) :]

                try:
                    if not self.dry_run:
                        # Use S3 copy operation (no download/re-upload)
                        copy_source = {"Bucket": self.bucket_name, "Key": old_key}
                        self.s3_client.copy_object(
                            CopySource=copy_source,
                            Bucket=self.bucket_name,
                            Key=new_key,
                            ServerSideEncryption="AES256",
                        )

                    successful += 1

                    # Progress indicator every 1000 files
                    if successful % 1000 == 0:
                        print(f"  Progress: {successful:,} files copied...")

                except ClientError as e:
                    print(f"  ✗ Failed to copy {old_key}: {e}")
                    failed += 1

        return successful, failed

    def migrate_all(self) -> Dict[str, Tuple[int, int]]:
        """
        Migrate all ESPN paths.

        Returns:
            Dictionary mapping old_prefix → (successful, failed)
        """
        print(f"\n{'=' * 60}")
        print(
            f"{'DRY RUN MODE - No changes will be made' if self.dry_run else 'MIGRATION MODE - Changes will be applied'}"
        )
        print(f"{'=' * 60}")

        results = {}

        for old_prefix, new_prefix in PATH_MAPPINGS.items():
            successful, failed = self.migrate_path(old_prefix, new_prefix)
            results[old_prefix] = (successful, failed)

            print(
                f"  ✓ {successful:,} files {'would be' if self.dry_run else ''} copied"
            )
            if failed > 0:
                print(f"  ✗ {failed:,} files failed")

        return results

    def verify_migration(self) -> bool:
        """
        Verify migration was successful by comparing file counts.

        Returns:
            True if all counts match, False otherwise
        """
        print("\n=== Verifying Migration ===")
        all_match = True

        for old_prefix, new_prefix in PATH_MAPPINGS.items():
            old_count = self.count_objects(old_prefix)
            new_count = self.count_objects(new_prefix)

            match = old_count == new_count
            all_match = all_match and match

            status = "✓" if match else "✗"
            print(f"{status} {old_prefix:20s} → {new_prefix:25s}")
            print(
                f"   Source: {old_count:6,d} files | Destination: {new_count:6,d} files"
            )

        return all_match

    def generate_report(self, results: Dict[str, Tuple[int, int]]) -> None:
        """
        Generate migration summary report.

        Args:
            results: Dictionary mapping old_prefix → (successful, failed)
        """
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Bucket: s3://{self.bucket_name}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        print()

        total_successful = 0
        total_failed = 0

        for old_prefix, (successful, failed) in results.items():
            new_prefix = PATH_MAPPINGS[old_prefix]
            total_successful += successful
            total_failed += failed

            print(f"{old_prefix:20s} → {new_prefix:25s}")
            print(f"  Successful: {successful:6,d}")
            if failed > 0:
                print(f"  Failed:     {failed:6,d} ⚠")

        print()
        print(
            f"Total files {'would be' if self.dry_run else ''} migrated: {total_successful:,}"
        )
        if total_failed > 0:
            print(f"Total failures: {total_failed:,} ⚠")
        print("=" * 60)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Migrate ESPN S3 paths to espn_* prefixed structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration without making changes
  python migrate_espn_s3_paths.py --dry-run

  # Execute migration
  python migrate_espn_s3_paths.py

  # Verify migration after execution
  python migrate_espn_s3_paths.py --verify
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing migration",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify migration success (compare source and destination counts)",
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts (auto-confirm)",
    )

    args = parser.parse_args()

    # Initialize migrator
    migrator = S3PathMigrator(BUCKET_NAME, dry_run=args.dry_run)

    try:
        # Verify source paths
        source_results = migrator.verify_source_paths()

        # Check for mismatches
        mismatches = [
            prefix for prefix, data in source_results.items() if not data["match"]
        ]

        if mismatches:
            print(
                f"\n⚠ WARNING: {len(mismatches)} source path(s) don't match expected counts:"
            )
            for prefix in mismatches:
                data = source_results[prefix]
                print(f"  {prefix}: {data['count']} (expected {data['expected']})")

            if not args.dry_run and not args.yes:
                response = input("\nContinue anyway? [y/N]: ")
                if response.lower() != "y":
                    print("Migration cancelled.")
                    return 1
            elif args.yes:
                print("\n--yes flag provided, continuing automatically...")

        # Check destination paths
        dest_results = migrator.check_destination_paths()

        # Check if any destinations already have files
        existing = [prefix for prefix, count in dest_results.items() if count > 0]

        if existing and not args.verify:
            print(f"\n⚠ WARNING: {len(existing)} destination path(s) already exist:")
            for prefix in existing:
                print(f"  {prefix}: {dest_results[prefix]:,} files")

            if not args.dry_run and not args.yes:
                response = input(
                    "\nThis may indicate a previous migration. Continue? [y/N]: "
                )
                if response.lower() != "y":
                    print("Migration cancelled.")
                    return 1
            elif args.yes:
                print("\n--yes flag provided, continuing automatically...")

        # Verify only mode
        if args.verify:
            success = migrator.verify_migration()
            if success:
                print("\n✓ Migration verification successful!")
                return 0
            else:
                print("\n✗ Migration verification failed!")
                return 1

        # Execute migration
        results = migrator.migrate_all()

        # Generate report
        migrator.generate_report(results)

        # Verify migration if not dry run
        if not args.dry_run:
            print("\nVerifying migration...")
            success = migrator.verify_migration()

            if success:
                print("\n✓ Migration completed successfully!")
                print(
                    "\n⚠ IMPORTANT: Original folders are still in place for rollback."
                )
                print(
                    "   After verifying downstream systems work, you can remove them with:"
                )
                print("   aws s3 rm s3://nba-sim-raw-data-lake/pbp/ --recursive")
                print("   aws s3 rm s3://nba-sim-raw-data-lake/box_scores/ --recursive")
                print("   aws s3 rm s3://nba-sim-raw-data-lake/team_stats/ --recursive")
                print("   aws s3 rm s3://nba-sim-raw-data-lake/schedule/ --recursive")
                return 0
            else:
                print("\n✗ Migration verification failed!")
                return 1

        return 0

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
