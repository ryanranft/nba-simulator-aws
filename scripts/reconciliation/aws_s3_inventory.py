#!/usr/bin/env python3
"""
AWS S3 Inventory Integration - ADCE Phase 2B
Leverage AWS S3 Inventory Reports for 1000x faster scanning

AWS S3 Inventory provides automated daily/weekly reports of bucket contents.
This is orders of magnitude faster than listing objects via API.

Benefits:
- 1000x faster than list_objects_v2 API calls
- Daily automated updates (no manual scanning needed)
- CSV/Parquet format with metadata
- Reduced API costs

Setup Required:
1. Enable S3 Inventory in AWS Console
2. Configure daily reports to S3 destination
3. Update this script with inventory bucket/prefix

Usage:
    # Use latest AWS inventory report
    python aws_s3_inventory.py

    # Fall back to sample scanning if inventory not available
    python aws_s3_inventory.py --fallback-to-sample
"""

import boto3
import csv
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AWSS3InventoryReader:
    """
    Read AWS S3 Inventory reports for fast bucket scanning

    AWS S3 Inventory generates daily reports with all objects in bucket.
    This is much faster than scanning via API calls.
    """

    def __init__(
        self,
        data_bucket,
        inventory_bucket=None,
        inventory_prefix="inventory-reports",
        output_dir="inventory/cache",
    ):
        """
        Initialize AWS S3 Inventory reader

        Args:
            data_bucket: S3 bucket with NBA data
            inventory_bucket: S3 bucket where inventory reports are stored (default: same as data_bucket)
            inventory_prefix: Prefix where inventory reports are stored
            output_dir: Where to save processed inventory
        """
        self.s3 = boto3.client("s3")
        self.data_bucket = data_bucket
        self.inventory_bucket = inventory_bucket or data_bucket
        self.inventory_prefix = inventory_prefix
        self.output_dir = Path(output_dir)

        logger.info(f"Initialized AWS S3 Inventory reader for bucket: {data_bucket}")
        logger.info(
            f"Inventory location: s3://{self.inventory_bucket}/{self.inventory_prefix}"
        )

    def check_inventory_configured(self):
        """
        Check if S3 Inventory is configured for the bucket

        Returns:
            bool: True if inventory configured, False otherwise
        """
        try:
            response = self.s3.list_bucket_inventory_configurations(
                Bucket=self.data_bucket
            )

            configs = response.get("InventoryConfigurationList", [])
            if configs:
                logger.info(f"Found {len(configs)} inventory configuration(s)")
                for config in configs:
                    logger.info(f"  - {config['Id']}: {config['Destination']}")
                return True
            else:
                logger.warning("No S3 Inventory configurations found")
                return False

        except Exception as e:
            logger.error(f"Error checking inventory configuration: {e}")
            return False

    def find_latest_inventory_manifest(self):
        """
        Find the most recent inventory manifest file

        Returns:
            str: S3 key of latest manifest.json, or None if not found
        """
        try:
            # List objects in inventory prefix
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=self.inventory_bucket, Prefix=self.inventory_prefix
            )

            # Find all manifest.json files
            manifests = []
            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    if key.endswith("manifest.json"):
                        manifests.append(
                            {
                                "key": key,
                                "last_modified": obj["LastModified"],
                                "size": obj["Size"],
                            }
                        )

            if not manifests:
                logger.warning("No inventory manifest files found")
                return None

            # Sort by last modified (newest first)
            manifests.sort(key=lambda x: x["last_modified"], reverse=True)
            latest = manifests[0]

            logger.info(f"Found latest manifest: {latest['key']}")
            logger.info(f"  Last modified: {latest['last_modified']}")
            logger.info(
                f"  Age: {(datetime.now(latest['last_modified'].tzinfo) - latest['last_modified']).days} days"
            )

            return latest["key"]

        except Exception as e:
            logger.error(f"Error finding inventory manifest: {e}")
            return None

    def download_manifest(self, manifest_key):
        """
        Download and parse inventory manifest

        Args:
            manifest_key: S3 key of manifest.json

        Returns:
            dict: Parsed manifest data
        """
        try:
            logger.info(f"Downloading manifest: {manifest_key}")

            response = self.s3.get_object(
                Bucket=self.inventory_bucket, Key=manifest_key
            )

            manifest = json.loads(response["Body"].read())

            logger.info(f"Manifest details:")
            logger.info(f"  Source bucket: {manifest.get('sourceBucket')}")
            logger.info(f"  Creation date: {manifest.get('creationTimestamp')}")
            logger.info(f"  File format: {manifest.get('fileFormat')}")
            logger.info(f"  Data files: {len(manifest.get('files', []))}")

            return manifest

        except Exception as e:
            logger.error(f"Error downloading manifest: {e}")
            return None

    def process_inventory_file(self, file_key, file_format="CSV"):
        """
        Process a single inventory data file

        Args:
            file_key: S3 key of inventory data file (CSV or Parquet)
            file_format: Format of file ('CSV' or 'Parquet')

        Returns:
            list: Parsed inventory records
        """
        records = []

        try:
            logger.info(f"Processing inventory file: {file_key}")

            # Download file
            response = self.s3.get_object(Bucket=self.inventory_bucket, Key=file_key)

            # Decompress if gzipped
            content = response["Body"].read()
            if file_key.endswith(".gz"):
                content = gzip.decompress(content)

            if file_format == "CSV":
                # Parse CSV
                lines = content.decode("utf-8").splitlines()
                reader = csv.DictReader(lines)

                for row in reader:
                    # Convert CSV row to structured record
                    records.append(
                        {
                            "s3_key": row.get("Key"),
                            "size_bytes": int(row.get("Size", 0)),
                            "last_modified": row.get("LastModifiedDate"),
                            "etag": row.get("ETag"),
                            "storage_class": row.get("StorageClass"),
                        }
                    )

            elif file_format == "Parquet":
                # Parse Parquet (requires pyarrow)
                import pyarrow.parquet as pq
                import io

                table = pq.read_table(io.BytesIO(content))
                df = table.to_pandas()

                for _, row in df.iterrows():
                    records.append(
                        {
                            "s3_key": row.get("key"),
                            "size_bytes": int(row.get("size", 0)),
                            "last_modified": str(row.get("last_modified_date")),
                            "etag": row.get("e_tag"),
                            "storage_class": row.get("storage_class"),
                        }
                    )

            logger.info(f"Processed {len(records)} records from {file_key}")
            return records

        except Exception as e:
            logger.error(f"Error processing inventory file {file_key}: {e}")
            return []

    def read_inventory(self):
        """
        Read complete inventory from AWS S3 Inventory reports

        Returns:
            dict: Structured inventory (same format as scan_s3_inventory.py)
        """
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("Reading AWS S3 Inventory Reports")
        logger.info("=" * 80)

        # Check if inventory is configured
        if not self.check_inventory_configured():
            logger.error("S3 Inventory not configured for this bucket")
            logger.error("Please enable S3 Inventory in AWS Console first")
            return None

        # Find latest manifest
        manifest_key = self.find_latest_inventory_manifest()
        if not manifest_key:
            logger.error("No inventory manifest found")
            return None

        # Download manifest
        manifest = self.download_manifest(manifest_key)
        if not manifest:
            logger.error("Failed to download manifest")
            return None

        # Process all data files
        all_records = []
        file_format = manifest.get("fileFormat", "CSV")

        for file_info in manifest.get("files", []):
            file_key = file_info.get("key")
            if file_key:
                records = self.process_inventory_file(file_key, file_format)
                all_records.extend(records)

        # Build structured inventory (same format as scan_s3_inventory.py)
        from scan_s3_inventory import S3InventoryScanner

        scanner = S3InventoryScanner(self.data_bucket, output_dir=str(self.output_dir))

        inventory = {
            "metadata": {
                "scan_timestamp": datetime.now().isoformat(),
                "bucket": self.data_bucket,
                "scan_mode": "aws_inventory",
                "inventory_manifest": manifest_key,
                "inventory_date": manifest.get("creationTimestamp"),
                "total_objects_scanned": len(all_records),
                "total_objects_kept": len(all_records),
                "total_size_bytes": sum(r.get("size_bytes", 0) for r in all_records),
                "scan_duration_seconds": (datetime.now() - start_time).total_seconds(),
            },
            "by_source": {},
            "by_season": {},
            "by_type": {},
            "files": [],
        }

        # Parse each record
        for record in all_records:
            s3_key = record["s3_key"]
            metadata = scanner.parse_s3_path(s3_key)
            metadata.update(record)

            inventory["files"].append(metadata)

            # Aggregate
            if metadata.get("source"):
                scanner._add_to_index(
                    inventory["by_source"].setdefault(
                        metadata["source"], {"count": 0, "total_size": 0, "files": []}
                    ),
                    metadata,
                )
            if metadata.get("season"):
                scanner._add_to_index(
                    inventory["by_season"].setdefault(
                        metadata["season"], {"count": 0, "total_size": 0, "files": []}
                    ),
                    metadata,
                )
            if metadata.get("data_type"):
                scanner._add_to_index(
                    inventory["by_type"].setdefault(
                        metadata["data_type"],
                        {"count": 0, "total_size": 0, "files": []},
                    ),
                    metadata,
                )

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n✅ AWS Inventory read complete in {duration:.1f}s")
        logger.info(
            f"Total objects: {inventory['metadata']['total_objects_scanned']:,}"
        )
        logger.info(
            f"Total size: {inventory['metadata']['total_size_bytes'] / 1024**3:.2f} GB"
        )

        return inventory

    def save_inventory(self, inventory, output_file="current_inventory.json"):
        """Save inventory to file"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / output_file

        logger.info(f"Saving inventory to {output_path}")

        with open(output_path, "w") as f:
            json.dump(inventory, f, indent=2, default=str)

        logger.info("Inventory saved successfully")
        return output_path


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Read AWS S3 Inventory reports for fast bucket scanning"
    )
    parser.add_argument(
        "--data-bucket",
        default="nba-sim-raw-data-lake",
        help="S3 bucket containing NBA data",
    )
    parser.add_argument(
        "--inventory-bucket",
        help="S3 bucket containing inventory reports (default: same as data-bucket)",
    )
    parser.add_argument(
        "--inventory-prefix",
        default="inventory-reports",
        help="Prefix where inventory reports are stored",
    )
    parser.add_argument(
        "--output", default="current_inventory.json", help="Output filename"
    )
    parser.add_argument(
        "--fallback-to-sample",
        action="store_true",
        help="Fall back to sample scanning if inventory not available",
    )

    args = parser.parse_args()

    # Initialize reader
    reader = AWSS3InventoryReader(
        data_bucket=args.data_bucket,
        inventory_bucket=args.inventory_bucket,
        inventory_prefix=args.inventory_prefix,
    )

    # Try to read inventory
    inventory = reader.read_inventory()

    if inventory is None and args.fallback_to_sample:
        logger.warning(
            "AWS Inventory not available, falling back to sample scanning..."
        )
        from scan_s3_inventory import S3InventoryScanner

        scanner = S3InventoryScanner(bucket_name=args.data_bucket, sample_rate=0.1)
        inventory = scanner.scan()

    if inventory:
        # Save results
        output_path = reader.save_inventory(inventory, args.output)
        print(f"\n✅ Inventory saved: {output_path}")

        # Print summary
        print(f"\n📊 Inventory Summary:")
        print(f"  Mode: {inventory['metadata']['scan_mode']}")
        print(f"  Objects: {inventory['metadata']['total_objects_scanned']:,}")
        print(f"  Size: {inventory['metadata']['total_size_bytes'] / 1024**3:.2f} GB")
        print(f"  Duration: {inventory['metadata']['scan_duration_seconds']:.1f}s")
        return 0
    else:
        print("\n❌ Failed to read inventory")
        print("Options:")
        print("  1. Enable S3 Inventory in AWS Console")
        print("  2. Use --fallback-to-sample for sample-based scanning")
        return 1


if __name__ == "__main__":
    exit(main())
