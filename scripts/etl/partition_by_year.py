#!/usr/bin/env python3
"""
Partition S3 Data by Year for Glue Crawler Processing

This script reorganizes S3 data from flat structure to year-partitioned structure,
allowing Glue Crawlers to process one year at a time (avoiding OOM errors).

Current S3 Structure (FLAT):
  s3://nba-sim-raw-data-lake/
    ├── schedule/171031017.json, 191103005.json, ... (11,633 files)
    ├── pbp/171031017.json, 191103005.json, ... (44,826 files)
    ├── box_scores/171031017.json, 191103005.json, ... (44,828 files)
    └── team_stats/171031017.json, 191103005.json, ... (44,828 files)

New S3 Structure (YEAR-PARTITIONED):
  s3://nba-sim-raw-data-lake/
    ├── schedule/year=1997/*.json
    ├── schedule/year=1998/*.json
    ├── schedule/year=2021/*.json
    ├── pbp/year=1997/*.json
    ├── pbp/year=1998/*.json
    └── ... (one folder per year)

Benefits:
- Each year has ~500-2000 files (well under 50K Glue Crawler limit)
- Can run Glue Crawlers per year without OOM errors
- Athena queries can use year partitioning for better performance
- Easy to process specific year ranges (e.g., only 2015-2025)

Author: Ryan Ranft
Date: 2025-10-01
Phase: 2.1 - Glue Crawler (Year-Based Approach)
"""

import boto3
import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from collections import defaultdict

# Import our game ID decoder
sys.path.append(str(Path(__file__).parent))
from game_id_decoder import decode_game_id, extract_year_from_filename


