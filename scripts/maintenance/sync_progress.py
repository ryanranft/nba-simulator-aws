#!/usr/bin/env python3
"""
scripts/maintenance/sync_progress.py

Synchronize PROGRESS.md with actual project state.

This script checks AWS resources, Git status, and file structure
to automatically update task statuses in PROGRESS.md.

Usage:
    python scripts/maintenance/sync_progress.py
    python scripts/maintenance/sync_progress.py --dry-run  # Preview changes
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class ProgressSync:
    def __init__(self, project_root="/Users/ryanranft/nba-simulator-aws"):
        self.project_root = Path(project_root)
        self.progress_file = self.project_root / "PROGRESS.md"
        self.changes = []

    def run_command(self, cmd):
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,  # nosec B602 - Required for AWS CLI pipe/redirect, commands are static
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip(), result.returncode
        except Exception as e:
            return f"Error: {e}", 1

    def check_s3_bucket(self):
        """Check if S3 bucket exists and has data"""
        cmd = "aws s3 ls s3://nba-sim-raw-data-lake/ 2>/dev/null"
        output, code = self.run_command(cmd)

        if code == 0 and output:
            # Count objects (checking for S3 count: 70,522 files)
            cmd = "aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize 2>/dev/null | grep 'Total Objects'"
            output, _ = self.run_command(cmd)
            if "70522" in output or "70,522" in output:
                return "complete"
        return "pending"

    def check_rds_status(self):
        """Check if RDS instance exists"""
        cmd = "aws rds describe-db-instances --db-instance-identifier nba-sim-db 2>/dev/null"
        output, code = self.run_command(cmd)

        if code == 0 and "DBInstanceStatus" in output:
            return "complete"
        return "pending"

    def check_glue_crawler(self):
        """Check if Glue crawler exists"""
        cmd = "aws glue get-crawler --name nba-data-crawler 2>/dev/null"
        output, code = self.run_command(cmd)

        if code == 0 and "Crawler" in output:
            return "complete"
        return "pending"

    def check_glue_etl_job(self):
        """Check if Glue ETL job exists"""
        cmd = "aws glue get-job --job-name nba-etl-job 2>/dev/null"
        output, code = self.run_command(cmd)

        if code == 0 and "Job" in output:
            return "complete"
        return "pending"

    def check_file_exists(self, filepath):
        """Check if a file exists in the project"""
        full_path = self.project_root / filepath
        return full_path.exists()

    def detect_phase_status(self):
        """Detect current phase based on AWS resources"""
        statuses = {
            "s3": self.check_s3_bucket(),
            "rds": self.check_rds_status(),
            "glue_crawler": self.check_glue_crawler(),
            "glue_etl": self.check_glue_etl_job(),
        }

        print("🔍 Resource Detection:")
        print(f"   S3 Data Lake: {statuses['s3']}")
        print(f"   RDS Database: {statuses['rds']}")
        print(f"   Glue Crawler: {statuses['glue_crawler']}")
        print(f"   Glue ETL Job: {statuses['glue_etl']}")
        print()

        return statuses

    def update_progress_status(self, phase_name, new_status):
        """Update a phase status in PROGRESS.md"""
        if not self.progress_file.exists():
            print(f"❌ {self.progress_file} not found")
            return

        content = self.progress_file.read_text()

        # Pattern to find phase status markers
        # Example: ### ✅ COMPLETED | ⏸️ PENDING | ⏳ IN PROGRESS
        pattern = rf"(### .* {re.escape(phase_name)}.*?)([✅⏸️⏳])"

        status_emoji = {"complete": "✅", "pending": "⏸️", "in_progress": "⏳"}

        new_emoji = status_emoji.get(new_status, "⏸️")

        new_content, count = re.subn(pattern, rf"\1{new_emoji}", content)

        if count > 0:
            self.changes.append(f"Updated {phase_name}: {new_status}")
            return new_content

        return content

    def generate_summary(self):
        """Generate project summary statistics"""
        print("📊 Project Summary:")
        print("=" * 60)

        # Git stats
        cmd = "git rev-list --count HEAD 2>/dev/null"
        commit_count, _ = self.run_command(cmd)
        print(f"Git commits: {commit_count}")

        # Documentation stats
        doc_count = len(list((self.project_root / "docs").rglob("*.md")))
        print(f"Documentation files: {doc_count}")

        # ADR count
        adr_count = len(list((self.project_root / "docs" / "adr").glob("[0-9]*.md")))
        print(f"Architecture Decision Records: {adr_count}")

        # Python files
        py_count = len(list(self.project_root.rglob("*.py")))
        print(f"Python files: {py_count}")

        # Test files
        test_count = (
            len(list((self.project_root / "tests").rglob("test_*.py")))
            if (self.project_root / "tests").exists()
            else 0
        )
        print(f"Test files: {test_count}")

        print("=" * 60)
        print()

    def run(self, dry_run=False):
        """Main execution"""
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("PROGRESS.md Synchronization")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

        # Detect current state
        statuses = self.detect_phase_status()

        # Generate summary
        self.generate_summary()

        # Suggest updates based on detected state
        print("💡 Suggested Updates:")

        if statuses["s3"] == "complete":
            print("   ✅ Phase 1 (S3 Data Lake) appears complete")
        else:
            print("   ⏸️ Phase 1 (S3 Data Lake) not complete")

        if statuses["glue_crawler"] == "complete":
            print("   ✅ 2.0001 (Glue Crawler) appears complete")
        else:
            print("   ⏸️ 2.0001 (Glue Crawler) pending")

        if statuses["rds"] == "complete":
            print("   ✅ 3.0001 (RDS Database) appears complete")
        else:
            print("   ⏸️ 3.0001 (RDS Database) pending")

        if statuses["glue_etl"] == "complete":
            print("   ✅ 2.0002 (Glue ETL Job) appears complete")
        else:
            print("   ⏸️ 2.0002 (Glue ETL Job) pending")

        print()

        if dry_run:
            print("🔍 Dry-run mode: No changes made")
            print("   Run without --dry-run to apply updates")
        else:
            print("💾 To apply updates, manually edit PROGRESS.md")
            print("   This script provides detection only for now")

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ Sync complete!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    sync = ProgressSync()
    sync.run(dry_run=dry_run)
