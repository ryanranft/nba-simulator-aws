#!/usr/bin/env python3
"""
ESPN Scrape Validation

Validates that scraped ESPN JSON files have the correct structure.
"""

import json
from pathlib import Path
from typing import Dict, List

# Base directory
BASE_DIR = Path("/Users/ryanranft/nba-simulator-aws/data")

# Games to validate
GAMES = ["400975770", "401070722"]
DATES = ["20180316", "20181022"]


class ESPNScrapeValidator:
    """Validate ESPN scraped data"""

    def __init__(self):
        self.validation_results = []

    def validate_box_score(self, game_id: str) -> Dict:
        """Validate box score file"""
        file_path = BASE_DIR / "nba_box_score" / f"{game_id}.json"

        result = {
            "game_id": game_id,
            "data_type": "box_score",
            "file_path": str(file_path),
            "exists": file_path.exists(),
            "valid_structure": False,
            "has_required_keys": False,
            "file_size": 0,
            "errors": [],
        }

        if not file_path.exists():
            result["errors"].append("File not found")
            return result

        try:
            # Load JSON
            with open(file_path, "r") as f:
                data = json.load(f)

            result["file_size"] = file_path.stat().st_size

            # Check structure
            if "page" in data and "content" in data["page"]:
                result["valid_structure"] = True

                gamepackage = data["page"]["content"].get("gamepackage", {})
                if "bxscr" in gamepackage:
                    result["has_required_keys"] = True
                else:
                    result["errors"].append("Missing 'bxscr' key in gamepackage")
            else:
                result["errors"].append(
                    "Invalid top-level structure (missing page/content)"
                )

        except json.JSONDecodeError as e:
            result["errors"].append(f"JSON decode error: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")

        return result

    def validate_pbp(self, game_id: str) -> Dict:
        """Validate play-by-play file"""
        file_path = BASE_DIR / "nba_pbp" / f"{game_id}.json"

        result = {
            "game_id": game_id,
            "data_type": "pbp",
            "file_path": str(file_path),
            "exists": file_path.exists(),
            "valid_structure": False,
            "has_required_keys": False,
            "file_size": 0,
            "play_count": 0,
            "errors": [],
        }

        if not file_path.exists():
            result["errors"].append("File not found")
            return result

        try:
            # Load JSON
            with open(file_path, "r") as f:
                data = json.load(f)

            result["file_size"] = file_path.stat().st_size

            # Check structure
            if "page" in data and "content" in data["page"]:
                result["valid_structure"] = True

                gamepackage = data["page"]["content"].get("gamepackage", {})
                if "pbp" in gamepackage:
                    result["has_required_keys"] = True

                    # Count plays
                    if "playGrps" in gamepackage["pbp"]:
                        for group in gamepackage["pbp"]["playGrps"]:
                            result["play_count"] += (
                                len(group) if isinstance(group, list) else 1
                            )

                    # Validate play count range (typical game has 400-500 plays)
                    if result["play_count"] < 300:
                        result["errors"].append(
                            f"Low play count: {result['play_count']}"
                        )
                    elif result["play_count"] > 600:
                        result["errors"].append(
                            f"High play count: {result['play_count']}"
                        )
                else:
                    result["errors"].append("Missing 'pbp' key in gamepackage")
            else:
                result["errors"].append(
                    "Invalid top-level structure (missing page/content)"
                )

        except json.JSONDecodeError as e:
            result["errors"].append(f"JSON decode error: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")

        return result

    def validate_team_stats(self, game_id: str) -> Dict:
        """Validate team stats file"""
        file_path = BASE_DIR / "nba_team_stats" / f"{game_id}.json"

        result = {
            "game_id": game_id,
            "data_type": "team_stats",
            "file_path": str(file_path),
            "exists": file_path.exists(),
            "valid_structure": False,
            "has_required_keys": False,
            "file_size": 0,
            "errors": [],
        }

        if not file_path.exists():
            result["errors"].append("File not found")
            return result

        try:
            # Load JSON
            with open(file_path, "r") as f:
                data = json.load(f)

            result["file_size"] = file_path.stat().st_size

            # Check structure
            if "page" in data and "content" in data["page"]:
                result["valid_structure"] = True

                gamepackage = data["page"]["content"].get("gamepackage", {})
                if "gmLdrs" in gamepackage:
                    result["has_required_keys"] = True
                else:
                    result["errors"].append("Missing 'gmLdrs' key in gamepackage")
            else:
                result["errors"].append(
                    "Invalid top-level structure (missing page/content)"
                )

        except json.JSONDecodeError as e:
            result["errors"].append(f"JSON decode error: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")

        return result

    def validate_schedule(self, date_str: str) -> Dict:
        """Validate schedule file"""
        file_path = BASE_DIR / "nba_schedule_json" / f"{date_str}.json"

        result = {
            "date": date_str,
            "data_type": "schedule",
            "file_path": str(file_path),
            "exists": file_path.exists(),
            "valid_structure": False,
            "has_required_keys": False,
            "file_size": 0,
            "game_count": 0,
            "errors": [],
        }

        if not file_path.exists():
            result["errors"].append("File not found")
            return result

        try:
            # Load JSON
            with open(file_path, "r") as f:
                data = json.load(f)

            result["file_size"] = file_path.stat().st_size

            # Check structure
            if "page" in data and "content" in data["page"]:
                result["valid_structure"] = True

                events = data["page"]["content"].get("events", {})
                if date_str in events:
                    result["has_required_keys"] = True
                    result["game_count"] = len(events[date_str])
                else:
                    result["errors"].append(f"Missing '{date_str}' key in events")
            else:
                result["errors"].append(
                    "Invalid top-level structure (missing page/content)"
                )

        except json.JSONDecodeError as e:
            result["errors"].append(f"JSON decode error: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")

        return result

    def validate_all(self) -> List[Dict]:
        """Validate all scraped files"""
        print("=" * 70)
        print("ESPN Scrape Validation")
        print("=" * 70)
        print()

        # Validate box scores
        print("Validating Box Scores...")
        for game_id in GAMES:
            result = self.validate_box_score(game_id)
            self.validation_results.append(result)
            self._print_result(result)

        # Validate PBP
        print("\nValidating Play-by-Play...")
        for game_id in GAMES:
            result = self.validate_pbp(game_id)
            self.validation_results.append(result)
            self._print_result(result)

        # Validate team stats
        print("\nValidating Team Stats...")
        for game_id in GAMES:
            result = self.validate_team_stats(game_id)
            self.validation_results.append(result)
            self._print_result(result)

        # Validate schedules
        print("\nValidating Schedules...")
        for date_str in DATES:
            result = self.validate_schedule(date_str)
            self.validation_results.append(result)
            self._print_result(result)

        return self.validation_results

    def _print_result(self, result: Dict):
        """Print validation result"""
        identifier = result.get("game_id") or result.get("date")
        data_type = result["data_type"]

        if (
            result["exists"]
            and result["valid_structure"]
            and result["has_required_keys"]
            and not result["errors"]
        ):
            status = "✅ PASS"
            extra = f" ({result['file_size']:,} bytes"
            if "play_count" in result and result["play_count"] > 0:
                extra += f", {result['play_count']} plays"
            elif "game_count" in result:
                extra += f", {result['game_count']} games"
            extra += ")"
            print(f"  {identifier} ({data_type}): {status}{extra}")
        else:
            status = "❌ FAIL"
            print(f"  {identifier} ({data_type}): {status}")
            for error in result["errors"]:
                print(f"    - {error}")

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("Validation Summary")
        print("=" * 70)
        print()

        total = len(self.validation_results)
        passed = sum(
            1
            for r in self.validation_results
            if r["exists"]
            and r["valid_structure"]
            and r["has_required_keys"]
            and not r["errors"]
        )
        failed = total - passed

        print(f"Total files validated: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")

        if failed == 0:
            print("\n✅ All files validated successfully!")
        else:
            print(f"\n❌ {failed} file(s) failed validation")

        print("\n" + "=" * 70)


def main():
    validator = ESPNScrapeValidator()
    validator.validate_all()
    validator.print_summary()


if __name__ == "__main__":
    main()