class S3YearPartitioner:
    """Reorganize S3 data into year-based partitions for Glue Crawler processing."""

    def __init__(self, bucket: str, dry_run: bool = True):
        """
        Initialize S3 partitioner.

        Args:
            bucket: S3 bucket name (e.g., "nba-sim-raw-data-lake")
            dry_run: If True, only show what would be done (no actual copies)
        """
        self.bucket = bucket
        self.dry_run = dry_run
        self.s3_client = boto3.client("s3")
        self.stats = defaultdict(lambda: defaultdict(int))

    def list_files(self, prefix: str) -> List[str]:
        """
        List all files in S3 prefix.

        Args:
            prefix: S3 prefix (e.g., "schedule/", "pbp/")

        Returns:
            List of S3 keys
        """
        print(f"Listing files in s3://{self.bucket}/{prefix}...")

        paginator = self.s3_client.get_paginator("list_objects_v2")
        files = []

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                # Skip if already partitioned (contains "year=")
                if "year=" in key:
                    continue
                # Only include .json files
                if key.endswith(".json"):
                    files.append(key)

        print(f"  Found {len(files)} files to partition")
        return files

    def partition_files(self, prefix: str) -> Dict[int, List[str]]:
        """
        Group files by year based on game ID.

        Args:
            prefix: S3 prefix (e.g., "schedule/", "pbp/")

        Returns:
            Dictionary mapping year -> list of S3 keys
        """
        files = self.list_files(prefix)
        partitions = defaultdict(list)
        errors = []

        for key in files:
            # Extract filename from key
            filename = key.split("/")[-1]

            # Decode year from game ID
            year = extract_year_from_filename(filename)

            if year:
                partitions[year].append(key)
                self.stats[prefix][year] += 1
            else:
                errors.append(key)

        if errors:
            print(f"  WARNING: Could not decode year for {len(errors)} files")
            if len(errors) <= 10:
                for err_key in errors:
                    print(f"    - {err_key}")

        return partitions

    def copy_to_partition(self, source_key: str, data_type: str, year: int) -> str:
        """
        Copy S3 object to year-partitioned location.

        Args:
            source_key: Original S3 key (e.g., "schedule/19961219.json")
            data_type: Data type prefix (e.g., "schedule", "pbp")
            year: Year for partition (e.g., 1996)

        Returns:
            New S3 key (e.g., "schedule/year=1996/19961219.json")
        """
        filename = source_key.split("/")[-1]
        new_key = f"{data_type}/year={year}/{filename}"

        if self.dry_run:
            print(f"  [DRY RUN] Would copy: s3://{self.bucket}/{source_key}")
            print(f"            to:        s3://{self.bucket}/{new_key}")
        else:
            # Copy object within same bucket
            copy_source = {"Bucket": self.bucket, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket, Key=new_key
            )
            print(f"  Copied: {source_key} -> {new_key}")

        return new_key

    def partition_data_type(self, data_type: str, delete_originals: bool = False):
        """
        Partition all files for a specific data type.

        Args:
            data_type: Data type to partition ("schedule", "pbp", "box_scores", "team_stats")
            delete_originals: If True, delete original files after successful copy
        """
        print(f"\n{'=' * 80}")
        print(f"Partitioning: {data_type}")
        print(f"{'=' * 80}")

        # Get partitions
        partitions = self.partition_files(f"{data_type}/")

        if not partitions:
            print(f"  No files found to partition for {data_type}")
            return

        # Show partition summary
        print(f"\nPartition Summary for {data_type}:")
        print(f"  Years: {min(partitions.keys())} to {max(partitions.keys())}")
        print(f"  Total files: {sum(len(files) for files in partitions.values())}")
        print(f"\n  Files per year:")

        for year in sorted(partitions.keys()):
            file_count = len(partitions[year])
            print(f"    {year}: {file_count:,} files")

        # Copy files to partitions
        print(f"\nCopying files to year partitions...")

        total_copied = 0
        for year, files in sorted(partitions.items()):
            print(f"\n  Year {year} ({len(files)} files):")

            for i, source_key in enumerate(files, 1):
                self.copy_to_partition(source_key, data_type, year)
                total_copied += 1

                # Progress indicator
                if i % 100 == 0:
                    print(f"    Progress: {i}/{len(files)} files...")

        print(f"\n  ✅ Completed: {total_copied} files copied to year partitions")

        # Optionally delete originals
        if delete_originals and not self.dry_run:
            print(f"\n  Deleting original files...")
            for year, files in partitions.items():
                for source_key in files:
                    self.s3_client.delete_object(Bucket=self.bucket, Key=source_key)
                    print(f"    Deleted: {source_key}")
            print(f"  ✅ Deleted {total_copied} original files")

    def print_summary(self):
        """Print final summary of partitioning."""
        print(f"\n{'=' * 80}")
        print("PARTITIONING SUMMARY")
        print(f"{'=' * 80}")

        for data_type, year_counts in sorted(self.stats.items()):
            total = sum(year_counts.values())
            print(f"\n{data_type.upper()}:")
            print(f"  Total files: {total:,}")
            print(f"  Years: {min(year_counts.keys())} to {max(year_counts.keys())}")
            print(f"  Files per year:")
            for year in sorted(year_counts.keys()):
                count = year_counts[year]
                print(f"    {year}: {count:,}")

        if self.dry_run:
            print(f"\n⚠️  DRY RUN MODE - No files were actually copied")
            print(f"   Run with --execute to perform actual S3 operations")


def main():
    parser = argparse.ArgumentParser(
        description="Partition S3 NBA data by year for Glue Crawler processing"
    )
    parser.add_argument(
        "--bucket",
        default="nba-sim-raw-data-lake",
        help="S3 bucket name (default: nba-sim-raw-data-lake)",
    )
    parser.add_argument(
        "--data-types",
        nargs="+",
        default=["schedule", "pbp", "box_scores", "team_stats"],
        help="Data types to partition (default: all)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform S3 operations (default: dry run)",
    )
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="Delete original files after successful copy (use with caution!)",
    )

    args = parser.parse_args()

    # Confirm execution
    if args.execute:
        print("⚠️  WARNING: This will copy files in S3, incurring data transfer costs!")
        if args.delete_originals:
            print("⚠️  WARNING: Original files will be DELETED after copying!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    # Initialize partitioner
    dry_run = not args.execute
    partitioner = S3YearPartitioner(bucket=args.bucket, dry_run=dry_run)

    # Partition each data type
    for data_type in args.data_types:
        partitioner.partition_data_type(
            data_type, delete_originals=args.delete_originals
        )

    # Print summary
    partitioner.print_summary()


if __name__ == "__main__":
    main()
