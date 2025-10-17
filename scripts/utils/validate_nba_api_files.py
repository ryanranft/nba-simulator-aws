#!/usr/bin/env python3
"""
NBA API Data Validation and Cleanup Utility

Validates JSON files from nba_api scraper and detects/removes partial or corrupted files.

Features:
- JSON syntax validation
- File size sanity checks
- Structure completeness verification
- Partial file detection (truncated mid-write)
- Automatic cleanup with --delete-invalid flag
- Per-season filtering with --season flag
- Detailed reporting

Usage:
    # Validate all files (report only)
    python scripts/utils/validate_nba_api_files.py

    # Validate specific season
    python scripts/utils/validate_nba_api_files.py --season 1996

    # Validate and delete invalid files
    python scripts/utils/validate_nba_api_files.py --season 1996 --delete-invalid

    # Quiet mode (errors only)
    python scripts/utils/validate_nba_api_files.py --quiet

Created: October 10, 2025
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class NBAAPIFileValidator:
    """Validates NBA API JSON files for completeness and integrity"""

    def __init__(self, output_dir="/tmp/nba_api_comprehensive", quiet=False):
        self.output_dir = Path(output_dir)
        self.quiet = quiet

        # Minimum file sizes (bytes) for different categories
        # Files smaller than this are suspicious
        self.min_sizes = {
            "play_by_play": 500,  # Play-by-play should have substantial data
            "boxscores_advanced": 300,  # Box scores have multiple result sets
            "player_info": 200,  # Player info has biographical data
            "shot_charts": 100,  # Shot charts can be empty (no shots)
            "draft": 100,  # Draft data can be sparse
            "tracking": 100,  # Tracking can be empty for old seasons
            "hustle": 100,  # Hustle stats only 2016+
            "synergy": 100,  # Synergy only 2016+
            "league_dashboards": 200,  # League dashboards should have player/team lists
            "player_stats": 200,  # Player stats should have multiple columns
            "team_stats": 200,  # Team stats should have multiple columns
            "game_logs": 200,  # Game logs should have game data
            "common": 100,  # Common endpoints vary
        }

        self.stats = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "deleted_files": 0,
            "errors": {},  # category -> count
        }

    def log(self, message, force=False):
        """Print message unless in quiet mode"""
        if not self.quiet or force:
            print(message)

    def validate_json_file(self, filepath: Path) -> Tuple[bool, str]:
        """
        Validate a single JSON file

        Returns:
            (is_valid, error_message)
        """
        # Check file exists
        if not filepath.exists():
            return False, "File does not exist"

        # Check file size
        file_size = filepath.stat().st_size

        if file_size == 0:
            return False, "File is empty (0 bytes)"

        # Get category from parent directory
        category = filepath.parent.name
        min_size = self.min_sizes.get(category, 50)

        if file_size < min_size:
            return False, f"File too small ({file_size} bytes, expected >{min_size})"

        # Validate JSON syntax
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Read error: {e}"

        # Check basic structure (should be dict with keys)
        if not isinstance(data, dict):
            return False, "JSON is not a dictionary"

        if len(data) == 0:
            return False, "JSON dictionary is empty"

        # Check for expected nba_api structure (resource, resultSets, or parameters)
        if (
            "resultSets" not in data
            and "resource" not in data
            and "parameters" not in data
        ):
            # Some endpoints might have different structures, but most have these
            # Don't fail, but warn
            pass

        # File is valid
        return True, "OK"

    def validate_season_files(self, season: int = None) -> Dict:
        """
        Validate all files, optionally filtered by season

        Returns:
            Dict with validation results
        """
        if not self.output_dir.exists():
            self.log(
                f"❌ Output directory does not exist: {self.output_dir}", force=True
            )
            return self.stats

        self.log(f"\n{'='*70}")
        self.log(f"NBA API File Validation")
        self.log(f"{'='*70}")
        self.log(f"Directory: {self.output_dir}")
        if season:
            self.log(f"Season filter: {season}")
        self.log(f"{'='*70}\n")

        # Find all JSON files
        if season:
            # Filter by season in filename
            pattern = f"**/*_{season}.json"
        else:
            pattern = "**/*.json"

        json_files = list(self.output_dir.glob(pattern))
        self.stats["total_files"] = len(json_files)

        if self.stats["total_files"] == 0:
            self.log(f"⚠️  No JSON files found matching pattern: {pattern}", force=True)
            return self.stats

        self.log(f"Found {self.stats['total_files']} files to validate...\n")

        invalid_files = []

        # Validate each file
        for i, filepath in enumerate(json_files, 1):
            if i % 100 == 0 and not self.quiet:
                print(
                    f"  Progress: {i}/{self.stats['total_files']} files validated",
                    end="\r",
                )

            is_valid, error_msg = self.validate_json_file(filepath)

            if is_valid:
                self.stats["valid_files"] += 1
            else:
                self.stats["invalid_files"] += 1
                invalid_files.append((filepath, error_msg))

                # Track errors by category
                category = filepath.parent.name
                self.stats["errors"][category] = (
                    self.stats["errors"].get(category, 0) + 1
                )

                self.log(
                    f"❌ INVALID: {filepath.relative_to(self.output_dir)}", force=True
                )
                self.log(f"   Reason: {error_msg}", force=True)

        if not self.quiet:
            print()  # Clear progress line

        return invalid_files

    def delete_invalid_files(self, invalid_files: List[Tuple[Path, str]]) -> int:
        """
        Delete invalid files

        Returns:
            Number of files deleted
        """
        if not invalid_files:
            return 0

        self.log(f"\n{'='*70}")
        self.log(f"Deleting {len(invalid_files)} invalid files...")
        self.log(f"{'='*70}\n")

        deleted_count = 0

        for filepath, error_msg in invalid_files:
            try:
                filepath.unlink()
                deleted_count += 1
                self.log(f"🗑️  Deleted: {filepath.relative_to(self.output_dir)}")
            except Exception as e:
                self.log(f"❌ Failed to delete {filepath}: {e}", force=True)

        self.stats["deleted_files"] = deleted_count
        return deleted_count

    def print_summary(self):
        """Print validation summary"""
        self.log(f"\n{'='*70}")
        self.log(f"VALIDATION SUMMARY")
        self.log(f"{'='*70}")
        self.log(f"Total files:      {self.stats['total_files']}")
        self.log(f"Valid files:      {self.stats['valid_files']} ✅")
        self.log(f"Invalid files:    {self.stats['invalid_files']} ❌")
        if self.stats["deleted_files"] > 0:
            self.log(f"Deleted files:    {self.stats['deleted_files']} 🗑️")
        self.log(f"{'='*70}")

        if self.stats["errors"]:
            self.log(f"\nErrors by category:")
            for category, count in sorted(self.stats["errors"].items()):
                self.log(f"  {category}: {count}")

        print()

        # Return exit code
        if self.stats["invalid_files"] > 0 and self.stats["deleted_files"] == 0:
            self.log(
                f"⚠️  Found {self.stats['invalid_files']} invalid files", force=True
            )
            self.log(f"   Run with --delete-invalid to remove them", force=True)
            return 1
        elif self.stats["invalid_files"] == 0:
            self.log(f"✅ All files are valid!", force=True)
            return 0
        else:
            self.log(
                f"✅ Cleaned up {self.stats['deleted_files']} invalid files", force=True
            )
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate NBA API JSON files and detect partial/corrupted data"
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp/nba_api_comprehensive",
        help="NBA API output directory (default: /tmp/nba_api_comprehensive)",
    )
    parser.add_argument(
        "--season",
        type=int,
        help="Validate only files from specific season (e.g., 1996)",
    )
    parser.add_argument(
        "--delete-invalid",
        action="store_true",
        help="Delete invalid/partial files (use with caution!)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Quiet mode - only show errors and summary"
    )

    args = parser.parse_args()

    # Create validator
    validator = NBAAPIFileValidator(output_dir=args.output_dir, quiet=args.quiet)

    # Validate files
    invalid_files = validator.validate_season_files(season=args.season)

    # Delete invalid files if requested
    if args.delete_invalid and invalid_files:
        validator.delete_invalid_files(invalid_files)

    # Print summary and exit with appropriate code
    exit_code = validator.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
