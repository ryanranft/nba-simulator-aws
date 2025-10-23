#!/usr/bin/env python3
"""
S3 Inventory Scanner - ADCE Phase 2A MVP
Scans S3 bucket and creates structured inventory of current data

Features:
- Sample-based scanning for MVP (10% by default)
- Full scan support for Phase 2B
- Parse S3 paths to extract metadata
- Aggregate by source, season, data type
- Cache results for performance

Usage:
    # MVP: Sample 10% of files
    python scan_s3_inventory.py --sample-rate 0.1

    # Full scan
    python scan_s3_inventory.py --full

    # Dry run (no save)
    python scan_s3_inventory.py --dry-run
"""

import boto3
import json
import re
import random
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import argparse
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class S3InventoryScanner:
    """
    Scans S3 bucket to build inventory of current data

    MVP: Uses sampling for speed
    Phase 2B: Full scan with AWS S3 Inventory integration
    """

    def __init__(self, bucket_name, output_dir="inventory/cache", sample_rate=None):
        """
        Initialize S3 inventory scanner

        Args:
            bucket_name: S3 bucket to scan
            output_dir: Where to save inventory
            sample_rate: If set, sample this fraction of files (0.1 = 10%)
        """
        self.s3 = boto3.client("s3")
        self.bucket = bucket_name
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate

        logger.info(f"Initialized S3InventoryScanner for bucket: {bucket_name}")
        if sample_rate:
            logger.info(f"Sample mode: {sample_rate*100}% of files")
        else:
            logger.info("Full scan mode")

    def scan(self, prefix=None, dry_run=False):
        """
        Scan S3 and build inventory

        Args:
            prefix: Optional S3 prefix to limit scan
            dry_run: If True, don't save results

        Returns:
            dict: Structured inventory
        """
        logger.info("Starting S3 scan...")
        start_time = datetime.now()

        inventory = {
            "metadata": {
                "scan_timestamp": start_time.isoformat(),
                "bucket": self.bucket,
                "scan_mode": "sample" if self.sample_rate else "full",
                "sample_rate": self.sample_rate,
                "prefix": prefix,
                "total_objects_scanned": 0,
                "total_objects_kept": 0,
                "total_size_bytes": 0,
            },
            "by_source": defaultdict(
                lambda: {"count": 0, "total_size": 0, "files": []}
            ),
            "by_season": defaultdict(
                lambda: {"count": 0, "total_size": 0, "files": []}
            ),
            "by_type": defaultdict(lambda: {"count": 0, "total_size": 0, "files": []}),
            "files": [],
        }

        # Paginate through S3 objects
        paginator = self.s3.get_paginator("list_objects_v2")
        page_config = {"Bucket": self.bucket}
        if prefix:
            page_config["Prefix"] = prefix

        try:
            for page in paginator.paginate(**page_config):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    inventory["metadata"]["total_objects_scanned"] += 1

                    # Sample if configured (using standard random for non-security sampling)
                    if (
                        self.sample_rate
                        and random.random() > self.sample_rate  # nosec B311
                    ):
                        continue

                    key = obj["Key"]
                    size = obj["Size"]
                    modified = obj["LastModified"]

                    # Parse S3 path to extract metadata
                    metadata = self.parse_s3_path(key)
                    metadata["size_bytes"] = size
                    metadata["last_modified"] = modified.isoformat()
                    metadata["s3_key"] = key

                    # Add to inventory
                    inventory["files"].append(metadata)
                    inventory["metadata"]["total_objects_kept"] += 1
                    inventory["metadata"]["total_size_bytes"] += size

                    # Aggregate by source, season, type
                    if metadata["source"]:
                        self._add_to_index(
                            inventory["by_source"][metadata["source"]], metadata
                        )
                    if metadata["season"]:
                        self._add_to_index(
                            inventory["by_season"][metadata["season"]], metadata
                        )
                    if metadata["data_type"]:
                        self._add_to_index(
                            inventory["by_type"][metadata["data_type"]], metadata
                        )

                    # Progress logging
                    if inventory["metadata"]["total_objects_scanned"] % 10000 == 0:
                        logger.info(
                            f"Scanned {inventory['metadata']['total_objects_scanned']:,} objects "
                            f"({inventory['metadata']['total_objects_kept']:,} kept)"
                        )

        except Exception as e:
            logger.error(f"Error during S3 scan: {e}")
            raise

        # Convert defaultdict to regular dict for JSON serialization
        inventory["by_source"] = dict(inventory["by_source"])
        inventory["by_season"] = dict(inventory["by_season"])
        inventory["by_type"] = dict(inventory["by_type"])

        scan_duration = (datetime.now() - start_time).total_seconds()
        inventory["metadata"]["scan_duration_seconds"] = scan_duration

        logger.info(f"Scan complete in {scan_duration:.1f}s")
        logger.info(
            f"Total objects scanned: {inventory['metadata']['total_objects_scanned']:,}"
        )
        logger.info(
            f"Total objects kept: {inventory['metadata']['total_objects_kept']:,}"
        )
        logger.info(
            f"Total size: {inventory['metadata']['total_size_bytes'] / 1024**3:.2f} GB"
        )
        logger.info(f"Sources found: {list(inventory['by_source'].keys())}")
        logger.info(f"Seasons found: {list(inventory['by_season'].keys())}")

        return inventory

    def parse_s3_path(self, s3_key):
        """
        Extract metadata from S3 path

        Handles various path patterns:
        - nba_pbp/espn/2023-24/play_by_play_401579404.json
        - nba_box_score/espn/2023-24/box_score_401579404.json
        - basketball_ref/2022-23/advanced_202212010LAL.html
        - hoopr_parquet/2023-24_pbp.parquet
        - nba_schedule_json/2024-25/schedule.json

        Args:
            s3_key: S3 object key (path)

        Returns:
            dict: Extracted metadata
        """
        parts = s3_key.split("/")
        filename = parts[-1] if parts else s3_key

        metadata = {
            "source": None,
            "season": None,
            "data_type": None,
            "game_id": None,
            "player_id": None,
            "team_id": None,
        }

        # Identify source from path
        path_lower = s3_key.lower()
        if "espn" in path_lower:
            metadata["source"] = "espn"
        elif "basketball_ref" in path_lower or "bbref" in path_lower:
            metadata["source"] = "basketball_reference"
        elif "nba_api" in path_lower or "nba_stats" in path_lower:
            metadata["source"] = "nba_api"
        elif "hoopr" in path_lower:
            metadata["source"] = "hoopr"
        elif "kaggle" in path_lower:
            metadata["source"] = "kaggle"

        # Extract season (YYYY-YY pattern like 2023-24)
        season_match = re.search(r"(20\d{2}-\d{2})", s3_key)
        if season_match:
            metadata["season"] = season_match.group(1)

        # Extract data type from path/filename
        if "play_by_play" in path_lower or "pbp" in path_lower:
            metadata["data_type"] = "play_by_play"
        elif "box_score" in path_lower or "boxscore" in path_lower:
            metadata["data_type"] = "box_scores"
        elif "schedule" in path_lower:
            metadata["data_type"] = "schedule"
        elif "player" in path_lower:
            metadata["data_type"] = "player_stats"
        elif "team" in path_lower:
            metadata["data_type"] = "team_stats"
        elif "advanced" in path_lower:
            metadata["data_type"] = "advanced_stats"
        elif "tracking" in path_lower:
            metadata["data_type"] = "player_tracking"
        elif "dashboard" in path_lower:
            metadata["data_type"] = "team_dashboards"

        # Extract IDs from filename
        # Game ID: 401579404 or 202212010LAL (9+ digits or date pattern)
        game_id_match = re.search(r"(\d{9,}|20\d{6}[A-Z]{3})", filename)
        if game_id_match:
            metadata["game_id"] = game_id_match.group(1)

        # Player ID: player_2544.json
        player_id_match = re.search(r"player_?(\d+)", filename)
        if player_id_match:
            metadata["player_id"] = player_id_match.group(1)

        # Team ID: team_1610612747.json
        team_id_match = re.search(r"team_?(\d+)", filename)
        if team_id_match:
            metadata["team_id"] = team_id_match.group(1)

        return metadata

    def _add_to_index(self, index_dict, metadata):
        """Add metadata to aggregated index"""
        index_dict["count"] += 1
        index_dict["total_size"] += metadata.get("size_bytes", 0)
        index_dict["files"].append(metadata)

    def save_inventory(self, inventory, output_file="current_inventory.json"):
        """
        Save inventory to file

        Args:
            inventory: Inventory dict to save
            output_file: Filename (within output_dir)

        Returns:
            Path: Path to saved file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / output_file

        logger.info(f"Saving inventory to {output_path}")

        with open(output_path, "w") as f:
            json.dump(inventory, f, indent=2, default=str)

        logger.info(f"Inventory saved successfully")
        return output_path

    def load_inventory(self, input_file="current_inventory.json"):
        """
        Load previously saved inventory

        Args:
            input_file: Filename to load

        Returns:
            dict: Loaded inventory
        """
        input_path = self.output_dir / input_file

        if not input_path.exists():
            logger.warning(f"Inventory file not found: {input_path}")
            return None

        logger.info(f"Loading inventory from {input_path}")

        with open(input_path, "r") as f:
            inventory = json.load(f)

        logger.info("Inventory loaded successfully")
        return inventory


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Scan S3 bucket and create structured inventory"
    )
    parser.add_argument(
        "--bucket", default="nba-sim-raw-data-lake", help="S3 bucket name"
    )
    parser.add_argument("--prefix", help="S3 prefix to limit scan")
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=0.1,
        help="Sample rate (0.1 = 10%%, None = full scan)",
    )
    parser.add_argument(
        "--full", action="store_true", help="Full scan (disable sampling)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Scan but don't save results"
    )
    parser.add_argument(
        "--output", default="current_inventory.json", help="Output filename"
    )

    args = parser.parse_args()

    # Determine sample rate
    sample_rate = None if args.full else args.sample_rate

    # Initialize scanner
    scanner = S3InventoryScanner(bucket_name=args.bucket, sample_rate=sample_rate)

    # Run scan
    inventory = scanner.scan(prefix=args.prefix, dry_run=args.dry_run)

    # Save results
    if not args.dry_run:
        output_path = scanner.save_inventory(inventory, args.output)
        print(f"\n✅ Inventory saved: {output_path}")
    else:
        print("\n🔍 DRY RUN - Results not saved")

    # Print summary
    print(f"\n📊 Scan Summary:")
    print(f"  Objects scanned: {inventory['metadata']['total_objects_scanned']:,}")
    print(f"  Objects kept: {inventory['metadata']['total_objects_kept']:,}")
    print(f"  Total size: {inventory['metadata']['total_size_bytes'] / 1024**3:.2f} GB")
    print(f"  Duration: {inventory['metadata']['scan_duration_seconds']:.1f}s")
    print(f"  Sources: {len(inventory['by_source'])}")
    print(f"  Seasons: {len(inventory['by_season'])}")
    print(f"  Data types: {len(inventory['by_type'])}")


if __name__ == "__main__":
    main()
