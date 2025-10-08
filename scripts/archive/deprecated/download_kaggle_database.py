#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE ⚠️

This script has been superseded by download_kaggle_basketball.py

DEPRECATED ON: October 8, 2025
REASON: Replaced by download_kaggle_basketball.py with better error handling
ACTIVE VERSION: scripts/etl/download_kaggle_basketball.py

---

Kaggle Basketball Database Downloader

Downloads the comprehensive NBA database from Kaggle:
https://www.kaggle.com/datasets/wyattowalsh/basketball/data

This database contains historical NBA data from 1946-present in SQLite format.

Prerequisites:
1. Kaggle account
2. Kaggle API credentials (~/.kaggle/kaggle.json)
3. Install kaggle package: pip install kaggle

Setup:
1. Create Kaggle account: https://www.kaggle.com/
2. Go to Account settings → API → Create New API Token
3. Save kaggle.json to ~/.kaggle/kaggle.json
4. chmod 600 ~/.kaggle/kaggle.json

Usage:
    python scripts/etl/download_kaggle_database.py
    python scripts/etl/download_kaggle_database.py --output-dir /tmp/kaggle_nba
    python scripts/etl/download_kaggle_database.py --extract-to-s3
"""

import argparse
import sys
from pathlib import Path
import os
import sqlite3
import json

try:
    from kaggle.api.kaggle_api_extended import KaggleApi
    HAS_KAGGLE = True
except ImportError:
    HAS_KAGGLE = False
    print("❌ Kaggle package not installed")
    print("Install with: pip install kaggle")

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class KaggleNBADownloader:
    """Download and process Kaggle NBA database"""

    DATASET_NAME = "wyattowalsh/basketball"

    def __init__(self, output_dir="/tmp/kaggle_nba", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None

        # Initialize Kaggle API
        if HAS_KAGGLE:
            self.api = KaggleApi()
            self.api.authenticate()
        else:
            self.api = None

    def download_dataset(self):
        """Download Kaggle dataset"""
        if not self.api:
            print("❌ Kaggle API not available")
            return False

        print(f"📥 Downloading Kaggle dataset: {self.DATASET_NAME}")
        print(f"💾 Output directory: {self.output_dir}")
        print()

        try:
            # Download and unzip dataset
            self.api.dataset_download_files(
                self.DATASET_NAME,
                path=str(self.output_dir),
                unzip=True
            )

            print(f"✅ Download complete!")
            return True

        except Exception as e:
            print(f"❌ Error downloading dataset: {e}")
            return False

    def list_database_files(self):
        """List all database files in output directory"""
        db_files = list(self.output_dir.glob("*.db")) + list(self.output_dir.glob("*.sqlite"))

        if not db_files:
            print(f"⚠️  No database files found in {self.output_dir}")
            return []

        print(f"\n📁 Found {len(db_files)} database file(s):")
        for db_file in db_files:
            size_mb = db_file.stat().st_size / (1024 * 1024)
            print(f"  - {db_file.name} ({size_mb:.1f} MB)")

        return db_files

    def inspect_database(self, db_path):
        """Inspect database schema and contents"""
        print(f"\n🔍 Inspecting database: {db_path.name}")
        print("="*60)

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            print(f"\n📊 Found {len(tables)} tables:")
            print()

            for (table_name,) in tables:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                print(f"Table: {table_name}")
                print(f"  Rows: {row_count:,}")
                print(f"  Columns: {len(columns)}")
                print(f"  Schema:")
                for col in columns[:5]:  # Show first 5 columns
                    col_id, col_name, col_type, _, _, _ = col
                    print(f"    - {col_name} ({col_type})")
                if len(columns) > 5:
                    print(f"    ... and {len(columns) - 5} more columns")
                print()

            conn.close()

        except Exception as e:
            print(f"❌ Error inspecting database: {e}")

    def extract_table_to_json(self, db_path, table_name, output_file=None, upload_to_s3=False):
        """
        Extract table data to JSON

        Args:
            db_path: Path to SQLite database
            table_name: Name of table to extract
            output_file: Output JSON file path (optional)
            upload_to_s3: Whether to upload to S3
        """
        if output_file is None:
            output_file = self.output_dir / f"{table_name}.json"

        print(f"\n📤 Extracting table: {table_name}")

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name

            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")

            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

            # Save to JSON
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"  ✅ Saved {len(data):,} rows to {output_file}")

            # Upload to S3
            if upload_to_s3 and self.s3_client:
                s3_key = f"kaggle_nba/{table_name}.json"
                self.s3_client.upload_file(str(output_file), self.s3_bucket, s3_key)
                print(f"  ✅ Uploaded to s3://{self.s3_bucket}/{s3_key}")

            conn.close()
            return True

        except Exception as e:
            print(f"  ❌ Error extracting table: {e}")
            return False

    def extract_all_tables(self, db_path, upload_to_s3=False):
        """Extract all tables from database to JSON"""
        print(f"\n📦 Extracting all tables from {db_path.name}")
        print("="*60)

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            conn.close()

            print(f"Found {len(tables)} tables to extract")
            print()

            success_count = 0
            for table in tables:
                if self.extract_table_to_json(db_path, table, upload_to_s3=upload_to_s3):
                    success_count += 1

            print()
            print("="*60)
            print(f"✅ Extracted {success_count}/{len(tables)} tables successfully")

        except Exception as e:
            print(f"❌ Error extracting tables: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download and extract Kaggle NBA database")
    parser.add_argument('--output-dir', default='/tmp/kaggle_nba', help='Local output directory')
    parser.add_argument('--download', action='store_true', help='Download dataset from Kaggle')
    parser.add_argument('--inspect', action='store_true', help='Inspect database schema')
    parser.add_argument('--extract', action='store_true', help='Extract tables to JSON')
    parser.add_argument('--extract-to-s3', action='store_true', help='Upload extracted JSON to S3')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake', help='S3 bucket name')
    parser.add_argument('--all', action='store_true', help='Download, inspect, and extract')

    args = parser.parse_args()

    # Check for Kaggle package
    if not HAS_KAGGLE:
        print("❌ Missing dependencies")
        print("Install with: pip install kaggle")
        print()
        print("Setup instructions:")
        print("1. Create Kaggle account: https://www.kaggle.com/")
        print("2. Go to Account → API → Create New API Token")
        print("3. Save kaggle.json to ~/.kaggle/kaggle.json")
        print("4. chmod 600 ~/.kaggle/kaggle.json")
        sys.exit(1)

    # Check for S3 dependencies
    if args.extract_to_s3 and not HAS_BOTO3:
        print("❌ boto3 required for S3 upload")
        print("Install with: pip install boto3")
        sys.exit(1)

    # Create downloader
    s3_bucket = args.s3_bucket if args.extract_to_s3 else None
    downloader = KaggleNBADownloader(output_dir=args.output_dir, s3_bucket=s3_bucket)

    # Run tasks
    if args.all or args.download:
        print("🚀 Starting Kaggle NBA database download")
        print()
        if not downloader.download_dataset():
            print("❌ Download failed")
            sys.exit(1)

    # Find database files
    db_files = downloader.list_database_files()
    if not db_files:
        print("❌ No database files found")
        print("Run with --download flag to download dataset first")
        sys.exit(1)

    # Use first database file
    db_path = db_files[0]

    if args.all or args.inspect:
        downloader.inspect_database(db_path)

    if args.all or args.extract or args.extract_to_s3:
        upload = args.extract_to_s3 or (args.all and args.extract_to_s3)
        downloader.extract_all_tables(db_path, upload_to_s3=upload)

    print()
    print("✅ Complete!")
    print(f"📁 Files saved to: {downloader.output_dir}")
    if s3_bucket:
        print(f"☁️  Files uploaded to s3://{s3_bucket}/kaggle_nba/")


if __name__ == '__main__':
    main()