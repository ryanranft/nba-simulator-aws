#!/usr/bin/env python3
"""
S3 Data Lake Manifest Generator (Python)

Purpose: Generate comprehensive manifest of all S3 objects
Usage: python3 scripts/backup/generate_s3_manifest.py
Author: Claude Code (NBA Simulator Project)
Date: October 30, 2025
"""

import json
import subprocess  # nosec B404 - Required for AWS CLI calls
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Colors
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def log_info(msg):
    print(f"{BLUE}[INFO]{NC} {msg}")


def log_success(msg):
    print(f"{GREEN}[SUCCESS]{NC} {msg}")


def log_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}")


def human_size(bytes_size):
    """Convert bytes to human-readable format."""
    if bytes_size >= 1024**3:
        return f"{bytes_size / 1024**3:.2f} GB"
    elif bytes_size >= 1024**2:
        return f"{bytes_size / 1024**2:.2f} MB"
    elif bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size} bytes"


def main():
    # Configuration
    S3_BUCKET = "nba-sim-raw-data-lake"
    BACKUP_DIR = Path("/Users/ryanranft/nba-simulator-aws/backups")
    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
    MANIFEST_FILE = BACKUP_DIR / f"s3_manifest_{TIMESTAMP}.txt"
    MANIFEST_JSON = BACKUP_DIR / f"s3_manifest_{TIMESTAMP}.json"

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    log_info("Starting S3 manifest generation...")

    # Fetch S3 object list
    log_info(f"Fetching S3 object list from s3://{S3_BUCKET}...")
    log_info("This may take several minutes for 146,115+ objects...")

    try:
        result = subprocess.run(  # nosec B603, B607 - AWS CLI call with hardcoded command
            [
                "aws",
                "s3api",
                "list-objects-v2",
                "--bucket",
                S3_BUCKET,
                "--output",
                "json",
                "--query",
                "Contents[].{Key:Key,Size:Size,LastModified:LastModified,ETag:ETag}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        objects = json.loads(result.stdout)

        # Save JSON manifest
        with open(MANIFEST_JSON, "w") as f:
            json.dump(objects, f, indent=2)

        log_success(f"S3 object list retrieved: {len(objects):,} objects")

    except subprocess.CalledProcessError as e:
        log_error(f"Failed to fetch S3 object list: {e}")
        sys.exit(1)

    # Process objects
    log_info("Generating human-readable manifest...")

    directories = defaultdict(list)
    total_size = 0
    total_count = 0

    for obj in objects:
        key = obj["Key"]
        size = obj["Size"]
        last_modified = obj["LastModified"]
        etag = obj["ETag"]

        # Get top-level directory
        parts = key.split("/")
        top_dir = parts[0] if len(parts) > 1 else "(root)"

        directories[top_dir].append(
            {"key": key, "size": size, "last_modified": last_modified, "etag": etag}
        )

        total_size += size
        total_count += 1

    # Create text manifest
    with open(MANIFEST_FILE, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("# S3 Data Lake Manifest\n")
        f.write("# NBA Simulator AWS Project\n")
        f.write(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Bucket: s3://{S3_BUCKET}\n")
        f.write("=" * 80 + "\n\n")

        # Summary by directory
        f.write("=" * 80 + "\n")
        f.write("SUMMARY BY DIRECTORY\n")
        f.write("=" * 80 + "\n\n")

        for dir_name in sorted(directories.keys()):
            dir_objects = directories[dir_name]
            dir_size = sum(obj["size"] for obj in dir_objects)
            dir_count = len(dir_objects)

            f.write(f"{dir_name}/\n")
            f.write(f"  Files: {dir_count:,}\n")
            f.write(f"  Size: {human_size(dir_size)} ({dir_size:,} bytes)\n\n")

        # Overall totals
        f.write("=" * 80 + "\n")
        f.write("OVERALL TOTALS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Files: {total_count:,}\n")
        f.write(f"Total Size: {human_size(total_size)} ({total_size:,} bytes)\n\n")

        # Detailed file list (sample from each directory)
        f.write("=" * 80 + "\n")
        f.write("DETAILED FILE LIST (Sample)\n")
        f.write("=" * 80 + "\n\n")

        for dir_name in sorted(directories.keys()):
            dir_objects = directories[dir_name]
            f.write(f"\n### {dir_name}/ ({len(dir_objects):,} files)\n\n")

            # Sort by last modified (newest first)
            sorted_objects = sorted(
                dir_objects, key=lambda x: x["last_modified"], reverse=True
            )

            # Show first 10 files
            display_count = min(10, len(sorted_objects))

            for obj in sorted_objects[:display_count]:
                f.write(f"  {obj['key']}\n")
                f.write(
                    f"    Size: {human_size(obj['size']):>12}  Modified: {obj['last_modified']}  ETag: {obj['etag'][:16]}...\n"
                )

            if len(sorted_objects) > display_count:
                f.write(
                    f"  ... and {len(sorted_objects) - display_count:,} more files\n"
                )

            f.write("\n")

    log_success("Human-readable manifest created")

    # Upload to S3
    log_info("Uploading manifest files to S3...")

    S3_MANIFEST_PREFIX = "backups/manifests"

    try:
        # Upload JSON
        subprocess.run(  # nosec B603, B607 - AWS CLI call with hardcoded command
            [
                "aws",
                "s3",
                "cp",
                str(MANIFEST_JSON),
                f"s3://{S3_BUCKET}/{S3_MANIFEST_PREFIX}/s3_manifest_{TIMESTAMP}.json",
                "--storage-class",
                "STANDARD_IA",
            ],
            check=True,
        )

        # Upload text
        subprocess.run(  # nosec B603, B607 - AWS CLI call with hardcoded command
            [
                "aws",
                "s3",
                "cp",
                str(MANIFEST_FILE),
                f"s3://{S3_BUCKET}/{S3_MANIFEST_PREFIX}/s3_manifest_{TIMESTAMP}.txt",
                "--storage-class",
                "STANDARD_IA",
            ],
            check=True,
        )

        log_success("Manifest files uploaded to S3")

    except subprocess.CalledProcessError as e:
        log_error(f"Failed to upload manifests: {e}")

    # Generate checksums
    log_info("Generating checksums...")

    try:
        subprocess.run(  # nosec B603, B607 - shasum call with hardcoded command
            ["shasum", "-a", "256", str(MANIFEST_FILE)],
            stdout=open(f"{MANIFEST_FILE}.sha256", "w"),
            check=True,
        )
        subprocess.run(  # nosec B603, B607 - shasum call with hardcoded command
            ["shasum", "-a", "256", str(MANIFEST_JSON)],
            stdout=open(f"{MANIFEST_JSON}.sha256", "w"),
            check=True,
        )
        log_success("Checksums generated")
    except Exception as e:
        log_error(f"Failed to generate checksums: {e}")

    # Summary
    manifest_size_mb = MANIFEST_FILE.stat().st_size / 1024 / 1024
    json_size_mb = MANIFEST_JSON.stat().st_size / 1024 / 1024

    print(f"\n{'=' * 80}")
    print("# S3 MANIFEST GENERATION COMPLETE")
    print(f"{'=' * 80}\n")
    print(f"Timestamp:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"S3 Bucket:        s3://{S3_BUCKET}\n")
    print("Local Files Created:")
    print(f"- Text Manifest:  {MANIFEST_FILE} ({manifest_size_mb:.2f} MB)")
    print(f"- JSON Manifest:  {MANIFEST_JSON} ({json_size_mb:.2f} MB)")
    print(f"- Checksums:      {MANIFEST_FILE}.sha256")
    print(f"                  {MANIFEST_JSON}.sha256\n")
    print("S3 Files Uploaded:")
    print(f"- s3://{S3_BUCKET}/{S3_MANIFEST_PREFIX}/s3_manifest_{TIMESTAMP}.txt")
    print(f"- s3://{S3_BUCKET}/{S3_MANIFEST_PREFIX}/s3_manifest_{TIMESTAMP}.json\n")
    print("Storage Class:    STANDARD_IA (Infrequent Access)\n")
    print(f"{'=' * 80}\n")

    log_success("S3 manifest generation completed successfully!")
    log_info(f"Text manifest: {MANIFEST_FILE}")
    log_info(f"JSON manifest: {MANIFEST_JSON}")


if __name__ == "__main__":
    main()
