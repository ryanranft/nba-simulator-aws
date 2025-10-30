#!/usr/bin/env python3
"""
System State Snapshot Generator

Purpose: Generate comprehensive JSON snapshot of database and system state
Usage: python3 scripts/backup/generate_system_snapshot.py
Author: Claude Code (NBA Simulator Project)
Date: October 30, 2025
"""

import json
import os
import subprocess  # nosec B404 - Required for AWS CLI calls
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import database config
from nba_simulator.config.database import DatabaseConfig

# Try to import psycopg2
try:
    import psycopg2

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("Warning: psycopg2 not available, database queries will be skipped")

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


def get_database_state() -> Dict[str, Any]:
    """Get database table counts and sizes."""
    if not HAS_PSYCOPG2:
        return {"error": "psycopg2 not available"}

    # Load credentials
    credentials_file = "/Users/ryanranft/nba-sim-credentials.env"
    if not os.path.exists(credentials_file):
        return {"error": "Credentials file not found"}

    # Load environment variables
    with open(credentials_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

    # Get config
    db_config = DatabaseConfig.from_env()

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
        )
        cursor = conn.cursor()

        # Get table counts
        cursor.execute(
            """
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY tablename
        """
        )
        tables = cursor.fetchall()

        table_data = {}
        total_rows = 0

        for schema, table in tables:
            full_table = f"{schema}.{table}"
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {full_table}")  # nosec B608
                count = cursor.fetchone()[0]
                total_rows += count

                # Get table size
                cursor.execute(  # nosec B608
                    f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{full_table}'))
                """
                )
                size = cursor.fetchone()[0]

                table_data[table] = {"rows": count, "size": size}
            except Exception as e:
                table_data[table] = {"rows": 0, "size": "N/A", "error": str(e)}

        # Get database size
        cursor.execute(
            f"""
            SELECT pg_size_pretty(pg_database_size('{db_config.database}'))
        """
        )
        db_size = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "database": db_config.database,
            "host": db_config.host,
            "total_tables": len(tables),
            "total_rows": total_rows,
            "database_size": db_size,
            "tables": table_data,
        }

    except Exception as e:
        return {"error": str(e)}


def get_s3_state() -> Dict[str, Any]:
    """Get S3 bucket state."""
    bucket = "nba-sim-raw-data-lake"

    try:
        # Get object count and size
        result = (
            subprocess.run(  # nosec B603, B607 - AWS CLI call with hardcoded command
                [
                    "aws",
                    "s3",
                    "ls",
                    f"s3://{bucket}",
                    "--recursive",
                    "--summarize",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        )

        total_objects = 0
        total_size = 0

        for line in result.stdout.split("\n"):
            if "Total Objects:" in line:
                total_objects = int(line.split(":")[1].strip())
            elif "Total Size:" in line:
                total_size = int(line.split(":")[1].strip())

        # Convert size to GB
        size_gb = total_size / (1024**3) if total_size > 0 else 0

        # Get directory counts
        directories = {}
        dir_result = subprocess.run(  # nosec B603, B607 - AWS CLI call
            ["aws", "s3", "ls", f"s3://{bucket}/"],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in dir_result.stdout.split("\n"):
            if "PRE" in line:
                dir_name = line.split("PRE")[1].strip().rstrip("/")
                directories[dir_name] = {}

        return {
            "bucket": bucket,
            "total_objects": total_objects,
            "total_size_bytes": total_size,
            "total_size_gb": round(size_gb, 2),
            "directories": list(directories.keys()),
        }

    except Exception as e:
        return {"error": str(e)}


def get_dims_metrics() -> Dict[str, Any]:
    """Get DIMS metrics from inventory file."""
    metrics_file = Path("/Users/ryanranft/nba-simulator-aws/inventory/metrics.yaml")

    if not metrics_file.exists():
        return {"error": "metrics.yaml not found"}

    try:
        import yaml

        with open(metrics_file) as f:
            metrics = yaml.safe_load(f)

        return {
            "last_updated": metrics.get("last_updated"),
            "s3": {
                "objects": metrics.get("s3", {}).get("object_count"),
                "size_gb": metrics.get("s3", {}).get("size_gb"),
            },
            "database": {
                "games": metrics.get("database", {})
                .get("games", {})
                .get("record_count"),
                "play_by_play": metrics.get("database", {})
                .get("play_by_play", {})
                .get("record_count"),
                "temporal_events": metrics.get("database", {})
                .get("temporal_events", {})
                .get("record_count"),
            },
        }

    except ImportError:
        return {"error": "PyYAML not available"}
    except Exception as e:
        return {"error": str(e)}


def main():
    log_info("Generating system state snapshot...")

    # Configuration
    BACKUP_DIR = Path("/Users/ryanranft/nba-simulator-aws/backups")
    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
    SNAPSHOT_FILE = BACKUP_DIR / f"system_state_snapshot_{TIMESTAMP}.json"

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Collect system state
    snapshot = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "snapshot_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project": "NBA Simulator AWS",
            "purpose": "Pre-refactoring system state snapshot",
        },
        "database": {},
        "s3": {},
        "dims_metrics": {},
        "git": {},
    }

    # Get database state
    log_info("Querying database state...")
    snapshot["database"] = get_database_state()

    if "error" not in snapshot["database"]:
        log_success(
            f"Database: {snapshot['database']['total_tables']} tables, {snapshot['database']['total_rows']:,} total rows"
        )
    else:
        log_error(f"Database query failed: {snapshot['database']['error']}")

    # Get S3 state
    log_info("Querying S3 state...")
    snapshot["s3"] = get_s3_state()

    if "error" not in snapshot["s3"]:
        log_success(
            f"S3: {snapshot['s3']['total_objects']:,} objects, {snapshot['s3']['total_size_gb']} GB"
        )
    else:
        log_error(f"S3 query failed: {snapshot['s3']['error']}")

    # Get DIMS metrics
    log_info("Loading DIMS metrics...")
    snapshot["dims_metrics"] = get_dims_metrics()

    if "error" not in snapshot["dims_metrics"]:
        log_success("DIMS metrics loaded")
    else:
        log_error(f"DIMS metrics failed: {snapshot['dims_metrics']['error']}")

    # Get git info
    log_info("Getting git information...")
    try:
        result = subprocess.run(  # nosec B603, B607 - git command
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        commit_hash = result.stdout.strip()

        result = subprocess.run(  # nosec B603, B607 - git command
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            check=True,
        )
        describe = result.stdout.strip()

        result = subprocess.run(  # nosec B603, B607 - git command
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()

        snapshot["git"] = {
            "commit_hash": commit_hash,
            "describe": describe,
            "branch": branch,
        }
        log_success(f"Git: {branch} @ {commit_hash[:8]}")

    except Exception as e:
        snapshot["git"] = {"error": str(e)}
        log_error(f"Git info failed: {e}")

    # Save snapshot
    log_info(f"Saving snapshot to {SNAPSHOT_FILE}...")
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)

    log_success("Snapshot saved")

    # Upload to S3
    log_info("Uploading snapshot to S3...")
    try:
        subprocess.run(  # nosec B603, B607 - AWS CLI call
            [
                "aws",
                "s3",
                "cp",
                str(SNAPSHOT_FILE),
                f"s3://nba-sim-raw-data-lake/backups/snapshots/system_state_snapshot_{TIMESTAMP}.json",
                "--storage-class",
                "STANDARD_IA",
            ],
            check=True,
        )
        log_success("Snapshot uploaded to S3")
    except Exception as e:
        log_error(f"S3 upload failed: {e}")

    # Generate checksum
    log_info("Generating checksum...")
    try:
        subprocess.run(  # nosec B603, B607 - shasum command
            ["shasum", "-a", "256", str(SNAPSHOT_FILE)],
            stdout=open(f"{SNAPSHOT_FILE}.sha256", "w"),
            check=True,
        )
        log_success("Checksum generated")
    except Exception as e:
        log_error(f"Checksum generation failed: {e}")

    # Print summary
    print(f"\n{'=' * 80}")
    print("# SYSTEM STATE SNAPSHOT COMPLETE")
    print(f"{'=' * 80}\n")
    print(f"Timestamp:     {snapshot['metadata']['snapshot_date']}")
    print(f"Snapshot File: {SNAPSHOT_FILE}")
    print(f"File Size:     {SNAPSHOT_FILE.stat().st_size / 1024:.2f} KB\n")

    if "error" not in snapshot["database"]:
        print("Database:")
        print(f"  Tables:      {snapshot['database']['total_tables']}")
        print(f"  Total Rows:  {snapshot['database']['total_rows']:,}")
        print(f"  Size:        {snapshot['database']['database_size']}\n")

    if "error" not in snapshot["s3"]:
        print("S3:")
        print(f"  Objects:     {snapshot['s3']['total_objects']:,}")
        print(f"  Size:        {snapshot['s3']['total_size_gb']} GB\n")

    if "error" not in snapshot["git"]:
        print("Git:")
        print(f"  Branch:      {snapshot['git']['branch']}")
        print(f"  Commit:      {snapshot['git']['commit_hash'][:8]}")
        print(f"  Tag:         {snapshot['git']['describe']}\n")

    print(f"{'=' * 80}\n")

    log_success("System state snapshot generation complete!")


if __name__ == "__main__":
    main()
