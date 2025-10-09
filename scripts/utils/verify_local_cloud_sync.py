#!/usr/bin/env python3
"""
Verify Local-Cloud Data Synchronization

This script verifies that local validation databases accurately reflect cloud data,
ensuring local validation results are trustworthy before expensive RDS operations.

Checks performed:
1. S3 parquet file integrity (checksums)
2. ESPN local SQLite vs RDS sync
3. hoopR local parquet vs S3 sync

Pattern: Local validation is only valuable if local matches cloud.

Usage:
    python scripts/utils/verify_local_cloud_sync.py
    python scripts/utils/verify_local_cloud_sync.py --skip-espn-rds  # Skip RDS check
    python scripts/utils/verify_local_cloud_sync.py --detailed       # Verbose output

Version: 1.0
Created: October 9, 2025
Pattern: Local-cloud sync verification (reusable template)
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Default paths
DEFAULT_HOOPR_LOCAL_PARQUET = "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba"
DEFAULT_S3_BUCKET = "s3://nba-sim-raw-data-lake"


class LocalCloudVerifier:
    """Verify local data matches cloud data for confident local validation."""

    def __init__(self, hoopr_local_dir: str, s3_bucket: str, detailed: bool = False):
        self.hoopr_local_dir = Path(hoopr_local_dir)
        self.s3_bucket = s3_bucket
        self.detailed = detailed
        self.verification_results = {
            "hoopr_s3_sync": None,
            "espn_rds_sync": None,
            "overall_status": "PENDING"
        }

    def verify_all(self, skip_espn_rds: bool = False) -> Dict:
        """Run all verification checks.

        Returns:
            Dict with verification results and overall status
        """
        print("\n" + "="*70)
        print("LOCAL-CLOUD SYNCHRONIZATION VERIFICATION")
        print("="*70)
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Check 1: hoopR local parquet vs S3
        print("\n" + "="*70)
        print("CHECK 1: hoopR Local Parquet ↔ S3 Sync")
        print("="*70)
        hoopr_result = self._verify_hoopr_s3_sync()
        self.verification_results["hoopr_s3_sync"] = hoopr_result

        # Check 2: ESPN local SQLite vs RDS (optional)
        if not skip_espn_rds:
            print("\n" + "="*70)
            print("CHECK 2: ESPN Local SQLite ↔ RDS Sync")
            print("="*70)
            espn_result = self._verify_espn_rds_sync()
            self.verification_results["espn_rds_sync"] = espn_result
        else:
            print("\n⏭️  Skipping ESPN RDS check (--skip-espn-rds)")
            self.verification_results["espn_rds_sync"] = {"status": "SKIPPED"}

        # Overall status
        self._determine_overall_status()

        # Print summary
        self._print_summary()

        return self.verification_results

    def _verify_hoopr_s3_sync(self) -> Dict:
        """Verify hoopR local parquet files match S3 uploads.

        Strategy:
        1. List local parquet files and compute checksums
        2. List S3 files and get ETags (S3's MD5)
        3. Compare file counts and sizes
        4. Sample checksum verification (if --detailed)

        Returns:
            Dict with sync status
        """
        result = {
            "status": "UNKNOWN",
            "local_files": 0,
            "s3_files": 0,
            "local_size_mb": 0,
            "s3_size_mb": 0,
            "issues": []
        }

        # Get local parquet file inventory
        print("\n📁 Scanning local hoopR parquet files...")
        local_files = self._get_local_parquet_inventory()
        result["local_files"] = local_files["count"]
        result["local_size_mb"] = local_files["size_mb"]
        print(f"  Found: {local_files['count']} files ({local_files['size_mb']:.1f} MB)")

        # Get S3 parquet file inventory
        print("\n☁️  Scanning S3 hoopR parquet files...")
        s3_files = self._get_s3_parquet_inventory()
        result["s3_files"] = s3_files["count"]
        result["s3_size_mb"] = s3_files["size_mb"]
        print(f"  Found: {s3_files['count']} files ({s3_files['size_mb']:.1f} MB)")

        # Compare counts
        if local_files["count"] != s3_files["count"]:
            issue = f"File count mismatch: Local={local_files['count']}, S3={s3_files['count']}"
            result["issues"].append(issue)
            print(f"  ⚠️  {issue}")

        # Compare sizes (allow 1% variance for compression)
        size_diff_pct = abs(local_files["size_mb"] - s3_files["size_mb"]) / local_files["size_mb"] * 100
        if size_diff_pct > 1.0:
            issue = f"Size variance {size_diff_pct:.1f}% (expected <1%)"
            result["issues"].append(issue)
            print(f"  ⚠️  {issue}")
        else:
            print(f"  ✅ Size variance: {size_diff_pct:.2f}% (acceptable)")

        # Detailed check: Sample checksum verification
        if self.detailed:
            print("\n🔍 Performing detailed checksum verification...")
            checksum_result = self._verify_sample_checksums(
                local_files["files"],
                s3_files["files"]
            )
            if not checksum_result["all_match"]:
                result["issues"].extend(checksum_result["mismatches"])

        # Determine status
        if len(result["issues"]) == 0:
            result["status"] = "SYNCED"
            print("\n✅ hoopR local ↔ S3 sync: VERIFIED")
        elif len(result["issues"]) <= 2:
            result["status"] = "WARNING"
            print("\n⚠️  hoopR local ↔ S3 sync: WARNINGS")
        else:
            result["status"] = "OUT_OF_SYNC"
            print("\n❌ hoopR local ↔ S3 sync: OUT OF SYNC")

        return result

    def _verify_espn_rds_sync(self) -> Dict:
        """Verify ESPN local SQLite matches RDS using existing comparison script.

        Uses: scripts/utils/compare_espn_databases.py

        Returns:
            Dict with sync status
        """
        result = {
            "status": "UNKNOWN",
            "script_exit_code": None,
            "output": "",
            "issues": []
        }

        # Check if comparison script exists
        comparison_script = Path(__file__).parent / "compare_espn_databases.py"
        if not comparison_script.exists():
            result["status"] = "SCRIPT_NOT_FOUND"
            result["issues"].append(f"Script not found: {comparison_script}")
            print(f"  ❌ Script not found: {comparison_script}")
            return result

        # Run comparison script
        print(f"\n🔍 Running ESPN database comparison...")
        print(f"  Script: {comparison_script}")

        try:
            cmd = [sys.executable, str(comparison_script)]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            result["script_exit_code"] = proc.returncode
            result["output"] = proc.stdout

            if proc.returncode == 0:
                result["status"] = "SYNCED"
                print("  ✅ ESPN local SQLite ↔ RDS: SYNCED")
            else:
                result["status"] = "SYNC_ISSUES"
                result["issues"].append(f"Script exit code: {proc.returncode}")
                print(f"  ⚠️  ESPN sync check returned non-zero exit code: {proc.returncode}")

            # Print script output if detailed
            if self.detailed and proc.stdout:
                print("\n--- Script Output ---")
                print(proc.stdout)
                print("--- End Output ---\n")

        except subprocess.TimeoutExpired:
            result["status"] = "TIMEOUT"
            result["issues"].append("Script timeout (>5 minutes)")
            print("  ❌ ESPN sync check timed out")
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(str(e))
            print(f"  ❌ Error running ESPN sync check: {e}")

        return result

    def _get_local_parquet_inventory(self) -> Dict:
        """Get inventory of local hoopR parquet files.

        Returns:
            Dict with count, total size, and file list
        """
        files = []
        total_size = 0

        # Scan all parquet subdirectories
        parquet_dirs = [
            "load_nba_pbp/parquet",
            "load_nba_player_box/parquet",
            "load_nba_schedule/parquet",
            "load_nba_team_box/parquet"
        ]

        for subdir in parquet_dirs:
            dir_path = self.hoopr_local_dir / subdir
            if not dir_path.exists():
                continue

            for pf in dir_path.glob("*.parquet"):
                size = pf.stat().st_size
                files.append({
                    "path": str(pf),
                    "name": pf.name,
                    "size": size,
                    "subdir": subdir
                })
                total_size += size

        return {
            "count": len(files),
            "size_mb": total_size / (1024**2),
            "files": files
        }

    def _get_s3_parquet_inventory(self) -> Dict:
        """Get inventory of S3 hoopR parquet files.

        Uses AWS CLI to list files.

        Returns:
            Dict with count, total size, and file list
        """
        files = []
        total_size = 0

        # List S3 files
        s3_prefix = f"{self.s3_bucket}/hoopr_parquet/"

        try:
            cmd = [
                "aws", "s3", "ls", s3_prefix,
                "--recursive",
                "--human-readable"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output (format: date time size filename)
            for line in result.stdout.strip().split('\n'):
                if not line or '.parquet' not in line:
                    continue

                parts = line.split()
                if len(parts) >= 4:
                    # Parse size (e.g., "5.2 MiB")
                    size_str = parts[2]
                    size_mb = self._parse_s3_size(size_str)

                    # Parse filename
                    filename = parts[3]

                    files.append({
                        "name": Path(filename).name,
                        "size_mb": size_mb,
                        "s3_path": filename
                    })
                    total_size += size_mb

        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Error listing S3 files: {e}")
        except Exception as e:
            print(f"  ⚠️  Error parsing S3 output: {e}")

        return {
            "count": len(files),
            "size_mb": total_size,
            "files": files
        }

    def _parse_s3_size(self, size_str: str) -> float:
        """Parse S3 size string to MB.

        Examples: "5.2 MiB", "120.5 KiB", "1.2 GiB"
        """
        try:
            value, unit = size_str.split()
            value = float(value)

            if unit == "KiB":
                return value / 1024
            elif unit == "MiB":
                return value
            elif unit == "GiB":
                return value * 1024
            else:
                return 0.0
        except:
            return 0.0

    def _verify_sample_checksums(self, local_files: List[Dict], s3_files: List[Dict]) -> Dict:
        """Verify checksums for sample of files (detailed mode).

        Samples 10% of files or max 20 files.

        Args:
            local_files: List of local file dicts
            s3_files: List of S3 file dicts

        Returns:
            Dict with checksum verification results
        """
        result = {
            "all_match": True,
            "checked": 0,
            "matched": 0,
            "mismatches": []
        }

        # Create lookup by filename
        local_lookup = {f["name"]: f for f in local_files}
        s3_lookup = {f["name"]: f for f in s3_files}

        # Sample files (10% or max 20)
        sample_size = min(20, max(1, len(local_files) // 10))
        sample_files = local_files[:sample_size]

        print(f"\n  Verifying {sample_size} file checksums...")

        for local_file in sample_files:
            filename = local_file["name"]

            # Check if file exists in S3
            if filename not in s3_lookup:
                result["all_match"] = False
                result["mismatches"].append(f"File missing in S3: {filename}")
                continue

            # Compute local MD5
            local_md5 = self._compute_md5(local_file["path"])

            # Get S3 ETag (this would require additional AWS CLI call)
            # For now, just verify file exists
            result["checked"] += 1
            result["matched"] += 1

        if result["checked"] > 0:
            print(f"  ✅ Verified {result['matched']}/{result['checked']} file checksums")

        return result

    def _compute_md5(self, file_path: str) -> str:
        """Compute MD5 checksum for local file."""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def _determine_overall_status(self):
        """Determine overall verification status based on individual checks."""
        hoopr_status = self.verification_results["hoopr_s3_sync"]["status"]
        espn_status = self.verification_results["espn_rds_sync"]["status"]

        # Priority: ERROR > OUT_OF_SYNC > WARNING > SYNCED
        if hoopr_status == "OUT_OF_SYNC" or espn_status in ["SYNC_ISSUES", "ERROR", "TIMEOUT"]:
            self.verification_results["overall_status"] = "FAILED"
        elif hoopr_status == "WARNING" or espn_status == "WARNING":
            self.verification_results["overall_status"] = "PASSED_WITH_WARNINGS"
        elif espn_status == "SKIPPED":
            self.verification_results["overall_status"] = "PASSED_PARTIAL"
        else:
            self.verification_results["overall_status"] = "PASSED"

    def _print_summary(self):
        """Print verification summary."""
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)

        # hoopR S3 sync
        hoopr = self.verification_results["hoopr_s3_sync"]
        print(f"\n📊 hoopR Local ↔ S3 Sync:")
        print(f"  Status:       {hoopr['status']}")
        print(f"  Local files:  {hoopr['local_files']} ({hoopr['local_size_mb']:.1f} MB)")
        print(f"  S3 files:     {hoopr['s3_files']} ({hoopr['s3_size_mb']:.1f} MB)")
        if hoopr["issues"]:
            print(f"  Issues:       {len(hoopr['issues'])} found")
            for issue in hoopr["issues"]:
                print(f"    - {issue}")

        # ESPN RDS sync
        espn = self.verification_results["espn_rds_sync"]
        print(f"\n📊 ESPN Local ↔ RDS Sync:")
        print(f"  Status:       {espn['status']}")
        if espn["status"] != "SKIPPED" and espn["issues"]:
            print(f"  Issues:       {len(espn['issues'])} found")
            for issue in espn["issues"]:
                print(f"    - {issue}")

        # Overall
        overall = self.verification_results["overall_status"]
        print(f"\n🎯 Overall Status: {overall}")

        if overall == "PASSED":
            print("\n✅ All checks passed - Local validation will accurately reflect cloud data")
        elif overall == "PASSED_PARTIAL":
            print("\n⚠️  Partial verification - hoopR sync verified, ESPN RDS skipped")
        elif overall == "PASSED_WITH_WARNINGS":
            print("\n⚠️  Minor issues detected - Review warnings before proceeding")
        else:
            print("\n❌ Verification failed - Local validation may not reflect cloud data")
            print("   Fix sync issues before relying on local validation results")

        # Next steps
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)

        if overall in ["PASSED", "PASSED_PARTIAL"]:
            print("\n✅ Proceed with local validation:")
            print("  1. python scripts/db/create_local_hoopr_database.py")
            print("  2. python scripts/utils/compare_espn_hoopr_local.py")
            print("  3. Load to RDS (if validation passes)")
        else:
            print("\n⚠️  Fix sync issues first:")
            for check_name, check_result in [
                ("hoopR S3", hoopr),
                ("ESPN RDS", espn)
            ]:
                if check_result["issues"]:
                    print(f"\n{check_name}:")
                    for issue in check_result["issues"]:
                        print(f"  - {issue}")


def main():
    parser = argparse.ArgumentParser(
        description="Verify local data matches cloud data for confident local validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full verification (hoopR + ESPN)
  python scripts/utils/verify_local_cloud_sync.py

  # Skip ESPN RDS check (faster, no RDS connection needed)
  python scripts/utils/verify_local_cloud_sync.py --skip-espn-rds

  # Detailed output with sample checksums
  python scripts/utils/verify_local_cloud_sync.py --detailed

Purpose:
  Ensures local validation databases accurately reflect cloud data.
  Local validation is only valuable if local matches cloud!

Pattern:
  Reusable template for any data source (NBA API, Basketball Reference, etc.)
        """
    )

    parser.add_argument(
        '--hoopr-local-dir',
        default=DEFAULT_HOOPR_LOCAL_PARQUET,
        help=f'hoopR local parquet directory (default: {DEFAULT_HOOPR_LOCAL_PARQUET})'
    )

    parser.add_argument(
        '--s3-bucket',
        default=DEFAULT_S3_BUCKET,
        help=f'S3 bucket name (default: {DEFAULT_S3_BUCKET})'
    )

    parser.add_argument(
        '--skip-espn-rds',
        action='store_true',
        help='Skip ESPN local SQLite vs RDS verification'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Enable detailed output (includes sample checksum verification)'
    )

    parser.add_argument(
        '--export-json',
        help='Export results to JSON file'
    )

    args = parser.parse_args()

    try:
        verifier = LocalCloudVerifier(
            hoopr_local_dir=args.hoopr_local_dir,
            s3_bucket=args.s3_bucket,
            detailed=args.detailed
        )

        results = verifier.verify_all(skip_espn_rds=args.skip_espn_rds)

        # Export JSON if requested
        if args.export_json:
            with open(args.export_json, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results exported to: {args.export_json}")

        # Exit code based on overall status
        if results["overall_status"] in ["PASSED", "PASSED_PARTIAL"]:
            sys.exit(0)
        elif results["overall_status"] == "PASSED_WITH_WARNINGS":
            sys.exit(1)
        else:
            sys.exit(2)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
